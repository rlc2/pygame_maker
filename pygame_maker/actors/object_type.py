#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# pygame maker object resource

import pygame
import math
import random
import re
import yaml
import logging
from pygame_maker.support import logging_object
import object_instance
import object_sprite
from pygame_maker.events import event
from pygame_maker.actions import action
from pygame_maker.actions import action_sequence
from pygame_maker.sounds import sound


class ObjectTypeException(logging_object.LoggingException):
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


def mask_from_surface(surface, threshold=127):
    """
    Create a precise mask of an ObjectSprite's pixels.

    Set a mask pixel if the corresponding surface's pixel has an alpha value
    greater than threshold (for a surface with an alpha channel), or if the
    pixel doesn't match the surface's color key.  Borrowed from pygame's
    mask.py demo code. For some reason, this works and
    :py:func:`pygame.mask.from_surface` doesn't for the sample image used in
    the unit test for object_type.

    :param surface: The drawing surface to create a mask from
    :type surface: :py:class:`pygame.Surface`
    :param threshold: The minimum alpha value for a pixel on the Surface to
        appear in the mask (ignored if the surface has a color key)
    :type threshold: int
    :return: The mask created from the surface
    :rtype: :py:class:`pygame.mask.Mask`
    """
    mask = pygame.mask.Mask(surface.get_size())
    key = surface.get_colorkey()
    if key:
        for y in range(surface.get_height()):
            for x in range(surface.get_width()):
                if surface.get_at((x, y)) != key:
                    mask.set_at((x, y), 1)
    else:
        for y in range(surface.get_height()):
            for x in range(surface.get_width()):
                if surface.get_at((x, y))[3] > threshold:
                    mask.set_at((x, y), 1)
    return mask


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
    nx = (instance_a.kind.mask.overlap_area(instance_b.kind.mask,
                                            (offset[0]+1, offset[1])) -
          instance_a.kind.mask.overlap_area(instance_b.kind.mask,
                                            (offset[0]-1, offset[1])))
    ny = (instance_a.kind.mask.overlap_area(instance_b.kind.mask,
                                            (offset[0], offset[1] + 1)) -
          instance_a.kind.mask.overlap_area(instance_b.kind.mask,
                                            (offset[0], offset[1] - 1)))
    if (nx == 0) and (ny == 0):
        # can't get a normal when one object is inside another..
        return None
    n = (nx, ny)
    return n


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
    overlap = instance_a.kind.mask.overlap_area(instance_b.kind.mask, offset)
    return overlap


def dot_product(v1, v2):
    """
    Calculate a dot product between 2 vectors.

    :param v1: The first vector
    :type v1: (float, float)
    :param v2: The second vector
    :type v2: (float, float)
    :return: The dot product
    :rtype: float
    """
    return v1[0] * v2[0] + v1[1] * v2[1]


class ObjectType(logging_object.LoggingObject):
    """
    PyGameMaker objects have:

    * sprite reference
    * depth (determines which objects draw on top of other objects) (numeric)
    * parent (another object)
    * collision mask (uses sprite reference, can be a different sprite)
    * visible flag (whether the object will be drawn)
    * persistent flag (unknown purpose, not implemented)
    * solid flag (for solid stationary objects, e.g. platform)
    * physics flag
    * events

      * ex: create. normal step. draw.
      * events can be modified, edited (appears to just add a run code
        action), or deleted.

    * actions

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
    #: Default object visibility
    DEFAULT_VISIBLE = True
    #: Default for 'solid' flag
    DEFAULT_SOLID = False
    #: Default depth
    DEFAULT_DEPTH = 0
    #: By default, a new ObjectType doesn't refer to a sprite yet
    DEFAULT_SPRITE_RESOURCE = None
    EVENT_NAME_OBJECT_HASH = {
        "outside_room": event.OtherEvent,
        "intersect_boundary": event.OtherEvent,
        "create": event.ObjectStateEvent,
        "image_loaded": event.OtherEvent,
        "destroy": event.ObjectStateEvent,
        "collision": event.CollisionEvent,
    }
    GLOBAL_MOUSE_RE = re.compile("global")

    @staticmethod
    def load_from_yaml(yaml_stream, game_engine):
        """
        Create an object type from a YAML-formatted file.
        Expected format::

            - obj_name1:
                visible: True | False
                solid: True | False
                depth: <int>
                sprite: <sprite resource name>
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

        :param yaml_stream: A file or stream containing the YAML string data
        :type yaml_stream: file-like
        :param game_engine: A reference to the main game engine
        :type game_engine: GameEngine
        :return: A new ObjectType with YAML-defined properties
        :type: :py:class:`ObjectType`
        """
        new_object_list = []
        yaml_repr = yaml.load(yaml_stream)
        if yaml_repr:
            for top_level in yaml_repr:
                kwargs = {
                    "visible": ObjectType.DEFAULT_VISIBLE,
                    "solid": ObjectType.DEFAULT_SOLID,
                    "depth": ObjectType.DEFAULT_DEPTH,
                    "sprite": ObjectType.DEFAULT_SPRITE_RESOURCE,
                    "event_action_sequences": {}
                }
                # hash of 1 key, the object name
                obj_name = top_level.keys()[0]
                # 'events' key contains event -> action sequence mappings
                obj_yaml = top_level[obj_name]
                if "visible" in obj_yaml.keys():
                    kwargs["visible"] = (obj_yaml["visible"] == True)
                if "solid" in obj_yaml.keys():
                    kwargs["solid"] = (obj_yaml["solid"] == True)
                if "depth" in obj_yaml.keys():
                    kwargs["depth"] = int(obj_yaml["depth"])
                if "sprite" in obj_yaml.keys():
                    kwargs["sprite"] = str(obj_yaml["sprite"])
                if "events" in obj_yaml.keys():
                    # print("Found '{}', passing {} to load..".format(kwarg, obj_yaml[kwarg]))
                    for ev_seq in obj_yaml["events"]:
                        game_engine.debug("{}: create event sequence from '{}'".format(obj_name,
                                                                                       obj_yaml['events'][ev_seq]))
                        kwargs["event_action_sequences"][ev_seq] = \
                            action_sequence.ActionSequence.load_sequence_from_yaml_obj(obj_yaml['events'][ev_seq])
                        game_engine.debug("Loaded sequence {}:".format(ev_seq))
                        if game_engine.logger.level <= logging.DEBUG:
                            kwargs["event_action_sequences"][ev_seq].pretty_print()
                new_object_list.append(ObjectType(obj_name, game_engine,
                                                  **kwargs))
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
        self.debug("New object {}, with args {}".format(object_name, kwargs))
        if object_name:
            self.name = object_name
        else:
            self.name = self.DEFAULT_OBJECT_PREFIX
        self.game_engine = game_engine
        self.sprite_resource = self.DEFAULT_SPRITE_RESOURCE
        self.image = None
        self.bounding_box_rect = None
        self.mask = None
        self.radius = None
        self._visible = self.DEFAULT_VISIBLE
        self.solid = self.DEFAULT_SOLID
        self.depth = self.DEFAULT_DEPTH
        self.group = pygame.sprite.LayeredDirty()
        self.event_action_sequences = {}
        self._id = 0
        self.instance_delete_list = []
        self.handler_table = {
            re.compile("^alarm(\d{1,2})$"):     self.handle_alarm_event,
            re.compile("^kb_(.*)$"):            self.handle_keyboard_event,
            re.compile("^mouse_(.*)$"):         self.handle_mouse_event,
            re.compile("^collision_(.*)$"):     self.handle_collision_event,
            re.compile("^([^_]+)_step$"):       self.handle_step_event,
            re.compile("^outside_room$"):       self.handle_instance_event,
            re.compile("^intersect_boundary$"): self.handle_instance_event,
            re.compile("^create$"):             self.handle_create_event,
            re.compile("^destroy$"):             self.handle_destroy_event,
        }
        if kwargs:
            for kw in kwargs:
                if kw == "visible":
                    self.visible = kwargs["visible"]
                if kw == "solid":
                    self.solid = (kwargs["solid"] == True)
                if kw == "depth":
                    self.depth = int(kwargs["depth"])
                if (kw == "sprite") and kwargs[kw]:
                    if kwargs['sprite'] in self.game_engine.resources['sprites'].keys():
                        assigned_sprite = self.game_engine.resources['sprites'][kwargs['sprite']]
                        if not isinstance(assigned_sprite, object_sprite.ObjectSprite):
                            raise(ObjectTypeException("'{}' is not a recognized sprite resource".format(kwargs["sprite"]),
                                                      self.error))
                        self.sprite_resource = assigned_sprite
                if (kw == "event_action_sequences") and kwargs[kw]:
                    ev_dict = kwargs[kw]
                    for ev_name in ev_dict:
                        if not isinstance(ev_dict[ev_name], action_sequence.ActionSequence):
                            raise(ObjectTypeException("Event '{}' does not contain an ActionSequence", self.error))
                        self[ev_name] = ev_dict[ev_name]

        # print("Finished setup of {}".format(self.name))

    @property
    def visible(self):
        """Flag whether the ObjectType is to be drawn"""
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
        yaml_str += "    events:\n"
        for event_name in self.event_action_sequences:
            yaml_str += "      {}:\n".format(event_name)
            yaml_str += self.event_action_sequences[event_name].to_yaml(8)
        return yaml_str

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
        # a simple list manages deletions
        self.debug("add_instance_to_delete_list(instance={}):".format(instance))
        self.instance_delete_list.append(instance)

    def create_instance(self, screen, settings=None, **kwargs):
        """
        Create a new instance of this object type.

        Every instance is assigned a unique ID, and placed inside a sprite
        group that handles drawing and positional updates for all contained
        instances.

        :param screen: The surface the instance will be drawn upon.  The
            instance will use this surface's width and height parameters to
            detect boundary collision events, which are queued in the event
            engine
        :type screen: :py:class:`pygame.Surface`
        :param settings: A hash of settings to be applied.  See kwargs entry
            in :py:meth:`~pygame_maker.actors.object_instance.ObjectInstance.__init__`
        :type settings: dict
        :param kwargs: Keyword arguments, in addition to or as an alternative
            to the settings dict
        """
        self.debug("create_instance(screen={}, settings={}, kwargs={}):".format(screen, settings, kwargs))
        # print("Create new instance of {}".format(self))
        # print("Create obj with args: '{}' and '{}'".format(settings,kwargs))
        self.info("  Create instance of {} with args {}, {}".format(self.name, settings, kwargs))
        screen_dims = (screen.get_width(), screen.get_height())
        new_instance = object_instance.ObjectInstance(self, screen_dims, self._id, settings, **kwargs)
        self.group.add(new_instance)
        self._id += 1
        # queue the creation event for the new instance
        self.game_engine.event_engine.queue_event(self.EVENT_NAME_OBJECT_HASH["create"]("create",
                                                                                        {"type": self,
                                                                                         "instance": new_instance}))
        self.game_engine.event_engine.transmit_event('create')
        return new_instance

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
        collision_types_queued = []
        for other_obj in other_obj_types:
            other_obj.group = other_obj.group
            if len(other_obj.group) == 0:
                continue
            if (len(self.group) == 1) and self.name == other_obj.name:
                # skip self collision detection if there's only one sprite
                continue
            collision_map = pygame.sprite.groupcollide(self.group,
                                                       other_obj.group, 0, 0,
                                                       collided=sprite_collision_test)
            for collider in collision_map.keys():
                collision_normal = None
                for other_inst in collision_map[collider]:
                    overlap = get_mask_overlap(collider, other_inst)
                    # print("Solid collision overlap: {}".format(overlap))
                    collision_normal = get_collision_normal(collider, other_inst)
                    # print("Collision normal: {}".format(collision_normal))
                    # in the event of a collision with a solid object (i.e.
                    #  stationary), kick the sprite outside of the other
                    #  object's collision mask
                    if other_inst.kind.solid and collision_normal:
                        divisor = float(dot_product(collision_normal, collision_normal))
                        distance = 0
                        if divisor != 0:
                            distance = (float(overlap) / divisor + 0.5)
                        # print("Distance: {}, divisor {}".format(distance, divisor))
                        adj_x = math.floor(distance * collision_normal[0] + 0.5)
                        adj_y = math.floor(distance * collision_normal[1] + 0.5)
                        # print("Moving obj {}, {}".format(adj_x, adj_y))
                        collider.position.x += adj_x
                        collider.position.y += adj_y
                collision_name = "collision_{}".format(other_obj.name)
                if collision_name not in collision_types_queued:
                    collision_types_queued.append(collision_name)
                self.info("{} inst {}: Queue collision {}".format(self.name,
                                                                  collider.inst_id,
                                                                  collision_name))
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
        return collision_types_queued

    def update(self):
        """
        Call to perform position updates for all instances.  After all
        instances have updated, handle any queued deletions.
        """
        self.debug("update():")
        if len(self.group) > 0:
            self.group.update()
        # after all instances update(), check the delete list to see which
        #  ones should be removed and remove them
        if len(self.instance_delete_list) > 0:
            self.group.remove(self.instance_delete_list)
            self.instance_delete_list = []

    def draw(self, surface):
        """
        Call to draw all instances. The sprite group handles this for us.

        :param surface: The surface the object instances will be drawn upon
        :type surface: :py:class:`pygame.Surface`
        """
        self.debug("draw(surface={}):".format(surface))
        if (len(self.group) > 0) and self.visible:
            self.group.draw(surface)

    def create_rectangle_mask(self, orig_rect):
        """
        Create a rectangular mask that covers the opaque pixels of an object.

        Normally, collisions between objects with collision_type "rectangle"
        will use the rectangle collision test, which only needs the rect
        attribute.  The mask is created in the event this object collides with
        an object that has a different collision_type, in which case the
        objects fall back to using a mask collision test.  The assumption is
        that the user wants a simple collision model, so the mask is made from
        the rect attribute, instead of creating an exact mask from the opaque
        pixels in the image.

        :param orig_rect: The Rect from the image
        :type orig_rect: :py:class:`pygame.Rect`
        :return: A new mask
        :rtype: :py:class:`pygame.mask.Mask`
        """
        self.debug("create_rectangle_mask(orig_rect={}):".format(orig_rect))
        self.mask = pygame.mask.Mask((orig_rect.width, orig_rect.height))
        self.mask.fill()

    def get_disk_radius(self, precise_mask, orig_rect):
        """
        Calculate the radius of a circle that covers the opaque pixels in
        precise_mask.

        :param precise_mask: The precise mask for every opaque pixel in the
            image.  If the original image was circular, this can aid in
            creating in a more accurate circular mask
        :type precise_mask: :py:class:`pygame.mask.Mask`
        :param orig_rect: The Rect from the image
        :type orig_rect: :py:class:`pygame.Rect`
        """
        self.debug("get_disk_radius(precise_mask={}, orig_rect={}):".format(precise_mask, orig_rect))
        # find the radius of a circle that contains bound_rect for the worst
        #  case
        disk_mask_center = (orig_rect.width/2, orig_rect.height/2)
        bound_rect = self.bounding_box_rect
        bound_right = bound_rect.x + bound_rect.width
        bound_bottom = bound_rect.y + bound_rect.height
        left_center_distance = abs(disk_mask_center[0]-bound_rect.x)
        right_center_distance = abs(disk_mask_center[0]-bound_right)
        top_center_distance = abs(disk_mask_center[1]-bound_rect.y)
        bottom_center_distance = abs(disk_mask_center[1]-bound_bottom)
        largest_x_distance = max(left_center_distance, right_center_distance)
        largest_y_distance = max(top_center_distance, bottom_center_distance)
        max_bound_radius = math.sqrt(largest_x_distance * largest_x_distance +
                                     largest_y_distance * largest_y_distance)
        # determine whether a smaller radius could be used (i.e.
        #  no corner pixels within the bounding rect are set)
        max_r = 0
        for y in range(bound_rect.y, bound_rect.height):
            for x in range(bound_rect.x, bound_rect.width):
                circ_x = disk_mask_center[0]-x
                circ_y = disk_mask_center[1]-y
                if precise_mask.get_at((x, y)) > 0:
                    r = math.sqrt(circ_x * circ_x + circ_y * circ_y)
                    if r > max_r:
                        max_r = r
        bound_radius = max_bound_radius
        if (max_r > 0) and (max_r < max_bound_radius):
            bound_radius = max_r
        radius = int(math.ceil(bound_radius))
        self.radius = radius
        return radius

    def create_disk_mask(self, orig_rect):
        """
        Create a circular mask that covers the opaque pixels of an object.

        Normally, collisions between objects with collision_type "disk" will
        use the circle collision test, which only needs the radius attribute.
        The mask is created in the event this object collides with an object
        that has a different collision_type, in which case the objects fall
        back to using a mask collision test.  The assumption is that the user
        wants a simple collision model, so the mask is made from a circle of
        the right radius, instead of creating an exact mask from the opaque
        pixels in the image.

        :param orig_rect: The Rect from the image
        :type orig_rect: :py:class:`pygame.Rect`
        :return: A new mask
        :rtype: :py:class:`pygame.mask.Mask`
        """
        # create a disk mask with a radius sufficient to cover the
        #  opaque pixels
        # NOTE: collisions with objects that have a different collision type
        #  will use this mask; the mask generated here won't fill the sprite's
        #  radius, but will be a circle with the correct radius that is clipped
        #  at the sprite's rect dimensions
        self.debug("create_disk_mask(orig_rect={}):".format(orig_rect))
        disk_mask_center = (orig_rect.width / 2, orig_rect.height / 2)
        disk_mask_surface = pygame.Surface((orig_rect.width, orig_rect.height),
                                           depth=8)
        disk_mask_surface.set_colorkey(pygame.Color("#000000"))
        disk_mask_surface.fill(pygame.Color("#000000"))
        pygame.draw.circle(disk_mask_surface, pygame.Color("#ffffff"), disk_mask_center, self.radius)
        self.mask = mask_from_surface(disk_mask_surface)

    def get_image(self):
        """
        Called by instances of this ObjectType, to get a new copy of
        the sprite resource's image.

        Load the image when the first instance using this image is created.
        Also, handle the collision type and create a collision mask.

        :return: A new pygame image, copied from the ObjectSprite resource
        :rtype: :py:class:`pygame.Surface`
        """
        self.debug("get_image():")
        if self.sprite_resource:
            if not self.sprite_resource.image:
                self.sprite_resource.load_graphic()
            if not self.mask:
                self.info("  {}: create collision mask".format(self.name))
                with logging_object.Indented(self):
                    original_image = self.sprite_resource.image
                    precise_mask = mask_from_surface(original_image)
                    bound_rect = self.sprite_resource.bounding_box_rect
                    self.image = original_image.copy()
                    orig_rect = original_image.get_rect()
                    if (orig_rect.width == 0) or (orig_rect.height == 0):
                        raise(ObjectTypeException("Found broken sprite resource when creating instance", self.error))
                    if (bound_rect.width == 0) or (bound_rect.height == 0):
                        # use the dimensions of the loaded graphic for the bounding
                        #  rect in case there's a problem with the sprite resources'
                        #  bounding rect
                        bound_rect = orig_rect
                    self.bounding_box_rect = bound_rect
                    self.info("  bounded dimensions: {}".format(bound_rect))
                    # create a mask based on the collision type
                    self.info("  Sprite collision type: {}".format(self.sprite_resource.collision_type))
                    self.info("  Sprite dimensions: {}".format(orig_rect))
                    # set a mask regardless of the collision type, to enable
                    #  collision checks between objects that have different
                    #  types
                    if self.sprite_resource.collision_type == "precise":
                        self.mask = precise_mask
                    elif self.sprite_resource.collision_type == "rectangle":
                        self.create_rectangle_mask(orig_rect)
                    elif self.sprite_resource.collision_type == "disk":
                        self.get_disk_radius(precise_mask, orig_rect)
                        self.create_disk_mask(orig_rect)
                    else:
                        # other collision types are not supported, fall back to
                        #  rectangle
                        self.create_rectangle_mask(orig_rect)
                    # queue the image_loaded event
                    self.game_engine.event_engine.queue_event(
                        self.EVENT_NAME_OBJECT_HASH["image_loaded"]("image_loaded",
                                                                    {"type": self,
                                                                     "sprite": self.sprite_resource})
                    )
                    self.info("  Queued 'image_loaded' event")
            return self.image
        else:
            return None

    def get_applied_instance_list(self, action, event):
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

        :param action: The action with an "apply_to" field
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        :param event: The received event
        :type event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("get_applied_instance_list(action={}, event={}):".format(action, event))
        apply_to_instances = []
        if (('instance' in event.event_params) and 
                (event.event_params['instance'] in self.group)):
            apply_to_instances = [event['instance']]
        if 'apply_to' not in action.action_data:
            return apply_to_instances
        if action["apply_to"] == "other":
            if 'others' in event:
                # "others" are part of a collision event
                apply_to_instances = event['others']
        elif action["apply_to"] != "self":
            # applies to an object type; this means apply it to all instances
            #  of that object
            if action["apply_to"] in self.game_engine.resources['objects'].keys():
                apply_to_instances = list(self.game_engine.resources['objects'][action["apply_to"]].group)
        return apply_to_instances

    def execute_action_sequence(self, event, targets=None):
        """
        Walk through an event action sequence when the event handler matches a
        known event.

        The sausage factory method.  There are many types of actions; the
        object instance actions make the most sense to handle here, but the
        game engine that inspired this one uses a model in which a hidden
        manager object type triggers actions that affect other parts of the
        game engine, so those actions need to be routed properly as well.

        :param event: The event to be handled
        :type event: :py:class:`~pygame_maker.events.event.Event`
        :param targets: The event handler may pass in a list of target
            instances for the action sequence to operate on
        :type event: array-like | None
        """
        self.debug("execute_action_sequence(event={}, targets={}):".format(event, targets))
        if event.name in self.event_action_sequences:
            self.info("  {}: Execute action sequence for event '{}'".format(self.name, event))
            with logging_object.Indented(self):
                self.info("  Event args: {}".format(event.event_params))
                for action in self.event_action_sequences[event.name].get_next_action():
                    self.info("  Execute action {}".format(action))
                    # forward instance actions to instance(s)
                    if (targets is not None) and len(targets) > 0:
                        self.info("  Apply to target(s) {}".format(str(targets)))
                        for target in targets:
                            if action.name not in self.game_engine.GAME_ENGINE_ACTIONS:
                                target.execute_action(action, event)
                            else:
                                self.game_engine.execute_action(action, event)
                    elif "apply_to" in action.action_data:
                        affected_instance_list = self.get_applied_instance_list(action, event)
                        self.info("  Apply to: {}".format(action, affected_instance_list))
                        for target in affected_instance_list:
                            # print("applying to {}".format(target))
                            target.execute_action(action, event)
                    else:
                        self.info("  call game engine execute_action for {}".format(action))
                        self.game_engine.execute_action(action, event)

    def handle_instance_event(self, event):
        """
        Execute action sequences generated by an instance.

        Possible ObjectInstance events:

        * intersect_boundary
        * outside_room

        :param event: The event generated by an ObjectInstance of this type
        :type event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_instance_event(event={}):".format(event))
        self.execute_action_sequence(event)

    def handle_mouse_event(self, event):
        """
        Execute the action sequence associated with the supplied mouse
        event.

        If mouse event's XY coordinate intersects one or more instances and the
        exact mouse event is handled by this object (button #, press/release),
        then handle the event.  mouse_global_* events are handled by instances
        watching for them, regardless of the XY coordinate.

        :param event: The mouse event
        :type event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_mouse_event(event={}):".format(event))
        gl_minfo = self.GLOBAL_MOUSE_RE.search(event.name)
        if gl_minfo:
            self.execute_action_sequence(event)
        else:
            clicked = self.group.get_sprites_at(event['position'])
            if len(clicked) > 0:
                self.execute_action_sequence(event, clicked)

    def handle_keyboard_event(self, event):
        """
        Execute the action sequence associated with the supplied key event,
        if the exact key event is handled by this object (which key,
        press/release).

        :param event: The keyboard event
        :type event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_keyboard_event(event={}):".format(event))
        matched_seq = None
        for ev_seq in self.event_action_sequences.keys():
            self.debug("  match key event {} vs {}".format(event.name, ev_seq))
            if ev_seq.find(event.name) == 0:
                # found this event in the list, find out if it's the right type
                if (ev_seq == event.name) or ev_seq.endswith('_keydn'):
                    if event.key_event_type == "down":
                        matched_seq = event.name
                        break
                elif (ev_seq.endswith('_keyup') and 
                        (event.key_event_type == "up")):
                    matched_seq = event.name
                    break
        if matched_seq:
            self.execute_action_sequence(event)

    def handle_collision_event(self, event):
        """
        Execute the action sequence associated with a collision event.

        The name of the object type collided with is part of the event's name,
        which should have been added as a key in the event_action_sequences
        attribute using the :py:meth:`__setitem__` interface.

        :param event: The collision event
        :type event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_collision_event(event={}):".format(event))
        self.execute_action_sequence(event)

    def handle_step_event(self, event):
        """
        Execute the action sequence associated with the supplied step event, if
        the exact step event is handled by this object (begin, end, normal),
        on every instance.

        :param event: The step event
        :type event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_step_event(event={}):".format(event))
        self.execute_action_sequence(event, targets=[inst for inst in self.group])

    def handle_alarm_event(self, event):
        """
        Execute the action sequence associated with the alarm event, if the
        exact alarm is handled by this object (one or more of alarms 0-11).

        :param event: The alarm event
        :type event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_alarm_event(event={}):".format(event))

    def handle_create_event(self, event):
        """
        Execute the action sequence associated with the create event, passing
        it on to the instance recorded in the event.

        :param event: The object creation event
        :type event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_create_event(event={}):".format(event))
        self.execute_action_sequence(event)

    def handle_destroy_event(self, event):
        """
        Execute the action sequence associated with the destroy event.

        :param event: The destroy event
        :type event: :py:class:`~pygame_maker.events.event.Event`
        """
        self.debug("handle_destroy_event(event={}):".format(event))
        self.execute_action_sequence(event)

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
            raise(KeyError("Event action sequence keys must be strings", self.error))
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
            raise(ObjectTypeException("ObjectType does not yet handle '{}' events (NYI)".format(itemname),
                                      self.error))

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
            del(self.event_action_sequences[itemname])

    def __repr__(self):
        rpr = "<{} '{}' sprite='{}'>".format(type(self).__name__, self.name, self.sprite_resource)
        return rpr
