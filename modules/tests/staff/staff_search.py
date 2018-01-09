# -*- coding: utf-8 -*-

""" Sahana Eden Member Search Module Automated Tests

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
import time
from gluon import current
from tests.web2unittest import SeleniumUnitTest
import functools

def _kwsearch(instance, column, items, keyword):
    for item in [instance.dt_data_item(i, column) for i in xrange(1, items + 1)]:
        if not (keyword.strip().lower() in item.strip().lower()):
            return False
    return True

class SearchStaff(SeleniumUnitTest):

    def setUp(self):
        super(SeleniumUnitTest, self).setUp()
        print "\n"
        self.login(account="admin", nexturl="hrm/staff/search?clear_opts=1")


    def test_hrm002_01_hrm_search_simple(self):
        """
            @case: hrm002-01
            @description: Search Members - Simple Search
        """
        key="Mem"
        self.search(self.search.simple_form,
            True,
            [],
            {"tablename":"hrm_human_resource", "key":key, "filters":[("type",1)]},
            manual_check=functools.partial(_kwsearch, keyword=key, items=1, column=2)
        )


    def test_hrm002_02_hrm_search_advance_by_Organization(self):
        """
            @case: hrm002-02
            @description: Search Members - Advanced Search by Organization
        """
        key="Finnish Red Cross (FRC)"
        self.search(self.search.advanced_form,
            True,
            ({
                "name": "human_resource_search_org",
                "label": key,
                "value": True
            },),
            {"tablename":"hrm_human_resource", "filters":[("type",1)]},
            manual_check=functools.partial(_kwsearch, keyword=key, items=1, column=4)
        )


    def test_hrm002_03_hrm_search_advance_by_Facility(self):
        """
            @case: hrm002-03
            @description: Search Members - Advanced Search by Facility
        """
        self.search(self.search.advanced_form,
            True,
            (
             {
                "name": "human_resource_search_site",
                "label": "AP Zone (Office)",
                "value": True
            },
             {
                "name": "human_resource_search_site",
                "label": "Victoria Branch Office (Office)",
                "value": True
            },
            ),
            {"tablename":"hrm_human_resource", "filters":[("type",1)]},
            manual_check=functools.partial(_kwsearch, keyword="(Office)", items=1, column=6)
        )


    def test_hrm002_04_hrm_search_advance_by_Training(self):
        """
            @case: hrm002-04
            @description: Search Members - Advanced Search by Training
        """
        key="Basics of First Aid"
        self.search(self.search.advanced_form,
            True,
            ({
                "name": "human_resource_search_training",
                "label": key,
                "value": True
            },),
            {"tablename":"hrm_human_resource", "filters":[("type",1)]},
            # "Basics of First Aid" is getting truncated
            manual_check=functools.partial(_kwsearch, keyword="Basics of Fir", items=1, column=9)
        )

