"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Base class for objects that need logging
"""

import logging


class Indented(object):
    """
    Manage log message indentation inside a ``with .. as`` statement.
    """

    def __init__(self, logger):
        self.logger = logger

    def __enter__(self):
        self.logger.log_indent += self.logger.indent_size

    def __exit__(self, a_type, value, traceback):
        self.logger.log_indent -= self.logger.indent_size


class LoggingException(Exception):
    """Exception base class that can log the exception message."""
    def __init__(self, msg, logger=None):
        super(LoggingException, self).__init__(msg)
        if logger:
            logger(msg)


class LoggingObject(object):
    """
    Base class for objects that provides logging with indentation.

    Log messages will include a suffix [``name``] for any subclass instance
    that has a ``name`` attribute.
    """

    def __init__(self, logger_name=""):
        """
        Initialize logging.

        :param logger_name: The name supplied to getLogger() that can be
            configured from the main application
        :type logger_name: str
        """
        #: The name of this object's logger
        self.logger_name = logger_name
        #: The current indent level
        self.log_indent = 0
        #: The logging object
        self.logger = logging.getLogger(self.logger_name)
        #: The number of spaces to indent by
        self.indent_size = 2

    def bump_indent_level(self):
        """Increase the indentation one level."""
        self.log_indent += self.indent_size

    def drop_indent_level(self):
        """Decrease the indentation one level."""
        if self.log_indent >= self.indent_size:
            self.log_indent -= self.indent_size

    def _get_format_string(self, message):
        name_field = ""
        if hasattr(self, 'name'):
            name_field = " [{}]".format(self.name)
        format_string = "{}{}{}".format(" " * self.log_indent, message,
                                        name_field)
        return format_string

    def debug(self, message):
        """
        Log a debug message, using the current indentation level.

        :param message: Message to be logged
        """
        self.logger.debug(self._get_format_string(message))

    def info(self, message):
        """
        Log an info message, using the current indentation level.

        :param message: Message to be logged
        """
        self.logger.info(self._get_format_string(message))

    def warn(self, message):
        """
        Log a warning message, using the current indentation level.

        :param message: Message to be logged
        """
        self.logger.warning(self._get_format_string(message))

    def error(self, message):
        """
        Log an error message, using the current indentation level.

        :param message: Message to be logged
        """
        self.logger.error(self._get_format_string(message))

    def critical(self, message):
        """
        Log a critical error message, using the current indentation level.

        :param message: Message to be logged
        """
        self.logger.critical(self._get_format_string(message))
