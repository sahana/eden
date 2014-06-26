# -*- coding: utf-8 -*-

from robot.libraries.OperatingSystem import OperatingSystem
import ast
from robot.api import logger
import os

class edentest_robot:

    def __init__(self, web2py, eden_path):
        logger.debug("Got arguments %s %s" % (web2py, eden_path), html=True)
        self.web2py = web2py
        self.eden_path = eden_path

    def get_deployment_settings(self, *asked):
        """
            Takes the required settings as arguments eg: Template  Base Public Url
            Returns a list of values if len(list) > 1 else returns the first value as a
            string.
            Raises a warning if a setting is not found.
        """
        self._setcwd()

        logger.info("Getting values for -  %s" % " ".join(asked), html=True)
        cmd = "python " + self.web2py + " --no-banner -S eden -M -R " + self.eden_path +"/tests/execution/libs/eden_interface.py -A -S"

        for key in asked:
            cmd = cmd + " " + key

        rc, output = OperatingSystem().run_and_return_rc_and_output(cmd)

        logger.debug("Return code for the cmd %s is %d" % (cmd, rc))
        logger.info("Returned Settings %s" % output)

        self._resetcwd()

        output = ast.literal_eval(output)

        for key in asked:
            if key not in output.keys():
                logger.warn("Could not fetch the setting %s" % key)

        return output

    def _setcwd(self):
        """
            Sets the CWD to the root of eden
        """
        self._oldcwd = os.getcwd()
        self._newcwd = self._oldcwd.split("/eden/")[0] + "/eden/"
        os.chdir(self._newcwd)

    def _resetcwd(self):
        """
            Resets the CWD to the directory from which tests were run
        """
        os.chdir(self._oldcwd)
