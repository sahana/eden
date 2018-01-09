# -*- coding: utf-8 -*-

""" Sahana Eden Staff Module Automated Tests

    @copyright: 2011-2018 (c) Sahana Software Foundation
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
import os

from gluon import current
from tests.web2unittest import SeleniumUnitTest

class ImportStaff(SeleniumUnitTest):
    def test_hrm004_import_staff(self):
        """
            @case: hrm004
            @description: Import Staff
        """
        print "\n"

        import datetime
        from dateutil.relativedelta import relativedelta
        base_dir = os.path.join(os.getcwd(), "applications", current.request.application)
        file_path = os.path.join(base_dir, "modules", "tests", "staff", "staff.csv")

        #@ToDo: Move these into we2unittest
        today = datetime.date.today().strftime("%Y-%m-%d")
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now_1_day = (datetime.datetime.now() + relativedelta( days = +1 )).strftime("%Y-%m-%d %H:%M:%S")
        now_1_week = (datetime.date.today() + relativedelta( weeks = +1 )).strftime("%Y-%m-%d %H:%M:%S")

        # HRM004
        # Login, if not-already done so
        self.login(account="admin", nexturl="hrm/person/import?group=staff")
        self.browser.find_element_by_css_selector('input[type="file"]').send_keys(file_path)
        # Submit the form
        self.browser.find_element_by_css_selector('input[type="submit"]').click()
        # waiting for the page to load
        self.wait_for_page_to_load()
        # Importing
        self.browser.find_element_by_id("submitSelection").click()

    def test_hrm005_import_staff(self):
        """
            @case: hrm005
            @description: Import Staff
            This test removes any exsisting data before importing
        """
        print "\n"

        import datetime
        from dateutil.relativedelta import relativedelta
        base_dir = os.path.join(os.getcwd(), "applications", current.request.application)
        file_path = os.path.join(base_dir, "modules", "tests", "staff", "staff.csv")

        #@ToDo: Move these into we2unittest
        today = datetime.date.today().strftime("%Y-%m-%d")
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now_1_day = (datetime.datetime.now() + relativedelta( days = +1 )).strftime("%Y-%m-%d %H:%M:%S")
        now_1_week = (datetime.date.today() + relativedelta( weeks = +1 )).strftime("%Y-%m-%d %H:%M:%S")

        # HRM004
        # Login, if not-already done so
        self.login(account="admin", nexturl="hrm/person/import?group=staff")
        self.browser.find_element_by_css_selector('input[type="file"]').send_keys(file_path)
        self.browser.find_element_by_id("s3_import_upload_replace_option").click()
        # Submit the form
        self.browser.find_element_by_css_selector('input[type="submit"]').click()
        # waiting for the page to load
        self.wait_for_page_to_load()
        # Importing
        self.browser.find_element_by_id("submitSelection").click()




