"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Pygame maker room resource type.
"""

import pygame
import yaml
from pygame_maker.support import logging_object
from pygame_maker.actions import action
from pygame_maker.support import color


class RoomException(Exception):
    """
    Raised when a room is unable to load its objects or object code, or when
    the screen dimensions change unexpectedly.
    """
    pass


class Room(logging_object.LoggingObject):
    """
    Represent "rooms" in PyGameMaker, which are where all actions happen.
    """
    #: Room background color used if not specified
    DEFAULT_BACKGROUND_COLOR = color.Color((0, 0, 0))
    #: Room dimensions used if not specified
    DEFAULT_DIMENSIONS = (640, 480)
    #: Room frame rate used if not specified
    DEFAULT_FRAME_RATE = 30
    DEFAULT_NAME = "rm_"
    ATTRIBUTES_TABLE = {
        'width': int,
        'height': int,
        'speed': float,
        'persistent': bool,
        'init_code': str,
        'background': str,
        'background_color': color.Color,
        'draw_background_color': bool,
        'background_horizontal_offset': int,
        'background_vertical_offset': int,
        'background_visible': bool,
        'tile_horizontal': bool,
        'tile_vertical': bool,
        'stretch:': bool,
        'grid_x_offset': int,
        'grid_y_offset': int,
        'grid_width': int,
        'grid_height': int,
    }

    @staticmethod
    def load_from_yaml(yaml_stream, game_engine):
        """
        Create room(s) from a YAML-formatted file.
        Expected format (missing fields will receive default values)::

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

        :param yaml_stream: The stream containing YAML-formatted strings
        :type yaml_stream: file-like
        :param game_engine: The game engine instance, which allows each Room
            instance to find other game resources
        :type game_engine: GameEngine
        :return: A list of valid rooms found in the YAML string
        :rtype: list
        """
        new_room_list = []
        yaml_repr = yaml.load(yaml_stream)
        if yaml_repr:
            for top_level in yaml_repr:
                kwargs = {}
                room_name = list(top_level.keys())[0]
                room_yaml = top_level[room_name]
                for attr in list(Room.ATTRIBUTES_TABLE.keys()):
                    if attr in list(room_yaml.keys()):
                        kwargs[attr] = room_yaml[attr]
                if 'object_instances' in list(room_yaml.keys()):
                    kwargs['object_instances'] = room_yaml['object_instances']
                new_room_list.append(Room(room_name, game_engine, **kwargs))
        return new_room_list

    def __init__(self, name, game_engine, **kwargs):
        """
        Initialize a new Room instance.

        :param name: The room's name
        :type name: str
        :param game_engine: The game engine instance
        :type game_engine: GameEngine
        :param kwargs: A dict containing Room parameters to set in the new
            instance:

            * width (int): The room's width [640]
            * height (int): The room's height [480]
            * speed (float): The speed the room's image will move in pixels per
              frame [0.0]
            * persistent (bool): True if the room's state will be saved when
              the game engine switches to a new room [False]
            * init_code (str): Game language code to run when the room is
              entered [None]
            * background (str): The name of the background resource to use for
              this room [None]
            * background_color (:py:class:`~pygame_maker.support.color.Color`):
              The background color to use for this room [black]
            * draw_background_color (bool): True if the background color should
              be drawn each frame [True]
            * background_horizontal_offset (int): The X coordinate to use for
              the background's left edge [0]
            * background_vertical_offset (int): The Y coordinate to use for the
              background's top edge [0]
            * background_visible (bool): True if the background should be
              visible (NYI) [True]
            * tile_horizontal (bool): True if the background should be tiled
              horizontally (separate from tileset properties) [False]
            * tile_vertical (bool): True if the background should be tiled
              vertically (separate from tileset properties) [False]
            * stretch: (bool): True if the background image should be stretched
              to fit the room's dimensions (NYI) [False]
            * grid_width (int): The default X snap distance (NYI) [0]
            * grid_height (int): The default Y snap distance (NYI) [0]
            * grid_x_offset (int): The left edge of the snap region (NYI) [0]
            * grid_y_offset (int): The top edge of the snap region (NYI) [0]
            * object_instances (list): A list of dicts containing one or more
              :py:class:`~pygame_maker.actors.object_type.ObjectType` names to
              populate the room with when initialized, along with their
              coordinates relative to the room's top left corner [empty]
        """
        super(Room, self).__init__(type(self).__name__)
        #: Name the room will be referenced by in other code
        self.name = name
        #: Handle to the main game engine
        self.game_engine = game_engine
        #: Room's width in pixels
        self.width = self.DEFAULT_DIMENSIONS[0]
        #: Room's height in pixels
        self.height = self.DEFAULT_DIMENSIONS[1]
        #: Speed of action in the room, in frames per second
        self.frame_rate = self.DEFAULT_FRAME_RATE
        #: Record the room's state when leaving, and restore it when the room
        #: is loaded again later
        self.persistent = False
        # Code string that will be executed when the room is loaded
        self._init_code = ""
        #: The list of object instances to create when the room loads
        self.init_object_instances = []
        #: The list of object instances inside the room
        self.object_instances = []
        #: The Background instance to draw
        self.background = None
        #: True if a background color should be painted
        self.draw_background_color = True
        #: True if the background should be tiled horizontally
        self.tile_horizontal = False
        #: True if the background should be tiled vertically
        self.tile_vertical = False
        #: True if the background should be stretched to fit the room
        self.stretch = False
        #: The background color to paint, if draw_background_color is True
        self.background_color = self.DEFAULT_BACKGROUND_COLOR
        # Shadow the 0th element of the background_offsets array (property)
        self._background_horizontal_offset = 0
        # Shadow the 1st element of the background_offsets array (property)
        self._background_vertical_offset = 0
        #: The upper left pixel coordinate to draw the background at
        self.background_offsets = [0, 0]
        #: True if the background will be drawn
        self.background_visible = True
        #: A pygame Rect representing the snap grid width, height, and upper
        #:  left coordinate
        self.grid = pygame.Rect(0, 0, 16, 16)
        # A pygame.Surface to draw the background on once, and reuse afterwards
        self._cached_background = None
        # A pygame.Rect containing the width, height, and upper left coordinate
        # of the cached background
        self._cached_rect = pygame.Rect(0, 0, 0, 0)
        #: The width of the background, determined after its image is loaded
        self.bkg_width = 0
        #: The height of the background, determined after its image is loaded
        self.bkg_height = 0
        #: The width of the surface drawn to, cached the first time the room
        #: is drawn
        self.disp_width = 0
        #: The height of the surface drawn to, cached the first time the room
        #: is drawn
        self.disp_height = 0
        if kwargs:
            for attr in list(self.ATTRIBUTES_TABLE.keys()):
                if attr in kwargs:
                    attr_type = self.ATTRIBUTES_TABLE[attr]
                    if attr_type != bool:
                        setattr(self, attr, attr_type(kwargs[attr]))
                    else:
                        setattr(self, attr, (kwargs[attr] is True))
            if 'object_instances' in kwargs:
                # This is a list of hashes inside hashes containing info
                #  about objects to be placed when the room is loaded.
                #  E.G. [{'obj_name1': {'position':(10,10)}},...]
                obj_list = list(kwargs['object_instances'])
                for obj_check in obj_list:
                    obj_ok = True
                    err_msg = ""
                    init_code = None
                    obj_name = list(obj_check.keys())[0]
                    if 'position' not in obj_check[obj_name]:
                        obj_ok = False
                        err_msg = "Missing position for object '{}'".format(obj_name)
                    pos_list = list(obj_check[obj_name]['position'])
                    if len(pos_list) < 2:
                        obj_ok = False
                        err_msg = "Invalid position '{}' for object '{}'".format(
                            obj_check[obj_name]['position'], obj_name)
                    if 'init_code' in list(obj_check[obj_name].keys()):
                        if not isinstance(obj_check[obj_name]['init_code'], str):
                            obj_ok = False
                            err_msg = "Invalid code block '{}' for object '{}'".format(
                                obj_check[obj_name]['init_code'], obj_name)
                        init_code = obj_check[obj_name]['init_code']
                    if not obj_ok:
                        self.error("{}: Failed to create room: {}".format(
                            type(self).__name__, err_msg))
                        raise RoomException
                    self.add_init_object_instance_at(obj_name,
                                                     obj_check[obj_name]['position'],
                                                     init_code)

    @property
    def init_code(self):
        """Get and set the code block to execute when the room is loaded."""
        return self._init_code

    @init_code.setter
    def init_code(self, value):
        self._init_code = value
        self.set_init_code_block(value)

    @property
    def background_horizontal_offset(self):
        """Get and set the background resource's horizontal offset."""
        return self._background_horizontal_offset

    @background_horizontal_offset.setter
    def background_horizontal_offset(self, value):
        self._background_horizontal_offset = value
        self.background_offsets[0] = value

    @property
    def background_vertical_offset(self):
        """Get and set the background resource's vertical offset."""
        return self._background_vertical_offset

    @background_vertical_offset.setter
    def background_vertical_offset(self, value):
        self._background_vertical_offset = value
        self.background_offsets[1] = value

    def add_init_object_instance_at(self, object_type_name, locationxy,
                                    init_code=None):
        """
        Add to the list of object instances that should be created when the
        room is loaded.

        :param object_type_name: Name of the kind of object to place
        :type object_type_name: str
        :param locationxy: The x,y coordinates for the object
        :type locationxy: 2-element array-like
        :param init_code: Source code to execute when the instance is
            created
        :type init_code: None | str
        """
        self.debug("add_init_object_instance_at({}, {}, {}):".format(
            object_type_name, locationxy, init_code))
        loc = [int(locationxy[0]), int(locationxy[1])]
        self.init_object_instances.append((object_type_name, loc, init_code))

    def add_object_instance_at(self, surface, object_type_name, locationxy,
                               init_code):
        """
        Create a new object instance in the room.

        :param surface: Usually the game screen
        :type surface: :py:class:`pygame.Surface`
        :param object_type_name: Name of the kind of object to place
        :type object_type_name: str
        :param locationxy: The x,y coordinates
        :type locationxy: 2-element array-like
        :param init_code: Optional source code block to run after
            creating the instance
        :type init_code: None | str
        """
        self.debug("add_object_instance_at({}, {}, {}, {}):".format(
            surface, object_type_name, locationxy, init_code))
        if object_type_name in list(self.game_engine.resources['objects'].keys()):
            self.object_instances.append(
                self.game_engine.resources['objects'][object_type_name].create_instance(
                    surface, position=locationxy))
            new_obj = self.object_instances[-1]
            self.info("  Room {}: Created obj {} id {:d}".format(
                self.name, object_type_name, new_obj.inst_id))
            if init_code is not None:
                # Create a throw-away code action, and send it to the new
                #  instance's execute_code method.
                code_action = action.CodeAction('execute_code', code=init_code)
                self.object_instances[-1].execute_code(code_action,
                                                       keep_code_block=False)

    def set_init_code_block(self, code_block_string):
        """
        Set the initialization code block to be run when the room is loaded.

        :param code_block_string: Source code string in game language
        :type code_block_string: str
        """
        self.debug("set_init_code_block({}):".format(code_block_string))
        self.game_engine.language_engine.register_code_block(
            "{}_init".format(self.name), code_block_string)

    def set_background(self, background):
        """
        Select a background resource to draw onto the room.

        :param background: An instance of Background
        :type background: :py:class:`Background`
        """
        self.debug("set_background({}):".format(background))
        self.background = background

    def load_room(self, surface):
        """
        Load the background, if any.  Create the room's objects.  Run the
        initialization code.

        :param surface: Usually the game screen
        :type surface: :py:class:`pygame.Surface`
        """
        self.debug("load_room({}):".format(surface))
        self.info("  load room named '{}'".format(self.name))
        if (self.background and (self.background in
                                 list(self.game_engine.resources['backgrounds'].keys()))):
            self.game_engine.resources['backgrounds'][self.background].load_graphic()
        if len(self._init_code) > 0:
            self.game_engine.language_engine.execute_code_block(
                "{}_init".format(self.name))
        # instantiate objects in the init_object_instances list
        for an_object, positionxy, init_code in self.init_object_instances:
            self.add_object_instance_at(surface, an_object, positionxy,
                                        init_code)

    def draw_room_background(self, surface):
        """
        Clear the surface to the background color if needed, then draw the
        background image (if any) on top of it.

        :param surface: Usually the game screen
        :type surface: :py:class:`pygame.Surface`
        """
        self.debug("draw_room_background({}):".format(surface))
        if self.draw_background_color:
            surface.fill(self.background_color.rgb)
        # draw the background
        if self.background:
            # draw background image, if any
            if self.background in list(self.game_engine.resources['backgrounds'].keys()):
                bkg = self.game_engine.resources['backgrounds'][self.background]
                if ((self.disp_width != surface.get_width()) or
                        (self.disp_height != surface.get_height())):
                    if self._cached_background is not None:
                        # What happened here?!
                        self.error("room {} draw_room_background():".format(self.name) + \
                                   " display surface changed dimensions!")
                        raise RoomException(
                            "room {} draw_room_background():".format(self.name) + \
                            "display surface changed dimensions!")
                    self.disp_width = surface.get_width()
                    self.disp_height = surface.get_height()
                if self._cached_background:
                    # The background is already done, so copy it to the display
                    surface.blit(self._cached_background,
                                 (self._cached_rect[0], self._cached_rect[1]),
                                 area=self._cached_rect)
                elif bkg.image:
                    # Draw to the background cache so these calculations only
                    #  need to happen once.
                    rows = 1
                    cols = 1
                    if self.bkg_width != bkg.image.get_width():
                        self.bkg_width = bkg.image.get_width()
                    if self.bkg_height != bkg.image.get_height():
                        self.bkg_height = bkg.image.get_height()
                    self._cached_background = surface.copy()
                    self._cached_rect.x = self.background_offsets[0]
                    self._cached_rect.y = self.background_offsets[1]
                    if bkg.tileset:
                        # Tilesets already know how to cover the display.
                        # print("Cache tiled background..")
                        self._cached_rect.width = self.disp_width - self.background_offsets[0]
                        self._cached_rect.height = self.disp_height - self.background_offsets[1]
                        bkg.draw_background(self._cached_background, self.background_offsets)
                    else:
                        # A simple background image can be tiled
                        #  horizontally and/or vertically using room
                        #  settings.  Remember to account for x,y offsets.
                        # print("Cache normal background")
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
                        self._cached_rect.height = (rows * self.bkg_height)
                        self._cached_rect.width = (cols * self.bkg_width)
                        for bkg_row in range(rows):
                            for bkg_col in range(cols):
                                offsets = [self.background_offsets[0] +
                                           bkg_col * self.bkg_width,
                                           self.background_offsets[1] +
                                           bkg_row * self.bkg_height]
                                bkg.draw_background(self._cached_background,
                                                    offsets)
