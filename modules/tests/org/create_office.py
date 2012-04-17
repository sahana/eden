__all__ = ["create_office"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *

def create_office():

    config = current.test_config
    browser = config.browser
    driver = browser
    driver.find_element_by_xpath("//div[@id='facility_box']/a[4]/div").click()
    driver.find_element_by_id("show-add-btn").click()
    driver.find_element_by_id("org_office_name").clear()
    driver.find_element_by_id("org_office_name").send_keys("Bucharest RFAAT Centre (Test)")
    driver.find_element_by_id("org_office_code").clear()
    driver.find_element_by_id("org_office_code").send_keys("12345678")
    driver.find_element_by_id("dummy_org_office_organisation_id").clear()
    driver.find_element_by_id("dummy_org_office_organisation_id").send_keys("Romanian Food Assistance Association (Test) (RFAAT)")
    driver.find_element_by_id("org_office_type").click()
    driver.find_element_by_id("org_office_type").send_keys("Headquarters")
    driver.find_element_by_id("gis_location_L0").send_keys("Romania")
    driver.find_element_by_id("gis_location_street").clear()
    driver.find_element_by_id("gis_location_street").send_keys("102 Diminescu St")
    driver.find_element_by_id("gis_location_L3_ac").clear()
    driver.find_element_by_id("gis_location_L3_ac").send_keys("Bucharest")
    driver.find_element_by_id("org_office_comments").click()
    driver.find_element_by_id("org_office_comments").clear()
    driver.find_element_by_id("org_office_comments").send_keys("This is a Test Office")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
#
#    # Logout
#    logout()