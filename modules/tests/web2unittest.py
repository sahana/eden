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
from unittest.case import SkipTest, _ExpectedFailure, _UnexpectedSuccess

from dateutil.relativedelta import relativedelta
from selenium.common.exceptions import NoSuchElementException

from gluon import current

from s3.s3utils import s3_unicode
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
    def s3_debug(self, message, value=None):
        """
           Provide an easy, safe, systematic way of handling Debug output
           (stdout/stderr are normally redirected within tests)
        """

        # Restore stderr
        stderr_redirector = sys.stderr
        sys.stderr = self._resultForDoCleanups.stderr0

        output = s3_unicode(message)
        if value:
            output = "%s: %s" % (output, s3_unicode(value))

        try:
            print >> sys.stderr, output
        except:
            # Unicode string
            print >> sys.stderr, "Debug crashed"

        # Redirect stderr back again
        sys.stderr = stderr_redirector

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
    def search(self, form_type, results_expected, fields, row_count, **kwargs):
        '''
        Generic method to test the validity of search results.

        @param form_type: This can either be search.simple_form or
                          search.advanced_form

        @param results_expected: Are results expected?

        @param fields: See the `fields` function.

        @param row_count: Expected row count

        Keyword arguments:

        These let you specify the kinds of checks to perform on the resulting
        datatable. Here are some of the options:

        1. data - You can pass in your own function here that receives the data
        from the results table as an argument. Return true if your check is
        successful and false otherwise. This directly corresponds to the
        'dt_data' function.

        2. manual_check - You can pass in your own function here, and it'll
        receive this instance as an argument. This can be used for all other
        kinds of checks.

        3. match_row - You can use this to match a series of values to a row in
        the result data table. The first value must be the index of the row to
        match against.

        4. match_column - You can use this to match a series of values to a
        column in the result data table. The first value must be the index of
        the row to match against.
        '''

        browser = self.browser

        browser.find_element_by_xpath("//a[text()='Clear']").click()

        try:
            if form_type == self.search.advanced_form:
                link = browser.find_element_by_xpath("//a[@class='action-lnk advanced-lnk']")
            elif form_type == self.search.simple_form:
                link = browser.find_element_by_xpath("//a[@class='action-lnk simple-lnk']")
        except NoSuchElementException:
            # There might be no link if one of the forms is the only option
            link = None

        if link and link.is_displayed():
            link.click()

        time.sleep(1)

        self.fill_fields(fields)

        browser.find_element_by_name(("simple_submit", "advanced_submit")[form_type]).click()

        time.sleep(1)

        if results_expected == True:
            self.assertFalse(
            browser.find_element_by_id("table-container").text
                    == "No Records Found",
                "No results found, when results expected.")
        else:
            return

        # We"re done entering and submitting data; now we need to check if the
        # results produced are valid.
        htmlRowCount = self.dt_row_cnt()[2]
        successMsg = "DB row count (" + str(row_count) + ") matches the HTML datatable row count (" + str(htmlRowCount) + ")." 
        failMsg = "DB row count (" + str(row_count) + ") does not match the HTML datatable row count (" + str(htmlRowCount) + ")." 
        self.assertTrue(row_count == htmlRowCount, failMsg)
        self.reporter(successMsg)

        if "data" in kwargs.keys():
            self.assertTrue(bool(kwargs["data"](self.dt_data())),
                "Data verification failed.")

        if "manual_check" in kwargs.keys():
            self.assertTrue(bool(kwargs["manual_check"](self)),
                "Manual checks failed.")

        if "match_row" in kwargs.keys():
            data = self.dt_data(row_list=(kwargs["match_row"][0]))
            kwargs["match_row"] = kwargs["match_row"][1:]
            for a, b in zip(kwargs["match_row"], data):
                self.assertTrue(a == b,
                    "Row match failed.")

        if "match_column" in kwargs.keys():
            column_index = kwargs["match_column"][0]
            kwargs["match_column"] = kwargs["match_column"][1:]
            shown_items = [dt_data_item(column=column_index,
            row=r) for r in xrange(1, len(kwargs["match_column"]) + 1)]
            for item in kwargs["match_column"]:
                self.assertTrue(item in shown_items)

        return self.dt_data()

    search.simple_form = 0
    search.advanced_form = 1

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

        settings = current.deployment_settings
        date_format = str(settings.get_L10n_date_format())
        datetime_format = str(settings.get_L10n_datetime_format())
        # If a confirmation is shown then clear it so that it doesn't give a false positive later
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
                if el_type == "automatic":
                    try:
                        browser.find_element_by_id("dummy_"+el_id)
                        if len(details) >= 5:
                            needle = details[4]
                        else:
                            needle = el_value
                        raw_value = self.w_autocomplete(el_value,
                                                        el_id,
                                                        needle,
                                                        )
                    except NoSuchElementException:
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
                        
                elif el_type == "option":
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
                        self.assertTrue(raw_value, "%s option cannot be found in %s" % (el_value, el_id))
                elif el_type == "checkbox":
                    for value in el_value:
                        self.browser.find_element_by_xpath("//label[contains(text(),'%s')]" % value).click()
                        # @ToDo: Add value to id_data to check for create function
                elif el_type == "autocomplete":
                    if len(details) >= 5:
                        needle = details[4]
                    else:
                        needle = el_value
                    raw_value = self.w_autocomplete(el_value,
                                                    el_id,
                                                    needle,
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
        successMsg = "Records added to database: %s" %id_data
        failMsg = "Records not added to database %s" %id_data
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
    def select_option(self, select_elem, option_label):
        if select_elem:
            select_elem.click()
            found = False
            for option in select_elem.find_elements_by_tag_name("option"):
                if option.text == option_label:
                    option.click()
                    found = True
                    return True
            if not found:
                return False

    # -------------------------------------------------------------------------
    class InvalidReportOrGroupException(Exception):
        pass

    # -------------------------------------------------------------------------
    def report(self, fields, report_of, grouped_by, report_fact, *args, **kwargs):
        browser = self.browser
        show_totals = True

        browser.find_element_by_xpath("//a[text()='Reset all filters']").click()

        if fields:
            self.fill_fields(fields)

        # Open the report options fieldset:
        report_options = browser.find_element_by_css_selector("#report_options button")
        if report_options.is_displayed():
            report_options.click()

        # Select the item to make a report of:
        rows_select = browser.find_element_by_id("report-rows")
        if not self.select_option(rows_select, report_of):
            raise self.InvalidReportOrGroupException()

        # Select the value to group by:
        cols_select = browser.find_element_by_id("report-cols")
        if not self.select_option(cols_select, grouped_by):
            raise self.InvalidReportOrGroupException()

        # Select the value to base the report on
        if report_fact:
            fact_select = browser.find_element_by_id("report-fact")
            if not self.select_option(fact_select, report_fact):
                raise self.InvalidReportOrGroupException()

        browser.find_element_by_xpath("//input[@type='submit']").click()

        time.sleep(1)

        # Now, check the generated report:
        for check in args:
            row = self.dt_find(check[0])
            if not row:
                raise self.InvalidReportOrGroupException()
            else:
                row = row[0][0]
            col = 1
            e = browser.find_element_by_xpath(".//*[@id='list']/thead/tr[2]/th[1]")
            while True:
                if e.text.strip() == check[1]:
                    break
                else:
                    col += 1
                    try:
                        e = browser.find_element_by_xpath(
                            ".//*[@id='list']/thead/tr[2]/th[{0}]".format(col))
                    except NoSuchElementException:
                        raise self.InvalidReportOrGroupException()

            import collections
            if isinstance(check[2], collections.Iterable):
                td = browser.find_element_by_xpath(
                    ".//*[@id='list']/tbody/tr[{0}]/td[{1}]".format(row,
                        col))
                shown_items = [item.text for item in td.find_elements_by_tag_name("li")]

                for item in check[2]:
                    self.assertTrue(item in shown_items,
                        u"Report check failed.")
            else:
                self.assertTrue(str(dt_data_item(row, col)) == str(check[2]),
                "Report check failed.")

        if 'row_count' in kwargs:
            self.assertTrue(kwargs['row_count'] == len(browser.find_elements_by_xpath(
                "//table[@id='list']/tbody/tr")))

    # -------------------------------------------------------------------------
    def fill_fields(self, fields):
        """
        Fills form fields with values.

        @param fields A list of dicts that specifies the fields to fill.
        """

        browser = self.browser

        for field_spec in fields:
            value = field_spec["value"]

            for query_type in ("xpath", "class", "name", "id"):
                if query_type in field_spec.keys():
                    field = getattr(browser, 'find_element_by_' + query_type)
                    field = field(field_spec[query_type])

            if ("label" in field_spec) and ("name" in field_spec):
                xpath = "//*[contains(@for,'{name}') and contains(text(), '{label}')]".format(**field_spec)
                field = browser.find_element_by_xpath(xpath)
            elif "label" in field_spec:
                field = browser.find_element_by_xpath(
                    "//label[contains(text(),'{label}')]".format(**field_spec))

            if isinstance(value, basestring):  # Text inputs
                field.send_keys(value)
            elif isinstance(value, bool) and value:  # Checkboxes and radios
                field.click()

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
    def dt_data_item(self,
                     row = 1,
                     column = 1,
                     tableID = "list",
                     ):
        return dt_data_item(row, column, tableID)

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

        config = current.test_config
        browser = config.browser

        autocomplete_id = "dummy_%s" % autocomplete
        throbber_id = "dummy_%s_throbber" % autocomplete
        if needle == None:
            needle = search

        elem = browser.find_element_by_id(autocomplete_id)
        elem.clear()
        elem.send_keys(search)
        # Give time for the throbber to appear
        time.sleep(1)
        # Now wait for throbber to close
        giveup = 0.0
        sleeptime = 0.2
        while browser.find_element_by_id(throbber_id).is_displayed():
            time.sleep(sleeptime)
            giveup += sleeptime
            if giveup > 60:
                return False
        # Throbber has closed and data was found, return
        for i in range(10):
            # For each autocomplete on the form the menu will have an id starting from 0
            automenu = 0
            try:
                menu = browser.find_element_by_id("ui-menu-%s" % automenu)
            except:
                menu = None
            while menu:
                # Try and get the value directly
                menu_items = menu.text.splitlines()
                autoitem = 0
                for linkText in menu_items:
                    if needle in linkText:
                        # Found the text, now need to click on it to get the db id
                        menuitem = browser.find_element_by_id("ui-menu-%s-%s" % (automenu,autoitem))
                        menuitem.click()
                        time.sleep(15)
                        # The id is copied into the value attribute so use that
                        db_id = browser.find_element_by_id(autocomplete)
                        value = db_id.get_attribute("value")
                        if value:
                            return int(value)
                        else:
                            return False
                    autoitem += 1
                automenu += 1
                try:
                    menu = browser.find_element_by_id("ui-menu-%s" % automenu)
                except:
                    menu = None
                # end of looping through each autocomplete menu
            time.sleep(sleeptime)

    # -------------------------------------------------------------------------
    def w_inv_item_select(self,
                          item_repr,
                          tablename,
                          field,
                          quiet = True,
                          ):

        config = current.test_config
        browser = config.browser

        el_id = "%s_%s" % (tablename, field)
        el = browser.find_element_by_id(el_id)
        raw_value = None
        for option in el.find_elements_by_tag_name("option"):
            if option.text == item_repr:
                option.click()
                raw_value = int(option.get_attribute("value"))
                break
        # Now wait for the pack_item to be populated
        el_id = "%s_%s" % (tablename, "item_pack_id")
        _autocomple_finish(el_id, browser)
        return raw_value

    # -------------------------------------------------------------------------
    def w_gis_location(self,
                       item_repr,
                       field,
                       quiet = True,
                       ):

        config = current.test_config
        browser = config.browser

        if field == "L0":
            el_id = "gis_location_%s" % field
            el = browser.find_element_by_id(el_id)
            for option in el.find_elements_by_tag_name("option"):
                if option.text == item_repr:
                    option.click()
                    raw_value = int(option.get_attribute("value"))
                    break
        elif field[0] == "L":
            # @todo make this a proper autocomplete widget (select or add)
            el_id = "gis_location_%s_ac" % field
            el = browser.find_element_by_id(el_id)
            el.send_keys(item_repr)
            raw_value = None # can't get the id at the moment (see the todo)
        else:
            el_id = "gis_location_%s" % field
            el = browser.find_element_by_id(el_id)
            el.send_keys(item_repr)
            raw_value = item_repr
        return raw_value

    # -------------------------------------------------------------------------
    def w_supply_select(self,
                        item_repr,
                        tablename,
                        field,
                        quiet = True,
                        ):

        el_id = "%s_%s" % (tablename, field)
        raw_value = self.w_autocomplete(item_repr, el_id)
        # Now wait for the pack_item to be populated
        browser = current.test_config.browser
        el_id = "%s_%s" % (tablename, "item_pack_id")
        _autocomple_finish(el_id, browser)
        return raw_value

    # -------------------------------------------------------------------------
    def w_facility_select(self,
                          org_repr,
                          tablename,
                          field,
                          quiet = True,
                          ):

        el_id = "%s_%s" % (tablename, field)
        raw_value = self.w_autocomplete(item_repr, el_id)
        # Now wait for the pack_item to be populated
        browser = current.test_config.browser
        el_id = "%s_%s" % (tablename, "site_id")
        _autocomple_finish(el_id, browser)
        return raw_value

# =============================================================================
def _autocomple_finish(el_id, browser):
    """
        Helper function
    """

    giveup = 0.0
    sleeptime = 0.2
    el = browser.find_element_by_id(el_id)
    while giveup < 60:
        try:
            if el.find_elements_by_tag_name("option")[0].text != "":
                return
        except: # StaleElementReferenceException
            print "StaleElementReferenceException %s" % giveup
            el = browser.find_element_by_id(el_id)
        # The pack drop down hasn't been populated yet so sleep
        time.sleep(sleeptime)
        giveup += sleeptime

# END =========================================================================
