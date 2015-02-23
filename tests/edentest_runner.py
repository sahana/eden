"""
    EdenTest Runner
    Usage :
    [1] To run the whole testsuite
    python web2py.py --no-banner -M -S eden  -R applications/eden/tests/edentest_runner.py -A applications/eden/tests/implementation/testsuites
    python web2py.py --no-banner -M -S eden  -R applications/eden/tests/edentest_runner.py

    [2] To run a testsuite eg: project
    python web2py.py --no-banner -M -S eden  -R applications/eden/tests/edentest_runner.py -A applications/eden/tests/implementation/testsuites/project
    python web2py.py --no-banner -M -S eden  -R applications/eden/tests/edentest_runner.py -A project

    For more usage and other features, run
    help : python web2py.py --no-banner -M -S eden  -R applications/eden/tests/edentest_runner.py -A --help

    NOTE :
    [1] -s --suite is disabled. Give the path of the testsuite directly instead.
    [2] giving multiple testsuites as arguments is disabled
    [3] your testsuite must be present inside eden/tests/implementation/testsuites
"""
from sys import argv
import os

try:
    from robot import run_cli
except:
    print >> sys.stderr, "Robot Framework is not installed"
    exit(1)

from robot.api import logger

testsuites_path = "%s/%s" % (os.path.dirname(argv[0]), "implementation/testsuites/")

# if no argument given, run the whole testsuite
if len(argv) == 1:
    logger.warn("Running the whole testsuite")
    argv.append(testsuites_path)
    run_cli(argv[1:])
    exit(0)

# if "-s" or "--suite" given as arguments, exit
if set.intersection(set(["-s", "--suite"]), set(argv)):
    logger.warn("-s/--suite command line argument is disabled. Please give the\
     direct path to the testsuite")
    exit(1)

# find the index where the path to the testsuite is given
position = None
for i in xrange(len(argv[1:])):
    arg = argv[i]

    if arg[:1] != "-" and arg[:2] != "--":
        if i == 0:
            position = 1
            break
        else:
            arg_before = argv[i-1]
            if arg_before[:1] != "-" and arg_before[:2] != "--":
                position = i
                break

common = os.path.commonprefix([testsuites_path, argv[position]])

child_suite = None

if common:
    # get the name of the child test suite
    child_suite = argv[position].split(common)[1]

if child_suite:
    # run the child_testsuite with -s argument
    argv[position] = child_suite

argv = argv[:position] + ["-s"] + argv[position:]
argv.append(testsuites_path)

run_cli(argv[1:])
