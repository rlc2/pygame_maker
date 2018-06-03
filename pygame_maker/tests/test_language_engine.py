#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test the pygame_maker.logic.language_engine module.
"""

import logging
import math
import os
import sys
import unittest
from pygame_maker.logic.language_engine import LanguageEngine, SymbolTable

CBLOGGER = logging.getLogger("CodeBlock")
CBHANDLER = logging.StreamHandler()
CBFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
CBHANDLER.setFormatter(CBFORMATTER)
CBLOGGER.addHandler(CBHANDLER)
CBLOGGER.setLevel(logging.INFO)

LELOGGER = logging.getLogger("LanguageEngine")
LEHANDLER = logging.StreamHandler()
LEFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
LEHANDLER.setFormatter(LEFORMATTER)
LELOGGER.addHandler(LEHANDLER)
LELOGGER.setLevel(logging.INFO)


class TestLanguageEngine(unittest.TestCase):
    """Unit tests for the language_engine module."""

    def sym_change_callback(self, item, val):
        """Keep track of symbol value changes."""
        self.symbol_change_list.append({item: val})

    def setUp(self):
        self.symbol_change_list = []

    def test_005language_engine(self):
        """Test code block registration and execution."""
        language_engine = LanguageEngine()
        source_string = ""
        with open("unittest_files/testpgm", "r") as source_f:
            source_string = source_f.read()
        #print("Program:\n{}".format(source_string))
        language_engine.register_code_block("testA", source_string)
        testa_locals = SymbolTable()
        another_program_string = """
radius = 2
circumference = 2.0 * pi * radius
        """
        language_engine.register_code_block("testB", another_program_string)
        testb_locals = SymbolTable()
        language_engine.execute_code_block("testB", testb_locals)
        language_engine.execute_code_block("testA", testa_locals)
        print("Global symbol table:")
        language_engine.global_symbol_table.dump_vars()
        print("test A symbol table:")
        testa_locals.dump_vars()
        print("test B symbol table:")
        testb_locals.dump_vars()
        testa_answers = {"a": 26, "b": -259, "x": 64, "y": 12}
        testb_answers = {"radius": 2, "circumference": 2 * math.pi * 2}
        self.assertEqual(testa_locals.vars, testa_answers)
        self.assertEqual(testb_locals.vars, testb_answers)

    def test_010unregister_code_blocks(self):
        """Test that code blocks get unregistered properly."""
        language_engine = LanguageEngine()
        language_engine.register_code_block("testA", "a = 1")
        language_engine.register_code_block("testB", "b = 2")
        self.assertEqual(['testA', 'testB'],
                         list(sorted(language_engine.code_blocks.keys())))
        language_engine.unregister_code_block("testA")
        self.assertEqual(['testB'], list(language_engine.code_blocks.keys()))
        language_engine.unregister_code_block("testB")
        self.assertEqual([], list(language_engine.code_blocks.keys()))

    def test_015symbol_change_callback(self):
        """
        Test that symbol changes result in the proper sequence of callbacks.
        """
        language_engine = LanguageEngine()
        code_block = """
sym1 = 24
sym3 = 25
global sym2 = 36
sym4 = 42
        """
        language_engine.register_code_block("testA", code_block)
        test_locals = SymbolTable(
            {}, sym_change_callback=lambda s, v: self.sym_change_callback(s, v))
        test_locals.set_constant('sym2', 64)
        language_engine.execute_code_block("testA", test_locals)
        expected_changes = [{'sym1': 24}, {'sym3': 25}, {'sym4': 42}]
        self.assertEqual(self.symbol_change_list, expected_changes)

# run from the tests directory to find the unittest_files subdirectory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

unittest.main()

