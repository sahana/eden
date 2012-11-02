# -*- coding: utf-8 -*-

""" Sahana Eden Member Search Module Automated Tests

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
from tests.web2unittest import SeleniumUnitTest

class Human Resources(SeleniumUnitTest):
    def mem004_member_search(self):
        """
            @case: mem004
            @description: Search Members
            
            * DOES NOT WORK
        """
        print "\n"

        # Login, if not-already done so
        self.login(account="normal", nexturl="member/membership/search")
        
		# MEM004-1
        # Member Simple Search
		self.search("membership_search_simple", 
                    [( "simple",
					   "mar")]
					 )
		
		# MEM004-2 
		# Member Advanced Search
		self.browser.find_element_by_class("action-lnk advanced-lnk").click()
		
		# Search by membership paid/expired/overdue
		self.search( "member_search",
					[( "paid",
					   "expired",
					   "checked"),
					 ( "paid",
					   "paid",
					   "unchecked"),
					 ( "overdue",
					   "checked")]
					 )
					 
		# Search by State/Province
		self.search( "member_search",
					[( "paid",
					   "expired",
					   "unchecked"),
					 ( "paid",
					   "overdue",
					   "unchecked"),
					 ( self.browser.find_element_by_id("location_search_select_L1_label_A").click()),
					 ( "L1",
					   "Aileu",
					   "checked"),
					 ( "L1",
					   "Baucau",
					   "checked")]
					 )

		# Search by County/District
		self.search( "member_search",
					[( "L1",
					   "Aileu",
					   "unchecked"),
					 ( "L1",
					   "Baucau",
					   "unchecked"),
					 ( self.browser.find_element_by_id("location_search_select_L2_label_A").click()),
					 ( "L2",
					   "Aileu Vila",
					   "checked")]
					 )
				 
		# Search by City/Town/Village
		self.search( "member_search",
					[( "L2",
					   "Aileu Vila",
					   "unchecked"),
					 ( self.browser.find_element_by_id("location_search_select_L3_label_T").click()),
					 ( "L3",
					   "Tequino Mata",
					   "checked")]
					 )
					 
					 
		
					 