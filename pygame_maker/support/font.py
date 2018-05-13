"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Implement pygame maker font resource.
"""

import re
import pygame
import yaml


class FontRenderer(object):
    """
    Render text onto a surface using selected font properties.
    """
    FILE_URI_RE = re.compile("^file://(.*)")
    NON_WHITESPACE_RE = re.compile(r"\S")

    @staticmethod
    def get_render_hash_key(text, color, background):
        """
        Produce a hash string composed of text, color and background strings
        for quick storage and retrieval of rendered text from the cache.
        """
        return "{}|{}|{}".format(text, color, background)

    def __init__(self, font_resource):
        self.font_resource = font_resource
        self.fontfile = False
        self.fontpath = None
        minfo = None
        if font_resource.fontname is not None:
            minfo = self.FILE_URI_RE.match(font_resource.fontname)
        if minfo:
            self.fontpath = minfo.group(1)
            if len(self.fontpath) > 0:
                self.fontfile = True
        if self.fontfile:
            self._renderer = pygame.font.Font(self.fontpath, font_resource.fontsize)
            # a font file is likely to be one of regular, bold, or italic.  In
            # this case, believe the user that created the font resource
            # regarding those text effects as well as font size.  It should be
            # obvious that an italic font wouldn't need the italic flag set..
            self._renderer.set_bold(font_resource.bold)
            self._renderer.set_italic(font_resource.italic)
        else:
            self._renderer = pygame.font.SysFont(font_resource.fontname,
                                                 font_resource.fontsize,
                                                 font_resource.bold,
                                                 font_resource.italic)
        if font_resource.underline:
            self._renderer.set_underline(True)
        self.cached_renders = {}
        # controls whether future lines will be added to the cache
        self._cache_enabled = True

    def cache_enabled(self):
        """Get the cache enabled status."""
        return self._cache_enabled

    def disable_text_cache(self):
        """Disable text caching."""
        self._cache_enabled = False

    def enable_text_cache(self):
        """Enable text caching."""
        self._cache_enabled = True

    def get_linesize(self):
        """Get the height of text drawn in the renderer's selected font."""
        return self._renderer.get_linesize()

    def cache_render(self, text_line, color, background, surface):
        """Store the surface containing rendered text for re-use."""
        if not self.cache_enabled():
            return
        line_hash_key = FontRenderer.get_render_hash_key(text_line, color, background)
        if line_hash_key not in list(self.cached_renders.keys()):
            self.cached_renders[line_hash_key] = surface
        # cache with a key without colors, to make calculating the size of
        # this line quicker in calc_render_size()
        no_color_hash_key = FontRenderer.get_render_hash_key(text_line, None, None)
        if no_color_hash_key not in list(self.cached_renders.keys()):
            self.cached_renders[no_color_hash_key] = surface
        # print("Updated text cache:\n{}".format(self.cached_renders))

    def calc_render_size(self, text):
        """
        Calculate the width and height of a block of text using the current font.

        The given text is split on newlines.  The returned height will hold
        all text lines with line spacing, and the returned width will hold the
        longest line.
        """
        lines = text.splitlines()
        # remove trailing empty lines
        while (len(lines)) > 0 and (len(lines[-1]) == 0):
            del lines[-1]
        width = 0
        height = 0
        has_text = False
        for idx, line in enumerate(lines):
            if idx > 0:
                height += self.font_resource.line_spacing
            minfo = self.NON_WHITESPACE_RE.search(line)
            if (len(line) == 0) or not minfo:
                height += self._renderer.get_linesize()
                continue
            has_text = True
            line_width = 0
            line_height = 0
            # every render also caches a version without colors, to be used
            # when querying the size of the text render later
            no_color_hash_key = FontRenderer.get_render_hash_key(line, None, None)
            if no_color_hash_key in list(self.cached_renders.keys()):
                line_width = self.cached_renders[no_color_hash_key].get_width()
                line_height = self.cached_renders[no_color_hash_key].get_height()
            else:
                line_width, line_height = self._renderer.size(line)
            if line_width > width:
                width = line_width
            height += line_height
        if not has_text:
            # no sense drawing empty space..
            return (0, 0)
        return (width, height)

    def render_text(self, screen, position, text, color, background=None):
        """
        Draw the text contained in the text string to the screen at the given
        position, using the given color and background (if any).

        Use pygame.font.render() to produce the text, which is then blitted
        to the given surface.  Rendered text is cached so it can be redrawn
        quickly later.

        :param screen: A pygame surface
        :type screen: :py:class:`pygame.Surface`
        :param position: X, Y coordinates of the upper left corner where the
            text will be drawn
        :type position: pygame_maker.support.coordinate.Coordinate
        :param text: The text string to be rendered
        :type text: str
        :param color: The text foreground color
        :type color: pygame_maker.support.color.Color
        :param background: The text background color.  If None, uses a
            transparent background
        :type background: None | pygame_maker.support.color.Color
        """
        lines = text.splitlines()
        # remove trailing empty lines
        while (len(lines)) > 0 and (len(lines[-1]) == 0):
            del lines[-1]
        x_posn = position.x
        y_posn = position.y
        # print("starting text @ ({},{})".format(x_posn, y_posn))
        # print("text lines: {}".format(lines))
        for idx, line in enumerate(lines):
            if idx > 0:
                # print("Adding gap {}".format(self.font_resource.line_spacing))
                y_posn += self.font_resource.line_spacing
            if len(line) == 0:
                y_posn += self._renderer.get_linesize()
                continue
            font_surf = None
            line_hash_key = FontRenderer.get_render_hash_key(line, color, background)
            if line_hash_key in list(self.cached_renders.keys()):
                font_surf = self.cached_renders[line_hash_key]
            else:
                if background is None:
                    font_surf = self._renderer.render(line, self.font_resource.antialias,
                                                      color.color)
                else:
                    font_surf = self._renderer.render(line, self.font_resource.antialias,
                                                      color.color, background.color)
                # cache this render to make drawing the same line again faster
                self.cache_render(line, color, background, font_surf)
            screen.blit(font_surf, (x_posn, y_posn))
            # print("Adding text line height {}".format(font_surf.get_height()))
            y_posn += font_surf.get_height()


class Font(object):
    """Pygame maker font resource class."""
    DEFAULT_FONT_PREFIX = "fnt_"

    FONT_CACHE = {}

    @staticmethod
    def load_from_yaml(font_yaml_stream, unused):
        """
        Create a new font resource from a YAML-formatted file.  Checks each
        key against known Font parameters, and uses only those parameters
        to initialize a new font.
        Expected YAML object format::

            - fnt_name1:
                fontname: <string>
                size: 12
                line_spacing: 12
                bold: true|false
                italic: true:false
                underline: true:false
                antialias: true:false
            - fnt_name2:
                ...

        :param font_yaml_stream: File or stream object containing YAML-
            formatted data
        :type font_yaml_stream: File-like object
        :param unused: This is a placeholder, since other load_from_yaml()
            resource methods take an additional argument.
        :return: An empty list, if the YAML-defined font(s) is (are) invalid,
            or a list of new fonts, for those with YAML fields that pass
            basic checks
        :rtype: list
        """
        new_font_list = []
        yaml_info = yaml.load(font_yaml_stream)
        if yaml_info:
            for top_level in yaml_info:
                font_args = {}
                font_name = list(top_level.keys())[0]
                yaml_info_hash = top_level[font_name]
                if 'fontname' in yaml_info_hash:
                    font_args['fontname'] = yaml_info_hash['fontname']
                if 'fontsize' in yaml_info_hash:
                    font_args['fontsize'] = yaml_info_hash['fontsize']
                if 'line_spacing' in yaml_info_hash:
                    font_args['line_spacing'] = yaml_info_hash['line_spacing']
                if 'bold' in yaml_info_hash:
                    font_args['bold'] = (yaml_info_hash['bold'] is True)
                if 'italic' in yaml_info_hash:
                    font_args['italic'] = (yaml_info_hash['italic'] is True)
                if 'underline' in yaml_info_hash:
                    font_args['underline'] = (yaml_info_hash['underline'] is True)
                if 'antialias' in yaml_info_hash:
                    font_args['antialias'] = (yaml_info_hash['antialias'] is True)
                new_font = Font(font_name, **font_args)
                new_font_list.append(new_font)
        return new_font_list

    @staticmethod
    def hash_font(font_resource):
        """Produce a hash key string from font resource properties."""
        return "|".join([str(font_resource.fontname), str(font_resource.fontsize),
                         str(font_resource.bold), str(font_resource.italic),
                         str(font_resource.underline), str(font_resource.antialias)])

    @classmethod
    def is_cached_font(cls, font_resource):
        """
        Returns True if the given font resource is found in the cache, False
        otherwise.
        """
        fhash = cls.hash_font(font_resource)
        return fhash in list(cls.FONT_CACHE.keys())

    @classmethod
    def get_cached_font(cls, font_resource):
        """Retrieve a font resource from the cache."""
        fhash = cls.hash_font(font_resource)
        # print("Get {} from font cache".format(fhash))
        return cls.FONT_CACHE[fhash]

    @classmethod
    def add_font_to_cache(cls, font_resource, renderer):
        """Add a font resource to the cache."""
        fhash = cls.hash_font(font_resource)
        if fhash not in list(cls.FONT_CACHE.keys()):
            # print("Add {} to font cache".format(fhash))
            cls.FONT_CACHE[fhash] = renderer

    def __init__(self, name, **kwargs):
        self.name = self.DEFAULT_FONT_PREFIX
        if name:
            self.name = name
        # The font's name
        self._fontname = ""
        # The font's size
        self._fontsize = 0
        # The vertical space between lines of text
        self._line_spacing = 0
        # Embolden
        self._bold = False
        # Italicize
        self._italic = False
        # Underline
        self._underline = False
        # Antialias
        self._antialias = False
        self._property_changed = True
        self._cached_renderer = None
        self._copy_count = 0
        if 'fontname' in kwargs:
            self.fontname = kwargs['fontname']
        if 'fontsize' in kwargs:
            self.fontsize = kwargs['fontsize']
        if 'line_spacing' in kwargs:
            self.line_spacing = kwargs['line_spacing']
        if 'bold' in kwargs:
            self.bold = kwargs['bold']
        if 'italic' in kwargs:
            self.italic = kwargs['italic']
        if 'underline' in kwargs:
            self.underline = kwargs['underline']
        if 'antialias' in kwargs:
            self.antialias = kwargs['antialias']

    @property
    def fontname(self):
        """Get and set the font's name."""
        return self._fontname

    @fontname.setter
    def fontname(self, new_fontname):
        if new_fontname != self._fontname:
            self._property_changed = True
            self._fontname = new_fontname

    @property
    def fontsize(self):
        """Get and set the font size."""
        return self._fontsize

    @fontsize.setter
    def fontsize(self, new_fontsize):
        if new_fontsize != self._fontsize:
            self._property_changed = True
            self._fontsize = new_fontsize

    @property
    def line_spacing(self):
        """Get and set the line spacing."""
        return self._line_spacing

    @line_spacing.setter
    def line_spacing(self, new_line_spacing):
        if new_line_spacing != self._line_spacing:
            self._line_spacing = new_line_spacing

    @property
    def bold(self):
        """Get and set bold font weight flag."""
        return self._bold

    @bold.setter
    def bold(self, new_bold):
        bold_truth = (new_bold is True)
        if bold_truth != self._bold:
            self._property_changed = True
            self._bold = bold_truth

    @property
    def italic(self):
        """Get and set italicization flag."""
        return self._italic

    @italic.setter
    def italic(self, new_italic):
        italic_truth = (new_italic is True)
        if italic_truth != self._italic:
            self._property_changed = True
            self._italic = italic_truth

    @property
    def underline(self):
        """Get and set text underline flag."""
        return self._underline

    @underline.setter
    def underline(self, new_underline):
        underline_truth = (new_underline is True)
        if underline_truth != self._underline:
            self._property_changed = True
            self._underline = underline_truth

    @property
    def antialias(self):
        """Get and set text antialias flag."""
        return self._antialias

    @antialias.setter
    def antialias(self, new_antialias):
        antialias_truth = (new_antialias is True)
        if antialias_truth != self._antialias:
            self._antialias = antialias_truth

    def get_font_renderer(self):
        """Get a renderer instance for the font resource."""
        if self._property_changed:
            renderer = None
            if not Font.is_cached_font(self):
                renderer = FontRenderer(self)
                Font.add_font_to_cache(self, renderer)
            else:
                renderer = Font.get_cached_font(self)
            self._cached_renderer = renderer
            self._property_changed = False
        return self._cached_renderer

    def font_settings_match(self, other):
        """
        Return True if this font's properties match another font, False
        otherwise.
        """
        return (self.fontname == other.fontname and
                self.fontsize == other.fontsize and
                self.bold == other.bold and
                self.italic == other.italic and
                self.underline == other.underline and
                self.antialias == other.antialias)

    def copy(self):
        """Duplicate a font instance."""
        new_font = Font("{}_copy{}".format(self.name, self._copy_count), fontname=self.fontname,
                        fontsize=self.fontsize, bold=self.bold, italic=self.italic,
                        underline=self.underline, antialias=self.antialias,
                        line_spacing=self.line_spacing)
        self._copy_count += 1
        if self._cached_renderer is not None:
            new_font._cached_renderer = self._cached_renderer

    def __repr__(self):
        return "<Font {} size {}>".format(self.name, self.fontsize)

