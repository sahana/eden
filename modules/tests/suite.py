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
current.deployment_settings.ui.navigate_away_confirm = False
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
config.base_dir = base_dir

test = None
remote = None
# Do we have any command-line arguments?
args = sys.argv
if args[1:]:
    # The 1st argument is taken to be the test name:
    test = args[1]
    if args[2:]:
        # The 2nd argument is taken to be a remote server:
        # @ToDo:
        #  Need to change this so can do remote for whole suite (normal case)
        #  - convert to proper params
        remote = args[2]

if remote:
    # @ToDo
    browser = config.browser = webdriver.Remote()
else:
    fp = webdriver.FirefoxProfile()
    fp.set_preference("network.proxy.type", 0)
    browser = config.browser = webdriver.Firefox(firefox_profile=fp)

browser.implicitly_wait(config.timeout)

# Shortcut
loadTests = unittest.TestLoader().loadTestsFromTestCase

if test:
    # Run specified Test after logging in
    # @ToDo: Each test should check whether it needs to login independently as they may wish to login using different credentials
    # Maybe this could be bypassed for a test run within the suite by passing it an argument

    print test
    suite = loadTests(globals()[test])

else:
    # Run all Tests

    # Create Organisation
    suite = loadTests(CreateOrganisation)
    
    # Shortcut
    addTests = suite.addTests
    
    # Create Office
    addTests(loadTests(CreateOffice))
    
    # Setup Staff
    addTests(loadTests(CreateStaff))
    
    # Setup New Volunteer
    addTests(loadTests(CreateVolunteer))
    
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
    addTests(loadTests(DeleteOrganisation))

try:
    import HTMLTestRunner
    fp = file("Sahana-Eden-Test-Result.html", "wb")
    runner = HTMLTestRunner.HTMLTestRunner(
                                           stream=fp,
                                           title="Sahana Eden Test Result",
                                          )
    runner.run(suite)
except:
    unittest.TextTestRunner(verbosity=2).run(suite)

# Cleanup
browser.close()

# END =========================================================================
