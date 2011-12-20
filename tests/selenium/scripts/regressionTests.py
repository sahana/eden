from Tkinter import *

from sahanaTest import SahanaTest
import HTMLTestRunner
from xmlrunner import *
from selenium import selenium

import os
import sys
import StringIO
import traceback
sys.path.append("GUI")
from mainWindow import TestWindow
from testConfig import TestConfig

if __name__ == "__main__":
    # Do we have any command-line arguments?
    args = sys.argv
    if args[1:]:
        # Yes: we are running the tests from the CLI (e.g. from Hudson)
        # The 1st argument is taken to be the config file:
        config_filename = args[1]

        path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(path)
        sys.path = [path] + [os.path.join(path, "config")] + [p for p in sys.path]
        exec("from %s import Settings" % config_filename)

        testSettings = Settings()
        browser = testSettings.radioB
        SahanaTest.setUpHierarchy(browser,
                                  testSettings.browserPath,
                                  testSettings.ipAddr,
                                  testSettings.ipPort,
                                  testSettings.URL + testSettings.app
                                 )
        # When running non-interactively, Username/Password are blank
        SahanaTest.useSahanaAccount("",
                                    "",
                                   )
        testConfig = TestConfig()
        moduleList = testConfig.getTestModuleDetails()
        testList = testConfig.getTestCasesToRun(moduleList)
        suite = testConfig.suite
        for testModule in testList: # dotted notation module.class
            testConfig.overrideClassSortList(testModule["class"],
                                             testModule["tests"])
        # Invoke TestRunner
        buf = StringIO.StringIO()
        try:
            report_format = args[2]
        except:
            report_format = "html"

        if report_format == "xml": # Arg 2 is used to generate xml output for jenkins
            runner = XMLTestRunner(file("../results/regressionTest-%s.xml" % (browser.replace("*", "")),
                                                                              "w"))
            runner.run(suite)

        elif report_format == "html":
            runner = HTMLTestRunner.HTMLTestRunner(
                        stream=buf,
                        title="<Sahana Eden Test>",
                        description="Suite of regressions tests for Sahana Eden."
                        )
            fileName = "../results/regressionTest-%s-%s.html" % (browser.replace("*", ""),
                                                                 time.strftime("%Y%m%d-%H%M%S"))
            file = open(fileName, "w")
            runner.run(suite)
            # check out the output
            byte_output = buf.getvalue()
            # output the main test output for debugging & demo
            # print byte_output
            # HTMLTestRunner pumps UTF-8 output
            output = byte_output.decode("utf-8")
            file.write(output)

        SahanaTest.selenium.stop()
    else:
        # No: we should bring up the GUI for interactive control
        TestWindow().mainloop()
