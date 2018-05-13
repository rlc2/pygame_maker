"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Widget style settings
"""


import re
import pygame
from pygame_maker.support import color


def split_regex_and_str_list(regex_and_str_list):
    """
    Given an iterable containing both strings and regular expressions, return
    a tuple of (regex list, str list).
    """
    regex_list = []
    str_list = []
    for entry in regex_and_str_list:
        if hasattr(entry, 'search'):
            regex_list.append(entry)
        if isinstance(entry, str):
            str_list.append(entry)
    return (regex_list, str_list)


class ShorthandStyleError(Exception):
    """
    Raised when values in a shorthand style were not recognized by the optional
    value_check_method() in ShorthandStyle.
    """
    pass


class ShorthandStyle(object):
    """
    Wrap a CSS style composed of multiple style settings (E.G. 'border-style'
    is composed of 'border-top-style', 'border-right-style', etc.).

    Used by WidgetStyle to initialize its SHORTHAND_STYLES class attribute in
    its construct_shorthand_style_table() class method.

    :param name: The shorthand style's name
    :type name: str
    :param sub_property_dict: A mapping of property value count to lists of
        lists of sub-property names (the fewer property values supplied, the
        more each value may be duplicated into multiple sub-properties)
    :type sub_property_dict: dict
    :param value_check_method: If supplied, calls to the get_sub_properties()
        method may call this method when the value count isn't found in
        sub_property_dict to determine sub-property values.
    :type value_check_method: None | callable
    """

    def __init__(self, name, sub_property_dict, value_check_method=None):
        self.name = name
        self.sub_property_dict = sub_property_dict
        self.value_check_method = value_check_method

    def get_sub_properties(self, value_list):
        """
        Given the list of values supplied to a shorthand style, return a
        mapping of sub-property names to corresponding values (shorthand CSS
        properties allow the same value to be supplied for multiple sub-
        properties).

        :param value_list: A list of values
        :type value_list: list
        :returns: A mapping of property names to values
        :rtype: dict
        """
        sub_prop_map = {}
        if len(value_list) in list(self.sub_property_dict.keys()):
            for idx, val in enumerate(value_list):
                for sub_prop in self.sub_property_dict[len(value_list)][idx]:
                    sub_prop_map[sub_prop] = val
        elif self.value_check_method is not None:
            # Use the supplied method to determine which sub-properties are
            # present.  The property values must still be in the right order.
            value_idx = 0
            # longest sub-property list is expected to contain all properties
            full_sub_property_list = [s[0] for s in \
                                     self.sub_property_dict[max(self.sub_property_dict.keys())]]
            for sub_prop_name in full_sub_property_list:
                # print("Check {} against {}".format(value_list[value_idx], val_id))
                if self.value_check_method(sub_prop_name, value_list[value_idx]):
                    # print("ID'd {} from {}".format(sub_prop_name, value_list[value_idx]))
                    sub_prop_map[sub_prop_name] = value_list[value_idx]
                    value_idx += 1
            if value_idx < len(value_list):
                raise ShorthandStyleError
        return sub_prop_map


class WidgetStyleInvalid(Exception):
    """
    Raised by WidgetStyle methods when given invalid style values.
    """
    pass


class WidgetStyle(object):
    """
    Wrap widget style settings.
    """

    COMMON_PROPERTIES = ("initial", "inherit")
    BORDER_STYLES = (("none", "dotted", "dashed", "solid", "double", "groove", "ridge", "inset",
                      "outset", "hidden") + COMMON_PROPERTIES)
    BORDER_WIDTHS = ("medium", "thin", "thick") + COMMON_PROPERTIES
    BORDER_COLORS = ("transparent",)
    BACKGROUND_IMAGE_OPTIONS = ("none",) + COMMON_PROPERTIES
    BACKGROUND_ATTACHMENTS = ("scroll", "fixed", "local") + COMMON_PROPERTIES
    BACKGROUND_REPEAT_OPTIONS = ("repeat", "repeat-x", "repeat-y", "no-repeat") + COMMON_PROPERTIES
    BACKGROUND_POSITIONS = ("left top", "left center", "left bottom", "right top", "right center",
                            "right bottom", "center top", "center center", "center bottom", "left",
                            "center", "right", "top", "bottom") + COMMON_PROPERTIES
    NUMBER_RE = re.compile(r"^\d+$")
    SIGNED_NUMBER_RE = re.compile(r"^[-+]?\d+$")
    PX_RE = re.compile(r"^(\d+)px$")
    PERCENT_RE = re.compile(r"^(\d+)%$")
    #: Web color interpretation:
    #:   * #123: red = 1, green = 2, blue = 3, alpha = 0xff
    #:   * #1234: red = 1, green = 2, blue = 3, alpha = 4
    #:   * #12345: red = 1, green = 2, blue = 3, alpha = 0x45
    #:   * #123456: red = 0x12, green = 0x34, blue = 0x56, alpha = 0xff
    #:   * #1234567: red = 0x12, green = 0x34, blue = 0x56, alpha = 7
    #:   * #12345678: red = 0x12, green = 0x34, blue = 0x56, alpha = 0x78
    WEB_COLOR_RE = re.compile("^#[0-9a-fA-F]{3,8}$")
    BACKGROUND_RESOURCE_RE = re.compile("^bkg_[0-9a-zA-Z_]+$")
    BACKGROUND_POSITION_RE = re.compile(r"^\d+%?( \d+%?)?$")
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
    COLOR_CONSTRAINTS = (list(color.Color.ADDITIONAL_COLORS.keys()) + list(pygame.colordict.THECOLORS.keys()) +
                         [WEB_COLOR_RE])
    HORIZONTAL_ALIGNMENT = ("left", "right", "center", "justify") + COMMON_PROPERTIES
    VERTICAL_ALIGNMENT = ("top", "middle", "bottom") + COMMON_PROPERTIES
    TEXT_DECORATIONS = ("none", "underline", "overline", "line-through") + COMMON_PROPERTIES
    TEXT_TRANSFORMATIONS = ("none", "uppercase", "lowercase", "capitalize") + COMMON_PROPERTIES
    FONT_STYLES = ("normal", "italic") + COMMON_PROPERTIES
    FONT_WEIGHTS = ("normal", "bold") + COMMON_PROPERTIES
    FONT_SIZES = ("small", "medium", "large") + COMMON_PROPERTIES
    FONTNAME_RE = re.compile("^[a-zA-Z][0-9a-zA-Z_]+$")
    FONT_FAMILIES = ("serif", "sans", "cursive", "mono") + COMMON_PROPERTIES
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
        "border-top-color": {"default": "black",
                             "valid_settings": COLOR_CONSTRAINTS + \
                                               list(BORDER_COLORS) + \
                                               list(COMMON_PROPERTIES)},
        "border-right-color": {"default": "black",
                               "valid_settings": COLOR_CONSTRAINTS + \
                                                 list(BORDER_COLORS) + \
                                                 list(COMMON_PROPERTIES)},
        "border-bottom-color": {"default": "black",
                                "valid_settings": COLOR_CONSTRAINTS + \
                                                  list(BORDER_COLORS) + \
                                                  list(COMMON_PROPERTIES)},
        "border-left-color": {"default": "black",
                              "valid_settings": COLOR_CONSTRAINTS + \
                                                list(BORDER_COLORS) + \
                                                list(COMMON_PROPERTIES)},
        "padding-top": {"default": "0px", "valid_settings": LENGTH_RE_SET},
        "padding-right": {"default": "0px", "valid_settings": LENGTH_RE_SET},
        "padding-bottom": {"default": "0px", "valid_settings": LENGTH_RE_SET},
        "padding-left": {"default": "0px", "valid_settings": LENGTH_RE_SET},
        "background-color": {"default": "transparent",
                             "valid_settings": COLOR_CONSTRAINTS + \
                                               list(BORDER_COLORS) + \
                                               list(COMMON_PROPERTIES)},
        "background-resource": {"default": "none",
                                "valid_settings": (BACKGROUND_RESOURCE_RE,) + \
                                                  BACKGROUND_IMAGE_OPTIONS},
        "background-repeat": {"default": "repeat", "valid_settings": BACKGROUND_REPEAT_OPTIONS},
        "background-attachment": {"default": "scroll", "valid_settings": BACKGROUND_ATTACHMENTS},
        "background-position": {"default": "0% 0%",
                                "valid_settings": (BACKGROUND_POSITION_RE,) + \
                                                  BACKGROUND_POSITIONS},
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
        "color": {"default": "black",
                  "valid_settings": COLOR_CONSTRAINTS + \
                                    list(COMMON_PROPERTIES)},
        "text-align": {"default": "left", "valid_settings": HORIZONTAL_ALIGNMENT},
        "vertical-align": {"default": "bottom", "valid_settings": VERTICAL_ALIGNMENT},
        "text-decoration": {"default": "none", "valid_settings": TEXT_DECORATIONS},
        "text-transform": {"default": "none", "valid_settings": TEXT_TRANSFORMATIONS},
        "font-style": {"default": "normal", "valid_settings": FONT_STYLES},
        "font-weight": {"default": "normal", "valid_settings": FONT_WEIGHTS},
        "font-size": {"default": "medium", "valid_settings": FONT_SIZES + LENGTH_RE_SET},
        "font": {"default": "", "valid_settings": ("",) + (FONTNAME_RE,)},
    }
    BACKGROUND_POSITION_TRANSFORMS = {
        re.compile("^((left)|(center)|(right))$"): "{group1} center",
        re.compile("^((top)|(bottom))$"): "center {group1}",
        re.compile(r"^(\d+%?)$"): "{group1} 50%",
    }
    STYLE_TRANSFORMATIONS = {
        "background-position": BACKGROUND_POSITION_TRANSFORMS,
    }
    # Join together adjacent properties that match the given regex tuple lists
    # for the properties named as keys
    PROPERTY_JOIN_TABLE = {
        "background-position": ((re.compile("^((left)|(right)|(center))$"),
                                 re.compile("^((top)|(center)|(bottom))$")),
                                (re.compile(r"\d+%?"), re.compile(r"\d+%?"))),
        "background": ((re.compile("^((left)|(right)|(center))$"),
                        re.compile("^((top)|(center)|(bottom))$")),
                       (re.compile(r"\d+%?"), re.compile(r"\d+%?"))),
    }
    SHORTHAND_STYLES = None

    @staticmethod
    def match_multi_regex(regex_list, str_list):
        """
        Test whether each item in a list of strings matches a corresponding
        regular expression in a list of regex's.

        :param regex_list: A list of regular expressions
        :type regex_list: list
        :param str_list: A list of strings to be compared against each regex
            in regex_list
        :type str_list: list
        :returns: True if each of the str_list items matched the regexes in
            regex_list, False if the list lengths don't match or any str_list
            item failed to match
        :rtype: bool
        """
        if len(regex_list) != len(str_list):
            return False
        matched = True
        for an_idx, a_regex in enumerate(regex_list):
            if a_regex.search(str_list[an_idx]) is None:
                matched = False
                break
        return matched

    @classmethod
    def compare_value_vs_constraint(cls, style_entry, value):
        """
        Given a style name in the STYLE_CONSTRAINTS dict, determine whether
        the given value is valid.

        :param style_entry: A style name
        :type style_entry: str
        :param value: A value to compare against the style constraints
        :returns: True if the value is valid, False otherwise
        :rtype: bool
        """
        compare_ok = False
        if style_entry in list(cls.STYLE_CONSTRAINTS.keys()):
            # split the valid_settings list into a tuple containing a list of
            #  all regex's and a list of all strings (exact matches)
            regex_list, match_list = split_regex_and_str_list(
                cls.STYLE_CONSTRAINTS[style_entry]["valid_settings"])
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
        """
        A one-shot method that fills in the SHORTHAND_STYLES class attribute,
        so that shorthand styles can be split into component styles set to
        values that depend on the number of values assigned to the shorthand
        style.
        """
        if cls.SHORTHAND_STYLES is None:
            cls.SHORTHAND_STYLES = {
                "margin": ShorthandStyle("margin", {
                    4: (("margin-top",), ("margin-right",), ("margin-bottom",), ("margin-left",)),
                    3: (("margin-top",), ("margin-right", "margin-left"), ("margin-bottom",)),
                    2: (("margin-top", "margin-bottom"), ("margin-right", "margin-left")),
                    1: (("margin-top", "margin-right", "margin-bottom", "margin-left"),)
                }),
                "border-style": ShorthandStyle("border-style", {
                    4: (("border-top-style",), ("border-right-style",),
                        ("border-bottom-style",), ("border-left-style",)),
                    3: (("border-top-style",), ("border-right-style", "border-left-style"),
                        ("border-bottom-style",)),
                    2: (("border-top-style", "border-bottom-style"),
                        ("border-right-style", "border-left-style")),
                    1: (("border-top-style", "border-right-style",
                         "border-bottom-style", "border-left-style"),)
                }),
                "border-width": ShorthandStyle("border-width", {
                    4: (("border-top-width",), ("border-right-width",),
                        ("border-bottom-width",), ("border-left-width",)),
                    3: (("border-top-width",), ("border-right-width", "border-left-width"),
                        ("border-bottom-width",)),
                    2: (("border-top-width", "border-bottom-width"),
                        ("border-right-width", "border-left-width")),
                    1: (("border-top-width", "border-right-width",
                         "border-bottom-width", "border-left-width"),)
                }),
                "border-color": ShorthandStyle("border-color", {
                    4: (("border-top-color",), ("border-right-color",),
                        ("border-bottom-color",), ("border-left-color",)),
                    3: (("border-top-color",), ("border-right-color", "border-left-color"),
                        ("border-bottom-color",)),
                    2: (("border-top-color", "border-bottom-color"),
                        ("border-right-color", "border-left-color")),
                    1: (("border-top-color", "border-right-color",
                         "border-bottom-color", "border-left-color"),)
                }),
                "border": ShorthandStyle("border", {
                    3: (("border-top-width", "border-right-width",
                         "border-bottom-width", "border-left-width"),
                        ("border-top-style", "border-right-style",
                         "border-bottom-style", "border-left-style"),
                        ("border-top-color", "border-right-color",
                         "border-bottom-color", "border-left-color"))
                }),
                "padding": ShorthandStyle("padding", {
                    4: (("padding-top",), ("padding-right",), ("padding-bottom",),
                        ("padding-left",)),
                    3: (("padding-top",), ("padding-right", "padding-left"), ("padding-bottom",)),
                    2: (("padding-top", "padding-bottom"), ("padding-right", "padding-left")),
                    1: (("padding-top", "padding-right", "padding-bottom", "padding-left"),)
                }),
                "background": ShorthandStyle("background", {
                    5: (("background-color",), ("background-resource",),
                        ("background-repeat",), ("background-attachment",),
                        ("background-position",))
                    },
                                             cls.compare_value_vs_constraint)
            }

    @classmethod
    def get_style_entry_default(cls, style_entry_name):
        """
        Return the default value for a given style name.

        :returns: The style's default value
        :raises: NameError if style_entry_name is not found in
            STYLE_CONSTRAINTS
        """
        if style_entry_name in list(cls.STYLE_CONSTRAINTS.keys()):
            return cls.STYLE_CONSTRAINTS[style_entry_name]["default"]
        else:
            raise NameError

    def __init__(self, style_table):
        self.style = {}
        self.collect_style_defaults()
        if self.SHORTHAND_STYLES is None:
            self.construct_shorthand_style_table()
        for style_entry in list(style_table.keys()):
            if style_entry in list(self.style.keys()):
                if not isinstance(style_table[style_entry], str) and \
                        hasattr(style_table[style_entry], '__len__'):
                    # the style engine always uses lists to store values
                    # if there are multiple entries, join them with spaces
                    self.style[style_entry] = " ".join(style_table[style_entry])
                else:
                    self.style[style_entry] = style_table[style_entry]
                if not type(self).compare_value_vs_constraint(style_entry, self.style[style_entry]):
                    raise WidgetStyleInvalid
            elif style_entry in list(self.SHORTHAND_STYLES.keys()):
                # shorthand properties must supply values in a list
                # print("Style before shorthand expansion:\n{}".format(self.style))
                self.style.update(self.expand_shorthand_style(style_entry,
                                                              style_table[style_entry]))
                # print("Style after shorthand expansion:\n{}".format(self.style))
        # transform values (E.G. fill in missing values)
        for style_entry in list(self.style.keys()):
            if style_entry in list(self.STYLE_TRANSFORMATIONS.keys()):
                # print("Transform {}={}:".format(style_entry, self.style[style_entry]))
                new_value = self.transform_value(style_entry, self.style[style_entry])
                # print("{} -> {}".format(self.style[style_entry], new_value))
                self.style[style_entry] = new_value

    def collect_style_defaults(self):
        """
        Give every style setting its default value.
        """
        for style_entry in list(self.STYLE_CONSTRAINTS.keys()):
            default = self.STYLE_CONSTRAINTS[style_entry]["default"]
            if not type(self).compare_value_vs_constraint(style_entry, default):
                print(("Warning: default value '{}' is not a valid setting for style entry '{}'!".
                      format(default, style_entry)))
            self.style[style_entry] = default

    def join_properties(self, property_name, property_values):
        """
        Combine space-separated values as needed by certain settings
        (exceptions to the usual rule of a single value per setting).

        :param property_name: The setting name
        :type property_name: str
        :param property_values: A list of the space-separated values
        :type property_values: list
        :returns: A re-formatted list with values combined with spaces as
            needed
        :rtype: list
        """
        new_value_list = []
        idx = 0
        if property_name not in list(self.PROPERTY_JOIN_TABLE.keys()):
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
                regex_list_match = WidgetStyle.match_multi_regex(a_regex_list,
                                                                 property_values[idx:])
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
        """
        Transform settings such that implied values are made explicit
        (currently only used for 'background-position', which implicitly sets
        unspecified values).

        :param style_name: The style's name
        :type style_name: str
        :param style_value: The value, with possibly missing (implied) values
        :type style_value: str
        """
        new_value = style_value
        for a_regex in list(self.STYLE_TRANSFORMATIONS[style_name].keys()):
            minfo = a_regex.search(style_value)
            if minfo is not None:
                groupnames = ["group{}".format(idx+1) for idx in range(len(minfo.groups()))]
                groupdict = dict(list(zip(groupnames, minfo.groups())))
                new_value = self.STYLE_TRANSFORMATIONS[style_name][a_regex].format(**groupdict)
        return new_value

    def expand_shorthand_style(self, style_name, style_values):
        """
        Given a shorthand style name along with its values, split it into each
        of its component styles with values assigned based on the number of
        values supplied.

        :param style_name: The setting's name
        :type style_name: str
        :param style_values: A list of values assigned to the shorthand
            setting
        :raises: WidgetStyleInvalid if any value fails to meet constraints
        :returns: A mapping of style names to style values
        :rtype: dict
        """
        joined_values = self.join_properties(style_name, style_values)
        sub_props = self.SHORTHAND_STYLES[style_name].get_sub_properties(joined_values)
        for sub_prop_name in list(sub_props.keys()):
            if not type(self).compare_value_vs_constraint(sub_prop_name, sub_props[sub_prop_name]):
                raise WidgetStyleInvalid
        return sub_props

    def keys(self):
        """
        Implement a dict-like interface for style settings.
        """
        return list(self.style.keys())

    def __getitem__(self, itemname):
        return self.style.get(itemname, None)

    def __setitem__(self, itemname, value):
        # check the value if given a known style parameter
        if itemname in self.style:
            if type(self).compare_value_vs_constraint(itemname, value):
                self.style[itemname] = value
            else:
                print(("Warning: value '{}' is not valid for style entry '{}'".
                      format(value, itemname)))

    def __repr__(self):
        key_list = list(self.style.keys())
        key_list.sort()
        prop_info = ["'{}': '{}'".format(k, self.style[k]) for k in key_list]
        return "{{{}}}".format(", ".join(prop_info))

