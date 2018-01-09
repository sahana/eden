# -*- coding: utf-8 -*-

""" Sahana Eden Asset Module Automated Tests

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

__all__ = ['AssetSearch']

from gluon import current
from tests.web2unittest import SeleniumUnitTest
import functools


def _kwsearch(instance, column, items, keyword):
    for item in [instance.dt_data_item(i, column) for i in xrange(1, items + 1)]:
        if not (keyword.strip().lower() in item.strip().lower()):
            return False
    return True


class AssetSearch(SeleniumUnitTest):
    """
        @case: asset005
        @description: Search Assets
    """

    def setUp(self):
        super(SeleniumUnitTest, self).setUp()
        print "\n"
        self.login(account="admin", nexturl="asset/asset/search")

    def test_asset_search_keyword(self):
        self.search(self.search.advanced_form,
            True,
            ({
                "name": "asset_search_text",
                "value": "Radio"
            },), 10,
            manual_check=functools.partial(_kwsearch, keyword="Radio", items=10, column=3)
        )

    def test_asset_search_category(self):
        self.search(self.search.advanced_form,
            True,
            ({
                "name": "asset_search_item_category",
                "label": "Default > IT",
                "value": True
            },), 10,
            manual_check=functools.partial(_kwsearch, keyword="IT", items=10, column=2)
        )

    def test_asset_search_category_keyword(self):
        self.search(self.search.advanced_form,
            True,
            ({
                "name": "asset_search_text",
                "value": "Hand"
            },
            {
                "name": "asset_search_item_category",
                "label": "Default > Communications",
                "value": True
            }), 5,
            manual_check=functools.partial(_kwsearch, keyword="Hand", items=5, column=3)
        )
