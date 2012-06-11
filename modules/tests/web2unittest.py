import unittest

# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys

from gluon import current

from s3 import s3_debug

from tests import *

# =============================================================================
class Web2UnitTest(unittest.TestCase):
    """ Web2Py Unit Test """

    def __init__(self,
                 methodName="runTest"):
        unittest.TestCase.__init__(self, methodName)
        #current should always be looked up from gluon.current
        #self.current = current
        self.config = current.test_config
        self.browser = self.config.browser
        self.app = current.request.application
        self.url = self.config.url
        self.user = "admin"

# =============================================================================
class SeleniumUnitTest(Web2UnitTest):
    """ Selenium Unit Test """

    # -------------------------------------------------------------------------
    def login(self, account=None, nexturl=None):

        if account == None:
            account = self.user
        login(account, nexturl)

    # -------------------------------------------------------------------------
    def getRows (self, table, data, dbcallback):
        """
            Get a copy of all the records that match the data passed in
            this can be modified by the callback function
        """

        query = (table.deleted == "F")
        for details in data:
            query = query & (table[details[0]] == details[1])
        rows = current.db(query).select(orderby=~table.id)
        if rows == None:
            rows = []
        if dbcallback:
            rows = dbcallback(table, data, rows)
        return rows

    # -------------------------------------------------------------------------
    def create(self,
               tablename,
               data,
               success = True,
               dbcallback = None
              ):
        """
            Generic method to create a record from the data passed in

            @param tablename: The table where the record belongs
            @param data: The data that is to be inserted
            @param success: The expectation that this create will succeed
            @param dbcallback: Used by getRows to return extra data from
                               the database before & after the create

            This will return a dictionary of rows before and after the create
        """

        browser = self.browser
        result = {}
        id_data = []
        table = current.s3db[tablename]
        # Fill in the Form
        for details in data:
            el_id = "%s_%s" % (tablename, details[0])
            el_value = details[1]
            if len(details) == 3:
                el_type = details[2]
                if el_type == "option":
                    el = browser.find_element_by_id(el_id)
                    for option in el.find_elements_by_tag_name("option"):
                        if option.text == el_value:
                            option.click()
                            raw_value = option.get_attribute("value")
                            try:
                                raw_value = int(raw_value)
                            except:
                                pass
                            break
                elif el_type == "autocomplete":
                    raw_value = self.w_autocomplete(el_value,
                                                    el_id,
                                                   )
                elif el_type == "inv_widget":
                    raw_value = self.w_inv_item_select(el_value,
                                                       tablename,
                                                       details[0],
                                                      )
                elif el_type == "supply_widget":
                    raw_value = self.w_supply_select(el_value,
                                                     tablename,
                                                     details[0],
                                                    )
                elif el_type == "gis_location":
                    self.w_gis_location(el_value,
                                        details[0],
                                       )
                    raw_value = None
                #@ToDp: Fix this statement:
                #else:
                #    raise "Invalid element type"
                
            else:
                # Normal Input field
                el = browser.find_element_by_id(el_id)
                el.send_keys(el_value)
                raw_value = el_value

            if raw_value:
                # Use the raw value to check that the record was added succesfully
                id_data.append([details[0], raw_value])

        result["before"] = self.getRows(table, id_data, dbcallback)
        # Submit the Form
        browser.find_element_by_css_selector("input[type='submit']").click()
        # Check & Report the results
        confirm = True
        try:
            elem = browser.find_element_by_xpath("//div[@class='confirmation']")
            s3_debug(elem.text)
        except NoSuchElementException:
            confirm = False
        self.assertTrue(confirm == success,
                        "Unexpected create success of %s" % confirm)
        result["after"] = self.getRows(table, id_data, dbcallback)
        successMsg = "Record added to database"
        failMsg = "Record not added to database"
        if success:
            self.assertTrue((len(result["after"]) - len(result["before"])) == 1,
                            failMsg)
            s3_debug(successMsg)
        else:
            self.assertTrue((len(result["after"]) == len(result["before"])),
                            successMsg)
            s3_debug(failMsg)
        return result

    # -------------------------------------------------------------------------
    def dt_filter(self,
                  search_string = " ",
                  forceClear = True,
                  quiet = True):

        return dt_filter(search_string, forceClear, quiet)

    # -------------------------------------------------------------------------
    def dt_row_cnt(self,
                   check = (),
                   quiet = True):

        return dt_row_cnt(check, quiet, self)

    # -------------------------------------------------------------------------
    def dt_data(self,
                row_list = None,
                add_header = False):

        return dt_data(row_list, add_header)

    # -------------------------------------------------------------------------
    def dt_find(self,
                search = "",
                row = None,
                column = None,
                cellList = None,
                tableID = "list",
                first = False,
               ):

        return dt_find(search, row, column, cellList, tableID, first)

    # -------------------------------------------------------------------------
    def dt_links(self,
                 row = 1,
                 tableID = "list",
                 quiet = True
                ):

        return dt_links(row, tableID, quiet)

    # -------------------------------------------------------------------------
    def dt_action(self,
                  row = 1,
                  action = None,
                  column = 1,
                  tableID = "list",
                 ):

        return dt_action(row, action, column, tableID)

    # -------------------------------------------------------------------------
    def w_autocomplete(self,
                       search,
                       autocomplete,
                       needle = None,
                       quiet = True,
                      ):

        return w_autocomplete(search, autocomplete, needle, quiet)

    # -------------------------------------------------------------------------
    def w_inv_item_select(self,
                          item_repr,
                          tablename,
                          field,
                          quiet = True,
                         ):

        return w_inv_item_select(item_repr, tablename, field, quiet)

    # -------------------------------------------------------------------------
    def w_gis_location(self,
                      item_repr,
                      field,
                      quiet = True,
                     ):

        return w_gis_location(item_repr, field, quiet)
    
    # -------------------------------------------------------------------------
    def w_supply_select(self,
                       item_repr,
                       tablename,
                       field,
                       quiet = True,
                      ):

        return w_supply_select(item_repr, tablename, field, quiet)

# END =========================================================================
