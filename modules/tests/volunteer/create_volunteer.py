""" Sahana Eden Automated Test - HRM002 Create Volunteer

    @copyright: 2011-2018 (c) Sahana Software Foundation
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

class CreateVolunteer(SeleniumUnitTest):
    def test_hrm002_create_volunteer(self):
        """
            @case: HRM002
            @description: Create Volunteer

            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """

        print "\n"

        self.login(account="admin", nexturl="vol/volunteer/create")

        self.create("hrm_human_resource",
                   [( "organisation_id",
                       "International Federation of Red Cross and Red Crescent Societies"),
                     ( "first_name",
                       "John",
                       "pr_person"),
                     ( "last_name",
                       "Thompson",
                       "pr_person"),
                     ( "email",
                       "test81@notavalidemail.com",
                       "pr_person"),
                     ( "job_title_id",
                       "Security"),
                     ]
                     )

#===============================================================================

    def test_mem001_create_volunteer_registry(self):
        """
            @case: HRM002
            @description: Create Volunteer from registery

            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """
        print "\n"

        self.login(account="admin", nexturl="vol/volunteer/create")

        # If a confirmation is shown then clear it so that it doesn't give a false positive later
        # This makes sure that there is no click between clicking 'Select from registry' and filling in name of person
        try:
            elem = self.browser.find_element_by_xpath("//div[@class='confirmation']")
            elem.click()
            time.sleep(2) # Give it time to dissolve
        except:
            pass

        self.browser.find_element_by_id("select_from_registry").click()

        self.create("hrm_human_resource",
                    [( "person_id",
                       "Duarte Botelheiro"),
                     ( "organisation_id",
                       "Timor-Leste Red Cross Society"),
                     ( "job_title_id",
                       "Coordinator"),
                    ]
                    )
