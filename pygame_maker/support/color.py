#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker color

import re


class ColorException(Exception):
    pass


class Color(object):
    """
    Wrap a color value.

    Colors can be accessed either as a 3-tuple containing R, G, B values, or by
    the red, green, or blue values directly.
    """
    COLOR_STRING_RE = re.compile("#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})")

    def __init__(self, color):
        """
        Initialize a new Color.

        The color can be specified either as a 3-tuple of R, G, and B values,
        or by a string #RRGGBB, as in HTML.

        :param color: A string or 3-element list specifying red, green, and
            blue values
        :type color: str | 3-element array-like
        """
        #: The red component
        self.red = 0
        #: The green component
        self.green = 0
        #: The blue component
        self.blue = 0
        if isinstance(color, str):
            # accept background colors in #RRGGBB format
            minfo = self.COLOR_STRING_RE.match(color)
            if minfo:
                self.red = int(minfo.group(1), base=16)
                self.green = int(minfo.group(2), base=16)
                self.blue = int(minfo.group(3), base=16)
            else:
                raise(ColorException("{}: Supplied color '{}' not recognized (supply a 3-item list or #RRGGBB string)".format(
                    type(self).__name__, color)))
        else:
            clist = list(color)
            if len(clist) >= 3:
                self.red = clist[0]
                self.green = clist[1]
                self.blue = clist[2]
            else:
                raise(ColorException("{}: Supplied color '{}' not recognized (supply a 3-item list or #RRGGBB string)".format(
                    type(self).__name__, color)))

    @property
    def color(self):
        """The color as a 3-tuple of R, G, B values"""
        return self.red, self.green, self.blue
