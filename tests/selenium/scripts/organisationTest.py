from sahanaTest import SahanaTest
import unittest, re

class OrganizationTest(SahanaTest):
    """ Test the Organization registry
    
        Test organisations are set up in the pre-populate phase.
        To ensure that the test data is loaded automatically set the status flag
        of deployment_settings.base.prepopulate to include the second bit.
        
        The organisation test data is held in the file:
        applications/eden/private/prepopulate/regression/organisation.csv  
    """
    
    _sortList = ("checkAuthentication",
                 "checkOrgForm",
                 "createDummyOrg",
                 "deleteDummyOrg",
                 "openOrgUIWithAdmin",
                 "openOrgUIWithNoUser",
                )
    
    def firstRun(self):
        # Setup the template for the Organisation From
        OrganizationTest.orgCreateTemplate = self.action.getFormTemplate()
        OrganizationTest.orgCreateTemplate.addInput(labelID="org_organisation_name__label",
                          inputID="org_organisation_name")
        OrganizationTest.orgCreateTemplate.addInput(labelID="org_organisation_acronym__label",
                          inputID="org_organisation_acronym")
        OrganizationTest.orgCreateTemplate.addSelect(labelID="org_organisation_type__label",
                           selectID="org_organisation_type")
        OrganizationTest.orgCreateTemplate.addSelect(labelID="org_organisation_sector_id__label",
                           selectID="org_organisation_sector_id")
        OrganizationTest.orgCreateTemplate.addSelect(labelID="org_organisation_country__label",
                           selectID="org_organisation_country")
        OrganizationTest.orgCreateTemplate.addInput(labelID="org_organisation_website__label",
                          inputID="org_organisation_website")
        OrganizationTest.orgCreateTemplate.addInput(labelID="org_organisation_twitter__label",
                          inputID="org_organisation_twitter").setBalloonTitle("Twitter")
        OrganizationTest.orgCreateTemplate.addInput(labelID="org_organisation_donation_phone__label",
                          inputID="org_organisation_donation_phone").setBalloonTitle("Donation")
        OrganizationTest.orgCreateTemplate.addTextArea(labelID="org_organisation_comments__label",
                          textID="org_organisation_comments").setBalloonTitle("Comments")
        OrganizationTest.orgCreateTemplate.addButton("Save")
        # load the pre-populated orgs from the csv file
        csvFile = "organisation.csv"
        OrganizationTest.orgs = self.action.prePopulateCSV(csvFile)
        print "orgs %s %s" % (len(OrganizationTest.orgs), OrganizationTest.orgs)


    def checkAuthentication(self):
        self.action.logout()
        self.action.openPage("org/organisation/create", heading="Login")

    def checkOrgForm(self):
        """ Test to check the elements of the create organisation form """
        # Log in as admin an then move to the add organisation page
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        self.action.openPage("org/organisation/create")
        # check that the UI controls are present
        self.orgCreateTemplate.checkForm()

    def createDummyOrg(self, name="DummyOrg"):
        # Log in as admin an then move to the add organisation page
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        # Add the dummy organisation
        
        acronym = "Dog"
        type = "International NGO"
        sector = "Education"
        country = "Australia"
        website = "www.dummy.org"
        phone = "05 1245 5421"
        comment = "This is a dummy organisation created by the OrganizationTest class."

        self.action.openPage("org/organisation/create", "Add Organization")

        self.action.fillForm("org_organisation_name",name)
        self.action.fillForm("org_organisation_acronym",acronym)
        self.action.fillForm("org_organisation_type",type,"select")
        self.action.fillForm("org_organisation_sector_id",sector,"select")
        self.action.fillForm("org_organisation_country",country,"select")
        self.action.fillForm("org_organisation_website",website)
        self.action.fillForm("org_organisation_donation_phone",phone)
        self.action.fillForm("org_organisation_comments",comment)
        # Now save the form
        self.assertTrue(self.action.saveForm("Save", "Organization added"))
        print "Organization %s created" % (name)

    def deleteDummyOrg(self, name="DummyOrg"):
        self.action.deleteObject("org/organisation", name, "Organization")

    def openOrgUIWithAdmin(self):
        """
            Test to check the elements of the list organisation form logged in with the admin account

            In turn it will check each of the tabs on the list screen
            and ensure that the data on the screen has been properly displayed.
        """

        if len(self.orgs) == 0:
            return
        org = self.orgs[0]
        self.orgCreateTemplate.addDataToTemplate(org, "org_organisation")
        self.orgCreateTemplate.getElementFromKey("org_organisation_sector_id").setValue(org["sector"])
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        self.action.openPage("org/organisation",force=True)
        print "Looking for %s" % org["name"]
        self.action.searchUnique(org["name"])
        self.action.clickBtn("Open")
        # check that the UI controls are present
        self.orgCreateTemplate.checkForm()

### NEED TO WORK ON THIS SOME MORE TO CHECK EACH TAB
        self.action.clickTab("Staff & Volunteers")
#        self.action.btnLink ("show-add-btn", "Add Staff")
#
        self.action.clickTab("Offices")
#        self.action.btnLink ("show-add-btn", "Add Office")

        self.action.clickTab("Assessments")
#        self.action.btnLink ("add-btn", "Add Assessment")
#
        self.action.clickTab("Projects")
#        self.action.btnLink ("show-add-btn", "Add Project")
#
        self.action.clickTab("Activities")
#        self.action.btnLink ("show-add-btn", "Add Activity")
        self.orgCreateTemplate.removeDataFromTemplate()
        
    def openOrgUIWithNoUser(self):
        """
            Test to check the elements of the list organisation form when not logged in

            In turn it will check each of the tabs on the list screen
            and ensure that the data on the screen has been properly displayed.
        """
        if len(self.orgs)==0:
            return
        org = self.orgs[0]
        self.orgCreateTemplate.addDataToTemplate(org, "org_organisation")
        self.orgCreateTemplate.getElementFromKey("org_organisation_sector_id").setValue(org["sector"])
        self.action.logout()
        self.action.openPage("org/organisation")
        self.action.searchUnique(org["name"])
        self.action.clickBtn("Details")
        # check that the UI controls are present
        self.orgCreateTemplate.checkForm(readonly=True)

        self.action.clickTab("Staff & Volunteers")
#        self.action.noBtnLink ("show-add-btn", "Add Staff")

        self.action.clickTab("Offices")
#        self.action.noBtnLink ("show-add-btn", "Add Office")

        self.action.clickTab("Assessments")
#        self.action.noBtnLink ("add-btn", "Add Assessment")

        self.action.clickTab("Projects")
#        self.action.noBtnLink ("show-add-btn", "Add Project")

        self.action.clickTab("Activities")
#        self.action.noBtnLink ("show-add-btn", "Add Activity")
        self.orgCreateTemplate.removeDataFromTemplate()

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
    OrganizationTest.selenium.stop()
