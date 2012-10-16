__all__ = ["login",
           "logout",
           "register"
           ]

from selenium.common.exceptions import NoSuchElementException

from gluon import current
from gluon.storage import Storage

from .core_utils import *

current.data = Storage()
current.data["auth"] = {
        "normal" : {
                "email": "test@example.com",
                "password": "eden",
                "first_name": "Test",
                "last_name": "User",
            },
        "admin" : {
                "email": "admin@example.com",
                "password": "testing",
                "first_name": "Admin",
                "last_name": "User",
            },
    }

# -----------------------------------------------------------------------------
def login(reporter, account="normal", nexturl=None):
    """ Login to the system """

    config = current.test_config
    browser = config.browser
    data = current.data["auth"]

    if account in data:
        email = data[account]["email"]
        password = data[account]["password"]
    elif isinstance(account, (tuple, list)):
        email = account[0]
        password = account[1]
    else:
        raise NotImplementedError

    # If the user is already logged in no need to do anything so return
    # auth_menu_email is used by the default template
    # username fright is used by the IFRC template 
    if browser.page_source != None and \
       (browser.page_source.find("<a id=\"auth_menu_email\">%s</a>" % email) > 0 or
        browser.page_source.find("<div class=\"username fright\">%s</div>" % email) > 0):
        # If the URL is different then move to the new URL
        if not browser.current_url.endswith(nexturl):
            url = "%s/%s" % (config.url, nexturl)
            browser.get(url)
        return

    if nexturl:
        url = "%s/default/user/login?_next=/%s/%s" % \
            (config.url, current.request.application, nexturl)
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
        reporter("Login failed.. so registering account")
        # Try registering
        register(account, reporter)
    else:
        reporter(elem.text)
        return True

# -----------------------------------------------------------------------------
def logout(reporter):
    """ Logout """

    config = current.test_config
    browser = config.browser

    url = "%s/default/user/login" % config.url
    browser.get(url)

    browser.find_element_by_id("auth_menu_email").click()

    try:
        elem = browser.find_element_by_id("auth_menu_logout")
    except NoSuchElementException:
        reporter("Logged-out already")
        return True

    elem.click()

    # Check the result
    try:
        elem = browser.find_element_by_xpath("//div[@class='confirmation']")
    except NoSuchElementException:
        assert 0, "Logout unsuccesful"
    else:
        reporter(elem.text)
        return True

# -----------------------------------------------------------------------------
def register(reporter, account="normal"):
    """ Register on the system """

    config = current.test_config
    browser = config.browser
    data = current.data["auth"]

    if account in data:
        email = data[account]["email"]
        first_name = data[account]["first_name"]
        last_name = data[account]["last_name"]
        password = data[account]["password"]
    else:
        raise NotImplementedError

    # Load homepage
    homepage()

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
        reporter(elem.text)
        return True

# END =========================================================================
