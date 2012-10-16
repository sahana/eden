""" Sahana Eden Module Automated Tests - INV002 Receive Items

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

class ReceiveItem(InvTestFunctions):
    """
            Inventory Test - Receive Workflow (Receive items)
            @Case: INV002
            @param items: This test receives a specific item from another party.
        This test assume that regression/inv-mngt has been added to prepop
        - e.g. via demo/IFRC_Train
        
            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
    """

    # -------------------------------------------------------------------------
    def test_inv002a_receive_items(self):
        """ Tests for Receive Workflow """

        user = "admin"
        recv_data = [("send_ref",
                      "WB_TEST_000002a",
                     ),
                     ("purchase_ref",
                      "PO_TEST_000002a",
                     ),
                     ("site_id",
                      "Same Warehouse (Warehouse)",
                      "option",
                     ),
                     ("type",
                      "Internal Shipment",
                      "option",
                     ),
                     ("from_site_id",
                      "Ainaro Warehouse (Warehouse)",
                      "option",
                     ),
                    ]

        item_data = [
                     [
                      ("item_id",
                       "Blankets",
                       "supply_widget",
                      ),
                      ("item_pack_id",
                       "Piece",
                       "option",
                      ),
                      ("quantity",
                       "3",
                      ),
                     ]
                    ]

        # Create the receive shipment
        result = self.receive(user, recv_data)
        recv_id = self.recv_get_id(result)
        # Add items to the shipment
        item_list = []
        for data in item_data:
            result = self.track_recv_item(user, recv_id, data)
            text = "%s %s" % (data[2][1], data[0][1])
            item_list.append({"text": text,
                              "record":result["after"].records[0]
                             })
        # Receive the shipment
        self.recv_shipment(user, recv_id, item_list)

    def test_inv002b_receive_items(self):
        """ Tests for Receive Workflow """
        user = "admin"
        recv_data = [("send_ref",
                      "WB_TEST_000002b",
                     ),
                     ("purchase_ref",
                      "PO_TEST_000002b",
                     ),
                     ("site_id",
                      "Same Warehouse (Warehouse)",
                      "option",
                     ),
                     ("type",
                      "Internal Shipment",
                      "option",
                     ),
                     ("from_site_id",
                      "Timor-Leste Red Cross Society (CVTL) National Warehouse (Warehouse)",
                      "option",
                     ),
                    ]

        item_data = [
                     [
                      ("item_id",
                       "Blankets",
                       "supply_widget",
                      ),
                      ("item_pack_id",
                       "Piece",
                       "option",
                      ),
                      ("quantity",
                       "3",
                      ),
                     ]
                    ]

        # Create the receive shipment
        result = self.receive(user, recv_data)
        recv_id = self.recv_get_id(result)
        # Add items to the shipment
        item_list = []
        for data in item_data:
            result = self.track_recv_item(user, recv_id, data)
            text = "%s %s" % (data[2][1], data[0][1])
            item_list.append({"text": text,
                              "record":result["after"].records[0]
                             })
        # Receive the shipment
        self.recv_shipment(user, recv_id, item_list)