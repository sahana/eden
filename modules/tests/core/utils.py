__all__ = ["homepage"]

# Selenium WebDriver
from selenium import webdriver
#from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys

from gluon import current

# -----------------------------------------------------------------------------
def homepage():
    """ Load the homepage """

    config = current.test_config
    browser = config.browser
    system_name = str(config.system_name)
    if system_name not in browser.title:
        browser.get(config.url)
        assert system_name in browser.title

    return True

# END =========================================================================