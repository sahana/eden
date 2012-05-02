# Set up Training Event
__all__ = ["hrm004"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *
import unittest, re, time

def hrm004():

    config = current.test_config
    browser = config.browser
    driver = browser
    driver.find_element_by_link_text("Staff & Volunteers").click()
    driver.find_element_by_link_text("New Training Event").click()
    driver.find_element_by_id("hrm_training_event_course_id").send_keys("Emergency First Aid")
    w_autocomplete("buch","hrm_training_event_site","Bucharest RFAAT Centre (Test) (Office)",False)
    driver.find_element_by_id("hrm_training_event_start_date").send_keys("2012-04-11")
    driver.find_element_by_id("hrm_training_event_end_date").send_keys("2012-04-12")
    driver.find_element_by_id("hrm_training_event_hours").send_keys("16")
    driver.find_element_by_id("hrm_training_event_comments").clear()
    driver.find_element_by_id("hrm_training_event_comments").send_keys("test")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    w_autocomplete("Rob","hrm_training_person","Robert James Lemon",False)
    driver.find_element_by_id("hrm_training_comments").send_keys("test")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_link_text("Home").click()
    
    s3_debug("hrm004 test: Pass")