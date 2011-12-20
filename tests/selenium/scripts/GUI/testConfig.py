import unittest
import sys
import StringIO
import HTMLTestRunner
import time
import traceback

class TestConfig(object):
    """ Functions which are useful in both interactive & non-interactive mode """
    def __init__(self):
        self.suite = unittest.TestSuite()

    def test_main(self, testList, browser):
        for testModule in testList: # dotted notation module.class
            self.overrideClassSortList(testModule["class"], testModule["tests"])
#            self.suite.addTests(unittest.defaultTestLoader.loadTestsFromName(testName))
        # Invoke TestRunner
        buf = StringIO.StringIO()
        runner = HTMLTestRunner.HTMLTestRunner(
                    stream=buf,
                    title="<Sahana Eden Test>",
                    description="Suite of regressions tests for Sahana Eden."
                    )
        runner.run(self.suite)
        # check out the output
        byte_output = buf.getvalue()
        # output the main test output for debugging & demo
        # print byte_output
        # HTMLTestRunner pumps UTF-8 output
        output = byte_output.decode("utf-8")
        self.fileName = "../results/regressionTest-%s-%s.html" % (browser.replace("*", ""), time.strftime("%Y%m%d-%H%M%S"))
        file = open(self.fileName, "w")
        file.write(output)

    def overrideClassSortList(self, className, testList):
        testLoader = unittest.defaultTestLoader
        tempTests = unittest.TestSuite
        try:
            # loadTestsFromName will also import the module 
            tempTests = testLoader.loadTestsFromName(className)
        except:
            print "Unable to run test %s, check the test exists." % className
            traceback.print_exc()
        parts = className.split(".")
        if len(parts) == 2:
            # Grab the loaded module and get a instance of the class
            module = sys.modules[parts[0]]
            obj = getattr(module, parts[1])
            obj.setSortList(testList)
            # Add the sorted tests to the suite of test cases to be run
            suite = unittest.TestSuite(map(obj, obj._sortList))
            self.suite.addTests(suite)

    # a file with test details listed per line, with the format being:
    # <display name>, <dotted notation of the test>
    # any line not meeting this criteria will be ignored.
    # <dotted notation of the test> is:
    # module optionally followed by the class name optionally followed by the method
    # OR: module[.class[.method]]
    def getTestModuleDetails(self):
        # Read in the testModules files this is a comma separated list
        # Each row consists of two values, the name to be displayed in the UI
        # and the name of the class that will be invoked.
        source = open("../data/testModules.txt", "r")
        modules = source.readlines()
        source.close()
        # moduleList is a data structure containing all the details required by the UI for a module
        # The outer structure is a list of modules
        # The value is a map that will have three values
        # name:display name, class the ClassName and tests:map of testcases
        # The map of tests consists of the testName and a bool to indicate if it should be run
        # [0]{
        #       name:CreateLocations:
        #       class:locations.Locations,
        #       tests:{'name':"loadLocationTestData",'state':True,
        #              'name':"test_locationEmpty",'state':False,
        #              'name':"test_addL0Location",'state':False,
        #              'name':"removeLocationTestData",'state':True
        #             }
        #    }
        moduleList = []
        for module in modules:
            details = module.split(",")
            if len(details) == 2:
                moduleDetails = {}
                moduleDetails["name"] = details[0].strip() 
                moduleDetails["class"] = details[1].strip()
                moduleDetails["tests"] = self.readTestCasesForClass(moduleDetails["class"])
                moduleList.append(moduleDetails)
        return moduleList

    def readTestCasesForClass(self, className):
        try:
            source = open("../tests/%s.txt" % className, "r")
            testcases = source.readlines()
            source.close()
        except:
            # Need to generate the list from the class
            print "File ../tests/%s.txt not found" % className
            return self.extractTestCasesFromClassSource(className)
        testList = []
        for test in testcases:
            details = test.split(",")
            if len(details) ==  2:
                testDetails = {}
                testDetails["name"] = details[0].strip()
                if details[1].strip() == "True":
                    testDetails["state"] = True
                else:
                    testDetails["state"] = False
                testList.append(testDetails)
        return testList

    def extractTestCasesFromClassSource(self, className):
        parts = className.split(".")
        if len(parts) == 2:
            # Grab the loaded module and get a instance of the class
            try:
                module = __import__( parts[0] )
            except ImportError:
                print "Failed to import module %s" % parts[0]
                raise
            module = sys.modules[parts[0]]
            obj = getattr(module, parts[1])
            testList = []
            for test in obj._sortList:
                tests = {}
                tests["state"] = True 
                tests["name"] = test
                testList.append(tests)
            return testList
        return []
    
    def getTestCasesToRun(self, moduleList):
        """ Take a moduleList & convert to the correct format """
        i = 0
        testModuleList = []
        for module in moduleList:
            testModule = {}
            testDetail = []
            for test in moduleList[i]["tests"]:
                if test["state"] == True:
                    testDetail.append(test["name"])
            testModule["class"] = moduleList[i]["class"]
            testModule["tests"] = testDetail
            testModuleList.append(testModule)
            i += 1
        return tuple(testModuleList)
