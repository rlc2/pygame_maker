#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker room backgrounds

import pygame
import os.path
import yaml
import re

class PyGameMakerBackgroundException(Exception):
    pass

class PyGameMakerTileProperties(object):
    DEFAULT_TILE_WIDTH=16
    DEFAULT_TILE_HEIGHT=16
    def __init__(self, **kwargs):
        self.tile_width = self.DEFAULT_TILE_WIDTH
        self.tile_height = self.DEFAULT_TILE_HEIGHT
        self.horizontal_offset = 0
        self.vertical_offset = 0
        self.horizontal_padding = 0
        self.vertical_padding = 0
        if kwargs:
            if 'tile_width' in kwargs.keys():
                self.tile_width = int(kwargs['tile_width'])
            if 'tile_height' in kwargs.keys():
                self.tile_height = int(kwargs['tile_height'])
            if 'horizontal_offset' in kwargs.keys():
                self.horizontal_offset = int(kwargs['horizontal_offset'])
            if 'vertical_offset' in kwargs.keys():
                self.vertical_offset = int(kwargs['vertical_offset'])
            if 'horizontal_padding' in kwargs.keys():
                self.horizontal_padding = int(kwargs['horizontal_padding'])
            if 'vertical_padding' in kwargs.keys():
                self.vertical_padding = int(kwargs['vertical_padding'])

    def __eq__(self, other):
        return(isinstance(other, PyGameMakerTileProperties) and
            (self.tile_width == other.tile_width) and
            (self.tile_height == other.tile_height) and
            (self.horizontal_offset == other.horizontal_offset) and
            (self.vertical_offset == other.vertical_offset) and
            (self.horizontal_padding == other.horizontal_padding))

class PyGameMakerBackground(object):
    DEFAULT_NAME="bkg_"
    COLOR_STRING_RE=re.compile("#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})")

    @staticmethod
    def load_from_yaml(yaml_file_name, unused=None):
        """
            load_from_yaml():
            Create background(s) from a YAML-formatted file.
            Expected format (missing fields will receive default values):
            - bkg_name1:
                filename: <image_file_name>
                smooth_edges: True|False
                preload_texture: True|False
                transparent: True|False
                tileset: True|False
                background_color: #RRGGBB | (R, G, B)
                tile_width: <# >= 0>
                tile_height: <# >= 0>
                horizontal_offset: <# >= 0>
                vertical_offset: <# >= 0>
                horizontal_padding: <# >= 0>
                vertical_padding: <# >= 0>
        """
        yaml_repr = None
        new_background_list = []
        with open(yaml_file_name, "r") as yaml_f:
            yaml_repr = yaml.load(yaml_f)
        if yaml_repr:
            for top_level in yaml_repr:
                kwargs = {}
                bkg_name = top_level.keys()[0]
                bkg_yaml = top_level[bkg_name]
                if 'filename' in bkg_yaml.keys():
                    kwargs['filename'] = bkg_yaml['filename']
                if 'smooth_edges' in bkg_yaml.keys():
                    kwargs['smooth_edges'] = (bkg_yaml['smooth_edges'] == True)
                if 'preload_texture' in bkg_yaml.keys():
                    kwargs['preload_texture'] = (bkg_yaml['preload_texture'] ==
                        True)
                if 'transparent' in bkg_yaml.keys():
                    kwargs['transparent'] = (bkg_yaml['transparent'] == True)
                if 'tileset' in bkg_yaml.keys():
                    kwargs['tileset'] = (bkg_yaml['tileset'] == True)
                if 'background_color' in bkg_yaml.keys():
                    kwargs['background_color'] = bkg_yaml['background_color']
                if 'tile_width' in bkg_yaml.keys():
                    kwargs['tile_width'] = bkg_yaml['tile_width']
                if 'tile_height' in bkg_yaml.keys():
                    kwargs['tile_height'] = bkg_yaml['tile_height']
                if 'horizontal_offset' in bkg_yaml.keys():
                    kwargs['horizontal_offset'] = bkg_yaml['horizontal_offset']
                if 'vertical_offset' in bkg_yaml.keys():
                    kwargs['vertical_offset'] = bkg_yaml['vertical_offset']
                if 'horizontal_padding' in bkg_yaml.keys():
                    kwargs['horizontal_padding'] = bkg_yaml['horizontal_padding']
                if 'vertical_padding' in bkg_yaml.keys():
                    kwargs['vertical_padding'] = bkg_yaml['vertical_padding']
                new_background_list.append(PyGameMakerBackground(bkg_name,
                    **kwargs))
        return new_background_list

    def __init__(self, name, **kwargs):
        self.name = name
        self.filename = ""
        self.tile_properties = PyGameMakerTileProperties(**kwargs)
        self.smooth_edges = False
        self.preload_texture = False
        self.transparent = False
        self.tileset = False
        self.image = None
        self.image_size = (0,0)
        self.background_color = (0,0,0)
        self.tile_rect = None
        self.tile_row_spacing = -1
        self.max_tile_rows = -1
        self.tile_col_spacing = -1
        self.max_tile_cols = -1
        if kwargs:
            if 'filename' in kwargs:
                self.filename = kwargs['filename']
            if 'smooth_edges' in kwargs:
                self.smooth_edges = (kwargs['smooth_edges'] == True)
            if 'preload_texture' in kwargs:
                self.preload_texture = (kwargs['preload_texture'] == True)
            if 'transparent' in kwargs:
                self.transparent = (kwargs['transparent'] == True)
            if 'tileset' in kwargs:
                self.tileset = (kwargs['tileset'] == True)
            if 'background_color' in kwargs:
                if isinstance(kwargs['background_color'], str):
                    # accept background colors in #RRGGBB format
                    minfo = self.COLOR_STRING_RE.match(kwargs['background_color'])
                    if minfo:
                        red = int(minfo.group(1), base=16)
                        green = int(minfo.group(2), base=16)
                        blue = int(minfo.group(3), base=16)
                        self.background_color = (red, green, blue)
                    else:
                        raise(PyGameMakerBackgroundException("{}: Supplied background_color '{}' not recognized (supply a 3-item list or #RRGGBB string)".format(type(self).__name__, kwargs['background_color'])))
                else:
                    clist = list(kwargs['background_color'])
                    if len(clist) >= 3:
                        self.background_color = (clist[0], clist[1], clist[2])
                    else:
                        raise(PyGameMakerBackgroundException("{}: Supplied background_color '{}' not recognized (supply a 3-item list or #RRGGBB string)".format(type(self).__name__, kwargs['background_color'])))
        # load the graphic immediately instead of waiting until the room is
        #  loaded, if preload_texture is set
        if self.filename and self.preload_texture and self.check_filename():
            self.load_graphic()

    def load_graphic(self):
        """
            load_graphic():
            Load the background image from the file.
        """
        if len(self.filename) > 0 and self.check_filename():
            img = pygame.image.load(self.filename).convert_alpha()
            if not self.transparent:
                # in case the image had transparent pixels, place it on a
                #  black background so there will no longer be transparent
                #  pixels on the display
                backfill = pygame.Surface.copy(img)
                backfill.fill( (0,0,0) )
                backfill.blit(img, (0,0))
                self.image = backfill
            else:
                self.image = img
            self.image_size = self.image.get_size()

    def draw_background(self, screen, xy_offset=(0,0)):
        """
            draw_background():
            Draw the background color and image (with tiling if specified) to
             the supplied screen
            Parameters:
             screen (pygame.Surface): The screen to draw this background onto
             xy_offset (tuple/list): X, Y offset for the upper left corner of
              the image/tileset (in addition to the background's configured
              horizontal/vertical offsets if it's a tileset)
        """
        screen.fill(self.background_color)
        if (len(self.filename) > 0) and self.check_filename():
            if not self.image:
                self.load_graphic()
            if not self.tileset:
                screen.blit(self.image, xy_offset)
            else:
                if not self.tile_rect:
                    self.tile_rect = pygame.Rect(0, 0,
                        self.tile_properties.tile_width,
                        self.tile_properties.tile_height)
                if self.tile_row_spacing < 0:
                    self.tile_row_spacing = (self.tile_properties.tile_height +
                        self.tile_properties.vertical_padding)
                    #print("row spacing: {}".format(self.tile_row_spacing))
                if self.max_tile_rows < 0:
                    self.max_tile_rows = ((screen.get_height() - xy_offset[1] -
                        self.tile_properties.vertical_offset) /
                        self.tile_row_spacing)
                    #print("max rows: {}".format(self.max_tile_rows))
                if self.tile_col_spacing < 0:
                    self.tile_col_spacing = (self.tile_properties.tile_width +
                        self.tile_properties.horizontal_padding)
                    #print("col spacing: {}".format(self.tile_col_spacing))
                if self.max_tile_cols < 0:
                    self.max_tile_cols = ((screen.get_width() -
                        self.tile_properties.horizontal_offset) /
                        self.tile_col_spacing)
                    #print("max cols: {}".format(self.max_tile_cols))
                for col in range(self.max_tile_cols):
                    for row in range(self.max_tile_rows):
                        position_x = (self.tile_properties.horizontal_offset +
                            xy_offset[0] + col *
                            (self.tile_properties.tile_width +
                                self.tile_properties.horizontal_padding))
                        position_y = (self.tile_properties.vertical_offset +
                            xy_offset[1] + row *
                            (self.tile_properties.tile_height +
                                self.tile_properties.vertical_padding))
                        screen.blit(self.image, (position_x, position_y),
                            area=self.tile_rect)

    def check_filename(self):
        """Error-check filename"""
        if not isinstance(self.filename, str):
            raise PyGameMakerBackgroundException("Background error ({}): filename '{}' is not a string".format(self,self.filename))
        elif len(self.filename) == 0:
            raise PyGameMakerBackgroundException("Background error ({}): filename is empty".format(self,self.filename))
        if len(self.filename) > 0:
            if not os.path.exists(self.filename):
                raise PyGameMakerBackgroundException("Background error ({}): filename '{}' not found".format(self,self.filename))
        return True

    def __eq__(self, other):
        return(isinstance(other, PyGameMakerBackground) and
            (self.name == other.name) and
            (self.filename == other.filename) and
            (self.smooth_edges == other.smooth_edges) and
            (self.preload_texture == other.preload_texture) and
            (self.transparent == other.transparent) and
            (self.tileset == other.tileset) and
            (self.tile_properties == other.tile_properties) and
            (self.background_color == other.background_color))

    def __repr__(self):
        return("<{} name='{}'>".format(type(self).__name__, self.name))

if __name__ == "__main__":
    import pg_template
    import unittest
    import tempfile
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
            self.backgrounds = PyGameMakerBackground.load_from_yaml(TEST_BACKGROUND_LIST_YAML_FILE)
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
            if self.background_idx < len(self.backgrounds):
                self.backgrounds[self.background_idx].draw_background(self.screen)

        def is_done(self):
            return self.done

    mymanager = MyGameManager()
    mygame = pg_template.PygameTemplate( (1024,768), "Background Tests",
        mymanager)
    mygame.run()

