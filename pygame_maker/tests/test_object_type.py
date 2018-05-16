#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test the pygame_maker.actors.object_type module.
"""

import logging
import os
import sys
import pygame
import pg_template
import pygame_maker.support.logging_object as logging_object
import pygame_maker.actions.action as action
from pygame_maker.actions.action_sequence import ActionSequence
from pygame_maker.actors.object_type import ObjectType, CollideableObjectType
from pygame_maker.actors import object_sprite
from pygame_maker.events import event
from pygame_maker.events import event_engine
from pygame_maker.logic import language_engine
from pygame_maker.sounds.sound import Sound

OTLOGGER = logging.getLogger("CollideableObjectType")
OTHANDLER = logging.StreamHandler()
OTFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
OTHANDLER.setFormatter(OTFORMATTER)
OTLOGGER.addHandler(OTHANDLER)
OTLOGGER.setLevel(logging.INFO)

OILOGGER = logging.getLogger("ObjectInstance")
OIHANDLER = logging.StreamHandler()
OIFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
OIHANDLER.setFormatter(OIFORMATTER)
OILOGGER.addHandler(OIHANDLER)
OILOGGER.setLevel(logging.INFO)

GELOGGER = logging.getLogger("GameEngine")
GEHANDLER = logging.StreamHandler()
GEFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
GEHANDLER.setFormatter(GEFORMATTER)
GELOGGER.addHandler(GEHANDLER)
GELOGGER.setLevel(logging.INFO)

EELOGGER = logging.getLogger("EventEngine")
EEHANDLER = logging.StreamHandler()
EEFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
EEHANDLER.setFormatter(EEFORMATTER)
EELOGGER.addHandler(EEHANDLER)
EELOGGER.setLevel(logging.INFO)

OBJ_TEST_FILE = "unittest_files/obj_test.yaml"
OBJ_TEST_FILE2 = "unittest_files/obj_spaceship.yaml"


class GameEngine(logging_object.LoggingObject):
    """A game engine class specifically for testing ObjectType."""
    GAME_ENGINE_ACTIONS = ["play_sound", "create_object"]
    MOUSE_EVENT_TABLE = [
        {"instance_event_name": "mouse_nobutton",
         "global_event_name": "mouse_global_nobutton"},
        {"instance_event_name": "mouse_button_left",
         "global_event_name": "mouse_global_button_left",
         "instance_pressed_name": "mouse_left_pressed",
         "global_pressed_name": "mouse_global_left_pressed",
         "instance_released_name": "mouse_left_released",
         "global_released_name": "mouse_global_left_released"},
        {"instance_event_name": "mouse_button_middle",
         "global_event_name": "mouse_global_button_middle",
         "instance_pressed_name": "mouse_middle_pressed",
         "global_pressed_name": "mouse_global_middle_pressed",
         "instance_released_name": "mouse_middle_released",
         "global_released_name": "mouse_global_middle_released"},
        {"instance_event_name": "mouse_button_right",
         "global_event_name": "mouse_global_button_right",
         "instance_pressed_name": "mouse_right_pressed",
         "global_pressed_name": "mouse_global_right_pressed",
         "instance_released_name": "mouse_right_released",
         "global_released_name": "mouse_global_right_released"},
        {"instance_event_name": "mouse_wheelup",
         "global_event_name": "mouse_global_wheelup"},
        {"instance_event_name": "mouse_wheeldown",
         "global_event_name": "mouse_global_wheeldown"},
        {"instance_event_name": "mouse_button_6",
         "global_event_name": "mouse_global_button_6"},
        {"instance_event_name": "mouse_button_7",
         "global_event_name": "mouse_global_button_7"},
        {"instance_event_name": "mouse_button_8",
         "global_event_name": "mouse_global_button_8"},
    ]
    def __init__(self):
        super(GameEngine, self).__init__(type(self).__name__)
        self.event_engine = event_engine.EventEngine()
        self.language_engine = language_engine.LanguageEngine()
        self.symbols = language_engine.SymbolTable()
        self.resources = {
            'sprites': {},
            'sounds': {},
            'objects': {}
        }
        self.mask_surface = None
        self.draw_surface = None
        self.screen = None
        self.mouse_pos = [0, 0]

    def draw_mask(self, surf, objtype):
        """Draw the ball sprite mask as a graphic in the upper left corner."""
        if not self.mask_surface and objtype.mask:
            mask_dims = objtype.mask.get_size()
            print("Mask size: {}".format(mask_dims))
            #pylint: disable=too-many-function-args
            #pylint: disable=unexpected-keyword-arg
            self.mask_surface = pygame.Surface(mask_dims, depth=8)
            #pylint: enable=unexpected-keyword-arg
            #pylint: enable=too-many-function-args
            self.mask_surface.fill(pygame.Color("#000000"))
            self.mask_surface.lock()
            for row in range(0, mask_dims[1]):
                for col in range(0, mask_dims[0]):
                    if objtype.mask.get_at((col, row)):
                        self.mask_surface.set_at((col, row), pygame.Color("#ffffff"))
            self.mask_surface.unlock()
        if self.mask_surface:
            surf.blit(self.mask_surface, (5, 5))

#pylint: disable=unused-argument
    def execute_action(self, an_action, an_event, instance=None):
        """Handle play_sound and create_object events."""
        action_params = {}
        for param in list(an_action.action_data.keys()):
            if param == 'apply_to':
                continue
            if param == 'child_instance':
                if an_action.action_data['child_instance'] and instance is not None:
                    # create_object: connect the child instance to its parent that
                    #   forwarded this action
                    action_params['parent'] = instance
                continue
            action_params[param] = an_action.get_parameter_expression_result(
                param, self.symbols, self.language_engine)

        #print("Engine recieved action: {}".format(action))
        if an_action.name == "play_sound":
            if ((len(action_params['sound']) > 0) and
                    (action_params['sound'] in list(self.resources['sounds'].keys()))):
                self.resources['sounds'][action_params['sound']].play_sound()
        if an_action.name == "create_object":
            if (self.screen and (len(action_params['object']) > 0) and
                    (action_params['object'] in list(self.resources['objects'].keys()))):
                self.resources['objects'][action_params['object']].create_instance(
                    self.screen, action_params)
#pylint: enable=unused-argument

    def send_key_event(self, key_event):
        """Produce appropriate keyboard events."""
        pk_map = event.KeyEvent.PYGAME_KEY_TO_KEY_EVENT_MAP
        key_event_name = None
        base_event_name = None
        if key_event is None:
            key_event_name = "kb_no_key"
        elif key_event.key in pk_map:
            base_event_name = pk_map[key_event.key]
            if key_event.type == pygame.KEYDOWN:
                key_event_name = "{}_keydn".format(pk_map[key_event.key])
            elif key_event.type == pygame.KEYUP:
                key_event_name = "{}_keyup".format(pk_map[key_event.key])
        if key_event is not None:
            # transmit the key name for event handlers that want to handle
            # both events in the same handler (no suffix)
            base_ev = event.KeyEvent(base_event_name)
            self.event_engine.queue_event(base_ev)
            self.event_engine.transmit_event(base_event_name)
        kev = event.KeyEvent(key_event_name)
        #print("queue event: {}".format(kev))
        self.event_engine.queue_event(kev)
        #print("xmit event: {}".format(key_event_name))
        self.event_engine.transmit_event(key_event_name)

    def send_mouse_event(self, mouse_event):
        """Produce appropriate mouse events."""
        if mouse_event:
            self.mouse_pos[0] = mouse_event.pos[0]
            self.mouse_pos[1] = mouse_event.pos[1]
            self.language_engine.global_symbol_table['mouse.x'] = self.mouse_pos[0]
            self.language_engine.global_symbol_table['mouse.y'] = self.mouse_pos[1]
            if mouse_event.type == pygame.MOUSEMOTION:
                return
        event_names = []
        if mouse_event:
            mouse_button = mouse_event.button
            if len(self.MOUSE_EVENT_TABLE) > mouse_button:
                ev_table_entry = self.MOUSE_EVENT_TABLE[mouse_button]
                #print("select mouse entries {}".format(ev_table_entry))
                # queue the instance version of the event (each object type
                #  listening for this kind of event only passes it on
                #  to instances that intersect with the mouse position)
                self.event_engine.queue_event(
                    event.MouseEvent(
                        ev_table_entry["instance_event_name"],
                        {"position": mouse_event.pos}
                    )
                )
                event_names.append(ev_table_entry["instance_event_name"])
                #print("queue {}".format(event_names[-1]))
                self.event_engine.queue_event(
                    event.MouseEvent(
                        ev_table_entry["global_event_name"],
                        {"position": mouse_event.pos}
                    )
                )
                event_names.append(ev_table_entry["global_event_name"])
                #print("queue {}".format(event_names[-1]))
                # press/release events exist only for a subset
                if mouse_event.type == pygame.MOUSEBUTTONDOWN:
                    if 'instance_pressed_name' in ev_table_entry:
                        self.event_engine.queue_event(
                            event.MouseEvent(
                                ev_table_entry["instance_pressed_name"],
                                {"position": mouse_event.pos}
                            )
                        )
                        event_names.append(ev_table_entry["instance_pressed_name"])
                        #print("queue {}".format(event_names[-1]))
                        self.event_engine.queue_event(
                            event.MouseEvent(
                                ev_table_entry["global_pressed_name"],
                                {"position": mouse_event.pos}
                            )
                        )
                        event_names.append(ev_table_entry["global_pressed_name"])
                        #print("queue {}".format(event_names[-1]))
                if mouse_event.type == pygame.MOUSEBUTTONUP:
                    if 'instance_released_name' in ev_table_entry:
                        self.event_engine.queue_event(
                            event.MouseEvent(
                                ev_table_entry["instance_released_name"],
                                {"position": mouse_event.pos}
                            )
                        )
                        event_names.append(ev_table_entry["instance_released_name"])
                        #print("queue {}".format(event_names[-1]))
                        self.event_engine.queue_event(
                            event.MouseEvent(
                                ev_table_entry["global_released_name"],
                                {"position": mouse_event.pos}
                            )
                        )
                        event_names.append(ev_table_entry["global_released_name"])
                        #print("queue {}".format(event_names[-1]))
        else:
            self.event_engine.queue_event(
                event.MouseEvent("mouse_nobutton",
                                 {"position": self.mouse_pos})
            )
            event_names.append("mouse_nobutton")
            self.event_engine.queue_event(
                event.MouseEvent("mouse_global_nobutton",
                                 {"position": self.mouse_pos})
            )
            event_names.append("mouse_global_nobutton")
        # transmit all queued event types
        for ev_name in event_names:
            #if not ev_name in ['mouse_nobutton', 'mouse_global_nobutton']:
            #    print("xmit ev {}".format(ev_name))
            self.event_engine.transmit_event(ev_name)

class TestGameManager(object):
    """
    Singleton class, an instance of which is sent to the PygameTemplate class
    constructor.  Handles the various stages (setup, event collection, drawing,
    etc.) of the main game loop.
    """
    LEFT_MARGIN = 10
    TOP_MARGIN = 8
    TEXT_COLOR = (128, 0, 128)
    TEXT_BACKG = (255, 255, 255)
    def __init__(self):
        self.current_events = []
        self.done = False
        self.test_sprite = None
        self.screen = None
        self.game_engine = GameEngine()
        print("Manager init complete")

    def setup(self, screen):
        """Handle the game setup phase, prior to the main game loop."""
        self.screen = screen
        self.game_engine.screen = screen
        self.game_engine.draw_surface = screen
        res = self.game_engine.resources
        res['sprites']['spr_test'] = object_sprite.ObjectSprite(
            "spr_test", filename="unittest_files/ball2.png", collision_type="precise")
        res['sprites']['spr_solid'] = object_sprite.ObjectSprite(
            "spr_solid", filename="unittest_files/solid.png", collision_type="precise")
        res['sprites']['spr_spaceship'] = object_sprite.ObjectSprite(
            "spr_spaceship", filename="unittest_files/spaceship_strip07.png",
            collision_type="precise")
        res['sounds']['snd_test'] = Sound(
            "snd_test", filename="unittest_files/Pop.wav")
        res['sounds']['snd_explosion'] = Sound(
            "snd_explosion", filename="unittest_files/explosion.wav")
        with open(OBJ_TEST_FILE, "r") as yaml_f:
            res['objects']['obj_test'] = ObjectType.load_from_yaml(
                yaml_f, self.game_engine)[0]
        res['objects']['obj_solid'] = CollideableObjectType(
            "obj_solid", self.game_engine, solid=True, sprite='spr_solid')
        # this doubles as a solid object and as the manager object
        res['objects']['obj_solid'].create_instance(
            self.screen, position=(308, 228))
        with open(OBJ_TEST_FILE2, "r") as yaml_f:
            res['objects']['obj_spaceship'] = ObjectType.load_from_yaml(
                yaml_f, self.game_engine)[0]
        res['objects']['obj_spaceship'].create_instance(
            self.screen, position=(308, 450))
        res['objects']['obj_solid']['kb_enter_keydn'] = ActionSequence()
        res['objects']['obj_solid']['kb_enter_keydn'].append_action(
            action.ObjectAction("create_object",
                                {
                                    'object': 'obj_test',
                                    'position.x':"=randint({})".format(self.screen.get_width()),
                                    'position.y':"=randint({})".format(self.screen.get_height())
                                })
        )
        res['objects']['obj_solid']['mouse_global_left_pressed'] = ActionSequence()
        res['objects']['obj_solid']['mouse_global_left_pressed'].append_action(
            action.ObjectAction("create_object",
                                {
                                    'object': 'obj_test',
                                    'position.x':"=mouse.x",
                                    'position.y':"=mouse.y"
                                })
        )
        print("Setup complete")

    def collect_event(self, an_event):
        """Add a new event to the current_events list."""
        self.current_events.append(an_event)

    def update(self):
        """Update the game state."""
        key_pressed = False
        mouse_button = False
        res = self.game_engine.resources
        for kev in self.current_events:
            if kev.type in (pygame.KEYDOWN, pygame.KEYUP):
                key_pressed = True
                if kev.key == pygame.K_ESCAPE:
                    self.done = True
                    break
                else:
                    self.game_engine.send_key_event(kev)
            #elif kev.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):
            if kev.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                self.game_engine.send_mouse_event(kev)
                if kev.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
                    mouse_button = True
        if not key_pressed:
            self.game_engine.send_key_event(None)
        if not mouse_button:
            self.game_engine.send_mouse_event(None)
        # done with event handling
        self.current_events = []
        for obj_name in list(res['objects'].keys()):
            res['objects'][obj_name].update()
        # check for object instance collisions
        obj_types = list(res['objects'].values())
        collision_types = set()
        for obj_name in list(res['objects'].keys()):
            collision_types |= res['objects'][obj_name].collision_check(obj_types)
        if len(collision_types) > 0:
            for coll_type in collision_types:
                self.game_engine.event_engine.transmit_event(coll_type)

    def draw_objects(self):
        """Draw object instances."""
        kev = event.DrawEvent('draw')
        self.game_engine.event_engine.queue_event(kev)
        self.game_engine.event_engine.transmit_event(kev.name)
        self.game_engine.draw_mask(
            self.screen, self.game_engine.resources['objects']['obj_test'])
        if self.game_engine.resources['objects']['obj_test'].image:
            self.screen.blit(self.game_engine.resources['objects']['obj_test'].image, (5, 5))

    def draw_background(self):
        """Clear the screen to black."""
        self.screen.fill(pg_template.PygameTemplate.BLACK)

    def final_pass(self):
        """
        Not using a software surface, so no need to do a copy to hw surface here.
        """
        pass

    def is_done(self):
        """Respond to requests about the game done state."""
        return self.done

# run from the tests directory to find the unittest_files subdirectory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

TESTMANAGER = TestGameManager()
TESTGAME = pg_template.PygameTemplate((640, 480), "Test Game", TESTMANAGER)
TESTGAME.run()

