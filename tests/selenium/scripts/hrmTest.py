"""
    This test class is designed to test the hrm functionality of Eden.
"""
from sahanaTest import SahanaTest
import unittest, re, time

class HRMTest(SahanaTest):
    """
        Test the Human Resource Management.

        This test suite assumes that the database has been prepopulated with
        test data, specifically:
        * Standard user data (admin@example.com)
        * 
    """
    _sortList = (
                 "createSearchDeletePerson",
                 "AddUserAsStaff",
                 "AddUserAsVolunteer",
                 "AddDifferentUsers",
                 "AddNewUserAsVolunteer",
                 "RegisterVolunteerAsUser",
                 "AddNewStaffWithDupEmail",
                 "CreateOffice",
                  "ModifyStaff",
                  "ModifyVolunteer",
                  "RegisterStaffAsUser",
                  "StaffAdvancedSearch",
                )


    def firstRun(self):
        # Setup the template for the pr/person/create From
        HRMTest.personCreateTemplate = self.action.getFormTemplate()
        HRMTest.personCreateTemplate.addInput(labelID="pr_person_pe_label__label",
                          inputID="pr_person_pe_label").setBalloonTitle("ID Tag Number")
        HRMTest.personCreateTemplate.addInput(labelID="pr_person_first_name__label",
                          inputID="pr_person_first_name").setBalloonTitle("First name")
        HRMTest.personCreateTemplate.addInput(labelID="pr_person_middle_name__label",
                          inputID="pr_person_middle_name")
        HRMTest.personCreateTemplate.addInput(labelID="pr_person_last_name__label",
                          inputID="pr_person_last_name")
        HRMTest.personCreateTemplate.addInput(labelID="pr_person_preferred_name__label",
                          inputID="pr_person_preferred_name").setBalloonTitle("Preferred")
        HRMTest.personCreateTemplate.addInput(labelID="pr_person_local_name__label",
                          inputID="pr_person_local_name").setBalloonTitle("Local")
        HRMTest.personCreateTemplate.addSelect(labelID="pr_person_gender__label",
                           selectID="pr_person_gender",
                           value="1")
        HRMTest.personCreateTemplate.addInput(labelID="pr_person_date_of_birth__label",
                           inputID="pr_person_date_of_birth")
        HRMTest.personCreateTemplate.addSelect(labelID="pr_person_age_group__label",
                           selectID="pr_person_age_group",
                           value="1")
        HRMTest.personCreateTemplate.addSelect(labelID="pr_person_nationality__label",
                          selectID="pr_person_nationality").setBalloonTitle("Nationality")
        HRMTest.personCreateTemplate.addInput(labelID="pr_person_occupation__label",
                          inputID="pr_person_occupation")
        HRMTest.personCreateTemplate.addInput(labelID="pr_person_picture__label",
                          inputID="pr_person_picture").setBalloonTitle("Picture")
        HRMTest.personCreateTemplate.addTextArea(labelID="pr_person_comments__label",
                          textID="pr_person_comments").setBalloonTitle("Comments")
        HRMTest.personCreateTemplate.addButton("Save")

        # Create the add Staff Member Form Template (hrm/human_resource/create?group=staff)
        HRMTest.staffCreateTemplate = self.action.getFormTemplate()
        HRMTest.staffCreateTemplate.addInput(labelID="hrm_human_resource_organisation_id__label",
                          inputID="dummy_hrm_human_resource_organisation_id")
        HRMTest.staffCreateTemplate.addInput(labelID="hrm_human_resource_organisation_id__label",
                          inputID="hrm_human_resource_organisation_id",
                          visible=False)
        HRMTest.staffCreateTemplate.addInput(labelID="hrm_human_resource_person_id__label",
                          inputID="hrm_human_resource_person_id",
                          visible=False)
        HRMTest.staffCreateTemplate.addInput(labelID="hrm_human_resource_person_id__label",
                          inputID="dummy_hrm_human_resource_person_id",
                          visible=False)
        HRMTest.staffCreateTemplate.addInput(labelID="pr_person_first_name__label",
                          inputID="pr_person_first_name")
        HRMTest.staffCreateTemplate.addInput(labelID="pr_person_middle_name__label",
                          inputID="pr_person_middle_name")
        HRMTest.staffCreateTemplate.addInput(labelID="pr_person_last_name__label",
                          inputID="pr_person_last_name")
        HRMTest.staffCreateTemplate.addInput(labelID="pr_person_date_of_birth__label",
                          inputID="pr_person_date_of_birth")
        HRMTest.staffCreateTemplate.addSelect(labelID="pr_person_gender__label",
                          selectID="pr_person_gender",
                          value="1")
        HRMTest.staffCreateTemplate.addInput(labelID="pr_person_occupation__label",
                          inputID="pr_person_occupation")
        HRMTest.staffCreateTemplate.addInput(labelID="pr_person_email__label",
                          inputID="pr_person_email")
        HRMTest.staffCreateTemplate.addInput(labelID="pr_person_mobile_phone__label",
                          inputID="pr_person_mobile_phone")
        HRMTest.staffCreateTemplate.addSelect(labelID="hrm_human_resource_type__label",
                          selectID="hrm_human_resource_type",
                          value="1")
        HRMTest.staffCreateTemplate.addInput(labelID="hrm_human_resource_job_title__label",
                          inputID="hrm_human_resource_job_title")
        HRMTest.staffCreateTemplate.addInput(labelID="hrm_human_resource_site_id__label",
                          inputID="dummy_hrm_human_resource_site_id")
        HRMTest.staffCreateTemplate.addInput(labelID="hrm_human_resource_site_id__label",
                          inputID="hrm_human_resource_site_id",
                          visible=False)
        HRMTest.staffCreateTemplate.addButton("Save")

        # Create the Staff Record Form Template (hrm/person/human_resource/create?group=staff)
        HRMTest.staffRecordTemplate = self.action.getFormTemplate()
        HRMTest.staffRecordTemplate.addInput(labelID="hrm_human_resource_organisation_id__label",
                          inputID="dummy_hrm_human_resource_organisation_id")
        HRMTest.staffRecordTemplate.addInput(labelID="hrm_human_resource_organisation_id__label",
                          inputID="hrm_human_resource_organisation_id",
                          visible=False)
        HRMTest.staffRecordTemplate.addSelect(labelID="hrm_human_resource_type__label",
                          selectID="hrm_human_resource_type",
                          value="1")
        HRMTest.staffRecordTemplate.addInput(labelID="hrm_human_resource_job_title__label",
                          inputID="hrm_human_resource_job_title")
        HRMTest.staffRecordTemplate.addSelect(labelID="hrm_human_resource_status__label",
                          selectID="hrm_human_resource_status",
                          value="1")
        HRMTest.staffRecordTemplate.addInput(labelID="hrm_human_resource_site_id__label",
                          inputID="dummy_hrm_human_resource_site_id")
        HRMTest.staffRecordTemplate.addInput(labelID="hrm_human_resource_site_id__label",
                          inputID="hrm_human_resource_site_id",
                          visible=False)
        HRMTest.staffRecordTemplate.addButton("Save")

        # Create the Add Volunteer template (hrm/human_resource/create?group=volunteer)
        HRMTest.volCreateTemplate = self.action.getFormTemplate()
        HRMTest.volCreateTemplate.addInput(labelID="hrm_human_resource_organisation_id__label",
                          inputID="dummy_hrm_human_resource_organisation_id")
        HRMTest.volCreateTemplate.addInput(labelID="hrm_human_resource_organisation_id__label",
                          inputID="hrm_human_resource_organisation_id",
                          visible=False)
        HRMTest.volCreateTemplate.addInput(labelID="hrm_human_resource_person_id__label",
                          inputID="hrm_human_resource_person_id",
                          visible=False)
        HRMTest.volCreateTemplate.addInput(labelID="hrm_human_resource_person_id__label",
                          inputID="dummy_hrm_human_resource_person_id",
                          visible=False)
        HRMTest.volCreateTemplate.addInput(labelID="pr_person_first_name__label",
                          inputID="pr_person_first_name")
        HRMTest.volCreateTemplate.addInput(labelID="pr_person_middle_name__label",
                          inputID="pr_person_middle_name")
        HRMTest.volCreateTemplate.addInput(labelID="pr_person_last_name__label",
                          inputID="pr_person_last_name")
        HRMTest.volCreateTemplate.addInput(labelID="pr_person_date_of_birth__label",
                          inputID="pr_person_date_of_birth")
        HRMTest.volCreateTemplate.addSelect(labelID="pr_person_gender__label",
                          selectID="pr_person_gender",
                          value="1")
        HRMTest.volCreateTemplate.addInput(labelID="pr_person_occupation__label",
                          inputID="pr_person_occupation")
        HRMTest.volCreateTemplate.addInput(labelID="pr_person_email__label",
                          inputID="pr_person_email")
        HRMTest.volCreateTemplate.addInput(labelID="pr_person_mobile_phone__label",
                          inputID="pr_person_mobile_phone")
        HRMTest.volCreateTemplate.addSelect(labelID="hrm_human_resource_type__label",
                          selectID="hrm_human_resource_type",
                          value="2")
        HRMTest.volCreateTemplate.addInput(labelID="hrm_human_resource_job_title__label",
                          inputID="hrm_human_resource_job_title")
        HRMTest.volCreateTemplate.addInput(inputID="hrm_human_resource_location_id", visible=False)
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_search_ac", visible=False)
        HRMTest.volCreateTemplate.addSelect(selectID="gis_location_L0")
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_L0_search", visible=False)
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_name")
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_name_search", visible=False)
        HRMTest.volCreateTemplate.addTextArea(textID="gis_location_street")
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_street_search", visible=False)
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_postcode")
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_postcode_search", visible=False)
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_L1", visible=False)
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_L1_ac")
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_L1_search", visible=False)
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_L2", visible=False)
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_L2_ac")
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_L2_search", visible=False)
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_L3", visible=False)
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_L3_ac")
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_L3_search", visible=False)
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_L4", visible=False)
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_L4_ac")
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_L4_search", visible=False)
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_lat")
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_lat_search", visible=False)
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_lon")
        HRMTest.volCreateTemplate.addInput(inputID="gis_location_lon_search", visible=False)
        HRMTest.volCreateTemplate.addButton("Save")
        
        HRMTest.volRecordTemplate = self.action.getFormTemplate()
        HRMTest.volRecordTemplate.addInput(labelID="hrm_human_resource_organisation_id__label",
                          inputID="dummy_hrm_human_resource_organisation_id")
        HRMTest.volRecordTemplate.addInput(labelID="hrm_human_resource_organisation_id__label",
                          inputID="hrm_human_resource_organisation_id",
                          visible=False)
        HRMTest.volRecordTemplate.addSelect(labelID="hrm_human_resource_type__label",
                          selectID="hrm_human_resource_type",
                          value="2")
        HRMTest.volRecordTemplate.addInput(labelID="hrm_human_resource_job_title__label",
                          inputID="hrm_human_resource_job_title")
        HRMTest.volRecordTemplate.addSelect(labelID="hrm_human_resource_status__label",
                          selectID="hrm_human_resource_status",
                          value="1")
        HRMTest.volRecordTemplate.addInput(inputID="hrm_human_resource_location_id", visible=False)
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_search_ac", visible=False)
        HRMTest.volRecordTemplate.addSelect(selectID="gis_location_L0")
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_L0_search", visible=False)
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_name")
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_name_search", visible=False)
        HRMTest.volRecordTemplate.addTextArea(textID="gis_location_street")
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_street_search", visible=False)
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_postcode")
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_postcode_search", visible=False)
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_L1", visible=False)
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_L1_ac")
#        HRMTest.volRecordTemplate.addInput(inputID="gis_location_L1_search", visible=False)
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_L2", visible=False)
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_L2_ac")
#        HRMTest.volRecordTemplate.addInput(inputID="gis_location_L2_search", visible=False)
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_L3", visible=False)
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_L3_ac")
#        HRMTest.volRecordTemplate.addInput(inputID="gis_location_L3_search", visible=False)
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_L4", visible=False)
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_L4_ac")
#        HRMTest.volRecordTemplate.addInput(inputID="gis_location_L4_search", visible=False)
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_lat")
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_lat_search", visible=False)
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_lon")
        HRMTest.volRecordTemplate.addInput(inputID="gis_location_lon_search", visible=False)
        HRMTest.volRecordTemplate.addButton("Save")

        # Register the organisation form
        HRMTest.OrgTemplate = self.action.getFormTemplate()
        HRMTest.OrgTemplate.addInput(labelID="org_organisation_name__label",
                                     inputID="org_organisation_name")
        HRMTest.OrgTemplate.addInput(labelID="org_organisation_acronym__label",
                                     inputID="org_organisation_acronym")
        HRMTest.OrgTemplate.addSelect(labelID="org_organisation_type__label",
                                     selectID="org_organisation_type")
        HRMTest.OrgTemplate.addSelect(labelID="org_organisation_sector_id__label",
                                     selectID="org_organisation_sector_id")
        HRMTest.OrgTemplate.addSelect(labelID="org_organisation_country__label",
                                     selectID="org_organisation_country")
        HRMTest.OrgTemplate.addInput(labelID="org_organisation_website__label",
                                     inputID="org_organisation_website")
        HRMTest.OrgTemplate.addInput(labelID="org_organisation_twitter__label",
                                     inputID="org_organisation_twitter")
        HRMTest.OrgTemplate.addInput(labelID="org_organisation_donation_phone__label",
                                     inputID="org_organisation_donation_phone")
        HRMTest.OrgTemplate.addTextArea(labelID="org_organisation_comments__label",
                                     textID="org_organisation_comments")
        HRMTest.OrgTemplate.addButton("Save")

        # Register the office form
        HRMTest.OfficeTemplate = self.action.getFormTemplate()
        HRMTest.OfficeTemplate.addInput(labelID="org_office_name__label",
                                     inputID="org_office_name")
        HRMTest.OfficeTemplate.addInput(labelID="org_office_code__label",
                                     inputID="org_office_code")
        HRMTest.OfficeTemplate.addSelect(labelID="org_office_type__label",
                                     selectID="org_office_type")
        HRMTest.OfficeTemplate.addSelect(labelID="org_office_office_id__label",
                                     selectID="org_office_office_id")
        HRMTest.OfficeTemplate.addInput(labelID="org_office_location_id__label",
                                     inputID="org_office_location_id",
                                     visible=False)
        HRMTest.OfficeTemplate.addInput(labelID="org_office_phone1__label",
                                     inputID="org_office_phone1")
        HRMTest.OfficeTemplate.addInput(labelID="org_office_phone2__label",
                                     inputID="org_office_phone2")
        HRMTest.OfficeTemplate.addInput(labelID="org_office_email__label",
                                     inputID="org_office_email")
        HRMTest.OfficeTemplate.addInput(labelID="org_office_fax__label",
                                     inputID="org_office_fax")
        HRMTest.OfficeTemplate.addInput(labelID="org_office_obsolete__label",
                                     inputID="org_office_obsolete",
                                     type="checkbox",
                                     value="off")
        HRMTest.OfficeTemplate.addTextArea(labelID="org_office_comments__label",
                                     textID="org_office_comments")
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_search_ac", visible=False)
        HRMTest.OfficeTemplate.addSelect(selectID="gis_location_L0")
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_L0_search", visible=False)
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_name")
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_name_search", visible=False)
        HRMTest.OfficeTemplate.addTextArea(textID="gis_location_street")
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_street_search", visible=False)
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_postcode")
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_postcode_search", visible=False)
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_L1", visible=False)
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_L1_ac")
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_L1_search", visible=False)
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_L2", visible=False)
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_L2_ac")
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_L2_search", visible=False)
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_L3", visible=False)
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_L3_ac")
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_L3_search", visible=False)
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_L4", visible=False)
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_L4_ac")
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_L4_search", visible=False)
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_lat")
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_lat_search", visible=False)
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_lon")
        HRMTest.OfficeTemplate.addInput(inputID="gis_location_lon_search", visible=False)
        HRMTest.OfficeTemplate.addButton("Save")

        # HRM advanced search form
        HRMTest.SearchTemplate = self.action.getFormTemplate()
        HRMTest.SearchTemplate.addInput(inputID="human_resource_name")
        HRMTest.SearchTemplate.addInput(inputID="human_resource_jobtitle")
        HRMTest.SearchTemplate.addButton("Search")

    def createSearchDeletePerson(self):
        """
            This will work with the pr/person form. It will check the following:
            # An authenticated user is required
            # form controls and validation
            # A new person can be created
            # The newly created person can be found
            # A non-existant person is not found
            # The newly created person can be deleted
        """
        template = self.personCreateTemplate
        # STEP 1: An authenticated user is required
        self.action.openPage("pr/person/create", heading="Login")
        result = self.action.errorMsg("Authentication Required")
        self.assertTrue(result)
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        # STEP 2: form controls and validation
        # check that the UI controls are present
        self.action.openPage("pr/person/create", heading="Add a Person")
        template.checkForm()
        ##################################################################
        # The highly experimental strict compliance:
        # Check that the elements and only the elements on the template
        # appear on the form.
        ##################################################################
        failures = template.checkFormStrict()
        if len(failures) == 0:
            print "Strict compliance met"
        else:
            print failures
        
        # Save a blank form and let's check the validation errors
        self.assertTrue(self.action.saveForm("Save", success=False))
        # validation on required field
        result = self.action.errorMsg("Please enter a first name")
        self.assertTrue(result)

        # A new person can be created
        person = "Person1"
        nonperson = "non-Person1"
        self.action.fillForm("pr_person_first_name", person)
        self.assertTrue(self.action.saveForm("Save", message="Person added", success=True))
        
        # STEP 3: The newly created person can be found
        self.action.openPage("pr/person", heading="List Persons")
        print "Looking for %s" % person
        self.assertTrue(self.action.searchUnique(person))
        # STEP 4: A non-existant person is not found
        print "Looking for non-existant %s" % nonperson
        self.assertTrue(self.action.searchMatchesFound(nonperson)==0)
        # STEP 5: The newly created person can be deleted
        result = self.action.deleteObject("pr/person", person, "Person")
        self.assertTrue(result)
        
        self.action.logout()

    def AddUserAsStaff(self):
        """
            This will add the normal user as a staff member of the organisation
            Example.com
        """
        template = self.staffCreateTemplate
        # STEP 1: Log in as admin
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        # STEP 2: Open the add staff page
        self.action.openPage("hrm/index", heading="Staff and Volunteers")
        self.assertTrue(self.action.openLink("link=Add staff members"))
        self.action.checkPageHeading("Add Staff Member")
        template.checkForm()
        ##################################################################
        # The highly experimental strict compliance:
        # Check that the elements and only the elements on the template
        # appear on the form.
        ##################################################################
        failures = template.checkFormStrict()
        if len(failures) == 0:
            print "Strict compliance met"
        else:
            print failures
        # STEP 3: Select the data
        # Select the organisation
        # Select the user
        org = "Example.com"
        person = "Normal User"
        self.action.fillAutoComplete("dummy_hrm_human_resource_organisation_id",
                                     org,
                                     "dummy_hrm_human_resource_organisation_id_throbber")
        self.assertTrue(self.action.quickLink("link=Select from registry"))
        self.action.fillAutoComplete("dummy_hrm_human_resource_person_id", person, "person_load_throbber")
        # STEP 4: Verify that the data has been correctly displayed
        template.getElementFromKey("dummy_hrm_human_resource_organisation_id").setValue("Example.com (eCom)")
        template.getElementFromKey("pr_person_first_name").setValue("Normal")
        template.getElementFromKey("pr_person_last_name").setValue("User")
        template.getElementFromKey("pr_person_email").setValue("normaluser@example.com")
        # press the edit link so that Selenium can read the values (otherwise they are disabled)
        self.assertTrue(self.action.quickLink("link=Edit Details"))
        template.checkForm()
        # STEP 5: save the form
        self.assertTrue(self.action.saveForm("Save", message="Staff member added", success=True))

        self.action.logout()


    def AddUserAsVolunteer(self):
        """
            This will add the admin user as a volunteer of the organisation
            Example.net
        """
        template = self.volCreateTemplate
        # STEP 1: Log in as admin
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        # STEP 2: Open the add volunteer page
        self.action.openPage("hrm/index", heading="Staff and Volunteers")
        self.assertTrue(self.action.openLink("link=Add volunteers"))
        self.action.checkPageHeading("Add Volunteer")
        template.checkForm()
        ##################################################################
        # The highly experimental strict compliance:
        # Check that the elements and only the elements on the template
        # appear on the form.
        ##################################################################
        failures = template.checkFormStrict()
        if len(failures) == 0:
            print "Strict compliance met"
        else:
            print failures
        # STEP 3: Select the data
        # Select the organisation
        # Select the user
        org = "Example.net"
        person = "Admin User"
        self.action.fillAutoComplete("dummy_hrm_human_resource_organisation_id",
                                     org,
                                     "dummy_hrm_human_resource_organisation_id_throbber")
        self.assertTrue(self.action.quickLink("link=Select from registry"))
        self.action.fillAutoComplete("dummy_hrm_human_resource_person_id",
                                     person,
                                     "person_load_throbber")
        self.assertTrue(self.action.quickLink("link=Edit Details"))
        # Add some more data to Admin
        self.action.fillForm("pr_person_middle_name", "Root")
        self.action.fillForm("pr_person_gender", "2")
        self.action.fillForm("pr_person_occupation", "Hacker")
        # STEP 4: Verify that the data has been correctly displayed
        template.getElementFromKey("dummy_hrm_human_resource_organisation_id").setValue("Example.net (eNet)")
        template.getElementFromKey("pr_person_first_name").setValue("Admin")
        template.getElementFromKey("pr_person_middle_name").setValue("Root")
        template.getElementFromKey("pr_person_last_name").setValue("User")
        template.getElementFromKey("pr_person_email").setValue("admin@example.com")
        template.getElementFromKey("pr_person_gender").setValue("2")
        template.getElementFromKey("pr_person_occupation").setValue("Hacker")
        template.checkForm()
        # STEP 5: save the form
        # clear middle name so that it doesn't affect other tests
        self.action.fillForm("pr_person_middle_name", "")
        template.getElementFromKey("pr_person_middle_name").setValue(None)
        self.assertTrue(self.action.saveForm("Save", message="Volunteer added", success=True))

        self.action.logout()

    def AddDifferentUsers(self):
        """
            This will add the admin user, check the details are correct
            Then it will clear and check the details are all removed
            Then it will add the admin user, check the details are correct
            Then it will select normal user and check the details are correct 
            Then it will add the admin user, add more details & check everything is displayed
            Then it will select normal user and check the details are correct 
        """
        template = self.volCreateTemplate
        # STEP 1: Log in as admin
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        # STEP 2: Open the add volunteer page
        self.action.openPage("hrm/index", heading="Staff and Volunteers")
        self.assertTrue(self.action.openLink("link=Add volunteers"))
        self.action.checkPageHeading("Add Volunteer")

        # STEP 3: Add Admin and check details
        person = "Admin User"
        self.assertTrue(self.action.quickLink("link=Select from registry"))
        self.action.fillAutoComplete("dummy_hrm_human_resource_person_id",
                                     person,
                                     "person_load_throbber")
        self.assertTrue(self.action.quickLink("link=Edit Details"))
        template.getElementFromKey("pr_person_first_name").setValue("Admin")
        template.getElementFromKey("pr_person_last_name").setValue("User")
        template.getElementFromKey("pr_person_email").setValue("admin@example.com")
        template.getElementFromKey("pr_person_gender").setValue("2")
        template.getElementFromKey("pr_person_occupation").setValue("Hacker")
        template.checkForm()
        # STEP 4: Remove admin and check details
        self.assertTrue(self.action.quickLink("link=Remove selection"))
        template.getElementFromKey("pr_person_first_name").setValue(None)
        template.getElementFromKey("pr_person_last_name").setValue(None)
        template.getElementFromKey("pr_person_email").setValue(None)
        template.getElementFromKey("pr_person_gender").setValue("1")
        template.getElementFromKey("pr_person_occupation").setValue(None)
        template.checkForm()
        # STEP 5: Add Admin and check details
        person = "Admin User"
        self.assertTrue(self.action.quickLink("link=Select from registry"))
        self.action.fillAutoComplete("dummy_hrm_human_resource_person_id",
                                     person,
                                     "person_load_throbber")
        self.assertTrue(self.action.quickLink("link=Edit Details"))
        template.getElementFromKey("pr_person_first_name").setValue("Admin")
        template.getElementFromKey("pr_person_last_name").setValue("User")
        template.getElementFromKey("pr_person_email").setValue("admin@example.com")
        template.getElementFromKey("pr_person_gender").setValue("2")
        template.getElementFromKey("pr_person_occupation").setValue("Hacker")
        template.checkForm()

        # STEP 6: Add Normal User and check details
        person = "Normal User"
        self.assertTrue(self.action.quickLink("link=Select from registry"))
        self.action.fillAutoComplete("dummy_hrm_human_resource_person_id",
                                     person,
                                     "person_load_throbber")
        self.assertTrue(self.action.quickLink("link=Edit Details"))
        template.getElementFromKey("pr_person_first_name").setValue("Normal")
        template.getElementFromKey("pr_person_last_name").setValue("User")
        template.getElementFromKey("pr_person_email").setValue("normaluser@example.com")
        template.getElementFromKey("pr_person_gender").setValue("1")
        template.getElementFromKey("pr_person_occupation").setValue(None)
        template.checkForm()
        # STEP 7: Add Admin and check details
        person = "Admin User"
        self.assertTrue(self.action.quickLink("link=Select from registry"))
        self.action.fillAutoComplete("dummy_hrm_human_resource_person_id",
                                     person,
                                     "person_load_throbber")
        self.assertTrue(self.action.quickLink("link=Edit Details"))
        self.action.fillForm("pr_person_middle_name", "Root")
        self.action.fillForm("pr_person_mobile_phone", "0123456789")
        self.action.fillForm("pr_person_date_of_birth", "1970-07-19")
        self.action.fillForm("hrm_human_resource_job_title", "System Administrator")
        template.getElementFromKey("pr_person_first_name").setValue("Admin")
        template.getElementFromKey("pr_person_middle_name").setValue("Root")
        template.getElementFromKey("pr_person_last_name").setValue("User")
        template.getElementFromKey("pr_person_email").setValue("admin@example.com")
        template.getElementFromKey("pr_person_mobile_phone").setValue("0123456789")
        template.getElementFromKey("pr_person_date_of_birth").setValue("1970-07-19")
        template.getElementFromKey("pr_person_gender").setValue("2")
        template.getElementFromKey("pr_person_occupation").setValue("Hacker")
        template.getElementFromKey("hrm_human_resource_job_title").setValue("System Administrator")
        template.checkForm()

        # STEP 8: Add Normal User and check details
        person = "Normal User"
        self.assertTrue(self.action.quickLink("link=Select from registry"))
        self.action.fillAutoComplete("dummy_hrm_human_resource_person_id",
                                     person,
                                     "person_load_throbber")
        self.assertTrue(self.action.quickLink("link=Edit Details"))
        template.getElementFromKey("pr_person_first_name").setValue("Normal")
        template.getElementFromKey("pr_person_middle_name").setValue(None)
        template.getElementFromKey("pr_person_last_name").setValue("User")
        template.getElementFromKey("pr_person_email").setValue("normaluser@example.com")
        template.getElementFromKey("pr_person_mobile_phone").setValue(None)
        template.getElementFromKey("pr_person_date_of_birth").setValue(None)
        template.getElementFromKey("pr_person_gender").setValue("1")
        template.getElementFromKey("pr_person_occupation").setValue(None)
        template.getElementFromKey("hrm_human_resource_job_title").setValue("System Administrator")
        template.checkForm()

        self.action.logout()


    def AddNewUserAsVolunteer(self):
        """
            This will add a newly created user as a volunteer of the organisation
            Example.net 
        """
        template = self.volCreateTemplate
        # STEP 1: Log in as admin
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        # STEP 2: Open the add volunteer page
        self.action.openPage("hrm/index", heading="Staff and Volunteers")
        self.assertTrue(self.action.openLink("link=Add volunteers"))
        self.action.checkPageHeading("Add Volunteer")
        self.action.fillAutoComplete("dummy_hrm_human_resource_organisation_id",
                                     "Example.com",
                                     "dummy_hrm_human_resource_organisation_id_throbber")
        self.action.fillForm("pr_person_first_name", "First")
        self.action.fillForm("pr_person_middle_name", "Middle")
        self.action.fillForm("pr_person_last_name", "Last")
        self.action.fillForm("pr_person_email", "first.m.last@example.com")
        self.action.fillForm("pr_person_mobile_phone", "0123456789")
        self.action.fillForm("pr_person_date_of_birth", "1981-12-14")
        self.action.fillForm("pr_person_gender", "3")
        self.action.fillForm("hrm_human_resource_job_title", "Driver")

        template.getElementFromKey("pr_person_first_name").setValue("First")
        template.getElementFromKey("pr_person_middle_name").setValue("Middle")
        template.getElementFromKey("pr_person_last_name").setValue("Last")
        template.getElementFromKey("pr_person_email").setValue("first.m.last@example.com")
        template.getElementFromKey("pr_person_mobile_phone").setValue("0123456789")
        template.getElementFromKey("pr_person_date_of_birth").setValue("1981-12-14")
        template.getElementFromKey("pr_person_gender").setValue("3")
        template.getElementFromKey("pr_person_occupation").setValue(None)
        template.getElementFromKey("hrm_human_resource_job_title").setValue("Driver")
        template.checkForm()

        self.assertTrue(self.action.saveForm("Save",
                                             message="Volunteer added",
                                             success=True,
                                            )
                       )

        self.action.logout()

    def RegisterVolunteerAsUser(self):
        """
            This will register the volunteer created above as a user
        """
        # STEP 1: Make sure we are logged out
        self.action.logout()
        # STEP 2: Open the home page and click the register user button
        self.action.openPage("default/index", heading="Sahana Eden Humanitarian Management Platform")
        self.assertTrue(self.action.quickLink("link=Sign-up for Account"))
        self.action.fillForm("auth_user_first_name", "First")
        self.action.fillForm("auth_user_last_name", "Last")
        # The HTML id for the email and password elements are duplicated in a clear violation of HTML rules!
        # so need to locate them directly  
        self.action.fillForm("document.forms[1].elements[4]", "first.m.last@example.com")
        self.action.fillForm("document.forms[1].elements[5]", "testing")
        self.action.fillForm("auth_user_password_two", "testing")
        self.assertTrue(self.action.saveForm("Register"))
        self.action.checkPageHeading("Account Registered - Please Check Your Email",
                                     level="h1"
                                    )
        self.action.logout()

    def AddNewStaffWithDupEmail(self):
        """
            Add a new member of staff but with the same email address as an
            existing member. Verify that the appropriate error message appears
        """
        template = self.staffCreateTemplate
        # STEP 1: Log in as admin
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        # STEP 2: Open the add staff page
        self.action.openPage("hrm/index", heading="Staff and Volunteers")
        self.assertTrue(self.action.openLink("link=Add staff members"))
        self.action.checkPageHeading("Add Staff Member")
        # STEP 3: Select the data
        # Select the organisation
        # Add a new user
        org = "Example.com"
        self.action.fillAutoComplete("dummy_hrm_human_resource_organisation_id",
                                     org,
                                     "dummy_hrm_human_resource_organisation_id_throbber")
        self.action.fillForm("pr_person_first_name", "Other")
        self.action.fillForm("pr_person_last_name", "User")
        self.action.fillForm("pr_person_email", "normaluser@example.com")
        self.action.fillForm("pr_person_date_of_birth","1970-07-19")
        self.action.fillForm("pr_person_gender", "3")
        # STEP 4: Verify that the data has been correctly displayed
        template.getElementFromKey("dummy_hrm_human_resource_organisation_id").setValue("Example.com (eCom)")
        template.getElementFromKey("pr_person_first_name").setValue("Other")
        template.getElementFromKey("pr_person_last_name").setValue("User")
        template.getElementFromKey("pr_person_email").setValue("normaluser@example.com")
        template.getElementFromKey("pr_person_date_of_birth").setValue("1970-07-19")
        template.getElementFromKey("pr_person_gender").setValue("3")
        template.checkForm()
        # STEP 5: save the form
        self.assertTrue(self.action.saveForm("Save",
                                             success=False
                                            )
                       )
        # validation on duplicate email field
        result = self.action.errorMsg("This email-address is already registered.")
        self.assertTrue(result)
        # STEP 5: change the email adress to a unique email and then save the form
        self.action.fillForm("pr_person_email", "otheruser@example.com")
        self.assertTrue(self.action.saveForm("Save",
                                             message="Staff member added",
                                             success=True
                                            )
                       )

        self.action.logout()

    def CreateOffice(self):
        """
            Create an office for the Example.com organisation
        """
        # STEP 1: Log on Open the Example.com organisation and move to office
        templateOrg = self.OrgTemplate
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        self.action.openPage("default/index",
                             heading="Sahana Eden Humanitarian Management Platform"
                            )
        self.assertTrue(self.action.openLink("link=Example.com (eCom)"))
        self.action.checkPageHeading("Edit Organization")

        templateOrg.getElementFromKey("org_organisation_name").setValue("Example.com")
        templateOrg.getElementFromKey("org_organisation_acronym").setValue("eCom")
        templateOrg.getElementFromKey("org_organisation_type").setValue("10") # Private
        templateOrg.getElementFromKey("org_organisation_sector_id").setValue("8") # logistics
        templateOrg.getElementFromKey("org_organisation_country").setValue("GB")
        templateOrg.getElementFromKey("org_organisation_website").setValue("http://www.example.com")
        templateOrg.getElementFromKey("org_organisation_twitter").setValue("extweet")
        templateOrg.getElementFromKey("org_organisation_donation_phone").setValue("44 21 78453434")
        templateOrg.getElementFromKey("org_organisation_comments").setValue("ships planes cars we do them all")
        templateOrg.checkForm()
        ##################################################################
        # The highly experimental strict compliance:
        # Check that the elements and only the elements on the template
        # appear on the form.
        ##################################################################
        failures = templateOrg.checkFormStrict()
        if len(failures) == 0:
            print "Strict compliance met"
        else:
            print failures

        templateOff = self.OfficeTemplate
        self.assertTrue(self.action.checkTab("Offices"))
        self.action.clickTab("Offices")
        self.action.checkPageHeading("Organization Details")
        self.action.quickLink("link=Add Office")
        templateOff.checkForm()
        ##################################################################
        # The highly experimental strict compliance:
        # Check that the elements and only the elements on the template
        # appear on the form.
        ##################################################################
        failures = templateOff.checkFormStrict()
        if len(failures) == 0:
            print "Strict compliance met"
        else:
            print failures
        # STEP 2: Add details for an office
        self.action.fillForm("org_office_name", "Example Head Office")
        self.action.fillForm("org_office_type", "1")
        self.action.fillForm("gis_location_L0", "United Kingdom","select")
        self.action.fillForm("gis_location_name", "Example.com Main Office")
        self.action.fillForm("gis_location_street", "Example house\nExample Street")
        self.action.fillForm("gis_location_postcode", "OX43 45D")
        self.action.fillForm("gis_location_L1_ac", "Oxon")
        self.action.fillForm("gis_location_L3_ac", "Waterperry")
        self.action.fillForm("gis_location_lat", "51.754848420123")
        self.action.fillForm("gis_location_lon", "-1.0940863470739")
        
        # STEP 3: save the form
        self.assertTrue(self.action.saveForm("Save",
                                             message="Office added",
                                             success=True
                                            )
                       )
        self.action.logout()

    def ModifyStaff(self):
        """
            Add staff to the office
            Give the staff job title
        """
        # Step 1 move to staff
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        
        self.action.openPage("hrm/index", heading="Staff and Volunteers")
        result = self.action.findLink('See all [0-9]+ staff members')
        self.assertTrue(result)
        # Step 2 open the Normal User
        self.action.searchUnique("Normal")
        self.action.openLink("link=Open")
        # Step 3 assign a job and office
        self.action.clickTab("Staff Record")
        template = self.staffRecordTemplate
        template.checkForm()
        ##################################################################
        # The highly experimental strict compliance:
        # Check that the elements and only the elements on the template
        # appear on the form.
        ##################################################################
        failures = template.checkFormStrict()
        if len(failures) == 0:
            print "Strict compliance met"
        else:
            print failures
        
        self.action.fillForm("hrm_human_resource_job_title", "Chief of Staff")
        self.action.fillAutoComplete("dummy_hrm_human_resource_site_id",
                                     "Example Head Office",
                                     "dummy_hrm_human_resource_site_id_throbber")
        self.assertTrue(self.action.saveForm("Save",
                                             message="Record updated",
                                             success=True
                                            )
                        )
        # Step 4 verify changes
        template.getElementFromKey("dummy_hrm_human_resource_organisation_id").setValue("Example.com")
        template.getElementFromKey("hrm_human_resource_job_title").setValue("Chief of Staff")
        template.getElementFromKey("dummy_hrm_human_resource_site_id").setValue("Example Head Office")
        template.checkForm()
        self.action.logout()

    def ModifyVolunteer(self):
        """
            Give the volunteer first middle last volunteer a location
        """
        # Step 1 move to staff
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        
        self.action.openPage("hrm/index", heading="Staff and Volunteers")
        result = self.action.findLink('See all [0-9]+ volunteers')
        self.assertTrue(result)
        # Step 2 open volunteer named First Middle Last  
        self.action.searchUnique("First")
        self.action.openLink("link=Open")
        # Step 3 assign a location
        self.action.clickTab("Volunteer Record")
        template = self.volRecordTemplate
        template.getElementFromKey("hrm_human_resource_job_title").setValue("Driver")
        template.checkForm()
        ##################################################################
        # The highly experimental strict compliance:
        # Check that the elements and only the elements on the template
        # appear on the form.
        ##################################################################
        failures = template.checkFormStrict()
        if len(failures) == 0:
            print "Strict compliance met"
        else:
            print failures
        self.action.fillForm("gis_location_L0", "Germany","select")
        self.action.fillForm("gis_location_street", "25 Other Street")
        self.action.fillForm("gis_location_postcode", "54321")
        self.action.fillForm("gis_location_L1_ac", "Mecklenburg-Vorpommern")
        self.action.fillForm("gis_location_L2_ac", "Landkreis Rostock")
        self.action.fillForm("gis_location_L3_ac", "Rostock")
        self.action.fillForm("gis_location_lat", "54.1")
        self.action.fillForm("gis_location_lon", "12.1")
        self.assertTrue(self.action.saveForm("Save",
                                             message="Record updated",
                                             success=True
                                            )
                        )
        # Step 4 verify changes
        template.getElementFromKey("gis_location_L0").setValue("Germany")
        template.getElementFromKey("gis_location_street").setValue("25 Other Street")
        template.getElementFromKey("gis_location_postcode").setValue("54321")
        template.getElementFromKey("gis_location_L1_ac").setValue("Mecklenburg-Vorpommern")
        template.getElementFromKey("gis_location_L2_ac").setValue("Landkreis Rostock")
        template.getElementFromKey("gis_location_L3_ac").setValue("Rostock")
        template.getElementFromKey("gis_location_lat").setValue("54.1")
        template.getElementFromKey("gis_location_lon").setValue("12.1")
        template.checkForm()

        self.action.logout()

    def RegisterStaffAsUser(self):
        """
            Register a staff member as a user
        """
        # Step 1 Assign a facility and job title to otheruser@example.com
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )

        self.action.openPage("hrm/index", heading="Staff and Volunteers")
        result = self.action.findLink('See all [0-9]+ staff members')
        self.assertTrue(result)

        self.action.searchUnique("Other")
        self.action.openLink("link=Open")

        self.action.clickTab("Staff Record")
        template = self.staffRecordTemplate
        self.action.fillForm("hrm_human_resource_job_title", "Senior Accountant")
        self.action.fillAutoComplete("dummy_hrm_human_resource_site_id",
                                     "Example Head Office",
                                     "dummy_hrm_human_resource_site_id_throbber")
        self.assertTrue(self.action.saveForm("Save",
                                             message="Record updated",
                                             success=True
                                            )
                        )

        template.getElementFromKey("dummy_hrm_human_resource_organisation_id").setValue("Example.com")
        template.getElementFromKey("hrm_human_resource_job_title").setValue("Senior Accountant")
        template.getElementFromKey("dummy_hrm_human_resource_site_id").setValue("Example Head Office")
        template.checkForm()
        # Step 2 Register the user with email otheruser@example.com
        self.action.logout()
        self.action.openPage("default/index", heading="Sahana Eden Humanitarian Management Platform")
        self.assertTrue(self.action.quickLink("link=Sign-up for Account"))
        self.action.fillForm("auth_user_first_name", "Other")
        self.action.fillForm("auth_user_last_name", "User")
        # The email and password HTML ids are duplicated so need to locate them directly  
        self.action.fillForm("document.forms[1].elements[4]", "otheruser@example.com")
        self.action.fillForm("document.forms[1].elements[5]", "testing")
        self.action.fillForm("auth_user_password_two", "testing")
        self.assertTrue(self.action.saveForm("Register"))
        self.action.checkPageHeading("Account Registered - Please Check Your Email",
                                     level="h1"
                                    )
        # Step 3 get admin to verify the registration
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        self.action.openPage("admin/user", heading="List Users")
        self.assertTrue(self.action.searchUnique("otheruser@example.com"))
        self.action.openLink("link=Open")
        self.assertTrue(self.action.saveForm("Save",
                                             message="User updated",
                                             success=True
                                            )
                        )
        self.action.logout()
        self.action.login("otheruser@example.com", "testing" )
        
        # Step 4 Open the staff member otheruser@example.com and verify details 
        self.action.openPage("hrm/index", heading="Personal Profile")
        self.action.openLink("link=Positions")
        self.assertTrue(self.action.searchUnique("Example.com"))
        self.action.openLink("link=Contact Information")
        self.assertTrue(self.action.searchUnique("otheruser@example.com"))
        self.action.logout()

    def StaffAdvancedSearch(self):
        """
            Use the search fields to search for specific users and roles
        """
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )

        self.action.openPage("hrm/index", heading="Staff and Volunteers")
        template = self.SearchTemplate
        self.action.fillForm("human_resource_jobtitle", "Chief of Staff")
        self.assertTrue(self.action.saveForm("Search"))
        self.assertTrue(self.action.searchUnique("normaluser@example.com"))

        self.action.fillForm("human_resource_jobtitle", "Chief of Something")
        self.assertTrue(self.action.saveForm("Search"))
        self.assertTrue(self.action.searchMatchesFound()==0)

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
    HRMTest.selenium.stop()
