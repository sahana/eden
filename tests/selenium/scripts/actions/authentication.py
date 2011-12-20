import unittest
from selenium import selenium

class Authenticate(unittest.TestCase):
    def __init__ (self, selenium):
        self.sel = selenium

    def login(self, action, username, password, reveal=True):
        """
            login to the system using the name provided
            username: the username to be used
            password: the password of the user
            reveal:   show the password on any error message
        """
        print "Logging in as user: %s" % username
        sel = self.sel
        if sel.is_element_present("link=Logout"):
            # Already logged in check the account
            if sel.is_element_present("link=%s" % username):
                # already logged in
                return
            else:
                # logged in but as a different user
                action.logout()
        sel.open("default/user/login")
        sel.click("auth_user_email")
        sel.type("auth_user_email", username)
        sel.type("auth_user_password", password)
        sel.click("//input[@value='Login']")
        msg = "Unable to log in as %s" % username
        if reveal:
            msg += " with password %s " % password
        self.assertTrue(action.successMsg("Logged in"), msg)

    def logout(self, action):
        " logout of the system "
        sel = self.sel
        if sel.is_element_present("link=Logout"):
            sel.click("link=Logout")
            sel.wait_for_page_to_load("30000")
            action.successMsg("Logged out")
