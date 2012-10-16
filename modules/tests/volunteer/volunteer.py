# -*- coding: utf-8 -*-

""" Sahana Eden Volunteer Module Automated Tests

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

class Volunteer(SeleniumUnitTest):
    def test_volunteer001_create_volunteer(self):
        """
            @case: asset001
            @description: Create a Volunteer - IN PROGRESS
            
            * RENE: Insert instructions
        """

        print "\n"

        # Login, if not-already done so
        self.login(account="normal", nexturl="hrm/volunteer/create")

        self.create("hrm_human_resource", 
                    [("Timor-Leste Red Cross Society",
                      "organisation_id",
                      "autocomplete"
                      ),
                     ("",
                      ""
                      ),
                     ("",
                      ""
                      ),
                     ("",
                      ""
                      ),
                     ("",
                      ""
                      ),
                     ]
                    )

        browser = self.browser
        #browser.find_element_by_link_text("Staff & Volunteers").click()
        browser.get("%s/hrm" % self.config.url)
        browser.find_element_by_link_text("New Volunteer").click()
        w_autocomplete("Rom",
                       "hrm_human_resource_organisation_id",
                       "Romanian Food Assistance Association (Test) (RFAAT)",
                       False)
        browser.find_element_by_id("pr_person_first_name").clear()
        browser.find_element_by_id("pr_person_first_name").send_keys("John")
        browser.find_element_by_id("pr_person_last_name").clear()
        browser.find_element_by_id("pr_person_last_name").send_keys("Thompson")
        browser.find_element_by_id("pr_person_date_of_birth").click()
        browser.find_element_by_id("pr_person_date_of_birth").clear()
        browser.find_element_by_id("pr_person_date_of_birth").send_keys("1982-11-01")
        browser.find_element_by_id("pr_person_gender").send_keys("male")
        browser.find_element_by_id("pr_person_occupation").clear()
        browser.find_element_by_id("pr_person_occupation").send_keys("Social Worker")
        browser.find_element_by_id("pr_person_email").clear()
        browser.find_element_by_id("pr_person_email").send_keys("test@notavalidemail.com")
        el = browser.find_element_by_id("hrm_human_resource_job_title_id")
        for option in el.find_elements_by_tag_name("option"):
            if option.text == "Child Care Worker, Part Time":
                option.click()
                #To check afterwards
                #raw_value = int(option.get_attribute("Child Care Worker, Part Time"))
                break
        browser.find_element_by_id("hrm_human_resource_start_date").click()
        browser.find_element_by_id("hrm_human_resource_start_date").clear()
        browser.find_element_by_id("hrm_human_resource_start_date").send_keys("2012-04-17")
        browser.find_element_by_id("gis_location_L0").send_keys("Romania")
        browser.find_element_by_id("gis_location_street").clear()
        browser.find_element_by_id("gis_location_street").send_keys("23 Petru St")
        browser.find_element_by_id("gis_location_L3_ac").clear()
        browser.find_element_by_id("gis_location_L3_ac").send_keys("Bucharest")
        time.sleep(5)
        browser.find_element_by_id("ui-menu-2-0").click()
        browser.find_element_by_css_selector("input[type=\"submit\"]").click()