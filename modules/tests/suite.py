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
import unittest, re, time
from gluon import current
from gluon.storage import Storage
import sys
# S3 Tests
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
    globals()[test]()

else:
    # Run all Tests

    # Log into admin testing account
    login(account="admin")
    
    suite = unittest.TestLoader().loadTestsFromTestCase(org_create_organization)  # run test org_create_organization.py
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(org_create_office)) # run test org_create_office.py
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(hrm_setup_staff)) # run test hrm_setup_staff.py
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(hrm_setup_volunteer)) # run test hrm_setup_volunteer.py
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(hrm_setup_trainingcourse)) # run test hrm_setup_trainingcourse.py
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(hrm_setup_trainingevent)) # run test hrm_setup_trainingevent.py
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(hrm_assign_organizationstaff)) # run test hrm_assign_organizationstaff.py
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(hrm_assign_officestaff)) # run test hrm_assign_officestaff.py
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(hrm_assign_warehousestaff)) # run test hrm_assign_warehousestaff.py
    unittest.TextTestRunner(verbosity=2).run(suite)

  

    # Log out of testing account
    logout() 
   
    # Cleanup 
    browser.close()
