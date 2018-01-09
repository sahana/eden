# -*- coding: utf-8 -*-

""" Sahana Eden Volunteer Search Module Automated Tests

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
    OTHER DEALINGS IN THE OFTWARE.
"""

from gluon import current
from tests.web2unittest import SeleniumUnitTest


class VolunteerSearch(SeleniumUnitTest):
    def setUp(self):
        super(SeleniumUnitTest, self).setUp()
        print "\n"
        self.login(account="admin", nexturl="vol/volunteer/search")

    def test_volunteer_search_simple(self):
        # HRM012-1
        # Volunteer Simple Search
        self.search(self.search.simple_form,
            True,
            ({
                "name": "human_resource_search_simple_simple",
                "value": "Maia"
            },), 1,
            match_row=(1, "Yakobus Maia")
        )

    def test_volunteer_search_advanced(self):
        # HRM012-2
        # Volunteer Advanced Search
        self.search(self.search.advanced_form,
            True,
            ({
                "name": "human_resource_search_L1",
                "label": "Baucau",
                "value": True
            },
            {
                "name": "human_resource_search_org",
                "label": "Timor-Leste Red Cross Society (CVTL)",
                "value": True
            }), 2,
            match_column=(2, "Yakobus Maia", "Isabel Zacarias")
        )

    def test_volunteer_search_L1(self):
        # Search by L1
        self.search(self.search.advanced_form,
            True,
            ({
                "name": "human_resource_search_L1",
                "label": "Manatuto",
                "value": True
            },
            {
                "name": "human_resource_search_L1",
                "label": "Viqueque",
                "value": True
            }), 4,
            match_column=(2, "Orlando Fahik Batak", "Mariana Sereno",
                "Adriana Ramos", "Justiano Macedo")
        )

    def test_volunteer_search_L2(self):
        # Search by L2
        self.search(self.search.advanced_form,
            True,
            ({
                "name": "human_resource_search_L2",
                "label": "Aileu Vila",
                "value": True
            },), 2,
            match_column=(2, "Marcelino Otilia", "Soraia Moises")
        )

    def test_volunteer_search_training(self):
        # Search by Training
        self.search(self.search.advanced_form,
            False,
            ({
                "name": "human_resource_search_training",
                "label": "Basics of First Aid",
                "value": True
            },), None,
        )

    def test_volunteer_search_L2_training(self):
        # Search by L2 and Training
        self.search(self.search.advanced_form,
            False,
            ({
                "name": "human_resource_search_training",
                "label": "Basics of First Aid",
                "value": True
            },
            {
                "name": "human_resource_search_L2",
                "label": "Aileu Vila",
                "value": True
            }), None,
        )
