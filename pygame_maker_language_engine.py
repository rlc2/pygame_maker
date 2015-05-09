#!/usr/bin/python -W all

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# Adapted from the fourFn.py example that ships with PyParser
# original code copyright 2003-2009 by Paul McGuire

# handles math operations, predefined functions, keywords, boolean comparisons,
#  function definitions, setting and using any supplied global variables,
#  if/elseif/else conditionals, comments
# represent toy language source code with python classes

from pyparsing import Literal,CaselessLiteral,Word,Group,Optional,\
    ZeroOrMore,OneOrMore,Forward,nums,alphas,Regex,ParseException,Keyword,\
    Dict,stringEnd,ParseFatalException
import numbers
import math
import random
import time
import operator
import infix_to_postfix
import os
import re
import imp
import sys
import pygame_maker_run_time_support as pgmrts

class PyGameMakerLanguageEngineException(Exception):
    pass

class PyGameMakerCodeBlockException(Exception):
    pass

class PyGameMakerSymbolTable(object):
    DEFAULT_UNINITIALIZED_VALUE = -sys.maxint - 1

    def __init__(self, initial_symbols={}):
        self._vars = {}
        self._consts = {}
        self._consts.update(initial_symbols)

    def dumpVars(self):
        constlist = list(self._consts.keys())
        constlist.sort()
        print("constants:")
        for const in constlist:
            print("{} = {}".format(const, self._consts[const]))
        varlist = list(self._vars.keys())
        varlist.sort()
        print("variables:")
        for var in varlist:
            print("{} = {}".format(var, self._vars[var]))

    def __setitem__(self, item, val):
        #print("Setting {} to {}".format(item, val))
        # don't allow constants to be written this way
        if not item in self._consts:
            self._vars[item] = val

    def __getitem__(self, item):
        new_val = self.DEFAULT_UNINITIALIZED_VALUE
        if item in self._consts:
            new_val = self._consts[item]
        elif item in self._vars:
            new_val = self._vars[item]
        #print("Retrieve item {}: {}".format(item, new_val))
        return new_val

    def setConstant(self, constant_name, constant_value):
        """
            setConstant():
            Called from within the game engine to set values that can be
             read from, but not written to, by user code
        """
        self._consts[constant_name] = constant_value

class PyGameMakerCodeBlock(object):
    """
        PyGameMakerCodeBlock class:
        Helper class that is created by the PyGameMakerCodeBlockGenerator
        class method, that collects the infix form of source code in the C-like
        language supported by the language engine and converts it to a more
        readily executable postfix form. Because of the generator's constraints
        (the pyparsing function re-uses the same object for every parsing run),
        this class supports deep copying. Optionally, the abstract syntax tree
        (AST) can be stored within the object.
    """
    OPERATOR_FUNCTIONS={
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
    OPERATOR_REPLACEMENTS={
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
    CONDITIONALS=[
        "operator.lt",
        "operator.le",
        "operator.gt",
        "operator.ge",
        "operator.eq",
        "operator.ne"
    ]
    REVERSE_OPERATORS={
        "operator.add":     "+",
        "operator.sub":     "-",
        "operator.mul":     "*",
        "operator.truediv": "/",
        "operator.mod":     "%",
        "operator.lt":      "<",
        "operator.le":     "<=",
        "operator.gt":      ">",
        "operator.ge":     ">=",
        "operator.eq":      "==",
        "operator.ne":      "!=",
        "math.pow":         "**"
    }
    SYMBOL_RE=re.compile("_[a-zA-Z][a-zA-Z0-9._]*$")
    RETURN_RE=re.compile("  return ")

    def __init__(self, name, module_context, funcmap={}, astree=None):
        """
            __init__():
            name: The name assigned to this code block
            module_context: A new module for the Python blocks to be loaded into
            optional args:
             funcmap: A dict with <function_name>: [arg_type1, .., arg_typeN]
              entries, representing the external function table made available
              to the code block. Void argument lists can be represented with an
              empty list. The number and type of arguments supplied assist with
              syntax checking.
             astree: the abstract syntax tree produced by pyparsing
        """
        self.name = name
        self.module_context = module_context
        self.outer_block = []
        self.inner_blocks = []
        self.stack = self.outer_block
        self.frame = self.outer_block
        self.scratch = []
        self.inner_block_count = 0
        self.func_name = None
        self.functionmap = dict(funcmap)
        self.astree = astree

    def addToFuncMap(self, func_map):
        """
            addToFuncMap()
            Supply a dict for <function_name>: [arg_type1, .., arg_typeN]
             entries. This helps the syntax check phase know how many args
             to expect. Later, the arg type list can be checked to make sure
             that supplied argument types match the function call signature.
        """
        self.functionmap.update(func_map)

    def pushAssignment(self, parsestr, loc, toks):
        """
            pushAssignment():
            When the parser finds a assignment match, the assignee and '='
             operator need to be added here, since the parser won't add these
             itself. Push these and the right-hand side of the assignment
             (which were already collected in self.scratch) onto the current
             stack. '=' will always go at the end.
        """
        assign_list = []
        for assign_tok in toks.asList():
            for inner_item in assign_tok:
                if inner_item == '=':
                    break
                assign_list.append("_{}".format(inner_item))
            break
        #print("assignment scratch: {}".format(self.scratch))
        self.stack.append(assign_list + list(self.scratch) + ['='])
        #print("assignment: {}".format(self.stack[-1]))
        self.scratch = []

    def pushConditionalBlock(self, parsestr, loc, toks):
        """
            pushConditionalBlock():
            When the parser matches a conditional's block, it's time to close
             it (the instructions were already collected on the current stack).
             Keep track here of the block level decrement, either from a child
             inner-node up to its parent, or the top-most inner block up to the
             outer block. Push a copy of the child inner node onto its parent's
             stack. This method changes the stack reference.
        """
        #print("push block")
        if (self.inner_block_count > 1):
            #print("inner block #{}\n{}".format(self.inner_block_count-1,self.stack))
            self.inner_block_count -= 1
            #print("append to {}".format(self.inner_blocks[self.inner_block_count-1]))
            self.inner_blocks[self.inner_block_count-1].append(list(self.stack))
            #print("stack now points to inner block #{}".format(self.inner_block_count-1))
            self.stack = self.inner_blocks[self.inner_block_count-1]
            #print("clear inner_blocks[{}]".format(self.inner_block_count))
            del(self.inner_blocks[self.inner_block_count])
        else:
            #print("inner block #0\n{}".format(self.stack))
            self.frame.append(list(self.stack))
            #print("clear inner_blocks[0]")
            self.inner_block_count = 0
            del(self.inner_blocks[0])
            self.stack = self.frame
            #print("stack now points to outer block")

    def pushIfCond(self, parsestr, loc, toks):
        """
            pushIfCond():
            When the parser matches if/elseif/else keywords, anticipate that
             a new block will be added. Increment the block level -- either
             outer block to topmost inner block, or parent inner block to
             child inner block. This is optimistic, since the parser might
             not recognize the pattern following the keyword, but that signals
             a syntax error, at which point the stack level will be moot.
             Collect the keyword name and push it onto the parent's stack.
             This method changes the stack reference.
        """
        #print("push {}".format(toks.asList()))
        if_statement = ""
        for tok in toks:
            if_statement = "_{}".format(tok)
            #print("push if statement: {}".format(if_statement))
            break
        container_block = self.frame
        if (self.inner_block_count > 0):
            container_block = self.inner_blocks[-1]
            #print("container: inner block {}\n{}".format(self.inner_block_count-1,self.inner_blocks[self.inner_block_count-1]))
        else:
            #print("container: outer block")
            pass
        container_block.append(if_statement)
        #print("outer block is now:\n{}".format(self.outer_block))
        self.inner_block_count += 1
        self.inner_blocks.append([])
        #print("stack now points at inner block {}".format(self.inner_block_count-1))
        self.stack = self.inner_blocks[-1]

    def pushComparison(self, parsestr, loc, toks):
        """
            pushComparison():
            When the parser matches a comparison, push it onto the current
             stack.
        """
        #print("append {} to stack".format(self.scratch))
        self.stack.append(list(self.scratch))
        self.scratch = []

    def countFunctionArgs(self, parsestr, loc, toks):
        """
            countFunctionArgs():
            This is where the parser needs help, since it has no idea how many
             args a function expects. The external function table in
             functionmap is checked against the supplied function name to
             determine its argument count. Unfortunately, in the case where
             function results are placed directly into function args, the
             whole mess appears in the toks list. The saving grace is that
             functions are checked from inner -> outer, so it's possible to
             skip over later toks containing function names, assuming that
             their argument lists will be checked separately. This still
             implies that the other functions in the list need to be checked
             to find out how many args will be skipped (and even then, it's
             only important for functions that have more than 1 arg, since
             the arg count is based on how many ','s are found).
             TODO: Argument type-checking. Assume this is as simple as number
              vs. string, and strings aren't supported yet.
        """
        #print("function w/ args: {}".format(toks))
        # assume embedded function calls have been validated, just skip
        #  them to count the args in the outer function call
        func_call = False
        func_name = ""
        skip_count = 0
        arg_count = 0
        tok_idx = 0
        for tok in toks:
            if (tok_idx == 0):
                if tok in self.functionmap:
                    func_call = True
                    func_name = str(tok)
                    tok_idx += 1
                    continue
                else:
                    # unknown function encountered
                    raise(ParseFatalException(parsestr, loc=loc, msg="Unknown function call '{}'".format(tok)))
                    break
            if func_call:
                if arg_count == 0:
                    arg_count = 1
                # if this function takes no arguments, we shouldn't be here..
                #print("check {} call vs map {}".format(tok, self.functionmap))
                if len(self.functionmap[func_name]["arglist"]) == 0:
                    raise(ParseFatalException(parsestr, loc=loc, msg="Too many arguments to function \"{}\"".format(func_name)))
                # check whether an embedded function call should be skipped
                #print("checking {}..".format(tok))
                if tok in self.functionmap:
                    skips = len(self.functionmap[tok]["arglist"])
                    if skips > 0:
                        skips -= 1 # future commas imply > 1 arg to skip
                    skip_count += skips
                    #print("skip call to {} with {} args".format(tok, len(self.functionmap[tok])))
                    #print("skip count now is: {}".format(skip_count))
                if tok == ',':
                    if skip_count > 0:
                        skip_count -= 1
                        #print("Found ',' and decrease skip count to {}".format(skip_count))
                    else:
                        arg_count += 1
                        #print("Found ',' and increase arg count to {}".format(arg_count))
            tok_idx += 1

        if func_call:
            if arg_count < len(self.functionmap[func_name]["arglist"]):
                raise(ParseFatalException(parsestr, loc=loc, msg="Too few arguments to function \"{}\"".format(func_name)))
            elif arg_count > len(self.functionmap[func_name]["arglist"]):
                raise(ParseFatalException(parsestr, loc=loc, msg="Too many arguments to function \"{}\"".format(func_name)))

    def pushFuncArgs(self, parsestr, loc, toks):
        """
            pushFuncArgs():
            Collect the function name and arguments from a function definition.
            Validate the argument types. Create a new block within the
            functionmap and point the frame at it, so future constructs will be
            placed in the function.
        """
        func_name = None
        arg_with_type = None
        arg_list = []
        for tok in toks:
            for item in tok:
                if item == ',':
                    continue
                if not func_name:
                    func_name = str(item)
                    #print("New function: {}".format(func_name))
                    if func_name in self.functionmap:
                        raise(ParseFatalException(parsestr, loc=loc, msg="Redefinition of existing function '{}'".format(func_name)))
                    continue
                if func_name:
                    if not arg_with_type:
                        typename = str(item)
                        if not typename in ["void", "number", "string"]:
                            raise(ParseFatalException(parsestr, loc=loc, msg="Missing type name in declaration of function '{}'".format(func_name)))
                        arg_with_type = {"type": typename }
                        if typename == "void":
                            arg_list.append(dict(arg_with_type))
                    else:
                        if arg_with_type["type"] == "void":
                            raise(ParseFatalException(parsestr, loc=loc, msg="Extraneous token following void in declaration of function '{}'".format(func_name)))
                        arg_with_type["name"] = str(item)
                        arg_list.append(dict(arg_with_type))
                        arg_with_type = None
        #print("Function w/ args: {} {}".format(func_name, arg_list))
        if arg_list[0]["type"] != "void":
            self.functionmap[func_name] = { "arglist": arg_list }
        else:
            self.functionmap[func_name] = { "arglist":[] }
        self.functionmap[func_name]["block"] = []
        #print("New functionmap: {}".format(self.functionmap))
        self.stack = self.functionmap[func_name]["block"]
        self.frame = self.functionmap[func_name]["block"]
        self.function_name = func_name

    def pushFuncBlock(self, parsestr, loc, toks):
        """
            Take the current function block frame and reduce it, before
            switching the frame back to the outer_block.
        """
        # reduce the function source
        self.reduceBlock(self.frame)
        func_loc = [0,0]
        param_list = [ fparam["name"] for fparam in self.functionmap[self.function_name]["arglist"]]
        function_body = self.toPythonBlock(self.frame, func_loc,
            self.function_name)
        param_list.append("count=0")
        func_lines = ["def userfunc_{}(_symbols, {}):".format(self.function_name, ",".join(param_list))]
        func_lines += [
            "  if (count > 100):",
            "    raise(PyGameMakerCodeBlockRuntimeError(\"{}: Call stack depth limit exceeded\"))".format(self.function_name)
        ]
        func_lines += function_body
        ret_minfo = self.RETURN_RE.match(func_lines[-1])
        if not ret_minfo:
            # force all functions to return a value. if the final line is
            #  not a return, return the "uninitialized" value
            func_lines.append("  return {}".format(-sys.maxint - 1))
        function_code = "\n".join(func_lines)
        print("Function code:\n{}".format(function_code))
        self.functionmap[self.function_name]['compiled'] = compile(function_code,
            "<c_{}>".format(self.function_name), 'exec')
        self.function_name = "None"
        # reset the stack and frame
        self.stack = self.outer_block
        self.frame = self.outer_block

    def pushAtom(self, parsestr, loc, toks):
        """
            pushAtom():
            When the parser finds an "atom": PI, e, a number, a function call,
            a '(' ')' delimited expression, or bare identifier, it will be
            pushed onto scratch. A copy of the scratch list is later pushed
            onto the current stack reference when a grouping is found
            (an assignment or conditional block).
        """
        tok_n = 0
        add_not = False
        add_tok = None
        for tok in toks:
            if (tok_n == 0):
                if (tok == 'not'):
                    add_not = True
                    tok_n += 1
                    continue
                else:
                    add_tok = tok
                    break
            else:
                add_tok = tok
                break
        func_call = False
        if add_tok in self.functionmap:
                func_call = True
        #print("atom: {}".format(toks.asList()))
        if func_call:
            self.scratch += infix_to_postfix.convert_infix_to_postfix([add_tok],
                self.OPERATOR_REPLACEMENTS)
            if add_not:
                self.scratch.append("operator.not_")
        else:
            if add_not:
                print("not tokens:".format(toks.asList()))
            self.scratch += infix_to_postfix.convert_infix_to_postfix(toks.asList(),
                self.OPERATOR_REPLACEMENTS)
        #print("scratch is now: {}".format(self.scratch))

    def pushFirst(self, parsestr, loc, toks):
        """
            pushFirst():
            When the parser finds an operator ('^', '*', "/", "%", "+", "-",
            "<", "<=", ">", ">=", "==", "!="), this is called to place it onto
            scratch, using the converter to rename it to an actual python
            method.
        """
        #print("pre-op: {}".format(toks.asList()))
        self.scratch += infix_to_postfix.convert_infix_to_postfix(toks[0],
            self.OPERATOR_REPLACEMENTS)
        #print("op + scratch is now: {}".format(self.scratch))

    def pushUMinus(self, parsestr, loc, toks):
        """
            pushUMinus():
            From the original fourFn.py demo. Push 'unary -' to keep track
             of any terms that have been negated.
        """
        for t in toks:
            if t == '-': 
                self.scratch.append( 'unary -' )
            else:
                break

    def pushReturn(self, parsestr, loc, toks):
        """
            pushReturn()
            Push the stack containing the arguments for a return keyword,
            followed by "_return"
        """
        self.stack.append(list(self.scratch) + ["_return"])
        self.scratch = []

    def reduceLine(self, code_line):
        """
            reduceLine():
            Iterate over a list containing an expression, pre-calculating
             simple numeric operations and replacing the operands and operator
             with the result. Repeat until no more changes are made.
        """
        marker_list = []
        changed_line = True
        while (changed_line):
            line_idx = 0
            changed_line = False
            result_type = int
            while line_idx < len(code_line):
                check_op = "{}".format(code_line[line_idx])
                #print("check op: {}".format(check_op))
                if check_op in self.OPERATOR_FUNCTIONS:
                    #print("found op: {}".format(check_op))
                    op_len = len(self.OPERATOR_FUNCTIONS[check_op])
                    if line_idx >= op_len:
                        all_numbers = True
                        for rev in range(line_idx-op_len, line_idx):
                            rev_item = code_line[rev]
                            #print("check if num: {}".format(rev_item))
                            if not isinstance(rev_item, numbers.Number):
                                all_numbers = False
                                break
                        if all_numbers:
                            op_result = self.executeOperation(check_op, code_line[line_idx-op_len:line_idx])
                            code_line[line_idx-op_len] = op_result
                            for dead_idx in range(op_len):
                                del code_line[line_idx-op_len+1]
                            changed_line = True
                            break
                elif check_op == "unary -":
                    # the special case
                    if (line_idx > 0):
                        if (isinstance(code_line[line_idx-1], numbers.Number)):
                            code_line[line_idx-1] = -1 * code_line[line_idx-1]
                            del code_line[line_idx]
                            changed_line = True
                            break
                line_idx += 1

    def reduceBlock(self, block):
        """
            reduceBlock():
            Iterate through each line within the given block of postfix
            expressions and recursively through sub-blocks, reducing numeric
            operations when found.
        """
        block_idx = 0
        while block_idx < len(block):
            code_line = block[block_idx]
            if (isinstance(code_line, str) and
                code_line in ['_if', '_elseif', '_else']):
                # handle the conditional block here, it's a list inside a list
                self.reduceBlock(block[block_idx+1])
                block_idx += 2
                continue
            if isinstance(code_line, list):
                #print("Reduce line: {}".format(code_line))
                self.reduceLine(code_line)
            block_idx += 1

    def reduce(self):
        """
            reduce():
            Perform as much argument reduction as possible. Operations on
            numeric values can be replaced with the results.
        """
        self.reduceBlock(self.outer_block)

    def toPythonLine(self, code_line, loc=[0,0], func_name=None):
        """
            toPythonLine():
            The hard work of arranging the postfix representation of a line of
            code into a line of executable Python code happens here. The
            round-trip serves 2 purposes: the game language is essentially
            used for calculations, so doesn't need the full features of Python;
            and this effectively isolates and sanitizes user-written code to
            prevent it from adversely affecting the game engine.
        """
        op_stack = []
        current_value = 0
        symbol = None
        start_pos = 0
        type_upgrade = False
        if code_line[-1] == '=':
            symbol = code_line[0][1:]
            start_pos = 1
        for op_idx in range(start_pos,len(code_line)):
            op = code_line[op_idx]
            if isinstance(op, int):
                op_stack.append({"type": "int", "val": str(op)})
            elif isinstance(op, float):
                op_stack.append({"type": "float", "val": str(op)})
            else:
                sym_minfo = self.SYMBOL_RE.match(op)
                if sym_minfo:
                    opname = op[1:]
                else:
                    opname = op
                if (opname in self.OPERATOR_FUNCTIONS or
                    opname in self.functionmap):
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
                        raise(PyGameMakerCodeBlockException("Stack underflow at line {} when assembling the line:\n{}".format(loc[0], code_line)))
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
                    for dead_idx in range(arg_count):
                        del(op_stack[-1])
                    param_list = func_params + [param['val'] for param in params]
                    if func_name and not (opcall in self.OPERATOR_FUNCTIONS):
                        # if calling a function within a function block, append
                        #  a count+1 arg to limit recursion depth (this is to
                        #  prevent user code from crashing the game engine)
                        param_list.append("count+1")
                    op_stack.append({"type": res_type, "val": "{}({})".format(opcall,",".join(param_list))})
                    if type_upgrade:
                        prev_val = op_stack[-1]["val"]
                        prev_val = "{}({})".format(res_type,prev_val)
                elif opname == "unary -":
                    # the special case
                    if len(op_stack) > 0:
                        last_op_val = op_stack[-1]["val"]
                        last_op_type = op_stack[-1]["type"]
                        if (last_op_type in ["int", "float"]):
                            op_stack.insert(-1, {"type": last_op_type, "val": "operator.mul(-1, {})".format(last_op_val)})
                            del op_stack[-1]
                elif opname in ["and", "or"]:
                    id_start = len(op_stack) - 2
                    id_end = len(op_stack)
                    if id_start < 0:
                        raise(PyGameMakerCodeBlockException("Stack underflow at line {} when assembling the line:\n{}".format(loc[0], code_line)))
                    params = list(op_stack[id_start:id_end])
                    for dead_idx in range(2):
                        del(op_stack[-1])
                    op_stack.append({"type": "bool", "val": "(({}) {} ({}))".format(params[0]['val'], opname, params[1]['val'])})
                elif opname == '=':
                    # '=' must always be the last token for an assignment.
                    #  Time to store the value in the symbol table
                    last_op_val = op_stack[-1]["val"]
                    last_op_val = "_symbols['{}'] = {}".format(symbol, last_op_val)
                    op_stack[-1]['val'] = last_op_val
                    break
                elif opname == 'return':
                    last_op_val = op_stack[-1]["val"]
                    last_op_val = "return {}".format(last_op_val)
                    op_stack[-1]['val'] = last_op_val
                    break
                else:
                    func_arg = False
                    if func_name:
                        func_arg_names = [narg["name"] for narg in self.functionmap[func_name]["arglist"]]
                        if opname in func_arg_names:
                            func_arg = True
                    if not func_arg:
                        op_stack.append({"type": "int",
                            "val": "_symbols['{}']".format(opname)})
                    else:
                        op_stack.append({"type": "int",
                            "val": "{}".format(opname)})
            #print("New op_stack: {}".format(op_stack))
        if len(op_stack) > 1:
            raise(PyGameMakerCodeBlockException("Stack overflow at line {} when assembling the line:\n{}".format(loc[0], code_line)))
        # apply the (possibly upgraded) result type to the remaining item
        #print("Result of {}: {}".format(code_line, op_stack))
        python_code_line = "{}{}".format(' '*loc[1], op_stack[-1]['val'])
        loc[0] += 1
        return python_code_line

    def toPythonBlock(self, block, loc=[0,0], func_name=None):
        """
            toPythonBlock():
            When supplied a block of code objects, produce the Python
            representations for contained conditionals and assignments using
            appropriate indentation.
        """
        python_code_lines=[]
        loc[1] += 2
        #print("block start: col is now: {}".format(loc[1]))
        py_code = ""
        block_idx = 0
        while block_idx < len(block):
            code_line = block[block_idx]
            if code_line in ["_if", "_elseif", "_else"]:
                cond_name = code_line[1:]
                python_code_lines += self.toPythonConditional(cond_name,
                    block[block_idx+1], loc, func_name)
                block_idx += 2
                continue
            else:
                python_code_lines.append(self.toPythonLine(code_line, loc, func_name))
                block_idx += 1
        loc[1] -= 2
        #print("block end: col is now: {}".format(loc[1]))
        return python_code_lines

    def toPythonConditional(self, conditional_name, block, loc=[0,0], func_name=None):
        """
            toPythonConditional():
            When a conditional is found in a code block, produce an executable
            line of Python containing the condition name, possibly followed
            by a condition (e.g. if, elseif), then a list of all the lines
            (and/or other conditionals) within its code block.
        """
        python_code_lines=[]
        #print("{} {{{}}} to python".format(conditional_name, block))
        conditional_code = self.toPythonLine(block[0], [loc[0],0], func_name)
        py_cond_name = str(conditional_name)
        block_start_idx = 1
        if conditional_name == "elseif":
            py_cond_name = "elif"
        if py_cond_name in ["if", "elif"]:
            python_code_lines.append("{}{} ({}):".format(' '*loc[1],
                py_cond_name, conditional_code))
        else:
            python_code_lines.append("{}{}:".format(' '*loc[1],
                py_cond_name))
            block_start_idx = 0
        python_code_lines += self.toPythonBlock(block[block_start_idx:], loc,
            func_name)
        return python_code_lines

    def toPython(self):
        """
            toPython():
            Convert the postfix code representation into executable Python
            code, then compile it.
        """
        code_loc = [0, 0]
        python_code = ""
        # the code block has to have SOMETHING in it, but if it only contains
        #  function definitions, don't construct the run() method
        if len(self.outer_block) > 0:
            python_lines = ["def run(_symbols):".format(self.name)]
            python_lines += self.toPythonBlock(self.outer_block, code_loc)
            python_code = "\n".join(python_lines)
            #print("Python code:\n{}".format("\n".join(python_lines)))
        return python_code

    def executeOperation(self, op_name, args):
        """
            executeOperation():
            Given a valid Python operation and a list containing its args,
            convert them into a string and eval() it.
        """
        eval_str = ""
        res = None
        stargs = [str(a) for a in args]
        result_type = int
        for a in args:
            if not isinstance(a, int):
                result_type = type(a)
        if op_name in self.OPERATOR_FUNCTIONS:
            #print("eval {} {}".format(op_name, stargs))
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
            load():
            Place all functions and executable code into the module's __dict__
        """
        for userfunc in self.functionmap:
            #print("exec {}".format(userfunc))
            if 'compiled' in self.functionmap[userfunc]:
                exec self.functionmap[userfunc]['compiled'] in self.module_context.__dict__
        import_lines = "from pygame_maker_run_time_support import *\n"
        if import_list:
            import_lines += "import {}\n".format(",".join(import_list))
        exec_code = self.toPython()
        if len(exec_code) > 0:
            pyth_code = import_lines + self.toPython()
            print("Run program:\n{}".format(pyth_code))
            exec pyth_code in self.module_context.__dict__

    def run(self, sym_table):
        """
            run():
            Execute the code block.
        """
        if "run" in self.module_context.__dict__:
            self.module_context.run(sym_table)

    def copyTo(self, other):
        """
            copyTo():
            Perform a deep copy to another code block object.
        """
        #other.stack = list(self.stack)
        #other.frame = list(self.frame)
        #other.scratch = list(self.scratch)
        #other.inner_blocks = list(self.inner_blocks)
        other.outer_block = list(self.outer_block)
        #print("Copied outer block:\n{}".format(other.outer_block))
        if self.astree:
            other.astree = list(self.astree)
        other.addToFuncMap(self.functionmap)

    def clear(self):
        """
            clear():
            Clear out all lists in preparation for a new parsing operation.
        """
        self.name = ""
        self.scratch = []
        self.inner_blocks = []
        self.inner_block_count = 0
        self.outer_block = []
        self.frame = self.outer_block
        self.stack = self.outer_block
        self.func_name = None
        self.functionmap = {}
        self.astree = None

class PyGameMakerCodeBlockGenerator(object):
    """
        PyGameMakerCodeBlockGenerator class:
        Generate a PyGameMakerCodeBlock using the wrap_code_block() class
         method upon a supplied source code string. A class member holds
         a code block object that is copied to a new code object, which is
         returned to the caller.
        args:
         source_code_str: A string containing C-like source code
         funcmap: A dict containing <function_name>: [arg_type1, .., arg_typeN]
          mappings, which will be supplied to the code block's external
          function table so it knows type and number of args for function call
          prototypes.
    """
    bnf = None
    code_block = PyGameMakerCodeBlock("none", None)
    @classmethod
    def wrap_code_block(cls, program_name, module_context, source_code_str, funcmap=[]):
        if module_context:
            cls.code_block.module_context = module_context
        if len(funcmap) > 0:
            cls.code_block.addToFuncMap(funcmap)
        cls.bnf = BNF(cls.code_block)
        try:
            astree = cls.bnf.parseString(source_code_str)
        except ParseException as exc:
            cls.code_block.clear()
            raise exc
        except ParseFatalException as exc:
            cls.code_block.clear()
            raise exc
        cls.code_block.reduce()
        new_block = PyGameMakerCodeBlock(program_name, module_context, funcmap,
            astree)
        cls.code_block.copyTo(new_block)
        cls.code_block.clear()
        return new_block

class PyGameMakerLanguageEngine(object):
    """
        PyGameMakerLanguageEngine class:
        Execute code blocks. Requires managing tables of variables and
        functions that can be accessed by and/or created within the code block.
    """
    def __init__(self):
        self.symbol_table = PyGameMakerSymbolTable()
        self.symbol_table.setConstant('pi', math.pi)
        self.symbol_table.setConstant('e', math.e)
        self.function_table = {}
        self.functionmap = {
            'distance': { "arglist":
            [{"type": "number", "name":"start"},{"type":"number", "name":"end"}],
            'block': ["_start", "_end", "operator.sub", "operator.abs", "_return"]
            },
            'randint': { "arglist":
            [{"type":"number", "name":"max"}],
            'block': [0, "_max", "random.randint", "_return"]
            },
            'time': { "arglist": [],
            'block': ["time.time", "_return"]
            }
        }
        self.code_blocks = {}

    def register_code_block(self, block_name, code_string):
        """
            register_code_block():
            Supply <code_string>, containing the source code in a single string.
            The executable code block will be placed in the code block hash,
             using its name as the key.
        """
        code_block_runnable = None
        code_block_id = -1
        if block_name in self.code_blocks:
            raise(PyGameMakerLanguageEngineException("Attempt to register another code block named '{}'".format(block_name)))
        module_context = imp.new_module('{}_module'.format(block_name))
        code_block_runnable = PyGameMakerCodeBlockGenerator.wrap_code_block(
            block_name, module_context, code_string, self.functionmap)
        code_block_runnable.load(['operator', 'math'])
        self.code_blocks[block_name] = code_block_runnable

    def execute_code_block(self, block_name):
        """
            execute_code_block():
            Supply the name of a registered code block that will be executed.
        """
        if not block_name in self.code_blocks:
            raise(PyGameMakerLanguageEngineException("Attempt to execute unknown code block named '{}'".format(block_name)))
        self.code_blocks[block_name].module_context.run(self.symbol_table)

bnf = None
def BNF(code_block_obj):
    """
    decimal_digit :: '0' .. '9'
    lower_case    :: 'a' .. 'z'
    upper_case    :: 'A' .. 'Z'
    boolean_op    :: 'or' | 'and'
    boolnot       :: 'not'
    conditional_keyword   :: 'if' | 'elseif' | 'else'
    identifier    :: lower_case | upper_case [ lower_case | upper_case | decimal_digit | '_' | '.' ]*
    equalop :: '='
    compareop :: '==' | '!=' | '<' | '>' | '>=' | '<='
    expop   :: '^'
    multop  :: '*' | '/'
    addop   :: '+' | '-'
    integer :: ['+' | '-'] '0'..'9'+
    atom    :: identifier | PI | E | real | fn '(' [ combinatorial [',' combinatorial ] ] ')' | '(' combinatorial ')'
    factor  :: atom [ expop factor ]*
    term    :: factor [ multop factor ]*
    expr    :: term [ addop term ]*
    combinatorial :: [boolnot] expr [ boolean_op [boolnot] expr ]*
    function_def  :: 'function' identifier '('[ identifier ] [',' identifier]* ')' block
    assignment    :: identifier equalop combinatorial
    comparison    :: combinatorial compareop combinatorial
    conditional   :: conditional_keyword '(' comparison ')' block
    block         :: '{' assignment | conditional '}'
    """
    global bnf
    if not bnf:
        point = Literal( "." )
        #~ fnumber = Combine( Word( "+-"+nums, nums ) + 
                           #~ Optional( point + Optional( Word( nums ) ) ) +
                           #~ Optional( e + Word( "+-"+nums, nums ) ) )
        fnumber = Regex(r"[+-]?\d+(:?\.\d*)?(:?[eE][+-]?\d+)?")
        ident = Word(alphas, alphas+nums+"._$")
     
        uptolineend = Regex(r".*{}".format(os.linesep))
        comment_sym = Literal( "#" )
        plus  = Literal( "+" )
        minus = Literal( "-" )
        mult  = Literal( "*" )
        div   = Literal( "/" )
        lpar  = Literal( "(" ).suppress()
        rpar  = Literal( ")" ).suppress()
        lbrack = Literal( "{" ).suppress()
        rbrack = Literal( "}" ).suppress()
        boolnot = Keyword( "not" )
        boolor = Keyword( "or" )
        booland = Keyword( "and" )
        ifcond = Keyword( "if" )
        elseifcond = Keyword( "elseif" )
        elsecond = Keyword( "else" )
        func = Keyword( "function" )
        num = Keyword( "number" )
        strn = Keyword( "string" )
        void = Keyword( "void" )
        ret = Keyword( "return" )
        is_equal = Keyword( "==" )
        is_nequal = Keyword( "!=" )
        is_lt = Keyword( "<" )
        is_lte = Keyword( "<=" )
        is_gt = Keyword( ">" )
        is_gte = Keyword( ">=" )
        assignop = Keyword( "=" )
        compareop = is_equal | is_nequal | is_lte | is_lt | is_gte | is_gt
        boolop = boolor | booland
        addop  = plus | minus
        multop = mult | div
        typestring = num | strn
        expop = Literal( "^" )

        comments = comment_sym + uptolineend
        combinatorial = Forward()
        expr = Forward()
        atom = ((0,None)*minus + ( ( ( ident + lpar + Optional( combinatorial + ZeroOrMore( "," + combinatorial ) ) + rpar ).setParseAction(code_block_obj.countFunctionArgs) | fnumber | ident ).setParseAction(code_block_obj.pushAtom) | 
                Group( lpar + combinatorial + rpar ))).setParseAction(code_block_obj.pushUMinus)
        
        # by defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-righ
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor <<= ( atom + ZeroOrMore( ( expop + factor ).setParseAction(code_block_obj.pushFirst) ) )
        term = ( factor + ZeroOrMore( ( multop + factor ).setParseAction(code_block_obj.pushFirst) ) )
        expr <<= ( term + ZeroOrMore( ( addop + term ).setParseAction(code_block_obj.pushFirst) ) )
        combinatorial <<= ( Optional( boolnot ) + expr + ZeroOrMore( ( ( boolop | compareop ) + Optional( boolnot ) + expr ).setParseAction(code_block_obj.pushFirst) ) )
        returnline = Group( ret + combinatorial ).setParseAction(code_block_obj.pushReturn)
        assignment = Group( ident + assignop + combinatorial ).setParseAction(code_block_obj.pushAssignment)
#        comparison = Forward()
#        comparison <<= Group( combinatorial + ZeroOrMore( compareop + comparison ).setParseAction(code_block_obj.pushFirst) ).setParseAction(code_block_obj.pushComparison)
        block = Forward()
        conditional_start = ( ifcond.setParseAction(code_block_obj.pushIfCond) + Group( lpar + combinatorial + rpar ).setParseAction(code_block_obj.pushComparison) + block.setParseAction(code_block_obj.pushConditionalBlock) )
        conditional_continue = ( elseifcond.setParseAction(code_block_obj.pushIfCond) + Group( lpar + combinatorial + rpar ).setParseAction(code_block_obj.pushComparison) + block.setParseAction(code_block_obj.pushConditionalBlock) )
        conditional_else = ( elsecond.setParseAction(code_block_obj.pushIfCond) + block.setParseAction(code_block_obj.pushConditionalBlock) )
        conditional_set = Group( conditional_start + ZeroOrMore( conditional_continue ) + Optional( conditional_else ) )
        block <<= Group( lbrack + ZeroOrMore( comments.suppress() | assignment | conditional_set ) + rbrack )
        func_def_args = Group( ident + lpar + ( ( typestring + ident + ZeroOrMore( "," + typestring + ident ) ) | void ) + rpar ).setParseAction(code_block_obj.pushFuncArgs)
        function_block = Group( lbrack + ZeroOrMore( comments.suppress() | assignment | conditional_set | returnline ) + rbrack ).setParseAction(code_block_obj.pushFuncBlock)
        func_def = Group( func + func_def_args + function_block )
        bnf = OneOrMore( comments.suppress() | func_def | assignment | conditional_set ) + stringEnd
    return bnf

if __name__ == "__main__":
    import unittest

    class TestPyGameMakerLanguageEngine(unittest.TestCase):

        def setUp(self):

            self.functionmap = {
                'distance': { "arglist":
                [{"type": "number", "name":"start"},{"type":"number", "name":"end"}],
                'block': ["_start", "_end", "operator.sub", "operator.abs", "_return"]
                },
                'randint': { "arglist":
                [{"type":"number", "name":"max"}],
                'block': [0, "_max", "random.randint", "_return"]
                },
                'time': { "arglist": [],
                'block': ["time.time", "_return"]
                }
            }
            self.sym_table = PyGameMakerSymbolTable()
            self.module_context = imp.new_module('game_functions')

        def test_005valid_assignment(self):
            simple_line = "x = 49"
            code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("goodassignment",
                self.module_context, simple_line, self.functionmap)
            code_block.load(['operator', 'math'])
            sym_table = PyGameMakerSymbolTable()
            code_block.run(sym_table)
            print("Symbol table:")
            sym_table.dumpVars()
            self.assertTrue(sym_table['x'] == 49)

        def test_010valid_conditional(self):
            valid_conditional="""
if (4 > 5) { x = 1 }
elseif (4 > 4) { x = 2 }
elseif (4 < 4) { x = 3 }
else { x = 4 }
            """
            code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("goodconditional",
                self.module_context, valid_conditional, self.functionmap)
            #print("ast:\n{}".format(code_block.astree))
            #print("outer block:\n{}".format(code_block.outer_block))
            code_block.load(['operator', 'math'])
            sym_table = PyGameMakerSymbolTable()
            code_block.run(sym_table)
            print("Symbol table:")
            sym_table.dumpVars()
            self.assertTrue(sym_table['x'] == 4)

        def test_015valid_operations(self):
            valid_operations="""
va = 1 > 0
vb = 1 < 0
vc = 2 >= 2
vd = 2 <= 2
ve = 1 >= 2
vf = 1 <= 2
vg = 1 != 2
vh = 1 == 2
vi = ((va == 0) and vb)
vj = ve or vf
vv = 7 / 3
vw = 6.0 / 1.5
vx = 4 + 5
vy = 6 ^ 3
vz = -2 * 4
            """
            code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("goodops",
                self.module_context, valid_operations, self.functionmap)
            #print("ast:\n{}".format(code_block.astree))
            #print("outer block:\n{}".format(code_block.outer_block))
            code_block.load(['operator', 'math'])
            sym_table = PyGameMakerSymbolTable()
            code_block.run(sym_table)
            print("Symbol table:")
            sym_table.dumpVars()
            answers = {
                "va": 1, "vb": 0, "vc": 1, "vd": 1, "ve": 0, "vf": 1,
                "vg": 1, "vh": 0, "vi": 0, "vj": 1,
                "vv": 2, "vw": 4.0, "vx": 9, "vy": 216, "vz": -8
            }
            self.assertEqual(sym_table._vars, answers)

        def test_020valid_function_def(self):
            valid_function="""
function set_X(number n) { x = n }
            """
            code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("goodfunc",
                self.module_context, valid_function, self.functionmap)
            #print("ast:\n{}".format(code_block.astree))
            #print("outer block:\n{}".format(code_block.outer_block))
            code_block.load(['operator', 'math'])
            sym_table = PyGameMakerSymbolTable()
            code_block.run(sym_table)
            self.module_context.userfunc_set_X(sym_table, 20)
            print("Symbol table:")
            sym_table.dumpVars()
            self.assertEqual(sym_table['x'], 20)

        def test_025valid_function_call(self):
            valid_function_call="""
x = distance(12, 19)
            """
            code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("goodfunccall",
                self.module_context, valid_function_call, self.functionmap)
            #print("ast:\n{}".format(code_block.astree))
            #print("outer block:\n{}".format(code_block.outer_block))
            code_block.load(['operator', 'math'])
            sym_table = PyGameMakerSymbolTable()
            code_block.run(sym_table)
            print("Symbol table:")
            sym_table.dumpVars()
            self.assertEqual(sym_table['x'], 7)

        def test_030invalid_syntax(self):
            module_context = imp.new_module('for_errors')
            bad_line1 = "x + 1 = 59"
            with self.assertRaises(ParseException):
                code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("badsyntax1",
                    module_context, bad_line1, self.functionmap)
            bad_line2 = "_y = 1"
            with self.assertRaises(ParseException):
                code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("badsyntax2",
                    module_context, bad_line2, self.functionmap)
            bad_line3 = "if { a = 2 }"
            with self.assertRaises(ParseException):
                code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("badsyntax3",
                    module_context, bad_line3, self.functionmap)
            bad_line4 = "function noparams() { a = 2 }"
            with self.assertRaises(ParseException):
                code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("badsyntax4",
                    module_context, bad_line4, self.functionmap)
            bad_line5 = "function oneparam(n) { a = n }"
            with self.assertRaises(ParseException):
                code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("badsyntax5",
                    module_context, bad_line5, self.functionmap)
            bad_line6 = "if 2 > 1 { a = 2 }"
            with self.assertRaises(ParseException):
                code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("badsyntax6",
                    module_context, bad_line6, self.functionmap)
            bad_line7 = "if ((2 > 1) or or (1 > 2)) { a = 2 }"
            with self.assertRaises(ParseFatalException):
                code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("badsyntax7",
                    module_context, bad_line7, self.functionmap)

        def test_035semantic_errors(self):
            module_context = imp.new_module('for_sem_errors')
            bad_code1 = "x = nosuchfunc(1)"
            with self.assertRaises(ParseFatalException):
                code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("semanticerror1",
                    module_context, bad_code1, self.functionmap)
            bad_code2 = "x = distance(12)"
            with self.assertRaises(ParseFatalException):
                code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("semanticerror2",
                    module_context, bad_code2, self.functionmap)

        def test_040call_stack_error(self):
            module_context = imp.new_module('for_recursion_error')
            call_stack_error_code="""
function infinite_recursion(void) {
    x = infinite_recursion()
    return 1
}
a = infinite_recursion()
            """
            code_block = PyGameMakerCodeBlockGenerator.wrap_code_block("recursionbomb",
                module_context, call_stack_error_code, self.functionmap)
            code_block.load(['operator', 'math'])
            sym_table = PyGameMakerSymbolTable()
            with self.assertRaises(pgmrts.PyGameMakerCodeBlockRuntimeError):
                code_block.run(sym_table)

        def test_045language_engine(self):
            language_engine = PyGameMakerLanguageEngine()
            source_string = ""
            with open("unittest_files/testpgm", "r") as source_f:
                source_string = source_f.read()
            #print("Program:\n{}".format(source_string))
            language_engine.register_code_block("testA", source_string)
            another_program_string="""
radius = 2
circumference = 2.0 * pi * radius
            """
            language_engine.register_code_block("testB", another_program_string)
            language_engine.execute_code_block("testB")
            language_engine.execute_code_block("testA")
            print("Symbol table:")
            language_engine.symbol_table.dumpVars()
            answers = {"radius": 2,
                "circumference": 2 * math.pi * 2,
                "a": 26, "b": -259, "x": 64, "y": 12}
            self.assertEqual(language_engine.symbol_table._vars, answers)

    unittest.main()

