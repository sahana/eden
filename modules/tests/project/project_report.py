# -*- coding: utf-8 -*-

""" Sahana Eden Project Automated Tests

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

class Project Report(SeleniumUnitTest):
    def test_proj009_project_report(self):
        """
            @case: proj009
            @description: Project Report

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
        self.login(account="normal", nexturl="project/location/report")

        # PROJ009
		# Project Report - Using Filter Options
		# Report by Name
		self.search( "project_location_search_text",
					 "Lori")

		# Report by State/Province
		self.create( "location_search_select_project_id$multi_theme_id_filter",
					[( "theme_id_filter",
					   "all",
					   "checked"),
					 ( self.browser.find_element_by_id("location_search_select_project_id$multi_theme_id-group-label-0").click()),
					 ( "theme_id",
					   "Capacity Development",
					   "checked"),
					 ( "theme_id",
					   "Media",
					   "checked")]
					 )

		# Project Report - Using Report Options
		# Default Report - Location/Project/Activity Type/List
		# Report by Organization/Facility/Person/Count
		self.browser.find_element_by_class("toggle-text").click()
		self.create( "report",
					[( "rows",
					   "Project",
					   "option"),
					 ( "cols",
					   "Activity Type",
					   "option"),
					 ( "fact",
					   "Location",
					   "option"),
					 ( "aggregate",
					   "List",
					   "option"),
					 ( "totals",
					   "checked")]
					 )
