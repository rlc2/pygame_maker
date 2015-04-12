#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# container type for sequences of actions

import pygame
import re
import weakref
import pygame_maker_action as pygm_action

class PyGameMakerEventActionSequenceStatementException(Exception):
    pass

class PyGameMakerEventActionSequenceStatement(object):
    @staticmethod
    def get_sequence_item_from_action(action):
        if (action.nest_adjustment):
            if action.name == "else":
                return PyGameMakerEventActionSequenceConditionalElse(action)
            minfo = pygm_action.PyGameMakerAction.IF_STATEMENT_RE.search(action.name)
            if minfo:
                return PyGameMakerEventActionSequenceConditionalIf(action)
            if action.nest_adjustment != "block_end":
                return PyGameMakerEventActionSequenceBlock(action)
        return PyGameMakerEventActionSequenceStatement(action)

    def __init__(self, action):
        self.is_block = False
        self.is_conditional = False
        self.action = action

    def get_action_list(self):
        return [self.action]

    def pretty_print(self, indent=0):
        indent_string = "\t" * indent
        print("{}{}".format(indent_string, self.action.name))

    def __repr__(self):
        return "<{}: {}>".format(type(self).__name__, self.action)

class PyGameMakerEventActionSequenceConditional(PyGameMakerEventActionSequenceStatement):
    def __init__(self, action):
        PyGameMakerEventActionSequenceStatement.__init__(self, action)
        self.is_conditional = True
        self.contained_statement = None

    def add_statement(self, statement):
        """
            Given a statement, try to add it to the current if block. If the
            if clause is empty, set its statement. If the if clause holds an
            open block, add it to the block. Otherwise, try the same steps with
            the else clause.
            Returns True if there was a place for the new statement, otherwise
            returns False.
        """
        found_place = True
        if not isinstance(statement, PyGameMakerEventActionSequenceStatement):
            raise(PyGameMakerEventActionSequenceStatementException("{} is not a PyGameMakerEventActionSequenceStatement".format(statement)))
        if not self.contained_statement:
            self.contained_statement = statement
        elif (self.contained_statement.is_block and
            not self.contained_statement.is_block_closed):
            self.contained_statement.add_statement(statement)
        elif (self.contained_statement.is_conditional and
            self.contained_statement.add_statement(statement)):
            # the contained conditional found a place for the statement
            pass
        else:
            found_place = False
        return found_place

    def set_statement(self, statement):
        if not isinstance(statement, PyGameMakerEventActionSequenceStatement):
            raise(PyGameMakerEventActionSequenceStatementException("{} is not a PyGameMakerEventActionSequenceStatement".format(statement)))
        if self.contained_statement:
            raise(PyGameMakerEventActionSequenceStatementException("{}: already contains a statement".format(self.action)))
        self.contained_statement = statement

    def get_action_list(self):
        contained_list = []
        if self.contained_statement:
            contained_list = self.contained_statement.get_action_list()
        return [self.action] + contained_list

    def pretty_print(self, indent=0):
        PyGameMakerEventActionSequenceStatement.pretty_print(self, indent)
        if self.contained_statement:
            self.contained_statement.pretty_print(indent+1)

    def __repr__(self):
        repr = "<{}:\n".format(type(self).__name__)
        repr += "\t{}>".format(self.contained_statement)
        return repr

class PyGameMakerEventActionSequenceConditionalIf(PyGameMakerEventActionSequenceConditional):
    def __init__(self, action):
        PyGameMakerEventActionSequenceConditional.__init__(self, action)
        self.else_condition = None

    def add_else(self, else_statement):
        if not isinstance(else_statement, PyGameMakerEventActionSequenceConditionalElse):
            raise(PyGameMakerEventActionSequenceStatementException("{} is not a PyGameMakerEventActionSequenceConditionalElse".format(else_statement)))
        if self.else_condition:
            raise(PyGameMakerEventActionSequenceStatementException("{}: already contains an else clause".format(self.action)))
        self.else_condition = else_statement

    def add_statement(self, statement):
        found_place = True
        if not PyGameMakerEventActionSequenceConditional.add_statement(self,
            statement):
            if (not self.else_condition and
                isinstance(statement,
                PyGameMakerEventActionSequenceConditionalElse)):
                self.else_condition = statement
            elif (self.else_condition and self.else_condition.is_conditional and
                self.else_condition.add_statement(statement)):
                # else clause had a place for the new statement
                pass
            elif (self.else_condition and self.else_condition.is_block and
                not self.else_condition.is_block_closed):
                self.else_condition.add_statement(statement)
            else:
                found_place = False
        return found_place

    def pretty_print(self, indent=0):
        PyGameMakerEventActionSequenceConditional.pretty_print(self, indent)
        if self.else_condition:
            self.else_condition.pretty_print(indent)

    def get_action_list(self):
        contained_list = PyGameMakerEventActionSequenceConditional.get_action_list(self)
        else_list = []
        if self.else_condition:
            else_list = self.else_condition.get_action_list()
        return contained_list + else_list

    def __repr__(self):
        repr = "<{} {}:\n".format(type(self).__name__, self.action)
        repr += "\t{}\n".format(self.contained_statement)
        if self.else_condition:
            repr += "{}>".format(self.else_condition)
        return repr

class PyGameMakerEventActionSequenceConditionalElse(PyGameMakerEventActionSequenceConditional):
    def __init__(self, action):
        PyGameMakerEventActionSequenceConditional.__init__(self, action)

class PyGameMakerEventActionSequenceBlock(PyGameMakerEventActionSequenceStatement):
    def __init__(self, action, main_block=False):
        # main block doesn't start with an explicit action, so action==None
        #  is ok. Remember this when trying to use self.action in any
        #  methods, including superclasses!
        PyGameMakerEventActionSequenceStatement.__init__(self, action)
        self.is_block = True
        self.is_block_closed = False
        self.contained_statements = []
        self.main_block = main_block

    def append_statement(self, statement):
        # the main block is never explicitly "closed"
        if statement.action and statement.action.nest_adjustment == "block_end":
            if not self.main_block:
                self.is_block_closed = True
                self.contained_statements.append(statement)
            else:
                raise(PyGameMakerEventActionSequenceStatementException("block_end cannot be added to a main block"))
        else:
            self.contained_statements.append(statement)

    def add_statement(self, statement):
        #print("Adding statement: {} .. ".format(statement))
        if not isinstance(statement, PyGameMakerEventActionSequenceStatement):
            raise(PyGameMakerEventActionSequenceStatementException("{} is not a PyGameMakerEventActionSequenceStatement".format(statement)))
        last_statement = None
        if len(self.contained_statements) > 0:
            last_statement = self.contained_statements[-1]
        if last_statement and last_statement.is_conditional:
            # If the last statement's conditional is still open, this statement
            #  belongs there. Otherwise, add it to this block
            if last_statement.add_statement(statement):
                #print("---> to last conditional")
                return
        if last_statement and last_statement.is_block:
            # If the last statement's block is still open, this statement
            #  belongs there. Otherwise, add it to this block
            if not last_statement.is_block_closed:
                #print("---> to last block")
                last_statement.add_statement(statement)
                return
        #print("---> to current block")
        self.append_statement(statement)

    def get_action_list(self):
        this_action = []
        if not self.main_block:
            this_action = [self.action]
        contained_list = []
        if self.contained_statements:
            for contained in self.contained_statements:
                contained_list += contained.get_action_list()
        return this_action + contained_list

    def pretty_print(self, indent=0):
        new_indent = indent
        if not self.main_block:
            PyGameMakerEventActionSequenceStatement.pretty_print(self,indent)
            new_indent += 1
        if self.contained_statements:
            for contained in self.contained_statements:
                if contained.action.nest_adjustment != "block_end":
                    contained.pretty_print(new_indent)
                else:
                    contained.pretty_print(indent)

    def __repr__(self):
        repr = "<{}:\n".format(type(self).__name__)
        for statement in self.contained_statements:
            repr += "{}\n".format(statement)
        repr += ">"
        return repr

class PyGameMakerEventActionSequence(object):
    """
        Store a list of the actions that are triggered by an event
    """
    # tuple indices
    ACTION_IDX=0
    NEST_IDX=1
    BLOCK_IDX=2

    def __init__(self):
        """
            main_block: the container for the top-level statements
        """
        self.main_block = PyGameMakerEventActionSequenceBlock(None, True)

    def append_action(self, action):
        """
            Add a new action to the end of the list
        """
        statement = PyGameMakerEventActionSequenceStatement.get_sequence_item_from_action(action)
        self.main_block.add_statement(statement)

    def __repr__(self):
        return("{}".format(self.main_block))

if __name__ == "__main__":
    import unittest

    class TestPyGameMakerObject(unittest.TestCase):

        def setUp(self):
            pass

        def test_005build_single_nested_action_sequence(self):
            actions=[
                pygm_action.PyGameMakerMotionAction("set_velocity_compass"),
                pygm_action.PyGameMakerSoundAction("if_sound_is_playing"),
                pygm_action.PyGameMakerSoundAction("stop_sound"),
                pygm_action.PyGameMakerOtherAction("else"),
                pygm_action.PyGameMakerSoundAction("play_sound"),
                pygm_action.PyGameMakerSoundAction("if_sound_is_playing", invert=True),
                pygm_action.PyGameMakerOtherAction("start_of_block"),
                pygm_action.PyGameMakerSoundAction("play_sound"),
                pygm_action.PyGameMakerMotionAction("set_velocity_compass"),
                pygm_action.PyGameMakerOtherAction("end_of_block"),
                pygm_action.PyGameMakerOtherAction("else"),
                pygm_action.PyGameMakerOtherAction("start_of_block"),
                pygm_action.PyGameMakerSoundAction("play_sound"),
                pygm_action.PyGameMakerObjectAction("create_object"),
                pygm_action.PyGameMakerOtherAction("end_of_block"),
                pygm_action.PyGameMakerObjectAction("create_object"),
            ]
            action_sequence = PyGameMakerEventActionSequence()
            for act in actions:
                action_sequence.append_action(act)
            #print(action_sequence)
            self.assertEqual(actions,
                action_sequence.main_block.get_action_list())
            action_sequence.main_block.pretty_print()

        def test_010build_multiple_nested_action_sequence(self):
            actions=[
                pygm_action.PyGameMakerMotionAction("set_velocity_compass"),
                pygm_action.PyGameMakerSoundAction("if_sound_is_playing"),
                pygm_action.PyGameMakerSoundAction("if_sound_is_playing", invert=True),
                pygm_action.PyGameMakerSoundAction("if_sound_is_playing"),
                pygm_action.PyGameMakerSoundAction("stop_sound"),
                pygm_action.PyGameMakerSoundAction("if_sound_is_playing", invert=True),
                pygm_action.PyGameMakerOtherAction("start_of_block"),
                pygm_action.PyGameMakerSoundAction("play_sound"),
                pygm_action.PyGameMakerSoundAction("if_sound_is_playing"),
                pygm_action.PyGameMakerOtherAction("start_of_block"),
                pygm_action.PyGameMakerMotionAction("set_velocity_compass"),
                pygm_action.PyGameMakerMotionAction("apply_gravity"),
                pygm_action.PyGameMakerOtherAction("end_of_block"),
                pygm_action.PyGameMakerOtherAction("end_of_block"),
                pygm_action.PyGameMakerObjectAction("create_object")
            ]
            action_sequence = PyGameMakerEventActionSequence()
            for act in actions:
                action_sequence.append_action(act)
#            print(action_sequence)
            self.assertEqual(actions,
                action_sequence.main_block.get_action_list())
            action_sequence.main_block.pretty_print()
            
    unittest.main()

