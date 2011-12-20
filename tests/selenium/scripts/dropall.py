from sahanaTest import SahanaTest
import actions

class DropAll(SahanaTest):
    """ 
        Drop all of the tables from the database 
        and then per-populate with regression test data
    """
    _sortList = ("dropTable",
                 "populate",
                )

    def dropTable(self):
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        self.selenium.set_timeout("120000")
        self.action.openPage("appadmin/dropall")

    def populate(self):
        self.selenium.set_timeout("120000")
        self.action.openPage("default/index")
        self.selenium.set_timeout("30000")
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )


if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
