# This script is designed to be run as a Web2Py application:
# python web2py.py -S eden -M -R applications/eden/modules/tests/suite.py
# or
# python web2py.py -S eden -M -R applications/eden/modules/tests/suite.py -A testscript

import sys
import re
import time
import unittest

# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from gluon import current
from gluon.storage import Storage

current.data = Storage()

# S3 Tests
from tests.web2unittest import *
from tests import *

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

browser = config.browser = webdriver.Firefox()
browser.implicitly_wait(config.timeout)

# Do we have any command-line arguments?
args = sys.argv
if args[1:]:
    # The 1st argument is taken to be the test name:
    test = args[1]
else:
    test = None

# Shortcut
loadTests = unittest.TestLoader().loadTestsFromTestCase

if test:
    # Run specified Test after logging in
    # @ToDo: Each test should check whether it needs to login independently as they may wish to login using different credentials
    # Maybe this could be bypassed for a test run within the suite by passing it an argument
    
    #login(account="admin")
    print test
    suite = loadTests(globals()[test])

else:
    # Run all Tests

    # Create Organisation
    suite = loadTests(org_create_organisation)
    # Shortcut
    addTests = suite.addTests
    # Create Office
    addTests(loadTests(org_create_office))
    # Setup Staff
    addTests(loadTests(hrm_setup_staff))
    # Setup New Volunteer
    addTests(loadTests(hrm_setup_volunteer))
    # Setup Training Course
    addTests(loadTests(hrm_setup_trainingcourse))
    # Setup Training Event
    addTests(loadTests(hrm_setup_trainingevent))
    # Inventory tests
    addTests(loadTests(Logistics))
    addTests(loadTests(Logistics2))

    # Assign Staff to Organisation
    #addTests(loadTests(hrm_assign_organisationstaff))
    # Assign Staff to Office
    #addTests(loadTests(hrm_assign_officestaff))
    # Assign Staff to Warehouse
    #addTests(loadTests(hrm_assign_warehousestaff))

try:
    import HTMLTestRunner
    fp = file("Sahana-Eden.html", "wb")
    runner = HTMLTestRunner.HTMLTestRunner(
                                           stream=fp,
                                           title="Sahana Eden",
                                          )
    runner.run(suite)
except:
    unittest.TextTestRunner(verbosity=2).run(suite)

# Cleanup
#browser.close()

# END =========================================================================
