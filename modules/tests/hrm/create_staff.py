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

from gluon import current
import unittest
from tests.web2unittest import SeleniumUnitTest
from selenium.common.exceptions import NoSuchElementException
from s3 import s3_debug
from tests import *
#import unittest, re, time
import time

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
        self.login(account="admin", nexturl="hrm/staff/create")

        self.create("hrm_human_resource", 
                    [( "organisation_id",
                       "Romanian Food Assistance Association",
                       "autocomplete"),
                     ( "first_name",
                       "Robert",
                       "pr_person"),
                     ( "middle_name",
                       "James",
                       "pr_person"),
                     ( "last_name",
                       "Lemon",
                       "pr_person"),
                     # To Do: Make 4th arg for this to support option
#                     ( "gender",
#                       "male",
#                       "option",
#                       "pr_person"),
                     ( "email",
                       "rjltestdonotusetest4@romanianfoodassistanceassociation.com",
                       "pr_person"),
                     ( "job_role_id",
                       "Administrative Officer",
                       "option"),
#                     ( "start_date",
#                       today),
#                     ( "end_date",
#                       now_1_week),
                     ( "site_id",
                       "Bucharest RFAAT Centre",
                       "autocomplete"),

                     ]
                     )


