# Set up Staff
from tests.web2unittest import SeleniumUnitTest
from tests import *

class hrm_setup_staff(SeleniumUnitTest):
    def test_setup_staff(self):

        browser = self.browser
        #browser.find_element_by_link_text("Staff & Volunteers").click()
        browser.get("%s/hrm" % self.config.url)
        browser.find_element_by_link_text("New Staff Member").click()
        w_autocomplete("Rom",
                       "hrm_human_resource_organisation_id",
                       "Romanian Food Assistance Association (Test) (RFAAT)",
                       False)
        browser.find_element_by_id("pr_person_first_name").clear()
        browser.find_element_by_id("pr_person_first_name").send_keys("Robert")
        browser.find_element_by_id("pr_person_middle_name").clear()
        browser.find_element_by_id("pr_person_middle_name").send_keys("James")
        browser.find_element_by_id("pr_person_last_name").clear()
        browser.find_element_by_id("pr_person_last_name").send_keys("Lemon")
        browser.find_element_by_id("pr_person_date_of_birth").click()
        browser.find_element_by_id("pr_person_date_of_birth").clear()
        browser.find_element_by_id("pr_person_date_of_birth").send_keys("1980-10-14")
        browser.find_element_by_id("pr_person_gender").click()
        browser.find_element_by_id("pr_person_gender").send_keys("male")
        browser.find_element_by_id("pr_person_occupation").clear()
        browser.find_element_by_id("pr_person_occupation").send_keys("Social Worker")
        browser.find_element_by_id("pr_person_email").clear()
        browser.find_element_by_id("pr_person_email").send_keys("rjltestdonotusetest4@romanianfoodassistanceassociation.com")
        browser.find_element_by_id("hrm_human_resource_job_title").clear()
        browser.find_element_by_id("hrm_human_resource_job_title").send_keys("Social Worker")
        browser.find_element_by_id("hrm_human_resource_start_date").click()
        browser.find_element_by_id("hrm_human_resource_start_date").clear()
        browser.find_element_by_id("hrm_human_resource_start_date").send_keys("2012-02-02")
        browser.find_element_by_css_selector("#hrm_human_resource_start_date__row > td").click()
        browser.find_element_by_id("hrm_human_resource_end_date").click()
        browser.find_element_by_id("hrm_human_resource_end_date").clear()
        browser.find_element_by_id("hrm_human_resource_end_date").send_keys("2015-03-02")
        w_autocomplete("Buch",
                       "hrm_human_resource_site_id",
                       "Bucharest RFAAT Centre (Test) (Office)",
                       False)
        browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        browser.find_element_by_link_text("Home").click()

