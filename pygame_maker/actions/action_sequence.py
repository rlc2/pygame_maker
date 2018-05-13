"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Container type for sequences of actions.
"""

import re
from pygame_maker.actions.action import Action, ActionException

__all__ = ["ActionSequence", "ActionSequenceStatement",
           "ActionSequenceConditional", "ActionSequenceConditionalIf",
           "ActionSequenceConditionalElse", "ActionSequenceBlock",
           "ActionSequenceStatementException"]


class ActionSequenceStatementException(Exception):
    """
    Raised when unknown action names or something other than an action is found
    in a sequence, when sequence statements are placed incorrectly, or when an
    attempt is made to add something other than an ActionSequenceStatement to a
    sequence.
    """
    pass


class ActionSequenceStatement(object):
    """
    The base class for all action sequence statements.

    A "statement" wraps an action and provides structure to represent if/else
    conditionals and blocks along with normal executable statements.

    :param action: The action to wrap into the statement
    :type action: Action
    """
    @staticmethod
    def get_sequence_item_from_action(action, **kwargs):
        """
        Given a name or Action, retrieve its ActionSequenceStatement.

        Provide a simple static method to retrieve the right statement
        representing the given action: if/else condition, block, or
        executable statement.  Can also accept a string containing the name
        of the action, in which case a new action will be retrieved with
        its parameters filled in with the supplied kwargs.

        :param action: An action name, or Action instance
        :type action: str|Action
        :param kwargs: Optional keyword arguments to apply to the named action
        :return: The appropriate action sequence statement
        :rtype: ActionSequenceStatement
        """
        # if given a string, see if it names a known action
        new_action = None
        if isinstance(action, str):
            try:
                new_action = Action.get_action_instance_by_name(action, **kwargs)
            except ActionException:
                raise ActionSequenceStatementException("'{}' is not a known action".format(action))
        else:
            new_action = action
        if not isinstance(new_action, Action):
            raise ActionSequenceStatementException("'{}' is not a recognized action")
        if new_action.nest_adjustment:
            if new_action.name == "else":
                return ActionSequenceConditionalElse(new_action)
            minfo = Action.IF_STATEMENT_RE.search(new_action.name)
            if minfo:
                return ActionSequenceConditionalIf(new_action)
            if new_action.nest_adjustment != "block_end":
                return ActionSequenceBlock(new_action)
        return ActionSequenceStatement(new_action)

    def __init__(self, action):
        self.is_block = False
        self.is_conditional = False
        self.action = action

    def get_action_list(self):
        """
        Return the statement's action list.

        This method places the action inside a list of length 1.
        This aids with unit testing, and it allows an action sequence to be
        serialized to storage.  The deserialized simple list can be expanded
        into an action sequence when the application starts up.

        :return: A single-element list containing the wrapped action
        :rtype: list
        """
        return [self.action]

    def pretty_print(self, indent=0):
        """
        Display the name of the wrapped action as indented code

        :param indent: Number of spaces to indent
        :type indent: int
        """
        indent_string = "\t" * indent
        print("{}{}".format(indent_string, self.action.name))

    def __repr__(self):
        return "<{}: {}>".format(type(self).__name__, self.action)


class ActionSequenceConditional(ActionSequenceStatement):
    """
    Represent a simple conditional ('else' is the only kind this fits).

    :param action: The action to wrap into the conditional
    :type action: Action
    """
    def __init__(self, action):
        ActionSequenceStatement.__init__(self, action)
        self.is_conditional = True
        self.contained_statement = None

    def add_statement(self, statement):
        """
        Attempt to add a statement to the conditional.

        Given a statement, try to add it to the current conditional.  If the
        clause is empty, set its statement.  If the clause holds an open
        block or conditional, pass it on.

        :param statement: New statement to add to the conditional
        :type statement: ActionSequenceStatement
        :return: True if there was room for the new statement, otherwise False
        :rtype: bool
        """
        found_place = True
        # basic type check
        if not isinstance(statement, ActionSequenceStatement):
            raise ActionSequenceStatementException
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

    def get_action_list(self):
        """
        Collect the conditional's list of actions.

        This method retrieves all the collected statements inside a simple
        conditional into a simple list.  This aids with unit testing and
        allows an action sequence to be serialized to storage.  The
        deserialized simple list can be expanded into an action sequence
        when the application starts up.

        :return: A list containing the conditional's wrapped actions
        :rtype: list
        """
        contained_list = []
        if self.contained_statement:
            contained_list = self.contained_statement.get_action_list()
        return [self.action] + contained_list

    def pretty_print(self, indent=0):
        """
        Display an action sequence simple conditional as indented code

        :param indent: Number of spaces to indent
        :type indent: int
        """
        ActionSequenceStatement.pretty_print(self, indent)
        if self.contained_statement:
            self.contained_statement.pretty_print(indent+1)

    def __repr__(self):
        repr_str = "<{}:\n".format(type(self).__name__)
        repr_str += "\t{}>".format(self.contained_statement)
        return repr_str


class ActionSequenceConditionalIf(ActionSequenceConditional):
    """
    Represent an entire if/else conditional.

    The 'else' clause is also placed here, to avoid having to search earlier
    statements to see if there is a free 'if' conditional that matches the
    'else'.

    :param action: The action to wrap into the 'if' conditional
    :type action: Action
    """
    def __init__(self, action):
        ActionSequenceConditional.__init__(self, action)
        self.else_condition = None

    def add_statement(self, statement):
        """
        Attempt to place the given statement into the clause for the 'if'.

        If there is already a block or another conditional, see if the new
        statement will be accepted there.  If not, check whether the new
        statement is an 'else' condition, and that no 'else' condition already
        exists.  If there is an 'else' condition that hasn't received a
        statement yet, add it there.  If the 'else' statement exists and
        contains another conditional or block, see if the new statement
        will be accepted there.

        :param statement: New statement to add to the conditional
        :type statement: ActionSequenceStatement
        :return: True if there was room for the new statement, otherwise False
        :rtype: bool
        """
        found_place = True
        if not ActionSequenceConditional.add_statement(self, statement):
            if (not self.else_condition and
                    isinstance(statement, ActionSequenceConditionalElse)):
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
        Display an action sequence if/else conditional as indented code.

        :param indent: Number of spaces to indent
        :type indent: int
        """
        ActionSequenceConditional.pretty_print(self, indent)
        if self.else_condition:
            self.else_condition.pretty_print(indent)

    def walk(self):
        """
        Iterate through each action within a Conditional.

        :return: Generator function
        :rtype: generator
        """
        yield self.action
        conditional_path = None
        if self.action.action_result:
            if not self.contained_statement:
                # incomplete "if" path (can only happen to final action in list)
                return
            conditional_path = self.contained_statement
        else:
            if not self.else_condition:
                # "if" not executed, and no "else" path
                return
            # no need to return the "else" action itself, it does nothing
            conditional_path = self.else_condition.contained_statement
        if conditional_path.is_block or conditional_path.is_conditional:
            for action in conditional_path.walk():
                yield action
        else:
            yield conditional_path.action

    def get_action_list(self):
        """
        Collect the conditional's list of actions.

        This method retrieves all the collected statements inside a
        conditional into a simple list.  This aids with unit
        testing and allows an action sequence to be serialized
        to storage.  The deserialized simple list can be expanded into an
        action sequence when the application starts up.

        :return: A list of the actions wrapped in the If conditional
        :rtype: list
        """
        contained_list = ActionSequenceConditional.get_action_list(self)
        else_list = []
        if self.else_condition:
            else_list = self.else_condition.get_action_list()
        return contained_list + else_list

    def __repr__(self):
        repr_str = "<{} {}:\n".format(type(self).__name__, self.action)
        repr_str += "\t{}\n".format(self.contained_statement)
        if self.else_condition:
            repr_str += "{}>".format(self.else_condition)
        return repr_str


class ActionSequenceConditionalElse(ActionSequenceConditional):
    """
    Clone of the ActionSequenceConditional class.

    Named for convenience to be used in a ActionSequenceConditionalIf.

    :param action: The action to wrap into the 'else' conditional
    :type action: Action
    """
    def __init__(self, action):
        ActionSequenceConditional.__init__(self, action)


class ActionSequenceBlock(ActionSequenceStatement):
    """
    Represent a block of action statements.

    All statements are placed into a block (even if just the 'main' block) or
    into conditionals within a block.  The first action in the main block
    is set to None.

    :param action: Usually a start_of_block action
    :type action: Action|None
    :param main_block: True if this is the main (outermost) block
    :type main_blocK: bool
    """
    def __init__(self, action, main_block=False):
        # main block doesn't start with an explicit action, so action==None
        #  is ok.  Remember this when trying to use self.action in any
        #  methods, including superclasses!
        ActionSequenceStatement.__init__(self, action)
        self.is_block = True
        self.is_block_closed = False
        self.contained_statements = []
        self.main_block = main_block

    def _append_statement(self, statement):
        # Called by add_statement() when an action is meant for this block.
        #
        # :param statement: New statement to add to the block
        # :type statement: ActionSequenceStatement

        # the main block is never explicitly "closed"
        if statement.action and statement.action.nest_adjustment == "block_end":
            if not self.main_block:
                self.is_block_closed = True
                self.contained_statements.append(statement)
            else:
                raise ActionSequenceStatementException("block_end cannot be added to a main block")
        elif isinstance(statement, ActionSequenceConditionalElse):
            raise ActionSequenceStatementException
        else:
            self.contained_statements.append(statement)

    def add_statement(self, statement):
        """
        Add a new statement to an open block.

        The action sequence "magic" happens here.  Normal statements, "if"
        conditionals and blocks can be added to the current block.  Open
        conditionals (no clause yet) or blocks (no "block_end" action) can
        receive new statements.  An "else" action can be attached to an "if"
        conditional.  All statements exist either inside a block (there is
        always a "main" block) or a conditional.

        :param statement: New statement to add to the block
        :type statement: ActionSequenceStatement
        """
        # print("Adding statement: {} .. ".format(statement))
        if not isinstance(statement, ActionSequenceStatement):
            raise TypeError("{} is not an ActionSequenceStatement".format(str(statement)))
        last_statement = None
        if len(self.contained_statements) > 0:
            last_statement = self.contained_statements[-1]
        if last_statement and last_statement.is_conditional:
            # If the last statement's conditional is still open, this statement
            #  belongs there.  Otherwise, add it to this block
            if last_statement.add_statement(statement):
                # print("---> to last conditional")
                return
        if last_statement and last_statement.is_block:
            # If the last statement's block is still open, this statement
            #  belongs there.  Otherwise, add it to this block
            if not last_statement.is_block_closed:
                # print("---> to last block")
                last_statement.add_statement(statement)
                return
        # print("---> to current block")
        self._append_statement(statement)

    def get_action_list(self):
        """
        Collect the conditional's list of actions.

        This method retrieves all the collected statements inside a
        block into a simple list.  This aids with unit testing
        and allows an action sequence to be serialized to storage.
        The deserialized simple list can be expanded into an action
        sequence when the application starts up.

        :return: A list of the actions wrapped in the If conditional
        :rtype: list
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
        Display the action sequence block as indented code.

        :param indent: Number of spaces to indent
        :type indent: int
        """
        new_indent = indent
        if not self.main_block:
            ActionSequenceStatement.pretty_print(self, indent)
            new_indent += 1
        if self.contained_statements:
            for contained in self.contained_statements:
                if contained.action.nest_adjustment != "block_end":
                    contained.pretty_print(new_indent)
                else:
                    contained.pretty_print(indent)

    def walk(self):
        """
        Iterate through each action within a block.

        :return: Generator function
        :rtype: generator
        """
        for statement in self.contained_statements:
            if statement.action is None:
                continue
            if statement.action.nest_adjustment == "block_end":
                return
            if statement.is_conditional or statement.is_block:
                for sub_statement_action in statement.walk():
                    yield sub_statement_action
            else:
                yield statement.action

    def __repr__(self):
        repr_str = "<{}:\n".format(type(self).__name__)
        for statement in self.contained_statements:
            repr_str += "{}\n".format(statement)
        repr_str += ">"
        return repr_str


class ActionSequence(object):
    """Store a sequence of actions, which runs when triggered by an event."""
    FIRST_ITEM_RE = re.compile(r"^\s*([^ ])")

    @staticmethod
    def load_sequence_from_yaml_obj(sequence_repr):
        """
        Create an event action sequence from its YAML representation.
        The expected format is as follows::

          [{<action_name>: { <action_param>:<action_value>, .. }, ..., ]

        :param sequence_repr: The YAML object containing action sequence data
        :type sequence_repr: yaml.load() result
        :return: The action sequence described in the YAML object
        :rtype: ActionSequence
        """
        new_sequence = None
        if len(sequence_repr) > 0:
            new_sequence = ActionSequence()
            for action_hash in sequence_repr:
                action_name = list(action_hash.keys())[0]
                action_params = {}
                if action_hash[action_name] and len(action_hash[action_name]) > 0:
                    action_params.update(action_hash[action_name])
                next_action = Action.get_action_instance_by_name(action_name, **action_params)
                # print("New action: {}".format(next_action))
                new_sequence.append_action(next_action)
        return new_sequence

    def __init__(self):
        """Wrap the outermost ActionSequenceBlock."""
        #: The main block, containing all actions in sequence
        self.main_block = ActionSequenceBlock(None, True)

    def append_action(self, action):
        """
        Add a new action to the end of the sequence.

        :param action: The name of a defined action, or an Action instance
        :type action: str|Action
        """
        statement = ActionSequenceStatement.get_sequence_item_from_action(action)
        self.main_block.add_statement(statement)

    def get_next_action(self):
        """
        Iterate through every action in the ActionSequence.

        :return: Generator function
        :rtype: generator
        """
        for next_action in self.main_block.walk():
            if next_action is not None:
                yield next_action

    def to_yaml(self, indent=0):
        """
        Produce the YAML representation of the action sequence.

        :param indent: Number of spaces to indent each line
        :type indent: int
        :return: YAML string
        :rtype: str
        """
        action_list = self.main_block.get_action_list()
        sequence_yaml = ""
        for action in action_list:
            action_yaml_lines = action.to_yaml(indent).splitlines()
            for idx, aline in enumerate(action_yaml_lines):
                if idx == 0:
                    sline = str(aline)
                    minfo = self.FIRST_ITEM_RE.search(aline)
                    # print("first item match for '{}': {}".format(aline, minfo))
                    if minfo:
                        mpos = minfo.start(1)
                        # print("match pos:{}".format(mpos))
                        sline = "{}- {}".format(aline[0:mpos], aline[mpos:])
                    else:
                        sline = "- {}".format(aline)
                    sequence_yaml += "{}\n".format(sline)
                else:
                    sequence_yaml += "  {}\n".format(aline)
        return sequence_yaml

    def pretty_print(self):
        """Print out properly-indented action sequence strings."""
        self.main_block.pretty_print()

    def __repr__(self):
        return "{}".format(str(self.main_block))
