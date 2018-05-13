"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Define the class that allows other classes to subscribe to and receive events.
"""

from pygame_maker.support import logging_object


class EventEngine(logging_object.LoggingObject):
    """
    The source and target of game-generated events. Events are queued before
    being routed on command to targets that have registered for accepting
    particular events.
    """
    def __init__(self):
        super(EventEngine, self).__init__(type(self).__name__)
        #: A dict with event names as keys; each key contains a list of all
        #: handlers registered for that event
        self.event_handlers = {}
        #: A dict with event names as keys; each key contains a list of
        #: `pygame_maker.events.event.Event` instances of that named type that
        #: have been queued, and that will be transmitted by transmit_event()
        #: when that event name is supplied as a parameter
        self.event_queues = {}

    def register_event_handler(self, event_name, event_handler):
        """
        Add a handler method reference to the named event.

        :param event_name: The name of the event to register a handler for
        :type event_name: str
        :param event_handler: The event handler method
        :type event_handler: callable
        """
        self.debug("register_event_handler({}, <hdlr>):".format(event_name))
        if event_name not in list(self.event_handlers.keys()):
            self.info("  add event handler #1 for {}".format(event_name))
            self.event_handlers[event_name] = [event_handler]
        else:
            idx = len(self.event_handlers[event_name]) + 1
            self.info("  add event handler #{:d} for {}".format(idx, event_name))
            self.event_handlers[event_name].append(event_handler)
        # print("handlers: {}".format(self.event_handlers))

    def unregister_event_handler(self, event_name, event_handler):
        """
        Remove a handler method reference from the named event.

        :param event_name: The name of the event to unregister a handler for
        :type event_name: str
        :param event_handler: The event handler method to remove
        :type event_handler: callable
        """
        self.debug("unregister_event_handler({}, <hdlr>):".format(event_name))
        if event_name in list(self.event_handlers.keys()):
            if event_handler in self.event_handlers[event_name]:
                self.info("  remove event handler for {}".format(event_name))
                self.event_handlers[event_name].remove(event_handler)
                if len(self.event_handlers[event_name]) == 0:
                    self.info("  delete last event handler for {}".format(event_name))
                    del self.event_handlers[event_name]

    def queue_event(self, an_event):
        """
        Add the given event to the event queue.

        :param an_event: The event to add to the queue
        :type an_event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("queue_event({}):".format(an_event))
        ename = an_event.name
        if ename not in list(self.event_queues.keys()):
            self.debug("  queue event #1 named {}".format(ename))
            self.event_queues[ename] = [an_event]
        else:
            idx = len(self.event_queues[ename]) + 1
            self.debug("  queue event #{:d} named {}".format(idx, ename))
            self.event_queues[ename].append(an_event)
        # print("queues: {}".format(self.event_queues))

    def transmit_event(self, event_name):
        """
        Forward queued events matching the named event (if handlers exist for
        it), to each registered handler.

        Delete the queued events after handling them.

        :param event_name: The name of the event to transmit to its handlers
        :type event_name: str
        """
        # print("check for {} handlers..".format(event_name))
        self.debug("transmit_event({}):".format(event_name))
        if event_name in list(self.event_handlers.keys()):
            # print("found. check for event queues..")
            queue_len = len(self.event_queues[event_name])
            if queue_len > 0:
                self.debug("  found {:d} queued {} events".format(queue_len,
                                                                  event_name))
            for queued in self.event_queues[event_name]:
                # print("handle queue item {}".format(queued))
                for idx, handler in enumerate(self.event_handlers[event_name]):
                    self.debug("    call handler #{:d}".format(idx+1))
                    handler(queued)
            # clear the queue
            self.debug("  delete queued {} events".format(event_name))
            del self.event_queues[event_name]

    def transmit_event_type(self, event_type):
        """
        Call handlers for all events of the given event type.

        For event types that are best handled all at one place in the game
        engine.

        :param event_type: An event type
        :type event_type: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("transmit_event_type({})".format(event_type))
        for event_name in event_type.HANDLED_EVENTS:
            self.transmit_event(event_name)
