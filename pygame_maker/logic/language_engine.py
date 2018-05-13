"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Adapted from the fourFn.py example that ships with PyParser
original code copyright 2003-2009 by Paul McGuire

handles math operations, predefined functions, keywords, boolean comparisons,
 function definitions, setting and using any supplied global variables,
 if/elseif/else conditionals, comments
represent toy language source code with python classes

toy language description:
expressions contain:
 atoms:
  numbers (int, float)
  bare identifiers (symbols)
  identifier( <empty> | <comma-delimited args> ) (function call)
  parenthesized expression
 operators:
  unary -, +, -, *, /, %, ^, <, <=, >, >=, ==, !=, and, or, not
 operations are all in infix format
high-level language constructs are one of three types:
 assignments:
  <symbol> = <expression>
  '=' must be delimited by spaces
 conditionals:
  if (expression) { <zero or more> ( assignment | conditional ) }
  optional elseif (expression) { <zero or more> ( assignment | conditional ) }
   (any number of elseif)
  optional else { <zero or more> ( assignment | conditional ) }
   only one, and it must come after if [elseif..]
 function definition:
  function <name>( void | (comma-delimited <type> <argname> ) ) {
   <zero or more> ( assignment | conditional | return <expression> )
   }
"""

import imp
import numbers
import math
import operator
import os
import re
import sys
from pyparsing import Literal, Word, Group, Optional, ZeroOrMore, OneOrMore, Forward, \
    nums, alphas, Regex, Keyword, stringEnd, ParseFatalException
import pygame_maker.support.logging_object as logging_object
import pygame_maker.logic.infix_to_postfix as infix_to_postfix


class DuplicateCodeBlockError(logging_object.LoggingException):
    """Raised when a duplicate code block name is found."""
    pass


class UnknownCodeBlockError(logging_object.LoggingException):
    """Raised when an unknown code block name is executed."""
    pass


class OpStackOverflowError(logging_object.LoggingException):
    """
    Raised when the number of symbols and operators in a code block are not
    compatible (too many symbols).
    """
    pass


class OpStackUnderflowError(logging_object.LoggingException):
    """
    Raised when the number of symbols and operators in a code block are not
    compatible (too few symbols).
    """
    pass


class SymbolTable(object):
    """
    Store symbols used by the language engine.  Store variables and constants
    separately; don't allow constants to change once defined.

    The language engine makes use of symbol tables when running the interpreted
    language code.  Symbol tables support both constants and variables.  An
    initial set of variables can be passed into initial_symbols.  A callback,
    if specified in sym_change_callback, will be called whenever a symbol
    changes.  The callback will be expected to have the signature
    callback(sym_name, new_value).
    """
    #: Any unknown symbol receives this value, to help with debugging
    DEFAULT_UNINITIALIZED_VALUE = -sys.maxsize - 1

    def __init__(self, initial_symbols=None, sym_change_callback=None):
        """
        Initialize a new symbol table.

        :param initial_symbols: The initial contents to place in the
            variables section of the symbol table
        :type initial_symbols: dict
        :param sym_change_callback: An optional callback to execute whenever
            the interpreted language changes a symbol's value
        :type sym_change_callback: callable
        """
        self.vars = {}
        if initial_symbols is not None:
            self.vars.update(initial_symbols)
        self.sym_change_callback = sym_change_callback
        self.consts = {}

    def dump_vars(self):
        """
        For debugging, dump the contents of the symbol table.  List constants
        and variables separately.
        """
        constlist = list(self.consts.keys())
        constlist.sort()
        print("constants:")
        for const in constlist:
            print("{} = {}".format(const, self.consts[const]))
        varlist = list(self.vars.keys())
        varlist.sort()
        print("variables:")
        for var in varlist:
            print("{} = {}".format(var, self.vars[var]))

    def keys(self):
        """
        Return the list of all symbols, whether constants or variables.

        :return: Symbol list
        :rtype: list
        """
        return list(self.vars.keys()) + list(self.consts.keys())

    def __setitem__(self, item, val):
        """
        Set a variable to a new value.  Don't allow constants to be written
        this way.

        :param item: The symbol to set
        :type item: str
        :param val: The symbol's new value
        """
        # print("Setting {} to {}".format(item, val))
        # don't allow constants to be written this way
        if item not in self.consts:
            self.vars[item] = val
            if self.sym_change_callback:
                self.sym_change_callback(item, val)

    def __getitem__(self, item):
        """
        Retrieve a symbol's value.  If not found, return the uninitialized
        value.

        :param item: The symbol to find the value of
        :type item: str
        :return: The symbol's value
        """
        new_val = self.DEFAULT_UNINITIALIZED_VALUE
        if item in self.consts:
            new_val = self.consts[item]
        elif item in self.vars:
            new_val = self.vars[item]
        # print("Retrieve item {}: {}".format(item, new_val))
        return new_val

    def set_constant(self, constant_name, constant_value):
        """
        Called from within the game engine to set values that can be read from,
        but not written to, by user code.

        User code doesn't (yet) have a way to create constants.

        :param constant_name: The constant's name
        :type constant_name: str
        :param constant_value: The constant's value
        """
        self.consts[constant_name] = constant_value


class CodeBlock(logging_object.LoggingObject):
    """
    Helper class that is created by the CodeBlockGenerator class method, that
    collects the infix form of source code in the C-like language supported by
    the language engine and converts it to a more readily executable postfix
    form. Because of the generator's constraints (the pyparsing function re-
    uses the same object for every parsing run), this class supports deep
    copying.  Optionally, the abstract syntax tree (AST) can be stored within
    the object.

    PyParsing API documentation can be found at:
    http://pythonhosted.org/pyparsing/
    """
    OPERATOR_FUNCTIONS = {
        "operator.add": ["number", "number"],
        "operator.sub": ["number", "number"],
        "operator.mul": ["number", "number"],
        "operator.truediv": ["number", "number"],
        "operator.mod": ["number", "number"],
        "operator.not_": ["bool"],
        "operator.lt": ["number", "number"],
        "operator.le": ["number", "number"],
        "operator.gt": ["number", "number"],
        "operator.ge": ["number", "number"],
        "operator.eq": ["number", "number"],
        "operator.ne": ["number", "number"],
        "math.pow": ["number", "number"]
    }
    OPERATOR_REPLACEMENTS = {
        "+": "operator.add",
        "-": "operator.sub",
        "*": "operator.mul",
        "/": "operator.truediv",
        "%": "operator.mod",
        "<": "operator.lt",
        "not": "operator.not_",
        "<=": "operator.le",
        ">": "operator.gt",
        ">=": "operator.ge",
        "==": "operator.eq",
        "!=": "operator.ne",
        "^": "math.pow"
    }
    CONDITIONALS = [
        "operator.lt",
        "operator.le",
        "operator.gt",
        "operator.ge",
        "operator.eq",
        "operator.ne"
    ]
    REVERSE_OPERATORS = {
        "operator.add": "+",
        "operator.sub": "-",
        "operator.mul": "*",
        "operator.truediv": "/",
        "operator.mod": "%",
        "operator.lt": "<",
        "operator.le": "<=",
        "operator.gt": ">",
        "operator.ge": ">=",
        "operator.eq": "==",
        "operator.ne": "!=",
        "math.pow": "**"
    }
    SYMBOL_RE = re.compile("_[a-zA-Z][a-zA-Z0-9._]*$")
    GLOBAL_RE = re.compile("^__")
    RETURN_RE = re.compile("  return ")

    def __init__(self, name, module_context, funcmap=None, astree=None):
        """
        Initialize a new code block.

        A function map, if supplied, represents the external function table
        made available to the code block.  Void argument lists can be
        represented with an empty list.  The number and type of arguments
        supplied assist with syntax checking.

        :param name: The name assigned to this code block
        :type name: str
        :param module_context: A new module for the Python blocks to be loaded
            into
        :type module_context: imp.new_module
        :param funcmap: A dict with <function_name>: [arg_type1, .., arg_typeN]
            entries
        :type funcmap: dict
        :param astree: the abstract syntax tree produced by pyparsing (stored
            in an attribute, but not currently used)
        """
        super(CodeBlock, self).__init__(type(self).__name__)
        self.name = name
        self.module_context = module_context
        self.outer_block = []
        self.inner_blocks = []
        self.stack = self.outer_block
        self.frame = self.outer_block
        self.scratch = []
        self.inner_block_count = 0
        self.__name__ = None
        self.functionmap = {}
        self.function_name = ''
        if funcmap is not None:
            self.functionmap.update(funcmap)
        self.astree = astree

    def add_to_func_map(self, func_map):
        """
        Supply a dict for <function_name>: [arg_type1, .., arg_typeN] entries.
        This helps the syntax check phase know how many args to expect.  Later,
        the arg type list can be checked to make sure that supplied argument
        types match the function call signature.

        :param func_map: The dict containing function name to argument type
            list mappings
        :type func_map: dict
        """
        self.debug("add_to_func_map({})".format(str(func_map)))
        self.functionmap.update(func_map)

    def push_assignment(self, parsestr, loc, toks):
        """
        Append an assignment operation to the current block.

        When the parser finds a assignment match, the assignee and '='
        operator need to be added here, since the parser won't add these
        itself.  Push these and the right-hand side of the assignment (which
        were already collected in self.scratch) onto the current stack.  '='
        will always go at the end.  An optional ``global`` keyword can precede
        the asignee, to make it part of the global symbol table.

        :param parsestr: The entire string parsed by pyparsing
        :type parsestr: str
        :param loc: The location passed in by pyparsing
        :param toks: The iterable sequence of tokens parsed
        :type toks: iterable
        """
        self.debug("push_assignment(<code str>, parsestr={}, loc={}, toks={}):".format(
            loc, parsestr, toks))
        assign_list = []
        global_prefix = ""
        for assign_tok in toks.asList():
            for inner_item in assign_tok:
                if inner_item == '=':
                    break
                if inner_item == "global":
                    global_prefix = "_"
                else:
                    assign_list.append("{}_{}".format(global_prefix,
                                                      inner_item))
            break
        # print("assignment scratch: {}".format(self.scratch))
        self.stack.append(assign_list + list(self.scratch) + ['='])
        self.debug("  assignment: {}".format(self.stack[-1]))
        self.scratch = []

    def push_conditional_block(self, parsestr, loc, toks):
        """
        Insert a new conditional block into its container block.  Keep track of
        nesting.

        When the parser matches a conditional's block, it's time to close it
        (the instructions were already collected on the current stack).  Keep
        track here of the block level decrement, either from a child inner-node
        up to its parent, or the top-most inner block up to the outer block.
        Push a copy of the child inner node onto its parent's stack.  This
        method changes the stack reference.

        :param parsestr: The entire string parsed by pyparsing
        :type parsestr: str
        :param loc: The location passed in by pyparsing
        :param toks: The iterable sequence of tokens parsed
        :type toks: iterable
        """
        self.debug("push_conditional_block(<code str>, parsestr={}, loc={}, toks={}):".
                   format(parsestr, loc, toks))
        if self.inner_block_count > 1:
            # print("inner block #{}\n{}".format(self.inner_block_count-1,self.stack))
            self.inner_block_count -= 1
            # print("append to {}".format(self.inner_blocks[self.inner_block_count-1]))
            self.inner_blocks[self.inner_block_count - 1].append(list(self.stack))
            self.debug("  stack now points to inner block #{:d}".format(self.inner_block_count - 1))
            self.stack = self.inner_blocks[self.inner_block_count - 1]
            self.debug("  delete inner_blocks[{:d}]".format(self.inner_block_count))
            del self.inner_blocks[self.inner_block_count]
        else:
            # print("inner block #0\n{}".format(self.stack))
            self.frame.append(list(self.stack))
            self.debug("  clear inner_blocks[0]")
            self.inner_block_count = 0
            del self.inner_blocks[0]
            self.stack = self.frame
            self.debug("  stack now points to outer block")

    def push_if_cond(self, parsestr, loc, toks):
        """
        Create a new block for a conditional.

        When the parser matches if/elseif/else keywords, anticipate that a new
        block will be added. Increment the block level -- either outer block to
        topmost inner block, or parent inner block to child inner block.  This
        is optimistic, since the parser might not recognize the pattern
        following the keyword, but that signals a syntax error, in which case
        the stack level is moot.  Collect the keyword name and push it onto the
        parent's stack.  This method changes the stack reference.

        :param parsestr: The entire string parsed by pyparsing
        :type parsestr: str
        :param loc: The location passed in by pyparsing
        :param toks: The iterable sequence of tokens parsed
        :type toks: iterable
        """
        # print("push {}".format(toks.asList()))
        self.debug("push_if_cond(<code str>, parsestr={}, loc={}, toks={}):".
                   format(parsestr, loc, toks))
        if_statement = ""
        for tok in toks:
            if_statement = "_{}".format(tok)
            self.debug("  push if statement: {}".format(if_statement))
            break
        container_block = self.frame
        if self.inner_block_count > 0:
            container_block = self.inner_blocks[-1]
            self.debug("  container: inner block #{:d}".format(self.inner_block_count - 1))
        else:
            self.debug("  container: outer block")
        container_block.append(if_statement)
        # print("outer block is now:\n{}".format(self.outer_block))
        self.inner_block_count += 1
        self.inner_blocks.append([])
        self.debug("  stack now points at inner block #{:d}".format(self.inner_block_count - 1))
        self.stack = self.inner_blocks[-1]

    def push_comparison(self, parsestr, loc, toks):
        """
        When the parser matches a comparison, push it onto the current stack.

        :param parsestr: The entire string parsed by pyparsing
        :type parsestr: str
        :param loc: The location passed in by pyparsing
        :param toks: The iterable sequence of tokens parsed
        :type toks: iterable
        """
        self.debug("push_comparison(<code str>, parsestr={}, loc={}, toks={}):".
                   format(parsestr, loc, toks))
        self.debug("  append comparison {} to stack".format(str(self.scratch)))
        self.stack.append(list(self.scratch))
        self.scratch = []

    def count_function_args(self, parsestr, loc, toks):
        """
        Count the arguments supplied in a function call.  Throw an exception
        if the count doesn't match the function signature.

        This is where the parser needs help, since it has no idea how many args
        a function expects.  The external function table in functionmap is
        checked against the supplied function name to determine its argument
        count.  Unfortunately, in the case where function results are placed
        directly into function args, the whole mess appears in the ``toks``
        list.  The saving grace is that functions are checked from inner ->
        outer, so it's possible to skip over later ``toks`` containing function
        names, assuming that their argument lists will be checked separately.
        This still implies that the other functions in the list need to be
        checked to find out how many args will be skipped (and even then, it's
        only important for functions that have more than 1 arg, since the arg
        count is based on how many ','s are found).

        TODO: Argument type-checking. Assume this is as simple as number vs.
        string, and strings aren't supported yet.

        :param parsestr: The entire string parsed by pyparsing
        :type parsestr: str
        :param loc: The location passed in by pyparsing
        :param toks: The iterable sequence of tokens parsed
        :type toks: iterable
        :raise: ParseFatalException for function call errors
        """
        # print("function w/ args: {}".format(toks))
        # assume embedded function calls have been validated, just skip
        #  them to count the args in the outer function call
        self.debug("count_function_args(<code str>, parsestr={}, loc={}, toks={}):".
                   format(parsestr, loc, toks))
        func_call = False
        func_name = ""
        skip_count = 0
        arg_count = 0
        tok_idx = 0
        in_string = False
        for tok in toks:
            if tok_idx == 0:
                if tok in self.functionmap:
                    func_call = True
                    func_name = str(tok)
                    tok_idx += 1
                    continue
                else:
                    # unknown function encountered
                    self.error("{} at {}: Unknown function call '{}'".format(parsestr, loc, tok))
                    raise ParseFatalException
            if tok == "\"":
                # keep track of strings, to ignore functions named inside a string
                in_string = not in_string
            if func_call:
                if arg_count == 0:
                    arg_count = 1
                # if this function takes no arguments, we shouldn't be here..
                self.debug("  check {} call vs function map".format(tok))
                if len(self.functionmap[func_name]["arglist"]) == 0:
                    self.error("{} at {}: Too many arguments to function \"{}\"".
                               format(parsestr, loc, func_name))
                    raise ParseFatalException
                # check whether an embedded function call should be skipped
                # print("checking {}..".format(tok))
                if tok in self.functionmap and not in_string:
                    skips = len(self.functionmap[tok]["arglist"])
                    if skips > 0:
                        skips -= 1  # future commas imply > 1 arg to skip
                    skip_count += skips
                    self.debug("  skip call to {} with {} args".
                               format(tok, len(self.functionmap[tok])))
                    # print("skip count now is: {}".format(skip_count))
                if tok == ',':
                    if skip_count > 0:
                        skip_count -= 1
                        self.debug("  Found ',' and decrease skip count to {}".format(skip_count))
                    else:
                        arg_count += 1
                        self.debug("  Found ',' and increase arg count to {}".format(arg_count))
            tok_idx += 1

        if func_call:
            if arg_count < len(self.functionmap[func_name]["arglist"]):
                self.error("{} at {}: Too few arguments to function \"{}\"".
                           format(parsestr, loc, func_name))
                raise ParseFatalException(
                    parsestr, loc=loc,
                    msg="Too few arguments to function \"{}\"".format(func_name))
            elif arg_count > len(self.functionmap[func_name]["arglist"]):
                self.error("{} at {}: Too many arguments to function \"{}\"".
                           format(parsestr, loc, func_name))
                raise ParseFatalException

    def push_func_args(self, parsestr, loc, toks):
        """
        Collect the function name and arguments from a function definition.

        Validate the argument types.  Create a new block within the functionmap
        and point the frame at it, so future constructs will be placed in the
        function.

        :param parsestr: The entire string parsed by pyparsing
        :type parsestr: str
        :param loc: The location passed in by pyparsing
        :param toks: The iterable sequence of tokens parsed
        :type toks: iterable
        :raise: ParseFatalException if the function already exists, has
            invalid argument types, or has anything following ``void``
        """
        self.debug("pushFunctionArgs(<code str>, parsestr={}, loc={}, toks={}):".
                   format(parsestr, loc, toks))
        func_name = None
        arg_with_type = None
        arg_list = []
        for tok in toks:
            for item in tok:
                if item == ',':
                    continue
                if not func_name:
                    func_name = str(item)
                    self.debug("  New function: {}".format(func_name))
                    if func_name in self.functionmap:
                        self.error("{} at {}: Redefinition of existing function '{}'".
                                   format(parsestr, loc, func_name))
                        raise ParseFatalException
                    continue
                if func_name:
                    if not arg_with_type:
                        typename = str(item)
                        if typename not in ["void", "number", "string"]:
                            self.error(
                                "{} at {}: Missing type name in declaration of function '{}'".
                                format(parsestr, loc, func_name))
                            raise ParseFatalException
                        arg_with_type = {"type": typename}
                        if typename == "void":
                            arg_list.append(dict(arg_with_type))
                    else:
                        if arg_with_type["type"] == "void":
                            self.error(
                                "{} at {}: Unexpected token '{}' in declaration of function '{}'".
                                format(parsestr, loc, str(item), func_name))
                            raise ParseFatalException
                        arg_with_type["name"] = str(item)
                        arg_list.append(dict(arg_with_type))
                        arg_with_type = None
        self.debug("  Function args: {}".format(str(arg_list)))
        if arg_list[0]["type"] != "void":
            self.functionmap[func_name] = {"arglist": arg_list}
        else:
            self.functionmap[func_name] = {"arglist": []}
        self.functionmap[func_name]["block"] = []
        # print("New functionmap: {}".format(self.functionmap))
        self.stack = self.functionmap[func_name]["block"]
        self.frame = self.functionmap[func_name]["block"]
        self.function_name = func_name

    def push_func_block(self, parsestr, loc, toks):
        """
        Take the current function block frame and reduce it, before switching
        the frame back to the outer_block.

        :param parsestr: The entire string parsed by pyparsing
        :type parsestr: str
        :param loc: The location passed in by pyparsing
        :param toks: The iterable sequence of tokens parsed
        :type toks: iterable
        """
        # reduce the function source
        self.debug("push_func_block(<code str>, parsestr={}, loc={}, toks={}):".
                   format(parsestr, loc, toks))
        self.reduce_block(self.frame)
        func_loc = [0, 0]
        param_list = [fparam["name"] for fparam in self.functionmap[self.function_name]["arglist"]]
        function_body = self.to_python_block(self.frame, func_loc, self.function_name)
        param_list.append("count=0")
        func_lines = ["def userfunc_{}(_symbols, {}):".format(self.function_name,
                                                              ",".join(param_list))]
        func_lines += [
            "  if (count > 100):",
            "    raise CodeBlockRuntimeError(\"{}: Call stack depth limit exceeded\")".
            format(self.function_name)
        ]
        func_lines += function_body
        ret_minfo = self.RETURN_RE.match(func_lines[-1])
        if not ret_minfo:
            # Force all functions to return a value.  If the final line is
            #  not 'return', return the "uninitialized" value
            func_lines.append("  return {:d}".format(-sys.maxsize - 1))
        function_code = "\n".join(func_lines)
        self.info("  Function code:\n{}".format(function_code))
        self.functionmap[self.function_name]['compiled'] = \
            compile(function_code, "<c_{}>".format(self.function_name), 'exec')
        self.function_name = "None"
        # reset the stack and frame
        self.stack = self.outer_block
        self.frame = self.outer_block

    def push_atom(self, parsestr, loc, toks):
        """
        When the parser finds an "atom": PI, e, a number, a function call, a
        '(' ')' delimited expression, or bare identifier, it will be pushed
        onto a scratch list.  A copy of the scratch list is later pushed onto
        the current stack reference when a logical grouping is found (an
        assignment statement or conditional block).

        :param parsestr: The entire string parsed by pyparsing
        :type parsestr: str
        :param loc: The location passed in by pyparsing
        :param toks: The iterable sequence of tokens parsed
        :type toks: iterable
        """
        self.debug("push_atom(<code str>, parsestr={}, loc={}, toks={}):".
                   format(parsestr, loc, toks))
        tok_n = 0
        add_not = False
        add_tok = None
        is_string = False
        for tok in toks:
            if tok_n == 0:
                if tok == 'not':
                    add_not = True
                    tok_n += 1
                    continue
                elif tok.startswith('"'):
                    is_string = True
                    add_tok = tok
                    break
                else:
                    add_tok = tok
                    break
            else:
                add_tok = tok
                break
        func_call = False
        if add_tok in self.functionmap:
            func_call = True
        # print("atom: {}".format(toks.asList()))
        if func_call:
            self.scratch += infix_to_postfix.convert_infix_to_postfix([add_tok],
                                                                      self.OPERATOR_REPLACEMENTS)
            if add_not:
                self.scratch.append("operator.not_")
        else:
            if add_not:
                self.debug("  not tokens: {}".format(toks.asList()))
            if not is_string:
                self.scratch += infix_to_postfix.convert_infix_to_postfix(
                    toks.asList(), self.OPERATOR_REPLACEMENTS)
            else:
                self.scratch += ["str({})".format("".join(toks.asList()))]
            # print("scratch is now: {}".format(self.scratch))

    def push_first(self, parsestr, loc, toks):
        """
        When the parser finds an operator ('^', '*', "/", "%", "+", "-", "<",
        "<=", ">", ">=", "==", "!="), this is called to place it onto a
        scratch list, using operator replacements to rename it to an actual
        python method.

        :param parsestr: The entire string parsed by pyparsing
        :type parsestr: str
        :param loc: The location passed in by pyparsing
        :param toks: The iterable sequence of tokens parsed
        :type toks: iterable
        """
        # print("pre-op: {}".format(toks.asList()))
        self.debug("push_first(<code str>, parsestr={}, loc={}, toks={}):".
                   format(parsestr, loc, toks))
        self.scratch += infix_to_postfix.convert_infix_to_postfix(toks[0],
                                                                  self.OPERATOR_REPLACEMENTS)
        self.debug("  op + scratch is now: {}".format(str(self.scratch)))

    def push_u_minus(self, parsestr, loc, toks):
        """
        From the original fourFn.py demo. Push 'unary -' to keep track of any
        terms that have been negated.

        :param parsestr: The entire string parsed by pyparsing
        :type parsestr: str
        :param loc: The location passed in by pyparsing
        :param toks: The iterable sequence of tokens parsed
        :type toks: iterable
        """
        self.debug("push_u_minus(<code str>, parsestr={}, loc={}, toks={}):".
                   format(parsestr, loc, toks))
        for tok in toks:
            if tok == '-':
                self.scratch.append('unary -')
            else:
                break

    def push_return(self, parsestr, loc, toks):
        """
        Push the stack containing the arguments for a return keyword, followed
        by "_return".

        :param parsestr: The entire string parsed by pyparsing
        :type parsestr: str
        :param loc: The location passed in by pyparsing
        :param toks: The iterable sequence of tokens parsed
        :type toks: iterable
        """
        self.debug("push_return(<code str>, parsestr={}, loc={}, toks={}):".
                   format(parsestr, loc, toks))
        self.stack.append(list(self.scratch) + ["_return"])
        self.scratch = []

    def reduce_line(self, code_line):
        """
        Iterate over a list containing an expression, pre-calculating
        simple numeric operations and replacing the operands and operator
        with the result.  Repeat until no more changes are made.

        :param code_line: The list of the terms in an expression
        :type code_line: list
        """
        self.debug("    reduce_line(code_line={}):".format(str(code_line)))
        changed_line = True
        while changed_line:
            line_idx = 0
            changed_line = False
            while line_idx < len(code_line):
                check_op = "{}".format(code_line[line_idx])
                # print("check op: {}".format(check_op))
                if check_op in self.OPERATOR_FUNCTIONS:
                    # print("found op: {}".format(check_op))
                    op_len = len(self.OPERATOR_FUNCTIONS[check_op])
                    if line_idx >= op_len:
                        all_numbers = True
                        for rev in range(line_idx - op_len, line_idx):
                            rev_item = code_line[rev]
                            # print("check if num: {}".format(rev_item))
                            if not isinstance(rev_item, numbers.Number):
                                all_numbers = False
                                break
                        if all_numbers:
                            op_result = self.execute_operation(
                                check_op, code_line[line_idx - op_len:line_idx])
                            code_line[line_idx - op_len] = op_result
                            for unused in range(op_len):
                                del code_line[line_idx - op_len + 1]
                            changed_line = True
                            break
                elif check_op == "unary -":
                    # the special case
                    if line_idx > 0:
                        if isinstance(code_line[line_idx - 1], numbers.Number):
                            code_line[line_idx - 1] *= -1
                            del code_line[line_idx]
                            changed_line = True
                            break
                line_idx += 1

    def reduce_block(self, block):
        """
        Iterate through each line within the given block of postfix expressions
        and recursively through sub-blocks, reducing numeric operations when
        found.

        :param block: A list of code lines, which are either lists themselves,
            or the marker strings '_if', '_elseif', or '_else'
        :type block: list containing lists and/or strings
        """
        self.debug("  reduce_block(block={}):".format(block))
        block_idx = 0
        while block_idx < len(block):
            code_line = block[block_idx]
            if isinstance(code_line, str) and code_line in ['_if', '_elseif', '_else']:
                # handle the conditional block here, it's a list inside a list
                self.reduce_block(block[block_idx + 1])
                block_idx += 2
                continue
            if isinstance(code_line, list):
                # print("Reduce line: {}".format(code_line))
                self.reduce_line(code_line)
            block_idx += 1

    def reduce(self):
        """
        Perform as much argument reduction as possible.  Operations on numeric
        values can be replaced with the results.
        """
        self.debug("reduce():")
        self.reduce_block(self.outer_block)

    def to_python_line(self, code_line, loc=(0, 0), func_name=None):
        """
        Convert a line of game language into Python code.

        The hard work of arranging the postfix representation of a line of code
        into a line of executable Python code happens here.  The round-trip
        serves 2 purposes: the game language is essentially used for
        calculations, so doesn't need the full features of Python; and this
        effectively isolates and sanitizes user-written code to prevent it from
        adversely affecting the game engine.

        :param code_line: A list of postfix expression tokens for conversion
        :type code_line: list
        :param loc: The location of the line of code in the original source
        :type loc: 2-element array-like
        :param func_name: If this line is part of a function definition, the
            function's name
        :type func_name: None | str
        :raise: OpStackOverflowError if tokens were left over, or
            OpStackUnderflowError if expected tokens were missing
        :return: A line of Python code
        :rtype: str
        """
        self.debug("    to_python_line(code_line={}, loc={}, func_name={}):".format(
            str(code_line), loc, func_name))
        op_stack = []
        symbol = None
        start_pos = 0
        type_upgrade = False
        if code_line[-1] == '=':
            symbol = code_line[0][1:]
            start_pos = 1
        for op_idx in range(start_pos, len(code_line)):
            an_op = code_line[op_idx]
            if isinstance(an_op, int):
                op_stack.append({"type": "int", "val": str(an_op)})
            elif isinstance(an_op, float):
                op_stack.append({"type": "float", "val": str(an_op)})
            else:
                sym_minfo = self.SYMBOL_RE.match(an_op)
                if sym_minfo:
                    opname = an_op[1:]
                else:
                    opname = an_op
                if opname in self.OPERATOR_FUNCTIONS or opname in self.functionmap:
                    # perform a calculation, and place the result in the
                    #  op stack
                    arg_count = 0
                    opcall = opname
                    func_params = []
                    if opname in self.OPERATOR_FUNCTIONS:
                        arg_count = len(self.OPERATOR_FUNCTIONS[opname])
                    else:
                        arg_count = len(self.functionmap[opname]["arglist"])
                        opcall = "userfunc_{}".format(opname)
                        func_params = ["_symbols"]
                    id_start = len(op_stack) - arg_count
                    id_end = len(op_stack)
                    if id_start < 0:
                        raise OpStackUnderflowError
                    res_type = "int"
                    last_type = None
                    type_upgrade = False
                    params = list(op_stack[id_start:id_end])
                    if opcall not in self.CONDITIONALS:
                        for arghash in params:
                            # track argument types
                            if arghash["type"] == "float":
                                res_type = "float"
                            elif arghash["type"] == "string":
                                res_type = "str"
                            if not last_type:
                                last_type = res_type
                            elif last_type != res_type:
                                type_upgrade = True
                    else:
                        res_type = "bool"
                    # replace args and function call/operator with python
                    #  code string, keeping track of the result type
                    for unused in range(arg_count):
                        del op_stack[-1]
                    param_list = func_params + [param['val'] for param in params]
                    if func_name and (opcall not in self.OPERATOR_FUNCTIONS):
                        # if calling a function within a function block, append
                        #  a count+1 arg to limit recursion depth (this is to
                        #  prevent user code from crashing the game engine)
                        param_list.append("count+1")
                    op_stack.append({"type": res_type,
                                     "val": "{}({})".format(opcall, ",".join(param_list))})
                    if type_upgrade:
                        prev_val = op_stack[-1]["val"]
                        prev_val = "{}({})".format(res_type, prev_val)
                elif opname == "unary -":
                    # the special case
                    if len(op_stack) > 0:
                        last_op_val = op_stack[-1]["val"]
                        last_op_type = op_stack[-1]["type"]
                        if last_op_type in ["int", "float"]:
                            op_stack.insert(-1,
                                            {"type": last_op_type,
                                             "val": "operator.mul(-1, {})".format(last_op_val)})
                            del op_stack[-1]
                elif opname in ["and", "or"]:
                    id_start = len(op_stack) - 2
                    id_end = len(op_stack)
                    if id_start < 0:
                        raise OpStackUnderflowError(
                            "Stack underflow at line {} when assembling the line:\n{}".
                            format(loc[0], code_line), self.error)
                    params = list(op_stack[id_start:id_end])
                    for unused in range(2):
                        del op_stack[-1]
                    op_stack.append(
                        {"type": "bool",
                         "val": "(({}) {} ({}))".format(params[0]['val'],
                                                        opname, params[1]['val'])})
                elif opname == '=':
                    # '=' must always be the last token for an assignment.
                    #  Time to store the value in the symbol table
                    last_op_val = op_stack[-1]["val"]
                    last_op_val = "update_symbol(_symbols, '{}', {})".format(symbol, last_op_val)
                    op_stack[-1]['val'] = last_op_val
                    break
                elif opname.startswith("str("):
                    op_stack.append({"type": "str", "val": opname})
                elif opname == 'return':
                    last_op_val = op_stack[-1]["val"]
                    last_op_val = "return {}".format(last_op_val)
                    op_stack[-1]['val'] = last_op_val
                    break
                else:
                    func_arg = False
                    if func_name:
                        func_arg_names = [narg["name"] \
                            for narg in self.functionmap[func_name]["arglist"]]
                        if opname in func_arg_names:
                            func_arg = True
                    if not func_arg:
                        op_stack.append({"type": "int",
                                         "val": "get_symbol(_symbols, '{}')".format(opname)})
                    else:
                        op_stack.append({"type": "int",
                                         "val": "{}".format(opname)})
                        # print("New op_stack: {}".format(op_stack))
        if len(op_stack) > 1:
            raise OpStackOverflowError
        # apply the (possibly upgraded) result type to the remaining item
        self.debug("      Result of {}: {}".format(str(code_line), op_stack))
        python_code_line = "{}{}".format(' ' * loc[1], op_stack[-1]['val'])
        loc[0] += 1
        return python_code_line

    def to_python_block(self, block, loc=(0, 0), func_name=None):
        """
        When supplied a block of code objects, produce the Python source code
        for contained conditionals and assignments, using appropriate
        indentation.

        :param block: The list of code lines in the block
        :type block: list of lists
        :param loc: The location of the source block in game language code
        :type loc: 2-element array-like
        :param func_name: If the block is inside a function definition, supply
            the function's name
        :type func_name: None | str
        :return: The list of Python source code lines
        :rtype: list
        """
        self.debug("  to_python_block(block={}, loc={}, func_name={}):".format(str(block),
                                                                               str(loc), func_name))
        python_code_lines = []
        loc[1] += 2
        # print("block start: col is now: {}".format(loc[1]))
        block_idx = 0
        while block_idx < len(block):
            code_line = block[block_idx]
            if code_line in ["_if", "_elseif", "_else"]:
                cond_name = code_line[1:]
                python_code_lines += self.to_python_conditional(
                    cond_name, block[block_idx + 1], loc, func_name)
                block_idx += 2
                continue
            else:
                python_code_lines.append(self.to_python_line(code_line, loc, func_name))
                block_idx += 1
        loc[1] -= 2
        # print("block end: col is now: {}".format(loc[1]))
        return python_code_lines

    def to_python_conditional(self, conditional_name, block, loc=(0, 0), func_name=None):
        """
        When a conditional is found in a code block, produce an executable line
        of Python source code containing the condition name, possibly followed
        by a condition (e.g. if, elseif), then a list of all the lines (and/or
        other conditionals) within its code block.

        :param conditional_name: The conditional's keyword (if, elseif, else)
        :type conditional_name: str
        :param block: The list of game engine source code lines inside the
            conditional
        :type block: list of lists
        :param loc: The location of the conditional in the game language
            source code
        :type loc: 2-element array-like
        :param func_name: If the conditional is inside a function definition,
            supply the function's name
        :type func_name: None | str
        :return: The list of lines of Python source code
        :rtype: list
        """
        self.debug("  to_python_conditional(conditional_name={}, loc={}, func_name={}):".
                   format(conditional_name, loc, func_name))
        python_code_lines = []
        conditional_code = self.to_python_line(block[0], [loc[0], 0], func_name)
        py_cond_name = str(conditional_name)
        block_start_idx = 1
        if conditional_name == "elseif":
            py_cond_name = "elif"
        if py_cond_name in ["if", "elif"]:
            python_code_lines.append("{}{} ({}):".format(' ' * loc[1],
                                                         py_cond_name, conditional_code))
        else:
            python_code_lines.append("{}{}:".format(' ' * loc[1],
                                                    py_cond_name))
            block_start_idx = 0
        python_code_lines += self.to_python_block(block[block_start_idx:], loc,
                                                  func_name)
        return python_code_lines

    def to_python(self):
        """
        Convert the postfix code representation into executable Python code.

        :return: The Python source code, inside a single string
        :rtype: str
        """
        self.debug("to_python():")
        code_loc = [0, 0]
        python_code = ""
        # the code block has to have SOMETHING in it, but if it only contains
        #  function definitions, don't construct the run() method
        if len(self.outer_block) > 0:
            python_lines = ["def run(_symbols):"]
            python_lines += self.to_python_block(self.outer_block, code_loc)
            python_code = "\n".join(python_lines)
        return python_code

    def execute_operation(self, op_name, args):
        """
        Given a valid Python operation and a list containing its args, convert
        them into a string and eval() it.

        :param op_name: The name of the operator
        :type op_name: str
        :param args: The list of arguments to the operator
        :type args: list
        """
        self.debug("execute_operation(op_name={}, args={}):".format(op_name, args))
        res = None
        stargs = [str(a) for a in args]
        result_type = int
        for arg in args:
            if not isinstance(arg, int):
                result_type = type(arg)
        if op_name in self.OPERATOR_FUNCTIONS:
            # print("eval {} {}".format(op_name, stargs))
            eval_str = "{}({})".format(op_name, ",".join(stargs))
            res = eval(eval_str)
            # true/false become ints
            if isinstance(res, bool):
                if res:
                    res = 1
                else:
                    res = 0
            else:
                res = result_type(res)
        return res

    def load(self, import_list=None):
        """
        Place all functions and executable code into the source code module's
        __dict__.

        :param import_list: The list of modules that need to be imported into
            the module
        :type import_list: None | list
        """
        self.debug("load(import_list={}):".format(str(import_list)))
        for userfunc in self.functionmap:
            # print("exec {}".format(userfunc))
            if 'compiled' in self.functionmap[userfunc]:
                exec(self.functionmap[userfunc]['compiled'], self.module_context.__dict__)
        import_lines = "from pygame_maker.logic.run_time_support import *\n"
        if import_list:
            import_lines += "import {}\n".format(",".join(import_list))
        exec_code = self.to_python()
        if len(exec_code) > 0:
            pyth_code = import_lines + exec_code
            self.info("  Run program:\n{}".format(pyth_code))
            exec(pyth_code, self.module_context.__dict__)

    def run(self, sym_tables):
        """
        Execute the ``run()`` function inside the Python code block.

        :param sym_tables: A mapping of 'globals' => global symbol table,
            'locals' => local symbol table
        :type sym_tables: dict
        """
        self.debug("run(sym_tables={}):".format(str(sym_tables)))
        if "run" in self.module_context.__dict__:
            return self.module_context.run(sym_tables)

    def copy_to(self, other):
        """
        Perform a deep copy to another code block object.

        :param other: The code block instance to copy to
        :type other: :py:class:`CodeBlock`
        """
        self.debug("copy_to():")
        # other.stack = list(self.stack)
        # other.frame = list(self.frame)
        # other.scratch = list(self.scratch)
        # other.inner_blocks = list(self.inner_blocks)
        other.outer_block = list(self.outer_block)
        # print("Copied outer block:\n{}".format(other.outer_block))
        if self.astree:
            other.astree = list(self.astree)
        other.add_to_func_map(self.functionmap)

    def clear(self):
        """Clear out all lists in preparation for a new parsing operation."""
        self.debug("clear():")
        self.name = ""
        self.scratch = []
        self.inner_blocks = []
        self.inner_block_count = 0
        self.outer_block = []
        self.frame = self.outer_block
        self.stack = self.outer_block
        self.__name__ = None
        self.functionmap = {}
        self.astree = None


class CodeBlockGenerator(object):
    """
    Generate a CodeBlock using the wrap_code_block() class method upon a
    supplied source code string. A class member holds a code block object that
    is copied to a new code object, which is returned to the caller.
    """
    bnf = None
    #: The fixed code block every source code string is converted into.  A copy
    #: is returned to the wrap_code_block() caller before it is cleared for
    #: re-use
    code_block = CodeBlock("none", None)

    @classmethod
    def wrap_code_block(cls, program_name, module_context, source_code_str, funcmap=None):
        """
        Create a new code block with the given program data.

        :param program_name: The name of the program
        :type program_name: str
        :param module_context: The module to place the code into
        :type module_context: imp.new_module
        :param source_code_str: A string containing the game language source
        :type source_code_str: str
        :param funcmap: A dict mapping function names to argument type info
        :type funcmap: dict
        :return: A new executable code block
        :rtype: :py:class:`CodeBlock`
        """
        if module_context:
            cls.code_block.module_context = module_context
        if funcmap is not None:
            cls.code_block.add_to_func_map(funcmap)
        cls.bnf = bnf_interpret(cls.code_block)
        try:
            astree = cls.bnf.parseString(source_code_str)
            cls.code_block.reduce()
            new_block = CodeBlock(program_name, module_context,
                                  funcmap, astree)
            cls.code_block.copy_to(new_block)
        finally:
            cls.code_block.clear()
        return new_block


class LanguageEngine(logging_object.LoggingObject):
    """
    Interpret, initialize, and execute code blocks.  Requires managing tables
    of variables and functions that can be accessed by and/or created within
    the code block.
    """

    def __init__(self):
        """
        Initialize a new language engine.
        """
        super(LanguageEngine, self).__init__(type(self).__name__)
        #: The language engine's global symbol table
        self.global_symbol_table = SymbolTable()
        self.global_symbol_table.set_constant('pi', math.pi)
        self.global_symbol_table.set_constant('e', math.e)
        #: A dict containing known function signatures
        self.functionmap = {
            'distance': {"arglist":
                         [{"type": "number", "name": "start"}, {"type": "number", "name": "end"}],
                         'block': ["_start", "_end", "operator.sub", "operator.abs", "_return"]
                        },
            'randint': {"arglist":
                        [{"type": "number", "name": "max"}],
                        'block': [0, "_max", "random.randint", "_return"]
                       },
            'time': {"arglist": [],
                     'block': ["time.time", "_return"]
                    },
            'debug': {"argslist":
                      [{"type": "string", "name": "debug_str"}],
                      'block': []
                     }
        }
        #: Code blocks registered in the language engine
        self.code_blocks = {}
        #: Local symbol tables associated with each code block
        self.local_tables = {}

    def register_code_block(self, block_name, code_string):
        """
        Register a block of game language code with the language engine.

        The executable code block will be placed in the code block hash,
        using its name as the key.

        :param block_name: The name to register the code block with
        :type block_name: str
        :param code_string: The game language source code block
        :type code_string: str
        :raise: DuplicateCodeBlockError if the block name is already registered
        """
        self.info("Register handle '{}'".format(block_name))
        self.debug("  code block:\n{}".format(code_string))
        if block_name in list(self.code_blocks.keys()):
            raise DuplicateCodeBlockError
        module_context = imp.new_module('{}_module'.format(block_name))
        code_block_runnable = CodeBlockGenerator.wrap_code_block(
            block_name, module_context, code_string, self.functionmap)
        code_block_runnable.load(['operator', 'math'])
        self.code_blocks[block_name] = code_block_runnable

    def execute_code_block(self, block_name, local_symbol_table):
        """
        Supply the name of a registered code block that will be executed.

        Local and global symbols may be accessed and/or created during code
        execution.  Symbols changed or created in the local symbol table will
        trigger a symbol change callback associated with the symbol table.

        :param block_name: The name of a registered code block
        :type block_name: str
        :param local_symbol_table: The local symbols to make available to the
            code block
        :type local_symbol_table: :py:class:`SymbolTable`
        :raise: UnknownCodeBlockError if the block name is not found
        """
        self.debug("Execute code with handle '{}'".format(block_name))
        if block_name not in self.code_blocks:
            raise UnknownCodeBlockError
        if local_symbol_table:
            if block_name not in self.local_tables:
                self.local_tables[block_name] = {}
            self.local_tables[block_name].update(local_symbol_table)
        symtables = {'globals': self.global_symbol_table,
                     'locals': local_symbol_table}
        self.code_blocks[block_name].module_context.run(symtables)

    def unregister_code_block(self, block_name):
        """
        Remove a code block that is no longer needed.

        :param block_name: The name of a registered code block
        :type block_name: str
        """
        self.info("Unregister code block handle '{}'".format(block_name))
        if block_name in list(self.code_blocks.keys()):
            del self.code_blocks[block_name]


BNF = None


def bnf_interpret(code_block_obj):
    """
    See https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_Form

    * decimal_digit :: '0' .. '9'
    * lower_case    :: 'a' .. 'z'
    * upper_case    :: 'A' .. 'Z'
    * alpha         :: lower_case | upper_case
    * boolean_op    :: 'or' | 'and'
    * boolnot       :: 'not'
    * conditional_keyword   :: 'if' | 'elseif' | 'else'
    * identifier    :: alpha [ alpha | decimal_digit | '_' | '.' ]*
    * equalop :: '='
    * compareop :: '==' | '!=' | '<' | '>' | '>=' | '<='
    * expop   :: '^'
    * multop  :: '*' | '/'
    * addop   :: '+' | '-'
    * integer :: ['+' | '-'] '0'..'9'+
    * float   :: ['+' | '-'] '0'..'9'+ [ '.' '0' .. '9'+ ] [ 'e' | 'E' ['+' | '-'] '0' .. '9'+ ]
    * string  :: '"' [ alpha | decimal_digit | [`~!@#$%^&*()_=+;:',<.>/? -]* ] '"'
    * atom    :: identifier | PI | E | real |
                 fn '(' [ combinatorial [',' combinatorial ] ] ')' | '(' combinatorial ')'
    * factor  :: atom [ expop factor ]*
    * term    :: factor [ multop factor ]*
    * expr    :: term [ addop term ]*
    * combinatorial :: [boolnot] expr [ boolean_op [boolnot] expr ]*
    * function_def  :: 'function' identifier '('[ identifier ] [',' identifier]* ')' block
    * assignment    :: identifier equalop combinatorial
    * comparison    :: combinatorial compareop combinatorial
    * conditional   :: conditional_keyword '(' comparison ')' block
    * block         :: '{' assignment | conditional '}'

    :param code_block_obj: A code block object supplying parse methods
    :type code_block_obj: :py:class:`CodeBlock`
    """
    global BNF
    if not BNF:
        # point = Literal( "." )
        # ~ fnumber = Combine( Word( "+-"+nums, nums ) +
        # ~ Optional( point + Optional( Word( nums ) ) ) +
        # ~ Optional( e + Word( "+-"+nums, nums ) ) )
        fnumber = Regex(r"[+-]?\d+(:?\.\d*)?(:?[eE][+-]?\d+)?")
        ident = Word(alphas, alphas + nums + "._$")
        quote = Literal("\"")
        string = quote + Regex(r"[^\"]+") + quote

        uptolineend = Regex(r".*{}".format(os.linesep))
        comment_sym = Literal("#")
        plus = Literal("+")
        minus = Literal("-")
        mult = Literal("*")
        div = Literal("/")
        mod = Literal("%")
        lpar = Literal("(").suppress()
        rpar = Literal(")").suppress()
        lbrack = Literal("{").suppress()
        rbrack = Literal("}").suppress()
        glbl = Keyword("global")
        boolnot = Keyword("not")
        boolor = Keyword("or")
        booland = Keyword("and")
        ifcond = Keyword("if")
        elseifcond = Keyword("elseif")
        elsecond = Keyword("else")
        func = Keyword("function")
        num = Keyword("number")
        strn = Keyword("string")
        void = Keyword("void")
        ret = Keyword("return")
        is_equal = Keyword("==")
        is_nequal = Keyword("!=")
        is_lt = Keyword("<")
        is_lte = Keyword("<=")
        is_gt = Keyword(">")
        is_gte = Keyword(">=")
        assignop = Keyword("=")
        compareop = is_equal | is_nequal | is_lte | is_lt | is_gte | is_gt
        boolop = boolor | booland
        addop = plus | minus
        multop = mult | div | mod
        typestring = num | strn
        expop = Literal("^")

        comments = comment_sym + uptolineend
        combinatorial = Forward()
        expr = Forward()
        atom = ((0, None) * minus + (((ident + lpar + Optional(
            combinatorial + ZeroOrMore("," + combinatorial)) + rpar).setParseAction(
                code_block_obj.count_function_args) | fnumber | ident | string).setParseAction(
                    code_block_obj.push_atom) | Group(
                        lpar + combinatorial + rpar))).setParseAction(code_block_obj.push_u_minus)

        # by defining exponentiation as "atom [ ^ factor ]..." instead of
        # "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-right
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor <<= (atom + ZeroOrMore((expop + factor).setParseAction(code_block_obj.push_first)))
        term = (factor + ZeroOrMore((multop + factor).setParseAction(code_block_obj.push_first)))
        expr <<= (term + ZeroOrMore((addop + term).setParseAction(code_block_obj.push_first)))
        combinatorial <<= (Optional(boolnot) + expr + ZeroOrMore(
            ((boolop | compareop) + Optional(boolnot) + expr).setParseAction(
                code_block_obj.push_first)))
        returnline = Group(ret + combinatorial).setParseAction(code_block_obj.push_return)
        assignment = Group(
            Optional(glbl) + ident + assignop + combinatorial | string).setParseAction(
                code_block_obj.push_assignment)
        # comparison = Forward()
        # comparison <<= Group(combinatorial + ZeroOrMore(compareop + comparison).setParseAction(
        #     code_block_obj.push_first) ).setParseAction(code_block_obj.push_comparison)
        block = Forward()
        conditional_start = (
            ifcond.setParseAction(code_block_obj.push_if_cond) + Group(
                lpar + combinatorial + rpar).setParseAction(
                    code_block_obj.push_comparison) + block.setParseAction(
                        code_block_obj.push_conditional_block))
        conditional_continue = (
            elseifcond.setParseAction(code_block_obj.push_if_cond) + Group(
                lpar + combinatorial + rpar).setParseAction(
                    code_block_obj.push_comparison) + block.setParseAction(
                        code_block_obj.push_conditional_block))
        conditional_else = (elsecond.setParseAction(
            code_block_obj.push_if_cond) + block.setParseAction(
                code_block_obj.push_conditional_block))
        conditional_set = Group(conditional_start + ZeroOrMore(
            conditional_continue) + Optional(conditional_else))
        block <<= Group(lbrack + ZeroOrMore(
            comments.suppress() | assignment | conditional_set) + rbrack)
        func_def_args = Group(
            ident + lpar + ((typestring + ident + ZeroOrMore(
                "," + typestring + ident)) | void) + rpar).setParseAction(
                    code_block_obj.push_func_args)
        function_block = Group(lbrack + ZeroOrMore(
            comments.suppress() | assignment | conditional_set |
            returnline) + rbrack).setParseAction(code_block_obj.push_func_block)
        func_def = Group(func + func_def_args + function_block)
        BNF = OneOrMore(comments.suppress() | func_def | assignment | conditional_set) + stringEnd
    return BNF
