# Assign Staff to Organisation
from tests.web2unittest import SeleniumUnitTest
from tests import *
#import unittest, re, time

class hrm_assign_organisationstaff(SeleniumUnitTest):
    def test_assign_organisation_staff(self):
        
        browser = self.browser
        #browser.find_element_by_link_text("Organizations").click()
        browser.get("%s/org" % self.config.url)
        browser.find_element_by_link_text("List All").click()
        browser.find_element_by_link_text("Open").click()
        browser.find_element_by_xpath("(//a[contains(text(),'Staff & Volunteers')])[2]").click()
        browser.find_element_by_id("pr_person_first_name").send_keys("Herculano")
        browser.find_element_by_id("pr_person_last_name").send_keys("Hugh")
        browser.find_element_by_id("pr_person_date_of_birth").send_keys("1968-10-18")
        browser.find_element_by_id("pr_person_gender").send_keys("male")
        browser.find_element_by_id("pr_person_email").send_keys("herculano@icandomybest.com")
        browser.find_element_by_id("hrm_human_resource_job_title").send_keys("Staff")
        browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        browser.find_element_by_link_text("Home").click()
