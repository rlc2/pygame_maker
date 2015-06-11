#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker object resource

import pygame
import re
import yaml
import pygame_maker_object_instance as pygm_instance
import pygame_maker_event as pygm_event
import pygame_maker_action as pygm_action
import pygame_maker_sprite as pygm_sprite
import pygame_maker_event_action_sequence as pygm_sequence

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
    EVENT_NAME_OBJECT_HASH={
        "outside_room": pygm_event.PyGameMakerOtherEvent,
        "intersect_boundary": pygm_event.PyGameMakerOtherEvent,
        "create": pygm_event.PyGameMakerObjectStateEvent,
        "image_loaded": pygm_event.PyGameMakerOtherEvent,
    }
    CREATE_ACTION_RE=re.compile("^create")

    def __init__(self, object_name, event_engine, **kwargs):

        """
            PyGameMakerObject.__init__():
            Create a new type of object. An object type can create instances
            of itself.
            parameters:
             object_name (str): Supply a name for the object type
             event_engine (PyGameMakerEventEngine): Supply the event engine for
              creating and handling events
             **kwargs: Supply alternatives for default object properties:
              visible (bool): Whether instances will be drawn [True]
              solid (bool): Whether instances block other object instances
                     (e.g. a platform) [False]
              depth (int): Which layer object instances will be placed into [0]
              sprite (PyGameMakerSprite): Sprite resource used as the
               image [None]
        """

        if object_name:
            self.name = object_name
        else:
            self.name = self.DEFAULT_OBJECT_PREFIX
        self.event_engine = event_engine
        self.sprite_resource = None
        self.mask = None
        self.visible = True
        self.solid = False
        self.depth = 0
        # begin inside a collection containing only our own type
        self.object_type_collection = {self.name: self}
        self.group = pygame.sprite.LayeredDirty()
        self.event_action_sequences = {}
        self.id = 0
        self.handler_table = {
            re.compile("^alarm(\d{1,2})$"):     self.handle_alarm_event,
            re.compile("^kb_(.*)$"):            self.handle_keyboard_event,
            re.compile("^mouse_(.*)$"):         self.handle_mouse_event,
            re.compile("^collision_(.*)$"):     self.handle_collision_event,
            re.compile("^([^_]+)_step$"):       self.handle_step_event,
            re.compile("^outside_room$"):       self.handle_instance_event,
            re.compile("^intersect_boundary$"): self.handle_instance_event,
            re.compile("^create$"):             self.handle_create_event,
        }
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
                if "event_action_sequences" in kwargs:
                    ev_dict = kwargs["event_action_sequences"]
                    if not (ev_dict, dict):
                        raise PyGameMakerObjectException("'{}' must contain a hash of event names -> action sequences")
                    for ev_name in ev_dict:
                        if not isinstance(ev_dict[ev_name],
                            pygm_sequence.PyGameMakerEventActionSequence):
                            raise PyGameMakerObjectException("Event '{}' does not contain a PyGameMakerEventActionSequence")
                    self.event_action_sequences = ev_dict

        print("Finished setup of {}".format(self.name))

    def belongs_to_collection(self, object_type_collection):
        """
            belongs_to_collection():
            Supply the object type collection this type belongs to. This allows
             actions to affect every instance of a particular type.
        """
        self.object_type_collection = object_type_collection

    def create_instance(self, screen, **kwargs):
        """
            create_instance():
            Create a new instance of this object type. Every instance is
             assigned a unique ID, and placed inside a sprite group that
             handles drawing and positional updates for all contained instances.
            parameters:
             screen (pygame.Surface): The surface the instance will be drawn
              upon. The instance will use this surface's width and height
              parameters to detect boundary collision events, which are queued
              in the event engine.
             **kwargs: Passed on to the instance constructor, to supply
              alternatives to object instance defaults (usually 'speed',
              'direction', and/or 'position')
        """
        print("Create new instance of {}".format(self))
        screen_dims = (screen.get_width(), screen.get_height())
        new_instance = pygm_instance.PyGameMakerObjectInstance(self,
            screen_dims, self.id, **kwargs)
        self.group.add(new_instance)
        self.id += 1
        # queue the creation event for the new instance
        self.event_engine.queue_event(self.EVENT_NAME_OBJECT_HASH["create"]("create", { "type": self, "instance": new_instance }))

    def update(self):
        """
            update():
            Call to perform position updates for all instances. The sprite
            group handles this for us.
        """
        if len(self.group) > 0:
            self.group.update()

    def draw(self, surface):
        """
            draw():
            Call to draw all instances. The sprite group handles this for us.
        """
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
                # queue the image_loaded event
                self.event_engine.queue_event(
                    self.EVENT_NAME_OBJECT_HASH["image_loaded"]("image_loaded",
                        { "type": self, "sprite": self.sprite_resource })
                )
            return self.sprite_resource.image.copy()
        else:
            return None

    def get_applied_instance_list(self, action, event):
        """
            get_applied_instance_list():
            For actions with "apply_to" parameters, return a list of the
             object instances affected. There could be one, called "self",
             which can refer to a particular instance (which needs to
             be part of the event data), or called "other", in cases where
             another instance is involved in the event (collisions); or
             multiple, if apply_to refers to an object type, in which case
             all objects of the named type recieve the action.
             For "create" type actions, "self" instead refers to the object
             type to be created.
            parameters:
             action (PyGameMakerAction): The action with an "apply_to" field
             event (PyGameMakerEvent): The received event
        """
        apply_to_instances = []
        if 'instance' in event.event_params:
            apply_to_instances = [event['instance']]
        if not 'apply_to' in action.action_data:
            return apply_to_instances
        if action["apply_to"] == "other":
            if 'other' in event:
                # receiving an "other" instance is uncommon. ignore actions
                #  that apply to "other" if an "other" instance isn't supplied
                apply_to_instances = [event['other']]
        elif action["apply_to"] != "self":
            # applies to an object type; this means apply it to all instances
            #  of that object
            if action["apply_to"] in self.object_type_collection:
                apply_to_instances = self.object_type_collection[action["apply_to"]].group
        return apply_to_instances

    def execute_action_sequence(self, event):
        if event.event_name in self.event_action_sequences:
            for action in self.event_action_sequences[event.event_name].get_next_action():
                print("Action {}".format(action))
                affected_instance_list = self.get_applied_instance_list(action,
                    event)
                #print("Action {} applies to {}".format(action, affected_instance_list))
                if "apply_to" in action.action_data:
                    for target in affected_instance_list:
                        print("applying to {}".format(target))
                        target.execute_action(action)

    def handle_instance_event(self, event):
        """
            handle_instance_event():
            Execute action sequences generated by an instance:
             intersect_boundary
             outside_room
        """
        print("Received event {}".format(event))
        self.execute_action_sequence(event)

    def handle_mouse_event(self, event):
        """
            handle_mouse_event():
            Execute the action sequence associated with the supplied mouse
             event, if its XY coordinate intersects one or more instances and
             the exact mouse event is handled by this object (button #,
             press/release). mouse_global_* events are handled by instances
             watching for them at any location.
        """
        pass

    def handle_keyboard_event(self, event):
        """
            handle_keyboard_event():
            Execute the action sequence associated with the supplied key event,
             if the exact key event is handled by this object (which key,
             press/release)
        """
        pass

    def handle_collision_event(self, event):
        """
            handle_collision_event():
            Execute the action sequence associated with the collision event,
             if the name of the object collided with is part of the event's name
        """
        pass

    def handle_step_event(self, event):
        """
            handle_step_event():
            Execute the action sequence associated with the supplied step event,
             if the exact step event is handled by this object (begin, end,
             normal), on every instance
        """
        pass

    def handle_alarm_event(self, event):
        """
            handle_alarm_event():
            Execute the action sequence associated with the alarm event, if
             the exact alarm is handled by this object (0-11)
        """
        pass

    def handle_create_event(self, event):
        """
            handle_create_event():
            Execute the action sequence associated with the create event,
             passing it on to the instance recorded in the event
        """
        pass

    def select_event_handler(self, event_name):
        hdlr = None
        for ev_re in self.handler_table.keys():
            minfo = ev_re.match(event_name)
            if minfo:
                hdlr = self.handler_table[ev_re]
        return hdlr

    def __getitem__(self, itemname):
        """
            __getitem__():
            PyGameMakerObject instances support obj[event_name] to directly
             access the action sequence for a particular event.
        """
        if itemname in self.event_action_sequences:
            return self.event_action_sequences[itemname]
        else:
            return None

    def __setitem__(self, itemname, val):
        """
            __setitem__():
            PyGameMakerObject instances support obj[event_name] = sequence for
             directly setting the action sequence for a particular event.
        """
        if not isinstance(itemname, str):
            raise PyGameMakerObjectException("Event action sequence keys must be strings")
        if not isinstance(val, pygm_sequence.PyGameMakerEventActionSequence):
            raise PyGameMakerObjectException("Supplied event action sequence is not a PyGameMakerEventActionSequence instance")
        self.event_action_sequences[itemname] = val
        # register our handler for this event
        new_handler = self.select_event_handler(itemname)
        if new_handler:
            self.event_engine.register_event_handler(itemname, new_handler)
        else:
            raise PyGameMakerObjectException("PyGameMakerObject does not yet handle '{}' events (NYI)".format(itemname))

    def __delitem__(self, itemname):
        if itemname in self.event_action_sequences:
            # stop handling the given event name
            old_handler = self.select_event_handler(itemname)
            self.event_engine.unregister_event_handler(itemname, old_handler)
            # remove the event from the table
            del(self.event_action_sequences[itemname])

    def __repr__(self):
        rpr = "<{} '{}'>".format(type(self).__name__, self.name)
        return rpr

if __name__ == "__main__":
    import pg_template
    import random
    import pygame_maker_event_engine as pgmee

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
            self.event_engine = pgmee.PyGameMakerEventEngine()
            print("Manager init complete")
        def setup(self, screen):
            self.screen = screen
            self.test_sprite = pygm_sprite.PyGameMakerSprite(
                "spr_test",
                filename="unittest_files/Ball.png"
            )
            self.objects = [PyGameMakerObject("obj_test", self.event_engine,
                sprite=self.test_sprite)]
            intersect_sequence = pygm_sequence.PyGameMakerEventActionSequence()
            intersect_sequence.append_action(
                pygm_action.PyGameMakerMotionAction('reverse_vertical_speed')
            )
            intersect_sequence.append_action(
                pygm_action.PyGameMakerMotionAction('reverse_horizontal_speed')
            )
            self.objects[0]['intersect_boundary'] = intersect_sequence
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

