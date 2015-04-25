#!/usr/bin/python -W all

# Copied from the fourFn.py example that ships with PyParser
# original code copyright 2003-2009 by Paul McGuire

# handles math operations, predefined functions, keywords, boolean comparisons,
#  function definitions, setting and using any supplied global variables

from pyparsing import Literal,CaselessLiteral,Word,Group,Optional,\
    ZeroOrMore,OneOrMore,Forward,nums,alphas,Regex,ParseException,Keyword,\
    Dict,stringEnd
import math
import operator
import infix_to_postfix

class PyGameMakerLanguageEngineException(Exception):
    pass

class PyGameMakerCodeBlockException(Exception):
    pass

class PyGameMakerCodeBlock(object):
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

    def __init__(self, funclist=[], ast=None):
        self.outer_block = []
        self.inner_blocks = []
        self.stack = self.outer_block
        self.scratch = []
        self.comparison_list = []
        self.block_stack = []
        self.last_candidate_match = None
        self.inner_block_count = 0
        self.functionlist = list(funclist)
        self.ast = ast

    def add_to_func_list(self, func_list):
        if isinstance(func_list, str):
            self.functionlist.append(func_list)
        else:
            for func in func_list:
                self.functionlist.append(func)

    def pushAssignment(self, parsestr, loc, toks):
        assign_list = []
        for assign_tok in toks.asList():
            for inner_item in assign_tok:
                if inner_item == '=':
                    break
                assign_list.append(inner_item)
            break
        print("assignment scratch: {}".format(self.scratch))
        self.stack.append(assign_list + list(self.scratch) + ['='])
        print("assignment: {}".format(self.stack[-1]))
        self.scratch = []

    def pushBlock(self, parsestr, loc, toks):
        #print("push block")
        if (self.inner_block_count > 1):
            #print("inner block #{}\n{}".format(self.inner_block_count-1,self.stack))
            self.inner_block_count -= 1
            self.inner_blocks[self.inner_block_count-1].append(list(self.stack))
            #print("stack now points to inner block #{}".format(self.inner_block_count-1))
            self.stack = self.inner_blocks[self.inner_block_count-1]
            self.inner_blocks[self.inner_block_count] = []
        else:
            #print("inner block #0\n{}".format(self.stack))
            self.inner_block_count = 0
            self.outer_block.append(list(self.stack))
            self.stack = self.outer_block
            #print("stack now points to outer block")

    def pushIfCond(self, parsestr, loc, toks):
        if_statement = ""
        for tok in toks:
            if_statement = str(tok)
            #print("push if statement: {}".format(if_statement))
            break
        container_block = self.outer_block
        if (self.inner_block_count > 0):
            container_block = self.inner_blocks[-1]
            #print("container: inner block {}".format(self.inner_block_count-1))
        else:
            pass
            #print("container: outer block")
        container_block.append(if_statement)
        self.inner_block_count += 1
        self.inner_blocks.append([])
        #print("stack now points at inner block {}".format(self.inner_block_count-1))
        self.stack = self.inner_blocks[-1]

    def pushComparison(self, parsestr, loc, toks):
        self.comparison_list.append(list(self.scratch))
        #print("comparisons: {}".format(self.comparison_list))
        self.stack.append(list(self.scratch))
        self.scratch = []

    def pushFunctionCall(self, parsestr, loc, toks):
        self.stack.append(toks[0])
        for args in toks[1:]:
            self.stack.append(args)

    def pushAtom(self, parsestr, loc, toks):
        func_call = False
        for tok in toks:
            if tok in self.functionlist:
                func_call = True
            break
        print("atom: {}".format(toks.asList()))
        if func_call:
            self.scratch += infix_to_postfix.convert_infix_to_postfix([toks[0]],
                self.OPERATOR_REPLACEMENTS)
        else:
            self.scratch += infix_to_postfix.convert_infix_to_postfix(toks,
                self.OPERATOR_REPLACEMENTS)
        print("scratch is now: {}".format(self.scratch))

    def pushFirst(self, parsestr, loc, toks):
        print("pre-op: {}".format(toks.asList()))
        self.scratch += infix_to_postfix.convert_infix_to_postfix(toks[0],
            self.OPERATOR_REPLACEMENTS)
        print("op + scratch is now: {}".format(self.scratch))

    def pushBoolNot(self, parsestr, loc, toks):
        for t in toks:
            if t == 'not':
                self.stack.append( 'not')
            else:
                break

    def pushUMinus(self, parsestr, loc, toks):
        for t in toks:
            if t == '-': 
                self.scratch.append( 'unary -' )
            else:
                break

    def copy(self, other):
        other.stack = list(self.stack)
        other.scratch = list(self.scratch)
        other.comparison_list = list(self.comparison_list)
        other.inner_blocks = list(self.inner_blocks)
        other.outer_block = list(self.outer_block)
        if self.ast:
            other.ast = list(self.ast)

    def clear(self):
        self.stack = []

class PyGameMakerCodeBlockGenerator(object):
    bnf = None
    code_block = PyGameMakerCodeBlock()
    @classmethod
    def wrap_code_block(cls, source_code_str, funclist=[]):
        if len(funclist) > 0:
            cls.code_block.add_to_func_list(funclist)
        cls.bnf = BNF(cls.code_block)
        ast = cls.bnf.parseString(source_code_str)
        new_block = PyGameMakerCodeBlock(ast)
        cls.code_block.copy(new_block)
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
    boolean_op    :: 'or' | 'and' | 'not'
    conditional_keyword   :: 'if' | 'elseif' | 'else'
    identifier    :: lower_case | upper_case [ lower_case | upper_case | decimal_digit | '_' ]*
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
    combinatorial :: expr [ boolean_op expr ]*
    function_def  :: 'def' identifier '('[ identifier ] [',' identifier]* ')' block
    assignment    :: identifier equalop combinatorial
    comparison    :: combinatorial compareop combinatorial
    conditional   :: conditional_keyword '(' comparison ')' block
    block         :: '{' assignment | comparison | conditional '}'
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
        is_equal = Literal( "==" )
        is_nequal = Literal( "!=" )
        is_lt = Literal( "<" )
        is_lte = Literal( "<=" )
        is_gt = Literal( ">" )
        is_gte = Literal( ">=" )
        assignop = Literal( "=" )
        compareop = is_equal | is_nequal | is_lt | is_lte | is_gt | is_gte
        boolop = boolor | booland
        addop  = plus | minus
        multop = mult | div
        expop = Literal( "^" )
        pi    = CaselessLiteral( "PI" )
        
        combinatorial = Forward()
        expr = Forward()
        atom = ((0,None)*minus + ( pi | e | ident + lpar + ZeroOrMore( combinatorial + ZeroOrMore( ',' + combinatorial ) ) + rpar | fnumber | ident ).setParseAction(code_block_obj.pushAtom) | 
                Group( lpar + combinatorial + rpar )).setParseAction(code_block_obj.pushUMinus)
        
        # by defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-righ
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor << ( atom + ZeroOrMore( ( expop + factor ).setParseAction(code_block_obj.pushFirst) ) )
        term = ( factor + ZeroOrMore( ( multop + factor ).setParseAction(code_block_obj.pushFirst) ) )
        expr << ( term + ZeroOrMore( ( addop + term ).setParseAction(code_block_obj.pushFirst) ) )
        combinatorial << ( Optional( boolnot ) + expr + ZeroOrMore( ( boolop + Optional( boolnot ) + expr ).setParseAction(code_block_obj.pushFirst) ) )
        assignment = Group( ident + assignop + combinatorial ).setParseAction(code_block_obj.pushAssignment)
        comparison = Group( combinatorial + Optional( compareop + combinatorial ).setParseAction(code_block_obj.pushFirst) ).setParseAction(code_block_obj.pushComparison)
        block = Forward()
        conditional_start = ( ifcond.setParseAction(code_block_obj.pushIfCond) + lpar + comparison + rpar + block )
        conditional_continue = ( elseifcond.setParseAction(code_block_obj.pushIfCond) + Group( lpar + comparison + rpar ) + block )
        conditional_else = ( elsecond.setParseAction(code_block_obj.pushIfCond) + block )
        conditional_set = Group( conditional_start + ZeroOrMore( conditional_continue ) + Optional( conditional_else ) )
        block << Group( lbrack + ZeroOrMore( assignment | conditional_set ) + rbrack ).setParseAction(code_block_obj.pushBlock)
        bnf = OneOrMore( assignment | conditional_set ) + stringEnd
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
    function_list = ['randint']
    with open("testpgm", "r") as pf:
        pgm = pf.read()
    code_block = PyGameMakerCodeBlockGenerator.wrap_code_block(pgm,
        function_list)
    print("Program:\n{}".format(pgm))
    print("=======")
    print("parsed:\n{}".format(code_block.ast))
    print("=======")
    print("scratch:\n{}".format(code_block.scratch))
    print("=======")
    print("stack:\n{}".format(code_block.stack))
    print("=======")
    print("comparisons:\n{}".format(code_block.comparison_list))
    print("=======")
    print("inner blocks:\n{}".format(code_block.inner_blocks))
    print("=======")
    print("outer block:\n{}".format(code_block.outer_block))

