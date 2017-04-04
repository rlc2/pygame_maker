#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# implement pygame_maker font resource

import re
import pygame
import os.path


class FontRenderer(object):
    def __init__(self, font_resource):
        self.font_resource = font_resource
        self._renderer = pygame.font.SysFont(font_resource.fontname,
                         font_resource.fontsize,
                         font_resource.bold,
                         font_resource.italic)
        if font_resource.underline:
            self._renderer.set_underline(True)

    def get_linesize(self):
        return self._renderer.get_linesize()

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
            del(lines[-1])
        width = 0
        height = 0
        has_text = False
        for idx, line in enumerate(lines):
            if idx > 0:
                height += self.font_resource.line_spacing
            if len(line) == 0:
                height += self._renderer.get_linesize()
                continue
            has_text = True
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
        
        Uses pygame.font.render() to produce the text, which is then blitted
        to the given surface.

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
            del(lines[-1])
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
            if background is None:
                font_surf = self._renderer.render(line, self.font_resource.antialias, color.color)
            else:
                font_surf = self._renderer.render(line, self.font_resource.antialias, color.color, background.color)
            screen.blit(font_surf, (x_posn, y_posn))
            # print("Adding text line height {}".format(font_surf.get_height()))
            y_posn += font_surf.get_height()


class Font(object):
    DEFAULT_FONT_PREFIX = "fnt_"

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
                font_name = top_level.keys()[0]
                yaml_info_hash = top_level[font_name]
                if 'fontname' in yaml_info_hash:
                    font_args['fontname'] = yaml_info_hash['fontname']
                if 'fontsize' in yaml_info_hash:
                    font_args['fontsize'] = yaml_info_hash['fontsize']
                if 'line_spacing' in yaml_info_hash:
                    font_args['line_spacing'] = yaml_info_hash['line_spacing']
                if 'bold' in yaml_info_hash:
                    font_args['bold'] = (yaml_info_hash['bold'] == True)
                if 'italic' in yaml_info_hash:
                    font_args['italic'] = (yaml_info_hash['italic'] == True)
                if 'underline' in yaml_info_hash:
                    font_args['underline'] = (yaml_info_hash['underline'] == True)
                if 'antialias' in yaml_info_hash:
                    font_args['antialias'] = (yaml_info_hash['antialias'] == True)
                new_font = Font(font_name, **font_args)
                new_font_list.append(new_font)
        return new_font_list

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
        return self._fontname

    @fontname.setter
    def fontname(self, new_fontname):
        if new_fontname != self._fontname:
            self._property_changed = True
            self._fontname = new_fontname

    @property
    def fontsize(self):
        return self._fontsize

    @fontsize.setter
    def fontsize(self, new_fontsize):
        if new_fontsize != self._fontsize:
            self._property_changed = True
            self._fontsize = new_fontsize

    @property
    def line_spacing(self):
        return self._line_spacing

    @line_spacing.setter
    def line_spacing(self, new_line_spacing):
        if new_line_spacing != self._line_spacing:
            self._line_spacing = new_line_spacing

    @property
    def bold(self):
        return self._bold

    @bold.setter
    def bold(self, new_bold):
        bold_truth = (new_bold == True)
        if bold_truth != self._bold:
            self._property_changed = True
            self._bold = bold_truth

    @property
    def italic(self):
        return self._italic

    @italic.setter
    def italic(self, new_italic):
        italic_truth = (new_italic == True)
        if italic_truth != self._italic:
            self._property_changed = True
            self._italic = italic_truth

    @property
    def underline(self):
        return self._underline

    @underline.setter
    def underline(self, new_underline):
        underline_truth = (new_underline == True)
        if underline_truth != self._underline:
            self._property_changed = True
            self._underline = underline_truth

    @property
    def antialias(self):
        return self._antialias

    @antialias.setter
    def antialias(self, new_antialias):
        antialias_truth = (new_antialias == True)
        if antialias_truth != self._antialias:
            self._antialias = antialias_truth

    def get_font_renderer(self):
        if self._property_changed:
            self._cached_renderer = FontRenderer(self)
            self._property_changed = False
        return self._cached_renderer

    def __repr__(self):
        return "<Font {} size {}>".format(self.name, self.fontsize)

