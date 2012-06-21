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

from gluon import current
import unittest
from tests.web2unittest import SeleniumUnitTest
from selenium.common.exceptions import NoSuchElementException
from s3 import s3_debug
from helper import InvTestFunctions

class InvSendItem(InvTestFunctions):

    """
            Inventory Test - Send Workflow (Send items)
            
            @param items: This test sends a specific item to another party.
        This test assume that regression/inv-mngt has been added to prepop
        - e.g. via demo/IFRC_Train
        
            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
    """

    # -------------------------------------------------------------------------
    def test_inv001_send_items(self):
        """ Tests for Send Workflow """
        user = "normal"
        self.login(account=user, nexturl="inv/send/create")
        send_data = [("site_id",
                 "Cruz Vermelha de Timor-Leste (CVTL) National Warehouse (Warehouse)",
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
                     [("send_inv_item_id",
                       "Jerry Cans - 123461 - Australian Red Cross",
                       "inv_widget",
                      ),
                      ("quantity",
                       "7",
                      ),
                     ],
                    ]

        result = self.helper_inv_send(user, send_data)
        send_id = self.helper_inv_send_get_id(result)
        for data in item_data:
            result = self.helper_inv_track_send_item(user, send_id, data)
        # Send the shipment
        self.helper_inv_send_shipment(user, send_id)

    # -------------------------------------------------------------------------
    def test020_receive_workflow(self):
        """ Tests for Receive Workflow """
        user = "normal"
        recv_data = [("send_ref",
                      "WB_TEST_000001",
                     ),
                     ("purchase_ref",
                      "PO_TEST_000001",
                     ),
                     ("site_id",
                      "Same Warehouse",
                      "autocomplete",
                     ),
                     ("type",
                      "Other Warehouse",
                      "option",
                     )
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
        result = self.helper_inv_receive(user, recv_data)
        recv_id = self.helper_inv_recv_get_id(result)
        # Add items to the shipment
        item_list = []
        for data in item_data:
            result = self.helper_inv_track_recv_item(user, recv_id, data)
            text = "%s %s" % (data[2][1], data[0][1])
            item_list.append({"text": text,
                              "record":result["after"].records[0]
                             })
        # Receive the shipment
        self.helper_inv_recv_shipment(user, recv_id, item_list)

    def test030_receive_workflow(self):
        """ Tests for Send - Receive Workflow """
        user = "normal"
        method = "search"
        send_data = [("site_id",
                 "Cruz Vermelha de Timor-Leste (CVTL) National Warehouse (Warehouse)",
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
                       "8",
                      ),
                     ],
                     [("send_inv_item_id",
                       "Jerry Cans - 123461 - Australian Red Cross",
                       "inv_widget",
                      ),
                      ("quantity",
                       "13",
                      ),
                     ],
                     [("send_inv_item_id",
                       "Kitchen Sets - 123458 - Australian Red Cross",
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
        send_result = self.helper_inv_send(user, send_data)
        send_id = self.helper_inv_send_get_id(send_result)
        send_ref= self.helper_inv_send_get_ref(send_result)
        # Add the items to the send record
        cnt = 0
        for data in item_data:
            item_result = self.helper_inv_track_send_item(user, send_id, data)
            recv_data[cnt].append(item_result["after"].records[0])
            cnt += 1
        # Send the shipment
        self.helper_inv_send_shipment(user, send_id)
        # Receive the shipment
        self.helper_inv_recv_sent_shipment(method, user, send_ref, recv_data)

# END =========================================================================
