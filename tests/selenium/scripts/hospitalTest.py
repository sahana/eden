from sahanaTest import SahanaTest
import unittest, re

class HospitalTest(SahanaTest):
    """ Test the Hospital Management System """

    _sortList = ("checkAuthentication",
                 "checkAddHospitalForm",
                 "createHospital",
                 #"removeHospitals"
                )


    def firstRun(self):
        sel = HospitalTest.selenium
        HospitalTest.hospitals = []
        HospitalTest.addHospitaltemplate = self.action.getFormTemplate()
        HospitalTest.addHospitaltemplate.addInput(labelID="hms_hospital_paho_uuid__label",
                                                  inputID="hms_hospital_paho_uuid")
        HospitalTest.addHospitaltemplate.addInput(labelID="hms_hospital_gov_uuid__label",
                                                  inputID="hms_hospital_gov_uuid")
        HospitalTest.addHospitaltemplate.addInput(labelID="hms_hospital_other_ids__label",
                                                  inputID="hms_hospital_other_ids")
        HospitalTest.addHospitaltemplate.addInput(labelID="hms_hospital_name__label",
                                                  inputID="hms_hospital_name")
        HospitalTest.addHospitaltemplate.addInput(labelID="hms_hospital_aka1__label",
                                                  inputID="hms_hospital_aka1")
        HospitalTest.addHospitaltemplate.addInput(labelID="hms_hospital_aka2__label",
                                                  inputID="hms_hospital_aka2")
        HospitalTest.addHospitaltemplate.addSelect(labelID="hms_hospital_facility_type__label",
                                                   selectID="hms_hospital_facility_type",
                                                   value="1")
        HospitalTest.addHospitaltemplate.addInput(labelID="hms_hospital_organisation_id__label",
                                                  inputID="dummy_hms_hospital_organisation_id")
        HospitalTest.addHospitaltemplate.addInput(labelID="hms_hospital_organisation_id__label",
                                                  inputID="hms_hospital_organisation_id",
                                                  visible=False)


    def create_hospital(self, gov_uuid, name, type):
        sel = HospitalTest.selenium

        gov_uuid = gov_uuid.strip()
        name = name.strip()

        sel.open("hms/hospital/create")
        self.assertEqual("Add Hospital", sel.get_text("//h2"))

        self.action.fillForm("hms_hospital_gov_uuid", gov_uuid)
        self.action.fillForm("hms_hospital_name", name)
        self.action.fillForm("hms_hospital_facility_type", type, "select")
        """ Now save the form """
        self.assertTrue(self.action.saveForm("Save", "Hospital information added"))
        print "Hospital %s created" % (name)

    def checkAuthentication(self):
        sel = self.selenium
        self.action.logout()
        sel.open("hms/hospital/create")
        self.assertEqual("Login", self.selenium.get_text("//h2"))

    def checkAddHospitalForm(self):
        # Log in as admin an then move to the add hospital page
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password)
        sel = self.selenium
        self.action.openPage("hms/hospital/create")
        # check that the UI controls are present
        self.addHospitaltemplate.checkForm()

    def createHospital(self):
        # Log in as admin an then move to the add hospital page
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password)
        # Add the test hospitals
        source = open("../data/hospital.txt", "r")
        values = source.readlines()
        source.close()
        for hospital in values:
            details = hospital.split(",")
            if len(details) == 3:
                self.create_hospital(details[0].strip(), # gov_uuid
                                     details[1].strip(), # name
                                     details[2].strip()  # facility_type
                                     )
                HospitalTest.hospitals.append(details[0].strip())

    # Fails to logout cleanly when not in lastRun
    #def removeHospitals(self):
    def lastRun(self):
        """ Delete the test hospitals """

        if len(self.hospitals) == 0:
            return

        sel = self.selenium
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password)
        self.action.openPage("hms/hospital")

        allPassed = True
        for hospital in self.hospitals:
            self.action.searchUnique(hospital)
            sel.click("link=Delete")
            self.action.confirmDelete()
            if self.action.successMsg("Hospital deleted"):
                print "Hospital %s deleted" % hospital
            else:
                print "Failed to deleted hospital %s" % hospital
                allPassed = False
        self.assertTrue(allPassed)

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
    HospitalTest.selenium.stop()
