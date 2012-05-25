# Set up Training Course
from tests.web2unittest import SeleniumUnitTest
from tests import *
import unittest, re, time

class hrm_setup_trainingcourse(SeleniumUnitTest):
    def test_setup_volunteer(self):
        
        browser = self.browser
        driver = browser
        driver.find_element_by_link_text("Staff & Volunteers").click()
        driver.find_element_by_link_text("New Training Course").click()
        driver.find_element_by_id("hrm_course_name").click()
        driver.find_element_by_id("hrm_course_name").clear()
        driver.find_element_by_id("hrm_course_name").send_keys("Emergency First Aid")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        driver.find_element_by_link_text("Home").click()
