# Assign staff to Organization
from tests.web2unittest import SeleniumUnitTest
from tests import *
import unittest, re, time

class hrm_assign_organizationstaff(SeleniumUnitTest):
    def test_assign_organization_staff(self):
        
        browser = self.browser
        driver = browser
        driver.find_element_by_link_text("Organizations").click()
        driver.find_element_by_link_text("List All").click()
        driver.find_element_by_link_text("Open").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Staff & Volunteers')])[2]").click()
        driver.find_element_by_id("pr_person_first_name").send_keys("Herculano")
        driver.find_element_by_id("pr_person_last_name").send_keys("Hugh")
        driver.find_element_by_id("pr_person_date_of_birth").send_keys("1968-10-18")
        driver.find_element_by_id("pr_person_gender").send_keys("male")
        driver.find_element_by_id("pr_person_email").send_keys("herculano@icandomybest.com")
        driver.find_element_by_id("hrm_human_resource_job_title").send_keys("Staff")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        driver.find_element_by_link_text("Home").click()
