"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Pygame maker simple object instances
"""

import re
import math
import pygame
import pygame_maker.events.event as event
from pygame_maker.support import coordinate
from pygame_maker.support import logging_object
from pygame_maker.logic.language_engine import SymbolTable


class SimpleObjectInstance(logging_object.LoggingObject):
    """
    SimpleObjectInstances wrap instances of ObjectType for use by types without
    sprites.

    The most useful features of this class is allowing the logic engine to
    access symbols, and supporting variable and code execution type actions.
    """
    INSTANCE_SYMBOLS = {}
    # Regex for searching for symbol interpolations in debug strings
    INTERPOLATION_REGEX = re.compile("{([^}]*)}")

    def __init__(self, kind, screen_dims, new_id, settings=None, **kwargs):
        """
        Initialize a SimpleObjectInstance.

        :param kind: The object type of this new instance
        :type kind: :py:class:`~pygame_maker.actors.object_type.ObjectType`
        :param screen_dims: Width, height of the surface this instance will be
            drawn to.  Allows boundary collisions to be detected.
        :type screen_dims: [int, int]
        :param new_id: A unique integer ID for this instance
        :type new_id: int
        :param settings: Used along with kwargs for settings attributes
            (allows attributes to be set that have a '.' character, which
            cannot be set in kwargs).  Known attributes are the same as for
            kwargs.
        :type settings: None or dict
        :param kwargs:
            Supply alternatives to instance attributes

            * position (list of float or pygame.Rect): Upper left XY coordinate.
              If not integers, each will be rounded to the next highest
              integer [(0,0)]

        """
        # call base class init
        super(SimpleObjectInstance, self).__init__(type(self).__name__)
        #: Name the instance based on the ObjectType's name and the ID
        self.name = "{}{}".format(kind.name, new_id)
        #: The ObjectType this SimpleObjectInstance belongs to
        self.kind = kind
        #: Keep a handle to the game engine for handling certain actions
        self.game_engine = kind.game_engine
        #: Keep track of the screen boundaries for collision detection
        self.screen_dims = list(screen_dims[0:2])
        #: Unique ID for this SimpleObjectInstance
        self.inst_id = new_id
        # rect for storing the instance's position
        self.rect = pygame.Rect(0, 0, 0, 0)
        # Symbols tracked by ObjectInstances
        self._symbols = {
            "parent": None,
            "children": [],
            "position": coordinate.Coordinate(0, 0,
                                              self._update_position_x,
                                              self._update_position_y)
        }
        #: Subclasses override this class variable to add their known symbols
        self._symbols.update(self.INSTANCE_SYMBOLS)
        #: Symbol table
        self.symbols = SymbolTable()
        for sym in self._symbols.keys():
            self.symbols[sym] = self._symbols[sym]

        attr_values = {}
        if settings is not None:
            attr_values.update(settings)
        attr_values.update(kwargs)
        if len(attr_values.keys()) > 0:
            self._apply_kwargs(attr_values)
        # print("Initial symbols:")
        # self.symbols.dumpVars()

        self.action_name_to_method_map = {
            'debug': self.print_debug,
            'execute_code': self.execute_code,
            'if_variable_value': self.if_variable_value,
            'set_variable_value': self.set_variable_value,
            'destroy_object': self.destroy_object,
        }
        self._code_block_id = 0

    def _update_position_x(self):
        # Automatically called when the X coordinate of the position changes
        self.debug("_update_position_x():")
        self._round_position_x_to_rect_x()
        #pylint: disable=no-member
        self.symbols['position.x'] = self.position.x
        #pylint: enable=no-member

    def _update_position_y(self):
        # Automatically called when the Y coordinate of the position changes
        self.debug("_update_position_y():")
        self._round_position_y_to_rect_y()
        #pylint: disable=no-member
        self.symbols['position.y'] = self.position.y
        #pylint: enable=no-member

    def _round_position_x_to_rect_x(self):
        # Called when the x coordinate of the position changes, to round
        # the floating-point value to the nearest integer and place it
        # in rect.x for the draw() method.
        self.debug("_round_position_x_to_rect_x():")
        #pylint: disable=no-member
        self.rect.x = math.floor(self.position.x + 0.5)
        #pylint: enable=no-member

    def _round_position_y_to_rect_y(self):
        # _round_position_y_to_rect_y():
        #  Called when the y coordinate of the position changes, to round
        #  the floating-point value to the nearest integer and place it
        #  in rect.y for the draw() method.
        self.debug("_round_position_y_to_rect_y():")
        #pylint: disable=no-member
        self.rect.y = math.floor(self.position.y + 0.5)
        #pylint: enable=no-member

    @property
    def code_block_id(self):
        """Return a unique code block id."""
        self._code_block_id += 1
        return self._code_block_id

    @property
    def position(self):
        """Position of this instance.  Set a new position using an x, y list."""
        return self.symbols['position']

    @position.setter
    def position(self, new_coord):
        if len(new_coord) >= 2:
            self.debug("Set {}'s position to {}".format(self.name, new_coord))
            self.symbols['position'].x = new_coord[0]
            self.symbols['position'].y = new_coord[1]

    def _apply_kwargs(self, kwargs):
        # Apply the kwargs dict mappings to the instance's properties.

        # Any keys that don't refer to built-in properties (speed, direction,
        # etc) will instead be tracked in the local symbol table to support
        # code execution actions.
        # Parameters themselves can have attributes up to 1 level, to support
        #     position.x and position.y

        # :param kwargs: A dictionary containing the new attributes to be
        #     applied
        # :type kwargs: dict
        self.debug("_apply_kwargs(kwargs={}):".format(str(kwargs)))
        relative = False
        if "relative" in kwargs.keys():
            relative = kwargs["relative"]
        for kwarg in kwargs.keys():
            if kwarg == 'relative':
                # 'relative' is not an attribute, it instead determines how the
                #  other attributes are applied.
                continue
            # Attributes can themselves have attributes, but only 1 level deep
            # is currently supported.  This facilitates setting the position.x
            #  and position.y attributes.
            attrs = kwarg.split('.')
            if hasattr(self, attrs[0]):
                new_val = kwargs[kwarg]
                if len(attrs) == 1:
                    old_val = getattr(self, kwarg)
                    if relative:
                        new_val += getattr(self, kwarg)
                    if new_val != old_val:
                        setattr(self, kwarg, new_val)
                elif len(attrs) == 2:
                    main_attr = getattr(self, attrs[0])
                    old_val = getattr(main_attr, attrs[1])
                    if relative:
                        new_val += old_val
                    if new_val != old_val:
                        setattr(main_attr, attrs[1], new_val)
            else:
                # keep track of local symbols created by code blocks
                self.symbols[kwarg] = kwargs[kwarg]

    def _symbol_change_callback(self, sym, new_value):
        # Callback for the SymbolTable.

        # Called whenever a symbol changes while running the language engine.

        # :param sym: The symbol's name
        # :type sym: str
        # :param new_value: The symbol's new value
        self.debug("_symbol_change_callback(sym={}, new_value={}):".format(sym,
                                                                           new_value))
        handled_change = False
        if hasattr(self, sym):
            setattr(self, sym, new_value)
            handled_change = True
        elif sym == 'position.x':
            self.position.x = new_value
            handled_change = True
        elif sym == 'position.y':
            self.position.y = new_value
            handled_change = True
        return handled_change

    def execute_code(self, action, keep_code_block=True):
        """
        Handle the execute_code action.

        Puts local variables into the symbols attribute, which is a symbol
        table.  Applies any built-in local variable changes for the instance.

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
            local_symbols = SymbolTable(self.symbols,
                                        lambda s, v: self._symbol_change_callback(s, v))
            # future: allow references to this instance in user code (E.G. set
            #  as parent, add as child instance).
            local_symbols.set_constant("self", self)
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
                del action.runtime_data['language_engine_handle']

    def print_debug(self, action):
        """
        Handle the debug action.

        Debug messages are treated as format strings, where {symbol} will be
        replaced with actual values from the symbol tables.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        """
        message_parts = ["DEBUG FROM {} instance #{}: ".format(self.kind.name, self.inst_id)]
        if len(action['message']) > 0:
            interpolations = self.INTERPOLATION_REGEX.findall(action['message'])
            msg_str = action['message']
            if len(interpolations) > 0:
                inter_set = set(interpolations)
                for inter in inter_set:
                    inter_str = "{" + inter + "}"
                    rstr = "UNKNOWN"
                    if inter in self.symbols.keys():
                        rstr = self.symbols[inter]
                    elif inter in self.game_engine.language_engine.global_symbol_table.keys():
                        rstr = self.game_engine.language_engine.global_symbol_table[inter]
                    msg_str = re.sub(inter_str, str(rstr), msg_str)
            message_parts.append(msg_str)
        else:
            message_parts.append("\nlocal symbol table entries:\n")
            for lsym in self.symbols.keys():
                if lsym in ["parent", "children", "position"]:
                    continue
                message_parts.append("\t{:30s} = {:30s}\n".format(lsym, str(self.symbols[lsym])))
            message_parts.append("global symbol table entries:\n")
            for gsym in self.game_engine.language_engine.global_symbol_table.keys():
                if gsym in ["pi", "e"]:
                    continue
                symname = str(self.game_engine.language_engine.global_symbol_table[gsym])
                message_parts.append("\t{:30s} = {:30s}\n".format(gsym, symname))
        print "".join(message_parts)

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
        test_val = action['value']
        test_result = False
        if action['variable'] in self.symbols.keys():
            var_val = self.symbols[action['variable']]
        elif action['variable'] in self.game_engine.language_engine.global_symbol_table.keys():
            var_val = self.game_engine.language_engine.global_symbol_table[action['variable']]
        if isinstance(action['value'], str):
            # replace a string with a symbol value, if the string is in a symbol table
            if action['value'] in self.symbols.keys():
                test_val = self.symbols[action['value']]
            elif action['value'] in self.game_engine.language_engine.global_symbol_table.keys():
                test_val = self.game_engine.language_engine.global_symbol_table[action['value']]
        if action['test'] == "equals":
            test_result = (var_val == test_val)
        if action['test'] == "not_equals":
            test_result = (var_val != test_val)
        if action['test'] == "less_than_or_equals":
            test_result = (var_val <= test_val)
        if action['test'] == "less_than":
            test_result = (var_val < test_val)
        if action['test'] == "greater_than_or_equals":
            test_result = (var_val >= test_val)
        if action['test'] == "greater_than":
            test_result = (var_val > test_val)
        self.debug("  {} inst {}: if {} {} {} is {}".format(self.kind.name, self.inst_id,
                                                            action['variable'],
                                                            action['test'],
                                                            test_val, test_result))
        # update the action's action_result attribute, so that the
        # action sequence can choose the right conditional path
        action.action_result = test_result

    def set_variable_value(self, action):
        """
        Handle the set_variable_value action.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        """
        self.debug("set_variable_value(action={}):".format(action))
        gsymtable = self.game_engine.language_engine.global_symbol_table
        if action['is_global']:
            value_result = action.get_parameter_expression_result('value',
                                                                  gsymtable,
                                                                  self.game_engine.language_engine)
            self.debug("  {} inst {}: set global var {} to {}".format(self.kind.name,
                                                                      self.inst_id,
                                                                      action['variable'],
                                                                      value_result))
            self.game_engine.language_engine.global_symbol_table[action['variable']] = value_result
        else:
            value_result = action.get_parameter_expression_result('value', self.symbols,
                                                                  self.game_engine.language_engine)
            self.debug("  {} inst {}: set local var '{}' to {}".format(self.kind.name,
                                                                       self.inst_id,
                                                                       action['variable'],
                                                                       value_result))
            self.symbols[action['variable']] = value_result

    def set_parent_instance(self, parent):
        """
        Set or replace this instance's parent, for forwarding 'child' events.
        """
        if not isinstance(parent, SimpleObjectInstance):
            self.warn("set_parent_instance() passed non-instance '{}'".format(parent))
            return
        # if this instance already has a parent, remove it from the parent's child instances
        if self.symbols["parent"] is not None:
            #pylint: disable=no-member
            self.symbols["parent"].remove_child_instance(self)
            #pylint: enable=no-member
        # add this instance as a child of the new parent
        parent.add_child_instance(self)
        self.symbols["parent"] = parent

    def remove_parent_instance(self):
        """Remove the parent instance, for example when it is destroyed"""
        self.debug("remove_parent_instance():")
        self.symbols["parent"] = None

    def add_child_instance(self, child):
        """Add a child instance to this one, for forwarding 'parent' events"""
        if not isinstance(child, SimpleObjectInstance):
            self.warn("add_child_instance() passed non-instance '{}'".format(child))
            return
        self.debug("add_child_instance(child={} inst {}):".format(child.kind.name, child.inst_id))
        #pylint: disable=unsupported-membership-test
        if child not in self.symbols["children"]:
            #pylint: enable=unsupported-membership-test
            #pylint: disable=no-member
            self.symbols["children"].append(child)
            #pylint: enable=no-member
        else:
            self.info("add_child_instance() called with already existing child instance")

    def remove_child_instance(self, child):
        """
            Remove a child instance from this one, to disconnect it from
            'parent' events
        """
        if not isinstance(child, SimpleObjectInstance):
            self.warn("add_child_instance() passed non-instance '{}'".format(child))
            return
        self.debug("remove_child_instance(child={} inst {}):".
                   format(child.kind.name, child.inst_id))
        #pylint: disable=unsupported-membership-test
        if child in self.symbols["children"]:
            #pylint: enable=unsupported-membership-test
            #pylint: disable=no-member
            self.symbols["children"].remove(child)
            #pylint: enable=no-member
        else:
            self.info("remove_child_instance() called with non-existent child instance")

    def destroy_object(self, action, no_destroy_event=False):
        """
            Queue and transmit the destroy event for this instance, then
            schedule it for removal from its object type.

            Also handles parent and child connections, sending "destroy_child"
            events to parent instances, and destroy any child instances.
            Remove any remaining references to the instance so it can be GC'd.
        """
        self.debug("destroy_object(action={}):".format(action))
        self.game_engine.event_engine.queue_event(
            event.ObjectStateEvent("destroy", {"type": self.kind, "instance": self})
        )
        if len(self.symbols["children"]) > 0:
            # destroy all child instances
            #pylint: disable=not-an-iterable
            for child_instance in self.symbols["children"]:
                #pylint: enable=not-an-iterable
                # no need to queue destroy_child events for ourself..
                child_instance.remove_parent_instance()
                child_instance.destroy_object(action, True)
        # break connection with parent (if any)
        if self.symbols["parent"] is not None:
            parent = self.symbols["parent"]
            # queue destroy_child event to parent instance
            #pylint: disable=no-member
            new_ev = event.ObjectStateEvent("destroy_child", {"type": parent.kind,
                                                              "instance": parent,
                                                              "child_type": self.kind})
            #pylint: enable=no-member
            self.game_engine.event_engine.queue_event(new_ev)
            #pylint: disable=no-member
            parent.remove_child_instance(self)
            #pylint: enable=no-member
            self.game_engine.event_engine.transmit_event("destroy_child")
        if not no_destroy_event:
            # only transmit the event once; child instances can skip this
            self.game_engine.event_engine.transmit_event("destroy")
        self.kind.add_instance_to_delete_list(self)

    def execute_action(self, action, an_event):
        """
        Perform an action in an action sequence, in response to an event.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        :param an_event: The Event instance that triggered this method
        :type an_event: :py:class:`~pygame_maker.events.event.Event`
        :return: A tuple containing the action parameters (``apply_to`` will
            be filtered out), and True/False based on whether the action was
            handled here in the base class or not.
        :rtype: (dict, bool)
        """
        # Apply any setting names that match property names found in the
        #  action_data.  For some actions, this is enough.
        # common exceptions:
        #  apply_to: assumed to have directed the action to this instance
        #  relative: add to instead of replace property settings
        self.debug("execute_action(action={}, an_event={}):".format(action, an_event))
        action_params = {}
        handled_action = False
        # check for expressions that need to be executed
        for param in action.action_data.keys():
            if param == 'apply_to':
                continue
            action_params[param] = action.get_parameter_expression_result(
                param, self.symbols, self.game_engine.language_engine)
        if action.name in self.action_name_to_method_map.keys():
            self.action_name_to_method_map[action.name](action)
            handled_action = True
            self.debug("  {} inst {} execute_action {} handled".format(self.kind.name,
                                                                       self.inst_id,
                                                                       action.name))
        return (action_params, handled_action)

    def __repr__(self):
        return "<{} {:03d}>".format(type(self).__name__, self.inst_id)
