# -*- coding: utf-8 -*-

""" Sahana Eden Warehouse Search Module Automated Tests

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
import functools

def _kwsearch(instance, column, items, keyword):
    for item in [instance.dt_data_item(i, column) for i in xrange(1, items + 1)]:
        if not (keyword.strip().lower() in item.strip().lower()):
            return False
    return True

class SearchWarehouse(SeleniumUnitTest):

    def setUp(self):
        super(SeleniumUnitTest, self).setUp()
        print "\n"
        self.login(account="admin", nexturl="inv/warehouse/search?clear_opts=1")


    def test_warehouse_01_search_name(self):
        """
            @case: warehouse_01
            @description: Search Warehouse - Simple Search
        """
        w = current.s3db["inv_warehouse"]
        key="na"
        dbRowCount = current.db( (w.deleted != "T") & (w.name.like("%"+ key + "%")) ).count()
        self.search(self.search.advanced_form,
            True,
            ({
                "id": "warehouse_search_simple",
                "value": key
            },), dbRowCount,
            manual_check=functools.partial(_kwsearch, keyword=key, items=dbRowCount, column=2)
        )

    def test_warehouse_02_search_by_Organization(self):
        """
            @case: warehouse_02
            @description: Search Warehouse - Advanced Search by Organization
        """
        w = current.s3db["inv_warehouse"]
        o = current.s3db["org_organisation"]
        key="Timor-Leste Red Cross Society (Cruz Vermelha de Timor-Leste)"
        dbRowCount = current.db((w.deleted != "T") & (w.organisation_id == o.id) & (o.name == key)).count()
        self.search(self.search.advanced_form,
            True,
            ({
                "name": "warehouse_search_org",
                "label": key,
                "value": True
            },), dbRowCount,
            manual_check=functools.partial(_kwsearch, keyword=key, items=dbRowCount, column=3)
        )

    def test_warehouse_03_search_by_District(self):
        """
            @case: warehouse_03
            @description: Search Warehouse - Advanced Search by District
        """
        w = current.s3db["inv_warehouse"]
        l = current.s3db["gis_location"]
        key="Viqueque"
        dbRowCount = current.db((w.deleted != "T") & (w.location_id == l.id) & (l.L2 == key)).count()
        self.search(self.search.advanced_form,
            True,
            ({
                "name": "warehouse_search_location",
                "label": key,
                "value": True
            },), dbRowCount,
            manual_check=functools.partial(_kwsearch, keyword=key, items=dbRowCount, column=5)
        )
