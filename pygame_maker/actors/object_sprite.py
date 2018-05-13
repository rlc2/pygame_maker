"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

implement pygame_maker sprite resource (not the same as a pygame Sprite;
 this is closer to a pygame.image)
"""

import re
import os.path
import math
import pygame
import yaml


def mask_from_surface(surface, threshold=127):
    """
    Create a precise mask of a pygame.Surface's pixels.

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
        for row in range(surface.get_height()):
            for col in range(surface.get_width()):
                if surface.get_at((col, row)) != key:
                    mask.set_at((col, row), 1)
    else:
        for row in range(surface.get_height()):
            for col in range(surface.get_width()):
                if surface.get_at((col, row))[3] > threshold:
                    mask.set_at((col, row), 1)
    return mask

def create_rectangle_mask(orig_rect):
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
    mask = pygame.mask.Mask((orig_rect.width, orig_rect.height))
    mask.fill()
    return mask

def create_disk_mask(orig_rect, radius):
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
    :param radius: The radius of the disk mask
    :type radius: int
    """
    # create a disk mask with a radius sufficient to cover the
    #  opaque pixels
    # NOTE: collisions with objects that have a different collision type
    #  will use this mask; the mask generated here won't fill the sprite's
    #  radius, but will be a circle with the correct radius that is clipped
    #  at the sprite's rect dimensions
    disk_mask_center = (int(orig_rect.width / 2), int(orig_rect.height / 2))
    #pylint: disable=too-many-function-args
    #pylint: disable=unexpected-keyword-arg
    disk_mask_surface = pygame.Surface((orig_rect.width, orig_rect.height), depth=8)
    #pylint: enable=unexpected-keyword-arg
    #pylint: enable=too-many-function-args
    disk_mask_surface.set_colorkey(pygame.Color("#000000"))
    disk_mask_surface.fill(pygame.Color("#000000"))
    pygame.draw.circle(disk_mask_surface, pygame.Color("#ffffff"), disk_mask_center, radius)
    mask = mask_from_surface(disk_mask_surface)
    return mask

def get_disk_radius(precise_mask, orig_rect, bound_rect):
    """
    Calculate the radius of a circle that covers the opaque pixels in
    precise_mask.

    :param precise_mask: The precise mask for every opaque pixel in the
        image.  If the original image was circular, this can aid in
        creating in a more accurate circular mask
    :type precise_mask: :py:class:`pygame.mask.Mask`
    :param orig_rect: The Rect from the image
    :type orig_rect: :py:class:`pygame.Rect`
    :param bound_rect: The bounding Rect for the image
    :type bound_rect: :py:class:`pygame.Rect`
    """
    # find the radius of a circle that contains bound_rect for the worst
    #  case
    disk_mask_center = (orig_rect.width/2, orig_rect.height/2)
    left_center_distance = abs(disk_mask_center[0]-bound_rect.x)
    right_center_distance = abs(disk_mask_center[0]-bound_rect.right)
    top_center_distance = abs(disk_mask_center[1]-bound_rect.y)
    bottom_center_distance = abs(disk_mask_center[1]-bound_rect.bottom)
    max_bound_radius = math.sqrt(max(left_center_distance, right_center_distance)**2 +
                                 max(top_center_distance, bottom_center_distance)**2)
    # determine whether a smaller radius could be used (i.e.
    #  no corner pixels within the bounding rect are set)
    max_r = 0
    for row in range(bound_rect.y, bound_rect.height):
        for col in range(bound_rect.x, bound_rect.width):
            if precise_mask.get_at((col, row)) > 0:
                rad = math.sqrt((disk_mask_center[0]-col)**2 + (disk_mask_center[1]-row)**2)
                if rad > max_r:
                    max_r = rad
    bound_radius = max_bound_radius
    if (max_r > 0) and (max_r < max_bound_radius):
        bound_radius = max_r
    radius = int(math.ceil(bound_radius))
    return radius


class ObjectSpriteException(Exception):
    """Raised when an ObjectSprite discovers an invalid attribute."""
    pass


class ObjectSprite(object):
    """Wrap a sprite resource to be used by ObjectTypes."""
    #: Available collision type names
    COLLISION_TYPES = [
        "precise",
        "rectangle",
        "disk",
        "diamond",
        "polygon"
    ]
    #: Available bounding box type names
    BOUNDING_BOX_TYPES = [
        "automatic",
        "full_image",
        "manual"
    ]

    IMAGE_STRIP_FILE_RE = re.compile(r".*_strip(\d+)\.\w+")
    DEFAULT_SPRITE_PREFIX = "spr_"

    @staticmethod
    def load_from_yaml(sprite_yaml_stream, game_engine):
        """
        Create a new sprite from a YAML-formatted file.  Checks each key
        against known ObjectSprite parameters, and uses only those
        parameters to initialize a new sprite.
        Expected YAML object format::

            - spr_name1:
                filename: <filename>
                smooth_edges: true|false
                manual_bounding_box_rect:
                  top: 0
                  bottom: 32
                  left: 0
                  right: 32
                ...
            - spr_name2:
                ...

        :param sprite_yaml_stream: File or stream object containing YAML-
            formatted data
        :type sprite_yaml_stream: File-like object
        :return: An empty list, if the YAML-defined sprite(s) is (are) invalid,
            or a list of new sprites, for those with YAML fields that pass
            basic checks
        :rtype: list
        """
        new_sprite_list = []
        yaml_info = yaml.load(sprite_yaml_stream)
        if yaml_info:
            for top_level in yaml_info:
                sprite_args = {}
                sprite_name = list(top_level.keys())[0]
                yaml_info_hash = top_level[sprite_name]
                if 'filename' in yaml_info_hash:
                    sprite_args['filename'] = yaml_info_hash['filename']
                if 'smooth_edges' in yaml_info_hash:
                    sprite_args['smooth_edges'] = yaml_info_hash['smooth_edges']
                if 'preload_texture' in yaml_info_hash:
                    sprite_args['preload_texture'] = yaml_info_hash['preload_texture']
                if 'transparency_pixel' in yaml_info_hash:
                    sprite_args['transparency_pixel'] = yaml_info_hash['transparency_pixel']
                if 'origin' in yaml_info_hash:
                    sprite_args['origin'] = yaml_info_hash['origin']
                if 'collision_type' in yaml_info_hash:
                    sprite_args['collision_type'] = yaml_info_hash['collision_type']
                if 'bounding_box_type' in yaml_info_hash:
                    sprite_args['bounding_box_type'] = yaml_info_hash['bounding_box_type']
                if 'manual_bounding_box_rect' in yaml_info_hash:
                    sprite_args['manual_bounding_box_rect'] = \
                        yaml_info_hash['manual_bounding_box_rect']
                if 'custom_subimage_columns' in yaml_info_hash:
                    sprite_args['custom_subimage_columns'] = \
                        yaml_info_hash['custom_subimage_columns']
                new_sprite = None
                try:
                    new_sprite = ObjectSprite(sprite_name, **sprite_args)
                except (ValueError, ObjectSpriteException) as exc:
                    game_engine.warn("Skipping YAML ObjectSprite '{}' due to error: {}".
                                     format(sprite_name, exc))
                    continue
                try:
                    new_sprite.check()
                except ObjectSpriteException as exc:
                    game_engine.warn("Skipping YAML ObjectSprite '{}' due to error: {}".
                                     format(sprite_name, exc))
                    continue
                new_sprite_list.append(new_sprite)
        return new_sprite_list

    def __init__(self, name=None, **kwargs):
        """
        Create a new sprite instance.

        :param name: Name for the new sprite instance
        :type name: str
        :param kwargs:
            Named arguments can be supplied to fill in sprite attributes:

            * filename: the name of the file containing the sprite graphic

                * if the file name (minus extension) ends with _strip## (## is
                  a number > 1), the file is assumed to contain multiple
                  adjacent subimages (E.G. for animations) - NYI

            * smooth_edges (bool): not implemented
            * preload_texture (bool): whether to load the sprite graphic from
              the file ahead of usage
            * transparency_pixel (bool): use transparency pixel defined in the
              sprite graphic
            * origin (array-like): where to offset the sprite graphic in
              relation to a supplied x, y in a 2-element list
            * collision_type (str): where and how to look for collisions:

                * precise: check every non-transparent edge pixel (slowest)
                * rectangle: check for edges of a rectangle surrounding the
                  image (fast)
                * disk: check for edges of a circle surrounding the image
                  (slower)
                * diamond: check for edges of a diamond surrounding the image
                  (average) - not implemented
                * polygon: check for edges of a polygon surrounding the image
                  (slow) - not implemented

            * bounding_box_type (str): a box containing the pixels that should
              be drawn

                * automatic: draw all non-tranparent pixels
                * full_image: draw the entire sprite graphic
                * manual: specify left, right, top, bottom dimensions in
                  manual_bounding_box_rect

            * manual_bounding_box_rect (dict): the box dimensions for the
              manual bounding_box_type, in a dict in {'left': left,
              'right': right, 'top': top, 'bottom': bottom} format
        """
        #: The name of the ObjectSprite, usually prefixed with "spr\_"
        self.name = self.DEFAULT_SPRITE_PREFIX
        if name:
            self.name = name
        #: The filename containing the sprite image
        self.filename = ""
        #: Flag whether to smooth the image edges
        self.smooth_edges = False
        #: Flag whether to preload the image in the setup() method
        self.preload_texture = True
        #: Flag whether to honor the transparency pixel inside the image file
        self.transparency_pixel = False
        #: Apply this coordinate offset when drawing the image
        self.origin = (0, 0)
        #: Which subimage number to use from an image strip
        self.subimage_number = 0
        #: How many subimages this sprite contains, derived from the file name
        self.subimage_info = {
            "count": 1,
            # Starting pixel columns for each subimage
            "columns": [0],
            # The individual bounding rects for each subimage
            "bbox_rects": [],
            # The sizes of each subsurface
            "sizes": [],
            # The subsurface masks
            "masks": [],
            # The subsurface radii for the disk collision type
            "radii": []
        }
        #: The subsurfaces for each image in an image strip
        self.subimages = []
        #: Mask type for collision detection, see :py:attr:`COLLISION_TYPES`
        self._collision_type = "rectangle"
        #: How to produce the rect containing drawable pixels, see
        #: :py:attr:`BOUNDING_BOX_TYPES`
        self.bounding_box_type = "automatic"
        #: The dimensions of the boundary rect, if the type is "manual"
        self.manual_bounding_box_rect = pygame.Rect(0, 0, 0, 0)
        if "filename" in kwargs:
            self.filename = kwargs["filename"]
        if "smooth_edges" in kwargs:
            self.smooth_edges = (kwargs["smooth_edges"] is True)
        if "preload_texture" in kwargs:
            self.preload_texture = (kwargs["preload_texture"] is True)
        if "transparency_pixel" in kwargs:
            self.transparency_pixel = (kwargs["transparency_pixel"] is True)
        if "origin" in kwargs:
            orig_item = kwargs["origin"]
            orig_x = 0
            orig_y = 0
            if not isinstance(orig_item, str) and hasattr(orig_item, '__iter__'):
                xylist = list(orig_item)
                if len(orig_item) == 0:
                    raise ValueError("ObjectSprite(): Invalid origin '{}'".format(kwargs["origin"]))
                if len(orig_item) >= 2:
                    try:
                        orig_y = int(xylist[1])
                    except ValueError:
                        raise ValueError
                try:
                    orig_x = int(xylist[0])
                except ValueError:
                    raise ValueError
            else:
                try:
                    orig_x = int(orig_item)
                except ValueError:
                    raise ValueError
            self.origin = (orig_x, orig_y)
        if "collision_type" in kwargs:
            if kwargs["collision_type"] in self.COLLISION_TYPES:
                self.collision_type = kwargs["collision_type"]
            else:
                raise ValueError
        if "bounding_box_type" in kwargs:
            if kwargs["bounding_box_type"] in self.BOUNDING_BOX_TYPES:
                self.bounding_box_type = kwargs["bounding_box_type"]
            else:
                raise ValueError
        if ("manual_bounding_box_rect" in kwargs and
                isinstance(kwargs["manual_bounding_box_rect"], dict)):
            dim = kwargs["manual_bounding_box_rect"]
            topp = 0
            botmp = 0
            leftp = 0
            rightp = 0
            if "left" in dim:
                try:
                    leftp = int(dim["left"])
                except ValueError:
                    pass
            if "right" in dim:
                try:
                    rightp = int(dim["right"])
                except ValueError:
                    pass
            if "top" in dim:
                try:
                    topp = int(dim["top"])
                except ValueError:
                    pass
            if "bottom" in dim:
                try:
                    botmp = int(dim["bottom"])
                except ValueError:
                    pass
            width = rightp - leftp
            height = botmp - topp
            self.manual_bounding_box_rect.left = leftp
            self.manual_bounding_box_rect.top = topp
            self.manual_bounding_box_rect.width = width
            self.manual_bounding_box_rect.height = height
        if 'custom_subimage_columns' in kwargs:
            im_cols = kwargs["custom_subimage_columns"]
            if isinstance(im_cols, dict) or not hasattr(im_cols, '__iter__'):
                raise ValueError
            else:
                self.subimage_info["columns"] = list(im_cols)

        #: The pygame.Surface returned when loading the image from the file
        self.image = None
        #: The dimensions of the image, determined after loading it
        self.image_size = (0, 0)
        #: The bounding rect, containing all pixels to be drawn to a surface
        #: from the image (depends on bounding_box_type)
        self.bounding_box_rect = None

    @property
    def collision_type(self):
        """Get and set the sprite's collision type."""
        return self._collision_type

    @collision_type.setter
    def collision_type(self, value):
        if value not in self.COLLISION_TYPES:
            raise ObjectSpriteException("ObjectSprite error ({}):\
            Unknown collision type '{}'".format(str(self), value))
        self._collision_type = value

    def setup(self):
        """
        Perform any tasks that can be done before the main program loop,
        but only after pygame.init().
        """
        if self.preload_texture:
            self.load_graphic()

    def _collect_subimage_data(self):
        sub_cols = self.subimage_info["columns"]
        if len(sub_cols) <= 1:
            # subimage columns weren't passed in, so calculate them
            max_si_width = int(self.image_size[0] / self.subimage_info["count"])
            for idx in range(len(sub_cols), self.subimage_info["count"]):
                sub_cols.append(max_si_width * idx)
        elif len(sub_cols) > self.subimage_info["count"]:
            # too many custom subimage columns. last one specifies the right
            # edge of the last subimage. trim off any excess
            sub_cols = sub_cols[0:self.subimage_info["count"]+1]
            self.subimage_info["columns"] = sub_cols
        elif len(sub_cols) < self.subimage_info["count"]:
            # too few custom subimage columns; split remaining image columns
            # (if any) between the missing X values
            missing_count = self.subimage_info["count"] - len(sub_cols)
            last_custom_column = sub_cols[-1]
            if (last_custom_column + missing_count + 1) < self.image_size[0]:
                # remember to leave room between the last custom column
                # and the first missing X value
                split_col_width = int((self.image_size[0] - last_custom_column) / (missing_count + 1))
                for ccol in range(missing_count):
                    sub_cols.append(last_custom_column + (ccol + 1) * split_col_width)
            else:
                # overlap the extra columns if there's no room
                for ccol in range(missing_count):
                    sub_cols.append(last_custom_column)
        # now that the subimage columns are known, create subsurfaces for each
        #  of them
        for subim_idx in range(self.subimage_info["count"]):
            subim_col = sub_cols[subim_idx]
            subim_rect = pygame.Rect(0, 0, 0, 0)
            subim_rect.left = subim_col
            subim_rect.height = self.image_size[1]
            if (subim_idx < (self.subimage_info["count"] - 1) or
                    len(sub_cols) > self.subimage_info["count"]):
                # this subimage's width is the next subimage's left column
                # minus this subimage's left column
                subim_rect.width = sub_cols[subim_idx+1] - subim_col
            else:
                # the last subimage's width is the image width minus this
                # subimage's left column, unless an extra custom column was
                # supplied, in which case the extra was used to calculate width
                subim_rect.width = self.image_size[0] - subim_col
            new_subimage = self.image.subsurface(subim_rect)
            self.subimages.append(new_subimage)
            bound_rect = None
            if self.bounding_box_type == "automatic":
                bound_rect = new_subimage.get_bounding_rect()
            elif self.bounding_box_type == "full_image":
                bound_rect = new_subimage.get_rect()
            else:
                bound_rect = pygame.Rect(self.manual_bounding_box_rect)
                # make the bounding rect fit in the subimage
                if bound_rect.left > subim_rect.right:
                    bound_rect.left = subim_rect.right - 1
                if (bound_rect.left + bound_rect.width) > subim_rect.right:
                    bound_rect.width = subim_rect.right - subim_rect.left
                if bound_rect.top > subim_rect.bottom:
                    bound_rect.top = subim_rect.bottom - 1
                if (bound_rect.top + bound_rect.height) > subim_rect.bottom:
                    bound_rect.height = subim_rect.bottom - subim_rect.top
            self.subimage_info["sizes"].append(new_subimage.get_size())
            self.subimage_info["bbox_rects"].append(bound_rect)

    def _create_subimage_masks(self):
        for subimg_idx, subimg in enumerate(self.subimages):
            precise_mask = mask_from_surface(subimg)
            bound_rect = pygame.Rect(self.subimage_info["bbox_rects"][subimg_idx])
            orig_rect = subimg.get_rect()
            if (orig_rect.width == 0) or (orig_rect.height == 0):
                raise ObjectSpriteException("Found broken sprite resource when creating mask")
            if (bound_rect.width == 0) or (bound_rect.height == 0):
                # use the dimensions of the loaded graphic for the bounding
                #  rect in case there's a problem with the sprite resources'
                #  bounding rect
                bound_rect = orig_rect
            # set a mask regardless of the collision type, to enable
            #  collision checks between objects that have different
            #  types
            if self.collision_type == "precise":
                self.subimage_info["masks"].append(precise_mask)
                self.subimage_info["radii"].append(None)
            elif self.collision_type == "disk":
                radius = get_disk_radius(precise_mask, orig_rect, bound_rect)
                self.subimage_info["masks"].append(create_disk_mask(orig_rect, radius))
                self.subimage_info["radii"].append(radius)
            else:
                # other collision types are not supported, fall back to
                #  rectangle
                self.subimage_info["masks"].append(create_rectangle_mask(orig_rect))
                self.subimage_info["radii"].append(None)

    def load_graphic(self):
        """
        Retrieve image data from the file named in the filename attribute.
        Split subimages from image strips, for appropriately-named files.
        Collect information about the graphic in the image_size,
        bounding_box_type, and bounding_box_rect attributes.
        Generate collision masks based on the collision_type.
        """
        if len(self.filename) <= 0:
            raise ObjectSpriteException(
                "ObjectSprite error ({}): Attempt to load image from empty filename".
                format(str(self)))
        if self.check_filename():
            name_minfo = self.IMAGE_STRIP_FILE_RE.search(self.filename)
            if name_minfo:
                self.subimage_info["count"] = int(name_minfo.group(1))
            self.image = pygame.image.load(self.filename).convert_alpha()
            self.image_size = self.image.get_size()
            if self.bounding_box_type == "automatic":
                self.bounding_box_rect = self.image.get_bounding_rect()
            elif self.bounding_box_type == "full_image":
                self.bounding_box_rect = self.image.get_rect()
            else:
                image_rect = self.image.get_rect()
                bound_rect = pygame.Rect(self.manual_bounding_box_rect)
                # make the bounding rect fit in the subimage
                if bound_rect.left >= image_rect.right:
                    bound_rect.left = image_rect.right - 1
                if (bound_rect.left + bound_rect.width) > image_rect.right:
                    bound_rect.width = image_rect.right - image_rect.left
                if bound_rect.top >= image_rect.bottom:
                    bound_rect.top = image_rect.bottom - 1
                if (bound_rect.top + bound_rect.height) > image_rect.bottom:
                    bound_rect.height = image_rect.bottom - image_rect.top
                self.bounding_box_rect = bound_rect
            if self.subimage_info["count"] > 1:
                self._collect_subimage_data()
            else:
                # subimages[0] is the original image, if not an image strip
                self.subimages.append(self.image)
                self.subimage_info["bbox_rects"].append(self.bounding_box_rect)
                self.subimage_info["sizes"].append(self.image_size)
        self._create_subimage_masks()

    def check_filename(self):
        """
        Validity test for filename attribute.

        :return: True if the validity test succeeded, or False
        :rtype: bool
        """
        if not isinstance(self.filename, str):
            raise ObjectSpriteException(
                "ObjectSprite error ({}): filename '{}' is not a string".
                format(str(self), self.filename))
        elif len(self.filename) == 0:
            raise ObjectSpriteException("ObjectSprite error ({}): filename is empty".
                                        format(str(self)))
        if len(self.filename) > 0:
            if not os.path.exists(self.filename):
                raise ObjectSpriteException(
                    "ObjectSprite error ({}): filename '{}' not found".
                    format(str(self), self.filename))
        return True

    def check_origin(self):
        """
        Validity test for origin attribute.

        :return: True if the validity test succeeded, or False
        :rtype: bool
        """
        if isinstance(self.origin, str):
            raise ObjectSpriteException("ObjectSprite error ({}): Origin is a string".
                                        format(str(self)))
        the_origin = list(self.origin)
        if len(the_origin) < 2:
            raise ObjectSpriteException(
                "ObjectSprite error ({}): Origin does not have at least x, y".format(str(self)))
        return True

    def check_collision_type(self):
        """
        Validity test for collision_type attribute.

        :return: True if the validity test succeeded, or False
        :rtype: bool
        """
        if self.collision_type not in self.COLLISION_TYPES:
            raise ObjectSpriteException(
                "ObjectSprite error ({}): Collision type \"{}\" is unknown".
                format(str(self), self.collision_type))
        return True

    def check_bounding_box(self):
        """
        Validity test for bounding_box_type attribute.

        :return: True if the validity test succeeded, or False
        :rtype: bool
        """
        if self.bounding_box_type not in self.BOUNDING_BOX_TYPES:
            raise ObjectSpriteException(
                "ObjectSprite error ({}): Bounding box type \"{}\" is unknown".
                format(str(self), self.bounding_box_type))
        if self.bounding_box_type == "manual":
            self.check_manual_bounding_box_rect()
        return True

    def check_manual_bounding_box_rect(self):
        """
        Validity test for manual_bounding_box_rect attribute.

        :return: True if the validity test succeeded, or False
        :rtype: bool
        """
        bound_rect = self.manual_bounding_box_rect
        if not isinstance(bound_rect, pygame.Rect):
            raise ObjectSpriteException
        dim = (bound_rect.left, bound_rect.right, bound_rect.top, bound_rect.bottom)
        if (bound_rect.left > bound_rect.right) or (bound_rect.top > bound_rect.bottom):
            raise ObjectSpriteException(
                "ObjectSprite error ({}): Bounding box dimensions {} are not sane".
                format(str(self), dim))
        if ((bound_rect.left < 0) or (bound_rect.right < 0) or
                (bound_rect.top < 0) or (bound_rect.bottom < 0)):
            raise ObjectSpriteException(
                "ObjectSprite error ({}): Bounding box dimensions {} are not sane".
                format(str(self), dim))
        return True

    def check(self):
        """
        Run all validity tests.  Used by the load_from_yaml() method to
        ensure the YAML defines valid sprite attributes.

        :return: True if the sprite attributes passed validity tests, or False
        :rtype: bool
        """
        self.check_filename()
        self.check_origin()
        self.check_collision_type()
        self.check_bounding_box()
        return True

    def to_yaml(self):
        """
        Produce the YAML string representing the sprite instance.

        :return: YAML-formatted sprite data
        :rtype: str
        """
        ystr = "- {}:\n".format(self.name)
        ystr += "    filename: {}\n".format(self.filename)
        ystr += "    smooth_edges: {}\n".format(self.smooth_edges)
        ystr += "    preload_texture: {}\n".format(self.preload_texture)
        ystr += "    transparency_pixel: {}\n".format(self.transparency_pixel)
        ystr += "    origin: {}\n".format(str(list(self.origin)))
        ystr += "    collision_type: {}\n".format(self.collision_type)
        ystr += "    bounding_box_type: {}\n".format(self.bounding_box_type)
        bounding_dict = {"left": self.manual_bounding_box_rect.left,
                         "right": self.manual_bounding_box_rect.right,
                         "top": self.manual_bounding_box_rect.top,
                         "bottom": self.manual_bounding_box_rect.bottom
                        }
        ystr += "    manual_bounding_box_rect: {}".format(str(bounding_dict))
        return ystr

    def __eq__(self, other):
        # Equality test, for unit test purposes.
        return (isinstance(other, ObjectSprite) and
                (self.name == other.name) and
                (self.filename == other.filename) and
                (self.smooth_edges == other.smooth_edges) and
                (self.preload_texture == other.preload_texture) and
                (self.transparency_pixel == other.transparency_pixel) and
                (list(self.origin) == list(other.origin)) and
                (self.collision_type == other.collision_type) and
                (self.bounding_box_type == other.bounding_box_type) and
                (self.manual_bounding_box_rect == other.manual_bounding_box_rect))

    def __repr__(self):
        return ("<{} {} file={}>".format(type(self).__name__, self.name,
                                         self.filename))
