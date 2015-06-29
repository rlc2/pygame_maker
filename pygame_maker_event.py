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
    def get_event_instance_by_event_name(cls, event_name, event_params={}):
        if len(cls.event_type_registry) > 0:
            for atype in cls.event_type_registry:
                if atype.find_event_by_name(event_name):
                    return atype(event_name, event_params)
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
        ev_parms_sorted = self.event_params.keys()
        ev_parms_sorted.sort()
        for evparam in ev_parms_sorted:
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
        "mouse_button_left",
        "mouse_button_right",
        "mouse_button_middle",
        "mouse_button_6"
        "mouse_button_7"
        "mouse_button_8"
        "mouse_nobutton",
        "mouse_left_pressed",
        "mouse_right_pressed",
        "mouse_middle_pressed",
        "mouse_left_released",
        "mouse_right_released",
        "mouse_middle_released",
        "mouse_enter",
        "mouse_leave",
        "mouse_wheelup",
        "mouse_wheeldown"
        "mouse_global_button_left",
        "mouse_global_button_right",
        "mouse_global_button_middle",
        "mouse_global_button_6"
        "mouse_global_button_7"
        "mouse_global_button_8"
        "mouse_global_nobutton",
        "mouse_global_left_pressed",
        "mouse_global_right_pressed",
        "mouse_global_middle_pressed",
        "mouse_global_left_released",
        "mouse_global_right_released",
        "mouse_global_middle_released",
        "mouse_global_wheelup",
        "mouse_global_wheeldown"
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
        "kb_left",
        "kb_right",
        "kb_up",
        "kb_down",
    ]
    META_KEYS=[
        "kb_lctrl",
        "kb_rctrl",
        "kb_lalt",
        "kb_ralt",
        "kb_lshift",
        "kb_rshift",
        "kb_lmeta",
        "kb_rmeta",
        "kb_lsuper",
        "kb_rsuper"
    ]
    KEYPAD_KEYS=[
        "kb_np0",
        "kb_np1",
        "kb_np2",
        "kb_np3",
        "kb_np4",
        "kb_np5",
        "kb_np6",
        "kb_np7",
        "kb_np8",
        "kb_np9",
        "kb_np/",
        "kb_np*",
        "kb_np-",
        "kb_np+",
        "kb_np.",
        "kb_np=",
        "kb_npenter",
    ]
    PUNCTUATION_KEYS=[
        "kb_,",
        "kb_.",
        "kb_/",
        "kb_;",
        "kb_'",
        "kb_[",
        "kb_]",
        "kb_-",
        "kb_=",
        "kb_`",
        "kb_\\"
    ]
    DIGIT_KEYS=["kb_{}".format(str(k)) for k in range(0,10)]
    LETTER_KEYS=["kb_{}".format(chr(l)) for l in range(65, 65+26)]
    FUNCTION_KEYS=["kb_F{}".format(n) for n in range(1,13)]
    OTHER_KEYS=[
        "kb_no_key",
        "kb_any_key",
        "kb_space",
        "kb_enter",
        "kb_backspace",
        "kb_escape",
        "kb_home",
        "kb_end",
        "kb_pageup",
        "kb_pagedown",
        "kb_delete",
        "kb_insert"
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
        "kb_,":        pygame.K_COMMA,
        "kb_.":        pygame.K_PERIOD,
        "kb_/":        pygame.K_SLASH,
        "kb_;":        pygame.K_SEMICOLON,
        "kb_'":        pygame.K_QUOTE,
        "kb_[":        pygame.K_LEFTBRACKET,
        "kb_]":        pygame.K_RIGHTBRACKET,
        "kb_-":        pygame.K_MINUS,
        "kb_=":        pygame.K_EQUALS,
        "kb_`":        pygame.K_BACKQUOTE,
        "kb_\\":       pygame.K_BACKSLASH,
        "kb_0":        pygame.K_0,
        "kb_1":        pygame.K_1,
        "kb_2":        pygame.K_2,
        "kb_3":        pygame.K_3,
        "kb_4":        pygame.K_4,
        "kb_5":        pygame.K_5,
        "kb_6":        pygame.K_6,
        "kb_7":        pygame.K_7,
        "kb_8":        pygame.K_8,
        "kb_9":        pygame.K_9,
        "kb_A":        pygame.K_a,
        "kb_B":        pygame.K_b,
        "kb_C":        pygame.K_c,
        "kb_D":        pygame.K_d,
        "kb_E":        pygame.K_e,
        "kb_F":        pygame.K_f,
        "kb_G":        pygame.K_g,
        "kb_H":        pygame.K_h,
        "kb_I":        pygame.K_i,
        "kb_J":        pygame.K_j,
        "kb_K":        pygame.K_k,
        "kb_L":        pygame.K_l,
        "kb_M":        pygame.K_m,
        "kb_N":        pygame.K_n,
        "kb_O":        pygame.K_o,
        "kb_P":        pygame.K_p,
        "kb_Q":        pygame.K_q,
        "kb_R":        pygame.K_r,
        "kb_S":        pygame.K_s,
        "kb_T":        pygame.K_t,
        "kb_U":        pygame.K_u,
        "kb_V":        pygame.K_v,
        "kb_W":        pygame.K_w,
        "kb_X":        pygame.K_x,
        "kb_Y":        pygame.K_y,
        "kb_Z":        pygame.K_z,
        "kb_left":     pygame.K_LEFT,
        "kb_right":    pygame.K_RIGHT,
        "kb_up":       pygame.K_UP,
        "kb_down":     pygame.K_DOWN,
        "kb_lctrl":    pygame.K_LCTRL,
        "kb_rctrl":    pygame.K_RCTRL,
        "kb_lalt":     pygame.K_LALT,
        "kb_ralt":     pygame.K_RALT,
        "kb_lshift":   pygame.K_LSHIFT,
        "kb_rshift":   pygame.K_RSHIFT,
        "kb_lmeta":    pygame.K_LMETA,
        "kb_rmeta":    pygame.K_RMETA,
        "kb_lsuper":   pygame.K_LSUPER,
        "kb_rsuper":   pygame.K_RSUPER,
        "kb_space":    pygame.K_SPACE,
        "kb_enter":    pygame.K_RETURN,
        "kb_backspace":pygame.K_BACKSPACE,
        "kb_escape":   pygame.K_ESCAPE,
        "kb_home":     pygame.K_HOME,
        "kb_end":      pygame.K_END,
        "kb_pageup":   pygame.K_PAGEUP,
        "kb_pagedown": pygame.K_PAGEDOWN,
        "kb_delete":   pygame.K_DELETE,
        "kb_insert":   pygame.K_INSERT,
        "kb_np0":      pygame.K_KP0,
        "kb_np1":      pygame.K_KP1,
        "kb_np2":      pygame.K_KP2,
        "kb_np3":      pygame.K_KP3,
        "kb_np4":      pygame.K_KP4,
        "kb_np5":      pygame.K_KP5,
        "kb_np6":      pygame.K_KP6,
        "kb_np7":      pygame.K_KP7,
        "kb_np8":      pygame.K_KP8,
        "kb_np9":      pygame.K_KP9,
        "kb_np/":      pygame.K_KP_DIVIDE,
        "kb_np*":      pygame.K_KP_MULTIPLY,
        "kb_np-":      pygame.K_KP_MINUS,
        "kb_np+":      pygame.K_KP_PLUS,
        "kb_np.":      pygame.K_KP_PERIOD,
        "kb_np=":      pygame.K_KP_EQUALS,
        "kb_npenter":  pygame.K_KP_ENTER,
        "kb_F1":       pygame.K_F1,
        "kb_F2":       pygame.K_F2,
        "kb_F3":       pygame.K_F3,
        "kb_F4":       pygame.K_F4,
        "kb_F5":       pygame.K_F5,
        "kb_F6":       pygame.K_F6,
        "kb_F7":       pygame.K_F7,
        "kb_F8":       pygame.K_F8,
        "kb_F9":       pygame.K_F9,
        "kb_F10":      pygame.K_F10,
        "kb_F11":      pygame.K_F11,
        "kb_F12":      pygame.K_F12
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
        #self.event_name = ev_info[0]
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
            good_event2 = PyGameMakerKeyEvent("kb_F1_keyup")
            print(good_event2)
            self.assertEqual(good_event2.event_name, "kb_F1")
            self.assertEqual(good_event2.key_event_type, "up")
            good_event3 = PyGameMakerKeyEvent("kb_npenter_keydn")
            print(good_event3)
            self.assertEqual(good_event3.event_name, "kb_npenter")
            self.assertEqual(good_event3.key_event_type, "down")
            good_event4 = PyGameMakerEvent.get_event_instance_by_event_name("kb_/_keydn")
            print(good_event4)
            self.assertIs(good_event4.__class__, PyGameMakerKeyEvent)

        def test_012valid_collision_events(self):
            good_event5 = PyGameMakerCollisionEvent("collision_obj1")
            print(good_event5)
            self.assertEqual(good_event5.event_name, "collision_obj1")
            self.assertEqual(good_event5.collision_object_name, "obj1")

        def test_015valid_mouse_events(self):
            good_event6 = PyGameMakerMouseEvent("mouse_button_middle")
            print(good_event6)
            self.assertEqual(good_event6.event_name, "mouse_button_middle")

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
            good_event11 = PyGameMakerMouseEvent("mouse_button_left",
                {"mouse.xy": (43,120)})
            print(good_event11)
            self.assertEqual(good_event11["mouse.xy"], (43,120))

        def test_045invalid_events(self):
            with self.assertRaises(PyGameMakerEventException):
                bad_event1 = PyGameMakerKeyEvent("bad_event1")
            with self.assertRaises(PyGameMakerEventException):
                bad_event2 = PyGameMakerEvent.get_event_instance_by_event_name("bogus_keyup")

    unittest.main()

