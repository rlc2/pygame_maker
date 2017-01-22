#!/usr/bin/env python

from pygame_maker.actors.object_type import *
from pygame_maker.actors import object_sprite
import pg_template
import random
import sys
import os
from pygame_maker.events import event_engine
from pygame_maker.logic import language_engine

otlogger = logging.getLogger("CollideableObjectType")
othandler = logging.StreamHandler()
otformatter = logging.Formatter("%(levelname)s: %(message)s")
othandler.setFormatter(otformatter)
otlogger.addHandler(othandler)
otlogger.setLevel(logging.INFO)

oilogger = logging.getLogger("ObjectInstance")
oihandler = logging.StreamHandler()
oiformatter = logging.Formatter("%(levelname)s: %(message)s")
oihandler.setFormatter(oiformatter)
oilogger.addHandler(oihandler)
oilogger.setLevel(logging.INFO)

gelogger = logging.getLogger("GameEngine")
gehandler = logging.StreamHandler()
geformatter = logging.Formatter("%(levelname)s: %(message)s")
gehandler.setFormatter(geformatter)
gelogger.addHandler(gehandler)
gelogger.setLevel(logging.INFO)

OBJ_TEST_FILE="unittest_files/obj_test.yaml"

class GameEngine(logging_object.LoggingObject):
    GAME_ENGINE_ACTIONS = ["play_sound", "create_object"]
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
        self.last_key_down = None
        self.screen = None
        self.mouse_pos = [0,0]
        self.action_blocks = {}

    def draw_mask(self, surf, objtype):
        if not self.mask_surface and objtype.mask:
            mask_dims = objtype.mask.get_size()
            print("Mask size: {}".format(mask_dims))
            self.mask_surface = pygame.Surface(mask_dims, depth=8)
            self.mask_surface.fill(pygame.Color("#000000"))
            self.mask_surface.lock()
            for y in range(0, mask_dims[1]):
                for x in range(0, mask_dims[0]):
                    if objtype.mask.get_at( (x,y) ):
                        self.mask_surface.set_at( (x,y),
                            pygame.Color("#ffffff"))
            self.mask_surface.unlock()
        if self.mask_surface:
            surf.blit(self.mask_surface, (5,5))

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

class TestGameManager(object):
    LEFT_MARGIN = 10
    TOP_MARGIN  = 8
    TEXT_COLOR  = (128,   0, 128)
    TEXT_BACKG  = (255, 255, 255)
    def __init__(self):
        self.current_events = []
        self.done = False
        self.test_sprite = None
        self.game_engine = GameEngine()
        print("Manager init complete")
    def setup(self, screen):
        self.screen = screen
        self.game_engine.screen = screen
        self.game_engine.draw_surface = screen
        self.game_engine.resources['sprites']['spr_test'] = object_sprite.ObjectSprite("spr_test", filename="unittest_files/ball2.png", collision_type="precise")
        self.game_engine.resources['sprites']['spr_solid'] = object_sprite.ObjectSprite("spr_solid", filename="unittest_files/solid.png", collision_type="precise")
        self.game_engine.resources['sounds']['snd_test'] = sound.Sound("snd_test", sound_file="unittest_files/Pop.wav")
        self.game_engine.resources['sounds']['snd_explosion'] = sound.Sound("snd_explosion", sound_file="unittest_files/explosion.wav")
        with open(OBJ_TEST_FILE, "r") as yaml_f:
            self.game_engine.resources['objects']['obj_test'] = ObjectType.load_from_yaml(yaml_f, self.game_engine)[0]
        self.game_engine.resources['objects']['obj_solid'] = CollideableObjectType("obj_solid", self.game_engine, solid=True, sprite='spr_solid')
        # this doubles as a solid object and as the manager object
        self.game_engine.resources['objects']['obj_solid'].create_instance(self.screen,
            position=(308,228))
        self.game_engine.resources['objects']['obj_solid']['kb_enter'] = action_sequence.ActionSequence()
        self.game_engine.resources['objects']['obj_solid']['kb_enter'].append_action(
            action.ObjectAction("create_object",
                {
                    'object': 'obj_test',
                    'position.x':"=randint({})".format(self.screen.get_width()),
                    'position.y':"=randint({})".format(self.screen.get_height())
                })
        )
        self.game_engine.resources['objects']['obj_solid']['mouse_global_left_pressed'] = action_sequence.ActionSequence()
        self.game_engine.resources['objects']['obj_solid']['mouse_global_left_pressed'].append_action(
            action.ObjectAction("create_object",
                {
                    'object': 'obj_test',
                    'position.x':"=mouse.x",
                    'position.y':"=mouse.y"
                })
        )
        print("Setup complete")
    def collect_event(self, event):
        self.current_events.append(event)
    def update(self):
        key_pressed = False
        mouse_button = False
        for ev in self.current_events:
            if ev.type in (pygame.KEYDOWN, pygame.KEYUP):
                key_pressed = True
                if ev.key == pygame.K_ESCAPE:
                    self.done = True
                    break
                else:
                    self.game_engine.send_key_event(ev)
            #elif ev.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):
            if ev.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                pygame.MOUSEMOTION]:
                self.game_engine.send_mouse_event(ev)
                if ev.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
                    mouse_button = True
        if not key_pressed:
            self.game_engine.send_key_event(None)
        if not mouse_button:
            self.game_engine.send_mouse_event(None)
        # done with event handling
        self.current_events = []
        for obj_name in self.game_engine.resources['objects'].keys():
            self.game_engine.resources['objects'][obj_name].update()
        # check for object instance collisions
        obj_types = self.game_engine.resources['objects'].values()
        collision_types = []
        for obj_name in self.game_engine.resources['objects'].keys():
            collision_types += self.game_engine.resources['objects'][obj_name].collision_check(obj_types)
        if len(collision_types) > 0:
            for coll_type in collision_types:
                self.game_engine.event_engine.transmit_event(coll_type)
    def draw_objects(self):
        ev = event.DrawEvent('draw')
        self.game_engine.event_engine.queue_event(ev)
        self.game_engine.event_engine.transmit_event(ev.name)
        self.game_engine.draw_mask(self.screen,
            self.game_engine.resources['objects']['obj_test'])
        if self.game_engine.resources['objects']['obj_test'].image:
            self.screen.blit(self.game_engine.resources['objects']['obj_test'].image,
                (5,5))
    def draw_background(self):
        self.screen.fill(pg_template.PygameTemplate.BLACK)
    def final_pass(self):
        pass
    def is_done(self):
        return self.done

# run from the tests directory to find the unittest_files subdirectory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

testmanager = TestGameManager()
testgame = pg_template.PygameTemplate( (640,480), "Test Game", testmanager)
testgame.run()

