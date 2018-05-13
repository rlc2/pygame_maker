"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Support module for code block generation.
"""

import random
import time
import sys

#: The default value used for uninitialized symbols
DEFAULT_UNINITIALIZED_VALUE = -sys.maxsize - 1


class CodeBlockRuntimeError(RuntimeError):
    """Raised when errors are encountered in code blocks at run time."""
    pass


def update_symbol(_symbols, symname, value):
    """
    Define the update_symbol function that changes symbol values (or creates
    new symbols) in generated code blocks.

    :param _symbols: The symbols dict containing ``locals`` and ``globals``
        keys, which each point to a :py:class:`SymbolTable`
    :type _symbols: dict
    :param symname: The symbol name to look up
    :type symname: str
    :param value: The symbol's new value
    """
    if symname[0] == "_":
        _symbols["globals"][symname[1:]] = value
    else:
        if symname in list(_symbols["locals"].keys()) or symname not in list(_symbols["globals"].keys()):
            _symbols["locals"][symname] = value
        else:
            _symbols["globals"][symname] = value


def get_symbol(_symbols, symname):
    """
    Define the get_symbol function that retrieves symbol values in generated
    code blocks.

    Always return a value, even if the symbol name is unknown, in which case
    the unitialized value will be returned.

    :param _symbols: The symbols dict containing ``locals`` and ``globals``
        keys, which each point to a :py:class:`SymbolTable`
    :type _symbols: dict
    :param symname: The symbol name to look up
    :type symname: str
    :return: The symbol's value
    """
    symval = DEFAULT_UNINITIALIZED_VALUE
    if symname in list(_symbols["locals"].keys()):
        # local variables can override globals
        symval = _symbols["locals"][symname]
    elif symname in list(_symbols["globals"].keys()):
        symval = _symbols["globals"][symname]
    return symval


def userfunc_distance(_symbols, start, end, count=0):
    """
    Make a ``distance`` function that calculates the distance between two
    values available to game language code.

    :param _symbols: The symbols dict
    :type _symbols: dict
    :param start: First value
    :type start: Number
    :param end: Second value
    :type end: Number
    :return: The absolute value of the difference between start and end
    """
    return abs(start - end)


def userfunc_randint(_symbols, max_int, count=0):
    """
    Make a ``randint`` function that creates a random integer available to game
    language code.

    Return a negative int less than the specified maximum value and greater
    than or equal to 0.  If the specified maximum value is negative, a negative
    integer between 0 and the maximum will be returned.

    :param _symbols: The symbols dict
    :type _symbols: dict
    :param max_int: The maximum integer value (returned values will always be
        less than ``max_int``, or greater if ``max_int`` is negative)
    :type max_int: Number
    :return: A new random integer
    """
    randrange = max_int
    if max < 0:
        randrange = abs(max_int)
    val = random.randint(0, randrange)
    if max < 0:
        val *= -1
    return val


def userfunc_time(_symbols, count=0):
    """
    Make a ``time`` function that returns the current number of seconds since
    the Epoch available to game language code.

    :param _symbols: The symbols dict
    :type _symbols: dict
    :return: The integer portion of the number of seconds since the Epoch
    :rtype: int
    """
    return int(time.time())

def userfunc_debug(_symbols, debug_str, count=0):
    """
    Make a ``debug`` function that displays a string to stderr.

    :param _symbols: The symbols dict
    :type _symbols: dict
    """
    sys.stderr.write("{}\n".format(debug_str))
    return debug_str
