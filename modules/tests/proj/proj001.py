# Set up Training Course
__all__ = ["proj001"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *
import unittest, re, time

def proj001():
    config = current.test_config
    browser = config.browser
    driver = browser

    # driver.find_element_by_xpath("//a[@href='/eden/project/index']").click()
    # driver.find_element_by_xpath("//a[@href='/eden/project/project/create']").click()

    #homepage()
    login()

    driver.find_element_by_link_text("Projects").click()
    driver.find_element_by_link_text("Add New Project").click()
    driver.find_element_by_name("name").click()
    # driver.find_element_by_id("hrm_course_name").clear()
    driver.find_element_by_name("name").send_keys("My Test Project")
    driver.find_element_by_name("name").submit()
    # driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    # driver.find_element_by_link_text("Home").click()
    s3_debug("proj001 test: Pass")