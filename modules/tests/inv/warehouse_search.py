# -*- coding: utf-8 -*-

""" Sahana Eden Warehouse Search Module Automated Tests

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

class Warehouses(SeleniumUnitTest):
    def org010_warehouse_search(self):
        """
            @case: org010
            @description: Search Warehouse
            
            * DOES NOT WORK
        """
        print "\n"

        # Login, if not-already done so
        self.login(account="normal", nexturl="hrm/staff/search")
        
        # ORG010
		# Warehouse Search by keyword
		self.search( "warehouse_search_text", 
                     "ainaro")
				
		# Search by Organization
		self.search( "warehouse_search",
					[( "text",
					   ""), 		# Clear text field
					 ( "org",
					   "Timor-Leste Red Cross Society",
					   "checked")
					 
		# Search by State/Province
		self.search( "warehouse_search",
					[( "org",
					   "Timor-Leste Red Cross Society",
					   "unchecked"),
					 ( self.browser.find_element_by_id("location_search_select_L1_label_A").click()),
					 ( "location",
					   "Manatuto",
					   "checked"),
					 ( "location",
					   "Ainaro",
					   "checked")]
					 )			 
		
		# Or Alternatively			 
		# Search by State/Province (using find_element)
		self.search( "warehouse_search",
					[( "org",
					   "Timor-Leste Red Cross Society",
					   "unchecked"),
					 ( self.browser.find_element_by_id("location_search_select_L1_label_A").click()),
					 ( self.browser.find_element_by_id("id-warehouse_search_location-Manatuto").click()),
					 ( self.browser.find_element_by_id("id-warehouse_search_location-Ainaro").click())]
					 )
		
		