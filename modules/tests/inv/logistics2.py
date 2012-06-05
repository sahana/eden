from gluon import current
from tests.web2unittest import SeleniumUnitTest
from selenium.common.exceptions import NoSuchElementException
from tests import *


class Logistics2(SeleniumUnitTest):
    # These tests assume that regression/inv-mngt has been added to prepop
    # -----------------------------------------------------------------------------

    def helper_inv_receive(self, user, data):
        """
Helper method to add a inv_send record by the given user
"""
        self.login(account=user, nexturl="inv/recv/create")
        table = "inv_recv"
        result = self.create(table, data)
        return result

    def helper_inv_send_rec(self, result):
        """
Simple helper function to get the waybill reference of the newly
created inv_send row so it can be used to filter dataTables
"""
        # The newly created inv_recv will be the first record in the "after" list
        if len(result["after"]) > 0:
            new_inv_recv = result["after"].records[0]
            return new_inv_recv.inv_recv
        return None

    def helper_inv_recv_get_id(self, result):
        """
Simple helper function to get the waybill reference of the newly
created inv_send row so it can be used to filter dataTables
"""
        # The newly created inv_recv will be the first record in the "after" list
        if len(result["after"]) > 0:
            new_inv_recv = result["after"].records[0]
            return new_inv_recv.inv_recv.id
        return None

    def helper_inv_send_get_ref(self, result):
        """
Simple helper function to get the waybill reference of the newly
created inv_send row so it can be used to filter dataTables
"""
        # The newly created inv_recv will be the first record in the "after" list
        if len(result["after"]) > 0:
            new_inv_recv = result["after"].records[0]
            return new_inv_recv.inv_send.send_ref
        return None


    def helper_inv_track_item(self, user, send_id, data, removed=True):
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
        self.login(account=user, nexturl="inv/recv/%s/track_item" % send_id)
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
            self.assertTrue( stock_before == stock_after, "Warehouse stock has been adjusted, from %s to %s, nothing should have been removed" % (stock_before, stock_after))
        return result
    
    def helper_inv_recv_shipment(self, user, send_id, data, removed=True):
        
        self.login(account=user, nexturl="inv/recv_process/%s" % send_id)


    # dbcallback for the inv_track item create function
    def dbcallback_getStockLevels(self, table, data, rows):
        """
Callback to add the total in stock for the selected item.

This can then be used to look at the value before and after
to ensure that the totals have been removed from the warehouse.
The stock row will be added to the *end* of the list of rows
"""
        table = current.s3db["inv_inv_item"]
        for details in data:
            if details[0] == "item_id":
                inv_item_id = details[1]
                break
        stock_row = table[inv_item_id]
        rows.records.append(stock_row)
        return rows

    def test_receive_workflow(self):
        """ Tests for Receive Workflow """
        data = [("send_ref",
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
        result = self.helper_inv_receive("normal", data)
        send_id = self.helper_inv_recv_get_id(result)

        data = [("item_id",
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
        result = self.helper_inv_track_item("normal", send_id, data)
        result = self.helper_inv_recv_shipment("normal", send_id, data)
        
        
