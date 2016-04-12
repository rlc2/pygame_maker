#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker object instance class

import pygame
import math
import random
import numpy as np
from pygame_maker.support import coordinate
from pygame_maker.support import logging_object
from pygame_maker.logic.language_engine import SymbolTable


def get_vector_xy_from_speed_direction(speed, direction):
    """
    Return an x,y vector representing the given speed and angle of motion.

    :param speed: The speed component of the velocity.
    :type speed: float
    :param direction: The direction component of the velocity.
    :type direction: float
    :return: A tuple (x, y) representing the velocity
    :rtype: (float, float)
    """
    xval = speed * math.sin(direction / 180.0 * math.pi)
    yval = speed * -1 * math.cos(direction / 180.0 * math.pi)
    xy = (xval, yval)
    return np.array(xy)


def get_speed_direction_from_xy(x, y):
    """
    Return speed and direction of motion, given an x,y vector starting from 0,0

    :param x: X component of the velocity.
    :type x: float
    :param y: Y component of the velocity.
    :type y: float
    :return: A tuple (speed, direction) representing the velocity
    :rtype: (float, float)
    """
    speed = math.sqrt(x * x + y * y)
    direction = direction_from_a_to_b(np.zeros(2), (x, y))
    spdir = (speed, direction)
    return spdir


def get_radius_angle_from_xy(x, y):
    """
    Return polar coordinates from an x, y coordinate.  This is the same
    operation as converting a velocity represented as x, y into speed,
    direction.

    :param x: X coordinate
    :param y: Y coordinate
    :return: A tuple (radius, angle) representing the polar coordinate
    :rtype: (float, float)
    """
    return get_speed_direction_from_xy(x, y)


def direction_from_a_to_b(pointa, pointb):
    """
    Calculate the direction in degrees for the line connecting points a and b.

    :param pointa: A 2-element list representing the coordinate in x, y order
    :type pointa: [float, float]
    :param pointb: A 2-element list representing the coordinate in x, y order
    :type pointb: [float, float]
    :return: The angle to pointb, using pointa as the origin.
    :rtype: float
    """
    normal_vector = np.array(pointb[:2]) - np.array(pointa[:2])
    return (math.atan2(normal_vector[1], normal_vector[0]) * 180) / math.pi


class ObjectInstance(logging_object.LoggingObject,
                     pygame.sprite.DirtySprite):
    """
    Fits the purpose of pygame's Sprite class.

    Represent an instance of an ObjectType.

    An instance has:

    * position
    * speed
    * direction of motion
    * gravity
    * gravity direction
    * friction

    An instance does:

    * respond to events
    * produce collision events
    * draw itself

    As a :py:class:`pygame.sprite.DirtySprite` subclass, instances support
    dirty, blendmode, source_rect, visible, and layer attributes.

    As a subclass of LoggingObject, instances support debug(), info(),
    warning(), error(), and critical() methods.
    """

    def __init__(self, kind, screen_dims, id_, settings=None, **kwargs):
        """
        Initialize an ObjectInstance.

        :param kind: The object type of this new instance
        :type kind: :py:class:`~pygame_maker.actors.object_type.ObjectType`
        :param screen_dims: Width, height of the surface this instance will be
            drawn to.  Allows boundary collisions to be detected.
        :type screen_dims: [int, int]
        :param id\_: A unique integer ID for this instance
        :type id\_: int
        :param settings: Used along with kwargs for settings attributes
            (allows attributes to be set that have a '.' character, which
            cannot be set in kwargs).  Known attributes are the same as for
            kwargs.
        :type settings: None or dict
        :param kwargs:
            Supply alternatives to instance attributes

            * position (list of float or pygame.Rect): Upper left XY coordinate.
              If not integers, each will be rounded to the next highest
              integer [(0,0)]
            * speed (float): How many pixels (or fraction thereof) the object
              moves in each update [0.0]
            * direction (float): 0-359 degrees for direction of motion [0.0]
            * gravity (float): Strength of gravity toward gravity_direction in
              pixels/sec^2 [0.0]
            * gravity_direction (float): 0-359 degrees for direction of gravity
              vector [0.0]
            * friction (float): Strength of friction vs direction of motion in
              pixels/sec [0.0]

        """
        # call the superclass __init__
        logging_object.LoggingObject.__init__(self, type(self).__name__)
        pygame.sprite.DirtySprite.__init__(self)
        # Unique ID for this ObjectInstance
        self.inst_id = id_
        # Symbols tracked by all ObjectInstances
        self._symbols = {
            "speed": 0.0,
            "direction": 0.0,
            "gravity": 0.0,
            "gravity_direction": 0.0,
            "friction": 0.0,
            "hspeed": 0.0,
            "vspeed": 0.0,
            "position": coordinate.Coordinate(0, 0,
                                   self._update_position_x,
                                   self._update_position_y)
        }
        #: Symbol table
        self.symbols = SymbolTable()
        for sym in self._symbols.keys():
            self.symbols[sym] = self._symbols[sym]
        # Flag when methods shouldn't automatically update speed, direction
        self._delay_motion_updates = False
        #: The ObjectType this ObjectInstance belongs to
        self.kind = kind
        #: Keep a handle to the game engine for handling certain actions
        self.game_engine = kind.game_engine
        #: Keep track of the screen boundaries for collision detection
        self.screen_dims = list(screen_dims)
        # set up the Sprite/DirtySprite expected parameters
        # default visibility comes from this instance's type
        self.dirty = 0
        self._visible = False
        self.visible = kind.visible
        # copy this instance's image and Rect from the sprite resource
        #: Keep a reference to the ObjectSprite's image
        self.image = kind.get_image()
        if self.image:
            self.rect = self.image.get_rect()
            self.mask = self.kind.mask
            if self.kind.radius:
                # disk collision type; get the predefined radius for collisions
                self.radius = self.kind.radius
            self.source_rect = pygame.Rect(self.kind.bounding_box_rect)
        else:
            #: The Sprite's Rect
            self.rect = pygame.Rect(0, 0, 0, 0)
            #: The bounding box rect containing drawn pixels
            self.source_rect = pygame.Rect(0, 0, 0, 0)
        self.blendmode = 0
        # use the instance type's 'depth' parameter as the layer for this
        #  instance
        self.layer = kind.depth
        attr_values = {}
        if settings is not None:
            attr_values.update(settings)
        attr_values.update(kwargs)
        if len(attr_values) > 0:
            self._apply_kwargs(attr_values)
        # print("Initial symbols:")
        # self.symbols.dumpVars()

        self.start_position = (self.position.x, self.position.y)
        self.action_name_to_method_map = {
            'set_velocity_compass': self.set_velocity_compass,
            'move_toward_point': self.move_toward_point,
            'set_horizontal_speed': self.set_horizontal_speed,
            'set_vertical_speed': self.set_vertical_speed,
            'execute_code': self.execute_code,
            'if_variable_value': self.if_variable_value,
            'set_variable_value': self.set_variable_value,
        }
        self._code_block_id = 0
        # print("{}".format(self))

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, is_visible):
        vis = (is_visible is True)
        if vis:
            self.dirty = 2
        else:
            self.dirty = 0
        self._visible = vis

    def _change_motion_x_y(self):
        # Keep track of horizontal and vertical components of velocity.

        # Motion is represented as x and y adjustments that are made every
        # update when using the speed/direction model (as opposed to
        # manually changing the position).  Caching these values reduces the
        # number of times math functions will be called for object instances
        # with constant velocity.
        self.debug("_change_motion_x_y():")
        xadj, yadj = get_vector_xy_from_speed_direction(self.symbols['speed'],
                                                        self.symbols['direction'])
        # print("new inst {} xyadj {}, {}".format(self.inst_id, xadj, yadj))
        self.symbols['hspeed'] = xadj
        self.symbols['vspeed'] = yadj

    def _update_position_x(self):
        # Automatically called when the X coordinate of the position changes
        self.debug("_update_position_x():")
        self._round_position_x_to_rect_x()
        self.symbols['position.x'] = self.position.x

    def _update_position_y(self):
        # Automatically called when the Y coordinate of the position changes
        self.debug("_update_position_y():")
        self._round_position_y_to_rect_y()
        self.symbols['position.y'] = self.position.y

    def _round_position_x_to_rect_x(self):
        # Called when the x coordinate of the position changes, to round
        # the floating-point value to the nearest integer and place it
        # in rect.x for the draw() method.
        self.debug("_round_position_x_to_rect_x():")
        self.rect.x = math.floor(self.position.x + 0.5)

    def _round_position_y_to_rect_y(self):
        # _round_position_y_to_rect_y():
        #  Called when the y coordinate of the position changes, to round
        #  the floating-point value to the nearest integer and place it
        #  in rect.y for the draw() method.
        self.debug("_round_position_y_to_rect_y():")
        self.rect.y = math.floor(self.position.y + 0.5)

    @property
    def code_block_id(self):
        # Return a unique code block id
        self._code_block_id += 1
        return self._code_block_id

    @property
    def direction(self):
        """Direction of motion in degrees, between 0.0 and 360.0"""
        return self.symbols['direction']

    @direction.setter
    def direction(self, value):
        new_value = value
        if new_value >= 360.0:
            new_value %= 360.0
        if new_value <= -360.0:
            new_value %= 360.0
        if (new_value > -360.0) and (new_value < 0.0):
            new_value = (360.0 + new_value)
        self.symbols['direction'] = new_value
        if not self._delay_motion_updates:
            self._change_motion_x_y()

    @property
    def speed(self):
        """Speed of motion in pixels (or fractions) per frame"""
        return self.symbols['speed']

    @speed.setter
    def speed(self, value):
        self.symbols['speed'] = value
        if not self._delay_motion_updates:
            self._change_motion_x_y()

    @property
    def position(self):
        """Position of this instance.  Set a new position using an x, y list"""
        return self.symbols['position']

    @position.setter
    def position(self, value):
        if len(value) >= 2:
            self.position.x = value[0]
            self.position.y = value[1]

    @property
    def friction(self):
        """Magnitude of friction applied against motion each frame"""
        return self.symbols['friction']

    @friction.setter
    def friction(self, value):
        self.symbols['friction'] = float(value)

    @property
    def gravity(self):
        """Magnitude of gravity applied each frame"""
        return self.symbols['gravity']

    @gravity.setter
    def gravity(self, value):
        self.symbols['gravity'] = float(value)

    @property
    def gravity_direction(self):
        """Direction gravity pulls the instance in degrees"""
        return self.symbols['gravity_direction']

    @gravity_direction.setter
    def gravity_direction(self, value):
        new_value = value
        if new_value >= 360.0:
            new_value %= 360.0
        if new_value <= -360.0:
            new_value %= 360.0
        if (new_value > -360.0) and (new_value < 0.0):
            new_value = (360.0 + new_value)
        self.symbols['gravity_direction'] = new_value

    @property
    def hspeed(self):
        """Horizontal speed"""
        return self.symbols['hspeed']

    @hspeed.setter
    def hspeed(self, value):
        # skip setting motion x,y and hspeed, vspeed
        self._delay_motion_updates = True
        self.speed, self.direction = get_speed_direction_from_xy(value,
                                                                 self.vspeed)
        self._delay_motion_updates = False
        self.symbols['hspeed'] = value

    @property
    def vspeed(self):
        """Vertical speed"""
        return self.symbols['vspeed']

    @vspeed.setter
    def vspeed(self, value):
        # skip setting motion x,y and hspeed, vspeed
        self._delay_motion_updates = True
        self.speed, self.direction = get_speed_direction_from_xy(self.hspeed,
                                                                 value)
        self._delay_motion_updates = False
        self.symbols['vspeed'] = value

    def get_center_point(self):
        """
        Return the approximate center pixel coordinate of the object.

        :return: A 2-element tuple x, y of the approximate position of the
            object's center point.
        :rtype: (int, int)
        """
        self.debug("get_center_point():")
        center_xy = (self.rect.x + self.rect.width / 2.0,
                     self.rect.y + self.rect.height / 2.0)
        return center_xy

    def _apply_kwargs(self, kwargs):
        # Apply the kwargs dict mappings to the instance's properties.

        # Any keys that don't refer to built-in properties (speed, direction,
        # etc) will instead be tracked in the local symbol table to support
        # code execution actions.
        # Parameters themselves can have attributes up to 1 level, to support
        #     position.x and position.y

        # :param kwargs: A dictionary containing the new attributes to be
        #     applied
        # :type kwargs: dict
        self.debug("_apply_kwargs(kwargs={}):".format(str(kwargs)))
        relative = False
        if "relative" in kwargs.keys():
            relative = kwargs["relative"]
        for kwarg in kwargs.keys():
            if kwarg == 'relative':
                # 'relative' is not an attribute, it instead determines how the
                #  other attributes are applied.
                continue
            # Attributes can themselves have attributes, but only 1 level deep
            # is currently supported.  This facilitates setting the position.x
            #  and position.y attributes.
            attrs = kwarg.split('.')
            if hasattr(self, attrs[0]):
                new_val = kwargs[kwarg]
                if len(attrs) == 1:
                    old_val = getattr(self, kwarg)
                    if relative:
                        new_val += getattr(self, kwarg)
                    if new_val != old_val:
                        setattr(self, kwarg, new_val)
                elif len(attrs) == 2:
                    main_attr = getattr(self, attrs[0])
                    old_val = getattr(main_attr, attrs[1])
                    if relative:
                        new_val += old_val
                    if new_val != old_val:
                        setattr(main_attr, attrs[1], new_val)
            else:
                # keep track of local symbols created by code blocks
                self.symbols[kwarg] = kwargs[kwarg]

    def update(self):
        """
        Move the instance from its current position.

        Calculate the new position using current speed and direction.  Queue
        events for boundary collisions or outside-of-room positions.  Make
        friction and/or gravity changes to speed and/or direction for the next
        update().
        """
        self.debug("update():")
        event_queued = None
        if self.speed > 0.0:
            self.position[0] += self.symbols['hspeed']
            self.position[1] += self.symbols['vspeed']
            self.rect.x = int(math.floor(self.position[0] + 0.5))
            self.rect.y = int(math.floor(self.position[1] + 0.5))
            # check for boundary collisions
            # allow boundary collisions for objects completely outside
            #  the other dimension's boundaries to be ignored; this
            #  makes intersect_boundary and outside_room mutually exclusive
            in_x_bounds = (((self.rect.x + self.rect.width) >= 0) and
                           (self.rect.x <= self.screen_dims[0]))
            in_y_bounds = (((self.rect.y + self.rect.height) >= 0) and
                           (self.rect.y <= self.screen_dims[1]))
            if ((self.rect.x <= 0 <= (self.rect.x + self.rect.width)) or
                (self.rect.x <= self.screen_dims[0] <=
                 (self.rect.x + self.rect.width)) and in_y_bounds):
                # queue and handle boundary collision event (async)
                event_queued = self.kind.EVENT_NAME_OBJECT_HASH["intersect_boundary"]("intersect_boundary",
                                                                                      {"type": self.kind,
                                                                                       "instance": self})
                # print("inst {} hit x bound".format(self.inst_id))
            if ((self.rect.y <= 0 <= (self.rect.y + self.rect.height)) or
                (self.rect.y <= self.screen_dims[1] <=
                 (self.rect.y + self.rect.width)) and in_x_bounds):
                # queue and handle boundary collision event (async)
                if not event_queued:
                    event_queued = self.kind.EVENT_NAME_OBJECT_HASH["intersect_boundary"]("intersect_boundary",
                                                                                          {"type": self.kind,
                                                                                           "instance": self})
                    # print("inst {} hit y bound".format(self.inst_id))
            # check for outside room
            if ((self.rect.x > self.screen_dims[0]) or
                    ((self.rect.x + self.rect.width) < 0)):
                event_queued = self.kind.EVENT_NAME_OBJECT_HASH["outside_room"]("outside_room",
                                                                                {"type": self.kind,
                                                                                 "instance": self})
            if ((self.rect.y > self.screen_dims[1]) or
                    ((self.rect.y + self.rect.height) < 0)):
                if not event_queued:
                    event_queued = self.kind.EVENT_NAME_OBJECT_HASH["outside_room"]("outside_room",
                                                                                    {"type": self.kind,
                                                                                     "instance": self})
            self.debug("  {} inst {} new position: {} ({})".format(self.kind.name,
                                                                   self.inst_id, self.position, self.rect))
        # apply forces for next update
        self._apply_gravity()
        self._apply_friction()
        # transmit outside_room or intersect_boundary event last
        if event_queued:
            self.game_engine.event_engine.queue_event(event_queued)
            self.debug("  {} inst {} transmitting {} event".format(self.kind.name,
                                                                   self.inst_id, event_queued))
            self.game_engine.event_engine.transmit_event(event_queued.name)

    def _apply_gravity(self):
        # Adjust speed and direction using value and direction of gravity.
        self.debug("_apply_gravity():")

    def _apply_friction(self):
        # Adjust speed based on friction value.
        self.debug("_apply_friction():")
        if (self.friction > 0.0) and (self.speed > 0.0):
            new_speed = self.speed - self.friction
            if new_speed < 0.0:
                new_speed = 0.0
            self.speed = new_speed

    def aim_toward_point(self, pointxy):
        """
        Change the direction of motion toward a given point.

        :param pointxy: A 2-element list of the x, y coordinate
        :type pointxy: array-like
        """
        self.debug("aim_toward_point():")
        self.direction = direction_from_a_to_b(self.get_center_point(), pointxy)

    def set_velocity_compass(self, action):
        """
        Handle the set_velocity_compass action.

        Possible directions:

        * NONE: don't set the direction, just the speed
        * '|' separated list of possible directions to be chosen at
          random: UP, UPLEFT, UPRIGHT, RIGHT, DOWN, DOWNLEFT, DOWNRIGHT, LEFT
          (see :py:attr:`~pygame_maker.actions.action.Action.COMPASS_DIRECTIONS`)

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        """
        self.debug("set_velocity_compass(action={}):".format(action))
        # convert compass direction into degrees
        new_params = dict(action.action_data)
        new_params["direction"] = 0.0
        if new_params["compass_directions"] != "NONE":
            dirs = new_params['compass_directions'].split('|')
            dir_count = len(dirs)
            new_dir = 0
            if dir_count > 1:
                new_dir = random.randint(0, dir_count - 1)
            if dirs[new_dir] in action.COMPASS_DIRECTIONS:
                # convert direction name to degrees
                new_params["direction"] = action.COMPASS_DIRECTION_DEGREES[dirs[new_dir]]
            elif dirs[new_dir] == "STOP":
                # if stop was selected, set speed to zero
                new_params['speed'] = 0
        del(new_params["compass_directions"])
        _apply_kwargs(new_params)

    def move_toward_point(self, action):
        """
        Handle the move_toward_point action.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        """
        self.debug("move_toward_point(action={}):".format(action))
        if "destination" in action.action_data:
            self._delay_motion_updates = True
            # change direction
            self.aim_toward_point(action.action_data["destination"])
            # apply speed parameter
            self._apply_kwargs({"speed": action.action_data['speed']})
            self._delay_motion_updates = False
            self._change_motion_x_y()

    def set_horizontal_speed(self, action):
        """
        Handle the set_horizontal_speed action.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        """
        self.debug("set_horizontal_speed(action={}):".format(action))
        relative = False
        if "relative" in action.action_data:
            relative = action.action_data["relative"]
        compass_name = action.action_data["horizontal_direction"]
        if compass_name in ["LEFT", "RIGHT"]:
            speed = action.action_data["horizontal_speed"]
            direction = action.COMPASS_DIRECTION_DEGREES[compass_name]
            # horiz_vec has only x direction
            horiz_vec = get_vector_xy_from_speed_direction(speed, direction)
            new_hspeed = horiz_vec[0]
            if relative:
                new_hspeed += self.hspeed
            self.hspeed = new_hspeed

    def set_vertical_speed(self, action):
        """
        Handle the set_vertical_speed action.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        """
        self.debug("set_vertical_speed(action={}):".format(action))
        relative = False
        if "relative" in action.action_data:
            relative = action.action_data["relative"]
        compass_name = action.action_data["vertical_direction"]
        if compass_name in ["UP", "DOWN"]:
            speed = action.action_data["vertical_speed"]
            direction = action.COMPASS_DIRECTION_DEGREES[compass_name]
            # vert_vec has only y direction
            vert_vec = get_vector_xy_from_speed_direction(speed, direction)
            new_vspeed = vert_vec[1]
            if relative:
                new_vspeed += self.vspeed
            self.vspeed = new_vspeed

    def _symbol_change_callback(self, sym, new_value):
        # Callback for the SymbolTable.

        # Called whenever a symbol changes while running the language engine.

        # :param sym: The symbol's name
        # :type sym: str
        # :param new_value: The symbol's new value
        self.debug("_symbol_change_callback(sym={}, new_value={}):".format(sym,
                                                                           new_value))
        if sym == 'speed':
            self.speed = new_value
        elif sym == 'direction':
            self.direction = new_value
        elif sym == 'hspeed':
            self.hspeed = new_value
        elif sym == 'vspeed':
            self.vspeed = new_value
        elif sym == 'position.x':
            self.position.x = new_value
        elif sym == 'position.y':
            self.position.y = new_value
        elif sym == 'position':
            self.position = new_value
        elif sym == 'friction':
            self.friction = new_value
        elif sym == 'gravity_direction':
            self.gravity_direction = new_value
        elif sym == 'gravity':
            self.gravity = new_value

    def execute_code(self, action, keep_code_block=True):
        """
        Handle the execute_code action.

        Puts local variables into the symbols attribute, which is a symbol
        table. Applies any built-in local variable changes for the instance
        (speed, direction, etc.).

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        :param keep_code_block: Specify whether the code block will be re-used,
            and so shouldn't be deleted after execution
        :type keep_code_block: bool
        """
        self.debug("execute_code(action={}, keep_code_block={}):".format(action,
                                                                         keep_code_block))
        if len(action.action_data['code']) > 0:
            instance_handle_name = "obj_{}_block{}".format(self.kind.name, self.code_block_id)
            if 'language_engine_handle' not in action.runtime_data:
                action['language_engine_handle'] = instance_handle_name
                # print("action {} runtime: '{}'".format(action, action.runtime_data))
                self.game_engine.language_engine.register_code_block(
                    instance_handle_name, action.action_data['code']
                )
            local_symbols = SymbolTable(self.symbols, lambda s, v: self._symbol_change_callback(s, v))
            self.debug("{} inst {} syms before code block: {}".format(self.kind.name,
                                                                      self.inst_id,
                                                                      local_symbols.vars))
            self.game_engine.language_engine.execute_code_block(
                action['language_engine_handle'], local_symbols
            )
            self.debug("  syms after code block: {}".format(local_symbols.vars))
            if not keep_code_block:
                # support one-shot actions
                self.game_engine.language_engine.unregister_code_block(
                    action['language_engine_handle']
                )
                del(action.runtime_data['language_engine_handle'])

    def if_variable_value(self, action):
        """
        Handle the if_variable_value action.

        Makes use of both the local symbol table in self.symbols, and the
        global symbol table managed by the language engine.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        """
        self.debug("if_variable_value(action={}):".format(action))
        # look in symbol tables for the answer, local table first
        var_val = self.symbols.DEFAULT_UNINITIALIZED_VALUE
        test_result = False
        if action['variable'] in self.symbols.keys():
            var_val = self.symbols[action['variable']]
        elif action['variable'] in self.game_engine.language_engine.global_symbol_table.keys():
            var_val = self.game_engine.language_engine.global_symbol_table[action['variable']]
        if action['test'] == "equals":
            if var_val == action['value']:
                test_result = True
        if action['test'] == "not_equals":
            if var_val == action['value']:
                test_result = True
        if action['test'] == "less_than_or_equals":
            if var_val <= action['value']:
                test_result = True
        if action['test'] == "less_than":
            if var_val < action['value']:
                test_result = True
        if action['test'] == "greater_than_or_equals":
            if var_val >= action['value']:
                test_result = True
        if action['test'] == "greater_than":
            if var_val > action['value']:
                test_result = True
        self.debug("  {} inst {}: if {} {} {} is {}".format(self.kind.name,
                                                            self.inst_id, action['variable'], action['test'],
                                                            action['value'],
                                                            test_result))
        action.action_result = test_result

    def set_variable_value(self, action):
        """
        Handle the set_variable_value action.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        """
        self.debug("set_variable_value(action={}):".format(action))
        if action['is_global']:
            value_result = action.get_parameter_expression_result('value',
                                                                  self.game_engine.language_engine.global_symbol_table,
                                                                  self.game_engine.language_engine)
            self.debug("  {} inst {}: set global var {} to {}".format(self.kind.name,
                                                                      self.inst_id,
                                                                      action['variable'],
                                                                      value_result))
            self.game_engine.language_engine.global_symbol_table[action['variable']] = value_result
        else:
            value_result = action.get_parameter_expression_result('value',
                                                                  self.symbols, self.game_engine.language_engine)
            self.debug("  {} inst {}: set local var '{}' to {}".format(self.kind.name,
                                                                       self.inst_id,
                                                                       action['variable'],
                                                                       value_result))
            self.symbols[action['variable']] = value_result

    def execute_action(self, action, event):
        """
        Perform an action in an action sequence, in response to an event.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        :param event: The Event instance that triggered this method
        :type event: :py:class:`~pygame_maker.events.event.Event`
        """
        # Apply any setting names that match property names found in the
        #  action_data.  For some actions, this is enough.
        # common exceptions:
        #  apply_to: assumed to have directed the action to this instance
        #  relative: add to instead of replace property settings
        self.debug("execute_action(action={}, event={}):".format(action, event))
        action_params = {}
        # check for expressions that need to be executed
        for param in action.action_data.keys():
            if param == 'apply_to':
                continue
            action_params[param] = action.get_parameter_expression_result(
                param, self.symbols, self.game_engine.language_engine)
        if action.name in self.action_name_to_method_map.keys():
            self.action_name_to_method_map[action.name](action)
        elif action.name == "jump_to_start":
            self.position = self.start_position
        elif action.name == "reverse_horizontal_speed":
            # old_dir = self.direction
            self.direction = -self.direction
            # self.debug("Reverse hdir {} to {}".format(old_dir, self.direction))
        elif action.name == "reverse_vertical_speed":
            # old_dir = self.direction
            self.direction = 180.0 - self.direction
            # self.debug("Reverse vdir {} to {}".format(old_dir, self.direction))
        elif action.name == "destroy_object":
            # Queue the destroy event for this instance and run it, then schedule
            #  ourselves for removal from our parent object.
            self.game_engine.event_engine.queue_event(
                self.kind.EVENT_NAME_OBJECT_HASH["destroy"]("destroy", {"type": self.kind, "instance": self})
            )
            self.game_engine.event_engine.transmit_event("destroy")
            self.kind.add_instance_to_delete_list(self)
        elif action.name == "bounce_off_collider":
            # self.debug("bounce event: {}".format(event))
            if ((action_params['precision'] == 'imprecise') or ('normal' not in
                                                                event.event_params.keys())):
                self.direction = 180.0 + self.direction
            else:
                norm = np.array(event['normal'])
                # print("Check normal {}".format(norm))
                if abs(norm[0]) == abs(norm[1]):
                    self.direction = 180.0 + self.direction
                elif abs(norm[0]) > abs(norm[1]):
                    # X component is greater; reverse X
                    self.direction = -self.direction
                else:
                    # Y component is greater; reverse Y
                    self.direction = 180.0 - self.direction
        else:
            self.debug("  {} inst {} execute_action {} fell through..".format(self.kind.name,
                                                                              self.inst_id,
                                                                              action.name))
            self._apply_kwargs(action_params)

    def __repr__(self):
        return "<{} {:03d} @ {} dir {} speed {}>".format(type(self).__name__,
                                                         self.inst_id, self.position, self.direction, self.speed)
