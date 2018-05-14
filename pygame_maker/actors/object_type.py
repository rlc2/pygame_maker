"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Pygame maker object type resource module.
"""

import math
import re
import logging
import pygame
import yaml
from pygame_maker.support import logging_object
import pygame_maker.actors.simple_object_instance as simple_object_instance
import pygame_maker.actors.object_instance as object_instance
import pygame_maker.actors.object_sprite as object_sprite
from pygame_maker.events import event
from pygame_maker.actions import action
from pygame_maker.actions import action_sequence


class ObjectTypeException(logging_object.LoggingException):
    """
    Raised when an ObjectType references an unknown sprite resource, or
    unhandled event types are added to the event handler, or an event
    handler was passed an invalid object.
    """
    pass


def sprite_collision_test(sprite_a, sprite_b):
    """
    Determine whether 2 sprites intersect.

    Currently, there are three types of collision masks that may be used to
    detect a collision:

    * rectangle: Used if both sprites have collision_type 'rectangle'
    * disk: Used if both sprites have collision_type 'disk'
    * precise: Used if both sprites have collision_type 'precise', or
      their collision types don't match

    :param sprite_a: The sprite to test for a collision
    :type sprite_a: :py:class:`~pygame_maker.actors.object_sprite.ObjectSprite`
    :param sprite_b: The other sprite to test for a collision
    :type sprite_b: :py:class:`~pygame_maker.actors.object_sprite.ObjectSprite`
    :return: True if the two sprites collided, or False
    :rtype: bool
    """
    if sprite_a == sprite_b:
        return False
    if not sprite_a or not sprite_b:
        return False
    if not sprite_a.image or not sprite_b.image:
        return False
    coll_types = (sprite_a.kind.sprite_resource.collision_type,
                  sprite_b.kind.sprite_resource.collision_type)
    # simple cases first: both rectangular or disk collision types
    if coll_types == ("rectangle", "rectangle"):
        return pygame.sprite.collide_rect(sprite_a, sprite_b)
    elif coll_types == ("disk", "disk"):
        return pygame.sprite.collide_circle(sprite_a, sprite_b)
    else:
        # any mismatches fall back to mask collisions
        return pygame.sprite.collide_mask(sprite_a, sprite_b)


def get_collision_normal(instance_a, instance_b):
    """
    Get an approximate collision normal between overlapping instances,
    from instance_a's perspective.

    :param instance_a: The first ObjectInstance to calculate a collision
        normal from
    :type instance_a: :py:class:`~pygame_maker.actors.object_instance.ObjectInstance`
    :param instance_b: The second ObjectInstance to calculate a collision
        normal from
    :type instance_b: :py:class:`~pygame_maker.actors.object_instance.ObjectInstance`
    :return: The normal vector
    :rtype: (int, int)
    """
    offset = get_offset_between_instances(instance_a, instance_b)
    overlap = get_mask_overlap(instance_a, instance_b)
    # print("Solid collision overlap for normal: {}".format(overlap))
    if overlap == 0:
        # no collision here..
        return None
    normx = (instance_a.mask.overlap_area(instance_b.mask,
                                          (offset[0]+1, offset[1])) -
             instance_a.mask.overlap_area(instance_b.mask,
                                          (offset[0]-1, offset[1])))
    normy = (instance_a.mask.overlap_area(instance_b.mask,
                                          (offset[0], offset[1] + 1)) -
             instance_a.mask.overlap_area(instance_b.mask,
                                          (offset[0], offset[1] - 1)))
    if (normx == 0) and (normy == 0):
        # can't get a normal when one object is inside another..
        return None
    return (normx, normy)


def get_offset_between_instances(instance_a, instance_b):
    """
    Return the position offset between instance_a and instance_b from
        instance_a's perspective.

    :param instance_a: The first ObjectInstance to calculate the offset from
    :type instance_a: :py:class:`~pygame_maker.actors.object_instance.ObjectInstance`
    :param instance_b: The second ObjectInstance to calculate the offset from
    :type instance_b: :py:class:`~pygame_maker.actors.object_instance.ObjectInstance`
    :return: The offset in pixels
    :rtype: int
    """
    instance_a_pos = (instance_a.rect.x, instance_a.rect.y)
    instance_b_pos = (instance_b.rect.x, instance_b.rect.y)
    offset = (instance_b_pos[0]-instance_a_pos[0],
              instance_b_pos[1]-instance_a_pos[1])
    return offset


def get_mask_overlap(instance_a, instance_b):
    """
    Return the number of pixels that instance_a overlaps instance_b.

    :param instance_a: The first ObjectInstance with overlapping pixels
    :type instance_a: :py:class:`~pygame_maker.actors.object_instance.ObjectInstance`
    :param instance_b: The second ObjectInstance with overlapping pixels
    :type instance_b: :py:class:`~pygame_maker.actors.object_instance.ObjectInstance`
    :return: The number of pixels that overlap
    :rtype: int
    """
    offset = get_offset_between_instances(instance_a, instance_b)
    overlap = instance_a.mask.overlap_area(instance_b.mask, offset)
    return overlap


def dot_product(vec1, vec2):
    """
    Calculate a dot product between 2 vectors.

    :param vec1: The first vector
    :type vec1: (float, float)
    :param vec2: The second vector
    :type vec2: (float, float)
    :return: The dot product
    :rtype: float
    """
    return vec1[0] * vec2[0] + vec1[1] * vec2[1]


class ObjectType(logging_object.LoggingObject):
    """
    All PyGameMaker objects:

    * respond to events

      * ex: create. normal step. draw.
      * events can be modified, edited (appears to just add a run code
        action), or deleted.

    * implement actions

      * things that happen in response to events
      * change direction.  jump to a location.  run code.  affect score/lives.
        play a sound.
      * actions can be chained together
      * actions can be "questions".  Depending on the answer, the following
        action(s) may execute

    Objects, like classes, are instantiated within the game.  There can be many
    instances of a particular kind of object.
    """
    DEFAULT_OBJECT_PREFIX = "obj_"
    EVENT_NAME_OBJECT_HASH = {
        "outside_room": event.OtherEvent,
        "intersect_boundary": event.OtherEvent,
        "child_outside_room": event.OtherEvent,
        "child_intersect_boundary": event.OtherEvent,
        "parent_outside_room": event.OtherEvent,
        "parent_intersect_boundary": event.OtherEvent,
        "create": event.ObjectStateEvent,
        "create_child": event.ObjectStateEvent,
        "image_loaded": event.OtherEvent,
        "destroy": event.ObjectStateEvent,
        "destroy_child": event.ObjectStateEvent,
        "destroy_parent": event.ObjectStateEvent,
        "collision": event.CollisionEvent,
        "child_collision": event.CollisionEvent,
        "parent_collision": event.CollisionEvent,
        "draw": event.DrawEvent,
    }
    GLOBAL_MOUSE_RE = re.compile("global")

    object_type_registry = []

    @classmethod
    def register_object_type(cls, object_type):
        """
        Register object type subclasses, so load_from_yaml() can recognize the
        object types named in YAML files and create them.

        :param object_type: The new ObjectType subclass
        :type object_type: ObjectType
        """
        cls.object_type_registry.append(object_type)

    @classmethod
    def gen_kwargs_from_yaml_obj(cls, obj_name, obj_yaml, game_engine):
        """
        Create a kwargs dict from the YAML parameters describing an object
        type.

        Every ObjectType knows how to interpret event action sequences.

        :param obj_yaml: The yaml.load() generated object
        :return: A dict mapping known parameters to the values defined in the
            YAML object
        :rtype: dict
        """
        kwargs = {"event_action_sequences": {}}
        if "events" in obj_yaml.keys():
            # print("Found '{}', passing {} to load..".format(kwarg, obj_yaml[kwarg]))
            for ev_seq in obj_yaml["events"]:
                game_engine.debug("{}: create event sequence from '{}'".
                                  format(obj_name, obj_yaml['events'][ev_seq]))
                kwargs["event_action_sequences"][ev_seq] = \
                    action_sequence.ActionSequence.load_sequence_from_yaml_obj(
                        obj_yaml['events'][ev_seq])
                game_engine.debug("Loaded sequence {}:".format(ev_seq))
                if game_engine.logger.level <= logging.DEBUG:
                    kwargs["event_action_sequences"][ev_seq].pretty_print()
        return kwargs

    @classmethod
    def load_from_yaml_obj(cls, yaml_obj, game_engine):
        """
        Create an object type from an object returned by yaml.load().

        :param yaml_stream: A file or stream containing the YAML string data
        :type yaml_stream: file-like
        :param game_engine: A reference to the main game engine
        :type game_engine: GameEngine
        :return: A new ObjectType with YAML-defined properties
        :type: :py:class:`ObjectType`
        """
        new_object_list = []
        for top_level in yaml_obj:
            # hash of 1 key, the object name
            obj_name = top_level.keys()[0]
            # 'events' key contains event -> action sequence mappings
            obj_yaml = top_level[obj_name]
            kwargs = cls.gen_kwargs_from_yaml_obj(obj_name, obj_yaml, game_engine)
            print "Creating new obj '{}' of type {}".format(obj_name, cls.__name__)
            new_cls = cls(obj_name, game_engine, **kwargs)
            new_object_list.append(new_cls)
        return new_object_list

    @classmethod
    def load_from_yaml(cls, yaml_stream, game_engine):
        """
        Create an object type list from a YAML-formatted file.
        Expected format::

            obj_type1:
              - obj_name1:
                  events:
                    <event1_name>:
                      <yaml representation for event action sequence>
                    ...
                    <eventN_name>:
                      <yaml representation for event action sequence>
              - obj_name2:
                ...
              ...
            obj_type2:
            ...

        For a description of the action sequence YAML format, see
        :py:meth:`~pygame_maker.actions.action_sequence.ActionSequence.load_sequence_from_yaml_obj`

        Each obj_typeN must match a registered object type's name.

        :param yaml_stream: A file or stream containing the YAML string data
        :type yaml_stream: file-like
        :param game_engine: A reference to the main game engine
        :type game_engine: GameEngine
        :return: A new ObjectType with YAML-defined properties
        :type: :py:class:`ObjectType`
        """
        new_object_list = []
        yaml_repr = yaml.load(yaml_stream)
        if yaml_repr is not None:
            for obj_type_name in yaml_repr.keys():
                for reg_obj_type in cls.object_type_registry:
                    # print("Compare {} with {}".format(obj_type_name, reg_obj_type.__name__))
                    if obj_type_name == reg_obj_type.__name__:
                        new_object_list += reg_obj_type.load_from_yaml_obj(
                            yaml_repr[obj_type_name], game_engine)
                        break
        return new_object_list

    def __init__(self, object_name, game_engine, **kwargs):

        """
        Create a new type of object.

        :param object_name: Supply a name for the object type
        :type object_name: str
        :param game_engine: Supply the main game engine
            containing an event engine, language engine, sprite resources,
            sound resources, other object types, and handlers for certain game
            actions
        :type game_engine: GameEngine
        :param kwargs: Supply alternatives for default object properties:

            * visible (bool): Whether instances will be drawn [True]
            * solid (bool): Whether instances block other object instances
              (e.g. a platform) [False]
            * depth (int): Which layer object instances will be placed into [0]
            * sprite (str): Name of a sprite resource used as the image [None]
        """
        super(ObjectType, self).__init__(type(self).__name__)
        self.debug("New object type {} named '{}', with args {}".format(
            type(self).__name__, object_name, kwargs))
        #: The name other resources will refer to this one by
        self.name = self.DEFAULT_OBJECT_PREFIX
        if object_name:
            self.name = object_name
        #: A reference to the game engine, for executing game engine actions
        self.game_engine = game_engine
        # A unique instance ID
        self._id = 0
        #: A list of instances of this object type
        self.instance_list = []
        #: For collideable object instances; left empty in base class
        self.group = []
        #: A list of instances to delete following update()
        self.instance_delete_list = set()
        #: A mapping of event regexs to handler methods
        self.handler_table = {
            re.compile(r"^alarm(\d{1,2})$"):    self.handle_alarm_event,
            re.compile("^kb_(.*)$"):            self.handle_keyboard_event,
            re.compile("^mouse_(.*)$"):         self.handle_mouse_event,
            re.compile("^(parent_|child_)?collision_(.*)$"):     self.handle_collision_event,
            re.compile("^([^_]+)_step$"):       self.handle_step_event,
            re.compile("^outside_room$"):       self.handle_instance_event,
            re.compile("^intersect_boundary$"): self.handle_instance_event,
            re.compile("^create$"):             self.handle_create_event,
            re.compile("^destroy$"):            self.handle_destroy_event,
            re.compile("^draw$"):               self.draw,
        }
        #: A dict mapping event names to action sequences
        self.event_action_sequences = {}
        if ((kwargs is not None) and ("event_action_sequences" in kwargs.keys()) and
                kwargs["event_action_sequences"]):
            ev_dict = kwargs["event_action_sequences"]
            for ev_name in ev_dict:
                if not isinstance(ev_dict[ev_name], action_sequence.ActionSequence):
                    raise(ObjectTypeException("Event '{}' does not contain an ActionSequence",
                                              self.error))
                self[ev_name] = ev_dict[ev_name]

    def add_instance_to_delete_list(self, instance):
        """
        Given a sprite reference, add it to the list of instances of this
        object to be deleted.

        This allows for iterating through objects and flagging them for removal
        without trying to remove them inside the iterator.  Deletion occurs
        following the update() call for the object.

        :param instance: The ObjectInstance of this type to be removed
        :type instance: :py:class:`~pygame_maker.actors.object_instance.ObjectInstance`
        """
        self.debug("add_instance_to_delete_list(instance={}):".format(instance))
        self.instance_delete_list.add(instance)

    def make_new_instance(self, screen, instance_properties=None):
        """
        Generate a new instance of this object type in response to
            :py:meth:`create_instance`

        :param screen: The surface the instance will be drawn upon.  The
            instance can use this surface's width and height parameters to
            detect boundary collision events, which are queued in the event
            engine
        :type screen: :py:class:`pygame.Surface`
        :param instance_properties: A hash of settings to be applied.  See
            kwargs entry in
            :py:meth:`~pygame_maker.actors.simple_object_instance.SimpleObjectInstance.__init__`
        :type instance_properties: dict
        """
        screen_dims = (screen.get_width(), screen.get_height())
        new_instance = simple_object_instance.SimpleObjectInstance(
            self, screen_dims, self._id, instance_properties)
        self.instance_list.append(new_instance)
        return new_instance

    def create_instance(self, screen, settings=None, **kwargs):
        """
        Create a new instance of this object type.

        Every instance is assigned a unique ID, and a create event is queued
        to be passed on to the new instance.

        :param screen: The surface the instance will be drawn upon.  The
            instance can use this surface's width and height parameters to
            detect boundary collision events, which are queued in the event
            engine
        :type screen: :py:class:`pygame.Surface`
        :param settings: A hash of settings to be applied.  See kwargs entry
            in :py:meth:`~pygame_maker.actors.object_instance.ObjectInstance.__init__`
        :type settings: dict
        :param kwargs: Named settings can be passed in, in addition to
            the settings hash
        """
        self.debug("create_instance(screen={}, settings={}, kwargs={}):".
                   format(screen, settings, kwargs))
        self.info("  Create instance of {} with args {}, {}".format(self.name, settings, kwargs))
        instance_properties = {}
        if settings is not None:
            instance_properties.update(settings)
        instance_properties.update(kwargs)
        parent_inst = None
        if 'parent' in instance_properties:
            # don't initialize the new instance with the 'parent' property,
            # just record the parent and connect the two instances once the
            # child instance has been created
            parent_inst = instance_properties["parent"]
            del instance_properties["parent"]
        new_instance = self.make_new_instance(screen, instance_properties)
        if parent_inst is not None:
            # connect parent and child instances
            new_instance.set_parent_instance(parent_inst)
        self._id += 1
        # queue and transmit the creation event for the new instance
        self.game_engine.event_engine.queue_event(
            self.EVENT_NAME_OBJECT_HASH["create"]("create", {"type": self,
                                                             "instance": new_instance}))
        self.game_engine.event_engine.transmit_event('create')
        if parent_inst is not None:
            # queue and transmit the create_child instance for the instance's parent
            self.game_engine.event_engine.queue_event(self.EVENT_NAME_OBJECT_HASH["create_child"](
                "create_child", {"type": parent_inst.kind, "instance": parent_inst,
                                 "child_type": self}))
            self.game_engine.event_engine.transmit_event('create_child')
        return new_instance

    def get_instances(self):
        """
        Return a list of all instances of the ObjectType.

        :return: A list of all instances
        :rtype: list
        """
        return self.instance_list

    #pylint: disable=no-self-use
    #pylint: disable=unused-argument
    def collision_check(self, other_obj_types):
        """
        Override this method in subclasses that implement collision detection.

        :param other_obj_types: A list of other ObjectTypes to test
            for collisions with this one
        :type other_obj_types: array-like
        :return: A list of collision event names that were queued, or an
            empty list if none
        """
        return set()
    #pylint: enable=unused-argument
    #pylint: enable=no-self-use

    def update(self):
        """
        Update all instances of this object type.  This base class method only
        handles instances scheduled for deletion, and is meant to be called by
        a subclass's update() method after updating its instances.
        """
        if len(self.instance_delete_list) > 0:
            for doomed_instance in self.instance_delete_list:
                self.instance_list.remove(doomed_instance)
            self.instance_delete_list = set()

    def draw(self, in_event):
        """
        Draw all instances in response to a ``draw_self`` event.  Meant to be
        overridden if needed by a subclass.

        :param in_event: The ``draw_self`` event
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        """
        pass

    #pylint: disable=no-self-use
    #pylint: disable=unused-argument
    def get_applied_instance_list(self, an_action, in_event):
        """
        Return a list of the instances affected by the combination of an event
        and an action triggered by the event.  Meant to be overridden if needed
        by a subclass.

        :param action: The action with an "apply_to" field
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        :param in_event: The event to be handled
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        """
        return []
    #pylint: enable=unused-argument
    #pylint: enable=no-self-use

    def execute_action_sequence(self, in_event, targets=None):
        """
        Walk through an event action sequence when the event handler matches a
        known event.

        The sausage factory method.  There are many types of actions; the
        object instance actions make the most sense to handle here, but the
        game engine that inspired this one uses a model in which a hidden
        manager object type triggers actions that affect other parts of the
        game engine, so those actions need to be routed properly as well.

        :param in_event: The event to be handled
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        :param targets: The event handler may pass in a list of target
            instances for the action sequence to operate on
        :type targets: array-like | None
        """
        self.debug("execute_action_sequence(in_event={}, targets={}):".format(in_event, targets))
        if in_event.name in self.event_action_sequences:
            self.info("  Execute action sequence for event '{}'".format(in_event))
            with logging_object.Indented(self):
                self.debug("  Event args: {}".format(in_event.event_params))
                affected_instances = None
                if (targets is not None) and len(targets) > 0:
                    self.debug("  Apply to target(s) {}".format(str(targets)))
                    affected_instances = targets
                elif isinstance(in_event, event.KeyEvent):
                    # key events will be sent to all instances
                    affected_instances = self.get_instances()
                elif isinstance(in_event, event.MouseEvent):
                    gl_minfo = self.GLOBAL_MOUSE_RE.search(in_event.name)
                    if gl_minfo is not None:
                        affected_instances = self.get_instances()
                for an_action in self.event_action_sequences[in_event.name].get_next_action():
                    self.debug("  Execute action {}".format(an_action))
                    # forward instance actions to instance(s)
                    action_targets = affected_instances
                    if "apply_to" in an_action.action_data and affected_instances is None:
                        # follow any special apply_to rules in the action
                        action_targets = self.get_applied_instance_list(an_action, in_event)
                    elif affected_instances is None:
                        self.debug("  call game engine execute_action for {}".format(an_action))
                        self.game_engine.execute_action(an_action, in_event)
                        continue
                    self.debug("apply {} to targets {}".format(an_action.name, action_targets))
                    for target in action_targets:
                        if target in self.instance_delete_list:
                            self.info("Skipping about-to-be-destroyed instance {}".
                                      format(target.inst_id))
                            continue
                        if an_action.name not in self.game_engine.GAME_ENGINE_ACTIONS:
                            target.execute_action(an_action, in_event)
                        else:
                            # the game engine additionally receives the target
                            #  instance as a parameter
                            self.game_engine.execute_action(an_action, in_event, target)

    def handle_instance_event(self, in_event):
        """
        Handle an event generated by an instance of this type.  Meant to be
        overridden if needed by a subclass.

        :param in_event: The instance event
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        """
        pass

    def handle_mouse_event(self, in_event):
        """
        Execute the action sequence associated with the supplied mouse
        event.

        This base class method only applies to global mouse events.  Subclasses
        that need to handle specific mouse events should call this method first
        and use its return value to determine whether the mouse event was a
        global event (and already handled here).

        :param in_event: The mouse event
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        :return: True if the received mouse event was global and already
            handled in this base class method, False otherwise
        """
        self.debug("handle_mouse_event(in_event={}):".format(in_event))
        ret = False
        gl_minfo = self.GLOBAL_MOUSE_RE.search(in_event.name)
        if gl_minfo:
            self.execute_action_sequence(in_event)
            ret = True
        return ret

    def handle_keyboard_event(self, in_event):
        """
        Execute the action sequence associated with the supplied key event,
        if the exact key event is handled by this object (which key,
        press/release).

        :param in_event: The keyboard event
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_keyboard_event(in_event={}):".format(in_event))
        self.execute_action_sequence(in_event)

    def handle_collision_event(self, in_event):
        """
        Execute the action sequence associated with a collision event.

        The name of the object type collided with is part of the event's name,
        which should have been added as a key in the event_action_sequences
        attribute using the :py:meth:`__setitem__` interface.

        :param in_event: The collision event
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_collision_event(in_event={}):".format(in_event))
        if ((in_event.event_params["type"] == self) and
                (in_event.event_params["instance"] in self.group)):
            self.execute_action_sequence(in_event)

    def handle_step_event(self, in_event):
        """
        Execute the action sequence associated with the supplied step event, if
        the exact step event is handled by this object (begin, end, normal),
        on every instance.

        :param in_event: The step event
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_step_event(in_event={}):".format(in_event))
        self.execute_action_sequence(in_event, targets=[inst for inst in self.instance_list])

    def handle_alarm_event(self, in_event):
        """
        Execute the action sequence associated with the alarm event, if the
        exact alarm is handled by this object (one or more of alarms 0-11).

        :param in_event: The alarm event
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_alarm_event(in_event={}):".format(in_event))

    def handle_create_event(self, in_event):
        """
        Execute the action sequence associated with the create event, passing
        it on to the instance recorded in the event.

        :param in_event: The object creation event
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_create_event(in_event={}):".format(in_event))
        if ((in_event.event_params["type"] == self) and
                (in_event.event_params["instance"] in self.group)):
            self.execute_action_sequence(in_event)

    def handle_destroy_event(self, in_event):
        """
        Execute the action sequence associated with the destroy event.

        :param in_event: The destroy event
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_destroy_event(in_event={}):".format(in_event))
        if ((in_event.event_params["type"] == self) and
                (in_event.event_params["instance"] in self.group)):
            self.execute_action_sequence(in_event)

    def _select_event_handler(self, event_name):
        # Return an event type, given the name of the handled event.

        # :param event_name: The name of the received event
        # :type event_name: str
        # :return: An event handler
        # :rtype: callable
        self.debug("_select_event_handler(event_name={}):".format(event_name))
        hdlr = None
        for ev_re in self.handler_table.keys():
            minfo = ev_re.match(event_name)
            if minfo:
                hdlr = self.handler_table[ev_re]
        return hdlr

    def keys(self):
        """
        Return the event names handled by this object type, in a list.

        :return: A list of event names handled by this object type
        :rtype: list
        """
        self.debug("keys():")
        return self.event_action_sequences.keys()

    def __getitem__(self, itemname):
        """
        ObjectType instances support obj[event_name] to directly access the
        action sequence for a particular event.

        :param itemname: Name of an event
        :type itemname: str
        :return: An action sequence, or None
        :rtype: None | :py:class:`~pygame_maker.actions.action_sequence.ActionSequence`
        """
        self.debug("__getitem__(itemname={}):".format(itemname))
        if itemname in self.event_action_sequences:
            return self.event_action_sequences[itemname]
        else:
            return None

    def __setitem__(self, itemname, val):
        """
        ObjectType instances support obj[event_name] = sequence for
        directly setting the action sequence for a particular event.

        After adding the event action sequence, register the event handler
        for the event.

        :param itemname: Name of an event
        :type itemname: str
        :param val: New action sequence to apply to an event
        :type val: :py:class:`~pygame_maker.actions.action_sequence.ActionSequence`
        :raise: KeyError, if itemname is not a string
        :raise: ValueError, if val is not an ActionSequence
        """
        self.debug("__setitem__(itemname={}, val={}):".format(itemname, val))
        if not isinstance(itemname, str):
            raise KeyError("Event action sequence keys must be strings", self.error)
        if not isinstance(val, action_sequence.ActionSequence):
            raise(ValueError("Supplied event action sequence is not an ActionSequence instance",
                             self.error))
        self.event_action_sequences[itemname] = val
        # register our handler for this event
        new_handler = self._select_event_handler(itemname)
        if new_handler:
            self.info("{}: Register handler for event '{}'".format(self.name, itemname))
            self.game_engine.event_engine.register_event_handler(itemname, new_handler)
        else:
            raise(ObjectTypeException("ObjectType does not yet handle '{}' events (NYI)".
                                      format(itemname), self.error))

    def __delitem__(self, itemname):
        """
        Remove the named event from the action sequence table.

        :param itemname: The name of the event to stop handling
        :type itemname: str
        """
        self.debug("__delitem__(itemname={}):".format(itemname))
        if itemname in self.event_action_sequences:
            # stop handling the given event name
            old_handler = self._select_event_handler(itemname)
            self.info("  {}: Unregister handler for event '{}'".format(self.name, itemname))
            self.game_engine.event_engine.unregister_event_handler(itemname, old_handler)
            # remove the event from the table
            del self.event_action_sequences[itemname]


class ManagerObjectType(ObjectType):
    """
    Another name for the base ObjectType, to flag that the object type is meant
    to manage game state.
    """
    pass


class CollideableObjectType(ManagerObjectType):
    """
    Most in-game objects are of this type.  Collideable objects have:

    * sprite reference
    * depth (determines which objects draw on top of other objects) (numeric)
    * parent (another object)
    * collision mask (uses sprite reference, can be a different sprite)
    * visible flag (whether the object will be drawn)
    * persistent flag (unknown purpose, not implemented)
    * solid flag (for solid stationary objects, e.g. platform)
    * physics flag
    * blend modes
       0. Normal
       1. Add
       2. Subtract
       3. Multiply
       4. Minimum
       5. Maximum
       6. RGBA Add
       7. RGBA Subtract
       8. RGBA Multiply
       9. RGBA Minimum
      10. RGBA Maximum
      11. Blending RGB Add
      12. Blending RGB Subtract
      13. Blending RGB Multiply
      14. Blending RGB Minimum
      15. Blending RGB Maximum
      
    Expected YAML format for CollideableObjectType::

        - obj_name1:
            visible: True | False
            solid: True | False
            depth: <int>
            sprite: <sprite resource name>
            blend_mode: <int>
            events:
              <event1_name>:
                <yaml representation for event action sequence>
              ...
              <eventN_name>:
                <yaml representation for event action sequence>
        - obj_name2:
        ...

    For a description of the action sequence YAML format, see
    :py:meth:`~pygame_maker.actions.action_sequence.ActionSequence.load_sequence_from_yaml_obj`
    """
    #: Default object visibility
    DEFAULT_VISIBLE = True
    #: Default for 'solid' flag
    DEFAULT_SOLID = False
    #: Default depth
    DEFAULT_DEPTH = 0
    #: By default, a new ObjectType doesn't refer to a sprite yet
    DEFAULT_SPRITE_RESOURCE = None
    #: Default blend mode
    DEFAULT_BLEND_MODE = 0

    @classmethod
    def gen_kwargs_from_yaml_obj(cls, obj_name, obj_yaml, game_engine):
        kwargs = super(CollideableObjectType, cls).gen_kwargs_from_yaml_obj(obj_name, obj_yaml,
                                                                            game_engine)
        kwargs.update({
            "visible": CollideableObjectType.DEFAULT_VISIBLE,
            "solid": CollideableObjectType.DEFAULT_SOLID,
            "depth": CollideableObjectType.DEFAULT_DEPTH,
            "sprite": CollideableObjectType.DEFAULT_SPRITE_RESOURCE,
            "blend_mode": CollideableObjectType.DEFAULT_BLEND_MODE,
        })
        if "visible" in obj_yaml.keys():
            kwargs["visible"] = (obj_yaml["visible"] is True)
        if "solid" in obj_yaml.keys():
            kwargs["solid"] = (obj_yaml["solid"] is True)
        if "depth" in obj_yaml.keys():
            kwargs["depth"] = int(obj_yaml["depth"])
        if "sprite" in obj_yaml.keys():
            kwargs["sprite"] = str(obj_yaml["sprite"])
        if "blend_mode" in obj_yaml.keys():
            kwargs["blend_mode"] = str(obj_yaml["blend_mode"])
        return kwargs

    def __init__(self, object_name, game_engine, **kwargs):

        """
        Create a new type of object.

        :param object_name: Supply a name for the object type
        :type object_name: str
        :param game_engine: Supply the main game engine
            containing an event engine, language engine, sprite resources,
            sound resources, other object types, and handlers for certain game
            actions
        :type game_engine: GameEngine
        :param kwargs: Supply alternatives for default object properties:

            * visible (bool): Whether instances will be drawn [True]
            * solid (bool): Whether instances block other object instances
              (e.g. a platform) [False]
            * depth (int): Which layer object instances will be placed into [0]
            * sprite (str): Name of a sprite resource used as the image [None]
        """
        super(CollideableObjectType, self).__init__(object_name, game_engine, **kwargs)
        self.sprite_resource = self.DEFAULT_SPRITE_RESOURCE
        self.image = None
        self.bounding_box_rect = None
        self.mask = None
        self._visible = self.DEFAULT_VISIBLE
        self.solid = self.DEFAULT_SOLID
        self.depth = self.DEFAULT_DEPTH
        self.group = pygame.sprite.LayeredDirty()
        self.blend_mode = self.DEFAULT_BLEND_MODE
        # default draw action sequence draws the object's sprite
        self["draw"] = action_sequence.ActionSequence()
        self["draw"].append_action(action.DrawAction("draw_self"))
        if kwargs:
            for kwarg in kwargs:
                if kwarg == "visible":
                    self.visible = kwargs["visible"]
                if kwarg == "solid":
                    self.solid = (kwargs["solid"] is True)
                if kwarg == "depth":
                    self.depth = int(kwargs["depth"])
                if (kwarg == "sprite") and kwargs[kwarg]:
                    if kwargs['sprite'] in self.game_engine.resources['sprites'].keys():
                        assigned_sprite = self.game_engine.resources['sprites'][kwargs['sprite']]
                        if not isinstance(assigned_sprite, object_sprite.ObjectSprite):
                            raise(ObjectTypeException("'{}' is not a recognized sprite resource".
                                                      format(kwargs["sprite"]), self.error))
                        self.sprite_resource = assigned_sprite
                if kwarg == "blend_mode":
                    self.blend_mode = int(kwargs["blend_mode"])

        # print("Finished setup of {}".format(self.name))

    @property
    def visible(self):
        """
        Get and set the flag that determines whether the ObjectType will be drawn.
        """
        return self._visible

    @visible.setter
    def visible(self, is_visible):
        vis = (is_visible is True)
        if self._visible != vis:
            self._visible = vis
            for instance in self.group:
                instance.visible = is_visible

    def to_yaml(self):
        """Return the YAML string representing this object type."""
        yaml_str = "- {}:\n".format(self.name)
        yaml_str += "    visible: {}\n".format(self.visible)
        yaml_str += "    solid: {}\n".format(self.solid)
        yaml_str += "    depth: {:d}\n".format(self.depth)
        yaml_str += "    sprite: {}\n".format(self.sprite_resource.name)
        yaml_str += "    blend_mode: {:d}\n".format(self.blend_mode)
        yaml_str += "    events:\n"
        for event_name in self.event_action_sequences:
            yaml_str += "      {}:\n".format(event_name)
            yaml_str += self.event_action_sequences[event_name].to_yaml(8)
        return yaml_str

    def get_image(self, subimage_number=0):
        """
        Called by instances of this ObjectType, to get a new copy of
        the sprite resource's image.

        Load the image when the first instance using this image is created.
        Also, handle the collision type and create a collision mask.

        :param subimage_number: Which subimage to copy
        :type subimage_number: int
        :return: A tuple containing a new pygame image (copied from the
            ObjectSprite resource), a collision mask, a bounding box, and
            possibly an image radius (for disk collision masks)
        :rtype: tuple(:py:class:`pygame.Surface`, :py:class:`pygame.Mask`,
            :py:class:`pygame.Rect`, None|int)
        """
        self.debug("get_image():")
        if self.sprite_resource:
            if self.sprite_resource.image is None:
                self.sprite_resource.load_graphic()
                self.image = self.sprite_resource.image
                # queue the image_loaded event
                self.game_engine.event_engine.queue_event(
                    self.EVENT_NAME_OBJECT_HASH["image_loaded"]("image_loaded",
                                                                {"type": self,
                                                                 "sprite": self.sprite_resource})
                )
                self.info("  Queued 'image_loaded' event")
            # return an image (a copy of the subimage), a mask and possibly
            # radius from the sprite resource
            snum = subimage_number
            if subimage_number >= self.sprite_resource.subimage_info["count"]:
                self.warn("{}: An instance requested a subimage number ({}) out of range (max {})".
                          format(self.name, subimage_number,
                                 self.sprite_resource.subimage_info["count"]))
                # select the last subimage (counting from 0)
                snum = self.sprite_resource.subimage_info["count"] - 1
            image = self.sprite_resource.subimages[snum].copy()
            mask = self.sprite_resource.subimage_info["masks"][snum]
            bounding_box = self.sprite_resource.subimage_info["bbox_rects"][snum]
            radius = self.sprite_resource.subimage_info["radii"][snum]
            return image, mask, bounding_box, radius
        else:
            return None, None, None, None

    def get_instances(self):
        """
        Return a list of all instances of the CollideableObjectType.

        :return: A list of all instances
        :rtype: list
        """
        #pylint: disable=no-member
        return self.group.sprites()
        #pylint: enable=no-member

    def collision_check(self, other_obj_types):
        """
        Check for collisions between this and other object types' instances,
        and queue collision events when detected.

        :param other_obj_types: A list of other ObjectTypes to test
            for collisions with this one
        :type other_obj_types: array-like
        :return: A list of collision event names that were queued, or an
            empty list if none
        """
        self.debug("collision_check(other_obj_types={}):".format(other_obj_types))
        collision_types_queued = set()
        for other_obj in other_obj_types:
            # other_obj.group = other_obj.group
            if len(other_obj.group) == 0:
                continue
            if (len(self.group) == 1) and self.name == other_obj.name:
                # skip self collision detection if there's only one sprite
                continue
            collision_map = pygame.sprite.groupcollide(
                self.group, other_obj.group, False, False, collided=sprite_collision_test)
            for collider in collision_map.keys():
                collision_normal = None
                for other_inst in collision_map[collider]:
                    overlap = get_mask_overlap(collider, other_inst)
                    collision_normal = get_collision_normal(collider, other_inst)
                    # in the event of a collision with a solid object (i.e.
                    #  stationary), kick the sprite outside of the other
                    #  object's collision mask
                    if other_inst.kind.solid and collision_normal:
                        divisor = float(dot_product(collision_normal, collision_normal))
                        distance = 0
                        if divisor != 0:
                            distance = (float(overlap) / divisor + 0.5)
                        adj_x = math.floor(distance * collision_normal[0] + 0.5)
                        adj_y = math.floor(distance * collision_normal[1] + 0.5)
                        collider.position.x += adj_x
                        collider.position.y += adj_y
                collision_name = "collision_{}".format(other_obj.name)
                if collision_name not in collision_types_queued:
                    collision_types_queued.add(collision_name)
                self.debug("{} inst {}: Queue collision {}".
                           format(self.name, collider.inst_id, collision_name))
                collision_event_info = {
                    "type": self, "instance": collider,
                    "others": collision_map[collider]
                }
                if collision_normal:
                    collision_event_info['normal'] = collision_normal
                self.game_engine.event_engine.queue_event(
                    self.EVENT_NAME_OBJECT_HASH["collision"](collision_name,
                                                             collision_event_info)
                )
                # queue a child collision event if this instance has a parent
                if collider.symbols["parent"] is not None:
                    parent = collider.symbols["parent"]
                    child_collision_name = "child_{}".format(collision_name)
                    collision_types_queued.add(child_collision_name)
                    child_collision_info = dict(collision_event_info)
                    child_collision_info["type"] = parent.kind
                    child_collision_info["instance"] = parent
                    child_collision_info["child_type"] = self
                    self.game_engine.event_engine.queue_event(
                        self.EVENT_NAME_OBJECT_HASH["child_collision"](child_collision_name,
                                                                       child_collision_info)
                    )
                # queue parent collision events if this instance has children
                if len(collider.symbols["children"]) > 0:
                    for a_child in collider.symbols["children"]:
                        parent_collision_name = "parent_{}".format(collision_name)
                        collision_types_queued.add(parent_collision_name)
                        parent_collision_info = dict(collision_event_info)
                        parent_collision_info["type"] = a_child.kind
                        parent_collision_info["instance"] = a_child
                        parent_collision_info["parent_type"] = self
                        self.game_engine.event_engine.queue_event(
                            self.EVENT_NAME_OBJECT_HASH["parent_collision"](parent_collision_name,
                                                                            parent_collision_info)
                        )
        return collision_types_queued

    def update(self):
        """
        Call to perform position updates for all instances.  After all
        instances have updated, handle any queued deletions.
        """
        self.debug("update():")
        if len(self.group) > 0:
            #pylint: disable=no-member
            self.group.update()
            #pylint: enable=no-member
        # after all instances update(), check the delete list to see which
        #  ones should be removed and remove them
        if len(self.instance_delete_list) > 0:
            self.group.remove(self.instance_delete_list)
            self.instance_delete_list = set()

    def draw(self, in_event):
        """
        Respond to draw events.

        :param in_event: The ``draw_self`` event
        :type in_event: py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("draw():")
        if (len(self.group) > 0) and self.visible:
            for an_action in self.event_action_sequences["draw"].get_next_action():
                if an_action.name == "draw_self":
                    # The normal, default action: each object instance draws
                    #  its sprite
                    #pylint: disable=no-member
                    self.group.draw(self.game_engine.draw_surface)
                    #pylint: enable=no-member

    def make_new_instance(self, screen, settings=None, **kwargs):
        screen_dims = (screen.get_width(), screen.get_height())
        new_instance = object_instance.ObjectInstance(
            self, screen_dims, self._id, settings, **kwargs)
        #pylint: disable=no-member
        self.group.add(new_instance)
        #pylint: enable=no-member
        return new_instance

    def get_applied_instance_list(self, an_action, in_event):
        """
        For actions with "apply_to" parameters, return a list of the
        object instances affected.

        The "apply_to" parameter may be "self", which can refer to a particular
        instance (which needs to be part of the event data); or may be "other",
        in cases where another instance is involved in the event (collisions);
        or affect multiple objects if apply_to refers to an object type,
        in which case all objects of the named type receive the action.  For
        "create" type actions, "self" instead refers to the object type to be
        created.

        :param an_action: The action with an "apply_to" field
        :type an_action: :py:class:`~pygame_maker.actions.action.Action`
        :param in_event: The received event
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        :return: A list of instances affected by the event that the action
            will apply to
        :rtype: list
        """
        self.debug("get_applied_instance_list(an_action={}, in_event={}):".
                   format(an_action, in_event))
        apply_to_instances = []
        if (('instance' in in_event.event_params) and
                (in_event.event_params['instance'] in self.group)):
            apply_to_instances = [in_event['instance']]
        if 'apply_to' not in an_action.action_data:
            return apply_to_instances
        if an_action["apply_to"] == "other":
            if 'others' in in_event:
                # "others" are part of a collision event
                apply_to_instances = in_event['others']
        elif an_action["apply_to"] != "self":
            # applies to an object type; this means apply it to all instances
            #  of that object
            if an_action["apply_to"] in self.game_engine.resources['objects'].keys():
                apply_to_instances = list(
                    self.game_engine.resources['objects'][an_action["apply_to"]].group)
        elif isinstance(in_event, event.KeyEvent) or isinstance(in_event, event.StepEvent):
            # certain events don't carry instance handles; just select all of
            # them (user code can decide which instance is "active")
            #pylint: disable=no-member
            apply_to_instances = self.group.sprites()
            #pylint: enable=no-member
        return apply_to_instances

    def handle_instance_event(self, in_event):
        """
        Execute action sequences generated by an instance.

        Possible ObjectInstance events:

        * intersect_boundary
        * outside_room

        :param in_event: The event generated by an ObjectInstance of this type
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_instance_event(in_event={}):".format(in_event))
        self.execute_action_sequence(in_event)

    def handle_mouse_event(self, in_event):
        """
        Handle mouse events that intersect with any of this object type's
        instances, after filtering global mouse events through the base class's
        method.

        If mouse event's XY coordinate intersects one or more instances and the
        exact mouse event is handled by this object (button #, press/release),
        then handle the event.

        :param in_event: The event generated by an ObjectInstance of this type
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        """
        super(CollideableObjectType, self).handle_mouse_event(in_event)
        #pylint: disable=no-member
        clicked = self.group.get_sprites_at(in_event['position'])
        #pylint: enable=no-member
        if len(clicked) > 0:
            self.execute_action_sequence(in_event, clicked)

    def handle_step_event(self, in_event):
        """
        Execute the action sequence associated with the supplied step event, if
        the exact step event is handled by this object (begin, end, normal),
        on every instance.

        :param in_event: The step event
        :type in_event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_step_event(in_event={}):".format(in_event))
        self.execute_action_sequence(in_event, targets=[inst for inst in self.group])

    def __repr__(self):
        rpr = "<{} '{}' sprite='{}'>".format(type(self).__name__, self.name, self.sprite_resource)
        return rpr

ObjectType.register_object_type(ManagerObjectType)
ObjectType.register_object_type(CollideableObjectType)
