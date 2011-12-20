from sahanaTest import SahanaTest
import unittest, time, re
import copy

class Locations(SahanaTest):
    """ Test the location code - specifically the implementation in the shelter registry
    
        All tests can assume that they will be logged in with the user account at the start
        any test that requires a different account must log into that account perform the action
        and then log back into the user account.  
    """
    holder = "**TEST**"
    _sortList = (
#                 "loadLocationTestData",
                # "locationEmpty",
                # "addShelterL0",
                # "locationInL0",
                 "locationL1",
#                 "test_addL0Location",
#                 "test_removeL0Location",
#                 "test_locationNoParent",
#                 "test_locationL0",
#                 "test_locationInL0",
#                 "test_locationL1",
#                 "test_locationInL1",
#                 "test_locationL2",
#                 "test_locationInL2",
#                 "test_locationL3",
#                 "test_locationInL3",
#                 "test_locationL4",
#                 "test_locationInL4",
#                 "test_updateLocationInL4NewInL3",
#                 "test_locationSelectSpecific",
#                 "test_locationSearch",
#                 "removeShelterTestData",
#                 "removeLocationTestData",
                 )
    
    def firstRun(self):
        sel = self.selenium
        self.action.logout()
        self.useSahanaUserAccount()
        self.action.login(self._user, self._password )

        Locations.line = []
        Locations.shelter = []
        self.initFormDetails()
        
    def initFormDetails(self):
        # Setup the template for the shelter From
        Locations.crShelterTemplate = self.action.getFormTemplate()
        Locations.crShelterTemplate.addInput(labelID="cr_shelter_location_id__label",
                           inputID="cr_shelter_location_id")
        Locations.crShelterTemplate.addInput(labelID="cr_shelter_organisation_id__label",
                           inputID="dummy_cr_shelter_organisation_id")
        Locations.crShelterTemplate.addInput(labelID="cr_shelter_organisation_id__label",
                           inputID="cr_shelter_organisation_id", visible=False)
        Locations.crShelterTemplate.addSelect(labelID="cr_shelter_shelter_type_id__label",
                           selectID="cr_shelter_shelter_type_id")
        Locations.crShelterTemplate.addSelect(labelID="cr_shelter_shelter_service_id__label",
                           selectID="cr_shelter_shelter_service_id")
        Locations.crShelterTemplate.addInput(inputID="cr_shelter_location_id", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_search_ac", visible=False)
        Locations.crShelterTemplate.addSelect(selectID="gis_location_L0")
        Locations.crShelterTemplate.addInput(inputID="gis_location_L0_search", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_name")
        Locations.crShelterTemplate.addTextArea(textID="gis_location_street")
        Locations.crShelterTemplate.addInput(inputID="gis_location_postcode")
        Locations.crShelterTemplate.addInput(inputID="gis_location_postcode_search", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_L1", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_L1_ac")
        Locations.crShelterTemplate.addInput(inputID="gis_location_L1_search", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_L2", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_L2_ac")
        Locations.crShelterTemplate.addInput(inputID="gis_location_L2_search", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_L3", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_L3_ac")
        Locations.crShelterTemplate.addInput(inputID="gis_location_L3_search", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_L4", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_L4_ac")
        Locations.crShelterTemplate.addInput(inputID="gis_location_L4_search", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_L5", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_L5_ac", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_L5_search", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_lat")
        Locations.crShelterTemplate.addInput(inputID="gis_location_lat_search", visible=False)
        Locations.crShelterTemplate.addInput(inputID="gis_location_lon")
        Locations.crShelterTemplate.addInput(inputID="gis_location_lon_search", visible=False)
        Locations.crShelterTemplate.addInput(labelID="cr_shelter_phone__label",
                           inputID="cr_shelter_phone")
        Locations.crShelterTemplate.addInput(labelID="cr_shelter_person_id__label",
                           inputID="dummy_cr_shelter_person_id")
        Locations.crShelterTemplate.addInput(labelID="cr_shelter_person_id__label",
                           inputID="cr_shelter_person_id", visible=False)
        Locations.crShelterTemplate.addInput(labelID="cr_shelter_population__label",
                           inputID="cr_shelter_population")
        Locations.crShelterTemplate.addInput(labelID="cr_shelter_capacity__label",
                           inputID="cr_shelter_capacity")
        Locations.crShelterTemplate.addInput(labelID="cr_shelter_source__label",
                           inputID="cr_shelter_source")
        Locations.crShelterTemplate.addInput(labelID="cr_shelter_document_id__label",
                           inputID="dummy_cr_shelter_document_id")
        Locations.crShelterTemplate.addInput(labelID="cr_shelter_document_id__label",
                           inputID="cr_shelter_document_id", visible=False)
        Locations.crShelterTemplate.addTextArea(labelID="cr_shelter_comments__label",
                           textID="cr_shelter_comments")
        Locations.crShelterTemplate.addButton("Save")

        Locations.formHeading = {"Name:"     : "-",
                                 "Location:" : "-"
                                }
    def makeNameUnique(self, name):
        return self.holder + name + self.holder
    
    def addLocation(self, holder, name, level, parent=None, parentLevel=None, grandParent="", lat=None, lon=None):
        sel = self.selenium
        name = holder + name + holder
        if parent == None:
            parentHolder = None
        else:
            parentHolder = "%s%s%s" % (holder, parent, holder)
        # Load the Create Location page
        sel.open("gis/location/create")
        # Create the Location
        sel.type("gis_location_name", name)
        if level:
            sel.select("gis_location_level", "value=%s" % level)
        if grandParent:
            grandParentHolder = ", %s%s%s" % (holder, grandParent, holder)
            grandParent = ", %s" % grandParent
        else:
            grandParentHolder = ""
        if parentLevel == "L0":
            levelLabel = " (Country)"
        elif parentLevel == "L1":
            # NB This doesn't work if deploymentSettings are set to only use a single Country!
            levelLabel = " (Province%s)" % grandParent
            levelLabelHolder = " (Province%s)" % grandParentHolder
        elif parentLevel == "L2":
            levelLabel = " (District%s)" % grandParent
            levelLabelHolder = " (District%s)" % grandParentHolder
        else:
            levelLabel = ""
            levelLabelHolder = ""
        if parent:
            try:
                try:
                    sel.select("gis_location_parent", "label=%s%s" % (parentHolder, levelLabelHolder))
                except:
                    sel.select("gis_location_parent", "label=%s%s" % (parentHolder, levelLabel))
            except:
                parentHolder = parent
                sel.select("gis_location_parent", "label=%s%s" % (parentHolder, levelLabel))
        if lat:
            sel.type("gis_location_lat", lat)
        if lon:
            sel.type("gis_location_lon", lon)
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Location saved
        msg = "Failed to add location %s level %s with parent %s" % (name , level, parentHolder)
        self.action.assertTrue(self.action.successMsg("Location added"), msg)
        print "Location %s level %s with parent %s added" % (name , level, parentHolder)


    def loadLocations(self):
        """ Create locations for testing the Locations Selector """
        sel = self.selenium
        source = open("../data/location.txt", "r")
        values = source.readlines()
        source.close()
        # wrap all location names with the holder __TEST__
        # This makes deletion of a unique name possible
        for location in values:
            name = level = parent = parentLevel = grandParent = lat = lon = None
            details = location.split(",")
            if len(details) >= 1:
                name = details[0].strip()
            if len(details) >= 2:
                level = details[1].strip()
            if len(details) >= 3:
                parent = details[2].strip()
            if len(details) >= 4:
                parentLevel = details[3].strip()
            if len(details) >= 5:
                grandParent = details[4].strip()
            if len(details) >= 6:
                lat = details[5].strip()
            if len(details) >= 7:
                lon = details[6].strip()
            # Load the Create Location page
            newLocation = self.makeNameUnique(name)
            sel.open("gis/location")
            if self.action.search(newLocation, "Showing 0 to 0 of 0 entries"):
                self.addLocation(self.holder, name, level, parent, parentLevel, grandParent, lat, lon)
            if parent == None:
                Locations.line.append(newLocation)
            else:
                Locations.line.insert(0,newLocation)
            
    def openRecord(self, name):
        """ Open an existing record """
        sel = self.selenium
        # Load the Shelter List page
        sel.open("cr/shelter")
        # Search for the Record
        self.action.searchUnique(name)

        # Open it
        sel.click("link=Edit")
        sel.wait_for_page_to_load("30000")
        # Check that the correct record is loaded
        self.assertEqual(name, sel.get_value("cr_shelter_name"))

    def loadLocationTestData(self):
        """ Load all the test locations """
        self.loadLocations()
    
    def removeLocationTestData(self):
        for location in Locations.line:
            self.action.deleteObject("gis/location", location, "Location")
    
    def removeShelterTestData(self):
        """ Remove all the data added by this test case """
        sel = self.selenium
        for shelter in Locations.shelter:
            self.action.deleteObject("cr/shelter", shelter, "Shelter")

    
    def locationEmpty(self):
        """ Create a new Shelter without any Location specified """
        shelterName = "Shelter with no Location"
        
        sel = self.selenium
        sel.open("cr/shelter/create")
        Locations.crShelterTemplate.checkForm()

        return # unable to progress from here since a shelter currently needs an L0
        
        # Fill in the mandatory fields
        self.action.fillForm("cr_shelter_name",shelterName)
        """ Now save the form """
        self.assertTrue(self.action.saveForm("Save", "Shelter added"))
        print "New shelter created"
        Locations.shelter.append(shelterName)
        # Load the Shelter
        self.openRecord(shelterName)
        Locations.crShelterTemplate.checkForm()
        # Save the form (without changes)
        self.assertTrue(self.action.saveForm("Save", "Shelter added"))
        self.assertEqual("List Shelters", sel.get_text("//div[@id='content']/h2"))

    def addShelterL0(self):
        """ Create a new Shelter with an L0 location """
        # Create the name variables
        shelterName = "Shelter with an L0 Location"
        L0 = "Haiti" 
        sel = self.selenium
        sel.open("cr/shelter/create")
        # Fill in the mandatory fields
        self.action.fillForm("cr_shelter_name",shelterName)
        # Select the L0
        self.action.fillForm("gis_location_L0",L0,"select")
        # Save the form
        self.assertTrue(self.action.saveForm("Save", "Shelter added"))
        print "New shelter created"
        Locations.shelter.append(shelterName)
        # Load again
        self.openRecord(shelterName)

        rHeading = self.action.getrHeaderTemplate()
        rHeading.addValue("Name:", shelterName)
        rHeading.addValue("Location:", "%s (%s)" % (shelterName, L0))
        rHeading.checkrHeader()

        editForm = copy.deepcopy(Locations.crShelterTemplate)
        editForm.getElementFromKey("cr_shelter_name").setValue(shelterName)
        editForm.getElementFromKey("gis_location_L0").setValue(L0)
        editForm.getElementFromKey("gis_location_name").setValue(shelterName)
        editForm.removeElement("gis_location_L1_search")
        editForm.removeElement("gis_location_L2_search")
        editForm.removeElement("gis_location_L3_search")
        editForm.removeElement("gis_location_L4_search")
        editForm.removeElement("gis_location_L5_search")

        viewForm = copy.deepcopy(editForm)
        viewForm.getElementFromKey("gis_location_street").setHide()
        viewForm.getElementFromKey("gis_location_postcode").setHide()
        viewForm.getElementFromKey("gis_location_L1_ac").setHide()
        viewForm.getElementFromKey("gis_location_L2_ac").setHide()
        viewForm.getElementFromKey("gis_location_L3_ac").setHide()
        viewForm.getElementFromKey("gis_location_L4_ac").setHide()
        viewForm.getElementFromKey("gis_location_lat").setHide()
        viewForm.getElementFromKey("gis_location_lon").setHide()

        viewForm.checkForm()

        sel.click("gis_location_edit-btn")
        editForm.checkForm()

    def locationInL0(self):
        """ Create a new Shelter inside an L0 location
            NB This should fail if deployment_settings.gis.strict_hierarchy = True
        """
        shelterName = "Shelter with an L0 Location"
        L0 = "Haiti" 
        L1 = self.makeNameUnique("Specific Location in L0")
        sel = self.selenium
        sel.open("cr/shelter/create")
        # Fill in the mandatory fields
        self.action.fillForm("cr_shelter_name",shelterName)
        # Select the L0
        self.action.fillForm("gis_location_L0",L0,"select")
        self.action.fillForm("gis_location_L1",L1)
        # Save the form
        self.assertTrue(self.action.saveForm("Save", "Shelter added"))
        print "New shelter created"
        Locations.shelter.append(shelterName)
        Locations.line.append(L1)

        # Load again
        self.openRecord(shelterName)

        rHeading = self.action.getrHeaderTemplate()
        rHeading.addValue("Name:", shelterName)
        rHeading.addValue("Location:", "%s (%s)" % (shelterName, L1))
        rHeading.checkrHeader()

        editForm = copy.deepcopy(Locations.crShelterTemplate)
        editForm.getElementFromKey("cr_shelter_name").setValue(shelterName)
        editForm.getElementFromKey("gis_location_L0").setValue(L0)
        editForm.getElementFromKey("gis_location_name").setValue(shelterName)
        editForm.removeElement("gis_location_L1_search")
        editForm.removeElement("gis_location_L2_search")
        editForm.removeElement("gis_location_L3_search")
        editForm.removeElement("gis_location_L4_search")
        editForm.removeElement("gis_location_L5_search")

        viewForm = copy.deepcopy(editForm)
        viewForm.getElementFromKey("gis_location_street").setHide()
        viewForm.getElementFromKey("gis_location_postcode").setHide()
        viewForm.getElementFromKey("gis_location_L2_ac").setHide()
        viewForm.getElementFromKey("gis_location_L3_ac").setHide()
        viewForm.getElementFromKey("gis_location_L4_ac").setHide()
        viewForm.getElementFromKey("gis_location_lat").setHide()
        viewForm.getElementFromKey("gis_location_lon").setHide()

        viewForm.checkForm()

        sel.click("gis_location_edit-btn")
        editForm.checkForm()

    def locationL1(self):
        """ Create a new Shelter with an L1 location """
        # Create the name variables
        shelterName = "Shelter with an L1 Location"
        L0 = "Haiti" 
        L1 = self.makeNameUnique("Ouest")
        
        sel = self.selenium
        sel.open("cr/shelter/create")
        # Fill in the mandatory fields
        self.action.fillForm("cr_shelter_name",shelterName)
        # Select the L0
        self.action.fillForm("gis_location_L0",L0,"select")
        self.action.fillForm("gis_location_L1",L1)
        # Save the form
        self.assertTrue(self.action.saveForm("Save", "Shelter added"))
        print "New shelter created"
        Locations.shelter.append(shelterName)
        Locations.line.append(L1)

        # Load again
        self.openRecord(shelterName)

        rHeading = self.action.getrHeaderTemplate()
        rHeading.addValue("Name:", shelterName)
        rHeading.addValue("Location:", "%s (%s)" % (shelterName, L1))
        rHeading.checkrHeader()

        editForm = copy.deepcopy(Locations.crShelterTemplate)
        editForm.getElementFromKey("cr_shelter_name").setValue(shelterName)
        editForm.getElementFromKey("gis_location_L0").setValue(L0)
        editForm.getElementFromKey("gis_location_name").setValue(shelterName)
        editForm.removeElement("gis_location_L1_search")
        editForm.removeElement("gis_location_L2_search")
        editForm.removeElement("gis_location_L3_search")
        editForm.removeElement("gis_location_L4_search")
        editForm.removeElement("gis_location_L5_search")

        viewForm = copy.deepcopy(editForm)
        viewForm.getElementFromKey("gis_location_street").setHide()
        viewForm.getElementFromKey("gis_location_postcode").setHide()
        viewForm.getElementFromKey("gis_location_L2_ac").setHide()
        viewForm.getElementFromKey("gis_location_L3_ac").setHide()
        viewForm.getElementFromKey("gis_location_L4_ac").setHide()
        viewForm.getElementFromKey("gis_location_lat").setHide()
        viewForm.getElementFromKey("gis_location_lon").setHide()

        viewForm.checkForm()

        sel.click("gis_location_edit-btn")
        editForm.checkForm()

        
















    def test_addL0Location(self):
        """ Update an existing Shelter without any Location specified to an L0 """
        shelterName = "Shelter with no Location"
        
        sel = self.selenium
        self.openRecord(shelterName)
        # Check that the location is still blank
        self.initFormDetails()
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Save the form (with changes)
        self.action.saveForm("Shelter updated")
        print "Level 0 Location added "
        # Load again
        self.openRecord(shelterName)
        # Check that the location is set
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : "Haiti (Country)",
                                 })

        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        
        self.initFormDetails()
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

    def test_removeL0Location(self):
        """ Update an existing Shelter with an L0 Location to have no location """
        shelterName = "Shelter with no Location"
        
        sel = self.selenium
        self.openRecord(shelterName)
        # Check that the details are correct
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : "Haiti (Country)",
                                 })
        # Check that the location is currently set
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.assertEqual(location_id, sel.get_value("cr_shelter_location_id"))
        # Check that the dropdown is set
        self.assertEqual(location_id, sel.get_value("gis_location_L0"))
        self.initFormDetails()
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

        # De-select the L0
        sel.select("gis_location_L0", "label=Select a location...")
        # Check that the real location has been set to blank
        self.assertEqual("", sel.get_value("cr_shelter_location_id"))
        # Save the form (with changes)
        self.action.saveForm("Shelter updated")
        # Load again
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : "-",
                                 })
        Locations.formDetails[0][3] = ""
        Locations.formDetails[5][2] = False
        Locations.formDetails[6][2] = False
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        
    def test_locationNoParent(self):
        """ Create a new Shelter with a parentless Location """
        # Create the name variables
        shelterName = "Shelter with no Parent"
        L0a = self.makeNameUnique("Location with no Parent")
        L0b = self.makeNameUnique("New parentless Location")
        address = "45 Sheep Street"
        
        sel = self.selenium
        sel.open("cr/shelter/create")
        self.initFormDetails()
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", shelterName)
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", L0a)
        # Save the form
        Locations.shelter.append(shelterName)
        Locations.line.append(L0a)
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : L0a,
                                 })
        # @ToDo: Hyperlink is no longer shown as we have no map location for this
        #location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        #location_id = location.split("(")[1].split(")")[0]
        self.initFormDetails()        
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        #Locations.formDetails[0][3] = location_id
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Deselect the L0 location
        sel.select("gis_location_", "label=Select a location...")
        # Check that the real location has been set to blank
        self.assertEqual("", sel.get_text("cr_shelter_location_id"))
        # Save the form (with changes)
        self.action.saveForm("Shelter updated")
        # Load again
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : "-",
                                 })
        Locations.formDetails[0][3] = ""
        Locations.formDetails[13][2] = False
        Locations.formDetails[14][2] = False
        Locations.formDetails[17][2] = False
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        sel.click("gis_location_add-btn")
        # Fill in a Name & Address
        sel.type("gis_location_name", L0b)
        sel.type("gis_location_addr_street", address)

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
        # Fill in Lat & Lon
        Locations.formDetails[3][2] = False
        Locations.formDetails[15][2] = True
        Locations.formDetails[16][2] = True
        Locations.formDetails[18][2] = True
        Locations.formDetails[20][2] = True
        Locations.formDetails[21][2] = True
        Locations.formDetails[22][2] = True
        Locations.formDetails[23][2] = True
        Locations.formDetails[24][2] = True
        Locations.formDetails[25][2] = True
        Locations.formDetails[26][2] = True
        Locations.formDetails[27][2] = True
        Locations.formDetails[28][2] = True
        Locations.formDetails[29][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        sel.type("gis_location_lat", "51")
        sel.type("gis_location_lon", "1")

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

        self.action.saveForm("Shelter updated")
        Locations.line.append(L0b)
        # Load again
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : "%s (N 51.0 E 1.0)" % L0b,
                                 })

        self.initFormDetails()
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        Locations.formDetails[25][3] = '51.0'
        Locations.formDetails[27][3] = '1.0'
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Click on 'Details' button
        sel.click("gis_location_details-btn")
        Locations.formDetails[20][2] = True
        Locations.formDetails[20][3] = address
        Locations.formDetails[21][2] = True
        Locations.formDetails[22][2] = True
        Locations.formDetails[23][2] = True
        Locations.formDetails[28][2] = True
        Locations.formDetails[29][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Open the Advanced Tab
        sel.click("gis_location_advanced_checkbox")
        Locations.formDetails[22][2] = True
        Locations.formDetails[23][2] = True
        Locations.formDetails[24][2] = True
        Locations.formDetails[25][2] = True
        Locations.formDetails[26][2] = True
        Locations.formDetails[27][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

        self.action.saveForm("Shelter updated")
        # Load again
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : "%s (N 51.0 E 1.0)" % L0b,
                                 })

        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        self.initFormDetails()
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        self.action.saveForm("Shelter updated")
        
    def test_locationL0(self):
        """ Create a new Shelter with an L0 location """
        # Create the name variables
        shelterName = "Shelter with an L0 Location"
        L0 = "Haiti" 
        sel = self.selenium
        sel.open("cr/shelter/create")
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", shelterName)
        # Select the L0
        sel.select("gis_location_L0", "label=%s" % L0)
        # Save the form
        Locations.shelter.append(shelterName)
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)

        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : L0,
                                })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        self.initFormDetails()
        location_id = location.split("(")[1].split(")")[0]
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

    def test_locationInL0(self):
        """ Create a new Shelter inside an L0 location
            NB This should fail if deployment_settings.gis.strict_hierarchy = True
        """
        # Create the name variables
        shelterName = "Shelter within L0 Location"
        L1 = self.makeNameUnique("Specific Location in L0")
        
        sel = self.selenium
        sel.open("cr/shelter/create")
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", shelterName)
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", L1)
        # Save the form
        Locations.shelter.append(shelterName)
        Locations.line.append(L1)
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : L1,
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

    def test_locationL1(self):
        """ Create a new Shelter with an L1 location """
        # Create the name variables
        shelterName = "Shelter with an L1 Location"
        L1 = self.makeNameUnique("Ouest")
        
        sel = self.selenium
        sel.open("cr/shelter/create")
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", shelterName)
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # wait for the L1 list to be populated
        for i in range(10):
            try:
                # Select the L1
                sel.select("gis_location_L1", "label=%s" % L1)
                break
            except:
                time.sleep(1)

        # Save the form
        Locations.shelter.append(shelterName)
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : "%s (Province, Haiti)" % L1,
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.initFormDetails()
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )


    def test_locationInL1(self):
        """ Create a new Shelter inside an L1 location """
        # Create the name variables
        shelterName = "Shelter within L1 Location"
        L1a = self.makeNameUnique("Ouest")
        L1b = self.makeNameUnique("Specific Location in L1")

        sel = self.selenium
        sel.open("cr/shelter/create")
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", shelterName)
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # wait for the L1 list to appear
        time.sleep(4)
        for i in range(10):
            if sel.is_visible("gis_location_L1"):
                break
            time.sleep(1)
        self.assertTrue(sel.is_visible("gis_location_L1"))
        # Select the L1
        sel.select("gis_location_L1", "label=%s" % L1a)
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", L1b)
        # Save the form
        Locations.shelter.append(shelterName)
        Locations.line.append(L1b)
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : L1b,
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

    def test_locationL2(self):
        """ Create a new Shelter with an L2 location """
        # Create the name variables
        shelterName = "Shelter with an L2 Location"
        L1 = self.makeNameUnique("Ouest")
        L2 = self.makeNameUnique("Port-Au-Prince")
        
        sel = self.selenium
        sel.open("cr/shelter/create")
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", shelterName)
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # wait for the L1 list to be populated
        for i in range(10):
            try:
                # Select the L1
                sel.select("gis_location_L1", "label=%s" % L1)
                break
            except:
                time.sleep(1)
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                # Select the L1
                sel.select("gis_location_L2", "label=%s" % L2)
                break
            except:
                time.sleep(1)


        # Save the form
        Locations.shelter.append(shelterName)
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : "%s" % shelterName,
                                  "Location:" : "%s (District, %s)" % (L2, L1),
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.initFormDetails()
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )


    def test_locationInL2(self):
        """ Create a new Shelter inside an L2 location """
        # Create the name variables
        shelterName = "Shelter within L2 Location"
        L1 = self.makeNameUnique("Ouest")
        L2a = self.makeNameUnique("Port-Au-Prince")
        L2b = self.makeNameUnique("Specific Location in L2")
        
        sel = self.selenium
        sel.open("cr/shelter/create")
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", shelterName)
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # wait for the L1 list to be populated
        for i in range(10):
            try:
                # Select the L1
                sel.select("gis_location_L1", "label=%s" % L1)
                break
            except:
                time.sleep(1)
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                # Select the L1
                sel.select("gis_location_L2", "label=%s" % L2a)
                break
            except:
                time.sleep(1)

        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", L2b)
        # Save the form
        Locations.shelter.append(shelterName)
        Locations.line.append(L2b)
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : L2b,
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.initFormDetails()
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

    def test_locationL3(self):
        """ Create a new Shelter with an L3 location """
        # Create the name variables
        shelterName = "Shelter with an L3 Location"
        L1 = self.makeNameUnique("Ouest")
        L2 = self.makeNameUnique("Port-Au-Prince")
        L3 = self.makeNameUnique("Martissant")
        
        sel = self.selenium
        sel.open("cr/shelter/create")
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", shelterName)
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # wait for the L1 list to be populated
        for i in range(10):
            try:
                # Select the L1
                sel.select("gis_location_L1", "label=%s" % L1)
                break
            except:
                time.sleep(1)
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                # Select the L1
                sel.select("gis_location_L2", "label=%s" % L2)
                break
            except:
                time.sleep(1)
        # wait for the L3 list to be populated
        for i in range(10):
            try:
                # Select the L1
                sel.select("gis_location_L3", "label=%s" % L3)
                break
            except:
                time.sleep(1)


        # Save the form
        Locations.shelter.append(shelterName)
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : "%s" % shelterName,
                                  "Location:" : "%s (Town, %s)" % (L3, L2),
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.initFormDetails()
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )


    def test_locationInL3(self):
        """ Create a new Shelter inside an L3 location """
        # Create the name variables
        shelterName = "Shelter within L3 Location"
        L1 = self.makeNameUnique("Ouest")
        L2 = self.makeNameUnique("Port-Au-Prince")
        L3a = self.makeNameUnique("Martissant")
        L3b = self.makeNameUnique("Specific Location in L3")
        
        sel = self.selenium
        sel.open("cr/shelter/create")
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", shelterName)
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # wait for the L1 list to be populated
        for i in range(10):
            try:
                # Select the L1
                sel.select("gis_location_L1", "label=%s" % L1)
                break
            except:
                time.sleep(1)
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                # Select the L1
                sel.select("gis_location_L2", "label=%s" % L2)
                break
            except:
                time.sleep(1)
        # wait for the L3 list to be populated
        for i in range(10):
            try:
                # Select the L1
                sel.select("gis_location_L3", "label=%s" % L3a)
                break
            except:
                time.sleep(1)

        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", L3b)
        # Save the form
        Locations.shelter.append(shelterName)
        Locations.line.append(L3b)
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : L3b,
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.initFormDetails()
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

    def test_locationL4(self):
        """ Create a new Shelter with an L4 location """
        # Create the name variables
        shelterName = "Shelter with an L4 Location"
        L1 = self.makeNameUnique("Ouest")
        L2 = self.makeNameUnique("Port-Au-Prince")
        L3 = self.makeNameUnique("Martissant")
        L4 = self.makeNameUnique("Carrefour Feuilles")
        
        sel = self.selenium
        sel.open("cr/shelter/create")
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", shelterName)
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # wait for the L1 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L1", "label=%s" % L1)
                break
            except:
                time.sleep(1)
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L2", "label=%s" % L2)
                break
            except:
                time.sleep(1)
        # wait for the L3 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L3", "label=%s" % L3)
                break
            except:
                time.sleep(1)
        # wait for the L4 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L4", "label=%s" % L4)
                break
            except:
                time.sleep(1)


        # Save the form
        Locations.shelter.append(shelterName)
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : "%s" % shelterName,
                                  "Location:" : L4,
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.initFormDetails()
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )


    def test_locationInL4(self):
        """ Create a new Shelter inside an L4 location """
        # Create the name variables
        shelterName = "Shelter within L4 Location"
        L1 = self.makeNameUnique("Ouest")
        L2 = self.makeNameUnique("Port-Au-Prince")
        L3 = self.makeNameUnique("Martissant")
        L4a = self.makeNameUnique("Carrefour Feuilles")
        L4b = self.makeNameUnique("Specific Location in L4")
        
        sel = self.selenium
        sel.open("cr/shelter/create")
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", shelterName)
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # wait for the L1 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L1", "label=%s" % L1)
                break
            except:
                time.sleep(1)
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L2", "label=%s" % L2)
                break
            except:
                time.sleep(1)
        # wait for the L3 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L3", "label=%s" % L3)
                break
            except:
                time.sleep(1)
        # wait for the L4 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L4", "label=%s" % L4a)
                break
            except:
                time.sleep(1)

        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", L4b)
        # Save the form
        Locations.shelter.append(shelterName)
        Locations.line.append(L4b)
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : L4b,
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.initFormDetails()
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
    
    def test_updateLocationInL4NewInL3(self):
        """ Update a Shelter inside an L4 location to being inside a NEW location in an L3"""
        # Create the name variables
        shelterName = "Shelter within L4 Location"
        L3a = self.makeNameUnique("Turgeau")
        L3b = self.makeNameUnique("New in L3")
        L4 = self.makeNameUnique("Specific Location in L4")
        addr = "5 Ruelle Chochotte"
        lat = "18.53171116"
        lon = "-72.33020758"
        
        sel = self.selenium
        # Load the Shelter
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : L4,
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.initFormDetails()
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

        # Select the L3
        sel.select("gis_location_L3", "label=%s" % L3a)

        # Click on the Add button
        sel.click("gis_location_add-btn")
        # Check that the components appear correctly
#        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
#        location_id = location.split("(")[1].split(")")[0]

        location_id = sel.get_selected_value("gis_location_L3")
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[3][2] = False
        Locations.formDetails[13][2] = False
        Locations.formDetails[14][2] = False
        Locations.formDetails[15][2] = True
        Locations.formDetails[16][2] = True
        Locations.formDetails[17][2] = False
        Locations.formDetails[18][2] = True
        Locations.formDetails[20][2] = True
        Locations.formDetails[21][2] = True
        Locations.formDetails[22][2] = True
        Locations.formDetails[23][2] = True
        Locations.formDetails[28][2] = True
        Locations.formDetails[29][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

        # Fill in a Name & Address
        sel.type("gis_location_name", L3b)
        sel.type("gis_location_addr_street", addr)

        # Open the Advanced Tab
        sel.click("gis_location_advanced_checkbox")
        # Check that the components appear correctly
        Locations.formDetails[24][2] = True
        Locations.formDetails[25][2] = True
        Locations.formDetails[26][2] = True
        Locations.formDetails[27][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

        # Fill in Lat & Lon
        sel.type("gis_location_lat", lat)
        sel.type("gis_location_lon", lon)

        # Save the form (with changes)
        Locations.line.append(L3b)
        self.action.saveForm("Shelter updated")

        # Shelter has correct location
        #self.action.checkHeading({"Name:" : shelterName,
        #                          "Location:" : "%s (N %s W %s)" %(L3b, lat, lon)
        #                         })
        # Save -> List not Record
        self.assertEqual("List Shelters", sel.get_text("//div[@id='content']/h2"))

        # Load again
        self.openRecord(shelterName)
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : "%s (N %s W %s)" %(L3b, lat, lon)
                                 })
        # Check that the location is set
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        Locations.formDetails[0][3] = location_id
        self.initFormDetails()
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

        # Click on 'Details' button
        sel.click("gis_location_details-btn")
        # Check that the components which should be visible, are
        Locations.formDetails[20][2] = True
        Locations.formDetails[20][3] = addr
        Locations.formDetails[21][2] = True
        Locations.formDetails[22][2] = True
        Locations.formDetails[23][2] = True
        Locations.formDetails[28][2] = True
        Locations.formDetails[29][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )


        # Open the Advanced Tab
        sel.click("gis_location_advanced_checkbox")
        # Check that the components appear correctly
        Locations.formDetails[24][2] = True
        Locations.formDetails[25][2] = True
        Locations.formDetails[25][3] = lat
        Locations.formDetails[26][2] = True
        Locations.formDetails[27][2] = True
        Locations.formDetails[27][3] = lon
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

    def test_locationSelectSpecific(self):
        """ Create a new Shelter with a pre-existing specific location """
        shelterName = "Shelter with a pre-existing specific Location"
        L1 = self.makeNameUnique("Ouest")
        L2 = self.makeNameUnique("Port-Au-Prince")
        L3 = self.makeNameUnique("Martissant")
        L4 = self.makeNameUnique("Carrefour Feuilles")
        location = self.makeNameUnique("Clinique Communautaire de Martissant")
        lat = "18.528000849"
        lon = "-72.3489983828"
        
        sel = self.selenium
        sel.open("cr/shelter/create")
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", shelterName)
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # wait for the L1 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L1", "label=%s" % L1)
                break
            except:
                time.sleep(1)
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L2", "label=%s" % L2)
                break
            except:
                time.sleep(1)
        # wait for the L3 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L3", "label=%s" % L3)
                break
            except:
                time.sleep(1)
        # wait for the L4 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L4", "label=%s" % L4)
                break
            except:
                time.sleep(1)
        # wait for the specific location list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_", "label=%s" % location)
                break
            except:
                time.sleep(1)
        # Save the form
        Locations.shelter.append(shelterName)   
        self.action.saveForm("Shelter added")

        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : "%s (N %s W %s)" %(location, lat, lon)
                                 })

    def test_locationSearch(self):
        """ Search for Locations using the Autocomplete """

        # @ToDo: Verify that the result is stored correctly
        # How do we get name from number without submitting? Should we just submit every time?

        shelterName = self.makeNameUnique("Shelter L2inL0")
        search = self.makeNameUnique("L2inL0")
        
        sel = self.selenium
        sel.open("cr/shelter/create")
        sel.type("cr_shelter_name", shelterName)
        # Open the Search box
        sel.click("gis_location_search-btn")
        self.initFormDetails()
        Locations.formDetails[19][2] = False
        Locations.formDetails[30][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

        # Enter the search String
        sel.type("gis_location_autocomplete", search)
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if search == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L2", "label=%s" % search)
                break
            except:
                time.sleep(1)
        
        self.initFormDetails()
        location_id = sel.get_selected_value("gis_location_L2")
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Save the form
        Locations.shelter.append(shelterName)   
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : search,
                                 })

        ###############################################################
        # Next Test
        ###############################################################
        shelterName = self.makeNameUnique("Shelter L2inL1withNoParent")
        search = self.makeNameUnique("L2inL1withNoParent")
        sel.open("cr/shelter/create")
        sel.type("cr_shelter_name", shelterName)
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Enter the search String
        sel.type("gis_location_autocomplete", search)
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if search == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L2", "label=%s" % search)
                break
            except:
                time.sleep(1)
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L0"))
        self.assertEqual(self.makeNameUnique("L1withNoParent"), sel.get_selected_label("gis_location_L1"))
        self.assertEqual(self.makeNameUnique("L2inL1withNoParent"), sel.get_selected_label("gis_location_L2"))

        self.initFormDetails()
        location_id = sel.get_selected_value("gis_location_L2")
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Save the form
        Locations.shelter.append(shelterName)   
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : search,
                                 })

        ###############################################################
        # Next Test
        ###############################################################
        shelterName = self.makeNameUnique("Shelter L3inL0")
        search = self.makeNameUnique("L3inL0")
        sel.open("cr/shelter/create")
        sel.type("cr_shelter_name", shelterName)
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Enter the search String
        sel.type("gis_location_autocomplete", search)
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if search == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L3", "label=%s" % search)
                break
            except:
                time.sleep(1)

        self.assertEqual("Haiti", sel.get_selected_label("gis_location_L0"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L1"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L2"))
        self.assertEqual(search, sel.get_selected_label("gis_location_L3"))
        
        self.initFormDetails()
        location_id = sel.get_selected_value("gis_location_L3")
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Save the form
        Locations.shelter.append(shelterName)   
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : search,
                                 })

        ###############################################################
        # Next Test
        ###############################################################
        shelterName = self.makeNameUnique("Shelter L3inL1withL0")
        search = self.makeNameUnique("L3inL1withL0")
        sel.open("cr/shelter/create")
        sel.type("cr_shelter_name", shelterName)
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Enter the search String
        sel.type("gis_location_autocomplete", search)
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if search == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L3", "label=%s" % search)
                break
            except:
                time.sleep(1)

        self.assertEqual("Haiti", sel.get_selected_label("gis_location_L0"))
        self.assertEqual(self.makeNameUnique("Ouest"), sel.get_selected_label("gis_location_L1"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L2"))
        self.assertEqual(search, sel.get_selected_label("gis_location_L3"))
        
        self.initFormDetails()
        location_id = sel.get_selected_value("gis_location_L3")
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Save the form
        Locations.shelter.append(shelterName)   
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : search,
                                 })

        ###############################################################
        # Next Test
        ###############################################################
        shelterName = self.makeNameUnique("Shelter L3inL1withNoParent")
        search = self.makeNameUnique("L3inL1withNoParent")
        sel.open("cr/shelter/create")
        sel.type("cr_shelter_name", shelterName)
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Enter the search String
        sel.type("gis_location_autocomplete", search)
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if search == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L3", "label=%s" % search)
                break
            except:
                time.sleep(1)

        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L0"))
        self.assertEqual(self.makeNameUnique("L1withNoParent"), sel.get_selected_label("gis_location_L1"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L2"))
        self.assertEqual(search, sel.get_selected_label("gis_location_L3"))
        
        self.initFormDetails()
        location_id = sel.get_selected_value("gis_location_L3")
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Save the form
        Locations.shelter.append(shelterName)   
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : search,
                                 })

        ###############################################################
        # Next Test
        ###############################################################
        shelterName = self.makeNameUnique("Shelter L4inL0")
        search = self.makeNameUnique("L4inL0")
        sel.open("cr/shelter/create")
        sel.type("cr_shelter_name", shelterName)
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Enter the search String
        sel.type("gis_location_autocomplete", search)
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if search == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L4", "label=%s" % search)
                break
            except:
                time.sleep(1)

        self.assertEqual("Haiti", sel.get_selected_label("gis_location_L0"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L1"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L2"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L3"))
        self.assertEqual(search, sel.get_selected_label("gis_location_L4"))
        
        self.initFormDetails()
        location_id = sel.get_selected_value("gis_location_L4")
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Save the form
        Locations.shelter.append(shelterName)   
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : search,
                                 })

        ###############################################################
        # Next Test
        ###############################################################
        shelterName = self.makeNameUnique("Shelter L4inL1withL0")
        search = self.makeNameUnique("L4inL1withL0")
        sel.open("cr/shelter/create")
        sel.type("cr_shelter_name", shelterName)
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Enter the search String
        sel.type("gis_location_autocomplete", search)
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if search == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L4", "label=%s" % search)
                break
            except:
                time.sleep(1)

        self.assertEqual("Haiti", sel.get_selected_label("gis_location_L0"))
        self.assertEqual(self.makeNameUnique("Ouest"), sel.get_selected_label("gis_location_L1"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L2"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L3"))
        self.assertEqual(search, sel.get_selected_label("gis_location_L4"))
        
        self.initFormDetails()
        location_id = sel.get_selected_value("gis_location_L4")
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Save the form
        Locations.shelter.append(shelterName)   
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : search,
                                 })

        ###############################################################
        # Next Test
        ###############################################################
        shelterName = self.makeNameUnique("Shelter L4inL1withNoParent")
        search = self.makeNameUnique("L4inL1withNoParent")
        sel.open("cr/shelter/create")
        sel.type("cr_shelter_name", shelterName)
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Enter the search String
        sel.type("gis_location_autocomplete", search)
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if search == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L4", "label=%s" % search)
                break
            except:
                time.sleep(1)

        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L0"))
        self.assertEqual(self.makeNameUnique("L1withNoParent"), sel.get_selected_label("gis_location_L1"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L2"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L3"))
        self.assertEqual(search, sel.get_selected_label("gis_location_L4"))
        
        self.initFormDetails()
        location_id = sel.get_selected_value("gis_location_L4")
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Save the form
        Locations.shelter.append(shelterName)   
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : search,
                                 })
        
        ###############################################################
        # Next Test
        ###############################################################
        shelterName = self.makeNameUnique("Shelter L4inL2withL1L0")
        search = self.makeNameUnique("L4inL2withL1L0")
        sel.open("cr/shelter/create")
        sel.type("cr_shelter_name", shelterName)
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Enter the search String
        sel.type("gis_location_autocomplete", search)
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if search == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L4", "label=%s" % search)
                break
            except:
                time.sleep(1)

        self.assertEqual("Haiti", sel.get_selected_label("gis_location_L0"))
        self.assertEqual(self.makeNameUnique("Ouest"), sel.get_selected_label("gis_location_L1"))
        self.assertEqual(self.makeNameUnique("Port-Au-Prince"), sel.get_selected_label("gis_location_L2"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L3"))
        self.assertEqual(search, sel.get_selected_label("gis_location_L4"))
        
        self.initFormDetails()
        location_id = sel.get_selected_value("gis_location_L4")
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Save the form
        Locations.shelter.append(shelterName)   
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : search,
                                 })
                                 
        ###############################################################
        # Next Test
        ###############################################################
        shelterName = self.makeNameUnique("Shelter L4inL2withL1only")
        search = self.makeNameUnique("L4inL2withL1only")
        sel.open("cr/shelter/create")
        sel.type("cr_shelter_name", shelterName)
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Enter the search String
        sel.type("gis_location_autocomplete", search)
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if search == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L4", "label=%s" % search)
                break
            except:
                time.sleep(1)

        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L0"))
        self.assertEqual(self.makeNameUnique("L1withNoParent"), sel.get_selected_label("gis_location_L1"))
        self.assertEqual(self.makeNameUnique("L2inL1withNoParent"), sel.get_selected_label("gis_location_L2"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L3"))
        self.assertEqual(search, sel.get_selected_label("gis_location_L4"))
        
        self.initFormDetails()
        location_id = sel.get_selected_value("gis_location_L4")
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Save the form
        Locations.shelter.append(shelterName)   
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : search,
                                 })
        
        ###############################################################
        # Next Test
        ###############################################################
        shelterName = self.makeNameUnique("Shelter L4inL2withL0only")
        search = self.makeNameUnique("L4inL2withL0only")
        sel.open("cr/shelter/create")
        sel.type("cr_shelter_name", shelterName)
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Enter the search String
        sel.type("gis_location_autocomplete", search)
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if search == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        # wait for the L2 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L4", "label=%s" % search)
                break
            except:
                time.sleep(1)

        self.assertEqual("Haiti", sel.get_selected_label("gis_location_L0"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L1"))
        self.assertEqual(self.makeNameUnique("L2inL0"), sel.get_selected_label("gis_location_L2"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L3"))
        self.assertEqual(search, sel.get_selected_label("gis_location_L4"))
        
        self.initFormDetails()
        location_id = sel.get_selected_value("gis_location_L4")
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Save the form
        Locations.shelter.append(shelterName)   
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : search,
                                 })
        
        ###############################################################
        # Next Test
        ###############################################################
        shelterName = self.makeNameUnique("Shelter L4inL2withNoParent")
        search = self.makeNameUnique("L4inL2withNoParent")
        sel.open("cr/shelter/create")
        sel.type("cr_shelter_name", shelterName)
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Enter the search String
        sel.type("gis_location_autocomplete", search)
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if search == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        # wait for the L4 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L4", "label=%s" % search)
                break
            except:
                time.sleep(1)

        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L0"))
        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L1"))
        self.assertEqual(self.makeNameUnique("L2withNoParent"), sel.get_selected_label("gis_location_L2"))
        self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L3"))
        self.assertEqual(search, sel.get_selected_label("gis_location_L4"))
        
        self.initFormDetails()
        location_id = sel.get_selected_value("gis_location_L4")
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[9][2] = True
        Locations.formDetails[10][2] = True
        Locations.formDetails[11][2] = True
        Locations.formDetails[12][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Save the form
        Locations.shelter.append(shelterName)   
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : search,
                                 })
        
        ###############################################################
        # Next Test
        ###############################################################
        shelterName = self.makeNameUnique("Shelter SpecificNoParent")
        search = self.makeNameUnique("SpecificNoParent")
        sel.open("cr/shelter/create")
        sel.type("cr_shelter_name", shelterName)
        # Open the Search box
        sel.click("gis_location_search-btn")
        # Enter the search String
        sel.type("gis_location_autocomplete", search)
        # Trigger the event to get the AJAX to send
        sel.fire_event("gis_location_autocomplete", "keydown")
        # Wait for the popup menu
        for i in range(60):
            try:
                if search == sel.get_text("css=ul.ui-autocomplete li:first-child a"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        # Select the Result
        sel.fire_event("css=ul.ui-autocomplete li:first-child a", "mouseover")
        sel.click("css=ul.ui-autocomplete li:first-child a")
        # wait for the L4 list to be populated
        for i in range(10):
            try:
                sel.select("gis_location_L4", "label=%s" % search)
                break
            except:
                time.sleep(1)

        self.assertEqual("Select a location...", sel.get_selected_label("gis_location_L0"))
        # Now hidden, so not loaded
        #self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L1"))
        #self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L2"))
        #self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L3"))
        #self.assertEqual("No locations registered at this level", sel.get_selected_label("gis_location_L4"))
        
        self.initFormDetails()
        location_id = sel.get_selected_value("gis_location_")
        Locations.formDetails[0][3] = location_id
        #Locations.formDetails[5][2] = True
        #Locations.formDetails[6][2] = True
        #Locations.formDetails[7][2] = True
        #Locations.formDetails[8][2] = True
        #Locations.formDetails[9][2] = True
        #Locations.formDetails[10][2] = True
        #Locations.formDetails[11][2] = True
        #Locations.formDetails[12][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Save the form
        Locations.shelter.append(shelterName)   
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord(shelterName)
        # Shelter has correct location
        self.action.checkHeading({"Name:" : shelterName,
                                  "Location:" : search,
                                 })
        
        
if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
