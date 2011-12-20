from selenium import selenium
import unittest, time, re
import actions
import inspect

# Class that will provide a constant interface to the Selenium test suite
#
# The following variables are shared by all classes that inherit SahanaTest 
# self.selenium will provide a reference to the shared selenium object
# self.action will provide a reference to the shared action object
#
# The following variables are unique to each class that will inherit SahanaTest
# These are used to create test data at the start of a run and delete the test data at the end
# self.testcaseStartedCount will provide a count of the number of tests within the class that have been started
# self.testcaseFinishedCount will provide a count of the number of tests within the class that have completed
# self.testcaseCount will provide a count of the number of tests within the class that will be run

class SahanaTest(unittest.TestCase):

    """
        All Sahana Test Case Classes should inherit this class
        The sub classes should not include the setUp() or tearDown() methods rather
        use a method called firstRun() or lastRun() in the sub classes
    """

    _seleniumCreated = False
    ipaddr = ""
    ipport = ""
    browser = ""
    webURL =  ""
    _classDetailsCollected = False
    _sortList = None
    _user = "user@example.com"
    _password = "testing"

    @staticmethod
    def setUpHierarchy(browser = "*chrome", 
                       path = "", 
                       ipaddr = "localhost", 
                       ipport = 4444, 
                       webURL = "http://127.0.0.1:8000/"):
        """
            This method would typically only be run once it will create a
            Selenium instance and then start it.
            
            This is a static method with the idea that the properties created
            in this method are shared amongst all subclasses. That is:
            SahanaTest.selenium and SahanaTest.action
        """
        if  (SahanaTest.ipaddr != ipaddr) or (SahanaTest.ipport != ipport) or (SahanaTest.browser != browser) or (SahanaTest.webURL !=  webURL):
            SahanaTest._seleniumCreated = False
        # Only run once
        if not SahanaTest._seleniumCreated:
            if browser == "*custom":
                browser += " %s" % path
            print "selenium %s %s %s %s" % (ipaddr, ipport, browser, webURL)
            SahanaTest.ipaddr = ipaddr
            SahanaTest.ipport = ipport
            SahanaTest.browser = browser
            SahanaTest.webURL =  webURL
            SahanaTest.selenium = selenium(ipaddr, ipport, browser, webURL)
            SahanaTest.action = actions.Action(SahanaTest.selenium)
            SahanaTest._seleniumCreated = True
        if SahanaTest.selenium.sessionId == None:
            SahanaTest.selenium.start()

    @classmethod
    def start(cls):
        """
            This method is called by the instance setUp method below.
        
            This is a class method and will create instance variables specific
            for each class within the hierarchy. That is:
            The number of testCases with the class
            The number that have started running
            The number that have finished running
            Whether a firstRun() method exists in the class (if so it will be called automatically)
            Whether a lastRun() method exists in the class (if so it will be called automatically)
        """

        if not cls._classDetailsCollected:
            cls.testcaseStartedCount = 0
            cls.testcaseFinishedCount = 0
            cls.testcaseCount = 0
            cls.firstRunExists = False
            cls.lastRunExists = False
            cls.timings = []
#            cls.action.openReport()
            # Use inspect to find the number of test methods
            # this is then used in tearDown() to work out if lastRun() needs to be invoked
            methods = inspect.getmembers(cls, inspect.ismethod)
            for (name, value) in methods:
                if re.search(r'^test_', name)!= None:
                    cls.testcaseCount += 1
                if name == "firstRun":
                    cls.firstRunExists = True
                if name == "lastRun":
                    cls.lastRunExists = True
            # the testcaseCount needs to be modified if _sortList exists
            if cls._sortList != None:
                cls.testcaseCount = len(cls._sortList)
            # This cls version will now hide the SahanaTest version
            cls._classDetailsCollected = True
            cls.timings.append(time.time())
        cls.testcaseStartedCount += 1
    
    @classmethod
    def finish(cls):
        cls.testcaseFinishedCount += 1
        return cls.testcaseFinishedCount == cls.testcaseCount

    @classmethod
    def sortTests(cls,list):
        print cls
        if cls._sortList:
            return map(cls,cls._sortList)
        else:
            return None

    @classmethod
    def setSortList(cls, list):
        cls._sortList = list
        
    @classmethod
    def useSahanaAdminAccount(cls):
        cls._user = "admin@example.com"
        cls._password = "testing"
        
    @classmethod
    def useSahanaUserAccount(cls):
        cls._user = "normaluser@example.com"
        cls._password = "testing"
        
    @classmethod
    def useSahanaAccount(cls, email, password):
        cls._user = email
        cls._password = password
    
    def setUp(self):
        self.action.openReport()
        print self.shortDescription()
        self.start()
        self.timings.append(time.time())
#        print "count %s started %s firstRunExists %s" % (self.testcaseCount, self.testcaseStartedCount, self.firstRunExists)
        if self.testcaseStartedCount == 1:
            if self.firstRunExists:
                self.firstRun()
        
    def tearDown(self):
        self.timings[self.testcaseStartedCount] = time.time() - self.timings[self.testcaseStartedCount]
        print "Processing time took %.3f seconds" % self.timings[self.testcaseStartedCount]
        if self.finish():
            if self.lastRunExists:
                self.lastRun()
            self.timings[0] = time.time() - self.timings[0]
            if (self.timings[0] > 60):
                print "Total processing time took %1.0f:%2.3f seconds" % (self.timings[0]//60, self.timings[0]%60)
            else:
                print "Total processing time took %.3f seconds" % self.timings[0]
            self.__class__._classDetailsCollected = False # Set it up for the next full run
            self.action.logout()
            self.action.closeReport("Total processing time took %.3f seconds\n" % self.timings[0])
            self.action.coverageToString()
