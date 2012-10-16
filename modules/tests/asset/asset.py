# -*- coding: utf-8 -*-

""" Sahana Eden Asset Module Automated Tests

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

class Asset(SeleniumUnitTest):
    def test_asset001_create_asset(self):
        """
            @case: asset001
            @description: Create an Asset
            
            * RENE: Insert instructions
        """

        print "\n"

        today = self.today()
        now = self.now()
        now_1_day = self.now_1_day()
        now_1_week = self.now_1_week()

        # Login, if not-already done so
        self.login(account="normal", nexturl="asset/asset/create")
        
        self.create("asset_asset", 
                    [( "number",
                       "WS-100-17"),
                     ( "item_id",
                       "Water Purification Unit",
                       "option"),
                     #( "type",
                     #  "Other"
                     #  "option"),
                     ( "sn",
                       "WPU-4536-9381"),
                     ( "supplier",
                       "Acme Suppliers",
                       "option"),
                     ( "purchase_date",
                       today ),
                     ( "purchase_price",
                       "8.50"),
                     ( "purchase_currency",
                       "USD",
                       "option"),
                     ( "comments",
                       "Test Asset")]
                     )
                     
        
        # Set Base Facility/Site
        self.browser.find_element_by_link_text("Set Base Facility/Site").click()
        
        self.create("asset_log", 
                    [( "datetime",
                       now),
                     ( "organisation_id",
                       "Timor-Leste Red Cross Society",
                       "autocomplete"),
                     ( "site_id",
                       "Lori",
                       "option",
                       3),
                     #( "room_id",
                     #  "-"),
                     ( "cond",
                       "Good Condition",
                       "option"),
                     ( "by_person_id",
                       "Admin User",
                       "autocomplete"),
                     ( "comments",
                       "Test site")]
                     )
                   
        # Assign to Facility/Site
        self.browser.find_element_by_link_text("Assign to Facility/Site").click()
                    
        #self.browser.find_element_by_id("rheader_tab_log").click()
        
        self.create("asset_log",
                    [( "datetime",
                       now),
                     ( "datetime_until",
                       now_1_week),
                     ( "person_id",
                       "Yakobus Sereno",
                       "autocomplete"),
                     ( "site_id",
                       "Besusu (Site)",
                       "option"),
                     #( "room-id",
                     #  "-",
                     #  "option"),
                     ( "cond",
                       "Good Condition",
                       "option"),
                     ( "by_person_id",
                       "Admin User",
                       "autocomplete"),
                     ( "comments",
                       "Test assign")]
                     )
                          
        # Assign to Person
        self.browser.find_element_by_link_text("Assign to Person").click()
                    
        #self.browser.find_element_by_id("rheader_tab_log").click()
        
        self.create("asset_log",
                    [( "datetime",
                       now_1_day),
                     ( "datetime_until",
                       now_1_week),
                     ( "person_id",
                       "Margarida Martins",
                       "autocomplete"),
                     # @ToDo: Determine how to enter checkboxes
                     #( "check_in_to_person",
                     #  "true",
                     #  "option"),
                     ( "site_id",
                       "Besusu (Site)",
                       "option"),
                     #( "room-id",
                     #  "-",
                     #  "option"),
                     ( "cond",
                       "Good Condition",
                       "option"),
                     ( "by_person_id",
                       "Yakobus Sereno",
                       "autocomplete"),
                     ( "comments",
                       "Test assign person")]
                     )