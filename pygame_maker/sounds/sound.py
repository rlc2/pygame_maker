"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

implement sound resources
"""

import os.path
import pygame
import yaml


class SoundException(Exception):
    """Raised for invalid sound file names or unknown sound types."""
    pass


class Sound(object):
    """
    Implement simple sound effects or background music loaded from sound files.
    """
    #: The available sound types
    SOUND_TYPES = [
        "effect",
        "music",
        "voice"
    ]
    DEFAULT_SOUND_PREFIX = "snd_"

    @staticmethod
    def load_from_yaml(yaml_stream, unused=None):
        """
        Create a new sound from a YAML-formatted file.  Expected YAML format::

            - sound_name1:
                filename: <sound_file_path>
                sound_type: <type>
                preload: true|false
            - sound_name2:
                ...

        Check each key against known Sound parameters, and use only those
        parameters to initalize a new sound.

        :param yaml_stream: A stream containing YAML-formatted text
        :type yaml_stream: file-like
        :param unused: This is a placeholder, since other load_from_yaml()
            resource methods take an additional argument
        :return: A list of new sound instances, one for each listed in the
            YAML stream that pass basic checks; if none are found, returns an
            empty list
        :rtype: list
        """
        new_sound_list = []
        yaml_info = yaml.load(yaml_stream)
        if yaml_info:
            for top_level in yaml_info:
                sound_args = {}
                sound_name = list(top_level.keys())[0]
                yaml_info_hash = top_level[sound_name]
                if 'filename' in list(yaml_info_hash.keys()):
                    sound_args['filename'] = yaml_info_hash['filename']
                if 'sound_type' in list(yaml_info_hash.keys()):
                    sound_args['sound_type'] = yaml_info_hash['sound_type']
                if 'preload' in list(yaml_info_hash.keys()):
                    sound_args['preload'] = yaml_info_hash['preload']
                new_sound_list.append(Sound(sound_name, **sound_args))
                new_sound_list[-1].check()
        return new_sound_list

    def __init__(self, sound_name=None, **kwargs):
        """
        Initialize a new Sound instance.

        :param sound_name: The name this sound will be referenced by in other
            resources
        :type sound_name: str
        :param kwargs: Sound options passed in keyword args.  The following
            options are available:

            * ``filename`` (str): The path to a file containing the audio
              data
            * ``sound_type`` (str): The type of sound this is, see
              :py:attr:`SOUND_TYPES`
            * ``preload`` (bool): True if the sound should be loaded before
              the game loop begins

        :return:
        """
        #: Set the name this sound resource will be known by
        self.name = None
        if sound_name:
            self.name = sound_name
        else:
            self.name = self.DEFAULT_SOUND_PREFIX
        #: The file name containing the audio data
        self.filename = None
        #: A string selecting the kind of sound file this is (effect or music)
        self.sound_type = "effect"
        #: Flag whether to pre-load the audio data in setup() or wait until
        #: used
        self.preload = True
        #: Flag set when the audio data has been read from the file
        self.loaded = False
        #: The `pygame.mixer.Sound` object created when the file is loaded
        self.audio = None
        #: The `pygame.mixer.Channel` returned when the audio is played
        self.channel = None
        if "filename" in kwargs:
            self.filename = kwargs["filename"]
        if (("sound_type" in kwargs) and
                (kwargs["sound_type"] in self.SOUND_TYPES)):
            self.sound_type = kwargs["sound_type"]
        if "preload" in kwargs:
            self.preload = (kwargs["preload"] is True)  # convert to boolean

    def setup(self):
        """
        Preload the sound if preload is set.  Must be done after
        ``pygame.init().``
        """
        if self.filename and self.preload:
            self.load_file()

    def load_file(self):
        """
        Load the audio data from the file, if it exists.

        :raise: SoundException if the file is not found
        """
        if not self.loaded:
            if self.filename is None:
                raise SoundException("SoundException: No sound filename provided.")
            if not os.path.exists(self.filename):
                raise SoundException("SoundException: Sound file '{}' not found.".format(
                    self.filename))
            self.audio = pygame.mixer.Sound(self.filename)
            self.loaded = True

    def play_sound(self, loop=False):
        """
        Play the sound.  Load it first if it wasn't already loaded.

        :param loop: Loop this sound until stopped using :py:meth:`stop_sound`
        """
        if not self.loaded:
            self.load_file()
        play_loops = 0
        if loop:
            play_loops = -1
        self.channel = self.audio.play(loops=play_loops)

    def stop_sound(self):
        """Stop the sound from playing."""
        self.audio.stop()

    def is_sound_playing(self):
        """
        Answer whether the sound is currently playing.

        :return: True if the sound is playing
        :rtype: bool
        """
        playing_sound = self.channel.get_sound()
        return playing_sound == self.audio

    def to_yaml(self):
        """
        Generate the YAML string describing this Sound instance.

        :return: The YAML-formatted string
        :rtype: str
        """
        ystr = "- {}:\n".format(self.name)
        if self.filename:
            ystr += "    filename: {}\n".format(self.filename)
        ystr += "    sound_type: {}\n".format(self.sound_type)
        ystr += "    preload: {}\n".format(str(self.preload))
        return ystr

    def check_type(self):
        """
        Error-check the ``sound_type`` attribute.

        :raise: SoundException if the type string is unrecognized
        :return: True if the sound type is known
        """
        if self.sound_type not in self.SOUND_TYPES:
            raise SoundException("Sound: Unknown sound type '{}'".format(self.sound_type))
        return True

    def check(self):
        """
        Run error-checking on this sound resource.

        :return: The results from the error check, True if OK
        :rtype: bool
        """
        return self.check_type()

    def __eq__(self, other):
        return(isinstance(other, Sound) and
               (self.name == other.name) and
               (self.filename == other.filename) and
               (self.sound_type == other.sound_type) and
               (self.preload == other.preload))
