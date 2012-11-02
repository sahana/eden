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

# Does not work
from gluon import current
from tests.web2unittest import SeleniumUnitTest

class Asset Report(SeleniumUnitTest):
    def test_asset006_asset_report(self):
        """
            @case: asset006
            @description: Asset Report
            
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
        self.login(account="normal", nexturl="asset/asset/report")
        
        # ASSET006
		# Asset Report - Using Filter Options
		# Report by Category
		self.search( "asset_search_select_item_id$item_category_id",
					 "equipment",
					 "checked")]
					 )
					 					 
		# Asset Report - Using Report Options
		# Default = Category/State Province/Asset Number/Count
		# Report by Organization/Facility/Person/Count
		self.browser.find_element_by_class("toggle-text").click()
		self.create( "report",
					[( "rows",
					   "Facility/Site",
					   "option"),
					 ( "cols",
					   "Item",
					   "option"),
					 ( "fact",
					   "Category",
					   "option"),
					 ( "aggregate",
					   "Count",
					   "option"),
					 ( "totals",
					   "checked")]
					 )
					 
		