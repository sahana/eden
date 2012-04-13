# Set up Items
__all__ = ["inv002"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *
import unittest, re, time



def inv002():
    
    config = current.test_config
    browser = config.browser
    driver = browser
    driver.find_element_by_link_text("Assets").click()
    driver.find_element_by_xpath("(//a[contains(text(),'New')])[2]").click()
    driver.find_element_by_id("supply_item_name").click()
    driver.find_element_by_id("supply_item_name").clear()
    driver.find_element_by_id("supply_item_name").send_keys("Soup")
    driver.find_element_by_id("supply_item_um").clear()
    driver.find_element_by_id("supply_item_um").send_keys("litre")
    driver.find_element_by_id("supply_item_year").clear()
    driver.find_element_by_id("supply_item_model").clear()
    driver.find_element_by_id("supply_item_model").send_keys("Tomato")
    driver.find_element_by_id("supply_item_comments").clear()
    driver.find_element_by_id("supply_item_comments").send_keys("This is a Test Item")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_link_text("Home").click()
    
    
    