# Set up Assets
__all__ = ["asset001"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *
import unittest, re, time

def asset001():
    
    config = current.test_config
    browser = config.browser
    driver = browser
    
    driver.find_element_by_xpath("//div[@id='menu_div_sit']/a[3]/div").click()
    driver.find_element_by_link_text("New").click()
    driver.find_element_by_id("asset_asset_number").click()
    driver.find_element_by_id("asset_asset_number").clear()
    driver.find_element_by_id("asset_asset_number").send_keys("WS-100-17")
    w_autocomplete("Wat","asset_asset_item","Water Purification Unit",False)
    driver.find_element_by_id("asset_asset_sn").clear()
    driver.find_element_by_id("asset_asset_sn").send_keys("WPU-4536-9381")
    driver.find_element_by_id("asset_asset_comments").clear()
    driver.find_element_by_id("asset_asset_comments").send_keys("test")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_link_text("Home").click()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    