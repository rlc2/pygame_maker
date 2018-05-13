#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test pygame_maker.support.font resource module.
"""

import sys
import pygame
import pg_template
import pygame_maker.support.font as font
import pygame_maker.support.color as color
import pygame_maker.support.coordinate as coord


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768


class MyGameManager(object):
    """Custom game manager for font module unit test."""
    HEADER_LINE_TOP = 5
    FONT_TABLE_COLUMNS = 5
    FONT_TABLE_ROWS = 4
    FONT_TABLE_TOP = 25
    FONT_TABLE_LEFT = 50
    FONT_TABLE_COLUMN_WIDTH = 200
    FONT_TABLE_FG_COLOR = color.Color("#888888")
    FONT_TABLE_ACTIVE_FG_COLOR = color.Color("white")
    FONT_PAGE_TOP = 85
    TEXT_TOP = 100
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
        self.file_font = None
        self.fonts = []
        self.bold = False
        self.italic = False
        self.underline = False
        self.antialias = False
        self.textlines = []
        self.text_pages = 0
        self.fonts_per_page = (self.FONT_TABLE_COLUMNS * self.FONT_TABLE_ROWS)
        self.font_pages = 0
        self.current_font_page = 0
        self.current_page = 0
        self.line_spacing = 0
        self.current_page = 0
        self.current_font = 0
        self.current_color = 0
        self.current_size = self.FONT_SIZE
        self.text_dims = None
        self.changed_setting = True
        self.done = False

    def setup(self, screen):
        """Handle setup callback from PygameTemplate."""
        self.screen = screen
        with open(sys.argv[0], "r") as source_f:
            self.textlines = source_f.readlines()
        self.system_font = font.Font("fnt_sys", fontname=None, fontsize=self.FONT_SIZE)
        self.file_font = font.Font(
            "fnt_file",
            fontname="file://pygame_maker/tests/unittest_files/DroidSansFallbackFull.ttf",
            fontsize=14)
        known_fonts = pygame.font.get_fonts()
        for idx, a_font in enumerate(known_fonts):
            self.fonts.append(font.Font("fnt_{}".format(idx),
                                        fontname=a_font,
                                        fontsize=self.FONT_SIZE))
        self.font_pages = int(len(known_fonts) / self.fonts_per_page)
        if (len(known_fonts) % self.fonts_per_page) != 0:
            self.font_pages += 1
        self.text_pages = int(len(self.textlines) / self.LINES_PER_PAGE)
        if (len(self.textlines) % self.LINES_PER_PAGE) != 0:
            self.text_pages += 1

    def collect_event(self, event):
        """Handle collect_event callback from PygameTemplate."""
        self.current_events.append(event)

    def update(self):
        """Handle PygameTemplate update callback."""
        for cev in self.current_events:
            if cev.type == pygame.KEYDOWN:
                if cev.key == pygame.K_ESCAPE or cev.key == pygame.K_q:
                    self.done = True
                    break
                elif cev.key == pygame.K_PAGEUP:
                    # select a different page of text
                    if self.current_page > 0:
                        self.current_page -= 1
                        self.changed_setting = True
                elif cev.key == pygame.K_PAGEDOWN:
                    # select a different page of text
                    if self.current_page < (self.text_pages-1):
                        self.current_page += 1
                        self.changed_setting = True
                elif cev.key == pygame.K_LEFT:
                    # select a different font
                    old_font = self.current_font
                    if (self.current_font % self.fonts_per_page) < self.FONT_TABLE_ROWS:
                        # move to rightmost column from leftmost
                        next_entry = (self.current_font + (self.FONT_TABLE_ROWS) *
                                      (self.FONT_TABLE_COLUMNS-1))
                        if next_entry >= len(self.fonts):
                            while next_entry > self.current_font:
                                # locate the last column of a partial page
                                next_entry -= self.FONT_TABLE_ROWS
                                if next_entry < (len(self.fonts) - 1):
                                    self.current_font = next_entry
                                    break
                        else:
                            self.current_font = next_entry
                    else:
                        if self.current_font > self.FONT_TABLE_ROWS:
                            # move one column to the left
                            self.current_font -= self.FONT_TABLE_ROWS
                    self.changed_setting = True
                    print("Moving to entry {} from {}".format(self.current_font, old_font))
                elif cev.key == pygame.K_RIGHT:
                    # select a different font
                    old_font = self.current_font
                    right_col = self.FONT_TABLE_ROWS * (self.FONT_TABLE_COLUMNS-1)
                    while ((right_col + self.current_font_page*self.fonts_per_page) >=
                           len(self.fonts)):
                        right_col -= self.FONT_TABLE_ROWS
                    if (self.current_font % self.fonts_per_page) >= right_col:
                        # move to leftmost column from rightmost
                        self.current_font -= right_col
                    else:
                        if self.current_font < (len(self.fonts) - self.FONT_TABLE_ROWS):
                            # move one columnt to the right
                            self.current_font += self.FONT_TABLE_ROWS
                    self.changed_setting = True
                    print("Moving to entry {} from {}".format(self.current_font, old_font))
                elif cev.key == pygame.K_UP:
                    # select a different font
                    old_font = self.current_font
                    if (self.current_font % self.FONT_TABLE_ROWS) == 0:
                        # switch to the previous font page when moving up from top row
                        if self.current_font_page > 0:
                            self.current_font_page -= 1
                            self.current_font -= ((self.FONT_TABLE_ROWS *
                                                   (self.FONT_TABLE_COLUMNS-1)) + 1)
                            print("Moving to font page {}".format(self.current_font_page))
                    else:
                        if self.current_font > 0:
                            # move up one row
                            self.current_font -= 1
                    self.changed_setting = True
                    print("Moving to entry {} from {}".format(self.current_font, old_font))
                elif cev.key == pygame.K_DOWN:
                    # select a different font
                    old_font = self.current_font
                    if (self.current_font % self.FONT_TABLE_ROWS) == (self.FONT_TABLE_ROWS-1):
                        # switch to the next font page when moving down from bottom row
                        if self.current_font_page < (self.font_pages-1):
                            self.current_font_page += 1
                            next_font_idx = (self.current_font +
                                             ((self.FONT_TABLE_ROWS *
                                               (self.FONT_TABLE_COLUMNS-1)) + 1))
                            if next_font_idx > (len(self.fonts) - 1):
                                self.current_font = len(self.fonts) - 1
                            else:
                                self.current_font = next_font_idx
                            print("Moving to font page {}".format(self.current_font_page))
                    else:
                        if self.current_font < (len(self.fonts) - 1):
                            # move down one row
                            self.current_font += 1
                    self.changed_setting = True
                    print("Moving to entry {} from {}".format(self.current_font, old_font))
                elif cev.key == pygame.K_MINUS:
                    # select the next smallest font size, down to minimum size
                    if self.current_size > self.MIN_FONT_SIZE:
                        self.current_size -= 1
                        self.changed_setting = True
                elif cev.key == pygame.K_EQUALS:
                    # select the next largest font size, up to maximum size
                    if self.current_size < self.MAX_FONT_SIZE:
                        self.current_size += 1
                        self.changed_setting = True
                elif cev.key == pygame.K_b:
                    # toggle bold
                    self.bold = not self.bold
                    self.changed_setting = True
                elif cev.key == pygame.K_i:
                    # toggle italic
                    self.italic = not self.italic
                    self.changed_setting = True
                elif cev.key == pygame.K_u:
                    # toggle underline
                    self.underline = not self.underline
                    self.changed_setting = True
                elif cev.key == pygame.K_a:
                    # toggle antialiasing
                    self.antialias = not self.antialias
                elif cev.key == pygame.K_COMMA:
                    # cycle through colors in reverse order
                    if self.current_color > 0:
                        self.current_color -= 1
                    else:
                        self.current_color = len(self.COLOR_LIST) - 1
                elif cev.key == pygame.K_PERIOD:
                    # cycle through colors in order
                    if self.current_color < (len(self.COLOR_LIST) - 1):
                        self.current_color += 1
                    else:
                        self.current_color = 0
        # done with event handling
        self.current_events = []

    def draw_text(self):
        """Render file contents to the screen."""
        line_index = self.LINES_PER_PAGE * self.current_page
        current_font = self.fonts[self.current_font]
        page_text = "".join(self.textlines[line_index:line_index+self.LINES_PER_PAGE])
        current_font.fontsize = self.current_size
        current_font.line_spacing = self.line_spacing
        current_font.bold = self.bold
        current_font.italic = self.italic
        current_font.underline = self.underline
        current_font.antialias = self.antialias
        fnt_renderer = current_font.get_font_renderer()
        if self.changed_setting:
            self.text_dims = fnt_renderer.calc_render_size(page_text)
            print("Text page dims: {}x{}".format(self.text_dims[0], self.text_dims[1]))
            self.changed_setting = False
        fnt_renderer.render_text(self.screen, coord.Coordinate(self.TEXT_INDENT, self.TEXT_TOP),
                                 page_text, self.COLOR_LIST[self.current_color])
        text_rect = pygame.Rect(self.TEXT_INDENT, self.TEXT_TOP, self.text_dims[0],
                                self.text_dims[1])
        pygame.draw.rect(self.screen, self.SYSTEM_FONT_COLOR.color, text_rect, 1)

    def draw_font_table(self):
        """Render a page's worth of font names into the font table area."""
        current_font = self.fonts[self.current_font]
        font_table_idx = self.fonts_per_page * self.current_font_page
        font_table_entries = self.fonts[font_table_idx:font_table_idx+self.fonts_per_page]
        table_x = self.FONT_TABLE_LEFT
        table_y = self.FONT_TABLE_TOP
        sys_renderer = self.system_font.get_font_renderer()
        line_height = sys_renderer.get_linesize()
        for col in range(self.FONT_TABLE_COLUMNS):
            for row in range(self.FONT_TABLE_ROWS):
                entry_idx = col*self.FONT_TABLE_ROWS + row
                if entry_idx > (len(font_table_entries) - 1):
                    break
                font_text = font_table_entries[entry_idx].fontname
                text_coord = coord.Coordinate(table_x + col*self.FONT_TABLE_COLUMN_WIDTH,
                                              table_y + row*line_height)
                font_color = self.FONT_TABLE_FG_COLOR
                if font_text == current_font.fontname:
                    font_color = self.FONT_TABLE_ACTIVE_FG_COLOR
                sys_renderer.render_text(self.screen, text_coord, font_text, font_color)
            if entry_idx > (len(font_table_entries) - 1):
                break
        file_font_renderer = self.file_font.get_font_renderer()
        page_indicator_text = "(page {} of {})".format(self.current_font_page+1, self.font_pages)
        indicator_width, indicator_height = file_font_renderer.calc_render_size(page_indicator_text)
        indic_left = (SCREEN_WIDTH / 2) - (indicator_width / 2)
        file_font_renderer.render_text(self.screen,
                                       coord.Coordinate(indic_left, self.FONT_PAGE_TOP),
                                       page_indicator_text, self.FONT_TABLE_ACTIVE_FG_COLOR)

    def draw_objects(self):
        """Handle draw_objects callback from PygameTemplate."""
        current_font = self.fonts[self.current_font]
        # draw the font name at the top center, using the system font
        sys_renderer = self.system_font.get_font_renderer()
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
        self.draw_font_table()
        # draw the current page of text using the current settings
        self.draw_text()

    def draw_background(self):
        """Handle draw_background callback from PygameTemplate."""
        self.screen.fill((0, 0, 0)) # grey background color

    def final_pass(self):
        """Handle final_pass callback from PygameTemplate."""
        pass

    def is_done(self):
        """Handle is_done callback from PygameTemplate."""
        return self.done


MYMANAGER = MyGameManager()
MYGAME = pg_template.PygameTemplate((SCREEN_WIDTH, SCREEN_HEIGHT), "Font Tests", MYMANAGER, 5)
MYGAME.run()

