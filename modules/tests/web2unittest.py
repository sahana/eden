# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys

from gluon import current

from s3 import s3_debug

from tests import *

import unittest

class Web2UnitTest(unittest.TestCase):
    def __init__(self,
                 methodName='runTest',):
        unittest.TestCase.__init__(self, methodName)
        self.current = current
        self.config = current.test_config
        self.browser = self.config.browser
        self.url = self.config.url
        self.user = "normal"

class SeleniumUnitTest(Web2UnitTest):
    def login(self, user=None):
        if user == None:
            user = self.user
        login(user)

    def dt_filter(self,
                  search_string = " ",
                  forceClear = True,
                  quiet = True):
        return dt_filter(search_string, forceClear, quiet)

    def dt_row_cnt(self,
                   check = (),
                   quiet = True):
        return dt_row_cnt(check, quiet, self)

    def dt_data(self,
                row_list = None,
                add_header = False):
        return dt_data(row_list, add_header)

    def dt_find(search = "",
                row = None,
                column = None,
                cellList = None,
                tableID = "list",
                first = False,
               ):
        return dt_find(search, row, column, cellList, tableID, first)

    def dt_links(self,
                 row = 1,
                 tableID = "list",
                 quiet = True
                ):
        return dt_links(row, tableID, quiet)

    def dt_action(row = 1,
                  action = "Open",
                  column = 1,
                  tableID = "list",
                 ):
        return dt_action(row, action, column, tableID)

    def w_autocomplete(self,
                       search,
                       autocomplete,
                       needle = None,
                       quiet = True,
                      ):
        return w_autocomplete(search, autocomplete, needle, quiet)