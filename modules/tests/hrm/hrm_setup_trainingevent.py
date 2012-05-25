# Set up Training Event
from tests.web2unittest import SeleniumUnitTest
from tests import *
import unittest, re, time

class hrm_setup_trainingevent(SeleniumUnitTest):
    def test_setup_trainingevent(self):
        
        browser = self.browser
        driver = browser
        driver.find_element_by_link_text("Staff & Volunteers").click()
        driver.find_element_by_link_text("New Training Event").click()
        driver.find_element_by_id("hrm_training_event_course_id").send_keys("Emergency First Aid")
        w_autocomplete("buch","hrm_training_event_site_id","Bucharest RFAAT Centre (Test) (Office)",False)
        driver.find_element_by_id("hrm_training_event_start_date").send_keys("2012-04-11")
        driver.find_element_by_id("hrm_training_event_end_date").send_keys("2012-04-12")
        driver.find_element_by_id("hrm_training_event_hours").send_keys("16")
        driver.find_element_by_id("hrm_training_event_comments").clear()
        driver.find_element_by_id("hrm_training_event_comments").send_keys("test")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        w_autocomplete("Adri","hrm_training_person_id","Adriana Macedo",False)
        driver.find_element_by_id("hrm_training_comments").send_keys("test")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        driver.find_element_by_link_text("Home").click()
        