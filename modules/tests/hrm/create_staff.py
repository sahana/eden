""" Sahana Eden Automated Test - HRM001 Create Staff

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

class CreateStaff(SeleniumUnitTest):
    def test_hrm001_create_staff(self):
        """
            @case: HRM001
            @description: Create a Staff
            
            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """

        print "\n"

        self.login(account="admin", nexturl="hrm/staff/create")

        self.create("hrm_human_resource", 
                    [( "organisation_id",
                       "International Federation of Red Cross and Red Crescent Societies (IFRC)",
                       "option"),
                     ( "first_name",
                       "Robert",
                       "pr_person"),
                     ( "middle_name",
                       "James",
                       "pr_person"),
                     ( "last_name",
                       "Lemon",
                       "pr_person"),
                     ( "email",
                       "rjltestdonotusetest99@romanian.com",
                       "pr_person"),
                     ( "job_title_id",
                       "Warehouse Manager",
                       "option"),
                     ( "site_id",
                       "AP Zone (Office)",
                       "option",
                       3),
                     ]
                     )
        

#===============================================================================
#    def test_hrm001_create_staff_registry(self):
#        """
#            @case: HRM001
#            @description: Create a Staff from registry
#            
#            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
#            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
#        """
#        print "\n"
# 
#        self.login(account="admin", nexturl="hrm/staff/create")
#        self.browser.find_element_by_id("select_from_registry").click()
#        self.create("hrm_human_resource", 
#                    [( "organisation_id",
#                       "Timor-Leste Red Cross Society",
#                       "autocomplete"),
#                     ( "person_id",
#                       "Yakobus Maia",
#                       "autocomplete"),
#                     ( "site_id",
#                       "Ainaro Branch Office",
#                       "autocomplete")
#                     ]
#                     )

# END =========================================================================
