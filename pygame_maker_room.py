#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker rooms

import pygame
import yaml
import re
import pygame_maker_action as pgm_action

class PyGameMakerRoomException(Exception):
    pass

class PyGameMakerRoom(object):
    """
        class PyGameMakerRoom:
        Represent "rooms" in PyGame Maker, which are where all actions happen.
    """
    DEFAULT_BACKGROUND_COLOR = (0,0,0)
    DEFAULT_DIMENSIONS=(640, 480)
    DEFAULT_FRAME_RATE=30
    DEFAULT_NAME="rm_"
    DEFAULT_LOCATION_XY=(0,0)
    COLOR_STRING_RE=re.compile("#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})")

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
                init_code_block: |
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
                if 'width' in room_yaml.keys():
                    kwargs['width'] = room_yaml['width']
                if 'height' in room_yaml.keys():
                    kwargs['height'] = room_yaml['height']
                if 'speed' in room_yaml.keys():
                    kwargs['speed'] = room_yaml['speed']
                if 'persistent' in room_yaml.keys():
                    kwargs['persistent'] = room_yaml['persistent']
                if 'init_code_block' in room_yaml.keys():
                    kwargs['init_code_block'] = room_yaml['init_code_block']
                if 'background' in room_yaml.keys():
                    kwargs['background'] = room_yaml['background']
                if 'background_color' in room_yaml.keys():
                    kwargs['background_color'] = room_yaml['background_color']
                if 'draw_background_color' in room_yaml.keys():
                    kwargs['draw_background_color'] = room_yaml['draw_background_color']
                if 'background_horizontal_offset' in room_yaml.keys():
                    kwargs['background_horizontal_offset'] = room_yaml['background_horizontal_offset']
                if 'background_vertical_offset' in room_yaml.keys():
                    kwargs['background_vertical_offset'] = room_yaml['background_vertical_offset']
                if 'background_visible' in room_yaml.keys():
                    kwargs['background_visible'] = room_yaml['background_visible']
                if 'tile_horizontal' in room_yaml.keys():
                    kwargs['tile_horizontal'] = room_yaml['tile_horizontal']
                if 'tile_vertical' in room_yaml.keys():
                    kwargs['tile_vertical'] = room_yaml['tile_vertical']
                if 'stretch' in room_yaml.keys():
                    kwargs['stretch'] = room_yaml['stretch']
                if 'grid_x_offset' in room_yaml.keys():
                    kwargs['grid_x_offset'] = room_yaml['grid_x_offset']
                if 'grid_y_offset' in room_yaml.keys():
                    kwargs['grid_y_offset'] = room_yaml['grid_y_offset']
                if 'grid_width' in room_yaml.keys():
                    kwargs['grid_width'] = room_yaml['grid_width']
                if 'grid_height' in room_yaml.keys():
                    kwargs['grid_height'] = room_yaml['grid_height']
                if 'object_instances' in room_yaml.keys():
                    kwargs['object_instances'] = room_yaml['object_instances']
                new_room_list.append(PyGameMakerRoom(room_name, game_engine,
                    **kwargs))
            return new_room_list

    def __init__(self, name, game_engine, **kwargs):
        self.name = name
        self.game_engine = game_engine
        self.width = self.DEFAULT_DIMENSIONS[0]
        self.height = self.DEFAULT_DIMENSIONS[1]
        self.frame_rate = self.DEFAULT_FRAME_RATE 
        self.persistent = False
        self.init_code_block = None
        self.init_object_instances = []
        self.object_instances = []
        self.background = None
        self.draw_background_color = True
        self.tile_horizontal = True
        self.tile_vertical = True
        self.stretch = False
        self.background_color = self.DEFAULT_BACKGROUND_COLOR
        self.background_offsets = [0,0]
        self.background_visible = False
        self.grid = pygame.Rect(0,0,16,16)
        self.cached_background = None
        self.bkg_width = 0
        self.bkg_height = 0
        self.disp_width = 0
        self.disp_height = 0
        if kwargs:
            for kwarg in kwargs:
                if kwarg == 'width':
                    self.width = kwargs['width']
                if kwarg == 'height':
                    self.height = kwargs['height']
                if kwarg == 'speed':
                    self.frame_rate = kwargs['speed']
                if kwarg == 'persistent':
                    self.persistent = (kwargs['persistent'] == True)
                if kwarg == 'init_code_block':
                    self.set_init_code_block(self.game_engine.language_engine,
                        kwargs['init_code_block'])
                if kwarg == 'background':
                    self.background = kwargs['background']
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
                            raise(PyGameMakerRoomException("{}: Supplied background_color '{}' not recognized (supply a 3-item list or #RRGGBB string)".format(type(self).__name__, kwargs['background_color'])))
                    else:
                        clist = list(kwargs['background_color'])
                        if len(clist) >= 3:
                            self.background_color = (clist[0], clist[1], clist[2])
                        else:
                            raise(PyGameMakerRoomException("{}: Supplied background_color '{}' not recognized (supply a 3-item list or #RRGGBB string)".format(type(self).__name__, kwargs['background_color'])))
                if kwarg == 'draw_background_color':
                    self.draw_background_color = (kwargs['draw_background_color'] == True)
                if kwarg == 'background_horizontal_offset':
                    self.background_offsets[0] = kwargs['background_horizontal_offset']
                if kwarg == 'background_vertical_offset':
                    self.background_offsets[1] = kwargs['background_vertical_offset']
                if kwarg == 'background_visible':
                    self.background_visible = (kwargs['background_visible'] == True)
                if kwarg == 'tile_horizontal':
                    self.tile_horizontal = (kwargs['tile_horizontal'] == True)
                if kwarg == 'tile_vertical':
                    self.tile_vertical = (kwargs['tile_vertical'] == True)
                if kwarg == 'stretch':
                    self.stretch = (kwargs['stretch'] == True)
                # grid options are for the room editor, not for the rooms
                #  themselves
                if kwarg == 'grid_x_offset':
                    self.grid.x = int(kwargs['grid_x_offset'])
                if kwarg == 'grid_y_offset':
                    self.grid.x = int(kwargs['grid_y_offset'])
                if kwarg == 'grid_width':
                    self.grid.width = int(kwargs['grid_width'])
                if kwarg == 'grid_height':
                    self.grid.height = int(kwargs['grid_height'])
                if kwarg == 'object_instances':
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
                            raise(PyGameMakerRoomException("{}: Failed to create room: {}".format(type(self).__name__, err_msg)))
                        self.add_init_object_instance_at(obj_name,
                            obj_check[obj_name]['position'], init_code)


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
        if object_type_name in self.game_engine.resources['objects'].keys():
            self.object_instances.append(self.game_engine.resources['objects'][object_type_name].create_instance(surface, position=locationxy))
            if init_code:
                # Create a throw-away code action, and send it to the new
                #  instance's execute_code method.
                code_action = pgm_action.PyGameMakerCodeAction('execute_code',
                    code=init_code)
                self.object_instances[-1].execute_code(code_action)

    def set_init_code_block(self, language_engine, code_block_string):
        """
            set_init_code_block():
            Set the initialization code block to be run when the room is
            loaded.
            parameters:
              language_engine (PyGameMakerLanguageEngine): Language engine
              code_block_string: Source code string in toy language
        """
        self.init_code_block = language_engine.register_code_block("{}_init".format(self.name), code_block_string)

    def set_background(self, background):
        """
            set_background():
            Select a background resource to draw onto the room
            parameters:
              background: An instance of PyGameMakerBackground
        """
        self.background = background

    def load_room(self, surface):
        """
            load_room():
            Create the room's objects. Run the init_code_block.
            Parameters:
              surface (pygame.Surface): Usually the game screen
        """
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
        if self.draw_background_color:
            surface.fill(self.background_color)
        # draw the background
        if self.background:
            # draw background image, if any
            if self.background in self.game_engine.resources['backgrounds'].keys():
                bkg = self.game_engine.resources['backgrounds'][self.background]
                if ((self.disp_width != surface.get_width()) or
                    (self.disp_height != surface.get_height())):
                    if self.cached_background:
                        # What happened here?!
                        raise(PyGameMakerRoomException("{}.draw_room_background: display surface changed dimensions!".format(type(self).__name__)))
                    self.disp_width = surface.get_width()
                    self.disp_height = surface.get_height()
                if self.cached_background:
                    # The background is already done, so copy it to the display
                    surface.blit(self.cached_background, (0,0))
                else:
                    # Draw to the background cache so these calculations only
                    #  need to happen once.
                    if bkg.image:
                        rows = 1
                        cols = 1
                        if (self.bkg_width <= 0):
                            self.bkg_width = bkg.image.get_width()
                        if (self.bkg_height <= 0):
                            self.bkg_height = bkg.image.get_height()
                        self.cached_background = pygame.Surface(self.disp_width,
                            self.disp_height)
                        if bkg.tileset:
                            # Tilesets already know how to cover the display.
                            bkg.draw_background(self.cached_background,
                                self.background_offsets)
                        else:
                            # A simple background image can be tiled
                            #  horizontally and/or vertically using room
                            #  settings. Remember to account for x,y offsets.
                            pix_width = disp_width - self.background_offsets[0]
                            if self.tile_horizontal and (self.bkg_width < pix_width):
                                cols = pix_width / self.bkg_width
                                overage = pix_width % self.bkg_width
                                if overage != 0:
                                    cols += 1
                            pix_height = disp_height - self.background_offsets[1]
                            if self.tile_vertical and (self.bkg_height < pix_height):
                                rows = pix_height / self.bkg_height
                                overage = pix_height % self.bkg_height
                                if overage != 0:
                                    rows += 1
                            for bkg_row in range(rows):
                                for bkg_col in range(cols):
                                    offsets = []
                                    offsets.append(self.background_offsets[0] +
                                        bkg_col * self.bkg_width)
                                    offsets.append(self.background_offsets[1] +
                                        bkg_row * self.bkg_height)
                                    bkg.draw_background(self.cached_background,
                                        offsets)


if __name__ == "__main__":
    import pg_template
    import tempfile
    import os
    import pygame_maker_background as pgm_background
    import pygame_maker_language_engine as pgm_language_engine

    TEST_BACKGROUND_LIST_YAML_FILE="unittest_files/test_backgrounds.yaml"
    TEST_ROOM_LIST_YAML_FILE="unittest_files/test_rooms.yaml"

    class MyGameManager:
        LEFT_MARGIN = 10
        TOP_MARGIN  = 8
        LINE_HEIGHT = 18
        TEXT_COLOR  = (128,   0, 128)
        TEXT_BACKG  = (255, 255, 255)
        def __init__(self):
            self.current_events = []
            self.resources = {
                'rooms': [],
                'sprites': {},
                'sounds': {},
                'objects': {},
                'backgrounds': {}
            }
            self.language_engine = pgm_language_engine.PyGameMakerLanguageEngine()
            self.text_objects = []
            backgrounds = pgm_background.PyGameMakerBackground.load_from_yaml(TEST_BACKGROUND_LIST_YAML_FILE)
            for bkg in backgrounds:
                self.resources['backgrounds'][bkg.name] = bkg
            if len(self.resources['backgrounds'].keys()) == 0:
                print("Unable to load backgrounds from {}, aborting.".format(TEST_BACKGROUND_LIST_YAML_FILE))
                exit(1)
            self.resources['rooms'] = PyGameMakerRoom.load_from_yaml(TEST_ROOM_LIST_YAML_FILE, self)
            if len(self.resources['rooms']) == 0:
                print("Unable to load rooms from {}, aborting.".format(TEST_ROOM_LIST_YAML_FILE))
                exit(1)
            self.largest_dims = [0,0]
            for rm in self.resources['rooms']:
                if rm.width > self.largest_dims[0]:
                    self.largest_dims[0] = rm.width
                if rm.height > self.largest_dims[1]:
                    self.largest_dims[1] = rm.height
            self.font = None
            self.done = False
            self.screen = None
            self.font = None
            self.background_idx = 0
            self.room_idx = 0

        def setup(self, screen):
            self.screen = screen
            self.font = pygame.font.Font(None, 16)
            self.resources['rooms'][0].draw_room_background(self.screen)
            self.create_text("Room {}, ok? Y/N".format(self.resources['rooms'][0].name))

        def collect_event(self, event):
            self.current_events.append(event)

        def create_text(self, text):
            if len(self.text_objects) > 25:
                # too many text lines, remove oldest object
                self.text_objects = self.text_objects[1:]
            self.text_objects.append( ("text", self.font.render(text, 1, self.TEXT_COLOR, self.TEXT_BACKG)) )

        def update(self):
            for ev in self.current_events:
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.done = True
                        break
                    elif ev.key == pygame.K_y:
                        if self.room_idx < (len(self.resources['rooms'])-1):
                            self.room_idx += 1
                            self.create_text("Room {}, ok? Y/N".format(self.resources['rooms'][self.room_idx].name))
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
            for line, ob in enumerate(self.text_objects):
                self.draw_text(ob, line)

        def draw_background(self):
            if self.room_idx < len(self.resources['rooms']):
                self.resources['rooms'][self.room_idx].draw_room_background(self.screen)

        def is_done(self):
            return self.done

    mymanager = MyGameManager()
    mygame = pg_template.PygameTemplate( mymanager.largest_dims, "Room Tests",
        mymanager)
    mygame.run()

