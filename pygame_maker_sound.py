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
    DEFAULT_SOUND_PREFIX="snd_"

    @staticmethod
    def load_from_yaml(sound_yaml_file, unused=None):
        """
            Create a new sound from a YAML-formatted file
            sound_yaml_file: name of the file
            Check each key against known PyGameMakerSound parameters, and use
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
        sound_name = PyGameMakerSound.DEFAULT_SOUND_PREFIX
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
                    new_sound_list.append(PyGameMakerSound(sound_name,
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
        if self.sound_file and self.preload:
            self.load_file()

    def load_file(self):
        if not os.path.exists(self.sound_file):
            raise PyGameMakerSoundException("PyGameMakerSoundException: Sound file '{}' not found.".format(self.sound_file))
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
            raise PyGameMakerSoundException("PyGameMakerSound: Unknown sound type '{}'".format(self.sound_type))
        return True

    def check(self):
        return self.check_type()

    def __eq__(self, other):
        return(isinstance(other, PyGameMakerSound) and
            (self.name == other.name) and
            (self.sound_file == other.sound_file) and
            (self.sound_type == other.sound_type) and
            (self.preload == other.preload))

if __name__ == "__main__":
    import unittest
    import tempfile
    import os
    import time

    class TestPyGameMakerSound(unittest.TestCase):

        def setUp(self):
            self.sound_test_file = "unittest_files/Pop.wav"
            self.valid_sound_yaml = "- yaml_sound:\n    sound_file: {}\n    sound_type: music\n    preload: False\n".format(self.sound_test_file)
            self.valid_sound_object = PyGameMakerSound("yaml_sound",
                sound_file=self.sound_test_file, sound_type="music",
                preload=False)

        def test_005valid_sound(self):
            sound1 = PyGameMakerSound("sound1")
            self.assertEqual(sound1.name, "sound1")

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

        def test_025yaml_to_sound(self):
            tmpf_info = tempfile.mkstemp(dir="/tmp")
            tmp_file = os.fdopen(tmpf_info[0], 'w')
            tmp_file.write(self.valid_sound_yaml)
            tmp_file.close()
            loaded_sound1 = PyGameMakerSound.load_from_yaml(tmpf_info[1])[0]
            os.unlink(tmpf_info[1])
            self.assertEqual(self.valid_sound_object, loaded_sound1)

        def test_030to_and_from_yaml(self):
            generated_sound_yaml = self.valid_sound_object.to_yaml()
            tmpf_info = tempfile.mkstemp(dir="/tmp")
            tmp_file = os.fdopen(tmpf_info[0], 'w')
            tmp_file.write(generated_sound_yaml)
            tmp_file.close()
            loaded_sound1 = PyGameMakerSound.load_from_yaml(tmpf_info[1])[0]
            os.unlink(tmpf_info[1])
            self.assertEqual(self.valid_sound_object, loaded_sound1)

    unittest.main()

