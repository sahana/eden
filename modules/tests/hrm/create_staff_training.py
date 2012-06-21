""" Sahana Eden Module Automated Tests - HRM003 Create Staff Training

    @copyright: 2011-2012 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

from tests.web2unittest import SeleniumUnitTest
#from tests import *
#import unittest, re, time

class CreateStaffTraining(SeleniumUnitTest):
    def test_hrm003_create_staff_training(self):
        """
            @case: HRM003
            @description: Create a Staff Training
            * Create Course
            * Create Training Event
            
            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
            
            @ToDo: 
            * Add Staff Participants
        """

        browser = self.browser
        browser.get("%s/hrm" % self.config.url)
        browser.find_element_by_link_text("New Training Course").click()
        browser.find_element_by_id("hrm_course_name").click()
        browser.find_element_by_id("hrm_course_name").clear()
        browser.find_element_by_id("hrm_course_name").send_keys("Emergency First Aid")
        browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        browser.find_element_by_link_text("Home").click()


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
