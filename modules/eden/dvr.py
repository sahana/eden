# -*- coding: utf-8 -*-

""" Sahana Eden Disaster Victim Registration Model

    @copyright: 2012 (c) Sahana Software Foundation
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

__all__ = ["S3DVRModel"]

from gluon import *
from gluon.storage import Storage
from gluon.tools import callback
from ..s3 import *

# =============================================================================
class S3DVRModel(S3Model):
    """
        Allow an individual or household to register to receive compensation
            &/or Distributions of Relief Items
    """

    names = ["dvr_case",
             ]

    def model(self):

        T = current.T
        s3 = current.response.s3

        person_id = self.pr_person_id
        location_id = self.gis_location_id
        multi_activity_id = self.project_multi_activity_id
        NONE = current.messages.NONE

        # ---------------------------------------------------------------------
        # Case
        #
        dvr_damage_opts = {
            1: T("Very High"),
            2: T("High"),
            3: T("Medium"),
            4: T("Low"),
        }

        dvr_status_opts = {
            1: T("Open"),
            2: T("Accepted"),
            3: T("Rejected"),
        }
        
        tablename = "dvr_case"
        table = self.define_table(tablename,
                                  # @ToDo: Option to autogenerate these, like Waybills, et al
                                  Field("reference", label = T("Case Number")),
                                  person_id(widget=S3AddPersonWidget(controller="pr"),
                                            # @ToDo: Modify this to update location_id if the selected person has a Home Address already
                                            requires=IS_ADD_PERSON_WIDGET(),
                                            comment=None
                                            ),
                                  location_id(label = T("Home Address")),
                                  Field("damage", "integer",
                                        requires = IS_NULL_OR(IS_IN_SET(dvr_damage_opts)),
                                        represent = lambda opt: dvr_damage_opts.get(opt, NONE),
                                        label= T("Damage Assessment")),
                                  Field("insurance", "boolean",
                                        label = T("Insurance")),
                                  Field("status", "integer",
                                        default = 1,
                                        requires = IS_NULL_OR(IS_IN_SET(dvr_status_opts)),
                                        represent = lambda opt: dvr_status_opts.get(opt, NONE),
                                        label= T("Status")),
                                  multi_activity_id(),
                                  s3.comments(),
                                  *s3.meta_fields())

        # CRUD Strings
        ADD_CASE = T("Add Case")
        LIST_CASES = T("List Cases")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_CASE,
            title_display = T("Case Details"),
            title_list = LIST_CASES,
            title_update = T("Edit Case"),
            title_search = T("Search Cases"),
            subtitle_create = T("Add New Case"),
            subtitle_list = T("Cases"),
            label_list_button = LIST_CASES,
            label_create_button = ADD_CASE,
            label_delete_button = T("Delete Case"),
            msg_record_created = T("Case added"),
            msg_record_modified = T("Case updated"),
            msg_record_deleted = T("Case deleted"),
            msg_list_empty = T("No Cases found")
        )

        #self.add_component("pr_address", pr_pentity="pe_id")

        self.configure(tablename,
                       onaccept=self.dvr_case_onaccept,
                    )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def dvr_case_onaccept(form):
        """
            Link the location_id to the Home Address
            @ToDo: Check Security of records (use S3Resource?)
        """

        vars = form.vars

        if "location_id" in vars and vars.location_id:
            person_id = vars.person_id
            db = current.db
            s3db = current.s3db
            ptable = s3db.pr_person
            atable = s3db.pr_address
            query = (ptable.id == person_id)
            left = atable.on((atable.pe_id == ptable.pe_id) & \
                             (atable.type == 1))
            person = db(query).select(ptable.pe_id,
                                      atable.id,
                                      atable.location_id,
                                      left=left).first()
            if person:
                _config = current.manager.model.get_config
                pe_id = person["pr_person"].pe_id
                if not person["pr_address"].id:
                    # Create Home Address from location_id
                    _vars = Storage(pe_id=pe_id,
                                    location_id=vars.location_id,
                                    type=1 # Home Address
                                    )
                    id = atable.insert(**_vars)
                    _vars.update(id=id)
                    _form = Storage(vars=_vars)
                    onaccept = _config("pr_address", "create_onaccept") or \
                               _config("pr_address", "onaccept")
                    callback(onaccept, _form, tablename="pr_address")
                    # Normally happens onvalidation:
                    current.response.s3.lx_update(atable, id)
                else:
                    # Update Home Address from location_id
                    id = person["pr_address"].id
                    query = (atable.type == 1) & \
                            (atable.id == id)
                    db(query).update(location_id = vars.location_id)
                    onaccept = _config("pr_address", "update_onaccept") or \
                               _config("pr_address", "onaccept")
                    _vars = Storage(id=id,
                                    pe_id=pe_id,
                                    location_id=vars.location_id,
                                    type=1 # Home Address
                                    )
                    _form = Storage(vars=_vars)
                    callback(onaccept, _form, tablename="pr_address")
                    # Normally happens onvalidation:
                    current.response.s3.lx_update(atable, id)
        return

# END =========================================================================
