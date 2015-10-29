#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# implement sound resources

import pygame
import os.path
import yaml

class SoundException(Exception):
    pass

class Sound(object):
    """
        Implement simple sound effects or background music loaded from
        sound files.
    """
    SOUND_TYPES=[
        "effect",
        "music",
        "voice"
    ]
    DEFAULT_SOUND_PREFIX="snd_"

    @staticmethod
    def load_from_yaml(sound_yaml_file, unused=None):
        """
            Create a new sound from a YAML-formatted file
            sound_yaml_file: name of the file
            Check each key against known Sound parameters, and use
            only those parameters to initalize a new sound.
            Returns:
                o None, if the yaml-formatted sound is invalid
                o a new sound, if the YAML fields pass basic checks
            
            Expected YAML format:
            - sound_name1:
                sound_file: <sound_file_path>
                sound_type: <type>
                preload: true|false
            - sound_name2:
                ...
        """
        yaml_info = None
        sound_name = Sound.DEFAULT_SOUND_PREFIX
        new_sound_list = []
        if os.path.exists(sound_yaml_file):
            with open(sound_yaml_file, "r") as yaml_f:
                yaml_info = yaml.load(yaml_f)
            if yaml_info:
                for top_level in yaml_info:
                    sound_args = {}
                    sound_name = top_level.keys()[0]
                    yaml_info_hash = top_level[sound_name]
                    if 'sound_file' in yaml_info_hash.keys():
                        sound_args['sound_file'] = yaml_info_hash['sound_file']
                    if 'sound_type' in yaml_info_hash.keys():
                        sound_args['sound_type'] = yaml_info_hash['sound_type']
                    if 'preload' in yaml_info_hash.keys():
                        sound_args['preload'] = yaml_info_hash['preload']
                    new_sound_list.append(Sound(sound_name,
                        **sound_args))
                    new_sound_list[-1].check()
        return new_sound_list

    def __init__(self, sound_name=None, **kwargs):
        if sound_name:
            self.name = sound_name
        else:
            self.name = self.DEFAULT_SOUND_PREFIX
        self.sound_file = None
        self.sound_type = "effect"
        self.preload = True
        self.loaded = False
        self.audio = None
        self.channel = None
        if "sound_file" in kwargs:
            self.sound_file = kwargs["sound_file"]
        if (("sound_type" in kwargs) and
            (kwargs["sound_type"] in self.SOUND_TYPES)):
            self.sound_type = kwargs["sound_type"]
        if "preload" in kwargs:
            self.preload = (kwargs["preload"] == True) # convert to boolean

    def setup(self):
        """
            setup():
            Preload the sound if preload is set. Must be done after
             pygame.init().
        """
        if self.sound_file and self.preload:
            self.load_file()

    def load_file(self):
        if not os.path.exists(self.sound_file):
            raise SoundException("SoundException: Sound file '{}' not found.".format(self.sound_file))
        if not self.loaded:
            self.audio = pygame.mixer.Sound(self.sound_file)
            self.loaded = True

    def play_sound(self, loop=False):
        if not self.loaded:
            self.load_file()
        play_loops = 0
        if loop:
            play_loops = -1
        self.channel = self.audio.play(loops=play_loops)

    def stop_sound(self):
        self.audio.stop()

    def is_sound_playing(self):
        playing_sound = self.channel.get_sound()
        return (playing_sound == self.audio)

    def to_yaml(self):
        ystr = "- {}:\n".format(self.name)
        if self.sound_file:
            ystr += "    sound_file: {}\n".format(self.sound_file)
        ystr += "    sound_type: {}\n".format(self.sound_type)
        ystr += "    preload: {}\n".format(self.preload)
        return(ystr)

    def check_type(self):
        if not self.sound_type in self.SOUND_TYPES:
            raise SoundException("Sound: Unknown sound type '{}'".format(self.sound_type))
        return True

    def check(self):
        return self.check_type()

    def __eq__(self, other):
        return(isinstance(other, Sound) and
            (self.name == other.name) and
            (self.sound_file == other.sound_file) and
            (self.sound_type == other.sound_type) and
            (self.preload == other.preload))

