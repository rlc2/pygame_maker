#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test the pygame_maker.events.event module.
"""

import unittest
from pygame_maker.events.event import Event, ObjectStateEvent, KeyEvent, CollisionEvent, \
    MouseEvent, AlarmEvent, StepEvent, OtherEvent, DrawEvent, UnknownEventError


class TestEvent(unittest.TestCase):
    """Unit tests for the event module."""

    def setUp(self):
        pass

    def test_002find_event_by_name(self):
        """Test whether an instance can be found from the event registry."""
        new_event = Event.get_event_instance_by_name("destroy")
        print(new_event)
        self.assertIs(new_event.__class__, ObjectStateEvent)

    def test_005valid_obj_state_event(self):
        """Test creation of a simple object event."""
        good_event1 = ObjectStateEvent("create")
        print(good_event1)
        self.assertEqual(good_event1.name, "create")

    def test_010valid_key_events(self):
        """
        Test creation of various keyboard events (including key up and key down
        states).
        """
        good_event2 = KeyEvent("kb_F1_keyup")
        print(good_event2)
        good_event3 = KeyEvent("kb_npenter_keydn")
        print(good_event3)
        good_event4 = Event.get_event_instance_by_name("kb_/_keydn")
        print(good_event4)
        self.assertIs(good_event4.__class__, KeyEvent)

    def test_012valid_collision_events(self):
        """Test that a collision event is properly recognized."""
        good_event5 = CollisionEvent("collision_obj1")
        print(good_event5)
        self.assertEqual(good_event5.name, "collision_obj1")
        self.assertEqual(good_event5.collision_object_name, "obj1")

    def test_015valid_mouse_events(self):
        """Test creation of a mouse event."""
        good_event6 = MouseEvent("mouse_button_middle")
        print(good_event6)
        self.assertEqual(good_event6.name, "mouse_button_middle")

    def test_020valid_alarm_events(self):
        """Test creation of an alarm event."""
        good_event7 = AlarmEvent("alarm0")
        print(good_event7)
        self.assertEqual(good_event7.name, "alarm0")

    def test_025valid_step_events(self):
        """Test creation of an alarm event."""
        good_event8 = StepEvent("begin_step")
        print(good_event8)
        self.assertEqual(good_event8.name, "begin_step")

    def test_030valid_other_events(self):
        """Test creation of an "other" event."""
        good_event9 = OtherEvent("user_defined_0")
        print(good_event9)
        self.assertEqual(good_event9.name, "user_defined_0")

    def test_035valid_draw_events(self):
        """Test creation of a drawing event."""
        good_event10 = DrawEvent("gui")
        print(good_event10)
        self.assertEqual(good_event10.name, "gui")

    def test_040event_parameters(self):
        """Test creation of an event with parameters."""
        good_event11 = MouseEvent("mouse_button_left", {"mouse.xy": (43, 120)})
        print(good_event11)
        self.assertEqual(good_event11["mouse.xy"], (43, 120))

    def test_045invalid_events(self):
        """Test that unknown event names produce the expected exception."""
        with self.assertRaises(UnknownEventError):
            KeyEvent("bad_event1")
        with self.assertRaises(UnknownEventError):
            Event.get_event_instance_by_name("bogus_keyup")

unittest.main()

