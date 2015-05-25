#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker events

import pygame
import re

class PyGameMakerEventException(Exception):
    pass

class PyGameMakerEvent(object):
    """Base class for events"""
    HANDLED_EVENTS=[]

    event_type_registry = []

    @classmethod
    def register_new_event_type(cls, eventtype):
        """
            Register a class (at init time) to make it possible to search
            through them for a particular action name
        """
        cls.event_type_registry.append(eventtype)

    @classmethod
    def find_event_by_name(cls, event_name):
        if event_name in cls.HANDLED_EVENTS:
            return True
        return False

    @classmethod
    def get_event_instance_by_event_name(cls, event_name, **kwargs):
        if len(cls.event_type_registry) > 0:
            for atype in cls.event_type_registry:
                if atype.find_event_by_name(event_name):
                    return atype(event_name, **kwargs)
        # no event type handles the named event
        raise PyGameMakerEventException("Event '{}' is unknown".format(event_name))

    def __init__(self, event_name="", event_params={}):
        self.event_name = event_name
        self.event_params = event_params

    def __getitem__(self, item_name):
        if item_name in self.event_params:
            return self.event_params[item_name]
        else:
            return None

    def __setitem__(self, item_name, val):
        self.event_params[item_name] = val

    def repr_event_strings(self):
        event_param_strs = []
        ev_str = ""
        for evparam in self.event_params:
            event_param_strs.append("{}={}".format(evparam, self.event_params[evparam]))
        if len(event_param_strs) > 0:
            ev_str = " "
            ev_str += ",".join(event_param_strs)
        return ev_str

    def __repr__(self):
        return("<{} \"{}\"{}>".format(self.__class__.__name__,
            self.event_name, self.repr_event_strings()))

class PyGameMakerObjectStateEvent(PyGameMakerEvent):
    OBJECT_STATE_EVENTS=[
        "create",
        "destroy"
    ]
    HANDLED_EVENTS=OBJECT_STATE_EVENTS

    def __init__(self, event_name, event_params={}):
        if not event_name in self.HANDLED_EVENTS:
            raise PyGameMakerEventException("PyGameMakerObjectStateEvent: Unknown event '{}'".format(event_name))
        PyGameMakerEvent.__init__(self, event_name, event_params)

class PyGameMakerAlarmEvent(PyGameMakerEvent):
    ALARM_COUNT=12
    ALARM_EVENTS=["alarm{}".format(n) for n in range(0,ALARM_COUNT)]
    HANDLED_EVENTS=ALARM_EVENTS

    def __init__(self, event_name, event_params={}):
        if not event_name in self.HANDLED_EVENTS:
            raise PyGameMakerEventException("PyGameMakerAlarmEvent: Unknown event '{}'".format(event_name))
        PyGameMakerEvent.__init__(self, event_name, event_params)

class PyGameMakerStepEvent(PyGameMakerEvent):
    STEP_EVENTS=[
        "normal_step",
        "begin_step",
        "end_step"
    ]
    HANDLED_EVENTS=STEP_EVENTS

    def __init__(self, event_name, event_params={}):
        if not event_name in self.HANDLED_EVENTS:
            raise PyGameMakerEventException("PyGameMakerStepEvent: Unknown event '{}'".format(event_name))
        PyGameMakerEvent.__init__(self, event_name, event_params)

class PyGameMakerMouseEvent(PyGameMakerEvent):
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
    HANDLED_EVENTS=MOUSE_EVENTS

    def __init__(self, event_name, event_params={}):
        if not event_name in self.HANDLED_EVENTS:
            raise PyGameMakerEventException("PyGameMakerMouseEvent: Unknown event '{}'".format(event_name))
        PyGameMakerEvent.__init__(self, event_name, event_params)

class PyGameMakerOtherEvent(PyGameMakerEvent):
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
    HANDLED_EVENTS=OTHER_EVENTS

    def __init__(self, event_name, event_params={}):
        if not event_name in self.HANDLED_EVENTS:
            raise PyGameMakerEventException("PyGameMakerOtherEvent: Unknown event '{}'".format(event_name))
        PyGameMakerEvent.__init__(self, event_name, event_params)

class PyGameMakerDrawEvent(PyGameMakerEvent):
    DRAW_EVENTS=[
        "draw",
        "gui",
        "resize"
    ]
    HANDLED_EVENTS=DRAW_EVENTS

    def __init__(self, event_name, event_params={}):
        if not event_name in self.HANDLED_EVENTS:
            raise PyGameMakerEventException("PyGameMakerDrawEvent: Unknown event '{}'".format(event_name))
        PyGameMakerEvent.__init__(self, event_name, event_params)

class PyGameMakerKeyEvent(PyGameMakerEvent):
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
        LETTER_KEYS + PUNCTUATION_KEYS + FUNCTION_KEYS + OTHER_KEYS)

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
    KEYBOARD_UP_SUFFIX = re.compile("(.*)(_keyup)$")
    KEYBOARD_DOWN_SUFFIX = re.compile("(.*)(_keydn)$")
    HANDLED_EVENTS=KEY_EVENTS

    @classmethod
    def find_key_event(cls, event_name):
        # check for a suffix
        key_event_type = None
        base_event_name = ""
        up_minfo = cls.KEYBOARD_UP_SUFFIX.search(event_name)
        dn_minfo = cls.KEYBOARD_DOWN_SUFFIX.search(event_name)
        if up_minfo:
            base_event_name = up_minfo.group(1)
            key_event_type = "up"
            if not (base_event_name in cls.HANDLED_EVENTS):
                raise (PyGameMakerEventException("PyGameMakerKeyEvent: key named '{}' unknown".format(base_event_name)))
        elif dn_minfo:
            base_event_name = dn_minfo.group(1)
            key_event_type = "down"
            if not (base_event_name in cls.HANDLED_EVENTS):
                raise (PyGameMakerEventException("PyGameMakerKeyEvent: key named '{}' unknown".format(base_event_name)))
        if len(base_event_name) == 0:
            raise PyGameMakerEventException("PyGameMakerKeyEvent: '{}' is invalid".format(event_name))
        else:
            event_info = (base_event_name, key_event_type)
        return event_info

    @classmethod
    def find_event_by_name(cls, event_name):
        try:
            ev_info = cls.find_key_event(event_name)
        except PyGameMakerEventException:
            return False
        return True

    def __init__(self, event_name, event_params={}):
        self.key_event_type = "up"
        PyGameMakerEvent.__init__(self, event_name, event_params)
        ev_info = self.find_key_event(event_name)
        self.event_name = ev_info[0]
        self.key_event_type = ev_info[1]

    def __repr__(self):
        return("<{} '{}' when {}{}>".format(self.__class__.__name__,
            self.event_name, self.key_event_type, self.repr_event_strings()))

class PyGameMakerCollisionEvent(PyGameMakerEvent):
    HANDLED_EVENTS=["collision"]

    COLLISION_RE=re.compile("collision_(.+)")

    @classmethod
    def find_collision_event(cls, event_name):
        ev_name = "collision"
        obj_name = ""
        minfo = cls.COLLISION_RE.search(event_name)
        if minfo:
            obj_name = minfo.group(1)
        else:
            raise PyGameMakerEventException("PyGameMakerCollisionEvent: Invalid event '{}'".format(event_name))
        ev_info = (ev_name, obj_name)
        return ev_info

    @classmethod
    def find_event_by_name(cls, event_name):
        try:
            ev_info = cls.find_collision_event(event_name)
        except PyGameMakerEventException:
            return False
        return True

    def __init__(self, event_name, event_params={}):
        """
            PyGameMakerCollisionEvent name must match the pattern:
            "collision_<objname>". The presence of an object objname is not
            checked.
        """
        PyGameMakerEvent.__init__(self, event_name, event_params)
        ev_info = PyGameMakerCollisionEvent.find_collision_event(event_name)
        self.event_name = ev_info[0]
        self.collision_object_name = ev_info[1]

    def __repr__(self):
        return("<{} vs \"{}\"{}>".format(self.__class__.__name__,
            self.collision_object_name, self.repr_event_strings()))

PyGameMakerEvent.register_new_event_type(PyGameMakerObjectStateEvent)
PyGameMakerEvent.register_new_event_type(PyGameMakerAlarmEvent)
PyGameMakerEvent.register_new_event_type(PyGameMakerStepEvent)
PyGameMakerEvent.register_new_event_type(PyGameMakerMouseEvent)
PyGameMakerEvent.register_new_event_type(PyGameMakerOtherEvent)
PyGameMakerEvent.register_new_event_type(PyGameMakerDrawEvent)
PyGameMakerEvent.register_new_event_type(PyGameMakerKeyEvent)
PyGameMakerEvent.register_new_event_type(PyGameMakerCollisionEvent)

if __name__ == "__main__":
    import unittest

    class TestObj:
        def __init__(self, name):
            self.name = name

    class TestPyGameMakerEvent(unittest.TestCase):

        def setUp(self):
            pass
 
        def test_002find_event_by_name(self):
            new_event = PyGameMakerEvent.get_event_instance_by_event_name("destroy")
            print(new_event)
            self.assertIs(new_event.__class__, PyGameMakerObjectStateEvent)

        def test_005valid_object_state_events(self):
            good_event1 = PyGameMakerObjectStateEvent("create")
            print(good_event1)
            self.assertEqual(good_event1.event_name, "create")

        def test_010valid_key_events(self):
            good_event2 = PyGameMakerKeyEvent("F1_keyup")
            print(good_event2)
            self.assertEqual(good_event2.event_name, "F1")
            self.assertEqual(good_event2.key_event_type, "up")
            good_event3 = PyGameMakerKeyEvent("npenter_keydn")
            print(good_event3)
            self.assertEqual(good_event3.event_name, "npenter")
            self.assertEqual(good_event3.key_event_type, "down")
            good_event4 = PyGameMakerEvent.get_event_instance_by_event_name("/_keydn")
            print(good_event4)
            self.assertIs(good_event4.__class__, PyGameMakerKeyEvent)

        def test_012valid_collision_events(self):
            good_event5 = PyGameMakerCollisionEvent("collision_obj1")
            print(good_event5)
            self.assertEqual(good_event5.event_name, "collision")
            self.assertEqual(good_event5.collision_object_name, "obj1")

        def test_015valid_mouse_events(self):
            good_event6 = PyGameMakerMouseEvent("button_middle")
            print(good_event6)
            self.assertEqual(good_event6.event_name, "button_middle")

        def test_020valid_alarm_events(self):
            good_event7 = PyGameMakerAlarmEvent("alarm0")
            print(good_event7)
            self.assertEqual(good_event7.event_name, "alarm0")

        def test_025valid_step_events(self):
            good_event8 = PyGameMakerStepEvent("begin_step")
            print(good_event8)
            self.assertEqual(good_event8.event_name, "begin_step")

        def test_030valid_other_events(self):
            good_event9 = PyGameMakerOtherEvent("user_defined_0")
            print(good_event9)
            self.assertEqual(good_event9.event_name, "user_defined_0")

        def test_035valid_draw_events(self):
            good_event10 = PyGameMakerDrawEvent("gui")
            print(good_event10)
            self.assertEqual(good_event10.event_name, "gui")

        def test_040event_parameters(self):
            good_event11 = PyGameMakerMouseEvent("button_left",
                {"mouse.xy": (43,120)})
            print(good_event11)
            self.assertEqual(good_event11["mouse.xy"], (43,120))

        def test_045invalid_events(self):
            with self.assertRaises(PyGameMakerEventException):
                bad_event1 = PyGameMakerKeyEvent("bad_event1")
            with self.assertRaises(PyGameMakerEventException):
                bad_event2 = PyGameMakerEvent.get_event_instance_by_event_name("bogus_keyup")

    unittest.main()

