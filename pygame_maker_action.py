#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# represent a PyGameMaker action that executes following an event

import pygame
import yaml
import re
import sys
from pygame_maker_language_engine import PyGameMakerSymbolTable

class PyGameMakerActionException(Exception):
    pass

class PyGameMakerActionParameterException(Exception):
    pass

class PyGameMakerAction(object):
    """Base class for actions"""
    DEFAULT_POINT_XY=(0,0)
    DEFAULT_SPEED=0
    DEFAULT_DIRECTION=0
    DEFAULT_GRAVITY=0.1
    DEFAULT_FRICTION=0.1
    DEFAULT_GRID_SNAP_XY=(16, 16)
    DEFAULT_WRAP_DIRECTION="HORIZONTAL"
    DEFAULT_PATH=None
    DEFAULT_PATH_LOCATION=0
    DEFAULT_COLLISION_TYPE="solid"
    DEFAULT_PRECISION_TYPE="imprecise"
    COMPASS_DIRECTIONS=[
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
    COMPASS_DIRECTION_DEGREES={
        "UPLEFT"    : 315,
        "UP"        : 0,
        "UPRIGHT"   : 45,
        "RIGHT"     : 90,
        "DOWNRIGHT" : 135,
        "DOWN"      : 180,
        "DOWNLEFT"  : 225,
        "LEFT"      : 270
    }
    HORIZONTAL_DIRECTIONS=["LEFT", "RIGHT"]
    VERTICAL_DIRECTIONS=["UP", "DOWN"]
    WRAP_DIRECTIONS=[
        "HORIZONTAL",
        "VERTICAL",
        "BOTH"
    ]
    COLLISION_TYPES=[
        "solid",
        "any"
    ]
    PRECISION_TYPES=[
        "precise",
        "imprecise"
    ]
    PATH_END_ACTIONS=[
        "stop",
        "continue_from_start",
        "continue_from_here",
        "reverse"
    ]
    ACTION_BLOCK_NEST_LEVEL_ADJUSTMENTS=[
        "nest_next_action",
        "nest_until_block_end",
        "block_end"
    ]
    COMMON_DATA_YAML="""
common_parameters:
    common_apply_to:
        type: from_list
        default: self
        accepted_list:
            - self
            - other
            - object_name
    common_relative:
        type: bool
        default: False
    common_speed:
        type: float
        default: '0.0'
    common_position:
        type: int
        default: '0'
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
        accepted_list:
            - solid
            - any
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
    IF_STATEMENT_RE=re.compile("^if_")
    TUPLE_RE=re.compile("\(([^)]+)\)")
    COMMON_RE=re.compile("^common_")

    action_type_registry = []

    @classmethod
    def register_new_action_type(cls, actiontype):
        """
            Register a class (at init time) to make it possible to search
            through them for a particular action name
        """
        cls.action_type_registry.append(actiontype)

    @classmethod
    def get_action_instance_by_action_name(cls, action_name, settings_dict={},
        **kwargs):
        if len(cls.action_type_registry) > 0:
            for atype in cls.action_type_registry:
                if action_name in atype.HANDLED_ACTIONS:
                    return atype(action_name, settings_dict, **kwargs)
        # no action type handles the named action
        raise PyGameMakerActionException("Action '{}' is unknown".format(action_name))

    def __init__(self, action_name, action_yaml, settings_dict={}, **kwargs):
        """
            Supply the basic properties for all actions
        """
        self.name = action_name
        self.action_data = {}
        self.action_constraints = {}
        self.runtime_data = {}
        args = {}
        args.update(settings_dict)
        args.update(kwargs)
        data_map, data_constraints = self.collect_parameter_yaml_info(action_yaml+self.COMMON_DATA_YAML)
        if action_name in data_map:
            self.action_data.update(data_map[action_name])
        if action_name in data_constraints:
            self.action_constraints.update(data_constraints[action_name])
        # default: don't nest subsequent action(s)
        minfo = self.IF_STATEMENT_RE.search(action_name)
        if minfo or (action_name == "else"):
            # automatically nest after question tasks
            self.nest_adjustment = "nest_next_action"
            if minfo:
                self.action_result = True
        else:
            self.nest_adjustment = None
        for param in args:
            if param in self.action_data:
                self.action_data[param] = args[param]

    def check_value_vs_constraint(self, value, constraint):
        fall_back_to_code_block = False
        typed_val = None
        if constraint['type'] == 'int':
            try:
                typed_val = int(value)
            except:
                fall_back_to_code_block = True
        elif constraint['type'] == 'float':
            try:
                typed_val = float(value)
            except:
                fall_back_to_code_block = True
        elif constraint['type'] == 'bool':
            typed_val = bool(value)
        elif constraint['type'] == 'from_list':
            if not value in constraint['accepted_list']:
                print("WARNING: default value '{}' is not in the list of accepted values '{}'".format(par_val['default'], par_val['accepted_list']))

    def collect_parameter_yaml_info(self, yaml_str):
        action_map = {}
        action_constraints = {}
        yaml_obj = yaml.load(yaml_str)
        common_params = yaml_obj['common_parameters']
        #print("Got common params:\n{}".format(common_params))
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
                        if not par_val['default'] in par_val['accepted_list']:
                            print("WARNING: default value '{}' is not in the list of accepted values '{}'".format(par_val['default'], par_val['accepted_list']))
                    action_map[action][par] = par_val['default']
                    action_constraints[action] = par_val
        #print("Got action_map:\n{}".format(action_map))
        #print("Got action_constraints:\n{}".format(action_constraints))
        parm_info = (action_map, action_constraints)
        return parm_info

    def get_parameter_expression_result(self, field_name, symbols,
        language_engine):
        """
            get_parameter_expression_result():
            Given a field name possibly containing an expression, register the
            expression with the language engine and execute the code, and
            return the result. Using spreadsheet formula scheme for indication
            an expression to execute: first char is '='.
             Parameters:
              field_name (string): The field containing the expression
              symbols (PyGameMakerSymbolTable): The symbols available to the
               code block
              language_engine (PyGameMakerLanguageEngine): The language engine
               instance
             Returns:
              The result from the expression
        """
        result = None
        if (not isinstance(self.action_data[field_name], str) or
            (self.action_data[field_name][0] != '=')):
            # not an expression, so just return the contents of the field
            return self.action_data[field_name]
        exp_name = "{}_block".format(field_name)
        #print("check for code block {}".format(exp_name))
        # create a hopefully unique symbol to store the expression result in
        sym_name = "intern_{}_{}".format(field_name, hash(field_name))
        #print("sym_name: {}".format(sym_name))
        if not exp_name in self.runtime_data.keys():
            # create an entry in the action data that points to a
            #  hopefully unique name that will be registered with the language
            #  engine
            exp_id = "{}_{}_{}".format(self.name,
                re.sub("\.", "_", field_name), id(self))
            #print("register new code block {}".format(exp_id))
            expression_code = "{} = {}".format(sym_name,
                self.action_data[field_name][1:])
            language_engine.register_code_block(exp_id, expression_code)
            self.runtime_data[exp_name] = exp_id
        # execute the expression and collect its result
        local_symbols = PyGameMakerSymbolTable(symbols)
        language_engine.execute_code_block(self.runtime_data[exp_name],
            local_symbols)
        #print("{} = {}".format(sym_name, local_symbols[sym_name]))
        return local_symbols[sym_name]

    def to_yaml(self, indent=0):
        indent_str=" "*indent
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

    def __getitem__(self, itemname):
        """
            Forward PyGameMakerAction[key] to the action_data member for
            convenience
        """
        val = None
        if not itemname in self.action_data:
            if not itemname in self.runtime_data:
                raise KeyError("{}".format(itemname))
            val = self.runtime_data[itemname]
        else:
            val = self.action_data[itemname]
        return val

    def __setitem__(self, itemname, value):
        """
            Allow action data to be modified.
        """
        if not itemname in self.action_data:
            # fall back to runtime data. this is data that is not serialized.
            self.runtime_data[itemname] = value
        self.action_data[itemname] = value

    def __repr__(self):
        return "<{} '{}': {}>".format(type(self).__name__, self.name,
            self.action_data)

    def __eq__(self, other):
        return(isinstance(other, PyGameMakerAction) and
            (self.name == other.name) and
            (self.action_data == other.action_data))

class PyGameMakerMotionAction(PyGameMakerAction):
    MOVE_ACTIONS=[
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
    JUMP_ACTIONS=[
        "jump_to",
        "jump_to_start",
        "jump_random",
        "snap_to_grid",
        "wrap_around",
        "move_until_collision",
        "bounce_off_collider"
    ]
    PATH_ACTIONS=[
        "set_path",
        "end_path",
        "set_location_on_path",
        "set_path_speed"
    ]
    STEP_ACTIONS=[
        "step_toward_point",
        "step_toward_point_around_objects"
    ]
    HANDLED_ACTIONS=MOVE_ACTIONS + JUMP_ACTIONS + PATH_ACTIONS + STEP_ACTIONS
    MOTION_ACTION_DATA_YAML="""
actions:
    set_velocity_compass:
        apply_to: common_apply_to
        compass_directions: common_compass_direction
        speed: common_speed
    set_velocity_degrees:
        apply_to: common_apply_to
        direction:
            type: float
            default: '0.0'
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
            accepted_list:
                - right
                - left
        horizontal_speed: common_speed
        relative: common_relative
    set_vertical_speed:
        apply_to: common_apply_to
        vertical_direction:
            type: from_list
            default: up
            accepted_list:
                - up
                - down
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
            accepted_list:
                - horizontal
                - vertical
                - both
    move_until_collision:
        apply_to: common_apply_to
        direction:
            type: float
            default: '0.0'
        max_distance:
            type: int
            default: '-1'
        stop_at_collision_type:
            common_collision_type
    bounce_off_collider:
        apply_to: common_apply_to
        precision:
            type: from_list
            default: imprecise
            accepted_list:
                - precise
                - imprecise
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
            default: '0'
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

    def __init__(self, action_name, settings_dict={}, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerMotionAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.MOTION_ACTION_DATA_YAML,
            settings_dict, **kwargs)
        #print("Created new action {}".format(self))
        # self.action_data = self.MOTION_ACTION_DATA_MAP[action_name]

class PyGameMakerObjectAction(PyGameMakerAction):
    OBJECT_ACTIONS=[
        "create_object",
        "create_object_with_velocity",
        "create_random_object",
        "transform_object",
        "destroy_object",
        "destroy_instances_at_location"
    ]
    SPRITE_ACTIONS=[
        "set_sprite",
        "transform_sprite",
        "color_sprite"
    ]
    HANDLED_ACTIONS=OBJECT_ACTIONS + SPRITE_ACTIONS
    OBJECT_ACTION_DATA_YAML="""
actions:
    create_object:
        object: common_object
        position.x: common_position
        position.y: common_position
        relative: common_relative
    create_object_with_velocity:
        object: common_object
        position.x: common_position
        position.y: common_position
        speed: common_speed
        direction:
            type: float
            default: 0.0
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

    def __init__(self, action_name, settings_dict={}, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerObjectAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.OBJECT_ACTION_DATA_YAML,
            settings_dict, **kwargs)

class PyGameMakerSoundAction(PyGameMakerAction):
    SOUND_ACTIONS=[
        "play_sound",
        "stop_sound",
        "if_sound_is_playing"
    ]
    HANDLED_ACTIONS=SOUND_ACTIONS

    SOUND_ACTION_DATA_YAML="""
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

    def __init__(self, action_name, settings_dict={}, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerSoundAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.SOUND_ACTION_DATA_YAML,
            settings_dict, **kwargs)

class PyGameMakerRoomAction(PyGameMakerAction):
    ROOM_ACTIONS=[
        "goto_previous_room",
        "goto_next_room",
        "restart_current_room",
        "goto_room",
        "if_previous_room_exists",
        "if_next_room_exists"
    ]
    HANDLED_ACTIONS=ROOM_ACTIONS
    DEFAULT_ROOM=0
    ROOM_ACTION_DATA_YAML="""
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

    def __init__(self, action_name, settings_dict={}, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerRoomAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.ROOM_ACTION_DATA_YAML,
            settings_dict, **kwargs)

class PyGameMakerTimingAction(PyGameMakerAction):
    TIMING_ACTIONS=[
        "set_alarm",
        "sleep",
        "set_timeline",
        "set_timeline_location",
        "set_timeline_speed",
        "start_resume_timeline",
        "pause_timeline",
        "stop_timeline"
    ]
    HANDLED_ACTIONS=TIMING_ACTIONS
    DEFAULT_ALARM=0
    DEFAULT_SLEEP=0.1
    DEFAULT_TIMELINE=0
    DEFAULT_TIMELINE_STEP=0
    TIMING_ACTION_DATA_YAML="""
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

    def __init__(self, action_name, settings_dict={}, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerTimingAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.TIMING_ACTION_DATA_YAML,
            settings_dict, **kwargs)

class PyGameMakerInfoAction(PyGameMakerAction):
    INFO_ACTIONS=[
        "display_message",
        "show_game_info",
        "show_video"
    ]
    HANDLED_ACTIONS=INFO_ACTIONS
    INFO_ACTION_DATA_YAML="""
actions:
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

    def __init__(self, action_name, settings_dict={}, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerInfoAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.INFO_ACTION_DATA_YAML,
            settings_dict, **kwargs)

class PyGameMakerGameAction(PyGameMakerAction):
    GAME_ACTIONS=[
        "restart_game",
        "end_game",
        "save_game",
        "load_game"
    ]
    HANDLED_ACTIONS=GAME_ACTIONS
    GAME_ACTION_DATA_YAML="""
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

    def __init__(self, action_name, settings_dict={}, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerGameAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.GAME_ACTION_DATA_YAML,
            settings_dict, **kwargs)

class PyGameMakerResourceAction(PyGameMakerAction):
    RESOURCE_ACTIONS=[
        "replace_sprite_with_file",
        "replace_sound_with_file",
        "replace_background_with_file"
    ]
    HANDLED_ACTIONS=RESOURCE_ACTIONS

    def __init__(self, action_name, settings_dict={}):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerResourceAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name, {}, {},
            settings_dict, **kwargs)

class PyGameMakerQuestionAction(PyGameMakerAction):
    QUESTION_ACTIONS=[
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
    HANDLED_ACTIONS=QUESTION_ACTIONS

    def __init__(self, action_name ,settings_dict={}):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerQuestionAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name, {}, {},
            settings_dict, **kwargs)

class PyGameMakerOtherAction(PyGameMakerAction):
    OTHER_ACTIONS=[
        "start_of_block",
        "else",
        "exit_event",
        "end_of_block",
        "repeat_next_action"
    ]
    HANDLED_ACTIONS=OTHER_ACTIONS
    OTHER_ACTION_DATA_MAP={
        "start_of_block": {},
        "else": {},
        "exit_event": {},
        "end_of_block": {},
        "repeat_next_action": {} 
    }

    def __init__(self, action_name, settings_dict={}, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerOtherAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
		self.OTHER_ACTION_DATA_MAP[action_name], {},
                settings_dict, **kwargs)
        # handle blocks
        if action_name == "start_of_block":
            self.nest_adjustment = "nest_until_block_end"
        elif action_name == "end_of_block":
            self.nest_adjustment = "block_end"

class PyGameMakerCodeAction(PyGameMakerAction):
    CODE_ACTIONS=[
        "execute_code",
        "execute_script"
    ]
    HANDLED_ACTIONS=CODE_ACTIONS

    CODE_ACTION_DATA_YAML="""
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

    def __init__(self, action_name, settings_dict={}, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerCodeAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.CODE_ACTION_DATA_YAML,
            settings_dict, **kwargs)

class PyGameMakerVariableAction(PyGameMakerAction):
    VARIABLE_ACTIONS=[
        "set_variable_value",
        "if_variable_value",
        "draw_variable_value"
    ]
    HANDLED_ACTIONS=VARIABLE_ACTIONS
    VARIABLE_ACTION_DATA_YAML="""
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

    def __init__(self, action_name, settings_dict={}, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerVariableAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.VARIABLE_ACTION_DATA_YAML,
            settings_dict, **kwargs)

class PyGameMakerAccountingAction(PyGameMakerAction):
    SCORE_ACTIONS=[
        "set_score_value",
        "if_score_value",
        "draw_score_value",
        "show_highscore_table",
        "clear_highscore_table"
    ]
    LIFE_ACTIONS=[
        "set_lives_value",
        "if_lives_value",
        "draw_lives_value",
        "draw_lives_image"
    ]
    HEALTH_ACTIONS=[
        "set_health_value",
        "if_health_value",
        "draw_health_bar",
        "set_window_caption"
    ]
    HANDLED_ACTIONS=SCORE_ACTIONS + LIFE_ACTIONS + HEALTH_ACTIONS
    SCORE_OPERATIONS=[
        "is_equal",
        "is_less_than",
        "is_greater_than",
        "is_less_than_or_equal",
        "is_greater_than_or_equal",
    ]

    ACCOUNTING_ACTION_DATA_YAML="""
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

    def __init__(self, action_name, settings_dict={}, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerAccountingAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.ACCOUNTING_ACTION_DATA_YAML,
            settings_dict, **kwargs)

class PyGameMakerParticleAction(PyGameMakerAction):
    PARTICLE_ACTIONS=[
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
    HANDLED_ACTIONS=PARTICLE_ACTIONS

    def __init__(self, action_name, settings_dict={}, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerParticleAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name, {}, {},
            settings_dict, **kwargs)

class PyGameMakerDrawAction(PyGameMakerAction):
    DRAW_ACTIONS=[
        "draw_self",
        "draw_sprite_at_location",
        "draw_background_at_location",
        "draw_text_at_location",
        "draw_transformed_text_at_location",
        "draw_rectangle",
        "draw_horizontal_gradient",
        "draw_vertical_gradient",
        "draw_ellipse",
        "draw_gradient_ellipse"<
        "draw_line",
        "draw_arrow"
    ]
    DRAW_SETTINGS_ACTIONS=[
        "set_draw_color",
        "set_draw_font",
        "set_fullscreen"
    ]
    OTHER_DRAW_ACTIONS=[
        "take_snapshot",
        "create_effect"
    ]
    HANDLED_ACTIONS=DRAW_ACTIONS + DRAW_SETTINGS_ACTIONS + OTHER_DRAW_ACTIONS

    def __init__(self, action_name, settings_dict={}, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerDrawAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name, {}, {},
            settings_dict, **kwargs)

# make it possible to request an action from any action type
PyGameMakerAction.register_new_action_type(PyGameMakerMotionAction)
PyGameMakerAction.register_new_action_type(PyGameMakerObjectAction)
PyGameMakerAction.register_new_action_type(PyGameMakerRoomAction)
PyGameMakerAction.register_new_action_type(PyGameMakerSoundAction)
PyGameMakerAction.register_new_action_type(PyGameMakerTimingAction)
PyGameMakerAction.register_new_action_type(PyGameMakerInfoAction)
PyGameMakerAction.register_new_action_type(PyGameMakerGameAction)
PyGameMakerAction.register_new_action_type(PyGameMakerResourceAction)
PyGameMakerAction.register_new_action_type(PyGameMakerQuestionAction)
PyGameMakerAction.register_new_action_type(PyGameMakerOtherAction)
PyGameMakerAction.register_new_action_type(PyGameMakerCodeAction)
PyGameMakerAction.register_new_action_type(PyGameMakerVariableAction)
PyGameMakerAction.register_new_action_type(PyGameMakerAccountingAction)
PyGameMakerAction.register_new_action_type(PyGameMakerParticleAction)
PyGameMakerAction.register_new_action_type(PyGameMakerDrawAction)

if __name__ == "__main__":
    import unittest

    class TestPyGameMakerAction(unittest.TestCase):

        def setUp(self):
            pass

        def test_003find_action_by_name(self):
            motion_action = PyGameMakerAction.get_action_instance_by_action_name("set_velocity_compass", compass_directions="DOWN")
            self.assertEqual(motion_action["compass_directions"], "DOWN")
            print("action: {}".format(motion_action))

        def test_005valid_motion_action(self):
            good_action = PyGameMakerMotionAction("set_velocity_degrees", speed=5)
            self.assertEqual(good_action["speed"], 5)
            print("action: {}".format(good_action))

        def test_010valid_object_action(self):
            object_action = PyGameMakerObjectAction("create_object",
                { 'position.x':250, 'position.y':250 } )
            self.assertEqual(object_action["position.x"], 250)
            self.assertEqual(object_action["position.y"], 250)
            print("action: {}".format(object_action))

        def test_015valid_sound_action(self):
            sound_action = PyGameMakerSoundAction("play_sound", loop=True)
            self.assertTrue(sound_action["loop"])
            print("action: {}".format(sound_action))

        def test_020valid_code_action(self):
            code_string = "print(\"this is a test\")"
            code_action = PyGameMakerCodeAction("execute_code",
                code=code_string)
            self.assertEqual(code_action["code"], code_string)
            print("action {}".format(code_action))

        def test_025valid_accounting_action(self):
            accounting_action = PyGameMakerAccountingAction("set_score_value",
                score=1, relative=True)
            self.assertEqual(accounting_action["score"], 1)
            self.assertTrue(accounting_action["relative"])
            print("action {}".format(accounting_action))

        def test_030invert(self):
            if_sound_action = PyGameMakerSoundAction("if_sound_is_playing")
            if_sound_action2 = PyGameMakerSoundAction("if_sound_is_playing",
                invert=True)
            self.assertEqual(if_sound_action.name, "if_sound_is_playing")
            self.assertFalse(if_sound_action["invert"])
            self.assertTrue(if_sound_action2["invert"])

        def test_035to_yaml(self):
            test_action = PyGameMakerMotionAction('jump_to', relative=True)
            test_yaml="""  jump_to:
    apply_to: self
    position.x: 0
    position.y: 0
    relative: True
"""
            self.assertEqual(test_action.to_yaml(2), test_yaml)
            yaml_in = yaml.load(test_action.to_yaml())
            print("{}".format(yaml_in))
            print("{}".format(test_action.to_yaml(2)))
            code_str="""code line 1
code line 2
  indented line 1
  indented line 2
code line 3"""
            test_action2 = PyGameMakerCodeAction('execute_code',
                code=code_str)
            test_yaml2="""  execute_code:
    apply_to: self
    code: |
      code line 1
      code line 2
        indented line 1
        indented line 2
      code line 3
"""
            self.assertEqual(test_action2.to_yaml(2), test_yaml2)
            yaml_in2 = yaml.load(test_action2.to_yaml())
            print("{}".format(yaml_in2))
            print("{}".format(test_action2.to_yaml(2)))

        def test_040valid_room_action(self):
            room_action = PyGameMakerRoomAction("goto_next_room",
                transition="create_from_top")
            self.assertEqual(room_action.name, "goto_next_room")
            self.assertEqual(room_action["transition"], "create_from_top")
            print("action {}".format(room_action))

        def test_045valid_timing_action(self):
            timing_action = PyGameMakerTimingAction("set_alarm",
                steps=30, alarm=1)
            self.assertEqual(timing_action.name, "set_alarm")
            self.assertEqual(timing_action["steps"], 30)
            self.assertEqual(timing_action["alarm"], 1)

        def test_050valid_info_action(self):
            info_action = PyGameMakerInfoAction("show_game_info")
            self.assertEqual(info_action.name, "show_game_info")

        def test_055valid_game_action(self):
            game_action = PyGameMakerGameAction("load_game", filename="game0")
            self.assertEqual(game_action.name, "load_game")
            self.assertEqual(game_action["filename"], "game0")

        def test_060valid_variable_action(self):
            variable_action = PyGameMakerVariableAction("set_variable_value",
                value='20', variable='ammo', is_global=True)
            self.assertEqual(variable_action.name, "set_variable_value")
            self.assertEqual(variable_action["value"], "20")
            self.assertEqual(variable_action["variable"], 'ammo')
            self.assertTrue(variable_action["is_global"])

    unittest.main()

