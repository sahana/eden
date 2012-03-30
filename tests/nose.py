#!/usr/bin/python

# The above line probably works for many people, but if not, 
# check your python executable is correct. 

# This script assumes it is in <app>/tests/ as nose.py
# and that there is a run.py sibling.

import sys

from os import system, getcwd, sep, chdir
from os.path import join, normpath, abspath, dirname, pardir

chdir(dirname(abspath(__file__)))

application_name = normpath(abspath(getcwd())).split(sep)[-2]

command = " ".join(
    [
        sys.executable, # i.e. whatever python executable this is
        join(pardir, pardir, pardir, "web2py.py"),
        "--shell=" + application_name,
        "--import_models",
        "--run " + join(
            # the code that makes all the test folders relative to
            # tests/unit_tests is in modules/test_utils/run.py
            "applications", application_name, "modules", "test_utils", "run.py"
        ),
        "--args"
    ] + sys.argv[1:] # nose arguments
)

# print command

sys.exit(system(command))
