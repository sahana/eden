# -*- coding: utf-8 -*-

""" Sahana Eden Project Module Automated Tests

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

class Projects(SeleniumUnitTest):
    def proj003_project_search(self):
        """
            @case: proj003
            @description: Search Projects
            * DOES NOT WORK
        """
        print "\n"

        # Login, if not-already done so
        self.login(account="normal", nexturl="project/project/search")

		# Project Search
        # Search by Project
		self.search( "project_search_simple",
					 "road")]
					 )

		# Search by Cluster - Filter type = All
		self.search( "project_search",
					[( "sector_filter",
					   "all",
					   "checked"),
					 ( "sector",
					   "DRR",
					   "checked"),
					 ( "sector",
					   "Health",
					   "checked")]
					 )

		# Search by Cluster - Filter type = Any
		self.search( "project_search",
					[( "sector_filter",
					   "any",
					   "checked"),
					 ( "sector",
					   "DRR",
					   "checked"),
					 ( "sector",
					   "Livelihoods",
					   "checked"),
					 ( "sector",
					   "Health",
					   "unchecked")]
					 )

		# Search by Hazard - Filter type = All
		self.search( "project_search",
					[( "sector",
					   "DRR",
					   "unchecked"),
					 ( "sector",
					   "Livelihoods",
					   "unchecked"),
					 ( "hazard_filter",
					   "all",
					   "checked"),
					 ( "hazard",
					   "Cyclone",
					   "checked"),
					 ( "hazard",
					   "Drought",
					   "checked")]
					 )

		# Search by Hazard - Filter type = Any
		self.search( "project_search",
					[( "hazard_filter",
					   "any",
					   "checked"),
					 ( "hazard",
					   "Drought",
					   "checked"),
					 ( "hazard",
					   "Flood",
					   "checked"),
					 ( "hazard",
					   "Cyclone",
					   "unchecked")]
					 )

		# Search by Description and Hazard
		self.search( "project_search",
					[( "simple",
					   "improvement"),
					 ( "hazard_filter",
					   "any",
					   "checked"),
					 ( "hazard",
					   "Cyclone",
					   "unchecked")]
					 )
