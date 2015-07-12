#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker object instance class

import pygame
import math
import random
import numpy as np
import pygame_maker_action as pygm_action
from pygame_maker_language_engine import PyGameMakerSymbolTable
from numbers import Number

class Coordinate(object):
    """
        Coordinate class:
        This class records an x,y location, and allows for running callback
         methods when x and/or y are changed.
    """
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
        """
            __getitem__():
            Support index form coordinate[0] for x or coordinate[1] for y.
        """
        if itemkey == 0:
            return self.x
        elif itemkey == 1:
            return self.y
        else:
            raise IndexError("Coordinates only have indices 0 or 1")

    def __setitem__(self, itemkey, value):
        """
            __setitem__():
            Support index form coordinate[0] for x or coordinate[1] for y.
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
        """
            __len__():
            A coordinate always has 2 items: x and y.
        """
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

def get_speed_direction_from_xy(x,y):
    """
        get_speed_direction_from_xy():
        Return speed and direction of motion, given an x,y vector starting from
         0,0
    """
    speed = 0.0
    direction = 0.0
    speed = math.sqrt(x * x + y * y)
    direction = direction_from_a_to_b(np.zeros(2), (x,y))
    spdir = (speed, direction)
    return spdir

def get_radius_angle_from_xy(x,y):
    return get_speed_direction_from_xy(x,y)

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
        self._symbols = {
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
        self.symbols = PyGameMakerSymbolTable()
        for sym in self._symbols.keys():
            self.symbols[sym] = self._symbols[sym]
        self.last_adjustment = [0.0, 0.0]
        self.delay_motion_updates = False
        self.kind = kind
        self.game_engine = kind.game_engine
        self.screen_dims = list(screen_dims)
        # set up the Sprite/DirtySprite expected parameters
        # default visibility comes from this instance's type
        self.visible = kind.visible
        # copy this instance's image and Rect from the sprite resource
        self.image = kind.get_image()
        if self.image:
            self.rect = self.image.get_rect()
            self.mask = self.kind.mask
            if self.kind.radius:
                # disk collision type; get the predefined radius for collisions
                self.radius = self.kind.radius
            self.source_rect = pygame.Rect(self.kind.bounding_box_rect)
        else:
            self.rect = pygame.Rect(0,0,0,0)
            self.source_rect = pygame.Rect(0,0,0,0)
        self.blendmode = 0
        # use the instance type's 'depth' parameter as the layer for this
        #  instance
        self.layer = kind.depth
        # call the superclass __init__
        if kwargs:
            self.apply_kwargs(kwargs)
        #print("Initial symbols:")
        #self.symbols.dumpVars()

        self.start_position = (self.position.x, self.position.y)
        self.action_name_to_method_map={
            'set_velocity_compass': self.set_velocity_compass,
            'move_toward_point': self.move_toward_point,
            'set_horizontal_speed': self.set_horizontal_speed,
            'set_vertical_speed': self.set_vertical_speed,
            'execute_code': self.execute_code,
            'if_variable_value': self.if_variable_value,
            'set_variable_value': self.set_variable_value,
        }
        self._code_block_id = 0
        #print("{}".format(self))

    @property
    def visible(self):
        return(self._visible)

    @visible.setter
    def visible(self, is_visible):
        vis = (is_visible == True)
        if vis:
            self.dirty = 2
        else:
            self.dirty = 0
        self._visible = vis

    def change_motion_x_y(self):
        """
            change_motion_x_y():
            Motion is represented as x and y adjustments that are made every
             update when using the speed/direction model (as opposed to
             manually changing the position). Caching these values reduces the
             number of times math functions will be called for object instances
             with constant velocity.
        """
        xadj, yadj = get_vector_xy_from_speed_direction(self.symbols['speed'],
            self.symbols['direction'])
        #print("new inst {} xyadj {}, {}".format(self.id, xadj, yadj))
        self.last_adjustment[0] = xadj
        self.last_adjustment[1] = yadj

    def change_hspeed_vspeed(self):
        """
            change_hspeed_vspeed():
            Horizontal and vertical speed components can be read or changed
             directly. These are cached to reduce the number of times math
             functions will be called for object instances with constant
             velocity.
        """
        motion_vec = get_vector_xy_from_speed_direction(self.speed,
            self.direction)
        self.symbols['hspeed'], self.symbols['vspeed'] = motion_vec

    def round_position_x_to_rect_x(self):
        """
            round_position_x_to_rect_x():
            Called when the x coordinate of the position changes, to round
             the floating-point value to the nearest integer and place it
             in rect.x for the draw() method.
        """
        self.rect.x = math.floor(self.position.x + 0.5)

    def round_position_y_to_rect_y(self):
        """
            round_position_y_to_rect_y():
            Called when the y coordinate of the position changes, to round
             the floating-point value to the nearest integer and place it
             in rect.y for the draw() method.
        """
        self.rect.y = math.floor(self.position.y + 0.5)

    @property
    def code_block_id(self):
        """Return a unique code block id"""
        self._code_block_id += 1
        return self._code_block_id

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
        if not self.delay_motion_updates:
            self.change_motion_x_y()
            self.change_hspeed_vspeed()

    @property
    def speed(self):
        """Speed property"""
        return self.symbols['speed']

    @speed.setter
    def speed(self, value):
        self.symbols['speed'] = value
        if not self.delay_motion_updates:
            self.change_motion_x_y()
            self.change_hspeed_vspeed()

    @property
    def position(self):
        """Position property"""
        return self.symbols['position']

    @position.setter
    def position(self, value):
        if len(value) >= 2:
            self.position.x = value[0]
            self.position.y = value[1]

    @property
    def friction(self):
        """Friction property"""
        return self.symbols['friction']

    @friction.setter
    def friction(self, value):
        self.symbols['friction'] = float(value)

    @property
    def gravity(self):
        """Gravity property"""
        return self.symbols['gravity']

    @gravity.setter
    def gravity(self, value):
        self.symbols['gravity'] = float(value)

    @property
    def gravity_direction(self):
        """Gravity direction property"""
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
        """Horizontal speed property"""
        return self.symbols['hspeed']

    @hspeed.setter
    def hspeed(self, value):
        # skip setting motion x,y and hspeed, vspeed
        self.delay_motion_updates = True
        self.speed, self.direction = get_speed_direction_from_xy(value,
            self.vspeed)
        self.delay_motion_updates = False
        self.change_motion_x_y()
        self.symbols['hspeed'] = value

    @property
    def vspeed(self):
        """Vertical speed property"""
        return self.symbols['vspeed']

    @vspeed.setter
    def vspeed(self, value):
        # skip setting motion x,y and hspeed, vspeed
        self.delay_motion_updates = True
        self.speed, self.direction = get_speed_direction_from_xy(self.hspeed,
            value)
        self.delay_motion_updates = False
        self.change_motion_x_y()
        self.symbols['vspeed'] = value

    def get_center_point(self):
        """
            get_center_point():
            Return the approximate center pixel coordinate of the object.
        """
        center_xy = (self.rect.x + self.rect.width / 2.0,
            self.rect.y + self.rect.height / 2.0)

    def apply_kwargs(self, kwargs):
        """
            apply_kwargs():
            Apply the kwargs dict mappings to the instance's properties. Any
             keys that don't refer to built-in properties (speed, direction,
             etc) will instead be tracked in the local symbol table to support
             code execution actions.
        """
        relative = False
        if "relative" in kwargs.keys():
            relative = kwargs["relative"]
        for kwarg in kwargs.keys():
            if kwarg == 'relative':
                continue
            if hasattr(self, kwarg):
                new_val = kwargs[kwarg]
                if relative:
                    new_val += getattr(self, kwarg)
                #print("apply_kwargs(): Set {} to {}".format(kwarg, new_val))
                setattr(self, kwarg, new_val)
            else:
                # keep track of local symbols created by code blocks
                self.symbols[kwarg] = kwargs[kwarg]

    def update(self):
        """
            update():
            Move the instance from its current position using its speed and
             direction. Queue events for boundary collisions or outside-of-room
             positions. Make friction and/or gravity changes to speed and/or
             direction for the next update().
        """
        event_queued = None
        if (self.speed > 0.0):
            self.position[0] += self.last_adjustment[0]
            self.position[1] += self.last_adjustment[1]
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
                event_queued = self.kind.EVENT_NAME_OBJECT_HASH["intersect_boundary"]("intersect_boundary", { "type": self.kind, "instance": self })
                #print("inst {} hit x bound".format(self.id))
            if ((self.rect.y <= 0 <= (self.rect.y + self.rect.height)) or
                (self.rect.y <= self.screen_dims[1] <=
                (self.rect.y + self.rect.width)) and in_x_bounds):
                # queue and handle boundary collision event (async)
                if not event_queued:
                    event_queued = self.kind.EVENT_NAME_OBJECT_HASH["intersect_boundary"]("intersect_boundary", { "type": self.kind, "instance": self })
                #print("inst {} hit y bound".format(self.id))
            # check for outside room
            if ((self.rect.x > self.screen_dims[0]) or
                ((self.rect.x + self.rect.width) < 0)):
                event_queued = self.kind.EVENT_NAME_OBJECT_HASH["outside_room"]("outside_room", { "type": self.kind, "instance": self })
            if ((self.rect.y > self.screen_dims[1]) or
                ((self.rect.y + self.rect.height) < 0)):
                if not event_queued:
                    event_queued = self.kind.EVENT_NAME_OBJECT_HASH["outside_room"]("outside_room", { "type": self.kind, "instance": self })
            #print("inst {} new position: {} ({})".format(self.id,
            #    self.position, self.rect))
        # apply forces for next update
        self.apply_gravity()
        self.apply_friction()
        # transmit outside_room or intersect_boundary event last
        if event_queued:
            self.game_engine.event_engine.queue_event(event_queued)
            #print("{} transmitting {} event".format(self, event_queued))
            self.game_engine.event_engine.transmit_event(event_queued.event_name)

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
        """
            aim_toward_point():
            Given an xy iteratable, change the direction of motion toward the
             given point.
        """
        self.direction = direction_from_a_to_b(self.get_center_point(), pointxy)

    def set_velocity_compass(self, action):
        """
            set_velocity_compass():
            Handle the set_velocity_compass action.
            Possible directions:
            NONE: don't set the direction, just the speed
            -or- '|' separated list of possible directions to be chosen at
             random: UP, UPLEFT, UPRIGHT, RIGHT, DOWN, DOWNLEFT, DOWNRIGHT, LEFT
        """
        # convert compass direction into degrees
        new_params = dict(action.action_data)
        new_params["direction"] = 0.0
        if new_params["compass_directions"] != "NONE":
            dirs = new_params['compass_directions'].split('|')
            dir_count = len(dirs)
            new_dir = 0
            if dir_count > 1:
                new_dir = random.randint(0, dir_count-1)
            if dirs[new_dir] in action.COMPASS_DIRECTIONS:
                # convert direction name to degrees
                new_params["direction"] = action.COMPASS_DIRECTION_DEGREES[dirs[new_dir]]
            elif dirs[new_dir] == "STOP":
                # if stop was selected, set speed to zero
                new_params['speed'] = 0
        del(new_params["compass_directions"])
        apply_kwargs(new_params)

    def move_toward_point(self, action):
        """
            move_toward_point():
            Handle the move_toward_point action.
        """
        if "destination" in action.action_data:
            self.delay_motion_updates = True
            # change direction
            self.aim_toward_point(action.action_data["destination"])
            # apply speed parameter
            self.apply_kwargs({"speed": action.action_data['speed']})
            self.delay_motion_updates = False
            self.change_motion_x_y()
            self.change_hspeed_vspeed()

    def set_horizontal_speed(self, action):
        """
            set_horizontal_speed():
            Handle the set_horizontal_speed action.
        """
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
            set_vertical_speed():
            Handle the set_vertical_speed action.
        """
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

    def execute_code(self, action):
        """
            execute_code():
            Handle the execute_code action. Puts local variables into the
             symbols attribute, which is a symbol table. Applies any built-in
             local variable changes for the instance (speed, direction, etc.).
        """
        if (len(action.action_data['code']) > 0):
            instance_handle_name = "obj{}.block{}".format(self.kind.name, self.code_block_id)
            if not 'language_engine_handle' in action.runtime_data:
                action.action_data['language_engine_handle'] = self.game_engine.language_engine.register_code_block(
                    instance_handle_name, action.action_data['code']
                )
            local_symbols = PyGameMakerSymbolTable(self.symbols)
            self.game_engine.language_engine.execute_code_block(
                action.action_data['language_engine_handle'], local_symbols
            )
            # apply any local variables contributed by the code block
            self.apply_kwargs(dict(local_symbols.vars))

    def if_variable_value(self, action):
        """
            if_variable_value():
            Handle the if_variable_value action. Makes use of both the local
             symbol table in self.symbols, and the global symbol table managed
             by the language engine.
        """
        # look in symbol tables for the answer, local table first
        var_val = self.symbols.DEFAULT_UNINITIALIZED_VALUE
        test_result = False
        if action['variable'] in self.symbols.keys():
            var_val = self.symbols[action['variable']]
        elif action['variable'] in self.game_engine.language_engine.global_symbol_table.keys():
            var_val = self.game_engine.language_engine.global_symbol_table[action['variable']]
        if action['test'] == "equals":
            if action['value'] == var_val:
                test_result = True
        if action['test'] == "not_equals":
            if action['value'] != var_val:
                test_result = True
        if action['test'] == "less_than_or_equals":
            if action['value'] <= var_val:
                test_result = True
        if action['test'] == "less_than":
            if action['value'] < var_val:
                test_result = True
        if action['test'] == "greater_than_or_equals":
            if action['value'] >= var_val:
                test_result = True
        if action['test'] == "greater_than":
            if action['value'] > var_val:
                test_result = True
        action.action_result = test_result

    def set_variable_value(self, action):
        """
            set_variable_value():
            Handle the set_variable_value action.
        """
        if action['global']:
            self.game_engine.language_engine.global_symbol_table[action['variable']] = action['value']
        else:
            self.symbols[action['variable']] = action['value']

    def execute_action(self, action):
        """
            execute_action():
            Perform the actions instances can do.
        """
        # apply any setting names that match property names found in the
        #  action_data. For some actions, this is enough
        # common exceptions:
        #  apply_to: assumed to have directed the action to this instance
        #  relative: add to instead of replace property settings
        kwargs = dict(action.action_data)
        del(kwargs['apply_to'])
        if action.name in self.action_name_to_method_map.keys():
            self.action_name_to_method_map[action.action_name](action)
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
        elif action.name == "destroy_object":
            # queue the destroy event for this instance and run it. then remove
            #  ourselves from our parent object
            self.game_engine.event_engine.queue_event(
                self.kind.EVENT_NAME_OBJECT_HASH["destroy"]("destroy", { "type": self.kind, "instance": self })
            )
            self.game_engine.event_engine.transmit_event("destroy")
            self.kind.add_instance_to_delete_list(self)
        else:
            apply_kwargs(kwargs)

    def __repr__(self):
        return "<{} {:03d} @ {} dir {} speed {}>".format(type(self).__name__,
            self.id, self.position, self.direction, self.speed)

