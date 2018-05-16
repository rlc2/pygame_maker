#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test the pygame_maker.support.color module.
"""

import unittest
from pygame_maker.support.color import Color


class TestColor(unittest.TestCase):
    """Unit tests for the color module."""

    def test_005color_names(self):
        """
        Verify normal color names are accepted and result in the correct rgb
        values.
        """
        red = Color("red")
        self.assertEqual((255, 0, 0), red.rgb)
        green = Color("green")
        self.assertEqual((0, 255, 0), green.rgb)
        blue = Color("blue")
        self.assertEqual((0, 0, 255), blue.rgb)

    def test_010color_hex_values(self):
        """
        Verify hexadecimal color strings are accepted and result in the correct
        rgb values.
        """
        red = Color("#ff0000")
        self.assertEqual((255, 0, 0), red.rgb)
        green = Color("#00FF00")
        self.assertEqual((0, 255, 0), green.rgb)
        blue = Color("#0000ff")
        self.assertEqual((0, 0, 255), blue.rgb)

    def test_015additional_color_names(self):
        """
        Verify that additional color names (not known to pygame.color) are
        accepted and result in the correct rgb values.
        """
        silver = Color("silver")
        self.assertEqual((0xc0, 0xc0, 0xc0), silver.rgb)

    def test_020list_initializer(self):
        """Verify that a 3-tuple is accepted and interpreted properly."""
        green = Color((0, 255, 0))
        self.assertEqual((0, 255, 0), green.rgb)

    def test_025alpha(self):
        """Verify color strings and 4-tuples containing alpha values."""
        alpha1 = Color("#f0f0f0f0")
        self.assertEqual((240, 240, 240, 240), alpha1.rgba)
        alpha2 = Color((100, 100, 100, 200))
        self.assertEqual((100, 100, 100, 200), alpha2.rgba)

    def test_030component_properties(self):
        """
        Verify that color components 'red', 'blue', 'green' and 'alpha' contain
        expected values, and can be set to new values.
        """
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
