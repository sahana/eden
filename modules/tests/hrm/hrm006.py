# Assign Staff to office
__all__ = ["hrm006"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *
import unittest, re, time

def hrm006():

    config = current.test_config
    browser = config.browser
    driver = browser

    driver.find_element_by_xpath("//div[@id='facility_box']/a[4]/div").click()
    driver.find_element_by_xpath("(//a[contains(text(),'Open')])[3]").click()
    driver.find_element_by_link_text("Staff").click()
    driver.find_element_by_id("select_from_registry").click()
    driver.find_element_by_id("dummy_hrm_human_resource_person_id").clear()
    w_autocomplete("Corn","hrm_human_resource_person","Cornelio  da Cunha",False)
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_css_selector("span.S3menulogo").click()
    driver.find_element_by_link_text("Home").click()

    s3_debug("hrm006 test: Pass")