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
    """
        PyGameMakerEventActionSequenceStatement class:
        The basis for all action sequence statements. A "statement" wraps
        an action and provides structure to represent if/else conditionals
        and blocks along with normal executable statements.
    """
    @staticmethod
    def get_sequence_item_from_action(action, **kwargs):
        """
            get_sequence_item_from_action():
            Provides a simple static method to retrieve the right statement
            representing the given action: if/else condition, block, or
            executable statement. Can also accept a string containing the name
            of the action, in which case a new action will be retrieved with
            its parameters filled in with supplied kwargs.
        """
        # if given a string, see if it names a known action
        new_action = None
        if isinstance(action, str):
            try:
                new_action = pygm_action.PyGameMakerAction.get_action_instance_by_action_name(action, **kwargs)
            except pygm_action.PyGameMakerActionException:
                raise PyGameMakerEventActionSequenceStatementException("'{}' is not a known action".format(action))
        else:
            new_action = action
        if not isinstance(new_action, pygm_action.PyGameMakerAction):
            raise PyGameMakerEventActionSequenceStatementException("'{}' is not a recognized action")
        if (new_action.nest_adjustment):
            if new_action.name == "else":
                return PyGameMakerEventActionSequenceConditionalElse(new_action)
            minfo = pygm_action.PyGameMakerAction.IF_STATEMENT_RE.search(new_action.name)
            if minfo:
                return PyGameMakerEventActionSequenceConditionalIf(new_action)
            if new_action.nest_adjustment != "block_end":
                return PyGameMakerEventActionSequenceBlock(new_action)
        return PyGameMakerEventActionSequenceStatement(new_action)

    def __init__(self, action):
        self.is_block = False
        self.is_conditional = False
        self.action = action

    def get_action_list(self):
        """
            get_action_list():
            This method places the action inside a list of length 1.
            For now, this aids with unit testing. Later, it will allow an
            action sequence to be serialized to storage.  The deserialized
            simple list can be expanded into an action sequence when the
            application starts up.
        """
        return [self.action]

    def pretty_print(self, indent=0):
        """
            pretty_print():
            Display the name of the wrapped action as indented code
        """
        indent_string = "\t" * indent
        print("{}{}".format(indent_string, self.action.name))

    def __repr__(self):
        return "<{}: {}>".format(type(self).__name__, self.action)

class PyGameMakerEventActionSequenceConditional(PyGameMakerEventActionSequenceStatement):
    """
        PyGameMakerEventActionSequenceConditional class:
        Represent a simple conditional ('else' is the only kind this fits).
    """
    def __init__(self, action):
        PyGameMakerEventActionSequenceStatement.__init__(self, action)
        self.is_conditional = True
        self.contained_statement = None

    def add_statement(self, statement):
        """
            Given a statement, try to add it to the current conditional. If the
            clause is empty, set its statement. If the clause holds an open
            block or conditional, pass it on.
            Returns True if there was a place for the new statement, otherwise
            returns False.
        """
        found_place = True
        # basic type check
        if not isinstance(statement, PyGameMakerEventActionSequenceStatement):
            raise(PyGameMakerEventActionSequenceStatementException("{} is not a PyGameMakerEventActionSequenceStatement".format(statement)))
        if not self.contained_statement:
            # the statement is now the conditional clause
            self.contained_statement = statement
        elif (self.contained_statement.is_block and
            not self.contained_statement.is_block_closed):
            # the statement fits within the conditional clause's block
            self.contained_statement.add_statement(statement)
        elif (self.contained_statement.is_conditional and
            self.contained_statement.add_statement(statement)):
            # the contained conditional found a place for the statement
            pass
        else:
            found_place = False
        return found_place

    def set_statement(self, statement):
        """
            set_statement()
            Currently unused. Places the given statement into the conditional
            clause if there isn't one already. Does not attempt to pass on
            the statement to an open conditional or block in an existing
            conditional clause.
        """
        if not isinstance(statement, PyGameMakerEventActionSequenceStatement):
            raise(PyGameMakerEventActionSequenceStatementException("{} is not a PyGameMakerEventActionSequenceStatement".format(statement)))
        if self.contained_statement:
            raise(PyGameMakerEventActionSequenceStatementException("{}: already contains a statement".format(self.action)))
        self.contained_statement = statement

    def get_action_list(self):
        """
            get_action_list():
            This method retrieves all the collected statements inside a simple
            conditional into a simple list. For now, this aids with unit
            testing. Later, it will allow an action sequence to be serialized
            to storage.  The deserialized simple list can be expanded into an
            action sequence when the application starts up.
        """
        contained_list = []
        if self.contained_statement:
            contained_list = self.contained_statement.get_action_list()
        return [self.action] + contained_list

    def pretty_print(self, indent=0):
        """
            pretty_print():
            Display an action sequence simple conditional as indented code
        """
        PyGameMakerEventActionSequenceStatement.pretty_print(self, indent)
        if self.contained_statement:
            self.contained_statement.pretty_print(indent+1)

    def __repr__(self):
        repr = "<{}:\n".format(type(self).__name__)
        repr += "\t{}>".format(self.contained_statement)
        return repr

class PyGameMakerEventActionSequenceConditionalIf(PyGameMakerEventActionSequenceConditional):
    """
        PyGameMakerEventActionSequenceConditionalIf class:
        This represents an entire if/else conditional. The 'else' clause is
        also placed here, to avoid having to search earlier statements to see
        if there is a free 'if' conditional that matches the 'else'.
    """
    def __init__(self, action):
        PyGameMakerEventActionSequenceConditional.__init__(self, action)
        self.else_condition = None

    def add_else(self, else_statement):
        """
            add_else():
            Currently unused. Places an 'else' action in the else slot for
            the 'if' conditional.
        """
        if not isinstance(else_statement, PyGameMakerEventActionSequenceConditionalElse):
            raise(PyGameMakerEventActionSequenceStatementException("{} is not a PyGameMakerEventActionSequenceConditionalElse".format(else_statement)))
        if self.else_condition:
            raise(PyGameMakerEventActionSequenceStatementException("{}: already contains an else clause".format(self.action)))
        self.else_condition = else_statement

    def add_statement(self, statement):
        """
            add_statement():
            Attempt to place the given statement into the clause for the 'if'.
            If there is already a block or another conditional, see if the new
            statement will be accepted there. If not, check whether the new
            statement is an 'else' condition, and no 'else' condition already
            exists. If there is an 'else' condition that hasn't received a
            statement yet, add it there. If the 'else' statement exists and
            contains another conditional or block, see if the new statement
            will be accepted there.
        """
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
        """
            pretty_print():
            Display an action sequence if/else conditional as indented code
        """
        PyGameMakerEventActionSequenceConditional.pretty_print(self, indent)
        if self.else_condition:
            self.else_condition.pretty_print(indent)

    def get_action_list(self):
        """
            get_action_list():
            This method retrieves all the collected statements inside a
            conditional into a simple list. For now, this aids with unit
            testing. Later, it will allow an action sequence to be serialized
            to storage. The deserialized simple list can be expanded into an
            action sequence when the application starts up.
        """
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
    """
        PyGameMakerEventActionSequenceConditionalElse class:
        Currently identical to the PyGameMakerEventActionSequenceConditional
        class, but named for convenience to be used in a
        PyGameMakerEventActionSequenceConditionalIf.
    """
    def __init__(self, action):
        PyGameMakerEventActionSequenceConditional.__init__(self, action)

class PyGameMakerEventActionSequenceBlock(PyGameMakerEventActionSequenceStatement):
    """
        PyGameMakerEventActionSequenceBlock class:
        Represent a block of action statements. All statements are placed into
        a block (even if just the 'main' block) or into conditionals within
        a block.
    """
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
        """
            append_statement():
            called by add_statement() when an action is meant for this block.
        """
        # the main block is never explicitly "closed"
        if statement.action and statement.action.nest_adjustment == "block_end":
            if not self.main_block:
                self.is_block_closed = True
                self.contained_statements.append(statement)
            else:
                raise(PyGameMakerEventActionSequenceStatementException("block_end cannot be added to a main block"))
        elif isinstance(statement, PyGameMakerEventActionSequenceConditionalElse):
            raise(PyGameMakerEventActionSequenceStatementException("Cannot add an 'else' statement without an 'if' statement."))
        else:
            self.contained_statements.append(statement)

    def add_statement(self, statement):
        """
            add_statement():
            The action sequence "magic" happens here. Normal statements, "if"
            conditionals and blocks can be added to the current block. Open
            conditionals (no clause yet) or blocks (no "block_end" action) can
            receive new statements. An "else" action can be attached to an "if"
            conditional. All statements exist either inside a block (there is
            always a "main" block) or a conditional.
        """
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
        """
            get_action_list():
            This method retrieves all the collected statements inside a block
            into a simple list. For now, this aids with unit testing. Later,
            it will allow an action sequence to be serialized to storage.
            The deserialized simple list can be expanded into an action
            sequence when the application starts up.
        """
        this_action = []
        if not self.main_block:
            this_action = [self.action]
        contained_list = []
        if self.contained_statements:
            for contained in self.contained_statements:
                contained_list += contained.get_action_list()
        return this_action + contained_list

    def pretty_print(self, indent=0):
        """
            pretty_print():
            Display the action sequence block as indented code
        """
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

    def pretty_print(self):
        self.main_block.pretty_print()

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
            action_sequence.pretty_print()

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
            action_sequence.pretty_print()
            
        def test_015broken_sequences(self):
            action_sequence = PyGameMakerEventActionSequence()
            action_sequence.pretty_print()
            with self.assertRaises(PyGameMakerEventActionSequenceStatementException):
                action_sequence.append_action(
                    pygm_action.PyGameMakerOtherAction("else"))
            with self.assertRaises(PyGameMakerEventActionSequenceStatementException):
                action_sequence.append_action(
                    pygm_action.PyGameMakerOtherAction("end_of_block"))
            with self.assertRaises(PyGameMakerEventActionSequenceStatementException):
                action_sequence.append_action("this is not an action!")


    unittest.main()

