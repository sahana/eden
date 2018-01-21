"""
    EdenTest Runner

    Usage :
    [1] To run all generic tests
    python web2py.py --no-banner -M -S eden -R applications/eden/tests/edentest.py -A applications/eden/tests/implementation/testsuites
    python web2py.py --no-banner -M -S eden -R applications/eden/tests/edentest.py

    [2] To run a specific generic testsuite (e.g. project)
    python web2py.py --no-banner -M -S eden -R applications/eden/tests/edentest.py -A applications/eden/tests/implementation/testsuites/project
    python web2py.py --no-banner -M -S eden -R applications/eden/tests/edentest.py -A project

    [3] To run a template test suite (e.g. DRKCM template, Subfolder "test")
    python web2py.py --no-banner -M -S eden -R applications/eden/tests/edentest.py -A template:DRKCM test

    For more usage and other features, run
    help : python web2py.py --no-banner -M -S eden  -R applications/eden/tests/edentest_runner.py -A --help

    NOTE :
    [a] -s --suite is disabled. Give the path of the testsuite directly instead.
    [b] giving multiple testsuites as arguments is disabled
    [c] your testsuite must be present inside either
        - eden/tests/implementation/testsuites
        - a subfolder of the template's folder
"""
from sys import argv
import os
import sys

try:
    from robot import run_cli
except:
    sys.stderr.write("ERROR: Robot Framework is not installed\n")
    exit(1)

from robot.api import logger

TESTHOME = os.path.dirname(argv[0])
testsuites_path = os.path.join(TESTHOME, "implementation/testsuites/")

# If no argument given, run the whole testsuite
if len(argv) == 1:
    logger.warn("Running the whole testsuite")
    argv.append(testsuites_path)
    run_cli(argv[1:])
    exit(0)

# If "-s" or "--suite" given as arguments, exit
if set.intersection(set(["-s", "--suite"]), set(argv)):
    logger.warn("-s/--suite command line argument is disabled." \
                " Please give the direct path to the testsuite")
    exit(1)

# Determine run_cli arguments
args = []
isopt = False
suitename = ""
for i in xrange(1, len(argv)):

    arg = argv[i]

    if arg[:1] == "-" or arg[:2] == "--":
        args.append(arg)
        isopt = True

    elif isopt:
        args.append(arg)
        isopt = False

    elif arg[:9] == "template:":
        template = arg[9:]
        testsuites_path = "%s/../modules/templates/%s" % (TESTHOME, template)

    else:
        # is test suite name
        suitename = arg

if suitename:
    common = os.path.commonprefix([testsuites_path, suitename])
else:
    common = None
if common:
    suite = suitename.split(common)[1]
else:
    suite = suitename

if suite:
    args.append("-s")
    args.append(suite)
args.append(testsuites_path)

run_cli(args)
