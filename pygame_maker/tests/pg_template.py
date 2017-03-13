#!/usr/bin/python

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

import pygame

class PygameTemplate:
    # define common colors
    BLACK = (  0,  0,  0)
    WHITE = (255,255,255)
    BLUE  = (  0,  0,255)
    GREEN = (  0,255,  0)
    RED   = (255,  0,  0)

    # every game_manager is an object that must support calls to:
    #  setup(screen)
    #  collect_event(event)
    #  update()
    #  draw_background()
    #  draw_objects()
    #  final_pass()
    #  is_done()
    def __init__(self, size_tuple, caption, game_manager, frame_rate=30):

        self.size = size_tuple
        self.caption = caption
        self.game_manager = game_manager
        self.frame_rate = frame_rate
        self.done = False

        # manage speed of screen updates

    def run(self):
        pygame.init()
        self.screen = pygame.display.set_mode(self.size)
        self.game_manager.setup(self.screen)
        pygame.display.set_caption(self.caption)
        self.clock = pygame.time.Clock()

        # --- Main Loop ---
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                self.game_manager.collect_event(event)
        
            # --- Game Logic ---
            self.game_manager.update()
        
            #self.screen.fill(self.WHITE)
            # --- Drawing ---
            self.game_manager.draw_background()
            self.game_manager.draw_objects()
        
            # update screen
            self.game_manager.final_pass()
            pygame.display.flip()
        
            # find out whether the game manager is done
            self.done = self.game_manager.is_done()

            # limit frame rate
            self.clock.tick(self.frame_rate)

        # close window & quit
        pygame.quit()

if __name__ == "__main__":
    class MyGameManager:
        LEFT_MARGIN = 10
        TOP_MARGIN  = 8
        LINE_HEIGHT = 18
        TEXT_COLOR  = (128,   0, 128)
        TEXT_BACKG  = (255, 255, 255)
        def __init__(self):
            self.current_events = []
            self.objects = []
            self.font = None
            self.done = False
        def setup(self, screen):
            self.screen = screen
            self.font = pygame.font.Font(None, 16)
        def collect_event(self, event):
            self.current_events.append(event)
        def create_text(self, a_key):
            text = "You pressed '{}'".format(pygame.key.name(a_key))
            if len(self.objects) > 25:
                # too many text lines, remove oldest object
                self.objects = self.objects[1:]
            self.objects.append( ("text", self.font.render(text, 1, self.TEXT_COLOR, self.TEXT_BACKG)) )
        def update(self):
            for ev in self.current_events:
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.done = True
                        break
                    else:
                        # create a new text object
                        self.create_text(ev.key)
            # done with event handling
            self.current_events = []
        def draw_text(self, textobj, line):
            y = self.TOP_MARGIN + line*self.LINE_HEIGHT
            textpos = (self.LEFT_MARGIN, y)
            self.screen.blit(textobj[1], textpos)
        def draw_objects(self):
            for line, ob in enumerate(self.objects):
                self.draw_text(ob, line)
        def final_pass(self):
            pass
        def draw_background(self):
            self.screen.fill(PygameTemplate.BLACK)
        def is_done(self):
            return self.done

    mymanager = MyGameManager()
    mygame = PygameTemplate( (700,500), "My Game", mymanager)
    mygame.run()

