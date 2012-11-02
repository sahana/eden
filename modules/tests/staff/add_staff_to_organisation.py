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

class AddStaffToOrganisation(SeleniumUnitTest):
    def test_hrm005_add_staff_to_organization(self):
        
        """
            @case: HRM005
            @description: Add a premade made staff to a Organisation
            
            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """

        browser = self.browser
        config = self.config
        self.login(account="admin", nexturl="org/organisation")
        self.dt_filter("Sri Lanka Red Cross Society")
        self.dt_action()
        url = browser.current_url
        url_parts = url.split("/")
        try:
            org_id = int(url_parts[-2])
        except:
            org_id = int(url_parts[-1])
        browser.get("%s/org/organisation/%s/human_resource" % (config.url, org_id))

        self.create("hrm_human_resource", 
                    [( "site_id",
                       "Lori (Facility)",
                       "option"),
                     ( "first_name",
                       "Herculano",
                       "pr_person"),
                     ( "last_name",
                       "Hugh",
                       "pr_person"),
                     ( "email",
                       "herculandfo@icandodfmybest.com",
                       "pr_person"),
                     ( "job_title_id",
                       "Secretary General",
                       "option"),
                     ]
                     )

