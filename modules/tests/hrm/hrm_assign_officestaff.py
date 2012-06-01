# Assign Staff to office
from tests.web2unittest import SeleniumUnitTest
from tests import *
#import unittest, re, time

class hrm_assign_officestaff(SeleniumUnitTest):
    def test_assign_office_staff(self):
        
        browser = self.browser
        homepage()
        browser.find_element_by_xpath("//div[@id='facility_box']/a[4]/div").click()
        browser.find_element_by_xpath("(//a[contains(text(),'Open')])[3]").click()
        browser.find_element_by_link_text("Staff").click()
        browser.find_element_by_id("show-add-btn").click()
        browser.find_element_by_id("select_from_registry").click()
        browser.find_element_by_id("dummy_hrm_human_resource_person_id").clear()
        w_autocomplete("Robe",
                       "hrm_human_resource_person_id",
                       "Robert James Lemon",
                       False)
        browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        browser.find_element_by_css_selector("span.S3menulogo").click()
        browser.find_element_by_link_text("Home").click()
