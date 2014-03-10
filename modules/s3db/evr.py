# -*- coding: utf-8 -*-

""" Sahana Eden Evacuees Registry Model

    @copyright: 2012-13 (c) Sahana Software Foundation
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

__all__ = ["S3EVRCaseModel",
           "evr_rheader",
           "evr_AvailableShelters",
           ]

from gluon import *
from gluon.storage import Storage
from gluon.tools import callback
from ..s3 import *
from s3layouts import S3AddResourceLink  

# =============================================================================
class S3EVRCaseModel(S3Model):

    names = ["evr_case"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Case Data
        #
        tablename = "evr_case"
        table = self.define_table(tablename,
                                  self.pr_person_id(),
                                  Field("fiscal_code", "string",
                                        length=16,
                                        label=T("Fiscal Code"),
                                        comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Fiscal Code"),
                                                                T("Insert the fiscal code with no spaces"))),
                                        ),
                                  Field("birthplace"),
                                  s3_comments(),
                                  *s3_meta_fields())
        
        # If fiscal code is present, it's unique
        fiscal_code = current.db.evr_case.fiscal_code
        fiscal_code.requires = IS_EMPTY_OR(IS_NOT_IN_DB(current.db, fiscal_code))
                                  
        # ---------------------------------------------------------------------
        # Medical Details
        #

        # @todo: use string-codes for option fields for better
        #        maintainability/interoperability
        #
        evr_therapy_opts = {1: T("Vital Long-Term Medication"),
                            2: T("Dialysis"),
                            3: T("Chronic Oxygen Supply"),
                            4: T("Intermittend Ventilator Support"),
                            5: T("Ventilator Dependend"),
                            6: T("Cardiac Assist Device"),
                            }

        evr_allergy_opts = {1: T("Drug"),
                            2: T("Food"),
                            3: T("Olive Tree"),
                            4: T("Grass"),
                            5: T("Dust"),
                            6: T("Other"),
                            }

        evr_disability_opts = {1: T("Visually Impaired"),
                               2: T("Blind"),
                               3: T("Hearing-Impaired"),
                               4: T("Deaf"),
                               5: T("Deaf-Mute"),
                               6: T("Deaf-Blind"),
                               7: T("Aphasic"),
                               8: T("Mobility-Impaired"),
                               9: T("Paralysed"),
                               10: T("Amputated"),
                               11: T("Other Physical Disability"),
                               12: T("Mentally Disabled"),
                               }
                               
        evr_aids_appliances_opts = {1: ("Guide Dog"),
                                    2: ("Wheelchair"),
                                    3: ("Walking stick"),
                                    4: ("Crutch"),
                                    5: ("Tripod"),
                                    6: ("Artificial limb"),
                                    7: ("Catheter"),
                                    8: ("Sanity Napkin"),
                                    }

        def med_multiopt_field(fieldname, options, label=None):
            """ Simple generator for option fields """
            return Field(fieldname, "list:integer",
                         requires = IS_IN_SET(options, multiple = True),
                         represent = S3Represent(options = options,
                                                 multiple = True),
                         label = label,
                         widget = S3MultiSelectWidget(filter = False,
                                                      selectedList = 3,
                                                      noneSelectedText = "Select",
                                                     )
                         )
                         
        evr_source_opts =  {1: "Self",
                            2: "Mother",
                            3: "Father",
                            4: "Uncle",
                            5: "Grandfather",
                            6: "Grandmother",
                            7: "Official",
                            8: "Attendant",
                            9: "Neighbour",
                            10: "Teacher",
                            11: "Priest",
                            12: "Other",
                            }

        tablename = "evr_medical_details"
        table = self.define_table(tablename,
                                  self.pr_person_id(),
                                  med_multiopt_field("therapy",
                                                     evr_therapy_opts,
                                                     label = T("Therapy"),
                                                    ),
                                                    
                                  Field("pregnancy", "boolean",
                                        label=T("Pregnancy"),
                                        ),
                                  med_multiopt_field("allergy",
                                                     evr_allergy_opts,
                                                     label = T("Allergies"),
                                                    ),
                                  Field("diet",
                                        label=T("Diet"),
                                        ),
                                  med_multiopt_field("disability",
                                                     evr_disability_opts,
                                                     label = T("Disabilities"),
                                                    ),
                                  Field("self_sufficient", "boolean",
                                        label=T("Self-Sufficient"),
                                        ),
                                  med_multiopt_field("aids_appliances",
                                                     evr_aids_appliances_opts,
                                                     label = T("Aids and Appliances"),
                                                    ),
                                  Field("declared_by_name",
                                        label = T("Declared by (Name)"),
                                        ),
                                  Field("declared_by_relationship", "integer",
                                        requires = IS_IN_SET(evr_source_opts,
                                                            zero=None),
                                        label = T("Declared by (Relationship)"),
                                        represent = S3Represent(options=evr_source_opts),
                                        ),
                                  Field("declared_by_phone",
                                        label=T("Declared by (Phone)"),
                                        requires = IS_NULL_OR(IS_PHONE_NUMBER()),
                                        ),
                                  Field("declared_by_email",
                                        label=T("Declared by (Email)"),
                                        requires = IS_NULL_OR(IS_EMAIL()),
                                        ),
                                  Field("has_attendant", "boolean",
                                        label=T("Has Attendand"),
                                        ),
                                  Field("attendant_name",
                                        label=T("Attendant (Name)"),
                                        ),
                                  Field("attendant_phone",
                                        label=T("Attendant (Phone)"),
                                        requires = IS_NULL_OR(IS_PHONE_NUMBER()),
                                        ),
                                  Field("attendant_email",
                                        label=T("Attendant (Email)"),
                                        requires = IS_NULL_OR(IS_EMAIL()),
                                        ),
                                  s3_comments(),
                                  *s3_meta_fields())
                                  
        # ---------------------------------------------------------------------
        # Socio-economic Background
        #
        tablename = "evr_background"
        table = self.define_table(tablename,
                                  self.pr_person_id(),
                                  Field("legal_measure", "boolean",
                                        label=T("Legal measure / Home warrant")
                                        ),
                                  Field("social_welfare", "boolean",
                                        label=T("Social Welfare")
                                        ),
                                  Field("home_help", "boolean",
                                        label=T("Home Help")
                                        ),
                                  Field("interpreter" , "boolean",
                                        label=T("Interpreter / Cultural Mediator")
                                        ),
                                  Field("distance_from_shelter", "integer",
                                        label=T("Distance from Shelter (km)")
                                        ),
                                  Field("job_lost_by_event", "boolean",
                                        label=T("Job lost by event")
                                        ),
                                  Field("car_available", "boolean",
                                        label=T("Car available")
                                        ),
                                  s3_comments(),
                                  *s3_meta_fields())

# =============================================================================
def evr_rheader(r):
    """
        EVR Resource Headers

        @param r: the S3Request
    """

    T = current.T
    if r.representation != "html" or not r.record:
        return None

    resourcename = r.name
    rheader_fields = None

    if resourcename == "person":

        tabs = [(T("Person"), None),
                (T("Addresses"), "address"),
                (T("Contact Data"), "contacts"),
                # these can be hidden since inline in the main form,
                # but can enabled to verify the functionality:
                #(T("Identity Documents"), "identity"),
                #(T("Case Details"), "case"),
                (T("Physical Description"), "physical_description"),
                (T("Medical Information"), "medical_details"),
                (T("Socio-Economic Background"), "background"),
                (T("Shelter Registration"), "shelter_registration"),
                ]

        rheader_fields = [["first_name", "last_name"],
                          ["date_of_birth"],
                         ]
                         
    elif resourcename == "group":

        rheader_fields = [["name"],
                          ["description"],
                         ]

        tabs = [("Group Details", None),
                (T("Contact Data"), "contact"),
                (T("Members"), "group_membership"),
                (T("Shelter Allocation"), "available_shelters"),
                ]

    if rheader_fields is not None:
        return S3ResourceHeader(rheader_fields, tabs)(r)
    else:
        return None
    
# =============================================================================
class evr_AvailableShelters(S3Method):
    """
        Method handler for the "available_shelters" method
    """

    def apply_method(self, r, **attr):
        
        T = current.T
        s3db = current.s3db
        response = current.response
        resource = s3db.resource("cr_shelter")
        
        if r.http == "GET":
            # Find out how many records are in the resource
            totalrows = resource.count()
            list_fields = ["name",
                           "capacity_day",
                           "population_day",
                           "capacity_night",
                           "population_night",
                           ]
            
            # Get all the data from the resource
            data = resource.select(list_fields)
            
            filteredrows = data["numrows"]
            
            # Create the resource fields
            dt = S3DataTable(data["rfields"], data["rows"])
            dt_id = "datatable"
            
            if r.extension == "html":
                # Create the html for the dataTable 
                items = dt.html(totalrows,
                                filteredrows,
                                dt_id,
                                dt_pagination="true"
                                )
                
                output = dict(items=items)
                response.view = "list_filter.html"
                return output
            
        elif r.http == "POST":
            pass
            # @todo: implement
        
        
# END =========================================================================
