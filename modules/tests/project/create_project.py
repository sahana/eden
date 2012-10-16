# -*- coding: utf-8 -*-

""" Sahana Eden Module Automated Tests - PROJECT001 Create Project

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

class CreateProject(SeleniumUnitTest):
    def test_project001_create_project(self):
        """
            @case: Project001
            @description:
            
            * Create Project
            * Create Project Organisation 
            * Create Project Community
            * Create Project Beneficiary
            
            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """
        print "\n"

        # Login, if not-already done so
        self.login(account="admin", nexturl="project/project/create")
        
        self.create("project_project", 
                    [("organisation_id", 
                      "International Federation of Red Cross and Red Crescent Societies (IFRC)", 
                      "option"),
                     ( "name",
                       "Community Strengthening through Dance" ),
                     ( "comments",
                       "Host National Society")
                    ]
                   )

#        # Show Add Form
#        self.browser.find_element_by_id("show-add-btn").click()
#        
#        self.create("project_organisation", 
#                    [( "organisation_id",
#                       "New Zealand Red Cross",
#                       "autocomplete"),
#                     ( "role",
#                       "Donor",
#                       "option"),
#                     ( "amount",
#                       "1000"),
#                     ( "currency",
#                       "USD"),
#                     ( "comments",
#                       "International Donation")
#                     ]
#                     )

        self.browser.find_element_by_id("rheader_tab_location").click()

        self.create("project_location", 
                    [( "location_id",
                       "Aileu Vila",
                       "autocomplete"),
                     # If using LocationSelector:
                     #( "L0",
                     #  "Timor-Leste",
                     #  "gis_location" ),
                     #( "L1",
                     #  "Aileu",
                     #  "gis_location"),
                     #( "L2",
                     #  "Aileu Vila",
                     #  "gis_location"),
                     #( "L3",
                     #  "Saboria", #"Aisirimou"
                     #  "gis_location"),
                     #( "L4",
                     #  "Aileu",
                     #  "gis_location"),
                     #( "lat",
                     #  "0",
                     #  "gis_location"),
                     #( "lon",
                     #  "0",
                     #  "gis_location")
                     # @ToDo: Activities - Community Organisation, Contingency Planning, Logistics
                     ]
                     )

        self.create("project_beneficiary", 
                    [( "parameter_id",
                       "Teachers",
                       "option"),
                     ( "value",
                       "100"),
                     ( "comments",
                       "Primary Beneficiary")
                     ]
                     )
        
        # Show Add Form
        self.browser.find_element_by_id("show-add-btn").click()
        
        self.create("project_beneficiary", 
                    [( "parameter_id",
                       "Pupils",
                       "option"),
                     ( "value",
                       "1000"),
                     ( "comments",
                       "Secondary Beneficiary")
                     ]
                     )