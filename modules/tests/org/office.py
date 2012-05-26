from tests.web2unittest import SeleniumUnitTest
from selenium.common.exceptions import NoSuchElementException


class Office(SeleniumUnitTest):

    def test_001_office(self):
        """ Tests to add a new office """
        data = [("name",
                 "Bucharest RFAAT Centre (Test)",
                ),
                ("code",
                 "12345678",
                ),
                ("organisation_id",
                 "Romanian Food Assistance Association (Test) (RFAAT)",
                 "autocomplete",
                ),
                ("type",
                 "Headquarters",
                 "option",
                ),
                ("comments",
                 "This is a Test Office",
                ),
                ("L0",
                 "Romania",
                 "gis_location"
                ),
                ("street",
                 "102 Diminescu St",
                 "gis_location"
                ),
                ("L3",
                 "Bucharest",
                 "gis_location"
                ),
               ]
        self.login(account="normal", nexturl="org/office/create")
        table = "org_office"
        result = self.create(table, data)
