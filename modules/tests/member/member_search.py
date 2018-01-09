# -*- coding: utf-8 -*-

""" Sahana Eden Member Search Module Automated Tests

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
import time
from gluon import current
from tests.web2unittest import SeleniumUnitTest
from selenium.webdriver.support.ui import WebDriverWait

class SearchMember(SeleniumUnitTest):

    def start(self):
        print "\n"
        # Login, if not-already done so
        self.login(account="admin",
                   nexturl="member/membership/search?clear_opts=1")

    def advancedSearchTest(self, ids):
        self.clickLabel(ids)

        self.browser.find_element_by_xpath("//form[@class='advanced-form']"
                                           "//input[@type='submit']").click()
        time.sleep(1)

        # click label again to reset to original status
        self.clickLabel(ids)


    def clickLabel(self, ids):
        try:
            self.browser.find_element_by_link_text("Advanced Search").click()
            time.sleep(1)
        except:
            pass

        for id in ids:
            self.browser.find_element_by_xpath("//label[text()='" + id + "']").click()
            time.sleep(1)


    def compareRowCount(self, dbRowCount):
        """
            Get html table row count and compare against the db row count
        """

        browser = self.browser

        # Wait for datatables script to complete
        elem = WebDriverWait(browser, 30).until(
                    lambda driver: \
                           driver.find_element_by_id("datatable_length"))

        htmlRowCount = len(browser.find_elements_by_xpath("//*[@id='datatable']/tbody/tr"))

        successMsg = "DB row count (%s)" \
                     " matches the HTML table row count (%s)." % \
                     (dbRowCount, htmlRowCount)

        failMsg = "DB row count (%s)" \
                  " does not match the HTML table row count (%s)." % \
                   (dbRowCount, htmlRowCount)

        self.assertTrue(dbRowCount == htmlRowCount, failMsg)
        self.reporter(successMsg)


    def test_mem004_01_member_search_simple(self):
        #return
        """
            @case: mem004-01
            @description: Search Members - Simple Search
        """
        self.start()
        self.browser.find_element_by_id("membership_search_simple").clear()
        self.browser.find_element_by_id("membership_search_simple").send_keys("mar")
        self.browser.find_element_by_css_selector("input[type=\"submit\"]").click()

        member = current.s3db["member_membership"]
        person = current.s3db["pr_person"]
        dbRowCount = current.db((member.deleted != 'T') & \
                                (member.person_id == person.id) & \
                                ((person.first_name.like('%mar%')) | \
                                 (person.middle_name.like('%mar%')) | \
                                 (person.last_name.like('%mar%')))).count()
        self.compareRowCount(dbRowCount)


    def test_mem004_02_member_search_advance_by_Paid(self):
        #return
        """
            @case: mem004-03
            @description: Search Members - Advanced Search by paid/expired/overdue
        """
        self.start()
        self.advancedSearchTest(["expired","paid"])
        member = current.s3db["member_membership"]
        rows = current.db((member.deleted != 'T')).select()
        dbRowCount = 0
        for row in rows:
            if row.paid() == "expired" or row.paid() == "paid" :
                dbRowCount = dbRowCount + 1
        self.compareRowCount(dbRowCount)


    def test_mem004_03_member_search_advance_by_Organisation(self):
        #return
        """
            @case: mem004-03
            @description: Search Members - Advanced Search by Organisation
        """
        self.start()
        self.advancedSearchTest(["Timor-Leste Red Cross Society (Cruz Vermelha de Timor-Leste)"])
        member = current.s3db["member_membership"]
        org = current.s3db["org_organisation"]
        dbRowCount = current.db((member.deleted != True) & (member.organisation_id == org.id) &
                                (org.name == 'Timor-Leste Red Cross Society (Cruz Vermelha de Timor-Leste)')).count()
        self.compareRowCount(dbRowCount)


    def test_mem004_04_member_search_advance_by_Country(self):
        #return
        """
            @case: mem004-04
            @description: Search Members - Advanced Search by Country
        """
        self.start()
        self.advancedSearchTest(["Timor-Leste"])
        member = current.s3db["member_membership"]
        loc = current.s3db["gis_location"]
        dbRowCount = current.db((member.deleted != 'T') & (member.location_id == loc.id) & (loc.L0 == 'Timor-Leste')).count()
        self.compareRowCount(dbRowCount)


    def test_mem004_05_member_search_advance_by_State_Province(self):
        #return
        """
            @case: mem004-05
            @description: Search Members - Advanced Search by State / Province
        """
        self.start()
        self.advancedSearchTest(["Baucau","Ermera"])
        member = current.s3db["member_membership"]
        loc = current.s3db["gis_location"]
        dbRowCount = current.db((member.deleted != 'T') & (member.location_id == loc.id) & ( (loc.L1 == 'Baucau') | (loc.L1 == 'Ermera') )).count()
        self.compareRowCount(dbRowCount)


    def test_mem004_06_member_search_advance_by_County_District(self):
        #return
        """
            @case: mem004-06
            @description: Search Members - Advanced Search by County / District
        """
        self.start()
        self.advancedSearchTest(["Laga"])
        member = current.s3db["member_membership"]
        loc = current.s3db["gis_location"]
        dbRowCount = current.db((member.deleted != 'T') & (member.location_id == loc.id) & (loc.L2 == 'Laga')).count()
        self.compareRowCount(dbRowCount)


    def test_mem004_07_member_search_advance_by_City_Town_Village(self):
        #return
        """
            @case: mem004-07
            @description: Search Members - Advanced Search by City / Town / Village
        """
        self.start()
        self.advancedSearchTest(["Lour","Tequino Mata"])
        member = current.s3db["member_membership"]
        loc = current.s3db["gis_location"]
        dbRowCount = current.db((member.deleted != 'T') & (member.location_id == loc.id) & ( (loc.L3 == 'Lour') | (loc.L3 == 'Tequino Mata') )).count()
        self.compareRowCount(dbRowCount)

