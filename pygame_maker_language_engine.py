#!/usr/bin/python -W all

# Copied from the fourFn.py example that ships with PyParser
# original code copyright 2003-2009 by Paul McGuire

# handles math operations, predefined functions, keywords, boolean comparisons,
#  function definitions, setting and using any supplied global variables

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

class PyGameMakerLanguageEngineException(Exception):
    pass

class PyGameMakerCodeBlockException(Exception):
    pass

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
        "operator.lt": ["number", "number"],
        "operator.lte": ["number", "number"],
        "operator.gt": ["number", "number"],
        "operator.gte": ["number", "number"],
        "operator.eq": ["number", "number"],
        "operator.neq": ["number", "number"],
        "math.pow": ["number", "number"]
    }
    KNOWN_CONSTANTS={
        "PI":   math.pi,
        "E":    math.e
    }
    OPERATOR_REPLACEMENTS={
        "+": "operator.add",
        "-": "operator.sub",
        "*": "operator.mul",
        "/": "operator.truediv",
        "%": "operator.mod",
        "<": "operator.lt",
        "<=": "operator.lte",
        ">": "operator.gt",
        ">=": "operator.gte",
        "==": "operator.eq",
        "!=": "operator.neq",
        "^": "math.pow"
    }

    def __init__(self, funcmap={}, ast=None):
        """
            __init__():
            optional args:
             funcmap: A dict with <function_name>: [arg_type1, .., arg_typeN]
              entries, representing the external function table made available
              to the code block. Void argument lists can be represented with an
              empty list. The number and type of arguments supplied assist with
              syntax checking.
             ast: the abstract syntax tree produced by pyparsing
        """
        self.outer_block = []
        self.inner_blocks = []
        self.stack = self.outer_block
        self.frame = self.outer_block
        self.scratch = []
        self.inner_block_count = 0
        self.functionmap = dict(funcmap)
        self.ast = ast

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
        #print("append {} to stack".format(comparison_list))
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

    def pushFuncBlock(self, parsestr, loc, toks):
        """
            Take the current function block frame and reduce it, before
            switching the frame back to the outer_block.
        """
        # reduce the function source
        self.reduceBlock(self.frame)
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
        func_call = False
        for tok in toks:
            if tok in self.functionmap:
                func_call = True
            break
        #print("atom: {}".format(toks.asList()))
        if func_call:
            self.scratch += infix_to_postfix.convert_infix_to_postfix([toks[0]],
                self.OPERATOR_REPLACEMENTS)
        else:
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
                if check_op in self.KNOWN_CONSTANTS:
                    code_line[line_idx] = self.KNOWN_CONSTANTS[check_op]
                    line_idx += 1
                    continue
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
                            if not isinstance(rev_item, int):
                                result_type = type(rev_item)
                        if all_numbers:
                            operation = "{}(".format(check_op)
                            operand_strs = [str(n) for n in code_line[line_idx-op_len:line_idx]]
                            operation += "{})".format(",".join(operand_strs))
                            #print("Perform calc: {}".format(operation))
                            op_result = eval(operation)
                            # true/false become ints
                            if isinstance(op_result, bool):
                                if op_result:
                                    op_result = 1
                                else:
                                    op_result = 0
                            else:
                                op_result = result_type(op_result)
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

    def execute(self):
        pass

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
        if self.ast:
            other.ast = list(self.ast)
        other.addToFuncMap(self.functionmap)

    def clear(self):
        """
            clear():
            Clear out all lists in preparation for a new parsing operation.
        """
        self.stack = []
        self.scratch = []
        self.inner_blocks = []
        self.inner_block_count = 0
        self.outer_block = []
        self.frame = []
        self.functionmap = {}
        self.ast = None

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
    code_block = PyGameMakerCodeBlock()
    @classmethod
    def wrap_code_block(cls, source_code_str, funcmap=[]):
        if len(funcmap) > 0:
            cls.code_block.addToFuncMap(funcmap)
        cls.bnf = BNF(cls.code_block)
        ast = cls.bnf.parseString(source_code_str)
        cls.code_block.reduce()
        new_block = PyGameMakerCodeBlock(funcmap, ast)
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
        self.constant_table = {}
        self.variable_table = {}
        self.function_table = {}
        self.code_block = PyGameMakerCodeBlock()

    def set_variable_value(self, variable_name, value):
        if variable_name in self.constant_table:
            raise(PyGameMakerLanguageEngineException("{} = {}: Cannot assign a value to a constant".format(variable_name, value)))
        # @@@ disallow using function names as variables
        self.variable_table[variable_name] = value

    def get_variable_value(self, variable_name):
        if not variable_name in self.variable_table:
            if not variable_name in self.constant_table:
                return None
            else:
                return self.constant_table[variable_name]
        else:
            return self.variable_table[variable_name]

    def add_function(self, function_name, function_block, *function_args):
        pass

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
        e     = CaselessLiteral( "E" )
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
        compareop = is_equal | is_nequal | is_lt | is_lte | is_gt | is_gte
        boolop = boolor | booland
        addop  = plus | minus
        multop = mult | div
        typestring = num | strn
        expop = Literal( "^" )
        pi    = CaselessLiteral( "PI" )

        comments = comment_sym + uptolineend
        combinatorial = Forward()
        expr = Forward()
        atom = ((0,None)*minus + ( pi | e | ( ident + lpar + Optional( combinatorial + ZeroOrMore( "," + combinatorial ) ) + rpar ).setParseAction(code_block_obj.countFunctionArgs) | fnumber | ident ).setParseAction(code_block_obj.pushAtom) | 
                Group( lpar + combinatorial + rpar )).setParseAction(code_block_obj.pushUMinus)
        
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

# map operator symbols to corresponding arithmetic operations
#epsilon = 1e-12
#opn = { "+" : operator.add,
#        "-" : operator.sub,
#        "*" : operator.mul,
#        "/" : operator.truediv,
#        "^" : operator.pow }
#fn  = { "sin" : math.sin,
#        "cos" : math.cos,
#        "tan" : math.tan,
#        "abs" : abs,
#        "trunc" : lambda a: int(a),
#        "round" : round,
#        "sgn" : lambda a: (a > epsilon) - (a < -epsilon) }
#def evaluateStack( s ):
#    op = s.pop()
#    if op == 'unary -':
#        return -evaluateStack( s )
#    if op in "+-*/^":
#        op2 = evaluateStack( s )
#        op1 = evaluateStack( s )
#        return opn[op]( op1, op2 )
#    elif op == "PI":
#        return math.pi # 3.1415926535
#    elif op == "E":
#        return math.e  # 2.718281828
#    elif op in fn:
#        return fn[op]( evaluateStack( s ) )
#    elif op[0].isalpha():
#        raise Exception("invalid identifier '%s'" % op)
#    else:
#        return float( op )

if __name__ == "__main__":
    pgm = ""
    functionmap = {
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
    with open("testpgm", "r") as pf:
        pgm = pf.read()
    code_block = PyGameMakerCodeBlockGenerator.wrap_code_block(pgm,
        functionmap)
    print("Program:\n{}".format(pgm))
    print("=======")
    print("parsed:\n{}".format(code_block.ast))
    #print("=======")
    #print("scratch:\n{}".format(code_block.scratch))
    print("=======")
    print("function map:\n{}".format(code_block.functionmap))
    #print("=======")
    #print("stack:\n{}".format(code_block.stack))
    #print("=======")
    #print("inner blocks:\n{}".format(code_block.inner_blocks))
    print("=======")
    print("outer block:\n{}".format(code_block.outer_block))

