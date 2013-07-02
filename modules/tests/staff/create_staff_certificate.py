""" Sahana Eden Automated Test - HRM001 Create Volunteer Certificate

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

class CreateStaffCertificate(SeleniumUnitTest):
    def test_hrm001_create_staff_certificate(self):
        """
            @case: HRM001
            @description: Create Staff Certificate
            
            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """

        print "\n"

        self.login(account="admin", nexturl="hrm/certificate/create")

        self.create("hrm_certificate", 
                    [( "name",
                       "Basics of First Aid ATEST"
                       ),
                     ( "organisation_id",
                       "Timor-Leste Red Cross Society"),
                     ( "expiry",
                       "12"
                       ),
                     ]
                     )
        