from gluon import current
from tests.web2unittest import SeleniumUnitTest
from selenium.common.exceptions import NoSuchElementException
from s3 import s3_debug

class Logistics(SeleniumUnitTest):
    """
        These tests assume that regression/inv-mngt has been added to prepop
        - e.g. via demo/IFRC_Train
    """

    ########################################################################
    # Functions which runs specific workflows
    ########################################################################
    def helper_inv_send(self, user, data):
        """
            Helper method to add a inv_send record by the given user
        """
        self.login(account=user, nexturl="inv/send/create")
        table = "inv_send"
        result = self.create(table, data)
        s3_debug("WB reference: %s" % self.helper_inv_send_get_ref(result))
        return result

    def helper_inv_track_send_item(self, user, send_id, data, removed=True):
        """
            Helper method to add a track item to the inv_send with the
            given send_id by the given user
        """
        try:
            add_btn = self.browser.find_element_by_id("show-add-btn")
            if add_btn.is_displayed():
                add_btn.click()
        except:
            pass
        self.login(account=user, nexturl="inv/send/%s/track_item" % send_id)
        table = "inv_track_item"
        result = self.create(table, data, dbcallback = self.dbcallback_getStockLevels)
        # Get the last record in the before & after
        # this will give the stock record which has been added to the end by
        # the getStockLevels callback
        if removed:
            qnty = 0
            for line in data:
                if line[0] == "quantity":
                    qnty = float(line[1])
                    break
            stock_before = result["before"].records[len(result["before"])-1].quantity
            stock_after = result["after"].records[len(result["after"])-1].quantity
            stock_shipped = qnty
            self.assertTrue( stock_before - stock_after == stock_shipped, "Warehouse stock not properly adjusted, was %s should be %s but is recorded as %s" % (stock_before, stock_after, stock_before - stock_shipped))
            s3_debug ("Stock level before %s, stock level after %s" % (stock_before, stock_after))
        return result

    def helper_inv_receive(self, user, data):
        """
            Helper method to add a inv_send record by the given user
        """
        self.login(account=user, nexturl="inv/recv/create")
        table = "inv_recv"
        result = self.create(table, data)
        return result

    def helper_inv_track_recv_item(self, user, recv_id, data, removed=True):
        """
            Helper method to add a track item to the inv_recv with the
            given recv_id
        """
        try:
            add_btn = self.browser.find_element_by_id("show-add-btn")
            if add_btn.is_displayed():
                add_btn.click()
        except:
            pass
        self.login(account=user, nexturl="inv/recv/%s/track_item" % recv_id)
        table = "inv_track_item"
        result = self.create(table, data)
        return result

    def helper_inv_recv_shipment(self, user, recv_id, data):
        """
            Helper method that will receive the shipment, adding the
            totals that arrived

            It will get the stock in the warehouse before and then after
            and check that the stock levels have been properly increased
        """
        s3db = current.s3db
        db = current.db
        rvtable = s3db.inv_recv
        iitable = s3db.inv_inv_item
        # First get the site_id
        query = (rvtable.id == recv_id)
        record = db(query).select(rvtable.site_id,
                                  limitby=(0, 1)).first()
        site_id = record.site_id
        # Now get all the inventory items for the site
        query = (iitable.site_id == site_id)
        before = db(query).select(orderby=iitable.id)
        self.login(account=user, nexturl="inv/recv_process/%s" % recv_id)
        query = (iitable.site_id == site_id)
        after = db(query).select(orderby=iitable.id)
        # Find the differences between the before and the after
        changes = []
        for a_rec in after:
            found = False
            for b_rec in before:
                if a_rec.id == b_rec.id:
                    if a_rec.quantity != b_rec.quantity:
                        changes.append(
                                       (a_rec.item_id,
                                        a_rec.item_pack_id,
                                        a_rec.quantity - b_rec.quantity)
                                      )
                    found = True
                    break
            if not found:
                changes.append(
                               (a_rec.item_id,
                                a_rec.item_pack_id,
                                a_rec.quantity)
                              )
        # changes now contains the list of changed or new records
        # these should match the records received
        # first check are the lengths the same?
        self.assertTrue(len(data) == len(changes),
                        "The number of changed inventory items (%s) doesn't match the number of items received  (%s)." %
                        (len(changes), len(data))
                       )
        for line in data:
            rec = line["record"]
            found = False
            for change in changes:
                if rec.inv_track_item.item_id == change[0] and \
                   rec.inv_track_item.item_pack_id == change[1] and \
                   rec.inv_track_item.quantity == change[2]:
                    found = True
                    break
            if found:
                s3_debug("%s accounted for." % line["text"])
            else:
                s3_debug("%s not accounted for." % line["text"])
            

    ########################################################################
    # Functions which extract data from the create results
    ########################################################################
    def helper_inv_send_rec(self, result):
        """
            Simple helper function to get the newly created inv_send row
        """
        # The newly created inv_send will be the first record in the "after" list
        if len(result["after"]) > 0:
            new_inv_send = result["after"].records[0]
            return new_inv_send.inv_send
        return None

    def helper_inv_send_get_id(self, result):
        """
            Simple helper function to get the record id of the newly
            created inv_send row so it can be used to open the record
        """
        # The newly created inv_send will be the first record in the "after" list
        if len(result["after"]) > 0:
            new_inv_send = result["after"].records[0]
            return new_inv_send.inv_send.id
        return None

    def helper_inv_send_get_ref(self, result):
        """
            Simple helper function to get the waybill reference of the newly
            created inv_send row so it can be used to filter dataTables
        """
        # The newly created inv_send will be the first record in the "after" list
        if len(result["after"]) > 0:
            new_inv_send = result["after"].records[0]
            return new_inv_send.inv_send.send_ref
        return None

    def helper_inv_recv_rec(self, result):
        """
            Simple helper function to get the newly created inv_recv row
        """
        # The newly created inv_recv will be the first record in the "after" list
        if len(result["after"]) > 0:
            new_inv_recv = result["after"].records[0]
            return new_inv_recv.inv_recv
        return None

    def helper_inv_recv_get_id(self, result):
        """
            Simple helper function to get the record id of the newly
            created inv_recv row so it can be used to open the record
        """
        # The newly created inv_recv will be the first record in the "after" list
        if len(result["after"]) > 0:
            new_inv_recv = result["after"].records[0]
            return new_inv_recv.inv_recv.id
        return None

    ########################################################################
    # Callback used to retrieve additional data to the create results
    ########################################################################
    def dbcallback_getStockLevels(self, table, data, rows):
        """
            Callback to add the total in stock for the selected item.

            This can then be used to look at the value before and after
            to ensure that the totals have been removed from the warehouse.
            The stock row will be added to the *end* of the list of rows
        """
        table = current.s3db["inv_inv_item"]
        for details in data:
            if details[0] == "send_inv_item_id":
                inv_item_id = details[1]
                break
        stock_row = table[inv_item_id]
        rows.records.append(stock_row)
        return rows

    def test010_send_workflow(self):
        """ Tests for Send Workflow """
        data = [("site_id",
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
        result = self.helper_inv_send("normal", data)
        send_id = self.helper_inv_send_get_id(result)

        data = [("send_inv_item_id",
                 "Blankets - 123457 - Australian Red Cross",
                 "inv_widget",
                ),
                ("quantity",
                 "3",
                ),
               ]
        result = self.helper_inv_track_send_item("normal", send_id, data)
        data = [("send_inv_item_id",
                 "Jerry Cans - 123461 - Australian Red Cross",
                 "inv_widget",
                ),
                ("quantity",
                 "7",
                ),
               ]
        result = self.helper_inv_track_send_item("normal", send_id, data)

    def test020_receive_workflow(self):
        """ Tests for Receive Workflow """
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

        item_data = [("item_id",
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

        # Create the receive shipment
        result = self.helper_inv_receive("normal", recv_data)
        recv_id = self.helper_inv_recv_get_id(result)
        # Add items to the shipment
        item_list = []
        result = self.helper_inv_track_recv_item("normal", recv_id, item_data)
        text = "%s %s" % (item_data[2][1], item_data[0][1])
        item_list.append({"text": text,
                          "record":result["after"].records[0]
                         })
        # Receive the shipment
        self.helper_inv_recv_shipment("normal", recv_id, item_list)
