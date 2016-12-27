""" Sahana Eden Module Automated Tests - ASSET001 Create Asset

    @copyright: 2011-2016 (c) Sahana Software Foundation
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
                       "Blankets"),
                     ("organisation_id",
                      "International Federation of Red Cross and Red Crescent Societies"),
                     ( "site_id",
                       "AP Zone"),
                     ( "sn",
                       "WPU-4536-9381"),
                     ( "supply_org_id",
                       "Acme Suppliers"),
                     ( "purchase_date",
                       today),
                     ( "purchase_price",
                       8),
                     ( "purchase_currency",
                       "USD"),
                     ( "comments",
                       "Test Asset")]
                     )
        # Give time for submission of record
        time.sleep(1)

        # Set Base Facility/Site
        self.browser.find_element_by_link_text("Set Base Facility/Site").click()


        self.create("asset_log",
                    [
# The datetime doesn't work so need to fix it
# It puts in a different time and so fails to find the record
#                     ( "datetime",
#                       now),
                     ( "cond",
                       "Good Condition"),
                     ( "by_person_id",
                       "Admin User"),
                     ( "comments",
                       "Test site")]
                     )

        # Give time for submission of record
        time.sleep(1)

        # Assign to Facility/Site
        self.browser.find_element_by_link_text("Assign to Facility/Site").click()

        self.create("asset_log",
                    [
#                     ( "datetime",
#                       now),
#                     ( "datetime_until",
#                       now_1_week),
                     ( "person_id",
                       "Yakobus Sereno"),
                     ( "site_id",
                       "AP Zone (Office)"),
                     #( "room-id",
                     #  "-",
                     #  "option"),
                     ( "cond",
                       "Good Condition"),
                     ( "by_person_id",
                       "Admin User"),
                     ( "comments",
                       "Test assign")]
                     )

        # Give time for submission of record
        time.sleep(1)

        self.browser.find_element_by_link_text("Assign to Person").click()

        self.create("asset_log",
#                    [( "datetime",
#                       now_1_day),
#                     ( "datetime_until",
#                       now_1_week),
                     [( "person_id",
                       "Margarida Martins"),
                     # @ToDo: Determine how to enter checkboxes
                     #( "check_in_to_person",
                     #  "true",
                     #  "option"),
                     ( "site_id",
                       "Besusu (Facility)"),
                     #( "room-id",
                     #  "-",
                     #  "option"),
                     ( "cond",
                       "Good Condition"),
                     ( "by_person_id",
                       "Yakobus Sereno"),
                     ( "comments",
                       "Test assign person")]
                     )
