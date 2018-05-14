"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Represent an action that executes following an event.
"""

import re
import yaml
from pygame_maker.logic.language_engine import SymbolTable

__all__ = ["Action", "AccountingAction", "CodeAction", "DrawAction",
           "GameAction", "InfoAction", "MotionAction", "ObjectAction",
           "OtherAction", "ParticleAction", "QuestionAction", "ResourceAction",
           "RoomAction", "SoundAction", "TimingAction", "VariableAction",
           "ActionException"]


class ActionException(Exception):
    """
    Raised by Action and its subclasses when an unknown action name is requested.
    """
    pass


class Action(object):
    """
    Base class for all actions.

    Specify the basic properties for any action, along with information
    about the properties' types and default values.

    The YAML description must match the following format::

        # map of parameters found in many different actions
        common_parameters:
            common_parameter1:
                # specify this parameter's type
                type: from_list|int|float|str|bool
                # specify this parameter's default value
                default: value # must match the type
                # for from_list parameters only: accepted_list
                # lists all accepted values (usually strings)
                accepted_list:
                    - value1
                    - value2
                    - valueN
            common_parameter2:
            # continue with parameters that appear in many actions
        # map of the actions supported by this subclass
        actions:
            action1:
                # example of referencing a common parameter type
                parameter1: common_parameter1
                parameterA:
                    type: float
                    default: 0.0
                # continue with this action's other parameters
                speed: common_speed
            action2:
            # continue with the rest of the actions as above

    Typically, a subclass combines the class attribute COMMON_DATA_YAML
    with the YAML descriptions of its actions.

    :param action_name: Name of the action
    :type action_name: str
    :param action_yaml: YAML string describing the action's parameters
    :type action_yaml: str
    :param settings_dict: dict mapping values to the action's parameters
    :type settings_dict: dict
    :param kwargs: Parameter values specified as named arguments
    """
    #: Any action with a position defaults to 0, 0
    DEFAULT_POINT_XY = (0, 0)
    #: Any action with a speed defaults to 0
    DEFAULT_SPEED = 0
    #: Any action with a direction defaults to 0 (up)
    DEFAULT_DIRECTION = 0
    #: Any action with gravity defaults to 0 (none)
    DEFAULT_GRAVITY = 0
    #: Any action with friction defaults to 0 (none)
    DEFAULT_FRICTION = 0
    #: Any action needing a grid defaults to 16, 16
    DEFAULT_GRID_SNAP_XY = (16, 16)
    #: Any action specifying motion wrapping defaults to "HORIZONTAL"
    DEFAULT_WRAP_DIRECTION = "HORIZONTAL"
    #: Any action with a path defaults to None
    DEFAULT_PATH = None
    #: Any action with a path location defaults to location 0
    DEFAULT_PATH_LOCATION = 0
    #: Any action with a collision defaults to "solid"
    DEFAULT_COLLISION_TYPE = "solid"
    #: Any action with collision precision defaults to "imprecise"
    DEFAULT_PRECISION_TYPE = "imprecise"
    #: Compass directions available to actions
    COMPASS_DIRECTIONS = [
        "NONE",
        "STOP",
        "UPLEFT",
        "UP",
        "UPRIGHT",
        "RIGHT",
        "DOWNRIGHT",
        "DOWN",
        "DOWNLEFT",
        "LEFT"
    ]
    #: The mapping between compass direction names and degrees
    COMPASS_DIRECTION_DEGREES = {
        "UPLEFT": 315,
        "UP": 0,
        "UPRIGHT": 45,
        "RIGHT": 90,
        "DOWNRIGHT": 135,
        "DOWN": 180,
        "DOWNLEFT": 225,
        "LEFT": 270
    }
    #: Names of horizontal directions
    HORIZONTAL_DIRECTIONS = ["LEFT", "RIGHT"]
    #: Names of vertical directions
    VERTICAL_DIRECTIONS = ["UP", "DOWN"]
    #: Possible names for actions with motion wrapping
    WRAP_DIRECTIONS = [
        "HORIZONTAL",
        "VERTICAL",
        "BOTH"
    ]
    #: Names of collision types
    COLLISION_TYPES = [
        "solid",
        "any"
    ]
    #: Names of precision types
    PRECISION_TYPES = [
        "precise",
        "imprecise"
    ]
    #: Names of path end actions
    PATH_END_ACTIONS = [
        "stop",
        "continue_from_start",
        "continue_from_here",
        "reverse"
    ]
    # YAML descriptions of common action parameters for re-use by other
    #  actions
    COMMON_DATA_YAML = """
common_parameters:
    common_apply_to:
        type: from_list
        default: self
        accepted_list: [self, other, object_name]
    common_relative:
        type: bool
        default: False
    common_speed:
        type: float
        default: 0.0
    common_position:
        type: int
        default: 0
    common_compass_direction:
        type: from_list
        default: none
        accepted_list:
            - none
            - stop
            - upleft
            - up
            - upright
            - right
            - downright
            - down
            - downleft
            - left
    common_collision_type:
        type: from_list
        default: solid
        accepted_list: [solid, any]
    common_object:
        type: str
        default: ''
    common_transition:
        type: from_list
        default: None
        accepted_list:
            - none
            - create_from_left
            - create_from_right
            - create_from_top
            - create_from_bottom
            - create_from_center
            - shift_from_left
            - shift_from_right
            - shift_from_top
            - shift_from_bottom
            - interlaced_from_left
            - interlaced_from_right
            - interlaced_from_top
            - interlaced_from_bottom
    common_invert:
        type: bool
        default: False
    common_test:
        type: from_list
        default: equals
        accepted_list:
            - equals
            - not_equals
            - less_than
            - less_than_or_equals
            - greater_than
            - greater_than_or_equals
"""
    IF_STATEMENT_RE = re.compile("^if_")
    TUPLE_RE = re.compile(r"\(([^)]+)\)")
    COMMON_RE = re.compile("^common_")

    # Class variable to be filled in with Action subclasses
    action_type_registry = []

    @classmethod
    def register_new_action_type(cls, actiontype):
        """
        Register Action subclasses.

        Register a class (at init time) to make it possible to search
        it for a particular action name.

        :param actiontype: Action subclass to register
        :type actiontype: Action subclass
        """
        cls.action_type_registry.append(actiontype)

    @classmethod
    def get_action_instance_by_name(cls, action_name, settings_dict=None, **kwargs):
        """
        Search for an action name in all registered actions and return an
        instance of the correct Action subclass if found.

        :param action_name: An action's name
        :type action_name: str
        :param settings_dict: dict mapping values to the action's parameters
        :type settings_dict: dict
        :param kwargs: Parameter values specified as named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if len(cls.action_type_registry) > 0:
            for atype in cls.action_type_registry:
                if action_name in atype.HANDLED_ACTIONS:
                    return atype(action_name, settings, **kwargs)
        # no action type handles the named action
        raise ActionException("Action '{}' is unknown".format(action_name))

    def __init__(self, action_name, action_yaml, settings_dict=None, **kwargs):
        """
        Supply the basic properties for any action.

        :param action_name: Name of the action
        :type action_name: str
        :param action_yaml: YAML string describing the action's parameters
        :type action_yaml: str
        :param settings_dict: dict mapping values to the action's parameters
        :type settings_dict: dict
        :param kwargs: Parameter values specified as named arguments
        """
        #: This action's name
        self.name = action_name
        #: The dict mapping parameters to their values (or expressions)
        self.action_data = {}
        #: The dict mapping parameters to their types and constraints
        self.action_constraints = {}
        #: Store parameters added to the action at runtime
        self.runtime_data = {}
        args = {}
        if settings_dict is not None:
            args.update(settings_dict)
        args.update(kwargs)
        data_map, data_constraints = self._collect_parameter_yaml_info(
            action_yaml + self.COMMON_DATA_YAML)
        if action_name in data_map:
            self.action_data.update(data_map[action_name])
        if action_name in data_constraints:
            self.action_constraints.update(data_constraints[action_name])
        # default: don't nest subsequent action(s)
        minfo = self.IF_STATEMENT_RE.search(action_name)
        if minfo is not None or (action_name == "else"):
            # automatically nest after question tasks
            self.nest_adjustment = "nest_next_action"
            if minfo:
                self.action_result = True
        else:
            self.nest_adjustment = None
        for param in args:
            if param in self.action_data:
                self.action_data[param] = args[param]

    def _collect_parameter_yaml_info(self, yaml_str):
        # Parse the YAML parameter information for the action.

        # :param yaml_str: YAML string with common params and actions
        # :type yaml_str: str
        # :return:
        #     A tuple of 2 dicts, one maps params with defaults, the other maps
        #     params with types and constraints
        # :rtype: (dict, dict)
        action_map = {}
        action_constraints = {}
        yaml_obj = yaml.load(yaml_str)
        common_params = yaml_obj['common_parameters']
        # print("Got common params:\n{}".format(common_params))
        for action in yaml_obj['actions'].keys():
            action_map[action] = {}
            for par in yaml_obj['actions'][action]:
                par_val = yaml_obj['actions'][action][par]
                if not isinstance(par_val, dict):
                    minfo = self.COMMON_RE.search(par_val)
                    if minfo:
                        action_map[action][par] = common_params[par_val]['default']
                        action_constraints[action] = common_params[par_val]
                elif len(par_val.keys()) > 0:
                    if par_val['type'] == "from_list":
                        if par_val['default'] not in par_val['accepted_list']:
                            print("WARNING: default value " +
                                  "'{}' is not in the list of accepted values '{}'".
                                  format(par_val['default'], par_val['accepted_list']))
                    action_map[action][par] = par_val['default']
                    action_constraints[action] = par_val
        # print("Got action_map:\n{}".format(action_map))
        # print("Got action_constraints:\n{}".format(action_constraints))
        parm_info = (action_map, action_constraints)
        return parm_info

    def get_parameter_expression_result(self, field_name, symbols,
                                        language_engine):
        """
        Calculate the value inside a field.

        Given a field name possibly containing an expression, register the
        expression with the language engine and execute the code, and
        return the result.  Use the spreadsheet formula scheme to indicate
        an expression to execute: first char is '='.

        :param field_name: The field containing the expression
        :type field_name: str
        :param symbols: The symbols available to the code block
        :type symbols: SymbolTable
        :param language_engine: The language engine instance
        :type language_engine: LanguageEngine
        :return: The result from the expression
        :rtype: varies by symbol
        """
        # print("{}: get expression for field {}: {}".format(self, field_name,
        #    self.action_data[field_name]))
        if (not isinstance(self.action_data[field_name], str) or
                (len(self.action_data[field_name]) == 0) or
                (self.action_data[field_name][0] != '=')):
            # not an expression, so just return the contents of the field
            return self.action_data[field_name]
        exp_name = "{}_block".format(field_name)
        # print("check for code block {}".format(exp_name))
        # create a hopefully unique symbol to store the expression result in
        sym_name = "intern_{}_{}".format(field_name, abs(hash(field_name)))
        # print("sym_name: {}".format(sym_name))
        if exp_name not in self.runtime_data.keys():
            # create an entry in the action data that points to a
            #  hopefully unique name that will be registered with the language
            #  engine
            exp_id = "{}_{}_{}".format(self.name,
                                       re.sub(r"\.", "_", field_name), id(self))
            expression_code = "{} = {}".format(sym_name,
                                               self.action_data[field_name][1:])
            # print("register new code block {}: {}".format(exp_id, expression_code))
            language_engine.register_code_block(exp_id, expression_code)
            self.runtime_data[exp_name] = exp_id
        # execute the expression and collect its result
        local_symbols = SymbolTable(symbols)
        language_engine.execute_code_block(self.runtime_data[exp_name],
                                           local_symbols)
        # print("{} = {}".format(sym_name, local_symbols[sym_name]))
        return local_symbols[sym_name]

    def to_yaml(self, indent=0):
        """
        Produce the action's YAML-formatted string representation

        :param indent: Number of spaces to indent each line
        :type indent: int
        """
        indent_str = " " * indent
        yaml_str = "{}{}:\n".format(indent_str, self.name)
        keylist = self.action_data.keys()
        keylist.sort()
        for act_key in keylist:
            value = self.action_data[act_key]
            value_str = "{}".format(value)
            minfo = self.TUPLE_RE.search(value_str)
            if minfo:
                value_str = "[{}]".format(minfo.group(1))
            val_lines = value_str.splitlines()
            if len(val_lines) > 1:
                yaml_str += "{}  {}: |\n".format(indent_str, act_key)
                for vline in val_lines:
                    yaml_str += "{}    {}\n".format(indent_str, vline)
            else:
                yaml_str += "{}  {}: {}\n".format(indent_str, act_key,
                                                  value_str)
        return yaml_str

    def keys(self):
        return self.action_data.keys() + self.runtime_data.keys()

    def __getitem__(self, itemname):
        """
        Create a shortcut for accessing parameters.

        Forward itemname to the action_data dict if found there, or otherwise
        to the runtime_data attribute, for convenience.

        :param itemname: Parameter name to access
        :type itemname: str
        :raise: KeyError, if the key is not found in either attribute's hash
        :return: The value stored in the parameter
        """
        val = None
        if itemname not in self.action_data:
            if itemname not in self.runtime_data:
                raise KeyError("{}".format(itemname))
            val = self.runtime_data[itemname]
        else:
            val = self.action_data[itemname]
        return val

    def __setitem__(self, itemname, value):
        """
        Allow action data to be modified.

        If itemname is found in the action_data dict, it will be changed
        to the new value.  Otherwise, the value will be added to the
        runtime_data dict, whether or not the key existed there before.

        :param itemname: Parameter name to set
        :type itemname: str
        :param value: New parameter value
        """
        if itemname not in self.action_data:
            # Fall back to runtime data.  This is data that is not serialized.
            self.runtime_data[itemname] = value
        self.action_data[itemname] = value

    def __repr__(self):
        return "<{} '{}': {}>".format(type(self).__name__, self.name,
                                      self.action_data)

    def __eq__(self, other):
        return (isinstance(other, Action) and
                (self.name == other.name) and
                (self.action_data == other.action_data))


class MotionAction(Action):
    """
    Wrap motion-related actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    MOVE_ACTIONS = [
        "set_velocity_compass",
        "set_velocity_degrees",
        "move_toward_point",
        "set_horizontal_speed",
        "set_vertical_speed",
        "apply_gravity",
        "reverse_horizontal_speed",
        "reverse_vertical_speed",
        "set_friction"
    ]
    JUMP_ACTIONS = [
        "jump_to",
        "jump_to_start",
        "jump_random",
        "snap_to_grid",
        "wrap_around",
        "move_until_collision",
        "bounce_off_collider"
    ]
    PATH_ACTIONS = [
        "set_path",
        "end_path",
        "set_location_on_path",
        "set_path_speed"
    ]
    STEP_ACTIONS = [
        "step_toward_point",
        "step_toward_point_around_objects"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = MOVE_ACTIONS + JUMP_ACTIONS + PATH_ACTIONS + STEP_ACTIONS
    MOTION_ACTION_DATA_YAML = """
actions:
    set_velocity_compass:
        apply_to: common_apply_to
        compass_directions: common_compass_direction
        speed: common_speed
    set_velocity_degrees:
        apply_to: common_apply_to
        direction:
            type: float
            default: 0.0
        speed: common_speed
        relative: common_relative
    move_toward_point:
        apply_to: common_apply_to
        destination.x: common_position
        destination.y: common_position
        speed: common_speed
        relative: common_relative
    set_horizontal_speed:
        apply_to: common_apply_to
        horizontal_direction:
            type: from_list
            default: right
            accepted_list: [right, left]
        horizontal_speed: common_speed
        relative: common_relative
    set_vertical_speed:
        apply_to: common_apply_to
        vertical_direction:
            type: from_list
            default: up
            accepted_list: [up, down]
        vertical_speed: common_speed
        relative: common_relative
    apply_gravity:
        apply_to: common_apply_to
        gravity_direction: common_compass_direction
        relative: common_relative
    reverse_horizontal_speed:
        apply_to: common_apply_to
    reverse_vertical_speed:
        apply_to: common_apply_to
    set_friction:
        apply_to: common_apply_to
        friction:
            type: float
            default: '0.0'
        relative: common_relative
    jump_to:
        apply_to: common_apply_to
        position.x: common_position
        position.y: common_position
        relative: common_relative
    jump_to_start:
        apply_to: common_apply_to
    jump_random:
        apply_to: common_apply_to
        snap.x: common_position
        snap.y: common_position
    snap_to_grid:
        apply_to: common_apply_to
        grid.x: common_position
        grid.y: common_position
    wrap_around:
        apply_to: common_apply_to
        wrap_direction:
            type: from_list
            default: horizontal
            accepted_list: [horizontal, vertical, both]
    move_until_collision:
        apply_to: common_apply_to
        direction:
            type: float
            default: 0.0
        max_distance:
            type: int
            default: -1
        stop_at_collision_type: common_collision_type
    bounce_off_collider:
        apply_to: common_apply_to
        precision:
            type: from_list
            default: imprecise
            accepted_list: [precise, imprecise]
        bounce_collision_type: common_collision_type
    set_path:
        apply_to: common_apply_to
        path:
            type: str
            default: ''
        speed:
            common_speed
        at_end:
            type: from_list
            default: stop
            accepted_list:
                - stop
                - continue_from_start
                - continue_from_here
                - reverse
        relative: common_relative
    end_path:
        apply_to: common_apply_to
    set_location_on_path:
        apply_to: common_apply_to
        location:
            type: str
            default: 0
        relative:
            common_relative
    set_path_speed:
        apply_to: common_apply_to
        speed: common_speed
        relative: common_relative
    step_toward_point:
        apply_to: common_apply_to
        destination.x: common_position
        destination.y: common_position
        speed: common_speed
        stop_at_collision_type: common_collision_type
        relative: common_relative
    step_toward_point_around_objects:
        apply_to: common_apply_to
        position.x: common_position
        position.y: common_position
        speed: common_speed
        avoid_collision_type: common_collision_type
        relative: common_relative

"""

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize a MotionAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("MotionAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name,
                        self.MOTION_ACTION_DATA_YAML,
                        settings, **kwargs)
        # print("Created new action {}".format(self))
        # self.action_data = self.MOTION_ACTION_DATA_MAP[action_name]


class ObjectAction(Action):
    """
    Wrap object-related actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    OBJECT_ACTIONS = [
        "create_object",
        "create_object_with_velocity",
        "create_random_object",
        "transform_object",
        "destroy_object",
        "destroy_instances_at_location"
    ]
    SPRITE_ACTIONS = [
        "set_sprite",
        "transform_sprite",
        "color_sprite"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = OBJECT_ACTIONS + SPRITE_ACTIONS
    OBJECT_ACTION_DATA_YAML = """
actions:
    create_object:
        object: common_object
        position.x: common_position
        position.y: common_position
        child_instance:
            type: bool
            default: False
        relative: common_relative
    create_object_with_velocity:
        object: common_object
        position.x: common_position
        position.y: common_position
        speed: common_speed
        direction:
            type: float
            default: 0.0
        child_instance:
            type: bool
            default: False
        relative: common_relative
    create_random_object:
        position.x: common_position
        position.y: common_position
        object_1: common_object
        object_2: common_object
        object_3: common_object
        object_4: common_object
        relative: common_relative
    transform_object:
        apply_to: common_apply_to
        object: common_object
        new_object: common_object
        perform_events:
            type: bool
            default: False
    destroy_object:
        apply_to: common_apply_to
    destroy_instances_at_location:
        apply_to: common_apply_to
        position.x: common_position
        position.y: common_position
        relative: common_relative
    set_sprite:
        apply_to: common_apply_to
        sprite:
            type: str
            default: ''
        subimage:
            type: int
            default: 0
        speed:
            type: int
            default: 1
    transform_sprite:
        apply_to: common_apply_to
        horizontal_scale:
            type: float
            default: 1.0
        vertical_scale:
            type: float
            default: 1.0
        rotation:
            type: float
            default: 0.0
        mirror:
            type: bool
            default: False
    color_sprite:
        apply_to: common_apply_to
        color:
            type: str
            default: '#000000'
        opacity:
            type: float
            default: 1.0
"""

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize an ObjectAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("ObjectAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name,
                        self.OBJECT_ACTION_DATA_YAML,
                        settings, **kwargs)


class SoundAction(Action):
    """
    Wrap sound-related actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    SOUND_ACTIONS = [
        "play_sound",
        "stop_sound",
        "if_sound_is_playing"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = SOUND_ACTIONS

    SOUND_ACTION_DATA_YAML = """
actions:
    play_sound:
        sound:
            type: str
            default: ''
        loop:
            type: bool
            default: False
    stop_sound:
        sound:
            type: str
            default: ''
    if_sound_is_playing:
        sound:
            type: str
            default: ''
        invert: common_invert
"""

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize a SoundAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("SoundAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name,
                        self.SOUND_ACTION_DATA_YAML,
                        settings, **kwargs)


class RoomAction(Action):
    """
    Wrap room-related actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    ROOM_ACTIONS = [
        "goto_previous_room",
        "goto_next_room",
        "restart_current_room",
        "goto_room",
        "if_previous_room_exists",
        "if_next_room_exists"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = ROOM_ACTIONS
    DEFAULT_ROOM = 0
    ROOM_ACTION_DATA_YAML = """
actions:
    goto_previous_room:
        transition: common_transition
    goto_next_room:
        transition: common_transition
    restart_current_room:
        transition: common_transition
    goto_room:
        new_room:
            type: str
            default: ''
        transition: common_transition
    if_previous_room_exists:
        invert: common_invert
    if_next_room_exists:
        invert: common_invert
"""

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize a RoomAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("RoomAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name,
                        self.ROOM_ACTION_DATA_YAML,
                        settings, **kwargs)


class TimingAction(Action):
    """
    Wrap timing-related actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    TIMING_ACTIONS = [
        "set_alarm",
        "sleep",
        "set_timeline",
        "set_timeline_location",
        "set_timeline_speed",
        "start_resume_timeline",
        "pause_timeline",
        "stop_timeline"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = TIMING_ACTIONS
    DEFAULT_ALARM = 0
    DEFAULT_SLEEP = 0.1
    DEFAULT_TIMELINE = 0
    DEFAULT_TIMELINE_STEP = 0
    TIMING_ACTION_DATA_YAML = """
actions:
    set_alarm:
        apply_to: common_apply_to
        steps:
            type: int
            default: 0
        alarm:
            type: int
            default: 0
    sleep:
        milliseconds:
            type: int
            default: 1000
        redraw:
            type: bool
            default: True
    set_timeline:
        timeline:
            type: str
            default: ''
        position:
            type: int
            default: 0
        start:
            type: bool
            default: True
        loop:
            type: bool
            default: False
    set_timeline_location:
        apply_to: common_apply_to
        position:
            type: int
            default: 0
        relative: common_relative
    set_timeline_speed:
        apply_to: common_apply_to
        speed:
            type: int
            default: 1
        relative: common_relative
    start_resume_timeline:
        apply_to: common_apply_to
    pause_timeline:
        apply_to: common_apply_to
    stop_timeline:
        apply_to: common_apply_to
"""

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize a TimingAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("TimingAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name,
                        self.TIMING_ACTION_DATA_YAML,
                        settings, **kwargs)


class InfoAction(Action):
    """
    Wrap information display actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    INFO_ACTIONS = [
        "debug",
        "display_message",
        "show_game_info",
        "show_video"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = INFO_ACTIONS
    INFO_ACTION_DATA_YAML = """
actions:
    debug:
        message:
            type: str
            default: ''
    display_message:
        message:
            type: str
            default: ''
    show_game_info: {}
    show_video:
        filename:
            type: str
            default: ''
        full_screen:
            type: bool
            default: False
        loop:
            type: bool
            default: False
"""

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize an InfoAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("InfoAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name,
                        self.INFO_ACTION_DATA_YAML,
                        settings, **kwargs)


class GameAction(Action):
    """
    Wrap game control actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    GAME_ACTIONS = [
        "restart_game",
        "end_game",
        "save_game",
        "load_game"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = GAME_ACTIONS
    GAME_ACTION_DATA_YAML = """
actions:
    restart_game: {}
    end_game: {}
    save_game:
        filename:
            type: str
            default: savegame
    load_game:
        filename:
            type: str
            default: savegame
"""

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize a GameAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("GameAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name,
                        self.GAME_ACTION_DATA_YAML,
                        settings, **kwargs)


class ResourceAction(Action):
    """
    Wrap resource actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    RESOURCE_ACTIONS = [
        "replace_sprite_with_file",
        "replace_sound_with_file",
        "replace_background_with_file"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = RESOURCE_ACTIONS

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize a ResourceAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("ResourceAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name,
                        "",
                        settings, **kwargs)


class QuestionAction(Action):
    """
    Wrap query actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    QUESTION_ACTIONS = [
        "if_collision_at_location",
        "if_collision_at_location",
        "if_object_at_location",
        "if_number_of_instances",
        "if_random_chance",
        "if_user_answers_yes",
        "if_expression",
        "if_mouse_button_is_pressed",
        "if_instance_aligned_with_grid"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = QUESTION_ACTIONS

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize a QuestionAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("QuestionAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name,
                        "",
                        settings, **kwargs)


class OtherAction(Action):
    """
    Wrap action sequence control actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    OTHER_ACTIONS = [
        "start_of_block",
        "else",
        "exit_event",
        "end_of_block",
        "repeat_next_action"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = OTHER_ACTIONS
    OTHER_ACTION_DATA_MAP = {
        "start_of_block": {},
        "else": {},
        "exit_event": {},
        "end_of_block": {},
        "repeat_next_action": {}
    }
    OTHER_ACTION_DATA_YAML = """
actions:
    start_of_block: {}
    else: {}
    exit_event: {}
    end_of_block: {}
    repeat_next_action: {}
"""

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize an OtherAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("OtherAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name,
                        self.OTHER_ACTION_DATA_YAML,
                        settings, **kwargs)
        # handle blocks
        if action_name == "start_of_block":
            self.nest_adjustment = "nest_until_block_end"
        elif action_name == "end_of_block":
            self.nest_adjustment = "block_end"


class CodeAction(Action):
    """
    Wrap code and script execution actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    CODE_ACTIONS = [
        "execute_code",
        "execute_script"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = CODE_ACTIONS

    CODE_ACTION_DATA_YAML = """
actions:
    execute_code:
        apply_to: common_apply_to
        code:
            type: str
            default: ''
    execute_script:
        apply_to: common_apply_to
        script:
            type: str
            default: ''
        parameters:
            type: str
            default: ''
"""

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize a CodeAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("CodeAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name,
                        self.CODE_ACTION_DATA_YAML,
                        settings, **kwargs)


class VariableAction(Action):
    """
    Wrap variable set, test, and display actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    VARIABLE_ACTIONS = [
        "set_variable_value",
        "if_variable_value",
        "draw_variable_value"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = VARIABLE_ACTIONS
    VARIABLE_ACTION_DATA_YAML = """
actions:
    set_variable_value:
        apply_to: common_apply_to
        variable:
            type: str
            default: test
        value:
            type: str
            default: '0'
        is_global:
            type: bool
            default: False
        relative: common_relative
    if_variable_value:
        apply_to: common_apply_to
        variable:
            type: str
            default: test
        test: common_test
        value:
            type: str
            default: '0'
        invert: common_invert
    draw_variable_value:
        apply_to: common_apply_to
        variable:
            type: str
            default: test
        position.x: common_position
        position.y: common_position
        relative: common_relative
"""

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize a VariableAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("VariableAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name,
                        self.VARIABLE_ACTION_DATA_YAML,
                        settings, **kwargs)


class AccountingAction(Action):
    """
    Wrap game accounting actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    SCORE_ACTIONS = [
        "set_score_value",
        "if_score_value",
        "draw_score_value",
        "show_highscore_table",
        "clear_highscore_table"
    ]
    LIFE_ACTIONS = [
        "set_lives_value",
        "if_lives_value",
        "draw_lives_value",
        "draw_lives_image"
    ]
    HEALTH_ACTIONS = [
        "set_health_value",
        "if_health_value",
        "draw_health_bar",
        "set_window_caption"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = SCORE_ACTIONS + LIFE_ACTIONS + HEALTH_ACTIONS
    SCORE_OPERATIONS = [
        "is_equal",
        "is_less_than",
        "is_greater_than",
        "is_less_than_or_equal",
        "is_greater_than_or_equal",
    ]

    ACCOUNTING_ACTION_DATA_YAML = """
actions:
    set_score_value:
        score:
            type: int
            default: 0
        relative: common_relative
    if_score_value:
        score:
            type: int
            default: 0
        test: common_test
        invert: common_invert
    draw_score_value:
        position.x: common_position
        position.y: common_position
        caption:
            type: str
            default: 'Score:'
        relative: common_relative
    show_highscore_table:
        background:
            type: str
            default: ''
        border:
            type: bool
            default: True
        new_color:
            type: str
            default: '#ff0000'
        other_color:
            type: str
            default: '#ffffff'
        font:
            type: str
            default: ''
    clear_highscore_table: {}
    set_lives_value:
        lives:
            type: int
            default: 0
        relative: common_relative
    if_lives_value:
        lives:
            type: int
            default: 0
        test: common_test
        invert: common_invert
    draw_lives_value:
        position.x: common_position
        position.y: common_position
        caption:
            type: str
            default: 'Lives:'
        relative: common_relative
    draw_lives_image:
        position.x: common_position
        position.y: common_position
        sprite:
            type: str
            default: ''
        relative: common_relative
    set_health_value:
        value:
            type: int
            default: 0
        relative: common_relative
    if_health_value:
        value:
            type: int
            default: 0
        test: common_test
        invert: common_invert
    draw_health_bar:
        x1:
            type: int
            default: 0
        y1:
            type: int
            default: 0
        x2:
            type: int
            default: 0
        y2:
            type: int
            default: 0
        back_color:
            type: str
            default: ''
        bar_color_min:
            type: str
            default: "#ff0000"
        bar_color_max:
            type: str
            default: "#00ff00"
        relative: common_relative
    set_window_caption:
        show_score:
            type: bool
            default: True
        score_caption:
            type: str
            default: 'score:'
        show_lives:
            type: bool
            default: True
        lives_caption:
            type: str
            default: 'lives:'
        show_health:
            type: bool
            default: True
        health_caption:
            type: str
            default: 'health:'
"""

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize an AccountingAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("AccountingAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name,
                        self.ACCOUNTING_ACTION_DATA_YAML,
                        settings, **kwargs)


class ParticleAction(Action):
    """
    Wrap particle field actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    PARTICLE_ACTIONS = [
        "create_particle_system",
        "destroy_particle_system",
        "clear_all_particles",
        "create_particle_type",
        "set_particle_type_color",
        "set_particle_type_lifetime",
        "set_particle_type_velocity",
        "set_particle_type_gravity",
        "create_secondary_particle_type",
        "create_particle_emitter",
        "destroy_particle_emitter",
        "burst_particles",
        "stream_particles"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = PARTICLE_ACTIONS

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize a ParticleAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("ParticleAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name, "",
                        settings, **kwargs)


class DrawAction(Action):
    """
    Wrap drawing actions.

    :param action_name: Name for the new action of this type
    :type action_name: str
    :param settings_dict: Optional map of parameter values
    :type settings_dict: dict
    :param kwargs: Set parameter values using named arguments
    """
    DRAW_ACTIONS = [
        "draw_self",
        "draw_sprite_at_location",
        "draw_background_at_location",
        "draw_text_at_location",
        "draw_transformed_text_at_location",
        "draw_rectangle",
        "draw_horizontal_gradient",
        "draw_vertical_gradient",
        "draw_ellipse",
        "draw_gradient_ellipse",
        "draw_line",
        "draw_arrow"
    ]
    DRAW_SETTINGS_ACTIONS = [
        "set_draw_color",
        "set_draw_font",
        "set_fullscreen"
    ]
    OTHER_DRAW_ACTIONS = [
        "take_snapshot",
        "create_effect"
    ]
    #: The full list of actions wrapped in this class
    HANDLED_ACTIONS = DRAW_ACTIONS + DRAW_SETTINGS_ACTIONS + OTHER_DRAW_ACTIONS

    DRAW_ACTION_DATA_YAML = """
actions:
    draw_sprite_at_location:
        apply_to: common_apply_to
        sprite:
            type: str
            default: ''
        position.x: common_position
        position.y: common_position
        subimage:
            type: int
            default: -1
        relative: common_relative
    draw_background_at_location:
        background:
            type: str
            default: ''
        position.x: common_position
        position.y: common_position
        tile:
            type: bool
            default: False
        relative: common_relative
    draw_text_at_location:
        apply_to: common_apply_to
        text:
            type: str
            default: ''
        position.x: common_position
        position.y: common_position
        relative: common_relative
    draw_transformed_text_at_location:
        apply_to: common_apply_to
        text:
            type: str
            default: ''
        position.x: common_position
        position.y: common_position
        hor_scale:
            type: float
            default: 1.0
        ver_scale:
            type: float
            default: 1.0
        angle:
            type: float
            default: 0
        relative: common_relative
    draw_rectangle:
        apply_to: common_apply_to
        x1: common_position
        y1: common_position
        x2: common_position
        y2: common_position
        filled:
            type: from_list
            default: filled
            accepted_list: [filled, outline]
        relative: common_relative
    draw_horizontal_gradient:
        apply_to: common_apply_to
        x1: common_position
        y1: common_position
        x2: common_position
        y2: common_position
        color1:
            type: str
            default: #000000
        color2:
            type: str
            default: #FFFFFF
        relative: common_relative
    draw_vertical_gradient:
        apply_to: common_apply_to
        x1: common_position
        y1: common_position
        x2: common_position
        y2: common_position
        color1:
            type: str
            default: #000000
        color2:
            type: str
            default: #FFFFFF
        relative: common_relative
    draw_ellipse:
        apply_to: common_apply_to
        x1: common_position
        y1: common_position
        x2: common_position
        y2: common_position
        filled:
            type: from_list
            default: filled
            accepted_list: [filled, outline]
        relative: common_relative
    draw_gradient_ellipse:
        apply_to: common_apply_to
        x1: common_position
        y1: common_position
        x2: common_position
        y2: common_position
        color1:
            type: str
            default: #000000
        color2:
            type: str
            default: #FFFFFF
        relative: common_relative
    draw_line:
        apply_to: common_apply_to
        x1: common_position
        y1: common_position
        x2: common_position
        y2: common_position
        relative: common_relative
    draw_arrow:
        apply_to: common_apply_to
        x1: common_position
        y1: common_position
        x2: common_position
        y2: common_position
        tip_size:
            type: int
            default: 12
        relative: common_relative
    set_draw_color:
        color:
            type: str
            default: #000000
    set_draw_font:
        font:
            type: str
            default: ''
        alignment:
            type: from_list
            default: left
            accepted_list: [left, center, right]
    set_fullscreen:
        screen_size:
            type: from_list
            default: toggle
            accepted_list: [toggle, windowed, fullscreen]
    take_snapshot:
        filename:
            type: str
            default: 'snapshot.png'
    create_effect:
        apply_to: common_apply_to
        effect_type:
            type: from_list
            default: explosion
            accepted_list:
                - explosion
                - ring
                - ellipse
                - firework
                - smoke
                - smoke_up
                - star
                - spark
                - flare
                - cloud
                - rain
                - snow
        position.x: common_position
        position.y: common_position
        size:
            type: from_list
            default: medium
            accepted_list: [small, medium, large]
        color:
            type: str
            default: #000000
        positioning:
            type: from_list
            default: foreground
            accepted_list: [foreground, background]
        relative: common_relative
"""

    def __init__(self, action_name, settings_dict=None, **kwargs):
        """
        Initialize a DrawAction instance.

        :param action_name: Name for the new action of this type
        :type action_name: str
        :param settings_dict: Optional map of parameter values
        :type settings_dict: dict
        :param kwargs: Set parameter values using named arguments
        """
        settings = {}
        if settings_dict is not None:
            settings = settings_dict
        if action_name not in self.HANDLED_ACTIONS:
            raise ActionException("DrawAction: Unknown action '{}'".format(action_name))
        Action.__init__(self, action_name,
                        self.DRAW_ACTION_DATA_YAML,
                        settings, **kwargs)
        self.action_data['draw_self'] = {}

# make it possible to request an action from any action type
Action.register_new_action_type(MotionAction)
Action.register_new_action_type(ObjectAction)
Action.register_new_action_type(RoomAction)
Action.register_new_action_type(SoundAction)
Action.register_new_action_type(TimingAction)
Action.register_new_action_type(InfoAction)
Action.register_new_action_type(GameAction)
Action.register_new_action_type(ResourceAction)
Action.register_new_action_type(QuestionAction)
Action.register_new_action_type(OtherAction)
Action.register_new_action_type(CodeAction)
Action.register_new_action_type(VariableAction)
Action.register_new_action_type(AccountingAction)
Action.register_new_action_type(ParticleAction)
Action.register_new_action_type(DrawAction)
