# Set up Categories
__all__ = ["inv004"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *
import unittest, re, time

def inv004():
    
    config = current.test_config
    browser = config.browser
    driver = browser
    
    driver.find_element_by_link_text("Warehouse").click()
    driver.find_element_by_link_text("New Item Category").click()
    driver.find_element_by_id("supply_item_category_parent_item_category_id").click()
    driver.find_element_by_id("supply_item_category_parent_item_category_id").send_keys("Vehicle")
    driver.find_element_by_id("supply_item_category_code").clear()
    driver.find_element_by_id("supply_item_category_code").send_keys("123")
    driver.find_element_by_id("supply_item_category_name").clear()
    driver.find_element_by_id("supply_item_category_name").send_keys("Large Items")
    driver.find_element_by_id("supply_item_category_comments").clear()
    driver.find_element_by_id("supply_item_category_comments").send_keys("This is a Test Item Category")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_link_text("Home").click()
    