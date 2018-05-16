#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test the pygame_maker.logic.infix_to_postfix module.
"""

import unittest
from pygame_maker.logic.infix_to_postfix import convert_infix_to_postfix


class InfixToPostfixTest(unittest.TestCase):
    """Unit tests for the infix_to_postfix module."""

    def setUp(self):
        self.replacement_table = {
            "+": "operator.add",
            "-": "operator.sub",
            "*": "operator.mul",
            "/": "operator.truediv",
            "%": "operator.mod",
            "^": "math.pow",
            ">": "operator.gt",
            "==": "operator.eq",
            "not": "operator.not_"
        }

    def test_005simple_sequence(self):
        """Test a simple series of binary operators."""
        tok_list = ['a', '+', '1', '*', '2', '^', '32', '-', '4']
        postfix = convert_infix_to_postfix(tok_list)
        expected = ['_a', 1, 2, 32, '^', '*', '+', 4, '-']
        self.assertEqual(expected, postfix)

    def test_010parenthesis(self):
        """Test a series of binary operators that includes parens."""
        tok_list = [['a', '+', '1'], '*', '2', '^', ['32', '-', '4']]
        postfix = convert_infix_to_postfix(tok_list)
        expected = ['_a', 1, '+', 2, 32, 4, '-', '^', '*']
        self.assertEqual(expected, postfix)

    def test_015replacements(self):
        """Test conversion of operator symbols to replacement strings."""
        tok_list = [['a', '+', '1'], '*', '2', '^', ['32', '-', '4']]
        postfix = convert_infix_to_postfix(tok_list, self.replacement_table)
        expected = ['_a', 1, 'operator.add', 2, 32, 4, 'operator.sub',
                    'math.pow', 'operator.mul']
        self.assertEqual(expected, postfix)

    def test_020boolean(self):
        """Test proper placement of boolean operators 'not' and 'or'."""
        tok_list = ['not', ['a', '>', '1'], 'or', ['a', '==', '4']]
        postfix = convert_infix_to_postfix(tok_list, self.replacement_table)
        expected = ['_a', 1, 'operator.gt', 'operator.not_', '_a', 4,
                    'operator.eq', 'or']
        self.assertEqual(expected, postfix)

unittest.main()
