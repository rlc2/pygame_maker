#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker rooms

import pygame
import yaml
from pygame_maker.support import logging_object
from pygame_maker.actions import action
from pygame_maker.support import color

class RoomException(Exception):
    pass

class Room(logging_object.LoggingObject):
    """
        class Room:
        Represent "rooms" in PyGame Maker, which are where all actions happen.
    """
    DEFAULT_BACKGROUND_COLOR = color.Color( (0,0,0) )
    DEFAULT_DIMENSIONS=(640, 480)
    DEFAULT_FRAME_RATE=30
    DEFAULT_NAME="rm_"
    DEFAULT_LOCATION_XY=(0,0)
    ATTRIBUTES_TABLE={
        'width':                        int,
        'height':                       int,
        'speed':                        float,
        'persistent':                   bool,
        'init_code':                    str,
        'background':                   str,
        'background_color':             color.Color,
        'draw_background_color':        bool,
        'background_horizontal_offset': int,
        'background_vertical_offset':   int,
        'background_visible':           bool,
        'tile_horizontal':              bool,
        'tile_vertical':                bool,
        'stretch:':                     bool,
        'grid_x_offset':                int,
        'grid_y_offset':                int,
        'grid_width':                   int,
        'grid_height':                  int,
    }

    @staticmethod
    def load_from_yaml(yaml_file_name, game_engine):
        """
            load_from_yaml():
            Create room(s) from a YAML-formatted file.
            Expected format (missing fields will receive default values):
            - rm_name1:
                width: <# >= 0>
                height: <# >= 0>
                speed: <number>
                persistent: True | False
                init_code: |
                    code block...
                background: <background_resource_name>
                background_color: <#RRGGBB | (R, G, B)>
                draw_background_color: True | False
                background_horizontal_offset: <# >= 0>
                background_vertical_offset: <# >= 0>
                background_visible: True | False
                tile_horizontal: True | False
                tile_vertical: True | False
                stretch: True | False
                grid_x_offset: <# >= 0>
                grid_y_offset: <# >= 0>
                grid_width: <# >= 0>
                grid_height: <# >= 0>
                object_instances:
                    - <obj_resource_name>:
                        position: [<pos_x>,<pos_y>]
                        init_code: |
                          init_code_block

        """
        yaml_repr = None
        new_room_list = []
        with open(yaml_file_name, "r") as yaml_f:
            yaml_repr = yaml.load(yaml_f)
        if yaml_repr:
            for top_level in yaml_repr:
                kwargs = {}
                room_name = top_level.keys()[0]
                room_yaml = top_level[room_name]
                for attr in Room.ATTRIBUTES_TABLE.keys():
                    if attr in room_yaml.keys():
                        kwargs[attr] = room_yaml[attr]
                if 'object_instances' in room_yaml.keys():
                    kwargs['object_instances'] = room_yaml['object_instances']
                new_room_list.append(Room(room_name, game_engine,
                    **kwargs))
        return(new_room_list)

    def __init__(self, name, game_engine, **kwargs):
        super(Room, self).__init__(type(self).__name__)
        self.name = name
        self.game_engine = game_engine
        self.width = self.DEFAULT_DIMENSIONS[0]
        self.height = self.DEFAULT_DIMENSIONS[1]
        self.frame_rate = self.DEFAULT_FRAME_RATE 
        self.persistent = False
        self._init_code = ""
        self.init_code_block = None
        self.init_object_instances = []
        self.object_instances = []
        self.background = None
        self.draw_background_color = True
        self.tile_horizontal = True
        self.tile_vertical = True
        self.stretch = False
        self.background_color = self.DEFAULT_BACKGROUND_COLOR
        self._background_horizontal_offset = 0
        self._background_vertical_offset = 0
        self.background_offsets = [0,0]
        self.background_visible = False
        self.grid = pygame.Rect(0,0,16,16)
        self.cached_background = None
        self.cached_rect = pygame.Rect(0,0,0,0)
        self.bkg_width = 0
        self.bkg_height = 0
        self.disp_width = 0
        self.disp_height = 0
        if kwargs:
            for attr in self.ATTRIBUTES_TABLE.keys():
                if attr in kwargs:
                    attr_type = self.ATTRIBUTES_TABLE[attr]
                    if attr_type != bool:
                        setattr(self, attr, attr_type(kwargs[attr]))
                    else:
                        setattr(self, attr, (kwargs[attr] == True))
            if 'object_instances' in kwargs:
                # This is a list of hashes inside hashes containing info
                #  about objects to be placed when the room is loaded.
                #  E.G. [{'obj_name1': {'position':(10,10)}},...]
                obj_list = list(kwargs['object_instances'])
                for obj_check in obj_list:
                    obj_ok = True
                    err_msg = ""
                    init_code = None
                    obj_name = obj_check.keys()[0]
                    if not 'position' in obj_check[obj_name]:
                        obj_ok = False
                        err_msg = "Missing position for object '{}'".format(obj_name)
                    pos_list = list(obj_check[obj_name]['position'])
                    if len(pos_list) < 2:
                        obj_ok = False
                        err_msg = "Invalid position '{}' for object '{}'".format(obj_check[obj_name]['position'], obj_name)
                    if 'init_code' in obj_check[obj_name].keys():
                        if (not isinstance(obj_check[obj_name]['init_code'],
                            str)):
                            obj_ok = False
                            err_msg = "Invalid code block '{}' for object '{}'".format(obj_check[obj_name]['init_code'], obj_name)
                        init_code = obj_check[obj_name]['init_code']
                    if not obj_ok:
                        self.error("{}: Failed to create room: {}".format(type(self).__name__, err_msg))
                        raise(RoomException("{}: Failed to create room: {}".format(type(self).__name__, err_msg)))
                    self.add_init_object_instance_at(obj_name,
                        obj_check[obj_name]['position'], init_code)


    @property
    def init_code(self):
        return self._init_code

    @init_code.setter
    def init_code(self, value):
        self._init_code = value
        self.set_init_code_block(value)

    @property
    def background_horizontal_offset(self):
        return self._background_horizontal_offset

    @background_horizontal_offset.setter
    def background_horizontal_offset(self, value):
        self._background_horizontal_offset = value
        self.background_offsets[0] = value

    @property
    def background_vertical_offset(self):
        return self._background_vertical_offset

    @background_vertical_offset.setter
    def background_vertical_offset(self, value):
        self._background_vertical_offset = value
        self.background_offsets[1] = value

    def add_init_object_instance_at(self, object_type_name, locationxy,
        init_code=None):
        """
            add_init_object_instance_at():
            Add to the list of object instances that should be created when
            the room is loaded.
            parameters:
              object_type (str): Name of the kind of object to place
              locationxy (list): The x,y coordinates
              init_code (str): Source code to execute when the instance is
               created
        """
        self.debug("add_init_object_instance_at({}, {}, {}):".format(object_type_name, locationxy, init_code))
        loc = []
        loc.append(int(locationxy[0]))
        loc.append(int(locationxy[1]))
        self.init_object_instances.append( (object_type_name, loc, init_code) )

    def add_object_instance_at(self, surface, object_type_name, locationxy,
        init_code):
        """
            add_object_instance_at():
            Create a new object instance in the room.
            parameters:
              surface (pygame.Surface): Usually the game screen
              object_type (str): Name of the kind of object to place
              locationxy (list): The x,y coordinates
              init_code (str or None): Optional source code block to run after
               creating the instance
        """
        self.debug("add_object_instance_at({}, {}, {}, {}):".format(surface, object_type_name, locationxy, init_code))
        if object_type_name in self.game_engine.resources['objects'].keys():
            self.object_instances.append(self.game_engine.resources['objects'][object_type_name].create_instance(surface, position=locationxy))
            new_obj = self.object_instances[-1]
            self.info("  Room {}: Created obj {} id {}".format(self.name,
                object_type_name, new_obj.id))
            if init_code:
                # Create a throw-away code action, and send it to the new
                #  instance's execute_code method.
                code_action = action.CodeAction('execute_code',
                    code=init_code)
                self.object_instances[-1].execute_code(code_action,
                    keep_code_block=False)

    def set_init_code_block(self, code_block_string):
        """
            set_init_code_block():
            Set the initialization code block to be run when the room is
            loaded.
            Parameters:
              language_engine (LanguageEngine): Language engine
              code_block_string: Source code string in toy language
        """
        self.debug("set_init_code_block({}):".format(code_block_string))
        self.init_code_block = self.game_engine.language_engine.register_code_block("{}_init".format(self.name), code_block_string)

    def set_background(self, background):
        """
            set_background():
            Select a background resource to draw onto the room
            Parameters:
              background: An instance of Background
        """
        self.debug("set_background({}):".format(background))
        self.background = background

    def load_room(self, surface):
        """
            load_room():
            Load the background, if any. Create the room's objects. Run the
             init_code_block.
            Parameters:
             surface (pygame.Surface): Usually the game screen
        """
        self.debug("load_room({}):".format(surface))
        self.info("  load room named '{}'".format(self.name))
        if (self.background and (self.background in
            self.game_engine.resources['backgrounds'].keys())):
            self.game_engine.resources['backgrounds'][self.background].load_graphic()
        if self.init_code_block:
            self.game_engine.language_engine.execute_code_block("{}_init".format(self.name))
        # instantiate objects in the init_object_instances list
        for an_object, positionxy, init_code in self.init_object_instances:
            self.add_object_instance_at(surface, an_object, positionxy,
                init_code)

    def draw_room_background(self, surface):
        """
            draw_room_background()
            Clear the surface to the background color, then draw the background
            image (if any) on top of it.
            Parameters:
              surface (pygame.Surface): Usually the game screen
        """
        self.debug("draw_room_background({}):".format(surface))
        if self.draw_background_color:
            surface.fill(self.background_color.color)
        # draw the background
        if self.background:
            # draw background image, if any
            if self.background in self.game_engine.resources['backgrounds'].keys():
                bkg = self.game_engine.resources['backgrounds'][self.background]
                if ((self.disp_width != surface.get_width()) or
                    (self.disp_height != surface.get_height())):
                    if self.cached_background:
                        # What happened here?!
                        self.error("room {} draw_room_background(): display surface changed dimensions!".format(name))
                        raise(RoomException("room {} draw_room_background(): display surface changed dimensions!".format(name)))
                    self.disp_width = surface.get_width()
                    self.disp_height = surface.get_height()
                if self.cached_background:
                    # The background is already done, so copy it to the display
                    surface.blit(self.cached_background,
                        (self.cached_rect[0],self.cached_rect[1]),
                        area=self.cached_rect)
                elif bkg.image:
                    # Draw to the background cache so these calculations only
                    #  need to happen once.
                    rows = 1
                    cols = 1
                    if (self.bkg_width != bkg.image.get_width()):
                        self.bkg_width = bkg.image.get_width()
                    if (self.bkg_height != bkg.image.get_height()):
                        self.bkg_height = bkg.image.get_height()
                    self.cached_background = surface.copy()
                    self.cached_rect.x = self.background_offsets[0]
                    self.cached_rect.y = self.background_offsets[1]
                    if bkg.tileset:
                        # Tilesets already know how to cover the display.
                        print("Cache tiled background..")
                        self.cached_rect.width = self.disp_width - self.background_offsets[0]
                        self.cached_rect.height = self.disp_height - self.background_offsets[1]
                        bkg.draw_background(self.cached_background,
                            self.background_offsets)
                    else:
                        # A simple background image can be tiled
                        #  horizontally and/or vertically using room
                        #  settings. Remember to account for x,y offsets.
                        print("Cache normal background")
                        pix_width = self.disp_width - self.background_offsets[0]
                        if self.tile_horizontal and (self.bkg_width < pix_width):
                            cols = pix_width / self.bkg_width
                            overage = pix_width % self.bkg_width
                            if overage != 0:
                                cols += 1
                        pix_height = self.disp_height - self.background_offsets[1]
                        if self.tile_vertical and (self.bkg_height < pix_height):
                            rows = pix_height / self.bkg_height
                            overage = pix_height % self.bkg_height
                            if overage != 0:
                                rows += 1
                        self.cached_rect.height = (rows * self.bkg_height)
                        self.cached_rect.width = (cols * self.bkg_width)
                        for bkg_row in range(rows):
                            for bkg_col in range(cols):
                                offsets = []
                                offsets.append(self.background_offsets[0] +
                                    bkg_col * self.bkg_width)
                                offsets.append(self.background_offsets[1] +
                                    bkg_row * self.bkg_height)
                                bkg.draw_background(self.cached_background,
                                    offsets)

