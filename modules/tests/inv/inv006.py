# Match Requests // needs more refining
__all__ = ["inv006"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *
import unittest, re, time

def inv006():

    config = current.test_config
    browser = config.browser
    driver = browser
    url = "http://127.0.0.1:8000/eden/default/user/login"
    browser.get(url)
    
    driver.find_element_by_link_text("Warehouse").click()
    driver.find_element_by_link_text("List All").click()
    driver.find_element_by_xpath("(//a[contains(text(),'Open')])[3]").click()
    driver.find_element_by_link_text("Match Requests").click()
    driver.find_element_by_xpath("(//a[contains(text(),'Commit')])[3]").click()
    driver.find_element_by_id("req_commit_item_req_item_id").click()
    driver.find_element_by_id("req_commit_item_req_item_id").send_keys("Soup")
    driver.find_element_by_id("req_commit_item_quantity").clear()
    driver.find_element_by_id("req_commit_item_quantity").send_keys("1000")
    time.sleep(5)
    driver.find_element_by_id("req_commit_item_comments").clear()
    driver.find_element_by_id("req_commit_item_comments").send_keys("test")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_id("prepare_commit").click()
    driver.find_element_by_link_text("Open").click()
    driver.find_element_by_id("inv_track_item_send_inv_item_id").click()
    driver.find_element_by_id("inv_track_item_send_inv_item_id").send_keys("Rice")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_id("send_process").click()
    driver.find_element_by_link_text("Home").click()
    
    
