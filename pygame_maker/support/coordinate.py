#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker coordinate class

from numbers import Number


class Coordinate(object):
    """
    Record an x,y location.

    Allows for running callback methods when x and/or y are changed.
    """
    def __init__(self, x=0, y=0, x_change_callback=None, y_change_callback=None):
        """
        Store an x, y coordinate.

        :param x: X component
        :type x: int | float
        :param y: Y component
        :type y: int | float
        :param x_change_callback: A callable to execute when the X component
            changes
        :type x_change_callback: callable
        :param y_change_callback: A callable to execute when the Y component
            changes
        :type y_change_callback: callable
        """
        self._x = x
        self._y = y
        self.x_callback = x_change_callback
        self.y_callback = y_change_callback

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        if self.x_callback:
            self.x_callback()

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        if self.y_callback:
            self.y_callback()

    def copy(self):
        return Coordinate(self.x, self.y, self.x_callback, self.y_callback)

    def __getitem__(self, itemkey):
        """
        Support index form coordinate[0] for x or coordinate[1] for y.

        :param itemkey: Must be 0 or 1
        :type itemkey: int
        :raise: IndexError if itemkey is not 0 or 1
        :return: The value of coordinate[0] or coordinate[1]
        :rtype: int | float
        """
        if itemkey == 0:
            return self.x
        elif itemkey == 1:
            return self.y
        else:
            raise IndexError("Coordinates only have indices 0 or 1")

    def __setitem__(self, itemkey, value):
        """
        Support index form coordinate[0] for x or coordinate[1] for y.

        :param itemkey: Must be 0 or 1
        :type itemkey: int
        :param value: New value for coordinate 0 or 1
        :type value: int | float
        :raise: ValueError if value is not a Number
        :raise: IndexError if itemkey is not 0 or 1
        """
        if not isinstance(value, Number):
            raise ValueError("Coordinates can only hold numbers")
        if itemkey == 0:
            self.x = value
        elif itemkey == 1:
            self.y = value
        else:
            raise IndexError("Coordinates only have indices 0 or 1")

    def __len__(self):
        """A coordinate always has 2 items: x and y."""
        return 2

    def __eq__(self, other):
        return ((self.x == other.x) and (self.y == other.y))

    def __repr__(self):
        return "({:d}, {:d})".format(int(self.x), int(self.y))
