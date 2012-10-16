__all__ = ["send",
           "track_send_item",
           "send_shipment",
           "receive",
           "track_recv_item",
           "recv_shipment",
           "recv_sent_shipment",
           "send_rec",
           "send_get_id",
           "send_get_ref",
           "recv_rec",
           "recv_get_id",
           "dbcallback_getStockLevels",
           ]

from gluon import current

from s3 import s3_debug

from tests.web2unittest import SeleniumUnitTest

class InvTestFunctions(SeleniumUnitTest):

    def send(self, user, data):
        """
            @case: INV
            @description: Functions which runs specific workflows for Inventory tes
            
            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """
        print "\n"
        
        """
            Helper method to add a inv_send record by the given user
        """

        self.login(account=user, nexturl="inv/send/create")
        table = "inv_send"
        result = self.create(table, data)
        s3_debug("WB reference: %s" % self.send_get_ref(result))
        return result

    # -------------------------------------------------------------------------
    def track_send_item(self, user, send_id, data, removed=True):
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
    def send_shipment(self, user, send_id):
        """
            Helper method to send a shipment with id of send_id
        """

        db = current.db
        s3db = current.s3db
        stable = s3db.inv_send
        ititable = s3db.inv_track_item
        # Get the current status
        query = (stable.id == send_id)
        record = db(query).select(stable.status,
                      limitby=(0, 1)).first()
        send_status = record.status
        query = (ititable.send_id == send_id)
        item_records = db(query).select(ititable.status)
        # check that the status is correct
        self.assertTrue(send_status == 0, "Shipment is not status preparing")
        s3_debug("Shipment status is: preparing")
        for rec in item_records:
            self.assertTrue(rec.status == 1, "Shipment item is not status preparing")
        s3_debug("Shipment items are all of status: preparing")

        # Now send the shipment on its way
        self.login(account=user, nexturl="inv/send_process/%s" % send_id)

        # Get the current status
        query = (stable.id == send_id)
        record = db(query).select(stable.status,
                                  limitby=(0, 1)).first()
        send_status = record.status
        query = (ititable.send_id == send_id)
        item_records = db(query).select(ititable.status)
        # check that the status is correct
        self.assertTrue(send_status == 2, "Shipment is not status sent")
        s3_debug("Shipment status is: sent")
        for rec in item_records:
            self.assertTrue(rec.status == 2, "Shipment item is not status sent")
        s3_debug("Shipment items are all of status: sent")

    # -------------------------------------------------------------------------
    def confirm_received_shipment(self, user, send_id):
        """
            Helper method to confirm that a shipment has been received
            outside of the system. This means that the items in the
            shipment will not be recorded as being at a site but
            the status of the shipment will be modified.
        """

        db = current.db
        s3db = current.s3db
        stable = s3db.inv_send
        ititable = s3db.inv_track_item
        # Get the current status
        query = (stable.id == send_id)
        record = db(query).select(stable.status,
                      limitby=(0, 1)).first()
        send_status = record.status
        query = (ititable.send_id == send_id)
        item_records = db(query).select(ititable.status)
        # check that the status is correct
        self.assertTrue(send_status == 2, "Shipment is not status sent")
        s3_debug("Shipment status is: preparing")
        for rec in item_records:
            self.assertTrue(rec.status == 2, "Shipment item is not status sent")
        s3_debug("Shipment items are all of status: sent")

        # Now send the shipment on its way
        self.login(account=user, nexturl="inv/send/%s?received=True" % send_id)

        # Get the current status
        query = (stable.id == send_id)
        record = db(query).select(stable.status,
                      limitby=(0, 1)).first()
        send_status = record.status
        query = (ititable.send_id == send_id)
        item_records = db(query).select(ititable.status)
        # check that the status is correct
        self.assertTrue(send_status == 1, "Shipment is not status received")
        s3_debug("Shipment status is: sent")
        for rec in item_records:
            self.assertTrue(rec.status == 4, "Shipment item is not status arrived")
        s3_debug("Shipment items are all of status: arrived")

    # -------------------------------------------------------------------------
    def receive(self, user, data):
        """
            Helper method to add a inv_send record by the given user
        """

        self.login(account=user, nexturl="inv/recv/create")
        table = "inv_recv"
        result = self.create(table, data)
        return result

    # -------------------------------------------------------------------------
    def track_recv_item(self, user, recv_id, data, removed=True):
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

    # -------------------------------------------------------------------------
    def recv_shipment(self, user, recv_id, data):
        """
            Helper method that will receive the shipment, adding the
            totals that arrived
    
            It will get the stock in the warehouse before and then after
            and check that the stock levels have been properly increased
        """

        db = current.db
        s3db = current.s3db
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

    # -------------------------------------------------------------------------
    def recv_sent_shipment(self, method, user, WB_ref, item_list):
        """
            Helper method that will receive the sent shipment.
    
            This supports two methods:
            method = "warehouse"
            ====================
            This requires going to the receiving warehouse
            Selecting the shipment (using the WB reference)
            Opening each item and selecting the received totals
            Then receive the shipment
    
            method = "search"
            ====================
            Search for all received shipments
            Select the matching WB reference
            Opening each item and selecting the received totals
            Then receive the shipment
    
            Finally:
            It will get the stock in the warehouse before and then after
            and check that the stock levels have been properly increased
        """

        browser = self.browser
        if method == "search":
            self.login(account=user, nexturl="inv/recv/search")
            # Find the WB reference in the dataTable (filter so only one is displayed)
            el = browser.find_element_by_id("recv_search_simple")
            el.send_keys(WB_ref)
            # Submit the search
            browser.find_element_by_css_selector("input[type='submit']").submit()
            # Select the only row in the dataTable
            if not self.dt_action():
                fail("Unable to select the incoming shipment with reference %s" % WB_ref)
        elif method == "warehouse":
                return # not yet implemented
        else:
            fail("Unknown method of %s" % method)
            return # invalid method
        #####################################################
        # We are now viewing the details of the receive item
        #####################################################
    
        # Now get the recv id from the url
        url = browser.current_url
        url_parts = url.split("/")
        try:
            recv_id = int(url_parts[-1])
        except:
            recv_id = int(url_parts[-2])
        # Click on the items tab
        self.login(account=user, nexturl="inv/recv/%s/track_item" % recv_id)
        data = []
        for item in item_list:
            # Find the item in the dataTable
            self.dt_filter(item[0])
            self.dt_action()
            el = browser.find_element_by_id("inv_track_item_recv_quantity")
            el.send_keys(item[1])
            text = "%s %s" % (item[1], item[0])
            data.append({"text" : text,
                 "record" : item[2]})
            # Save the form
            browser.find_element_by_css_selector("input[type='submit']").submit()
        # Now receive the shipment and check the totals
        self.recv_shipment(user, recv_id, data)

    # -------------------------------------------------------------------------
    # Functions which extract data from the create results
    #
    def send_rec(self, result):
        """
            Simple helper function to get the newly created inv_send row
        """

        # The newly created inv_send will be the first record in the "after" list
        if len(result["after"]) > 0:
            new_inv_send = result["after"].records[0]
            return new_inv_send.inv_send
        return None

    def send_get_id(self, result):
        """
            Simple helper function to get the record id of the newly
            created inv_send row so it can be used to open the record
        """

        # The newly created inv_send will be the first record in the "after" list
        if len(result["after"]) > 0:
            new_inv_send = result["after"].records[0]
            return new_inv_send.inv_send.id
        return None

    def send_get_ref(self, result):
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
    def recv_rec(self, result):
        """
            Simple helper function to get the newly created inv_recv row
        """

        # The newly created inv_recv will be the first record in the "after" list
        if len(result["after"]) > 0:
            new_inv_recv = result["after"].records[0]
            return new_inv_recv.inv_recv
        return None

    # -------------------------------------------------------------------------
    def recv_get_id(self, result):
        """
            Simple helper function to get the record id of the newly
            created inv_recv row so it can be used to open the record
        """

        # The newly created inv_recv will be the first record in the "after" list
        if len(result["after"]) > 0:
            new_inv_recv = result["after"].records[0]
            return new_inv_recv.inv_recv.id
        return None

    # -------------------------------------------------------------------------
    # Callback used to retrieve additional data to the create results
    #
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

# END =========================================================================
