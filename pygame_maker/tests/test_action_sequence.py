#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test the pygame_maker.actions.action_sequence module.
"""

import unittest
import yaml
from pygame_maker.actions.action import MotionAction, SoundAction, OtherAction, ObjectAction
from pygame_maker.actions.action_sequence import ActionSequence, ActionSequenceStatementException


class TestActionSequence(unittest.TestCase):
    """Unit tests for the action_sequence module."""

    def setUp(self):
        pass

    def test_005single_nested_sequence(self):
        """
        Test creation of an ActionSequence containing single if/else statements
        and statement blocks.
        """
        actions = [
            (MotionAction("set_velocity_compass"), None),
            (SoundAction("if_sound_is_playing", sound="sound1"), False),
            (SoundAction("stop_sound", sound="sound1"), None),
            (OtherAction("else"), None),
            (SoundAction("play_sound", sound="sound1"), None),
            (SoundAction("if_sound_is_playing", sound="sound2", invert=True), True),
            (OtherAction("start_of_block"), False),
            (SoundAction("play_sound", sound="sound2"), None),
            (MotionAction("set_velocity_compass"), None),
            (OtherAction("end_of_block"), None),
            (OtherAction("else"), None),
            (OtherAction("start_of_block"), None),
            (SoundAction("play_sound", sound="sound3"), None),
            (ObjectAction("create_object", object="object1"), None),
            (OtherAction("end_of_block"), None),
            (ObjectAction("create_object", object="object2"), None)
        ]
        action_list = [action[0] for action in actions]
        result_list = [action[1] for action in actions]
        all_true_action_list = [
            action_list[0], action_list[1], action_list[2], action_list[5],
            action_list[7], action_list[8], action_list[15]
        ]
        all_false_action_list = [
            action_list[0], action_list[1], action_list[4], action_list[5],
            action_list[12], action_list[13], action_list[15]
        ]
        simulated_list = [
            action_list[0], action_list[1], action_list[4], action_list[5],
            action_list[7], action_list[8], action_list[15]
        ]
        action_sequence = ActionSequence()
        for act in action_list:
            action_sequence.append_action(act)
        #print(action_sequence)
        self.assertEqual(action_list, action_sequence.main_block.get_action_list())
        action_sequence.pretty_print()
        walked_list = []
        print("\nconditional True paths:")
        for action in action_sequence.get_next_action():
            print("{}".format(action))
            if hasattr(action, "action_result"):
                action.action_result = True
            walked_list.append(action)
        self.assertEqual(walked_list, all_true_action_list)
        walked_list = []
        print("\nconditional False paths:")
        for action in action_sequence.get_next_action():
            print("{}".format(action))
            if hasattr(action, "action_result"):
                action.action_result = False
            walked_list.append(action)
        self.assertEqual(walked_list, all_false_action_list)
        walked_list = []
        print("\nSimulated real-time conditionals:")
        if_idx = 0
        for action in action_sequence.get_next_action():
            if_idx = action_list.index(action)
            if_result = result_list[if_idx]
            print("{}".format(action))
            if hasattr(action, "action_result"):
                print("---> RETURNED {}".format(if_result))
                action.action_result = if_result
            walked_list.append(action)
        self.assertEqual(walked_list, simulated_list)

    def test_010multi_nested_sequence(self):
        """
        Test creation of an ActionSequence containing nested single if/else
        statements and statement blocks.
        """
        actions = [
            (MotionAction("set_velocity_compass"), None),
            (SoundAction("if_sound_is_playing", sound="sound1"), True),
            (SoundAction("if_sound_is_playing", sound="sound2", invert=True), False),
            (SoundAction("if_sound_is_playing", sound="sound3"), True),
            (SoundAction("stop_sound", sound="sound3"), None),
            (SoundAction("if_sound_is_playing", sound="sound4", invert=True), True),
            (OtherAction("start_of_block"), None),
            (SoundAction("play_sound", sound="sound5"), None),
            (SoundAction("if_sound_is_playing", sound="sound6"), False),
            (OtherAction("start_of_block"), None),
            (MotionAction("set_velocity_compass"), None),
            (MotionAction("apply_gravity"), None),
            (OtherAction("end_of_block"), None),
            (OtherAction("end_of_block"), None),
            (ObjectAction("create_object"), None)
        ]
        action_list = [action[0] for action in actions]
        result_list = [action[1] for action in actions]
        all_true_action_list = [
            action_list[0], action_list[1], action_list[2], action_list[3],
            action_list[4], action_list[5], action_list[7], action_list[8],
            action_list[10], action_list[11], action_list[14]
        ]
        all_false_action_list = [
            action_list[0], action_list[1], action_list[5], action_list[14]
        ]
        simulated_list = [
            action_list[0], action_list[1], action_list[2], action_list[5],
            action_list[7], action_list[8], action_list[14]
        ]
        action_sequence = ActionSequence()
        for act in action_list:
            action_sequence.append_action(act)
        #print(action_sequence)
        self.assertEqual(action_list, action_sequence.main_block.get_action_list())
        action_sequence.pretty_print()
        walked_list = []
        print("\nconditional True paths:")
        for action in action_sequence.get_next_action():
            print("{}".format(action))
            if hasattr(action, "action_result"):
                action.action_result = True
            walked_list.append(action)
        self.assertEqual(walked_list, all_true_action_list)
        walked_list = []
        print("\nconditional False paths:")
        for action in action_sequence.get_next_action():
            print("{}".format(action))
            if hasattr(action, "action_result"):
                action.action_result = False
            walked_list.append(action)
        self.assertEqual(walked_list, all_false_action_list)
        walked_list = []
        print("\nSimulated real-time conditionals:")
        if_idx = 0
        for action in action_sequence.get_next_action():
            if_idx = action_list.index(action)
            if_result = result_list[if_idx]
            print("{}".format(action))
            if hasattr(action, "action_result"):
                print("---> RETURNED {}".format(if_result))
                action.action_result = if_result
            walked_list.append(action)
        self.assertEqual(walked_list, simulated_list)

    def test_015broken_sequences(self):
        """Test that invalid action sequences raise the expected exception."""
        action_sequence = ActionSequence()
        action_sequence.pretty_print()
        with self.assertRaises(ActionSequenceStatementException):
            action_sequence.append_action(
                OtherAction("else"))
        with self.assertRaises(ActionSequenceStatementException):
            action_sequence.append_action(
                OtherAction("end_of_block"))
        with self.assertRaises(ActionSequenceStatementException):
            action_sequence.append_action("this is not an action!")

    def test_020to_and_from_yaml(self):
        """
        Test that converting a sequence to yaml and back doesn't introduce any
        errors.
        """
        action_list = [
            MotionAction("set_velocity_compass"),
            SoundAction("if_sound_is_playing", sound="sound1"),
            SoundAction("stop_sound", sound="sound1"),
            OtherAction("else"),
            SoundAction("play_sound", sound="sound1"),
        ]
        action_sequence = ActionSequence()
        for act in action_list:
            action_sequence.append_action(act)
        print("{}".format(action_sequence.to_yaml()))
        yaml_out = yaml.load(action_sequence.to_yaml())
        print("{}".format(yaml_out))
        new_seq = ActionSequence.load_sequence_from_yaml_obj(yaml_out)
        self.assertEqual(action_list, new_seq.main_block.get_action_list())
        new_seq.pretty_print()

unittest.main()

