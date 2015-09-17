#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# bring all the things together

import pygame
import pg_template
import pygame_maker_event as pgmev
import pygame_maker_event_engine as pgmee
import pygame_maker_language_engine as pgmle

class PyGameMakerGameEngine(object):
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
        self.event_engine = pgmee.PyGameMakerEventEngine()
        self.language_engine = pgmle.PyGameMakerLanguageEngine()
        self.symbols = pgmle.PyGameMakerSymbolTable()
        self.sprites = {}
        self.sounds = {}
        self.objects = {}
        self.mask_surface = None
        self.last_key_down = None
        self.screen = None
        self.mouse_pos = [0,0]
        self.action_blocks = {}
        self.current_events = []

    def execute_action(self, action, event):
        """
            execute_action():
            Perform an action that is not specific to existing objects.
            Parameters:
             action (PyGameMakerAction): The action instance to be executed.
             event (PyGameMakerEvent): The event that triggered the action.
        """
        # filter the action parameters
        action_params = {}
        for param in action.action_data.keys():
            if param == 'apply_to':
                continue
            action_params[param] = action.get_parameter_expression_result(
                param, self.symbols, self.language_engine)

        #print("Engine recieved action: {}".format(action))
        if action.name == "play_sound":
            if ((len(action_params['sound']) > 0) and
                (action_params['sound'] in self.sounds.keys())):
                self.sounds[action_params['sound']].play_sound()
        if action.name == "create_object":
            if (self.screen and (len(action_params['object']) > 0) and
                (action_params['object'] in self.objects.keys())):
                self.objects[action_params['object']].create_instance(
                    self.screen, action_params)

    def send_key_event(self, key_event):
        """
            send_key_event():
            Called with a keyboard event from pygame, or None if no key events
             were collected this frame. Pygame key codes will be translated
             into PyGameMakerKeyEvents with _keyup or _keydn appended to the
             name based on the pygame event received. If no keyboard event was
             received during the frame, fire off the kb_no_key event.
            Parameters:
             key_event (pygame.event): The pygame keyboard event, or None to
              signal that no button event occurred during the frame.
        """
        pk_map = pgmev.PyGameMakerKeyEvent.PYGAME_KEY_TO_KEY_EVENT_MAP
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
        ev = pgmev.PyGameMakerKeyEvent(key_event_init_name)
        #print("queue event: {}".format(ev))
        self.event_engine.queue_event(ev)
        #print("xmit event: {}".format(key_event_name))
        self.event_engine.transmit_event(key_event_name)

    def send_mouse_event(self, mouse_event):
        """
            send_mouse_event():
            Called with a mouse event collected from pygame, or None if no
             mouse button events were collected this frame. Motion events will
             simply capture the x, y of the mouse cursor. Button events will
             trigger PyGameMakerMouseEvents of the appropriate global and
             instance press or release types. If no button event was received,
             fire off the nobutton global and instance events.
            Parameters:
             mouse_event (pygame.event): The pygame mouse event, or None to
              signal that no button event occurred during the frame.
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
                    pgmev.PyGameMakerMouseEvent(
                        ev_table_entry["instance_event_name"],
                        {"position": mouse_event.pos}
                    )
                )
                event_names.append(ev_table_entry["instance_event_name"])
                #print("queue {}".format(event_names[-1]))
                self.event_engine.queue_event(
                    pgmev.PyGameMakerMouseEvent(
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
                            pgmev.PyGameMakerMouseEvent(
                                ev_table_entry["instance_pressed_name"],
                                {"position": mouse_event.pos}
                            )
                        )
                        event_names.append(ev_table_entry["instance_pressed_name"])
                        #print("queue {}".format(event_names[-1]))
                        self.event_engine.queue_event(
                            pgmev.PyGameMakerMouseEvent(
                                ev_table_entry["global_pressed_name"],
                                {"position": mouse_event.pos}
                            )
                        )
                        event_names.append(ev_table_entry["global_pressed_name"])
                        #print("queue {}".format(event_names[-1]))
                if mouse_event.type == pygame.MOUSEBUTTONUP:
                    if 'instance_released_name' in ev_table_entry:
                        self.event_engine.queue_event(
                            pgmev.PyGameMakerMouseEvent(
                                ev_table_entry["instance_released_name"],
                                {"position": mouse_event.pos}
                            )
                        )
                        event_names.append(ev_table_entry["instance_released_name"])
                        #print("queue {}".format(event_names[-1]))
                        self.event_engine.queue_event(
                            pgmev.PyGameMakerMouseEvent(
                                ev_table_entry["global_released_name"],
                                {"position": mouse_event.pos}
                            )
                        )
                        event_names.append(ev_table_entry["global_released_name"])
                        #print("queue {}".format(event_names[-1]))
        else:
            self.event_engine.queue_event(
                pgmev.PyGameMakerMouseEvent("mouse_nobutton",
                    {"position": self.mouse_pos})
            )
            event_names.append("mouse_nobutton")
            self.event_engine.queue_event(
                pgmev.PyGameMakerMouseEvent("mouse_global_nobutton",
                    {"position": self.mouse_pos})
            )
            event_names.append("mouse_global_nobutton")
        # transmit all queued event types
        for ev_name in event_names:
            #if not ev_name in ['mouse_nobutton', 'mouse_global_nobutton']:
            #    print("xmit ev {}".format(ev_name))
            self.event_engine.transmit_event(ev_name)

    def setup(self, screen):
        """
            setup():
            Called by the pygame template when pygame has been initialized.
             This is a good place to put any initialization that needs pygame
             to be set up already -- e.g. loading images and audio.
            Parameters:
             screen (pygame.Surface): The full pygame display surface itself.
              This is passed to objects so they know where the screen boundaries
              are, for transmitting boundary collision events.
        """
        self.screen = screen

    def collect_event(self, event):
        """
            collect_event():
            The pygame event queue will lose events unless they are handled.
            This method is called by the pygame template to move the events
            out of pygame and into an instance list.
        """
        self.current_events.append(event)

    def update(self):
        """
            update():
            Called by the pygame template to update object positions. This is
             also a good time to check for any keyboard or mouse events, and to
             check for and send collision events.
        """
        # keep track of whether any mouse button or key events have been
        #  received this frame
        key_pressed = False
        mouse_button = False
        for ev in self.current_events:
            if ev.type in (pygame.KEYDOWN, pygame.KEYUP):
                key_pressed = True
                # @@@@ replace this with the QUIT event, whatever it was called
                if ev.key == pygame.K_ESCAPE:
                    self.done = True
                    break
                else:
                    self.send_key_event(ev)
            if ev.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                pygame.MOUSEMOTION]:
                self.send_mouse_event(ev)
                if ev.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
                    mouse_button = True
        if not key_pressed:
            # no key events, so send the kb_no_key event
            self.send_key_event(None)
        if not mouse_button:
            # no mouse button events, so send the nobutton events
            self.send_mouse_event(None)
        # done with event handling
        self.current_events = []
        # perform position updates on all objects
        for obj_name in self.objects.keys():
            self.objects[obj_name].update()
        # check for object instance collisions
        obj_types = self.objects.values()
        collision_types = []
        for obj_name in self.objects.keys():
            collision_types += self.objects[obj_name].collision_check(obj_types)
        if len(collision_types) > 0:
            for coll_type in collision_types:
                self.event_engine.transmit_event(coll_type)

    def draw_objects(self):
        """
            draw_objects():
            Called by the pygame template to draw the foreground items.
        """
        for obj_name in self.objects.keys():
            self.objects[obj_name].draw(self.screen)

    def draw_background(self):
        """
            draw_background():
            Called by the pygame template to draw the background.
        """
        # @@@@ this should use info from the current room
        self.screen.fill(pg_template.PygameTemplate.BLACK)

