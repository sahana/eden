# -*- coding: utf-8 -*-
""" Sahana Eden Items Search Module Automated Tests
    This is a test for items search.
    Template used : default.
    Web browser : Firefox 16
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
        self.search(self.search.advanced_form,
            True,
            ({
                "name":"item_search_text",
                "value":"ATM"
                },),1,
            match_row=(1,"ATM"))
        






