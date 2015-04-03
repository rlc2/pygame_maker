#!/usr/bin/python -Wall

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

# implement pygame_maker sounds

import pygame
import os.path
import yaml

class PyGameMakerSoundException(Exception):
    pass

class PyGameMakerSound(object):
    """
        Implement simple sound effects or background music loaded from
        sound files.
    """
    SOUND_TYPES=[
        "effect",
        "music",
        "voice"
    ]
    @classmethod
    def load_sound(cls, sound_yaml_file):
        """
            Create a new sound from a YAML-formatted file
            sound_yaml_file: name of the file
            Check each key against known PyGameMakerSound parameters, and use
            only those parameters to initalize a new sound.
            Returns:
                o None, if the yaml-formatted sound is invalid
                o a new sound, if the YAML fields pass basic checks
        """

    def __init__(self, sound_name=None, **kwargs):
        self.sound_name = sound_name
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
        if self.sound_file and self.preload:
            self.load_file()

    def load_file(self):
        if not os.path.exists(self.sound_file):
            raise PyGameMakerSoundException("PyGameMakerSoundException: Sound file '{}' not found.".format(self.sound_file))
        if not self.loaded:
            self.audio = pygame.mixer.Sound(file=self.sound_file)
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
        ystr = "sound_name: {}\n".format(self.sound_name)
        if self.sound_file:
            ystr += "sound_file: {}\n".format(self.sound_file)
        ystr += "sound_type: {}\n".format(self.sound_type)
        ystr += "preload: {}\n".format(self.preload)
        return(ystr)

if __name__ == "__main__":
    import unittest
    import tempfile
    import os
    import time

    class TestPyGameMakerSound(unittest.TestCase):

        def setUp(self):
            self.sound_test_file = "unittest_files/Pop.wav"
            self.valid_sound_yaml = "sound_name: yaml_sound\nsound_file: {}\nsound_type: music\npreload: False\n".format(self.sound_test_file)
            self.valid_sound_object = PyGameMakerSound("yaml_sound",
                sound_file=self.sound_test_file, sound_type="music",
                preload=False)

        def test_005valid_sound(self):
            sound1 = PyGameMakerSound("sound1")
            self.assertEqual(sound1.sound_name, "sound1")

        def test_010sound_parameters(self):
            pygame.init()
            music1 = PyGameMakerSound("music1", sound_type="music")
            self.assertEqual(music1.sound_type, "music")
            sound_with_file = PyGameMakerSound("dontpanic",
                sound_file=self.sound_test_file)
            sound_with_file.play_sound()
            self.assertTrue(sound_with_file.is_sound_playing())
            time.sleep(2)
            self.assertFalse(sound_with_file.is_sound_playing())
            self.assertEqual(sound_with_file.sound_file, self.sound_test_file)

        def test_015missing_sound_file(self):
            with self.assertRaises(PyGameMakerSoundException):
                missing_music1 = PyGameMakerSound("missing1",
                    sound_type="music", sound_file="unittest/missing1.wav")
            missing_sound1 = PyGameMakerSound("missing2",
                preload=False, sound_file="unittest/missing2.wav")
            with self.assertRaises(PyGameMakerSoundException):
                missing_sound1.play_sound()

        def test_020sound_to_yaml(self):
            self.assertEqual(self.valid_sound_object.to_yaml(),
                self.valid_sound_yaml)

    unittest.main()

