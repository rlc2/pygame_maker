#!/usr/bin/python -Wall
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Pygame maker game engine module.
"""

import os
import logging
import logging.config
import yaml
import pygame
from pygame_maker.support import logging_object
from pygame_maker.support import css_to_style
from pygame_maker.actors import object_sprite
from pygame_maker.sounds import sound
from pygame_maker.actors import object_type
from pygame_maker.scenes import background
from pygame_maker.scenes import room
from pygame_maker.events import event
from pygame_maker.events import event_engine
from pygame_maker.logic import language_engine


class GameEngineException(Exception):
    """Raised when a game has no rooms."""
    pass


class GameEngine(logging_object.LoggingObject):
    """
    The main game engine class.  Only one instance of this class is expected
    to be created.

    Call the :py:meth:`run` method to begin the main game loop.
    """
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
    # directories where game resources are expected to reside. The path names
    #  must match the resource key names
    RESOURCE_TABLE = [
        ('sprites', object_sprite.ObjectSprite),
        ('sounds', sound.Sound),
        ('objects', object_type.ObjectType),
        ('backgrounds', background.Background),
        ('rooms', room.Room),
    ]
    DEFAULT_GAME_SETTINGS = {
        "game_name": "PyGameMaker Game",
        "screen_dimensions": (640, 480),
        "frames_per_second": 60,
        "stylesheet": "",
        "logging_config": {
            "version": 1,
            "formatters": {
                "normal": {
                    "format": '%(name)s [%(levelname)s]:%(message)s'
                },
                "timestamped": {
                    "format": '%(asctime)s - %(name)s [%(levelname)s]:%(message)s'
                }
            },
            "handlers": {
                "console": {
                    "class": 'logging.StreamHandler',
                    "level": 'WARNING',
                    "formatter": "normal",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": 'logging.FileHandler',
                    "level": 'DEBUG',
                    "formatter": "timestamped",
                    "filename": "pygame_maker_game_engine.log",
                    "mode": "w"
                }
            },
            "loggers": {
                "GameEngine": {
                    "level": "INFO",
                    "handlers": ["console", "file"]
                },
                "CodeBlock": {
                    "level": "INFO",
                    "handlers": ["console", "file"]
                },
                "LanguageEngine": {
                    "level": "INFO",
                    "handlers": ["console", "file"]
                },
                "EventEngine": {
                    "level": "INFO",
                    "handlers": ["console", "file"]
                },
                "ObjectType": {
                    "level": "INFO",
                    "handlers": ["console", "file"]
                },
                "ObjectInstance": {
                    "level": "INFO",
                    "handlers": ["console", "file"]
                },
                "Room": {
                    "level": "INFO",
                    "handlers": ["console", "file"]
                },
                "CSSStyleParser": {
                    "level": "INFO",
                    "handlers": ["console", "file"]
                },
            },
        },
    }
    GAME_SETTINGS_FILE = "game_settings.yaml"
    GAME_ENGINE_ACTIONS = [
        "play_sound",
        "create_object",
        "create_object_with_velocity"
    ]

    def __init__(self):
        """
        Initialize the game engine instance.
        """
        #: The game's event engine for queuing, transmitting and receiving
        #: events
        self.event_engine = event_engine.EventEngine()
        #: The game's language engine for executing code blocks
        self.language_engine = language_engine.LanguageEngine()
        #: The dict for organizing the game's resources, so each resource
        #: can find the others
        self.resources = {
            'sprites': {},
            'sounds': {},
            'backgrounds': {},
            'fonts': {},
            'objects': {},
            'rooms': []
        }
        #: The dict containing the global game settings
        self.game_settings = dict(self.DEFAULT_GAME_SETTINGS)
        #: The main game screen created by :py:func:`pygame.display.set_mode`
        self.screen = None
        #: The surface drawn upon by other resources, copied to the main game
        #: screen each frame.  This makes it possible to create pygame
        #: sub-surfaces, which is not supported directly on hardware-
        #: accelerated screens
        self.draw_surface = None
        #: Set True to end the main game loop
        self.done = False
        #: The mouse coordinate saved each time a mouse motion event occurs
        self.mouse_pos = [0, 0]
        #: The list where pygame events get stored, so that the pygame event
        #: FIFO doesn't fill up
        self.current_events = []
        #: The list containing new objects whose creation was triggered by
        #: create_object type events
        self.new_object_queue = []
        #: The index into the ``resources['rooms']`` list, updated when a new
        #: room is loaded
        self.room_index = 0
        #: Store a :py:class:`pygame.time.Clock` instance, used for
        #: controlling the frame rate
        self.clock = None

        self.load_game_settings()

        if 'logging_config' in list(self.game_settings.keys()):
            logging.config.dictConfig(self.game_settings['logging_config'])
        else:
            logging.basicConfig(level=logging.WARNING)

        # Now that logging has been configured, initialize the LoggingObject
        # base class.
        super(GameEngine, self).__init__(type(self).__name__)

        self.info("Loading game resources..")
        self.global_style_settings = None
        if "stylesheet" in self.game_settings and len(self.game_settings["stylesheet"]) > 0:
            with open(self.game_settings["stylesheet"], "r") as style_f:
                self.global_style_settings = css_to_style.CSSStyleGenerator.get_css_style(
                    style_f.read())

        with logging_object.Indented(self):
            self.load_game_resources()

        if len(self.resources['rooms']) == 0:
            raise GameEngineException("No game room resource found")

    def load_game_settings(self):
        """
        Collect the settings for the game itself, expected to be found in a
        file in the base game directory named ``game_settings.yaml``.

        The YAML format follows::

            game_name: <name>
            screen_dimensions: [<width>, <height>]
            frames_per_second: <positive integer>
            stylesheet: <name of CSS-formatted file>
            logging_config:
              version: 1
              formatters:
                normal:
                  format: '%(name)s [%(levelname)s]:%(message)s'
                timestamped:
                  format: '%(asctime)s - %(name)s [%(levelname)s]:%(message)s'
              handlers:
                console:
                  class: logging.StreamHandler
                  level: WARNING
                  formatter: normal
                  stream: ext://sys.stdout
            # uncomment the lines below starting with 'file:' to create a log file
            # remember to change the 'handlers:' lines below to add the file handler, E.G.:
            # handlers: [console, file]
            #    file:
            #      class: logging.FileHandler
            #      level: WARNING
            #      formatter: timestamped
            #      filename: pygame_maker_game_engine.log
            #      mode: w
              loggers:
                GameEngine:
                  level: INFO
                  handlers: [console]
                CodeBlock:
                  level: INFO
                  handlers: [console]
                LanguageEngine:
                  level: INFO
                  handlers: [console]
                EventEngine:
                  level: INFO
                  handlers: [console]
                ObjectType:
                  level: INFO
                  handlers: [console]
                ObjectInstance:
                  level: INFO
                  handlers: [console]
                Room:
                  level: INFO
                  handlers: [console]
                CSSStyleParser:
                  level: INFO
                  handlers: [console]
        """
        if os.path.exists(self.GAME_SETTINGS_FILE):
            with open(self.GAME_SETTINGS_FILE, "r") as yaml_f:
                yaml_info = yaml.load(yaml_f)
                if yaml_info:
                    for yaml_key in list(yaml_info.keys()):
                        if yaml_key in self.game_settings:
                            self.game_settings[yaml_key] = yaml_info[yaml_key]

    def _fix_file_path(self, subdir, resource):
        if hasattr(resource, 'filename'):
            # Append the subdirectory to resource filenames.
            if isinstance(resource.filename, str) and "/" not in resource.filename:
                resource.filename = "{}/{}".format(subdir, resource.filename)

    def load_game_resources(self):
        """
        Bring in resource YAML files from their expected directories:
        ``sprites/``, ``backgrounds/``, ``sounds/``, ``objects/``, and
        ``rooms/``
        """
        topdir = os.getcwd()
        for res_path, res_type in self.RESOURCE_TABLE:
            self.info("Loading {}..".format(res_path))
            if not os.path.exists(res_path):
                continue
            # resource directories are expected to contain YAML descriptions
            #  for each of their respective resource types.  Sprites and sounds
            #  may also contain image or sound files, respectively, so filter
            #  out files with other extensions.  Any file name(s) in the
            #  resource directories ending in .yaml or .yml will be processed.
            res_files = os.listdir(res_path)
            res_yaml_files = []
            for resf in res_files:
                if resf.endswith('.yaml') or resf.endswith('.yml'):
                    res_yaml_files.append(resf)
            # need to chdir, since the filenames found in YAML resource
            #  files are assumed to be relative to the YAML resource's path
            os.chdir(res_path)
            with logging_object.Indented(self):
                for res_file in res_yaml_files:
                    self.info("Import {}".format(res_file))
                    with open(res_file, "r") as yaml_f:
                        new_resources = res_type.load_from_yaml(yaml_f, self)
                    if res_path != "rooms":
                        with logging_object.Indented(self):
                            for res in new_resources:
                                # if multiple resources have the same name, the
                                # last one read in will override the others
                                self.debug("{}".format(res))
                                self._fix_file_path(res_path, res)
                                self.resources[res_path][res.name] = res
                    else:
                        # rooms are meant to stay in order
                        self.resources[res_path] = new_resources
            os.chdir(topdir)

    def execute_action(self, action, an_event, instance=None):
        """
        Perform an action that is not specific to existing objects.

        Many actions are handled by object instances, but the rest must be
        handled here.

        :param action: The action instance to be executed
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        :param an_event: The event that triggered the action
        :type an_event: :py:class:`~pygame_maker.events.event.Event`
        :param instance: If supplied, the object instance that initiated the
            action
        :type instance: :py:class:`~pygame_maker.actors.simple_object_instance.SimpleObjectInstance`
        """
        # filter the action parameters
        action_params = {}
        for param in list(action.action_data.keys()):
            if param == 'apply_to':
                continue
            if param == 'child_instance':
                if action.action_data['child_instance'] and instance is not None:
                    # create_object: connect the child instance to its parent that
                    #   forwarded this action
                    action_params['parent'] = instance
                continue
            action_params[param] = action.get_parameter_expression_result(
                param, self.language_engine.global_symbol_table, self.language_engine)

        # print("Engine received action: {}".format(action))
        self.debug("Handle action '{}'".format(action.name))
        self.bump_indent_level()
        if action.name == "play_sound":
            if ((len(action_params['sound']) > 0) and
                    (action_params['sound'] in list(self.resources['sounds'].keys()))):
                self.debug("Playing sound '{}'".format(action_params['sound']))
                self.resources['sounds'][action_params['sound']].play_sound()
            else:
                self.debug("Sound '{}' not played".format(action_params['sound']))
        elif action.name in ["create_object", "create_object_with_velocity"]:
            if (self.screen and (len(action_params['object']) > 0) and
                    (action_params['object'] in list(self.resources['objects'].keys()))):
                self.info("Creating object '{}'".format(action_params['object']))
                self.new_object_queue.append(
                    (self.resources['objects'][action_params['object']], action_params))
            else:
                self.debug("Object '{}' not created".format(action_params['object']))
        else:
            self.debug("No handler for action '{}'".format(action.name))
        self.drop_indent_level()

    def send_key_event(self, key_event):
        """
        Handle a keyboard event received from pygame.

        Pygame key codes will be translated into KeyEvents with _keyup or
        _keydn appended to the name based on the pygame event received.  If no
        keyboard event was received during the frame, fire off the kb_no_key
        event.

        :param key_event: The pygame keyboard event, or None to
            signal that no button event occurred during the frame.
        :type key_event: None | :py:class:`~pygame_maker.events.event.Event`
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
        # print("queue event: {}".format(kev))
        self.event_engine.queue_event(kev)
        # print("xmit event: {}".format(key_event_name))
        self.event_engine.transmit_event(key_event_init_name)
        self.debug("Event '{}' queued and transmitted".format(key_event_init_name))

    def send_mouse_event(self, mouse_event):
        """
        Handle a mouse event received from pygame.

        Motion events will simply capture the x, y of the mouse cursor.  Button
        events will trigger MouseEvents of the appropriate global and instance
        press or release types.  If no button event was received, fire off the
        nobutton global and instance events.

        :param mouse_event: The pygame mouse event, or None to signal that no
            button event occurred during the frame.
        :type mouse_event: None | :py:class:`~pygame_maker.events.event.Event`
        """
        if mouse_event:
            self.mouse_pos[0] = mouse_event.pos[0]
            self.mouse_pos[1] = mouse_event.pos[1]
            self.language_engine.global_symbol_table.set_constant(
                'mouse.x', self.mouse_pos[0])
            self.language_engine.global_symbol_table.set_constant(
                'mouse.y', self.mouse_pos[1])
            if mouse_event.type == pygame.MOUSEMOTION:
                return
        event_names = []
        if mouse_event:
            mouse_button = mouse_event.button
            if len(self.MOUSE_EVENT_TABLE) > mouse_button:
                ev_table_entry = self.MOUSE_EVENT_TABLE[mouse_button]
                # print("select mouse entries {}".format(ev_table_entry))
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
                # print("queue {}".format(event_names[-1]))
                self.event_engine.queue_event(
                    event.MouseEvent(
                        ev_table_entry["global_event_name"],
                        {"position": mouse_event.pos}
                    )
                )
                event_names.append(ev_table_entry["global_event_name"])
                # print("queue {}".format(event_names[-1]))
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
                        # print("queue {}".format(event_names[-1]))
                        self.event_engine.queue_event(
                            event.MouseEvent(
                                ev_table_entry["global_pressed_name"],
                                {"position": mouse_event.pos}
                            )
                        )
                        event_names.append(ev_table_entry["global_pressed_name"])
                        # print("queue {}".format(event_names[-1]))
                if mouse_event.type == pygame.MOUSEBUTTONUP:
                    if 'instance_released_name' in ev_table_entry:
                        self.event_engine.queue_event(
                            event.MouseEvent(
                                ev_table_entry["instance_released_name"],
                                {"position": mouse_event.pos}
                            )
                        )
                        event_names.append(ev_table_entry["instance_released_name"])
                        # print("queue {}".format(event_names[-1]))
                        self.event_engine.queue_event(
                            event.MouseEvent(
                                ev_table_entry["global_released_name"],
                                {"position": mouse_event.pos}
                            )
                        )
                        event_names.append(ev_table_entry["global_released_name"])
                        # print("queue {}".format(event_names[-1]))
        else:
            self.event_engine.queue_event(
                event.MouseEvent("mouse_nobutton", {"position": self.mouse_pos}))
            event_names.append("mouse_nobutton")
            self.event_engine.queue_event(
                event.MouseEvent("mouse_global_nobutton", {"position": self.mouse_pos}))
            event_names.append("mouse_global_nobutton")
        # transmit all queued event types
        for ev_name in event_names:
            self.event_engine.transmit_event(ev_name)
            if ev_name not in ['mouse_nobutton', 'mouse_global_nobutton']:
                self.debug("Event '{}' queued and transmitted".format(ev_name))

    def setup(self, screen):
        """
        Called by :py:meth:`run` after pygame has been initialized.

        This is a good place to put any initialization that needs pygame to be
        set up already -- e.g. loading images and audio.

        :param screen: The main pygame display surface
        :type screen: :py:class:`pygame.Surface`
        """
        self.info("Setup:")
        with logging_object.Indented(self):
            self.screen = screen
            self.language_engine.global_symbol_table.set_constant('screen_width', screen.get_width())
            self.language_engine.global_symbol_table.set_constant('screen_height', screen.get_height())
            self.info("Pre-load game resources..")
            with logging_object.Indented(self):
                self.setup_game_resources()
            self.info("Load first room..")
            with logging_object.Indented(self):
                self.load_room(0)

    def setup_game_resources(self):
        """
        Call the ``setup()`` method of every resource type that supplies one.
        """
        topdir = os.getcwd()
        if os.path.exists('sprites'):
            self.info("Preloading sprite images..")
            with logging_object.Indented(self):
                for spr in list(self.resources['sprites'].keys()):
                    self.info("{}".format(spr))
                    self.resources['sprites'][spr].setup()
        sound_dir = os.path.join(topdir, 'sounds')
        if os.path.exists(sound_dir):
            self.info("Preloading sound files..")
            with logging_object.Indented(self):
                for snd in list(self.resources['sounds'].keys()):
                    self.info("{}".format(snd))
                    self.resources['sounds'][snd].setup()
        background_dir = os.path.join(topdir, 'backgrounds')
        if os.path.exists(background_dir):
            self.info("Preloading background images..")
            with logging_object.Indented(self):
                for bkg in list(self.resources['backgrounds'].keys()):
                    self.info("{}".format(bkg))
                    self.resources['backgrounds'][bkg].setup()
        os.chdir(topdir)

    def load_room(self, room_n):
        """
        Initialize the given room number.

        Create the room's objects and run its init block (if any).

        :param room_n: The number of the room to load (starting from 0)
        :type room_n: int
        """
        self.info("Loading room {:d} ('{}')..".format(
            room_n, self.resources['rooms'][room_n].name))
        self.room_index = room_n
        room_width = self.resources['rooms'][room_n].width
        room_height = self.resources['rooms'][room_n].height
        # Create a new surface the same size as the room. This can differ from
        #  the screen dimensions. Also, for HWSURFACE displays, this allows the
        #  draw surface to be subsurface()'d, according to pygame documentation.
        #pylint: disable=too-many-function-args
        self.draw_surface = pygame.Surface((room_width, room_height))
        #pylint: enable=too-many-function-args
        self.resources['rooms'][room_n].draw_room_background(self.draw_surface)
        self.resources['rooms'][room_n].load_room(self.draw_surface)
        self.language_engine.global_symbol_table.set_constant('room_width', room_width)
        self.language_engine.global_symbol_table.set_constant('room_height', room_height)
        self.info("Room {:d} loaded.".format(room_n))

    def collect_event(self, an_event):
        """
        The pygame event queue will lose events unless they are handled.  This
        method is called by :py:meth:`run` to move the events out of pygame and
        into a list.

        :param an_event: The event received from pygame
        :type an_event: :py:class:`pygame.event.EventType`
        """
        self.current_events.append(an_event)

    def update(self):
        """
        Called by :py:meth:`run()` to update all object instance positions.

        This is also a good time to check for any keyboard or mouse events, and
        to check for and send collision events.
        """
        # keep track of whether any mouse button or key events have been
        #  received this frame
        key_pressed = False
        mouse_button = False
        # create any new objects that were queued by create_object* events
        for new_obj, params in self.new_object_queue:
            # This will transmit a 'create' event that will be received by the
            #  new instance; I.E., all 'create' events happen here
            new_obj.create_instance(self.draw_surface, params)
        # clear the queue for next frame
        self.new_object_queue = []
        # begin_step happens before other events, but after create (new
        #  instances receive all events)
        sev = event.StepEvent('begin_step')
        self.event_engine.queue_event(sev)
        self.event_engine.transmit_event(sev.name)
        while len(self.current_events) > 0:
            cev = self.current_events.pop()
            if cev.type == pygame.QUIT:
                self.done = True
                break
            elif cev.type in (pygame.KEYDOWN, pygame.KEYUP):
                key_pressed = True
                if cev.key == pygame.K_ESCAPE:
                    self.done = True
                    break
                else:
                    self.send_key_event(cev)
            elif cev.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                              pygame.MOUSEMOTION]:
                self.send_mouse_event(cev)
                if cev.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
                    mouse_button = True
        if not key_pressed:
            # no key events, so send the kb_no_key event
            self.send_key_event(None)
        if not mouse_button:
            # no mouse button events, so send the nobutton events
            self.send_mouse_event(None)
        # normal_step happens before updating object instance positions
        sev = event.StepEvent('normal_step')
        self.event_engine.queue_event(sev)
        self.event_engine.transmit_event(sev.name)
        # perform position updates on all objects
        for obj_name in list(self.resources['objects'].keys()):
            self.resources['objects'][obj_name].update()
        # check for object instance collisions
        obj_types = list(self.resources['objects'].values())
        collision_types = set()
        for obj_name in list(self.resources['objects'].keys()):
            collision_types |= self.resources['objects'][obj_name].collision_check(obj_types)
        if len(collision_types) > 0:
            for coll_type in collision_types:
                self.event_engine.transmit_event(coll_type)

    def draw_objects(self):
        """Called by :py:meth:`run` to draw the foreground items."""
        # end_step happens just before drawing object instances
        sev = event.StepEvent('end_step')
        self.event_engine.queue_event(sev)
        self.event_engine.transmit_event(sev.name)
        drev = event.DrawEvent('draw')
        self.event_engine.queue_event(drev)
        self.event_engine.transmit_event(drev.name)

    def draw_background(self):
        """Called by :py:meth:`run` to draw the room background."""
        if self.room_index < len(self.resources['rooms']):
            self.resources['rooms'][self.room_index].draw_room_background(self.draw_surface)

    def final_pass(self):
        """Copy the room's pixels onto the display."""
        self.screen.blit(self.draw_surface, (0, 0))

    def is_done(self):
        """Report game's 'done' state."""
        return self.done

    def run(self):
        """
        The main game event loop.

        Run :py:func:`pygame.init` first, then call :py:meth:`setup` to run
        all operations that require ``pygame.init()``, prior to entering the
        loop.
        """
        pygame.init()
        self.screen = pygame.display.set_mode(self.game_settings['screen_dimensions'])
        self.setup(self.screen)
        pygame.display.set_caption(self.game_settings['game_name'])
        self.clock = pygame.time.Clock()

        # --- Main Loop ---
        while not self.done:
            for an_event in pygame.event.get():
                self.collect_event(an_event)

            # --- Game Logic ---
            self.update()

            #self.screen.fill(self.WHITE)
            # --- Drawing ---
            self.draw_background()
            self.draw_objects()

            # update screen
            self.final_pass()
            pygame.display.flip()

            # limit frame rate
            self.clock.tick(self.game_settings['frames_per_second'])

        # close window & quit
        pygame.quit()

if __name__ == "__main__":
    GAME_ENGINE = GameEngine()
    GAME_ENGINE.run()
