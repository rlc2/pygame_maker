#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker object instance class

import pygame
import math

def get_vector_xy(speed, angle):
    xval = speed * math.sin(angle / 180.0 * math.pi)
    yval = speed * -1 * math.cos(angle / 180.0 * math.pi)
    xy = (xval, yval)
    return xy

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
    MINIMUM_FRACTION = 1.0e-4
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
        self.speed = 0.0
        self._direction = 0.0
        self.gravity = 0.0
        self.gravity_direction = 0.0
        self.friction = 0.0
        self.last_vector = [0.0, 0.0]
        self.last_adjustment = [0.0, 0.0]
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
        self.position = [0.0, 0.0]
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
            for arg in kwargs:
                if arg == "position":
                    # position should either be a tuple (x,y) or a pygame Rect
                    pos = list(kwargs["position"])
                    if len(pos) >= 2:
                        #print("Set position to {}".format(pos))
                        self.position[0] = pos[0]
                        self.position[1] = pos[1]
                        self.rect.x = math.floor(pos[0] + 0.5)
                        self.rect.y = math.floor(pos[1] + 0.5)
                if arg == "speed":
                    self.speed = math.fabs(float(kwargs["speed"]))
                if arg == "direction":
                    self.direction = float(kwargs["direction"])
                    # restrict direction between 0.0 and 360.0 degrees
                if arg == "gravity":
                    self.gravity = float(kwargs["gravity"])
                if arg == "gravity_direction":
                    self.gravity_direction = float(kwargs["gravity_direction"])
                    # restrict gravity direction between 0.0 and 360.0 degrees
                    if (self.gravity_direction >= 360.0):
                        self.gravity_direction %= 360.0
                    if (self.gravity_direction <= -360.0):
                        self.gravity_direction %= 360.0
                    if ((self.gravity_direction > -360.0) and
                        (self.gravity_direction < 0.0)):
                        self.gravity_direction = (360.0 +
                            self.gravity_direction)
                if arg == "friction":
                    self.friction = float(kwargs["friction"])
        self.start_position = (self.position[0], self.position[1])
        #print("{}".format(self))

    @property
    def direction(self):
        """Direction property"""
        return self._direction

    @direction.setter
    def direction(self, value):
        new_value = value
        if (new_value >= 360.0):
            new_value %= 360.0
        if (new_value <= -360.0):
            new_value %= 360.0
        if (new_value > -360.0) and (new_value < 0.0):
            new_value = (360.0 + new_value)
        self._direction = new_value

    def update(self):
        """
            update():
            Move the instance from its current position using its speed and
            direction.
        """
        # handle the simple cases
        if (self.speed > 0.0):
            xadj = 0.0
            yadj = 0.0
            if (self.last_vector == [self.speed, self.direction]):
                # no need to calculate, if the motion vector didn't change
                xadj = self.last_adjustment[0]
                yadj = self.last_adjustment[1]
            else:
                xadj, yadj = get_vector_xy(self.speed, self.direction)
                print("new inst {} xyadj {}, {}".format(self.id, xadj, yadj))
                self.last_adjustment[0] = xadj
                self.last_adjustment[1] = yadj
            self.position[0] += xadj
            self.position[1] += yadj
            self.rect.x = int(math.floor(self.position[0] + 0.5))
            self.rect.y = int(math.floor(self.position[1] + 0.5))
            if self.visible and self.dirty == 0:
                self.dirty = 1
            # check for boundary collisions
            if ((self.rect.x <= 0) or
                ((self.rect.x + self.rect.width) >= self.screen_dims[0])):
                # queue boundary collision event
                self.event_engine.queue_event(
                    self.kind.EVENT_NAME_OBJECT_HASH["intersect_boundary"]("intersect_boundary", { "type": self.kind, "instance": self })
                )
                print("inst {} hit x bound".format(self.id))
                self.speed = 0.0
            elif ((self.rect.y <= 0) or
                ((self.rect.y + self.rect.height) >= self.screen_dims[1])):
                # queue boundary collision event
                self.event_engine.queue_event(
                    self.kind.EVENT_NAME_OBJECT_HASH["intersect_boundary"]("intersect_boundary", { "type": self.kind, "instance": self })
                )
                print("inst {} hit y bound".format(self.id))
                self.speed = 0.0
            # check for outside room
            if ((self.rect.x > self.screen_dims[0]) or
                ((self.rect.x + self.rect.width) < 0)):
                self.event_engine.queue_event(
                    self.kind.EVENT_NAME_OBJECT_HASH["outside_room"]("outside_room", { "type": self.kind, "instance": self })
                    )
            if ((self.rect.y > self.screen_dims[1]) or
                ((self.rect.y + self.rect.height) < 0)):
                self.event_engine.queue_event(
                    self.kind.EVENT_NAME_OBJECT_HASH["outside_room"]("outside_room", { "type": self.kind, "instance": self })
                )
            #print("inst {} new position: {} ({})".format(self.id,
            #    self.position, self.rect))
        # apply forces for next update
        self.apply_gravity()
        self.apply_friction()
        self.last_vector[0] = self.speed
        self.last_vector[1] = self.direction

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

    def __repr__(self):
        return "<{} @ {},{} dir {} speed {}>".format(type(self).__name__,
            int(self.position[0]), int(self.position[1]), self.direction,
            self.speed)

