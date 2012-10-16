# This script is designed to be run as a Web2Py application:
# python web2py.py -S eden -M -R applications/eden/modules/tests/suite.py
# or
# python web2py.py -S eden -M -R applications/eden/modules/tests/suite.py -A testscript

import argparse
import unittest

from gluon import current
from gluon.storage import Storage

current.data = Storage()

# @ToDo: Load these only when running Selenium tests
# (shouldn't be required for Smoke tests)
# (means removing the *)
from selenium import webdriver
from tests.asset import *
from tests.hrm import *
from tests.inv import *
from tests.member import *
from tests.org import *
from tests.project import *
from tests.staff import *
from tests.volunteer import *

def loadAllTests():

    # Create Organisation
    loadTests = unittest.TestLoader().loadTestsFromTestCase
    suite = loadTests(CreateOrganisation)

    # Shortcut
    addTests = suite.addTests

    # Create Office
    addTests(loadTests(CreateOffice))

    # Setup Staff
    addTests(loadTests(CreateStaff))
    addTests(loadTests(CreateStaffJobRole))
    addTests(loadTests(CreateStaffCertificate))

    # Setup Volunteer
    addTests(loadTests(CreateVolunteer))
    addTests(loadTests(CreateVolunteerJobRole))
    addTests(loadTests(CreateVolunteerProgramme))
    addTests(loadTests(CreateVolunteerSkill))
    addTests(loadTests(CreateVolunteerCertificate))

    # Create Staff & Volunteer Training
    addTests(loadTests(CreateStaffTraining))
    addTests(loadTests(CreateVolunteerTraining))

    # Inventory tests
    addTests(loadTests(SendItem))
    addTests(loadTests(ReceiveItem))
    addTests(loadTests(SendReceiveItem))

    # Project Tests
    addTests(loadTests(CreateProject))

    # Asset Tests
    addTests(loadTests(CreateAsset))

    # Assign Staff to Organisation
    addTests(loadTests(AddStaffToOrganisation))

    # Assign Staff to Office
    addTests(loadTests(AddStaffToOffice))

    # Assign Staff to Warehouse
    addTests(loadTests(AddStaffToWarehouse))
    # Delete a prepop organisation
    #addTests(loadTests(DeleteOrganisation))

    # Create a Warehouse
    addTests(loadTests(CreateWarehouse))

    # Create an Item
    addTests(loadTests(CreateItem))

    # Create a Catalog
    addTests(loadTests(CreateCatalog))

    # Create a Category
    addTests(loadTests(CreateCategory))

    # Create Members
    addTests(loadTests(CreateMember))

    # Search Staff (Simple & Advanced)
    #addTests(loadTests(SearchStaff))
    return suite

# Set up the command line arguments
desc = "Script to run the Sahana Eden test suite."
parser = argparse.ArgumentParser(description = desc)
parser.add_argument("-C", "--class",
                    help = "Name of class to run")

method_desc = """Name of method to run, this is used in conjunction with the
class argument or with the name of the class followed by the name of the method
separated with a period, class.method.
"""

parser.add_argument("-M",
                    "--method",
                    "--test",
                    help = method_desc)
parser.add_argument("-A",
                    "--auth",
                    help = "web2py default argument feed")
parser.add_argument("-V", "--verbose",
                    type = int,
                    default = 1,
                    help = "The level of verbose reporting")
parser.add_argument("--nohtml",
                    action='store_const',
                    const=True,
                    help = "Disable HTML reporting.")
parser.add_argument("--html-path",
                    help = "Path where the HTML report will be saved.",
                    default = "")
parser.add_argument("--html-name-date",
                    action='store_const',
                    const=True,
                    help = "Include just the date in the name of the HTML report.")

suite_desc = """This will execute a standard testing schedule. The valid values
are, smoke, quick, complete and full. If a method or class options is selected
the the suite will be ignored.

The suite options can be described as follows:

smoke: This will run the broken link test
quick: This will run all the tests marked as essential
complete: This will run all tests except those marked as long
full: This will run all test
"""
parser.add_argument("--suite",
                    help = suite_desc,
                    choices = ["smoke", "roles", "quick", "complete", "full"],
                    default = "quick")
parser.add_argument("--link-depth",
                    type = int,
                    default = 16,
                    help = "The recursive depth when looking for links")

up_desc = """The user name and password, separated by a /. Multiple user name
and passwords can be added by separating them with a comma. If multiple user
name and passwords are provided then the same test will be run sequentially
using the given user in each case.
"""
parser.add_argument("--user-password",
                    default = "admin@example.com/testing",
                    help = up_desc)
parser.add_argument("--keep-browser-open",
                    help = "Keep the browser open once the tests have finished running",
                    action='store_const',
                    const = True)

desc = """Run the smoke tests even if debug is set to true.

With debug on it can add up to a second per link and given that a full run
of the smoke tests will include thousands of links the difference of having
this setting one can be measured in hours.
"""
parser.add_argument("--force-debug",
                    action='store_const',
                    const=True,
                    help = desc)
desc = """Set a threshold in seconds.
If takes longer than this to get the link then it will be reported.
"""
parser.add_argument("--threshold",
                    type = int,
                    default = 10,
                    help = desc)
argsObj = parser.parse_args()
args = argsObj.__dict__

# Read Settings
settings = current.deployment_settings
public_url = settings.get_base_public_url()
base_url = "%s/%s" % (public_url, current.request.application)
system_name = settings.get_system_name()

# Store these to be available to modules
config = current.test_config = Storage()
config.system_name = system_name
config.timeout = 5 # seconds
config.url = base_url

base_dir = os.path.join(os.getcwd(), "applications", current.request.application)
test_dir = os.path.join(base_dir, "modules", "tests")
config.base_dir = base_dir

if not args["suite"] == "smoke" and settings.get_ui_navigate_away_confirm():
    print "The tests will fail unless you have settings.ui.navigate_away_confirm = False in models/000_config.py"
    exit()
if args["suite"] == "smoke" or args["suite"] == "complete":
    if settings.get_base_debug() and not args["force_debug"]:
        print "settings.base.debug is set to True in 000_config.py, either set it to False or use the --force-debug switch"
        exit()

config.verbose = args["verbose"]
browser_open = False
# @todo test with invalid class and methods passed as CLA
if args["method"]:
    browser = config.browser = webdriver.Firefox()
    browser.implicitly_wait(config.timeout)
    browser_open = True
    if args["class"]:
        name = "%s.%s" % (args["class"], args["method"])
    else:
        name = args["method"]
    suite = unittest.TestLoader().loadTestsFromName(args["method"],
                                                    globals()[args["class"]]
                                                    )
elif args["class"]:
    browser = config.browser = webdriver.Firefox()
    browser.implicitly_wait(config.timeout)
    browser_open = True
    suite = unittest.TestLoader().loadTestsFromTestCase(globals()[args["class"]])

elif args["suite"] == "smoke":
    try:
        from tests.smoke import *
        broken_links = BrokenLinkTest()
        broken_links.setDepth(args["link_depth"])
        broken_links.threshold = args["threshold"]
        broken_links.setUser(args["user_password"])
        suite = unittest.TestSuite()
        suite.addTest(broken_links)
    except NameError as msg:
        from s3 import s3_debug
        s3_debug("%s, unable to run the smoke tests." % msg)
        pass

elif args["suite"] == "roles":

    from tests.roles.test_roles import *
    #suite = unittest.TestSuite()
    suite = test_roles()

    #test_role = TestRole()
    #test_role.set(org = "Org-A",
    #              user = "asset_reader@Org-A.com",
    #              row_num = 0,
    #                     method = "create",
    #                     table = "org_organisation",
    #                     c = None,
    #                     f = None,
    #                     record_id = 42,
    #                     uuid = "uuid",
    #                     permission = True)
    #suite.addTest(test_role)
    #suite = unittest.TestLoader().loadTestsFromTestCase(globals()[args["auth"]])

elif args["suite"] == "complete":
    browser = config.browser = webdriver.Firefox()
    browser.implicitly_wait(config.timeout)
    browser_open = True
    suite = loadAllTests()
    try:
        from tests.smoke import *
        broken_links = BrokenLinkTest()
        broken_links.setDepth(args["link_depth"])
        broken_links.threshold = args["threshold"]
        broken_links.setUser(args["user_password"])
        suite.addTest(broken_links)
    except NameError as msg:
        from s3 import s3_debug
        s3_debug("%s, unable to run the smoke tests." % msg)
        pass

else:
    # Run all Tests
    browser = config.browser = webdriver.Firefox()
    browser.implicitly_wait(config.timeout)
    browser_open = True
    suite = loadAllTests()

config.html = False
if args["nohtml"]:
    unittest.TextTestRunner(verbosity=config.verbose).run(suite)
else:
    try:
        path = args["html_path"]
        if args["html_name_date"]:
            filename = "Sahana-Eden-%s.html" % current.request.now.date()
        else:
            filename = "Sahana-Eden-%s.html" % current.request.now
        # Windows compatibility
        filename = filename.replace(":", "-")
        fullname = os.path.join(path,filename)
        fp = open(fullname, "wb")

        config.html = True
        from tests.runner import EdenHTMLTestRunner
        runner = EdenHTMLTestRunner(stream = fp,
                                    title = "Sahana Eden",
                                    verbosity = config.verbose,
                                    )
        runner.run(suite)
    except ImportError:
        config.html = False
        unittest.TextTestRunner(verbosity=config.verbose).run(suite)

# Cleanup
if browser_open and not args["keep_browser_open"]:
    browser.close()

# END =========================================================================
