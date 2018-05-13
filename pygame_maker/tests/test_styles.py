#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test the pygame_maker.actors.gui.styles module.
"""

# Unit tests for widget.py

import unittest
from pygame_maker.actors.gui.styles import WidgetStyle, WidgetStyleInvalid


class TestWidget(unittest.TestCase):
    "Unit tests for the gui styles module."""

    def test_005basic_style(self):
        """Test creation of a style with empty parameters."""
        WidgetStyle({})

    def test_010transform_values(self):
        """
        Test addition of extra parameter fields for parameters with default
        values for missing fields.
        """
        widget_bkpos1 = WidgetStyle({"background-position": ("left")})
        self.assertEqual(widget_bkpos1["background-position"], "left center")
        widget_bkpos2 = WidgetStyle({"background-position": ("0")})
        self.assertEqual(widget_bkpos2["background-position"], "0 50%")

    def test_015shorthand_border(self):
        """Test shorthand notation for border styles."""
        border_style1 = WidgetStyle({"border-style": ("dotted", "dashed", "solid", "double")})
        self.assertEqual(border_style1["border-top-style"], "dotted")
        self.assertEqual(border_style1["border-right-style"], "dashed")
        self.assertEqual(border_style1["border-bottom-style"], "solid")
        self.assertEqual(border_style1["border-left-style"], "double")
        border_style2 = WidgetStyle({"border-style": ("dotted", "dashed", "solid")})
        self.assertEqual(border_style2["border-top-style"], "dotted")
        self.assertEqual(border_style2["border-right-style"], "dashed")
        self.assertEqual(border_style2["border-bottom-style"], "solid")
        self.assertEqual(border_style2["border-left-style"], "dashed")
        border_style3 = WidgetStyle({"border-style": ("dotted", "dashed")})
        self.assertEqual(border_style3["border-top-style"], "dotted")
        self.assertEqual(border_style3["border-right-style"], "dashed")
        self.assertEqual(border_style3["border-bottom-style"], "dotted")
        self.assertEqual(border_style3["border-left-style"], "dashed")
        border_style4 = WidgetStyle({"border-style": ("dotted",)})
        self.assertEqual(border_style4["border-top-style"], "dotted")
        self.assertEqual(border_style4["border-right-style"], "dotted")
        self.assertEqual(border_style4["border-bottom-style"], "dotted")
        self.assertEqual(border_style4["border-left-style"], "dotted")
        border_width1 = WidgetStyle({"border-width": ("4", "5%", "thin", "medium")})
        self.assertEqual(border_width1["border-top-width"], "4")
        self.assertEqual(border_width1["border-right-width"], "5%")
        self.assertEqual(border_width1["border-bottom-width"], "thin")
        self.assertEqual(border_width1["border-left-width"], "medium")
        border_width2 = WidgetStyle({"border-width": ("4", "5%", "thin")})
        self.assertEqual(border_width2["border-top-width"], "4")
        self.assertEqual(border_width2["border-right-width"], "5%")
        self.assertEqual(border_width2["border-bottom-width"], "thin")
        self.assertEqual(border_width2["border-left-width"], "5%")
        border_width3 = WidgetStyle({"border-width": ("4", "5%")})
        self.assertEqual(border_width3["border-top-width"], "4")
        self.assertEqual(border_width3["border-right-width"], "5%")
        self.assertEqual(border_width3["border-bottom-width"], "4")
        self.assertEqual(border_width3["border-left-width"], "5%")
        border_width4 = WidgetStyle({"border-width": ("4",)})
        self.assertEqual(border_width4["border-top-width"], "4")
        self.assertEqual(border_width4["border-right-width"], "4")
        self.assertEqual(border_width4["border-bottom-width"], "4")
        self.assertEqual(border_width4["border-left-width"], "4")
        border_color1 = WidgetStyle({"border-color": ("red", "yellow", "orange", "brown")})
        self.assertEqual(border_color1["border-top-color"], "red")
        self.assertEqual(border_color1["border-right-color"], "yellow")
        self.assertEqual(border_color1["border-bottom-color"], "orange")
        self.assertEqual(border_color1["border-left-color"], "brown")
        border_color2 = WidgetStyle({"border-color": ("red", "yellow", "orange")})
        self.assertEqual(border_color2["border-top-color"], "red")
        self.assertEqual(border_color2["border-right-color"], "yellow")
        self.assertEqual(border_color2["border-bottom-color"], "orange")
        self.assertEqual(border_color2["border-left-color"], "yellow")
        border_color3 = WidgetStyle({"border-color": ("red", "yellow")})
        self.assertEqual(border_color3["border-top-color"], "red")
        self.assertEqual(border_color3["border-right-color"], "yellow")
        self.assertEqual(border_color3["border-bottom-color"], "red")
        self.assertEqual(border_color3["border-left-color"], "yellow")
        border_color4 = WidgetStyle({"border-color": ("red",)})
        self.assertEqual(border_color4["border-top-color"], "red")
        self.assertEqual(border_color4["border-right-color"], "red")
        self.assertEqual(border_color4["border-bottom-color"], "red")
        self.assertEqual(border_color4["border-left-color"], "red")
        border_sh1 = WidgetStyle({"border": ("1px", "dashed", "#f0f0f0")})
        self.assertEqual(border_sh1["border-top-width"], "1px")
        self.assertEqual(border_sh1["border-right-width"], "1px")
        self.assertEqual(border_sh1["border-bottom-width"], "1px")
        self.assertEqual(border_sh1["border-left-width"], "1px")
        self.assertEqual(border_sh1["border-top-style"], "dashed")
        self.assertEqual(border_sh1["border-right-style"], "dashed")
        self.assertEqual(border_sh1["border-bottom-style"], "dashed")
        self.assertEqual(border_sh1["border-left-style"], "dashed")
        self.assertEqual(border_sh1["border-top-color"], "#f0f0f0")
        self.assertEqual(border_sh1["border-right-color"], "#f0f0f0")
        self.assertEqual(border_sh1["border-bottom-color"], "#f0f0f0")
        self.assertEqual(border_sh1["border-left-color"], "#f0f0f0")

    def test_020shorthand_background(self):
        """Test shorthand notation for background styles."""
        widget_bk1 = WidgetStyle({"background": ("red", "bkg_foo", "repeat-x", "fixed",
                                                 "left center")})
        self.assertEqual(widget_bk1.style["background-color"], "red")
        self.assertEqual(widget_bk1.style["background-resource"], "bkg_foo")
        self.assertEqual(widget_bk1.style["background-repeat"], "repeat-x")
        self.assertEqual(widget_bk1.style["background-attachment"], "fixed")
        self.assertEqual(widget_bk1.style["background-position"], "left center")
        widget_bk2 = WidgetStyle({"background": ("blue", "repeat-y", "inherit", "right top")})
        self.assertEqual(widget_bk2.style["background-color"], "blue")
        self.assertEqual(widget_bk2.style["background-resource"], "none")
        self.assertEqual(widget_bk2.style["background-repeat"], "repeat-y")
        self.assertEqual(widget_bk2.style["background-attachment"], "inherit")
        self.assertEqual(widget_bk2.style["background-position"], "right top")
        widget_bk2 = WidgetStyle({"background": ("top",)})
        self.assertEqual(widget_bk2.style["background-color"], "transparent")
        self.assertEqual(widget_bk2.style["background-resource"], "none")
        self.assertEqual(widget_bk2.style["background-repeat"], "repeat")
        self.assertEqual(widget_bk2.style["background-attachment"], "scroll")
        self.assertEqual(widget_bk2.style["background-position"], "center top")

    def test_025shorthand_margin(self):
        """Test shorthand notation for margin styles."""
        margin1 = WidgetStyle({"margin": ("4", "5%", "3", "0px")})
        self.assertEqual(margin1.style["margin-top"], "4")
        self.assertEqual(margin1.style["margin-right"], "5%")
        self.assertEqual(margin1.style["margin-bottom"], "3")
        self.assertEqual(margin1.style["margin-left"], "0px")
        margin2 = WidgetStyle({"margin": ("4", "5%", "0px")})
        self.assertEqual(margin2.style["margin-top"], "4")
        self.assertEqual(margin2.style["margin-right"], "5%")
        self.assertEqual(margin2.style["margin-bottom"], "0px")
        self.assertEqual(margin2.style["margin-left"], "5%")
        margin3 = WidgetStyle({"margin": ("4", "3")})
        self.assertEqual(margin3.style["margin-top"], "4")
        self.assertEqual(margin3.style["margin-right"], "3")
        self.assertEqual(margin3.style["margin-bottom"], "4")
        self.assertEqual(margin3.style["margin-left"], "3")
        margin4 = WidgetStyle({"margin": ("4",)})
        self.assertEqual(margin4.style["margin-top"], "4")
        self.assertEqual(margin4.style["margin-right"], "4")
        self.assertEqual(margin4.style["margin-bottom"], "4")
        self.assertEqual(margin4.style["margin-left"], "4")

    def test_030shorthand_padding(self):
        """Test shorthand notation for padding styles."""
        pad1 = WidgetStyle({"padding": ("4", "5%", "3", "0px")})
        self.assertEqual(pad1.style["padding-top"], "4")
        self.assertEqual(pad1.style["padding-right"], "5%")
        self.assertEqual(pad1.style["padding-bottom"], "3")
        self.assertEqual(pad1.style["padding-left"], "0px")
        pad2 = WidgetStyle({"padding": ("4", "5%", "0px")})
        self.assertEqual(pad2.style["padding-top"], "4")
        self.assertEqual(pad2.style["padding-right"], "5%")
        self.assertEqual(pad2.style["padding-bottom"], "0px")
        self.assertEqual(pad2.style["padding-left"], "5%")
        pad3 = WidgetStyle({"padding": ("4", "3")})
        self.assertEqual(pad3.style["padding-top"], "4")
        self.assertEqual(pad3.style["padding-right"], "3")
        self.assertEqual(pad3.style["padding-bottom"], "4")
        self.assertEqual(pad3.style["padding-left"], "3")
        pad4 = WidgetStyle({"padding": ("4",)})
        self.assertEqual(pad4.style["padding-top"], "4")
        self.assertEqual(pad4.style["padding-right"], "4")
        self.assertEqual(pad4.style["padding-bottom"], "4")
        self.assertEqual(pad4.style["padding-left"], "4")

    def test_035valid_colors(self):
        """Test valid color values for color parameters."""
        color_values = ("purple", "#aabbccfe", "#add", "#face", "#faced",
                        "#c0ffee", "#c0ffeed", "inherit", "initial")
        for color in color_values:
            style = WidgetStyle({"background-color": color})
            self.assertEqual(style.style["background-color"], color)
        border_color1 = WidgetStyle({"border-right-color": "transparent"})
        self.assertEqual(border_color1.style["border-right-color"], "transparent")

    def test_040valid_lengths(self):
        """Test valid length values for parameters that accept them."""
        test_plain_values = ("4", "3px", "10%")
        test_plain_styles = ("margin-top", "padding-top", "margin-right")
        test_plain_dict = dict(zip(test_plain_styles, test_plain_values))
        for style_test_key in test_plain_dict:
            style = WidgetStyle({style_test_key: test_plain_dict[style_test_key]})
            self.assertEqual(style.style[style_test_key], test_plain_dict[style_test_key])
        test_str_values = ("auto", "inherit", "initial")
        test_str_styles = ("width", "left", "right")
        test_str_dict = dict(zip(test_str_styles, test_str_values))
        for style_test_key in test_str_dict:
            style = WidgetStyle({style_test_key: test_str_dict[style_test_key]})
            self.assertEqual(style.style[style_test_key], test_str_dict[style_test_key])
        max_width = WidgetStyle({"max-width": "none"})
        self.assertEqual(max_width.style["max-width"], "none")

    def test_045valid_widths(self):
        """Test valid width values for parameters that accept them."""
        test_plain_values = ("4", "3px", "10%")
        test_plain_styles = ("border-top-width", "border-right-width", "border-left-width")
        test_plain_dict = dict(zip(test_plain_styles, test_plain_values))
        for style_test_key in test_plain_dict:
            style = WidgetStyle({style_test_key: test_plain_dict[style_test_key]})
            self.assertEqual(style.style[style_test_key], test_plain_dict[style_test_key])

        test_str_values = ("thin", "thick", "medium", "inherit", "initial")
        test_str_styles = ("border-top-width", "border-left-width", "border-right-width",
                           "border-bottom-width", "border-top-width")
        test_str_dict = dict(zip(test_str_styles, test_str_values))
        for style_test_key in test_str_dict:
            style = WidgetStyle({style_test_key: test_str_dict[style_test_key]})
            self.assertEqual(style.style[style_test_key], test_str_dict[style_test_key])

    def test_050valid_border_styles(self):
        """Test valid border style settings."""
        test_values = ("none", "dotted", "dashed", "solid", "double", "groove", "ridge", "inset",
                       "outset", "hidden", "inherit", "initial")
        for val in test_values:
            style = WidgetStyle({"border-top-style": val})
            self.assertEqual(style.style["border-top-style"], val)

    def test_055valid_alignment(self):
        """
        Test valid horizontal and vertical alignment values for parameters that
        accept them.
        """
        test_values = ("left", "center", "right")
        for val in test_values:
            style = WidgetStyle({"text-align": val})
            self.assertEqual(style.style["text-align"], val)
        test_values = ("top", "middle", "bottom")
        for val in test_values:
            style = WidgetStyle({"vertical-align": val})
            self.assertEqual(style.style["vertical-align"], val)

    def test_060valid_background_image(self):
        """Test valid background image values."""
        test_values = ("bkg_test_0", "none", "inherit", "initial")
        for val in test_values:
            style = WidgetStyle({"background-resource": val})
            self.assertEqual(style.style["background-resource"], val)

    def test_065valid_background_attach(self):
        """Test valid background attachment values."""
        test_values = ("scroll", "fixed", "local", "inherit", "initial")
        for val in test_values:
            style = WidgetStyle({"background-attachment": val})
            self.assertEqual(style.style["background-attachment"], val)

    def test_070valid_background_repeat(self):
        """Test valid background repeat values."""
        test_values = ("repeat", "repeat-x", "repeat-y", "no-repeat", "inherit", "initial")
        for val in test_values:
            style = WidgetStyle({"background-repeat": val})
            self.assertEqual(style.style["background-repeat"], val)

    def test_075valid_background_pos(self):
        """Test valid background positioning values."""
        test_values = ("left top", "left center", "left bottom", "right top", "right center",
                       "right bottom", "center top", "center center", "center bottom", "4 2",
                       "0% 15%", "10% 5", "2 20%", "inherit", "initial")
        for val in test_values:
            style = WidgetStyle({"background-position": val})
            self.assertEqual(style.style["background-position"], val)
        test_single_values = ("left", "center", "right", "top", "bottom", "4", "10%")
        test_single_answers = ("left center", "center center", "right center", "center top",
                               "center bottom", "4 50%", "10% 50%")
        for idx, val in enumerate(test_single_values):
            style = WidgetStyle({"background-position": val})
            self.assertEqual(style.style["background-position"], test_single_answers[idx])

    def test_080valid_display_options(self):
        """Test valid display values."""
        test_values = ("none", "inline", "block", "inherit", "initial")
        for val in test_values:
            style = WidgetStyle({"display": val})
            self.assertEqual(style.style["display"], val)

    def test_085valid_visibility(self):
        """Test valid visibility values."""
        test_values = ("visible", "hidden", "inherit", "initial")
        for val in test_values:
            style = WidgetStyle({"visibility": val})
            self.assertEqual(style.style["visibility"], val)

    def test_090valid_position(self):
        """Test valid position values."""
        test_values = ("static", "relative", "fixed", "absolute", "inherit", "initial")
        for val in test_values:
            style = WidgetStyle({"position": val})
            self.assertEqual(style.style["position"], val)

    def test_095valid_z_index(self):
        """Test valid z-index values."""
        test_values = ("-5", "40", "+19")
        for val in test_values:
            style = WidgetStyle({"z-index": val})
            self.assertEqual(style.style["z-index"], val)

    def test_100invalid_styles(self):
        """Test that invalid style values provoke the expected exceptions."""
        with self.assertRaises(WidgetStyleInvalid):
            WidgetStyle({"background-color": "#foo"})
        with self.assertRaises(WidgetStyleInvalid):
            WidgetStyle({"background-color": "notacolor"})
        with self.assertRaises(WidgetStyleInvalid):
            WidgetStyle({"padding-top": "5p"})
        with self.assertRaises(WidgetStyleInvalid):
            WidgetStyle({"z-index": "+-5"})
        with self.assertRaises(WidgetStyleInvalid):
            WidgetStyle({"background-resource": "bkginvalid"})


unittest.main()
