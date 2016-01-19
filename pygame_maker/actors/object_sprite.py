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
    COLLISION_TYPES = [
        "precise",
        "rectangle",
        "disk",
        "diamond",
        "polygon"
    ]
    BOUNDING_BOX_TYPES = [
        "automatic",
        "full_image",
        "manual"
    ]

    DEFAULT_SPRITE_PREFIX="spr_"

    @staticmethod
    def load_from_yaml(sprite_yaml_stream, unused=None):
        """Create a new sprite from a YAML-formatted file
            sprite_yaml_stream: file or stream object
            Check each key against known ObjectSprite parameters, and use only
             those parameters to initialize a new sprite.
            Returns:
                o Empty list, if the YAML-defined sprite(s) is (are) invalid
                o a list of new sprites, for those with YAML fields that pass
                  basic checks

            Expected YAML object format:
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
        """
        yaml_info = None
        sprite_name = ObjectSprite.DEFAULT_SPRITE_PREFIX
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
        """Create a new sprite
            parameters:
                o name: a name for the sprite (default is spr_)
                o filename: the name of the file containing the sprite graphic
                    * if the file name (minus extension) ends with _strip## (## is a number > 1), the file is
                      assumed to contain multiple adjacent subimages (e.g. for animations)
                o smooth_edges: not implemented
                o preload_texture: whether to load the sprite graphic from the file ahead of usage
                o transparency_pixel: use transparency pixel defined in the sprite graphic
                o origin: where to offset the sprite graphic in relation to a supplied x,y
                o collision_type: where and how to look for collisions:
                    * precise: check every non-transparent edge pixel (slowest)
                    * rectangle: check for edges of a rectangle surrounding the image (fast)
                    * disk: check for edges of a circle surrounding the image (slower)
                    * diamond: check for edges of a diamond surrounding the image (average)
                    * polygon: check for edges of a polygon surrounding the image (slow)
                o bounding_box_type: a box containing the pixels that should be drawn
                    * automatic: draw all non-tranparent pixels
                    * full_image: draw the entire sprite graphic
                    * manual: specify left, right, top, bottom dimensions in manual_bounding_box_rect
                o manual_bounding_box_rect: the box dimensions for the manual bounding_box_type
        """
        self.name = self.DEFAULT_SPRITE_PREFIX
        if name:
            self.name = name
        self.filename = ""
        self.smooth_edges = False
        self.preload_texture = True
        self.transparency_pixel = False
        self.origin = (0,0)
        self._collision_type = "rectangle"
        self.collision_mask = None
        self.bounding_box_type = "automatic"
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
        if "manual_bounding_box_rect" in kwargs and isinstance(kwargs["manual_bounding_box_rect"], dict):
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
        self.image_size = (0,0)
        self.bounding_box_rect = None

    @property
    def collision_type(self):
        return self._collision_type

    @collision_type.setter
    def collision_type(self, value):
        if not value in (self.COLLISION_TYPES):
            raise ObjectSpriteException("ObjectSprite error ({}): Unknown collision type '{}'".format(self, value))
        self._collision_type = value

    def setup(self):
        """Perform any tasks that can be done before the main program loop, but only after pygame init"""
        if self.preload_texture:
            self.load_graphic()

    def load_graphic(self):
        if not len(self.filename) > 0:
            raise ObjectSpriteException("ObjectSprite error ({}): Attempt to load image from empty filename".format(self))
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
        """Reset the sprite's parameters to defaults"""
        self.filename = ""
        self.smooth_edges = False
        self.preload_texture = True
        self.transparency_pixel = False
        self.origin = (0,0)
        self.collision_type = "rectangle"
        self.image = None
        self.image_size = (0,0)
        self.bounding_box_type = "automatic"
        self.manual_bounding_box_rect = pygame.Rect(0, 0, 0, 0)

    def check_filename(self):
        """Error-check filename"""
        if not isinstance(self.filename, str):
            raise ObjectSpriteException("ObjectSprite error ({}): filename '{}' is not a string".format(self,self.filename))
        elif len(self.filename) == 0:
            raise ObjectSpriteException("ObjectSprite error ({}): filename is empty".format(self,self.filename))
        if len(self.filename) > 0:
            if not os.path.exists(self.filename):
                raise ObjectSpriteException("ObjectSprite error ({}): filename '{}' not found".format(self,self.filename))
        return True

    def check_origin(self):
        """Error-check origin"""
        if isinstance(self.origin, str):
            raise ObjectSpriteException("ObjectSprite error ({}): Origin is a string".format(self))
        the_origin = list(self.origin)
        if len(the_origin) < 2:
            raise ObjectSpriteException("ObjectSprite error ({}): Origin does not have at least x, y".format(self))
        return True

    def check_collision_type(self):
        """Error-check collision_type"""
        if not self.collision_type in self.COLLISION_TYPES:
            raise ObjectSpriteException("ObjectSprite error ({}): Collision type \"{}\" is unknown".format(self,self.collision_type))
        return True

    def check_bounding_box(self):
        """Error-check bounding_box_type"""
        if not self.bounding_box_type in self.BOUNDING_BOX_TYPES:
            raise ObjectSpriteException("ObjectSprite error ({}): Bounding box type \"{}\" is unknown".format(self,self.bounding_box_type))
        if self.bounding_box_type == "manual":
            self.check_manual_bounding_box_rect()
        return True

    def check_manual_bounding_box_rect(self):
        """Error-check manual_bounding_box_rect"""
        bound_rect = self.manual_bounding_box_rect
        if not isinstance(bound_rect, pygame.Rect):
            raise ObjectSpriteException("ObjectSprite error ({}): Bounding box dimensions {} is not a Rect".format(self,self.manual_bounding_box_rect))
        dim = (bound_rect.left, bound_rect.right, bound_rect.top, bound_rect.bottom)
        if (bound_rect.left > bound_rect.right) or (bound_rect.top > bound_rect.bottom):
            raise ObjectSpriteException("ObjectSprite error ({}): Bounding box dimensions {} are not sane".format(self,dim))
        if (bound_rect.left < 0) or (bound_rect.right < 0) or (bound_rect.top < 0) or (bound_rect.bottom < 0):
            raise ObjectSpriteException("ObjectSprite error ({}): Bounding box dimensions {} are not sane".format(self,dim))
        return True

    def check(self):
        """Run all validity tests"""
        self.check_filename()
        self.check_origin()
        self.check_collision_type()
        self.check_bounding_box()
        return True

    def to_yaml(self):
        ystr = "- {}:\n".format(self.name)
        ystr += "    filename: {}\n".format(self.filename)
        ystr += "    smooth_edges: {}\n".format(self.smooth_edges)
        ystr += "    preload_texture: {}\n".format(self.preload_texture)
        ystr += "    transparency_pixel: {}\n".format(self.transparency_pixel)
        ystr += "    origin: {}\n".format(list(self.origin))
        ystr += "    collision_type: {}\n".format(self.collision_type)
        ystr += "    bounding_box_type: {}\n".format(self.bounding_box_type)
        bounding_dict = {"left": self.manual_bounding_box_rect.left,
            "right": self.manual_bounding_box_rect.right,
            "top": self.manual_bounding_box_rect.top,
            "bottom": self.manual_bounding_box_rect.bottom
        }
        ystr += "    manual_bounding_box_rect: {}".format(bounding_dict)
        return(ystr)

    def __eq__(self, other):
        return(isinstance(other, ObjectSprite) and
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
        return("<{} {} file={}>".format(type(self).__name__, self.name,
            self.filename))

