""" Sahana Eden Module Automated Tests - INV003 Send - Receive Items

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

from helper import InvTestFunctions

class SendReceiveItem(InvTestFunctions):
    """
            Inventory Test - Send-Receive Workflow (Send-Receive items)
            @Case: INV003
            @param items: This test Send-Receive a specific item to another party.
        This test assume that test/inv-mngt has been added to prepop
        - e.g. via demo/IFRC_Train

            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
    """

    def test_inv003_send_receive_items(self):
        """ Tests for Send-Receive - Receive Workflow """

        user = "admin"
        method = "search"
        send_data = [("site_id",
                 "Timor-Leste Red Cross Society (CVTL) National Warehouse (Warehouse)",
                ),
                 ("type",
                  "Internal Shipment",
                 ),
                ("to_site_id",
                 "Lospalos Warehouse (Warehouse)",
                ),
                ("sender_id",
                 "Beatriz de Carvalho",
                ),
                ("recipient_id",
                 "Liliana Otilia",
                )
               ]
        item_data = [
                     [("send_inv_item_id",
                       "Blankets - Australian Red Cross",
                       "inv_widget",
                      ),
                      ("quantity",
                       "8",
                      ),
                     ],
                     [("send_inv_item_id",
                       "Jerry Cans - Australian Red Cross",
                       "inv_widget",
                      ),
                      ("quantity",
                       "13",
                      ),
                     ],
                     [("send_inv_item_id",
                       "Kitchen Sets - Australian Red Cross",
                       "inv_widget",
                      ),
                      ("quantity",
                       "4",
                      ),
                     ]
                    ]
        recv_data = [
                     ["Blankets",
                       "8",
                      ],
                     ["Jerry Cans",
                       "13",
                      ],
                     ["Kitchen Sets",
                       "4",
                      ],
                     ]
        # Create the send record
        send_result = self.send(user, send_data)
        send_id = self.send_get_id(send_result)
        send_ref= self.send_get_ref(send_result)
        # Add the items to the send record
        cnt = 0
        for data in item_data:
            item_result = self.track_send_item(user, send_id, data)
            recv_data[cnt].append(item_result["after"].records[0])
            cnt += 1
        # Send the shipment
        self.send_shipment(user, send_id)
        # Receive the shipment
        self.recv_sent_shipment(method, user, send_ref, recv_data)

    def test_inv021_send_and_confirm(self):
        """ Test to send a shipment and confirm that it is receive outside of the system """
        user = "admin"
        method = "search"
        send_data = [("site_id",
                 "Timor-Leste Red Cross Society (CVTL) National Warehouse (Warehouse)",
                ),
                 ("type",
                  "Internal Shipment",
                 ),
                ("to_site_id",
                 "Lori (Facility)",
                ),
                ("sender_id",
                 "Beatriz de Carvalho",
                ),
               ]
        item_data = [
                     [("send_inv_item_id",
                       "Blankets - Australian Red Cross",
                       "inv_widget",
                      ),
                      ("quantity",
                       "6",
                      ),
                     ],
                     [("send_inv_item_id",
                       "Jerry Cans - Australian Red Cross",
                       "inv_widget",
                      ),
                      ("quantity",
                       "3",
                      ),
                     ],
                     [("send_inv_item_id",
                       "Kitchen Sets - Australian Red Cross",
                       "inv_widget",
                      ),
                      ("quantity",
                       "2",
                      ),
                     ]
                    ]
        # Create the send record
        send_result = self.send(user, send_data)
        send_id = self.send_get_id(send_result)
        send_ref= self.send_get_ref(send_result)
        # Add the items to the send record
        for data in item_data:
            item_result = self.track_send_item(user, send_id, data)
        # Send the shipment
        self.send_shipment(user, send_id)
        # Confirm Receipt of the shipment
        self.confirm_received_shipment(user, send_id)
# END =========================================================================
