import unittest, time, re
from selenium import selenium
import sys
import os
import csv
sys.path.append("actions")
from authentication import Authenticate
from search import Search
from messages import Message
from form import Form, FormTemplate, rHeaderTemplate

### TODO ###
# Change addUser to use the addForm methods
# Change addRole to use the addForm methods
# addRole currently toggles the roles, need a check to see if it is selected first

# The Coverage class helps to measure coverage of the testing API,
# not I repeat NOT coverage of the Eden code base.
class Coverage:
    def __init__ (self, methodName):
        self.name = methodName
        self.visits = 1
        self.callList = []
        
    def inc (self):
        self.visits += 1
        
    def calling (self, callMethod):
        if callMethod in self.callList:
            return
        else:
            self.callList.append(callMethod)
        
    def toString (self):
         data = "%s %s\n" % (self.name, self.visits)
         if len(self.callList) != 0:
             for method in self.callList:
                 data += "\t%s\n" % method
         return data
    
class Action(unittest.TestCase):
    def __init__ (self, selenium):
        self.sel = selenium
        self._diag = True # make True for profiling diagnostics
        self._diagResults = None
        self._diag_sleepTime = None
        self._diag_performCalls = None
        self.openReport()
        self.coverage = False # make False to turn off coverage data
        self.coverageMap = {}
        self.coverageTrace = []
        
    def openReport(self):
        """ used to save the diagnostics to a file """
        if self._diag:
            self._diagResults = open("../results/diagResults.txt", "a")
            self._diagResults.write(time.strftime("New Search run %d %b %Y (%H:%M:%S)\n"))
    
    def closeReport(self, msg):
        """ Close the file that is recording the diagnostics """
        if self._diag:
            self._diagResults.write(msg)
            self._diagResults.close()

    # Methods for managing the code coverage within the API
    def startCoverage(self, methodName):
        if self.coverage:
            if len(self.coverageTrace)!= 0:
                parentName = self.coverageTrace[0]
                self.coverageMap[parentName].calling(methodName)
            self.coverageTrace.insert(0, methodName)
            self.add(methodName)

    def endCoverage(self):
        if self.coverage:
            self.coverageTrace.pop()

    def add(self, methodName):
        if self.coverage:
            if methodName in self.coverageMap:
                self.coverageMap[methodName].inc()
            else:
                self.coverageMap[methodName] = Coverage(methodName)
            
    def coverageToString(self):
        if self.coverage:
            file = open("../results/coverageResults.txt", "a")
            file.write(time.strftime("New run %d %b %Y (%H:%M:%S)\n"))
            for key, value in self.coverageMap.items():
                file.write(value.toString())
            self._diagResults.close()
    # END OF Methods for managing the code coverage within the API
    
    def prePopulateCSV(self, file, testType = "regression"):
        """
            load the details from the pre-populate file 
            into a list of dictionary items
        """
        result = []
        key = []
        fullPath = os.path.join("..",
                                "..",
                                "..",
                                "private",
                                "prepopulate",
                                testType,
                                file)
        if os.path.exists(fullPath) == False:
            print >> sys.stderr, "Failed to find pre-populate file %s" % file
            return []
        else:
            try:
                csvFile = open(fullPath, "rb")
            except IOError:
                print >> sys.stderr, "Failed to open pre-populate file %s" % file
                return []
            reader = csv.reader(csvFile,)
            for line in reader:
                if key == []:
                    key=line
                else:
                    data = {}
                    for cnt in range(len(key)):
                        if cnt < len(line):
                            data[key[cnt]] = line[cnt]
                        else:
                            data[key[cnt]] = None
                    result.append(data)
        return result
    
    def openPage(self, page, force=False, heading=None):
        """ Open the specified Page if not already open or if forced """
        index = -1 * len(page)
        location = self.sel.get_location()[index:]
        if force or location != page:
            print "Opening page %s" % page
            # True stops a http HEAD being sent
            self.sel.do_command("open", [page,True])
        if heading != None:
            self.checkPageHeading(heading)
    
    def checkPageHeading(self, heading, level="h2"):
        """ Check that the heading matches the expected value """
        self.assertEqual(heading, self.sel.get_text("//%s"%level))

    def openLink(self, link):
        """ click on the specific anchor """
        if self.sel.is_element_present(link):
            self.sel.click(link)
            self.sel.wait_for_page_to_load("30000")
            return True
        else:
            return False
 
    def quickLink(self, link):
        """ click on the specific anchor """
        if self.sel.is_element_present(link):
            self.sel.click(link)
            return True
        else:
            return False
 
    # Methods for managing authentication into Sahana
    # login
    # logout
    def login(self, username, password, reveal=True):
        """
            login to the system using the name provided
            @param username: the username to be used
            @param password: the password of the user
            @param reveal:   show the password on any error message
        """
        self.startCoverage("login")
        a = Authenticate(self.sel)
        a.login(self, username, password, reveal);
        self.endCoverage()

    def logout(self):
        """ logout of the system """
        self.startCoverage("logout")
        a = Authenticate(self.sel)
        a.logout(self)
        self.endCoverage()

    # Searching methods
    # search
    # searchUnique
    # clearSearch
    # searchMatchesFound - returns the filter string
    def search(self, searchString, expected):
        self.startCoverage("search")
        s = Search(self)
        result = s.search(searchString, expected)
        self.endCoverage()
        return result
    
    def searchUnique(self, uniqueName):
        """
            Perform a search when one and only one result will be returned
            @param uniqueName: the value to search for
        """
        self.startCoverage("searchUnique")
        result = self.search(uniqueName, r"1 entries")
        self.endCoverage()
        return result
        
    def clearSearch(self):
        """ Helper function used to clear the search results """
        self.startCoverage("clearSearch")
        self.search("", r"entries")
        self.endCoverage()

    def searchMatchesFound(self, searchString=None):
        """ Helper function used to return the number of search results """
        self.startCoverage("searchMatchesFound")
        s = Search(self)
        result = s.searchMatchesFound(searchString)
        self.endCoverage()
        return result
        
        
    # Many actions are reported on in Sahana by displaying a banner at the top of the page
    # Methods to check each banner for the desired message
    # successMsg
    # errorMsg
    # findResponse
    def successMsg(self, message):
        """
            Method used to check for confirmation messages
            @param message: the message to be searched for in the banner
            returns:        boolean reporting success
        """
        self.startCoverage("successMsg")
        m = Message(self)
        result = m._findMsg(message, "confirmation")
        self.endCoverage()
        return result

    def errorMsg(self, message):
        """
            Method used to check for error messages
            @param message: the message to be searched for in the banner
            returns:        boolean reporting success
        """
        self.startCoverage("errorMsg")
        m = Message(self)
        result = m._findMsg(message, "error")
        self.endCoverage()
        return result

    def findResponse(self, successMsg, errorMsg):
        """
            Method to check on the response of an action by looking at the message
            @param SuccessMsg:  the message to be searched for in the banner upon success
            @param errorMsg:    the message to be searched for in the banner upon failure
            returns:            boolean reflecting the type of message found
            side effect:        exception if neither message found
        """
        self.startCoverage("findResponse")
        m = Message(self)
        result = m.findResponse(successMsg, errorMsg)
        self.endCoverage()
        return result

        
    # Methods to manage form manipulation
    # saveForm
    # getFormTemplate
    # checkForm
    def fillForm(self, id, value, type="text"):
        self.startCoverage("fillForm")
        f = Form(self)
        result = f.fillForm(id, value, type)
        self.endCoverage()
        return result

    def fillAutoComplete(self, fieldID, value, throbber=None):
        self.startCoverage("fillAutoComplete")
        f = Form(self)
        result = f.fillAutoComplete(fieldID, value, throbber)
        self.endCoverage()
        return result

    def saveForm(self, submit, message=None, success=True):
        """
            Method to save the details
            @param message: the success message to check (optional)
            @param success: whether we're looking for a confirmation (default) or failure
        """
        self.startCoverage("saveForm")
        f = Form(self)
        result = f.saveForm(submit, message, success)
        self.endCoverage()
        return result

    def getFormTemplate(self):
        """ Method to return a new empty form element """
        self.startCoverage("getFormTemplate")
        f = FormTemplate(self)
        self.endCoverage()
        return f

    def addFormElement(self, formTemplate, id=None, tag=None, type=None, visible=True, value=None, elementDetails=()):
        """ Method to add a form element to the template """
        self.startCoverage("addFormElement")
        formTemplate.addFormElement(id, tag, type, visible, value, elementDetails)
        self.endCoverage()
        return formTemplate

    def removeElement(self, formTemplate, id):
        """ Method to remove an element from the template """
        self.startCoverage("removeElement")
        formTemplate.removeElement(id)
        self.endCoverage()
        return formTemplate

    def getFormElements(self, formName):
        self.startCoverage("getFormElements")
        f = Form(self)
        elementList = f.getFormElements(formName)
        self.endCoverage()
        return elementList
        
    def addButton(self, formTemplate, value):
        """ Method to add a submit button to the template """
        self.startCoverage("addButton")
        formTemplate.addButton(value)
        self.endCoverage()
        return formTemplate
        
    def showElement(self, formTemplate, elementId):
        """ Method to set an element to be visible """
        self.startCoverage("showElement")
        formTemplate.getElementFromKey(value).setVisible(True)
        self.endCoverage()
        return formTemplate
        
    def hideElement(self, formTemplate, elementDetails):
        """ Method to set an element to be hidden """
        self.startCoverage("showElement")
        formTemplate.getElementFromKey(value).setVisible(False)
        self.endCoverage()
        return formTemplate
        
    def checkForm (self, formTemplate, readonly=False):
        """
            Method to check the layout of a form
            elementList:  data to check the elements on the form
            buttonList:   data to check the buttons on the form
            helpList:     data to check the help balloons 
            side effects: TestCase::fail() is called if any check failed
            side effects: messages are written out reflecting what was verified
        """
        self.startCoverage("checkForm")
        f = Form(self)
        f.checkForm(formTemplate, readonly)
        self.endCoverage()
        return f
        
    def checkFormStrict(self, formTemplate, formName=None):
        """
            Method to check that the visible element in the template
            Are all displayed and that they are the only ones displayed

            NOTE this is an *experimental method* it tries to check that the template
            matches what is displayed. It is not guaranteed to manage all possible form elements.

            If you have a element that you would like to be added to this method raise a ticket on Trac
        """

        self.startCoverage("checkFormStrict")
        error = []
        f = Form(self)
        error = f.checkFormStrict(formTemplate, formName)
        self.endCoverage()
        return error
        
    def getrHeaderTemplate(self):
        """ Method to return a new empty rHeader template """
        self.startCoverage("getrHeaderTemplate")
        r = rHeaderTemplate(self)
        self.endCoverage()
        return r

    def addrHeaderLine(self, template, header, value):
        """ Method to add a line to an existing rHeader template """
        self.startCoverage("addrHeaderLine")
        template.addValue(header, value)
        self.endCoverage()
        return template

    def checkHeading(self, template):
        """ Method to check the details that are displayed in the heading """
        self.startCoverage("checkHeading")
        template.checkrHeader()
        self.endCoverage()
        return template

#    def checkForm (self, elementList, buttonList, helpList):
#        # Method to check the layout of a form
#        # elementList:  data to check the elements on the form
#        # buttonList:   data to check the buttons on the form
#        # helpList:     data to check the help balloons 
#        # side effects: TestCase::fail() is called if any check failed
#        # side effects: messages are written out reflecting what was verified
#        elements = []
#        failed = []
#        for element in elementList:
#            result = self._element(element)
#            if result == True:
#                if len(element) > 2 and element[2]: elements.append(element[1])
#            else: failed.append(result)
#        for name in buttonList:
#            self._button(name)
#        for title in helpList:
#            self._helpBalloon(title)
#        if len(failed) > 0:
#            msg = '/n'.join(failed)
#            self.fail(msg)
#        if len(elements) > 0:
#            print "Verified the following form elements %s" % elements

#    def _button(self, name):
#        # Method to check that form button is present
#        sel = self.sel
#        element = '//input[@value="%s"]' % (name)
#        errmsg = "%s button is missing" % (name)
#        self.assertTrue(sel.is_element_present(element), errmsg)
#        print "%s button is present" % (name)        

#    def _helpBalloon(self, helpTitle):
#        # Method to check that the help message is displayed
#        # helpTitle: the balloon help that is displyed on the form 
#        sel = self.sel
#        element = "//div[contains(@title,'%s')]" % (helpTitle)
#        self.assertTrue(sel.is_element_present(element))
#        sel.mouse_over(element)
#        self.assertFalse(sel.is_element_present(element), "Help %s is missing" % (helpTitle))
#        print "Help %s is present" % (helpTitle)

#    def _element(self, elementDetails):
#        # Method to check that form _element is present
#        # The elementDetails parameter is a list of up to 4 elements
#        # elementDetails[0] the type of HTML tag
#        # elementDetails[1] the id associated with the HTML tag
#        # elementDetails[2] *optional* the visibility of the HTML tag
#        # elementDetails[3] *optional* the value or text of the HTML tag
#        # return            True on success error message on failure
#        sel = self.sel
#        type = elementDetails[0]
#        id = elementDetails[1]
#        msg = ""
#        if (len(elementDetails) >= 3):
#            visible = elementDetails[2] 
#        else:
#            visible = True
#        if (len(elementDetails) >= 4):
#            value = elementDetails[3] 
#        else:
#            value = None
#        elementDetails = '//%s[@id="%s"]' % (type, id)
#        if visible:
#            if not sel.is_element_present(elementDetails): return "%s element %s is missing" % (type, id)
#        if sel.is_visible(elementDetails) != visible: return "%s element %s doesn't have a visibility of %s" % (type, id, visible)
#        if value != None:
#            actual = sel.get_value(elementDetails)
#            msg = "expected %s for element %s doesn't equal the actual value of %s" % (value, id, actual)
#            if value != actual: return msg
#        return True

        
    def showNamedElement(self, name, elementList):
        """
            Method to set an element to be visible
            @param name:        The id of the element
            @param elementList: The element list
        """
        for element in elementList:
            if element[1] == name:
                self.showElement(element)
                return True
        return False
        
    def hideNamedElement(self, name, elementList):
        """
            Method to set an element to be hidden
            @param name:        The id of the element
            @param elementList: The element list
        """
        for element in elementList:
            if element[1] == name:
                self.hideElement(element)
                return True
        return False
        
#    # Method to check on the rheading table that displays read only data related to a form
#    def checkHeading(self, detailMap):
#        # Method to check the details that are displayed in the heading
#        # detailMap:   A (name, value) pair of the data which is displayed in Sahana as a table
#        # side effect: Assert the values are present
#        sel = self.sel
#        heading = sel.get_text("//div[@id='rheader']/div/table/tbody")
#        searchString = ""
#        for key, value in detailMap.items():
#            msg = "Unable to find details of %s in the header of %s"
#            self.assertTrue(key in heading, msg % (key, heading))
#            self.assertTrue(value in heading, msg % (value, heading))

    def checkTab(self, name):
        """ Method to check if a tab is present """
        sel = self.sel
        element = "//div[@class='tabs']/span/a[text()='%s']" % (name)
        return sel.is_element_present(element)

    def clickTab(self, name):
        """ Method to click on a tab """
        sel = self.sel
        element = "//div[@class='tabs']/span/a[text()='%s']" % (name)
        sel.click(element)
        sel.wait_for_page_to_load("30000")

    def findLink(self, expression):
        sel = self.sel
        text = sel.get_text("//div[@id='content']")
        m = re.search(expression, text)
        if m != None:
            result = m.group(0)
            self.openLink("link=%s"%result)
            return True
        else:
            return False


    def btnLink(self, id, name):
        """ Method to check button link """
        sel = self.sel
        element = '//a[@id="%s"]' % (id)
        errMsg = "%s button is missing" % (name)
        self.assertTrue(sel.is_element_present(element), errMsg)
        self.assertTrue(sel.get_text(element), errMsg)
        print "%s button is present" % (name)
        
    def noBtnLink(self, id, name):
        """ Method to check button link is not present """
        sel = self.sel
        element = '//a[@id="%s"]' % (id)
        errMsg = "Unexpected presence of %s button" % (name)
        if sel.is_element_present(element):
            self.assertFalse(sel.get_text(element), errMsg)
        print "%s button is not present" % (name)

    def clickBtn(self, name="Open"):
        """ Method to click on a button """
        sel = self.sel
        element = "link=%s" % (name)
        sel.click(element)
        sel.wait_for_page_to_load("30000")
        
    def deleteObject(self, page, objName, type="Object"):
        sel = self.sel
        # need the following line which reloads the page otherwise the search gets stuck  
        sel.open(page)
        try:
            self.searchUnique(objName)
            sel.click("link=Delete")
            #self.confirmDelete()
            if self.findResponse("%s deleted" % type, "Integrity error:"):
                print "%s %s deleted" % (type, objName)
                return True
            else:
                print "Failed to delete %s %s" % (type, objName)
                return False
        except:
            print "Failed to delete %s %s from page %s" % (type, objName, page)
            return False

    def confirmDelete(self):
        sel = self.sel
        confirm = ""
        result = None
        try:
            confirm = sel.get_confirmation()
            search = r"^Sure you want to delete this object?[\s\S]$"
            result = re.search(search, confirm)
            self.assertTrue(result)
        except:
            # Not working with FF4:
            # http://code.google.com/p/selenium/issues/detail?id=1604
            # Can workaround by setting deployment_settings.ui.confirm = False
            print "Failed to properly manage a delete confirmation. " \
                   "Looking for %s. Got %s as the message " \
                   "result was %s" % (search, confirm, result)
            pass

    def registerUser(self, first_name, last_name, email, password):
        first_name = first_name.strip()
        last_name = last_name.strip()
        email = email.strip()
        password = password.strip()
        
        sel = self.sel
        sel.open("default/user/register")
        sel.type("auth_user_first_name", first_name)
        sel.type("auth_user_last_name", last_name)
        sel.select("auth_user_language", "label=English")
        sel.type("auth_user_email", email)
        sel.type("auth_user_password", password)
        sel.type("password_two", password)
        sel.click("//input[@value='Register']")
        sel.wait_for_page_to_load("30000")
        msg = "Unable to register user %s %s with email %s" % (first_name, last_name, email)
        self.assertTrue(self.successMsg("Registration successful"), msg)
        # Only open this page if on another page
        print sel.get_location()[-10:]
        if sel.get_location()[-10:]=="admin/user":
            print "Already on page admin/user"
        else:
            sel.open("admin/user")
        self.searchUnique(email)
        self.assertTrue(re.search(r"Showing 1 to 1 of 1 entries", sel.get_text("//div[@class='dataTables_info']")))
        print "User %s created" % (email)

    def addUser(self, first_name, last_name, email, password):
        first_name = first_name.strip()
        last_name = last_name.strip()
        email = email.strip()
        password = password.strip()
        
        sel = self.sel
        # Only open this page if on another page
        print sel.get_location()[-10:]
        self.openPage("admin/user")
        if self.searchMatchesFound(email) > 0:
            sel.click("link=Open")
            sel.wait_for_page_to_load("30000")
            sel.type("auth_user_first_name", first_name)
            sel.type("auth_user_last_name", last_name)
            sel.select("auth_user_language", "label=English")
            sel.type("auth_user_email", email)
            sel.type("auth_user_password", password)
            sel.type("password_two", password)
            sel.select("auth_user_registration_key", "")
            sel.click("//input[@value='Save']")
            sel.wait_for_page_to_load("30000")
            msg = "Unable to update user %s %s with email %s" % (first_name, last_name, email)
            self.assertTrue(self.successMsg("User updated"), msg)
            self.searchUnique(email)
            self.assertTrue(re.search(r"Showing 1 to 1 of 1 entries", sel.get_text("//div[@class='dataTables_info']")))
            print "User %s enabled" % (email)
        else:
            # This may need changing if the embedded add user page is reinstalled
            # It has been removed because it broke the searching
            self.assertTrue(sel.is_element_present("add-btn"))
            sel.click("add-btn")
            sel.wait_for_page_to_load("30000")
            sel.type("auth_user_first_name", first_name)
            sel.type("auth_user_last_name", last_name)
            sel.select("auth_user_language", "label=English")
            sel.type("auth_user_email", email)
            sel.type("auth_user_password", password)
            sel.type("password_two", password)
            sel.click("//input[@value='Save']")
            sel.wait_for_page_to_load("30000")
            msg = "Unable to create user %s %s with email %s" % (first_name, last_name, email)
            self.assertTrue(self.successMsg("User added"), msg)
            self.searchUnique(email)
            self.assertTrue(re.search(r"Showing 1 to 1 of 1 entries", sel.get_text("//div[@class='dataTables_info']")))
            print "User %s created" % (email)

    def addRole(self, email, roles):
        email = email.strip()
        roles = roles.strip()
        roleList = roles.split(" ")
        
        sel = self.sel
        if sel.get_location()[-10:]!="admin/user":
            sel.open("admin/user")
            sel.wait_for_page_to_load("30000")
        self.searchUnique(email)
        # Cannot click on link=Roles because that will trigger off the menu item admin/roles 
        sel.click("//table[@id='list']/tbody/tr[1]/td[1]/a[2]")
        sel.wait_for_page_to_load("30000")
        for role in roleList:
            sel.click("//input[@name='roles' and @value='%s']" % role.strip())
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # @ToDo: Message to get all roles (if multiple) not just last 1
        msg = "Failed to add role %s to user %s" % (role.strip() , email)
        self.assertTrue(self.successMsg("User Updated"), msg)
        print "User %s added to group %s" % (email, role.strip())

    def delUser(self, email):
        email = email.strip()
        print "Deleting user %s" % email
        sel = self.sel
        if sel.get_location()[-10:]!="admin/user":
            sel.open("admin/user")
            sel.wait_for_page_to_load("30000")
        self.searchUnique(email)
        sel.click("link=Disable")
        self.assertTrue(self.successMsg("User Account has been Disabled"))
        print "User %s disabled" % (email)

