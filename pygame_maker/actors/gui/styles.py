#!/usr/bin/python -W all

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker widgets

import re
import pygame
from pygame_maker.support import color


def split_regex_and_str_list(regex_and_str_list):
    regex_list = []
    str_list = []
    for entry in regex_and_str_list:
        if hasattr(entry, 'search'):
            regex_list.append(entry)
        if isinstance(entry, str):
            str_list.append(entry)
    return (regex_list, str_list)


class ShorthandStyleError(Exception):
    pass


class ShorthandStyle(object):

    def __init__(self, name, sub_property_dict, value_check_method=None):
        self.name = name
        self.sub_property_dict = sub_property_dict
        self.value_check_method = value_check_method

    def get_sub_properties(self, value_list):
        sub_prop_map = {}
        if len(value_list) in self.sub_property_dict.keys():
            for idx, v in enumerate(value_list):
                for sub_prop in self.sub_property_dict[len(value_list)][idx]:
                    sub_prop_map[sub_prop] = v
        elif self.value_check_method is not None:
            # Use the supplied method to determine which sub-properties are
            # present.  The property values must still be in the right order.
            value_idx = 0
            # longest sub-property list is expected to contain all properties
            full_sub_property_list = [s[0] for s in self.sub_property_dict[max(self.sub_property_dict.keys())]]
            for id_idx, sub_prop_name in enumerate(full_sub_property_list):
                # print("Check {} against {}".format(value_list[value_idx], val_id))
                if self.value_check_method(sub_prop_name, value_list[value_idx]):
                    # print("ID'd {} from {}".format(sub_prop_name, value_list[value_idx]))
                    sub_prop_map[sub_prop_name] = value_list[value_idx]
                    value_idx += 1
            if value_idx < len(value_list):
                raise ShorthandStyleError("Unable to ID all values in shorthand property {}".format(self.name))
        return sub_prop_map


class WidgetStyleInvalid(Exception):
    pass


class WidgetStyle(object):

    COMMON_PROPERTIES = ("initial", "inherit")
    BORDER_STYLES = (("none", "dotted", "dashed", "solid", "double", "groove", "ridge", "inset", "outset", "hidden") +
        COMMON_PROPERTIES)
    BORDER_WIDTHS = ("medium", "thin", "thick") + COMMON_PROPERTIES
    BORDER_COLORS = ("transparent",) + COMMON_PROPERTIES
    HORIZONTAL_POSITIONS = ("left", "center", "right")
    VERTICAL_POSITIONS = ("top", "center", "bottom")
    BACKGROUND_IMAGE_OPTIONS = ("none",) + COMMON_PROPERTIES
    BACKGROUND_ATTACHMENTS = ("scroll", "fixed", "local") + COMMON_PROPERTIES
    BACKGROUND_REPEAT_OPTIONS = ("repeat", "repeat-x", "repeat-y", "no-repeat") + COMMON_PROPERTIES
    BACKGROUND_POSITIONS = ("left top", "left center", "left bottom", "right top", "right center", "right bottom",
        "center top", "center center", "center bottom", "left", "center", "right", "top", "bottom") + COMMON_PROPERTIES
    NUMBER_RE = re.compile("^\d+$")
    SIGNED_NUMBER_RE = re.compile("^[-+]?\d+$")
    PX_RE = re.compile("^(\d+)px$")
    PERCENT_RE = re.compile("^(\d+)%$")
    #: Web color interpretation:
    #:   * #123: red = 1, green = 2, blue = 3, alpha = 0xff
    #:   * #1234: red = 1, green = 2, blue = 3, alpha = 4
    #:   * #12345: red = 1, green = 2, blue = 3, alpha = 0x45
    #:   * #123456: red = 0x12, green = 0x34, blue = 0x56, alpha = 0xff
    #:   * #1234567: red = 0x12, green = 0x34, blue = 0x56, alpha = 7
    #:   * #12345678: red = 0x12, green = 0x34, blue = 0x56, alpha = 0x78
    WEB_COLOR_RE = re.compile("^#[0-9a-fA-F]{3,8}$")
    BACKGROUND_RESOURCE_RE = re.compile("^bkg_[0-9a-zA-Z_]+$")
    BACKGROUND_POSITION_RE = re.compile("^\d+%?( \d+%?)?$")
    LENGTH_RE_SET = (
        NUMBER_RE,
        PX_RE,
        PERCENT_RE,
    )
    MAX_LENGTHS = ("none",) + COMMON_PROPERTIES
    LENGTHS = ("auto",) + COMMON_PROPERTIES
    DISPLAY_OPTIONS = ("none", "inline", "block") + COMMON_PROPERTIES
    VISIBILITY = ("visible", "hidden") + COMMON_PROPERTIES
    POSITIONS = ("static", "relative", "fixed", "absolute") + COMMON_PROPERTIES
    COLOR_CONSTRAINTS = (color.Color.ADDITIONAL_COLORS.keys() + pygame.colordict.THECOLORS.keys() + [WEB_COLOR_RE] +
        list(BORDER_COLORS))
    STYLE_CONSTRAINTS = {
        "margin-top": {"default": "0", "valid_settings": LENGTH_RE_SET},
        "margin-right": {"default": "0", "valid_settings": LENGTH_RE_SET},
        "margin-bottom": {"default": "0", "valid_settings": LENGTH_RE_SET},
        "margin-left": {"default": "0", "valid_settings": LENGTH_RE_SET},
        "border-top-style": {"default": "none", "valid_settings": BORDER_STYLES},
        "border-right-style": {"default": "none", "valid_settings": BORDER_STYLES},
        "border-bottom-style": {"default": "none", "valid_settings": BORDER_STYLES},
        "border-left-style": {"default": "none", "valid_settings": BORDER_STYLES},
        "border-top-width": {"default": "0px", "valid_settings": BORDER_WIDTHS + LENGTH_RE_SET},
        "border-right-width": {"default": "0px", "valid_settings": BORDER_WIDTHS + LENGTH_RE_SET},
        "border-bottom-width": {"default": "0px", "valid_settings": BORDER_WIDTHS + LENGTH_RE_SET},
        "border-left-width": {"default": "0px", "valid_settings": BORDER_WIDTHS + LENGTH_RE_SET},
        "border-top-color": {"default": "black", "valid_settings": COLOR_CONSTRAINTS},
        "border-right-color": {"default": "black", "valid_settings": COLOR_CONSTRAINTS},
        "border-bottom-color": {"default": "black", "valid_settings": COLOR_CONSTRAINTS},
        "border-left-color": {"default": "black", "valid_settings": COLOR_CONSTRAINTS},
        "padding-top": {"default": "0px", "valid_settings": LENGTH_RE_SET},
        "padding-right": {"default": "0px", "valid_settings": LENGTH_RE_SET},
        "padding-bottom": {"default": "0px", "valid_settings": LENGTH_RE_SET},
        "padding-left": {"default": "0px", "valid_settings": LENGTH_RE_SET},
        "align": {"default": "left", "valid_settings": HORIZONTAL_POSITIONS},
        "valign": {"default": "top", "valid_settings": VERTICAL_POSITIONS},
        "background-color": {"default": "transparent", "valid_settings": COLOR_CONSTRAINTS},
        "background-resource": {"default": "none", "valid_settings": (BACKGROUND_RESOURCE_RE,) + BACKGROUND_IMAGE_OPTIONS},
        "background-repeat": {"default": "repeat", "valid_settings": BACKGROUND_REPEAT_OPTIONS},
        "background-attachment": {"default": "scroll", "valid_settings": BACKGROUND_ATTACHMENTS},
        "background-position": {"default": "0% 0%", "valid_settings": (BACKGROUND_POSITION_RE,) + BACKGROUND_POSITIONS},
        "min-width": {"default": "0", "valid_settings": LENGTH_RE_SET + COMMON_PROPERTIES},
        "width": {"default": "auto", "valid_settings": LENGTH_RE_SET + LENGTHS},
        "max-width": {"default": "none", "valid_settings": LENGTH_RE_SET + MAX_LENGTHS},
        "min-height": {"default": "0", "valid_settings": LENGTH_RE_SET + COMMON_PROPERTIES},
        "height": {"default": "auto", "valid_settings": LENGTH_RE_SET + LENGTHS},
        "max-height": {"default": "none", "valid_settings": LENGTH_RE_SET + MAX_LENGTHS},
        "display": {"default": "inline", "valid_settings": DISPLAY_OPTIONS},
        "visibility": {"default": "visible", "valid_settings": VISIBILITY},
        "position": {"default": "static", "valid_settings": POSITIONS},
        "left": {"default": "auto", "valid_settings": LENGTH_RE_SET + LENGTHS},
        "right": {"default": "auto", "valid_settings": LENGTH_RE_SET + LENGTHS},
        "top": {"default": "auto", "valid_settings": LENGTH_RE_SET + LENGTHS},
        "bottom": {"default": "auto", "valid_settings": LENGTH_RE_SET + LENGTHS},
        "z-index": {"default": "auto", "valid_settings": (SIGNED_NUMBER_RE,) + LENGTHS},
    }
    BACKGROUND_POSITION_TRANSFORMATIONS = {
        re.compile("^((left)|(center)|(right))$"): "{group1} center",
        re.compile("^((top)|(bottom))$"): "center {group1}",
        re.compile("^(\d+%?)$"): "{group1} 50%",
    }
    STYLE_TRANSFORMATIONS = {
        "background-position": BACKGROUND_POSITION_TRANSFORMATIONS,
    }
    # Join together adjacent properties that match the given regex tuple lists
    # for the properties named as keys
    PROPERTY_JOIN_TABLE = {
        "background-position": ((re.compile("^((left)|(right)|(center))$"), re.compile("^((top)|(center)|(bottom))$")),
            (re.compile("\d+%?"), re.compile("\d+%?"))),
        "background": ((re.compile("^((left)|(right)|(center))$"), re.compile("^((top)|(center)|(bottom))$")),
            (re.compile("\d+%?"), re.compile("\d+%?"))),
    }
    SHORTHAND_STYLES = None

    @classmethod
    def compare_value_vs_constraint(cls, style_entry, value):
        compare_ok = False
        if style_entry in cls.STYLE_CONSTRAINTS.keys():
            regex_list, match_list = split_regex_and_str_list(cls.STYLE_CONSTRAINTS[style_entry]["valid_settings"])
            if value in match_list:
                compare_ok = True
            else:
                for a_regex in regex_list:
                    if a_regex.search(value) is not None:
                        compare_ok = True
                        break
        return compare_ok

    @classmethod
    def construct_shorthand_style_table(cls):
        if cls.SHORTHAND_STYLES is None:
            cls.SHORTHAND_STYLES = {
                "margin": ShorthandStyle("margin", {
                    4: (("margin-top",), ("margin-right",), ("margin-bottom",), ("margin-left",)),
                    3: (("margin-top",), ("margin-right", "margin-left"), ("margin-bottom",)),
                    2: (("margin-top", "margin-bottom"), ("margin-right", "margin-left")),
                    1: (("margin-top", "margin-right", "margin-bottom", "margin-left"),)
                }),
                "border-style": ShorthandStyle("border-style", {
                    4: (("border-top-style",), ("border-right-style",), ("border-bottom-style",), ("border-left-style",)),
                    3: (("border-top-style",), ("border-right-style", "border-left-style"), ("border-bottom-style",)),
                    2: (("border-top-style", "border-bottom-style"), ("border-right-style", "border-left-style")),
                    1: (("border-top-style", "border-right-style", "border-bottom-style", "border-left-style"),)
                }),
                "border-width": ShorthandStyle("border-width", {
                    4: (("border-top-width",), ("border-right-width",), ("border-bottom-width",), ("border-left-width",)),
                    3: (("border-top-width",), ("border-right-width", "border-left-width"), ("border-bottom-width",)),
                    2: (("border-top-width", "border-bottom-width"), ("border-right-width", "border-left-width")),
                    1: (("border-top-width", "border-right-width", "border-bottom-width", "border-left-width"),)
                }),
                "border-color": ShorthandStyle("border-color", {
                    4: (("border-top-color",), ("border-right-color",), ("border-bottom-color",), ("border-left-color",)),
                    3: (("border-top-color",), ("border-right-color", "border-left-color"), ("border-bottom-color",)),
                    2: (("border-top-color", "border-bottom-color"), ("border-right-color", "border-left-color")),
                    1: (("border-top-color", "border-right-color", "border-bottom-color", "border-left-color"),)
                }),
                "border": ShorthandStyle("border", {
                    3: (("border-top-width", "border-right-width", "border-bottom-width", "border-left-width"),
                        ("border-top-style", "border-right-style", "border-bottom-style", "border-left-style"),
                        ("border-top-color", "border-right-color", "border-bottom-color", "border-left-color"))
                }),
                "padding": ShorthandStyle("padding", {
                    4: (("padding-top",), ("padding-right",), ("padding-bottom",), ("padding-left",)),
                    3: (("padding-top",), ("padding-right", "padding-left"), ("padding-bottom",)),
                    2: (("padding-top", "padding-bottom"), ("padding-right", "padding-left")),
                    1: (("padding-top", "padding-right", "padding-bottom", "padding-left"),)
                }),
                "background": ShorthandStyle("background", {
                    5: (("background-color",), ("background-resource",), ("background-repeat",), ("background-attachment",),
                        ("background-position",))
                    },
                    cls.compare_value_vs_constraint)
            }

    @classmethod
    def get_style_entry_default(cls, style_entry_name):
        if style_entry_name in cls.STYLE_CONSTRAINTS.keys():
            return cls.STYLE_CONSTRAINTS[style_entry_name]["default"]
        else:
            raise(NameError, "Unknown style entry '{}'".format(style_entry_name))

    def __init__(self, style_table):
        self.style = {}
        self.collect_style_defaults()
        if self.SHORTHAND_STYLES is None:
            self.construct_shorthand_style_table()
        for style_entry in style_table.keys():
            if style_entry in self.style.keys():
                if not isinstance(style_table[style_entry], str) and hasattr(style_table[style_entry], 'join'):
                    # the style engine always uses lists to store values
                    # if there are multiple entries, join them with spaces
                    self.style[style_entry] = " ".join(style_table[style_entry])
                else:
                    self.style[style_entry] = style_table[style_entry]
                if not type(self).compare_value_vs_constraint(style_entry, style_table[style_entry]):
                    raise(WidgetStyleInvalid("Invalid value {} for style {}".format(style_table[style_entry], style_entry)))
            elif style_entry in self.SHORTHAND_STYLES.keys():
                # shorthand properties must supply values in a list
                # print("Style before shorthand expansion:\n{}".format(self.style))
                self.style.update(self.expand_shorthand_style(style_entry, style_table[style_entry]))
                # print("Style after shorthand expansion:\n{}".format(self.style))
        # transform values (E.G. fill in missing values)
        for style_entry in self.style.keys():
            if style_entry in self.STYLE_TRANSFORMATIONS.keys():
                # print("Transform {}={}:".format(style_entry, self.style[style_entry]))
                new_value = self.transform_value(style_entry, self.style[style_entry])
                # print("{} -> {}".format(self.style[style_entry], new_value))
                self.style[style_entry] = new_value

    def collect_style_defaults(self):
        for style_entry in self.STYLE_CONSTRAINTS.keys():
            default = self.STYLE_CONSTRAINTS[style_entry]["default"]
            if not type(self).compare_value_vs_constraint(style_entry, default):
                print("Warning: default value '{}' is not a valid setting for style entry '{}'!".format(default,
                    style_entry))
            self.style[style_entry] = default

    def match_multi_regex(self, regex_list, str_list):
        # return True if each of the str_list items matched the regexes in
        # regex_list, 0 if the list lengths don't match or any str_list
        # item failed to match
        if len(regex_list) != len(str_list):
            return False
        matched = True
        for an_idx, a_regex in enumerate(regex_list):
            if a_regex.search(str_list[an_idx]) is None:
                matched = False
                break
        return matched

    def join_properties(self, property_name, property_values):
        new_value_list = []
        idx = 0
        if property_name not in self.PROPERTY_JOIN_TABLE.keys():
            return property_values
        while idx < len(property_values):
            # print("Check value {}:".format(property_values[idx]))
            if idx == len(property_values) - 1:
                # can't match multiple regexes at the last index
                # print("Add {} to new list".format(property_values[idx]))
                new_value_list.append(property_values[idx])
                break
            found_match = False
            for a_regex_list in self.PROPERTY_JOIN_TABLE[property_name]:
                regex_list_match = self.match_multi_regex(a_regex_list, property_values[idx:])
                if regex_list_match:
                    match_len = len(a_regex_list)
                    # matched set: join the values into a single space-
                    # separated value
                    new_value_list.append(" ".join(property_values[idx:idx+match_len]))
                    # print("Add {} to new list".format(new_value_list[-1]))
                    idx += match_len
                    found_match = True
                    break
            if not found_match:
                new_value_list.append(property_values[idx])
                # print("Add {} to new list".format(new_value_list[-1]))
                idx += 1
        return new_value_list

    def transform_value(self, style_name, style_value):
        new_value = style_value
        for a_regex in self.STYLE_TRANSFORMATIONS[style_name].keys():
            minfo = a_regex.search(style_value)
            if minfo is not None:
                groupnames = ["group{}".format(idx+1) for idx in range(len(minfo.groups()))]
                groupdict = dict(zip(groupnames, minfo.groups()))
                new_value = self.STYLE_TRANSFORMATIONS[style_name][a_regex].format(**groupdict)
        return new_value

    def expand_shorthand_style(self, style_name, style_values):
        joined_values = self.join_properties(style_name, style_values)
        sub_props = self.SHORTHAND_STYLES[style_name].get_sub_properties(joined_values)
        for sub_prop_name in sub_props.keys():
            if not type(self).compare_value_vs_constraint(sub_prop_name, sub_props[sub_prop_name]):
                raise(WidgetStyleInvalid("Invalid value {} for style {}".format(sub_props[sub_prop_name], sub_prop_name)))
        return sub_props

    def __getitem__(self, itemname):
        return self.style.get(itemname, None)

    def __setitem__(self, itemname, value):
        # check the value if given a known style parameter
        if itemname in self.style:
            if type(self).compare_value_vs_constraint(itemname, value):
                self.style[itemname] = value
            else:
                print("Warning: value '{}' is not valid for style entry '{}'".format(value, itemname))

