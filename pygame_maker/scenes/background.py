#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker room backgrounds

import pygame
import os.path
import yaml
import re


class BackgroundException(Exception):
    pass


class TileProperties(object):
    """
    Wrap tiling properties.
    """
    DEFAULT_TILE_WIDTH=16
    DEFAULT_TILE_HEIGHT=16
    def __init__(self, **kwargs):
        """
        Initialize a new TileProperties instance.

        :param kwargs: Dict containing parameter settings to apply to the new
            instance:

            * tile_width (int): Horizontal width of tiles [16]
            * tile_height (int): Vertical height of tiles [16]
            * horizontal_offset (int): X coordinate of the left edge of the
              tileset [0]
            * vertical_offset (int): Y coordinate of the top edge of the
              tileset [0]
            * horizontal_padding (int): Horizontal gap between tiles [0]
            * vertical_padding (int): Vertical gap between tiles [0]
        """
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
        return(isinstance(other, TileProperties) and
            (self.tile_width == other.tile_width) and
            (self.tile_height == other.tile_height) and
            (self.horizontal_offset == other.horizontal_offset) and
            (self.vertical_offset == other.vertical_offset) and
            (self.horizontal_padding == other.horizontal_padding))


class Background(object):
    """
    The Background resource used by Rooms.
    """
    DEFAULT_NAME="bkg_"

    @staticmethod
    def load_from_yaml(yaml_stream, unused=None):
        """
        Create background(s) from a YAML-formatted file.
        Expected format (missing fields will receive default values)::

            - bkg_name1:
                filename: <image_file_name>
                smooth_edges: True|False
                preload_texture: True|False
                transparent: True|False
                tileset: True|False
                tile_width: <# >= 0>
                tile_height: <# >= 0>
                horizontal_offset: <# >= 0>
                vertical_offset: <# >= 0>
                horizontal_padding: <# >= 0>
                vertical_padding: <# >= 0>

        :param yaml_stream: A stream containing YAML-formatted strings
        :type yaml_stream: file-like
        :param unused: A placeholder, since other load_from_yaml() methods
            receive a game engine handle here
        :return: A list of new Background instances for all valid backgrounds
            defined in the YAML stream
        """
        new_background_list = []
        yaml_repr = yaml.load(yaml_stream)
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
                new_background_list.append(Background(bkg_name, **kwargs))
        return new_background_list

    def __init__(self, name, **kwargs):
        """
        Initialize a new Background instance.

        :param name: The name for the new background
        :type name: str
        :param kwargs: The list of parameters to set in the new instance:

            * filename (str): The filename to use as a background image [""]
            * smooth_edges (bool): Whether to smooth edges (NYI) [False]
            * preload_texture (bool): Whether to preload the background image
              [False]
            * transparent (bool): Whether the background image should have
              pixel transparency [False]
            * tileset (bool): Whether the background image is a tile set
              [False]

            Parameters recognized by TileProperties will be passed on, and
            wrapped in a :py:class:`TileProperties` instance.
        :return:
        """
        self.name = name
        self.filename = ""
        self.tile_properties = TileProperties(**kwargs)
        self.smooth_edges = False
        self.preload_texture = False
        self.transparent = False
        self.tileset = False
        self.image = None
        self.image_size = (0,0)
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

    def setup(self):
        """
        Preload the image if ``preload_texture`` is set.

        Only call this method after pygame.init().
        """
        if self.filename and self.preload_texture and self.check_filename():
            self.load_graphic()

    def load_graphic(self):
        """
        Load the background image from the file.

        Use a black background in case there are transparent pixels in the
        image, and the transparent attribute is False.
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
        Draw the background color and image (with tiling if specified) to the
        supplied screen.

        :param screen: The screen to draw this background onto
        :type screen: :py:class:`pygame.Surface`
        :param xy_offset: X, Y offset for the upper left corner of
            the image/tileset (in addition to the background's configured
            horizontal/vertical offsets if it's a tileset)
        :type xy_offset: 2-element array-like
        """
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
        """
        Error-check filename.

        :raise: BackgroundException if the filename is not a string, or if the
            file was missing or empty
        :return: True if the filename is found, and not empty
        :rtype: bool
        """
        if not isinstance(self.filename, str):
            raise BackgroundException("Background error ({}): filename '{}' is not a string".format(str(self),
                                                                                                    self.filename))
        elif len(self.filename) == 0:
            raise BackgroundException("Background error ({}): filename is empty".format(str(self),
                                                                                        self.filename))
        if len(self.filename) > 0:
            if not os.path.exists(self.filename):
                raise BackgroundException("Background error ({}): filename '{}' not found".format(str(self),
                                                                                                  self.filename))
        return True

    def __eq__(self, other):
        return(isinstance(other, Background) and
            (self.name == other.name) and
            (self.filename == other.filename) and
            (self.smooth_edges == other.smooth_edges) and
            (self.preload_texture == other.preload_texture) and
            (self.transparent == other.transparent) and
            (self.tileset == other.tileset) and
            (self.tile_properties == other.tile_properties))

    def __repr__(self):
        return "<{} name='{}'>".format(type(self).__name__, self.name)
