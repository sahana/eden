""" Sahana Eden Test Framework

    @copyright: 2011-2012 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

import datetime
import sys
import time
import unittest

from dateutil.relativedelta import relativedelta
from selenium.common.exceptions import NoSuchElementException

from gluon import current

from s3.s3widgets import *

from tests.core import *

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
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    # -------------------------------------------------------------------------
    @staticmethod
    def today():
        return datetime.date.today().strftime("%Y-%m-%d")

    # -------------------------------------------------------------------------
    @staticmethod
    def now():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # -------------------------------------------------------------------------
    @staticmethod
    def now_1_day():
        return (datetime.datetime.now() + relativedelta( days = +1 )).strftime("%Y-%m-%d %H:%M:%S")

    # -------------------------------------------------------------------------
    @staticmethod
    def now_1_week():
        return (datetime.date.today() + relativedelta( weeks = +1 )).strftime("%Y-%m-%d %H:%M:%S")

    # -------------------------------------------------------------------------
    def reporter(self, msg, verbose_level = 1):
        if self.config.verbose >= verbose_level:
            print >> sys.stderr, msg

# =============================================================================
class SeleniumUnitTest(Web2UnitTest):
    """ Selenium Unit Test """

    # -------------------------------------------------------------------------
    def login(self, account=None, nexturl=None):

        if account == None:
            account = self.user
        login(self.reporter, account, nexturl)

    # -------------------------------------------------------------------------
    def getRows (self, table, data, dbcallback):
        """
            Get a copy of all the records that match the data passed in
            this can be modified by the callback function
        """

        query = (table.deleted != True)
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

        date_format = str(current.deployment_settings.get_L10n_date_format())
        datetime_format = str(current.deployment_settings.get_L10n_datetime_format())
        # if the logged in confirm is shown then try and clear it.
        try:
            elem = browser.find_element_by_xpath("//div[@class='confirmation']")
            elem.click()
        except:
            pass

        # Fill in the Form
        for details in data:
            el_id = "%s_%s" % (tablename, details[0])
            el_value = details[1]
            if len(details) >= 4:
                time.sleep(details[3])
            if len(details) >= 3:
                el_type = details[2]
                if el_type == "option":
                    el = browser.find_element_by_id(el_id)
                    raw_value = False
                    for option in el.find_elements_by_tag_name("option"):
                        if option.text == el_value:
                            option.click()
                            raw_value = option.get_attribute("value")
                            try:
                                raw_value = int(raw_value)
                            except:
                                pass
                            break
                    # Test that we have an id that can be used in the database
                    if el_value and el_value != "-":
                        self.assertTrue(raw_value,"%s option cannot be found in %s" % (el_value, el_id))
                elif el_type == "checkbox":
                    for value in el_value:
                        self.browser.find_element_by_xpath("//label[contains(text(),'%s')]" % value).click()
                        # @ToDo: Add value to id_data to check for create function
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
                elif el_type == "facility_widget":
                    raw_value = self.w_facility_select(el_value,
                                                       tablename,
                                                       details[0],
                                                      )
                elif el_type == "gis_location":
                    self.w_gis_location(el_value,
                                        details[0],
                                       )
                    raw_value = None
                else: # Embedded form fields
                    el_id = "%s_%s" % (el_type, details[0])
                    el = browser.find_element_by_id(el_id)
                    el.send_keys(el_value)
                    raw_value = None

            else:
                # Normal Input field
                el = browser.find_element_by_id(el_id)
                if isinstance(table[details[0]].widget, S3DateWidget):
                    el_value_date = datetime.datetime.strptime(el_value,"%Y-%m-%d")# %H:%M:%S")
                    el_value = el_value_date.strftime(date_format)
                    el.send_keys(el_value)
                    raw_value = el_value_date
                elif isinstance(table[details[0]].widget, S3DateTimeWidget):
                    el_value_datetime = datetime.datetime.strptime(el_value,"%Y-%m-%d %H:%M:%S")
                    el_value = el_value_datetime.strftime(datetime_format)
                    el.send_keys(el_value)
                    #raw_value = el_value_datetime
                    raw_value = el_value
                    # @ToDo: Fix hack to stop checking datetime field. This is because the field does not support data entry by key press
                    # Use the raw value to check that the record was added succesfully
                else:
                    el.clear()
                    el.send_keys(el_value)
                    raw_value = el_value

            if raw_value:
                id_data.append([details[0], raw_value])

        result["before"] = self.getRows(table, id_data, dbcallback)
        # Submit the Form
        submit_btn = browser.find_element_by_css_selector("input[type='submit']")
        submit_btn.click()
        # Check & Report the results
        confirm = True
        try:
            elem = browser.find_element_by_xpath("//div[@class='confirmation']")
            self.reporter(elem.text)
        except NoSuchElementException:
            confirm = False
        if (confirm != success):
            # Do we have a validation error?
            try:
                elem_error = browser.find_element_by_xpath("//div[@class='error']")
                if elem_error:
                    msg = "%s %s" % (elem_error.get_attribute("id"), elem_error.text)
                    self.reporter(msg)
            except NoSuchElementException:
                pass
        self.assertTrue(confirm == success,
                        "Unexpected %s to create record" %
                        (confirm and "success" or "failure"))
        result["after"] = self.getRows(table, id_data, dbcallback)
        successMsg = "Record added to database"
        failMsg = "Record not added to database"
        if success:
            self.assertTrue((len(result["after"]) - len(result["before"])) == 1,
                            failMsg)
            self.reporter(successMsg)
        else:
            self.assertTrue((len(result["after"]) == len(result["before"])),
                            successMsg)
            self.reporter(failMsg)
        return result

    # -------------------------------------------------------------------------
    def dt_filter(self,
                  search_string = " ",
                  forceClear = True,
                  quiet = True):

        return dt_filter(self.reporter, search_string, forceClear, quiet)

    # -------------------------------------------------------------------------
    def dt_row_cnt(self,
                   check = (),
                   quiet = True):

        return dt_row_cnt(self.reporter,check, quiet, self)

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

        return dt_links(self.reporter, row, tableID, quiet)

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

    # -------------------------------------------------------------------------
    def w_facility_select(self,
                          org_repr,
                          tablename,
                          field,
                          quiet = True,
                          ):

        return w_facility_select(org_repr, tablename, field, quiet)

# END =========================================================================
