# -*- coding: utf-8 -*-

""" Sahana Eden Beneficiary Registry and Case Management Models

    @copyright: 2018-2019 (c) Sahana Software Foundation
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
           "BRResponseModel",
           "BRAppointmentModel",
           "BRCaseEventModel",
           "BRPaymentModel",
           "BRNotesModel",
           "BRLanguageModel",
           "BRLegalStatusModel",
           "BRServiceContactModel",
           "BRReferralModel",
           "BRVulnerabilityModel",
           "br_DocEntityRepresent",
           "br_case_read_orgs",
           "br_case_default_org",
           "br_case_root_org",
           "br_case_default_status",
           "br_case_status_filter_opts",
           "br_group_membership_onaccept",
           "br_household_size",
           "br_rheader",
           "br_terminology",
           "br_crud_strings",
           )

from collections import OrderedDict

from gluon import *
from gluon.storage import Messages, Storage

from ..s3 import *
from s3layouts import S3PopupLink

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
        default_organisation = settings.get_org_default_organisation()
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
                            label = T("Assigned To"),
                            comment = DIV(_class = "tooltip",
                                          _title = "%s|%s" % (T("Assigned To"),
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

        # Update closed_on date TODO
        #if row.br_case_status.is_closed:
        #    if not case.closed_on:
        #        case.update_record(closed_on = current.request.utcnow.date())
        #elif case.closed_on:
        #    case.update_record(closed_on = None)

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
                                               # notes
                                               ),
                           )
            set_realm_entity("pr_person", person_id, force_update=True)

            # Force-update the realm entity for all related activities
            atable = s3db.br_case_activity
            query = (atable.person_id == person_id)
            set_realm_entity(atable, query, force_update=True)

            # Force-update the realm entity for all related responses (TODO)

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
             "br_case_activity_status",
             "br_case_activity_update_type",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        define_table = self.define_table
        configure = self.configure
        crud_strings = s3.crud_strings

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
                                       ondelete = "CASCADE",
                                       writable = False,
                                       ),

                     # Case Manager
                     self.hrm_human_resource_id(
                            label = T("Assigned To"),
                            comment = DIV(_class = "tooltip",
                                          _title = "%s|%s" % (T("Assigned To"),
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
                     status_id(),

                     # Dates
                     s3_date(label = T("Date"),
                             default = "now",
                             set_min = "#br_case_activity_end_date",
                             ),
                     s3_date("end_date",
                             label = T("Closed on"),
                             # TODO make optional CRUD field
                             readable = False,
                             writable = False,
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
                            )

        # Optional inline components
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
                       "activity_details",  # TODO alternative: responses
                       "status_id",         # TODO make optional
                       updates,
                       #"end_date",         # TODO make optional
                       "outcome",           # TODO make optional
                       attachments,
                       "comments",
                       ]

        # List fields (for case file tab)
        list_fields = ["priority",
                       "date",
                       "status_id",         # TODO make optional
                       #"end_date",         # TODO make optional
                       ]
        if case_activity_manager:
            list_fields.insert(2, "human_resource_id")
        if case_activity_subject:
            list_fields.insert(2, "subject")
        if case_activity_need:
            list_fields.insert(2, "need_id")

        # Filter widgets
        text_filter_fields = ["person_id$pe_label",
                              "person_id$first_name",
                              "person_id$middle_name",
                              "person_id$last_name",
                              ]
        if case_activity_subject:
            text_filter_fields.append("subject")

        filter_widgets = [S3TextFilter(text_filter_fields,
                                       label = T("Search"),
                                       ),
                          S3DateFilter("date",
                                       hidden = True,
                                       ),
                          # TODO needs-filter
                          S3OptionsFilter("status_id",
                                          cols = 4,
                                          hidden = True,
                                          sort = False,
                                          options = s3_get_filter_opts(
                                                      "br_case_activity_status",
                                                      orderby = "br_case_activity_status.workflow_position",
                                                      ),
                                          ),
                         ]

        # Report options TODO

        # Table configuration
        configure(tablename,
                  crud_form = S3SQLCustomForm(*crud_fields),
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  onaccept = self.case_activity_onaccept,
                  orderby = "br_case_activity.priority",
                  #report_options = report_options,
                  realm_components = ("case_activity_update",
                                      ),
                  super_entity = "doc_entity",
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Activity"),
            title_display = T("Activity Details"),
            title_list = T("Activities"),
            title_update = T("Edit Activity"),
            label_list_button = T("List Activities"),
            label_delete_button = T("Delete Activity"),
            msg_record_created = T("Activity added"),
            msg_record_modified = T("Activity updated"),
            msg_record_deleted = T("Activity deleted"),
            msg_list_empty = T("No Activities currently registered"),
            )

        # Reusable field
        # TODO switch default representation between subject and need
        #      based on deployment setting
        represent = br_CaseActivityRepresent(show_link=True,
                                             show_as = "subject",
                                             )
        case_activity_id = S3ReusableField("case_activity_id",
                                           "reference %s" % tablename,
                                           ondelete = "CASCADE",
                                           represent = represent,
                                           requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "%s.id" % tablename,
                                                                  represent,
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
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        #dummy = S3ReusableField("dummy_id", "integer",
        #                        readable = False,
        #                        writable = False,
        #                        )

        return {#"example_example_id": lambda **attr: dummy("example_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def case_activity_status_onaccept(form):
        """
            Onaccept routine for activity statuses:
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

        # Ensure that there is only one default status
        if "is_default" in form_vars and form_vars.is_default:
            table = current.s3db.br_case_activity_status
            current.db(table.id != record_id).update(is_default = False)

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

        join = stable.on(atable.status_id == stable.id)
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

            if data:
                activity.update_record(**data)

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
                                                              IS_ONE_OF(db, "dvr_case_appointment_type.id",
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
                                  comment = S3PopupLink(c = "br",
                                                        f = "need",
                                                        title = ADD_NEED,
                                                        tooltip = T("Choose the need type from the drop-down, or click the link to create a new type"),
                                                        ),
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
class BRVulnerabilityModel(S3Model):
    pass

# =============================================================================
# Response Action Models
# =============================================================================
class BRResponseModel(S3Model):
    """
        Model to document individual measures taken in support of a case
    """
    pass

# =============================================================================
class BRDistributionModel(S3Model):
    """
        Model to process+track item distributions to beneficiaries
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
                          s3_language(list_from_settings = False),
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
    pass

# =============================================================================
class BRNotesModel(S3Model):
    pass

# =============================================================================
class BRReferralModel(S3Model):
    pass

# =============================================================================
# Representation Methods
# =============================================================================
class br_CaseActivityRepresent(S3Represent):
    """ Representation of case activity IDs """

    def __init__(self, show_as=None, fmt=None, show_link=False, linkto=None):
        """
            Constructor

            @param show_as: alternative representations:
                            "beneficiary"|"need"|"subject"
            @param show_link: show representation as clickable link
            @param fmt: string format template for person record
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
            rows = current.db(query).select(table.id,
                                            ptable.id,
                                            ptable.pe_label,
                                            ptable.first_name,
                                            ptable.middle_name,
                                            ptable.last_name,
                                            left = left,
                                            limitby = (0, count),
                                            )

        # TODO
        #elif show_as == "need":
        #    ntable = current.s3db.br_need
        #    left.append(ntable.on(ntable.id == table.need_id))
        #    rows = current.db(query).select(table.id,
        #                                    ptable.id,
        #                                    ntable.name,
        #                                    left = left,
        #                                    limitby = (0, count),
        #                                    )
        else:
            # Subject line (default)
            rows = current.db(query).select(table.id,
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

            return self.fmt % beneficiary

        # TODO
        #elif show_as == "need":
        #
        #    need = row.br_need.name
        #    if self.translate:
        #        need = current.T(need) if need else self.none
        #
        #    return need

        else:

            return row.dvr_case_activity.subject

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link

            @param k: the key (dvr_case_activity.id)
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
            query = itable.doc_id.belongs(doc_entities.keys())
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

    default_org = current.deployment_settings.get_org_default_organisation()
    if default_org:
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
    person_ids = set([row.id for row in rows])

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
                groups[case_id] = set([member_id])
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
                if settings.get_br_case_activities():
                    append((T("Activities"), "case_activity"))
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

        terminology = current.deployment_settings.get_br_terminology()
        labels = Messages(current.T)

        if terminology == "Beneficiary":
            labels.CASE = "Beneficiary"
            labels.CASES = "Beneficiaries"
            labels.CASES_MINE = "My Beneficiaries"
            labels.CURRENT = "Current Beneficiaries"
            labels.CURRENT_MINE = "My Current Beneficiaries"
            labels.CLOSED = "Former Beneficiaries"

        elif terminology == "Client":
            labels.CASE = "Client"
            labels.CASES = "Clients"
            labels.CASES_MINE = "My Clients"
            labels.CURRENT = "Current Clients"
            labels.CURRENT_MINE = "My Current Clients"
            labels.CLOSED = "Former Clients"

        else:
            labels.CASE = "Case"
            labels.CASES = "Cases"
            labels.CASES_MINE = "My Cases"
            labels.CURRENT = "Current Cases"
            labels.CURRENT_MINE = "My Current Cases"
            labels.CLOSED = "Closed Cases"

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
    terminology = current.deployment_settings.get_br_terminology()

    if tablename == "pr_person":
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
    else:
        crud_strings = current.response.s3.crud_strings.get(tablename)

    return crud_strings

# END =========================================================================
