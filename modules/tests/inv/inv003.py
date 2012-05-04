# Set up Catalogues
__all__ = ["inv003"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *
import unittest, re, time

def inv003():
    
    config = current.test_config
    browser = config.browser
    driver = browser
    
    driver.find_element_by_link_text("Warehouse").click()
    driver.find_element_by_xpath("(//a[contains(text(),'New')])[5]").click()
    driver.find_element_by_id("supply_catalog_name").click()
    driver.find_element_by_id("supply_catalog_name").clear()
    driver.find_element_by_id("supply_catalog_name").send_keys("Romanian Food Catalogue")
    w_autocomplete("Rom","supply_catalog_organisation","Romanian Food Assistance Association (Test) (RFAAT)",False)
    driver.find_element_by_id("supply_catalog_comments").clear()
    driver.find_element_by_id("supply_catalog_comments").send_keys("This is a test Catalogue")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_link_text("Home").click()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    