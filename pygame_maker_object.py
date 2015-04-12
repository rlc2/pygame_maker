#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker object resource

import pygame
import re
import weakref
import yaml
import pygame_maker_event as pygm_event
import pygame_maker_action as pygm_action
import pygame_maker_event_action_sequence as pygm_sequence

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

    unittest.main()

