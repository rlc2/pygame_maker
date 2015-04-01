#!/usr/bin/python -Wall

# pygame maker events

import pygame
import re

class PyGameMakerEventError(Exception):
    pass

class PyGameMakerEvent:
    OBJECT_STATE_EVENTS=[
        "create",
        "destroy"
    ]
    ALARM_COUNT=12
    ALARM_EVENTS=["alarm{}".format(n) for n in range(0,ALARM_COUNT)]
    STEP_EVENTS=[
        "normal_step",
        "begin_step",
        "end_step"
    ]
    MOUSE_EVENTS=[
        "button_left",
        "button_right",
        "button_middle",
        "button_6"
        "button_7"
        "button_8"
        "nobutton",
        "left_pressed",
        "right_pressed",
        "middle_pressed",
        "left_released",
        "right_released",
        "middle_released",
        "mouse_enter",
        "mouse_leave",
        "mousewheelup",
        "mousewheeldown"
    ]
    OTHER_EVENTS=[
        "outside_room",
        "intersect_boundary",
        "game_start",
        "game_end",
        "room_start",
        "room_end",
        "no_lives",
        "animation_end",
        "end_of_path",
        "out_of_health",
        "close_button",
        "user_defined_0",
        "user_defined_1",
        "user_defined_2",
        "user_defined_3",
        "user_defined_4",
        "user_defined_5",
        "user_defined_6",
        "user_defined_7",
        "image_loaded",
        "sound_loaded"
    ]
    DRAW_EVENTS=[
        "draw",
        "gui",
        "resize"
    ]
    ARROW_KEYS=[
        "left",
        "right",
        "up",
        "down",
    ]
    META_KEYS=[
        "lctrl",
        "rctrl",
        "lalt",
        "ralt",
        "lshift",
        "rshift",
        "lmeta",
        "rmeta",
        "lsuper",
        "rsuper"
    ]
    KEYPAD_KEYS=[
        "np0",
        "np1",
        "np2",
        "np3",
        "np4",
        "np5",
        "np6",
        "np7",
        "np8",
        "np9",
        "np/",
        "np*",
        "np-",
        "np+",
        "np.",
        "np=",
        "npenter",
    ]
    PUNCTUATION_KEYS=[
        ",",
        ".",
        "/",
        ";",
        "'",
        "[",
        "]",
        "-",
        "=",
        "`",
        "\\"
    ]
    DIGIT_KEYS=[str(k) for k in range(0,10)]
    LETTER_KEYS=[chr(l) for l in range(65, 65+26)]
    FUNCTION_KEYS=["F{}".format(n) for n in range(1,13)]
    OTHER_KEYS=[
        "no_key",
        "any_key",
        "space",
        "enter",
        "backspace",
        "escape",
        "home",
        "end",
        "pageup",
        "pagedown",
        "delete",
        "insert"
    ]
    KEYBOARD_EVENT_KEY_CATEGORIES={
        "arrows":   ARROW_KEYS,
        "meta":     META_KEYS,
        "keypad":   KEYPAD_KEYS,
        "digits":   DIGIT_KEYS,
        "letters":  LETTER_KEYS,
        "function": FUNCTION_KEYS,
        "other":    OTHER_KEYS
    }
    KEY_EVENTS=(ARROW_KEYS + META_KEYS + KEYPAD_KEYS + DIGIT_KEYS +
        LETTER_KEYS + FUNCTION_KEYS + OTHER_KEYS)

    KEY_EVENT_TO_PYGAME_KEY_MAP={
        ",":        pygame.K_COMMA,
        ".":        pygame.K_PERIOD,
        "/":        pygame.K_SLASH,
        ";":        pygame.K_SEMICOLON,
        "'":        pygame.K_QUOTE,
        "[":        pygame.K_LEFTBRACKET,
        "]":        pygame.K_RIGHTBRACKET,
        "-":        pygame.K_MINUS,
        "=":        pygame.K_EQUALS,
        "`":        pygame.K_BACKQUOTE,
        "\\":       pygame.K_BACKSLASH,
        "0":        pygame.K_0,
        "1":        pygame.K_1,
        "2":        pygame.K_2,
        "3":        pygame.K_3,
        "4":        pygame.K_4,
        "5":        pygame.K_5,
        "6":        pygame.K_6,
        "7":        pygame.K_7,
        "8":        pygame.K_8,
        "9":        pygame.K_9,
        "A":        pygame.K_a,
        "B":        pygame.K_b,
        "C":        pygame.K_c,
        "D":        pygame.K_d,
        "E":        pygame.K_e,
        "F":        pygame.K_f,
        "G":        pygame.K_g,
        "H":        pygame.K_h,
        "I":        pygame.K_i,
        "J":        pygame.K_j,
        "K":        pygame.K_k,
        "L":        pygame.K_l,
        "M":        pygame.K_m,
        "N":        pygame.K_n,
        "O":        pygame.K_o,
        "P":        pygame.K_p,
        "Q":        pygame.K_q,
        "R":        pygame.K_r,
        "S":        pygame.K_s,
        "T":        pygame.K_t,
        "U":        pygame.K_u,
        "V":        pygame.K_v,
        "W":        pygame.K_w,
        "X":        pygame.K_x,
        "Y":        pygame.K_y,
        "Z":        pygame.K_z,
        "left":     pygame.K_LEFT,
        "right":    pygame.K_RIGHT,
        "up":       pygame.K_UP,
        "down":     pygame.K_DOWN,
        "lctrl":    pygame.K_LCTRL,
        "rctrl":    pygame.K_RCTRL,
        "lalt":     pygame.K_LALT,
        "ralt":     pygame.K_RALT,
        "lshift":   pygame.K_LSHIFT,
        "rshift":   pygame.K_RSHIFT,
        "lmeta":    pygame.K_LMETA,
        "rmeta":    pygame.K_RMETA,
        "lsuper":   pygame.K_LSUPER,
        "rsuper":   pygame.K_RSUPER,
        "space":    pygame.K_SPACE,
        "enter":    pygame.K_RETURN,
        "backspace":pygame.K_BACKSPACE,
        "escape":   pygame.K_ESCAPE,
        "home":     pygame.K_HOME,
        "end":      pygame.K_END,
        "pageup":   pygame.K_PAGEUP,
        "pagedown": pygame.K_PAGEDOWN,
        "delete":   pygame.K_DELETE,
        "insert":   pygame.K_INSERT,
        "np0":      pygame.K_KP0,
        "np1":      pygame.K_KP1,
        "np2":      pygame.K_KP2,
        "np3":      pygame.K_KP3,
        "np4":      pygame.K_KP4,
        "np5":      pygame.K_KP5,
        "np6":      pygame.K_KP6,
        "np7":      pygame.K_KP7,
        "np8":      pygame.K_KP8,
        "np9":      pygame.K_KP9,
        "np/":      pygame.K_KP_DIVIDE,
        "np*":      pygame.K_KP_MULTIPLY,
        "np-":      pygame.K_KP_MINUS,
        "np+":      pygame.K_KP_PLUS,
        "np.":      pygame.K_KP_PERIOD,
        "np=":      pygame.K_KP_EQUALS,
        "npenter":  pygame.K_KP_ENTER,
        "F1":       pygame.K_F1,
        "F2":       pygame.K_F2,
        "F3":       pygame.K_F3,
        "F4":       pygame.K_F4,
        "F5":       pygame.K_F5,
        "F6":       pygame.K_F6,
        "F7":       pygame.K_F7,
        "F8":       pygame.K_F8,
        "F9":       pygame.K_F9,
        "F10":      pygame.K_F10,
        "F11":      pygame.K_F11,
        "F12":      pygame.K_F12
    }
    EVENT_NAMES=(OBJECT_STATE_EVENTS + ALARM_EVENTS + STEP_EVENTS +
        MOUSE_EVENTS + OTHER_EVENTS + DRAW_EVENTS + KEY_EVENTS)

    EVENT_CATEGORIES={
        "object_state": OBJECT_STATE_EVENTS,
        "alarm":        ALARM_EVENTS,
        "step":         STEP_EVENTS,
        "collision":    ["collision"],
        "keyboard":     KEY_EVENTS,
        "mouse":        MOUSE_EVENTS,
        "other":        OTHER_EVENTS,
        "draw":         DRAW_EVENTS,
    }
    KEYBOARD_UP_SUFFIX = re.compile("(.*)(_keyup)$")
    KEYBOARD_DOWN_SUFFIX = re.compile("(.*)(_keydn)$")

    event_registry = None

    @staticmethod
    def is_equal(a, b):
        return ((a.event_name == b.event_name) and
            (a.event_category == b.event_category) and
            (a.key_event_type == b.key_event_type) and
            (a.collision_object_name == b.collision_object_name))

    @classmethod
    def get_category_by_event_name(cls, event_name):
        for cat in cls.EVENT_CATEGORIES:
            if event_name in cls.EVENT_CATEGORIES[cat]:
                return cat
        raise (PyGameMakerEventError("Unknown event name '{}'".format(event_name)))

    def __init__(self, event_name, collision_event=False):
        """
            Create a new event. The event name must be one defined in one of
            PyGameMakerEvent's event lists, or the name of an object that will
            be checked for collision events. Key event names can optionally
            have a suffix, _keyup or _keydn, to match a press or release key
            event. collision_event must be True for collision events.
        """
        self.event_name = ""
        self.event_category = ""
        self.collision_object_name = None
        self.defunct = False
        # check for a suffix (implies keyboard event)
        self.key_event_type = None
        up_minfo = self.KEYBOARD_UP_SUFFIX.search(event_name)
        dn_minfo = self.KEYBOARD_DOWN_SUFFIX.search(event_name)
        if up_minfo:
            self.event_name = up_minfo.group(1)
            self.key_event_type = "up"
            if not (self.event_name in self.KEY_EVENTS):
                raise (PyGameMakerEventError("Event {}: key named '{}' unknown".format(self, self.event_name)))
        elif dn_minfo:
            self.event_name = dn_minfo.group(1)
            self.key_event_type = "down"
            if not (self.event_name in self.KEY_EVENTS):
                raise (PyGameMakerEventError("Event {}: key named '{}' unknown".format(self, self.event_name)))
        else:
            if not (event_name in self.EVENT_NAMES):
                # check whether the event is named after an object: implies a
                #  collision event
                if collision_event:
                    self.event_name = "collision"
                    self.collision_object_name = event_name
            else:
                self.event_name = event_name
        self.event_category = PyGameMakerEvent.get_category_by_event_name(self.event_name)

    def __repr__(self):
        repr_string = "<PyGameMakerEvent "
        if self.collision_object_name:
            repr_string += "'{}:{}'>".format(self.event_category,
                self.collision_object_name)
        elif self.key_event_type:
            repr_string += "'{}:{}:{}'>".format(self.event_category,
                self.event_name, self.key_event_type)
        else:
            repr_string += "'{}:{}'>".format(self.event_category,
            self.event_name)
        return repr_string

if __name__ == "__main__":
    import unittest

    class TestObj:
        def __init__(self, name):
            self.name = name

    class TestPyGameMakerEvent(unittest.TestCase):

        def setUp(self):
            self.object_list = [TestObj("obj1"), TestObj("obj2"), TestObj("obj3")]

        def test_005valid_object_state_events(self):
            good_event1 = PyGameMakerEvent("create")
            print(good_event1)
            self.assertEqual(good_event1.event_name, "create")
            self.assertFalse(good_event1.collision_object_name)
            self.assertFalse(good_event1.key_event_type)
            self.assertEqual(good_event1.event_category, "object_state")

        def test_010valid_key_events(self):
            good_event2 = PyGameMakerEvent("F1_keyup")
            print(good_event2)
            self.assertEqual(good_event2.event_name, "F1")
            self.assertFalse(good_event2.collision_object_name)
            self.assertEqual(good_event2.key_event_type, "up")
            self.assertEqual(good_event2.event_category, "keyboard")
            good_event3 = PyGameMakerEvent("npenter_keydn")
            print(good_event3)
            self.assertEqual(good_event3.event_name, "npenter")
            self.assertFalse(good_event3.collision_object_name)
            self.assertEqual(good_event3.key_event_type, "down")
            self.assertEqual(good_event3.event_category, "keyboard")
            good_event4 = PyGameMakerEvent("home")
            print(good_event4)
            self.assertEqual(good_event4.event_name, "home")
            self.assertFalse(good_event4.collision_object_name)
            self.assertFalse(good_event4.key_event_type)
            self.assertEqual(good_event4.event_category, "keyboard")

        def test_012valid_collision_events(self):
            good_event5 = PyGameMakerEvent("obj1", self.object_list)
            print(good_event5)
            self.assertEqual(good_event5.event_name, "collision")
            self.assertEqual(good_event5.collision_object_name, "obj1")
            self.assertFalse(good_event5.key_event_type)
            self.assertEqual(good_event5.event_category, "collision")

        def test_015valid_mouse_events(self):
            good_event6 = PyGameMakerEvent("button_middle")
            print(good_event6)
            self.assertEqual(good_event6.event_name, "button_middle")
            self.assertFalse(good_event6.collision_object_name)
            self.assertFalse(good_event6.key_event_type)
            self.assertEqual(good_event6.event_category, "mouse")

        def test_020valid_alarm_events(self):
            good_event7 = PyGameMakerEvent("alarm0")
            print(good_event7)
            self.assertEqual(good_event7.event_name, "alarm0")
            self.assertFalse(good_event7.collision_object_name)
            self.assertFalse(good_event7.key_event_type)
            self.assertEqual(good_event7.event_category, "alarm")

        def test_025valid_step_events(self):
            good_event8 = PyGameMakerEvent("begin_step")
            print(good_event8)
            self.assertEqual(good_event8.event_name, "begin_step")
            self.assertFalse(good_event8.collision_object_name)
            self.assertFalse(good_event8.key_event_type)
            self.assertEqual(good_event8.event_category, "step")

        def test_030valid_other_events(self):
            good_event9 = PyGameMakerEvent("user_defined_0")
            print(good_event9)
            self.assertEqual(good_event9.event_name, "user_defined_0")
            self.assertFalse(good_event9.collision_object_name)
            self.assertFalse(good_event9.key_event_type)
            self.assertEqual(good_event9.event_category, "other")

        def test_035valid_draw_events(self):
            good_event10 = PyGameMakerEvent("gui")
            print(good_event10)
            self.assertEqual(good_event10.event_name, "gui")
            self.assertFalse(good_event10.collision_object_name)
            self.assertFalse(good_event10.key_event_type)
            self.assertEqual(good_event10.event_category, "draw")

        def test_040invalid_events(self):
            with self.assertRaises(PyGameMakerEventError):
                bad_event1 = PyGameMakerEvent("bad_event1")
            with self.assertRaises(PyGameMakerEventError):
                bad_event2 = PyGameMakerEvent("bogus_keyup")

    unittest.main()

