#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test the pygame_maker.scenes.room module.
"""

import logging
import sys
import os
import pygame
import pg_template
from pygame_maker.support import logging_object
from pygame_maker.logic import language_engine
from pygame_maker.sounds import sound
from pygame_maker.actors import object_sprite
from pygame_maker.actors import object_type
from pygame_maker.events import event
from pygame_maker.events import event_engine
from pygame_maker.scenes import background
from pygame_maker.scenes.room import Room

RLOGGER = logging.getLogger("Room")
RHANDLER = logging.StreamHandler()
RFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
RHANDLER.setFormatter(RFORMATTER)
RLOGGER.addHandler(RHANDLER)
RLOGGER.setLevel(logging.INFO)

GMLOGGER = logging.getLogger("MyGameManager")
GMHANDLER = logging.StreamHandler()
GMFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
GMHANDLER.setFormatter(GMFORMATTER)
GMLOGGER.addHandler(GMHANDLER)
GMLOGGER.setLevel(logging.INFO)

TEST_BACKGROUND_LIST_YAML_FILE = "unittest_files/test_backgrounds.yaml"
TEST_ROOM_LIST_YAML_FILE = "unittest_files/test_rooms.yaml"
TEST_SPRITE_LIST_YAML_FILE = "unittest_files/test_sprites.yaml"
TEST_OBJECT_LIST_YAML_FILE = "unittest_files/test_objects.yaml"
TEST_SOUND_LIST_YAML_FILE = "unittest_files/test_sounds.yaml"


class MyGameManager(logging_object.LoggingObject):
    """Custom game manager for room module tests."""
    LEFT_MARGIN = 10
    TOP_MARGIN = 8
    LINE_HEIGHT = 18
    TEXT_COLOR = (128, 0, 128)
    TEXT_BACKG = (255, 255, 255)
    GAME_ENGINE_ACTIONS = ['play_sound', 'create_object']
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
        super(MyGameManager, self).__init__(type(self).__name__)
        self.current_events = []
        self.resources = {
            'rooms': [],
            'sprites': {},
            'sounds': {},
            'objects': {},
            'backgrounds': {}
        }
        self.language_engine = language_engine.LanguageEngine()
        self.symbols = language_engine.SymbolTable()
        self.event_engine = event_engine.EventEngine()
        self.draw_surface = None
        self.text_objects = []
        backgrounds = None
        with open(TEST_BACKGROUND_LIST_YAML_FILE, "r") as yaml_f:
            backgrounds = background.Background.load_from_yaml(yaml_f)
        for bkg in backgrounds:
            self.resources['backgrounds'][bkg.name] = bkg
        if len(list(self.resources['backgrounds'].keys())) == 0:
            print(("Unable to load backgrounds from {}, aborting.".format(
                TEST_BACKGROUND_LIST_YAML_FILE)))
            exit(1)
        sprites = None
        with open(TEST_SPRITE_LIST_YAML_FILE, "r") as yaml_f:
            sprites = object_sprite.ObjectSprite.load_from_yaml(yaml_f, self)
        for spr in sprites:
            self.resources['sprites'][spr.name] = spr
        if len(list(self.resources['sprites'].keys())) == 0:
            print(("Unable to load sprites from {}, aborting.".format(
                TEST_SPRITE_LIST_YAML_FILE)))
        sounds = None
        with open(TEST_SOUND_LIST_YAML_FILE, "r") as yaml_f:
            sounds = sound.Sound.load_from_yaml(yaml_f)
        for snd in sounds:
            self.resources['sounds'][snd.name] = snd
        if len(self.resources['sounds']) == 0:
            print(("Unable to load sounds from {}, aborting.".format(
                TEST_SOUND_LIST_YAML_FILE)))
        objects = None
        with open(TEST_OBJECT_LIST_YAML_FILE, "r") as yaml_f:
            objects = object_type.ObjectType.load_from_yaml(yaml_f, self)
        for obj in objects:
            self.resources['objects'][obj.name] = obj
        if len(self.resources['objects']) == 0:
            print(("Unable to load objects from {}, aborting.".format(
                TEST_OBJECT_LIST_YAML_FILE)))
        with open(TEST_ROOM_LIST_YAML_FILE, "r") as yaml_f:
            self.resources['rooms'] = Room.load_from_yaml(yaml_f, self)
        if len(self.resources['rooms']) == 0:
            print(("Unable to load rooms from {}, aborting.".format(
                TEST_ROOM_LIST_YAML_FILE)))
            exit(1)
        self.largest_dims = [0, 0]
        for room in self.resources['rooms']:
            if room.width > self.largest_dims[0]:
                self.largest_dims[0] = room.width
            if room.height > self.largest_dims[1]:
                self.largest_dims[1] = room.height
        self.font = None
        self.done = False
        self.screen = None
        self.font = None
        self.background_idx = 0
        self.room_idx = 0
        self.mouse_pos = [0, 0]

    def setup(self, screen):
        """Handle setup callback from PygameTemplate."""
        self.screen = screen
        self.draw_surface = self.screen
        self.font = pygame.font.Font(None, 16)
        for spr in list(self.resources['sprites'].keys()):
            print("Setup {}".format(spr))
            self.resources['sprites'][spr].setup()
        for snd in list(self.resources['sounds'].keys()):
            print("Setup {}".format(snd))
            self.resources['sounds'][snd].setup()
        for bkg in list(self.resources['backgrounds'].keys()):
            print("Setup {}".format(bkg))
            self.resources['backgrounds'][bkg].setup()
        self.resources['rooms'][0].load_room(self.screen)
        self.resources['rooms'][0].draw_room_background(self.screen)
        self.symbols['room_width'] = self.resources['rooms'][0].width
        self.symbols['room_height'] = self.resources['rooms'][0].height
        self.create_text("Room {} ok (Y/N)?".format(self.resources['rooms'][0].name))

    def collect_event(self, an_event):
        """Handle collect_event callback from PygameTemplate."""
        self.current_events.append(an_event)

    def create_text(self, text):
        """
        Create a maximum of 25 lines of text objects for rendering to the screen.
        """
        if len(self.text_objects) > 25:
            # too many text lines, remove oldest object
            self.text_objects = self.text_objects[1:]
        self.text_objects.append(("text", self.font.render(
            text, 1, self.TEXT_COLOR, self.TEXT_BACKG)))

    def execute_action(self, action, an_event):
        """Handle execute_action() method calls from object instances."""
        action_params = {}
        for param in list(action.action_data.keys()):
            if param == 'apply_to':
                continue
            action_params[param] = action.get_parameter_expression_result(
                param, self.symbols, self.language_engine)

        #print("Engine received action: {}".format(action))
        if action.name == "play_sound":
            if ((len(action_params['sound']) > 0) and
                    (action_params['sound'] in list(self.resources['sounds'].keys()))):
                self.resources['sounds'][action_params['sound']].play_sound()
        if action.name == "create_object":
            if (self.screen and (len(action_params['object']) > 0) and
                    (action_params['object'] in list(self.resources['objects'].keys()))):
                self.resources['objects'][action_params['object']].create_instance(
                    self.screen, action_params)

    def send_key_event(self, key_event):
        """
        Translate pygame keyboard events (including no keys pressed) to
        appropriate pygame_maker keyboard events.
        """
        pk_map = event.KeyEvent.PYGAME_KEY_TO_KEY_EVENT_MAP
        key_event_init_name = None
        key_event_name = None
        if not key_event:
            key_event_init_name = "kb_no_key"
            key_event_name = key_event_init_name
        elif key_event.key in pk_map:
            key_event_name = str(pk_map[key_event.key])
            if key_event.type == pygame.KEYDOWN:
                key_event_init_name = "{}_keydn".format(pk_map[key_event.key])
            elif key_event.type == pygame.KEYUP:
                key_event_init_name = "{}_keyup".format(pk_map[key_event.key])
        kev = event.KeyEvent(key_event_init_name)
        #print("queue event: {}".format(kev))
        self.event_engine.queue_event(kev)
        #print("xmit event: {}".format(key_event_name))
        self.event_engine.transmit_event(key_event_name)

    def send_mouse_event(self, mouse_event):
        """
        Translate pygame mouse events (including no buttons pressed) to
        appropriate pygame_maker mouse events.
        """
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
                event.MouseEvent("mouse_nobutton", {"position": self.mouse_pos})
            )
            event_names.append("mouse_nobutton")
            self.event_engine.queue_event(
                event.MouseEvent("mouse_global_nobutton", {"position": self.mouse_pos})
            )
            event_names.append("mouse_global_nobutton")
        # transmit all queued event types
        for ev_name in event_names:
            #if not ev_name in ['mouse_nobutton', 'mouse_global_nobutton']:
            #    print("xmit ev {}".format(ev_name))
            self.event_engine.transmit_event(ev_name)

    def update(self):
        """Handle PygameTemplate update callback."""
        key_pressed = False
        mouse_button = False
        for cev in self.current_events:
            if cev.type == pygame.KEYDOWN:
                if cev.key == pygame.K_ESCAPE:
                    self.done = True
                    break
                elif cev.key == pygame.K_y:
                    if self.room_idx < (len(self.resources['rooms'])-1):
                        self.room_idx += 1
                        self.resources['rooms'][self.room_idx].load_room(self.screen)
                        self.symbols['room_width'] = self.resources['rooms'][self.room_idx].width
                        self.symbols['room_height'] = self.resources['rooms'][self.room_idx].height
                        self.create_text("Room {}, ok? Y/N".format(
                            self.resources['rooms'][self.room_idx].name))
                    else:
                        self.done = True
                elif cev.key == pygame.K_n:
                    # create a new text object
                    self.create_text("Failed.")
                    self.done = True
                else:
                    self.send_key_event(cev)
                    key_pressed = True
            if cev.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                self.send_mouse_event(cev)
                if cev.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
                    mouse_button = True
        if not key_pressed:
            self.send_key_event(None)
        if not mouse_button:
            self.send_mouse_event(None)
        # done with event handling
        self.current_events = []
        for obj in list(self.resources['objects'].keys()):
            self.resources['objects'][obj].update()
        # check for object instance collisions
        obj_types = list(self.resources['objects'].values())
        collision_types = []
        for obj_name in list(self.resources['objects'].keys()):
            collision_types += self.resources['objects'][obj_name].collision_check(obj_types)
        if len(collision_types) > 0:
            for coll_type in collision_types:
                self.event_engine.transmit_event(coll_type)

    def draw_text(self, textobj, line):
        """Blit a text line to the screen."""
        ypos = self.TOP_MARGIN + line*self.LINE_HEIGHT
        textpos = (self.LEFT_MARGIN, ypos)
        self.screen.blit(textobj[1], textpos)

    def draw_objects(self):
        """Handle draw_objects callback from PygameTemplate."""
        drev = event.DrawEvent('draw')
        self.event_engine.queue_event(drev)
        self.event_engine.transmit_event(drev.name)
        # draw text over the top of other objects
        for line, obj in enumerate(self.text_objects):
            self.draw_text(obj, line)

    def draw_background(self):
        """Handle draw_background callback from PygameTemplate."""
        if self.room_idx < len(self.resources['rooms']):
            self.resources['rooms'][self.room_idx].draw_room_background(self.screen)

    def final_pass(self):
        """Handle final_pass callback from PygameTemplate."""
        pass

    def is_done(self):
        """Handle is_done callback from PygameTemplate."""
        return self.done

# run from the tests directory to find the unittest_files subdirectory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

MYMANAGER = MyGameManager()
MYGAME = pg_template.PygameTemplate(MYMANAGER.largest_dims, "Room Tests", MYMANAGER)
MYGAME.run()

