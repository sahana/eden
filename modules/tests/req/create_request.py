__all__ = ["create_request"]
# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *
import unittest, re, time

def create_request():
    
    config = current.test_config
    browser = config.browser
    driver = browser
    
    driver.find_element_by_css_selector("#menu_div_dec > a.menu-btn-l > div.menu-btn-r").click()
    driver.find_element_by_link_text("New").click()
    driver.find_element_by_id("req_req_type").click()
    driver.find_element_by_id("req_req_type").send_keys("Warehouse Stock")
    driver.find_element_by_id("req_req_request_number").clear()
    driver.find_element_by_id("req_req_request_number").send_keys("TestReq1")
    driver.find_element_by_id("req_req_purpose").clear()
    driver.find_element_by_id("req_req_purpose").send_keys("More Stock Required")
    driver.find_element_by_id("req_req_date_required").click()
    driver.find_element_by_id("req_req_date_required").clear()
    driver.find_element_by_id("req_req_date_required").send_keys("2012-08-08")
    driver.find_element_by_id("dummy_req_req_requester_id").click()
    driver.find_element_by_id("dummy_req_req_requester_id").clear()
    w_autocomplete("Beat","req_req_requester","Beatriz de Carvalho",False)
    driver.find_element_by_id("req_req_site_id").send_keys("Same Warehouse (Warehouse)")
    driver.find_element_by_id("req_req_transport_req").click()
    driver.find_element_by_id("req_req_comments").clear()
    driver.find_element_by_id("req_req_comments").send_keys("Test Request")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_link_text("Open").click()
    driver.find_element_by_link_text("Items").click()
    driver.find_element_by_name("item_id_search_simple_simple").click()
    driver.find_element_by_name("item_id_search_simple_simple").clear()
    driver.find_element_by_name("item_id_search_simple_simple").send_keys("Blankets") #test
    time.sleep(5)
    driver.find_element_by_id("req_req_item_quantity").clear()
    driver.find_element_by_id("req_req_item_quantity").send_keys("1000")
    driver.find_element_by_id("req_req_item_pack_value").clear()
    driver.find_element_by_id("req_req_item_pack_value").send_keys("5")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_css_selector("tr.even > td > a.action-btn").click()
    driver.find_element_by_id("show-add-btn").click()
    driver.find_element_by_name("item_id_search_simple_simple").send_keys("Rice") #test
    time.sleep(5)
    driver.find_element_by_id("req_req_item_quantity").clear()
    driver.find_element_by_id("req_req_item_quantity").send_keys("2000")
    driver.find_element_by_id("req_req_item_pack_value").clear()
    driver.find_element_by_id("req_req_item_pack_value").send_keys("1.2")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()
    driver.find_element_by_link_text("Request From").click()
    driver.find_element_by_link_text("Home").click()
    
    
