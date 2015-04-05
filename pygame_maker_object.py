#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker object resource

import pygame
import re
import weakref
import yaml
import pygame_maker_event as pygme
import pygame_maker_action as pygma

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
            actions: the list of action tuples
                (PyGameMakerAction, int nest_level, list code_block_tags)
            nest_level: the nest level following the last action in the list
            current_code_block_id: the code block id following the last action
                in the list
            current_code_block_list: the active list of code block IDs following
                the last action in the list
        """
        self.actions = []
        self.nest_level = 0
        self.code_block_id = 0
        self.current_code_block_id = 0
        self.current_code_block_list = []

    def append_action(self, action):
        """
            Add a new action to the end of the list
        """
        action_ref = weakref.ref(action)
        self.actions.append( (action_ref, self.nest_level,
            self.current_code_block_list) )
        if action.nest_adjustment:
            self.nest_level += 1
            if action.nest_adjustment == "nest_until_block_end":
                self.current_code_block_id += 1
                self.current_code_block_list.append(self.current_code_block_id)
            elif action.nest_adjustment == "block_end":
                if len(self.current_code_block_list) > 0:
                    # remove the last code block ID from the list moving forward
                    del(self.current_code_block_list[-1])
                if self.nest_level > 0:
                    # reduce the nest level
                    self.nest_level -= 1
        elif self.nest_level > 0:
            # this command doesn't start or continue nesting
            self.nest_level -= 1

    def __repr__(self):
        rep_str = "PyGameMakerEventActionSequence:\n"
        if len(self.actions) == 0:
            rep_str += "\t(empty)\n"
        for action in self.actions:
            rep_str += "\taction: {}\n".format(action[self.ACTION_IDX])
            rep_str += "\tnest_level: {}\n".format(action[self.NEST_IDX])
            rep_str += "\tcode block list{}\n".format(action[self.BLOCK_IDX])
        return rep_str

class PyGameMakerObject(object):
    """
        pygame maker objects have:
        o sprite reference
        o depth? (Z dimension?) (numeric)
        o parent? (another object?)
        o collision mask (uses sprite reference, can be a different sprite)
        o visible flag
        o persistent flag?
        o solid flag (for solid stationary objects, e.g. platform)
        o physics flag
        o events!
          * ex: create. normal step. draw.
          * events can be modified, edited (appears to just add a run code
            action), or deleted.
        o actions!
          * things that happen in response to events
          * change direction. jump to a location. run code. affect score/lives.
            play a sound.
          * actions can be chained together
          * actions can be "questions". depending on the answer, the following
            action(s) can be taken
    """
    DEFAULT_OBJECT_PREFIX="obj_"

    def __init__(self, object_name=None, **kwargs):

        if object_name:
            self.name = object_name
        else:
            self.name = self.DEFAULT_OBJECT_PREFIX
        self.sprite = None
        self.mask = None
        self.visible = True
        self.solid = False
        self.events = {}
        self.actions = {}

if __name__ == "__main__":
    import unittest

    class TestPyGameMakerObject(unittest.TestCase):

        def setUp(self):
            pass

        def test_005build_action_sequence(self):
            action_sequence = PyGameMakerEventActionSequence()
            action_sequence.append_action(pygma.PyGameMakerMotionAction("set_velocity_compass"))
            action_sequence.append_action(pygma.PyGameMakerSoundAction("if_sound_is_playing"))
            action_sequence.append_action(pygma.PyGameMakerSoundAction("stop_sound"))
            print(action_sequence)

    unittest.main()

