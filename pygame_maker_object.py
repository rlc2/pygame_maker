#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker object resource

import pygame
import re
import math
import yaml
import pygame_maker_event as pygm_event
import pygame_maker_action as pygm_action
import pygame_maker_sprite as pygm_sprite
import pygame_maker_event_action_sequence as pygm_sequence

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
        pygame.sprite.DirtySprite.__init__(self)
        self.id = id
        self.speed = 0.0
        self.direction = 0.0
        self.gravity = 0.0
        self.gravity_direction = 0.0
        self.friction = 0.0
        self.last_vector = [0.0, 0.0]
        self.last_adjustment = [0.0, 0.0]
        self.kind = kind
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
                        print("Set position to {}".format(pos))
                        self.position[0] = pos[0]
                        self.position[1] = pos[1]
                        self.rect.x = math.floor(pos[0] + 0.5)
                        self.rect.y = math.floor(pos[1] + 0.5)
                if arg == "speed":
                    self.speed = math.fabs(float(kwargs["speed"]))
                if arg == "direction":
                    self.direction = float(kwargs["direction"])
                    # restrict direction between 0.0 and 360.0 degrees
                    if (self.direction >= 360.0):
                        self.direction %= 360.0
                    if (self.direction <= -360.0):
                        self.direction %= 360.0
                    if (self.direction > -360.0) and (self.direction < 0.0):
                        self.direction = (360.0 + self.direction)
                if arg == "gravity":
                    self.gravity = float(kwargs["gravity"])
                if arg == "gravity_direction":
                    self.gravity_direction = float(kwargs["gravity_direction"])
                    # restrict gravity direction between 0.0 and 360.0 degrees
                    if (self.gravity_direction >= 360.0):
                        self.gravity_direction %= 360.0
                    if (self.gravity_direction <= -360.0):
                        self.gravity_direction %= 360.0
                    if (self.gravity_direction > -360.0) and
                        (self.gravity_direction < 0.0):
                        self.gravity_direction = (360.0 +
                            self.gravity_direction)
                if arg == "friction":
                    self.friction = float(kwargs["friction"])
        print("obj {} pos: {} ({})".format(self.id, self.position, self.rect))
        print("obj {} speed: {}, dir: {}".format(self.id, self.speed, self.direction))

    def update(self):
        """
            update():
            Move the instance from its current position using its speed and
            direction.
            Expected args:
                screen: a reference to the surface that will be drawn onto,
                    to check for boundary collisions
                event_manager: a reference to the event manager for generating
                    any events
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
                # @@@ queue boundary collision
                print("inst {} hit x bound".format(self.id))
                self.speed = 0.0
            elif ((self.rect.y <= 0) or
                ((self.rect.y + self.rect.height) >= self.screen_dims[1])):
                # @@@ queue boundary collision
                print("inst {} hit y bound".format(self.id))
                self.speed = 0.0
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

class PyGameMakerObjectException(Exception):
    pass

class PyGameMakerObject(object):
    """
        pygame maker objects have:
        o sprite reference
        o depth? (Z dimension?) (numeric)
        o parent? (another object?)
        o collision mask (uses sprite reference, can be a different sprite)
        o visible flag
        o persistent flag?
        o solid flag (for solid stationary objects, e.g. platform)
        o physics flag
        o events!
          * ex: create. normal step. draw.
          * events can be modified, edited (appears to just add a run code
            action), or deleted.
          * actions!
            - things that happen in response to events
            - change direction. jump to a location. run code. affect
              score/lives.  play a sound.
            - actions can be chained together
            - actions can be "questions". depending on the answer, the following
              action(s) can be taken
        Objects, like classes, are instantiated within the game.
         There can be many instances of a particular kind of object.
    """
    DEFAULT_OBJECT_PREFIX="obj_"

    def __init__(self, object_name=None, **kwargs):

        if object_name:
            self.name = object_name
        else:
            self.name = self.DEFAULT_OBJECT_PREFIX
        self.sprite_resource = None
        self.mask = None
        self.visible = True
        self.solid = False
        self.depth = 0
        self.group = pygame.sprite.LayeredDirty()
        self.events = {}
        self.id = 0
        if kwargs:
            for kw in kwargs:
                if "visible" in kwargs:
                    self.visible = (kwargs["visible"] == True)
                if "solid" in kwargs:
                    self.solid = (kwargs["solid"] == True)
                if "depth" in kwargs:
                    self.depth = int(kwargs["depth"])
                if "sprite" in kwargs:
                    if not (isinstance(kwargs["sprite"],
                        pygm_sprite.PyGameMakerSprite)):
                        raise PyGameMakerObjectException("'{}' is not a recognized sprite resource".format(kwargs["sprite"]))
                    self.sprite_resource = kwargs["sprite"]
        print("Finished setup of {}".format(self.name))

    def create_instance(self, screen, **kwargs):
        print("Create new instance of {}".format(self))
        screen_dims = (screen.get_width(), screen.get_height())
        new_instance = PyGameMakerObjectInstance(self, screen_dims, self.id,
            **kwargs)
        self.group.add(new_instance)
        self.id += 1

    def update(self):
        if len(self.group) > 0:
            self.group.update()

    def draw(self, surface):
        if len(self.group) > 0:
            self.group.draw(surface)

    def get_image(self):
        """
            Called by instances of this Object type, to get a new copy of
            the sprite resource's image. Also, make sure the image has been
            loaded now that an instance with this image has been created.
        """
        if self.sprite_resource:
            if not self.sprite_resource.image:
                self.sprite_resource.load_graphic()
            return self.sprite_resource.image.copy()
        else:
            return None

    def __repr__(self):
        rpr = "<{} '{}'>".format(type(self).__name__, self.name)
        return rpr

if __name__ == "__main__":
    import pg_template
    import random

    class TestGameManager(object):
        LEFT_MARGIN = 10
        TOP_MARGIN  = 8
        TEXT_COLOR  = (128,   0, 128)
        TEXT_BACKG  = (255, 255, 255)
        def __init__(self):
            self.current_events = []
            self.done = False
            self.test_sprite = None
            self.objects = None
            print("Manager init complete")
        def setup(self, screen):
            self.screen = screen
            self.test_sprite = pygm_sprite.PyGameMakerSprite(
                "spr_test",
                filename="unittest_files/Ball.png"
            )
            self.objects = [PyGameMakerObject("obj_test",
                sprite=self.test_sprite)]
            print("Setup complete")
        def collect_event(self, event):
            self.current_events.append(event)
        def update(self):
            for ev in self.current_events:
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.done = True
                        break
                    elif ev.key == pygame.K_RETURN:
                        # create a new object instance
                        posn = (float(random.randint(0, self.screen.get_width())),
                            float(random.randint(0, self.screen.get_height())))
                        self.objects[0].create_instance(self.screen,
                            speed=random.random(),
                            direction=(360.0 * random.random()),
                            position=posn)
            # done with event handling
            self.current_events = []
            self.objects[0].update()
        def draw_objects(self):
            self.objects[0].draw(self.screen)
        def draw_background(self):
            self.screen.fill(pg_template.PygameTemplate.BLACK)
        def is_done(self):
            return self.done

    testmanager = TestGameManager()
    testgame = pg_template.PygameTemplate( (640,480), "Test Game", testmanager)
    testgame.run()

