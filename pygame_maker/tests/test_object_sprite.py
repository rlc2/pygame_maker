#!/usr/bin/env python

from pygame_maker.actors.object_sprite import *
import unittest
import tempfile
import pygame
import sys
import os


class DummyGameEngine:
    def __init__(self):
        pass
    def warn(self, message):
        print(message)


class TestSprite(unittest.TestCase):

    def setUp(self):
        self.game_engine = DummyGameEngine()
        self.base_good_sprite_info = {
            "filename": "unittest_files/Ball.png", "smooth_edges": True, "preload_texture": False,
            "transparency_pixel": True, "origin": (5,5), "collision_type": "disk",
            "bounding_box_type": "manual",
            "manual_bounding_box_rect": {"left": 1, "top": 1, "right":11, "bottom":11}
        }
        self.good_sprite = ObjectSprite("spr_good", **self.base_good_sprite_info)
        self.sprite_yaml = """
- spr_yaml:
    filename: unittest_files/Ball.png
    smooth_edges: true
    preload_texture: false
    transparency_pixel: true
    origin: [10,10]
    collision_type: disk
    bounding_box_type: manual
    manual_bounding_box_rect: {left: 5, right: 10, top: 5, bottom: 10}
"""
        self.yaml_sprite = ObjectSprite("spr_yaml",
            filename="unittest_files/Ball.png",
            smooth_edges=True,
            preload_texture=False,
            transparency_pixel=True,
            origin=(10,10),
            collision_type="disk",
            bounding_box_type="manual",
            manual_bounding_box_rect={"left":5, "right":10, "top":5, "bottom":10}
        )

    def test_005predefined_sprite(self):
        new_sprite = ObjectSprite("spr_good", **self.base_good_sprite_info)
        new_sprite.check()
        self.assertEqual(self.good_sprite, new_sprite)
        new_sprite.load_graphic()
        self.assertEqual(new_sprite.image, new_sprite.subimages[0])

    def test_010sprite_strip(self):
        sprite_strip = ObjectSprite("spr_strip", filename="unittest_files/sinistar_ship_strip07.png")
        sprite_strip.load_graphic()
        self.assertEqual(sprite_strip.subimage_count, 7)
        expected_strip_width = (sprite_strip.image_size[0] / 7)
        expected_strip_height = sprite_strip.image_size[1]
        expected_width_offset = 0
        for idx, subim_size in enumerate(sprite_strip.subimage_sizes):
            self.assertEqual(subim_size[0], expected_strip_width)
            self.assertEqual(subim_size[1], expected_strip_height)
            self.assertEqual(sprite_strip.subimages[idx].get_offset(), (expected_width_offset, 0))
            expected_width_offset += expected_strip_width

    def test_015bad_filename(self):
        bad_filename_hash = dict(self.base_good_sprite_info)
        bad_filename_hash["filename"] = "bad_filename"
        bad_sprite = ObjectSprite("spr_bad1", **bad_filename_hash)
        self.assertRaises(ObjectSpriteException, bad_sprite.check_filename)

    def test_020broken_sprites(self):
        with self.assertRaises(ValueError):
            bad_origin = ObjectSprite("spr_bad2", origin="foo")
        with self.assertRaises(ValueError):
            bad_colltype = ObjectSprite("spr_bad3", collision_type="bar")
        with self.assertRaises(ValueError):
            bad_bbtype = ObjectSprite("spr_bad4", bounding_box_type="baz")
        bad_bbdim = ObjectSprite("spr_bad5")
        bad_bbdim.manual_bounding_box_rect = "whack"
        self.assertRaises(ObjectSpriteException, bad_bbdim.check_manual_bounding_box_rect)
        bad_bbdim2 = ObjectSprite("spr_bad6", manual_bounding_box_rect = {"left":10, "right":5, "top":0, "bottom":10})
        self.assertRaises(ObjectSpriteException, bad_bbdim2.check_manual_bounding_box_rect)
        bad_bbdim3 = ObjectSprite("spr_bad7", manual_bounding_box_rect = {"left":0, "right":5, "top":10, "bottom":0})
        self.assertRaises(ObjectSpriteException, bad_bbdim3.check_manual_bounding_box_rect)
        bad_bbdim4 = ObjectSprite("spr_bad8", manual_bounding_box_rect = {"top":10})
        self.assertRaises(ObjectSpriteException, bad_bbdim4.check_manual_bounding_box_rect)
        bad_bbdim5 = ObjectSprite("spr_bad9", manual_bounding_box_rect = {"left":5})
        self.assertRaises(ObjectSpriteException, bad_bbdim5.check_manual_bounding_box_rect)

    def test_025load_sprite(self):
        tmpf_info = tempfile.mkstemp(dir="/tmp")
        tmp_file = os.fdopen(tmpf_info[0], "w")
        tmp_file.write(self.sprite_yaml)
        tmp_file.close()
        new_sprite = None
        with open(tmpf_info[1], "r") as yaml_f:
            new_sprite = ObjectSprite.load_from_yaml(yaml_f, self.game_engine)[0]
        os.unlink(tmpf_info[1])
        self.assertEqual(self.yaml_sprite, new_sprite)

    def test_026load_bad_yaml(self):
        bad_yaml = """
            - foo:
                filename: foo
        """
        tmpf_info = tempfile.mkstemp(dir="/tmp")
        tmp_file = os.fdopen(tmpf_info[0], "w")
        tmp_file.write(bad_yaml)
        tmp_file.close()
        with open(tmpf_info[1], "r") as yaml_f:
            no_sprite = ObjectSprite.load_from_yaml(yaml_f, self.game_engine)
            self.assertEqual(len(no_sprite), 0)
        os.unlink(tmpf_info[1])

    def test_030to_and_from_yaml(self):
        good_sprite_yaml = self.good_sprite.to_yaml()
        tmpf_info = tempfile.mkstemp(dir="/tmp")
        tmp_file = os.fdopen(tmpf_info[0], "w")
        tmp_file.write(good_sprite_yaml)
        tmp_file.close()
        new_sprite = None
        with open(tmpf_info[1], "r") as yaml_f:
            new_sprite = ObjectSprite.load_from_yaml(yaml_f, self.game_engine)[0]
        os.unlink(tmpf_info[1])
        self.assertEqual(self.good_sprite, new_sprite)

# run from the tests directory to find the unittest_files subdirectory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

pygame.init()
display = pygame.display.set_mode((640, 480))
unittest.main()
pygame.quit()

