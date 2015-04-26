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
        if not event_name in self.event_handlers:
            self.event_handlers[event_name] = [event_handler]
        else:
            self.event_handlers[event_name].append(event_handler)

    def queue_event(self, event, **event_kwargs):
        """
            queue_event():
            Add the given event along with a possible keyword-argument hash
            to the event queue.
        """
        ename = event.event_name
        if not ename in self.event_queues:
            self.event_queues[ename] = [(event, **event_kwargs)]
        else:
            self.event_queues[ename].append( (event, **event_kwargs) )

    def transmit_event(self, event_name):
        """
            Check the event names of all queued events, and if one or more
            handlers is found, forward the named event along with a possible
            keyword-argument hash.
        """
        for evname in self.event_queues:
            if evname in self.event_handlers:
                for queued in self.event_queues[evname]:
                    for handler in self.event_handlers[evname]:
                        handler[0](queued[1])

    def transmit_event_type(self, event_type):
        """
            transmit_event_type():
            Handle all events of the given event type.
        """
        for event_name in event_type.HANDLED_EVENTS:
            self.transmit_event(event_name)


