#!/usr/bin/python -Wall

# base class for objects that need logging

import logging

class Indented(object):
    def __init__(self, logger):
        self.logger = logger

    def __enter__(self):
        self.logger.log_indent += self.logger.indent_size

    def __exit__(self, type, value, traceback):
        self.logger.log_indent -= self.logger.indent_size

class PyGameMakerLoggingException(Exception):
    def __init__(self, msg, logger=None):
        if logger:
            logger(msg)
        self.msg = msg

class PyGameMakerLoggingObject(object):

    def __init__(self, logger_name=""):
      self.logger_name = logger_name
      self.log_indent = 0
      self.logger = logging.getLogger(self.logger_name)
      self.indent_size = 2

    def bump_indent_level(self):
        self.log_indent += self.indent_size

    def drop_indent_level(self):
        if self.log_indent >= self.indent_size:
            self.log_indent -= self.indent_size

    def get_format_string(self, message):
        name_field = ""
        if hasattr(self, 'name'):
            name_field = " [{}]".format(self.name)
        format_string = "{}{}{}".format(" "*self.log_indent, message,
            name_field)
        return(format_string)

    def debug(self, message):
        self.logger.debug(self.get_format_string(message))

    def info(self, message):
        self.logger.info(self.get_format_string(message))

    def warn(self, message):
        self.logger.warn(self.get_format_string(message))

    def error(self, message):
        self.logger.error(self.get_format_string(message))

    def critical(self, message):
        self.logger.critical(self.get_format_string(message))

