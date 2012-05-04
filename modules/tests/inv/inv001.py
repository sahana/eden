# Set up Warehouses
__all__ = ["inv001"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *
import unittest, re, time



def inv001():

    config = current.test_config
    browser = config.browser
    driver = browser
    driver.find_element_by_link_text("Warehouse").click()
    driver.find_element_by_link_text("New").click()
    driver.find_element_by_id("org_office_name").click()
    driver.find_element_by_id("org_office_name").clear()
    driver.find_element_by_id("org_office_name").send_keys("Bucharest RFAAT Central Warehouse (Test)")
    driver.find_element_by_id("org_office_code").clear()
    driver.find_element_by_id("org_office_code").send_keys("12345679")
    w_autocomplete("Rom","org_office_organisation","Romanian Food Assistance Association (Test) (RFAAT)",False)
    driver.find_element_by_id("gis_location_L0").click()
    driver.find_element_by_id("gis_location_L0").send_keys("Romania")
    driver.find_element_by_id("gis_location_street").clear()
    driver.find_element_by_id("gis_location_street").send_keys("103 Diminescu St")
    driver.find_element_by_id("org_office_comments").clear()
    driver.find_element_by_id("org_office_comments").send_keys("This is a Test Warehouse")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_link_text("Home").click()