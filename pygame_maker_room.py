#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker rooms

import pygame
import yaml
import pygame_maker_action as pgm_action
import pygame_maker_color as pgm_color

class PyGameMakerRoomException(Exception):
    pass

class PyGameMakerRoom(object):
    """
        class PyGameMakerRoom:
        Represent "rooms" in PyGame Maker, which are where all actions happen.
    """
    DEFAULT_BACKGROUND_COLOR = pgm_color.PyGameMakerColor( (0,0,0) )
    DEFAULT_DIMENSIONS=(640, 480)
    DEFAULT_FRAME_RATE=30
    DEFAULT_NAME="rm_"
    DEFAULT_LOCATION_XY=(0,0)
    ATTRIBUTES_TABLE={
        'width':                        int,
        'height':                       int,
        'speed':                        float,
        'persistent':                   bool,
        'init_code':                    str,
        'background':                   str,
        'background_color':             pgm_color.PyGameMakerColor,
        'draw_background_color':        bool,
        'background_horizontal_offset': int,
        'background_vertical_offset':   int,
        'background_visible':           bool,
        'tile_horizontal':              bool,
        'tile_vertical':                bool,
        'stretch:':                     bool,
        'grid_x_offset':                int,
        'grid_y_offset':                int,
        'grid_width':                   int,
        'grid_height':                  int,
    }

    @staticmethod
    def load_from_yaml(yaml_file_name, game_engine):
        """
            load_from_yaml():
            Create room(s) from a YAML-formatted file.
            Expected format (missing fields will receive default values):
            - rm_name1:
                width: <# >= 0>
                height: <# >= 0>
                speed: <number>
                persistent: True | False
                init_code: |
                    code block...
                background: <background_resource_name>
                background_color: <#RRGGBB | (R, G, B)>
                draw_background_color: True | False
                background_horizontal_offset: <# >= 0>
                background_vertical_offset: <# >= 0>
                background_visible: True | False
                tile_horizontal: True | False
                tile_vertical: True | False
                stretch: True | False
                grid_x_offset: <# >= 0>
                grid_y_offset: <# >= 0>
                grid_width: <# >= 0>
                grid_height: <# >= 0>
                object_instances:
                    - <obj_resource_name>:
                        position: [<pos_x>,<pos_y>]
                        init_code: |
                          init_code_block

        """
        yaml_repr = None
        new_room_list = []
        with open(yaml_file_name, "r") as yaml_f:
            yaml_repr = yaml.load(yaml_f)
        if yaml_repr:
            for top_level in yaml_repr:
                kwargs = {}
                room_name = top_level.keys()[0]
                room_yaml = top_level[room_name]
                for attr in PyGameMakerRoom.ATTRIBUTES_TABLE.keys():
                    if attr in room_yaml.keys():
                        kwargs[attr] = room_yaml[attr]
                if 'object_instances' in room_yaml.keys():
                    kwargs['object_instances'] = room_yaml['object_instances']
                new_room_list.append(PyGameMakerRoom(room_name, game_engine,
                    **kwargs))
            return new_room_list

    def __init__(self, name, game_engine, **kwargs):
        self.name = name
        self.game_engine = game_engine
        self.width = self.DEFAULT_DIMENSIONS[0]
        self.height = self.DEFAULT_DIMENSIONS[1]
        self.frame_rate = self.DEFAULT_FRAME_RATE 
        self.persistent = False
        self._init_code = ""
        self.init_code_block = None
        self.init_object_instances = []
        self.object_instances = []
        self.background = None
        self.draw_background_color = True
        self.tile_horizontal = True
        self.tile_vertical = True
        self.stretch = False
        self.background_color = self.DEFAULT_BACKGROUND_COLOR
        self._background_horizontal_offset = 0
        self._background_vertical_offset = 0
        self.background_offsets = [0,0]
        self.background_visible = False
        self.grid = pygame.Rect(0,0,16,16)
        self.cached_background = None
        self.cached_rect = pygame.Rect(0,0,0,0)
        self.bkg_width = 0
        self.bkg_height = 0
        self.disp_width = 0
        self.disp_height = 0
        if kwargs:
            for attr in self.ATTRIBUTES_TABLE.keys():
                if attr in kwargs:
                    attr_type = self.ATTRIBUTES_TABLE[attr]
                    if attr_type != bool:
                        setattr(self, attr, attr_type(kwargs[attr]))
                    else:
                        setattr(self, attr, (kwargs[attr] == True))
            if 'object_instances' in kwargs:
                # This is a list of hashes inside hashes containing info
                #  about objects to be placed when the room is loaded.
                #  E.G. [{'obj_name1': {'position':(10,10)}},...]
                obj_list = list(kwargs['object_instances'])
                for obj_check in obj_list:
                    obj_ok = True
                    err_msg = ""
                    init_code = None
                    obj_name = obj_check.keys()[0]
                    if not 'position' in obj_check[obj_name]:
                        obj_ok = False
                        err_msg = "Missing position for object '{}'".format(obj_name)
                    pos_list = list(obj_check[obj_name]['position'])
                    if len(pos_list) < 2:
                        obj_ok = False
                        err_msg = "Invalid position '{}' for object '{}'".format(obj_check[obj_name]['position'], obj_name)
                    if 'init_code' in obj_check[obj_name].keys():
                        if (not isinstance(obj_check[obj_name]['init_code'],
                            str)):
                            obj_ok = False
                            err_msg = "Invalid code block '{}' for object '{}'".format(obj_check[obj_name]['init_code'], obj_name)
                        init_code = obj_check[obj_name]['init_code']
                    if not obj_ok:
                        raise(PyGameMakerRoomException("{}: Failed to create room: {}".format(type(self).__name__, err_msg)))
                    self.add_init_object_instance_at(obj_name,
                        obj_check[obj_name]['position'], init_code)


    @property
    def init_code(self):
        return self._init_code

    @init_code.setter
    def init_code(self, value):
        self._init_code = value
        self.set_init_code_block(value)

    @property
    def background_horizontal_offset(self):
        return self._background_horizontal_offset

    @background_horizontal_offset.setter
    def background_horizontal_offset(self, value):
        self._background_horizontal_offset = value
        self.background_offsets[0] = value

    @property
    def background_vertical_offset(self):
        return self._background_vertical_offset

    @background_vertical_offset.setter
    def background_vertical_offset(self, value):
        self._background_vertical_offset = value
        self.background_offsets[1] = value

    def add_init_object_instance_at(self, object_type_name, locationxy,
        init_code=None):
        """
            add_init_object_instance_at():
            Add to the list of object instances that should be created when
            the room is loaded.
            parameters:
              object_type (str): Name of the kind of object to place
              locationxy (list): The x,y coordinates
              init_code (str): Source code to execute when the instance is
               created
        """
        loc = []
        loc.append(int(locationxy[0]))
        loc.append(int(locationxy[1]))
        self.init_object_instances.append( (object_type_name, loc, init_code) )

    def add_object_instance_at(self, surface, object_type_name, locationxy,
        init_code):
        """
            add_object_instance_at():
            Create a new object instance in the room.
            parameters:
              surface (pygame.Surface): Usually the game screen
              object_type (str): Name of the kind of object to place
              locationxy (list): The x,y coordinates
              init_code (str or None): Optional source code block to run after
               creating the instance
        """
        if object_type_name in self.game_engine.resources['objects'].keys():
            self.object_instances.append(self.game_engine.resources['objects'][object_type_name].create_instance(surface, position=locationxy))
            new_obj = self.object_instances[-1]
            print("Room {}: Created obj {} id {}".format(self.name,
                object_type_name, new_obj.id))
            if init_code:
                # Create a throw-away code action, and send it to the new
                #  instance's execute_code method.
                code_action = pgm_action.PyGameMakerCodeAction('execute_code',
                    code=init_code)
                self.object_instances[-1].execute_code(code_action,
                    keep_code_block=False)

    def set_init_code_block(self, code_block_string):
        """
            set_init_code_block():
            Set the initialization code block to be run when the room is
            loaded.
            Parameters:
              language_engine (PyGameMakerLanguageEngine): Language engine
              code_block_string: Source code string in toy language
        """
        self.init_code_block = self.game_engine.language_engine.register_code_block("{}_init".format(self.name), code_block_string)

    def set_background(self, background):
        """
            set_background():
            Select a background resource to draw onto the room
            Parameters:
              background: An instance of PyGameMakerBackground
        """
        self.background = background

    def load_room(self, surface):
        """
            load_room():
            Load the background, if any. Create the room's objects. Run the
             init_code_block.
            Parameters:
             surface (pygame.Surface): Usually the game screen
        """
        if (self.background and (self.background in
            self.game_engine.resources['backgrounds'].keys())):
            self.game_engine.resources['backgrounds'][self.background].load_graphic()
        if self.init_code_block:
            self.game_engine.language_engine.execute_code_block("{}_init".format(self.name))
        # instantiate objects in the init_object_instances list
        for an_object, positionxy, init_code in self.init_object_instances:
            self.add_object_instance_at(surface, an_object, positionxy,
                init_code)

    def draw_room_background(self, surface):
        """
            draw_room_background()
            Clear the surface to the background color, then draw the background
            image (if any) on top of it.
            Parameters:
              surface (pygame.Surface): Usually the game screen
        """
        if self.draw_background_color:
            surface.fill(self.background_color.color)
        # draw the background
        if self.background:
            # draw background image, if any
            if self.background in self.game_engine.resources['backgrounds'].keys():
                bkg = self.game_engine.resources['backgrounds'][self.background]
                if ((self.disp_width != surface.get_width()) or
                    (self.disp_height != surface.get_height())):
                    if self.cached_background:
                        # What happened here?!
                        raise(PyGameMakerRoomException("{}.draw_room_background: display surface changed dimensions!".format(type(self).__name__)))
                    self.disp_width = surface.get_width()
                    self.disp_height = surface.get_height()
                if self.cached_background:
                    # The background is already done, so copy it to the display
                    surface.blit(self.cached_background,
                        (self.cached_rect[0],self.cached_rect[1]),
                        area=self.cached_rect)
                elif bkg.image:
                    # Draw to the background cache so these calculations only
                    #  need to happen once.
                    rows = 1
                    cols = 1
                    if (self.bkg_width != bkg.image.get_width()):
                        self.bkg_width = bkg.image.get_width()
                    if (self.bkg_height != bkg.image.get_height()):
                        self.bkg_height = bkg.image.get_height()
                    self.cached_background = surface.copy()
                    self.cached_rect.x = self.background_offsets[0]
                    self.cached_rect.y = self.background_offsets[1]
                    if bkg.tileset:
                        # Tilesets already know how to cover the display.
                        print("Cache tiled background..")
                        self.cached_rect.width = self.disp_width - self.background_offsets[0]
                        self.cached_rect.height = self.disp_height - self.background_offsets[1]
                        bkg.draw_background(self.cached_background,
                            self.background_offsets)
                    else:
                        # A simple background image can be tiled
                        #  horizontally and/or vertically using room
                        #  settings. Remember to account for x,y offsets.
                        print("Cache normal background")
                        pix_width = self.disp_width - self.background_offsets[0]
                        if self.tile_horizontal and (self.bkg_width < pix_width):
                            cols = pix_width / self.bkg_width
                            overage = pix_width % self.bkg_width
                            if overage != 0:
                                cols += 1
                        pix_height = self.disp_height - self.background_offsets[1]
                        if self.tile_vertical and (self.bkg_height < pix_height):
                            rows = pix_height / self.bkg_height
                            overage = pix_height % self.bkg_height
                            if overage != 0:
                                rows += 1
                        self.cached_rect.height = (rows * self.bkg_height)
                        self.cached_rect.width = (cols * self.bkg_width)
                        for bkg_row in range(rows):
                            for bkg_col in range(cols):
                                offsets = []
                                offsets.append(self.background_offsets[0] +
                                    bkg_col * self.bkg_width)
                                offsets.append(self.background_offsets[1] +
                                    bkg_row * self.bkg_height)
                                bkg.draw_background(self.cached_background,
                                    offsets)


if __name__ == "__main__":
    import pg_template
    import tempfile
    import os
    import pygame_maker_background as pgm_background
    import pygame_maker_language_engine as pgm_language_engine
    import pygame_maker_sound as pgm_sound
    import pygame_maker_sprite as pgm_sprite
    import pygame_maker_object as pgm_object
    import pygame_maker_event as pgm_event
    import pygame_maker_event_engine as pgm_event_engine

    TEST_BACKGROUND_LIST_YAML_FILE="unittest_files/test_backgrounds.yaml"
    TEST_ROOM_LIST_YAML_FILE="unittest_files/test_rooms.yaml"
    TEST_SPRITE_LIST_YAML_FILE="unittest_files/test_sprites.yaml"
    TEST_OBJECT_LIST_YAML_FILE="unittest_files/test_objects.yaml"
    TEST_SOUND_LIST_YAML_FILE="unittest_files/test_sounds.yaml"

    class MyGameManager:
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
            self.current_events = []
            self.resources = {
                'rooms': [],
                'sprites': {},
                'sounds': {},
                'objects': {},
                'backgrounds': {}
            }
            self.language_engine = pgm_language_engine.PyGameMakerLanguageEngine()
            self.symbols = pgm_language_engine.PyGameMakerSymbolTable()
            self.event_engine = pgm_event_engine.PyGameMakerEventEngine()
            self.text_objects = []
            backgrounds = pgm_background.PyGameMakerBackground.load_from_yaml(TEST_BACKGROUND_LIST_YAML_FILE)
            for bkg in backgrounds:
                self.resources['backgrounds'][bkg.name] = bkg
            if len(self.resources['backgrounds'].keys()) == 0:
                print("Unable to load backgrounds from {}, aborting.".format(TEST_BACKGROUND_LIST_YAML_FILE))
                exit(1)
            sprites = pgm_sprite.PyGameMakerSprite.load_from_yaml(TEST_SPRITE_LIST_YAML_FILE)
            for spr in sprites:
                self.resources['sprites'][spr.name] = spr
            if len(self.resources['sprites'].keys()) == 0:
                print("Unable to load sprites from {}, aborting.".format(TEST_SPRITE_LIST_YAML_FILE))
            sounds = pgm_sound.PyGameMakerSound.load_from_yaml(TEST_SOUND_LIST_YAML_FILE)
            for snd in sounds:
                self.resources['sounds'][snd.name] = snd
            if len(self.resources['sounds']) == 0:
                print("Unable to load sounds from {}, aborting.".format(TEST_SOUND_LIST_YAML_FILE))
            objects = pgm_object.PyGameMakerObject.load_from_yaml(TEST_OBJECT_LIST_YAML_FILE, self)
            for obj in objects:
                self.resources['objects'][obj.name] = obj
            if len(self.resources['objects']) == 0:
                print("Unable to load objects from {}, aborting.".format(TEST_OBJECT_LIST_YAML_FILE))
            self.resources['rooms'] = PyGameMakerRoom.load_from_yaml(TEST_ROOM_LIST_YAML_FILE, self)
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
            pk_map = pgm_event.PyGameMakerKeyEvent.PYGAME_KEY_TO_KEY_EVENT_MAP
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
            ev = pgm_event.PyGameMakerKeyEvent(key_event_init_name)
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
                        pgm_event.PyGameMakerMouseEvent(
                            ev_table_entry["instance_event_name"],
                            {"position": mouse_event.pos}
                        )
                    )
                    event_names.append(ev_table_entry["instance_event_name"])
                    #print("queue {}".format(event_names[-1]))
                    self.event_engine.queue_event(
                        pgm_event.PyGameMakerMouseEvent(
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
                                pgm_event.PyGameMakerMouseEvent(
                                    ev_table_entry["instance_pressed_name"],
                                    {"position": mouse_event.pos}
                                )
                            )
                            event_names.append(ev_table_entry["instance_pressed_name"])
                            #print("queue {}".format(event_names[-1]))
                            self.event_engine.queue_event(
                                pgm_event.PyGameMakerMouseEvent(
                                    ev_table_entry["global_pressed_name"],
                                    {"position": mouse_event.pos}
                                )
                            )
                            event_names.append(ev_table_entry["global_pressed_name"])
                            #print("queue {}".format(event_names[-1]))
                    if mouse_event.type == pygame.MOUSEBUTTONUP:
                        if 'instance_released_name' in ev_table_entry:
                            self.event_engine.queue_event(
                                pgm_event.PyGameMakerMouseEvent(
                                    ev_table_entry["instance_released_name"],
                                    {"position": mouse_event.pos}
                                )
                            )
                            event_names.append(ev_table_entry["instance_released_name"])
                            #print("queue {}".format(event_names[-1]))
                            self.event_engine.queue_event(
                                pgm_event.PyGameMakerMouseEvent(
                                    ev_table_entry["global_released_name"],
                                    {"position": mouse_event.pos}
                                )
                            )
                            event_names.append(ev_table_entry["global_released_name"])
                            #print("queue {}".format(event_names[-1]))
            else:
                self.event_engine.queue_event(
                    pgm_event.PyGameMakerMouseEvent("mouse_nobutton",
                        {"position": self.mouse_pos})
                )
                event_names.append("mouse_nobutton")
                self.event_engine.queue_event(
                    pgm_event.PyGameMakerMouseEvent("mouse_global_nobutton",
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

        def is_done(self):
            return self.done

    mymanager = MyGameManager()
    mygame = pg_template.PygameTemplate( mymanager.largest_dims, "Room Tests",
        mymanager)
    mygame.run()

