#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker color

import re

class PyGameMakerColorException(object):
    pass

class PyGameMakerColor(object):
    COLOR_STRING_RE=re.compile("#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})")
    def __init__(self, color):
        self.color = (0,0,0)
        self.red = 0
        self.green = 0
        self.blue = 0
        if isinstance(color, str):
            # accept background colors in #RRGGBB format
            minfo = self.COLOR_STRING_RE.match(color)
            if minfo:
                self.red = int(minfo.group(1), base=16)
                self.green = int(minfo.group(2), base=16)
                self.blue = int(minfo.group(3), base=16)
                self.color = (self.red, self.green, self.blue)
            else:
                raise(PyGameMakerColorException("{}: Supplied background_color '{}' not recognized (supply a 3-item list or #RRGGBB string)".format(type(self).__name__, color)))
        else:
            clist = list(color)
            if len(clist) >= 3:
                self.red = clist[0]
                self.green = clist[1]
                self.blue = clist[2]
                self.color = (self.red, self.green, self.blue)
            else:
                raise(PyGameMakerColorException("{}: Supplied background_color '{}' not recognized (supply a 3-item list or #RRGGBB string)".format(type(self).__name__, color)))

