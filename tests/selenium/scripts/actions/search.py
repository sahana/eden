import unittest, time
from selenium import selenium

class Search(unittest.TestCase):
    def __init__ (self, action):
        self.action = action
        self.sel = action.sel

    def searchMatchesFound(self, searchString=None):
        if searchString != None:
            if not self._performSearch(searchString): return 0
        result = self.sel.get_text("//div[@id='list_info']")
        if result.find("Showing")>-1:
            start = result.find("of")+3
            end = result.find("entries")
            return int(result[start:end].strip())
        else:
            return 0
        
    def _performSearch(self, searchString, force=False):
        # Not intended to be called directly:
        # Searches using the searchString in the quick search filter box
         
        # The search filter is part of the http://datatables.net/ JavaScript getting it to work with Selenium needs a bit of care.
        # Entering text in the filter textbox doesn't always trigger off the filtering and it is not possible with this method to clear the filter.
        # The solution is to put in a call to the DataTables API, namely the fnFilter function
        # However, the first time that the fnFilter() is called in the testing suite it doesn't complete the processing, hence it is called twice.
        sel = self.sel
        if not sel.is_element_present("list_filter"):
            return False
        clearString = ""
        if searchString == '': clearString = "Clearing..."
        # First clear the search field and add a short pause
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( '%s' );" % clearString)
        if force:
            sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( 'Clearing filter...' );")
        time.sleep(1)
        self.action._diag_sleepTime += 1
        # Now trigger off the true search
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( '%s' );" % searchString)
        for i in range(10):
            # Shouldn't need to do the following loop but
            # occasionally Selenuin appears to lose the label
            # and then using sel.visible() cause a crash
            for i in range(10):
                if not sel.is_element_present("list_processing"):
                    time.sleep(1)
            if not sel.is_visible('list_processing'):
                return True
            time.sleep(1)
            self.action._diag_sleepTime += 1
        return False

    def search(self, searchString, expected):
        # Perform a search using the search string, checking against the expected outcome
        # searchString: the value to search for
        # expected:     the expected result of the search
        # return        Boolean indicating the success of the search
        # side effect:  TestCase::fail() called in case of no search data being returned  
        sel = self.sel
        self.action._diag_sleepTime = 0
        self.action._diag_performCalls = 0
        found = False
        result = ""
        # perform the search it should work first time but, give it up to three attempts before giving up
        force = False
        for i in range (3):
            self.action._diag_performCalls += 1
            found = self._performSearch(searchString, force)
            if found:
                break
            force = True
        if not found:
            if self.action._diag:
                self.action._diagResults.write("%s\tFAILED\t%s\t%s\n" % (searchString, self.action._diag_sleepTime, self.action._diag_performCalls))
                self.fail("time out search didn't respond, whilst searching for %s" % searchString)
        else:
            if self.action._diag:
                self.action._diagResults.write("%s\tSUCCEEDED\t%s\t%s\n" % (searchString, self.action._diag_sleepTime, self.action._diag_performCalls))
        # The search has returned now read the results
        try:
            result = sel.get_text("//div[@id='table-container']")
        except:
            self.fail("No search data found, whilst searching for %s" % searchString)
        return expected in result
