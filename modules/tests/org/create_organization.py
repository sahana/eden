__all__ = ["create_organization"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *

# -----------------------------------------------------------------------------

def create_organization():

    config = current.test_config
    browser = config.browser
    driver = browser
    url = "http://127.0.0.1:8000/eden/default/user/login"
    browser.get(url)
#    driver.find_element_by_id("auth_menu_login").click()
    driver.find_element_by_css_selector("form").click()
    driver.find_element_by_id("auth_user_email").clear()
    driver.find_element_by_id("auth_user_email").send_keys("admin@example.com")
    driver.find_element_by_id("auth_user_password").clear()
    driver.find_element_by_id("auth_user_password").send_keys("testing")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_link_text("Organizations").click()
    driver.find_element_by_link_text("New").click()
    driver.find_element_by_id("org_organisation_name").click()
    driver.find_element_by_id("org_organisation_name").clear()
    driver.find_element_by_id("org_organisation_name").send_keys("Romanian Food Assistance Association (Test)")
    driver.find_element_by_id("org_organisation_acronym").clear()
    driver.find_element_by_id("org_organisation_acronym").send_keys("RFAAT")
    driver.find_element_by_id("org_organisation_type").send_keys("Institution")
    # ERROR: Caught exception [ERROR: Unsupported command [addSelection]]
    driver.find_element_by_id("org_organisation_region").clear()
    driver.find_element_by_id("org_organisation_region").send_keys("???")
    driver.find_element_by_id("org_organisation_country").send_keys("Romania")
    driver.find_element_by_id("org_organisation_website").clear()
    driver.find_element_by_id("org_organisation_website").send_keys("www.rfaat.com")
    driver.find_element_by_id("org_organisation_comments").clear()
    driver.find_element_by_id("org_organisation_comments").send_keys("This is a Test Organization")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()

    # Logout
    logout()


