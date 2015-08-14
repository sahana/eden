# -*- coding: utf-8 -*-

""" Sahana Eden Disaster Victim Registration Model

    @copyright: 2012-15 (c) Sahana Software Foundation
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

__all__ = ("S3DVRModel",)

from gluon import *
from gluon.storage import Storage
from gluon.tools import callback
from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class S3DVRModel(S3Model):
    """
        Allow an individual or household to register to receive compensation
            &/or Distributions of Relief Items
    """

    names = ("dvr_need",
             "dvr_case",
             "dvr_case_need",
             )

    def model(self):

        T = current.T
        db = current.db

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Needs
        #
        tablename = "dvr_need"
        define_table(tablename,
                     Field("name",
                           label = T("name"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_NEED = T("Create Need")
        crud_strings[tablename] = Storage(
            label_create = ADD_NEED,
            title_display = T("Need Details"),
            title_list = T("Needs"),
            title_update = T("Edit Need"),
            label_list_button = T("List Needs"),
            label_delete_button = T("Delete Need"),
            msg_record_created = T("Need added"),
            msg_record_modified = T("Need updated"),
            msg_record_deleted = T("Need deleted"),
            msg_list_empty = T("No Needs found")
        )

        represent = S3Represent(lookup=tablename, translate=True)
        need_id = S3ReusableField("need_id", "reference %s" % tablename,
                                  label = T("Need"),
                                  ondelete = "RESTRICT",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "dvr_need.id",
                                                          represent)),
                                  comment=S3AddResourceLink(c="dvr",
                                                            f="need",
                                                            label=ADD_NEED),
                                  )

        # ---------------------------------------------------------------------
        # Case
        #
        #dvr_damage_opts = {
        #    1: T("Very High"),
        #    2: T("High"),
        #    3: T("Medium"),
        #    4: T("Low"),
        #}

        #dvr_status_opts = {
        #    1: T("Open"),
        #    2: T("Accepted"),
        #    3: T("Rejected"),
        #}

        tablename = "dvr_case"
        define_table(tablename,
                     # @ToDo: Option to autogenerate these, like Waybills, et al
                     Field("reference",
                           label = T("Case Number"),
                           ),
                     self.pr_person_id(
                        # @ToDo: Modify this to update location_id if the selected person has a Home Address already
                        comment = None,
                        represent = self.pr_PersonRepresent(show_link=True),
                        requires = IS_ADD_PERSON_WIDGET2(),
                        widget = S3AddPersonWidget2(controller="pr"),
                     ),
                     #Field("damage", "integer",
                     #      label= T("Damage Assessment"),
                     #      represent = lambda opt: \
                     #           dvr_damage_opts.get(opt, UNKNOWN_OPT),
                     #      requires = IS_EMPTY_OR(IS_IN_SET(dvr_damage_opts)),
                     #      ),
                     #Field("insurance", "boolean",
                     #      label = T("Insurance"),
                     #      represent = s3_yes_no_represent,
                     #      ),
                     #Field("status", "integer",
                     #      default = 1,
                     #      label = T("Status"),
                     #      represent = lambda opt: \
                     #           dvr_status_opts.get(opt, UNKNOWN_OPT),
                     #      requires = IS_EMPTY_OR(IS_IN_SET(dvr_status_opts)),
                     #      ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Case"),
            title_display = T("Case Details"),
            title_list = T("Cases"),
            title_update = T("Edit Case"),
            label_list_button = T("List Cases"),
            label_delete_button = T("Delete Case"),
            msg_record_created = T("Case added"),
            msg_record_modified = T("Case updated"),
            msg_record_deleted = T("Case deleted"),
            msg_list_empty = T("No Cases found")
        )

        represent = S3Represent(lookup=tablename, fields=("reference",))
        case_id = S3ReusableField("case_id", "reference %s" % tablename,
                                  label = T("Case"),
                                  ondelete = "RESTRICT",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "dvr_case.id",
                                                          represent)),
                                  )

        self.add_components(tablename,
                            dvr_need =  {"link": "dvr_need_case",
                                         "joinby": "case_id",
                                         "key": "need_id",
                                         },
                            pr_address = ({"name": "current_address",
                                           "link": "pr_person",
                                           "joinby": "id",
                                           "key": "pe_id",
                                           "fkey": "pe_id",
                                           "pkey": "person_id",
                                           "filterby": "type",
                                           "filterfor": ("1",),
                                           },
                                          {"name": "permanent_address",
                                           "link": "pr_person",
                                           "joinby": "id",
                                           "key": "pe_id",
                                           "fkey": "pe_id",
                                           "pkey": "person_id",
                                           "filterby": "type",
                                           "filterfor": ("2",),
                                           },
                                          ),
                            )

        crud_form = S3SQLCustomForm("reference",
                                    "person_id",
                                    S3SQLInlineComponent("current_address",
                                                         label = T("Current Address"),
                                                         fields = [("", "location_id"),
                                                                   ],
                                                         default = {"type": 1}, # Current Home Address
                                                         link = False,
                                                         multiple = False,
                                                         ),
                                    S3SQLInlineComponent("permanent_address",
                                                         comment = T("If Displaced"),
                                                         label = T("Normal Address"),
                                                         fields = [("", "location_id"),
                                                                   ],
                                                         default = {"type": 2}, # Permanent Home Address
                                                         link = False,
                                                         multiple = False,
                                                         ),
                                    S3SQLInlineLink("need",
                                                    field = "need_id",
                                                    ),
                                    "comments",
                                    )
        
        self.configure(tablename,
                       crud_form = crud_form,
                       )

        # ---------------------------------------------------------------------
        # Cases <> Needs
        #
        tablename = "dvr_case_need"
        define_table(tablename,
                     case_id(empty = False,
                             ondelete = "CASCADE",
                             ),
                     need_id(empty = False,
                             ondelete = "CASCADE",
                             ),
                     s3_comments(),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# END =========================================================================
