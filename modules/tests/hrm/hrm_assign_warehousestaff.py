# Assign Staff to Warehouse
from tests.web2unittest import SeleniumUnitTest
from tests import *
#import unittest, re, time

class hrm_assign_warehousestaff(SeleniumUnitTest):
    def test_assign_warehouse_staff(self):
        
        browser = self.browser
        #browser.find_element_by_link_text("Warehouse").click()
        browser.get("%s/inv" % self.config.url)
        browser.find_element_by_link_text("List All").click()
        browser.find_element_by_link_text("Open").click()
        browser.find_element_by_link_text("Staff").click()
        browser.find_element_by_id("select_from_registry").click()
        w_autocomplete("Herc",
                       "hrm_human_resource_person_id",
                       "Herculano Hugh",
                       False)
        browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        browser.find_element_by_css_selector("span.S3menulogo").click()
        browser.find_element_by_link_text("Home").click()
