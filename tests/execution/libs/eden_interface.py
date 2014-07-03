# -*- coding: utf-8 -*-

# This script is designed to be run as a Web2Py application:
# python web2py.py -S eden -M -R applications/eden/tests/execution/libs/eden_interface.py

import argparse
import __builtin__

from gluon import current

settings = current.deployment_settings

# Set up the command line arguments
desc = "Interface to Eden for EdenTest"
parser = argparse.ArgumentParser(description = desc)
parser.add_argument("-S", "--asked_settings", nargs="+", metavar="return deployment settings")
argsObj = parser.parse_args()
args = argsObj.__dict__


if args["asked_settings"]:
    return_settings = {}

    for item in args["asked_settings"]:
        func_name = "get_" + item
        try:
            function = getattr(settings, func_name)
            # eg value of function - settings.get_template()
            value = function()
            return_settings[item] = value
        except:
            # Not catching the error because that is done in the edentest_robot file
            continue

    print return_settings
