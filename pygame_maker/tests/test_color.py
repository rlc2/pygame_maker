#!/usr/bin/python -W all

# unit test for Color

import unittest
from pygame_maker.support.color import *


class TestColor(unittest.TestCase):

    def test_005color_names(self):
        red = Color("red")
        self.assertEqual((255, 0, 0), red.rgb)
        green = Color("green")
        self.assertEqual((0, 255, 0), green.rgb)
        blue = Color("blue")
        self.assertEqual((0, 0, 255), blue.rgb)

    def test_010color_hex_values(self):
        red = Color("#ff0000")
        self.assertEqual((255, 0, 0), red.rgb)
        green = Color("#00FF00")
        self.assertEqual((0, 255, 0), green.rgb)
        blue = Color("#0000ff")
        self.assertEqual((0, 0, 255), blue.rgb)

    def test_015additional_color_names(self):
        silver = Color("silver")
        self.assertEqual((0xc0, 0xc0, 0xc0), silver.rgb)

    def test_020list_initializer(self):
        green = Color((0, 255, 0))
        self.assertEqual((0, 255, 0), green.rgb)

    def test_025alpha(self):
        alpha1 = Color("#f0f0f0f0")
        self.assertEqual((240, 240, 240, 240), alpha1.rgba)
        alpha2 = Color((100, 100, 100, 200))
        self.assertEqual((100, 100, 100, 200), alpha2.rgba)

    def test_030component_properties(self):
        gray = Color("gray")
        self.assertEqual(gray.red, 190)
        self.assertEqual(gray.green, 190)
        self.assertEqual(gray.blue, 190)
        self.assertEqual(gray.alpha, 255)
        gray.red = 100
        gray.blue = 110
        gray.green = 120
        gray.alpha = 140
        self.assertEqual(gray.red, 100)
        self.assertEqual(gray.green, 120)
        self.assertEqual(gray.blue, 110)
        self.assertEqual(gray.alpha, 140)


unittest.main()
