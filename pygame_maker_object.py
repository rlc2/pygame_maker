#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker object resource

# objects have:
#  sprite reference
#  depth? (numeric)
#  parent? (another object?)
#  mask? (has something to do with the sprite, can use a different sprite)
#  visible flag
#  persistent flag
#  solid flag (for solid stationary objects, e.g. platform
#  physics flag
#  events! (need another class for this?)
#   create. normal step. draw.
#   events can be modified. edited (appears to just add a run code action), or
#    deleted.
#  actions! (""?)
#   things that happen in response to events
#   change direction. jump to a location. run code. affect score/lives.
#   actions can be chained together
#   actions can be "questions". depending on the answer, the following action(s)
#    can be taken


