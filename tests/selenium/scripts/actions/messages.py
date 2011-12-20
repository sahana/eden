import unittest, time
from selenium import selenium

class Message(unittest.TestCase):
    def __init__ (self, action):
        self.action = action
        self.sel = action.sel
        
    # Many actions are reported on in Sahana by displaying a banner at the top of the page
    # Methods to check each banner for the desired message
    # _checkBanner
    # _findMsg
    def _checkBanner(self, message, type):
        """
            This method should not be called directly
            @param message: the message to be searched for in the banner
            @param type:    the type of banner to be searched for (confirmation or error)
            returns:  boolean reporting success
        """
        sel = self.sel
        i = 1
        self.waitForAjax()
        while sel.is_element_present('//div[@class="%s"][%s]' % (type, i)):
            banner = sel.get_text('//div[@class="%s"][%s]' % (type, i))
            if message in banner:
                if self.action._diag:
                    self.action._diagResults.write("%s\tSUCCEEDED\t%s\t\n" % (message, self.action._diag_sleepTime))
                return True
            i += 1
            
    def _findMsg(self, message, type):
        """
            This method should not be called directly.
            Method to locate a message in a div with a class given by type
            The method will pause for up to 10 seconds waiting for the banner to appear.
            @param message: the message to be searched for in the banner
            @param type:    the type of banner to be searched for (confirmation or error)
            returns:  boolean reporting success
        """
        sel = self.sel
        self.action._diag_sleepTime = 0
        for cnt in range (10):
            if self._checkBanner(message, type):
                return True
            time.sleep(1)
            self.action._diag_sleepTime += 1
        if self.action._diag:
            self.action._diagResults.write("%s\tFAILED\t%s\t\n" % (message, self.action._diag_sleepTime))
        return False
    
    def findResponse(self, successMsg, errorMsg):
        """
            Method to check on the response of an action by looking at the message
            @param SuccessMsg:  the message to be searched for in the banner upon success
            @param errorMsg:    the message to be searched for in the banner upon failure
            returns:      boolean reflecting the type of message found
            side effect:  exception if neither message found
        """
        sel = self.sel
        sType = "confirmation"
        eType = "error"
        self.action._diag_sleepTime = 0
        for cnt in range (10):
            if self._checkBanner(successMsg, sType):
                return True
            if self._checkBanner(errorMsg, eType):
                return False
            time.sleep(1)
            self.action._diag_sleepTime += 1
        if self.action._diag:
            self.action._diagResults.write("findReponse %s\tFAILED\t%s\t\n" % (successMsg, self.action._diag_sleepTime))
        raise UserWarning("Response not found")

    def waitForAjax(self,timeout=120):
        #Function to help wait while a test is in progress
        # timeout: The time to wait for to check if Jquery is active
        js_condition = "selenium.browserbot.getCurrentWindow().jQuery.active == 0"
        selenium.wait_for_condition(js_condition, timeout)


