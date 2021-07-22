# -*- coding: utf-8 -*-

""" Sahana Eden Beneficiary Registry and Case Management Models

    @copyright: 2018-2021 (c) Sahana Software Foundation
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

__all__ = ("BRCaseModel",
           "BRNeedsModel",
           "BRCaseActivityModel",
           "BRAssistanceModel",
           "BRAppointmentModel",
           "BRCaseEventModel",
           "BRPaymentModel",
           "BRNotesModel",
           "BRLanguageModel",
           "BRLegalStatusModel",
           "BRServiceContactModel",
           "BRReferralModel",
           "BRVulnerabilityModel",
           "br_AssistanceMeasureThemeRepresent",
           "br_DocEntityRepresent",
           "br_case_read_orgs",
           "br_case_default_org",
           "br_case_root_org",
           "br_case_default_status",
           "br_case_status_filter_opts",
           "br_case_activity_default_status",
           "br_org_assistance_themes",
           "br_group_membership_onaccept",
           "br_assistance_default_status",
           "br_assistance_status_colors",
           "br_household_size",
           "br_rheader",
           "br_terminology",
           "br_crud_strings",
           "br_person_anonymize",
           )

from collections import OrderedDict

from gluon import *
from gluon.storage import Messages, Storage

from ..s3 import *
from s3compat import long
#from s3layouts import S3PopupLink

CASE_GROUP = 7

# =============================================================================
class BRCaseModel(S3Model):
    """
        Model to register cases ("case registry") and track their processing
        status; uses pr_person for beneficiary person data
    """

    names = ("br_case",
             "br_case_status",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        crud_strings = s3.crud_strings

        define_table = self.define_table
        configure = self.configure

        # ---------------------------------------------------------------------
        # TODO Case Type
        #

        # ---------------------------------------------------------------------
        # Case Status
        #
        tablename = "br_case_status"
        define_table(tablename,
                     Field("code", length=64, notnull=True, unique=True,
                           label = T("Status Code"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       IS_NOT_ONE_OF(db,
                                                     "%s.code" % tablename,
                                                     ),
                                       ],
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Status Code"),
                                                             T("A unique code to identify the status"),
                                                             ),
                                         ),
                           ),
                     Field("name",
                           label = T("Status"),
                           # Prep only, to allow single column imports of cases:
                           #requires = IS_NOT_EMPTY(),
                           ),
                     Field("workflow_position", "integer",
                           default = 1,
                           label = T("Workflow Position"),
                           requires = IS_INT_IN_RANGE(1, None),
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Workflow Position"),
                                                             T("Rank when ordering cases by status"),
                                                             ),
                                         ),
                           ),
                     Field("is_default", "boolean",
                           default = False,
                           label = T("Default Status"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Default Status"),
                                                             T("This status applies for new cases unless specified otherwise"),
                                                             ),
                                         ),
                           ),
                     Field("is_closed", "boolean",
                           default = False,
                           label = T("Case Closed"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Case Closed"),
                                                           T("Cases with this status are closed"),
                                                           ),
                                         ),
                           ),
                     s3_comments(
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Comments"),
                                                             T("Describe the meaning, reasons and potential consequences of this status"),
                                                             ),
                                         ),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Case Status"),
            title_display = T("Case Status"),
            title_list = T("Case Statuses"),
            title_update = T("Edit Case Status"),
            label_list_button = T("List Case Statuses"),
            label_delete_button = T("Delete Case Status"),
            msg_record_created = T("Case Status added"),
            msg_record_modified = T("Case Status updated"),
            msg_record_deleted = T("Case Status deleted"),
            msg_list_empty = T("No Case Statuses currently defined")
            )

        # Table configuration
        configure(tablename,
                  # Allow imports to change the status code:
                  deduplicate = S3Duplicate(primary = ("name",),
                                            ignore_deleted = True,
                                            ),
                  onaccept = self.case_status_onaccept,
                  orderby = "%s.workflow_position" % tablename,
                  )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        status_id = S3ReusableField("status_id", "reference %s" % tablename,
                                    label = T("Case Status"),
                                    ondelete = "RESTRICT",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "br_case_status.id",
                                                          represent,
                                                          orderby = "br_case_status.workflow_position",
                                                          sort = False,
                                                          )),
                                    sortby = "workflow_position",
                                    )

        # ---------------------------------------------------------------------
        # Case: establishes a case file for the beneficiary (=pr_person),
        #       thereby linking the person record to the registry
        #

        # Case assignment options
        if settings.get_br_case_global_default_org():
            default_organisation = settings.get_org_default_organisation()
        else:
            default_organisation = None
        case_manager = settings.get_br_case_manager()

        # Household size tracking
        household_size = settings.get_br_household_size()
        household_size_writable = household_size and household_size != "auto"

        tablename = "br_case"
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),

                     # Case assignment
                     self.org_organisation_id(
                            default = default_organisation,
                            readable = not default_organisation,
                            writable = not default_organisation,
                            ),
                     self.hrm_human_resource_id(
                            label = T("Staff Member in Charge"),
                            comment = DIV(_class = "tooltip",
                                          _title = "%s|%s" % (T("Staff Member in Charge"),
                                                              T("The staff member managing this case"),
                                                              ),
                                          ),
                            represent = self.hrm_HumanResourceRepresent(show_link=False),
                            widget = None,
                            readable = case_manager,
                            writable = case_manager,
                            ),

                     # The beneficiary
                     self.pr_person_id(ondelete = "CASCADE",
                                       ),

                     # Basic date fields
                     s3_date(label = T("Registration Date"),
                             default = "now",
                             empty = False,
                             ),

                     # Case status
                     status_id(),

                     # Household size tracking
                     Field("household_size", "integer",
                           default = 1,
                           label = T("Household Size"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(1, None)),
                           readable = household_size,
                           writable = household_size_writable,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Household Size"),
                                                           T("Number of persons belonging to the same household"),
                                                           ),
                                         ),
                           ),

                     # Invalid flag
                     Field("invalid", "boolean",
                           default = False,
                           label = T("Invalid"),
                           represent = s3_yes_no_represent,
                           # Enabled in controller:
                           readable = False,
                           writable = False,
                           ),

                     # Standard comments and meta fields
                     s3_comments(),
                     *s3_meta_fields())

        # Table Configuration
        self.configure(tablename,
                       create_onaccept = self.case_create_onaccept,
                       update_onaccept = self.case_onaccept,
                       update_realm = True,
                       super_entity = ("doc_entity",),
                       )

        # ---------------------------------------------------------------------
        # TODO Case Details
        #

        # ---------------------------------------------------------------------
        # TODO Case Dates
        #

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        #dummy = S3ReusableField("dummy_id", "integer",
        #                        readable = False,
        #                        writable = False,
        #                        )

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def case_status_onaccept(form):
        """
            Onaccept routine for case statuses:
                - only one status can be the default

            @param form: the FORM
        """

        form_vars = form.vars
        try:
            record_id = form_vars.id
        except AttributeError:
            record_id = None
        if not record_id:
            return

        # If this status is the default, then set is_default-flag
        # for all other statuses to False:
        if "is_default" in form_vars and form_vars.is_default:
            table = current.s3db.br_case_status
            current.db(table.id != record_id).update(is_default = False)

    # -------------------------------------------------------------------------
    @classmethod
    def case_create_onaccept(cls, form):
        """
            Wrapper for case_onaccept when called during create
            rather than update

            @param form: the FORM
        """

        cls.case_onaccept(form, create=True)

    # -------------------------------------------------------------------------
    @staticmethod
    def case_onaccept(form, create=False):
        """
            Case onaccept routine:
            - auto-create active appointments
            - count household size for new cases

            @param form: the FORM
            @param create: perform additional actions for new cases
        """

        db = current.db
        s3db = current.s3db

        # Read form data
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        # Get the case
        ctable = s3db.br_case
        stable = s3db.br_case_status
        left = stable.on(stable.id == ctable.status_id)
        query = (ctable.id == record_id)
        row = db(query).select(ctable.id,
                               ctable.person_id,
                               #ctable.closed_on,
                               stable.is_closed,
                               left = left,
                               limitby = (0, 1),
                               ).first()
        if not row:
            return
        case = row.br_case

        if row.br_case_status.is_closed:

            # TODO Update end date in case
            #if row.br_case_status.is_closed:
            #    if not case.closed_on:
            #        case.update_record(closed_on = current.request.utcnow.date())
            #elif case.closed_on:
            #    case.update_record(closed_on = None)

            atable = s3db.br_case_activity
            stable = s3db.br_case_activity_status

            default_closure = br_case_activity_default_status(closing=True)
            if default_closure:
                join = stable.on((stable.id == atable.status_id) & \
                                 (stable.is_closed == False))
                query = (atable.deleted == False)
                open_activities = db(query).select(atable.id,
                                                   join = join,
                                                   )
                activity_ids = {row.id for row in rows}
                db(atable.id.belongs(activity_ids)).update(status_id = default_closure,
                                                           )
        # Get the person ID
        person_id = case.person_id

        if person_id:
            # Update realm entity throughout the case file
            # in case the org/branch has changed:
            set_realm_entity = current.auth.set_realm_entity

            # Force-update the realm entity for the person record
            # and its primary components
            s3db.configure("pr_person",
                           realm_components = (#"case_details",
                                               "case_language",
                                               "address",
                                               "contact",
                                               "contact_emergency",
                                               "group_membership",
                                               "identity",
                                               "image",
                                               "person_details",
                                               "person_tag",
                                               # TODO
                                               # appointments
                                               # case events
                                               "br_note",
                                               ),
                           )
            set_realm_entity("pr_person", person_id, force_update=True)

            # Force-update the realm entity for all related activities
            atable = s3db.br_case_activity
            query = (atable.person_id == person_id)
            set_realm_entity(atable, query, force_update=True)

            # Force-update the realm entity for all related assistance measures
            mtable = s3db.br_assistance_measure
            query = (mtable.person_id == person_id)
            set_realm_entity(mtable, query, force_update=True)

            # Auto-create standard appointments (if create) TODO

            if create and \
               current.deployment_settings.get_br_household_size() == "auto":
                # Count household size for newly created cases, in order
                # to catch pre-existing case group memberships
                gtable = s3db.pr_group
                mtable = s3db.pr_group_membership
                query = ((mtable.person_id == person_id) & \
                         (mtable.deleted != True) & \
                         (gtable.id == mtable.group_id) & \
                         (gtable.group_type == 7))
                rows = db(query).select(gtable.id)
                for row in rows:
                    br_household_size(row.id)

# =============================================================================
# Process Models
# =============================================================================
class BRCaseActivityModel(S3Model):
    """
        Model for problem/needs-oriented case processing: activities taking
        place in response to individual needs of the beneficiary
    """

    names = ("br_case_activity",
             "br_case_activity_id",
             "br_case_activity_status",
             "br_case_activity_update_type",
             )

    def model(self):

        T = current.T

        db = current.db
        settings = current.deployment_settings
        s3 = current.response.s3
        crud_strings = s3.crud_strings

        define_table = self.define_table
        configure = self.configure

        labels = br_terminology()

        hr_represent = self.hrm_HumanResourceRepresent(show_link=False)

        # ---------------------------------------------------------------------
        # Activity Status
        #
        tablename = "br_case_activity_status"
        define_table(tablename,
                     Field("name",
                           label = T("Status"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("workflow_position", "integer",
                           label = T("Workflow Position"),
                           requires = IS_INT_IN_RANGE(0, None),
                           ),
                     Field("is_default", "boolean",
                           default = False,
                           label = T("Default Status"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("is_closed", "boolean",
                           default = False,
                           label = T("Closes Activity"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("is_default_closed", "boolean",
                           # typically for "obsolete" type of status
                           default = False,
                           label = T("Is default closure status"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Table Configuration
        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("name",),
                                            ignore_deleted = True,
                                            ),
                  onaccept = self.case_activity_status_onaccept,
                  orderby = "%s.workflow_position" % tablename,
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Activity Status"),
            title_display = T("Activity Status Details"),
            title_list = T("Activity Statuses"),
            title_update = T("Edit Activity Status"),
            label_list_button = T("List Activity Statuses"),
            label_delete_button = T("Delete Activity Status"),
            msg_record_created = T("Activity Status created"),
            msg_record_modified = T("Activity Status updated"),
            msg_record_deleted = T("Activity Status deleted"),
            msg_list_empty = T("No Activity Statuses currently defined"),
        )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        status_id = S3ReusableField("status_id",
                                    "reference %s" % tablename,
                                    label = T("Status"),
                                    represent = represent,
                                    requires = IS_ONE_OF(db, "%s.id" % tablename,
                                                         represent,
                                                         orderby = "workflow_position",
                                                         sort = False,
                                                         zero = None,
                                                         ),
                                    sortby = "workflow_position",
                                    )

        # ---------------------------------------------------------------------
        # Activity: generic problem container to track beneficiary support
        #           (subject-based/need-based)
        #
        case_activity_manager = settings.get_br_case_activity_manager()
        case_activity_need = settings.get_br_case_activity_need()
        case_activity_subject = settings.get_br_case_activity_subject()
        case_activity_need_details = settings.get_br_case_activity_need_details()
        case_activity_status = settings.get_br_case_activity_status()
        case_activity_end_date = case_activity_status and \
                                 settings.get_br_case_activity_end_date()

        # Priority options
        priority_opts = [#(0, T("Urgent")),
                         (1, T("High")),
                         (2, T("Normal")),
                         (3, T("Low")),
                         ]
        if settings.get_br_case_activity_urgent_option():
            priority_opts.insert(0, (0, T("Urgent")))

        tablename = "br_case_activity"
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),

                     # Beneficiary
                     self.pr_person_id(comment = None,
                                       empty = False,
                                       label = labels.CASE,
                                       ondelete = "CASCADE",
                                       writable = False,
                                       ),

                     # Case Manager
                     self.hrm_human_resource_id(
                            label = T("Staff Member in Charge"),
                            comment = DIV(_class = "tooltip",
                                          _title = "%s|%s" % (T("Staff Member in Charge"),
                                                              T("The staff member managing this activity"),
                                                              ),
                                          ),
                            represent = hr_represent,
                            widget = None,
                            readable = case_activity_manager,
                            writable = case_activity_manager,
                            ),

                     # Priority
                     Field("priority", "integer",
                           label = T("Priority"),
                           represent = S3PriorityRepresent(priority_opts,
                                                           {0: "red",
                                                            1: "blue",
                                                            2: "lightblue",
                                                            3: "grey",
                                                            }).represent,
                           requires = IS_IN_SET(priority_opts, sort=False, zero=None),
                           default = 2, # normal
                           ),

                     # Subject and Details
                     self.br_need_id(
                            readable = case_activity_need,
                            writable = case_activity_need,
                            ),
                     self.gis_location_id(
                            # Location of the activity,
                            # - usually the current tracking location of the beneficiary
                            # - enable in template if/as necessary
                            readable = False,
                            writable = False,
                            ),
                     Field("subject",
                           label = T("Subject / Occasion"),
                           readable = case_activity_subject,
                           writable = case_activity_subject,
                           ),
                     Field("need_details", "text",
                           label = T("Need Details"),
                           represent = s3_text_represent,
                           widget = s3_comments_widget,
                           readable = case_activity_need_details,
                           writable = case_activity_need_details,
                           # TODO tooltip
                           ),
                     Field("activity_details", "text",
                           label = T("Support provided"),
                           represent = s3_text_represent,
                           widget = s3_comments_widget,
                           ),

                     # Status
                     status_id(readable = case_activity_status,
                               writable = case_activity_status,
                               ),
                     # Dates
                     s3_date(label = T("Date"),
                             default = "now",
                             set_min = "#br_case_activity_end_date",
                             ),
                     s3_date("end_date",
                             label = T("Ended on"),
                             readable = case_activity_end_date,
                             writable = case_activity_end_date == "writable",
                             set_max = "#br_case_activity_date",
                             ),

                     # Outcome
                     Field("outcome", "text",
                           label = T("Outcome"),
                           represent = s3_text_represent,
                           widget = s3_comments_widget,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Components
        self.add_components(tablename,
                            br_case_activity_update = "case_activity_id",
                            br_assistance_measure = "case_activity_id",
                            br_assistance_measure_theme = "case_activity_id",
                            )

        # Optional fields and inline components
        manage_assistance = settings.get_br_manage_assistance()
        if manage_assistance and settings.get_br_assistance_inline():
            # Show inline assistance measures
            assistance = BRAssistanceModel.assistance_inline_component()
        elif not manage_assistance:
            # Show a free-text field to record "support provided"
            assistance = "activity_details"
        else:
            # Track assistance measures on separate tab
            assistance = None

        if settings.get_br_case_activity_updates():
            updates = S3SQLInlineComponent("case_activity_update",
                                           label = T("Progress"),
                                           fields = ["date",
                                                     "update_type_id",
                                                     "human_resource_id",
                                                     "comments",
                                                     ],
                                           layout = S3SQLVerticalSubFormLayout,
                                           explicit_add = T("Add Entry"),
                                           )
        else:
            updates = None

        if settings.get_br_case_activity_outcome():
            outcome = "outcome"
        else:
            outcome = None

        if settings.get_br_case_activity_documents():
            attachments = S3SQLInlineComponent("document",
                                               name = "file",
                                               label = T("Attachments"),
                                               fields = ["file", "comments"],
                                               filterby = {"field": "file",
                                                           "options": "",
                                                           "invert": True,
                                                           },
                                               )
        else:
            attachments = None

        # CRUD form
        crud_fields = ["person_id",
                       "human_resource_id",
                       "priority",
                       "date",
                       "need_id",
                       "subject",
                       "need_details",
                       "location_id",
                       assistance,
                       "status_id",
                       updates,
                       "end_date",
                       outcome,
                       attachments,
                       "comments",
                       ]

        # List fields (for case file tab)
        list_fields = ["priority",
                       "date",
                       #"need_id",
                       #"subject",
                       #"human_resource_id",
                       #"status_id",
                       #"end_date",
                       ]
        append = list_fields.append
        if case_activity_need:
            append("need_id")
        if case_activity_subject:
            append("subject")
        if case_activity_manager:
            append("human_resource_id")
        if case_activity_status:
            append("status_id")
        if case_activity_end_date:
            append("end_date")

        # Table configuration
        configure(tablename,
                  crud_form = S3SQLCustomForm(*crud_fields),
                  list_fields = list_fields,
                  onaccept = self.case_activity_onaccept,
                  orderby = "br_case_activity.priority",
                  realm_components = ("case_activity_update",
                                      ),
                  super_entity = "doc_entity",
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Activity"),
            title_display = T("Activity Details"),
            title_list = T("Activities"),
            title_report = T("Activity Statistic"),
            title_update = T("Edit Activity"),
            label_list_button = T("List Activities"),
            label_delete_button = T("Delete Activity"),
            msg_record_created = T("Activity added"),
            msg_record_modified = T("Activity updated"),
            msg_record_deleted = T("Activity deleted"),
            msg_list_empty = T("No Activities currently registered"),
            )

        # Reusable field
        if case_activity_subject:
            label = T("Subject")
            show_as = "subject"
            show_date = False
        else:
            label = T("Need")
            show_as = "need"
            show_date = True
        represent = br_CaseActivityRepresent(show_as = show_as,
                                             show_date = show_date,
                                             show_link = True,
                                             )
        if show_date:
            # Don't alphasort, show latest first
            sort, orderby = False, "%s.date desc" % tablename
        else:
            sort, orderby = True, None
        case_activity_id = S3ReusableField("case_activity_id",
                                           "reference %s" % tablename,
                                           label = label,
                                           ondelete = "CASCADE",
                                           represent = represent,
                                           requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "%s.id" % tablename,
                                                                  represent,
                                                                  orderby = orderby,
                                                                  sort = sort,
                                                                  )),
                                                        )

        # ---------------------------------------------------------------------
        # Activity Update Type:
        # - describes the occasion (reason) for an update entry
        #
        tablename = "br_case_activity_update_type"
        define_table(tablename,
                     Field("name",
                           label = T("Occasion"),
                           requires = IS_NOT_EMPTY(),
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Occasion"),
                                                             T("The occasion (reason) for an activity update"),
                                                             ),
                                         ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Table configuration
        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Update Type"),
            title_display = T("Update Type Details"),
            title_list = T("Update Types"),
            title_update = T("Edit Update Type"),
            label_list_button = T("List Update Types"),
            label_delete_button = T("Delete Update Type"),
            msg_record_created = T("Update Type added"),
            msg_record_modified = T("Update Type updated"),
            msg_record_deleted = T("Update Type deleted"),
            msg_list_empty = T("No Update Types currently defined"),
            )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        update_type_id = S3ReusableField("update_type_id",
                                         "reference %s" % tablename,
                                         label = T("Occasion"),
                                         represent = represent,
                                         requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "%s.id" % tablename,
                                                                  represent,
                                                                  )),
                                         sortby = "name",
                                         )

        # ---------------------------------------------------------------------
        # Activity Updates: inline-journal to document progress
        #
        tablename = "br_case_activity_update"
        define_table(tablename,
                     case_activity_id(),
                     s3_date(default = "now",
                             ),
                     update_type_id(),
                     self.hrm_human_resource_id(
                            comment = None,
                            represent = hr_represent,
                            widget = None,
                            ),
                     s3_comments(),
                     *s3_meta_fields())

        # Table configuration
        configure(tablename,
                  orderby = "%s.date" % tablename,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"br_case_activity_id": case_activity_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return {"br_case_activity_id": lambda **attr: dummy("case_activity_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def case_activity_status_onaccept(form):
        """
            Onaccept routine for activity statuses:
            - only one status can be the default
            - only one status can be the default closure

            @param form: the FORM
        """

        form_vars = form.vars
        try:
            record_id = form_vars.id
        except AttributeError:
            record_id = None
        if not record_id:
            return

        update = {}

        # Ensure that there is only one default status
        if "is_default" in form_vars and form_vars.is_default:
            update["is_default"] = False

        # Ensure that there is only one default closure status
        if "is_default_closed" in form_vars and form_vars.is_default_closed:
            update["is_default_closed"] = False

        if update:
            table = current.s3db.br_case_activity_status
            current.db(table.id != record_id).update(**update)

    # -------------------------------------------------------------------------
    @staticmethod
    def case_activity_onaccept(form):
        """
            Onaccept-callback for case activites:
                - set end date when marked as completed
        """

        db = current.db
        s3db = current.s3db

        # Read form data
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        # Get current status and end_date of the record
        atable = s3db.br_case_activity
        stable = s3db.br_case_activity_status

        join = stable.on(stable.id == atable.status_id)
        query = (atable.id == record_id)

        row = db(query).select(atable.id,
                               atable.end_date,
                               stable.is_closed,
                               join = join,
                               limitby = (0, 1),
                               ).first()
        if row:
            data = {}
            activity = row.br_case_activity

            if row.br_case_activity_status.is_closed:
                # Set the end-date if it hasn't been set before
                if not activity.end_date:
                    data["end_date"] = current.request.utcnow.date()
            elif activity.end_date:
                # Remove the end-date
                data["end_date"] = None

# =============================================================================
class BRAppointmentModel(S3Model):
    """
        Model for workflow-oriented case processing: cases must pass a number
        of predefined processing steps (=appointments) in order to achieve a
        certain outcome/status
    """

    names = ("br_appointment",
             "br_appointment_type",
             )

    def model(self):

        # TODO explain entities
        # TODO controllers
        # TODO case file tab
        # TODO auto-create when creating cases
        # TODO import option/prepop for appointment types
        # TODO automatic case status updates
        # TODO mandatory appointments
        # TODO presence_required and last_seen

        T = current.T
        db = current.db
        #settings = current.deployment_settings

        crud_strings = current.response.s3.crud_strings

        configure = self.configure
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Appointment Type
        #
        tablename = "br_appointment_type"
        define_table(tablename,
                     Field("name", length=64, notnull=True, unique=True,
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       IS_NOT_ONE_OF(db,
                                                     "%s.name" % tablename,
                                                     ),
                                       ],
                           ),
                     Field("autocreate", "boolean",
                           default = True,
                           label = T("Create automatically"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Create automatically"),
                                                             T("Automatically create this appointment for new cases"),
                                                             ),
                                         ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Appointment Type"),
            title_display = T("Appointment Type Details"),
            title_list = T("Appointment Types"),
            title_update = T("Edit Appointment Type"),
            label_list_button = T("List Appointment Types"),
            label_delete_button = T("Delete Appointment Type"),
            msg_record_created = T("Appointment Type added"),
            msg_record_modified = T("Appointment Type updated"),
            msg_record_deleted = T("Appointment Type deleted"),
            msg_list_empty = T("No Appointment Types currently registered"),
            )

        # Reusable Field
        represent = S3Represent(lookup=tablename, translate=True)
        appointment_type_id = S3ReusableField("type_id", "reference %s" % tablename,
                                              label = T("Appointment Type"),
                                              ondelete = "RESTRICT",
                                              represent = represent,
                                              requires = IS_EMPTY_OR(
                                                              IS_ONE_OF(db, "%s.id" % tablename,
                                                                        represent,
                                                                        )),
                                              )

        # ---------------------------------------------------------------------
        # Appointment
        #
        # TODO reduce statuses
        appointment_status_opts = {1: T("Planning"),
                                   2: T("Planned"),
                                   3: T("In Progress"),
                                   4: T("Completed"),
                                   5: T("Missed"),
                                   6: T("Cancelled"),
                                   7: T("Not Required"),
                                   }

        tablename = "br_appointment"
        define_table(tablename,
                     self.pr_person_id(comment = None,
                                       empty = False,
                                       ondelete = "CASCADE",
                                       writable = False,
                                       ),
                     appointment_type_id(empty = False,
                                         ),
                     s3_date(),
                     # Activate in template as needed:
                     self.hrm_human_resource_id(readable=False,
                                                writable=False,
                                                ),
                     Field("status", "integer",
                           default = 1, # Planning
                           requires = IS_IN_SET(appointment_status_opts,
                                                zero = None,
                                                ),
                           represent = S3Represent(options = appointment_status_opts,
                                                   ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Appointment"),
            title_display = T("Appointment Details"),
            title_list = T("Appointments"),
            title_update = T("Edit Appointment"),
            label_list_button = T("List Appointments"),
            label_delete_button = T("Delete Appointment"),
            msg_record_created = T("Appointment added"),
            msg_record_modified = T("Appointment updated"),
            msg_record_deleted = T("Appointment deleted"),
            msg_list_empty = T("No Appointments currently registered"),
            )

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("person_id",
                                                       "type_id",
                                                       ),
                                            ),
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        #dummy = S3ReusableField("dummy_id", "integer",
        #                        readable = False,
        #                        writable = False,
        #                        )

        return {}

# =============================================================================
# Category Models
# =============================================================================
class BRNeedsModel(S3Model):
    """ Model for Need Categories """

    names = ("br_need",
             "br_need_id",
             )

    def model(self):

        T = current.T
        db = current.db

        settings = current.deployment_settings
        crud_strings = current.response.s3.crud_strings

        hierarchical_needs = settings.get_br_needs_hierarchical()
        org_specific_needs = settings.get_br_needs_org_specific()

        # ---------------------------------------------------------------------
        # Needs: categories of things a beneficiary needs, e.g. shelter,
        #        protection, water, food, psychological support...
        #
        tablename = "br_need"
        self.define_table(tablename,
                          Field("name",
                                label = T("Need"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          # This form of hierarchy may not work on all Databases:
                          Field("parent", "reference br_need",
                                label = T("Subtype of"),
                                ondelete = "RESTRICT",
                                readable = hierarchical_needs,
                                writable = hierarchical_needs,
                                ),
                          self.org_organisation_id(readable = org_specific_needs,
                                                   writable = org_specific_needs,
                                                   ),
                          # Activate in template as needed:
                          Field("protection", "boolean",
                                default = False,
                                label = T("Protection Need"),
                                comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (T("Protection Need"),
                                                                  T("This need type indicates a particular need for protection"),
                                                                  ),
                                              ),
                                represent = s3_yes_no_represent,
                                readable = False,
                                writable = False,
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        # Hierarchy
        if hierarchical_needs:
            hierarchy = "parent"
            widget = S3HierarchyWidget(multiple = False,
                                       leafonly = False,
                                       )
        else:
            hierarchy = None
            widget = None

        # Table configuration
        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("name",),
                                                 secondary = ("parent",
                                                              "organisation_id",
                                                              ),
                                                 ),
                       hierarchy = hierarchy,
                       )

        # CRUD Strings
        ADD_NEED = T("Create Need Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_NEED,
            title_display = T("Need Type Details"),
            title_list = T("Need Types"),
            title_update = T("Edit Need Type"),
            label_list_button = T("List Need Types"),
            label_delete_button = T("Delete Need Type"),
            msg_record_created = T("Need Type added"),
            msg_record_modified = T("Need Type updated"),
            msg_record_deleted = T("Need Type deleted"),
            msg_list_empty = T("No Need Types found"),
            )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        need_id = S3ReusableField("need_id", "reference %s" % tablename,
                                  label = T("Need Type"),
                                  ondelete = "RESTRICT",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "%s.id" % tablename,
                                                          represent,
                                                          )),
                                  #comment = S3PopupLink(c = "br",
                                  #                      f = "need",
                                  #                      title = ADD_NEED,
                                  #                      tooltip = T("Choose the need type from the drop-down, or click the link to create a new type"),
                                  #                      ),
                                  widget = widget,
                                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"br_need_id": need_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return {"br_need_id": lambda **attr: dummy("need_id", **attr),
                }

# =============================================================================
# Assistance Models
# =============================================================================
class BRAssistanceModel(S3Model):
    """
        Generic model to track individual measures of assistance
    """

    names = ("br_assistance_measure",
             "br_assistance_measure_theme",
             "br_assistance_offer",
             "br_assistance_status",
             "br_assistance_theme",
             "br_assistance_type",
             "br_assistance_offer_status",
             "br_assistance_offer_availability",
             )

    def model(self):

        T = current.T

        db = current.db
        settings = current.deployment_settings
        s3 = current.response.s3
        crud_strings = s3.crud_strings

        define_table = self.define_table
        configure = self.configure

        labels = br_terminology()
        NONE = current.messages["NONE"]

        case_activity_id = self.br_case_activity_id

        # ---------------------------------------------------------------------
        # Assistance Theme
        #
        org_specific_themes = settings.get_br_assistance_themes_org_specific()
        themes_sectors = settings.get_br_assistance_themes_sectors()
        themes_needs = settings.get_br_assistance_themes_needs()

        tablename = "br_assistance_theme"
        define_table(tablename,
                     self.org_organisation_id(
                         comment = None,
                         readable = org_specific_themes,
                         writable = org_specific_themes,
                         ),
                     Field("name",
                           label = T("Theme"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     self.org_sector_id(readable = themes_sectors,
                                        writable = themes_sectors,
                                        ),
                     self.br_need_id(readable = themes_needs,
                                     writable = themes_needs,
                                     ),
                     s3_comments(),
                     *s3_meta_fields())

        # Table configuration
        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("name",),
                                            secondary = ("organisation_id",),
                                            ),
                  ondelete_cascade = self.assistance_theme_ondelete_cascade,
                  )

        # CRUD strings
        crud_strings[tablename] = br_crud_strings(tablename)

        # Reusable field
        themes_represent = br_AssistanceThemeRepresent(multiple=True)
        requires = IS_ONE_OF(db, "%s.id" % tablename,
                             themes_represent,
                             multiple = True,
                             )
        if org_specific_themes:
            root_org = current.auth.root_org()
            if root_org:
                requires.set_filter(filterby = "organisation_id",
                                    filter_opts = (root_org,),
                                    )
        theme_ids = S3ReusableField("theme_ids",
                                    "list:reference %s" % tablename,
                                    label = T("Themes"),
                                    ondelete = "RESTRICT",
                                    represent = themes_represent,
                                    requires = IS_EMPTY_OR(requires),
                                    sortby = "name",
                                    widget = S3MultiSelectWidget(header = False,
                                                                 ),
                                    )

        # ---------------------------------------------------------------------
        # Types of Assistance
        #
        tablename = "br_assistance_type"
        define_table(tablename,
                     Field("name",
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Table configuration
        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Type"),
            title_display = T("Assistance Type Details"),
            title_list = T("Types of Assistance"),
            title_update = T("Edit Type"),
            label_list_button = T("List Types"),
            label_delete_button = T("Delete Type"),
            msg_record_created = T("Type created"),
            msg_record_modified = T("Type updated"),
            msg_record_deleted = T("Type deleted"),
            msg_list_empty = T("No Types of Assistance currently defined"),
            )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        assistance_type_id = S3ReusableField(
                                "assistance_type_id",
                                "reference %s" % tablename,
                                label = T("Type of Assistance"),
                                represent = represent,
                                requires = IS_EMPTY_OR(
                                            IS_ONE_OF(db, "%s.id" % tablename,
                                                      represent,
                                                      )),
                                sortby = "name",
                                )

        # ---------------------------------------------------------------------
        # Offers of assistance
        #
        offer_availability = (("AVL", T("available")),
                              ("OCP", T("occupied")),
                              ("RTD", T("no longer available")),
                              )
        offer_status = (("NEW", T("new")),
                        ("APR", T("approved")),
                        ("BLC", T("blocked")),
                        )

        # Representation of provider
        pe_represent = self.pr_PersonEntityRepresent(show_label = False,
                                                     show_link = False,
                                                     show_type = True,
                                                     )
        tablename = "br_assistance_offer"
        define_table(tablename,
                     self.event_event_id(),
                     Field("pe_id", "reference pr_pentity",
                           label = T("Provider##assistance"),
                           represent = pe_represent,
                           requires = IS_EMPTY_OR(IS_ONE_OF(db, "pr_pentity.pe_id",
                                                            pe_represent,
                                                            instance_types = ["pr_person",
                                                                              "org_organisation",
                                                                              ],
                                                            )),
                           ),
                     self.br_need_id(),
                     assistance_type_id(
                         # Enable in template if/as required
                         readable = False,
                         writable = False,
                         ),
                     Field("name",
                           label = T("Offer"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("description", "text",
                           label = T("Details"),
                           represent = s3_text_represent,
                           widget = s3_comments_widget,
                           ),
                     Field("capacity",
                           label = T("Quantity / Size / Capacity"),
                           represent = lambda v, row=None: v if v else "-",
                           ),
                     Field("chargeable", "boolean",
                           default = False,
                           label = T("Chargeable"),
                           represent = s3_yes_no_represent,
                           ),
                     self.gis_location_id(), # Location of the offer (if housing)
                     s3_date(label = T("Available from"),
                             default = "now",
                             # TODO setmin
                             ),
                     s3_date("end_date",
                             label = T("Available until"),
                             # TODO setmax
                             ),
                     Field("contact_name",
                           label = T("Contact Name"),
                           represent = lambda v, row=None: v if v else "-",
                           ),
                     Field("contact_email",
                           label = T("Email"),
                           requires = IS_EMPTY_OR(IS_EMAIL()),
                           represent = lambda v, row=None: v if v else "-",
                           ),
                     Field("contact_phone",
                           label = T("Contact Phone"),
                           requires = IS_EMPTY_OR(IS_PHONE_NUMBER_SINGLE()),
                           represent = lambda v, row=None: v if v else "-",
                           ),
                     Field("availability",
                           default = "AVL",
                           label = T("Availability"),
                           requires = IS_IN_SET(offer_availability, zero=None, sort=False),
                           represent = S3Represent(options=dict(offer_availability),
                                                   ),
                           ),
                     Field("status",
                           default = "NEW",
                           label = T("Status"),
                           requires = IS_IN_SET(offer_status, zero=None, sort=False),
                           represent = S3Represent(options=dict(offer_status),
                                                   ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # List fields
        list_fields = ["need_id",
                       "name",
                       "chargeable",
                       "location_id",
                       "availability",
                       "date",
                       "end_date",
                       ]

        # Filters
        filter_widgets = [S3TextFilter(["name",
                                        "description",
                                        ],
                                       label = T("Search"),
                                       ),
                          S3OptionsFilter("need_id",
                                          ),
                          S3OptionsFilter("chargeable",
                                          cols = 2,
                                          ),
                          S3LocationFilter("location_id",
                                           ),
                          ]

        self.configure(tablename,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Assistance Offer"),
            title_display = T("Assistance Offer Details"),
            title_list = T("Assistance Offers"),
            title_update = T("Edit Offer"),
            label_list_button = T("List Offers"),
            label_delete_button = T("Delete Offer"),
            msg_record_created = T("Offer created"),
            msg_record_modified = T("Offer updated"),
            msg_record_deleted = T("Offer deleted"),
            msg_list_empty = T("No Assistance Offers currently registered"),
            )

        # ---------------------------------------------------------------------
        # Status of Assistance
        #
        tablename = "br_assistance_status"
        define_table(tablename,
                     Field("workflow_position", "integer",
                           label = T("Workflow Position"),
                           requires = IS_INT_IN_RANGE(0, None),
                           ),
                     Field("name",
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("is_default", "boolean",
                           default = False,
                           label = T("Default Initial Status"),
                           ),
                     Field("is_termination", "boolean",
                           default = False,
                           label = T("Terminates the Measure"),
                           ),
                     Field("is_default_termination", "boolean",
                           default = False,
                           label = T("Default Termination"),
                           ),
                     Field("color",
                           requires = IS_HTML_COLOUR(),
                           widget = S3ColorPickerWidget(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Table Configuration
        configure(tablename,
                  deduplicate = S3Duplicate(),
                  onaccept = self.assistance_status_onaccept,
                  orderby = "%s.workflow_position" % tablename,
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Status"),
            title_display = T("Status Details"),
            title_list = T("Assistance Statuses"),
            title_update = T("Edit Status"),
            label_list_button = T("List Statuses"),
            label_delete_button = T("Delete Status"),
            msg_record_created = T("Status created"),
            msg_record_modified = T("Status updated"),
            msg_record_deleted = T("Status deleted"),
            msg_list_empty = T("No Assistance Statuses currently defined"),
        )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        assistance_status_id = S3ReusableField(
                                "status_id",
                                "reference %s" % tablename,
                                label = T("Status"),
                                represent = represent,
                                requires = IS_ONE_OF(db, "%s.id" % tablename,
                                                     represent,
                                                     orderby = "workflow_position",
                                                     sort = False,
                                                     zero = None,
                                                     ),
                                sortby = "workflow_position",
                                )

        # ---------------------------------------------------------------------
        # Measures of Assistance
        #
        use_type = settings.get_br_assistance_types()
        use_themes = settings.get_br_assistance_themes()
        assistance_manager = settings.get_br_assistance_manager()
        track_effort = settings.get_br_assistance_track_effort()
        use_activities = settings.get_br_case_activities()

        use_time = settings.get_br_assistance_measures_use_time()

        tablename = "br_assistance_measure"
        define_table(tablename,
                     # Beneficiary
                     self.pr_person_id(
                         comment = None,
                         empty = False,
                         label = labels.CASE,
                         widget = S3PersonAutocompleteWidget(controller="br"),
                         ),
                     case_activity_id(
                         readable = use_activities,
                         writable = use_activities,
                         ),
                     s3_datetime("start_date",
                                 label = T("Date"),
                                 default = "now",
                                 widget = None if use_time else "date",
                                 ),
                     s3_datetime("end_date",
                                 label = T("End"),
                                 widget = None if use_time else "date",
                                 readable = False,
                                 writable = False,
                                 ),
                     assistance_type_id(readable = use_type,
                                        writable = use_type,
                                        ),
                     theme_ids(readable = use_themes,
                               writable = use_themes,
                               ),
                     assistance_status_id(),
                     self.hrm_human_resource_id(
                        comment = None,
                        represent = self.hrm_HumanResourceRepresent(show_link=False),
                        widget = None,
                        readable = assistance_manager,
                        writable = assistance_manager,
                        ),
                     Field("hours", "double",
                           label = T("Effort (Hours)"),
                           requires = IS_EMPTY_OR(
                                       IS_FLOAT_IN_RANGE(0.0, None)),
                           represent = lambda hours: "%.2f" % hours if hours else NONE,
                           widget = S3HoursWidget(precision = 2,
                                                  ),
                           readable = track_effort,
                           writable = track_effort,
                           ),
                     s3_comments(label = T("Details"),
                                 comment = None,
                                 represent = lambda v: s3_text_represent(v, lines=8),
                                 ),
                     *s3_meta_fields())

        # Components
        self.add_components(tablename,
                            br_assistance_measure_theme = "measure_id",
                            )

        # CRUD form
        crud_fields = ["person_id",
                       "start_date",
                       #"case_activity_id",
                       "assistance_type_id",
                       #"theme_ids" | inline theme links,
                       #"comments",
                       "human_resource_id",
                       "hours",
                       "status_id",
                       ]
        details_per_theme = settings.get_br_assistance_details_per_theme()
        autolink = settings.get_br_assistance_activity_autolink()
        if use_themes and details_per_theme:
            if autolink:
                pos = 3
            else:
                crud_fields.insert(2, "case_activity_id")
                pos = 4
            crud_fields.insert(pos, S3SQLInlineComponent("assistance_measure_theme",
                                                         fields = ["theme_id",
                                                                   "comments",
                                                                   ],
                                                         label = T("Details"),
                                                         ))
        else:
            crud_fields.insert(2, "case_activity_id")
            crud_fields[4:4] = ["theme_ids",
                                "comments",
                                ]
        crud_form = S3SQLCustomForm(*crud_fields)

        # List_fields (for component tab, master perspective see controller)
        list_fields = ["start_date",
                       #"case_activity_id",
                       #"assistance_type_id",
                       #"theme_ids" | measure-theme links,
                       #"comments",
                       #"human_resource_id",
                       #"hours",
                       "status_id",
                       ]

        if not details_per_theme:
            list_fields.insert(1, "comments")
        if use_themes:
            if details_per_theme:
                list_fields.insert(1, (T("Themes"), "assistance_measure_theme.id"))
            else:
                list_fields.insert(1, "theme_ids")
        if use_type:
            list_fields.insert(1, "assistance_type_id")
        if use_activities and not autolink:
            list_fields.insert(1, "case_activity_id")
        if assistance_manager:
            list_fields.insert(-1, "human_resource_id")
        if track_effort:
            list_fields.insert(-1, "hours")

        # Filter widgets
        filter_widgets = [S3TextFilter(["person_id$pe_label",
                                        "person_id$first_name",
                                        "person_id$middle_name",
                                        "person_id$last_name",
                                        "comments",
                                        ],
                                       label = T("Search"),
                                       ),
                          S3OptionsFilter("status_id",
                                          options = lambda: s3_get_filter_opts("br_assistance_status"),
                                          cols = 3,
                                          translate = True,
                                          ),
                          S3DateFilter("start_date",
                                       hidden = True,
                                       hide_time = not use_time,
                                       ),
                          ]
        if use_type:
            filter_widgets.append(S3OptionsFilter("assistance_type_id",
                                                  hidden = True,
                                                  options = lambda: s3_get_filter_opts("br_assistance_type"),
                                                  ))
        if use_themes:
            filter_widgets.append(S3OptionsFilter("theme_ids",
                                                  hidden = True,
                                                  options = lambda: s3_get_filter_opts("br_assistance_theme"),
                                                  ))

        # Organizer
        description = ["status_id"]
        if assistance_manager:
            description.insert(0, "human_resource_id")
        if use_themes:
            description.insert(0, "theme_ids")
        if use_type:
            description.insert(0, "assistance_type_id")
        #if not use_themes or not details_per_theme:
        #    description.insert(0, "comments")
        organize = {"start": "start_date",
                    "title": "person_id",
                    "description": description,
                    "color": "status_id",
                    "colors": br_assistance_status_colors,
                    }
        if use_time:
            organize["end"] = "end_date"
        else:
            organize["use_time"] = False

        # Table Configuration
        configure(tablename,
                  crud_form = crud_form,
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  organize = organize,
                  onaccept = self.assistance_measure_onaccept,
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Measure"),
            title_display = T("Measure Details"),
            title_list = T("Measures"),
            title_update = T("Edit Measure"),
            label_list_button = T("List Measures"),
            label_delete_button = T("Delete Measure"),
            msg_record_created = T("Measure created"),
            msg_record_modified = T("Measure updated"),
            msg_record_deleted = T("Measure deleted"),
            msg_list_empty = T("No Measures currently registered"),
        )

        # ---------------------------------------------------------------------
        # Measure <=> Theme link table
        #
        theme_represent = br_AssistanceThemeRepresent(multiple=False)
        measure_represent = br_AssistanceMeasureRepresent()
        tablename = "br_assistance_measure_theme"
        define_table(tablename,
                     Field("measure_id", "reference br_assistance_measure",
                           label = T("Measure"),
                           ondelete = "CASCADE",
                           represent = measure_represent,
                           requires = IS_ONE_OF(db, "br_assistance_measure.id",
                                                measure_represent,
                                                ),
                           ),
                     Field("theme_id", "reference br_assistance_theme",
                           label = T("Theme"),
                           # NB ondelete should be the same as for
                           #    br_assistance_measure.theme_ids:
                           ondelete = "RESTRICT",
                           represent = theme_represent,
                           requires = IS_ONE_OF(db, "br_assistance_theme.id",
                                                theme_represent,
                                                ),
                           ),
                     case_activity_id(ondelete = "SET NULL",
                                      readable = False,
                                      writable = False,
                                      ),
                     s3_comments(label = T("Details"),
                                 comment = None,
                                 represent = lambda v: s3_text_represent(v, lines=8),
                                 ),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = self.assistance_measure_theme_onaccept,
                  ondelete = self.assistance_measure_theme_ondelete,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"br_assistance_offer_status": offer_status,
                "br_assistance_offer_availability": offer_availability,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        return {"br_assistance_offer_status": (),
                "br_assistance_offer_availability": (),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def assistance_theme_ondelete_cascade(row):
        """
            Explicit deletion cascade for assistance theme list:references
            (which are not caught by standard cascade), action depending
            on "ondelete" setting of assistance_measure.theme_ids:
                - RESTRICT  => block deletion cascade
                - otherwise => clean up the list:reference

            @param row: the br_assistance_theme Row to be deleted
        """

        db = current.db

        # Table with list:reference br_assistance_theme
        mtable = current.s3db.br_assistance_measure
        reference = mtable.theme_ids

        # Referencing rows
        theme_id = row.id
        query = (reference.contains(theme_id)) & (mtable.deleted == False)
        if reference.ondelete == "RESTRICT":
            measures = db(query).select(mtable.id,
                                        limitby = (0, 1),
                                        ).first()
            if measures:
                # Raise to stop deletion cascade
                raise RuntimeError("Attempt to delete a theme that is referenced in a measure")
        else:
            measures = db(query).select(mtable.id, reference)
            for measure in measures:
                # Clean up reference list
                theme_ids = measure[reference]
                measure.update_record(theme_ids = [tid for tid in theme_ids
                                                        if tid != theme_id])

    # -------------------------------------------------------------------------
    @staticmethod
    def assistance_status_onaccept(form):
        """
            Onaccept routine for assistance statuses:
            - only one status can be the default
            - only one status can be the default termination

            @param form: the FORM
        """

        form_vars = form.vars
        try:
            record_id = form_vars.id
        except AttributeError:
            record_id = None
        if not record_id:
            return

        table = current.s3db.br_assistance_status
        db = current.db

        if form_vars.get("is_default"):
            db(table.id != record_id).update(is_default = False)

        if form_vars.get("is_default_termination"):
            db(table.id == record_id).update(is_termination = True)
            db(table.id != record_id).update(is_default_termination = False)

    # -------------------------------------------------------------------------
    @staticmethod
    def assistance_measure_onaccept(form):
        """
            Onaccept routine for assistance measures
                - update theme links from inline theme_ids
        """

        form_vars = form.vars
        try:
            record_id = form_vars.id
        except AttributeError:
            record_id = None
        if not record_id:
            return

        db = current.db
        s3db = current.s3db

        # Get the record
        mtable = s3db.br_assistance_measure
        query = (mtable.id == record_id)
        record = db(query).select(mtable.id,
                                  mtable.theme_ids,
                                  mtable.case_activity_id,
                                  limitby = (0, 1),
                                  ).first()
        if not record:
            return

        if "theme_ids" in form_vars:
            theme_ids = record.theme_ids
            if not theme_ids:
                theme_ids = []

            # Get all selected themes
            selected = set(theme_ids)

            # Get all linked themes
            ltable = s3db.br_assistance_measure_theme
            query = (ltable.measure_id == record_id) & \
                    (ltable.deleted == False)
            links = db(query).select(ltable.theme_id)
            linked = set(link.theme_id for link in links)

            # Remove obsolete theme links
            obsolete = linked - selected
            if obsolete:
                query &= ltable.theme_id.belongs(obsolete)
                db(query).delete()

            # Inline-created theme links inherit case_activity_id
            case_activity_id = record.case_activity_id

            # Add links for newly selected themes
            added = selected - linked
            for theme_id in added:
                ltable.insert(measure_id = record_id,
                              theme_id = theme_id,
                              case_activity_id = case_activity_id,
                              )

    # -------------------------------------------------------------------------
    @staticmethod
    def get_case_activity_by_need(person_id, need_id, hr_id=None):
        """
            DRY helper to find or create a case activity matching a need_id

            @param person_id: the beneficiary person ID
            @param need_id: the need ID (or a list of need IDs)
            @param human_resource_id: the HR responsible

            @returns: a br_case_activity record ID
        """

        if not person_id:
            return None

        s3db = current.s3db
        table = s3db.br_case_activity

        # Look up a matching case activity for this beneficiary
        query = (table.person_id == person_id)
        if isinstance(need_id, (list, tuple)):
            need = need_id[0] if len(need_id) == 1 else None
            query &= (table.need_id.belongs(need_id))
        else:
            need = need_id
            query &= (table.need_id == need_id)
        query &= (table.deleted == False)
        activity = current.db(query).select(table.id,
                                            orderby = ~table.date,
                                            limitby = (0, 1),
                                            ).first()
        if activity:
            activity_id = activity.id
        elif need is not None:
            # Create an activity for the case
            activity_id = table.insert(person_id = person_id,
                                       need_id = need,
                                       start_date = current.request.utcnow,
                                       human_resource_id = hr_id,
                                       )
            s3db.update_super(table, {"id": activity_id})
        else:
            activity_id = None

        return activity_id

    # -------------------------------------------------------------------------
    @classmethod
    def assistance_measure_theme_onaccept(cls, form):
        """
            Onaccept routine for measure-theme links
                - update theme_ids in measure record
                - link to case activity if required
        """

        form_vars = form.vars
        try:
            record_id = form_vars.id
        except AttributeError:
            record_id = None
        if not record_id:
            return

        db = current.db
        s3db = current.s3db

        # Look up the record
        table = s3db.br_assistance_measure_theme
        query = (table.id == record_id)
        record = db(query).select(table.id,
                                  table.measure_id,
                                  table.theme_id,
                                  table.comments,
                                  limitby = (0, 1),
                                  ).first()
        if not record:
            return

        # Look up the measure
        measure_id = record.measure_id
        if measure_id:
            mtable = s3db.br_assistance_measure
            query = (mtable.id == measure_id)
            measure = db(query).select(mtable.id,
                                       mtable.person_id,
                                       mtable.human_resource_id,
                                       limitby = (0, 1),
                                       ).first()
        else:
            measure = None

        if measure:
            theme_id = record.theme_id
            if theme_id:

                # Merge duplicate measure-theme links
                query = (table.id != record.id) & \
                        (table.measure_id == measure_id) & \
                        (table.theme_id == record.theme_id) & \
                        current.auth.s3_accessible_query("delete", table) & \
                        (table.deleted == False)
                rows = db(query).select(table.id,
                                        table.comments,
                                        orderby = table.created_on,
                                        )
                duplicates = []
                details = []
                for row in rows:
                    if row.comments:
                        details.append(row.comments.strip())
                    duplicates.append(row.id)
                if record.comments:
                    details.append(record.comments.strip())

                record.update_record(comments="\n\n".join(c for c in details if c))
                s3db.resource("br_assistance_measure_theme", id=duplicates).delete()

            # Update theme_ids in the measure
            query = (table.measure_id == measure_id) & \
                    (table.deleted == False)
            rows = db(query).select(table.theme_id)
            theme_ids = [row.theme_id for row in rows if row.theme_id]
            measure.update_record(theme_ids=theme_ids)

            # Auto-link to case activity
            settings = current.deployment_settings
            if settings.get_br_case_activity_need() and \
               settings.get_br_assistance_themes_needs() and \
               settings.get_br_assistance_activity_autolink():

                # Look up the theme's need_id
                ttable = s3db.br_assistance_theme
                query = (ttable.id == record.theme_id)
                theme = db(query).select(ttable.need_id, limitby=(0, 1)).first()
                if theme:
                    activity_id = cls.get_case_activity_by_need(
                                            measure.person_id,
                                            theme.need_id,
                                            hr_id = measure.human_resource_id,
                                            )
                    record.update_record(case_activity_id=activity_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def assistance_measure_theme_ondelete(row):
        """
            On-delete actions for measure-theme links
                - update theme_ids in measure record
        """

        db = current.db
        s3db = current.s3db

        # Look up the measure
        measure_id = row.measure_id
        if measure_id:
            mtable = s3db.br_assistance_measure
            query = (mtable.id == measure_id)
            measure = db(query).select(mtable.id, limitby = (0, 1)).first()
        else:
            measure = None

        if measure:
            # Update theme_ids in the measure
            table = s3db.br_assistance_measure_theme
            query = (table.measure_id == measure_id) & \
                    (table.deleted == False)
            rows = db(query).select(table.theme_id)
            theme_ids = [row.theme_id for row in rows if row.theme_id]
            measure.update_record(theme_ids=theme_ids)

    # -------------------------------------------------------------------------
    @staticmethod
    def assistance_inline_component():
        """
            Configure inline-form for assistance measures

            @returns: S3SQLInlineComponent
        """

        T = current.T

        settings = current.deployment_settings

        use_themes = settings.get_br_assistance_themes()
        details_per_theme = settings.get_br_assistance_details_per_theme()

        if use_themes and details_per_theme and \
           settings.get_br_case_activity_need() and \
           settings.get_br_assistance_activity_autolink():

            # Embed details per theme rather than measures
            return S3SQLInlineComponent("assistance_measure_theme",
                                        fields = ["measure_id",
                                                  "theme_id",
                                                  "comments",
                                                  ],
                                        label = T("Themes"),
                                        orderby = "measure_id",
                                        )
        else:
            fields = ["start_date",
                      #"assistance_type_id",
                      #"theme_ids",
                      #"comments",
                      #"human_resource_id",
                      #"hours",
                      "status_id",
                      ]

            if not use_themes or not details_per_theme:
                fields.insert(1, "comments")
            if use_themes:
                fields.insert(1, "theme_ids")
            if settings.get_br_assistance_types():
                fields.insert(1, "assistance_type_id")
            if settings.get_br_assistance_manager():
                fields.insert(-1, "human_resource_id")
            if settings.get_br_assistance_track_effort():
                fields.insert(-1, "hours")

            return S3SQLInlineComponent("assistance_measure",
                                        label = T("Measures"),
                                        fields = fields,
                                        layout = S3SQLVerticalSubFormLayout,
                                        explicit_add = T("Add Measure"),
                                        )

# =============================================================================
class BRDistributionModel(S3Model):
    """
        Model to process+track relief item distributions to beneficiaries
    """
    pass

# =============================================================================
class BRPaymentModel(S3Model):
    """
        Model to process+track benefits payments to beneficiaries
    """
    pass

# =============================================================================
# Tracking Models
# =============================================================================
class BRCaseEventModel(S3Model):
    """
        Model for checkpoint-style tracking of beneficiaries
    """
    pass

# =============================================================================
# Case Documentation Models
# =============================================================================
class BRLanguageModel(S3Model):
    """
        Model to document language options for communication
        with a beneficiary
    """

    names = ("br_case_language",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Case Language: languages that can be used to communicate with
        #                a case beneficiary, intended as inline-component
        #                of beneficiary form

        # Quality/Mode of communication:
        lang_quality_opts = (("N", T("native")),
                             ("F", T("fluent")),
                             ("S", T("simplified/slow")),
                             ("W", T("written-only")),
                             ("I", T("interpreter required")),
                             )

        tablename = "br_case_language"
        self.define_table(tablename,
                          self.pr_person_id(empty = False,
                                            ondelete = "CASCADE",
                                            ),
                          s3_language(select = None),
                          Field("quality",
                                default = "N",
                                label = T("Quality/Mode"),
                                represent = S3Represent(options=dict(lang_quality_opts)),
                                requires = IS_IN_SET(lang_quality_opts,
                                                     sort = False,
                                                     zero = None,
                                                     ),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       orderby = "language",
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        return {}

# =============================================================================
class BRLegalStatusModel(S3Model):
    pass

# =============================================================================
class BRServiceContactModel(S3Model):
    """ Model to track external service contacts of beneficiaries """

    names = ("br_service_contact",
             "br_service_contact_type",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3

        crud_strings = s3.crud_strings

        define_table = self.define_table
        configure = self.configure

        # ---------------------------------------------------------------------
        # Service Contact Types
        #
        tablename = "br_service_contact_type"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Table configuration
        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # CRUD Strings
        ADD_TYPE = T("Create Service Contact Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_TYPE,
            title_display = T("Service Contact Type"),
            title_list = T("Service Contact Types"),
            title_update = T("Edit Service Contact Types"),
            label_list_button = T("List Service Contact Types"),
            label_delete_button = T("Delete Service Contact Type"),
            msg_record_created = T("Service Contact Type added"),
            msg_record_modified = T("Service Contact Type updated"),
            msg_record_deleted = T("Service Contact Type deleted"),
            msg_list_empty = T("No Service Contact Types currently defined"),
            )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        contact_type_id = S3ReusableField("contact_type_id", "reference %s" % tablename,
                                          label = T("Contact Type"),
                                          ondelete = "RESTRICT",
                                          represent = represent,
                                          requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "%s.id" % tablename,
                                                                  represent,
                                                                  )),
                                          sortby = "name",
                                          )

        # ---------------------------------------------------------------------
        # Service Contacts of Beneficiaries
        #
        AGENCY = T("Providing Agency")

        tablename = "br_service_contact"
        define_table(tablename,
                     # Beneficiary (component link):
                     self.pr_person_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),

                     # Service and contact type
                     self.org_service_id(readable = False,
                                         writable = False,
                                         ),
                     contact_type_id(),

                     Field("organisation",
                           label = AGENCY,
                           ),
                     # Alternative organisation_id (if tracking providers in-DB)
                     # - enable in template as required
                     self.org_organisation_id(label = AGENCY,
                                              readable = False,
                                              writable = False,
                                              ),

                     Field("reference",
                           label = T("Ref.No."),
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Ref.No."),
                                                             T("Customer number, file reference or other reference number"),
                                                             ),
                                         ),
                           ),
                     Field("contact",
                           label = T("Contact Person"),
                           ),
                     Field("phone",
                           label = T("Phone"),
                           ),
                     Field("email",
                           label = T("Email"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Service Contact"),
            title_display = T("Service Contact Details"),
            title_list = T("Service Contacts"),
            title_update = T("Edit Service Contacts"),
            label_list_button = T("List Service Contacts"),
            label_delete_button = T("Delete Service Contact"),
            msg_record_created = T("Service Contact added"),
            msg_record_modified = T("Service Contact updated"),
            msg_record_deleted = T("Service Contact deleted"),
            msg_list_empty = T("No Service Contacts currently registered"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        return {}

# =============================================================================
class BRNotesModel(S3Model):
    """ Simple Journal for Case Files """

    names = ("br_note",
             "br_note_type",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings

        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Note Types
        #
        tablename = "br_note_type"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     # Code field for deduplication, and to allow hard-coded
                     # filters and differential authorization
                     Field("code", length=64, notnull=True, unique=True,
                           label = T("Type Code"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       IS_NOT_ONE_OF(db,
                                                     "%s.code" % tablename,
                                                     ),
                                       ],
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Type Code"),
                                                             T("A unique code to identify this type"),
                                                             ),
                                         ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Note Type"),
            title_display = T("Note Type Details"),
            title_list = T("Note Types"),
            title_update = T("Edit Note Type"),
            label_list_button = T("List Note Types"),
            label_delete_button = T("Delete Note Type"),
            msg_record_created = T("Note Type added"),
            msg_record_modified = T("Note Type updated"),
            msg_record_deleted = T("Note Type deleted"),
            msg_list_empty = T("No Note Types found"),
            )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        note_type_id = S3ReusableField("note_type_id", "reference %s" % tablename,
                                       label = T("Note Type"),
                                       ondelete = "RESTRICT",
                                       represent = represent,
                                       requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                        "%s.id" % tablename,
                                                        represent,
                                                        )),
                                       )

        # ---------------------------------------------------------------------
        # Notes
        #
        tablename = "br_note"
        define_table(tablename,
                     self.pr_person_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     note_type_id(empty = False,
                                  ),
                     s3_datetime(default = "now",
                                 ),
                     s3_comments("note",
                                 label = T("Note"),
                                 represent = lambda v: s3_text_represent(v, lines=8),
                                 comment = None,
                                 ),
                     *s3_meta_fields())

        # List fields
        list_fields = ["id",
                       "person_id",
                       "date",
                       "note_type_id",
                       "note",
                       (T("Author"), "modified_by"),
                       ]

        # Table configuration
        self.configure(tablename,
                       list_fields = list_fields,
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Note"),
            title_display = T("Note Details"),
            title_list = T("Notes"),
            title_update = T("Edit Note"),
            label_list_button = T("List Notes"),
            label_delete_button = T("Delete Note"),
            msg_record_created = T("Note added"),
            msg_record_modified = T("Note updated"),
            msg_record_deleted = T("Note deleted"),
            msg_list_empty = T("No Notes found"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class BRReferralModel(S3Model):
    pass

# =============================================================================
class BRVulnerabilityModel(S3Model):
    pass

# =============================================================================
# Representation Methods
# =============================================================================
class br_AssistanceThemeRepresent(S3Represent):
    """ Representation of assistance themes """

    def __init__(self, multiple=False, translate=True, show_need=False):

        super(br_AssistanceThemeRepresent, self).__init__(
                                                lookup = "br_assistance_theme",
                                                multiple = multiple,
                                                translate = translate,
                                                )
        self.show_need = show_need

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        table = self.table

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        if self.show_need:
            ntable = current.s3db.br_need
            left = ntable.on(ntable.id == table.need_id)
            rows = current.db(query).select(table.id,
                                            table.name,
                                            ntable.id,
                                            ntable.name,
                                            left = left,
                                            limitby = (0, count),
                                            )
        else:
            rows = current.db(query).select(table.id,
                                            table.name,
                                            limitby = (0, count),
                                            )
        self.queries += 1

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        T = current.T
        translate = self.translate

        if self.show_need:

            theme = row.br_assistance_theme.name
            if theme:
                theme = T(theme) if translate else theme
            else:
                theme = self.none

            need = row.br_need.name
            if need:
                need = T(need) if translate else need

            if need:
                reprstr = "%s: %s" % (need, theme)
            else:
                reprstr = theme
        else:
            theme = row.name
            if theme:
                reprstr = T(theme) if translate else theme
            else:
                reprstr = self.none

        return reprstr

# -----------------------------------------------------------------------------
class br_AssistanceMeasureRepresent(S3Represent):
    """ Representation of assistance measures """

    def __init__(self, show_hr=True, show_link=True):
        """
            Constructor

            @param show_hr: include the staff member name
        """

        super(br_AssistanceMeasureRepresent, self).__init__(
                                    lookup = "br_assistance_measure",
                                    show_link = show_link,
                                    )

        self.show_hr = show_hr

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: list of fields to look up (unused)
        """

        show_hr = self.show_hr

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        table = self.table

        fields = [table.id, table.start_date, table.person_id]
        if show_hr:
            fields.append(table.human_resource_id)

        rows = current.db(query).select(limitby=(0, count), *fields)
        self.queries += 1

        # Bulk-represent human_resource_ids
        if show_hr:
            hr_ids = [row.human_resource_id for row in rows]
            table.human_resource_id.represent.bulk(hr_ids)

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        table = self.table
        date = table.start_date.represent(row.start_date)

        if self.show_hr:
            hr = table.human_resource_id.represent(row.human_resource_id,
                                                   show_link = False,
                                                   )
            reprstr = "[%s] %s" % (date, hr)
        else:
            reprstr = date

        return reprstr

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link

            @param k: the key (br_assistance_measure.id)
            @param v: the representation of the key
            @param row: the row with this key
        """

        try:
            person_id = row.person_id
        except AttributeError:
            return v

        url = URL(c = "br",
                  f = "person",
                  args = [person_id, "assistance_measure", k],
                  extension = "",
                  )

        return A(v, _href = url)

# -----------------------------------------------------------------------------
class br_AssistanceMeasureThemeRepresent(S3Represent):
    """ Representation of measure-theme links """

    def __init__(self, paragraph=False, details=False):
        """
            Constructor

            @param paragraph: render as HTML paragraph
            @param details: include details in paragraph
        """

        super(br_AssistanceMeasureThemeRepresent, self).__init__(
                                    lookup = "br_assistance_measure_theme",
                                    )

        self.paragraph = paragraph
        self.details = details

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: list of fields to look up (unused)
        """

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        table = self.table

        fields = [table.id, table.measure_id, table.theme_id]
        if self.details:
            fields.append(table.comments)

        rows = current.db(query).select(limitby=(0, count), *fields)
        self.queries += 1

        # Bulk-represent themes
        theme_ids = [row.theme_id for row in rows]
        table.theme_id.represent.bulk(theme_ids)

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        table = self.table

        theme = table.theme_id.represent(row.theme_id)

        if self.paragraph:
            # CSS class to allow styling
            css = "br-assistance-measure-theme"
            if self.details:
                comments = table.comments.represent(row.comments)
                reprstr = DIV(H6(theme), comments, _class=css)
            else:
                reprstr = P(theme, _class=css)
        else:
            reprstr = theme

        return reprstr

    # -------------------------------------------------------------------------
    def render_list(self, value, labels, show_link=True):
        """
            Render list-type representations from bulk()-results.

            @param value: the list
            @param labels: the labels as returned from bulk()
            @param show_link: render references as links, should
                              be the same as used with bulk()
        """

        if self.paragraph:
            reprstr = TAG[""]([labels[v] if v in labels else self.default
                               for v in value
                               ])
        else:
            reprstr = super(br_AssistanceMeasureThemeRepresent, self) \
                        .render_list(value, labels, show_link=show_link)
        return reprstr

# -----------------------------------------------------------------------------
class br_CaseActivityRepresent(S3Represent):
    """ Representation of case activity IDs """

    def __init__(self,
                 show_as=None,
                 fmt=None,
                 show_date=False,
                 show_link=False,
                 linkto=None,
                 ):
        """
            Constructor

            @param show_as: alternative representations:
                            "beneficiary"|"need"|"subject"
            @param fmt: string format template for person record
            @param show_date: include the activity date in the representation
            @param show_link: show representation as clickable link
            @param linkto: URL for the link, using "[id]" as placeholder
                           for the record ID
        """

        super(br_CaseActivityRepresent, self).__init__(
                                                lookup = "br_case_activity",
                                                show_link = show_link,
                                                linkto = linkto,
                                                )

        if show_as is None:
            self.show_as = "beneficiary"
        else:
            self.show_as = show_as

        if fmt:
            self.fmt = fmt
        else:
            self.fmt = "%(first_name)s %(last_name)s"

        self.show_date = show_date

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        table = self.table

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        ptable = current.s3db.pr_person
        left = [ptable.on(ptable.id == table.person_id)]

        show_as = self.show_as
        if show_as == "beneficiary":
            # Beneficiary name
            rows = current.db(query).select(table.id,
                                            table.date,
                                            ptable.id,
                                            ptable.pe_label,
                                            ptable.first_name,
                                            ptable.middle_name,
                                            ptable.last_name,
                                            left = left,
                                            limitby = (0, count),
                                            )

        elif show_as == "need":
            # Need type
            ntable = current.s3db.br_need
            left.append(ntable.on(ntable.id == table.need_id))
            rows = current.db(query).select(table.id,
                                            table.date,
                                            ptable.id,
                                            ntable.name,
                                            left = left,
                                            limitby = (0, count),
                                            )
        else:
            # Subject line (default)
            rows = current.db(query).select(table.id,
                                            table.date,
                                            table.subject,
                                            ptable.id,
                                            left = left,
                                            limitby = (0, count),
                                            )

        self.queries += 1

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        show_as = self.show_as
        if show_as == "beneficiary":
            beneficiary = dict(row.pr_person)
            # Do not show "None" for no label
            if beneficiary.get("pe_label") is None:
                beneficiary["pe_label"] = ""
            reprstr = self.fmt % beneficiary

        elif show_as == "need":
            need = row.br_need.name
            if self.translate:
                need = current.T(need) if need else self.none
            reprstr = need

        else:
            reprstr = row.br_case_activity.subject

        if self.show_date:
            dt = S3DateTime.date_represent(row.br_case_activity.date)
            reprstr = "[%s] %s" % (dt, reprstr)

        return reprstr

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link

            @param k: the key (br_case_activity.id)
            @param v: the representation of the key
            @param row: the row with this key
        """

        try:
            beneficiary = row.pr_person
        except AttributeError:
            return v

        url = URL(c = "br",
                  f = "person",
                  args = [beneficiary.id, "case_activity", k],
                  extension = "",
                  )

        return A(v, _href = url)

# -----------------------------------------------------------------------------
class br_DocEntityRepresent(S3Represent):
    """ Module context-specific representation of doc-entities """

    def __init__(self,
                 case_label=None,
                 case_group_label=None,
                 activity_label=None,
                 use_sector=True,
                 use_need=False,
                 show_link=False,
                 ):
        """
            Constructor

            @param case_label: label for cases (default: "Case")
            @param case_group_label: label for case groups (default: "Case Group")
            @param activity_label: label for case activities
                                   (default: "Activity")
            @param use_need: use need if available instead of subject
            @param use_sector: use sector if available instead of
                               activity label
            @param show_link: show representation as clickable link
        """

        super(br_DocEntityRepresent, self).__init__(lookup = "doc_entity",
                                                    show_link = show_link,
                                                    )

        T = current.T

        if case_label:
            self.case_label = case_label
        else:
            self.case_label = br_terminology().CASE

        if case_group_label:
            self.case_group_label = case_group_label
        else:
            self.case_group_label = T("Family")

        if activity_label:
            self.activity_label = activity_label
        else:
            self.activity_label = T("Activity")

        self.use_need = use_need
        self.use_sector = use_sector

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        db = current.db
        s3db = current.s3db

        table = self.table
        ptable = s3db.pr_person

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        rows = db(query).select(table.doc_id,
                                table.instance_type,
                                limitby = (0, count),
                                orderby = table.instance_type,
                                )
        self.queries += 1

        # Sort by instance type
        doc_ids = {}
        for row in rows:
            doc_id = row.doc_id
            instance_type = row.instance_type
            if instance_type not in doc_ids:
                doc_ids[instance_type] = {doc_id: row}
            else:
                doc_ids[instance_type][doc_id] = row

        need_ids = set()
        sector_ids = set()
        for instance_type in ("br_case", "br_case_activity", "pr_group"):

            doc_entities = doc_ids.get(instance_type)
            if not doc_entities:
                continue

            # The instance table
            itable = s3db[instance_type]

            # Look up person and instance data
            query = itable.doc_id.belongs(set(doc_entities.keys()))
            if instance_type == "pr_group":
                mtable = s3db.pr_group_membership
                left = [mtable.on((mtable.group_id == itable.id) & \
                                  (mtable.deleted == False)),
                        ptable.on(ptable.id == mtable.person_id),
                        ]
            else:
                left = ptable.on(ptable.id == itable.person_id)
            fields = [itable.id,
                      itable.doc_id,
                      ptable.id,
                      ptable.first_name,
                      ptable.middle_name,
                      ptable.last_name,
                      ]
            if instance_type == "br_case_activity":
                fields.extend((#itable.sector_id, # TODO
                               itable.subject,
                               #itable.need_id,   # TODO
                               ))
            if instance_type == "pr_group":
                fields.extend((itable.name,
                               itable.group_type,
                               ))
            irows = db(query).select(left=left, *fields)
            self.queries += 1

            # Add the person+instance data to the entity rows
            for irow in irows:
                instance = irow[instance_type]
                entity = doc_entities[instance.doc_id]

                if hasattr(instance, "sector_id"):
                    sector_ids.add(instance.sector_id)
                if hasattr(instance, "need_id"):
                    need_ids.add(instance.need_id)

                entity[instance_type] = instance
                entity.pr_person = irow.pr_person

            # Bulk represent any sector ids
            if sector_ids and "sector_id" in itable.fields:
                represent = itable.sector_id.represent
                if represent and hasattr(represent, "bulk"):
                    represent.bulk(list(sector_ids))

            # Bulk represent any need ids
            if need_ids and "need_id" in itable.fields:
                represent = itable.need_id.represent
                if represent and hasattr(represent, "bulk"):
                    represent.bulk(list(need_ids))

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        reprstr = self.default

        instance_type = row.instance_type
        if hasattr(row, "pr_person"):

            if instance_type == "br_case":

                person = row.pr_person
                title = s3_fullname(person)
                label = self.case_label

            elif instance_type == "br_case_activity":

                #table = current.s3db.br_case_activity
                activity = row.br_case_activity

                title = activity.subject
                # TODO
                #if self.use_need:
                #    need_id = activity.need_id
                #    if need_id:
                #        represent = table.need_id.represent
                #        title = represent(need_id)

                label = self.activity_label
                # TODO
                #if self.use_sector:
                #    sector_id = activity.sector_id
                #    if sector_id:
                #        represent = table.sector_id.represent
                #        label = represent(sector_id)

            elif instance_type == "pr_group":

                group = row.pr_group

                if group.group_type == 7:
                    label = self.case_group_label
                    if group.name:
                        title = group.name
                    else:
                        person = row.pr_person
                        title = s3_fullname(person)
                else:
                    label = current.T("Group")
                    title = group.name or self.default
            else:
                title = None
                label = None

            if title:
                reprstr = "%s (%s)" % (s3_str(title), s3_str(label))

        return reprstr

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link

            @param k: the key (doc_entity.doc_id)
            @param v: the representation of the key
            @param row: the row with this key
        """

        link = v

        if row:
            if row.instance_type == "br_case_activity":
                try:
                    person_id = row.pr_person.id
                    case_activity_id = row.br_case_activity.id
                except AttributeError:
                    pass
                else:
                    url = URL(c = "br",
                              f = "person",
                              args = [person_id,
                                      "case_activity",
                                      case_activity_id,
                                      ],
                              extension="",
                              )
                    link = A(v, _href=url)

        return link

# =============================================================================
# Utility Functions
# =============================================================================
def br_case_read_orgs():
    """
        Check if the user has read access to cases of more than one org

        @returns: tuple (multiple_orgs, org_ids)
    """

    realms = current.auth.permission.permitted_realms("br_case", "read")
    if realms is None:
        multiple_orgs = True
        org_ids = []
    else:
        otable = current.s3db.org_organisation
        query = (otable.pe_id.belongs(realms)) & \
                (otable.deleted == False)
        rows = current.db(query).select(otable.id)
        multiple_orgs = len(rows) > 1
        org_ids = [row.id for row in rows]

    return multiple_orgs, org_ids

# -----------------------------------------------------------------------------
def br_case_default_org():
    """
        Determine the default organisation for new cases

        @returns: tuple (default_org, multiple_orgs)
    """

    settings = current.deployment_settings

    default_org = settings.get_org_default_organisation()
    if default_org and settings.get_br_case_global_default_org():
        # All cases are linked to the global default organisation
        return default_org, False

    auth = current.auth
    realms = auth.permission.permitted_realms("br_case", "create")

    if realms is None:
        # User can create cases for any org
        orgs = []
        multiple_orgs = True
    else:
        otable = current.s3db.org_organisation
        query = (otable.pe_id.belongs(realms)) & \
                (otable.deleted == False)
        rows = current.db(query).select(otable.id)
        orgs = [row.id for row in rows]
        multiple_orgs = len(rows) > 1

    if multiple_orgs:
        user_org = auth.user.organisation_id if auth.user else None
        if user_org and user_org in orgs:
            default_org = user_org
    elif orgs:
        default_org = orgs[0]

    return default_org, multiple_orgs

# -----------------------------------------------------------------------------
def br_case_root_org(person_id):
    """
        Get the root organisation managing a case

        @param person_id: the person record ID

        @returns: the root organisation record ID
    """

    db = current.db
    s3db = current.s3db

    if person_id:
        ctable = s3db.br_case
        otable = s3db.org_organisation
        left = otable.on(otable.id == ctable.organisation_id)
        query = (ctable.person_id == person_id) & \
                (ctable.invalid == False) & \
                (ctable.deleted == False)
        row = db(query).select(otable.root_organisation,
                               left = left,
                               limitby = (0, 1),
                               orderby = ~ctable.modified_on,
                               ).first()
        case_root_org = row.root_organisation if row else None
    else:
        case_root_org = None

    return case_root_org

# -----------------------------------------------------------------------------
def br_case_default_status():
    """
        Helper to get/set the default status for case records

        @return: the default status_id
    """

    s3db = current.s3db

    ctable = s3db.br_case
    field = ctable.status_id

    default = field.default
    if not default:

        # Look up the default status
        stable = s3db.br_case_status
        query = (stable.is_default == True) & \
                (stable.deleted != True)
        row = current.db(query).select(stable.id, limitby=(0, 1)).first()

        if row:
            # Set as field default in case table
            default = field.default = row.id

    return default

# -----------------------------------------------------------------------------
def br_case_status_filter_opts(closed=None):
    """
        Get filter options for case status, ordered by workflow position

        @return: OrderedDict of options

        @note: set sort=False for filter widget to retain this order
    """

    table = current.s3db.br_case_status
    query = (table.deleted != True)
    if closed is not None:
        if closed:
            query &= (table.is_closed == True)
        else:
            query &= ((table.is_closed == False) | (table.is_closed == None))
    rows = current.db(query).select(table.id,
                                    table.name,
                                    orderby = "workflow_position",
                                    )

    if not rows:
        return {}

    T = current.T
    return OrderedDict((row.id, T(row.name)) for row in rows)

# -----------------------------------------------------------------------------
def br_case_activity_default_status(closing=False):
    """
        Helper to get/set the default status for case activities

        @param closing: return the default closure status

        @return: the default status_id
    """

    s3db = current.s3db

    atable = s3db.br_case_activity
    field = atable.status_id

    if closing:
        default = None
        flag = stable.is_default_closed
    else:
        default = field.default
        flag = stable.is_default

    if not default:
        # Look up the default status
        stable = s3db.br_case_activity_status
        query = (flag == True) & (stable.deleted != True)
        row = current.db(query).select(stable.id,
                                       cache = s3db.cache,
                                       limitby = (0, 1),
                                       ).first()
        if row:
            default = row.id
            if not closing:
                # Set as field default in case table
                field.default = default

    return default

# -----------------------------------------------------------------------------
def br_org_assistance_themes(organisation_id):
    """
        Generate a dbset of br_assistance_theme filtered to organisation_id,
        for use with IS_ONE_OF field validation
        - when using org-specific themes, the themes of this org
        - otherwise, the themes matching the org's sectors (if themes are
          sector-specific) and need types (if themes are need-specific)

        @param organisation_id: the organisation ID, usually the case root
                                organisation
    """

    db = current.db
    s3db = current.s3db
    settings = current.deployment_settings

    table = s3db.br_assistance_theme
    filters = []

    if settings.get_br_assistance_themes_org_specific():
        # Filter themes by organisation_id
        if organisation_id:
            query = table.organisation_id == organisation_id
        else:
            query = table.organisation_id.belongs(set())
        filters.append(query)

    else:
        if settings.get_br_assistance_themes_sectors():
            # Filter themes by sectors linked to organisation_id
            ltable = s3db.org_sector_organisation
            query = (ltable.organisation_id == organisation_id) & \
                    (ltable.deleted == False)
            links = db(query).select(ltable.sector_id)
            sector_ids = set(link.sector_id for link in links)
            filters.append(table.sector_id.belongs(sector_ids))

        if settings.get_br_assistance_themes_needs() and \
           settings.get_br_needs_org_specific():
            # Filter themes by need types linked to organisation_id
            ntable = s3db.br_need
            query = (ntable.organisation_id == organisation_id) & \
                    (ntable.deleted == False)
            needs = db(query).select(ntable.id)
            need_ids = set(need.id for need in needs)
            filters.append(table.need_id.belongs(need_ids))

    if filters:
        q = None
        for f in filters:
            q = f if q is None else q & f
        dbset = db(q)
    else:
        dbset = db

    return dbset

# -----------------------------------------------------------------------------
def br_assistance_default_status():
    """
        Set the default status for assistance measures

        @returns: the default status ID
    """

    db = current.db
    s3db = current.s3db

    table = s3db.br_assistance_measure
    field = table.status_id

    default = field.default
    if not default:
        stable = s3db.br_assistance_status
        if current.deployment_settings.get_br_assistance_measure_default_closed():
            query = (stable.is_default_termination == True)
        else:
            query = (stable.is_default == True)
        query &= (stable.deleted == False)
        row = db(query).select(stable.id,
                               limitby = (0, 1),
                               orderby = stable.workflow_position,
                               ).first()
        if row:
            default = field.default = row.id

    return default

# -----------------------------------------------------------------------------
def br_assistance_status_colors(resource, selector):
    """
        Get colors for assistance statuses (organizer)

        @param resource: the S3Resource the caller is looking at
        @param selector: the Field selector (usually "status_id")

        @returns: a dict with colors {field_value: "#RRGGBB", ...}
    """

    table = current.s3db.br_assistance_status
    query = (table.color != None)
    rows = current.db(query).select(table.id,
                                    table.color,
                                    )
    return {row.id: ("#%s" % row.color) for row in rows if row.color}

# -----------------------------------------------------------------------------
def br_household_size(group_id):
    """
        Update the household_size for all cases in the given case group,
        taking into account that the same person could belong to multiple
        case groups. To be called onaccept of pr_group_membership if automatic
        household size is enabled

        @param group_id: the group_id of the case group (group_type == 7)
    """

    db = current.db
    s3db = current.s3db
    ptable = s3db.pr_person
    gtable = s3db.pr_group
    mtable = s3db.pr_group_membership

    # Get all persons related to this group_id, make sure this is a case group
    join = [mtable.on((mtable.group_id == gtable.id) &
                      (mtable.deleted != True)),
            ptable.on(ptable.id == mtable.person_id)
            ]
    query = (gtable.id == group_id) & \
            (gtable.group_type == 7) & \
            (gtable.deleted != True)
    rows = db(query).select(ptable.id, join=join)
    person_ids = {row.id for row in rows}

    if person_ids:
        # Get case group members for each of these person_ids
        ctable = s3db.br_case
        rtable = ctable.with_alias("member_cases")
        otable = mtable.with_alias("case_members")
        join = ctable.on(ctable.person_id == mtable.person_id)
        left = [otable.on((otable.group_id == mtable.group_id) &
                          (otable.deleted != True)),
                rtable.on(rtable.person_id == otable.person_id),
                ]
        query = (mtable.person_id.belongs(person_ids)) & \
                (mtable.deleted != True) & \
                (rtable.id != None)
        rows = db(query).select(ctable.id,
                                otable.person_id,
                                join = join,
                                left = left,
                                )

        # Count heads
        CASE = str(ctable.id)
        MEMBER = str(otable.person_id)
        groups = {}
        for row in rows:
            member_id = row[MEMBER]
            case_id = row[CASE]
            if case_id not in groups:
                groups[case_id] = {member_id}
            else:
                groups[case_id].add(member_id)

        # Update the related cases
        for case_id, members in groups.items():
            number_of_members = len(members)
            db(ctable.id == case_id).update(household_size = number_of_members)

# -----------------------------------------------------------------------------
def br_group_membership_onaccept(membership, group, group_id, person_id):
    """
        Module-specific extensions for pr_group_membership_onaccept

        @param membership: the pr_group_membership record
                           - required fields: id, deleted, group_head
        @param group: the pr_group record
                      - required fields: id, group_type
        @param group_id: the group ID (if membership was deleted)
        @param person_id: the person ID (if membership was deleted)
    """

    db = current.db
    s3db = current.s3db

    table = s3db.pr_group_membership
    gtable = s3db.pr_group
    ctable = s3db.br_case

    response = current.response
    s3 = response.s3
    if s3.purge_case_groups:
        return

    # Get the group type
    if not group.id and group_id:
        query = (gtable.id == group_id) & \
                (gtable.deleted != True)
        row = db(query).select(#gtable.id,
                               gtable.group_type,
                               limitby = (0, 1),
                               ).first()
        if row:
            group = row

    if group.group_type == CASE_GROUP:

        # Case groups should only have one group head
        if not membership.deleted and membership.group_head:
            query = (table.group_id == group_id) & \
                    (table.id != membership.id) & \
                    (table.group_head == True)
            db(query).update(group_head=False)

        update_household_size = current.deployment_settings.get_br_household_size() == "auto"
        recount = s3db.br_household_size

        if update_household_size and membership.deleted and person_id:
            # Update the household size for removed group member
            query = (table.person_id == person_id) & \
                    (table.group_id != group_id) & \
                    (table.deleted != True) & \
                    (gtable.id == table.group_id) & \
                    (gtable.group_type == CASE_GROUP)
            row = db(query).select(table.group_id, limitby=(0, 1)).first()
            if row:
                # Person still belongs to other case groups, count properly:
                recount(row.group_id)
            else:
                # No further case groups, so household size is 1
                ctable = s3db.br_case
                cquery = (ctable.person_id == person_id)
                db(cquery).update(household_size = 1)

        if not s3.bulk:
            # Get number of (remaining) members in this group
            query = (table.group_id == group_id) & \
                    (table.deleted != True)
            rows = db(query).select(table.id, limitby = (0, 2))

            if len(rows) < 2:
                # Update the household size for current group members
                if update_household_size:
                    recount(group_id)
                    update_household_size = False
                # Remove the case group if it only has one member
                s3.purge_case_groups = True
                resource = s3db.resource("pr_group", id=group_id)
                resource.delete()
                s3.purge_case_groups = False

            elif not membership.deleted:
                # Generate a case for new case group member
                # ...unless we already have one
                query = (ctable.person_id == person_id) & \
                        (ctable.deleted != True)
                row = db(query).select(ctable.id, limitby=(0, 1)).first()
                if not row:
                    # Customise case resource
                    r = S3Request("br", "case", current.request)
                    r.customise_resource("br_case")

                    # Get the default case status from database
                    s3db.br_case_default_status()

                    # Create a case
                    cresource = s3db.resource("br_case")
                    try:
                        # Using resource.insert for proper authorization
                        # and post-processing (=audit, ownership, realm,
                        # onaccept)
                        cresource.insert(person_id=person_id)
                    except S3PermissionError:
                        # Unlikely (but possible) that this situation
                        # is deliberate => issue a warning
                        response.warning = current.T("No permission to create a case record for new group member")

        # Update the household size for current group members
        if update_household_size:
            recount(group_id)

# =============================================================================
# User Interface
# =============================================================================
def br_rheader(r, tabs=None):
    """ BR Resource Headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:

        T = current.T
        settings = current.deployment_settings

        record_id = record.id

        if tablename == "pr_person":

            if not tabs:

                # Basic Case Documentation
                tabs = [(T("Basic Details"), None),
                        ]
                append = tabs.append

                if settings.get_br_case_contacts_tab():
                    append((T("Contact Info"), "contacts"))
                if settings.get_br_case_id_tab():
                    append((T("ID"), "identity"))
                if settings.get_br_case_family_tab():
                    append((T("Family Members"), "group_membership/"))

                activities_tab = settings.get_br_case_activities()
                measures_tab = settings.get_br_manage_assistance() and \
                               settings.get_br_assistance_tab()

                if activities_tab and measures_tab:
                    activities_label = T("Needs")
                    measures_label = T("Measures")
                else:
                    activities_label = T("Activities")
                    measures_label = T("Assistance")

                if activities_tab:
                    append((activities_label, "case_activity"))
                if measures_tab:
                    append((measures_label, "assistance_measure"))

                if settings.get_br_service_contacts():
                    append((T("Service Contacts"), "service_contact"))
                if settings.get_br_case_notes_tab():
                    append((T("Notes"), "br_note"))
                if settings.get_br_case_photos_tab():
                    append((T("Photos"), "image"))
                if settings.get_br_case_documents_tab():
                    append((T("Documents"), "document/"))

            case = resource.select(["first_name",
                                    "middle_name",
                                    "last_name",
                                    "case.status_id",
                                    "case.invalid",
                                    "case.household_size",
                                    "case.organisation_id",
                                    ],
                                    represent = True,
                                    raw_data = True,
                                    ).rows

            if not case:
                # Target record exists, but doesn't match filters
                return None

            # Extract case data
            case = case[0]

            name = s3_fullname
            case_status = lambda row: case["br_case.status_id"]
            organisation = lambda row: case["br_case.organisation_id"]

            household = settings.get_br_household_size()
            if household:
                if household == "auto":
                    label = T("Size of Family")
                else:
                    label = T("Household Size")
                household_size = (label,
                                  lambda row: case["br_case.household_size"],
                                  )
            else:
                household_size = None

            rheader_fields = [[(T("ID"), "pe_label"),
                               (T("Case Status"), case_status),
                               (T("Organisation"), organisation),
                               ],
                              ["date_of_birth",
                               household_size,
                               ],
                              ]

            invalid = case["_row"]["br_case.invalid"]
            if invalid:
                # "Invalid Case" Hint
                hint = lambda record: SPAN(T("Invalid Case"),
                                           _class="invalid-case",
                                           )
                rheader_fields.insert(0, [(None, hint)])

            # Generate rheader XML
            rheader = S3ResourceHeader(rheader_fields, tabs, title=name)(
                            r,
                            table = resource.table,
                            record = record,
                            )

            # Add profile picture
            from s3 import s3_avatar_represent
            rheader.insert(0, A(s3_avatar_represent(record_id,
                                                    "pr_person",
                                                    _class = "rheader-avatar",
                                                    ),
                                _href=URL(f = "person",
                                          args = [record_id, "image"],
                                          vars = r.get_vars,
                                          ),
                                )
                           )
        else:
            rheader = None

    return rheader

# =============================================================================
def br_terminology():
    """
        Terminology-sensitive labels for BR (other than CRUD strings)

        @returns: Messages instance
    """

    labels = current.response.s3.br_labels
    if labels is None:

        labels = Messages(current.T)
        settings = current.deployment_settings

        # Case Terminology
        terminology = settings.get_br_case_terminology()

        if terminology == "Beneficiary":
            labels.CASE = "Beneficiary"
            labels.CASES = "Beneficiaries"
            labels.CASES_MINE = "My Beneficiaries"
            labels.CURRENT = "Current Beneficiaries"
            labels.CURRENT_MINE = "My Current Beneficiaries"
            labels.CLOSED = "Former Beneficiaries"
            labels.NUMBER_OF_CASES = "Number of Beneficiaries"

        elif terminology == "Client":
            labels.CASE = "Client"
            labels.CASES = "Clients"
            labels.CASES_MINE = "My Clients"
            labels.CURRENT = "Current Clients"
            labels.CURRENT_MINE = "My Current Clients"
            labels.CLOSED = "Former Clients"
            labels.NUMBER_OF_CASES = "Number of Clients"

        else:
            labels.CASE = "Case"
            labels.CASES = "Cases"
            labels.CASES_MINE = "My Cases"
            labels.CURRENT = "Current Cases"
            labels.CURRENT_MINE = "My Current Cases"
            labels.CLOSED = "Closed Cases"
            labels.NUMBER_OF_CASES = "Number of Cases"

        # Assistance Terminology
        terminology = settings.get_br_assistance_terminology()

        if terminology == "Counseling":
            labels.THEMES = "Counseling Themes"

        else:
            labels.THEMES = "Assistance Themes"

        current.response.s3.br_labels = labels

    return labels

# =============================================================================
def br_crud_strings(tablename):
    """
        Terminology-sensitive CRUD strings for BR

        @param tablename: the table name

        @returns: Storage of CRUD strings
    """

    T = current.T
    if tablename == "pr_person":
        terminology = current.deployment_settings.get_br_case_terminology()

        if terminology == "Beneficiary":
            crud_strings = Storage(
                label_create = T("Create Beneficiary"),
                title_display = T("Beneficiary Details"),
                title_list = T("Beneficiaries"),
                title_update = T("Edit Beneficiary Details"),
                label_list_button = T("List Beneficiaries"),
                label_delete_button = T("Delete Beneficiary"),
                msg_record_created = T("Beneficiary added"),
                msg_record_modified = T("Beneficiary details updated"),
                msg_record_deleted = T("Beneficiary deleted"),
                msg_list_empty = T("No Beneficiaries currently registered")
                )
        elif terminology == "Client":
            crud_strings = Storage(
                label_create = T("Create Client"),
                title_display = T("Client Details"),
                title_list = T("Clients"),
                title_update = T("Edit Client Details"),
                label_list_button = T("List Clients"),
                label_delete_button = T("Delete Client"),
                msg_record_created = T("Client added"),
                msg_record_modified = T("Client details updated"),
                msg_record_deleted = T("Client deleted"),
                msg_list_empty = T("No Clients currently registered")
                )
        else:
            crud_strings = Storage(
                label_create = T("Create Case"),
                title_display = T("Case Details"),
                title_list = T("Cases"),
                title_update = T("Edit Case Details"),
                label_list_button = T("List Cases"),
                label_delete_button = T("Delete Case"),
                msg_record_created = T("Case added"),
                msg_record_modified = T("Case details updated"),
                msg_record_deleted = T("Case deleted"),
                msg_list_empty = T("No Cases currently registered")
                )

    elif tablename == "br_assistance_theme":

        terminology = current.deployment_settings.get_br_assistance_terminology()

        if terminology == "Counseling":
            crud_strings = Storage(
                label_create = T("Create Counseling Theme"),
                title_display = T("Counseling Theme"),
                title_list = T("Counseling Themes"),
                title_update = T("Edit Counseling Theme"),
                label_list_button = T("List Counseling Themes"),
                label_delete_button = T("Delete Counseling Theme"),
                msg_record_created = T("Counseling Theme added"),
                msg_record_modified = T("Counseling Theme updated"),
                msg_record_deleted = T("Counseling Theme deleted"),
                msg_list_empty = T("No Counseling Themes currently defined")
                )
        else:
            crud_strings = Storage(
                label_create = T("Create Assistance Theme"),
                title_display = T("Assistance Theme"),
                title_list = T("Assistance Themes"),
                title_update = T("Edit Assistance Theme"),
                label_list_button = T("List Assistance Themes"),
                label_delete_button = T("Delete Assistance Theme"),
                msg_record_created = T("Assistance Theme added"),
                msg_record_modified = T("Assistance Theme updated"),
                msg_record_deleted = T("Assistance Theme deleted"),
                msg_list_empty = T("No Assistance Themes currently defined")
                )

    else:
        crud_strings = current.response.s3.crud_strings.get(tablename)

    return crud_strings

# =============================================================================
def br_anonymous_address(record_id, field, value):
    """
        Helper to anonymize a pr_address location; removes street and
        postcode details, but retains Lx ancestry for statistics

        @param record_id: the pr_address record ID
        @param field: the location_id Field
        @param value: the location_id

        @return: the location_id
    """

    db = current.db
    s3db = current.s3db

    # Get the location
    if value:
        ltable = s3db.gis_location
        row = db(ltable.id == value).select(ltable.id,
                                            ltable.level,
                                            limitby = (0, 1),
                                            ).first()
        if not row.level:
            # Specific location => remove address details
            data = {"addr_street": None,
                    "addr_postcode": None,
                    "gis_feature_type": 0,
                    "lat": None,
                    "lon": None,
                    "wkt": None,
                    }
            # Doesn't work - PyDAL doesn't detect the None value:
            #if "the_geom" in ltable.fields:
            #    data["the_geom"] = None
            row.update_record(**data)
            if "the_geom" in ltable.fields:
                db.executesql("UPDATE gis_location SET the_geom=NULL WHERE id=%s" % row.id)

    return value

# -----------------------------------------------------------------------------
def br_obscure_dob(record_id, field, value):
    """
        Helper to obscure a date of birth; maps to the first day of
        the quarter, thus retaining the approximate age for statistics

        @param record_id: the pr_address record ID
        @param field: the location_id Field
        @param value: the location_id

        @return: the new date
    """

    if value:
        month = int((value.month - 1) / 3) * 3 + 1
        value = value.replace(month=month, day=1)

    return value

# -----------------------------------------------------------------------------
def br_person_anonymize():
    """ Rules to anonymize a case file """

    ANONYMOUS = "-"

    # Helper to produce an anonymous ID (pe_label)
    anonymous_id = lambda record_id, f, v: "NN%06d" % long(record_id)

    # General rule for attachments
    documents = ("doc_document", {"key": "doc_id",
                                  "match": "doc_id",
                                  "fields": {"name": ("set", ANONYMOUS),
                                             "file": "remove",
                                             "url": "remove",
                                             "comments": "remove",
                                             },
                                  "delete": True,
                                  })

    # Cascade rule for case activities
    activity_details = [("br_case_activity_update", {
                                "key": "case_activity_id",
                                "match": "id",
                                "fields": {"comments": ("set", ANONYMOUS),
                                           },
                                }),
                        ]

    # Cascade rule for assistance measures
    assistance_details = [("br_assistance_measure_theme", {
                                "key": "measure_id",
                                "match": "id",
                                "fields": {"comments": ("set", ANONYMOUS),
                                           },
                                }),
                          ]

    rules = [# Rules to remove PID from basic beneficiary details
             {"name": "default",
              "title": "Names, IDs, Reference Numbers, Contact Information, Addresses",
              "fields": {"first_name": ("set", ANONYMOUS),
                         "last_name": ("set", ANONYMOUS),
                         "pe_label": anonymous_id,
                         "date_of_birth": br_obscure_dob,
                         "comments": "remove",
                         },
              "cascade": [("br_case", {
                                "key": "person_id",
                                "match": "id",
                                "fields": {"comments": "remove",
                                           },
                                }),
                          ("br_case_language", {
                                "key": "person_id",
                                "match": "id",
                                "fields": {"comments": "remove",
                                           },
                                }),
                          ("pr_contact", {
                                "key": "pe_id",
                                "match": "pe_id",
                                "fields": {"contact_description": "remove",
                                           "value": ("set", ""),
                                           "comments": "remove",
                                           },
                                "delete": True,
                                }),
                          ("pr_contact_emergency", {
                                "key": "pe_id",
                                "match": "pe_id",
                                "fields": {"name": ("set", ANONYMOUS),
                                           "relationship": "remove",
                                           "phone": "remove",
                                           "comments": "remove",
                                           },
                                "delete": True,
                                }),
                          ("pr_address", {
                                "key": "pe_id",
                                "match": "pe_id",
                                "fields": {"location_id": br_anonymous_address,
                                           "comments": "remove",
                                           },
                                }),
                          ("pr_person_details", {
                                "key": "person_id",
                                "match": "id",
                                "fields": {"education": "remove",
                                           "occupation": "remove",
                                           },
                                }),
                          ("pr_person_tag", {
                                "key": "person_id",
                                "match": "id",
                                "fields": {"value": ("set", ANONYMOUS),
                                           },
                                "delete": True,
                                }),
                          ],
              },

             # Rules to remove PID from activities, assistance details and notes
             {"name": "activities",
              "title": "Activities, Assistance Details and Notes",
              "cascade": [("br_case_activity", {
                                "key": "person_id",
                                "match": "id",
                                "fields": {"subject": ("set", ANONYMOUS),
                                           "need_details": "remove",
                                           "outcome": "remove",
                                           "comments": "remove",
                                           },
                                "cascade": activity_details,
                                }),
                          ("br_assistance_measure", {
                                "key": "person_id",
                                "match": "id",
                                "fields": {"comments": "remove",
                                           },
                                "cascade": assistance_details,
                                }),
                          ("br_note", {
                                "key": "person_id",
                                "match": "id",
                                "fields": {"note": "remove",
                                           },
                                "delete": True,
                                }),
                          ],
              },

             # Rules to remove photos and attachments
             {"name": "documents",
              "title": "Photos and Documents",
              "cascade": [("br_case", {"key": "person_id",
                                       "match": "id",
                                       "cascade": [documents,
                                                   ],
                                       }),
                          ("br_case_activity", {"key": "person_id",
                                                "match": "id",
                                                "cascade": [documents,
                                                            ],
                                                }),
                          ("pr_image", {"key": "pe_id",
                                        "match": "pe_id",
                                        "fields": {"image": "remove",
                                                   "url": "remove",
                                                   "description": "remove",
                                                   },
                                        "delete": True,
                                        }),
                          ],
              },
             ]

    return rules

# END =========================================================================
