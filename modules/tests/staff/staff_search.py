# -*- coding: utf-8 -*-

""" Sahana Eden Member Search Module Automated Tests

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
import time
from gluon import current
from tests.web2unittest import SeleniumUnitTest

class SearchStaff(SeleniumUnitTest):

    def start(self):
        print "\n"
        # Login, if not-already done so
        self.login(account="admin", nexturl="hrm/staff/search?clear_opts=1")

    def advancedSearchTest(self, ids):
        self.clickLabel(ids)

        self.browser.find_element_by_xpath("//form[@class='advanced-form']/table/tbody/tr[11]/td[2]/input[@type='submit']").click()
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
        htmlRowCount = len(self.browser.find_elements_by_xpath("//*[@id='list']/tbody/tr"));
        successMsg = "DB row count (" + str(dbRowCount) + ") matches the HTML table row count (" + str(htmlRowCount) + ")." 
        failMsg = "DB row count (" + str(dbRowCount) + ") does not match the HTML table row count (" + str(htmlRowCount) + ")." 
        self.assertTrue(dbRowCount == htmlRowCount, failMsg)
        self.reporter(successMsg)


    def test_hrm002_01_hrm_search_simple(self):
        #return 
        """
            @case: hrm002-01
            @description: Search Members - Simple Search
        """
        self.start()
        self.browser.find_element_by_id("human_resource_search_simple").clear()
        self.browser.find_element_by_id("human_resource_search_simple").send_keys("mem")
        self.browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        time.sleep(1)        
        h = current.s3db["hrm_human_resource"]
        p = current.s3db["pr_person"]
        dbRowCount = current.db((h.deleted != 'T') & (h.type == 1) & (h.person_id == p.id) & ( (p.first_name.like('%mem%')) | (p.middle_name.like('%mem%')) | (p.last_name.like('%mem%')) )).count()
        self.compareRowCount(dbRowCount)
               
               
    def test_hrm002_02_hrm_search_advance_by_Organization(self):
        #return 
        """
            @case: hrm002-02
            @description: Search Members - Advanced Search by Organization
        """
        self.start()
        self.advancedSearchTest(["Finnish Red Cross (FRC)",])
        h = current.s3db["hrm_human_resource"]
        o = current.s3db["org_organisation"]
        dbRowCount = current.db((h.deleted != 'T') & (h.type == 1) & (h.organisation_id == o.id) & (o.name == 'Finnish Red Cross')).count()
        self.compareRowCount(dbRowCount)

      
    def test_hrm002_03_hrm_search_advance_by_Facility(self):
        #return 
        """
            @case: hrm002-03
            @description: Search Members - Advanced Search by Facility
        """
        self.start()
        self.advancedSearchTest(["AP Zone (Office)", "Victoria Branch Office (Office)"])
        h = current.s3db["hrm_human_resource"]
        ofc = current.s3db["org_office"]
        dbRowCount = current.db((h.deleted != 'T') & (h.type == 1) & (h.site_id == ofc.site_id) & ( (ofc.name == 'AP Zone') | (ofc.name == 'Victoria Branch Office') )).count()
        self.compareRowCount(dbRowCount)
        

    def test_hrm002_04_hrm_search_advance_by_Training(self):
        #return 
        """
            @case: hrm002-04
            @description: Search Members - Advanced Search by Training
        """
        self.start()
        self.advancedSearchTest(["Basics of First Aid",])
        h = current.s3db["hrm_human_resource"]
        p = current.s3db["pr_person"]
        t = current.s3db["hrm_training"]
        c = current.s3db["hrm_course"]
        dbRowCount = len(current.db((h.deleted != 'T') & (h.type == 1) & (h.person_id == p.id) & (t.person_id == p.id) & (t.course_id == c.id) &  (c.name == 'Basics of First Aid') ).select(h.id, distinct=True))
        self.compareRowCount(dbRowCount)

        
                       