from tests.web2unittest import SeleniumUnitTest
from selenium.common.exceptions import NoSuchElementException


class Logistics(SeleniumUnitTest):
    # These tests assume that regression/inv-mngt has been added to prepop
    # -----------------------------------------------------------------------------

    def test_001_send(self):
        """ Tests for Send Workflow """
        self.login(account="normal", nexturl="inv/send/create")
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
        table = "inv_send"
        result = self.create(table, data)
        data = [("send_inv_item_id",
                 "Blankets - 123457 - Australian Red Cross",
                 "option",
                ),
                ("quantity",
                 "3",
                ),
               ]
        table = "inv_track_item"
        result = self.create(table, data, dbcallback = self.getStockLevels)
        # Get the last record in the before & after (it should give the stock
        stock_before = result["before"].records[len(result["before"])-1].quantity
        stock_after = result["after"].records[len(result["after"])-1].quantity
        stock_shipped = 3
        self.assertTrue( stock_before - stock_after == stock_shipped, "Warehouse stock not properly adjusted, was %s should be %s but is recorded as %s" % (stock_before, stock_after, stock_before - stock_shipped))
        return result

    def getStockLevels(self, table, data, rows):
        table = self.current.s3db["inv_inv_item"]
        for details in data:
            if details[0] == "send_inv_item_id":
                inv_item_id = details[1]
                break
        stock_row = table[inv_item_id]
        rows.records.append(stock_row)
        return rows

#    def test_inventory(self):
#        """ Tests for Inventory """
#
#        browser = self.browser
#
#        # Login
#        self.login()
#
#        # Open Inv module
#        url = "%s/inv/inv_item" % self.url
#        url = "%s/inv/warehouse" % self.url
#        browser.get(url)
#
#        # Check that the inventory is correct.
#        (start, end, length) = self.dt_row_cnt(check=(1,6,6), quiet=False)
#        # look for the entries in Lospalos Warehouse
#        warehouse = "Lospalos Warehouse"
#        self.assertTrue(self.dt_filter(warehouse), "DataTable not working correctly")
#
#        (start, end, total, filtered) = self.dt_row_cnt(check=(1,1,1,6), quiet=False)
#        self.assertTrue(self.dt_filter(), "DataTable not working correctly")
#        (start, end, length) = self.dt_row_cnt(check=(1,6,6))
#
#        links = self.dt_links(quiet=False)
#
#        records = self.dt_data()
#        warehouse_found = False
#        tried = []
#        for cnt, line in enumerate(records):
#            if warehouse in line:
#                tried.append(cnt)
#                if self.dt_action(cnt+1,"Details"):
#                    warehouse_found = True
#                    break
#        self.assertTrue(not warehouse_found, "Unable to locate warehouse %s, tried to click rows %s" % (warehouse, tried))
#
#        # Having opened the Lospalos warehouse
#        # After a prepop the warehouse should have:
#        #    4200 plastic sheets from Australia RC
#        #    2000 plastic sheets from Acme
#        match = self.dt_find("Plastic Sheets")
#        if match:
#            if not self.dt_find(4200, cellList=match, column=5, first=True):
#                assert 0, "Unable to find 4200 Plastic Sheets"
#            if not self.dt_find(2000, cellList=match, column=5, first=True):
#                assert 0, "Unable to find 2000 Plastic Sheets"
#        else:
#            assert 0, "Unable to find any Plastic Sheets"
#
#
#    # -----------------------------------------------------------------------------
#    def test_requests(self):
#        """ Tests for Requests """
#
#        browser = self.browser
#
#        # Login
#        self.login()
#
#        # Open Request module
#        url = "%s/req/req/create" % self.url
#        browser.get(url)
#        self.w_autocomplete("Beatriz de C",
#                            "req_req_requester",
#                            "Beatriz de Carvalho",
#                            )
#        