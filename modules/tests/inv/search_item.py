# -*- coding: utf-8 -*-
""" Sahana Eden Items Search Module Automated Tests

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

from tests.web2unittest import SeleniumUnitTest


class SearchItems(SeleniumUnitTest):
    def setUp(self):
        super(SeleniumUnitTest, self).setUp()
        print "\n"
        self.login(account="admin", nexturl="supply/item/search")


    def test_inv018_01_inv_search_simple(self):
        """
            @case: inv018
            @description: Search Items - Simple Search
        """
        self.search(self.search.simple_form,
            True,
            ({
                "name":"item_search_text",
                "value":"ATM"
                },),1,
            match_row=(1,"ATM"))
        






