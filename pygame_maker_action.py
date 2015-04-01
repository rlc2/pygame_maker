#!/usr/bin/python -Wall

# represent a PyGameMaker action that executes following an event

class PyGameMakerActionException(Exception):
    pass

class PyGameMakerAction:
    """Base class for actions"""
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

    def __init__(self, action_name=""):
        """
            Supply the basic properties for all actions
        """
        self.name = action_name
        self.action_data = {}

    def __getitem__(self, itemname):
        """
            Forward PyGameMakerAction[key] to the action_data member for
            convenience
        """
        if not itemname in self.action_data:
            raise PyGameMakerActionException
        return self.action_data[itemname]

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
    DEFAULT_POINT_XY=(0,0)
    DEFAULT_SPEED=0
    DEFAULT_DIRECTION=0
    DEFAULT_GRAVITY=0.1
    DEFAULT_FRICTION=0.1
    DEFAULT_GRID_SNAP_XY=(16, 16)
    DEFAULT_WRAP_DIRECTION="HORIZONTAL"
    DEFAULT_PATH=0
    DEFAULT_PATH_LOCATION=0
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
    MOTION_ACTION_DATA_MAP={
        "set_velocity_compass": {"direction":"UP", "speed":DEFAULT_SPEED},
        "set_velocity_degrees": {"direction":DEFAULT_DIRECTION,
            "speed":DEFAULT_SPEED},
        "move_toward_point": {"targetxy":DEFAULT_POINT_XY},
        "move_horizontal": {"horizontal_direction": "LEFT"},
        "move_vertical": {"vertical_direction": "UP"},
        "apply_gravity": {"gravity": DEFAULT_GRAVITY},
        "reverse_horizontal_speed": {},
        "reverse_vertical_speed": {},
        "set_friction": {"friction": DEFAULT_FRICTION},
        "jump_to": {"locationxy": DEFAULT_POINT_XY},
        "jump_to_start": {},
        "jump_random": {},
        "snap_to_grid": {"gridxy": DEFAULT_GRID_SNAP_XY},
        "wrap_around": {"wrap_direction": DEFAULT_WRAP_DIRECTION},
        "jump_to_collider": {},
        "bounce_off_collider": {},
        "set_path": {"path": DEFAULT_PATH},
        "end_path": {},
        "set_location_on_path": {"location": DEFAULT_PATH_LOCATION},
        "set_path_speed": {"speed": DEFAULT_SPEED},
        "step_toward_point": {"locationxy": DEFAULT_POINT_XY},
        "step_toward_point_around_objects": {"locationxy": DEFAULT_POINT_XY}
    }

    def __init__(self, action_name, **kwargs):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerMotionAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name)
        self.action_data = self.MOTION_ACTION_DATA_MAP[action_name]
        for param in kwargs:
            if param in self.action_data:
                self.action_data[param] = kwargs[param]

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
    def __init__(self, action_name):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerObjectAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name)

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

    def __init__(self):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerOtherAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name)

class PyGameMakerCodeAction(PyGameMakerAction):
    CODE_ACTIONS=[
        "execute_code",
        "execute_script"
    ]
    HANDLED_ACTIONS=CODE_ACTIONS

    def __init__(self):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerCodeAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name)

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

    def __init__(self):
        if not action_name in self.HANDLED_ACTIONS:
            raise PyGameMakerActionException("PyGameMakerAccountingAction: Unknown action '{}'".format(action_name))
        PyGameMakerAction.__init__(self, action_name)

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

        def test_005valid_motion_action(self):
            good_action = PyGameMakerMotionAction("set_velocity_degrees", speed=5)
            self.assertEqual(good_action["speed"], 5)
            print("speed: {}".format(good_action["speed"]))

        def test_010find_action_by_name(self):
            motion_action = PyGameMakerAction.get_action_instance_by_action_name("set_velocity_compass", direction="DOWN")
            self.assertEqual(motion_action["direction"], "DOWN")
            print("direction: {}".format(motion_action["direction"]))

    unittest.main()

