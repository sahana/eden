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

# S3 Tests
from tests.web2unittest import *
from tests import *

# Read Settings
settings = current.deployment_settings
public_url = settings.get_base_public_url()
base_url = "%s/%s" % (public_url, request.application)
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

if test:
    # Run specified Test after logging in
    # @ToDo: Each test should check whether it needs to login independently as they may wish to login using different credentials
    # Maybe this could be bypassed for a test run within the suite by passing it an argument
#    login(account="admin")
#    globals()[test]()
    print test
    suite = unittest.TestLoader().loadTestsFromTestCase(globals()[test])
    unittest.TextTestRunner(verbosity=2).run(suite)

else:
    # Run all Tests
    # Log into admin testing account
#    login(account="admin")

    suite = unittest.TestLoader().loadTestsFromTestCase(Logistics)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(Org001))
    unittest.TextTestRunner(verbosity=2).run(suite)
#    inventory()
    # List of individual automated test scripts which Suite will run one by one:
    # Organization Management (ORG) tests
#    org001() # Setup Organizations
    org002() # Setup Offices
    
    # Human Resources Management (HRM) tests
    hrm001() # Setup Staff
    hrm002() # Setup New Volunteer
    hrm003() # Setup Training Course
    hrm004() # Setup Training Event
    hrm005() # Assign staff to Organization
    hrm006() # Assign Staff to office
    hrm007() # Assign staff to warehouse
    
    # Inventory management (INV) tests
    inv001() # Setup Warehouses     // needs more refining
    inv002() # Setup Items        // needs more refining
    inv003() # Setup Catalogues // needs more refining
    inv004() # Setup Categories // needs more refining
    inv005() # Create Requests // needs more refining
    inv006() # Match Requests // needs more refining
    
    # Assets management (ASSET) tests
    asset001() # Set up Assets
    
    # Log out of testing account
    logout() #
    
    # Cleanup 
    browser.close()
