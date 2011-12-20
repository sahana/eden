from sahanaTest import SahanaTest
import actions

class DeleteTestAccount(SahanaTest):
    """ Delete the common accounts that were created for the suite of test classes """
    _sortList = ("deleteAll",)

    def deleteAll(self):
        if self._user == "" or self._password == "":
            """ Delete the standard testing account: normaluser@example.com """
            self.action.login("adminuser@example.com", "testing", False)
            self.action.delUser("normaluser@example.com")
        else:
            """ Delete the standard testing accounts: admin@example.com & normaluser@example.com """
            self.action.login(self._user, self._password, False)
            self.action.delUser('adminuser@example.com')
            self.action.delUser("normaluser@example.com")

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
