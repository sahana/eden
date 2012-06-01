# Set up Training Course
from tests.web2unittest import SeleniumUnitTest
#from tests import *
#import unittest, re, time

class hrm_setup_trainingcourse(SeleniumUnitTest):
    def test_setup_volunteer(self):
        
        browser = self.browser
        #browser.find_element_by_link_text("Staff & Volunteers").click()
        browser.get("%s/hrm" % self.config.url)
        browser.find_element_by_link_text("New Training Course").click()
        browser.find_element_by_id("hrm_course_name").click()
        browser.find_element_by_id("hrm_course_name").clear()
        browser.find_element_by_id("hrm_course_name").send_keys("Emergency First Aid")
        browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        browser.find_element_by_link_text("Home").click()
