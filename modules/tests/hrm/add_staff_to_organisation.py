""" Sahana Eden Module Automated Tests - HRM005 Add Staff To Organization

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
from tests import *
#import unittest, re, time

class AddStaffToOrganisation(SeleniumUnitTest):
    def test_hrm005_add_staff_to_organization(self):
        
        """
            @case: HRM005
            @description: Add a premade made staff to a Organisation
            
            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """
        
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
