"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Pygame maker events.
"""

import re
import pygame


__all__ = ["Event", "AlarmEvent", "CollisionEvent", "DrawEvent", "KeyEvent",
           "MouseEvent", "ObjectStateEvent", "OtherEvent", "StepEvent",
           "UnknownEventError"]


class UnknownEventError(Exception):
    """Raised when an Event type recieves an unknown event name."""
    pass


class Event(object):
    """Base class for events."""
    HANDLED_EVENTS = []

    event_type_registry = []

    @classmethod
    def register_new_event_type(cls, eventtype):
        """
        Register a class (at init time) to make it possible to search through
        them for a particular action name.

        :param eventtype: A subclass for registration
        :type eventtype: Event
        """
        cls.event_type_registry.append(eventtype)

    @classmethod
    def find_event_by_name(cls, event_name):
        """
        Answer whether the event class handles the named event.

        :param event_name: The name of an event
        :type event_name: str
        :return: True if the event is handled, False otherwise
        :rtype: bool
        """
        if event_name in cls.HANDLED_EVENTS:
            return True
        return False

    @classmethod
    def get_event_instance_by_name(cls, event_name, event_params=None):
        """
        Return an event instance of the right type, by searching for the
        event type in the registry.  Event parameters may be applied to the
        returned instance.

        :param event_name: The name of the new event instance
        :type event_name: str
        :param event_params: A dict containing parameters to apply to the new
            instance, or None
        :type event_params: dict|None
        :return: A new event instance
        :raise: UnknownEventError if the named event is not found
        """
        instance_params = {}
        if event_params is not None:
            instance_params.update(event_params)
        if len(cls.event_type_registry) > 0:
            for atype in cls.event_type_registry:
                if atype.find_event_by_name(event_name):
                    return atype(event_name, instance_params)
        # no event type handles the named event
        raise UnknownEventError("Event '{}' is unknown".format(event_name))

    def __init__(self, event_name="", event_params=None):
        """
        Create a new Event instance.  Meant to be called by subclasses.

        :param event_name: The event's name
        :type event_name: str
        :param event_params: A dict containing the new event's parameters, or
            None
        :type event_params: dict|None
        """
        self.name = event_name
        ev_params = {}
        if event_params is not None:
            ev_params.update(event_params)
        self.event_params = ev_params

    def __getitem__(self, item_name):
        """
        Retrieve an event parameter from the event_params attribute.

        :param item_name: A parameter name
        :type item_name: str
        :return: The contents of the named parameter, if found
        :raise: KeyError if the named parameter isn't found
        """
        if item_name in self.event_params:
            return self.event_params[item_name]
        else:
            raise KeyError("No parameter '{}' found in event")

    def __setitem__(self, item_name, val):
        """
        Set an event parameter in the event_params attribute.

        :param item_name: A parameter name
        :type item_name: str
        :param val: The parameter's new value
        """
        self.event_params[item_name] = val

    def _repr_event_strings(self):
        event_param_strs = []
        ev_str = ""
        ev_parms_sorted = list(self.event_params.keys())
        ev_parms_sorted.sort()
        for evparam in ev_parms_sorted:
            event_param_strs.append("{}={}".format(evparam, self.event_params[evparam]))
        if len(event_param_strs) > 0:
            ev_str = " "
            ev_str += ",".join(event_param_strs)
        return ev_str

    def __repr__(self):
        return("<{} \"{}\"{}>".format(self.__class__.__name__,
                                      self.name, self._repr_event_strings()))


class ObjectStateEvent(Event):
    """Wrap object state events."""
    OBJECT_STATE_EVENTS = [
        "create",
        "create_child",
        "destroy",
        "destroy_child",
        "destroy_parent"
    ]
    #: Complete list of object state event names
    HANDLED_EVENTS = OBJECT_STATE_EVENTS

    def __init__(self, event_name, event_params=None):
        """
        Create an ObjectStateEvent instance with the given name and parameters.

        :param event_name: The name of an ObjectStateEvent
        :type event_name: str
        :param event_params: A dict containing the event's parameters, or None
        :type event_params: dict|None
        """
        if event_name not in self.HANDLED_EVENTS:
            raise UnknownEventError("ObjectStateEvent: Unknown event '{}'".format(event_name))
        Event.__init__(self, event_name, event_params)


class AlarmEvent(Event):
    """Wrap alarm events."""
    ALARM_COUNT = 12
    ALARM_EVENTS = ["alarm{:d}".format(n) for n in range(0, ALARM_COUNT)]
    #: Complete list of alarm event names
    HANDLED_EVENTS = ALARM_EVENTS

    def __init__(self, event_name, event_params=None):
        """
        Create an AlarmEvent instance with the given name and parameters.

        :param event_name: The name of an AlarmEvent
        :type event_name: str
        :param event_params: A dict containing the event's parameters, or None
        :type event_params: dict|None
        """
        if event_name not in self.HANDLED_EVENTS:
            raise UnknownEventError("AlarmEvent: Unknown event '{}'".format(event_name))
        Event.__init__(self, event_name, event_params)


class StepEvent(Event):
    """Wrap step events."""
    STEP_EVENTS = [
        "normal_step",
        "begin_step",
        "end_step"
    ]
    #: Complete list of step event names
    HANDLED_EVENTS = STEP_EVENTS

    def __init__(self, event_name, event_params=None):
        """
        Create a StepEvent instance with the given name and parameters.

        :param event_name: The name of a StepEvent
        :type event_name: str
        :param event_params: A dict containing the event's parameters, or None
        :type event_params: dict|None
        """
        if event_name not in self.HANDLED_EVENTS:
            raise UnknownEventError("StepEvent: Unknown event '{}'".format(event_name))
        Event.__init__(self, event_name, event_params)


class MouseEvent(Event):
    """Wrap mouse events."""
    MOUSE_EVENTS = [
        "mouse_button_left",
        "mouse_button_right",
        "mouse_button_middle",
        "mouse_button_6",
        "mouse_button_7",
        "mouse_button_8",
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
        "mouse_wheeldown",
        "mouse_global_button_left",
        "mouse_global_button_right",
        "mouse_global_button_middle",
        "mouse_global_button_6",
        "mouse_global_button_7",
        "mouse_global_button_8",
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
    #: Complete list of mouse events
    HANDLED_EVENTS = MOUSE_EVENTS

    def __init__(self, event_name, event_params=None):
        """
        Create a MouseEvent instance with the given name and parameters.

        :param event_name: The name of a MouseEvent
        :type event_name: str
        :param event_params: A dict containing the event's parameters, or None
        :type event_params: dict|None
        """
        if event_name not in self.HANDLED_EVENTS:
            raise UnknownEventError("MouseEvent: Unknown event '{}'".format(event_name))
        Event.__init__(self, event_name, event_params)


class OtherEvent(Event):
    """Wrap miscellaneous events."""
    OTHER_EVENTS = [
        "outside_room",
        "parent_outside_room",
        "child_outside_room",
        "intersect_boundary",
        "parent_intersect_boundary",
        "child_intersect_boundary",
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
    #: Complete list of 'other' events
    HANDLED_EVENTS = OTHER_EVENTS

    def __init__(self, event_name, event_params=None):
        """
        Create an OtherEvent instance with the given name and parameters.

        :param event_name: The name of an OtherEvent
        :type event_name: str
        :param event_params: A dict containing the event's parameters, or None
        :type event_params: dict|None
        """
        if event_name not in self.HANDLED_EVENTS:
            raise UnknownEventError("OtherEvent: Unknown event '{}'".format(event_name))
        Event.__init__(self, event_name, event_params)


class DrawEvent(Event):
    """Wrap draw events."""
    DRAW_EVENTS = [
        "draw",
        "gui",
        "resize"
    ]
    #: Complete list of draw events
    HANDLED_EVENTS = DRAW_EVENTS

    def __init__(self, event_name, event_params=None):
        """
        Create a DrawEvent instance with the given name and parameters.

        :param event_name: The name of a DrawEvent
        :type event_name: str
        :param event_params: A dict containing the event's parameters, or None
        :type event_params: dict|None
        """
        if event_name not in self.HANDLED_EVENTS:
            raise UnknownEventError("DrawEvent: Unknown event '{}'".format(event_name))
        Event.__init__(self, event_name, event_params)


class KeyEvent(Event):
    """Wrap keyboard events."""
    ARROW_KEYS = [
        "kb_left",
        "kb_right",
        "kb_up",
        "kb_down",
    ]
    META_KEYS = [
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
    KEYPAD_KEYS = [
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
    PUNCTUATION_KEYS = [
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
    DIGIT_KEYS = ["kb_{}".format(str(k)) for k in range(0, 10)]
    LETTER_KEYS = ["kb_{}".format(chr(l)) for l in range(65, 65+26)]
    FUNCTION_KEYS = ["kb_F{:d}".format(n) for n in range(1, 13)]
    OTHER_KEYS = [
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
    KEYBOARD_EVENT_KEY_CATEGORIES = {
        "arrows":   ARROW_KEYS,
        "meta":     META_KEYS,
        "keypad":   KEYPAD_KEYS,
        "digits":   DIGIT_KEYS,
        "letters":  LETTER_KEYS,
        "function": FUNCTION_KEYS,
        "other":    OTHER_KEYS
    }
    #: Complete list of keyboard events
    KEY_EVENTS = (ARROW_KEYS + META_KEYS + KEYPAD_KEYS + PUNCTUATION_KEYS +
                  DIGIT_KEYS + LETTER_KEYS + PUNCTUATION_KEYS + FUNCTION_KEYS +
                  OTHER_KEYS)

    PYGAME_KEY_TO_KEY_EVENT_MAP = {
        pygame.K_COMMA:         "kb_,",
        pygame.K_PERIOD:        "kb_.",
        pygame.K_SLASH:         "kb_/",
        pygame.K_SEMICOLON:     "kb_;",
        pygame.K_QUOTE:         "kb_'",
        pygame.K_LEFTBRACKET:   "kb_[",
        pygame.K_RIGHTBRACKET:  "kb_]",
        pygame.K_MINUS:         "kb_-",
        pygame.K_EQUALS:        "kb_=",
        pygame.K_BACKQUOTE:     "kb_`",
        pygame.K_BACKSLASH:     "kb_\\",
        pygame.K_0:             "kb_0",
        pygame.K_1:             "kb_1",
        pygame.K_2:             "kb_2",
        pygame.K_3:             "kb_3",
        pygame.K_4:             "kb_4",
        pygame.K_5:             "kb_5",
        pygame.K_6:             "kb_6",
        pygame.K_7:             "kb_7",
        pygame.K_8:             "kb_8",
        pygame.K_9:             "kb_9",
        pygame.K_a:             "kb_A",
        pygame.K_b:             "kb_B",
        pygame.K_c:             "kb_C",
        pygame.K_d:             "kb_D",
        pygame.K_e:             "kb_E",
        pygame.K_f:             "kb_F",
        pygame.K_g:             "kb_G",
        pygame.K_h:             "kb_H",
        pygame.K_i:             "kb_I",
        pygame.K_j:             "kb_J",
        pygame.K_k:             "kb_K",
        pygame.K_l:             "kb_L",
        pygame.K_m:             "kb_M",
        pygame.K_n:             "kb_N",
        pygame.K_o:             "kb_O",
        pygame.K_p:             "kb_P",
        pygame.K_q:             "kb_Q",
        pygame.K_r:             "kb_R",
        pygame.K_s:             "kb_S",
        pygame.K_t:             "kb_T",
        pygame.K_u:             "kb_U",
        pygame.K_v:             "kb_V",
        pygame.K_w:             "kb_W",
        pygame.K_x:             "kb_X",
        pygame.K_y:             "kb_Y",
        pygame.K_z:             "kb_Z",
        pygame.K_LEFT:          "kb_left",
        pygame.K_RIGHT:         "kb_right",
        pygame.K_UP:            "kb_up",
        pygame.K_DOWN:          "kb_down",
        pygame.K_LCTRL:         "kb_lctrl",
        pygame.K_RCTRL:         "kb_rctrl",
        pygame.K_LALT:          "kb_lalt",
        pygame.K_RALT:          "kb_ralt",
        pygame.K_LSHIFT:        "kb_lshift",
        pygame.K_RSHIFT:        "kb_rshift",
        pygame.K_LMETA:         "kb_lmeta",
        pygame.K_RMETA:         "kb_rmeta",
        pygame.K_LSUPER:        "kb_lsuper",
        pygame.K_RSUPER:        "kb_rsuper",
        pygame.K_SPACE:         "kb_space",
        pygame.K_RETURN:        "kb_enter",
        pygame.K_BACKSPACE:     "kb_backspace",
        pygame.K_ESCAPE:        "kb_escape",
        pygame.K_HOME:          "kb_home",
        pygame.K_END:           "kb_end",
        pygame.K_PAGEUP:        "kb_pageup",
        pygame.K_PAGEDOWN:      "kb_pagedown",
        pygame.K_DELETE:        "kb_delete",
        pygame.K_INSERT:        "kb_insert",
        pygame.K_KP0:           "kb_np0",
        pygame.K_KP1:           "kb_np1",
        pygame.K_KP2:           "kb_np2",
        pygame.K_KP3:           "kb_np3",
        pygame.K_KP4:           "kb_np4",
        pygame.K_KP5:           "kb_np5",
        pygame.K_KP6:           "kb_np6",
        pygame.K_KP7:           "kb_np7",
        pygame.K_KP8:           "kb_np8",
        pygame.K_KP9:           "kb_np9",
        pygame.K_KP_DIVIDE:     "kb_np/",
        pygame.K_KP_MULTIPLY:   "kb_np*",
        pygame.K_KP_MINUS:      "kb_np-",
        pygame.K_KP_PLUS:       "kb_np+",
        pygame.K_KP_PERIOD:     "kb_np.",
        pygame.K_KP_EQUALS:     "kb_np=",
        pygame.K_KP_ENTER:      "kb_npenter",
        pygame.K_F1:            "kb_F1",
        pygame.K_F2:            "kb_F2",
        pygame.K_F3:            "kb_F3",
        pygame.K_F4:            "kb_F4",
        pygame.K_F5:            "kb_F5",
        pygame.K_F6:            "kb_F6",
        pygame.K_F7:            "kb_F7",
        pygame.K_F8:            "kb_F8",
        pygame.K_F9:            "kb_F9",
        pygame.K_F10:           "kb_F10",
        pygame.K_F11:           "kb_F11",
        pygame.K_F12:           "kb_F12"
    }
    #: Append this string to the event name, to specify key release
    KEYBOARD_UP_SUFFIX = "_keyup"
    KEYBOARD_UP_SUFFIX_RE = re.compile("(.*)({})$".format(KEYBOARD_UP_SUFFIX))
    #: Append this string to the event name, to specify key press
    KEYBOARD_DOWN_SUFFIX = "_keydn"
    KEYBOARD_DOWN_SUFFIX_RE = re.compile("(.*)({})$".format(KEYBOARD_DOWN_SUFFIX))
    HANDLED_EVENTS = KEY_EVENTS

    @classmethod
    def find_key_event(cls, event_name):
        """
        Given a full key event name (possibly including _keyup or _keydn),
        search for the event's base name to make sure it exists.  Used by
        find_event_by_name() and __init__().
        """
        # check for a suffix
        base_event_name = str(event_name)
        up_minfo = cls.KEYBOARD_UP_SUFFIX_RE.search(event_name)
        dn_minfo = cls.KEYBOARD_DOWN_SUFFIX_RE.search(event_name)
        if up_minfo:
            base_event_name = up_minfo.group(1)
        elif dn_minfo:
            base_event_name = dn_minfo.group(1)
        if base_event_name not in cls.HANDLED_EVENTS:
            raise UnknownEventError("KeyEvent: key named '{}' unknown".format(base_event_name))
        if len(base_event_name) == 0:
            raise UnknownEventError("KeyEvent: '{}' is invalid".format(event_name))
        return event_name

    @classmethod
    def find_event_by_name(cls, event_name):
        """
        Override the base class method
        :py:meth:`Event.find_event_by_name`, which doesn't handle the keyup or
        keydown suffixes.

        :param event_name: The name of a keyboard event
        :type event_name: str
        :return: True if the event is known, False otherwise
        :rtype: bool
        """
        try:
            cls.find_key_event(event_name)
        except UnknownEventError:
            return False
        return True

    def __init__(self, event_name, event_params=None):
        """
        Create a KeyEvent instance with the given name and parameters.

        :param event_name: The name of an KeyEvent
        :type event_name: str
        :param event_params: A dict containing the event's parameters, or None
        :type event_params: dict|None
        """
        Event.__init__(self, event_name, event_params)
        self.find_key_event(event_name)

    def __repr__(self):
        return "<{} '{}' {}>".format(self.__class__.__name__, self.name, self._repr_event_strings())


class CollisionEvent(Event):
    """Wrap collision events."""
    #: All collision events start with this prefix
    HANDLED_EVENTS = ["collision", "parent_collision", "child_collision"]

    COLLISION_RE = re.compile("(parent_|child_)?collision_(.+)")

    @classmethod
    def find_collision_event(cls, event_name):
        """
        Given a full collision event name (which may include the other object
        type's name), search for the event's base name to make sure it's
        correct.  Used by find_event_by_name() and __init__().
        """
        ev_name = "collision"
        obj_name = ""
        minfo = cls.COLLISION_RE.search(event_name)
        if minfo:
            obj_name = minfo.group(2)
        else:
            raise UnknownEventError("CollisionEvent: Invalid event '{}'".format(event_name))
        ev_info = (ev_name, obj_name)
        return ev_info

    @classmethod
    def find_event_by_name(cls, event_name):
        """
        Override the base class find_event_by_name, since the collision event
        name is really just a prefix.

        :param event_name: The name of a collision event
        :type event_name: str
        :return: True if the event name
        """
        try:
            cls.find_collision_event(event_name)
        except UnknownEventError:
            return False
        return True

    def __init__(self, event_name, event_params=None):
        """
        Create a CollisionEvent instance with the given name and parameters.

        CollisionEvent name must match the pattern:
        "collision_<``objname``>". The existence of an object type matching
        ``objname`` is not checked.

        :param event_name: The name of a CollisionEvent
        :type event_name: str
        :param event_params: A dict containing the event's parameters, or None
        :type event_params: dict|None
        """
        Event.__init__(self, event_name, event_params)
        ev_info = CollisionEvent.find_collision_event(event_name)
        # self.name = ev_info[0]
        self.collision_object_name = ev_info[1]

    def __repr__(self):
        return("<{} vs \"{}\"{}>".format(self.__class__.__name__,
                                         self.collision_object_name,
                                         self._repr_event_strings()))

Event.register_new_event_type(ObjectStateEvent)
Event.register_new_event_type(AlarmEvent)
Event.register_new_event_type(StepEvent)
Event.register_new_event_type(MouseEvent)
Event.register_new_event_type(OtherEvent)
Event.register_new_event_type(DrawEvent)
Event.register_new_event_type(KeyEvent)
Event.register_new_event_type(CollisionEvent)
