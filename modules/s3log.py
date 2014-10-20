# -*- coding: utf-8 -*-

""" S3 Logging Facility

    @copyright: (c) 2014 Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

import logging
import sys

from gluon import current

# =============================================================================
class S3Log(object):
    """
        Simple global logging facility, called like:

            current.log.error("Something went wrong", value="Example")

        gives:

            2014-02-16 11:58:41 S3LOG ERROR: Something went wrong: Example

        Configurable in 000_config.py (set up in models/00_db.py)

            - to include caller details (file name, line number, function name):

            2014-02-16 11:58:23 (applications/eden/modules/s3/s3rest.py 477 __init__)
                ERROR: Something went wrong: Example

            - to write to console (sys.stderr), to a log file, or both.

        Configuration see modules/s3cfg.py.
    """

    def __init__(self):
        """
            Constructor
        """

        settings = current.deployment_settings

        log_level = settings.get_log_level()
        if log_level is None:
            self.critical = \
            self.error = \
            self.warning = \
            self.info = \
            self.debug = self.ignore

            self.log_level = 100
        else:
            try:
                level = getattr(logging, log_level.upper())
            except AttributeError:
                raise SyntaxError("Invalid settings.log.level: %s" % log_level)

            self.log_level = level

            self.critical = self._critical \
                            if level <= logging.CRITICAL else self.ignore

            self.error = self._error \
                            if level <= logging.ERROR else self.ignore

            self.warning = self._warning \
                            if level <= logging.WARNING else self.ignore

            self.info = self._info \
                            if level <= logging.INFO else self.ignore

            self.debug = self._debug \
                            if level <= logging.DEBUG else self.ignore

        self.configure_logger()
        
    # -------------------------------------------------------------------------
    @classmethod
    def setup(cls):
        """
            Set up current.log
        """

        if hasattr(current, "log"):
            return
        current.log = cls()
        return
        
    # -------------------------------------------------------------------------
    def configure_logger(self):
        """
            Configure output handlers
        """

        if hasattr(current, "log"):
            return
            
        settings = current.deployment_settings
        console = settings.get_log_console()
        logfile = settings.get_log_logfile()
        if not console and not logfile:
            # No point to log without output channel
            self.critical = \
            self.error = \
            self.warning = \
            self.info = \
            self.debug = self.ignore
            return

        self.name = __name__
        logger = logging.getLogger(__name__)
        logger.propagate = False
        logger.setLevel(self.log_level)
        logger.handlers = []

        m_format = "%(asctime)s %(caller)s %(levelname)s: %(message)s"
        d_format = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(m_format, d_format)

        # Set up console handler       
        if console:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(self.log_level)
            logger.addHandler(console_handler)

        # Set up log file handler
        if logfile:
            from logging.handlers import RotatingFileHandler
            MAXBYTES = 1048576
            logfile_handler = RotatingFileHandler(logfile,
                                                  maxBytes = MAXBYTES,
                                                  backupCount = 3)
            logfile_handler.setFormatter(formatter)
            logfile_handler.setLevel(self.log_level)
            logger.addHandler(logfile_handler)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def ignore(message, value=None):
        """
            Dummy to ignore messages below minimum severity level
        """

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def get_name():
        """
            Provide name to allow access to the logger.
            This may be useful in testing, to capture messages.
        """

        return __name__

    # -------------------------------------------------------------------------
    @staticmethod
    def _log(severity, message, value=None):
        """
            Log a message

            @param severity: the severity of the message
            @param message: the message
            @param value: message suffix (optional)
        """

        logger = logging.getLogger(__name__)
        logger.propagate = False

        msg = "%s: %s" % (message, value) if value else message
        extra = {"caller": "S3LOG"}
        
        if current.deployment_settings.get_log_caller_info():
            caller = logger.findCaller()
            if caller:
                extra = {"caller": "(%s %s %s)" % caller}
                
        logger.log(severity, msg, extra=extra)
        return

    # -------------------------------------------------------------------------
    @classmethod
    def _critical(cls, message, value=None):
        """
            Log a critical message (highest severity level),
            called via current.log.critical()
            
            @param message: the message
            @param value: message suffix (optional)
        """

        cls._log(logging.CRITICAL, message, value=value)
        
    # -------------------------------------------------------------------------
    @classmethod
    def _error(cls, message, value=None):
        """
            Log an error message,
            called via current.log.error()

            @param message: the message
            @param value: message suffix (optional)
        """

        cls._log(logging.ERROR, message, value=value)

    # -------------------------------------------------------------------------
    @classmethod
    def _warning(cls, message, value=None):
        """
            Log a warning message,
            called via current.log.warning()

            @param message: the message
            @param value: message suffix (optional)
        """

        cls._log(logging.WARNING, message, value=value)

    # -------------------------------------------------------------------------
    @classmethod
    def _info(cls, message, value=None):
        """
            Log an general info message,
            called via current.log.info()

            @param message: the message
            @param value: message suffix (optional)
        """

        cls._log(logging.INFO, message, value=value)

    # -------------------------------------------------------------------------
    @classmethod
    def _debug(cls, message, value=None):
        """
            Log a detailed debug message (lowest severity level),
            called via current.log.debug()

            @param message: the message
            @param value: message suffix (optional)
        """

        cls._log(logging.DEBUG, message, value=value)
        
# END =========================================================================
