# Set up Organizations
__all__ = ["org001"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *

# -----------------------------------------------------------------------------

def org001():

    config = current.test_config
    browser = config.browser
    driver = browser
    driver.find_element_by_link_text("Organizations").click()
    driver.find_element_by_link_text("New").click()
    driver.find_element_by_id("org_organisation_name").click()
    driver.find_element_by_id("org_organisation_name").clear()
    driver.find_element_by_id("org_organisation_name").send_keys("Romanian Food Assistance Association (Test)")
    driver.find_element_by_id("org_organisation_acronym").clear()
    driver.find_element_by_id("org_organisation_acronym").send_keys("RFAAT")
    driver.find_element_by_id("org_organisation_type").send_keys("Institution")
    driver.find_element_by_id("org_organisation_region").clear()
    driver.find_element_by_id("org_organisation_region").send_keys("???")
    driver.find_element_by_id("org_organisation_country").send_keys("Romania")
    driver.find_element_by_id("org_organisation_website").clear()
    driver.find_element_by_id("org_organisation_website").send_keys("www.rfaat.com")
    driver.find_element_by_id("org_organisation_comments").clear()
    driver.find_element_by_id("org_organisation_comments").send_keys("This is a Test Organization")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_link_text("Home").click()

#    # Logout
#    logout()


