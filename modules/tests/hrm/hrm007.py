# Assign Staff to Warehouse
__all__ = ["hrm007"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *
import unittest, re, time

def hrm007():

    config = current.test_config
    browser = config.browser
    driver = browser

    driver.find_element_by_link_text("Warehouse").click()
    driver.find_element_by_link_text("List All").click()
    driver.find_element_by_link_text("Open").click()
    driver.find_element_by_link_text("Staff").click()
    driver.find_element_by_id("select_from_registry").click()
    w_autocomplete("Fel","hrm_human_resource_person","Felix  Ximenes",False)
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_css_selector("span.S3menulogo").click()
    driver.find_element_by_link_text("Home").click()

    s3_debug("hrm007 test: Pass")