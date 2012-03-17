#!/usr/bin/python

# The above line probably works for many people, but if not, 
# check your python executable is correct. 

# This script assumes it is in <app>/tests/ as nose.py
# and that there is a run.py sibling.

import sys

from os import system, getcwd, sep, chdir
from os.path import join, normpath, abspath, dirname, pardir as parent_directory, isabs

chdir(dirname(abspath(__file__)))

application_name = normpath(abspath(getcwd())).split(sep)[-1]

script_path = sys.argv[1]
if not isabs(script_path):
    web2py_script_path = join("applications", application_name, script_path)
else:
    web2py_script_path = script_path

command = " ".join(
    [
        sys.executable, # i.e. whatever python executable this is
        join(
            parent_directory, parent_directory, 
            "web2py.py"
        ),
        "--shell=" + application_name,
        "--import_models",
        "--no-banner",
        "--no-cron",
        
        "--run ", web2py_script_path,
        "--args"
    ] + map("\"%s\"".__mod__, sys.argv[2:])
)

#print command

sys.exit(system(command))
