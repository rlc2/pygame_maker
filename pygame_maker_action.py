#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# represent a PyGameMaker action that executes following an event

import pygame
import re

class PyGameMakerActionException(Exception):
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
    VERTICAL_DIRECTIONS=["LEFT", "RIGHT"]
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
    NESTED_STATEMENT_RE=re.compile("^if_")

    action_type_registry = []

    @classmethod
    def register_new_action_type(cls, actiontype):
        """
            Register a class (at init time) to make it possible to search
            through them for a particular action name
        """
        cls.action_type_registry.append(actiontype)

    @classmethod
    def get_action_instance_by_action_name(cls, action_name, **kwargs):
        if len(cls.action_type_registry) > 0:
            for atype in cls.action_type_registry:
                if action_name in atype.HANDLED_ACTIONS:
                    return atype(action_name, **kwargs)
        # no action type handles the named action
        raise PyGameMakerActionException("Action '{}' is unknown".format(action_name))

    def __init__(self, action_name="", action_data={}, **kwargs):
        """
            Supply the basic properties for all actions
        """
        self.name = action_name
        self.action_data = {}
        self.action_data.update(action_data)
        # default: don't nest subsequent action(s)
        minfo = self.NESTED_STATEMENT_RE.search(action_name)
        if minfo:
            # automatically nest after question tasks
            self.nest_adjustment = "nest_next_action"
        else:
            self.nest_adjustment = None
        for param in kwargs:
            if param in self.action_data:
                self.action_data[param] = kwargs[param]

    def __getitem__(self, itemname):
        """
            Forward PyGameMakerAction[key] to the action_data member for
            convenience
        """
        if not itemname in self.action_data:
            raise PyGameMakerActionException
        return self.action_data[itemname]

    def __repr__(self):
        return "<{} '{}': {}>".format(type(self).__name__, self.name,
            self.action_data)

class PyGameMakerMotionAction(PyGameMakerAction):
    MOVE_ACTIONS=[
        "set_velocity_compass",
        "set_velocity_degrees",
        "move_toward_point",
        "move_horizontal",
        "move_vertical",
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
        "jump_to_collider",
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
    MOTION_ACTION_DATA_MAP={
        "set_velocity_compass": {"apply_to": "self", "direction":"UP",
            "speed": PyGameMakerAction.DEFAULT_SPEED, "relative": False},
        "set_velocity_degrees": {"apply_to": "self",
            "direction": PyGameMakerAction.DEFAULT_DIRECTION,
            "speed": PyGameMakerAction.DEFAULT_SPEED,
            "relative": False},
        "move_toward_point": {"apply_to": "self",
            "locationxy": PyGameMakerAction.DEFAULT_POINT_XY,
            "speed": PyGameMakerAction.DEFAULT_SPEED, "relative": False},
        "move_horizontal": {"apply_to": "self", "direction": "RIGHT",
            "speed": PyGameMakerAction.DEFAULT_SPEED, "relative": False},
        "move_vertical": {"apply_to": "self", "direction": "DOWN",
            "speed": PyGameMakerAction.DEFAULT_SPEED, "relative": False},
        "apply_gravity": {"apply_to": "self", "direction": "DOWN",
            "gravity": PyGameMakerAction.DEFAULT_GRAVITY, "relative": False},
        "reverse_horizontal_speed": {"apply_to": "self"},
        "reverse_vertical_speed": {"apply_to": "self"},
        "set_friction": {"apply_to": "self",
            "friction": PyGameMakerAction.DEFAULT_FRICTION,
            "relative": False},
        "jump_to": {"apply_to": "self",
            "locationxy": PyGameMakerAction.DEFAULT_POINT_XY,
            "relative": False},
        "jump_to_start": {"apply_to": "self"},
        "jump_random": {"apply_to": "self", "snapxy": (0,0) },
        "snap_to_grid": {"apply_to": "self",
        "gridxy": PyGameMakerAction.DEFAULT_GRID_SNAP_XY},
        "wrap_around": {"apply_to": "self",
            "wrap_direction": PyGameMakerAction.DEFAULT_WRAP_DIRECTION},
        "move_until_collision": {"apply_to": "self",
            "direction": PyGameMakerAction.DEFAULT_DIRECTION,
            "max_distance": -1,
            "collision_type": PyGameMakerAction.DEFAULT_COLLISION_TYPE},
        "bounce_off_collider": {"apply_to": "self", "precision": "imprecise",
            "collision_type": PyGameMakerAction.DEFAULT_COLLISION_TYPE},
        "set_path": {"apply_to": "self", "path": PyGameMakerAction.DEFAULT_PATH,
            "speed": PyGameMakerAction.DEFAULT_SPEED,
            "at_end": "stop", "relative": True},
        "end_path": {"apply_to": "self"},
        "set_location_on_path": {"apply_to": "self",
            "location": PyGameMakerAction.DEFAULT_PATH_LOCATION,
            "relative": False},
        "set_path_speed": {"apply_to": "self",
            "speed": PyGameMakerAction.DEFAULT_SPEED,
            "relative": False},
        "step_toward_point": {"apply_to": "self",
            "locationxy": PyGameMakerAction.DEFAULT_POINT_XY,
            "speed": PyGameMakerAction.DEFAULT_SPEED,
            "collision_type": PyGameMakerAction.DEFAULT_COLLISION_TYPE,
            "relative": False },
        "step_toward_point_around_objects": {"apply_to": "self",
            "locationxy": PyGameMakerAction.DEFAULT_POINT_XY,
            "speed": PyGameMakerAction.DEFAULT_SPEED,
            "collision_type": PyGameMakerAction.DEFAULT_COLLISION_TYPE,
            "relative": False }
    }

    def __init__(self, action_name, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerMotionAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.MOTION_ACTION_DATA_MAP[action_name], **kwargs)
        # self.action_data = self.MOTION_ACTION_DATA_MAP[action_name]

class PyGameMakerObjectAction(PyGameMakerAction):
    OBJECT_ACTIONS=[
        "create_object",
        "create_object_with_velocity",
        "create_random_object",
        "transform_self",
        "destroy_self",
        "destroy_instances_at_location"
    ]
    SPRITE_ACTIONS=[
        "set_sprite",
        "transform_sprite",
        "color_sprite"
    ]
    HANDLED_ACTIONS=OBJECT_ACTIONS + SPRITE_ACTIONS
    OBJECT_ACTION_DATA_MAP={
        "create_object": {"apply_to": "self", "object": None,
            "locationxy": PyGameMakerAction.DEFAULT_POINT_XY,
            "relative": False},
        "create_object_with_velocity": {"apply_to": "self", "object": None,
            "locationxy": PyGameMakerAction.DEFAULT_POINT_XY,
            "speed": PyGameMakerAction.DEFAULT_SPEED,
            "direction": PyGameMakerAction.DEFAULT_DIRECTION,
            "relative": False},
        "create_random_object": {"apply_to": "self",
            "locationxy": PyGameMakerAction.DEFAULT_POINT_XY,
            "object_list": [], "relative": False},
        "transform_object": {"apply_to": "self", "object": None,
            "new_object": None, "perform_events": "no"},
        "destroy_object": {"apply_to": "self"},
        "destroy_instances_at_location": {"apply_to": "self",
            "locationxy": PyGameMakerAction.DEFAULT_POINT_XY,
            "relative": False},
        "set_sprite": {"apply_to": "self", "sprite": None, "subimage": 0,
            "speed": 1},
        "transform_sprite": {"apply_to": "self", "horizontal_scale": 1.0,
            "vertical_scale": 1.0, "rotation": 0.0, "mirror": False },
        "color_sprite": {"apply_to": "self", "color": "#000000",
            "opacity": 1.0}
    }

    def __init__(self, action_name, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerObjectAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.OBJECT_ACTION_DATA_MAP[action_name], **kwargs)

class PyGameMakerSoundAction(PyGameMakerAction):
    SOUND_ACTIONS=[
        "play_sound",
        "stop_sound",
        "if_sound_is_playing"
    ]
    HANDLED_ACTIONS=SOUND_ACTIONS

    SOUND_ACTION_DATA_MAP={
        "play_sound": {"sound": None, "loop": False},
        "stop_sound": {"sound": None},
        "if_sound_is_playing": {"sound": None, "invert": False}
    }

    def __init__(self, action_name, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerSoundAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.SOUND_ACTION_DATA_MAP[action_name], **kwargs)

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

    def __init__(self, action_name):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerRoomAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name)

class PyGameMakerTimingAction(PyGameMakerAction):
    TIMING_ACTIONS=[
        "set_alarm",
        "sleep",
        "set_timeline",
        "set_timeline_location",
        "start_resume_timeline",
        "pause_timeline",
        "stop_timeline"
    ]
    HANDLED_ACTIONS=TIMING_ACTIONS
    DEFAULT_ALARM=0
    DEFAULT_SLEEP=0.1
    DEFAULT_TIMELINE=0
    DEFAULT_TIMELINE_STEP=0

    def __init__(self, action_name):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerTimingAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name)

class PyGameMakerInfoAction(PyGameMakerAction):
    INFO_ACTIONS=[
        "display_message",
        "show_game_info",
        "show_video"
    ]
    HANDLED_ACTIONS=INFO_ACTIONS

    def __init__(self, action_name):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerInfoAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name)

class PyGameMakerGameAction(PyGameMakerAction):
    GAME_ACTIONS=[
        "restart_game",
        "end_game",
        "save_game",
        "load_game"
    ]
    HANDLED_ACTIONS=GAME_ACTIONS

    def __init__(self, action_name):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerGameAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name)

class PyGameMakerResourceAction(PyGameMakerAction):
    RESOURCE_ACTIONS=[
        "replace_sprite_with_file",
        "replace_sound_with_file",
        "replace_background_with_file"
    ]
    HANDLED_ACTIONS=RESOURCE_ACTIONS

    def __init__(self, action_name):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerResourceAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name)

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

    def __init__(self, action_name):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerQuestionAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name)

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

    def __init__(self, action_name, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerOtherAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
		self.OTHER_ACTION_DATA_MAP[action_name], **kwargs)
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

    CODE_ACTION_DATA_MAP={
        "execute_code": {"apply_to": "self", "code": ""},
        "execute_script": {"apply_to": "self", "script": None,
            "parameter_list": []}
    }

    def __init__(self, action_name, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerCodeAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.CODE_ACTION_DATA_MAP[action_name], **kwargs)

class PyGameMakerVariableAction(PyGameMakerAction):
    VARIABLE_ACTIONS=[
        "set_variable_value",
        "if_variable_value",
        "draw_variable_value"
    ]
    HANDLED_ACTIONS=VARIABLE_ACTIONS

    def __init__(self):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerVariableAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name)

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

    ACCOUNTING_ACTION_DATA_MAP={
        "set_score_value": {"score": 0, "relative": False},
        "if_score_value": {"score": 0, "operation": "is_equal", "invert": False},
        "draw_score_value": {"locationxy": PyGameMakerAction.DEFAULT_POINT_XY,
            "caption": "Score:", "relative": False},
        "show_highscore_table": {"background": None, "border": True,
            "new_color": "#ff0000", "other_color": "#ffffff",
            "font": None},
        "clear_highscore_table": {},
        "set_lives_value": {"lives": 0, "relative": False},
        "if_lives_value": {"lives": 0, "operation": "is_equal", "invert": False},
        "draw_lives_value": {"locationxy": PyGameMakerAction.DEFAULT_POINT_XY,
            "caption": "Lives:", "relative": False},
        "draw_lives_image": {"locationxy": PyGameMakerAction.DEFAULT_POINT_XY,
            "sprite": None, "relative": False},
        "set_health_value": {"value": 0, "relative": False},
        "if_health_value": {"value": 0, "operation": "is_equal", "invert": False},
        "draw_health_bar": {"rectangle": pygame.Rect(0,0,0,0),
            "background_color": "clear",
            "bar_color_gradient": ("#00ff00", "#ff0000")},
        "set_window_caption": {"show_score": True, "score_caption": "score:",
            "show_lives": False, "lives_caption": "lives:",
            "show_health": False, "health_caption": "health:"}
    }

    def __init__(self, action_name, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerAccountingAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name,
            self.ACCOUNTING_ACTION_DATA_MAP[action_name], **kwargs)

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

    def __init__(self):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerParticleAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name)

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

    def __init__(self):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerDrawAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name)

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
            motion_action = PyGameMakerAction.get_action_instance_by_action_name("set_velocity_compass", direction="DOWN")
            self.assertEqual(motion_action["direction"], "DOWN")
            print("action: {}".format(motion_action))

        def test_005valid_motion_action(self):
            good_action = PyGameMakerMotionAction("set_velocity_degrees", speed=5)
            self.assertEqual(good_action["speed"], 5)
            print("action: {}".format(good_action))

        def test_010valid_object_action(self):
            object_action = PyGameMakerObjectAction("create_object",
                locationxy=(250,250))
            self.assertEqual(object_action["locationxy"], (250,250))
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

    unittest.main()

