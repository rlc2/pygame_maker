"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Pygame maker color module.
"""

import math
import pygame


def normalize_alpha_byte_value(alpha):
    """Normalize 0-255 alpha byte value to a float between 0.0 and 1.0."""
    return alpha * (1.0 / 255.0)

def byte_value_from_norm_alpha(normalized_alpha):
    """Convert normalized alpha value to byte value."""
    return int(math.floor(normalized_alpha * 255.0 + 0.5))


class ColorException(Exception):
    pass


class Color(object):
    """
    Initialize a color value.

    Colors can be specified in the following ways:

    * A known color name, e.g. "red"
    * '#' followed by a 6-digit hex color value, e.g. "#00FF00" (add 2 digits
      to specify alpha)
    * a 3-tuple containing R, G, B values
    * a 4-tuple containing R, G, B, A values

    Colors can be accessed in the following ways:

    * as a 3-tuple containing R, G, B values
    * a 4-tuple containing R, G, B, A values
    * the red, green, blue, or alpha values individually

    """
    # support color names not listed in pygame.colordict
    ADDITIONAL_COLORS = {
        "aqua": "#00ffff",
        "crimson": "#dc143c",
        "fuchsia": "#ff00ff",
        "indigo": "#4b0082",
        "lime": "#00ff00",
        "olive": "#808000",
        "rebeccapurple": "#663399",
        "silver": "#c0c0c0",
        "teal": "#008080",
    }
    all_known_colors = []

    @classmethod
    def is_known_color(cls, color_name):
        """Determine whether a given color name is known."""
        if len(cls.all_known_colors) == 0:
            cls.all_known_colors = list(pygame.colordict.THECOLORS.keys()) + list(cls.ADDITIONAL_COLORS.keys())
        return color_name.lower() in cls.all_known_colors

    def __init__(self, *params):
        """
        Initialize a new Color.

        The color can be specified as:
        * a color name
        * a 3-tuple of R, G, and B values
        * a 4-tuple of R, G, B, and A values
        * by a string #RRGGBB, as in HTML (2 additional alpha digits can be
          appended)

        This class wraps pygame.Color, until such time as it is possible to
        subclass pygame.Color without crashing the script with an uncatchable
        ValueError when unknown color names are specified.

        :param params: Contains one of the following:
            * A string containing a color name
            * A string containing #RRGGBB (optionally with alpha digits)
            * A 3-element list specifying red, green, and blue values
            * A 4-element list specifying red, green, blue and alpha values
            * Individual color component values as arguments instead of in
              a list
        """
        color_str = params[0]
        self.color = None
        if params[0] in list(self.ADDITIONAL_COLORS.keys()):
            color_str = self.ADDITIONAL_COLORS[params[0]]
            # print("Passing named color {} as {} to pygame.Color".format(params[0], color_str))
            self.color = pygame.Color(color_str)
        elif not isinstance(params[0], str):
            # accept a single list as the first parameter
            clist = list(params[0])
            if len(clist) >= 3:
                self.color = pygame.Color(*clist)
        else:
            self.color = pygame.Color(*params)

    @property
    def red(self):
        """Get and set the red component of the color."""
        return self.color.r

    @red.setter
    def red(self, red):
        self.color.r = red

    @property
    def green(self):
        """Get and set the green component of the color."""
        return self.color.g

    @green.setter
    def green(self, green):
        self.color.g = green

    @property
    def blue(self):
        """Get and set the blue component of the color."""
        return self.color.b

    @blue.setter
    def blue(self, blue):
        self.color.b = blue

    @property
    def alpha(self):
        """Get and set the alpha component of the color."""
        return self.color.a

    @alpha.setter
    def alpha(self, alpha):
        self.color.a = alpha

    @property
    def rgb(self):
        """Get the color as a 3-tuple of R, G, B values"""
        return self.color.r, self.color.g, self.color.b

    @property
    def rgba(self):
        """Get the color as a 4-tuple of R, G, B, A values"""
        return self.color.r, self.color.g, self.color.b, self.color.a

    def __repr__(self):
        return "Color <r={} g={} b={} a={}>".format(self.red, self.green, self.blue, self.alpha)

