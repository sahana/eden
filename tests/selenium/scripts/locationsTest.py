from sahanaTest import SahanaTest
import unittest, time, re
import copy

class LocationTest(SahanaTest):
    """
        Test the locationWidget - This is done using the shelter registry
    
        All tests can assume that they will be logged in with the admin account at the start.
        Any test that requires a different account must log into that account perform the action
        and then log back into the admin account.  
    """
    holder = "**TEST**"
    _sortList = ("testSecurity",
                 "createLocations",
                 "createSheltersUsingLocations",
                 #"createSheltersCreatingLocations",
                 "deleteShelters",
                 #"deleteLocations",
                 )

    def firstRun(self):
        self.action.logout()
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password)

        LocationTest.line = []
        LocationTest.shelter = []
        self.initFormDetails()

    def initFormDetails(self):
        """ Setup the templates for the Shelter Form """

        # Initial Template
        LocationTest.crShelterTemplate = self.action.getFormTemplate()
        LocationTest.crShelterTemplate.addInput(labelID="cr_shelter_location_id__label",
                                                inputID="cr_shelter_location_id")
        LocationTest.crShelterTemplate.addInput(labelID="cr_shelter_organisation_id__label",
                                                inputID="dummy_cr_shelter_organisation_id")
        LocationTest.crShelterTemplate.addInput(labelID="cr_shelter_organisation_id__label",
                                                inputID="cr_shelter_organisation_id", visible=False)
        LocationTest.crShelterTemplate.addSelect(labelID="cr_shelter_shelter_type_id__label",
                                                 selectID="cr_shelter_shelter_type_id")
        LocationTest.crShelterTemplate.addSelect(labelID="cr_shelter_shelter_service_id__label",
                                                 selectID="cr_shelter_shelter_service_id")
        LocationTest.crShelterTemplate.addInput(inputID="cr_shelter_location_id", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_search_ac", visible=False)
        LocationTest.crShelterTemplate.addSelect(selectID="gis_location_L0")
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L0_search", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_name")
        LocationTest.crShelterTemplate.addTextArea(textID="gis_location_street")
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_postcode")
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_postcode_search", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L1", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L1_ac")
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L1_search", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L2", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L2_ac")
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L2_search", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L3", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L3_ac")
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L3_search", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L4", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L4_ac")
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L4_search", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L5", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L5_ac", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_L5_search", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_lat")
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_lat_search", visible=False)
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_lon")
        LocationTest.crShelterTemplate.addInput(inputID="gis_location_lon_search", visible=False)
        LocationTest.crShelterTemplate.addInput(labelID="cr_shelter_phone__label",
                                                inputID="cr_shelter_phone")
        LocationTest.crShelterTemplate.addInput(labelID="cr_shelter_person_id__label",
                                                inputID="dummy_cr_shelter_person_id")
        LocationTest.crShelterTemplate.addInput(labelID="cr_shelter_person_id__label",
                                                inputID="cr_shelter_person_id", visible=False)
        LocationTest.crShelterTemplate.addInput(labelID="cr_shelter_population__label",
                                                inputID="cr_shelter_population")
        LocationTest.crShelterTemplate.addInput(labelID="cr_shelter_capacity__label",
                                                inputID="cr_shelter_capacity")
        LocationTest.crShelterTemplate.addInput(labelID="cr_shelter_source__label",
                                                inputID="cr_shelter_source")
        LocationTest.crShelterTemplate.addInput(labelID="cr_shelter_document_id__label",
                                                inputID="dummy_cr_shelter_document_id")
        LocationTest.crShelterTemplate.addInput(labelID="cr_shelter_document_id__label",
                                                inputID="cr_shelter_document_id", visible=False)
        LocationTest.crShelterTemplate.addTextArea(labelID="cr_shelter_comments__label",
                                                   textID="cr_shelter_comments")
        LocationTest.crShelterTemplate.addButton("Save")

        LocationTest.rHeading = self.action.getrHeaderTemplate()
        LocationTest.rHeading.addValue("Name:", "-")
        LocationTest.rHeading.addValue("Location:", "-")

        # Template for Update form
        LocationTest.editcrShelterTemplate = copy.deepcopy(LocationTest.crShelterTemplate)
        LocationTest.editcrShelterTemplate.removeElement("gis_location_L1_search")
        LocationTest.editcrShelterTemplate.removeElement("gis_location_L2_search")
        LocationTest.editcrShelterTemplate.removeElement("gis_location_L3_search")
        LocationTest.editcrShelterTemplate.removeElement("gis_location_L4_search")
        LocationTest.editcrShelterTemplate.removeElement("gis_location_L5_search")

        # Template for View form
        LocationTest.viewcrShelterTemplate = copy.deepcopy(LocationTest.editcrShelterTemplate)
        LocationTest.viewcrShelterTemplate.getElementFromKey("gis_location_street").setHide()
        LocationTest.viewcrShelterTemplate.getElementFromKey("gis_location_postcode").setHide()
        LocationTest.viewcrShelterTemplate.getElementFromKey("gis_location_L1_ac").setHide()
        LocationTest.viewcrShelterTemplate.getElementFromKey("gis_location_L2_ac").setHide()
        LocationTest.viewcrShelterTemplate.getElementFromKey("gis_location_L3_ac").setHide()
        LocationTest.viewcrShelterTemplate.getElementFromKey("gis_location_L4_ac").setHide()
        LocationTest.viewcrShelterTemplate.getElementFromKey("gis_location_lat").setHide()
        LocationTest.viewcrShelterTemplate.getElementFromKey("gis_location_lon").setHide()

    # Helper methods
    def makeNameUnique(self, name):
        return self.holder + name + self.holder

    def loadLocations(self):
        """ Create locations from the data file """
        sel = self.selenium
        source = open("../data/testLocations.txt", "r")
        values = source.readlines()
        source.close()
        for location in values:
            name = level = parent = lat = lon = None
            details = location.split(",")
            if len(details) >= 1:
                name = details[0].strip()
            if len(details) >= 2:
                level = details[1].strip()
            if len(details) >= 3:
                parent = details[2].strip()
            if len(details) >= 4:
                lat = details[3].strip()
            if len(details) >= 5:
                lon = details[4].strip()
            # wrap all location names with the holder **TEST**
            # This makes deletion of a unique name easier
            newLocation = self.makeNameUnique(name)
            # Load the Location page and check that the location doesn't already exist
            sel.open("gis/location")
            matches = self.action.searchMatchesFound(newLocation)
            if matches == 0:
                self.addLocation(name, level, parent, lat, lon)
            if parent == None:
                LocationTest.line.append(newLocation)
            else:
                LocationTest.line.insert(0,newLocation)
            print "%s %s" % (name, matches)

    def addLocation(self, name, level, parent=None, lat=None, lon=None):
        """ Add a Location """
        sel = self.selenium
        name = self.makeNameUnique(name)
        if parent == None:
            parentHolder = None
        else:
            parentHolder = self.makeNameUnique(parent)
        # Load the Create Location page
        sel.open("gis/location/create")
        # Create the Location
        sel.type("gis_location_name", name)
        if level:
            sel.select("gis_location_level", "value=%s" % level)
        # Fill the form
        self.action.fillForm("gis_location_name", name)
        self.action.fillForm("gis_location_level", name)
        if parent != None:
            self.action.fillForm("gis_location_parent", parent)
        if lat != None:
            self.action.fillForm("gis_location_lat", lat)
        if lon != None:
            self.action.fillForm("gis_location_lon", lon)
        # Save the form
        self.assertTrue(self.action.saveForm("Save", "Location added"))
        print "Location %s created" % name

    def createLocations(self):
        self.loadLocations()
    
    def testSecurity(self):
        """ Check that normal users cannot create L1 locations """
        # Login as User
        self.action.logout()
        self.useSahanaUserAccount()
        self.action.login(self._user, self._password)
        
        # Try to create an L1 record
        sel = self.selenium
        sel.open("gis/location/create")
        sel.select("gis_location_level", "value=L1")
        self.action.fillForm("gis_location_name", "L1 Fail")
        self.assertTrue(self.action.saveForm("Save", "Sorry, only users", success=False))

        # Log back in as Admin
        self.action.logout()
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password)

    def createSheltersUsingLocations(self):
        """ Create Shelters using the created locations """

        for location in LocationTest.line:
            # Create a new Shelter using location
            # Create the name variables
            shelterName = "Shelter with Location %s" % location
            sel = self.selenium
            self.action.openPage("cr/shelter/create")
            # Fill in the mandatory fields
            self.action.fillForm("cr_shelter_name", shelterName)
            # Select the Location
            sel.click("gis_location_search-btn")
            self.action.fillForm("gis_location_search_ac", location)
            # Save the form
            self.assertTrue(self.action.saveForm("Save", "Shelter added"))
            print "%s created" % shelterName
            LocationTest.shelter.append(shelterName)
            LocationTest.editcrShelterTemplate.getElementFromKey("cr_shelter_name").setValue(shelterName)
            #LocationTest.editcrShelterTemplate.getElementFromKey("gis_location_L0").setValue("L0")
            LocationTest.editcrShelterTemplate.getElementFromKey("gis_location_name").setValue(shelterName)

            # Load again to check View form
            self.action.openPage("cr/shelter")
            self.action.searchUnique(shelterName)
            sel.click("link=Open")
            LocationTest.viewcrShelterTemplate.checkForm()

            # Check Edit form
            sel.click("gis_location_edit-btn")
            LocationTest.editcrShelterTemplate.checkForm()
    
    def createSheltersCreatingLocations(self):
        """ Create Shelters & new Locations at the same time, thus testing the Location Selector """
        pass
    
    def deleteShelters(self):
        """ Delete the shelters """
        for shelter in LocationTest.shelter:
            self.action.deleteObject("cr/shelter", shelter, "Shelter")
    
    def deleteLocations(self):
        """ Delete the locations """
        for location in LocationTest.line:
            self.action.deleteObject("gis/location", location, "Location")
