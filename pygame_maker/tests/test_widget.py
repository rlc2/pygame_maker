#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test the pygame_maker.actors.gui.widget module.
"""

# Unit tests for widget.py

import logging
import pygame
import pg_template
from pygame_maker.actors.gui.widget import WidgetObjectType, LabelWidgetObjectType
from pygame_maker.events import event
from pygame_maker.events import event_engine
from pygame_maker.logic import language_engine
from pygame_maker.support import css_to_style
import pygame_maker.support.drawing as drawing
import pygame_maker.support.color as color
import pygame_maker.support.coordinate as coord
import pygame_maker.support.font as font

WTLOGGER = logging.getLogger("WidgetObjectType")
WTHANDLER = logging.StreamHandler()
WTFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
WTHANDLER.setFormatter(WTFORMATTER)
WTLOGGER.addHandler(WTHANDLER)
WTLOGGER.setLevel(logging.DEBUG)

WILOGGER = logging.getLogger("WidgetInstance")
WIHANDLER = logging.StreamHandler()
WIFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
WIHANDLER.setFormatter(WIFORMATTER)
WILOGGER.addHandler(WIHANDLER)
WILOGGER.setLevel(logging.DEBUG)

LWTLOGGER = logging.getLogger("LabelWidgetObjectType")
LWTHANDLER = logging.StreamHandler()
LWTFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
LWTHANDLER.setFormatter(LWTFORMATTER)
LWTLOGGER.addHandler(LWTHANDLER)
LWTLOGGER.setLevel(logging.DEBUG)

LWILOGGER = logging.getLogger("LabelWidgetInstance")
LWIHANDLER = logging.StreamHandler()
LWIFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
LWIHANDLER.setFormatter(LWIFORMATTER)
LWILOGGER.addHandler(LWIHANDLER)
LWILOGGER.setLevel(logging.DEBUG)


class MyGameManager(object):
    """Custom game manager for widget unit tests."""
    WIDGET_STYLES = """
WidgetObjectType#0 {
    border-top-color: red;
    border-top-style: hidden;
    border-top-width: 1;
    border-right-color: green;
    border-right-style: solid;
    border-right-width: 0;
    border-bottom-color: #777777;
    border-bottom-style: none;
    border-bottom-width: 1;
    border-left-color: transparent;
    border-left-style: solid;
    border-left-width: 1;
    width: 100px;
    height: 100px;
}
WidgetObjectType#1 {
    border-top-color: yellow;
    border-top-style: dashed;
    border-top-width: 1;
    border-right-color: green;
    border-right-style: solid;
    border-right-width: 2;
    border-bottom-color: white;
    border-bottom-style: dotted;
    border-bottom-width: 3;
    border-left-color: #777777;
    border-left-style: solid;
    border-left-width: 1;
    width: 100%;
    height: 100%;
}
LabelWidgetObjectType {
    color: orange;
}
LabelWidgetObjectType#0 {
    border: 1 solid red;
}
"""
    GRID_COLOR = color.Color((255, 0, 255))
    GRID_START_X = 100
    GRID_START_Y = 100
    GRID_SPACING_X = 200
    GRID_SPACING_Y = 200
    def __init__(self):
        self.current_events = []
        self.event_engine = event_engine.EventEngine()
        self.language_engine = language_engine.LanguageEngine()
        self.symbols = language_engine.SymbolTable()
        self.done = False
        self.screen = None
        self.draw_surface = None
        self.global_style_settings = css_to_style.CSSStyleGenerator.get_css_style(
            self.WIDGET_STYLES)
        self.global_style_settings.pretty_print()
        self.widget_rows = 0
        self.widget_cols = 0
        self.widget_surface_matrix = []
        self.widget_types = {}
        self.resources = {'fonts': {}}

    def create_subsurfaces(self, screen_width, screen_height):
        """Create a grid of subsurfaces for drawing widgets into."""
        self.widget_rows = (screen_width - self.GRID_START_X) / self.GRID_SPACING_X
        self.widget_cols = (screen_height - self.GRID_START_Y) / self.GRID_SPACING_Y
        first_col_left = self.GRID_START_X
        first_row_top = self.GRID_START_Y
        for row_idx in range(self.widget_rows):
            # make sure the widget's height fits inside the screen
            if first_row_top + (row_idx+1) * self.GRID_SPACING_Y > screen_height:
                break
            for col_idx in range(self.widget_cols):
                # make sure the widget's width fits inside the screen
                if first_col_left + (col_idx+1) * self.GRID_SPACING_X > screen_width:
                    break
                surf_rect = pygame.Rect(0, 0, 0, 0)
                surf_rect.left = first_col_left + (col_idx * self.GRID_SPACING_X) + 1
                surf_rect.width = self.GRID_SPACING_X - 1
                surf_rect.top = first_row_top + (row_idx * self.GRID_SPACING_Y) + 1
                surf_rect.height = self.GRID_SPACING_Y - 1
                print("Widget @ ({},{}) rect: {}".format(row_idx, col_idx, surf_rect))
                widget_surf = self.draw_surface.subsurface(surf_rect)
                if col_idx == 0:
                    self.widget_surface_matrix.append([])
                self.widget_surface_matrix[-1].append(widget_surf)
        print("Surface matrix rows={}, cols=".format(len(self.widget_surface_matrix)))
        for row in range(len(self.widget_surface_matrix)):
            print("  {}".format(len(self.widget_surface_matrix[row])))

    def create_widgets(self):
        """Create all widget instances to be displayed."""
        self.widget_types['WidgetObjectType'] = WidgetObjectType(
            'WidgetObjectType', self, visible=True)
        self.widget_types['WidgetObjectType'].create_instance(self.widget_surface_matrix[0][0])
        self.widget_types['WidgetObjectType'].create_instance(self.widget_surface_matrix[0][1])
        # import pdb; pdb.set_trace()
        self.widget_types['LabelWidgetObjectType'] = LabelWidgetObjectType(
            'LabelWidgetObjectType', self, visible=True)
        self.widget_types['LabelWidgetObjectType'].create_instance(
            self.widget_surface_matrix[0][2], font="fnt_test", label="Test Font")
        position_surf = self.widget_surface_matrix[1][0]
        pwidth = position_surf.get_width()
        pheight = position_surf.get_height()
        self.widget_types['LabelWidgetObjectType'].create_instance(
            position_surf, font="fnt_test", label="LB", width=str(pwidth), height=str(pheight))
        self.widget_types['LabelWidgetObjectType'].create_instance(
            position_surf, {"vertical-align": "top"},
            font="fnt_test", label="LT", width=str(pwidth), height=str(pheight))
        self.widget_types['LabelWidgetObjectType'].create_instance(
            position_surf, {"vertical-align": "middle"},
            font="fnt_test", label="LM", width=str(pwidth), height=str(pheight))
        self.widget_types['LabelWidgetObjectType'].create_instance(
            position_surf, {"text-align": "center"},
            font="fnt_test", label="CB", width=str(pwidth), height=str(pheight))
        self.widget_types['LabelWidgetObjectType'].create_instance(
            position_surf, {"text-align": "center", "vertical-align": "top"},
            font="fnt_test", label="CT", width=str(pwidth), height=str(pheight))
        self.widget_types['LabelWidgetObjectType'].create_instance(
            position_surf, {"text-align": "center", "vertical-align": "middle"},
            font="fnt_test", label="CM", width=str(pwidth), height=str(pheight))
        self.widget_types['LabelWidgetObjectType'].create_instance(
            position_surf, {"text-align": "right"},
            font="fnt_test", label="RB", width=str(pwidth), height=str(pheight))
        self.widget_types['LabelWidgetObjectType'].create_instance(
            position_surf, {"text-align": "right", "vertical-align": "top"},
            font="fnt_test", label="RT", width=str(pwidth), height=str(pheight))
        self.widget_types['LabelWidgetObjectType'].create_instance(
            position_surf, {"text-align": "right", "vertical-align": "middle"},
            font="fnt_test", label="RM", width=str(pwidth), height=str(pheight))

    def setup(self, screen):
        """Handle setup callback from PygameTemplate."""
        self.screen = screen
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        #pylint: disable=too-many-function-args
        self.draw_surface = pygame.Surface((screen_width, screen_height))
        #pylint: enable=too-many-function-args
        self.create_subsurfaces(screen_width, screen_height)
        self.resources['fonts']['fnt_test'] = font.Font("fnt_test", fontname="freemono",
                                                        fontsize=18)
        self.create_widgets()

    def collect_event(self, an_event):
        """Handle collect_event callback from PygameTemplate."""
        self.current_events.append(an_event)

    def update(self):
        """Handle PygameTemplate update callback."""
        for cev in self.current_events:
            if cev.type == pygame.KEYDOWN:
                if cev.key == pygame.K_ESCAPE:
                    self.done = True
                    break
        # done with event handling
        self.current_events = []

    def draw_grid(self):
        """Draw the widget display grid."""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        # draw vertical grid lines
        for grid_x in range(self.GRID_START_X, screen_width, self.GRID_SPACING_X):
            line_start = coord.Coordinate(grid_x, 0)
            line_end = coord.Coordinate(grid_x, screen_height)
            drawing.draw_line(self.draw_surface, line_start, line_end, 1, self.GRID_COLOR, "dotted")
        # draw horizontal grid lines
        for grid_y in range(self.GRID_START_Y, screen_height, self.GRID_SPACING_Y):
            line_start = coord.Coordinate(0, grid_y)
            line_end = coord.Coordinate(screen_width, grid_y)
            drawing.draw_line(self.draw_surface, line_start, line_end, 1, self.GRID_COLOR, "dotted")

    def draw_objects(self):
        """Handle draw_objects callback from PygameTemplate."""
        self.draw_grid()
        # draw guides here
        # drawing.draw_line(self.draw_surface, coord.Coordinate(200, 297),
        #                   coord.Coordinate(300, 297), 1, self.GRID_COLOR, "solid")
        # drawing.draw_line(self.draw_surface, coord.Coordinate(200, 299),
        #                   coord.Coordinate(300, 299), 1, self.GRID_COLOR, "solid")
        drev = event.DrawEvent('draw')
        self.event_engine.queue_event(drev)
        self.event_engine.transmit_event(drev.name)

    def draw_background(self):
        """Handle draw_background callback from PygameTemplate."""
        self.screen.fill((0, 0, 0)) # grey background color

    def final_pass(self):
        """Handle final_pass callback from PygameTemplate."""
        self.screen.blit(self.draw_surface, (0, 0))

    def is_done(self):
        """Handle is_done callback from PygameTemplate."""
        return self.done


MYMANAGER = MyGameManager()
MYGAME = pg_template.PygameTemplate((1024, 768), "Widget Border Tests", MYMANAGER, 5)
MYGAME.run()

