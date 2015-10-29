#!/usr/bin/python -W all

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# define the class that allows other classes to subscribe to and receive events

from pygame_maker.support import logging_object
import re
import event

class EventEngine(logging_object.LoggingObject):
    """
        EventEngine class:
        The source and target of game-generated events. Events are queued
        before being routed on command to targets that have registered for
        accepting particular events.
    """
    def __init__(self):
        super(EventEngine, self).__init__(type(self).__name__)
        self.event_handlers = {}
        self.event_queues = {}

    def register_event_handler(self, event_name, event_handler):
        """
            register_event_handler():
            Add a handler method reference to the named event
        """
        self.debug("register_event_handler({}, <hdlr>):".format(event_name))
        if not event_name in self.event_handlers.keys():
            self.info("  add event handler #1 for {}".format(event_name))
            self.event_handlers[event_name] = [event_handler]
        else:
            idx = len(self.event_handlers[event_name]) + 1
            self.info("  add event handler #{} for {}".format(idx, event_name))
            self.event_handlers[event_name].append(event_handler)
        #print("handlers: {}".format(self.event_handlers))

    def unregister_event_handler(self, event_name, event_handler):
        """
            unregister_event_handler():
            Remove a handler method reference from the named event
        """
        self.debug("unregister_event_handler({}, <hdlr>):".format(event_name))
        if event_name in self.event_handlers.keys():
            if event_handler in self.event_handlers[event_name]:
                self.info("  remove event handler for {}".format(event_name))
                self.event_handlers[event_name].remove(event_handler)
                if len(self.event_handlers[event_name]) == 0:
                    self.info("  delete last event handler for {}".format(event_name))
                    del(self.event_handlers[event_name])

    def queue_event(self, event):
        """
            queue_event():
            Add the given event along with a possible keyword-argument hash
            to the event queue.
        """
        self.debug("queue_event({}):".format(event))
        ename = event.name
        if not ename in self.event_queues.keys():
            self.debug("  queue event #1 named {}".format(ename))
            self.event_queues[ename] = [event]
        else:
            idx = len(self.event_queues[ename]) + 1
            self.debug("  queue event #{} named {}".format(idx, ename))
            self.event_queues[ename].append(event)
        #print("queues: {}".format(self.event_queues))

    def transmit_event(self, event_name):
        """
            Check the event names of all queued events, and if one or more
            handlers is found, forward the named event along with a possible
            keyword-argument hash.
        """
        #print("check for {} handlers..".format(event_name))
        self.debug("transmit_event({}):".format(event_name))
        if event_name in self.event_handlers.keys():
            #print("found. check for event queues..")
            queue_len = len(self.event_queues[event_name])
            if queue_len > 0:
                self.debug("  found {} queued {} events".format(queue_len, event_name))
            for queued in self.event_queues[event_name]:
                #print("handle queue item {}".format(queued))
                for idx, handler in enumerate(self.event_handlers[event_name]):
                    self.debug("    call handler #{}".format(idx+1))
                    handler(queued)
            # clear the queue
            self.debug("  delete queued {} events".format(event_name))
            del(self.event_queues[event_name])

    def transmit_event_type(self, event_type):
        """
            transmit_event_type():
            Call handlers for all events of the given event type.
        """
        self.debug("transmit_event_type({})".format(event_type))
        for event_name in event_type.HANDLED_EVENTS:
            self.transmit_event(event_name)

