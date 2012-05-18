from tests.web2unittest import SeleniumUnitTest

class Logistics(SeleniumUnitTest):
    # These tests assume that regression/inv-mngt has been added to prepop
    # -----------------------------------------------------------------------------
    def send(self):
        """ Test for sending inventory items from one site to another """
        browser = self.browser
        self.login()
        # Open Send Create page
        url = "%s/inv/send/create" % self.url
        browser.get(url)

        el = browser.find_element_by_id("inv_send_site_id")
        for option in el.find_elements_by_tag_name("option"):
            if option.text == "Cruz Vermelha de Timor-Leste (CVTL) National Warehouse (Warehouse)":
                option.click()
        el = browser.find_element_by_id("inv_send_to_site_id")
        for option in el.find_elements_by_tag_name("option"):
            if option.text == "Lospalos Warehouse (Warehouse)":
                option.click()
        self.w_autocomplete("Beatriz de C",
                            "inv_send_sender",
                            "Beatriz de Carvalho",
                            )
        self.w_autocomplete("Liliana  Otilia",
                            "inv_send_recipient",
                            )
        browser.find_element_by_css_selector("input[type=\"submit\"]").click()

    def test_001_send(self):
        """ Tests for Send Workflow """
        self.send()

    def test_inventory(self):
        """ Tests for Inventory """

        browser = self.browser

        # Login
        self.login()

        # Open Inv module
        url = "%s/inv/inv_item" % self.url
        url = "%s/inv/warehouse" % self.url
        browser.get(url)

        # Check that the inventory is correct.
        (start, end, length) = self.dt_row_cnt(check=(1,6,6), quiet=False)
        # look for the entries in Lospalos Warehouse
        warehouse = "Lospalos Warehouse"
        self.assertTrue(self.dt_filter(warehouse), "DataTable not working correctly")

        (start, end, total, filtered) = self.dt_row_cnt(check=(1,1,1,6), quiet=False)
        self.assertTrue(self.dt_filter(), "DataTable not working correctly")
        (start, end, length) = self.dt_row_cnt(check=(1,6,6))

        links = self.dt_links(quiet=False)

        records = self.dt_data()
        warehouse_found = False
        tried = []
        for cnt, line in enumerate(records):
            if warehouse in line:
                tried.append(cnt)
                if self.dt_action(cnt+1,"Details"):
                    warehouse_found = True
                    break
        self.assertTrue(not warehouse_found, "Unable to locate warehouse %s, tried to click rows %s" % (warehouse, tried))

        # Having opened the Lospalos warehouse
        # After a prepop the warehouse should have:
        #    4200 plastic sheets from Australia RC
        #    2000 plastic sheets from Acme
        match = self.dt_find("Plastic Sheets")
        if match:
            if not self.dt_find(4200, cellList=match, column=5, first=True):
                assert 0, "Unable to find 4200 Plastic Sheets"
            if not self.dt_find(2000, cellList=match, column=5, first=True):
                assert 0, "Unable to find 2000 Plastic Sheets"
        else:
            assert 0, "Unable to find any Plastic Sheets"


    # -----------------------------------------------------------------------------
    def test_requests(self):
        """ Tests for Requests """

        browser = self.browser

        # Login
        self.login()

        # Open Request module
        url = "%s/req/req/create" % self.url
        browser.get(url)
        self.w_autocomplete("Beatriz de C",
                            "req_req_requester",
                            "Beatriz de Carvalho",
                            )
        