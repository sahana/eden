# Assign Staff to Warehouse
from tests.web2unittest import SeleniumUnitTest
from tests import *
import unittest, re, time

class hrm_assign_warehousestaff(SeleniumUnitTest):
    def test_assign_warehouse_staff(self):
        
        browser = self.browser
        driver = browser
        driver.find_element_by_link_text("Warehouse").click()
        driver.find_element_by_link_text("List All").click()
        driver.find_element_by_link_text("Open").click()
        driver.find_element_by_link_text("Staff").click()
        driver.find_element_by_id("select_from_registry").click()
        w_autocomplete("Herc","hrm_human_resource_person_id","Herculano Hugh",False)
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        driver.find_element_by_css_selector("span.S3menulogo").click()
        driver.find_element_by_link_text("Home").click()
