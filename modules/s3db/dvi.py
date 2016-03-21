# -*- coding: utf-8 -*-

""" Sahana Eden Disaster Victim Identification Model

    @copyright: 2009-2016 (c) Sahana Software Foundation
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

__all__ = ("S3DVIModel",)

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3PopupLink

# =============================================================================
class S3DVIModel(S3Model):

    names = ("dvi_recreq",
             "dvi_body",
             "dvi_morgue",
             "dvi_checklist",
             "dvi_effects",
             "dvi_identification",
             "dvi_id_status",
             )

    def model(self):

        T = current.T
        db = current.db
        request = current.request

        person_id = self.pr_person_id
        location_id = self.gis_location_id

        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        dvi_id_status = {
            1:T("Preliminary"),
            2:T("Confirmed"),
        }
        dvi_id_status_filteropts = dict(dvi_id_status)
        dvi_id_status_filteropts[None] = T("Unidentified")

        # ---------------------------------------------------------------------
        # Recovery Request
        #
        task_status = {
            1:T("Not Started"),
            2:T("Assigned"),
            3:T("In Progress"),
            4:T("Completed"),
            5:T("Not Applicable"),
            6:T("Not Possible")
        }

        tablename = "dvi_recreq"
        define_table(tablename,
                     s3_datetime(label = T("Date/Time of Find"),
                                 empty=False,
                                 default = "now",
                                 future=0
                                 ),
                     Field("marker", length=64,
                           label = T("Marker"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Marker"),
                                                           T("Number or code used to mark the place of find, e.g. flag code, grid coordinates, site reference number or similar (if available)")))),
                     person_id(label = T("Finder")),
                     Field("bodies_found", "integer",
                           label = T("Bodies found"),
                           requires = IS_INT_IN_RANGE(1, 99999),
                           represent = lambda v, row=None: IS_INT_AMOUNT.represent(v),
                           default = 0,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Number of bodies found"),
                                                           T("Please give an estimated figure about how many bodies have been found.")))),
                     Field("bodies_recovered", "integer",
                           label = T("Bodies recovered"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 99999)),
                           represent = lambda v, row=None: IS_INT_AMOUNT.represent(v),
                           default = 0),
                     Field("description", "text"),
                     location_id(label=T("Location")),
                     Field("status", "integer",
                           requires = IS_IN_SET(task_status,
                                                zero=None),
                           default = 1,
                           label = T("Task Status"),
                           represent = lambda opt: \
                                       task_status.get(opt, UNKNOWN_OPT)),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Body Recovery Request"),
            title_display = T("Request Details"),
            title_list = T("Body Recovery Requests"),
            title_update = T("Update Request"),
            label_list_button = T("List Requests"),
            label_delete_button = T("Delete Request"),
            msg_record_created = T("Recovery Request added"),
            msg_record_modified = T("Recovery Request updated"),
            msg_record_deleted = T("Recovery Request deleted"),
            msg_list_empty = T("No requests found"))

        # Resource configuration
        configure(tablename,
                  orderby="dvi_recreq.date desc",
                  list_fields = ["id",
                                 "date",
                                 "marker",
                                 "location_id",
                                 "bodies_found",
                                 "bodies_recovered",
                                 "status"
                                 ])

        # Reusable fields
        dvi_recreq_id = S3ReusableField("dvi_recreq_id", "reference %s" % tablename,
                                        requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                        "dvi_recreq.id",
                                                        "[%(marker)s] %(date)s: %(bodies_found)s bodies")),
                                        represent = lambda id: id,
                                        label=T("Recovery Request"),
                                        ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Morgue
        #
        tablename = "dvi_morgue"
        define_table(tablename,
                     super_link("pe_id", "pr_pentity"),
                     super_link("site_id", "org_site"),
                     Field("name", length=255, unique=True, notnull=True,
                           label = T("Morgue"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_NOT_ONE_OF(db,
                                                     "dvi_morgue.name",
                                                     ),
                                       ],
                           ),
                     self.org_organisation_id(),
                     Field("description",
                           label = T("Description")),
                     location_id(),
                     Field("obsolete", "boolean",
                     label = T("Obsolete"),
                     represent = lambda opt: \
                                 (opt and [T("Obsolete")] or [messages["NONE"]])[0],
                     default = False,
                     readable = False,
                     writable = False),
                     *s3_meta_fields())

        # Reusable Field
        morgue_id = S3ReusableField("morgue_id", "reference %s" % tablename,
                                    requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                    "dvi_morgue.id", "%(name)s")),
                                    represent = self.morgue_represent,
                                    ondelete = "RESTRICT")

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Morgue"),
            title_display = T("Morgue Details"),
            title_list = T("Morgues"),
            title_update = T("Update Morgue Details"),
            label_list_button = T("List Morgues"),
            label_delete_button = T("Delete Morgue"),
            msg_record_created = T("Morgue added"),
            msg_record_modified = T("Morgue updated"),
            msg_record_deleted = T("Morgue deleted"),
            msg_list_empty = T("No morgues found"))

        # Resource Configuration
        configure(tablename,
                  super_entity = ("pr_pentity", "org_site"),
                  )

        # Components
        self.add_components("dvi_morgue",
                            dvi_body="morgue_id",
                           )

        # ---------------------------------------------------------------------
        # Body
        #
        bool_repr = lambda opt: (opt and [T("yes")] or [""])[0]
        tablename = "dvi_body"
        define_table(tablename,
                     super_link("pe_id", "pr_pentity"),
                     super_link("track_id", "sit_trackable"),
                     self.pr_pe_label(requires = [IS_NOT_EMPTY(error_message=T("Enter a unique label!")),
                                                  IS_NOT_ONE_OF(db, "dvi_body.pe_label")]),
                     morgue_id(),
                     dvi_recreq_id(label = T("Recovery Request")),
                     s3_datetime("date_of_recovery",
                                 label = T("Date of Recovery"),
                                 empty=False,
                                 default = "now",
                                 future=0
                                 ),
                     Field("recovery_details","text"),
                     Field("incomplete", "boolean",
                           label = T("Incomplete"),
                           represent = bool_repr),
                     Field("major_outward_damage", "boolean",
                           label = T("Major outward damage"),
                           represent = bool_repr),
                     Field("burned_or_charred", "boolean",
                           label = T("Burned/charred"),
                           represent = bool_repr),
                     Field("decomposed","boolean",
                           label = T("Decomposed"),
                           represent = bool_repr),
                     self.pr_gender(label=T("Apparent Gender")),
                     self.pr_age_group(label=T("Apparent Age")),
                     location_id(label=T("Place of Recovery")),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Dead Body Report"),
            title_display = T("Dead Body Details"),
            title_list = T("Dead Body Reports"),
            title_update = T("Edit Dead Body Details"),
            label_list_button = T("List Reports"),
            label_delete_button = T("Delete Report"),
            msg_record_created = T("Dead body report added"),
            msg_record_modified = T("Dead body report updated"),
            msg_record_deleted = T("Dead body report deleted"),
            msg_list_empty = T("No dead body reports available"))

        # Filter widgets
        filter_widgets = [
            S3TextFilter(["pe_label"],
                         label = T("ID Tag"),
                         comment = T("To search for a body, enter the ID "
                                     "tag number of the body. You may use "
                                     "% as wildcard."),
                        ),
            S3OptionsFilter("gender",
                            options=self.pr_gender_opts),
            S3OptionsFilter("age_group",
                            options=self.pr_age_group_opts),
            S3OptionsFilter("identification.status",
                            options=dvi_id_status_filteropts,
                            none=True),
        ]

        # Resource configuration
        configure(tablename,
                  super_entity=("pr_pentity", "sit_trackable"),
                  create_onaccept=self.body_onaccept,
                  create_next=URL(f="body", args=["[id]", "checklist"]),
                  filter_widgets=filter_widgets,
                  list_fields=["id",
                               "pe_label",
                               "gender",
                               "age_group",
                               "incomplete",
                               "date_of_recovery",
                               "location_id"
                               ],
                  main="pe_label",
                  extra="gender",
                 )

        # ---------------------------------------------------------------------
        # Checklist of operations
        #
        checklist_item = S3ReusableField("checklist_item", "integer",
                                         requires = IS_IN_SET(task_status, zero=None),
                                         default = 1,
                                         label = T("Checklist Item"),
                                         represent = lambda opt: \
                                                     task_status.get(opt, UNKNOWN_OPT))

        tablename = "dvi_checklist"
        define_table(tablename,
                     super_link("pe_id", "pr_pentity"),
                     checklist_item("personal_effects",
                                    label = T("Inventory of Effects")),
                     checklist_item("body_radiology",
                                    label = T("Radiology")),
                     checklist_item("fingerprints",
                                    label = T("Fingerprinting")),
                     checklist_item("anthropology",
                                    label = T("Anthropology")),
                     checklist_item("pathology",
                                    label = T("Pathology")),
                     checklist_item("embalming",
                                    label = T("Embalming")),
                     checklist_item("dna",
                                    label = T("DNA Profiling")),
                     checklist_item("dental",
                                    label = T("Dental Examination")),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Checklist"),
            title_display = T("Checklist of Operations"),
            title_list = T("Checklists"),
            title_update = T("Update Task Status"),
            label_list_button = T("List Checklists"),
            msg_record_created = T("Checklist created"),
            msg_record_modified = T("Checklist updated"),
            msg_record_deleted = T("Checklist deleted"),
            msg_list_empty = T("No Checklist available"))

        # Resource configuration
        configure(tablename, list_fields=["id"])

        # ---------------------------------------------------------------------
        # Effects Inventory
        #
        tablename = "dvi_effects"
        define_table(tablename,
                     super_link("pe_id", "pr_pentity"),
                     Field("clothing", "text"),  # @todo: elaborate
                     Field("jewellery", "text"), # @todo: elaborate
                     Field("footwear", "text"),  # @todo: elaborate
                     Field("watch", "text"),     # @todo: elaborate
                     Field("other", "text"),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_PERSONAL_EFFECTS = T("Create Personal Effects")
        crud_strings[tablename] = Storage(
            label_create = ADD_PERSONAL_EFFECTS,
            title_display = T("Personal Effects Details"),
            title_list = T("Personal Effects"),
            title_update = T("Edit Personal Effects Details"),
            label_list_button = T("List Personal Effects"),
            msg_record_created = T("Record added"),
            msg_record_modified = T("Record updated"),
            msg_record_deleted = T("Record deleted"),
            msg_list_empty = T("No Details currently registered"))

        configure(tablename, list_fields=["id"])

        # ---------------------------------------------------------------------
        # Identification Report
        #
        dvi_id_status = {
            1:T("Preliminary"),
            2:T("Confirmed"),
        }

        dvi_id_methods = {
            1:T("Visual Recognition"),
            2:T("Physical Description"),
            3:T("Fingerprints"),
            4:T("Dental Profile"),
            5:T("DNA Profile"),
            6:T("Combined Method"),
            9:T("Other Evidence")
        }

        tablename = "dvi_identification"
        define_table(tablename,
                     super_link("pe_id", "pr_pentity"),
                     Field("status", "integer",
                           requires = IS_IN_SET(dvi_id_status, zero=None),
                           default = 1,
                           label = T("Identification Status"),
                           represent = lambda opt: \
                                       dvi_id_status.get(opt, UNKNOWN_OPT)),
                     person_id("identity",
                               label=T("Identified as"),
                               comment = self.person_id_comment("identity"),
                               empty=False),
                     person_id("identified_by",
                               default=current.auth.s3_logged_in_person(),
                               label=T("Identified by"),
                               comment = self.person_id_comment("identified_by"),
                               empty=False),
                     Field("method", "integer",
                           requires = IS_IN_SET(dvi_id_methods, zero=None),
                           default = 1,
                           label = T("Method used"),
                           represent = lambda opt: \
                                       dvi_id_methods.get(opt, UNKNOWN_OPT)),
                     Field("comment", "text"),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Identification Report"),
            title_display = T("Identification Report"),
            title_list = T("Identification Reports"),
            title_update = T("Edit Identification Report"),
            label_list_button = T("List Reports"),
            msg_record_created = T("Report added"),
            msg_record_modified = T("Report updated"),
            msg_record_deleted = T("Report deleted"),
            msg_list_empty = T("No Identification Report Available"))

        # Resource configuration
        configure(tablename,
                  mark_required = ("identity", "identified_by"),
                  list_fields = ["id"],
                  )


        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(dvi_id_status=dvi_id_status)

    # -------------------------------------------------------------------------
    @staticmethod
    def body_onaccept(form):
        """ Update body presence log """

        db = current.db
        table = db.dvi_body
        body = db(table.id == form.vars.id).select(table.uuid,
                                                   table.location_id,
                                                   table.track_id,
                                                   table.date_of_recovery,
                                                   limitby=(0, 1)).first()
        if body and body.location_id:
            tracker = S3Tracker()
            tracker(record=body).set_location(body.location_id,
                                              timestmp=body.date_of_recovery)

    # -------------------------------------------------------------------------
    @staticmethod
    def person_id_comment(fieldname):

        T = current.T

        c_title = T("Person.")
        c_comment = T("Type the first few characters of one of the Person's names.")

        ADD_PERSON = T("Add Person")
        return S3PopupLink(c = "pr",
                           f = "person",
                           vars = {"child": fieldname},
                           label = ADD_PERSON,
                           title = c_title,
                           tooltip = c_comment,
                           )

    # -------------------------------------------------------------------------
    @staticmethod
    def morgue_represent(id):

        if not id:
            return current.messages["NONE"]

        db = current.db
        table = db.dvi_morgue
        row = db(table.id == id).select(table.name,
                                        limitby=(0, 1)).first()
        try:
            return row.name
        except:
            return current.messages.UNKNOWN_OPT

# END =========================================================================
