#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker object instance class

import pygame
import math
import numpy as np
import pygame_maker_action as pygm_action
from numbers import Number

class Coordinate(object):
    def __init__(self, x=0, y=0, x_change_callback=None, y_change_callback=None):
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
        
    def __getitem__(self, itemkey):
        if itemkey == 0:
            return self.x
        elif itemkey == 1:
            return self.y
        else:
            raise IndexError("Coordinates only have indices 0 or 1")

    def __setitem__(self, itemkey, value):
        if not isinstance(value, Number):
            raise ValueError("Coordinates can only hold numbers")
        if itemkey == 0:
            self.x = value
        elif itemkey == 1:
            self.y = value
        else:
            raise IndexError("Coordinates only have indices 0 or 1")

    def __len__(self):
        return 2

    def __repr__(self):
        return "({}, {})".format(int(self.x), int(self.y))

def get_vector_xy_from_speed_direction(speed, angle):
    """
        get_vector_xy_from_speed_direction():
        Return an x,y vector representing the given speed and angle of motion.
    """
    xval = speed * math.sin(angle / 180.0 * math.pi)
    yval = speed * -1 * math.cos(angle / 180.0 * math.pi)
    xy = (xval, yval)
    return np.array(xy)

def get_speed_direction_from_vector(xyvec):
    """
        get_speed_direction_from_xy():
        Return speed and direction of motion, given an x,y vector starting from
         0,0
    """
    speed = 0.0
    direction = 0.0
    speed = math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])
    direction = direction_from_a_to_b(np.zeros(2), xyvec)
    spdir = (speed, direction)
    return spdir

def direction_from_a_to_b(pointa, pointb):
    """
        direction_from_a_to_b():
        Return the direction in degrees for the line connecting points
         a and b
        parameters:
         pointa, pointb: 2-element lists in x, y order
    """
    normal_vector = np.array(pointb[:2]) - np.array(pointa[:2])
    return (math.atan2(normal_vector[1], normal_vector[0]) * 180) / math.pi
#    x1 = pointa[0]
#    x2 = pointb[0]
#    y1 = pointa[1]
#    y2 = pointb[1]
#    x_shift = x2 - x1
#    y_shift = y2 - y1
#    return (math.atan2(y_shift, x_shift) * 180) / math.pi

class PyGameMakerObjectInstance(pygame.sprite.DirtySprite):
    """
        PyGameMakerObjectInstance class:
        Fits the purpose of pygame's Sprite class
        Represent an instance of a particular kind of object
        An instance has:
         o position
         o speed
         o direction of motion
         o gravity
         o gravity direction
         o friction
        An instance does:
         o respond to events
         o produce collision events
         o draws itself
    """
    def __init__(self, kind, screen_dims, id, **kwargs):
        """
            PyGameMakerObjectInstance.__init__():
            Constructor for object instances. As a pygame.sprite.DirtySprite
             subclass, instances support dirty, blendmode, source_rect,
             visible, and layer attributes.
            parameters:
             kind (PyGameMakerObject): The object type of this new instance
             screen_dims (list of int): Width, height of the surface this
              instance will be drawn to. Allows boundary collisions to be
              detected.
             **kwargs: Supply alternatives to instance defaults
              position (list of float or pygame.Rect): Upper left XY coordinate.
               If not integers, each will be rounded to the next highest
               integer [(0,0)]
              speed (float): How many pixels (or fraction thereof) the object
               moves in each update [0.0]
              direction (float): 0-359 degrees for direction of motion [0.0]
              gravity (float): Strength of gravity toward gravity_direction in
               pixels/sec^2 [0.0]
              gravity_direction (float): 0-359 degrees for direction of gravity
               vector [0.0]
              friction (float): Strength of friction vs direction of motion in
               pixels/sec [0.0]
        """
        pygame.sprite.DirtySprite.__init__(self)
        self.id = id
        self.symbols = {
            "speed"             : 0.0,
            "direction"         : 0.0,
            "gravity"           : 0.0,
            "gravity_direction" : 0.0,
            "friction"          : 0.0,
            "hspeed"            : 0.0,
            "vspeed"            : 0.0,
            "position"          : Coordinate(0.0, 0.0,
                                  self.round_position_x_to_rect_x,
                                  self.round_position_y_to_rect_y)
        }
        self.last_adjustment = [0.0, 0.0]
        self.motion_changed = False
        self.delay_motion_xy = False
        self.kind = kind
        self.event_engine = kind.event_engine
        self.screen_dims = list(screen_dims)
        # set up the Sprite/DirtySprite expected parameters
        # default visibility comes from this instance's type
        self.visible = kind.visible
        if self.visible:
            # instance was never drawn, consider it "dirty"
            self.dirty = 1
        else:
            self.dirty = 0
        # copy this instance's image and Rect from the sprite resource
        self.image = kind.get_image()
        if self.image:
            self.rect = self.image.get_rect()
        else:
            self.rect = pygame.Rect(0,0,0,0)
        if kind.sprite_resource:
            self.source_rect = pygame.Rect(kind.sprite_resource.bounding_box_rect)
        else:
            self.source_rect = pygame.Rect(0,0,0,0)
        self.blendmode = 0
        # use the instance type's 'depth' parameter as the layer for this
        #  instance
        self.layer = kind.depth
        # call the superclass __init__
        if kwargs:
            self.apply_kwargs(kwargs)

        self.start_position = (self.position.x, self.position.y)
        #print("{}".format(self))

    def change_motion_x_y(self):
        xadj, yadj = get_vector_xy_from_speed_direction(self.symbols['speed'],
            self.symbols['direction'])
        #print("new inst {} xyadj {}, {}".format(self.id, xadj, yadj))
        self.last_adjustment[0] = xadj
        self.last_adjustment[1] = yadj

    def round_position_x_to_rect_x(self):
        self.rect.x = math.floor(self.position.x + 0.5)

    def round_position_y_to_rect_y(self):
        self.rect.y = math.floor(self.position.y + 0.5)

    @property
    def direction(self):
        """Direction property"""
        return self.symbols['direction']

    @direction.setter
    def direction(self, value):
        new_value = value
        if (new_value >= 360.0):
            new_value %= 360.0
        if (new_value <= -360.0):
            new_value %= 360.0
        if (new_value > -360.0) and (new_value < 0.0):
            new_value = (360.0 + new_value)
        self.symbols['direction'] = new_value
        if not self.delay_motion_xy:
            self.change_motion_x_y()
        self.motion_changed = True

    @property
    def speed(self):
        return self.symbols['speed']

    @speed.setter
    def speed(self, value):
        self.symbols['speed'] = value
        if not self.delay_motion_xy:
            self.change_motion_x_y()
        self.motion_changed = True

    @property
    def position(self):
        return self.symbols['position']

    @position.setter
    def position(self, value):
        if len(value) >= 2:
            self.position.x = value[0]
            self.position.y = value[1]

    @property
    def friction(self):
        return self.symbols['friction']

    @friction.setter
    def friction(self, value):
        self.symbols['friction'] = float(value)

    @property
    def gravity(self):
        return self.symbols['gravity']

    @gravity.setter
    def gravity(self, value):
        self.symbols['gravity'] = float(value)

    @property
    def gravity_direction(self):
        return self.symbols['gravity_direction']

    @gravity_direction.setter
    def gravity_direction(self, value):
        new_value = value
        if (new_value >= 360.0):
            new_value %= 360.0
        if (new_value <= -360.0):
            new_value %= 360.0
        if (new_value > -360.0) and (new_value < 0.0):
            new_value = (360.0 + new_value)
        self.symbols['gravity_direction'] = new_value

    @property
    def hspeed(self):
        if self.motion_changed:
            motion_vec = get_vector_xy_from_speed_direction(self.speed,
                self.direction)
            self.symbols['hspeed'] = motion_vec[0]
            self.motion_changed = False
        return self.symbols['hspeed']

    @hspeed.setter
    def hspeed(self, value):
        self.delay_motion_xy = True # don't get the new x,y adjustments twice
        self.speed, self.direction = get_speed_direction_from_xy(value,
            self.vspeed)
        self.delay_motion_xy = False
        self.change_motion_x_y()
        # motion_changed gets set as a side-effect; cancel it because we
        #  already know the new value
        self.motion_changed = False
        self.symbols['hspeed'] = value

    @property
    def vspeed(self):
        if self.motion_changed:
            motion_vec = get_vector_xy_from_speed_direction(self.speed,
                self.direction)
            self.symbols['vspeed'] = motion_vec[1]
            self.motion_changed = False
        return self.symbols['vspeed']

    @vspeed.setter
    def vspeed(self, value):
        self.delay_motion_xy = True # don't get the new x,y adjustments twice
        self.speed, self.direction = get_speed_direction_from_xy(self.hspeed,
            value)
        self.delay_motion_xy = False
        self.change_motion_x_y()
        # motion_changed gets set as a side-effect; cancel it because we
        #  already know the new value
        self.motion_changed = False
        self.symbols['vspeed'] = value

    def get_instance_symbols(self):
        symbols = {}
        symbols["hspeed"] = self.hspeed
        symbols["vspeed"] = self.vspeed
        symbols["x"] = self.position[0]
        symbols["y"] = self.position[1]
        symbols["direction"] = self.direction
        symbols["visible"] = self.visible

    def center_point(self):
        center_xy = (self.rect.x + self.rect.width / 2.0,
            self.rect.y + self.rect.height / 2.0)

    def apply_kwargs(self, kwargs):
        relative = False
        if "relative" in kwargs:
            relative = kwargs["relative"]
        for kwarg in kwargs.keys():
            if hasattr(self, kwarg):
                new_val = kwargs[kwarg]
                if relative:
                    new_val += getattr(self, kwarg)
                print("apply_kwargs(): Set {} to {}".format(kwarg, new_val))
                setattr(self, kwarg, new_val)

    def update(self):
        """
            update():
            Move the instance from its current position using its speed and
            direction.
        """
        if (self.symbols['speed'] > 0.0):
            self.position[0] += self.last_adjustment[0]
            self.position[1] += self.last_adjustment[1]
            self.rect.x = int(math.floor(self.position[0] + 0.5))
            self.rect.y = int(math.floor(self.position[1] + 0.5))
            if self.visible and self.dirty == 0:
                self.dirty = 1
            # check for boundary collisions
            if ((self.rect.x <= 0) or
                ((self.rect.x + self.rect.width) >= self.screen_dims[0])):
                # queue and handle boundary collision event (async)
                self.event_engine.queue_event(
                    self.kind.EVENT_NAME_OBJECT_HASH["intersect_boundary"]("intersect_boundary", { "type": self.kind, "instance": self })
                )
                self.event_engine.transmit_event("intersect_boundary")
                print("inst {} hit x bound".format(self.id))
                # +x direction is to the right
#                dir_plus_x = ((self.direction < 180.0) and
#                    (self.direction > 0.0))
#                if (((self.rect.x <= 0) and not dir_plus_x) or
#                    (((self.rect.x + self.rect.width) >= self.screen_dims[0])
#                    and dir_plus_x)):
#                    new_action = pygm_action.PyGameMakerMotionAction("reverse_horizontal_speed")
#                    self.execute_action(new_action)
#                else:
#                    print("dir_plus_x: {} and x coord {} and dir {}".format(dir_plus_x, self.rect.x, self.direction))
                #self.speed = 0.0
            elif ((self.rect.y <= 0) or
                ((self.rect.y + self.rect.height) >= self.screen_dims[1])):
                # queue and handle boundary collision event (async)
                self.event_engine.queue_event(
                    self.kind.EVENT_NAME_OBJECT_HASH["intersect_boundary"]("intersect_boundary", { "type": self.kind, "instance": self })
                )
                self.event_engine.transmit_event("intersect_boundary")
                print("inst {} hit y bound".format(self.id))
                # +y direction is down
#                dir_plus_y = ((self.direction > 90.0) and
#                    (self.direction < 270.0))
#                if (((self.rect.y <= 0) and not dir_plus_y) or
#                    (((self.rect.y + self.rect.height) >= self.screen_dims[1])
#                    and dir_plus_y)):
#                    new_action = pygm_action.PyGameMakerMotionAction("reverse_vertical_speed")
#                    self.execute_action(new_action)
#                else:
#                    print("dir_plus_y: {} and y coord {} and dir {}".format(dir_plus_y, self.rect.y, self.direction))
            # check for outside room
            if ((self.rect.x > self.screen_dims[0]) or
                ((self.rect.x + self.rect.width) < 0)):
                self.event_engine.queue_event(
                    self.kind.EVENT_NAME_OBJECT_HASH["outside_room"]("outside_room", { "type": self.kind, "instance": self })
                    )
                self.speed = 0.0
            if ((self.rect.y > self.screen_dims[1]) or
                ((self.rect.y + self.rect.height) < 0)):
                self.event_engine.queue_event(
                    self.kind.EVENT_NAME_OBJECT_HASH["outside_room"]("outside_room", { "type": self.kind, "instance": self })
                )
                self.speed = 0.0
            #print("inst {} new position: {} ({})".format(self.id,
            #    self.position, self.rect))
        # apply forces for next update
        self.apply_gravity()
        self.apply_friction()

    def apply_gravity(self):
        """
            apply_gravity():
            Adjust speed and direction using value and direction of gravity
        """
        pass

    def apply_friction(self):
        """
            apply_friction():
            Adjust speed based on friction value
        """
        if (self.friction) > 0.0 and (self.speed > 0.0):
            new_speed = self.speed - self.friction
            if new_speed < 0.0:
                new_speed = 0.0
            self.speed = new_speed

    def aim_toward_point(self, pointxy):
        self.direction = direction_from_a_to_b(self.center_point(), pointxy)

    def execute_action(self, action):
        # apply any setting names that match property names found in the
        #  action_data. For some actions, this is enough
        # common exceptions:
        #  apply_to: assumed to have directed the action to this instance
        #  relative: add to instead of replace property settings
        relative = False
        if "relative" in action.action_data:
            relative = action.action_data["relative"]
        if action.name == "set_velocity_compass":
            # convert compass direction into degrees
            new_params = dict(action.action_data)
            new_params["direction"] = 0.0
            if new_params["compass_direction"] in action.COMPASS_DIRECTIONS:
                new_params["direction"] = action.COMPASS_DIRECTION_DEGREES[new_params["compass_direction"]]
            apply_kwargs(new_params)
        elif action.name == "move_toward_point":
            if "destination" in action.action_data:
                # change direction
                self.aim_toward_point(action.action_data["destination"])
                # apply speed parameter
                self.apply_kwargs(action.action_data)
        elif action.name == "jump_to_start":
            self.position = self.start_position
        elif action.name == "reverse_horizontal_speed":
            old_dir = self.direction
            self.direction = -self.direction
            #print("Reverse hdir {} to {}".format(old_dir, self.direction))
        elif action.name == "reverse_vertical_speed":
            old_dir = self.direction
            self.direction = 180.0 - self.direction
            #print("Reverse vdir {} to {}".format(old_dir, self.direction))
        elif action.name == "set_horizontal_speed":
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
        elif action.name == "set_vertical_speed":
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
        else:
            apply_kwargs(action.action_data)

    def __repr__(self):
        return "<{} @ {} dir {} speed {}>".format(type(self).__name__,
            self.position, self.direction, self.speed)

