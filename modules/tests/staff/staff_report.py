# -*- coding: utf-8 -*-

""" Sahana Eden Staff Module Automated Tests

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

class Staff Report(SeleniumUnitTest):
    def test_hrm008_staff_report(self):
        """
            @case: hrm008
            @description: Staff Report
            
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
        self.login(account="normal", nexturl="hrm/staff/report")
        
        # HRM008
		# Staff Report - Using Filter Options
		# Report by Organization
		self.search( "human_resource_search_select",
					[( "organisation_id",
					   "Timor-Leste Red Cross Society (CVTL)",
					   "checked")]
					 )
					 					 
		# Report by State/Province
		self.create( "human_resource_search_select",
					[( "organisation_id",
					   "Timor-Leste Red Cross Society (CVTL)",
					   "unchecked"),
					 ( "location_id$L1",
					   "Ainaro",
					   "checked"),
					 ( "location_id$L1",
					   "Manatuto",
					   "checked")]
					 )

		# Report by County/District
		self.create( "human_resource_search_select",
					[( "location_id$L1",
					   "Ainaro",
					   "unchecked"),
					 ( "location_id$L1",
					   "Manatuto",
					   "unchecked"),
					 ( "location_id$L2",
					   "Ainaro",
					   "checked"),
					 ( "location_id$L2",
					   "Same",
					   "checked")]
					 )

		# Report by Facility
		self.create( "human_resource_search_select",
					[( "location_id$L2",
					   "Ainaro",
					   "unchecked"),
					 ( "location_id$L2",
					   "Same",
					   "unchecked"),
					 ( "site_id",
					   "Viqueque Branch Office",
					   "checked"),
					 ( "site_id",
					   "Ainaro Branch Office",
					   "checked")]
					 )
	 			   
		# Report by County/District & Facility
		self.create( "human_resource_search_select",
					[( "site_id",
					   "Viqueque Branch Office",
					   "unchecked"),
					 ( "site_id",
					   "Ainaro Branch Office",
					   "unchecked"),
					 ( "location_id$L2",
					   "Ainaro",
					   "checked"),
					 ( "site_id",
					   "Manatuto Branch Office",
					   "checked")]
					 )
	 	
		# Staff Report - Using Report Options
		# Report by Organization/Facility/Person/Count
		self.browser.find_element_by_class("toggle-text").click()
		self.create( "report",
					[( "rows",
					   "Organization",
					   "option"),
					 ( "cols",
					   "Facility",
					   "option"),
					 ( "fact",
					   "Person",
					   "option"),
					 ( "aggregate",
					   "Count",
					   "option"),
					 ( "totals",
					   "checked")]
					 )
					 	
		# Report by Training/Organization/Facility/Count
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
		
		