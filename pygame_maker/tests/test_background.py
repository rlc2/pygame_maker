#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test the pygame_maker.scenes.background module.
"""

import sys
import os
import pygame
import pg_template
from pygame_maker.scenes.background import Background

TEST_BACKGROUND_LIST_YAML_FILE = "unittest_files/test_backgrounds.yaml"


class MyGameManager(object):
    """Custom game manager for background module unit tests."""
    LEFT_MARGIN = 10
    TOP_MARGIN = 8
    LINE_HEIGHT = 18
    TEXT_COLOR = (128, 0, 128)
    TEXT_BACKG = (255, 255, 255)
    def __init__(self):
        self.current_events = []
        self.objects = []
        self.backgrounds = None
        with open(TEST_BACKGROUND_LIST_YAML_FILE, "r") as yaml_f:
            self.backgrounds = Background.load_from_yaml(yaml_f)
        if len(self.backgrounds) == 0:
            print(("Unable to load backgrounds from {}, aborting.".format(
                TEST_BACKGROUND_LIST_YAML_FILE)))
            exit(1)
        self.font = None
        self.done = False
        self.screen = None
        self.font = None
        self.background_idx = 0

    def setup(self, screen):
        """Handle setup callback from PygameTemplate."""
        self.screen = screen
        self.font = pygame.font.Font(None, 16)
        self.backgrounds[0].draw_background(self.screen)
        self.create_text("Background {}, ok? Y/N".format(self.backgrounds[0].name))

    def collect_event(self, event):
        """Handle collect_event callback from PygameTemplate."""
        self.current_events.append(event)

    def create_text(self, text):
        """
        Create a maximum of 25 lines of text objects for rendering to the screen.
        """
        if len(self.objects) > 25:
            # too many text lines, remove oldest object
            self.objects = self.objects[1:]
        self.objects.append(("text", self.font.render(text, 1, self.TEXT_COLOR, self.TEXT_BACKG)))

    def update(self):
        """Handle PygameTemplate update callback."""
        for cev in self.current_events:
            if cev.type == pygame.KEYDOWN:
                if cev.key == pygame.K_ESCAPE:
                    self.done = True
                    break
                elif cev.key == pygame.K_y:
                    if self.background_idx < (len(self.backgrounds)-1):
                        self.background_idx += 1
                        self.create_text("Background {}, ok? Y/N".format(
                            self.backgrounds[self.background_idx].name))
                    else:
                        self.done = True
                elif cev.key == pygame.K_n:
                    # create a new text object
                    self.create_text("Failed.")
                    self.done = True
        # done with event handling
        self.current_events = []

    def draw_text(self, textobj, line):
        """Blit a text line to the screen."""
        ypos = self.TOP_MARGIN + line*self.LINE_HEIGHT
        textpos = (self.LEFT_MARGIN, ypos)
        self.screen.blit(textobj[1], textpos)

    def draw_objects(self):
        """Handle draw_objects callback from PygameTemplate."""
        for line, obj in enumerate(self.objects):
            self.draw_text(obj, line)

    def draw_background(self):
        """Handle draw_background callback from PygameTemplate."""
        self.screen.fill((64, 64, 64)) # grey background color
        if self.background_idx < len(self.backgrounds):
            self.backgrounds[self.background_idx].draw_background(self.screen)

    def final_pass(self):
        """Handle final_pass callback from PygameTemplate."""
        pass

    def is_done(self):
        """Handle is_done callback from PygameTemplate."""
        return self.done

# run from the tests directory to find the unittest_files subdirectory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

MYMANAGER = MyGameManager()
MYGAME = pg_template.PygameTemplate((1024, 768), "Background Tests", MYMANAGER)
MYGAME.run()

