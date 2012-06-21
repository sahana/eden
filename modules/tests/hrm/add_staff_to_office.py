""" Sahana Eden Module Automated Tests - HRM006 Add Staff To Office

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

class AddStaffToOffice(SeleniumUnitTest):
    def test_hrm006_add_staff_to_office(self):
        
        """
            @case: HRM006
            @description: Add a premade made staff to an Office
            
            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """
        
        browser = self.browser
        homepage()
        browser.find_element_by_xpath("//div[@id='facility_box']/a[4]/div").click()
        browser.find_element_by_xpath("(//a[contains(text(),'Open')])[3]").click()
        browser.find_element_by_link_text("Staff").click()
        browser.find_element_by_id("show-add-btn").click()
        browser.find_element_by_id("select_from_registry").click()
        browser.find_element_by_id("dummy_hrm_human_resource_person_id").clear()
        w_autocomplete("Robe",
                       "hrm_human_resource_person_id",
                       "Robert James Lemon",
                       False)
        browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        browser.find_element_by_css_selector("span.S3menulogo").click()
        browser.find_element_by_link_text("Home").click()
