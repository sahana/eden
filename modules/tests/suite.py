# This script is designed to be run as a Web2Py application:
# python web2py.py -S eden -M -R applications/eden/modules/tests/suite.py
# or
# python web2py.py -S eden -M -R applications/eden/modules/tests/suite.py -A testscript

# Selenium WebDriver
from selenium import webdriver

from gluon import current
from gluon.storage import Storage

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
    # Run specified Test
    globals()[test]()
else:
    # Run all Tests
    staff()

# Cleanup
browser.close()
