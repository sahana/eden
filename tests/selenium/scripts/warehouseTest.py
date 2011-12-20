from sahanaTest import SahanaTest
import unittest, re, time

class WarehouseTest(SahanaTest):
    """ Test the Warehouse component of the Inventory Management System """
    _sortList = ("addWarehouses",
                 "stockWarehouse",
                 #"removeWarehouses",
                )
    
    def firstRun(self):
        WarehouseTest.warehouses = []
        WarehouseTest.orgs = []
        # Setup the template for the Warehouse From
        WarehouseTest.warehouseCreateTemplate = self.action.getFormTemplate()
        WarehouseTest.warehouseCreateTemplate.addInput(labelID="org_office_name__label",
                                                       inputID="org_office_name")


    def createWarehouse(self, name, organisation,
                        country, state=None, district=None,
                        lat=None, lon=None, address=None,
                        phone=None, email=None, comment=None):
        sel = self.selenium

        name = name.strip()
        organisation = organisation.strip()
        country = country.strip()
        state = state.strip()
        district = district.strip()
        lat = lat.strip()
        lon = lon.strip()
        address = address.strip()
        phone = phone.strip()
        email = email.strip()
        comment = comment.strip()

        if organisation not in self.orgs:
            self.action.openPage("org/organisation")
            matches = self.action.searchMatchesFound(organisation)
            if matches == 0:
                self.createOrganisation(organisation)
            self.orgs.append(organisation)
        
        self.action.openPage("inv/warehouse/create")
        self.assertEqual("Add Warehouse", sel.get_text("//h2"))

        self.action.fillForm("org_office_name", name)
        self.action.fillAutoComplete("dummy_org_office_organisation_id", organisation)
        self.action.fillForm("gis_location_L0", country, "select")
        self.action.fillForm("gis_location_L1", state)
        self.action.fillForm("gis_location_L2", district)
        self.action.fillForm("gis_location_lat", lat)
        self.action.fillForm("gis_location_street", address)
        self.action.fillForm("gis_location_lon", lon)
        self.action.fillForm("org_office_phone1", phone)
        self.action.fillForm("org_office_email", email)
        self.action.fillForm("org_office_comments", comment)

        # Now save the form
        self.assertTrue(self.action.saveForm("Save", "Warehouse added"))
        print "Warehouse %s created" % name

    def createOrganisation(self, name):
        sel = self.selenium

        name = name.strip()

        self.action.openPage("org/organisation/create")
        self.assertEqual("Add Organization", sel.get_text("//h2"))

        self.action.fillForm("org_organisation_name", name)

        # Now save the form
        self.assertTrue(self.action.saveForm("Save", "Organization added"))
        print "Organization %s created" % name

    def addWarehouses(self):
        # Log in as admin an then move to the add warehouse page
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password)
        # Add the test warehouses
        source = open("../data/warehouse.txt", "r")
        values = source.readlines()
        source.close()
        self.action.openPage("inv/warehouse")
        for warehouse in values:
            details = warehouse.split(",")
            if len(details) == 11:
                name = details[0].strip()
                matches = self.action.searchMatchesFound(name)
                if matches == 0:
                    self.createWarehouse(name,
                                         details[1].strip(),
                                         details[2].strip(),
                                         details[3].strip(),
                                         details[4].strip(),
                                         details[5].strip(),
                                         details[6].strip(),
                                         details[7].strip(),
                                         details[8].strip(),
                                         details[9].strip(),
                                         details[10].strip(),
                                         )
                self.warehouses.append(name)
    
    def addItem(self, warehouse, item, size, quantity, expireDate, comments):
        """
            Add an Item to a Warehouse
            @ToDo: Currently this does it by going to a URL without a menu entry
                   This should eb changed to doing it via the Warehouse's Inventory Items tab
        """
        sel = self.selenium
        self.action.openPage("inv/inv_item")
        sel.click("show-add-btn")
        self.assertEqual("List Items in Inventory", sel.get_text("//h2"))

        self.action.fillForm("inv_inv_item_site_id", warehouse, "select")
        self.action.fillForm("inv_inv_item_item_id", item, "select")
        # Pause to let the select box be filled up
        for i in range(30):
            if size in sel.get_text("inv_inv_item_item_pack_id"):
                break
            time.sleep(1)
        self.action.fillForm("inv_inv_item_item_pack_id", size, "select")
        self.action.fillForm("inv_inv_item_quantity", quantity)
        self.action.fillForm("inv_inv_item_expiry_date", expireDate)
        self.action.fillForm("inv_inv_item_comments", comments)

        # Now save the form
        self.assertTrue(self.action.saveForm("Save", "Item added to Inventory"))
        
    def stockWarehouse(self):
        # Log in as admin an then move read the inventory item file
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password)
        # Add the test warehouses
        source = open("../data/inventoryItems.txt", "r")
        values = source.readlines()
        source.close()
        # For each item add it to the warehouse
        for items in values:
            details = items.split(",")
            if len(details) == 6:
                self.addItem(details[0].strip(),
                             details[1].strip(),
                             details[2].strip(),
                             details[3].strip(),
                             details[4].strip(),
                             details[5].strip(),
                            )

    # Fails to logout cleanly when not in lastRun
    #def removeWarehouses(self):
    def lastRun(self):
        """ Delete the test warehouses """
        
        if len(self.warehouses) == 0:
            return

        sel = self.selenium
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password)
        self.action.openPage("inv/warehouse")

        allPassed = True
        for warehouse in self.warehouses:
            self.action.searchUnique(warehouse)
            sel.click("link=Delete")
            self.action.confirmDelete()
            if self.action.successMsg("Warehouse deleted"):
                print "Warehouse %s deleted" % warehouse
            else:
                print "Failed to deleted warehouse %s" % warehouse
                allPassed = False
        self.assertTrue(allPassed)

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
    WarehouseTest.selenium.stop()
