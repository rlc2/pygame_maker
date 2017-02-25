#!/usr/bin/python -Wall

# Unit tests for widget.py

from pygame_maker.actors.gui.widget import *
from pygame_maker.support import css_to_style
import pygame_maker.support.drawing as drawing
import pygame_maker.support.color as color
import pygame_maker.support.coordinate as coord
import pg_template
import pygame
import math
import sys
import os


class MyGameManager:
    WIDGET_STYLES = """
WidgetObjectType#0 {
    border-top-color: red;
    border-top-style: hidden;
    border-top-width: 1;
    border-right-color: green;
    border-right-style: solid;
    border-right-width: 0;
    border-bottom-color: #777777;
    border-bottom-style: dotted;
    border-bottom-width: 1;
    border-left-color: transparent;
    border-left-style: solid;
    border-left-width: 1;
    width: 200px;
    height: 200px;
}
WidgetObjectType#1 {
    border-top-color: red;
    border-top-style: dashed;
    border-top-width: 1;
    border-right-color: green;
    border-right-style: solid;
    border-right-width: 1;
    border-bottom-color: blue;
    border-bottom-style: solid;
    border-bottom-width: 3;
    border-left-color: #777777;
    border-left-style: solid;
    border-left-width: 1;
    width: 80%;
    height: 80%;
}
"""
    GRID_COLOR = color.Color( (255,0,255) )
    def __init__(self):
        self.current_events = []
        self.objects = []
        self.done = False
        self.screen = None
        self.global_style_settings = css_to_style.CSSStyleGenerator.get_css_style(self.WIDGET_STYLES)

    def setup(self, screen):
        self.screen = screen

    def collect_event(self, event):
        self.current_events.append(event)

    def update(self):
        for ev in self.current_events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.done = True
                    break
        # done with event handling
        self.current_events = []

    def draw_grid(self):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        # draw vertical grid lines
        for grid_x in range(100, screen_width, 200):
            line_start = coord.Coordinate(grid_x, 0)
            line_end = coord.Coordinate(grid_x, screen_height)
            drawing.draw_line(self.screen, line_start, line_end, 1, self.GRID_COLOR, "dotted")
        # draw horizontal grid lines
        for grid_y in range(100, screen_height, 200):
            line_start = coord.Coordinate(0, grid_y)
            line_end = coord.Coordinate(screen_width, grid_y)
            drawing.draw_line(self.screen, line_start, line_end, 1, self.GRID_COLOR, "dotted")

    def draw_objects(self):
        self.draw_grid()

    def draw_background(self):
        self.screen.fill( (0,0,0) ) # grey background color

    def final_pass(self):
        pass

    def is_done(self):
        return self.done


mymanager = MyGameManager()
mygame = pg_template.PygameTemplate( (1024,768), "Widget Border Tests",
    mymanager)
mygame.run()

