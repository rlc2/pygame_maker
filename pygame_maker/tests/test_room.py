#!/usr/bin/env python

from pygame_maker.scenes.room import *
import pg_template
import tempfile
import logging
import sys
import os
from pygame_maker.scenes import background
from pygame_maker.logic import language_engine
from pygame_maker.sounds import sound
from pygame_maker.actors import object_sprite
from pygame_maker.actors import object_type
from pygame_maker.events import event
from pygame_maker.events import event_engine

rlogger = logging.getLogger("Room")
rhandler = logging.StreamHandler()
rformatter = logging.Formatter("%(levelname)s: %(message)s")
rhandler.setFormatter(rformatter)
rlogger.addHandler(rhandler)
rlogger.setLevel(logging.INFO)

gmlogger = logging.getLogger("MyGameManager")
gmhandler = logging.StreamHandler()
gmformatter = logging.Formatter("%(levelname)s: %(message)s")
gmhandler.setFormatter(gmformatter)
gmlogger.addHandler(gmhandler)
gmlogger.setLevel(logging.INFO)

TEST_BACKGROUND_LIST_YAML_FILE="unittest_files/test_backgrounds.yaml"
TEST_ROOM_LIST_YAML_FILE="unittest_files/test_rooms.yaml"
TEST_SPRITE_LIST_YAML_FILE="unittest_files/test_sprites.yaml"
TEST_OBJECT_LIST_YAML_FILE="unittest_files/test_objects.yaml"
TEST_SOUND_LIST_YAML_FILE="unittest_files/test_sounds.yaml"

class MyGameManager(logging_object.LoggingObject):
    LEFT_MARGIN = 10
    TOP_MARGIN  = 8
    LINE_HEIGHT = 18
    TEXT_COLOR  = (128,   0, 128)
    TEXT_BACKG  = (255, 255, 255)
    MOUSE_EVENT_TABLE=[
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
        self.text_objects = []
        backgrounds = background.Background.load_from_yaml(TEST_BACKGROUND_LIST_YAML_FILE)
        for bkg in backgrounds:
            self.resources['backgrounds'][bkg.name] = bkg
        if len(self.resources['backgrounds'].keys()) == 0:
            print("Unable to load backgrounds from {}, aborting.".format(TEST_BACKGROUND_LIST_YAML_FILE))
            exit(1)
        sprites = object_sprite.ObjectSprite.load_from_yaml(TEST_SPRITE_LIST_YAML_FILE)
        for spr in sprites:
            self.resources['sprites'][spr.name] = spr
        if len(self.resources['sprites'].keys()) == 0:
            print("Unable to load sprites from {}, aborting.".format(TEST_SPRITE_LIST_YAML_FILE))
        sounds = sound.Sound.load_from_yaml(TEST_SOUND_LIST_YAML_FILE)
        for snd in sounds:
            self.resources['sounds'][snd.name] = snd
        if len(self.resources['sounds']) == 0:
            print("Unable to load sounds from {}, aborting.".format(TEST_SOUND_LIST_YAML_FILE))
        objects = object_type.ObjectType.load_from_yaml(TEST_OBJECT_LIST_YAML_FILE, self)
        for obj in objects:
            self.resources['objects'][obj.name] = obj
        if len(self.resources['objects']) == 0:
            print("Unable to load objects from {}, aborting.".format(TEST_OBJECT_LIST_YAML_FILE))
        self.resources['rooms'] = Room.load_from_yaml(TEST_ROOM_LIST_YAML_FILE, self)
        if len(self.resources['rooms']) == 0:
            print("Unable to load rooms from {}, aborting.".format(TEST_ROOM_LIST_YAML_FILE))
            exit(1)
        self.largest_dims = [0,0]
        for rm in self.resources['rooms']:
            if rm.width > self.largest_dims[0]:
                self.largest_dims[0] = rm.width
            if rm.height > self.largest_dims[1]:
                self.largest_dims[1] = rm.height
        self.font = None
        self.done = False
        self.screen = None
        self.font = None
        self.background_idx = 0
        self.room_idx = 0
        self.mouse_pos = [0, 0]

    def setup(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 16)
        for spr in self.resources['sprites'].keys():
            print("Setup {}".format(spr))
            self.resources['sprites'][spr].setup()
        for snd in self.resources['sounds'].keys():
            print("Setup {}".format(snd))
            self.resources['sounds'][snd].setup()
        for bkg in self.resources['backgrounds'].keys():
            print("Setup {}".format(bkg))
            self.resources['backgrounds'][bkg].setup()
        self.resources['rooms'][0].load_room(self.screen)
        self.resources['rooms'][0].draw_room_background(self.screen)
        self.symbols['room_width'] = self.resources['rooms'][0].width
        self.symbols['room_height'] = self.resources['rooms'][0].height
        self.create_text("Room {} ok (Y/N)?".format(self.resources['rooms'][0].name))

    def collect_event(self, event):
        self.current_events.append(event)

    def create_text(self, text):
        if len(self.text_objects) > 25:
            # too many text lines, remove oldest object
            self.text_objects = self.text_objects[1:]
        self.text_objects.append( ("text", self.font.render(text, 1, self.TEXT_COLOR, self.TEXT_BACKG)) )

    def execute_action(self, action, event):
        action_params = {}
        for param in action.action_data.keys():
            if param == 'apply_to':
                continue
            action_params[param] = action.get_parameter_expression_result(
                param, self.symbols, self.language_engine)

        #print("Engine recieved action: {}".format(action))
        if action.name == "play_sound":
            if ((len(action_params['sound']) > 0) and
                (action_params['sound'] in self.resources['sounds'].keys())):
                self.resources['sounds'][action_params['sound']].play_sound()
        if action.name == "create_object":
            if (self.screen and (len(action_params['object']) > 0) and
                (action_params['object'] in self.resources['objects'].keys())):
                self.resources['objects'][action_params['object']].create_instance(
                    self.screen, action_params)

    def send_key_event(self, key_event):
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
        ev = event.KeyEvent(key_event_init_name)
        #print("queue event: {}".format(ev))
        self.event_engine.queue_event(ev)
        #print("xmit event: {}".format(key_event_name))
        self.event_engine.transmit_event(key_event_name)

    def send_mouse_event(self, mouse_event):
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

    def update(self):
        key_pressed = False
        mouse_button = False
        for ev in self.current_events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.done = True
                    break
                elif ev.key == pygame.K_y:
                    if self.room_idx < (len(self.resources['rooms'])-1):
                        self.room_idx += 1
                        self.resources['rooms'][self.room_idx].load_room(self.screen)
                        self.symbols['room_width'] = self.resources['rooms'][self.room_idx].width
                        self.symbols['room_height'] = self.resources['rooms'][self.room_idx].height
                        self.create_text("Room {}, ok? Y/N".format(self.resources['rooms'][self.room_idx].name))
                    else:
                        self.done = True
                elif ev.key == pygame.K_n:
                    # create a new text object
                    self.create_text("Failed.")
                    self.done = True
                else:
                    self.send_key_event(ev)
                    key_pressed = True
            if ev.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                pygame.MOUSEMOTION]:
                self.send_mouse_event(ev)
                if ev.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
                    mouse_button = True
        if not key_pressed:
            self.send_key_event(None)
        if not mouse_button:
            self.send_mouse_event(None)
        # done with event handling
        self.current_events = []
        for obj in self.resources['objects'].keys():
            self.resources['objects'][obj].update()
        # check for object instance collisions
        obj_types = self.resources['objects'].values()
        collision_types = []
        for obj_name in self.resources['objects'].keys():
            collision_types += self.resources['objects'][obj_name].collision_check(obj_types)
        if len(collision_types) > 0:
            for coll_type in collision_types:
                self.event_engine.transmit_event(coll_type)

    def draw_text(self, textobj, line):
        y = self.TOP_MARGIN + line*self.LINE_HEIGHT
        textpos = (self.LEFT_MARGIN, y)
        self.screen.blit(textobj[1], textpos)

    def draw_objects(self):
        for obj in self.resources['objects'].keys():
            self.resources['objects'][obj].draw(self.screen)
        # draw text over the top of other objects
        for line, ob in enumerate(self.text_objects):
            self.draw_text(ob, line)

    def draw_background(self):
        if self.room_idx < len(self.resources['rooms']):
            self.resources['rooms'][self.room_idx].draw_room_background(self.screen)

    def final_pass(self):
        pass

    def is_done(self):
        return self.done

# run from the tests directory to find the unittest_files subdirectory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

mymanager = MyGameManager()
mygame = pg_template.PygameTemplate( mymanager.largest_dims, "Room Tests",
    mymanager)
mygame.run()
