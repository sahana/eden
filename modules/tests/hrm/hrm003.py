# Set up Training Course
__all__ = ["hrm003"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *
import unittest, re, time

def hrm003():
    
    config = current.test_config
    browser = config.browser
    driver = browser
    
    driver.find_element_by_link_text("Staff & Volunteers").click()
    driver.find_element_by_link_text("New Training Course").click()
    driver.find_element_by_id("hrm_course_name").click()
    driver.find_element_by_id("hrm_course_name").clear()
    driver.find_element_by_id("hrm_course_name").send_keys("Emergency First Aid")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_link_text("Home").click()
    s3_debug("hrm003 test: Pass")