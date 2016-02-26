#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# implement pygame_maker sprite resource (not the same as a pygame Sprite;
#  this is closer to a pygame.image)

import pygame
import os.path
import yaml


class ObjectSpriteException(Exception):
    pass


class ObjectSprite(object):
    """Wrap a sprite resource to be used by ObjectTypes."""
    #: Available collision type names
    COLLISION_TYPES = [
        "precise",
        "rectangle",
        "disk",
        "diamond",
        "polygon"
    ]
    #: Available bounding box type names
    BOUNDING_BOX_TYPES = [
        "automatic",
        "full_image",
        "manual"
    ]

    DEFAULT_SPRITE_PREFIX = "spr_"

    @staticmethod
    def load_from_yaml(sprite_yaml_stream, unused=None):
        """
        Create a new sprite from a YAML-formatted file.  Checks each key
        against known ObjectSprite parameters, and uses only those
        parameters to initialize a new sprite.
        Expected YAML object format::

            - spr_name1:
                filename: <filename>
                smooth_edges: true|false
                manual_bounding_box_rect:
                  top: 0
                  bottom: 32
                  left: 0
                  right: 32
                ...
            - spr_name2:
                ...

        :param sprite_yaml_stream: File or stream object containing YAML-
            formatted data
        :type sprite_yaml_stream: File-like object
        :param unused: This is a placeholder, since other load_from_yaml()
            methods take an additional argument.
        :return: An empty list, if the YAML-defined sprite(s) is (are) invalid,
            or a list of new sprites, for those with YAML fields that pass
            basic checks
        :rtype: list
        """
        new_sprite_list = []
        yaml_info = yaml.load(sprite_yaml_stream)
        if yaml_info:
            for top_level in yaml_info:
                sprite_args = {}
                sprite_name = top_level.keys()[0]
                yaml_info_hash = top_level[sprite_name]
                if 'filename' in yaml_info_hash:
                    sprite_args['filename'] = yaml_info_hash['filename']
                if 'smooth_edges' in yaml_info_hash:
                    sprite_args['smooth_edges'] = yaml_info_hash['smooth_edges']
                if 'preload_texture' in yaml_info_hash:
                    sprite_args['preload_texture'] = yaml_info_hash['preload_texture']
                if 'transparency_pixel' in yaml_info_hash:
                    sprite_args['transparency_pixel'] = yaml_info_hash['transparency_pixel']
                if 'origin' in yaml_info_hash:
                    sprite_args['origin'] = yaml_info_hash['origin']
                if 'collision_type' in yaml_info_hash:
                    sprite_args['collision_type'] = yaml_info_hash['collision_type']
                if 'bounding_box_type' in yaml_info_hash:
                    sprite_args['bounding_box_type'] = yaml_info_hash['bounding_box_type']
                if 'manual_bounding_box_rect' in yaml_info_hash:
                    sprite_args['manual_bounding_box_rect'] = yaml_info_hash['manual_bounding_box_rect']
                new_sprite_list.append(ObjectSprite(sprite_name,
                                                    **sprite_args))
                new_sprite_list[-1].check()
        return new_sprite_list

    def __init__(self, name=None, **kwargs):
        """
        Create a new sprite instance.

        :param name: Name for the new sprite instance
        :type name: str
        :param kwargs:
            Named arguments can be supplied to fill in sprite attributes:

            * filename: the name of the file containing the sprite graphic

                * if the file name (minus extension) ends with _strip## (## is
                  a number > 1), the file is assumed to contain multiple
                  adjacent subimages (E.G. for animations) - NYI

            * smooth_edges (bool): not implemented
            * preload_texture (bool): whether to load the sprite graphic from
              the file ahead of usage
            * transparency_pixel (bool): use transparency pixel defined in the
              sprite graphic
            * origin (array-like): where to offset the sprite graphic in
              relation to a supplied x, y in a 2-element list
            * collision_type (str): where and how to look for collisions:

                * precise: check every non-transparent edge pixel (slowest)
                * rectangle: check for edges of a rectangle surrounding the
                  image (fast)
                * disk: check for edges of a circle surrounding the image
                  (slower)
                * diamond: check for edges of a diamond surrounding the image
                  (average) - not implemented
                * polygon: check for edges of a polygon surrounding the image
                  (slow) - not implemented

            * bounding_box_type (str): a box containing the pixels that should
              be drawn

                * automatic: draw all non-tranparent pixels
                * full_image: draw the entire sprite graphic
                * manual: specify left, right, top, bottom dimensions in
                  manual_bounding_box_rect

            * manual_bounding_box_rect (dict): the box dimensions for the
              manual bounding_box_type, in a dict in {'left': left,
              'right': right, 'top': top, 'bottom': bottom} format
        """
        #: The name of the ObjectSprite, usually prefixed with "spr\_"
        self.name = self.DEFAULT_SPRITE_PREFIX
        if name:
            self.name = name
        #: The filename containing the sprite image
        self.filename = ""
        #: Flag whether to smooth the image edges
        self.smooth_edges = False
        #: Flag whether to preload the image in the setup() method
        self.preload_texture = True
        #: Flag whether to honor the transparency pixel inside the image file
        self.transparency_pixel = False
        #: Apply this coordinate offset when drawing the image
        self.origin = (0, 0)
        self._collision_type = "rectangle"
        #: Mask type for collision detection, see :py:attr:`COLLISION_TYPES`
        self.collision_mask = None
        #: How to produce the rect containing drawable pixels, see
        #: :py:attr:`BOUNDING_BOX_TYPES`
        self.bounding_box_type = "automatic"
        #: The dimensions of the boundary rect, if the type is "manual"
        self.manual_bounding_box_rect = pygame.Rect(0, 0, 0, 0)
        if "filename" in kwargs:
            self.filename = kwargs["filename"]
        if "smooth_edges" in kwargs:
            self.smooth_edges = kwargs["smooth_edges"]
        if "preload_texture" in kwargs:
            self.preload_texture = kwargs["preload_texture"]
        if "transparency_pixel" in kwargs:
            self.transparency_pixel = kwargs["transparency_pixel"]
        if "origin" in kwargs:
            self.origin = kwargs["origin"]
        if "collision_type" in kwargs:
            self.collision_type = kwargs["collision_type"]
        if "bounding_box_type" in kwargs:
            self.bounding_box_type = kwargs["bounding_box_type"]
        if ("manual_bounding_box_rect" in kwargs and
                isinstance(kwargs["manual_bounding_box_rect"], dict)):
            dim = kwargs["manual_bounding_box_rect"]
            topp = 0
            botmp = 0
            leftp = 0
            rightp = 0
            if "left" in dim:
                try:
                    leftp = int(dim["left"])
                except ValueError:
                    pass
            if "right" in dim:
                try:
                    rightp = int(dim["right"])
                except ValueError:
                    pass
            if "top" in dim:
                try:
                    topp = int(dim["top"])
                except ValueError:
                    pass
            if "bottom" in dim:
                try:
                    botmp = int(dim["bottom"])
                except ValueError:
                    pass
            width = rightp - leftp
            height = botmp - topp
            self.manual_bounding_box_rect.left = leftp
            self.manual_bounding_box_rect.top = topp
            self.manual_bounding_box_rect.width = width
            self.manual_bounding_box_rect.height = height

        self.image = None
        self.image_size = (0, 0)
        self.bounding_box_rect = None

    @property
    def collision_type(self):
        return self._collision_type

    @collision_type.setter
    def collision_type(self, value):
        if value not in self.COLLISION_TYPES:
            raise ObjectSpriteException("ObjectSprite error ({}):\
            Unknown collision type '{}'".format(str(self), value))
        self._collision_type = value

    def setup(self):
        """
        Perform any tasks that can be done before the main program loop,
        but only after pygame.init().
        """
        if self.preload_texture:
            self.load_graphic()

    def load_graphic(self):
        """
        Retrieve image data from the file named in the filename
        attribute.  Collect information about the graphic in the
        image_size, bounding_box_type, and bounding_box_rect
        attributes.
        """
        if len(self.filename) <= 0:
            raise ObjectSpriteException(
                "ObjectSprite error ({}): Attempt to load image from empty filename".format(str(self)))
        if self.check_filename():
            self.image = pygame.image.load(self.filename).convert_alpha()
            self.image_size = self.image.get_size()
            if self.bounding_box_type == "automatic":
                self.bounding_box_rect = self.image.get_bounding_rect()
            elif self.bounding_box_type == "full_image":
                self.bounding_box_rect = self.image.get_rect()
            else:
                self.bounding_box_rect = self.manual_bounding_box_rect

    def set_defaults(self):
        """
        Reset the sprite's parameters to defaults.

        This allows a GUI sprite-creation utility to support a "reset"
        operation.
        """
        self.filename = ""
        self.smooth_edges = False
        self.preload_texture = True
        self.transparency_pixel = False
        self.origin = (0, 0)
        self.collision_type = "rectangle"
        self.image = None
        self.image_size = (0, 0)
        self.bounding_box_type = "automatic"
        self.manual_bounding_box_rect = pygame.Rect(0, 0, 0, 0)

    def check_filename(self):
        """
        Validity test for filename attribute.

        :return: True if the validity test succeeded, or False
        :rtype: bool
        """
        if not isinstance(self.filename, str):
            raise ObjectSpriteException(
                "ObjectSprite error ({}): filename '{}' is not a string".format(str(self), self.filename))
        elif len(self.filename) == 0:
            raise ObjectSpriteException("ObjectSprite error ({}): filename is empty".format(str(self),
                                                                                            self.filename))
        if len(self.filename) > 0:
            if not os.path.exists(self.filename):
                raise ObjectSpriteException(
                    "ObjectSprite error ({}): filename '{}' not found".format(str(self), self.filename))
        return True

    def check_origin(self):
        """
        Validity test for origin attribute.

        :return: True if the validity test succeeded, or False
        :rtype: bool
        """
        if isinstance(self.origin, str):
            raise ObjectSpriteException("ObjectSprite error ({}): Origin is a string".format(str(self)))
        the_origin = list(self.origin)
        if len(the_origin) < 2:
            raise ObjectSpriteException("ObjectSprite error ({}): Origin does not have at least x, y".format(str(self)))
        return True

    def check_collision_type(self):
        """
        Validity test for collision_type attribute.

        :return: True if the validity test succeeded, or False
        :rtype: bool
        """
        if self.collision_type not in self.COLLISION_TYPES:
            raise ObjectSpriteException(
                "ObjectSprite error ({}): Collision type \"{}\" is unknown".format(str(self),
                                                                                   self.collision_type))
        return True

    def check_bounding_box(self):
        """
        Validity test for bounding_box_type attribute.

        :return: True if the validity test succeeded, or False
        :rtype: bool
        """
        if self.bounding_box_type not in self.BOUNDING_BOX_TYPES:
            raise ObjectSpriteException(
                "ObjectSprite error ({}): Bounding box type \"{}\" is unknown".format(str(self),
                                                                                      self.bounding_box_type))
        if self.bounding_box_type == "manual":
            self.check_manual_bounding_box_rect()
        return True

    def check_manual_bounding_box_rect(self):
        """
        Validity test for manual_bounding_box_rect attribute.

        :return: True if the validity test succeeded, or False
        :rtype: bool
        """
        bound_rect = self.manual_bounding_box_rect
        if not isinstance(bound_rect, pygame.Rect):
            raise(ObjectSpriteException("ObjectSprite error ({}):\
                  Bounding box dimensions {} is not a Rect".format(str(self),
                  self.manual_bounding_box_rect)))
        dim = (bound_rect.left, bound_rect.right, bound_rect.top, bound_rect.bottom)
        if (bound_rect.left > bound_rect.right) or (bound_rect.top > bound_rect.bottom):
            raise ObjectSpriteException(
                "ObjectSprite error ({}): Bounding box dimensions {} are not sane".format(str(self), dim))
        if (bound_rect.left < 0) or (bound_rect.right < 0) or (bound_rect.top < 0) or (bound_rect.bottom < 0):
            raise ObjectSpriteException(
                "ObjectSprite error ({}): Bounding box dimensions {} are not sane".format(str(self), dim))
        return True

    def check(self):
        """
        Run all validity tests.  Used by the load_from_yaml() method to
        ensure the YAML defines valid sprite attributes.

        :return: True if the sprite attributes passed validity tests, or False
        :rtype: bool
        """
        self.check_filename()
        self.check_origin()
        self.check_collision_type()
        self.check_bounding_box()
        return True

    def to_yaml(self):
        """
        Produce the YAML string representing the sprite instance.

        :return: YAML-formatted sprite data
        :rtype: str
        """
        ystr = "- {}:\n".format(self.name)
        ystr += "    filename: {}\n".format(self.filename)
        ystr += "    smooth_edges: {}\n".format(self.smooth_edges)
        ystr += "    preload_texture: {}\n".format(self.preload_texture)
        ystr += "    transparency_pixel: {}\n".format(self.transparency_pixel)
        ystr += "    origin: {}\n".format(str(list(self.origin)))
        ystr += "    collision_type: {}\n".format(self.collision_type)
        ystr += "    bounding_box_type: {}\n".format(self.bounding_box_type)
        bounding_dict = {"left": self.manual_bounding_box_rect.left,
                         "right": self.manual_bounding_box_rect.right,
                         "top": self.manual_bounding_box_rect.top,
                         "bottom": self.manual_bounding_box_rect.bottom
                         }
        ystr += "    manual_bounding_box_rect: {}".format(str(bounding_dict))
        return ystr

    def __eq__(self, other):
        # Equality test, for unit test purposes.
        return (isinstance(other, ObjectSprite) and
                (self.name == other.name) and
                (self.filename == other.filename) and
                (self.smooth_edges == other.smooth_edges) and
                (self.preload_texture == other.preload_texture) and
                (self.transparency_pixel == other.transparency_pixel) and
                (list(self.origin) == list(other.origin)) and
                (self.collision_type == other.collision_type) and
                (self.bounding_box_type == other.bounding_box_type) and
                (self.manual_bounding_box_rect == other.manual_bounding_box_rect))

    def __repr__(self):
        return ("<{} {} file={}>".format(type(self).__name__, self.name,
                                         self.filename))
