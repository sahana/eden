"""
    This test class is designed as a tutorial to help you to learn how to 
    construct a test case for Eden. Typically a test class is designed for a
    model and thus should help with testing the work flow.

    To get a new test class to appear in the UI it is necessary to edit the
    data/testModules.txt file 
    All test classes should be extended from the class SahanaTest which in turn
    is inherited from unittest.TestCase 
    So the following import is always required
"""
from sahanaTest import SahanaTest

class TutorialTest(SahanaTest):
    """ 
        The _sortList variable is used to keep a list of all test methods
        that will be run by the test class.
        The test methods  will be run in the order given in this list.

        If this variable is not provided then only methods that have the prefix test_
        will be run and the order is not guaranteed 
    """
    _sortList = (
                 "simpleAuthentication",
                 "simpleSearch",
                 "checkMessages",
                 "simpleFormTest",
                 "saveFormTest",
                )
    
    # This method demonstrates how to log into the Eden system using the 
    # action methods provided. 
    def simpleAuthentication(self):
        """
            Two basic accounts have been provided by the SahanaTest class
            These are admin@example.com and user@example.com

            You set the details for these account by using the convenience methods
            and then passing the member variables to the action.login function 
        """

        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )

        self.useSahanaUserAccount()
        self.action.login(self._user, self._password )

        self.action.logout()

    # This method demonstrates how to do a simple search
    def simpleSearch(self):
        """
            First open a page with a search widget.
            The search widget that is used is the list_filter
            which is used to filter a list from a database.
            Using the action.searchMatchesFound() method it is possible to
            record the number of records there are which match.
        """

        self.selenium.open("pr/person")
        result = self.action.searchMatchesFound()

        # A search is done using the action.search() method
        # the search checks on the message returned,
        # expecting a message as specific as the following can be problematic
        # because it is hard to guarantee that there will not be more matches
        self.action.search("User", "Showing 1 to 2 of 2 entries")

        # A search that will return just one match is done as follows
        self.action.searchUnique("Admin")

        # Finally let's clear the search criteria
        self.action.clearSearch()

        # Now having cleared the search box let's check that 
        # the number of results are the same as what we started with
        self.assertEqual(result, self.action.searchMatchesFound())

    # The next method shows how to check the response from different actions
    def checkMessages(self):
        """ 
            Let's log in using the admin account then log out
            after each call check on the confirmation message displayed
        """

        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        self.action.successMsg("Logged in")
        self.action.logout()
        self.action.successMsg("Logged out")

        # Now let's log in manually using the admin account
        # but with an invalid password and check on the error message displayed
        sel = self.selenium
        sel.open("default/user/login")
        sel.click("auth_user_email")
        sel.type("auth_user_email", self._user)
        sel.type("auth_user_password", "WrongPassword")
        sel.click("//input[@value='Login']")
        # The above manual codes are only needed to avoid the error checking done by action.login()
        self.action.errorMsg("Invalid login")

    # The following test will be used to introduce some of the more common
    # tasks associated with testing a form
    def simpleFormTest(self):
        """
            Open the form to register a new user
            Check that the form has the right elements
        """

        sel = self.selenium
        sel.open("default/user/register")
        # The steps to check a form are as follows:
        # 1. Get a formTemplate object
        # 2. Using the formTemplate object, add elements to this form
        # 3. check the form
        # The action.getFormTemplate() method returns a new formTemplate object
        # The action.addFormElement() method adds an element to the formTemplate object
        #                             by default the element will be an input with type text,
        #                             visible with no expected value.
        # The action.checkForm() method checks that the elements on the screen
        # conform with the template 
        template = self.action.getFormTemplate()
        self.action.addFormElement(template, "auth_user_first_name__label", "label", "")
        self.action.addFormElement(template, "auth_user_first_name")
        self.action.checkForm(template)

        # The following code will add the next label input pair but using the
        # template methods directly
        template.addFormElement("auth_user_last_name__label", "label", "")
        template.addFormElement("auth_user_last_name")
        template.checkForm()

        # Element can be removed from the form
        template.removeElement("auth_user_last_name__label")
        template.removeElement("auth_user_last_name")
        template.checkForm()

        # Labels can be added as part of a form element, if this is done
        # then the label is only reported on if there is an error
        template.addFormElement("auth_user_last_name").setLabelID("auth_user_last_name__label")
        template.checkForm()

        # Some convenience methods have been provided to speed up the
        # process of building the template form
        template.addSelect(labelID="auth_user_language__label",
                           selectID="auth_user_language",
                           value="en",)
        template.addInput(labelID="auth_user_mobile__label",
                          inputID="auth_user_mobile")
        template.addInput(labelID="auth_user_email__label",
                          inputID="auth_user_email")
        template.addInput(labelID="auth_user_password__label",
                          inputID="auth_user_password")
        template.addInput(labelID="auth_user_password_two__label",
                          inputID="auth_user_password_two")
        template.addInput(labelID="auth_user_password_two__label",
                          inputID="auth_user_password_two")

        # Submit buttons are added using the addButton method
        # it would be possible to add them via the addInput method if the 
        # button has been assigned a unique id but that is not always the case.
        # So an additional method is provided and, under the hood,
        # these buttons are managed in a slightly different way.
        template.addButton("Register")

        # Now the form can be checked
        # since all the elements have been added to the template the checkFormStrict method
        # can be used. NOTE this is an *experimental method* it tries to check that the template
        # matches what is displayed. It is not guaranteed to manage all possible form elements.
        # If you have an element that you would like to be added to this method, raise a ticket on Trac
        template.checkForm()
        failures = template.checkFormStrict("regform")
        if len(failures) == 0:
            print "Strict compliance met"
        else:
            print failures
        
        # The help buttons can also be checked, first add the help details to each element
        template.getElementFromKey("auth_user_language").setBalloonTitle("Language")
        template.getElementFromKey("auth_user_language").setBalloonText("The language you wish the site to be displayed in.")
        template.getElementFromKey("auth_user_mobile").setBalloonTitle("Mobile Phone").setBalloonText("Entering a phone number is optional, but doing so allows you to subscribe to receive SMS messages.")
        template.checkForm()

    def saveFormTest(self):
        """ Log in as admin and then open the form to create a new organisation """

        sel = self.selenium
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password)
        sel.open("org/organisation/create")

        # Fill the form using the fillForm method
        # Data can be entered into each element in the form the element is assumed to be a text box
        # For other types of input (such as the select) the type needs to be specified
        self.action.fillForm("org_organisation_name", "Example.com")
        self.action.fillForm("org_organisation_acronym", "eCom")
        self.action.fillForm("org_organisation_type", "Institution", "select")
        self.action.fillForm("org_organisation_cluster_id", "Telecommunications", "select")
        self.action.fillForm("org_organisation_country", "United States", "select")
        self.action.fillForm("org_organisation_website", "www.example.com")
        self.action.fillForm("org_organisation_donation_phone", "0123456789")
        self.action.fillForm("org_organisation_comments", "Give a person a phone they'll talk for a day. Teach a person to dial and they'll talk for a lifetime.")

        # Now save the form
        self.assertTrue(self.action.saveForm("Save", "Organization added"))

        # Now delete the object that was created
        self.action.deleteObject("org/organisation", "Example.com", "Organization")

# Now that the test class has been completed it is necessary to edit the
# data/testModules.txt file. Add the following line:
# Tutorial, tutorialTest.TutorialTest
