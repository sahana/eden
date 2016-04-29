# -*- coding: utf-8 -*-

""" Sahana Eden Disaster Victim Registration Model

    @copyright: 2012-2016 (c) Sahana Software Foundation
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

__all__ = ("DVRCaseModel",
           "DVRCaseFlagModel",
           "DVRNeedsModel",
           "DVRNotesModel",
           "DVRCaseActivityModel",
           "DVRCaseAppointmentModel",
           "DVRCaseBeneficiaryModel",
           "DVRCaseEconomyInformationModel",
           "DVRCaseAllowanceModel",
           "DVRCaseEventModel",
           "dvr_case_default_status",
           "dvr_case_status_filter_opts",
           "dvr_case_household_size",
           "dvr_update_last_seen",
           "dvr_get_flag_instructions",
           "dvr_due_followups",
           "dvr_rheader",
           )

from gluon import *
from gluon.storage import Storage
from gluon.tools import callback
from ..s3 import *
from s3layouts import S3PopupLink

# =============================================================================
class DVRCaseModel(S3Model):
    """
        Model for DVR Cases

        Allow an individual or household to register to receive
        compensation and/or distributions of relief items
    """

    names = ("dvr_case",
             "dvr_case_id",
             "dvr_case_language",
             "dvr_case_status",
             "dvr_case_status_id",
             "dvr_case_type",
             )

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        crud_strings = current.response.s3.crud_strings

        configure = self.configure
        define_table = self.define_table
        person_id = self.pr_person_id

        manage_transferability = settings.get_dvr_manage_transferability()

        # ---------------------------------------------------------------------
        # Case Types
        #
        tablename = "dvr_case_type"
        define_table(tablename,
                     Field("name",
                           label = T("Type"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     # Enable in template if/when org-specific
                     # case types are required:
                     self.org_organisation_id(readable = False,
                                              writable = False,
                                              ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_CASE_TYPE = T("Create Case Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_CASE_TYPE,
            title_display = T("Case Type"),
            title_list = T("Case Types"),
            title_update = T("Edit Case Type"),
            label_list_button = T("List Case Types"),
            label_delete_button = T("Delete Case Type"),
            msg_record_created = T("Case Type added"),
            msg_record_modified = T("Case Type updated"),
            msg_record_deleted = T("Case Type deleted"),
            msg_list_empty = T("No Case Types currently registered")
            )

        # Represent for reference
        case_type_represent = S3Represent(lookup = "dvr_case_type",
                                          translate = True,
                                          )

        # ---------------------------------------------------------------------
        # Case Statuses
        #
        tablename = "dvr_case_status"
        define_table(tablename,
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
                     Field("code", length=64, notnull=True, unique=True,
                           label = T("Status Code"),
                           requires = [IS_NOT_EMPTY(),
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
                           # Removed to allow single column imports of Cases
                           #requires = IS_NOT_EMPTY(),
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
                     Field("is_not_transferable", "boolean",
                           default = False,
                           label = T("Not Transferable"),
                           represent = s3_yes_no_represent,
                           readable = manage_transferability,
                           writable = manage_transferability,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Not Transferable"),
                                                             T("Cases with this status are not transferable"),
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
            msg_list_empty = T("No Case Statuses currently registered")
            )

        # Table configuration
        configure(tablename,
                  # Allow imports to change the status code:
                  deduplicate = S3Duplicate(primary = ("name",)),
                  onaccept = self.case_status_onaccept,
                  )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        status_id = S3ReusableField("status_id", "reference %s" % tablename,
                                    label = T("Status"),
                                    ondelete = "RESTRICT",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "dvr_case_status.id",
                                                          represent,
                                                          orderby = "dvr_case_status.workflow_position",
                                                          sort = False,
                                                          )),
                                    sortby = "workflow_position",
                                    )

        # ---------------------------------------------------------------------
        # Cases
        #

        # Case priority options
        # => tuple list to enforce widget order
        # => numeric key so it can be sorted by
        case_priority_opts = ((3, T("High")),
                              (2, T("Medium")),
                              (1, T("Low")),
                              )

        # Case beneficiary options
        case_beneficiary_opts = {"INDIVIDUAL": T("Individual"),
                                 "HOUSEHOLD": T("Household"),
                                 }

        SITE = settings.get_org_site_label()
        site_represent = self.org_SiteRepresent(show_link=False)

        default_organisation = settings.get_org_default_organisation()
        default_site = settings.get_org_default_site()
        permitted_facilities = current.auth.permitted_facilities(redirect_on_error=False)

        household_size = settings.get_dvr_household_size()
        household_size_writable = household_size and household_size != "auto"

        tablename = "dvr_case"
        define_table(tablename,
                     person_id(represent = self.pr_PersonRepresent(show_link=True),
                               requires = IS_ADD_PERSON_WIDGET2(),
                               widget = S3AddPersonWidget2(controller="dvr"),
                               ),
                     # @ToDo: Option to autogenerate these, like Waybills, et al
                     Field("reference",
                           label = T("Case Number"),
                           ),
                     FieldS3("case_type_id", "reference dvr_case_type",
                             label = T("Case Type"),
                             represent = case_type_represent,
                             requires = IS_EMPTY_OR(IS_ONE_OF(
                                                db, "dvr_case_type.id",
                                                case_type_represent,
                                                )),
                             sortby = "name",
                             comment = S3PopupLink(c = "dvr",
                                                   f = "case_type",
                                                   title = ADD_CASE_TYPE,
                                                   tooltip = T("Choose the case type from the drop-down, or click the link to create a new type"),
                                                   # Always look up options from dvr/case
                                                   # (required if inline in person form):
                                                   vars = {"parent": "case",
                                                           },
                                                   ),
                             ),
                     Field("beneficiary",
                           default = "INDIVIDUAL",
                           label = T("Assistance for"),
                           represent = S3Represent(options=case_beneficiary_opts),
                           requires = IS_IN_SET(case_beneficiary_opts,
                                                zero = None,
                                                ),
                           # Enable in template if required
                           readable = False,
                           writable = False,
                           ),
                     s3_date(label = T("Registration Date"),
                             default = "now",
                             empty = False,
                             ),
                     s3_date("closed_on",
                             label = T("Case closed on"),
                             # Automatically set onaccept
                             writable = False,
                             ),
                     s3_date("valid_until",
                             label = T("Valid until"),
                             # Enable in template if required
                             readable = False,
                             writable = False,
                             ),
                     s3_date("stay_permit_until",
                             label = T("Stay Permit until"),
                             # Enable in template if required
                             readable = False,
                             writable = False,
                             ),
                     s3_datetime("last_seen_on",
                                 label = T("Last seen on"),
                                 # Enable in template if required
                                 readable = False,
                                 writable = False,
                                 ),
                     status_id(),
                     Field("priority", "integer",
                           default = 2,
                           label = T("Priority"),
                           represent = S3Represent(options=dict(case_priority_opts)),
                           requires = IS_IN_SET(case_priority_opts,
                                                sort = False,
                                                zero = None,
                                                ),
                           ),
                     self.org_organisation_id(default = default_organisation,
                                              readable = not default_organisation,
                                              writable = not default_organisation,
                                              ),
                     self.super_link("site_id", "org_site",
                                     default = default_site,
                                     filterby = "site_id",
                                     filter_opts = permitted_facilities,
                                     label = SITE,
                                     readable = not default_site,
                                     writable = not default_site,
                                     represent = site_represent,
                                     updateable = True,
                                     ),
                     Field("origin_site_id", "reference org_site",
                           label = T("Admission from"),
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "org_site.site_id",
                                                  site_represent,
                                                  sort = True,
                                                  filterby = "instance_type",
                                                  filter_opts = ("cr_shelter",
                                                                 "org_office",
                                                                 "org_facility",
                                                                 ),
                                                  not_filterby = "obsolete",
                                                  not_filter_opts = (True,),
                                                  )),
                           represent = site_represent,
                           # Enable in template if required
                           readable = False,
                           writable = False,
                           ),
                     Field("destination_site_id", "reference org_site",
                           label = T("Transfer to"),
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "org_site.site_id",
                                                  site_represent,
                                                  sort = True,
                                                  filterby = "instance_type",
                                                  filter_opts = ("cr_shelter",
                                                                 "org_office",
                                                                 "org_facility",
                                                                 ),
                                                  not_filterby = "obsolete",
                                                  not_filter_opts = (True,),
                                                  )),
                           represent = site_represent,
                           # Enable in template if required
                           readable = False,
                           writable = False,
                           ),
                     Field("archived", "boolean",
                           default = False,
                           label = T("Archived"),
                           represent = s3_yes_no_represent,
                           # Enabled in controller:
                           readable = False,
                           writable = False,
                           ),
                     # "transferable" indicates whether this case is
                     # ready for transfer (=workflow is complete)
                     Field("transferable", "boolean",
                           default = False,
                           label = T("Transferable"),
                           represent = s3_yes_no_represent,
                           readable = manage_transferability,
                           writable = manage_transferability,
                           ),
                     # "household transferable" indicates whether all
                     # open cases in the case group are ready for transfer
                     Field("household_transferable", "boolean",
                           default = False,
                           label = T("Household Transferable"),
                           represent = s3_yes_no_represent,
                           readable = manage_transferability,
                           writable = manage_transferability,
                           ),
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
                     # Simplified "head of household" fields:
                     # (if not tracked as separate case beneficiaries)
                     Field("head_of_household", "boolean",
                           default = True,
                           label = T("Head of Household"),
                           represent = s3_yes_no_represent,
                           # Enable in template if required
                           readable = False,
                           writable = False,
                           ),
                     Field("hoh_name",
                           label = T("Head of Household Name"),
                           # Enable in template if required
                           readable = False,
                           writable = False,
                           ),
                     self.pr_gender("hoh_gender",
                                    label = T("Head of Household Gender"),
                                    # Enable in template if required
                                    readable = False,
                                    writable = False,
                                    ),
                     Field("hoh_relationship",
                           label = T("Head of Household Relationship"),
                           # Enable in template if required
                           readable = False,
                           writable = False,
                           ),
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
            msg_list_empty = T("No Cases found"),
            )

        # Components
        self.add_components(tablename,
                            dvr_beneficiary_data = "case_id",
                            dvr_case_activity = "case_id",
                            dvr_case_event = "case_id",
                            dvr_case_service_contact = "case_id",
                            dvr_economy = {"joinby": "case_id",
                                           "multiple": False,
                                           },
                            dvr_need =  {"link": "dvr_case_need",
                                         "joinby": "case_id",
                                         "key": "need_id",
                                         },
                            )

        # Report options FIXME
        #axes = ["organisation_id",
        #        "case_need.need_id",
        #        ]
        #levels = current.gis.get_relevant_hierarchy_levels()
        #for level in levels:
        #    axes.append("current_address.location_id$%s" % level)
        #highest_lx = "current_address.location_id$%s" % levels[0]
        #
        #facts = [(T("Number of Cases"), "count(id)"),
        #         ]
        #
        #report_options = {"rows": axes,
        #                  "cols": axes,
        #                  "fact": facts,
        #                  "defaults": {"rows": "case_need.need_id",
        #                               "cols": highest_lx,
        #                               "fact": facts[0],
        #                               "totals": True,
        #                               },
        #                  }

        # Table configuration
        configure(tablename,
                  #report_options = report_options,
                  onvalidation = self.case_onvalidation,
                  create_onaccept = self.case_create_onaccept,
                  update_onaccept = self.case_onaccept,
                  )

        # Reusable field
        represent = S3Represent(lookup=tablename, fields=("reference",))
        case_id = S3ReusableField("case_id", "reference %s" % tablename,
                                  label = T("Case"),
                                  ondelete = "RESTRICT",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "dvr_case.id",
                                                          represent)),
                                  )

        # ---------------------------------------------------------------------
        # Case Language: languages that can be used to communicate with
        #                a case beneficiary
        #

        # Quality/Mode of communication:
        lang_quality_opts = (("N", T("native")),
                             ("F", T("fluent")),
                             ("S", T("simplified/slow")),
                             ("W", T("written-only")),
                             ("I", T("interpreter required")),
                             )

        tablename = "dvr_case_language"
        define_table(tablename,
                     person_id(empty = False,
                               ondelete = "CASCADE",
                               ),
                     Field("language",
                           label = T("Language"),
                           represent = IS_ISO639_2_LANGUAGE_CODE.represent_local,
                           requires = IS_ISO639_2_LANGUAGE_CODE(select = None,
                                                                translate = True,
                                                                ),
                           ),
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

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"dvr_case_id": case_id,
                "dvr_case_status_id": status_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return {"dvr_case_id": lambda name="case_id", **attr: \
                               dummy(name, **attr),
                "dvr_case_status_id": lambda name="status_id", **attr: \
                                      dummy(name, **attr),
                }

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
            table = current.s3db.dvr_case_status
            db = current.db
            db(table.id != record_id).update(is_default = False)

    # -------------------------------------------------------------------------
    @staticmethod
    def case_onvalidation(form):
        """
            Case onvalidation:
            - make sure case numbers are unique within the organisation

            @param form: the FORM
        """

        db = current.db
        s3db = current.s3db

        # Read form data
        form_vars = form.vars
        if "id" in form_vars:
            # Inline subtable update
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            # Regular update form
            record_id = form.record_id
        else:
            # New record
            record_id = None
        try:
            reference = form_vars.reference
        except AttributeError:
            reference = None

        if reference:
            # Make sure the case reference is unique within the organisation

            ctable = s3db.dvr_case
            otable = s3db.org_organisation

            # Get the organisation_id
            if "organisation_id" not in form_vars:
                if not record_id:
                    # Create form with hidden organisation_id
                    # => use default
                    organisation_id = ctable.organisation_id.default
                else:
                    # Reload the record to get the organisation_id
                    query = (ctable.id == record_id)
                    row = db(query).select(ctable.organisation_id,
                                           limitby = (0, 1)).first()
                    if not row:
                        return
                    organisation_id = row.organisation_id
            else:
                # Use the organisation_id in the form
                organisation_id = form_vars.organisation_id

            # Case duplicate query
            dquery = (ctable.reference == reference) & \
                     (ctable.deleted != True)
            if record_id:
                dquery &= (ctable.id != record_id)
            msg = current.T("This Case Number is already in use")

            # Add organisation query to duplicate query
            if current.deployment_settings.get_org_branches():
                # Get the root organisation
                query = (otable.id == organisation_id)
                row = db(query).select(otable.root_organisation,
                                    limitby = (0, 1)).first()
                root_organisation = row.root_organisation \
                                    if row else organisation_id
                dquery &= (otable.root_organisation == root_organisation)
                left = otable.on(otable.id == ctable.organisation_id)
            else:
                dquery &= (ctable.organisation_id == organisation_id)
                left = None

            # Is there a record with the same reference?
            row = db(dquery).select(ctable.id,
                                    left = left,
                                    limitby = (0, 1)).first()
            if row:
                form.errors["reference"] = msg

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
        ctable = s3db.dvr_case
        stable = s3db.dvr_case_status
        left = stable.on(stable.id == ctable.status_id)
        query = (ctable.id == record_id)
        row = db(query).select(ctable.id,
                               ctable.person_id,
                               ctable.closed_on,
                               stable.is_closed,
                               left = left,
                               limitby = (0, 1),
                               ).first()
        if not row:
            return

        # Update closed_on date
        case = row.dvr_case
        if row.dvr_case_status.is_closed:
            if not case.closed_on:
                case.update_record(closed_on = current.request.utcnow.date())
        elif case.closed_on:
            case.update_record(closed_on = None)

        # Get the person ID
        person_id = case.person_id

        atable = s3db.dvr_case_appointment
        ttable = s3db.dvr_case_appointment_type
        left = atable.on((atable.type_id == ttable.id) &
                         (atable.person_id == person_id) &
                         (atable.deleted != True))
        query = (atable.id == None) & \
                (ttable.active == True) & \
                (ttable.deleted != True)
        rows = db(query).select(ttable.id, left=left)
        for row in rows:
            atable.insert(case_id = record_id,
                          person_id = person_id,
                          type_id = row.id,
                          )

        if create and \
           current.deployment_settings.get_dvr_household_size() == "auto":
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
                dvr_case_household_size(row.id)

# =============================================================================
class DVRCaseFlagModel(S3Model):
    """ Model for Case Flags """

    names = ("dvr_case_flag",
             "dvr_case_flag_case",
             )

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        crud_strings = current.response.s3.crud_strings

        configure = self.configure
        define_table = self.define_table

        manage_transferability = settings.get_dvr_manage_transferability()

        # ---------------------------------------------------------------------
        # Case Flags
        #
        tablename = "dvr_case_flag"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("advise_at_check_in", "boolean",
                           default = False,
                           label = T("Advice at Check-in"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Advice at Check-in"),
                                                             T("Show handling instructions at check-in"),
                                                             ),
                                         ),
                           ),
                     Field("advise_at_check_out", "boolean",
                           default = False,
                           label = T("Advice at Check-out"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Advice at Check-out"),
                                                             T("Show handling instructions at check-out"),
                                                             ),
                                         ),
                           ),
                     Field("advise_at_id_check", "boolean",
                           default = False,
                           label = T("Advice at ID Check"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Advice at ID Check"),
                                                             T("Show handling instructions at ID checks (e.g. for event registration, payments)"),
                                                             ),
                                         ),
                           ),
                     Field("instructions", "text",
                           label = T("Instructions"),
                           represent = s3_text_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Instructions"),
                                                             T("Instructions for handling of the case"),
                                                             ),
                                         ),
                           ),
                     Field("deny_check_in", "boolean",
                           default = False,
                           label = T("Deny Check-in"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Deny Check-in"),
                                                             T("Deny the person to check-in when this flag is set"),
                                                             ),
                                         ),
                           ),
                     Field("deny_check_out", "boolean",
                           default = False,
                           label = T("Deny Check-out"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Deny Check-out"),
                                                             T("Deny the person to check-out when this flag is set"),
                                                             ),
                                         ),
                           ),
                     Field("allowance_suspended", "boolean",
                           default = False,
                           label = T("Allowance Suspended"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Allowance Suspended"),
                                                             T("Person shall not receive allowance payments when this flag is set"),
                                                             ),
                                         ),
                           ),
                     Field("is_not_transferable", "boolean",
                           default = False,
                           label = T("Not Transferable"),
                           represent = s3_yes_no_represent,
                           readable = manage_transferability,
                           writable = manage_transferability,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Not Transferable"),
                                                             T("Cases with this flag are not transferable"),
                                                             ),
                                         ),
                           ),
                     Field("is_external", "boolean",
                           default = False,
                           label = T("External"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("External"),
                                                             T("This flag indicates that the person is currently accommodated/being held externally (e.g. in Hospital or with Police)"),
                                                             ),
                                         ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_FLAG = T("Create Case Flag")
        crud_strings[tablename] = Storage(
            label_create = ADD_FLAG,
            title_display = T("Case Flag Details"),
            title_list = T("Case Flags"),
            title_update = T("Edit Case Flag"),
            label_list_button = T("List Case Flags"),
            label_delete_button = T("Delete Case Flag"),
            msg_record_created = T("Case Flag added"),
            msg_record_modified = T("Case Flag updated"),
            msg_record_deleted = T("Case Flag deleted"),
            msg_list_empty = T("No Case Flags found"),
            )

        # Table configuration
        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        flag_id = S3ReusableField("flag_id", "reference %s" % tablename,
                                  label = T("Case Flag"),
                                  ondelete = "RESTRICT",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "dvr_case_flag.id",
                                                          represent)),
                                  comment=S3PopupLink(c = "dvr",
                                                      f = "case_flag",
                                                      title = ADD_FLAG,
                                                      tooltip = T("Choose the flag from the drop-down, or click the link to create a new flag"),
                                                      ),
                                  )

        # ---------------------------------------------------------------------
        # Link table Case <=> Flag
        #
        tablename = "dvr_case_flag_case"
        define_table(tablename,
                     self.pr_person_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     flag_id(empty = False,
                             ondelete = "CASCADE",
                             ),
                     *s3_meta_fields())

        # Table configuration
        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("person_id",
                                                       "flag_id",
                                                       ),
                                            ),
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"dvr_case_flag_id": flag_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return {"dvr_case_flag_id": lambda name="flag_id", **attr: \
                                    dummy(name, **attr),
                }

# =============================================================================
class DVRNeedsModel(S3Model):
    """ Model for Needs """

    names = ("dvr_need",
             "dvr_need_id",
             "dvr_case_need",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings

        define_table = self.define_table
        configure = self.configure

        # ---------------------------------------------------------------------
        # Needs
        #
        tablename = "dvr_need"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

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

        # Table configuration
        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        need_id = S3ReusableField("need_id", "reference %s" % tablename,
                                  label = T("Need Type"),
                                  ondelete = "RESTRICT",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "dvr_need.id",
                                                          represent)),
                                  comment=S3PopupLink(c = "dvr",
                                                      f = "need",
                                                      title = ADD_NEED,
                                                      tooltip = T("Choose the need type from the drop-down, or click the link to create a new type"),
                                                      ),
                                  )

        # ---------------------------------------------------------------------
        # Link table Case <=> Need
        #
        tablename = "dvr_case_need"
        define_table(tablename,
                     self.dvr_case_id(empty = False,
                                      ondelete = "CASCADE",
                                      ),
                     need_id(empty = False,
                             ondelete = "CASCADE",
                             ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"dvr_need_id": need_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return {"dvr_need_id": lambda name="need_id", **attr: \
                               dummy(name, **attr),
                }

# =============================================================================
class DVRNotesModel(S3Model):
    """
        Model for Notes
    """

    names = ("dvr_note_type",
             "dvr_note",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings

        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Note Types
        #
        tablename = "dvr_note_type"
        define_table(tablename,
                     Field("name", length=128, unique=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_NOT_ONE_OF(db,
                                                     "dvr_note_type.name",
                                                     ),
                                       ],
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

        # Table configuration
        #self.configure(tablename,
        #               # Not needed as unique=True
        #               deduplicate = S3Duplicate(),
        #               )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        note_type_id = S3ReusableField("note_type_id", "reference %s" % tablename,
                                       label = T("Note Type"),
                                       ondelete = "RESTRICT",
                                       represent = represent,
                                       requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "dvr_note_type.id",
                                                              represent)),
                                       )

        # ---------------------------------------------------------------------
        # Notes
        #
        tablename = "dvr_note"
        define_table(tablename,
                     # Uncomment if needed for the Case perspective
                     #self.dvr_case_id(empty = False,
                     #                 ondelete = "CASCADE",
                     #                 ),
                     self.pr_person_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     note_type_id(empty = False),
                     s3_date(),
                     s3_comments("note",
                                 comment=None,
                                 ),
                     *s3_meta_fields())

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
class DVRCaseActivityModel(S3Model):
    """ Model for Case Activities """

    names = ("dvr_case_activity",
             "dvr_case_service_contact",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings

        configure = self.configure
        define_table = self.define_table

        twoweeks = current.request.utcnow + datetime.timedelta(days=14)

        # ---------------------------------------------------------------------
        # Case Activity
        #
        tablename = "dvr_case_activity"
        define_table(tablename,
                     self.dvr_case_id(comment = None,
                                      empty = False,
                                      label = T("Case Number"),
                                      ondelete = "CASCADE",
                                      writable = False,
                                      ),
                     # Beneficiary (component link):
                     # @todo: populate from case and hide in case perspective
                     self.pr_person_id(comment = None,
                                       empty = False,
                                       ondelete = "CASCADE",
                                       writable = False,
                                       ),
                     s3_date("start_date",
                             label = T("Registered on"),
                             default = "now",
                             ),
                     self.dvr_need_id(),
                     Field("need_details", "text",
                           label = T("Need Details"),
                           represent = s3_text_represent,
                           widget = s3_comments_widget,
                           ),
                     Field("emergency", "boolean",
                           default = False,
                           label = T("Emergency"),
                           represent = s3_yes_no_represent,
                           ),
                     # Activate in template as needed:
                     self.org_organisation_id(label = T("Referral Agency"),
                                              readable = False,
                                              writable = False,
                                              ),
                     Field("referral_details", "text",
                           label = T("Support provided"),
                           represent = s3_text_represent,
                           ),
                     Field("followup", "boolean",
                           default = True,
                           label = T("Follow up"),
                           represent = s3_yes_no_represent,
                           ),
                     s3_date("followup_date",
                             default = twoweeks,
                             label = T("Date for Follow-up"),
                             past = 0,
                             ),
                     # @todo: provide options lookup?
                     Field("outcome",
                           label = T("Outcome"),
                           ),
                     Field("completed", "boolean",
                           default = False,
                           label = T("Completed"),
                           represent = s3_yes_no_represent,
                           ),
                     #s3_date("end_date",
                     #        readable = False,
                     #        writable = False,
                     #        ),
                     s3_comments(),
                     *s3_meta_fields())

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

        # List fields
        list_fields = ["start_date",
                       "need_id",
                       "need_details",
                       "emergency",
                       "referral_details",
                       "followup",
                       "followup_date",
                       "completed",
                       ]

        # Filter widgets
        filter_widgets = [S3TextFilter(["person_id$pe_label",
                                        "person_id$first_name",
                                        "person_id$last_name",
                                        "case_id$reference",
                                        "need_details",
                                        "referral_details",
                                        ],
                                        label = T("Search"),
                                        ),
                          S3OptionsFilter("emergency",
                                          options = {True: T("Yes"),
                                                     False: T("No"),
                                                     },
                                          cols = 2,
                                          ),
                          S3OptionsFilter("need_id",
                                          options = lambda: s3_get_filter_opts("dvr_need",
                                                                               translate = True,
                                                                               ),
                                          ),
                          S3OptionsFilter("completed",
                                          default = False,
                                          options = {True: T("Yes"),
                                                     False: T("No"),
                                                     },
                                          cols = 2,
                                          ),
                          S3OptionsFilter("followup",
                                          label = T("Follow-up required"),
                                          options = {True: T("Yes"),
                                                     False: T("No"),
                                                     },
                                          cols = 2,
                                          hidden = True,
                                          ),
                          S3DateFilter("followup_date",
                                       cols = 2,
                                       hidden = True,
                                       ),
                          ]

        # Report options
        axes = ["need_id",
                (T("Case Status"), "case_id$status_id"),
                "emergency",
                "followup",
                "completed",
                ]
        facts = [(T("Number of Activities"), "count(id)"),
                 (T("Number of Cases"), "count(case_id)"),
                 ]
        report_options = {"rows": axes,
                          "cols": axes,
                          "fact": facts,
                          "defaults": {"rows": "need_id",
                                       "cols": "completed",
                                       "fact": facts[0],
                                       "totals": True,
                                       "chart": "barchart:rows",
                                       },
                          }

        # Table configuration
        configure(tablename,
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  orderby = "dvr_case_activity.start_date desc",
                  report_options = report_options,
                  )

        # ---------------------------------------------------------------------
        # Case Service Contacts (other than case activities)
        #
        tablename = "dvr_case_service_contact"
        define_table(tablename,
                     # Beneficiary (component link):
                     # @todo: populate from case and hide in case perspective
                     self.pr_person_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     self.dvr_case_id(empty = False,
                                      label = T("Case Number"),
                                      ondelete = "CASCADE",
                                      ),
                     s3_date(),
                     self.dvr_need_id(),
                     self.org_organisation_id(label=T("Providing Agency"),
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
class DVRCaseAppointmentModel(S3Model):
    """ Model for Case Appointments """

    names = ("dvr_case_appointment",
             "dvr_case_appointment_type",
             "dvr_appointment_type_id",
             )

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        crud_strings = current.response.s3.crud_strings

        configure = self.configure
        define_table = self.define_table

        mandatory_appointments = settings.get_dvr_mandatory_appointments()
        update_case_status = settings.get_dvr_appointments_update_case_status()

        # ---------------------------------------------------------------------
        # Case Appointment Type
        #
        mandatory_comment = DIV(_class="tooltip",
                                _title="%s|%s" % (T("Mandatory Appointment"),
                                                  T("This appointment is mandatory before transfer"),
                                                  ),
                                ),

        tablename = "dvr_case_appointment_type"
        define_table(tablename,
                     Field("name", length=64, notnull=True, unique=True,
                           requires = [IS_NOT_EMPTY(),
                                       IS_NOT_ONE_OF(db,
                                                     "%s.name" % tablename,
                                                     ),
                                       ],
                           ),
                     Field("active", "boolean",
                           default = True,
                           label = T("Active"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Active Appointment"),
                                                             T("Automatically create this appointment for new cases"),
                                                             ),
                                         ),
                           ),
                     Field("mandatory_children", "boolean",
                           default = False,
                           label = T("Mandatory for Children"),
                           represent = s3_yes_no_represent,
                           readable = mandatory_appointments,
                           writable = mandatory_appointments,
                           comment = mandatory_comment,
                           ),
                     Field("mandatory_adolescents", "boolean",
                           default = False,
                           label = T("Mandatory for Adolescents"),
                           represent = s3_yes_no_represent,
                           readable = mandatory_appointments,
                           writable = mandatory_appointments,
                           comment = mandatory_comment,
                           ),
                     Field("mandatory_adults", "boolean",
                           default = False,
                           label = T("Mandatory for Adults"),
                           represent = s3_yes_no_represent,
                           readable = mandatory_appointments,
                           writable = mandatory_appointments,
                           comment = mandatory_comment,
                           ),
                     Field("presence_required", "boolean",
                           default = True,
                           label = T("Presence required"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Presence required"),
                                                             T("This appointment requires the presence of the person concerned"),
                                                             ),
                                         ),
                           ),
                     self.dvr_case_status_id(
                        label = T("Case Status upon Completion"),
                        readable = update_case_status,
                        writable = update_case_status,
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
        # Case Appointments
        #
        appointment_status_opts = {1: T("Planning"),
                                   2: T("Planned"),
                                   3: T("In Progress"),
                                   4: T("Completed"),
                                   5: T("Missed"),
                                   6: T("Cancelled"),
                                   7: T("Not Required"),
                                   }

        tablename = "dvr_case_appointment"
        define_table(tablename,
                     self.dvr_case_id(comment = None,
                                      # @ToDo: Populate this onaccept from imports
                                      #empty = False,
                                      label = T("Case Number"),
                                      ondelete = "CASCADE",
                                      writable = False,
                                      ),
                     # Beneficiary (component link):
                     # @todo: populate from case and hide in case perspective
                     self.pr_person_id(comment = None,
                                       empty = False,
                                       ondelete = "CASCADE",
                                       writable = False,
                                       ),
                     appointment_type_id(empty = False,
                                         ),
                     s3_date(label = T("Planned on"),
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

        # Custom methods
        self.set_method("dvr", "case_appointment",
                        method = "manage",
                        action = DVRManageAppointments,
                        )

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("person_id",
                                                       "type_id",
                                                       ),
                                            ),
                  onaccept = self.case_appointment_onaccept,
                  ondelete = self.case_appointment_ondelete,
                  onvalidation = self.case_appointment_onvalidation,
                  )

        # @todo: onaccept to change status "planning" to "planned" if a date
        #        has been entered, and vice versa

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"dvr_appointment_status_opts": appointment_status_opts,
                "dvr_appointment_type_id": appointment_type_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return {"dvr_appointment_status_opts": {},
                "dvr_appointment_type_id": lambda name="type_id", **attr: \
                                           dummy(name, **attr),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def case_appointment_onvalidation(form):
        """
            Validate appointment form
                - Future appointments can not be set to completed

            @param form: the FORM
        """

        formvars = form.vars

        date = formvars.get("date")
        status = formvars.get("status")

        if date and str(status) == "4" and \
           date > current.request.utcnow.date():

            form.errors["status"] = current.T("Appointments with future dates can not be marked as completed")

    # -------------------------------------------------------------------------
    @staticmethod
    def case_appointment_onaccept(form):
        """
            Actions after creating/updating appointments
                - Update last_seen_on in the corresponding case(s)
                - Update the case status if configured to do so

            @param form: the FORM
        """

        # Read form data
        formvars = form.vars
        if "id" in formvars:
            record_id = formvars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            record_id = None
        if not record_id:
            return

        db = current.db
        s3db = current.s3db

        settings = current.deployment_settings

        person_id = formvars.get("person_id")
        case_id = formvars.get("case_id")

        if not person_id or not case_id:
            table = s3db.dvr_case_appointment
            row = db(table.id == record_id).select(table.case_id,
                                                   table.person_id,
                                                   limitby = (0, 1),
                                                   ).first()
            if row:
                person_id = row.person_id
                case_id = row.case_id

        if settings.get_dvr_appointments_update_last_seen_on() and person_id:
            # Update last_seen_on
            dvr_update_last_seen(person_id)

        # Update the case status if appointment is completed
        # NB appointment status "completed" must be set by this form
        if settings.get_dvr_appointments_update_case_status() and \
           s3_str(formvars.get("status")) == "4":

            # Get the case status to be set when appointment is completed today
            today = current.request.utcnow.date()
            ttable = s3db.dvr_case_appointment_type
            query = (table.id == record_id) & \
                    (table.deleted != True) & \
                    (ttable.id == table.type_id) & \
                    (ttable.status_id != None)
            row = db(query).select(table.date,
                                   ttable.status_id,
                                   limitby = (0, 1),
                                   ).first()
            if row:
                # Check whether there is a later appointment that
                # would have set a different case status (we don't
                # want to override this when closing appointments
                # restrospectively):
                date = row.dvr_case_appointment.date
                status_id = row.dvr_case_appointment_type.status_id
                query = (table.person_id == person_id)
                if case_id:
                    query &= (table.case_id == case_id)
                query &= (table.date != None) & \
                         (table.status == 4) & \
                         (table.date > date) & \
                         (table.deleted != True) & \
                         (ttable.id == table.type_id) & \
                         (ttable.status_id != None) & \
                         (ttable.status_id != status_id)
                later = db(query).select(table.id, limitby = (0, 1)).first()
                if later:
                    status_id = None
            else:
                status_id = None

            if status_id:
                # Update the corresponding case(s)
                # NB appointments without case_id update all cases for the person
                ctable = s3db.dvr_case
                stable = s3db.dvr_case_status
                query = (ctable.person_id == person_id) & \
                        (ctable.archived != True) & \
                        (ctable.deleted != True) & \
                        (stable.id == ctable.status_id) & \
                        (stable.is_closed != True)
                if case_id:
                    query &= (ctable.id == case_id)
                cases = db(query).select(ctable.id,
                                         ctable.person_id,
                                         ctable.archived,
                                         )
                has_permission = current.auth.s3_has_permission
                for case in cases:
                    if has_permission("update", ctable, record_id=case.id):
                        # Customise case resource
                        r = S3Request("dvr", "case",
                                      current.request,
                                      args = [],
                                      get_vars = {},
                                      )
                        r.customise_resource("dvr_case")
                        # Update case status + run onaccept
                        case.update_record(status_id = status_id)
                        s3db.onaccept(ctable, case, method="update")

    # -------------------------------------------------------------------------
    @staticmethod
    def case_appointment_ondelete(row):
        """
            Actions after deleting appointments
                - Update last_seen_on in the corresponding case(s)

            @param row: the deleted Row
        """

        if current.deployment_settings.get_dvr_appointments_update_last_seen_on():

            # Get the deleted keys
            table = current.s3db.dvr_case_appointment
            row = current.db(table.id == row.id).select(table.deleted_fk,
                                                        limitby = (0, 1),
                                                        ).first()
            if row and row.deleted_fk:

                # Get the person ID
                try:
                    deleted_fk = json.loads(row.deleted_fk)
                except (ValueError, TypeError):
                    person_id = None
                else:
                    person_id = deleted_fk.get("person_id")

                # Update last_seen_on
                if person_id:
                    dvr_update_last_seen(person_id)

# =============================================================================
class DVRCaseBeneficiaryModel(S3Model):
    """
        Model for Case Beneficiary Data (=statistical data about beneficiaries
        of the case besides the main beneficiary, e.g. household members)
    """

    names = ("dvr_beneficiary_type",
             "dvr_beneficiary_data",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings

        configure = self.configure
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Beneficiary Types (e.g. Age Groups)
        #
        tablename = "dvr_beneficiary_type"
        define_table(tablename,
                     Field("name",
                           label = T("Type"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_BENEFICIARY_TYPE = T("Create Beneficiary Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_BENEFICIARY_TYPE,
            title_display = T("Beneficiary Type"),
            title_list = T("Beneficiary Types"),
            title_update = T("Edit Beneficiary Type"),
            label_list_button = T("List Beneficiary Types"),
            label_delete_button = T("Delete Beneficiary Type"),
            msg_record_created = T("Beneficiary Type added"),
            msg_record_modified = T("Beneficiary Type updated"),
            msg_record_deleted = T("Beneficiary Type deleted"),
            msg_list_empty = T("No Beneficiary Types currently registered")
            )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        beneficiary_type_id = S3ReusableField("beneficiary_type_id", "reference %s" % tablename,
                                              label = T("Beneficiary Type"),
                                              ondelete = "RESTRICT",
                                              represent = represent,
                                              requires = IS_EMPTY_OR(
                                                            IS_ONE_OF(db, "dvr_beneficiary_type.id",
                                                                      represent)),
                                              )

        # ---------------------------------------------------------------------
        # Beneficiary data
        #
        show_third_gender = not current.deployment_settings.get_pr_hide_third_gender()

        tablename = "dvr_beneficiary_data"
        define_table(tablename,
                     # Main Beneficiary (component link):
                     # @todo: populate from case and hide in case perspective
                     self.pr_person_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     self.dvr_case_id(empty = False,
                                      label = T("Case Number"),
                                      ondelete = "CASCADE",
                                      ),
                     beneficiary_type_id(),
                     Field("total", "integer",
                           label = T("Number of Beneficiaries"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           # Expose in templates when not using per-gender fields
                           readable = False,
                           writable = False,
                           ),
                     Field("female", "integer",
                           label = T("Number Female"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           ),
                     Field("male", "integer",
                           label = T("Number Male"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           ),
                     Field("other", "integer",
                           label = T("Number Other Gender"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           readable = show_third_gender,
                           writable = show_third_gender,
                           ),
                     Field("in_school", "integer",
                           label = T("Number in School"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           ),
                     Field("employed", "integer",
                           label = T("Number Employed"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Beneficiary Data"),
            title_display = T("Beneficiary Data"),
            title_list = T("Beneficiary Data"),
            title_update = T("Edit Beneficiary Data"),
            label_list_button = T("List Beneficiary Data"),
            label_delete_button = T("Delete Beneficiary Data"),
            msg_record_created = T("Beneficiary Data added"),
            msg_record_modified = T("Beneficiary Data updated"),
            msg_record_deleted = T("Beneficiary Data deleted"),
            msg_list_empty = T("No Beneficiary Data currently registered"),
            )

        # List fields
        list_fields = ["beneficiary_type_id",
                       "female",
                       "male",
                       "in_school",
                       "employed",
                       "comments",
                       ]
        if show_third_gender:
            list_fields.insert(3, "other")

        # Table configuration
        configure(tablename,
                  list_fields = list_fields,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"dvr_beneficiary_type_id": beneficiary_type_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return {"dvr_beneficiary_type_id": lambda name="beneficiary_type_id", **attr: \
                                           dummy(name, **attr),
                }


# =============================================================================
class DVRCaseEconomyInformationModel(S3Model):
    """ Model for Household Economy Information """

    names = ("dvr_economy",
             "dvr_income_source",
             "dvr_income_source_economy",
             "dvr_housing_type",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings

        configure = self.configure
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Housing Types
        #
        tablename = "dvr_housing_type"
        define_table(tablename,
                     Field("name",
                           label = T("Type"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_HOUSING_TYPE = T("Create Housing Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_HOUSING_TYPE,
            title_display = T("Housing Type"),
            title_list = T("Housing Types"),
            title_update = T("Edit Housing Type"),
            label_list_button = T("List Housing Types"),
            label_delete_button = T("Delete Housing Type"),
            msg_record_created = T("Housing Type added"),
            msg_record_modified = T("Housing Type updated"),
            msg_record_deleted = T("Housing Type deleted"),
            msg_list_empty = T("No Housing Types currently defined")
            )

        # Represent for reference
        housing_type_represent = S3Represent(lookup = "dvr_housing_type",
                                             translate = True,
                                             )

        # ---------------------------------------------------------------------
        # Income sources
        #
        tablename = "dvr_income_source"
        define_table(tablename,
                     Field("name",
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_INCOME_SOURCE = T("Create Income Source")
        crud_strings[tablename] = Storage(
            label_create = ADD_INCOME_SOURCE,
            title_display = T("Income Source"),
            title_list = T("Income Sources"),
            title_update = T("Edit Income Source"),
            label_list_button = T("List Income Sources"),
            label_delete_button = T("Delete Income Source"),
            msg_record_created = T("Income Source added"),
            msg_record_modified = T("Income Source updated"),
            msg_record_deleted = T("Income Source deleted"),
            msg_list_empty = T("No Income Sources currently defined")
            )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        income_source_id = S3ReusableField("income_source_id", "reference %s" % tablename,
                                           label = T("Income Source"),
                                           ondelete = "RESTRICT",
                                           represent = represent,
                                           requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db,
                                                                  "dvr_income_source.id",
                                                                  represent,
                                                                  )),
                                           )

        # Table configuration
        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Household Economy Information
        #
        tablename = "dvr_economy"
        define_table(tablename,
                     # Beneficiary (component link):
                     # @todo: populate from case and hide in case perspective
                     self.pr_person_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     self.dvr_case_id(empty = False,
                                      label = T("Case Number"),
                                      ondelete = "CASCADE",
                                      ),
                     FieldS3("housing_type_id", "reference dvr_housing_type",
                             label = T("Housing Type"),
                             represent = housing_type_represent,
                             requires = IS_EMPTY_OR(IS_ONE_OF(
                                                db, "dvr_housing_type.id",
                                                housing_type_represent,
                                                )),
                             sortby = "name",
                             comment = S3PopupLink(c = "dvr",
                                                   f = "housing_type",
                                                   title = ADD_HOUSING_TYPE,
                                                   tooltip = T("Choose the housing type from the drop-down, or click the link to create a new type"),
                                                   ),
                             ),
                     Field("monthly_costs", "double",
                           label = T("Monthly Costs"),
                           requires = IS_EMPTY_OR(IS_FLOAT_IN_RANGE(0.0, None)),
                           ),
                     Field("average_weekly_income", "double",
                           label = T("Average Weekly Income"),
                           requires = IS_EMPTY_OR(IS_FLOAT_IN_RANGE(0.0, None)),
                           ),
                     s3_currency(),
                     s3_comments(),
                     *s3_meta_fields())

        # Components
        self.add_components(tablename,
                            dvr_income_source = {"link": "dvr_income_source_economy",
                                                 "joinby": "economy_id",
                                                 "key": "income_source_id",
                                                 "actuate": "link",
                                                 "autodelete": False,
                                                 },
                            )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Economy Information"),
            title_display = T("Economy Information"),
            title_list = T("Economy Information"),
            title_update = T("Edit Economy Information"),
            label_list_button = T("List Economy Information"),
            label_delete_button = T("Delete Economy Information"),
            msg_record_created = T("Economy Information added"),
            msg_record_modified = T("Economy Information updated"),
            msg_record_deleted = T("Economy Information deleted"),
            msg_list_empty = T("No Economy Information currently registered"),
            )

        # CRUD Form
        crud_form = S3SQLCustomForm("housing_type_id",
                                    "monthly_costs",
                                    S3SQLInlineLink("income_source",
                                                    field = "income_source_id",
                                                    label = T("Income Sources"),
                                                    cols = 3,
                                                    ),
                                    "average_weekly_income",
                                    "currency",
                                    "comments",
                                    )

        # List fields
        list_fields = ["housing_type_id",
                       "monthly_costs",
                       "income_source_economy.income_source_id",
                       "average_weekly_income",
                       "comments",
                       ]

        # Table configuration
        configure(tablename,
                  crud_form = crud_form,
                  list_fields = list_fields,
                  )

        # ---------------------------------------------------------------------
        # Link table Economy Information <=> Income Sources
        #
        tablename = "dvr_income_source_economy"
        define_table(tablename,
                     Field("economy_id", "reference dvr_economy",
                           ondelete = "CASCADE",
                           requires = IS_ONE_OF(db, "dvr_economy.id"),
                           ),
                     income_source_id(),
                     s3_comments(),
                     *s3_meta_fields())


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
class DVRCaseAllowanceModel(S3Model):
    """ Model for Allowance Management """

    names = ("dvr_allowance",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings

        configure = self.configure
        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        # Allowance Information
        #
        allowance_status_opts = {1: T("pending"),
                                 2: T("paid"),
                                 3: T("refused"),
                                 4: T("missed"),
                                 }
        amount_represent = lambda v: IS_FLOAT_AMOUNT.represent(v,
                                                               precision = 2,
                                                               fixed = True,
                                                               )

        tablename = "dvr_allowance"
        define_table(tablename,
                     # Beneficiary (component link):
                     # @todo: populate from case and hide in case perspective
                     self.pr_person_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     self.dvr_case_id(# @ToDo: Populate this onaccept from imports
                                      #empty = False,
                                      label = T("Case Number"),
                                      ondelete = "CASCADE",
                                      ),
                     s3_date("entitlement_period",
                             label = T("Entitlement Period"),
                             ),
                     s3_date(default="now",
                             label = T("Planned on"),
                             ),
                     s3_datetime("paid_on",
                                 label = T("Paid on"),
                                 future = 0,
                                 ),
                     Field("amount", "double",
                           label = T("Amount"),
                           represent = amount_represent,
                           ),
                     s3_currency(),
                     Field("status", "integer",
                           default = 1, # pending
                           requires = IS_IN_SET(allowance_status_opts,
                                                zero = None,
                                                ),
                           represent = S3Represent(options=allowance_status_opts,
                                                   ),
                           widget = S3GroupedOptionsWidget(cols = 4,
                                                           multiple = False,
                                                           ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Allowance Information"),
            title_display = T("Allowance Information"),
            title_list = T("Allowance Information"),
            title_update = T("Edit Allowance Information"),
            label_list_button = T("List Allowance Information"),
            label_delete_button = T("Delete Allowance Information"),
            msg_record_created = T("Allowance Information added"),
            msg_record_modified = T("Allowance Information updated"),
            msg_record_deleted = T("Allowance Information deleted"),
            msg_list_empty = T("No Allowance Information currently registered"),
            )

        # Custom list fields
        list_fields = ["person_id",
                       "entitlement_period",
                       "date",
                       "currency",
                       "amount",
                       "status",
                       "paid_on",
                       "comments",
                       ]

        # Table configuration
        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("person_id",
                                                       "entitlement_period",
                                                       ),
                                            ),
                  list_fields = list_fields,
                  onaccept = self.allowance_onaccept,
                  ondelete = self.allowance_ondelete,
                  onvalidation = self.allowance_onvalidation,
                  )

        set_method("dvr", "allowance",
                   method = "register",
                   action = DVRRegisterPayment,
                   )
        set_method("dvr", "allowance",
                   method = "manage",
                   action = DVRManageAllowance,
                   )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"dvr_allowance_status_opts": allowance_status_opts,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        return {"dvr_allowance_status_opts": {},
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def allowance_onvalidation(form):
        """
            Validate allowance form
                - Status paid requires paid_on date

            @param form: the FORM
        """

        formvars = form.vars

        date = formvars.get("paid_on")
        status = formvars.get("status")

        if str(status) == "2" and not date:
            form.errors["paid_on"] = current.T("Date of payment required")

    # -------------------------------------------------------------------------
    @staticmethod
    def allowance_onaccept(form):
        """
            Actions after creating/updating allowance information
                - update last_seen_on
        """

        if current.deployment_settings.get_dvr_payments_update_last_seen_on():

            # Read form data
            form_vars = form.vars
            if "id" in form_vars:
                record_id = form_vars.id
            elif hasattr(form, "record_id"):
                record_id = form.record_id
            else:
                record_id = None
            if not record_id:
                return

            # Get the person ID
            table = current.s3db.dvr_allowance
            row = current.db(table.id == record_id).select(table.person_id,
                                                           limitby = (0, 1),
                                                           ).first()
            # Update last_seen_on
            if row:
                dvr_update_last_seen(row.person_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def allowance_ondelete(row):
        """
            Actions after deleting allowance information
                - Update last_seen_on in the corresponding case(s)

            @param row: the deleted Row
        """

        if current.deployment_settings.get_dvr_payments_update_last_seen_on():

            # Get the deleted keys
            table = current.s3db.dvr_allowance
            row = current.db(table.id == row.id).select(table.deleted_fk,
                                                        limitby = (0, 1),
                                                        ).first()
            if row and row.deleted_fk:

                # Get the person ID
                try:
                    deleted_fk = json.loads(row.deleted_fk)
                except (ValueError, TypeError):
                    person_id = None
                else:
                    person_id = deleted_fk.get("person_id")

                # Update last_seen_on
                if person_id:
                    dvr_update_last_seen(person_id)

# =============================================================================
class DVRCaseEventModel(S3Model):
    """ Model representing monitoring events for cases """

    names = ("dvr_case_event_type",
             "dvr_case_event",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        crud_strings = s3.crud_strings

        configure = self.configure
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Case Event Types
        #
        role_table = str(current.auth.settings.table_group)
        role_represent = S3Represent(lookup=role_table, fields=("role",))

        close_appointments = settings.get_dvr_case_events_close_appointments()

        tablename = "dvr_case_event_type"
        define_table(tablename,
                     Field("code", notnull=True, length=64, unique=True,
                           label = T("Code"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_NOT_ONE_OF(db,
                                                     "dvr_case_event_type.code",
                                                     ),
                                       ],
                           ),
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("is_default", "boolean",
                           default = False,
                           label = T("Default Event Type"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Default Event Type"),
                                                             T("Assume this event type if no type was specified for an event"),
                                                             ),
                                         ),
                           ),
                     Field("role_required", "reference %s" % role_table,
                           label = T("User Role Required"),
                           ondelete = "SET NULL",
                           represent = role_represent,
                           requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                            "%s.id" % role_table,
                                                            role_represent,
                                                            )),
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("User Role Required"),
                                                             T("User role required to register events of this type"),
                                                             ),
                                         ),
                           ),
                     self.dvr_appointment_type_id(
                        "appointment_type_id",
                        label = T("Appointment Type"),
                        readable = close_appointments,
                        writable = close_appointments,
                        comment = DIV(_class = "tooltip",
                                      _title = "%s|%s" % (T("Appointment Type"),
                                                          T("The type of appointments which are completed with this type of event"),
                                                          ),
                                      ),

                        ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Event Type"),
            title_display = T("Event Type Details"),
            title_list = T("Event Types"),
            title_update = T("Edit Event Type"),
            label_list_button = T("List Event Types"),
            label_delete_button = T("Delete Event Type"),
            msg_record_created = T("Event Type created"),
            msg_record_modified = T("Event Type updated"),
            msg_record_deleted = T("Event Type deleted"),
            msg_list_empty = T("No Event Types currently defined"),
        )

        # Table Configuration
        configure(tablename,
                  onaccept = self.case_event_type_onaccept,
                  )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        event_type_id = S3ReusableField("type_id", "reference %s" % tablename,
                                        label = T("Event Type"),
                                        ondelete = "RESTRICT",
                                        represent = represent,
                                        requires = IS_ONE_OF(db, "%s.id" % tablename,
                                                             represent,
                                                             ),
                                        sortby = "name",
                                        comment = S3PopupLink(c = "dvr",
                                                              f = "case_event_type",
                                                              tooltip = T("Create a new event type"),
                                                              ),
                                        )

        # ---------------------------------------------------------------------
        # Case Events
        #
        tablename = "dvr_case_event"
        define_table(tablename,
                     self.dvr_case_id(comment = None,
                                      empty = False,
                                      label = T("Case Number"),
                                      ondelete = "CASCADE",
                                      readable = False,
                                      writable = False,
                                      ),
                     # Beneficiary (component link):
                     # @todo: populate from case and hide in case perspective
                     self.pr_person_id(comment = None,
                                       empty = False,
                                       ondelete = "CASCADE",
                                       writable = False,
                                       ),
                     event_type_id(comment = None,
                                   ondelete = "CASCADE",
                                   # Not user-writable as this is for automatic
                                   # event registration, override in template if
                                   # required:
                                   writable = False,
                                   ),
                     s3_datetime(label = T("Date/Time"),
                                 default = "now",
                                 empty = False,
                                 future = 0,
                                 writable = False,
                                 ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Event"),
            title_display = T("Event Details"),
            title_list = T("Events"),
            title_update = T("Edit Event"),
            label_list_button = T("List Events"),
            label_delete_button = T("Delete Event"),
            msg_record_created = T("Event added"),
            msg_record_modified = T("Event updated"),
            msg_record_deleted = T("Event deleted"),
            msg_list_empty = T("No Events currently registered"),
            )

        # Filter Widgets
        filter_widgets = [S3TextFilter(["person_id$pe_label",
                                        "person_id$first_name",
                                        "person_id$middle_name",
                                        "person_id$last_name",
                                        "created_by$email",
                                        "comments",
                                        ],
                                        label = T("Search"),
                                       ),
                          S3OptionsFilter("type_id",
                                          options = lambda: s3_get_filter_opts("dvr_case_event_type",
                                                                               translate = True,
                                                                               ),
                                          ),
                          S3DateFilter("date"),
                          ]

        # Table Configuration
        configure(tablename,
                  create_onaccept = self.case_event_create_onaccept,
                  deduplicate = S3Duplicate(primary = ("person_id",
                                                       "type_id",
                                                       ),
                                            ),
                  filter_widgets = filter_widgets,
                  # Not user-insertable as this is for automatic
                  # event registration, override in template if
                  # required:
                  insertable = False,
                  list_fields = ["person_id",
                                 "date",
                                 "type_id",
                                 (T("Registered by"), "created_by"),
                                 "comments",
                                 ],
                  ondelete = self.case_event_ondelete,
                  orderby = "%s.date desc" % tablename,
                  )

        # Custom method for event registration
        self.set_method("dvr", "case_event",
                        method = "register",
                        action = DVRRegisterCaseEvent,
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

    # -------------------------------------------------------------------------
    @staticmethod
    def case_event_type_onaccept(form):
        """
            Onaccept routine for case event types:
            - only one type can be the default

            @param form: the FORM
        """

        form_vars = form.vars
        try:
            record_id = form_vars.id
        except AttributeError:
            record_id = None
        if not record_id:
            return

        # If this type is the default, then set is_default-flag
        # for all other types to False:
        if "is_default" in form_vars and form_vars.is_default:
            table = current.s3db.dvr_case_event_type
            db = current.db
            db(table.id != record_id).update(is_default = False)

    # -------------------------------------------------------------------------
    @staticmethod
    def case_event_create_onaccept(form):
        """
            Actions after creation of a case event:
                - update last_seen_on in the corresponding cases
                - close appointments if configured to do so

            @param form: the FORM
        """

        formvars = form.vars
        try:
            record_id = formvars.id
        except AttributeError:
            record_id = None
        if not record_id:
            return

        db = current.db
        s3db = current.s3db

        close_appointments = current.deployment_settings \
                                    .get_dvr_case_events_close_appointments()

        case_id = formvars.get("case_id")
        person_id = formvars.get("person_id")
        type_id = formvars.get("type_id")

        if not person_id or \
           close_appointments and (not case_id or not type_id):
            # Reload the record
            table = s3db.dvr_case_event
            row = db(table.id == record_id).select(table.case_id,
                                                   table.person_id,
                                                   table.type_id,
                                                   limitby = (0, 1),
                                                   ).first()
            if not row:
                return

            case_id = row.case_id
            person_id == row.person_id
            type_id = row.type_id

        if not person_id:
            return

        # Update last_seen
        dvr_update_last_seen(person_id)

        # Close appointments
        if close_appointments and type_id:

            atable = s3db.dvr_case_appointment
            ttable = s3db.dvr_case_event_type

            today = current.request.utcnow.date()

            left = atable.on((atable.type_id == ttable.appointment_type_id) & \
                             (atable.person_id == person_id) & \
                             ((atable.date == None) | (atable.date <= today)) & \
                             (atable.deleted != True)
                             )

            query = (ttable.id == type_id) & \
                    (ttable.appointment_type_id != None) & \
                    (ttable.deleted != True)

            if case_id:
                query &= (atable.case_id == case_id) | \
                         (atable.case_id == None)
            rows = db(query).select(ttable.appointment_type_id,
                                    atable.id,
                                    atable.date,
                                    atable.status,
                                    left = left,
                                    orderby = ~atable.date,
                                    )

            data = {"date": today, "status": 4}
            if rows:
                update = None
                create = False

                first = rows[0].dvr_case_appointment
                if first.id is None:
                    # No appointment of this type yet
                    create = True

                else:
                    # Find key dates
                    undated = open_today = closed_today = previous = None
                    for row in rows:
                        appointment = row.dvr_case_appointment
                        if appointment.date is None:
                            if not undated:
                                # An appointment without date
                                undated = appointment
                        elif appointment.date == today:
                            if appointment.status != 4:
                                # An open or cancelled appointment today
                                open_today = appointment
                            else:
                                # A closed appointment today
                                closed_today = appointment
                        elif previous is None:
                            # The last appointment before today
                            previous = appointment

                    if open_today:
                        # If we have an open appointment for today, update it
                        update = open_today
                    elif closed_today:
                        # If we already have a closed appointment for today,
                        # do nothing
                        update = None
                    elif previous:
                        if previous.status not in (1, 2, 3):
                            # Last appointment before today is closed
                            # => create a new one unless there is an undated one
                            if undated:
                                update = undated
                            else:
                                create = True
                        else:
                            # Last appointment before today is still open
                            # => update it
                            update = previous
                    else:
                        update = undated

                if create:
                    # Create a new closed appointment
                    data["type_id"] = rows[0].dvr_case_event_type.appointment_type_id
                    data["person_id"] = person_id
                    data["case_id"] = case_id
                    aresource = s3db.resource("dvr_case_appointment")
                    try:
                        record_id = aresource.insert(**data)
                    except S3PermissionError:
                        current.log.error("Event Registration: %s" % sys.exc_info()[1])

                elif update:
                    # Update the appointment
                    permitted = current.auth.s3_has_permission("update",
                                                               atable,
                                                               record_id=update.id,
                                                               )
                    if permitted:
                        # Customise appointment resource
                        r = S3Request("dvr", "case_appointment",
                                      current.request,
                                      args = [],
                                      get_vars = {},
                                      )
                        r.customise_resource("dvr_case_appointment")
                        # Update appointment
                        success = update.update_record(**data)
                        if success:
                            data["id"] = update.id
                            s3db.onaccept(atable, data, method="update")
                        else:
                            current.log.error("Event Registration: could not update appointment %s" % update.id)
                    else:
                        current.log.error("Event registration: not permitted to update appointment %s" % update.id)

    # -------------------------------------------------------------------------
    @staticmethod
    def case_event_ondelete(row):
        """
            Actions after deleting a case event:
                - update last_seen_on in the corresponding cases

            @param row: the deleted Row
        """

        # Get the deleted keys
        table = current.s3db.dvr_case_event
        row = current.db(table.id == row.id).select(table.deleted_fk,
                                                    limitby = (0, 1),
                                                    ).first()
        if row and row.deleted_fk:

            # Get the person ID
            try:
                deleted_fk = json.loads(row.deleted_fk)
            except (ValueError, TypeError):
                person_id = None
            else:
                person_id = deleted_fk.get("person_id")

            # Update last_seen_on
            if person_id:
                dvr_update_last_seen(person_id)

# =============================================================================
def dvr_case_default_status():
    """
        Helper to get/set the default status for case records

        @return: the default status_id
    """

    s3db = current.s3db

    ctable = s3db.dvr_case
    field = ctable.status_id

    default = field.default
    if default:
        # Already set
        return default

    # Look up the default status
    stable = s3db.dvr_case_status
    query = (stable.is_default == True) & \
            (stable.deleted != True)
    row = current.db(query).select(stable.id, limitby=(0, 1)).first()

    if row:
        # Set as field default in case table
        ctable = s3db.dvr_case
        default = field.default = row.id

    return default

# =============================================================================
def dvr_case_status_filter_opts(closed=None):
    """
        Get filter options for case status, ordered by workflow position

        @return: OrderedDict of options

        @note: set sort=False for filter widget to retain this order
    """

    table = current.s3db.dvr_case_status
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

# =============================================================================
def dvr_case_household_size(group_id):
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
        ctable = s3db.dvr_case
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

# =============================================================================
def dvr_due_followups():
    """ Number of due follow-ups """

    query = (FS("followup") == True) & \
            (FS("followup_date") <= datetime.datetime.utcnow().date()) & \
            (FS("completed") != True) & \
            (FS("person_id$dvr_case.archived") == False)
    resource = current.s3db.resource("dvr_case_activity", filter=query)

    return resource.count()

# =============================================================================
class DVRManageAppointments(S3Method):
    """ Custom method to bulk-manage appointments """

    def apply_method(self, r, **attr):

        T = current.T
        s3db = current.s3db

        get_vars = r.get_vars
        response = current.response

        if not self._permitted("update"):
            r.unauthorised()

        if r.http == "POST" and r.representation != "aadata":

            count = 0

            base_query = (FS("person_id$case.archived") == None) | \
                         (FS("person_id$case.archived") == False)

            post_vars = r.post_vars
            if "selected" in post_vars and "mode" in post_vars and \
               any([n in post_vars for n in ("completed", "cancelled")]):

                selected = post_vars.selected
                if selected:
                    selected = selected.split(",")
                else:
                    selected = []

                db = current.db
                atable = s3db.dvr_case_appointment

                # Handle exclusion filter
                if post_vars.mode == "Exclusive":
                    if "filterURL" in post_vars:
                        filters = S3URLQuery.parse_url(post_vars.filterURL)
                    else:
                        filters = None
                    query = ~(FS("id").belongs(selected)) & base_query

                    aresource = s3db.resource("dvr_case_appointment",
                                              filter = query,
                                              vars =  filters,
                                              )
                    rows = aresource.select(["id"], as_rows=True)
                    selected = [str(row.id) for row in rows]

                if selected:
                    query = (atable.id.belongs(selected)) & \
                            (atable.deleted != True)
                    if "completed" in post_vars:
                        count = db(query).update(status=4) # Completed
                    elif "cancelled" in post_vars:
                        count = db(query).update(status=6) # Cancelled

            current.session.confirmation = T("%(count)s Appointments updated") % \
                                           {"count": count}
            redirect(URL(f="case_appointment", args=["manage"], vars={}))

        elif r.http == "GET" or r.representation == "aadata":
            resource = r.resource

            # Filter widgets
            filter_widgets = resource.get_config("filter_widgets")

            # List fields
            list_fields = ["id",
                           (T("ID"), "person_id$pe_label"),
                           "person_id",
                           "type_id",
                           "date",
                           "status",
                           ]

            # Data table
            totalrows = resource.count()
            if "pageLength" in get_vars:
                display_length = get_vars["pageLength"]
                if display_length == "None":
                    display_length = None
                else:
                    display_length = int(display_length)
            else:
                display_length = 25
            if display_length:
                limit = 4 * display_length
            else:
                limit = None

            # Sorting by person_id requires introspection => use datatable_filter
            if r.representation != "aadata":
                get_vars = dict(get_vars)
                dt_sorting = {"iSortingCols": "1",
                              "bSortable_0": "false",
                              "iSortCol_0": "1",
                              "sSortDir_0": "asc",
                              }
                get_vars.update(dt_sorting)
            filter, orderby, left = resource.datatable_filter(list_fields, get_vars)
            resource.add_filter(filter)
            data = resource.select(list_fields,
                                   start = 0,
                                   limit = limit,
                                   orderby = orderby,
                                   left = left,
                                   count = True,
                                   represent = True,
                                   )
            filteredrows = data["numrows"]
            dt = S3DataTable(data["rfields"], data["rows"], orderby=orderby)
            dt_id = "datatable"

            # Bulk actions
            dt_bulk_actions = [(T("Completed"), "completed"),
                               (T("Cancelled"), "cancelled"),
                               ]

            if r.representation == "html":
                # Page load
                resource.configure(deletable = False)

                dt.defaultActionButtons(resource)
                response.s3.no_formats = True

                # Data table (items)
                items = dt.html(totalrows,
                                filteredrows,
                                dt_id,
                                dt_pageLength = display_length,
                                dt_ajax_url = URL(c = "dvr",
                                                  f = "case_appointment",
                                                  args = ["manage"],
                                                  vars = {},
                                                  extension = "aadata",
                                                  ),
                                dt_searching = "false",
                                dt_pagination = "true",
                                dt_bulk_actions = dt_bulk_actions,
                                )

                # Filter form
                if filter_widgets:

                    # Where to retrieve filtered data from:
                    _vars = resource.crud._remove_filters(r.get_vars)
                    filter_submit_url = r.url(vars=_vars)

                    # Where to retrieve updated filter options from:
                    filter_ajax_url = URL(f = "case_appointment",
                                          args = ["filter.options"],
                                          vars = {},
                                          )

                    get_config = resource.get_config
                    filter_clear = get_config("filter_clear", True)
                    filter_formstyle = get_config("filter_formstyle", None)
                    filter_submit = get_config("filter_submit", True)
                    filter_form = S3FilterForm(filter_widgets,
                                               clear = filter_clear,
                                               formstyle = filter_formstyle,
                                               submit = filter_submit,
                                               ajax = True,
                                               url = filter_submit_url,
                                               ajaxurl = filter_ajax_url,
                                               _class = "filter-form",
                                               _id = "datatable-filter-form",
                                               )
                    fresource = current.s3db.resource(resource.tablename)
                    alias = resource.alias if r.component else None
                    ff = filter_form.html(fresource,
                                          r.get_vars,
                                          target = "datatable",
                                          alias = alias,
                                          )
                else:
                    ff = ""

                output = dict(items = items,
                              title = T("Manage Appointments"),
                              list_filter_form = ff,
                              )

                response.view = "list_filter.html"
                return output

            elif r.representation == "aadata":

                # Ajax refresh
                if "draw" in get_vars:
                    echo = int(get_vars["draw"])
                else:
                    echo = None
                items = dt.json(totalrows,
                                filteredrows,
                                dt_id,
                                echo,
                                dt_bulk_actions = dt_bulk_actions,
                                )
                response.headers["Content-Type"] = "application/json"
                return items

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

# =============================================================================
class DVRManageAllowance(S3Method):
    """ Method handler to bulk-update allowance payments status """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Main entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller parameters
        """

        # User must be permitted to update allowance information
        permitted = self._permitted("update")
        if not permitted:
            r.unauthorised()

        if r.representation in ("html", "iframe"):
            if r.http in ("GET", "POST"):
                output = self.bulk_update_status(r, **attr)
            else:
                r.error(405, current.ERROR.BAD_METHOD)
        else:
            r.error(415, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def bulk_update_status(self, r, **attr):
        """
            Method to bulk-update status of allowance payments

            @param r: the S3Request instance
            @param attr: controller parameters
        """

        T = current.T
        s3db = current.s3db

        settings = current.deployment_settings
        response = current.response

        output = {"title": T("Update Allowance Status"),
                  }

        status_opts = dict(s3db.dvr_allowance_status_opts)

        # Can not bulk-update from or to status "paid"
        del status_opts[2]

        # Form fields
        formfields = [s3_date("from_date",
                              label = T("Planned From"),
                              set_min = "#allowance_to_date",
                              ),
                      s3_date("to_date",
                              default = "now",
                              label = T("Planned Until"),
                              set_max = "#allowance_from_date",
                              empty = False,
                              ),
                      Field("current_status", "integer",
                            default = 1, # pending
                            label = T("Current Status"),
                            requires = IS_IN_SET(status_opts),
                            ),
                      Field("new_status", "integer",
                            default = 4, # missed
                            label = T("New Status"),
                            requires = IS_IN_SET(status_opts),
                            ),
                      ]

        # Form buttons
        submit_btn = INPUT(_class = "tiny primary button",
                           _name = "submit",
                           _type = "submit",
                           _value = T("Update"),
                           )
        cancel_btn = A(T("Cancel"),
                       _href = r.url(id=None, method=""),
                       _class = "action-lnk",
                       )
        buttons = [submit_btn, cancel_btn]

        # Generate the form and add it to the output
        resourcename = r.resource.name
        formstyle = settings.get_ui_formstyle()
        form = SQLFORM.factory(record = None,
                               showid = False,
                               formstyle = formstyle,
                               table_name = resourcename,
                               buttons = buttons,
                               *formfields)
        output["form"] = form

        # Process the form
        formname = "%s/manage" % resourcename
        if form.accepts(r.post_vars,
                        current.session,
                        formname = formname,
                        onvalidation = self.validate,
                        keepvalues = False,
                        hideerror = False,
                        ):

            formvars = form.vars

            current_status = formvars.current_status
            new_status = formvars.new_status

            table = s3db.dvr_allowance
            query = current.auth.s3_accessible_query("update", table) & \
                    (table.status == current_status) & \
                    (table.deleted != True)
            from_date = formvars.from_date
            if from_date:
                query &= table.date >= from_date
            to_date = formvars.to_date
            if to_date:
                query &= table.date <= to_date

            result = current.db(query).update(status=int(new_status))
            if result:
                response.confirmation = T("%(number)s records updated") % \
                                        {"number": result}
            else:
                response.warning = T("No records found")

        response.view = self._view(r, "update.html")
        return output

    # -------------------------------------------------------------------------
    def validate(self, form):
        """
            Update form validation

            @param form: the FORM
        """

        T = current.T

        formvars = form.vars
        errors = form.errors

        # Must not update from status "paid"
        if str(formvars.current_status) == "2":
            errors.current_status = T("Bulk update from this status not allowed")

        # Must not update to status "paid"
        if str(formvars.new_status) == "2":
            errors.new_status = T("Bulk update to this status not allowed")

        # To-date must be after from-date
        from_date = formvars.from_date
        to_date = formvars.to_date
        if from_date and to_date and from_date > to_date:
            errors.to_date = T("Date until must be after date from")

# =============================================================================
class DVRRegisterCaseEvent(S3Method):
    """ Method handler to register case events """

    # Action to check flag restrictions for
    ACTION = "id-check"

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Main entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller parameters
        """

        if not self.permitted():
            current.auth.permission.fail()

        output = {}
        representation = r.representation

        if representation == "html":
            if r.http in ("GET", "POST"):
                output = self.registration_form(r, **attr)
            else:
                r.error(405, current.ERROR.BAD_METHOD)

        elif representation == "json":
            if r.http == "POST":
                output = self.registration_ajax(r, **attr)
            else:
                r.error(405, current.ERROR.BAD_METHOD)

        else:
            r.error(415, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def registration_form(self, r, **attr):
        """
            Render and process the registration form

            @param r: the S3Request instance
            @param attr: controller parameters
        """

        T = current.T

        s3db = current.s3db
        response = current.response
        settings = current.deployment_settings

        s3 = response.s3

        output = {}
        error = None

        http = r.http
        request_vars = r.get_vars

        check = True
        label = None

        if http == "POST":
            # Form submission
            request_vars = r.post_vars
            if "check" in request_vars:
                # Only check ID label, don't register an event
                label = request_vars.get("label")
            else:
                # Form has been submitted with "Register"
                check = False
        else:
            # Coming from external scan app (e.g. Zxing), or from a link
            label = request_vars.get("label")

        scanner = request_vars.get("scanner")

        person = None
        pe_label = None

        if label is not None:
            # Identify the person
            person = self.get_person(label)
            if person is None:
                if http == "GET":
                    response.error = T("No person found with this ID number")
            else:
                pe_label = person.pe_label
                request_vars["label"] = pe_label

        # Get flag and permission info
        flags = []
        if person:
            name = s3_fullname(person)
            dob = person.date_of_birth
            if dob:
                dob = S3DateTime.date_represent(dob)
                person_data = "%s (%s %s)" % (name, T("Date of Birth"), dob)
            else:
                person_data = name
            flag_info = dvr_get_flag_instructions(person.id,
                                                  action = self.ACTION,
                                                  )
            permitted = flag_info["permitted"]
            if check:
                info = flag_info["info"]
                for flagname, instructions in info:
                    flags.append({"n": s3_str(T(flagname)),
                                  "i": s3_str(T(instructions)),
                                  })
        else:
            person_data = ""
            permitted = False

        # Identify the event type
        event_code = request_vars.get("event")
        event_type = self.get_event_type(event_code)
        if not event_type:
            # Fall back to default event type
            event_type = self.get_event_type()
        event_code = event_type.code if event_type else None

        # Whether the event registration is actionable
        actionable = event_code is not None

        # Standard form fields and data
        formfields = [Field("label",
                            label = T("ID"),
                            requires = IS_NOT_EMPTY(error_message=T("Enter or scan an ID")),
                            ),
                      Field("person",
                            label = "",
                            writable = False,
                            default = "",
                            ),
                      Field("flaginfo",
                            label = "",
                            writable = False,
                            ),
                      ]

        data = {"id": "",
                "label": pe_label,
                "person": person_data,
                "flaginfo": "",
                }

        # Hidden fields to store event type, scanner, flag info and permission
        hidden = {"event": event_code,
                  "scanner": scanner,
                  "actionable": json.dumps(actionable),
                  "permitted": json.dumps(permitted),
                  "flags": json.dumps(flags),
                  }

        # Additional form data
        widget_id, submit = self.get_form_data(person,
                                               formfields,
                                               data,
                                               hidden,
                                               permitted = permitted,
                                               )

        # Form buttons
        check_btn = INPUT(_class = "tiny secondary button check-btn",
                          _name = "check",
                          _type = "submit",
                          _value = T("Check ID"),
                          )
        submit_btn = INPUT(_class = "tiny primary button submit-btn",
                           _name = "submit",
                           _type = "submit",
                           _value = submit,
                           )

        # Toggle buttons (active button first, otherwise pressing Enter
        # hits the disabled button so requiring an extra tab step)
        actionable = hidden.get("actionable") == "true"
        if person and actionable and permitted:
            check_btn["_disabled"] = "disabled"
            check_btn.add_class("hide")
            buttons = [submit_btn, check_btn]
        else:
            submit_btn["_disabled"] = "disabled"
            submit_btn.add_class("hide")
            buttons = [check_btn, submit_btn]

        # Add the cancel-action
        buttons.append(A(T("Cancel"), _class = "cancel-action action-lnk"))

        resourcename = r.resource.name

        # Generate the form and add it to the output
        formstyle = settings.get_ui_formstyle()
        form = SQLFORM.factory(record = data if check else None,
                               showid = False,
                               formstyle = formstyle,
                               table_name = resourcename,
                               buttons = buttons,
                               hidden = hidden,
                               _id = widget_id,
                               *formfields)
        output["form"] = form

        # Process the form
        formname = "%s/registration" % resourcename
        if form.accepts(r.post_vars,
                        current.session,
                        onvalidation = self.validate,
                        formname = formname,
                        keepvalues = False,
                        hideerror = False,
                        ):

            if not check:
                self.accept(r, form, event_type=event_type)

        header = self.get_header(event_type)
        output.update(header)

        # ZXing Barcode Scanner Launch Button
        output["zxing"] = self.get_zxing_launch_button(event_code)

        # Custom view
        response.view = self._view(r, "dvr/register_case_event.html")

        # Inject JS
        options = {"tablename": resourcename,
                   "ajaxURL": r.url(None,
                                    method = "register",
                                    representation = "json",
                                    ),
                   }
        self.inject_js(widget_id, options)

        return output

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    def permitted(self):
        """
            Helper function to check permissions

            @return: True if permitted to use this method, else False
        """

        # User must be permitted to create case events
        return self._permitted("create")

    # -------------------------------------------------------------------------
    def get_event_type(self, code=None):
        """
            Get a case event type for an event code

            @param code: the type code (using default event type if None)

            @return: the dvr_case_event_type Row, or None if not found
        """

        event_types = self.get_event_types()

        event_type = None
        if code is None:
            event_type = event_types.get("_default")
        else:
            for value in event_types.values():
                if value.code == code:
                    event_type = value
                    break

        return event_type

    # -------------------------------------------------------------------------
    def validate(self, form):
        """
            Validate the event registration form

            @param form: the FORM
        """

        T = current.T

        formvars = form.vars
        pe_label = formvars.get("label").strip()

        person = self.get_person(pe_label)
        if person is None:
            form.errors["label"] = T("No person found with this ID number")
            permitted = False
        else:
            person_id = person.id
            formvars.person_id = person_id
            flag_info = dvr_get_flag_instructions(person_id,
                                                  action = self.ACTION,
                                                  )
            permitted = flag_info["permitted"]
        formvars.permitted = permitted

        # Validate the event type (if not default)
        type_id = None
        event_code = formvars.get("event_code")
        if event_code:
            event_type = self.get_event_type(event_code)
            if not event_type:
                form.errors["event_code"] = T("Invalid event code")
            else:
                type_id = event_type.id
        formvars.type_id = type_id

    # -------------------------------------------------------------------------
    def accept(self, r, form, event_type=None):
        """
            Helper function to process the form

            @param r: the S3Request
            @param form: the FORM
            @param event_type: the event_type (Row)
        """

        T = current.T
        response = current.response

        formvars = form.vars
        person_id = formvars.person_id

        success = False

        if not formvars.get("permitted"):
            response.error = T("Event registration not permitted")

        elif person_id:
            event_type_id = event_type.id if event_type else None
            success = self.register_event(person_id, event_type_id)
            if success:
                success = True
                response.confirmation = T("Event registered")
            else:
                response.error = T("Could not register event")

        else:
            response.error = T("Person not found")

        return success

    # -------------------------------------------------------------------------
    def registration_ajax(self, r, **attr):
        """
            Ajax response method, expects a JSON input like:

                {l: the PE label (from the input field),
                 c: boolean to indicate whether to just check
                    the PE label or to register payments
                 t: the event type code
                 }

            @param r: the S3Request instance
            @param attr: controller parameters

            @return: JSON response, structure:

                    {l: the actual PE label (to update the input field),
                     p: the person details,
                     f: [{n: the flag name
                          i: the flag instructions
                          },
                         ...],

                     s: whether the action is permitted or not

                     e: form error (for label field)

                     a: error message
                     w: warning message
                     m: success message
                     }
        """

        T = current.T

        # Load JSON data from request body
        s = r.body
        s.seek(0)
        try:
            data = json.load(s)
        except (ValueError, TypeError):
            r.error(400, current.ERROR.BAD_REQUEST)


        # Initialize processing variables
        output = {}

        error = None

        alert = None
        message = None
        warning = None

        permitted = False
        flags = []

        # Identify the person
        pe_label = data.get("l")
        person = self.get_person(pe_label)

        if person is None:
            error = s3_str(T("No person found with this ID number"))

        else:
            # Get flag info
            flag_info = dvr_get_flag_instructions(person.id,
                                                  action = "id-check",
                                                  )
            permitted = flag_info["permitted"]

            check = data.get("c")
            if check:

                name = s3_fullname(person)
                dob = person.date_of_birth
                if dob:
                    dob = S3DateTime.date_represent(dob)
                    person_data = "%s (%s %s)" % (name, T("Date of Birth"), dob)
                else:
                    person_data = name

                output["p"] = s3_str(person_data)
                output["l"] = person.pe_label

                info = flag_info["info"]
                for flagname, instructions in info:
                    flags.append({"n": s3_str(T(flagname)),
                                  "i": s3_str(T(instructions)),
                                  })
            else:
                event_code = data.get("t")
                if not event_code:
                    alert = T("No event type specified")
                elif not permitted:
                    alert = T("Event registration not permitted")
                else:
                    event_type = self.get_event_type(event_code)
                    if not event_type:
                        alert = T("Invalid event type %s" % event_code)
                    else:
                        success = self.register_event(person.id, event_type.id)
                        if success:
                            message = T("Event registered")
                        else:
                            alert = T("Could not register event")

        # Add messages to output
        if alert:
            output["a"] = s3_str(alert)
        if error:
            output["e"] = s3_str(error)
        if message:
            output["m"] = s3_str(message)
        if warning:
            output["w"] = s3_str(warning)

        # Add flag info to output
        output["s"] = permitted
        output["f"] = flags

        current.response.headers["Content-Type"] = "application/json"
        return json.dumps(output)

    # -------------------------------------------------------------------------
    def get_form_data(self, person, formfields, data, hidden, permitted=False):
        """
            Helper function to extend the form

            @param person: the person (Row)
            @param formfields: list of form fields (Field)
            @param data: the form data (dict)
            @param hidden: hidden form fields (dict)
            @param permitted: whether the action is permitted

            @return: tuple (widget_id, submit_label)
        """

        widget_id = "case-event-form"
        submit = current.T("Register")

        return widget_id, submit

    # -------------------------------------------------------------------------
    def get_header(self, event_type=None):
        """
            Helper function to construct the event type header

            @param event_type: the event type (Row)
            @returns: dict of view items
        """

        T = current.T

        output = {}

        # Event type header
        if event_type:
            event_type_name = T(event_type.name)
        else:
            event_type_name = current.messages["NONE"]

        event_type_header = DIV(H4(SPAN(T(event_type_name),
                                        _class = "event-type-name",
                                        ),
                                   SPAN(ICON("settings"),
                                        _class = "event-type-setting",
                                        ),
                                   _class = "event-type-toggle",
                                   _id = "event-type-toggle",
                                   ),
                                _class = "event-type-header",
                                )
        output["event_type"] = event_type_header

        # Event type selector
        event_types = self.get_event_types()
        buttons = []
        for k, v in event_types.items():
            if k != "_default":
                button = LI(A(T(v.name),
                              _class = "secondary button event-type-selector",
                              data = {"code": s3_str(v.code),
                                      "name": s3_str(T(v.name)),
                                      },
                              ),
                            )
                buttons.append(button)
        output["event_type_selector"] = UL(buttons,
                                           _class="button-group stack hide event-type-selector",
                                           _id="event-type-selector",
                                           )

        return output

    # -------------------------------------------------------------------------
    # Class-specific functions
    # -------------------------------------------------------------------------
    @staticmethod
    def register_event(person_id, type_id):
        """
            Register a case event

            @param person_id: the person record ID
            @param type:id: the event type record ID
        """

        s3db = current.s3db

        ctable = s3db.dvr_case
        etable = s3db.dvr_case_event

        # Get the case ID for the person_id
        query = (ctable.person_id == person_id) & \
                (ctable.deleted != True)
        case = current.db(query).select(ctable.id,
                                        limitby=(0, 1),
                                        ).first()
        if case:
            case_id = case.id
        else:
            case_id = None

        # Customise event resource
        r = S3Request("dvr", "case_event",
                      current.request,
                      args = [],
                      get_vars = {},
                      )
        r.customise_resource("dvr_case_event")

        data = {"person_id": person_id,
                "case_id": case_id,
                "type_id": type_id,
                "date": current.request.utcnow,
                }
        record_id = etable.insert(**data)
        if record_id:
            # Set record owner
            auth = current.auth
            auth.s3_set_record_owner(etable, record_id)
            auth.s3_make_session_owner(etable, record_id)
            # Execute onaccept
            data["id"] = record_id
            s3db.onaccept(etable, data, method="create")

        return record_id

    # -------------------------------------------------------------------------
    def get_event_types(self):
        """
            Lazy getter for case event types

            @return: a dict {id: Row} for dvr_case_event_type, with an
                     additional key "_default" for the default event type
        """

        if not hasattr(self, "event_types"):

            event_types = {}
            table = current.s3db.dvr_case_event_type

            query = (table.deleted != True)

            sr = current.auth.get_system_roles()
            roles = current.session.s3.roles
            if sr.ADMIN not in roles:
                query &= (table.role_required == None) | \
                         (table.role_required.belongs(roles))

            rows = current.db(query).select(table.id,
                                            table.code,
                                            table.name,
                                            table.is_default,
                                            table.comments,
                                            )
            for row in rows:
                event_types[row.id] = row
                if row.is_default:
                    event_types["_default"] = row
            self.event_types = event_types

        return self.event_types

    # -------------------------------------------------------------------------
    # Common methods
    # -------------------------------------------------------------------------
    @classmethod
    def get_person(cls, pe_label):
        """
            Get the person record for a PE Label (or ID code), search only
            for persons with an open DVR case.

            @param pe_label: the PE label (or a scanned ID code as string)
        """

        s3db = current.s3db
        person = None

        # Fields to extract
        fields = ["id",
                  "pe_label",
                  "first_name",
                  "middle_name",
                  "last_name",
                  "date_of_birth",
                  "gender",
                  ]

        data = cls.parse_code(pe_label)

        def person_(label):
            """ Helper function to find a person by pe_label """

            query = (FS("pe_label") == pe_label) & \
                    (FS("dvr_case.id") != None) & \
                    (FS("dvr_case.archived") != True) & \
                    (FS("dvr_case.status_id$is_closed") != True)
            presource = s3db.resource("pr_person", filter=query)
            rows = presource.select(fields,
                                    start = 0,
                                    limit = 1,
                                    as_rows = True,
                                    )
            return rows[0] if rows else None

        pe_label = data["label"]
        if pe_label:
            person = person_(pe_label)
        if person:
            data_match = True
        else:
            family = data.get("family")
            if family:
                # Get the head of family
                person = person_(family)
                data_match = False

        if person:

            first_name, last_name = None, None
            if "first_name" in data:
                first_name = s3_unicode(data["first_name"]).lower()
                if s3_unicode(person.first_name).lower() != first_name:
                    data_match = False
            if "last_name" in data:
                last_name = s3_unicode(data["last_name"]).lower()
                if s3_unicode(person.last_name).lower() != last_name:
                    data_match = False

            if not data_match:
                # Family member? => search by names/DoB
                ptable = s3db.pr_person
                query = current.auth.s3_accessible_query("read", ptable)

                gtable = s3db.pr_group
                mtable = s3db.pr_group_membership
                otable = mtable.with_alias("family")
                ctable = s3db.dvr_case
                stable = s3db.dvr_case_status

                left = [gtable.on((gtable.id == mtable.group_id) & \
                                  (gtable.group_type == 7)),
                        otable.on((otable.group_id == gtable.id) & \
                                  (otable.person_id != mtable.person_id) & \
                                  (otable.deleted != True)),
                        ptable.on((ptable.id == otable.person_id) & \
                                  (ptable.pe_label != None)),
                        ctable.on((ctable.person_id == otable.person_id) & \
                                  (ctable.archived != True)),
                        stable.on((stable.id == ctable.status_id)),
                        ]
                query &= (mtable.person_id == person.id) & \
                         (ctable.id != None) & \
                         (stable.is_closed != True) & \
                         (mtable.deleted != True) & \
                         (ptable.deleted != True)
                if first_name:
                    query &= (ptable.first_name.lower() == first_name)
                if last_name:
                    query &= (ptable.last_name.lower() == last_name)

                if "date_of_birth" in data:
                    # Include date of birth
                    dob, error = IS_UTC_DATE()(data["date_of_birth"])
                    if not error and dob:
                        query &= (ptable.date_of_birth == dob)

                fields_ = [ptable[fn] for fn in fields]
                rows = current.db(query).select(left=left,
                                                limitby = (0, 2),
                                                *fields_)
                if len(rows) == 1:
                    person = rows[0]

        elif "first_name" in data and "last_name" in data:

            first_name = s3_unicode(data["first_name"]).lower()
            last_name = s3_unicode(data["last_name"]).lower()

            # Search by names
            query = (FS("pe_label") != None)
            if first_name:
                query &= (FS("first_name").lower() == first_name)
            if last_name:
                query &= (FS("last_name").lower() == last_name)

            if "date_of_birth" in data:
                # Include date of birth
                dob, error = IS_UTC_DATE()(data["date_of_birth"])
                if not error and dob:
                    query &= (FS("date_of_birth") == dob)

            # Find only open cases
            query &= (FS("dvr_case.id") != None) & \
                     (FS("dvr_case.archived") != True) & \
                     (FS("dvr_case.status_id$is_closed") != True)

            presource = s3db.resource("pr_person", filter=query)
            rows = presource.select(fields,
                                    start = 0,
                                    limit = 2,
                                    as_rows = True,
                                    )
            if len(rows) == 1:
                person = rows[0]

        return person

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_code(code):
        """
            Parse a scanned ID code (QR Code)

            @param code: the scanned ID code (string)

            @return: a dict {"label": the PE label,
                             "first_name": optional first name,
                             "last_name": optional last name,
                             "date_of_birth": optional date of birth,
                             }
        """

        data = {"label": code}

        pattern = current.deployment_settings.get_dvr_id_code_pattern()
        if pattern and code:
            import re
            pattern = re.compile(pattern)
            m = pattern.match(code)
            if m:
                data.update(m.groupdict())

        return data

    # -------------------------------------------------------------------------
    @staticmethod
    def get_zxing_launch_button(event_code):
        """
            Renders the button to launch the Zxing barcode scanner app

            @param event_code: the current event code
            @return: the Zxing launch button
        """

        T = current.T

        # URL template
        template = "zxing://scan/?ret=%s&SCAN_FORMATS=Code 128,UPC_A,EAN_13"

        # Query variables for return URL
        scan_vars = {"label": "{CODE}",
                     "scanner": "zxing",
                     "event": "{EVENT}",
                     }

        # Return URL template
        tmp = URL(args = ["register"],
                  vars = scan_vars,
                  host = True,
                  )
        tmp = str(tmp).replace("&", "%26")

        # Current return URL
        if event_code:
            # must double-escape ampersands:
            scan_vars["event"] = event_code.replace("&", "%2526")
        ret = URL(args = ["register"],
                  vars = scan_vars,
                  host = True,
                  )
        ret = str(ret).replace("&", "%26")

        # Construct button
        return A(T("Scan with Zxing"),
                 _href = template % ret,
                 _class = "tiny primary button zxing-button",
                 data = {"tmp": template % tmp,
                         },
                 )

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_js(widget_id, options):
        """
            Helper function to inject static JS and instantiate
            the eventRegistration widget

            @param widget_id: the node ID where to instantiate the widget
            @param options: dict of widget options (JSON-serializable)
        """

        s3 = current.response.s3
        appname = current.request.application

        # Static JS
        scripts = s3.scripts
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.dvr.js" % appname
        else:
            script = "/%s/static/scripts/S3/s3.dvr.min.js" % appname
        scripts.append(script)

        # Instantiate widget
        scripts = s3.jquery_ready
        script = '''$('#%(id)s').eventRegistration(%(options)s)''' % \
                 {"id": widget_id, "options": json.dumps(options)}
        if script not in scripts:
            scripts.append(script)

# =============================================================================
class DVRRegisterPayment(DVRRegisterCaseEvent):
    """ Method handler to register case events """

    # Action to check flag restrictions for
    ACTION = "payment"

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    def permitted(self):
        """
            Helper function to check permissions

            @return: True if permitted to use this method, else False
        """

        # User must be permitted to update allowance records
        return self._permitted("update")

    # -------------------------------------------------------------------------
    def get_event_type(self, code=None):
        """
            Get a case event type for an event code

            @param code: the type code (using default event type if None)

            @return: the dvr_case_event_type Row, or None if not found
        """

        # Only one type of event
        return Storage(code="PAYMENT")

    # -------------------------------------------------------------------------
    def accept(self, r, form, event_type=None):
        """
            Helper function to process the form

            @param r: the S3Request
            @param form: the FORM
            @param event_type: the event_type (Row)
        """

        T = current.T
        response = current.response

        formvars = form.vars
        person_id = formvars.person_id

        success = False

        if not formvars.get("permitted"):
            response.error = T("Payment registration not permitted")

        elif person_id:
            # Get payment data from hidden input
            payments = r.post_vars.get("actions")
            if payments:

                # @todo: read date from formvars (utcnow as fallback)
                date = r.utcnow
                comments = formvars.get("comments")

                updated, failed = self.register_payments(person_id,
                                                         payments,
                                                         date = date,
                                                         comments = comments,
                                                         )
                response.confirmation = T("%(number)s payment(s) registered") % \
                                        {"number": updated}
                if failed:
                    response.warning = T("%(number)s payment(s) not found") % \
                                       {"number": failed}
            else:
                response.error = T("No payments specified")
        else:
            response.error = T("Person not found")

        return success

    # -------------------------------------------------------------------------
    def registration_ajax(self, r, **attr):
        """
            Ajax response method, expects a JSON input like:

                {l: the PE label (from the input field),
                 c: boolean to indicate whether to just check
                    the PE label or to register payments
                 d: the payment data (raw data, which payments to update)
                 }

            @param r: the S3Request instance
            @param attr: controller parameters

            @return: JSON response, structure:

                    {l: the actual PE label (to update the input field),
                     p: the person details,
                     f: [{n: the flag name
                          i: the flag instructions
                          },
                         ...],

                     u: whether there are any actionable data
                     s: whether the action is permitted or not

                     d: {t: time stamp
                         h: payment details (raw data)
                         d: payment details (HTML)
                         }

                     e: form error (for label field)

                     a: error message
                     w: warning message
                     m: success message
                     }
        """

        T = current.T

        # Load JSON data from request body
        s = r.body
        s.seek(0)
        try:
            data = json.load(s)
        except (ValueError, TypeError):
            r.error(400, current.ERROR.BAD_REQUEST)


        # Initialize processing variables
        output = {}
        alert = None
        error = None
        warning = None
        message = None
        permitted = False
        flags = []

        # Identify the person
        pe_label = data.get("l")
        person = self.get_person(pe_label)

        if person is None:
            error = s3_str(T("No person found with this ID number"))

        else:
            # Get flag info
            flag_info = dvr_get_flag_instructions(person.id,
                                                  action = self.ACTION,
                                                  )
            permitted = flag_info["permitted"]

            check = data.get("c")
            if check:
                name = s3_fullname(person)
                dob = person.date_of_birth
                if dob:
                    dob = S3DateTime.date_represent(dob)
                    person_data = "%s (%s %s)" % (name, T("Date of Birth"), dob)
                else:
                    person_data = name

                output["p"] = s3_str(person_data)
                output["l"] = person.pe_label

                info = flag_info["info"]
                for flagname, instructions in info:
                    flags.append({"n": s3_str(T(flagname)),
                                  "i": s3_str(T(instructions)),
                                  })

                if permitted:
                    payments = self.get_payment_data(person.id)
                else:
                    payments = []
                date = S3DateTime.datetime_represent(current.request.utcnow,
                                                     utc = True,
                                                     )
                output["d"] = {"d": s3_str(self.payment_data_represent(payments)),
                               "t": s3_str(date),
                               "h": payments,
                               }
                if payments:
                    output["u"] = True
                else:
                    output["u"] = False
            else:
                if not permitted:
                    alert = T("Payment registration not permitted")
                else:
                    # Get payment data from JSON
                    payments = data.get("d")
                    if payments:

                        # @todo: read date from JSON data (utcnow as fallback)
                        date = r.utcnow
                        comments = data.get("c")

                        updated, failed = self.register_payments(
                                                    person.id,
                                                    payments,
                                                    date = date,
                                                    comments = comments,
                                                    )
                        message = T("%(number)s payment(s) registered") % \
                                  {"number": updated}
                        if failed:
                            warning = T("%(number)s payment(s) not found") % \
                                      {"number": failed}
                    else:
                        alert = T("No payments specified")

        # Add messages to output
        if alert:
            output["a"] = s3_str(alert)
        if error:
            output["e"] = s3_str(error)
        if message:
            output["m"] = s3_str(message)
        if warning:
            output["w"] = s3_str(warning)

        # Add flag info to output
        output["s"] = permitted
        output["f"] = flags

        current.response.headers["Content-Type"] = "application/json"
        return json.dumps(output)

    # -------------------------------------------------------------------------
    def get_form_data(self, person, formfields, data, hidden, permitted=False):
        """
            Helper function to extend the form

            @param person: the person (Row)
            @param formfields: list of form fields (Field)
            @param data: the form data (dict)
            @param hidden: hidden form fields (dict)
            @param permitted: whether the action is permitted

            @return: tuple (widget_id, submit_label)
        """

        T = current.T

        if person and permitted:
            payments = self.get_payment_data(person.id)
        else:
            payments = []

        date = S3DateTime.datetime_represent(current.request.utcnow,
                                             utc = True,
                                             )

        # Additional form fields for payments
        formfields.extend([Field("details",
                                label = T("Pending Payments"),
                                writable = False,
                                represent = self.payment_data_represent,
                                ),
                           Field("date",
                                 label = T("Payment Date"),
                                 writable = False,
                                 default = date,
                                 ),
                           Field("comments",
                                 label = T("Comments"),
                                 widget = s3_comments_widget,
                                 ),
                           ])

        # Additional data for payments
        data["date"] = s3_str(date)
        data["details"] = payments
        data["comments"] = ""

        # Add payments JSON to hidden form fields, update actionable info
        hidden["actions"] = json.dumps(payments)
        if not payments:
            hidden["actionable"] = "false"

        widget_id = "payment-form"
        submit = current.T("Register")

        return widget_id, submit

    # -------------------------------------------------------------------------
    def get_header(self, event_type=None):
        """
            Helper function to construct the event type header

            @param event_type: the event type (Row)
            @returns: dict of view items
        """

        # Simple title, no selector/toggle
        event_type_header = DIV(H4(SPAN(current.T("Allowance Payment"),
                                        _class = "event-type-name",
                                        ),
                                   ),
                                _class = "event-type-header",
                                )

        output = {"event_type": event_type_header,
                  "event_type_selector": "",
                  }

        return output

    # -------------------------------------------------------------------------
    # Class-specific functions
    # -------------------------------------------------------------------------
    def get_payment_data(self, person_id):
        """
            Helper function to extract currently pending allowance
            payments for the person_id.

            @param person_id: the person record ID

            @return: a list of dicts [{i: record_id,
                                       d: date,
                                       c: currency,
                                       a: amount,
                                       }, ...]
        """

        query = (FS("person_id") == person_id) & \
                (FS("status") == 1) & \
                (FS("date") <= current.request.utcnow.date())

        resource = current.s3db.resource("dvr_allowance",
                                         filter = query,
                                         )
        data = resource.select(["id",
                                "date",
                                "currency",
                                "amount",
                                ],
                                orderby = "dvr_allowance.date",
                                represent = True,
                               )

        payments = []
        append = payments.append
        for row in data.rows:
            payment_details = {"r": row["dvr_allowance.id"],
                               "d": row["dvr_allowance.date"],
                               "c": row["dvr_allowance.currency"],
                               "a": row["dvr_allowance.amount"],
                               }
            append(payment_details)

        return payments

    # -------------------------------------------------------------------------
    def register_payments(self, person_id, payments, date=None, comments=None):
        """
            Helper function to register payments

            @param person_id: the person record ID
            @param payments: the payments as sent from form
            @param date: the payment date (default utcnow)
            @param comments: comments for the payments

            @return: tuple (updated, failed), number of records
        """

        if isinstance(payments, basestring):
            try:
                payments = json.loads(payments)
            except (ValueError, TypeError):
                payments = []

        if not date:
            date = current.request.utcnow

        # Data to write
        data = {"status": 2,
                "paid_on": date,
                }
        if comments:
            data["comments"] = comments

        atable = current.s3db.dvr_allowance

        updated = 0
        failed = 0

        # Customise allowance resource
        r = S3Request("dvr", "allowance",
                      current.request,
                      args = [],
                      get_vars = {},
                      )
        r.customise_resource("dvr_allowance")
        onaccept = current.s3db.onaccept

        db = current.db
        accessible = current.auth.s3_accessible_query("update", atable)
        for payment in payments:
            record_id = payment.get("r")
            query = accessible & \
                    (atable.id == record_id) & \
                    (atable.person_id == person_id) & \
                    (atable.status != 2) & \
                    (atable.deleted != True)
            success = db(query).update(**data)
            if success:
                record = {"id": record_id, "person_id": person_id}
                record.update(data)
                onaccept(atable, record, method="update")
                updated += 1
            else:
                failed += 1

        return updated, failed

    # -------------------------------------------------------------------------
    def payment_data_represent(self, data):
        """
            Representation method for the payment details field

            @param data: the payment data (from get_payment_data)
        """

        if data:
            output = TABLE(_class="payment-details")
            for payment in data:
                details = TR(TD(payment["d"], _class="payment-date"),
                             TD(payment["c"], _class="payment-currency"),
                             TD(payment["a"], _class="payment-amount"),
                             )
                output.append(details)
        else:
            output = current.T("No pending payments")

        return output

# =============================================================================
def dvr_get_flag_instructions(person_id, action=None):
    """
        Get handling instructions if flags are set for a person

        @param person_id: the person ID
        @param action: the action for which instructions are needed:
                       - check-in|check-out|payment|id-check

        @returns: dict {"permitted": whether the action is permitted
                        "info": list of tuples (flagname, instructions)
                        }
    """

    s3db = current.s3db

    ftable = s3db.dvr_case_flag
    ltable = s3db.dvr_case_flag_case
    query = (ltable.person_id == person_id) & \
            (ltable.deleted != True) & \
            (ftable.id == ltable.flag_id) & \
            (ftable.deleted != True)

    if action == "check-in":
        query &= (ftable.advise_at_check_in == True) | \
                 (ftable.deny_check_in == True)
    elif action == "check-out":
        query &= (ftable.advise_at_check_out == True) | \
                 (ftable.deny_check_out == True)
    elif action == "payment":
        query &= (ftable.advise_at_id_check == True) | \
                 (ftable.allowance_suspended == True)
    else:
        query &= (ftable.advise_at_id_check == True)

    flags = current.db(query).select(ftable.name,
                                     ftable.deny_check_in,
                                     ftable.deny_check_out,
                                     ftable.allowance_suspended,
                                     ftable.advise_at_check_in,
                                     ftable.advise_at_check_out,
                                     ftable.advise_at_id_check,
                                     ftable.instructions,
                                     )

    info = []
    permitted = True
    for flag in flags:
        advise = False
        if action == "check-in":
            if flag.deny_check_in:
                permitted = False
            advise = flag.advise_at_check_in
        elif action == "check-out":
            if flag.deny_check_out:
                permitted = False
            advise = flag.advise_at_check_out
        elif action == "payment":
            if flag.allowance_suspended:
                permitted = False
            advise = flag.advise_at_id_check
        else:
            advise = flag.advise_at_id_check
        if advise:
            instructions = flag.instructions
            if not instructions.strip():
                instructions = current.T("No instructions for this flag")
            info.append((flag.name, instructions))

    return {"permitted": permitted,
            "info": info,
            }

# =============================================================================
def dvr_update_last_seen(person_id):
    """
        Helper function for automatic updates of dvr_case.last_seen_on

        @param person_id: the person ID
    """

    db = current.db
    s3db = current.s3db

    now = current.request.utcnow
    last_seen_on = None

    if not person_id:
        return

    # Get the last case event
    etable = s3db.dvr_case_event
    query = (etable.person_id == person_id) & \
            (etable.date != None) & \
            (etable.date <= now) & \
            (etable.deleted != True)
    event = db(query).select(etable.date,
                             orderby = ~etable.date,
                             limitby = (0, 1),
                             ).first()
    if event:
        last_seen_on = event.date

    # Check shelter registration history for newer entries
    htable = s3db.cr_shelter_registration_history
    query = (htable.person_id == person_id) & \
            (htable.status.belongs(2, 3)) & \
            (htable.date != None) & \
            (htable.deleted != True)
    if last_seen_on is not None:
        query &= htable.date > last_seen_on
    entry = db(query).select(htable.date,
                             orderby = ~htable.date,
                             limitby = (0, 1),
                             ).first()
    if entry:
        last_seen_on = entry.date

    settings = current.deployment_settings

    # Case appointments to update last_seen_on?
    if settings.get_dvr_appointments_update_last_seen_on():

        atable = s3db.dvr_case_appointment
        ttable = s3db.dvr_case_appointment_type
        left = ttable.on(ttable.id == atable.type_id)
        query = (atable.person_id == person_id) & \
                (atable.date != None) & \
                (ttable.presence_required == True) & \
                (atable.date <= now.date()) & \
                (atable.status == 4) & \
                (atable.deleted != True)
        if last_seen_on is not None:
            query &= atable.date > last_seen_on.date()
        appointment = db(query).select(atable.date,
                                       left = left,
                                       orderby = ~atable.date,
                                       limitby = (0, 1),
                                       ).first()
        if appointment:
            date = appointment.date
            try:
                date = datetime.datetime.combine(date, datetime.time(0, 0, 0))
            except TypeError:
                pass
            # Local time offset to UTC (NB: can be 0)
            delta = S3DateTime.get_offset_value(current.session.s3.utc_offset)
            # Default to 08:00 local time (...unless that would be future)
            date = min(now, date + datetime.timedelta(seconds = 28800 - delta))
            last_seen_on = date

    # Allowance payments to update last_seen_on?
    if settings.get_dvr_payments_update_last_seen_on():

        atable = s3db.dvr_allowance
        query = (atable.person_id == person_id) & \
                (atable.paid_on != None) & \
                (atable.status == 2) & \
                (atable.deleted != True)
        if last_seen_on is not None:
            query &= atable.paid_on > last_seen_on
        payment = db(query).select(atable.paid_on,
                                   orderby = ~atable.paid_on,
                                   limitby = (0, 1),
                                   ).first()
        if payment:
            last_seen_on = payment.paid_on

    # Update last_seen_on
    ctable = s3db.dvr_case
    query = (ctable.person_id == person_id) & \
            (ctable.archived != True) & \
            (ctable.deleted != True)
    db(query).update(last_seen_on = last_seen_on,
                     # Don't change author stamp for
                     # system-controlled record update:
                     modified_on = ctable.modified_on,
                     modified_by = ctable.modified_by,
                     )

# =============================================================================
def dvr_rheader(r, tabs=[]):
    """ DVR module resource headers """

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

        if tablename == "pr_person":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Activities"), "case_activity"),
                        (T("Beneficiaries"), "beneficiary_data"),
                        (T("Economy"), "economy"),
                        (T("Service Contacts"), "case_service_contact"),
                        (T("Identity"), "identity"),
                        ]

            case = resource.select(["dvr_case.reference",
                                    "dvr_case.case_type_id",
                                    ],
                                    represent = True,
                                    ).rows
            if case:
                case = case[0]
                case_number = lambda row: case["dvr_case.reference"]
                case_type = lambda row: case["dvr_case.case_type_id"]
                name = lambda row: s3_fullname(row)
            else:
                # Target record exists, but doesn't match filters
                return None

            rheader_fields = [[(T("Case Number"), case_number)],
                              [(T("Case Type"), case_type)],
                              [(T("Name"), name)],
                              ["date_of_birth"],
                              ]

        elif tablename == "dvr_case":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Activities"), "case_activity"),
                        ]

            rheader_fields = [["reference"],
                              ["status_id"],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table = resource.table,
                                                         record = record,
                                                         )

    return rheader

# END =========================================================================
