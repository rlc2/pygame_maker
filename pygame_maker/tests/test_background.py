#!/usr/bin/env python

from pygame_maker.scenes.background import Background
import pg_template
import tempfile
import pygame
import sys
import os

TEST_BACKGROUND_LIST_YAML_FILE="unittest_files/test_backgrounds.yaml"

class MyGameManager:
    LEFT_MARGIN = 10
    TOP_MARGIN  = 8
    LINE_HEIGHT = 18
    TEXT_COLOR  = (128,   0, 128)
    TEXT_BACKG  = (255, 255, 255)
    def __init__(self):
        self.current_events = []
        self.objects = []
        self.backgrounds = Background.load_from_yaml(TEST_BACKGROUND_LIST_YAML_FILE)
        if len(self.backgrounds) == 0:
            print("Unable to load backgrounds from {}, aborting.".format(TEST_BACKGROUND_LIST_YAML_FILE))
            exit(1)
        self.font = None
        self.done = False
        self.screen = None
        self.font = None
        self.background_idx = 0

    def setup(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 16)
        self.backgrounds[0].draw_background(self.screen)
        self.create_text("Background {}, ok? Y/N".format(self.backgrounds[0].name))

    def collect_event(self, event):
        self.current_events.append(event)

    def create_text(self, text):
        if len(self.objects) > 25:
            # too many text lines, remove oldest object
            self.objects = self.objects[1:]
        self.objects.append( ("text", self.font.render(text, 1, self.TEXT_COLOR, self.TEXT_BACKG)) )

    def update(self):
        for ev in self.current_events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.done = True
                    break
                elif ev.key == pygame.K_y:
                    if self.background_idx < (len(self.backgrounds)-1):
                        self.background_idx += 1
                        self.create_text("Background {}, ok? Y/N".format(self.backgrounds[self.background_idx].name))
                    else:
                        self.done = True
                elif ev.key == pygame.K_n:
                    # create a new text object
                    self.create_text("Failed.")
                    self.done = True
        # done with event handling
        self.current_events = []

    def draw_text(self, textobj, line):
        y = self.TOP_MARGIN + line*self.LINE_HEIGHT
        textpos = (self.LEFT_MARGIN, y)
        self.screen.blit(textobj[1], textpos)

    def draw_objects(self):
        for line, ob in enumerate(self.objects):
            self.draw_text(ob, line)

    def draw_background(self):
        self.screen.fill( (64,64,64) ) # grey background color
        if self.background_idx < len(self.backgrounds):
            self.backgrounds[self.background_idx].draw_background(self.screen)

    def final_pass(self):
        pass

    def is_done(self):
        return self.done

# run from the tests directory to find the unittest_files subdirectory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

mymanager = MyGameManager()
mygame = pg_template.PygameTemplate( (1024,768), "Background Tests",
    mymanager)
mygame.run()

