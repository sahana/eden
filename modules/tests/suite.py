# This script is designed to be run as a Web2Py application:
# python web2py.py -S eden -M -R applications/eden/modules/tests/suite.py
# or
# python web2py.py -S eden -M -R applications/eden/modules/tests/suite.py -A testscript

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
    login(account="admin")
    globals()[test]()
    
else:
    # Log into admin testing account
    login(account="admin")
    
    # List of individual automated test scripts which Suite will run one by one:
    # Organization Management (ORG) tests
    org001() # Set up Organizations
    org002() # Set up Offices
    
    # Human Resources Management (HRM) tests
    hrm001() # Set up Staff
    hrm002() # Set up New Volunteer
    hrm003() # Set up Training Course
    
    # Inventory management (INV) tests
    inv001() # Set up Warehouses
    inv002() # Set up Items
    inv003() # Set up Catalogues
    inv004() # Set up Categories
    inv005() # Create Requests // needs more refining
    inv006() # Match Requests // needs more refining
    
    # Assets management (ASSET) tests
    asset001() # Set up Assets
    
    # Log out of testing account
    logout() #
    
    # Cleanup 
    browser.close()
