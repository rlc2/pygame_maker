#!/usr/bin/env python

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# test font resource

import pygame_maker.actors.font as font
import pygame_maker.support.color as color
import pygame_maker.support.coordinate as coord
import pg_template
import pygame
import sys


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768


class MyGameManager:
    HEADER_LINE_TOP = 20
    TEXT_TOP = 40
    TEXT_INDENT = 10
    FONT_SIZE = 20
    MIN_FONT_SIZE = 8
    MAX_FONT_SIZE = 48
    LINES_PER_PAGE = 20
    COLOR_LIST = [
        color.Color("#ff0000"),
        color.Color("#00ff00"),
        color.Color("#0000ff"),
        color.Color("#ffff00"),
        color.Color("#ff00ff"),
        color.Color("#00ffff"),
        color.Color("#888888"),
        color.Color("#ffffff"),
        color.Color("#222222"),
    ]
    SYSTEM_FONT_COLOR = color.Color("orange")

    def __init__(self):
        self.screen = None
        self.current_events = []
        self.system_font = None
        self.fonts = []
        self.bold = False
        self.italic = False
        self.underline = False
        self.antialias = False
        self.textlines = []
        self.text_pages = 0
        self.line_spacing = 0
        self.current_page = 0
        self.current_font = 0
        self.current_color = 0
        self.current_size = self.FONT_SIZE
        self.changed_setting = True
        self.done = False

    def setup(self, screen):
        self.screen = screen
        with open(sys.argv[0], "r") as source_f:
            self.textlines = source_f.readlines()
        self.system_font = font.Font("fnt_sys", fontname=None, fontsize=self.FONT_SIZE)
        known_fonts = pygame.font.get_fonts()
        for idx, a_font in enumerate(known_fonts):
            self.fonts.append(font.Font("fnt_{}".format(idx),
                fontname=a_font,
                fontsize=self.FONT_SIZE))
        self.text_pages = (len(self.textlines) / self.LINES_PER_PAGE)
        if (len(self.textlines) % self.LINES_PER_PAGE) != 0:
            self.text_pages += 1

    def collect_event(self, event):
        self.current_events.append(event)

    def update(self):
        for ev in self.current_events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE or ev.key == pygame.K_q:
                    self.done = True
                    break
                elif ev.key == pygame.K_PAGEUP:
                    if self.current_page > 0:
                        self.current_page -= 1
                        self.changed_setting = True
                elif ev.key == pygame.K_PAGEDOWN:
                    if self.current_page < (self.text_pages-1):
                        self.current_page += 1
                        self.changed_setting = True
                elif ev.key == pygame.K_MINUS:
                    if self.current_size > self.MIN_FONT_SIZE:
                        self.current_size -= 1
                        self.changed_setting = True
                elif ev.key == pygame.K_EQUALS:
                    if self.current_size < self.MAX_FONT_SIZE:
                        self.current_size += 1
                        self.changed_setting = True
                elif ev.key == pygame.K_b:
                    self.bold = not self.bold
                    self.changed_setting = True
                elif ev.key == pygame.K_i:
                    self.italic = not self.italic
                    self.changed_setting = True
                elif ev.key == pygame.K_u:
                    self.underline = not self.underline
                    self.changed_setting = True
                elif ev.key == pygame.K_a:
                    self.antialias = not self.antialias
                elif ev.key == pygame.K_COMMA:
                    if self.current_color > 0:
                        self.current_color -= 1
                    else:
                        self.current_color = len(self.COLOR_LIST) - 1
                elif ev.key == pygame.K_PERIOD:
                    if self.current_color < (len(self.COLOR_LIST) - 1):
                        self.current_color += 1
                    else:
                        self.current_color = 0
        # done with event handling
        self.current_events = []

    def draw_objects(self):
        line_index = self.LINES_PER_PAGE * self.current_page
        current_font = self.fonts[self.current_font]
        # draw the font name at the top center, using the system font
        sys_renderer = self.system_font.get_font_renderer()
        fontname_text = current_font.fontname
        font_info_text = "{} size {} spacing {}".format(current_font.fontname,
            self.current_size, self.line_spacing)
        if self.bold:
            font_info_text += " bold"
        if self.italic:
            font_info_text += " italic"
        if self.underline:
            font_info_text += " underline"
        if self.antialias:
            font_info_text += " antialias"
        header_width, header_height = sys_renderer.calc_render_size(font_info_text)
        header_x = SCREEN_WIDTH / 2 - header_width / 2
        sys_renderer.render_text(self.screen, coord.Coordinate(header_x, self.HEADER_LINE_TOP),
            font_info_text, self.SYSTEM_FONT_COLOR, color.Color("black"))
        # draw the current page of text using the current settings
        page_text = "".join(self.textlines[line_index:line_index+self.LINES_PER_PAGE])
        current_font.fontsize = self.current_size
        current_font.line_spacing = self.line_spacing
        current_font.bold = self.bold
        current_font.italic = self.italic
        current_font.underline = self.underline
        current_font.antialias = self.antialias
        fnt_renderer = current_font.get_font_renderer()
        if self.changed_setting:
            text_dims = fnt_renderer.calc_render_size(page_text)
            print("Text page dims: {}x{}".format(text_dims[0], text_dims[1]))
            self.changed_setting = False
        fnt_renderer.render_text(self.screen, coord.Coordinate(self.TEXT_INDENT, self.TEXT_TOP),
            page_text, self.COLOR_LIST[self.current_color])

    def draw_background(self):
        self.screen.fill( (0,0,0) ) # grey background color

    def final_pass(self):
        pass

    def is_done(self):
        return self.done


mymanager = MyGameManager()
mygame = pg_template.PygameTemplate( (SCREEN_WIDTH,SCREEN_HEIGHT), "Font Tests",
    mymanager, 5)
mygame.run()

