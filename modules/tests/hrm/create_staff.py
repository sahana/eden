""" Sahana Eden Module Automated Tests - HRM001 Create Staff

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

class CreateStaff(SeleniumUnitTest):
    def test_hrm001_create_staff(self):
        """
            @case: HRM001
            @description: Create a Staff
            
            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """
        print "\n"
        browser = self.browser
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
        el = browser.find_element_by_id("hrm_human_resource_job_role_id")
        for option in el.find_elements_by_tag_name("option"):
            if option.text == "Administrative Officer":
                option.click()
                #To check afterwards
                #raw_value = int(option.get_attribute("Administrative Officer"))
                break
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
