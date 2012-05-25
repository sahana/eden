# Set up Staff
from tests.web2unittest import SeleniumUnitTest
from tests import *

class hrm_setup_staff(SeleniumUnitTest):
    def test_setup_staff(self):

        browser = self.browser
        driver = self.browser
        driver.find_element_by_link_text("Staff & Volunteers").click()
        driver.find_element_by_link_text("New Staff Member").click()
        w_autocomplete("Rom","hrm_human_resource_organisation_id","Romanian Food Assistance Association (Test) (RFAAT)",False)
        driver.find_element_by_id("pr_person_first_name").clear()
        driver.find_element_by_id("pr_person_first_name").send_keys("Robert")
        driver.find_element_by_id("pr_person_middle_name").clear()
        driver.find_element_by_id("pr_person_middle_name").send_keys("James")
        driver.find_element_by_id("pr_person_last_name").clear()
        driver.find_element_by_id("pr_person_last_name").send_keys("Lemon")
        driver.find_element_by_id("pr_person_date_of_birth").click()
        driver.find_element_by_id("pr_person_date_of_birth").clear()
        driver.find_element_by_id("pr_person_date_of_birth").send_keys("1980-10-14")
        driver.find_element_by_id("pr_person_gender").click()
        driver.find_element_by_id("pr_person_gender").send_keys("male")
        driver.find_element_by_id("pr_person_occupation").clear()
        driver.find_element_by_id("pr_person_occupation").send_keys("Social Worker")
        driver.find_element_by_id("pr_person_email").clear()
        driver.find_element_by_id("pr_person_email").send_keys("rjltestdonotusetest4@romanianfoodassistanceassociation.com")
        driver.find_element_by_id("hrm_human_resource_job_title").clear()
        driver.find_element_by_id("hrm_human_resource_job_title").send_keys("Social Worker")
        driver.find_element_by_id("hrm_human_resource_start_date").click()
        driver.find_element_by_id("hrm_human_resource_start_date").clear()
        driver.find_element_by_id("hrm_human_resource_start_date").send_keys("2012-02-02")
        driver.find_element_by_css_selector("#hrm_human_resource_start_date__row > td").click()
        driver.find_element_by_id("hrm_human_resource_end_date").click()
        driver.find_element_by_id("hrm_human_resource_end_date").clear()
        driver.find_element_by_id("hrm_human_resource_end_date").send_keys("2015-03-02")
        w_autocomplete("Buch","hrm_human_resource_site_id","Bucharest RFAAT Centre (Test) (Office)",False)
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        driver.find_element_by_link_text("Home").click()

