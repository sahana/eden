from sahanaTest import SahanaTest
import time, re

class LocationSelector(SahanaTest):
    """
        Tests assume that data has been preloaded by createLocations.py

        Tests assume these settings in 000_config.py:
            #deployment_settings.L10n.countries
            #"L5":T("Neighbourhood"),
            deployment_settings.gis.strict_hierarchy = False
            # In case of errors:
            deployment_settings.ui.navigate_away_confirm = False
    """

    def login(self):
        """ Login """
        # Login
        self.action.login("user@example.com", "testing" )
        self.assertTrue(self.selenium.is_element_present("link=user@example.com"))
    
    def create_header(self):
        """ Start a new Create form """
        sel = self.selenium
        # Load the Create Shelter page
        sel.open("/eden/cr/shelter/create")
        # Check that the location is currently blank
        self.check_blank()

    def open_record(self, name):
        """ Open an existing record """
        sel = self.selenium
        # Load the Shelter List page
        sel.open("/eden/cr/shelter")
        # Search for the Record
        self.action.searchUnique(name)
        # Open it
        sel.click("link=Open")
        sel.wait_for_page_to_load("30000")
        # Check that the correct record is loaded
        self.assertEqual(name, sel.get_value("cr_shelter_name"))

    def check_blank(self):
        """ Check that a form is free of location (create or update empty) """
        sel = self.selenium

        # Check that the location is currently blank
        self.assertEqual("", sel.get_value("cr_shelter_location_id"))
        # Check that the L0 dropdown is blank
        self.assertEqual("", sel.get_value("gis_location_L0"))

        # Check that the components which should be visible, are
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_L1"))
        self.failIf(sel.is_visible("gis_location_label_L1"))
        self.failIf(sel.is_visible("gis_location_L2"))
        self.failIf(sel.is_visible("gis_location_label_L2"))
        self.failIf(sel.is_visible("gis_location_L3"))
        self.failIf(sel.is_visible("gis_location_label_L3"))
        self.failIf(sel.is_visible("gis_location_L4"))
        self.failIf(sel.is_visible("gis_location_label_L4"))
        self.failIf(sel.is_visible("gis_location_"))
        self.failIf(sel.is_visible("gis_location_label_"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_details-btn"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))

class CreateLocationEmpty(LocationSelector):
    def test_locationEmpty(self):
        """ Create a new Shelter without any Location specified """
        sel = self.selenium
        # Login
        self.login()
        self.create_header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with no Location")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter added")

class UpdateLocationEmptyL0(LocationSelector):
    def test_updateLocationEmptyL0(self):
        """ Update an existing Shelter without any Location specified to an L0 """
        sel = self.selenium
        # Login
        self.login()
        # Load the Shelter
        self.open_record("Shelter with no Location")
        # Check that the location is currently blank
        self.check_blank()

        # Save the form (without changes)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter updated")
        # Shelter has correct location
        self.assertEqual("-", sel.get_table("//div[@id='rheader']/div/table.1.1"))

        # Load again
        self.open_record("Shelter with no Location")
        # Check that the location is still blank
        self.check_blank()
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Save the form (with changes)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter updated")
        # Shelter has correct location
        self.assertEqual("Haiti", sel.get_table("//div[@id='rheader']/div/table.1.1"))

        # Load again
        self.open_record("Shelter with no Location")
        # Check that the location is set
        self.assertEqual("Haiti", sel.get_table("//div[@id='rheader']/div/table.1.1"))
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.assertEqual(location_id, sel.get_value("cr_shelter_location_id"))
        # Check that the dropdown is set
        self.assertEqual(location_id, sel.get_value("gis_location_L0"))

        # Check that the components which should be visible, are
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_L2"))
        self.failIf(sel.is_visible("gis_location_label_L2"))
        self.failIf(sel.is_visible("gis_location_L3"))
        self.failIf(sel.is_visible("gis_location_label_L3"))
        self.failIf(sel.is_visible("gis_location_L4"))
        self.failIf(sel.is_visible("gis_location_label_L4"))
        self.failIf(sel.is_visible("gis_location_"))
        self.failIf(sel.is_visible("gis_location_label_"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_details-btn"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))

class UpdateLocationL0Empty(LocationSelector):
    def test_updateLocationL0Empty(self):
        """ Update an existing Shelter with an L0 Location to have no location """
        sel = self.selenium
        # Login
        self.login()
        # Load the Shelter
        self.open_record("Shelter with no Location")
        # Check that the location is currently set
        self.assertEqual("Haiti", sel.get_table("//div[@id='rheader']/div/table.1.1"))
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.assertEqual(location_id, sel.get_value("cr_shelter_location_id"))
        # Check that the dropdown is set
        self.assertEqual(location_id, sel.get_value("gis_location_L0"))

        # Check that the components which should be visible, are
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_L2"))
        self.failIf(sel.is_visible("gis_location_label_L2"))
        self.failIf(sel.is_visible("gis_location_L3"))
        self.failIf(sel.is_visible("gis_location_label_L3"))
        self.failIf(sel.is_visible("gis_location_L4"))
        self.failIf(sel.is_visible("gis_location_label_L4"))
        self.failIf(sel.is_visible("gis_location_"))
        self.failIf(sel.is_visible("gis_location_label_"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_details-btn"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))

        # De-select the L0
        sel.select("gis_location_L0", "label=Select a location...")
        # Check that the real location has been set to blank
        self.assertEqual("", sel.get_value("cr_shelter_location_id"))
        # Check that L1 dropdown disappears correctly
        time.sleep(1)
        self.failIf(sel.is_visible("gis_location_L1"))
        self.failIf(sel.is_visible("gis_location_label_L1"))
        # Save the form (with changes)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter updated")
        # Shelter has correct location
        self.assertEqual("-", sel.get_table("//div[@id='rheader']/div/table.1.1"))
        
class CreateLocationNoParent(LocationSelector):
    def test_locationNoParent(self):
        """ Create a new Shelter with a parentless Location """
        sel = self.selenium
        # Login
        self.login()
        self.create_header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with no Parent")
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Location with no Parent")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter added")
        # Shelter has correct location
        self.assertEqual("Location with no Parent", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class UpdateLocationNoParentEmpty(LocationSelector):
    def test_updateLocationNoParentEmpty(self):
        """ Update an existing Shelter with a parentless location to not having a location """
        sel = self.selenium
        # Login
        self.login()
        # Load the Shelter
        self.open_record("Shelter with no Parent")

        # Check that the location is set
        self.assertEqual("Location with no Parent", sel.get_table("//div[@id='rheader']/div/table.1.1"))
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.assertEqual(location_id, sel.get_value("cr_shelter_location_id"))
        # Check that the dropdown is set
        self.assertEqual(location_id, sel.get_value("gis_location_"))

        # Check that the components which should be visible, are
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.failUnless(sel.is_visible("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_label_"))
        self.failUnless(sel.is_visible("gis_location_details-btn"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_L1"))
        self.failIf(sel.is_visible("gis_location_label_L1"))
        self.failIf(sel.is_visible("gis_location_L2"))
        self.failIf(sel.is_visible("gis_location_label_L2"))
        self.failIf(sel.is_visible("gis_location_L3"))
        self.failIf(sel.is_visible("gis_location_label_L3"))
        self.failIf(sel.is_visible("gis_location_L4"))
        self.failIf(sel.is_visible("gis_location_label_L4"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))

        # De-select the Specific
        sel.select("gis_location_", "label=Select a location...")
        # Check that the real location has been set to blank
        self.assertEqual("", sel.get_value("cr_shelter_location_id"))
        # Save the form (with changes)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter updated")
        # Shelter has correct location
        self.assertEqual("-", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class UpdateLocationEmptyNewNoParent(LocationSelector):
    def test_updateLocationEmptyNewNoParent(self):
        """
            Update an existing Shelter without any Location specified to a NEW parentless one
        """
        sel = self.selenium
        # Login
        self.login()
        # Load the Shelter
        self.open_record("Shelter with no Parent")
        # Check that the location is currently blank
        self.check_blank()

        # Click on the Add button
        sel.click("gis_location_add-btn")
        # Check that the components appear correctly
        self.failUnless(sel.is_visible("gis_location_name"))
        self.failUnless(sel.is_visible("gis_location_name_label"))
        self.failUnless(sel.is_visible("gis_location_cancel-btn"))
        self.failUnless(sel.is_visible("gis_location_addr_street_row"))
        self.failUnless(sel.is_visible("gis_location_addr_street_label"))
        self.failUnless(sel.is_visible("gis_location_map-btn"))
        self.failUnless(sel.is_visible("gis_location_advanced_div"))
        # Check that components which should remain invisible, are
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))

        # Fill in a Name & Address
        sel.type("gis_location_name", "New parentless Location")
        sel.type("gis_location_addr_street", "45 Sheep Street")

        # Open Map
        sel.click("gis_location_map-btn")
        # Check it's now visible
        time.sleep(1)
        self.failUnless(sel.is_visible("gis-map-window"))
        # Close Map
        sel.click("//div[@id='gis-map-window']/div/div/div/div/div[contains(@class, 'x-tool-close')]")
        # Check it's not visible
        self.failIf(sel.is_visible("gis-map-window"))

        # Open the Advanced Tab
        sel.click("gis_location_advanced_checkbox")
        # Check that the components appear correctly
        self.failUnless(sel.is_visible("gis_location_lat_row"))
        self.failUnless(sel.is_visible("gis_location_lon_row"))

        # Open Converter
        sel.click("gis_location_converter-btn")
        # Check it's now visible
        time.sleep(1)
        self.failUnless(sel.is_visible("gis-convert-win"))
        # @ToDo: Use this to do a conversion
        # Close Converter
        sel.click("//div[@id='gis-convert-win']/div/div/div/div/div[contains(@class, 'x-tool-close')]")
        # Check it's not visible
        self.failIf(sel.is_visible("gis-convert-win"))

        # Fill in Lat & Lon
        sel.type("gis_location_lat", "51")
        sel.type("gis_location_lon", "1")

        # Save the form (with changes)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter updated")
        # Shelter has correct location
        self.assertEqual("New parentless Location (N 51.0 E 1.0)", sel.get_table("//div[@id='rheader']/div/table.1.1"))

        # Load again
        self.open_record("Shelter with no Parent")
        # Check that the location is set
        self.assertEqual("New parentless Location (N 51.0 E 1.0)", sel.get_table("//div[@id='rheader']/div/table.1.1"))
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.assertEqual(location_id, sel.get_value("cr_shelter_location_id"))
        # Check that the dropdown is set
        self.assertEqual(location_id, sel.get_value("gis_location_"))

        # Check that the components which should be visible, are
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.failUnless(sel.is_visible("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_label_"))
        self.failUnless(sel.is_visible("gis_location_details-btn"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_L1"))
        self.failIf(sel.is_visible("gis_location_label_L1"))
        self.failIf(sel.is_visible("gis_location_L2"))
        self.failIf(sel.is_visible("gis_location_label_L2"))
        self.failIf(sel.is_visible("gis_location_L3"))
        self.failIf(sel.is_visible("gis_location_label_L3"))
        self.failIf(sel.is_visible("gis_location_L4"))
        self.failIf(sel.is_visible("gis_location_label_L4"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))

        # Click on 'Details' button
        sel.click("gis_location_details-btn")
        # Check that the components which should be visible, are
        self.failUnless(sel.is_visible("gis_location_addr_street_row"))
        self.failUnless(sel.is_visible("gis_location_addr_street_label"))
        self.failUnless(sel.is_visible("gis_location_map-btn"))
        self.failUnless(sel.is_visible("gis_location_advanced_div"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))

        # Check that the Street Address is populated
        self.assertEqual("45 Sheep Street", sel.get_text("gis_location_addr_street"))

        # Open the Advanced Tab
        sel.click("gis_location_advanced_checkbox")
        # Check that the components appear correctly
        self.failUnless(sel.is_visible("gis_location_lat_row"))
        self.failUnless(sel.is_visible("gis_location_lon_row"))

        # Check that the Lat/Lon are populated
        self.assertEqual("51.0", sel.get_value("gis_location_lat"))
        self.assertEqual("1.0", sel.get_value("gis_location_lon"))

class UpdateLocationNoParentL0(LocationSelector):
    def test_updateLocationNoParentL0(self):
        """ Update an existing Shelter with a parentless location to an L0"""
        sel = self.selenium
        # Login
        self.login()
        # Load the Shelter
        self.open_record("Shelter with no Parent")

        # Check that the location is set
        self.assertEqual("New parentless Location (N 51.0 E 1.0)", sel.get_table("//div[@id='rheader']/div/table.1.1"))
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.assertEqual(location_id, sel.get_value("cr_shelter_location_id"))
        # Check that the dropdown is set
        self.assertEqual(location_id, sel.get_value("gis_location_"))

        # Check that the components which should be visible, are
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.failUnless(sel.is_visible("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_label_"))
        self.failUnless(sel.is_visible("gis_location_details-btn"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_L1"))
        self.failIf(sel.is_visible("gis_location_label_L1"))
        self.failIf(sel.is_visible("gis_location_L2"))
        self.failIf(sel.is_visible("gis_location_label_L2"))
        self.failIf(sel.is_visible("gis_location_L3"))
        self.failIf(sel.is_visible("gis_location_label_L3"))
        self.failIf(sel.is_visible("gis_location_L4"))
        self.failIf(sel.is_visible("gis_location_label_L4"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))

        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Save the form (with changes)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter updated")
        # Shelter has correct location
        self.assertEqual("Haiti", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class CreateLocationL0(LocationSelector):
    def test_locationL0(self):
        """ Create a new Shelter with an L0 location """
        sel = self.selenium
        # Login
        self.login()
        self.create_header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with an L0 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter added")
        # Shelter has correct location
        self.assertEqual("Haiti", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class CreateLocationInL0(LocationSelector):
    def test_locationInL0(self):
        """
            Create a new Shelter inside an L0 location
            NB This should fail if deployment_settings.gis.strict_hierarchy = True
        """
        sel = self.selenium
        # Login
        self.login()
        self.create_header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter within L0 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Specific Location in L0")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter added")
        # Shelter has correct location
        self.assertEqual("Specific Location in L0", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class CreateLocationL1(LocationSelector):
    def test_locationL1(self):
        """ Create a new Shelter with an L1 location """
        sel = self.selenium
        # Login
        self.login()
        self.create_header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with an L1 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter added")
        # Shelter has correct location
        self.assertEqual("Ouest (Haiti)", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class CreateLocationInL1(LocationSelector):
    def test_locationInL1(self):
        """ Create a new Shelter inside an L1 location """
        sel = self.selenium
        # Login
        self.login()
        self.create_header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter within L1 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Specific Location in L1")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter added")
        # Shelter has correct location
        self.assertEqual("Specific Location in L1", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class CreateLocationL2(LocationSelector):
    def test_locationL2(self):
        """ Create a new Shelter with an L2 location """
        sel = self.selenium
        # Login
        self.login()
        self.create_header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with an L2 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Select the L2
        sel.select("gis_location_L2", "label=Port-Au-Prince")
        # Check that L3 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...MartissantTurgeau", sel.get_table("//div[@id='content']/div[2]/form/table.15.0"))
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter added")
        # Shelter has correct location
        self.assertEqual("Port-Au-Prince (Ouest)", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class CreateLocationInL2(LocationSelector):
    def test_locationInL2(self):
        """ Create a new Shelter inside an L2 location """
        sel = self.selenium
        # Login
        self.login()
        self.create_header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter within L2 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Select the L2
        sel.select("gis_location_L2", "label=Port-Au-Prince")
        # Check that L3 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...MartissantTurgeau", sel.get_table("//div[@id='content']/div[2]/form/table.15.0"))
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Specific Location in L2")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter added")
        # Shelter has correct location
        self.assertEqual("Specific Location in L2", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class CreateLocationL3(LocationSelector):
    def test_locationL3(self):
        """ Create a new Shelter with an L3 location """
        sel = self.selenium
        # Login
        self.login()
        self.create_header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with an L3 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Select the L2
        sel.select("gis_location_L2", "label=Port-Au-Prince")
        # Check that L3 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...MartissantTurgeau", sel.get_table("//div[@id='content']/div[2]/form/table.15.0"))
        # Select the L3
        sel.select("gis_location_L3", "label=Martissant")
        # Check that L4 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Carrefour Feuilles", sel.get_table("//div[@id='content']/div[2]/form/table.17.0"))
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter added")
        # Shelter has correct location
        self.assertEqual("Martissant (Port-Au-Prince)", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class CreateLocationInL3(LocationSelector):
    def test_locationInL3(self):
        """ Create a new Shelter inside an L3 location """
        sel = self.selenium
        # Login
        self.login()
        self.create_header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter within L3 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Select the L2
        sel.select("gis_location_L2", "label=Port-Au-Prince")
        # Check that L3 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...MartissantTurgeau", sel.get_table("//div[@id='content']/div[2]/form/table.15.0"))
        # Select the L3
        sel.select("gis_location_L3", "label=Martissant")
        # Check that L4 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Carrefour Feuilles", sel.get_table("//div[@id='content']/div[2]/form/table.17.0"))
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Specific Location in L3")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter added")
        # Shelter has correct location
        self.assertEqual("Specific Location in L3", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class CreateLocationL4(LocationSelector):
    def test_locationL4(self):
        """ Create a new Shelter with an L4 location """
        sel = self.selenium
        # Login
        self.login()
        self.create_header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with an L4 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Select the L2
        sel.select("gis_location_L2", "label=Port-Au-Prince")
        # Check that L3 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...MartissantTurgeau", sel.get_table("//div[@id='content']/div[2]/form/table.15.0"))
        # Select the L3
        sel.select("gis_location_L3", "label=Martissant")
        # Check that L4 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Carrefour Feuilles", sel.get_table("//div[@id='content']/div[2]/form/table.17.0"))
        # Select the L4
        sel.select("gis_location_L4", "label=Carrefour Feuilles")
        # Check that 'L5' dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Clinique Communautaire de Martissant", sel.get_table("//div[@id='content']/div[2]/form/table.19.0"))
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter added")
        # Shelter has correct location
        self.assertEqual("Carrefour Feuilles", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class CreateLocationInL4(LocationSelector):
    def test_locationInL4(self):
        """ Create a new Shelter inside an L4 location """
        sel = self.selenium
        # Login
        self.login()
        self.create_header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter within L4 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Select the L2
        sel.select("gis_location_L2", "label=Port-Au-Prince")
        # Check that L3 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...MartissantTurgeau", sel.get_table("//div[@id='content']/div[2]/form/table.15.0"))
        # Select the L3
        sel.select("gis_location_L3", "label=Martissant")
        # Check that L4 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Carrefour Feuilles", sel.get_table("//div[@id='content']/div[2]/form/table.17.0"))
        # Select the L4
        sel.select("gis_location_L4", "label=Carrefour Feuilles")
        # Check that specific location dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Clinique Communautaire de Martissant", sel.get_table("//div[@id='content']/div[2]/form/table.19.0"))
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Specific Location in L4")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter added")
        # Shelter has correct location
        self.assertEqual("Specific Location in L4", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class UpdateLocationInL4NewInL3(LocationSelector):
    def test_updateLocationInL4NewInL3(self):
        """ Update a Shelter inside an L4 location to being inside a NEW location in an L3"""
        sel = self.selenium
        # Login
        self.login()
        # Load the Shelter
        self.open_record("Shelter within L4 Location")

        # Check that the location is set
        self.assertEqual("Specific Location in L4", sel.get_table("//div[@id='rheader']/div/table.1.1"))
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.assertEqual(location_id, sel.get_value("cr_shelter_location_id"))
        # Check that the dropdown is set
        self.assertEqual(location_id, sel.get_value("gis_location_"))

        # Check that the components which should be visible, are
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.failUnless(sel.is_visible("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_label_L2"))
        self.failUnless(sel.is_visible("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_label_L3"))
        self.failUnless(sel.is_visible("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_label_L4"))
        self.failUnless(sel.is_visible("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_label_"))
        self.failUnless(sel.is_visible("gis_location_details-btn"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))

        # Select the L3
        sel.select("gis_location_L3", "label=Turgeau")
        # Check that L4 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Babiole", sel.get_table("//div[@id='content']/div[2]/form/table.17.0"))

        # Click on the Add button
        sel.click("gis_location_add-btn")
        # Check that the components appear correctly
        self.failUnless(sel.is_visible("gis_location_name"))
        self.failUnless(sel.is_visible("gis_location_name_label"))
        self.failUnless(sel.is_visible("gis_location_cancel-btn"))
        self.failUnless(sel.is_visible("gis_location_addr_street_row"))
        self.failUnless(sel.is_visible("gis_location_addr_street_label"))
        self.failUnless(sel.is_visible("gis_location_map-btn"))
        self.failUnless(sel.is_visible("gis_location_advanced_div"))
        # Check that components which should remain invisible, are
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))

        # Fill in a Name & Address
        sel.type("gis_location_name", "New in L3")
        sel.type("gis_location_addr_street", "5 Ruelle Chochotte")

        # Open the Advanced Tab
        sel.click("gis_location_advanced_checkbox")
        # Check that the components appear correctly
        self.failUnless(sel.is_visible("gis_location_lat_row"))
        self.failUnless(sel.is_visible("gis_location_lon_row"))

        # Fill in Lat & Lon
        sel.type("gis_location_lat", "18.53171116")
        sel.type("gis_location_lon", "-72.33020758")

        # Save the form (with changes)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter updated")
        # Shelter has correct location
        self.assertEqual("New in L3 (N 18.53171116 W -72.33020758)", sel.get_table("//div[@id='rheader']/div/table.1.1"))

        # Load again
        self.open_record("Shelter within L4 Location")
        # Check that the location is set
        self.assertEqual("New in L3 (N 18.53171116 W -72.33020758)", sel.get_table("//div[@id='rheader']/div/table.1.1"))
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.assertEqual(location_id, sel.get_value("cr_shelter_location_id"))
        # Check that the dropdown is set
        self.assertEqual(location_id, sel.get_value("gis_location_"))

        # Check that the components which should be visible, are
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.failUnless(sel.is_visible("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_label_L2"))
        self.failUnless(sel.is_visible("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_label_L3"))
        self.failUnless(sel.is_visible("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_label_L4"))
        self.failUnless(sel.is_visible("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_label_"))
        self.failUnless(sel.is_visible("gis_location_details-btn"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))

        # Click on 'Details' button
        sel.click("gis_location_details-btn")
        # Check that the components which should be visible, are
        self.failUnless(sel.is_visible("gis_location_addr_street_row"))
        self.failUnless(sel.is_visible("gis_location_addr_street_label"))
        self.failUnless(sel.is_visible("gis_location_map-btn"))
        self.failUnless(sel.is_visible("gis_location_advanced_div"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))

        # Check that the Street Address is populated
        self.assertEqual("5 Ruelle Chochotte", sel.get_text("gis_location_addr_street"))

        # Open the Advanced Tab
        sel.click("gis_location_advanced_checkbox")
        # Check that the components appear correctly
        self.failUnless(sel.is_visible("gis_location_lat_row"))
        self.failUnless(sel.is_visible("gis_location_lon_row"))

        # Check that the Lat/Lon are populated
        self.assertEqual("18.53171116", sel.get_value("gis_location_lat"))
        self.assertEqual("-72.33020758", sel.get_value("gis_location_lon"))

class CreateLocationSelectSpecific(LocationSelector):
    def test_locationSelectSpecific(self):
        """ Create a new Shelter with a pre-existing specific location """
        sel = self.selenium
        # Login
        self.login()
        self.create_header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with a pre-existing specific Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Select the L2
        sel.select("gis_location_L2", "label=Port-Au-Prince")
        # Check that L3 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...MartissantTurgeau", sel.get_table("//div[@id='content']/div[2]/form/table.15.0"))
        # Select the L3
        sel.select("gis_location_L3", "label=Martissant")
        # Check that L4 dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Carrefour Feuilles", sel.get_table("//div[@id='content']/div[2]/form/table.17.0"))
        # Select the L4
        sel.select("gis_location_L4", "label=Carrefour Feuilles")
        # Check that specific location dropdown appears correctly
        time.sleep(4)
        self.assertEqual("Select a location...Clinique Communautaire de Martissant", sel.get_table("//div[@id='content']/div[2]/form/table.19.0"))
        # Select the Specific
        sel.select("gis_location_", "label=Clinique Communautaire de Martissant")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.action.successMsg("Shelter added")
        # Shelter has correct location
        self.assertEqual("Clinique Communautaire de Martissant (N 18.528000849 W -72.3489983828)", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class SearchLocations(LocationSelector):
    def test_locationSearch(self):
        """ Search for Locations using the Autocomplete """
        sel = self.selenium
        
        # Login
        self.login()

        # L2inL0
        # Create a new Shelter
        self.create_header()
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Verify it opens
        self.failUnless(sel.is_visible("gis_location_autocomplete_div"))
        # & that button disappears
        self.failIf(sel.is_visible("gis_location_search-btn"))
        # Enter the search String
        sel.type("gis_location_autocomplete", "L2inL0")
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if "L2inL0" == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        time.sleep(4)
        # Verify that the dropdowns are set/opened
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.assertEqual("Haiti", sel.get_selected_label("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        self.failUnless(sel.is_visible("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_label_L2"))
        self.assertEqual("L2inL0", sel.get_selected_label("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_label_L3"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        self.failUnless(sel.is_visible("gis_location_search-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("gis_location_autocomplete_div"))
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_L4"))
        self.failIf(sel.is_visible("gis_location_label_L4"))
        self.failIf(sel.is_visible("gis_location_"))
        self.failIf(sel.is_visible("gis_location_label_"))
        self.failIf(sel.is_visible("gis_location_details-btn"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))
 
        # @ToDo: Verify that the result is stored correctly
        # How do we get name from number without submitting? SHould we just submit every time?
        

        # L2inL1withNoParent
        # Create a new Shelter
        self.create_header()
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Verify it opens
        self.failUnless(sel.is_visible("gis_location_autocomplete_div"))
        # & that button disappears
        self.failIf(sel.is_visible("gis_location_search-btn"))
        # Enter the search String
        sel.type("gis_location_autocomplete", "L2inL1withNoParent")
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if "L2inL1withNoParent" == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        time.sleep(4)
        # Verify that the dropdowns are set/opened
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.assertEqual("L1withNoParent", sel.get_selected_label("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_label_L2"))
        self.assertEqual("L2inL1withNoParent", sel.get_selected_label("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_label_L3"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        self.failUnless(sel.is_visible("gis_location_search-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("gis_location_autocomplete_div"))
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_L4"))
        self.failIf(sel.is_visible("gis_location_label_L4"))
        self.failIf(sel.is_visible("gis_location_"))
        self.failIf(sel.is_visible("gis_location_label_"))
        self.failIf(sel.is_visible("gis_location_details-btn"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))

        # L3inL0
        # Create a new Shelter
        self.create_header()
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Verify it opens
        self.failUnless(sel.is_visible("gis_location_autocomplete_div"))
        # & that button disappears
        self.failIf(sel.is_visible("gis_location_search-btn"))
        # Enter the search String
        sel.type("gis_location_autocomplete", "L3inL0")
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if "L3inL0" == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        time.sleep(4)
        # Verify that the dropdowns are set/opened
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.assertEqual("Haiti", sel.get_selected_label("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_label_L2"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_label_L3"))
        self.assertEqual("L3inL0", sel.get_selected_label("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_label_L4"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        self.failUnless(sel.is_visible("gis_location_search-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("gis_location_autocomplete_div"))
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_"))
        self.failIf(sel.is_visible("gis_location_label_"))
        self.failIf(sel.is_visible("gis_location_details-btn"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))
        
        # L3inL1withL0
        # Create a new Shelter
        self.create_header()
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Verify it opens
        self.failUnless(sel.is_visible("gis_location_autocomplete_div"))
        # & that button disappears
        self.failIf(sel.is_visible("gis_location_search-btn"))
        # Enter the search String
        sel.type("gis_location_autocomplete", "L3inL1withL0")
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if "L3inL1withL0" == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        time.sleep(4)
        # Verify that the dropdowns are set/opened
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.assertEqual("Haiti", sel.get_selected_label("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.assertEqual("Ouest", sel.get_selected_label("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_label_L2"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_label_L3"))
        self.assertEqual("L3inL1withL0", sel.get_selected_label("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_label_L4"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        self.failUnless(sel.is_visible("gis_location_search-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("gis_location_autocomplete_div"))
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_"))
        self.failIf(sel.is_visible("gis_location_label_"))
        self.failIf(sel.is_visible("gis_location_details-btn"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))

        # L3inL1withNoParent
        # Create a new Shelter
        self.create_header()
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Verify it opens
        self.failUnless(sel.is_visible("gis_location_autocomplete_div"))
        # & that button disappears
        self.failIf(sel.is_visible("gis_location_search-btn"))
        # Enter the search String
        sel.type("gis_location_autocomplete", "L3inL1withNoParent")
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if "L3inL1withNoParent" == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        time.sleep(4)
        # Verify that the dropdowns are set/opened
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.assertEqual("L1withNoParent", sel.get_selected_label("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_label_L2"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_label_L3"))
        self.assertEqual("L3inL1withNoParent", sel.get_selected_label("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_label_L4"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        self.failUnless(sel.is_visible("gis_location_search-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("gis_location_autocomplete_div"))
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_"))
        self.failIf(sel.is_visible("gis_location_label_"))
        self.failIf(sel.is_visible("gis_location_details-btn"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))

        # L4inL0
        # Create a new Shelter
        self.create_header()
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Verify it opens
        self.failUnless(sel.is_visible("gis_location_autocomplete_div"))
        # & that button disappears
        self.failIf(sel.is_visible("gis_location_search-btn"))
        # Enter the search String
        sel.type("gis_location_autocomplete", "L4inL0")
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if "L4inL0" == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        time.sleep(4)
        # Verify that the dropdowns are set/opened
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.assertEqual("Haiti", sel.get_selected_label("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_label_L2"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_label_L3"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_label_L4"))
        self.assertEqual("L4inL0", sel.get_selected_label("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        self.failUnless(sel.is_visible("gis_location_search-btn"))
        self.failUnless(sel.is_visible("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_label_"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_details-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("gis_location_autocomplete_div"))
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))

        # L4inL1withL0
        # Create a new Shelter
        self.create_header()
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Verify it opens
        self.failUnless(sel.is_visible("gis_location_autocomplete_div"))
        # & that button disappears
        self.failIf(sel.is_visible("gis_location_search-btn"))
        # Enter the search String
        sel.type("gis_location_autocomplete", "L4inL1withL0")
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if "L4inL1withL0" == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        time.sleep(4)
        # Verify that the dropdowns are set/opened
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.assertEqual("Haiti", sel.get_selected_label("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.assertEqual("Ouest", sel.get_selected_label("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_label_L2"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_label_L3"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_label_L4"))
        self.assertEqual("L4inL1withL0", sel.get_selected_label("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        self.failUnless(sel.is_visible("gis_location_search-btn"))
        self.failUnless(sel.is_visible("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_label_"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_details-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("gis_location_autocomplete_div"))
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))

        # L4inL1withNoParent
        # Create a new Shelter
        self.create_header()
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Verify it opens
        self.failUnless(sel.is_visible("gis_location_autocomplete_div"))
        # & that button disappears
        self.failIf(sel.is_visible("gis_location_search-btn"))
        # Enter the search String
        sel.type("gis_location_autocomplete", "L4inL1withNoParent")
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if "L4inL1withNoParent" == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        time.sleep(4)
        # Verify that the dropdowns are set/opened
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.assertEqual("L1withNoParent", sel.get_selected_label("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_label_L2"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_label_L3"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_label_L4"))
        self.assertEqual("L4inL1withNoParent", sel.get_selected_label("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        self.failUnless(sel.is_visible("gis_location_search-btn"))
        self.failUnless(sel.is_visible("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_label_"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_details-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("gis_location_autocomplete_div"))
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))

        # L4inL2withL1L0          
        # Create a new Shelter
        self.create_header()
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Verify it opens
        self.failUnless(sel.is_visible("gis_location_autocomplete_div"))
        # & that button disappears
        self.failIf(sel.is_visible("gis_location_search-btn"))
        # Enter the search String
        sel.type("gis_location_autocomplete", "L4inL2withL1L0")
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if "L4inL2withL1L0" == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        time.sleep(4)
        # Verify that the dropdowns are set/opened
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.assertEqual("Haiti", sel.get_selected_label("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.assertEqual("Ouest", sel.get_selected_label("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_label_L2"))
        self.assertEqual("Port-Au-Prince", sel.get_selected_label("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_label_L3"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_label_L4"))
        self.assertEqual("L4inL2withL1L0", sel.get_selected_label("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        self.failUnless(sel.is_visible("gis_location_search-btn"))
        self.failUnless(sel.is_visible("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_label_"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_details-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("gis_location_autocomplete_div"))
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))
        
        # L4inL2withL1only
        # Create a new Shelter
        self.create_header()
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Verify it opens
        self.failUnless(sel.is_visible("gis_location_autocomplete_div"))
        # & that button disappears
        self.failIf(sel.is_visible("gis_location_search-btn"))
        # Enter the search String
        sel.type("gis_location_autocomplete", "L4inL2withL1only")
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if "L4inL2withL1only" == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        time.sleep(4)
        # Verify that the dropdowns are set/opened
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.assertEqual("L1withNoParent", sel.get_selected_label("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_label_L2"))
        self.assertEqual("L2inL1withNoParent", sel.get_selected_label("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_label_L3"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_label_L4"))
        self.assertEqual("L4inL2withL1only", sel.get_selected_label("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        self.failUnless(sel.is_visible("gis_location_search-btn"))
        self.failUnless(sel.is_visible("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_label_"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_details-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("gis_location_autocomplete_div"))
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))
        
        # L4inL2withL0only
        # Create a new Shelter
        self.create_header()
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Verify it opens
        self.failUnless(sel.is_visible("gis_location_autocomplete_div"))
        # & that button disappears
        self.failIf(sel.is_visible("gis_location_search-btn"))
        # Enter the search String
        sel.type("gis_location_autocomplete", "L4inL2withL0only")
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if "L4inL2withL0only" == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        time.sleep(4)
        # Verify that the dropdowns are set/opened
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.assertEqual("Haiti", sel.get_selected_label("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_label_L2"))
        self.assertEqual("L2inL0", sel.get_selected_label("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_label_L3"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_label_L4"))
        self.assertEqual("L4inL2withL0only", sel.get_selected_label("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        self.failUnless(sel.is_visible("gis_location_search-btn"))
        self.failUnless(sel.is_visible("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_label_"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_details-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("gis_location_autocomplete_div"))
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))
        
        # L4inL2withNoParent
        # Create a new Shelter
        self.create_header()
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Verify it opens
        self.failUnless(sel.is_visible("gis_location_autocomplete_div"))
        # & that button disappears
        self.failIf(sel.is_visible("gis_location_search-btn"))
        # Enter the search String
        sel.type("gis_location_autocomplete", "L4inL2withNoParent")
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if "L4inL2withNoParent" == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        time.sleep(4)
        # Verify that the dropdowns are set/opened
        self.failUnless(sel.is_visible("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_label_L0"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L0"))
        self.failUnless(sel.is_visible("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_label_L1"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L1"))
        self.failUnless(sel.is_visible("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_label_L2"))
        self.assertEqual("L2withNoParent", sel.get_selected_label("gis_location_L2"))
        self.failUnless(sel.is_visible("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_label_L3"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L3"))
        self.failUnless(sel.is_visible("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_label_L4"))
        self.assertEqual("L4inL2withNoParent", sel.get_selected_label("gis_location_L4"))
        self.failUnless(sel.is_visible("gis_location_add-btn"))
        self.failUnless(sel.is_visible("gis_location_search-btn"))
        self.failUnless(sel.is_visible("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_label_"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_"))
        self.failUnless(sel.is_visible("gis_location_details-btn"))
        # Check that the components which should be hidden, are
        self.failIf(sel.is_visible("gis_location_autocomplete_div"))
        self.failIf(sel.is_visible("cr_shelter_location_id"))
        self.failIf(sel.is_visible("gis_location_name"))
        self.failIf(sel.is_visible("gis_location_name_label"))
        self.failIf(sel.is_visible("gis_location_cancel-btn"))
        self.failIf(sel.is_visible("gis_location_addr_street_row"))
        self.failIf(sel.is_visible("gis_location_addr_street_label"))
        self.failIf(sel.is_visible("gis_location_map-btn"))
        self.failIf(sel.is_visible("gis_location_advanced_div"))
        self.failIf(sel.is_visible("gis_location_lat_row"))
        self.failIf(sel.is_visible("gis_location_lon_row"))

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
