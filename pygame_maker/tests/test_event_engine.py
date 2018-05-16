#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test the pygame_maker.events.event_engine module.
"""

import unittest
import logging
from pygame_maker.events.event import StepEvent, MouseEvent
from pygame_maker.events.event_engine import EventEngine

EELOGGER = logging.getLogger("EventEngine")
EEHANDLER = logging.StreamHandler()
EEFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
EEHANDLER.setFormatter(EEFORMATTER)
EELOGGER.addHandler(EEHANDLER)
EELOGGER.setLevel(logging.INFO)


class TestEventEngine(unittest.TestCase):
    """Unit tests for the event_engine module."""

    def setUp(self):
        self.event_engine = EventEngine()
        self.called_events = []

    def event_handler(self, event, ev_tag):
        """
        A simple event handler that prints a message when called and keeps a
        list of events in the order received for comparison.
        """
        print("{} received event {}.".format(ev_tag, event))
        self.called_events.append("{} {}".format(event, ev_tag))

    def test_005register_event_handler(self):
        """Test registration and de-registration of event handlers."""
        engine = EventEngine()
        begin_hdlr1 = lambda name: self.event_handler(name, 'bhdlr1')
        begin_hdlr2 = lambda name: self.event_handler(name, 'bhdlr2')
        normal_hdlr1 = lambda name: self.event_handler(name, 'nhdlr1')
        normal_hdlr2 = lambda name: self.event_handler(name, 'nhdlr2')
        begin_handlers = [begin_hdlr1, begin_hdlr2]
        normal_handlers = [normal_hdlr1, normal_hdlr2]
        engine.register_event_handler('begin_step', begin_hdlr1)
        engine.register_event_handler('begin_step', begin_hdlr2)
        engine.register_event_handler('normal_step', normal_hdlr1)
        engine.register_event_handler('normal_step', normal_hdlr2)
        self.assertEqual(begin_handlers, engine.event_handlers['begin_step'])
        self.assertEqual(normal_handlers, engine.event_handlers['normal_step'])
        engine.unregister_event_handler('normal_step', normal_hdlr1)
        self.assertEqual([normal_hdlr2], engine.event_handlers['normal_step'])
        engine.unregister_event_handler('normal_step', normal_hdlr2)
        self.assertTrue('normal_step' not in engine.event_handlers)

    def test_010event_handling(self):
        """Test queuing and transmission of events."""
        self.called_events = []
        self.event_engine.register_event_handler(
            'mouse_left_pressed', lambda name: self.event_handler(name, 'hdlr1'))
        self.event_engine.register_event_handler(
            'mouse_left_pressed', lambda name: self.event_handler(name, 'hdlr2'))
        self.event_engine.register_event_handler(
            'normal_step', lambda name: self.event_handler(name, 'hdlr1'))
        self.event_engine.queue_event(StepEvent('begin_step'))
        self.event_engine.queue_event(MouseEvent('mouse_left_pressed', {"x":20, "y":42}))
        self.event_engine.queue_event(MouseEvent('mouse_left_pressed', {"x":40, "y":62}))
        self.event_engine.queue_event(MouseEvent('mouse_left_pressed', {"x":0, "y":0}))
        self.event_engine.queue_event(StepEvent('normal_step'))
        self.event_engine.transmit_event('begin_step')
        self.event_engine.transmit_event('mouse_left_pressed')
        self.event_engine.transmit_event('normal_step')
        print("event handler calls:\n{}".format(self.called_events))
        expected_calls = [
            '<MouseEvent "mouse_left_pressed" x=20,y=42> hdlr1',
            '<MouseEvent "mouse_left_pressed" x=20,y=42> hdlr2',
            '<MouseEvent "mouse_left_pressed" x=40,y=62> hdlr1',
            '<MouseEvent "mouse_left_pressed" x=40,y=62> hdlr2',
            '<MouseEvent "mouse_left_pressed" x=0,y=0> hdlr1',
            '<MouseEvent "mouse_left_pressed" x=0,y=0> hdlr2',
            '<StepEvent "normal_step"> hdlr1'
        ]
        self.assertEqual(self.called_events, expected_calls)

unittest.main()

