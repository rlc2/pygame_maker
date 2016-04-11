#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker simple object instances

from object_instance import Coordinate
from pygame_maker.support import logging_object
from pygame_maker.logic.language_engine import SymbolTable


class SimpleObjectInstance(logging_object.LoggingObject):
    """
    SimpleObjectInstances wrap instances of ObjectType for use by types without
    sprites.

    The most useful features of this class is allowing the logic engine to
    access symbols, and supporting variable and code execution type actions.
    """
    def __init__(self, kind, screen_dims, id_, settings=None, **kwargs):
        super(SimpleObjectInstance, self).__init__(type(self).__name__)
        #: The ObjectType this ObjectInstance belongs to
        self.kind = kind
        #: Keep a handle to the game engine for handling certain actions
        self.game_engine = kind.game_engine
        #: Keep track of the screen boundaries for collision detection
        self.screen_dims = list(screen_dims)
        # Unique ID for this SimpleObjectInstance
        self.inst_id = id_
        self._symbols = {
            "position": Coordinate(0, 0,
                                   self._update_position_x,
                                   self._update_position_y)
        }
        if settings:
            self._symbols.update(settings)
        self._symbols.update(kwargs)
        #: Symbol table
        self.symbols = SymbolTable()
        for sym in self._symbols.keys():
            self.symbols[sym] = self._symbols[sym]

        self.action_name_to_method_map = {
            'execute_code': self.execute_code,
            'if_variable_value': self.if_variable_value,
            'set_variable_value': self.set_variable_value,
        }
        self._code_block_id = 0

    def _update_position_x(self):
        # Automatically called when the X coordinate of the position changes
        self.debug("_update_position_x():")
        self._round_position_x_to_rect_x()
        self.symbols['position.x'] = self.position.x

    def _update_position_y(self):
        # Automatically called when the Y coordinate of the position changes
        self.debug("_update_position_y():")
        self._round_position_y_to_rect_y()
        self.symbols['position.y'] = self.position.y

    def execute_code(self, action, keep_code_block=True):
        """
        Handle the execute_code action.

        Puts local variables into the symbols attribute, which is a symbol
        table. Applies any built-in local variable changes for the instance.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        :param keep_code_block: Specify whether the code block will be re-used,
            and so shouldn't be deleted after execution
        :type keep_code_block: bool
        """
        self.debug("execute_code(action={}, keep_code_block={}):".format(action,
                                                                         keep_code_block))
        if len(action.action_data['code']) > 0:
            instance_handle_name = "obj_{}_block{}".format(self.kind.name, self.code_block_id)
            if 'language_engine_handle' not in action.runtime_data:
                action['language_engine_handle'] = instance_handle_name
                # print("action {} runtime: '{}'".format(action, action.runtime_data))
                self.game_engine.language_engine.register_code_block(
                    instance_handle_name, action.action_data['code']
                )
            local_symbols = SymbolTable(self.symbols, lambda s, v: self._symbol_change_callback(s, v))
            self.debug("{} inst {} syms before code block: {}".format(self.kind.name,
                                                                      self.inst_id,
                                                                      local_symbols.vars))
            self.game_engine.language_engine.execute_code_block(
                action['language_engine_handle'], local_symbols
            )
            self.debug("  syms after code block: {}".format(local_symbols.vars))
            if not keep_code_block:
                # support one-shot actions
                self.game_engine.language_engine.unregister_code_block(
                    action['language_engine_handle']
                )
                del(action.runtime_data['language_engine_handle'])

    def if_variable_value(self, action):
        """
        Handle the if_variable_value action.

        Makes use of both the local symbol table in self.symbols, and the
        global symbol table managed by the language engine.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        """
        self.debug("if_variable_value(action={}):".format(action))
        # look in symbol tables for the answer, local table first
        var_val = self.symbols.DEFAULT_UNINITIALIZED_VALUE
        test_result = False
        if action['variable'] in self.symbols.keys():
            var_val = self.symbols[action['variable']]
        elif action['variable'] in self.game_engine.language_engine.global_symbol_table.keys():
            var_val = self.game_engine.language_engine.global_symbol_table[action['variable']]
        if action['test'] == "equals":
            if var_val == action['value']:
                test_result = True
        if action['test'] == "not_equals":
            if var_val == action['value']:
                test_result = True
        if action['test'] == "less_than_or_equals":
            if var_val <= action['value']:
                test_result = True
        if action['test'] == "less_than":
            if var_val < action['value']:
                test_result = True
        if action['test'] == "greater_than_or_equals":
            if var_val >= action['value']:
                test_result = True
        if action['test'] == "greater_than":
            if var_val > action['value']:
                test_result = True
        self.debug("  {} inst {}: if {} {} {} is {}".format(self.kind.name,
                                                            self.inst_id, action['variable'], action['test'],
                                                            action['value'],
                                                            test_result))
        action.action_result = test_result

    def set_variable_value(self, action):
        """
        Handle the set_variable_value action.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        """
        self.debug("set_variable_value(action={}):".format(action))
        if action['is_global']:
            value_result = action.get_parameter_expression_result('value',
                                                                  self.game_engine.language_engine.global_symbol_table,
                                                                  self.game_engine.language_engine)
            self.debug("  {} inst {}: set global var {} to {}".format(self.kind.name,
                                                                      self.inst_id,
                                                                      action['variable'],
                                                                      value_result))
            self.game_engine.language_engine.global_symbol_table[action['variable']] = value_result
        else:
            value_result = action.get_parameter_expression_result('value',
                                                                  self.symbols, self.game_engine.language_engine)
            self.debug("  {} inst {}: set local var '{}' to {}".format(self.kind.name,
                                                                       self.inst_id,
                                                                       action['variable'],
                                                                       value_result))
            self.symbols[action['variable']] = value_result

    def execute_action(self, action, event):
        """
        Perform an action in an action sequence, in response to an event.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        :param event: The Event instance that triggered this method
        :type event: :py:class:`~pygame_maker.events.event.Event`
        """
        # Apply any setting names that match property names found in the
        #  action_data.  For some actions, this is enough.
        # common exceptions:
        #  apply_to: assumed to have directed the action to this instance
        #  relative: add to instead of replace property settings
        self.debug("execute_action(action={}, event={}):".format(action, event))
        action_params = {}
        # check for expressions that need to be executed
        for param in action.action_data.keys():
            if param == 'apply_to':
                continue
            action_params[param] = action.get_parameter_expression_result(
                param, self.symbols, self.game_engine.language_engine)
        if action.name in self.action_name_to_method_map.keys():
            self.action_name_to_method_map[action.name](action)
        else:
            self.debug("  {} inst {} execute_action {} fell through..".format(self.kind.name,
                                                                              self.inst_id,
                                                                              action.name))

    def __repr__(self):
        return "<{} {:03d}>".format(type(self).__name__, self.inst_id)
