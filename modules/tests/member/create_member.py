# -*- coding: utf-8 -*-

""" Sahana Eden Member Module Automated Tests

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

class CreateMember(SeleniumUnitTest):
    def test_mem001_create_member(self):
        """
            @case: mem001
            @description: Create Member

        """

        print "\n"

        today = self.today()

        self.login(account="admin", nexturl="member/membership/create")
        self.create("member_membership", 
                    [( "organisation_id",
                       "Timor-Leste Red Cross Society (CVTL)",
                       "option"),
                     ( "first_name",
                       "Denise",
                       "pr_person"),
                     ( "last_name",
                       "Grey",
                       "pr_person"),
                     ( "email",
                       "denise.grey3@cvtl.tl",
                       "pr_person"),
                     ( "start_date",
                       today,),
                     ( "membership_fee",
                       "10.00"),
                     ( "membership_paid",
                       today)]
                     )
        

#    def test_mem001_create_member_registry(self):
#        """
#            @case: mem001
#            @description: Create Member from registery
#
#        """
#        print "\n"   
#                    
#        today = self.today()
#
#        self.login(account="admin", nexturl="member/membership/create")
#        self.browser.find_element_by_id("select_from_registry").click()
#        
#        self.create("member_membership", 
#                    [( "person_id",
#                       "Beatriz Albuquequer",
#                       "autocomplete"),
#                     ( "organisation_id",
#                       "Timor-Leste Red Cross Society",
#                       "autocomplete"),
#                     ( "start_date",
#                       today),
#                     ( "membership_fee",
#                       "10.00"),
#                     ( "membership_paid",
#                       today)]
#                     )
      
        