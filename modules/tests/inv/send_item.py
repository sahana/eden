""" Sahana Eden Module Automated Tests - INV001 Send Items

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

from helper import InvTestFunctions

class SendItem(InvTestFunctions):
    """
            Inventory Test - Send Workflow (Send items)
            
            @param items: This test sends a specific item to another party.
        This test assume that regression/inv-mngt has been added to prepop
        - e.g. via demo/IFRC_Train
            @Case: INV001
            
            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
    """

    # -------------------------------------------------------------------------
    def test_inv001_send_items(self):
        """ Tests for Send Workflow """

        user = "admin"
        self.login(account="admin", nexturl="inv/send/create")
        send_data = [("site_id",
                 "Timor-Leste Red Cross Society (CVTL) National Warehouse (Warehouse)",
                 "option",
                ),
                 ("type",
                  "Internal Shipment",
                  "option",
                 ),
                ("to_site_id",
                 "Lospalos Warehouse (Warehouse)",
                 "option",
                ),
                ("sender_id",
                 "Beatriz de Carvalho",
                 "autocomplete",
                ),
                ("recipient_id",
                 "Liliana Otilia",
                 "autocomplete",
                )
               ]
        item_data = [
                     [("send_inv_item_id",
                       "Blankets - 123457 - Australian Red Cross",
                       "inv_widget",
                      ),
                      ("quantity",
                       "3",
                      ),
                     ],
                    ]

        result = self.send(user, send_data)
        send_id = self.send_get_id(result)
        for data in item_data:
            result = self.track_send_item(user, send_id, data)
        # Send the shipment
        self.send_shipment(user, send_id)

