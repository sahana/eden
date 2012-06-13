# Set up New Volunteer
from tests.web2unittest import SeleniumUnitTest
from tests import *
#import unittest, re, time
import time

class hrm_setup_volunteer(SeleniumUnitTest):
    def test_setup_volunteer(self):
        
        browser = self.browser
        browser.get("%s/vol" % self.config.url)
        browser.find_element_by_link_text("New Volunteer").click()
        w_autocomplete("Rom",
                       "hrm_human_resource_organisation_id",
                       "Romanian Food Assistance Association (Test) (RFAAT)",
                       False)
        browser.find_element_by_id("pr_person_first_name").clear()
        browser.find_element_by_id("pr_person_first_name").send_keys("John")
        browser.find_element_by_id("pr_person_last_name").clear()
        browser.find_element_by_id("pr_person_last_name").send_keys("Thompson")
        browser.find_element_by_id("pr_person_date_of_birth").click()
        browser.find_element_by_id("pr_person_date_of_birth").clear()
        browser.find_element_by_id("pr_person_date_of_birth").send_keys("1982-11-01")
        browser.find_element_by_id("pr_person_gender").send_keys("male")
        browser.find_element_by_id("pr_person_occupation").clear()
        browser.find_element_by_id("pr_person_occupation").send_keys("Social Worker")
        browser.find_element_by_id("pr_person_email").clear()
        browser.find_element_by_id("pr_person_email").send_keys("test@notavalidemail.com")
        el = browser.find_element_by_id("hrm_human_resource_job_role_id")
        for option in el.find_elements_by_tag_name("option"):
            if option.text == "Child Care Worker, Part Time":
                option.click()
                #To check afterwards
                #raw_value = int(option.get_attribute("Child Care Worker, Part Time"))
                break
        browser.find_element_by_id("hrm_human_resource_start_date").click()
        browser.find_element_by_id("hrm_human_resource_start_date").clear()
        browser.find_element_by_id("hrm_human_resource_start_date").send_keys("2012-04-17")
        browser.find_element_by_id("gis_location_L0").send_keys("Romania")
        browser.find_element_by_id("gis_location_street").clear()
        browser.find_element_by_id("gis_location_street").send_keys("23 Petru St")
        browser.find_element_by_id("gis_location_L3_ac").clear()
        browser.find_element_by_id("gis_location_L3_ac").send_keys("Bucharest")
        time.sleep(5)
        browser.find_element_by_id("ui-menu-2-0").click()
        browser.find_element_by_css_selector("input[type=\"submit\"]").click()
