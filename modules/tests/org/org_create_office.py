# Set up Offices
from tests.web2unittest import SeleniumUnitTest
from tests import *

class org_create_office(SeleniumUnitTest):
    def test_create_office(self):

        browser = self.browser
        org_table = self.current.s3db.org_organisation
        name = "Bucharest RFAAT Centre (Test)"
        query = ((org_table.name == name) & (org_table.deleted == "F"))
        org_id = self.current.db(query).select(org_table.id,limitby=(0, 1)).first()
        if org_id:
            print "test_create_office - Not run as Office name already exists in the db"
            return False
        driver = self.browser
        driver.find_element_by_xpath("//div[@id='facility_box']/a[4]/div").click()
        driver.find_element_by_id("show-add-btn").click()
        driver.find_element_by_id("org_office_name").clear()
        driver.find_element_by_id("org_office_name").send_keys("Bucharest RFAAT Centre (Test)")
        driver.find_element_by_id("org_office_code").clear()
        driver.find_element_by_id("org_office_code").send_keys("12345678")
        w_autocomplete("Rom","org_office_organisation_id","Romanian Food Assistance Association (Test) (RFAAT)",False)
        driver.find_element_by_id("org_office_type").click()
        driver.find_element_by_id("org_office_type").send_keys("Headquarters")
        driver.find_element_by_id("gis_location_L0").send_keys("Romania")
        driver.find_element_by_id("gis_location_street").clear()
        driver.find_element_by_id("gis_location_street").send_keys("102 Diminescu St")
        driver.find_element_by_id("gis_location_L3_ac").clear()
        driver.find_element_by_id("gis_location_L3_ac").send_keys("Bucharest")
        driver.find_element_by_id("org_office_comments").click()
        driver.find_element_by_id("org_office_comments").clear()
        driver.find_element_by_id("org_office_comments").send_keys("This is a Test Office")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
