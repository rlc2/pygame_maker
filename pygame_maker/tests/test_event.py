#!/usr/bin/env python

from pygame_maker.events.event import *
import unittest

class TestObj:
    def __init__(self, name):
        self.name = name

class TestEvent(unittest.TestCase):

    def setUp(self):
        pass

    def test_002find_event_by_name(self):
        new_event = Event.get_event_instance_by_event_name("destroy")
        print(new_event)
        self.assertIs(new_event.__class__, ObjectStateEvent)

    def test_005valid_object_state_events(self):
        good_event1 = ObjectStateEvent("create")
        print(good_event1)
        self.assertEqual(good_event1.name, "create")

    def test_010valid_key_events(self):
        good_event2 = KeyEvent("kb_F1_keyup")
        print(good_event2)
        self.assertEqual(good_event2.name, "kb_F1")
        self.assertEqual(good_event2.key_event_type, "up")
        good_event3 = KeyEvent("kb_npenter_keydn")
        print(good_event3)
        self.assertEqual(good_event3.name, "kb_npenter")
        self.assertEqual(good_event3.key_event_type, "down")
        good_event4 = Event.get_event_instance_by_event_name("kb_/_keydn")
        print(good_event4)
        self.assertIs(good_event4.__class__, KeyEvent)

    def test_012valid_collision_events(self):
        good_event5 = CollisionEvent("collision_obj1")
        print(good_event5)
        self.assertEqual(good_event5.name, "collision_obj1")
        self.assertEqual(good_event5.collision_object_name, "obj1")

    def test_015valid_mouse_events(self):
        good_event6 = MouseEvent("mouse_button_middle")
        print(good_event6)
        self.assertEqual(good_event6.name, "mouse_button_middle")

    def test_020valid_alarm_events(self):
        good_event7 = AlarmEvent("alarm0")
        print(good_event7)
        self.assertEqual(good_event7.name, "alarm0")

    def test_025valid_step_events(self):
        good_event8 = StepEvent("begin_step")
        print(good_event8)
        self.assertEqual(good_event8.name, "begin_step")

    def test_030valid_other_events(self):
        good_event9 = OtherEvent("user_defined_0")
        print(good_event9)
        self.assertEqual(good_event9.name, "user_defined_0")

    def test_035valid_draw_events(self):
        good_event10 = DrawEvent("gui")
        print(good_event10)
        self.assertEqual(good_event10.name, "gui")

    def test_040event_parameters(self):
        good_event11 = MouseEvent("mouse_button_left",
            {"mouse.xy": (43,120)})
        print(good_event11)
        self.assertEqual(good_event11["mouse.xy"], (43,120))

    def test_045invalid_events(self):
        with self.assertRaises(UnknownEventError):
            bad_event1 = KeyEvent("bad_event1")
        with self.assertRaises(UnknownEventError):
            bad_event2 = Event.get_event_instance_by_event_name("bogus_keyup")

unittest.main()

