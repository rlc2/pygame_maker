"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Pygame maker object instance module.
"""

import math
import random
import pygame
import numpy as np
from pygame_maker.actors.simple_object_instance import SimpleObjectInstance
import pygame_maker.events.event as event


def get_vector_xy_from_velocity(speed, direction):
    """
    Return an x,y vector representing the given speed and angle of motion.

    :param speed: The speed component of the velocity.
    :type speed: float
    :param direction: The direction component of the velocity.
    :type direction: float
    :return: A tuple (x, y) representing the velocity
    :rtype: (float, float)
    """
    xval = speed * math.sin(direction / 180.0 * math.pi)
    yval = speed * -1 * math.cos(direction / 180.0 * math.pi)
    xy_tuple = (xval, yval)
    return np.array(xy_tuple)


def get_velocity_from_xy(xcom, ycom):
    """
    Return speed and direction of motion, given an x, y vector starting from
    0, 0.

    :param xcom: X component of the velocity.
    :type xcom: float
    :param ycom: Y component of the velocity.
    :type ycom: float
    :return: A tuple (speed, direction) representing the velocity
    :rtype: (float, float)
    """
    speed = math.sqrt(xcom**2 + ycom**2)
    direction = direction_from_a_to_b(np.zeros(2), (xcom, ycom))
    return (speed, direction)


def get_radius_angle_from_xy(xpos, ypos):
    """
    Return polar coordinates from an x, y coordinate.  This is the same
    operation as converting a velocity represented as x, y into speed,
    direction.

    :param xpos: X coordinate
    :param ypos: Y coordinate
    :return: A tuple (radius, angle) representing the polar coordinate
    :rtype: (float, float)
    """
    return get_velocity_from_xy(xpos, ypos)


def direction_from_a_to_b(pointa, pointb):
    """
    Calculate the direction in degrees for the line connecting points a and b.

    :param pointa: A 2-element list representing the coordinate in x, y order
    :type pointa: [float, float]
    :param pointb: A 2-element list representing the coordinate in x, y order
    :type pointb: [float, float]
    :return: The angle to pointb, using pointa as the origin.
    :rtype: float
    """
    normal_vector = np.array(pointb[:2]) - np.array(pointa[:2])
    return (math.atan2(normal_vector[1], normal_vector[0]) * 180) / math.pi


class ObjectInstance(SimpleObjectInstance, pygame.sprite.DirtySprite):
    """
    Fits the purpose of pygame's Sprite class.

    Represent an instance of an ObjectType.

    An instance has:

    * position
    * speed
    * direction of motion
    * gravity
    * gravity direction
    * friction

    An instance can:

    * update its position each frame
    * apply friction and gravity accelerations each frame
    * respond to events
    * produce collision events (boundaries and other instances)
    * produce outside_room events
    * draw itself

    As a :py:class:`~pygame.sprite.DirtySprite` subclass, instances support
    ``dirty``, ``blendmode``, ``source_rect``, ``visible``, and ``layer``
    attributes.

    As a
    :py:class:`~pygame_maker.actors.simple_object_instance.SimpleObjectInstance`
    subclass, instances automatically know how to:
    execute action sequences; handle execute_code, if_variable and set_variable
    actions; respond to symbol changes that occur inside code blocks; keep
    track of position; and apply kwargs to the symbol table.
    In addition, SimpleObjectInstance adds the ``name``, ``inst_id``, ``kind``,
    ``game_engine``, ``screen_dims``, ``symbols``, and ``rect`` attributes.

    As a subclass of
    :py:class:`~pygame_maker.support.logging_object.LoggingObject`, instances
    support ``debug()``, ``info()``, ``warning()``, ``error()``, and
    ``critical()`` methods.
    """
    INSTANCE_SYMBOLS = {
        "visible": 0,
        "speed": 0.0,
        "direction": 0.0,
        "gravity": 0.0,
        "gravity_direction": 0.0,
        "friction": 0.0,
        "hspeed": 0.0,
        "vspeed": 0.0,
        "subimage_number": 0,
    }

    def __init__(self, kind, screen_dims, new_id, settings=None, **kwargs):
        """
        Initialize an ObjectInstance.

        :param kind: The object type of this new instance
        :type kind: :py:class:`~pygame_maker.actors.object_type.ObjectType`
        :param screen_dims: Width, height of the surface this instance will be
            drawn to.  Allows boundary collisions to be detected.
        :type screen_dims: [int, int]
        :param new_id: A unique integer ID for this instance
        :type new_id: int
        :param settings: Used along with kwargs for settings attributes
            (allows attributes to be set that have a '.' character, which
            cannot be set in kwargs).  Known attributes are the same as for
            kwargs.
        :type settings: None or dict
        :param kwargs:
            Supply alternatives to instance attributes

            * position (list of float or pygame.Rect): Upper left XY coordinate.
              If not integers, each will be rounded to the next highest
              integer [(0,0)]
            * speed (float): How many pixels (or fraction thereof) the object
              moves in each update [0.0]
            * direction (float): 0-359 degrees for direction of motion [0.0]
            * gravity (float): Strength of gravity toward gravity_direction in
              pixels/frame^2 [0.0]
            * gravity_direction (float): 0-359 degrees for direction of gravity
              vector [0.0]
            * friction (float): Strength of friction vs direction of motion in
              pixels/frame [0.0]
            * parent (ObjectInstance): An object instance that "owns" this one.
              Makes this object instance's coordinates relative to its parent.
              Connects the two instances, so events can be communicated.

        """
        # Flag when methods shouldn't automatically update speed, direction
        self._delay_motion_updates = False
        # call the superclasses' __init__
        SimpleObjectInstance.__init__(self, kind, screen_dims, new_id, settings, **kwargs)
        pygame.sprite.DirtySprite.__init__(self)
        # set up the Sprite/DirtySprite expected parameters
        # default visibility comes from this instance's type
        self.dirty = 0
        self._visible = False
        self.visible = kind.visible
        self.source_rect = pygame.Rect(0, 0, 0, 0)
        # Get a copy of the selected subimage and its collision mask (and a
        # radius, if the disk collision mask was selected)
        self.set_subimage()
        self.blendmode = kind.blend_mode
        # use the instance type's 'depth' parameter as the layer for this
        #  instance
        self.layer = kind.depth

        self.start_position = tuple(self.position)
        self.action_name_to_method_map.update({
            'set_velocity_compass': self.set_velocity_compass,
            'move_toward_point': self.move_toward_point,
            'set_horizontal_speed': self.set_horizontal_speed,
            'set_vertical_speed': self.set_vertical_speed,
        })
        # print("{}".format(self))

    @property
    def visible(self):
        """Get and set the instance's visibility."""
        vis = self.symbols["visible"]
        # self.warn("{}{} visible is {}".format(self.kind.name, self.inst_id, vis))
        return vis

    @visible.setter
    def visible(self, is_visible):
        vis = (is_visible is True)
        # self.warn("{}{} visible is now {}".format(self.kind.name, self.inst_id, vis))
        if vis:
            self.dirty = 2
        else:
            self.dirty = 0
        self._visible = vis
        self.symbols["visible"] = vis

    def _change_motion_x_y(self):
        # Keep track of horizontal and vertical components of velocity.

        # Motion is represented as x and y adjustments that are made every
        # update when using the speed/direction model (as opposed to
        # manually changing the position).  Caching these values reduces the
        # number of times math functions will be called for object instances
        # with constant velocity.
        self.debug("_change_motion_x_y():")
        xadj, yadj = get_vector_xy_from_velocity(self.symbols['speed'],
                                                 self.symbols['direction'])
        # print("new inst {} xyadj {}, {}".format(self.inst_id, xadj, yadj))
        self.symbols['hspeed'] = xadj
        self.symbols['vspeed'] = yadj

    @property
    def direction(self):
        """
        Get and set direction of motion in degrees, between 0.0 and 360.0.
        """
        return self.symbols['direction']

    @direction.setter
    def direction(self, value):
        new_value = value
        if new_value >= 360.0:
            new_value %= 360.0
        if new_value <= -360.0:
            new_value %= 360.0
        if (new_value > -360.0) and (new_value < 0.0):
            new_value = (360.0 + new_value)
        self.symbols['direction'] = new_value
        if not self._delay_motion_updates:
            self._change_motion_x_y()

    @property
    def speed(self):
        """Get and set speed of motion in pixels (or fractions) per frame."""
        return self.symbols['speed']

    @speed.setter
    def speed(self, value):
        self.symbols['speed'] = value
        if not self._delay_motion_updates:
            self._change_motion_x_y()

    @property
    def friction(self):
        """
        Get and set magnitude of friction applied against motion each frame.
        """
        return self.symbols['friction']

    @friction.setter
    def friction(self, value):
        self.symbols['friction'] = float(value)

    @property
    def gravity(self):
        """Get and set magnitude of gravity applied each frame."""
        return self.symbols['gravity']

    @gravity.setter
    def gravity(self, value):
        self.symbols['gravity'] = float(value)

    @property
    def gravity_direction(self):
        """Get and set direction gravity pulls the instance in degrees."""
        return self.symbols['gravity_direction']

    @gravity_direction.setter
    def gravity_direction(self, value):
        new_value = value
        if new_value >= 360.0:
            new_value %= 360.0
        if new_value <= -360.0:
            new_value %= 360.0
        if (new_value > -360.0) and (new_value < 0.0):
            new_value = (360.0 + new_value)
        self.symbols['gravity_direction'] = new_value

    @property
    def hspeed(self):
        """Get and set horizontal speed."""
        return self.symbols['hspeed']

    @hspeed.setter
    def hspeed(self, value):
        # skip setting motion x,y and hspeed, vspeed
        self._delay_motion_updates = True
        self.speed, self.direction = get_velocity_from_xy(value,
                                                          self.vspeed)
        self._delay_motion_updates = False
        self.symbols['hspeed'] = value

    @property
    def vspeed(self):
        """Get and set vertical speed."""
        return self.symbols['vspeed']

    @vspeed.setter
    def vspeed(self, value):
        # skip setting motion x,y and hspeed, vspeed
        self._delay_motion_updates = True
        self.speed, self.direction = get_velocity_from_xy(self.hspeed,
                                                          value)
        self._delay_motion_updates = False
        self.symbols['vspeed'] = value

    @property
    def subimage_number(self):
        """Get and set current subimage number."""
        return self.symbols['subimage_number']

    @subimage_number.setter
    def subimage_number(self, value):
        self.symbols['subimage_number'] = int(value)
        self.set_subimage()

    def get_center_point(self):
        """
        Return the approximate center pixel coordinate of the object.

        :return: A 2-element tuple x, y of the approximate position of the
            object's center point.
        :rtype: (int, int)
        """
        self.debug("get_center_point():")
        center_xy = (self.rect.x + self.rect.width / 2.0,
                     self.rect.y + self.rect.height / 2.0)
        return center_xy

    def update(self):
        """
        Move the instance from its current position.

        Calculate the new position using current speed and direction.  Queue
        events for boundary collisions or outside-of-room positions.  Make
        friction and/or gravity changes to speed and/or direction for the next
        update().
        """
        self.debug("update():")
        event_queued = None
        if self in self.kind.instance_delete_list:
            # save time detecting events for instances that have already been
            # destroyed this frame
            return
        # child instances do not use any of the 'speed' parameters, since
        # they are placed relative to their parent instance
        if self.symbols["parent"] is None and self.speed > 0.0:
            self.position[0] += self.symbols['hspeed']
            self.position[1] += self.symbols['vspeed']
            self.rect.x = int(math.floor(self.position[0] + 0.5))
            self.rect.y = int(math.floor(self.position[1] + 0.5))
            event_queued = self._detect_boundary_events()
            self.debug("  {} inst {} new position: {} ({})".
                       format(self.kind.name, self.inst_id, self.position, self.rect))
        # ultimate parent will update all descendants
        if self.symbols["parent"] is None:
            event_names_queued = self._update_child_instances(event_queued)
            # transmit all events at the end
            sorted_event_name_list = list(event_names_queued)
            sorted_event_name_list.sort()
            for event_name in sorted_event_name_list:
                self.debug("  {} inst {} transmitting {} event".format(self.kind.name,
                                                                       self.inst_id, event_name))
                self.game_engine.event_engine.transmit_event(event_name)
        # apply forces for next update
        self._apply_gravity()
        self._apply_friction()
        # transmit outside_room or intersect_boundary event last
        if event_queued is not None:
            self.game_engine.event_engine.queue_event(event_queued)
            self.debug("  {} inst {} transmitting {} event".format(self.kind.name,
                                                                   self.inst_id, event_queued))
            self.game_engine.event_engine.transmit_event(event_queued.name)

    def _detect_boundary_events(self):
        # check for boundary collisions
        # allow boundary collisions for objects completely outside
        #  the other dimension's boundaries to be ignored; this
        #  makes intersect_boundary and outside_room mutually exclusive
        event_queued = None
        in_x_bounds = (((self.rect.x + self.rect.width) >= 0) and
                       (self.rect.x <= self.screen_dims[0]))
        in_y_bounds = (((self.rect.y + self.rect.height) >= 0) and
                       (self.rect.y <= self.screen_dims[1]))
        if ((self.rect.x <= 0 <= (self.rect.x + self.rect.width)) or
                (self.rect.x <= self.screen_dims[0] <=
                 (self.rect.x + self.rect.width)) and in_y_bounds):
            # queue and handle boundary collision event
            event_queued = event.OtherEvent("intersect_boundary", {"type": self.kind,
                                                                   "instance": self})
            # print("inst {} hit x bound".format(self.inst_id))
        if ((self.rect.y <= 0 <= (self.rect.y + self.rect.height)) or
                (self.rect.y <= self.screen_dims[1] <=
                 (self.rect.y + self.rect.width)) and in_x_bounds):
            # queue and handle boundary collision event
            if event_queued is None:
                event_queued = event.OtherEvent("intersect_boundary", {"type": self.kind,
                                                                       "instance": self})
        # check for outside room
        if ((self.rect.x > self.screen_dims[0]) or
                ((self.rect.x + self.rect.width) < 0)):
            if event_queued is None:
                event_queued = event.OtherEvent("outside_room", {"type": self.kind,
                                                                 "instance": self})
        if ((self.rect.y > self.screen_dims[1]) or
                ((self.rect.y + self.rect.height) < 0)):
            if event_queued is None:
                event_queued = event.OtherEvent("outside_room", {"type": self.kind,
                                                                 "instance": self})
        if event_queued is not None:
            self.game_engine.event_engine.queue_event(event_queued)
        return event_queued

    def _update_child_instances(self, parent_event_queued):
        # update any child instances' positions based on this one's position
        event_names_queued = set()
        new_event = None
        #pylint: disable=not-an-iterable
        for child_inst in self.symbols["children"]:
            #pylint: enable=not-an-iterable
            # pass on parent events (if any)
            if parent_event_queued is not None:
                new_event = None
                if parent_event_queued.name == "outside_room":
                    ev_name = "parent_outside_room"
                    event_names_queued.add(ev_name)
                    new_event = event.OtherEvent(ev_name, {"type": child_inst.kind,
                                                           "instance": child_inst,
                                                           "parent_type": self.kind})
                elif parent_event_queued.name == "intersect_boundary":
                    ev_name = "parent_intersect_boundary"
                    event_names_queued.add(ev_name)
                    new_event = event.OtherEvent(ev_name, {"type": child_inst.kind,
                                                           "instance": child_inst,
                                                           "parent_type": self.kind})
                self.game_engine.event_engine.queue_event(new_event)
            # set child x and y relative to parent x and y
            child_inst.rect.x = self.rect.x + child_inst.position[0]
            child_inst.rect.y = self.rect.y + child_inst.position[1]
            # perform boundary checks on child instance
            child_event_queued = None
            if hasattr(child_inst, "_detect_boundary_events"):
                child_event_queued = child_inst._detect_boundary_events()
            if child_event_queued is not None:
                event_names_queued.add(child_event_queued.name)
                self.debug("bounds {} event in child {}".
                           format(child_event_queued.name, child_inst))
                if child_event_queued.name == "outside_room":
                    ev_name = "child_outside_room"
                    event_names_queued.add(ev_name)
                    new_event = event.OtherEvent(ev_name, {"type": self.kind,
                                                           "instance": self,
                                                           "child_type": child_inst.kind})
                elif child_event_queued.name == "intersect_boundary":
                    ev_name = "child_intersect_boundary"
                    event_names_queued.add(ev_name)
                    new_event = event.OtherEvent(ev_name, {"type": self.kind,
                                                           "instance": self,
                                                           "child_type": child_inst.kind})
                self.game_engine.event_engine.queue_event(new_event)
            event_names_queued |= child_inst._update_child_instances(child_event_queued)
        return event_names_queued

    def _apply_gravity(self):
        # Adjust speed and direction using value and direction of gravity.
        self.debug("_apply_gravity():")

    def _apply_friction(self):
        # Adjust speed based on friction value.
        self.debug("_apply_friction():")
        if (self.friction > 0.0) and (self.speed > 0.0):
            new_speed = self.speed - self.friction
            if new_speed < 0.0:
                new_speed = 0.0
            self.speed = new_speed

    def set_subimage(self):
        """
        Set the current subimage, source_rect, and collision mask (and possibly
        a radius)
        """
        subimage_info = self.kind.get_image(self.symbols["subimage_number"])
        self.image, self.mask, self.source_rect, radius = subimage_info
        if self.image is not None:
            self.debug("Setting subimage {}".format(self.symbols["subimage_number"]))
            image_rect = self.image.get_rect()
            self.rect.width = image_rect.width
            self.rect.height = image_rect.height
            if radius is not None:
                # disk collision type; get the predefined radius for collisions
                self.radius = radius

    def aim_toward_point(self, pointxy):
        """
        Change the direction of motion toward a given point.

        :param pointxy: A 2-element list of the x, y coordinate
        :type pointxy: array-like
        """
        self.debug("aim_toward_point():")
        self.direction = direction_from_a_to_b(self.get_center_point(), pointxy)

    def set_velocity_compass(self, action):
        """
        Handle the set_velocity_compass action.

        Possible directions:

        * NONE: don't set the direction, just the speed
        * '|' separated list of possible directions to be chosen at
          random: UP, UPLEFT, UPRIGHT, RIGHT, DOWN, DOWNLEFT, DOWNRIGHT, LEFT
          (see :py:attr:`~pygame_maker.actions.action.Action.COMPASS_DIRECTIONS`)

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        """
        self.debug("set_velocity_compass(action={}):".format(action))
        # convert compass direction into degrees
        new_params = dict(action.action_data)
        new_params["direction"] = 0.0
        if new_params["compass_directions"] != "NONE":
            dirs = new_params['compass_directions'].split('|')
            dir_count = len(dirs)
            new_dir = 0
            if dir_count > 1:
                new_dir = random.randint(0, dir_count - 1)
            if dirs[new_dir] in action.COMPASS_DIRECTIONS:
                # convert direction name to degrees
                new_params["direction"] = action.COMPASS_DIRECTION_DEGREES[dirs[new_dir]]
            elif dirs[new_dir] == "STOP":
                # if stop was selected, set speed to zero
                new_params['speed'] = 0
        del new_params["compass_directions"]
        self._apply_kwargs(new_params)

    def move_toward_point(self, action):
        """
        Handle the move_toward_point action.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        """
        self.debug("move_toward_point(action={}):".format(action))
        if "destination" in action.action_data:
            self._delay_motion_updates = True
            # change direction
            self.aim_toward_point(action.action_data["destination"])
            # apply speed parameter
            self._apply_kwargs({"speed": action.action_data['speed']})
            self._delay_motion_updates = False
            self._change_motion_x_y()

    def set_horizontal_speed(self, action):
        """
        Handle the set_horizontal_speed action.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        """
        self.debug("set_horizontal_speed(action={}):".format(action))
        relative = False
        if "relative" in action.action_data:
            relative = action.action_data["relative"]
        compass_name = action.action_data["horizontal_direction"]
        if compass_name in ["LEFT", "RIGHT"]:
            speed = action.action_data["horizontal_speed"]
            direction = action.COMPASS_DIRECTION_DEGREES[compass_name]
            # horiz_vec has only x direction
            horiz_vec = get_vector_xy_from_velocity(speed, direction)
            new_hspeed = horiz_vec[0]
            if relative:
                new_hspeed += self.hspeed
            self.hspeed = new_hspeed

    def set_vertical_speed(self, action):
        """
        Handle the set_vertical_speed action.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        """
        self.debug("set_vertical_speed(action={}):".format(action))
        relative = False
        if "relative" in action.action_data:
            relative = action.action_data["relative"]
        compass_name = action.action_data["vertical_direction"]
        if compass_name in ["UP", "DOWN"]:
            speed = action.action_data["vertical_speed"]
            direction = action.COMPASS_DIRECTION_DEGREES[compass_name]
            # vert_vec has only y direction
            vert_vec = get_vector_xy_from_velocity(speed, direction)
            new_vspeed = vert_vec[1]
            if relative:
                new_vspeed += self.vspeed
            self.vspeed = new_vspeed

    def execute_action(self, action, an_event):
        """
        Perform an action in an action sequence, in response to an event.

        :param action: The Action instance that triggered this method
        :type action: :py:class:`~pygame_maker.actions.action.Action`
        :param an_event: The Event instance that triggered this method
        :type an_event: :py:class:`~pygame_maker.events.event.Event`
        """
        # Apply any setting names that match property names found in the
        #  action_data.  For some actions, this is enough.
        # common exceptions:
        #  apply_to: assumed to have directed the action to this instance
        #  relative: add to instead of replace property settings
        action_params, handled_action = SimpleObjectInstance.execute_action(self, action, an_event)
        # check for expressions that need to be executed
        if not handled_action:
            if action.name == "jump_to_start":
                self.position = self.start_position
            elif action.name == "reverse_horizontal_speed":
                # old_dir = self.direction
                self.direction = -self.direction
                # self.debug("Reverse hdir {} to {}".format(old_dir, self.direction))
            elif action.name == "reverse_vertical_speed":
                # old_dir = self.direction
                self.direction = 180.0 - self.direction
                # self.debug("Reverse vdir {} to {}".format(old_dir, self.direction))
            elif action.name == "bounce_off_collider":
                # self.debug("bounce event: {}".format(an_event))
                if ((action_params['precision'] == 'imprecise') or
                        ('normal' not in list(an_event.event_params.keys()))):
                    self.direction = 180.0 + self.direction
                else:
                    norm = np.array(an_event['normal'])
                    # print("Check normal {}".format(norm))
                    if abs(norm[0]) == abs(norm[1]):
                        self.direction = 180.0 + self.direction
                    elif abs(norm[0]) > abs(norm[1]):
                        # X component is greater; reverse X
                        self.direction = -self.direction
                    else:
                        # Y component is greater; reverse Y
                        self.direction = 180.0 - self.direction
            else:
                self.debug("  {} inst {} execute_action {} fell through..".
                           format(self.kind.name, self.inst_id, action.name))
                self._apply_kwargs(action_params)

    def __repr__(self):
        return ("<{} {:03d} @ {} dir {} speed {}>".
                format(type(self).__name__, self.inst_id, self.position, self.direction,
                       self.speed))
