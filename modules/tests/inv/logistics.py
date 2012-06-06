from gluon import current
from tests.web2unittest import SeleniumUnitTest
from selenium.common.exceptions import NoSuchElementException
from s3 import s3_debug

class Logistics(SeleniumUnitTest):
    """
        These tests assume that regression/inv-mngt has been added to prepop
        - e.g. via demo/IFRC_Train
    """

    # -------------------------------------------------------------------------
    def helper_inv_send(self, user, data):
        """
            Helper method to add a inv_send record by the given user
        """
        self.login(account=user, nexturl="inv/send/create")
        table = "inv_send"
        result = self.create(table, data)
        s3_debug("WB reference: %s" % self.helper_inv_send_get_ref(result))
        return result

    # -------------------------------------------------------------------------
    def helper_inv_send_rec(self, result):
        """
            Simple helper function to get the waybill reference of the newly
            created inv_send row so it can be used to filter dataTables
        """
        # The newly created inv_send will be the first record in the "after" list
        if len(result["after"]) > 0:
            new_inv_send = result["after"].records[0]
            return new_inv_send.inv_send
        return None

    # -------------------------------------------------------------------------
    def helper_inv_send_get_id(self, result):
        """
            Simple helper function to get the waybill reference of the newly
            created inv_send row so it can be used to filter dataTables
        """
        # The newly created inv_send will be the first record in the "after" list
        if len(result["after"]) > 0:
            new_inv_send = result["after"].records[0]
            return new_inv_send.inv_send.id
        return None

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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
            if details[0] == "send_inv_item_id":
                inv_item_id = details[1]
                break
        stock_row = table[inv_item_id]
        rows.records.append(stock_row)
        return rows

    # -------------------------------------------------------------------------
    def test_send_workflow(self):
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
        result = self.helper_inv_track_item("normal", send_id, data)
        data = [("send_inv_item_id",
                 "Jerry Cans - 123461 - Australian Red Cross",
                 "inv_widget",
                ),
                ("quantity",
                 "7",
                ),
               ]
        result = self.helper_inv_track_item("normal", send_id, data)

# def test_inventory(self):
# """ Tests for Inventory """
#
# browser = self.browser
#
# # Login
# self.login()
#
# # Open Inv module
# url = "%s/inv/inv_item" % self.url
# url = "%s/inv/warehouse" % self.url
# browser.get(url)
#
# # Check that the inventory is correct.
# (start, end, length) = self.dt_row_cnt(check=(1,6,6), quiet=False)
# # look for the entries in Lospalos Warehouse
# warehouse = "Lospalos Warehouse"
# self.assertTrue(self.dt_filter(warehouse), "DataTable not working correctly")
#
# (start, end, total, filtered) = self.dt_row_cnt(check=(1,1,1,6), quiet=False)
# self.assertTrue(self.dt_filter(), "DataTable not working correctly")
# (start, end, length) = self.dt_row_cnt(check=(1,6,6))
#
# links = self.dt_links(quiet=False)
#
# records = self.dt_data()
# warehouse_found = False
# tried = []
# for cnt, line in enumerate(records):
# if warehouse in line:
# tried.append(cnt)
# if self.dt_action(cnt+1,"Details"):
# warehouse_found = True
# break
# self.assertTrue(not warehouse_found, "Unable to locate warehouse %s, tried to click rows %s" % (warehouse, tried))
#
# # Having opened the Lospalos warehouse
# # After a prepop the warehouse should have:
# # 4200 plastic sheets from Australia RC
# # 2000 plastic sheets from Acme
# match = self.dt_find("Plastic Sheets")
# if match:
# if not self.dt_find(4200, cellList=match, column=5, first=True):
# assert 0, "Unable to find 4200 Plastic Sheets"
# if not self.dt_find(2000, cellList=match, column=5, first=True):
# assert 0, "Unable to find 2000 Plastic Sheets"
# else:
# assert 0, "Unable to find any Plastic Sheets"
#
#
# # -----------------------------------------------------------------------------
# def test_requests(self):
# """ Tests for Requests """
#
# browser = self.browser
#
# # Login
# self.login()
#
# # Open Request module
# url = "%s/req/req/create" % self.url
# browser.get(url)
# self.w_autocomplete("Beatriz de C",
# "req_req_requester",
# "Beatriz de Carvalho",
# )
# 