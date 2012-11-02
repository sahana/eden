# -*- coding: utf-8 -*-

""" Sahana Eden Volunteer Search Module Automated Tests

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
    def hrm012_volunteer_search(self):
        """
            @case: hrm012
            @description: Search Volunteers
            
            * DOES NOT WORK
        """
        print "\n"

        # Login, if not-already done so
        self.login(account="normal", nexturl="vol/volunteer/search")
        
		# HRM012-1
        # Volunteer Simple Search
		self.search("human_resource", 
                    [( "search_simple",
					   "bea")]
					 )
		
		# HRM012-2 
		# Volunteer Advanced Search
		self.browser.find_element_by_class("action-lnk advanced-lnk").click()
		
		# Search by Status and Organization
		self.search( "human_resource",
					[( "search_active",
					   "Yes",
					   "checked"),
					 ( "search_org",
					   "Timor-Leste Red Cross Society",
					   "checked")]
					 )
					 
		# Search by State/Province
		self.search( "human_resource",
					[( "search_active",
					   "unchecked"),
					 ( "search_org",
					   "unchecked"),
					 ( self.browser.find_element_by_id("location_search_select_L1_label_A").click()),
					 ( "search_L1",
					   "Manatuto",
					   "checked"),
					 ( self.browser.find_element_by_id("location_search_select_L1_label_R").click()),
					 ( "search_L1",
					   "Viqueque",
					   "checked")]
					 )			   
					 
		# Search by County/District
		self.search( "human_resource",
					[( "search_L1",
					   "Manatuto",
					   "unchecked"),
					 ( "search_L1",
					   "Viqueque",
					   "unchecked")
					 ( self.browser.find_element_by_id("location_search_select_L2_label_A").click()),
					 ( "search_L2",
					   "Ainaro",
					   "checked")]
					 )
					 
		# Search by Training
		self.search( "human_resource",
					[( "search_L2",
					   "Ainaro",
					   "unchecked"),
					 ( "search_training",
					   "First Aid Team Leader",
					   "checked"),
					 ( "search_training",
					   "Basics of First Aid",
					   "checked")]
					 )
					 
		# Search by County/District and Training
		self.search( "human_resource",
					[( "search_L2",
					   "Ainaro",
					   "checked"),
					 ( "search_training",
					   "First Aid Team Leader",
					   "checked"),
					 ( "search_training",
					   "Basics of First Aid",
					   "checked")]
					 )
					 		 