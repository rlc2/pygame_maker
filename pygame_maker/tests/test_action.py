#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test the pygame_maker.actions.action module.
"""

import unittest
import yaml
from pygame_maker.actions.action import Action, MotionAction, ObjectAction, SoundAction, \
    CodeAction, AccountingAction, RoomAction, TimingAction, InfoAction, GameAction, \
    VariableAction


class TestAction(unittest.TestCase):
    """Unit tests for the action module."""

    def setUp(self):
        pass

    def test_003find_action_by_name(self):
        """Test the Action.get_action_instance_by_name() method."""
        motion_action = Action.get_action_instance_by_name(
            "set_velocity_compass", compass_directions="DOWN")
        self.assertEqual(motion_action["compass_directions"], "DOWN")
        print("action: {}".format(motion_action))

    def test_005valid_motion_action(self):
        """Test creation of a MotionAction instance with proper keyword args."""
        good_action = MotionAction("set_velocity_degrees", speed=5)
        self.assertEqual(good_action["speed"], 5)
        print("action: {}".format(good_action))

    def test_010valid_object_action(self):
        """
        Test creation of an ObjectAction instance with proper keyword args.
        """
        object_action = ObjectAction(
            "create_object", {'position.x':250, 'position.y':250})
        self.assertEqual(object_action["position.x"], 250)
        self.assertEqual(object_action["position.y"], 250)
        print("action: {}".format(object_action))

    def test_015valid_sound_action(self):
        """Test creation of a SoundAction instance with proper keyword args."""
        sound_action = SoundAction("play_sound", loop=True)
        self.assertTrue(sound_action["loop"])
        print("action: {}".format(sound_action))

    def test_020valid_code_action(self):
        """Test creation of a CodeAction instance with proper keyword args."""
        code_string = "print(\"this is a test\")"
        code_action = CodeAction("execute_code", code=code_string)
        self.assertEqual(code_action["code"], code_string)
        print("action {}".format(code_action))

    def test_025valid_accounting_action(self):
        """
        Test creation of an AccountingAction instance with proper keyword args.
        """
        accounting_action = AccountingAction("set_score_value", score=1, relative=True)
        self.assertEqual(accounting_action["score"], 1)
        self.assertTrue(accounting_action["relative"])
        print("action {}".format(accounting_action))

    def test_030invert(self):
        """Test setting and retrieving an action attribute."""
        if_sound_action = SoundAction("if_sound_is_playing")
        if_sound_action2 = SoundAction("if_sound_is_playing", invert=True)
        self.assertEqual(if_sound_action.name, "if_sound_is_playing")
        self.assertFalse(if_sound_action["invert"])
        self.assertTrue(if_sound_action2["invert"])

    def test_035to_yaml(self):
        """Test conversion of actions into YAML format."""
        test_action = MotionAction('jump_to', relative=True)
        test_yaml = """  jump_to:
    apply_to: self
    position.x: 0
    position.y: 0
    relative: True
"""
        self.assertEqual(test_action.to_yaml(2), test_yaml)
        yaml_in = yaml.load(test_action.to_yaml())
        print("{}".format(yaml_in))
        print("{}".format(test_action.to_yaml(2)))
        code_str = """code line 1
code line 2
  indented line 1
  indented line 2
code line 3"""
        test_action2 = CodeAction('execute_code', code=code_str)
        test_yaml2 = """  execute_code:
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
        """Test creation of a RoomAction instance with proper keyword args."""
        room_action = RoomAction("goto_next_room", transition="create_from_top")
        self.assertEqual(room_action.name, "goto_next_room")
        self.assertEqual(room_action["transition"], "create_from_top")
        print("action {}".format(room_action))

    def test_045valid_timing_action(self):
        """
        Test creation of a TimingAction instance with proper keyword args.
        """
        timing_action = TimingAction("set_alarm", steps=30, alarm=1)
        self.assertEqual(timing_action.name, "set_alarm")
        self.assertEqual(timing_action["steps"], 30)
        self.assertEqual(timing_action["alarm"], 1)

    def test_050valid_info_action(self):
        """Test creation of an InfoAction instance."""
        info_action = InfoAction("show_game_info")
        self.assertEqual(info_action.name, "show_game_info")

    def test_055valid_game_action(self):
        """Test creation of a GameAction instance with proper keyword args."""
        game_action = GameAction("load_game", filename="game0")
        self.assertEqual(game_action.name, "load_game")
        self.assertEqual(game_action["filename"], "game0")

    def test_060valid_variable_action(self):
        """
        Test creation of a VariableAction instance with proper keyword args.
        """
        variable_action = VariableAction(
            "set_variable_value", value='20', variable='ammo', is_global=True)
        self.assertEqual(variable_action.name, "set_variable_value")
        self.assertEqual(variable_action["value"], "20")
        self.assertEqual(variable_action["variable"], 'ammo')
        self.assertTrue(variable_action["is_global"])

unittest.main()


