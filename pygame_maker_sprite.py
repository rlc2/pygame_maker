#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# implement pygame_maker sprite resource (not the same as a pygame Sprite;
#  this is closer to a pygame.image)

import pygame
import os.path
import yaml

class PyGameMakerSpriteException(Exception):
    pass

class PyGameMakerSprite(object):
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

    @classmethod
    def load_sprite(cls, sprite_yaml_file):
        """Create a new sprite from a YAML-formatted file
            sprite_yaml_file: name of the file
            Check each key against known PyGameMakerSprite parameters, and use only those parameters
            to initialize a new sprite.
            Returns:
                o None, if the YAML-defined sprite is invalid
                o a new sprite, if the YAML fields pass basic checks
        """
        yaml_info = None
        sprite_name = cls.DEFAULT_SPRITE_PREFIX
        sprite_args = {}
        new_sprite = None
        if (os.path.exists(sprite_yaml_file)):
            with open(sprite_yaml_file, "r") as yaml_f:
                yaml_info = yaml.load(yaml_f)
            if yaml_info:
                if 'name' in yaml_info:
                    sprite_name = yaml_info['name']
                if 'filename' in yaml_info:
                    sprite_args['filename'] = yaml_info['filename']
                if 'smooth_edges' in yaml_info:
                    sprite_args['smooth_edges'] = yaml_info['smooth_edges']
                if 'preload_texture' in yaml_info:
                    sprite_args['preload_texture'] = yaml_info['preload_texture']
                if 'transparency_pixel' in yaml_info:
                    sprite_args['transparency_pixel'] = yaml_info['transparency_pixel']
                if 'origin' in yaml_info:
                    sprite_args['origin'] = yaml_info['origin']
                if 'collision_type' in yaml_info:
                    sprite_args['collision_type'] = yaml_info['collision_type']
                if 'bounding_box_type' in yaml_info:
                    sprite_args['bounding_box_type'] = yaml_info['bounding_box_type']
                if 'manual_bounding_box_rect' in yaml_info:
                    sprite_args['manual_bounding_box_rect'] = yaml_info['manual_bounding_box_rect']
                new_sprite = PyGameMakerSprite(sprite_name, **sprite_args)
                new_sprite.check()
        return new_sprite

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
            raise PyGameMakerSpriteException("Unknown collision type '{}'".format(value))
        self._collision_type = value

    def setup(self):
        """Perform any tasks that can be done before the main program loop, but only after pygame init"""
        if self.preload_texture:
            self.load_graphic()

    def load_graphic(self):
        if not len(self.filename) > 0:
            raise PyGameMakerSpriteException("Sprite error ({}): Attempt to load image from empty filename".format(self))
        if self.check_filename():
            self.image = pygame.image.load(self.filename).convert_alpha()
            self.image_size = self.image.get_size()
            if self.bounding_box_type == "automatic":
                self.bounding_box_rect = self.image.get_bounding_rect()
            elif self.bounding_box_type == "full_image":
                self.bounding_box_rect = self.image.get_rect()
            else:
                self.bounding_box_rect = self.manual_bounding_box_rect

    def get_extents_from_position(self, pos):
        """Find furthest left, right, top, and bottom pixel locations for sprite from supplied (x, y) position
            pos: (x, y) tuple
            returns a dict {"left": int, "right": int, "top": int, "bottom": int}
        """
        left_extent = 0
        right_extent = 0
        top_extent = 0
        bottom_extent = 0

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
            raise PyGameMakerSpriteException("Sprite error ({}): filename '{}' is not a string".format(self,self.filename))
        elif len(self.filename) == 0:
            raise PyGameMakerSpriteException("Sprite error ({}): filename is empty".format(self,self.filename))
        if len(self.filename) > 0:
            if not os.path.exists(self.filename):
                raise PyGameMakerSpriteException("Sprite error ({}): filename '{}' not found".format(self,self.filename))
        return True

    def check_origin(self):
        """Error-check origin"""
        if isinstance(self.origin, str):
            raise PyGameMakerSpriteException("Sprite error ({}): Origin is a string".format(self))
        the_origin = list(self.origin)
        if len(the_origin) < 2:
            raise PyGameMakerSpriteException("Sprite error ({}): Origin does not have at least x, y".format(self))
        return True

    def check_collision_type(self):
        """Error-check collision_type"""
        if not self.collision_type in self.COLLISION_TYPES:
            raise PyGameMakerSpriteException("Sprite error ({}): Collision type \"{}\" is unknown".format(self,self.collision_type))
        return True

    def check_bounding_box(self):
        """Error-check bounding_box_type"""
        if not self.bounding_box_type in self.BOUNDING_BOX_TYPES:
            raise PyGameMakerSpriteException("Sprite error ({}): Bounding box type \"{}\" is unknown".format(self,self.bounding_box_type))
        if self.bounding_box_type == "manual":
            self.check_manual_bounding_box_rect()
        return True

    def check_manual_bounding_box_rect(self):
        """Error-check manual_bounding_box_rect"""
        bound_rect = self.manual_bounding_box_rect
        if not isinstance(bound_rect, pygame.Rect):
            raise PyGameMakerSpriteException("Sprite error ({}): Bounding box dimensions {} is not a Rect".format(self,self.manual_bounding_box_rect))
        dim = (bound_rect.left, bound_rect.right, bound_rect.top, bound_rect.bottom)
        if (bound_rect.left > bound_rect.right) or (bound_rect.top > bound_rect.bottom):
            raise PyGameMakerSpriteException("Sprite error ({}): Bounding box dimensions {} are not sane".format(self,dim))
        if (bound_rect.left < 0) or (bound_rect.right < 0) or (bound_rect.top < 0) or (bound_rect.bottom < 0):
            raise PyGameMakerSpriteException("Sprite error ({}): Bounding box dimensions {} are not sane".format(self,dim))
        return True

    def check(self):
        """Run all validity tests"""
        self.check_filename()
        self.check_origin()
        self.check_collision_type()
        self.check_bounding_box()
        return True

    def to_yaml(self):
        ystr = "name: {}\n".format(self.name)
        ystr += "filename: {}\n".format(self.filename)
        ystr += "smooth_edges: {}\n".format(self.smooth_edges)
        ystr += "preload_texture: {}\n".format(self.preload_texture)
        ystr += "transparency_pixel: {}\n".format(self.transparency_pixel)
        ystr += "origin: {}\n".format(list(self.origin))
        ystr += "collision_type: {}\n".format(self.collision_type)
        ystr += "bounding_box_type: {}\n".format(self.bounding_box_type)
        bounding_dict = {"left": self.manual_bounding_box_rect.left,
            "right": self.manual_bounding_box_rect.right,
            "top": self.manual_bounding_box_rect.top,
            "bottom": self.manual_bounding_box_rect.bottom
        }
        ystr += "manual_bounding_box_rect: {}".format(bounding_dict)
        return(ystr)

    def __eq__(self, other):
        return(isinstance(other, PyGameMakerSprite) and
            (self.name == other.name) and
            (self.filename == other.filename) and
            (self.smooth_edges == other.smooth_edges) and
            (self.preload_texture == other.preload_texture) and
            (self.transparency_pixel == other.transparency_pixel) and
            (list(self.origin) == list(other.origin)) and
            (self.collision_type == other.collision_type) and
            (self.bounding_box_type == other.bounding_box_type) and
            (self.manual_bounding_box_rect == other.manual_bounding_box_rect))

if __name__ == "__main__":
    import unittest
    import tempfile
    import os

    class TestPyGameMakerSprite(unittest.TestCase):

        def setUp(self):
            self.base_good_sprite_info = {
                "filename": "unittest_files/Ball.png", "smooth_edges": True, "preload_texture": False,
                "transparency_pixel": True, "origin": (5,5), "collision_type": "disk",
                "bounding_box_type": "manual",
                "manual_bounding_box_rect": {"left": 1, "top": 1, "right":11, "bottom":11}
            }
            self.good_sprite = PyGameMakerSprite("spr_good", **self.base_good_sprite_info)
            self.sprite_yaml = """
                name: spr_yaml
                filename: unittest_files/Ball.png
                smooth_edges: true
                preload_texture: false
                transparency_pixel: true
                origin: [10,10]
                collision_type: disk
                bounding_box_type: manual
                manual_bounding_box_rect: {left: 5, right: 10, top: 5, bottom: 10}
            """
            self.yaml_sprite = PyGameMakerSprite("spr_yaml",
                filename="unittest_files/Ball.png",
                smooth_edges=True,
                preload_texture=False,
                transparency_pixel=True,
                origin=(10,10),
                collision_type="disk",
                bounding_box_type="manual",
                manual_bounding_box_rect={"left":5, "right":10, "top":5, "bottom":10}
            )

        def test_005empty_sprite(self):
            new_sprite = PyGameMakerSprite()
            self.assertTrue(new_sprite.name == PyGameMakerSprite.DEFAULT_SPRITE_PREFIX)
            self.assertTrue(len(new_sprite.filename) == 0)
            self.assertFalse(new_sprite.smooth_edges)
            self.assertTrue(new_sprite.preload_texture)
            self.assertFalse(new_sprite.transparency_pixel)
            self.assertTrue(list(new_sprite.origin) == [0,0])
            self.assertTrue(new_sprite.collision_type == "rectangle")
            self.assertTrue(new_sprite.bounding_box_type == "automatic")
            self.assertTrue(new_sprite.manual_bounding_box_rect == pygame.Rect(0,0,0,0))

        def test_010predefined_sprite(self):
            new_sprite = PyGameMakerSprite("spr_good", **self.base_good_sprite_info)
            new_sprite.check()
            self.assertEqual(self.good_sprite, new_sprite)

        def test_015bad_filename(self):
            bad_filename_hash = dict(self.base_good_sprite_info)
            bad_filename_hash["filename"] = "bad_filename"
            bad_sprite = PyGameMakerSprite("spr_bad1", **bad_filename_hash)
            self.assertRaises(PyGameMakerSpriteException, bad_sprite.check_filename)

        def test_020broken_sprites(self):
            bad_origin = PyGameMakerSprite("spr_bad2", origin="foo")
            self.assertRaises(PyGameMakerSpriteException, bad_origin.check_origin)
            with self.assertRaises(PyGameMakerSpriteException):
                bad_colltype = PyGameMakerSprite("spr_bad3", collision_type="bar")
            bad_bbtype = PyGameMakerSprite("spr_bad4", bounding_box_type="baz")
            self.assertRaises(PyGameMakerSpriteException, bad_bbtype.check_bounding_box)
            bad_bbdim = PyGameMakerSprite("spr_bad5")
            bad_bbdim.manual_bounding_box_rect = "whack"
            self.assertRaises(PyGameMakerSpriteException, bad_bbdim.check_manual_bounding_box_rect)
            bad_bbdim2 = PyGameMakerSprite("spr_bad6", manual_bounding_box_rect = {"left":10, "right":5, "top":0, "bottom":10})
            self.assertRaises(PyGameMakerSpriteException, bad_bbdim2.check_manual_bounding_box_rect)
            bad_bbdim3 = PyGameMakerSprite("spr_bad7", manual_bounding_box_rect = {"left":0, "right":5, "top":10, "bottom":0})
            self.assertRaises(PyGameMakerSpriteException, bad_bbdim3.check_manual_bounding_box_rect)
            bad_bbdim4 = PyGameMakerSprite("spr_bad8", manual_bounding_box_rect = {"top":10})
            self.assertRaises(PyGameMakerSpriteException, bad_bbdim4.check_manual_bounding_box_rect)
            bad_bbdim5 = PyGameMakerSprite("spr_bad9", manual_bounding_box_rect = {"left":5})
            self.assertRaises(PyGameMakerSpriteException, bad_bbdim5.check_manual_bounding_box_rect)

        def test_025load_sprite(self):
            tmpf_info = tempfile.mkstemp(dir="/tmp")
            tmp_file = os.fdopen(tmpf_info[0], "w")
            tmp_file.write(self.sprite_yaml)
            tmp_file.close()
            new_sprite = PyGameMakerSprite.load_sprite(tmpf_info[1])
            os.unlink(tmpf_info[1])
            self.assertEqual(self.yaml_sprite, new_sprite)

        def test_026load_bad_yaml(self):
            bad_yaml = """
                name: foo
                filename: foo
            """
            tmpf_info = tempfile.mkstemp(dir="/tmp")
            tmp_file = os.fdopen(tmpf_info[0], "w")
            tmp_file.write(bad_yaml)
            tmp_file.close()
            self.assertRaises(PyGameMakerSpriteException, PyGameMakerSprite.load_sprite, tmpf_info[1])
            os.unlink(tmpf_info[1])

        def test_030to_and_from_yaml(self):
            good_sprite_yaml = self.good_sprite.to_yaml()
            tmpf_info = tempfile.mkstemp(dir="/tmp")
            tmp_file = os.fdopen(tmpf_info[0], "w")
            tmp_file.write(good_sprite_yaml)
            tmp_file.close()
            new_sprite = PyGameMakerSprite.load_sprite(tmpf_info[1])
            os.unlink(tmpf_info[1])
            self.assertEqual(self.good_sprite, new_sprite)

    unittest.main()

