# -*- coding: utf-8 -*-

""" Sahana Eden Staff Search Module Automated Tests

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
    def hrm002_staff_search(self):
        """
            @case: hrm002
            @description: Search Staff
            
            * DOES NOT WORK
        """
        print "\n"

        # Login, if not-already done so
        self.login(account="normal", nexturl="hrm/staff/search")
        
        # HRM002-1
		# Staff Simple Search
		self.search("human_resource", 
                    [( "search_simple",
					   "mariana")]
					 )
				
		# HRM002-2
		# Staff Advanced Search
		self.browser.find_element_by_class("action-lnk advanced-lnk").click()
		
		# Search by Organization
		self.search( "human_resource",
					[( "search_org",
					   "Timor-Leste Red Cross Society",
					   "checked")]
					 )
					 
		# Search by State/Province
		self.search( "human_resource",
					[( "search_org",
					   "Timor-Leste Red Cross Society",
					   "unchecked"),
					 ( self.browser.find_element_by_id("location_search_select_L1_label_A").click()),
					 ( "search_L1",
					   "Dili",
					   "checked"),
					 ( self.browser.find_element_by_id("location_search_select_L1_label_R").click()),
					 ( "search_L1",
					   "Viqueque",
					   "checked")]
					 )			   
					 
		# Search by County/District
		self.search( "human_resource",
					[( "search_L1",
					   "Dili",
					   "unchecked"),
					 ( "search_L1",
					   "Viqueque",
					   "unchecked")
					 ( self.browser.find_element_by_id("location_search_select_L2_label_A").click()),
					 ( "search_L2",
					   "Ainaro",
					   "checked"),
					 ( self.browser.find_element_by_id("location_search_select_L2_label_L").click()),
					 # the label suffix (A, L etc)seems to change depending on nr of districts
					 ( "search_L2",
					   "Lospalos",
					   "checked")]
					 )
					 
		# Search by Facility
		self.search( "human_resource",
					[( "search_L2",
					   "Ainaro",
					   "unchecked"),
					 ( "search_L2",
					   "Lospalos",
					   "unchecked"),
					 ( "search_site",
					   "Lospalos Branch Office",
					   "checked")]
					 )
		
		# Search by Training			 
		self.search( "human_resource",
					[( "search_site",
					   "Lospalos Branch Office",
					   "unchecked"),
					 ( "search_training",
					   "Basics of First Aid",
					   "checked")]
					 )
					 				 
		# Search by Facility and Training
		self.search( "human_resource",
					[( "search_site",
					   "Lospalos Branch Office",
					   "checked"),
					 ( "search_training",
					   "Basics of First Aid",
					   "checked")]
					 )
					 