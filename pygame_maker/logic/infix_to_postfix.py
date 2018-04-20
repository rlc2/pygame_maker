#!/usr/bin/python -W all

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# convert infix token stack into postfix (aka RPN) form

# Taken from the wikipedia page describing RPN:
# https://en.wikipedia.org/wiki/Reverse_Polish_notation#Postfix_algorithm

# While there are tokens to be read:
#
#  Read a token.
#  If the token is a number, then add it to the output queue.
#  If the token is a function token, then push it onto the stack.
#  If the token is a function argument separator (e.g., a comma):
#
#   Until the token at the top of the stack is a left parenthesis, pop
#    operators off the stack onto the output queue. If no left
#    parentheses are encountered, either the separator was misplaced
#    or parentheses were mismatched.

# If the token is an operator, o1, then:
#
#  while there is an operator token, o2, at the top of the operator stack, and
#   either:
#   o1 is left-associative and its precedence is less than or equal to that of
#    o2, or
#   o1 is right associative, and has precedence less than that of o2,
#
#  then pop o2 off the operator stack, onto the output queue;
#
#  push o1 onto the operator stack.

# If the token is a left parenthesis, then push it onto the stack.
# If the token is a right parenthesis:
#
#  Until the token at the top of the stack is a left parenthesis, pop operators
#   off the stack onto the output queue.
#  Pop the left parenthesis from the stack, but not onto the output queue.
#  If the token at the top of the stack is a function token, pop it onto the
#   output queue.
#  If the stack runs out without finding a left parenthesis, then
#   there are mismatched parentheses.

# When there are no more tokens to read:
#
#  While there are still operator tokens in the stack:
#
#   If the operator token on the top of the stack is a parenthesis, then there
#    are mismatched parentheses.
#   Pop the operator onto the output queue.
#
# Exit.

import re

#: Known operators
OPERATORS = ['^', '*', '/', '%', '-', '+', 'not', '<', '<=', '>', '>=', '==', '!=', '=', 'and', 'or']
#: Operator precedence table
PRECEDENCE_TABLE = [
    ('not', 11),
    ('^', 10),
    ('*', 9), ('/', 9), ('%', 9),
    ('-', 8), ('+', 8),
    ('<', 7), ('<=', 7), ('>', 7), ('>=', 7), ('==', 7), ('!=', 7),
    ('and', 6), ('or', 6),
    ('=', 5)
]
#: Left associativity
LEFT = 0
#: Right associativity
RIGHT = 1
#: Table to keep track of operator associativity
ASSOCIATIVITY = {
    'not': RIGHT,
    '^': RIGHT,
    '*': LEFT,
    '/': LEFT,
    '%': LEFT,
    '-': LEFT,
    '+': LEFT,
    '<': LEFT,
    '<=': LEFT,
    '>': LEFT,
    '>=': LEFT,
    '==': LEFT,
    '!=': LEFT,
    'and': LEFT,
    'or': LEFT,
    '=': RIGHT
}

FLOAT_RE = re.compile("^\d+\.\d+$")
INT_RE = re.compile("^\d+$")


class ExpressionException(Exception):
    pass


def convert_infix_to_postfix(tok_list, replacement_ops=None):
    """
    Convert a list of tokens in infix notation into postfix notation.

    :param tok_list: The list of infix tokens (or a single token string)
    :type tok_list: str | list
    :param replacement_ops: Optional dict containing mappings from an infix
        operator to a postfix operator (E.G. {'+': operator.add, ...})
    :type replacement_ops: dict
    :return: A list of the tokens in postfix order
    :rtype: list
    """
    stack = []
    op_stack = []
    item_list = tok_list
    if isinstance(tok_list, str):
        item_list = [tok_list]
    for tok in item_list:
        val = None
        if isinstance(tok, str):
            minfo = FLOAT_RE.search(tok)
            if minfo:
                val = float(tok)
            else:
                minfo = INT_RE.search(tok)
                if minfo:
                    val = int(tok)
                else:
                    val = str(tok)
            if val in OPERATORS:
                while len(op_stack) > 0:
                    prec_diff = precedence_check(val, op_stack[0])
                    if (((ASSOCIATIVITY[op_stack[0]] == RIGHT) and
                        (prec_diff < 0)) or
                        ((ASSOCIATIVITY[op_stack[0]] == LEFT) and
                         (prec_diff <= 0))):
                        stack.append(op_stack[0])
                        if len(op_stack) > 1:
                            op_stack = op_stack[1:]
                        else:
                            op_stack = []
                    else:
                        break
                op_stack.insert(0, val)
            elif isinstance(val, str):
                # make sure no identifier aliases to python operators
                val = "_" + val
                stack.append(val)
            else:
                stack.append(val)
        elif len(tok) > 0:
            # @@@@ figure out what exception is thrown if len()
            #  isn't supported..
            stack = stack + convert_infix_to_postfix(tok, replacement_ops)
    while len(op_stack) > 0:
        stack.append(op_stack[0])
        if len(op_stack) > 1:
            op_stack = op_stack[1:]
        else:
            op_stack = []
    if len(op_stack) > 0:
        raise ExpressionException("Stack underflow in token list '{}'".format(tok_list))
    if replacement_ops:
        for idx in range(len(stack)):
            if stack[idx] in replacement_ops:
                stack[idx] = replacement_ops[stack[idx]]
    return stack


def precedence_check(a, b):
    """
    Sort two operators by precedence.

    :param a: First operator
    :type a: str
    :param b: Second operator
    :type b: str
    :return: negative if a has lower precedence than b, 0 if both operators
        have the same precedence, positive if a has higher precedence
    :rtype: int
    """
    prec_a = -1
    prec_b = -1
    for prec in PRECEDENCE_TABLE:
        if a == prec[0]:
            prec_a = prec[1]
        if b == prec[0]:
            prec_b = prec[1]
        if (prec_a >= 0) and (prec_b >= 0):
            break
    diff = prec_a - prec_b
    return diff
