__all__ = ["staff"]

# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys

from gluon import current

from s3 import s3_debug

from tests import *

# -----------------------------------------------------------------------------
def staff():
    """ Tests for Staff """

    config = current.test_config
    browser = config.browser

    # Logout
    logout()

    # Open HRM module
    url = "%s/hrm" % config.url
    browser.get(url)

    # Check no unauthenticated access
    try:
        elem = browser.find_element_by_xpath("//div[@class='error']")
    except NoSuchElementException:
        if "Staff" in browser.title:
            assert 0, "HRM accessible to unauthenticated users!"
        else:
            raise RuntimeError
    else:
        s3_debug(elem.text)

    # Login
    login()

    # Open HRM module
    browser.get(url)

    # Check authenticated access
    if "Staff" not in browser.title:
        assert 0, "HRM inaccessible to authenticated user!"

    # Create a Staff member
    _create()

# -----------------------------------------------------------------------------
def _create():
    """ Create a Staff member """

    config = current.test_config
    browser = config.browser

    # Login
    login()
    
    # Open Create form
    url = "%s/hrm/human_resource/create?group=staff" % config.url
    browser.get(url)

    # Check authenticated access
    try:
        elem = browser.find_element_by_xpath("//div[@class='error']")
    except NoSuchElementException:
        # ok, continue
        pass
    else:
        #assert 0, elem.text
        assert 0, "Insufficient Privileges"

    # Fill in sample data
    # @ToDo

# END =========================================================================
