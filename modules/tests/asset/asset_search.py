# -*- coding: utf-8 -*-

""" Sahana Eden Asset Module Automated Tests

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

class Asset Search(SeleniumUnitTest):
    def test_asset005_asset_search(self):
        """
            @case: asset005
            @description: Search Assets
            
            * DOES NOT WORK
        """
        print "\n"
        
        import datetime
        from dateutil.relativedelta import relativedelta

        #@ToDo: Move these into we2unittest
        today = datetime.date.today().strftime("%Y-%m-%d")
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now_1_day = (datetime.datetime.now() + relativedelta( days = +1 )).strftime("%Y-%m-%d %H:%M:%S")
        now_1_week = (datetime.date.today() + relativedelta( weeks = +1 )).strftime("%Y-%m-%d %H:%M:%S")
        
        # Login, if not-already done so
        self.login(account="normal", nexturl="asset/asset/search")
        
        # ASSET005
		# Asset Search by keyword
		self.search( "asset_search_text", 
                     "radio")
				
		# Search by Category
		self.search( "asset_search_item_category",
					 "equipment",
					 "checked")
					 
		# Search by Keyword and Category
		self.search( "asset_search",
					[( "text",
					   "laptop"),
					 ( "item_category",
					   "IT",
					   "checked")]
					 )
					 			 
		