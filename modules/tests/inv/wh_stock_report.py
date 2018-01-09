# -*- coding: utf-8 -*-

""" Sahana Eden Warehouses Module Automated Tests

    @copyright: 2011-2018 (c) Sahana Software Foundation
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

class Warehouse Stock Report(SeleniumUnitTest):
    def test_inv006_warehouse_stock_report(self):
        """
            @case: inv006
            @description: Warehouse Stock Report

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
        self.login(account="normal", nexturl="inv/inv_item/report")

        # INV006
		# Warehouse Stock Report - Using Filter Options
		# Report by Item
		self.search( "inv_item_search",
					 "text",
					 "cans")]
					 )

		# Report by Facility
		self.create( "inv_item_search",
					[( "select_site_id",
					   "Lospalos Warehouse",
					   "checked")]
					 )

		# Report by Owning Organisation
		self.create( "inv_item_search",
					[( "select_site_id",
					   "Lospalos Warehouse",
					   "unchecked"),
					 ( "select_owner_org_id",
					   "Timor-Leste Red Cross Society (Cruz Vermelha de Timor-Leste)",
					   "checked")]
					 )

		# Report by Donating Organisation
		self.create( "inv_item_search",
					[( "select_owner_org_id",
					   "Timor-Leste Red Cross Society (Cruz Vermelha de Timor-Leste)",
					   "unchecked"),
					 ( "select_supply_org_id",
					   "Australian Red Cross",
					   "checked")]
					 )

		# Report by Expiry Date (min)
		self.create( "inv_item_search",
					[( "select_supply_org_id",
					   "Australian Red Cross",
					   "unchecked"),
					 ( "expiry_date_min",
					   "2012-01-01")]
					 )

		# Report by Expiry Date (max)
		self.create( "inv_item_search",
				     ( "expiry_date_max",
					    "2012-06-30")]
					 )

	 	# Report by Keyword and Owning Organisation
		self.create( "inv_item_search",
					[( "text",
					   "kitchen"),
					 ( "select_owner_org_id",
					   "Timor-Leste Red Cross Society (Cruz Vermelha de Timor-Leste)",
					   "checked")]
					 )

		# Report by Facility and Donating Organisation
		self.create( "inv_item_search",
					[( "select_owner_org_id",
					   "Timor-Leste Red Cross Society (Cruz Vermelha de Timor-Leste)",
					   "unchecked"),
					 ( "select_site_id",
					   "Lospalos Warehouse",
					   "checked"),
					 ( "select_supply_org_id",
					   "Acme Suppliers",
					   "checked")]
					 )

		# Staff Report - Using Report Options
		# Default Options = Item/Warehouse/Quantity/Sum
		# Report by Organization/Facility/Person/Count
		self.browser.find_element_by_class("toggle-text").click()
		self.create( "report",
					[( "rows",
					   "Category",
					   "option"),
					 ( "cols",
					   "Supplier/Donor",
					   "option"),
					 ( "fact",
					   "Total Value",
					   "option"),
					 ( "aggregate",
					   "Sum",
					   "option"),
					 ( "totals",
					   "checked")]
					 )

		# Report by Organization/Facility/Person/Count
		self.browser.find_element_by_class("toggle-text").click()
		self.create( "report",
					[( "rows",
					   "Training",
					   "option"),
					 ( "cols",
					   "Organization",
					   "option"),
					 ( "fact",
					   "Facility",
					   "option"),
					 ( "aggregate",
					   "Count",
					   "option"),
					 ( "totals",
					   "checked")]
					 )


