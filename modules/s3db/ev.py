# -*- coding: utf-8 -*-

""" Sahana Eden Evacuees Model

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

__all__ = ["S3EvModel",
           "ev_group_controller",
           "ev_guest_rheader"
           ]

from gluon import *
from gluon.storage import Storage
from gluon.tools import callback
from ..s3 import *
from s3layouts import S3AddResourceLink  

# =============================================================================
class S3EvModel(S3Model):
    """
        Allow an individual or household to register to receive compensation
            &/or Distributions of Relief Items
    """

    names = ["ev_guest",
             "ev_guest_id",
             "ev_medicaldata",
             "ev_otherdata"
             ]

    def model(self):

        T = current.T
        s3db = current.s3db

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT
        
        # ---------------------------------------------------------------------
        # Personal details dropdown menus
        #
        ev_maritalStatus_opts = current.deployment_settings.get_ev_maritalStatus()
        ev_maritalStatus = S3ReusableField("maritalStatus", "integer",
                                            requires = IS_IN_SET(ev_maritalStatus_opts, zero=None),
                                            default = 1,
                                            label = T("Marital Status"),
                                            represent = lambda opt: \
                                                     ev_maritalStatus_opts.get(opt, UNKNOWN_OPT))
        
        # ---------------------------------------------------------------------
        # Physical details dropdown menus
        #
        ev_eyeColor_opts = current.deployment_settings.get_ev_eyeColor()
        ev_eyeColor = S3ReusableField("eyeColor", "integer",
                                       requires = IS_IN_SET(ev_eyeColor_opts, zero=None),
                                       default = 1,
                                       label = T("Eye Color"),
                                       represent = lambda opt: \
                                                     ev_eyeColor_opts.get(opt, UNKNOWN_OPT))

        ev_skinColor_opts = current.deployment_settings.get_ev_skinColor()
        ev_skinColor = S3ReusableField("skinColor", "integer",
                                    requires = IS_IN_SET(ev_skinColor_opts, zero=None),
                                    default = 1,
                                    label = T("Skin Color"),
                                    represent = lambda opt: \
                                                ev_skinColor_opts.get(opt, UNKNOWN_OPT))
        
        ev_hairColor_opts = current.deployment_settings.get_ev_hairColor()
        ev_hairColor = S3ReusableField("hairColor", "integer",
                                       requires = IS_IN_SET(ev_hairColor_opts, zero=None),
                                       default = 1,
                                       label = T("Hair Color"),
                                       represent = lambda opt: \
                                                     ev_hairColor_opts.get(opt, UNKNOWN_OPT))
        
        ev_bloodType_opts = current.deployment_settings.get_ev_bloodType()
        ev_bloodType = S3ReusableField("bloodType", "integer",
                                       requires = IS_IN_SET(ev_bloodType_opts, zero=None),
                                       default = 1,
                                       label = T("Blood Type"),
                                       represent = lambda opt: \
                                                     ev_bloodType_opts.get(opt, UNKNOWN_OPT))
        
        
        # ---------------------------------------------------------------------
        # Personal data table
        #
        tablename = "ev_guest"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  self.super_link("sit_id", "sit_situation"),
                                  self.pr_person_id(
                                      widget=S3AddPersonWidget(controller="hrm",
                                                               # TODO: understand why hrm controller is needed
                                                               # remove the possibility to choose pre-existing person
                                                               #select_existing = False
                                                               ),
                                      requires=IS_ADD_PERSON_WIDGET(),
                                      comment=None
                                      ),
                                  Field("shelter_id", "integer",
                                        readable = False,
                                        writable = False),
                                  Field("birthplace",
                                        label=T("Birthplace")
                                        ),
                                  ev_maritalStatus(),
                                  Field("fiscalCode", "string",
                                       length=16,
                                       label=T("Fiscal Code")
                                       ),
                                  # Identity details
                                  Field("identityCard",
                                        label=T("Identity Card")
                                        ),
                                  Field("passportNumber",
                                        label=T("Passport Number")
                                        ),
                                  Field("drivingLicense",
                                        label=T("Driving License")
                                        ),
                                  # Physical details
                                  ev_eyeColor(),
                                  ev_skinColor(),
                                  ev_hairColor(),
                                  ev_bloodType(),
                                  Field("height", 'integer',
                                        label=T("Height"),
                                        ),
                                  Field("weight", 'integer',
                                        label=T("Weight")
                                        ),
                                  self.gis_location_id(
                                        label=T("Origin"),
#                                         widget = S3LocationSelectorWidget2(
#                                                       hide_lx=False
#                                                       ),
                                        ),
#                                   self.pr_group_id(label = T("Family"),
#                                                    comment = S3AddResourceLink(c="pr",
#                                                                                f="group",
#                                                                                label=T("Add New Group")
#                                                                                )
#                                                    ),
                                  s3_comments(),
                                  *s3_meta_fields()
                                  )
        
        s3db.configure(tablename,
                       # Redirect to medical data
                       create_next = URL(f="guest",
                                     args=["[id]", "medicaldata"]),
                       super_entity = "pr_pentity"
                       )
        
        # CRUD Strings
        ADD_CASE = T("Add Guest")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_CASE,
            title_display = T("Guest Details"),
            title_list = T("Evacuees"),
            title_update = T("Edit Guest"),
            title_search = T("Search Guests"),
            subtitle_create = T("Add New Guest"),
            label_list_button = T("List Guests"),
            label_create_button = ADD_CASE,
            label_delete_button = T("Delete Guest"),
            msg_record_created = T("Guest added"),
            msg_record_modified = T("Guest updated"),
            msg_record_deleted = T("Guest deleted"),
            msg_list_empty = T("No Guests found")
        )
        
        # ---------------------------------------------------------------------
        # Medical details dropdown menus
        #
        ev_therapy_opts = current.deployment_settings.get_ev_therapy()
        ev_therapy = S3ReusableField("therapy", "integer",
                                     requires = IS_IN_SET(ev_therapy_opts, zero=None),
                                     default = 1,
                                     label = T("Therapy"),
                                     represent = lambda opt: \
                                                     ev_therapy_opts.get(opt, UNKNOWN_OPT)
                                     )
        
        ev_allergy_opts = current.deployment_settings.get_ev_allergy()
        ev_allergy = S3ReusableField("allergy", "integer",
                                       requires = IS_IN_SET(ev_allergy_opts, zero=None),
                                       default = 1,
                                       label = T("Allergy"),
                                       represent = lambda opt: \
                                                     ev_allergy_opts.get(opt, UNKNOWN_OPT)
                                       )
        
        ev_invalid_opts = current.deployment_settings.get_ev_invalid()
        ev_invalid = S3ReusableField("invalid", "integer",
                                     requires = IS_IN_SET(ev_invalid_opts, zero=None),
                                     default = 1,
                                     label = T("Invalid"),
                                     represent = lambda opt: \
                                                     ev_invalid_opts.get(opt, UNKNOWN_OPT)
                                     )
        
        ev_assistanceOf_opts = current.deployment_settings.get_ev_assistanceOf()
        ev_assistanceOf = S3ReusableField("assistanceOf", "integer",
                                           requires = IS_IN_SET(ev_assistanceOf_opts, zero=None),
                                           default = 1,
                                           label = T("Assistance of"),
                                           represent = lambda opt: \
                                                     ev_assistanceOf_opts.get(opt, UNKNOWN_OPT)
                                           )
        
        ev_relationship_opts = current.deployment_settings.get_ev_relationship()
        ev_relationship = S3ReusableField("relationship", "integer",
                                           requires = IS_IN_SET(ev_relationship_opts, zero=None),
                                           default = 1,
                                           label = T("Relationship"),
                                           represent = lambda opt: \
                                                     ev_relationship_opts.get(opt, UNKNOWN_OPT)
                                           )
        
         # Reusable field
        guest_id = S3ReusableField("guest_id", table,
                                   requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "ev_guest.id",
                                                              S3Represent(lookup=tablename),
                                                              sort=True,
                                                              error_message=T("Person must be specified")
                                                              )
                                                         ),
                                   represent = S3Represent(lookup=tablename),
                                   ondelete = "RESTRICT",
                                   comment=S3AddResourceLink(c="ev",
                                                             f="guest",
                                                             label=T("Add Guest"),
                                                             title=T("Add Guest"),
                                                             vars=dict(child="guest_id"),
#                                                              tooltip="%s (%s)." % (T("Add guest to into this shelter"),
#                                                                                     T("optional"))
                                                             tooltip=T("Add guest to this shelter")
                                                             ),
                                   label = T("Evacuee"),
                                   widget = S3AutocompleteWidget("ev", "guest")
                                   )

        self.add_components(tablename,
                            ev_medicaldata={"name": "medicaldata",
                                            "joinby": "guest_id",
                                            "multiple": False
                                            },
                            ev_otherdata={"name": "otherdata",
                                          "joinby": "guest_id",
                                          "multiple": False
                                          }
                            )
        # ---------------------------------------------------------------------
        # Medical data table
        #
        tablename = "ev_medicaldata"
        table = self.define_table(tablename,
                                  guest_id(),
                                  ev_therapy(),
                                  Field("pregnancy", "boolean",
                                        label=T("Pregnancy")
                                        ),
                                  ev_allergy(),
                                  Field("diet",
                                        label=T("Diet")
                                        ),
                                  ev_invalid(),
                                  Field("selfSufficient", "boolean",
                                        label=T("Self-Sufficient")
                                        ),
                                  ev_assistanceOf(),
                                  Field("declaredByFamilyName",
                                        label=T("Declared by (Family Name)"),
                                        ),
                                  Field("declaredByLastName",
                                        label=("Declared by (Last Name)"),
                                        ),
                                  ev_relationship(),
                                  Field("declaredByPhone",# "integer",
                                        label=T("Declared by (Phone)"),
                                        requires = IS_NULL_OR(s3_phone_requires),
                                        ),
                                  Field("declaredByEmail",
                                        label=T("Declared by (Email)")
                                        # TODO: validator for email
                                        ),
                                  Field("isTutor", "boolean",
                                        label=T("Is Tutor"),
                                        ),
                                  Field("tutorFamilyName",
                                        label=T("Tutor (Family Name)"),
                                        ),
                                  Field("tutorLastName",
                                        label=T("Tutor (Last Name)"),
                                        ),
                                  Field("tutorPhone",# "integer",
                                        label=T("Tutor (Phone)"),
                                        requires = IS_NULL_OR(s3_phone_requires),
                                        ),
                                  Field("tutorEmail",
                                        label=T("Tutor (Email)"),
                                        # TODO: validator for email
                                        ),
                                  #*s3_meta_fields()
                                  )
        
        s3db.configure(tablename,
                       # Redirect to medical data
                       create_next = URL(f="guest",
                                     args=["[id]", "otherdata"]),
                       )
        
        # CRUD Strings
        ADD_CASE = T("Add Medical Data")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_CASE,
            title_display = T("Guest Details"),
            title_list = T("Evacuees"),
            title_update = T("Edit Medical Data"),
            title_search = T("Search Medical Data"),
            subtitle_create = ADD_CASE,
            label_list_button = T("List Medical Data"),
            label_create_button = ADD_CASE,
            label_delete_button = T("Delete Medical Data"),
            msg_record_created = T("Medical Data added"),
            msg_record_modified = T("Medical Data updated"),
            msg_record_deleted = T("Medical Data deleted"),
            msg_list_empty = T("No Medical Data found")
        )
        
        # ---------------------------------------------------------------------
        # Other data table
        #
        tablename = "ev_otherdata"
        table = self.define_table(tablename,
                                  guest_id(),
                                  Field("legalMeasure", "boolean",
                                        label=T("Legal measure / Home warrant")
                                        ),
                                  s3_comments(),
                                  Field("socialWalfare", "boolean",
                                        label=T("Social Walfare")
                                        ),
                                  s3_comments(),
                                  Field("homeHelp", "boolean",
                                        label=T("Home help")
                                        ),
                                  s3_comments(),
                                  Field("interpreteur" , "boolean",
                                        label=T("Interpreter / Cultural Mediator")
                                        ),
                                  s3_comments(),
                                  Field("job",
                                        label=T("Job")
                                        ),
                                  Field("company",
                                        label=T("Company / School / University")
                                        ),
                                  Field("distanceFromShelter", "integer",
                                        label=T("Distance from Shelter")
                                        ),
                                  Field("jobLostByEvent", "boolean",
                                        label=T("Job lost by event")
                                        ),
                                  Field("carAvailable", "boolean",
                                        label=T("Car available")
                                        ),
                                  s3_comments(),
                                  #*s3_meta_fields()
                                  )

        # CRUD Strings
        ADD_GUEST = T("Add Other Data")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_GUEST,
            title_display = T("Guest Details"),
            title_list = T("Evacuees"),
            title_update = T("Edit Other Data"),
            title_search = T("Search Other Data"),
            subtitle_create = T("Add New Data"),
            label_list_button = T("List Data"),
            label_create_button = ADD_GUEST,
            label_delete_button = T("Delete Data"),
            msg_record_created = T("Data added"),
            msg_record_modified = T("Data updated"),
            msg_record_deleted = T("Data deleted"),
            msg_list_empty = T("No Data found")
        )
        
        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage(ev_guest_id=guest_id)
    
def ev_group_controller():
    """
        Group controller
        - uses the group table from PR
    """

    T = current.T
    s3db = current.s3db
    s3 = current.response.s3

    tablename = "pr_group"
    table = s3db[tablename]

    _group_type = table.group_type
#     _group_type.label = T("Team Type")
#     table.description.label = T("Family Description")
#     table.name.label = T("Family Name")

    # Set Defaults
    _group_type.default = 1  # 'Family'
    # We use crud_form
    #_group_type.readable = _group_type.writable = False

    # Only show Families
    # Do not show system groups
    s3.filter = (table.system == False) & \
                (_group_type == 1 or
                 _group_type == 4 or
                 _group_type == 6 or
                 _group_type == 7 or
                 _group_type == 8 or
                 _group_type == 9 or
                 _group_type == 10 or
                 _group_type == 11
                 )

    # CRUD Strings
#     s3.crud_strings[tablename] = Storage(
#         title_create = T("Add Team"),
#         title_display = T("Family Details"),
#         title_list = T("Families"),
#         title_update = T("Edit Family"),
#         title_search = T("Search Families"),
#         subtitle_create = T("Add New Family"),
#         label_list_button = T("List Families"),
#         label_create_button = T("Add New Family"),
#         label_search_button = T("Search Families"),
#         msg_record_created = T("Family added"),
#         msg_record_modified = T("Family updated"),
#         msg_record_deleted = T("Family deleted"),
#         msg_list_empty = T("No Families currently registered"))

    filter_widgets = [
        S3TextFilter(["name",
                      "description",
                      "comments",
                      ],
                     label = T("Search"),
                     comment = T("You can search by group name, description or comments and by organization name or acronym. You may use % as wildcard. Press 'Search' without input to list all."),
                     #_class="filter-search",
                     ),
        ]

    list_fields = ["id",
                   "name",
                   "description",
                   "comments",
                   ]

    s3db.configure(tablename,
                   # Redirect to member list when a new group has been created
                   create_next = URL(f="group",
                                     args=["[id]", "group_membership"]),
                   filter_widgets = filter_widgets,
                   list_fields = list_fields,
                   )

    # Post-process
    def postp(r, output):

        if r.interactive:
            if not r.component:
                update_url = URL(args=["[id]", "group_membership"])
                S3CRUD.action_buttons(r, update_url=update_url)

        return output
    s3.postp = postp
    
    tabs = [("Group Details", None),
            (T("Contact Data"), "contact"),
            (T("Members"), "group_membership"),
            ]

    output = current.rest_controller("pr", "group",
                                     hide_filter = False,
                                     rheader = lambda r: \
                                        s3db.pr_rheader(r, tabs=tabs)
                                     )

    return output

# =============================================================================
def ev_guest_rheader(r, tabs=[]):
    """ Resource Headers """

    rheader = None
    if r.representation == "html":

        tablename, record = s3_rheader_resource(r)
        if tablename == "ev_guest" and record:
            T = current.T
            s3db = current.s3db
            
            tabs = [("Personal Details", None),
                    (T("Medical Data"), "medicaldata"),
                    (T("Other Data"), "otherdata"),
                    ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            rheader = DIV(TABLE(
                                # TODO: should we show the name or the fiscal code?
                                TR(TH("%s: " % T("Fiscal Code")),
                                   record.fiscalCode
                                   ),
                                ),
                          rheader_tabs
                          )

    return rheader
# END =========================================================================
