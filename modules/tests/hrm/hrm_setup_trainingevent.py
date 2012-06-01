# Set up Training Event
from tests.web2unittest import SeleniumUnitTest
from tests import *
#import unittest, re, time

class hrm_setup_trainingevent(SeleniumUnitTest):
    def test_setup_trainingevent(self):
        
        browser = self.browser
        #browser.find_element_by_link_text("Staff & Volunteers").click()
        browser.get("%s/hrm" % self.config.url)
        browser.find_element_by_link_text("New Training Event").click()
        browser.find_element_by_id("hrm_training_event_course_id").send_keys("Emergency First Aid")
        w_autocomplete("buch",
                       "hrm_training_event_site_id",
                       "Bucharest RFAAT Centre (Test) (Office)",
                       False)
        browser.find_element_by_id("hrm_training_event_start_date").send_keys("2012-04-11")
        browser.find_element_by_id("hrm_training_event_end_date").send_keys("2012-04-12")
        browser.find_element_by_id("hrm_training_event_hours").send_keys("16")
        browser.find_element_by_id("hrm_training_event_comments").clear()
        browser.find_element_by_id("hrm_training_event_comments").send_keys("test")
        browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        w_autocomplete("Adri",
                       "hrm_training_person_id",
                       "Adriana Macedo",
                       False)
        browser.find_element_by_id("hrm_training_comments").send_keys("test")
        browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        browser.find_element_by_link_text("Home").click()
        