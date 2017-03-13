#!/usr/bin/python -W all

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker widgets

import re
import pygame
from styles import WidgetStyle
from .. import object_type
from .. import simple_object_instance
import pygame_maker.support.drawing as drawing
import pygame_maker.support.coordinate as coord


def get_int_from_length_setting(length_setting, total_length):
    """
    For any length setting, whether numeric, a number with 'px' suffix, or
    a percentage, return a numeric value.

    Invalid length strings will be returned as 0.

    :param length_setting: The length found in a style property
    :type length_setting: str
    :param total_length: The maximum possible numeric value, for calculating
        percentages
    :return: The numeric value
    :rtype: int
    """
    pass


class DummySurface(pygame.Rect):
    def get_width(self):
        return self.width
    def get_height(self):
        return self.height


class WidgetInstance(simple_object_instance.SimpleObjectInstance):
    INSTANCE_SYMBOLS = {
        "visible": 0,
        "widget_id": "",
        "widget_class": "",
        "hover": False,
        "selected": False,
        "width": 0,
        "height": 0,
    }
    THIN_BORDER_WIDTH = 1
    MEDIUM_BORDER_WIDTH = 3
    THICK_BORDER_WIDTH = 5
    def __init__(self, kind, screen_dims, id_, settings=None, **kwargs):
        simple_object_instance.SimpleObjectInstance.__init__(self, kind, screen_dims, id_, settings, **kwargs)
        self.screen_width = self.screen_dims[0]
        self.screen_height = self.screen_dims[1]
        self.style_settings = {}
        self.style_values = {}
        self.has_focus = False

        style_hash = self.get_widget_instance_style_hash()
        style_info = self.game_engine.global_style_settings.get_style(**style_hash)
        self.get_widget_settings(style_info)

    @property
    def visible(self):
        return self.symbols["visible"]

    @visible.setter
    def visible(self, is_visible):
        vis = (is_visible is True)
        self.symbols["visible"] = vis

    @property
    def widget_id(self):
        return self.symbols["widget_id"]

    @widget_id.setter
    def widget_id(self, new_id):
        self.symbols["widget_id"] = new_id

    @property
    def widget_class(self):
        return self.symbols["widget_class"]

    @widget_class.setter
    def widget_class(self, new_id):
        self.symbols["widget_class"] = new_id

    @property
    def hover(self):
        return int(self.symbols["hover"])

    @hover.setter
    def hover(self, hover_on):
        self.symbols["hover"] = (hover_on == True)

    @property
    def selected(self):
        return int(self.symbols["selected"])

    @selected.setter
    def selected(self, hover_on):
        self.symbols["selected"] = (hover_on == True)

    @property
    def width(self):
        return self.symbols["width"]

    @width.setter
    def width(self, new_width):
        int_width = int(new_width)
        self.rect.width = int_width
        self.symbols["width"] = int_width

    @property
    def height(self):
        return self.symbols["height"]

    @height.setter
    def height(self, new_height):
        int_height = int(new_height)
        self.rect.height = int_height
        self.symbols["height"] = int_height

    def get_style_setting(self, setting_name, css_properties, parent_settings):
        default_setting = WidgetStyle.get_style_entry_default(setting_name)
        setting = default_setting
        if setting_name in css_properties.keys():
            check_setting = css_properties[setting_name]
            if check_setting != "initial":
                if (WidgetStyle.compare_value_vs_constraint(setting_name, "inherit") and
                                check_setting == "inherit" and self.parent is not None):
                    setting = parent_settings[setting_name]
                elif WidgetStyle.compare_value_vs_constraint(setting_name, check_setting):
                    setting = check_setting
        return setting

    def get_widget_settings(self, css_properties):
        if self.parent is not None:
            # this could result in the parent checking its parent's
            # settings..
            parent_settings = self.parent.get_widget_settings(css_properties)
        for setting_name in WidgetStyle.STYLE_CONSTRAINTS.keys():
            self.style_settings[setting_name] = self.get_style_setting(setting_name, css_properties,
                parent_settings)

    def _get_integer_setting(self, setting, max_value):
        value = 0
        num_minfo = WidgetStyle.NUMBER_RE.search(setting)
        if num_minfo:
            value = int(setting)
        num_minfo = WidgetStyle.SIGNED_NUMBER_RE.search(setting)
        if num_minfo:
            value = int(setting)
        px_minfo = WidgetStyle.PX_RE.search(setting)
        if px_minfo:
            value = int(px_minfo.group(1))
        pc_minfo = WidgetStyle.PERCENT_RE.search(setting)
        if pc_minfo:
            perc = float(px_minfo.group(1)) / 100.0
            if perc > 1.0:
                # WidgetStyle doesn't constrain the percentage; force
                # maximum to 100% 
                perc = 1.0
            value = int(math.floor(perc * max_value))
        return value

    def get_outer_setting_values(self, surface):
        # CSS box model: calculate margin, border, and padding so the remaining
        # setting values can be calculated
        surface_width = surface.get_width()
        surface_height = surface.get_height()
        for setting_name in ("margin-left", "border-left-width", "padding-left",
                             "padding-right", "border-right-width", "margin-right"):
            style_val = self._get_integer_setting(self.style_settings[setting_name], surface_width)
            self.style_values[setting_name] = style_val
        for setting_name in ("margin-top", "border-top-width", "padding-top",
                             "padding-bottom", "border-bottom-width", "margin-bottom"):
            style_val = self._get_integer_setting(self.style_settings[setting_name], surface_height)
            self.style_values[setting_name] = style_val

    def calculate_outer_dimensions(self):
        # calculate width
        outer_width = (self.style_values["margin-left"] + self.style_values["margin-right"] +
            self.style_values["padding-left"] + self.style_values["padding-right"])
        border_left_width = 0
        if self.style_settings["border-left-style"] not in ("none", "hidden"):
            border_left_width = self.style_values["border-left-width"]
            if self.style_settings["border-left-style"] == "double":
                border_left_width = border_left_width * 2 + 1
        border_right_width = 0
        if self.style_settings["border-right-style"] not in ("none", "hidden"):
            border_right_width = self.style_values["border-right-width"]
            if self.style_settings["border-right-style"] == "double":
                border_right_width = border_right_width * 2 + 1
        outer_width += border_left_width + border_right_width
        # calculate height
        outer_height = (self.style_values["margin-top"] + self.style_values["margin-bottom"] +
            self.style_values["padding-top"] + self.style_values["padding-bottom"])
        border_top_height = 0
        if self.style_settings["border-top-style"] not in ("none", "hidden"):
            border_top_height = self.style_values["border-top-width"]
            if self.style_settings["border-top-style"] == "double":
                border_top_height = border_top_height * 2 + 1
        border_bottom_height = 0
        if self.style_settings["border-bottom-style"] not in ("none", "hidden"):
            border_bottom_height = self.style_values["border-bottom-width"]
            if self.style_settings["border-bottom-style"] == "double":
                border_bottom_height = border_bottom_height * 2 + 1
        outer_height += border_top_height + border_bottom_height
        return (outer_width, outer_height)

    def get_inner_setting_values(self, max_dimensions):
        # calculate min-width, width, max-width values
        min_width_val = self._get_integer_setting(self.style_settings["min-width"], max_dimensions[0])
        if min_width_val > max_dimensions[0]:
            min_width_val = max_dimensions[0]
        self.style_values["min-width"] = min_width_val
        max_width_val = max_dimensions[0]
        if self.style_settings["max-width"] != "none":
            max_width_val = self._get_integer_setting(self.style_settings["max-width"], max_dimensions[0])
            if max_width_val > max_dimensions[0]:
                max_width_val = max_dimensions[0]
            elif max_width_val < min_width_val:
                max_width_val = min_width_val
            self.style_values["max-width"] = max_width_val
        if self.style_settings["width"] != "auto":
            width_val = self._get_integer_setting(self.style_settings["width"], max_dimensions[0])
            if width_val < min_width_val:
                width_val = min_width_val
            if width_val > max_width_val:
                width_val = max_width_val
            self.style_values["width"] = width_val
        # calculate min-height, height, max-height values
        min_height_val = self._get_integer_setting(self.style_settings["min-height"], max_dimensions[1])
        if min_height_val > max_dimensions[1]:
            min_height_val = max_dimensions[1]
        self.style_values["min-height"] = min_height_val
        max_height_val = max_dimensions[1]
        if self.style_settings["max-height"] != "none":
            max_height_val = self._get_integer_setting(self.style_settings["max-height"], max_dimensions[1])
            if max_height_val > max_dimensions[1]:
                max_height_val = max_dimensions[1]
            elif max_height_val < min_height_val:
                max_height_val = min_height_val
            self.style_values["max-height"] = max_height_val
        if self.style_settings["height"] != "auto":
            height_val = self._get_integer_setting(self.style_settings["height"], max_dimensions[1])
            if height_val < min_height_val:
                height_val = min_height_val
            if height_val > max_height_val:
                height_val = max_height_val
            self.style_values["height"] = height_val

    def get_element_dimensions(self):
        """
        Called after get_inner_setting_values() to determine the size of the
        widget's content.

        The base class will use the 'min-width' and 'min-height' properties as
        element dimensions, if the 'width' and 'height' properties are 'auto';
        otherwise, it will use the 'width' and/or 'height' properties' values.
        Subclasses should start here, and expand as needed to fit widget
        content, honoring the 'max-width' and 'max-height' properties.
        """
        element_width = self.style_values["min-width"]
        element_height = self.style_values["min-height"]
        if self.style_settings["width"] != "auto":
            element_width = self.style_values["width"]
        if self.style_settings["height"] != "auto":
            element_width = self.style_values["height"]
        return (element_width, element_height)

    def get_color_values(self):
        # put Color objects into border/background color settings
        for color_property in ("border-top-color", "border-right-color", "border-bottom-color", "border-left-color",
                               "background-color"):
            color_name = self.style_settings[color_property]
            color_string = color_name
            if color_name != "transparent":
                minfo = WidgetStyle.WEB_COLOR_RE.match(color_name)
                if minfo:
                    if len(color_name) == 4:
                        color_string = "#0{}0{}0{}".format(*color_name[1:4])
                    elif len(color_name) == 5:
                        color_string = "#0{}0{}0{}0{}".format(*color_name[1:5])
                    elif len(color_name) == 6:
                        str_ary = [color_name[idx] for idx in range(1,4)]
                        str_ary.append(color_name[4:])
                        color_string = "#0{}0{}0{}{}".format(*str_ary)
                    elif len(color_name) == 8:
                        color_string = "{}0{}".format(color_name[:7], color_name[7])
            self.style_values[color_property] = color.Color(color_string)

    def get_min_size(self):
        """
        Calculate the widget's mininum width and height, and return them in a
        tuple.

        Container widgets may call this to find out how much space it needs
        to reserve for each of its child widgets.
        The base class only returns the space surrounding the widget's
        contents: the sum of margin, border, and padding widths for each side.
        Subclasses should call this method, then determine the element's
        actual dimensions after taking min/max width and height into account.

        :param screen: The surface the widget will be drawn on
        :type screen: pygame.Surface
        :param css_properties: The CSS properties that apply to this widget
        :type css_properties: dict
        :param parent_settings: The parent's widget style
        :type parent_settings: dict
        """
        # create a surface such that 1% is a minimum of 1 pixel
        dummy_surface = DummySurface(0,0,100,100)
        min_width = 1
        min_height = 1
        style_hash = self.get_widget_instance_style_hash()
        style_info = self.game_engine.global_style_settings.get_style(**style_hash)
        self.get_widget_settings(style_info)
        self.get_outer_setting_values(dummy_surface)
        min_outer_dims = self.calculate_outer_dimensions()
        if min_outer_dims[0] > min_width:
            min_width = min_outer_dims[0]
        if min_outer_dims[1] > min_height:
            min_height = min_outer_dims[1]
        return (min_width, min_height)

    def _calculate_top_outer_border_size(self):
        top_size = self.style_values["margin-top"] + self.style_values["padding-top"]
        border_top_height = 0
        if self.style_settings["border-top-style"] not in ("none", "hidden"):
            border_top_height = self.style_values["border-top-width"]
            if self.style_settings["border-top-style"] == "double":
                border_top_height = border_top_height * 2 + 1
        top_size += border_top_height
        return top_size

    def _calculate_left_outer_border_size(self):
        left_size = self.style_values["margin-left"] + self.style_values["padding-left"]
        border_left_width = 0
        if self.style_settings["border-left-style"] not in ("none", "hidden"):
            border_left_width = self.style_values["border-left-width"]
            if self.style_settings["border-left-style"] == "double":
                border_left_width = border_left_width * 2 + 1
        left_size += border_left_width
        return left_size

    def _draw_border_side(self, screen, side, outer_dims, element_dims, width, color, style):
        draw_rect = pygame.Rect(0,0,0,0)
        if side == "top":
            draw_rect.left = self.style_values["margin-left"]
            draw_rect.top = self.style_values["margin-top"]
            draw_rect.width = self.style_values["padding-left"] + element_dims[0] + self.style_values["padding-right"]
            if draw_rect.width <= 1:
                return
        elif side == "bottom":
            draw_rect.left = self.style_values["margin-left"]
            draw_rect.top = (self._calculate_top_outer_border_size() + element_dims[1] +
                self.style_values["padding-bottom"])
            draw_rect.width = self.style_values["padding_left"] + element_dims[0] + self.style_values["padding-right"]
            if draw_rect.width <= 1:
                return
        elif side == "left":
            draw_rect.left = self.style_values["margin-left"]
            draw_rect.top = self.style_values["margin-top"]
            draw_rect.height = self.style_values["padding-top"] + element_dims[1] + self.style_values["padding-bottom"]
            if draw_rect.height <= 1:
                return
        elif side == "right":
            draw_rect.left = (self._calculate_left_outer_border_size() + element_dims[0] +
                sefl.style_values["padding-right"])
            draw_rect.top = self.style_values["margin-top"]
            draw_rect.height = self.style_values["padding-top"] + element_dims[1] + self.style_values["padding-bottom"]
            if draw_rect.height <= 1:
                return
        start_coord = coord.Coordinate(draw_rect.left, draw_rect.top)
        end_coord = coord.Coordinate(draw_rect.right, draw_rect.bottom)
        drawing.draw_line(screen, start_coord, end_coord, width, color, style)

    def draw_border(self, screen, outer_dims):
        element_dims = self.get_element_dimensions()
        for side in ("top", "right", "bottom", "left"):
            border_width = self.style_settings["border-{}-width".format(side)]
            border_style = self.style_settings["border-{}-style".format(side)]
            border_color_style = self.style_settings["border-{}-color".format(side)]
            border_color = "transparent"
            if border_color_style != "transparent":
                border_color = self.style_values["border-{}-color".format(side)]
            if border_style in ("none", "hidden") or (border_width < 1) or border_color == "transparent":
                continue
            self._draw_border_side(screen, side, outer_dims, element_dims, width, color, style)

    def draw(self, screen):
        """
        Draw the widget instance to a surface using css properties.

        Always recalculate the settings, in case the style has been updated,
        or an attribute has changed that may affect the style.
        """
        style_hash = self.get_widget_instance_style_hash()
        style_info = self.game_engine.global_style_settings.get_style(**style_hash)
        self.get_widget_settings(style_info)
        self.get_outer_setting_values(screen)
        outer_dims = self.calculate_outer_dimensions()
        max_inner_dims = (screen.get_width() - outer_dims[0], screen.get_height() - outer_dims[1])
        self.get_inner_setting_values(max_inner_dims)
        self.get_color_values()
        self.draw_border(screen, outer_dims)

    def get_widget_instance_style_hash(self):
        """
        Collect widget instance style information for comparison with
        stylesheet settings.

        Subclasses should start here and add attribute matches (e.g. a
        checkbutton could match on "checked" attribute "on" or "off")
        """
        props = {
            "element_type": self.kind.name,
            "element_class": self.widget_class,
            "element_id": self.widget_id,
        }
        if self.hover:
            props["pseudo_class"] = "hover"
        return props


class WidgetObjectTypeInvalid(Exception):
    pass


class WidgetObjectType(object_type.ObjectType):

    def __init__(self, widget_name, game_engine, **kwargs):
        super(WidgetObjectType, self).__init__(widget_name, game_engine, **kwargs)
        #: Flag whether this widget type is a container for other widgets
        self.is_container = False
        #: A Rect bounding the inner portion of the widget after accounting
        #: for the margins, border size (if any), and padding
        self.inside_rect = pygame.Rect(0,0,0,0)
        self.inside_rect_calulated = False

    def make_new_instance(self, screen, settings=None, **kwargs):
        """
        Generate a new instance of the widget type in response to
            :py:meth:`~pygame_maker.actors.object_type.ObjectType.create_instance`

        :param screen: The surface the instance will be drawn upon.  The
            instance can use this surface's (often a sub-surface's) width and
            height parameters to determine child widget placement
        :type screen: :py:class:`pygame.Surface`
        :param instance_properties: A hash of settings to be applied.  See
            kwargs entry in
            :py:meth:`~pygame_maker.actors.simple_object_instance.SimpleObjectInstance.__init__`
        :type instance_properties: dict
        """
        pass

    def update(self):
        """
        Update all instances of this widget type.
        """
        pass

    def draw(self, in_event):
        """Draw all visible instances."""
        if len(self.instance_list) > 0 and self.visible:
            for inst in self.instance_list:
                if inst.parent is not None:
                    continue
                inst.draw(self.game_engine.draw_surface)
