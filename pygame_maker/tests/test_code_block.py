#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test the pygame_maker.logic.code_block module.
"""

import imp
import logging
import unittest
from pyparsing import ParseException, ParseFatalException
from pygame_maker.events.event import Event
from pygame_maker.logic.code_block import CodeBlockGenerator
from pygame_maker.logic.language_engine import SymbolTable
from pygame_maker.logic import run_time_support

CBLOGGER = logging.getLogger("CodeBlock")
CBHANDLER = logging.StreamHandler()
CBFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
CBHANDLER.setFormatter(CBFORMATTER)
CBLOGGER.addHandler(CBHANDLER)
CBLOGGER.setLevel(logging.INFO)

def dump_symtables(symtables):
    """Display symbol table contents."""
    print("Symbol table:")
    print("globals:")
    symtables['globals'].dump_vars()
    print("locals:")
    symtables['locals'].dump_vars()


class DummyObject(object):
    """Stub object for testing action methods."""
    def __init__(self):
        self.action_called = False

    def forward_action(self, an_action, in_event):
        """
        Log and keep track of whether this method has been called from user code.
        """
        print("Forward action {}, with event {}".format(an_action, in_event))
        self.action_called = True


class TestCodeBlock(unittest.TestCase):
    """Unit tests for the code_block module."""

    def sym_change_callback(self, item, val):
        """Keep track of symbol value changes."""
        self.symbol_change_list.append({item: val})

    def setUp(self):
        self.functionmap = {
            'distance': {"arglist":
                         [{"type": "number", "name":"start"}, {"type":"number", "name":"end"}],
                         'block':
                         ["_start", "_end", "operator.sub", "operator.abs", "_return"]
                        },
            'randint': {"arglist":
                        [{"type":"number", "name":"max"}],
                        'block': [0, "_max", "random.randint", "_return"]
                       },
            'time': {"arglist": [], 'block': ["time.time", "_return"]},
            'print': {"arglist": [{"type": "string", "name": "print_str"}], 'block': []},
            'debug': {"arglist": [{"type": "string", "name": "message"}], 'block': []}
        }
        self.sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        self.module_context = imp.new_module('game_functions')
        self.symbol_change_list = []

    def test_005valid_assignment(self):
        """Test variable assignments to both local and global tables."""
        simple_line = "x = 49"
        code_block = CodeBlockGenerator.wrap_code_block(
            "goodassignment", self.module_context, simple_line, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        code_block.run(sym_tables)
        dump_symtables(sym_tables)
        self.assertEqual(sym_tables['locals']['x'], 49)
        simple_line = "x = true"
        code_block = CodeBlockGenerator.wrap_code_block(
            "goodassignment2", self.module_context, simple_line, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        code_block.run(sym_tables)
        dump_symtables(sym_tables)
        self.assertTrue(sym_tables['locals']['x'])
        simple_line2 = "global y = 49"
        code_block = CodeBlockGenerator.wrap_code_block(
            "goodassignment3", self.module_context, simple_line2, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        code_block.run(sym_tables)
        dump_symtables(sym_tables)
        self.assertTrue(sym_tables['globals']['y'] == 49)
        a_string = "mystr = \"This is a string\""
        code_block = CodeBlockGenerator.wrap_code_block(
            "goodstringassignment", self.module_context, a_string, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        code_block.run(sym_tables)
        dump_symtables(sym_tables)
        self.assertTrue(sym_tables['locals']['mystr'] == "This is a string")

    def test_006global_vs_local_symbols(self):
        """Mix global and local symbol assignments and accesses."""
        symbol_test = """
global answer = 42
wrong_answer = 54
x = wrong_answer - answer
answer = wrong_answer
"""
        code_block = CodeBlockGenerator.wrap_code_block(
            "symbol_tables", self.module_context, symbol_test, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        code_block.run(sym_tables)
        dump_symtables(sym_tables)
        self.assertTrue(sym_tables['globals']['answer'] == 54)
        self.assertTrue(sym_tables['locals']['wrong_answer'] == 54)
        self.assertTrue(sym_tables['locals']['x'] == 12)

    def test_010valid_conditional(self):
        """Test simple conditional statements."""
        valid_conditional = """
if (4 > 5) { x = 1 }
elseif (4 > 4) { x = 2 }
elseif (4 < 4) { x = 3 }
elseif (false) { x = 4 }
elseif (true and false) { x = 5 }
else { x = 6 }
        """
        code_block = CodeBlockGenerator.wrap_code_block(
            "goodconditional", self.module_context, valid_conditional, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        code_block.run(sym_tables)
        dump_symtables(sym_tables)
        self.assertTrue(sym_tables['locals']['x'] == 6)

    def test_015valid_operations(self):
        """Test various operators."""
        valid_operations = """
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
vk = true == false
vv = 7 / 3
vw = 6.0 / 1.5
vx = 4 + 5
vy = 6 ^ 3
vz = -2 * 4
        """
        code_block = CodeBlockGenerator.wrap_code_block(
            "goodops", self.module_context, valid_operations, self.functionmap)
        #print("ast:\n{}".format(code_block.astree))
        #print("outer block:\n{}".format(code_block.outer_block))
        code_block.load(['operator', 'math'])
        sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        code_block.run(sym_tables)
        dump_symtables(sym_tables)
        answers = {
            "va": 1, "vb": 0, "vc": 1, "vd": 1, "ve": 0, "vf": 1,
            "vg": 1, "vh": 0, "vi": 0, "vj": 1, "vk": False,
            "vv": 2, "vw": 4.0, "vx": 9, "vy": 216, "vz": -8
        }
        self.assertEqual(sym_tables['locals'].vars, answers)

    def test_020valid_function_def(self):
        """Test defining a function."""
        valid_function = """
function set_X(number n) { x = n }
        """
        code_block = CodeBlockGenerator.wrap_code_block(
            "goodfunc", self.module_context, valid_function, self.functionmap)
        #print("ast:\n{}".format(code_block.astree))
        #print("outer block:\n{}".format(code_block.outer_block))
        exec("from pygame_maker.logic.run_time_support import *\n", self.module_context.__dict__)
        code_block.load(['operator', 'math'])
        sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        code_block.run(sym_tables)
        self.module_context.userfunc_set_X(sym_tables, 20)
        print("Symbol table:")
        dump_symtables(sym_tables)
        self.assertEqual(sym_tables['locals']['x'], 20)

    def test_025valid_function_call(self):
        """Test calling functions."""
        valid_function_call = """
x = distance(12, 19)
        """
        code_block = CodeBlockGenerator.wrap_code_block(
            "goodfunccall", self.module_context, valid_function_call, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        code_block.run(sym_tables)
        dump_symtables(sym_tables)
        self.assertEqual(sym_tables['locals']['x'], 7)
        debug_function_call = """
y = print("THIS IS A STRING")
        """
        code_block = CodeBlockGenerator.wrap_code_block(
            "debugfunccall", self.module_context, debug_function_call, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        code_block.run(sym_tables)
        self.assertEqual(sym_tables['locals']['y'], "THIS IS A STRING")

    def test_030func_arg_string(self):
        """
        Test both definining and calling a function that accepts a string
        argument and returns a string.
        """
        module_context = imp.new_module('for_func_arg_string')
        str_func_arg_code = """
function string_arg(string a_str) {
    a = print(a_str)
    return "I returned a string"
}
b = string_arg("THIS IS A STRING ARG with a known function name userfunc_time")
"""
        code_block = CodeBlockGenerator.wrap_code_block(
            "func_arg_string", module_context, str_func_arg_code, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        code_block.run(sym_tables)
        self.assertEqual(sym_tables['locals']['a'],
                         "THIS IS A STRING ARG with a known function name userfunc_time")
        self.assertEqual(sym_tables['locals']['b'], "I returned a string")

    def test_035func_arg_bool(self):
        """Test defining and calling a function that accepts a boolean."""
        module_context = imp.new_module('for_func_arg_bool')
        bool_func_arg_code = """
function bool_arg(boolean a_bool) {
    a = a_bool
    return true
}
b = bool_arg(false)
"""
        code_block = CodeBlockGenerator.wrap_code_block(
            "func_arg_bool", module_context, bool_func_arg_code, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        code_block.run(sym_tables)
        self.assertEqual(sym_tables['locals']['a'], False)
        self.assertEqual(sym_tables['locals']['b'], True)

    def test_040action_method(self):
        """Test that user code can call action methods."""
        module_context = imp.new_module('for_action_methods')
        action_method_code = """
a = debug("This is a debug message!")
"""
        code_block = CodeBlockGenerator.wrap_code_block(
            "action_method", module_context, action_method_code, self.functionmap, ("debug",))
        code_block.load(['operator', 'math'])
        sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        obj_inst = DummyObject()
        sym_tables['locals']['self'] = obj_inst
        sym_tables['locals']['in_event'] = Event.get_event_instance_by_name("begin_step")
        code_block.run(sym_tables)
        self.assertTrue(obj_inst.action_called)

    def test_045invalid_syntax(self):
        """Test that syntax errors produce the expected exceptions."""
        module_context = imp.new_module('for_errors')
        bad_line1 = "x + 1 = 59"
        with self.assertRaises(ParseException):
            CodeBlockGenerator.wrap_code_block(
                "badsyntax1", module_context, bad_line1, self.functionmap)
        bad_line2 = "_y = 1"
        with self.assertRaises(ParseException):
            CodeBlockGenerator.wrap_code_block(
                "badsyntax2", module_context, bad_line2, self.functionmap)
        bad_line3 = "if { a = 2 }"
        with self.assertRaises(ParseException):
            CodeBlockGenerator.wrap_code_block(
                "badsyntax3", module_context, bad_line3, self.functionmap)
        bad_line4 = "function noparams() { a = 2 }"
        with self.assertRaises(ParseException):
            CodeBlockGenerator.wrap_code_block(
                "badsyntax4", module_context, bad_line4, self.functionmap)
        bad_line5 = "function oneparam(n) { a = n }"
        with self.assertRaises(ParseException):
            CodeBlockGenerator.wrap_code_block(
                "badsyntax5", module_context, bad_line5, self.functionmap)
        bad_line6 = "if 2 > 1 { a = 2 }"
        with self.assertRaises(ParseException):
            CodeBlockGenerator.wrap_code_block(
                "badsyntax6", module_context, bad_line6, self.functionmap)
        bad_line7 = "if ((2 > 1) or or (1 > 2)) { a = 2 }"
        with self.assertRaises(ParseFatalException):
            CodeBlockGenerator.wrap_code_block(
                "badsyntax7", module_context, bad_line7, self.functionmap)

    def test_050semantic_errors(self):
        """
        Test that calling an undefined function and incorrect argument counts
        to a function result in the expected exception.
        """
        module_context = imp.new_module('for_sem_errors')
        bad_code1 = "x = nosuchfunc(1)"
        with self.assertRaises(ParseFatalException):
            CodeBlockGenerator.wrap_code_block(
                "semanticerror1", module_context, bad_code1, self.functionmap)
        bad_code2 = "x = distance(12)"
        with self.assertRaises(ParseFatalException):
            CodeBlockGenerator.wrap_code_block(
                "semanticerror2", module_context, bad_code2, self.functionmap)

    def test_055call_stack_error(self):
        """Test that maximum recursion depth is enforced correctly."""
        module_context = imp.new_module('for_recursion_error')
        call_stack_error_code = """
function infinite_recursion(void) {
    x = infinite_recursion()
    return 1
}
a = infinite_recursion()
        """
        code_block = CodeBlockGenerator.wrap_code_block(
            "recursionbomb", module_context, call_stack_error_code, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = {"globals": SymbolTable(), "locals": SymbolTable()}
        with self.assertRaises(run_time_support.CodeBlockRuntimeError):
            code_block.run(sym_tables)

unittest.main()
