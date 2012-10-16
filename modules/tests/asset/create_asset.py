""" Sahana Eden Module Automated Tests - ASSET001 Create Asset

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

class CreateAsset(SeleniumUnitTest):
    def test_asset001_create_asset(self):
        """
            @case: asset001
            @description: Create an Asset
            
            @Test Doc: https://docs.google.com/a/aidiq.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE#gid=2
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """

        today = self.today()
        now = self.now()
        now_1_day = self.now_1_day()
        now_1_week = self.now_1_week()

        # Login, if not-already done so
        self.login(account="admin", nexturl="asset/asset/create")

        self.create("asset_asset", 
                    [( "number",
                       "WS_100_17"),
                     ( "item_id",
                       "Blankets",
                       "option"),
                     ("organisation_id", 
                      "International Federation of Red Cross and Red Crescent Societies (IFRC)", 
                      "option"),
                     ( "site_id",
                       "AP Zone",
                       "option",
                        4),
                     ( "sn",
                       "WPU-4536-9381"),
                     ( "supply_org_id",
                       "Acme Suppliers",
                       "option"),
                     ( "purchase_date",
                       today),
                     ( "purchase_price",
                       8),
                     ( "purchase_currency",
                       "USD",
                       "option"),
                     ( "comments",
                       "Test Asset")]
                     )
                     
        
        # Set Base Facility/Site
        self.browser.find_element_by_link_text("Set Base Facility/Site").click()
        
        self.create("asset_log",
                    [
# The datetime doesn't work so need to fix it
# It puts in a different time and so fails to find the record
#                     ( "datetime",
#                       now),
                     ( "organisation_id",
                       "Timor-Leste Red Cross Society (CVTL)",
                       "option"),
                     ( "site_id",
                       "Lori (Facility)",
                       "option",
                       3),
                     ( "cond",
                       "Good Condition",
                       "option"),
                     ( "by_person_id",
                       "Admin User",
                       "autocomplete"),
                     ( "comments",
                       "Test site")]
                     )

#        # Assign to Facility/Site
#        self.browser.find_element_by_link_text("Assign to Facility/Site").click()
#                    
#        #self.browser.find_element_by_id("rheader_tab_log").click()
#        
#        self.create("asset_log",
#                    [
#                     ( "datetime",
#                       now),
#                     ( "datetime_until",
#                       now_1_week),
#                     ( "person_id",
#                       "Yakobus Sereno",
#                       "autocomplete"),
#                     ( "site_id",
#                       "Besusu (Site)",
#                       "option"),
#                     #( "room-id",
#                     #  "-",
#                     #  "option"),
#                     ( "cond",
#                       "Good Condition",
#                       "option"),
#                     ( "by_person_id",
#                       "Admin User",
#                       "autocomplete"),
#                     ( "comments",
#                       "Test assign")]
#                     )
#                          
#        # Assign to Person
#        self.browser.find_element_by_link_text("Assign to Person").click()
#                    
#        #self.browser.find_element_by_id("rheader_tab_log").click()
#        
#        self.create("asset_log",
#                    [( "datetime",
#                       now_1_day),
#                     ( "datetime_until",
#                       now_1_week),
#                     ( "person_id",
#                       "Margarida Martins",
#                       "autocomplete"),
#                     # @ToDo: Determine how to enter checkboxes
#                     #( "check_in_to_person",
#                     #  "true",
#                     #  "option"),
#                     ( "site_id",
#                       "Besusu (Site)",
#                       "option"),
#                     #( "room-id",
#                     #  "-",
#                     #  "option"),
#                     ( "cond",
#                       "Good Condition",
#                       "option"),
#                     ( "by_person_id",
#                       "Yakobus Sereno",
#                       "autocomplete"),
#                     ( "comments",
#                       "Test assign person")]
#                     )