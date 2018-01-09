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

from gluon import current
from tests.web2unittest import SeleniumUnitTest


class AssetReport(SeleniumUnitTest):
    """
        @case: asset006
        @description: Asset Report
    """
    def setUp(self):
        super(SeleniumUnitTest, self).setUp()
        print "\n"
        self.login(account="admin", nexturl="asset/asset/report")

    def test_asset_report(self):
        self.report(None, "Item", "Category", None,
            ("Motorcyle - DT50MX - Yamaha", "Default > Vehicle", 5))

    def test_asset_report_filter(self):
        self.report(
            ({
                "label": "Default > Vehicle",
                "value": True
            },), "Item", "Category", None,
            ("Motorcyle - DT50MX - Yamaha", "Default > Vehicle", 5),
            row_count=1)

    def test_asset_report_filter_L0_L1(self):
        self.report(
            ({
                "name": "asset_search_select_location_id$L0",
                "label": "Timor-Leste",
                "value": True
            },
            {
                "name": "asset_search_select_location_id$L1",
                "label": "Ainaro",
                "value": True
            }), "Item", "Category", None, row_count=5)
