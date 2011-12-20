#!python

# capture web2py environment before doing anything else

web2py_environment = dict(globals())

__doc__ = """This script is run from the nose command in the 
application being tested:

e.g. 

python2.6 ./applications/eden/tests/nose.py <nose arguments>

web2py runs a file which:
1. Sets up a plugin. This plugin registers itself so nose can use it.
2. Runs nose programmatically giving it the plugin
nose loads the tests via the plugin. 
when the plugin loads the tests, it injects the web2py environment.

"""

import sys

from types import ModuleType
import nose
import glob
import os.path
import os
import copy
from gluon.globals import Request
import unittest


def load_module(application_relative_module_path):
    import os
    web2py_relative_module_path = ".".join((
        "applications", request.application, application_relative_module_path
    ))
    imported_module = __import__(web2py_relative_module_path)
    for step in web2py_relative_module_path.split(".")[1:]:
        imported_module = getattr(imported_module, step)
    return imported_module

web2py_environment["load_module"] = load_module
web2py_env_module = ModuleType("web2py_env")
web2py_env_module.__dict__.update(web2py_environment)
sys.modules["web2py_env"] = web2py_env_module


application_name = request.application
application_folder_path = os.path.join("applications",application_name)

application = application_name
controller = "controller"
function = "function"
folder = os.path.join(os.getcwd(), "applications", application_name)

web2py_environment["Request"] = Request
request = Request()
request.application = application
request.controller = controller
request.function = function
request.folder = folder

web2py_environment["request"] = request
current.request = request

controller_configuration = OrderedDict()
for controller_name in ["default"]+glob.glob(
    os.path.join(application_folder_path, "controllers", "*.py")
):
    controller_configuration[controller_name] = Storage(
        name_nice = controller_name,
        description = controller_name,
        restricted = False,
        module_type = 0
    )
    
current.deployment_settings.modules = controller_configuration

test_folders = set()
argv = []

# folder in which tests are kept
# non-option arguments (test paths) are made relative to this
test_root = os.path.join(application_folder_path, "tests", "unit_tests")

current_working_directory = os.getcwd()

disallowed_options = {}
disallowed_options["-w"] = disallowed_options["--where"] = (
    "web2py does not allow changing directory"
)
for arg in sys.argv[1:]:
    if arg.startswith("-"):
        if not arg.startswith("--"):
            print (
                "\nSorry, please use verbose option names "
                "(currently need this to distinguish options from paths)"
            )
            sys.exit(1)
        else:
            try:
                reason = disallowed_options[arg]
            except KeyError:
                pass
            else:
                print "\nSorry, %s option is not accepted as %s" % (arg, reason)
                sys.exit(1)
            argv.append(arg)
    else:
        test_path = arg
        test_folder_fuller_path = os.path.join(test_root, test_path)
        test_folders.add(test_folder_fuller_path)
        if not os.path.exists(test_folder_fuller_path):
            print "\n", test_folder_fuller_path, "not found"
            #sys.exit(1)

# test paths in command line aren't passed, just added to test_folders
# the plugin does the testing
# nose just searches everything from the test_root
# so we give it the test root
argv.append(test_root)

# if no test folders are given, assume we test everything from the test_root
if len(test_folders) == 0:
    test_folders.add(test_root)

sys.argv[1:] = argv

test_utils = local_import("test_utils")

nose.main(
# seems at least this version of nose ignores passed in argv
#    argv = argv, 
    addplugins = nose.plugins.PluginManager([
        test_utils.Web2pyNosePlugin(
            application_name,
            web2py_environment,
            re.compile(
                re.escape(os.path.sep).join(
                    (
                        "web2py(?:",
                        "applications(?:",
                        application_name+"(?:",
                        "tests(?:",
                        "[^","]*)*)?)?)?$"
                    )
                )
            ),
            test_folders
        )
    ])
)
