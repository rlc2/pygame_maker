#!/usr/bin/env python
from pygame_maker.logic.language_engine import CodeBlock, CodeBlockGenerator,\
    LanguageEngine, SymbolTable
from pygame_maker.logic import run_time_support
from pyparsing import ParseException, ParseFatalException
import unittest
import logging
import math
import imp
import sys
import os

cblogger = logging.getLogger("CodeBlock")
cbhandler = logging.StreamHandler()
cbformatter = logging.Formatter("%(levelname)s: %(message)s")
cbhandler.setFormatter(cbformatter)
cblogger.addHandler(cbhandler)
cblogger.setLevel(logging.INFO)

lelogger = logging.getLogger("LanguageEngine")
lehandler = logging.StreamHandler()
leformatter = logging.Formatter("%(levelname)s: %(message)s")
lehandler.setFormatter(leformatter)
lelogger.addHandler(lehandler)
lelogger.setLevel(logging.INFO)

class TestLanguageEngine(unittest.TestCase):

    def dumpSymtables(self, symtables):
        print("Symbol table:")
        print("globals:")
        symtables['globals'].dumpVars()
        print("locals:")
        symtables['locals'].dumpVars()

    def symChangeCallback(self, item, val):
        self.symbol_change_list.append( {item: val} )

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
        self.sym_tables = { "globals": SymbolTable(),
            "locals": SymbolTable() }
        self.module_context = imp.new_module('game_functions')
        self.symbol_change_list = []

    def test_005valid_assignment(self):
        simple_line = "x = 49"
        code_block = CodeBlockGenerator.wrap_code_block("goodassignment",
            self.module_context, simple_line, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = { "globals": SymbolTable(),
            "locals": SymbolTable() }
        code_block.run(sym_tables)
        self.dumpSymtables(sym_tables)
        self.assertTrue(sym_tables['locals']['x'] == 49)
        simple_line2 = "global y = 49"
        code_block = CodeBlockGenerator.wrap_code_block("goodassignment2",
            self.module_context, simple_line2, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = { "globals": SymbolTable(),
            "locals": SymbolTable() }
        code_block.run(sym_tables)
        self.dumpSymtables(sym_tables)
        self.assertTrue(sym_tables['globals']['y'] == 49)

    def test_006global_vs_local_symbols(self):
        symbol_test="""
global answer = 42
wrong_answer = 54
x = wrong_answer - answer
answer = wrong_answer
"""
        code_block = CodeBlockGenerator.wrap_code_block("symbol_tables",
            self.module_context, symbol_test, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = { "globals": SymbolTable(),
            "locals": SymbolTable() }
        code_block.run(sym_tables)
        self.dumpSymtables(sym_tables)
        self.assertTrue(sym_tables['globals']['answer'] == 54)
        self.assertTrue(sym_tables['locals']['wrong_answer'] == 54)
        self.assertTrue(sym_tables['locals']['x'] == 12)

    def test_010valid_conditional(self):
        valid_conditional="""
if (4 > 5) { x = 1 }
elseif (4 > 4) { x = 2 }
elseif (4 < 4) { x = 3 }
else { x = 4 }
        """
        code_block = CodeBlockGenerator.wrap_code_block("goodconditional",
            self.module_context, valid_conditional, self.functionmap)
        #print("ast:\n{}".format(code_block.astree))
        #print("outer block:\n{}".format(code_block.outer_block))
        code_block.load(['operator', 'math'])
        sym_tables = { "globals": SymbolTable(),
            "locals": SymbolTable() }
        code_block.run(sym_tables)
        self.dumpSymtables(sym_tables)
        self.assertTrue(sym_tables['locals']['x'] == 4)

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
        code_block = CodeBlockGenerator.wrap_code_block("goodops",
            self.module_context, valid_operations, self.functionmap)
        #print("ast:\n{}".format(code_block.astree))
        #print("outer block:\n{}".format(code_block.outer_block))
        code_block.load(['operator', 'math'])
        sym_tables = { "globals": SymbolTable(),
            "locals": SymbolTable() }
        code_block.run(sym_tables)
        self.dumpSymtables(sym_tables)
        answers = {
            "va": 1, "vb": 0, "vc": 1, "vd": 1, "ve": 0, "vf": 1,
            "vg": 1, "vh": 0, "vi": 0, "vj": 1,
            "vv": 2, "vw": 4.0, "vx": 9, "vy": 216, "vz": -8
        }
        self.assertEqual(sym_tables['locals'].vars, answers)

    def test_020valid_function_def(self):
        valid_function="""
function set_X(number n) { x = n }
        """
        code_block = CodeBlockGenerator.wrap_code_block("goodfunc",
            self.module_context, valid_function, self.functionmap)
        #print("ast:\n{}".format(code_block.astree))
        #print("outer block:\n{}".format(code_block.outer_block))
        exec "from pygame_maker.logic.run_time_support import *\n" in self.module_context.__dict__
        code_block.load(['operator', 'math'])
        sym_tables = { "globals": SymbolTable(),
            "locals": SymbolTable() }
        code_block.run(sym_tables)
        self.module_context.userfunc_set_X(sym_tables, 20)
        print("Symbol table:")
        self.dumpSymtables(sym_tables)
        self.assertEqual(sym_tables['locals']['x'], 20)

    def test_025valid_function_call(self):
        valid_function_call="""
x = distance(12, 19)
        """
        code_block = CodeBlockGenerator.wrap_code_block("goodfunccall",
            self.module_context, valid_function_call, self.functionmap)
        #print("ast:\n{}".format(code_block.astree))
        #print("outer block:\n{}".format(code_block.outer_block))
        code_block.load(['operator', 'math'])
        sym_tables = { "globals": SymbolTable(),
            "locals": SymbolTable() }
        code_block.run(sym_tables)
        self.dumpSymtables(sym_tables)
        self.assertEqual(sym_tables['locals']['x'], 7)

    def test_030invalid_syntax(self):
        module_context = imp.new_module('for_errors')
        bad_line1 = "x + 1 = 59"
        with self.assertRaises(ParseException):
            code_block = CodeBlockGenerator.wrap_code_block("badsyntax1",
                module_context, bad_line1, self.functionmap)
        bad_line2 = "_y = 1"
        with self.assertRaises(ParseException):
            code_block = CodeBlockGenerator.wrap_code_block("badsyntax2",
                module_context, bad_line2, self.functionmap)
        bad_line3 = "if { a = 2 }"
        with self.assertRaises(ParseException):
            code_block = CodeBlockGenerator.wrap_code_block("badsyntax3",
                module_context, bad_line3, self.functionmap)
        bad_line4 = "function noparams() { a = 2 }"
        with self.assertRaises(ParseException):
            code_block = CodeBlockGenerator.wrap_code_block("badsyntax4",
                module_context, bad_line4, self.functionmap)
        bad_line5 = "function oneparam(n) { a = n }"
        with self.assertRaises(ParseException):
            code_block = CodeBlockGenerator.wrap_code_block("badsyntax5",
                module_context, bad_line5, self.functionmap)
        bad_line6 = "if 2 > 1 { a = 2 }"
        with self.assertRaises(ParseException):
            code_block = CodeBlockGenerator.wrap_code_block("badsyntax6",
                module_context, bad_line6, self.functionmap)
        bad_line7 = "if ((2 > 1) or or (1 > 2)) { a = 2 }"
        with self.assertRaises(ParseFatalException):
            code_block = CodeBlockGenerator.wrap_code_block("badsyntax7",
                module_context, bad_line7, self.functionmap)

    def test_035semantic_errors(self):
        module_context = imp.new_module('for_sem_errors')
        bad_code1 = "x = nosuchfunc(1)"
        with self.assertRaises(ParseFatalException):
            code_block = CodeBlockGenerator.wrap_code_block("semanticerror1",
                module_context, bad_code1, self.functionmap)
        bad_code2 = "x = distance(12)"
        with self.assertRaises(ParseFatalException):
            code_block = CodeBlockGenerator.wrap_code_block("semanticerror2",
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
        code_block = CodeBlockGenerator.wrap_code_block("recursionbomb",
            module_context, call_stack_error_code, self.functionmap)
        code_block.load(['operator', 'math'])
        sym_tables = { "globals": SymbolTable(),
            "locals": SymbolTable() }
        with self.assertRaises(run_time_support.CodeBlockRuntimeError):
            code_block.run(sym_tables)

    def test_045language_engine(self):
        language_engine = LanguageEngine()
        source_string = ""
        with open("unittest_files/testpgm", "r") as source_f:
            source_string = source_f.read()
        #print("Program:\n{}".format(source_string))
        language_engine.register_code_block("testA", source_string)
        testa_locals = SymbolTable()
        another_program_string="""
radius = 2
circumference = 2.0 * pi * radius
        """
        language_engine.register_code_block("testB", another_program_string)
        testb_locals = SymbolTable()
        language_engine.execute_code_block("testB", testb_locals)
        language_engine.execute_code_block("testA", testa_locals)
        print("Global symbol table:")
        language_engine.global_symbol_table.dumpVars()
        print("test A symbol table:")
        testa_locals.dumpVars()
        print("test B symbol table:")
        testb_locals.dumpVars()
        testa_answers = { "a": 26, "b": -259, "x": 64, "y": 12 }
        testb_answers = { "radius": 2,
            "circumference": 2 * math.pi * 2 }
        self.assertEqual(testa_locals.vars, testa_answers)
        self.assertEqual(testb_locals.vars, testb_answers)

    def test_050unregister_code_blocks(self):
        language_engine = LanguageEngine()
        language_engine.register_code_block("testA", "a = 1")
        language_engine.register_code_block("testB", "b = 2")
        self.assertEqual(['testA', 'testB'],
            language_engine.code_blocks.keys())
        language_engine.unregister_code_block("testA")
        self.assertEqual(['testB'], language_engine.code_blocks.keys())
        language_engine.unregister_code_block("testB")
        self.assertEqual([], language_engine.code_blocks.keys())

    def test_055symbol_change_callback(self):
        language_engine = LanguageEngine()
        code_block = """
sym1 = 24
sym3 = 25
global sym2 = 36
sym4 = 42
        """
        language_engine.register_code_block("testA", code_block)
        test_locals = SymbolTable({}, sym_change_callback=lambda s, v: self.symChangeCallback(s, v))
        test_locals.setConstant('sym2', 64)
        language_engine.execute_code_block("testA", test_locals)
        expected_changes = [{'sym1': 24}, {'sym3': 25}, {'sym4': 42}]
        self.assertEqual(self.symbol_change_list, expected_changes)

# run from the tests directory to find the unittest_files subdirectory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

unittest.main()

