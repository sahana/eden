# -*- coding: utf-8 -*-

""" Sahana Eden Staff Search Module Automated Tests

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

from tests.web2unittest import SeleniumUnitTest

class SearchStaff(SeleniumUnitTest):
    def test_hrm002_search_staff_simple(self):
        """
            @case: hrm002
            @description: Search Staff - Simple Search
        """
        print "\n"

        self.login(account="admin", nexturl="hrm/staff/search")

        self.browser.find_element_by_id("human_resource_search_simple").clear()
        self.browser.find_element_by_id("human_resource_search_simple").send_keys("Mariana")
        self.browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        
    def test_hrm002_search_staff_advance_by_organisation(self):
        """
            @case: hrm002
            @description: Advanced Search Staff by Organisation (Timor-Leste Red Cross Society (CVTL)
        """
        print "\n"
        self.login(account="admin", nexturl="hrm/staff/search")
        self.browser.find_element_by_link_text("Advanced Search").click()
        #self.browser.find_element_by_id("id-human_resource_search_org-3").click()
        
        self.browser.find_element_by_xpath("//label[contains(text(),'Timor-Leste Red Cross Society')]").click()
#        "Timor-Leste Red Cross Society"
        self.browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        
    def test_hrm002_search_staff_advance_by_stateProvince(self):
        """
            @case: hrm002
            @description: Advanced Search Staff by State/Province (Dili & Viqueque)
        """
        print "\n"
        self.login(account="admin", nexturl="hrm/staff/search")
        self.browser.find_element_by_link_text("Advanced Search").click()
        self.browser.find_element_by_id("id-human_resource_search_L1-1").click()
        self.browser.find_element_by_id("id-human_resource_search_L1-5").click()
        self.browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        
    def test_hrm002_search_staff_advance_by_district(self):
        """
            @case: hrm002
            @description: Advanced Search Staff by County/District (Ainaro & Viqueque)
        """
        print "\n"
        self.login(account="admin", nexturl="hrm/staff/search")
        self.browser.find_element_by_link_text("Advanced Search").click()
        self.browser.find_element_by_id("id-human_resource_search_L2-0").click()
        self.browser.find_element_by_id("id-human_resource_search_L2-5").click()
        self.browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        
    def test_hrm002_search_staff_advance_by_facility(self):
        """
            @case: hrm002
            @description: Advanced Search Staff by Facility (Lospalos Branch Office (Office))
        """
        print "\n"
        self.login(account="admin", nexturl="hrm/staff/search")
        self.browser.find_element_by_link_text("Advanced Search").click()
        self.browser.find_element_by_id("id-human_resource_search_site-6").click()
        self.browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        
    def test_hrm002_search_staff_advance_by_training(self):
        """
            @case: hrm002
            @description: Advanced Search Staff by Training (Basics of First Aid)
        """
        print "\n"
        self.login(account="admin", nexturl="hrm/staff/search")
        self.browser.find_element_by_link_text("Advanced Search").click()
        self.browser.find_element_by_id("id-human_resource_search_training-2").click()
        self.browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        
    def test_hrm002_search_staff_advance_by_training_and_facility(self):
        """
            @case: hrm002
            @description: Advanced Search Staff by Training (Basics of First Aid)
        """
        print "\n"
        self.login(account="admin", nexturl="hrm/staff/search")
        self.browser.find_element_by_link_text("Advanced Search").click()
        self.browser.find_element_by_id("id-human_resource_search_site-6").click()
        self.browser.find_element_by_id("id-human_resource_search_training-2").click()
        self.browser.find_element_by_css_selector("input[type=\"submit\"]").click()
        