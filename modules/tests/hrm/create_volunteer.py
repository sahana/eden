""" Sahana Eden Automated Test - HRM002 Create Volunteer

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

class CreateVolunteer(SeleniumUnitTest):
    def test_hrm002_create_volunteer(self):
        """
            @case: HRM002
            @description: Create Volunteer
            
            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """
        print "\n"

        import datetime
        from dateutil.relativedelta import relativedelta

        browser = self.browser
        self.login(account="admin", nexturl="vol/volunteer/create")

        self.create("hrm_human_resource", 
                    [( "organisation_id",
                       "Romanian Food Assistance Association",
                       "autocomplete"),
                     ( "first_name",
                       "John",
                       "pr_person"),
                     ( "last_name",
                       "Thompson",
                       "pr_person"),
                     ( "date_of_birth",
                       "1980-10-14",
                       "pr_person"),
                     # To Do: Make 4th arg for this to support option
#                     ( "gender",
#                       "male",
#                       "option",
#                       "pr_person"),
                     ( "email",
                       "test@notavalidemail.com",
                       "pr_person"),
                     ( "job_role_id",
                       "Child Care Worker, Part Time",
                       "option"),
#                     ( "start_date",
#                       today),
#                     ( "end_date",
#                       now_1_week),
                     ( "L0",
                       "Romania",
                       "gis_location"),
                     ( "street",
                       "23 Petru St",
                       "gis_location" ),
                     ( "L3",
                       "Bucharest",
                       "gis_location" ),
                     ]
                     )

