__all__ = ["login", "logout", "register"]

# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from .utils import *

# -----------------------------------------------------------------------------
def login(account="normal", nexturl=None):
    """ Login to the system """

    config = current.test_config
    browser = config.browser

    if isinstance(account,(list,tuple)):
        email = account[0]
        password = account[1]
    if account == "normal":
        email = "test@example.com"
        password = "eden"
    elif account == "admin":
        email = "admin@example.com"
        password = "testing"
    elif isinstance(account, (tuple,list)) and len(account) == 2:
        email = account[0]
        password = account[1]
    else:
        raise NotImplementedError

    # If the user is already logged in no need to do anything so return
    if browser.page_source.find("<a id=\"auth_menu_email\">%s</a>" % email) > 0:
        # if the url is different then move to the new url
        if not browser.current_url.endswith(nexturl):
            url = "%s/%s" % (config.url, nexturl)
            browser.get(url)
        return

    if nexturl:
        url = "%s/default/user/login?_next=%s" % (config.url, nexturl)
    else:
        url = "%s/default/user/login" % config.url
    browser.get(url)


    # Login
    elem = browser.find_element_by_id("auth_user_email")
    elem.send_keys(email)
    elem = browser.find_element_by_id("auth_user_password")
    elem.send_keys(password)
    elem = browser.find_element_by_xpath("//input[contains(@value,'Login')]")
    elem.click()

    # Check the result
    try:
        elem = browser.find_element_by_xpath("//div[@class='confirmation']")
    except NoSuchElementException:
        s3_debug("Login failed.. so registering account")
        # Try registering
        register(account)
    else:
        s3_debug(elem.text)
        return True
        
# -----------------------------------------------------------------------------
def logout():
    """ Logout """

    config = current.test_config
    browser = config.browser

    url = "%s/default/user/login" % config.url
    browser.get(url)

    browser.find_element_by_id("auth_menu_email").click()

    try:
        elem = browser.find_element_by_id("auth_menu_logout")
    except NoSuchElementException:
        s3_debug("Logged-out already")
        return True

    elem.click()

    # Check the result
    try:
        elem = browser.find_element_by_xpath("//div[@class='confirmation']")
    except NoSuchElementException:
        assert 0, "Logout unsuccesful"
    else:
        s3_debug(elem.text)
        return True

# -----------------------------------------------------------------------------
def register(account="normal"):
    """ Register on the system """

    config = current.test_config
    browser = config.browser

    # Load homepage
    homepage()

    if account == "normal":
        first_name = "Test"
        last_name = "User"
        email = "test@example.com"
    elif account == "admin":
        first_name = "Admin"
        last_name = "User"
        email = "admin@example.com"
    else:
        raise NotImplementedError
    password = "eden"

    # Register user
    elem = browser.find_element_by_id("auth_user_first_name")
    elem.send_keys(first_name)
    elem = browser.find_element_by_id("auth_user_last_name")
    elem.send_keys(last_name)
    elem = browser.find_element_by_id("auth_user_email")
    elem.send_keys(email)
    elem = browser.find_element_by_id("auth_user_password")
    elem.send_keys(password)
    elem = browser.find_element_by_id("auth_user_password_two")
    elem.send_keys(password)
    elem = browser.find_element_by_xpath("//input[contains(@value,'Register')]")
    elem.click()

    # Check the result
    try:
        elem = browser.find_element_by_xpath("//div[@class='confirmation']")
    except NoSuchElementException:
        assert 0, "Registration unsuccesful"
    else:
        s3_debug(elem.text)
        return True

# END =========================================================================