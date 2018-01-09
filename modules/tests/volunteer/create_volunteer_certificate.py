""" Sahana Eden Automated Test - HRM001 Create Volunteer Certificate

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

from gluon import current
from tests.web2unittest import SeleniumUnitTest

class CreateVolunteerCertificate(SeleniumUnitTest):
    def test_hrm001_create_volunteer_certificate(self):
        """
            @case: HRM001
            @description: Create Volunteer Certificate

            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """
        print "\n"

        if not current.deployment_settings.get_hrm_use_certificates():
            return

        # To check if required database is prepopulated
        # If not prepopulate it with a test value
        if current.deployment_settings.get_hrm_use_skills():
            skill_table = current.s3db["hrm_skill"]
            db = current.db
            query = (skill_table.id > 0)
            row = db(query).select(skill_table.name,
                                   limitby=(0, 1)).first()
            if row:
                name=row.name

            else:
                skill_table.insert(name="Test")
                db.commit()
                name="Test"

        # Start the test
        self.login(account="admin", nexturl="vol/certificate/create")

        self.create("hrm_certificate",
                    [("name",
                       "Advance First Aid ATest"
                       ),
                     ("organisation_id",
                       "Timor-Leste Red Cross Society",
                       ),
                     ("expiry",
                       "12"
                       ),
                     ]
                     )

        # Find the current URL of the browser
        current_url = str(self.browser.current_url)
        current_form = str(current_url.split('/')[-1])

        # Check if the form we arrived on is right or not
        if current_form == "certificate_skill":
            # Check if add button is present on the page. Click it if found.
            add_btn = self.browser.find_elements_by_id("show-add-btn")
            if len(add_btn) > 0:
                add_btn[0].click()

                self.create("hrm_certificate_skill",
                           [("skill_id",
                              name),
                           ]
                           )
