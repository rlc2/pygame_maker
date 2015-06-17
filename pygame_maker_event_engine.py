#!/usr/bin/python -W all

import re
import pygame_maker_event as pygm_event

class PyGameMakerEventEngine(object):
    """
        PyGameMakerEventEngine class:
        The source and target of game-generated events. Events are queued
        before being routed on command to targets that have registered for
        accepting particular events.
    """
    def __init__(self):
        self.event_handlers = {}
        self.event_queues = {}

    def register_event_handler(self, event_name, event_handler):
        """
            register_event_handler():
            Add a handler method reference to the named event
        """
        if not event_name in self.event_handlers.keys():
            self.event_handlers[event_name] = [event_handler]
        else:
            self.event_handlers[event_name].append(event_handler)
        #print("handlers: {}".format(self.event_handlers))

    def unregister_event_handler(self, event_name, event_handler):
        """
            unregister_event_handler():
            Remove a handler method reference from the named event
        """
        if event_name in self.event_handlers.keys():
            if event_handler in self.event_handlers[event_name]:
                self.event_handlers[event_name].remove(event_handler)
                if len(self.event_handlers[event_name]) == 0:
                    del(self.event_handlers[event_name])

    def queue_event(self, event):
        """
            queue_event():
            Add the given event along with a possible keyword-argument hash
            to the event queue.
        """
        ename = event.event_name
        if not ename in self.event_queues.keys():
            self.event_queues[ename] = [event]
        else:
            self.event_queues[ename].append(event)
        #print("queues: {}".format(self.event_queues))

    def transmit_event(self, event_name):
        """
            Check the event names of all queued events, and if one or more
            handlers is found, forward the named event along with a possible
            keyword-argument hash.
        """
        #print("check for {} handlers..".format(event_name))
        if event_name in self.event_handlers.keys():
            #print("found. check for event queues..")
            for queued in self.event_queues[event_name]:
                #print("handle queue item {}".format(queued))
                for handler in self.event_handlers[event_name]:
                    #print("call handler!")
                    handler(queued)
            # clear the queue
            del(self.event_queues[event_name])

    def transmit_event_type(self, event_type):
        """
            transmit_event_type():
            Call handlers for all events of the given event type.
        """
        for event_name in event_type.HANDLED_EVENTS:
            self.transmit_event(event_name)

if __name__ == "__main__":
    import unittest

    class TestPyGameMakerEventEngine(unittest.TestCase):

        def setUp(self):
            self.event_engine = PyGameMakerEventEngine()
            self.called_events = []
 
        def event_handler(self, event, ev_tag):
            print("{} received event {}.".format(ev_tag, event))
            self.called_events.append("{} {}".format(event, ev_tag))

        def test_005event_handler_registration(self):
            engine = PyGameMakerEventEngine()
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
            self.assertEqual(begin_handlers,
                engine.event_handlers['begin_step'])
            self.assertEqual(normal_handlers,
                engine.event_handlers['normal_step'])
            engine.unregister_event_handler('normal_step', normal_hdlr1)
            self.assertEqual([normal_hdlr2],
                engine.event_handlers['normal_step'])
            engine.unregister_event_handler('normal_step', normal_hdlr2)
            self.assertTrue('normal_step' not in engine.event_handlers)

        def test_010event_handling(self):
            self.called_events = []
            self.event_engine.register_event_handler('left_pressed',
                lambda name: self.event_handler(name, 'hdlr1'))
            self.event_engine.register_event_handler('left_pressed',
                lambda name: self.event_handler(name, 'hdlr2'))
            self.event_engine.register_event_handler('normal_step',
                lambda name: self.event_handler(name, 'hdlr1'))
            self.event_engine.queue_event(pygm_event.PyGameMakerStepEvent('begin_step'))
            self.event_engine.queue_event(pygm_event.PyGameMakerMouseEvent('left_pressed', { "x":20, "y":42 } ))
            self.event_engine.queue_event(pygm_event.PyGameMakerMouseEvent('left_pressed', { "x":40, "y":62 } ))
            self.event_engine.queue_event(pygm_event.PyGameMakerMouseEvent('left_pressed', { "x":0, "y":0 } ))
            self.event_engine.queue_event(pygm_event.PyGameMakerStepEvent('normal_step'))
            self.event_engine.transmit_event('begin_step')
            self.event_engine.transmit_event('left_pressed')
            self.event_engine.transmit_event('normal_step')
            print("event handler calls:\n{}".format(self.called_events))
            expected_calls = [
                '<PyGameMakerMouseEvent "left_pressed" x=20,y=42> hdlr1',
                '<PyGameMakerMouseEvent "left_pressed" x=20,y=42> hdlr2',
                '<PyGameMakerMouseEvent "left_pressed" x=40,y=62> hdlr1',
                '<PyGameMakerMouseEvent "left_pressed" x=40,y=62> hdlr2',
                '<PyGameMakerMouseEvent "left_pressed" x=0,y=0> hdlr1',
                '<PyGameMakerMouseEvent "left_pressed" x=0,y=0> hdlr2',
                '<PyGameMakerStepEvent "normal_step"> hdlr1'
            ]
            self.assertEqual(self.called_events, expected_calls)

    unittest.main()

