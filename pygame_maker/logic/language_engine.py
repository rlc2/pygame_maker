"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Language engine classes.
"""

import imp
import math
import sys
import pygame_maker.support.logging_object as logging_object
from pygame_maker.logic.code_block import CodeBlockGenerator


class DuplicateCodeBlockError(logging_object.LoggingException):
    """Raised when a duplicate code block name is found."""
    pass


class UnknownCodeBlockError(logging_object.LoggingException):
    """Raised when an unknown code block name is executed."""
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


class LanguageEngine(logging_object.LoggingObject):
    """
    Interpret, initialize, and execute code blocks.  Requires managing tables
    of variables and functions that can be accessed by and/or created within
    the code block.
    """

    #: A dict containing known function signatures
    functionmap = {
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
        'debug': {"arglist":
                  [{"type": "string", "name": "debug_str"}],
                  'block': []
                 }
    }
    #: A list of user-callable action methods.
    action_methods = []

    @classmethod
    def add_new_function_call(cls, function_name, arg_list):
        """
        Add new function_name that can be called by user code.  Used mainly
        by Action for registering actions as function calls.

        :param function_name: A function name not already in the table.
        :type function_name: str
        :param arg_list: A list of dicts containing type and argument name
            info, E.G. [{"type": "string", "name": "apply_to"}, ...]
        :type arg_list: list
        """
        if function_name not in cls.functionmap.keys():
            cls.functionmap[function_name] = {"arglist": arg_list, "block": []}
            cls.action_methods.append(function_name)

    def __init__(self):
        """
        Initialize a new language engine.
        """
        super(LanguageEngine, self).__init__(type(self).__name__)
        #: The language engine's global symbol table
        self.global_symbol_table = SymbolTable()
        self.global_symbol_table.set_constant('pi', math.pi)
        self.global_symbol_table.set_constant('e', math.e)
        #: Code blocks registered in the language engine
        self.code_blocks = {}

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
            raise DuplicateCodeBlockError("Attempt to register another code block named '{}':\n{}".
                                          format(block_name, self.error))
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
            raise UnknownCodeBlockError("Attempt to execute unknown code block named '{}':\n{}".
                                        format(block_name, self.error))
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
