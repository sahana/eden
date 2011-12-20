from sahanaTest import SahanaTest
import actions

class CreateTestAccount(SahanaTest):
    """ Set up common accounts to be used by the suite of test classes """
    _sortList = ("createAll",)

    def createAll(self):
        """ Create the standard testing accounts admin@example.com and user@example.com """
        if self._user == "" or self._password == "":
            # The 1st user is created through the User Registration process
            # - assumes that this is a fresh install & hence this 1st user will get Admin rights
            self.action.registerUser("Admin", "User", "admin@example.com", "testing")
        else:
            # We already have a username/password
            self.action.login(self._user, self._password, False)
            self.action.addUser("Admin", "User", "admin@example.com", "testing")
            self.action.addRole("admin@example.com", "1")
        # Create an unpriviliged user to use for normal (non-admin) Tests
        self.action.addUser("Normal", "User", "user@example.com", "testing")

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
