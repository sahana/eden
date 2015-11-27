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

__all__ = ("DVRCaseModel",
           "DVRNeedsModel",
           "DVRCaseActivityModel",
           "DVRCaseAppointmentModel",
           "DVRCaseBeneficiaryModel",
           "DVRCaseEconomyInformationModel",
           "dvr_case_default_status",
           "dvr_case_status_filter_opts",
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
             "dvr_case_type",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        settings = current.deployment_settings

        person_id = self.pr_person_id

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
                     self.org_organisation_id(readable=False,
                                              writable=False,
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
                           ),
                     Field("code", notnull=True, unique=True,
                           label = T("Status Code"),
                           length = 64,
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("name",
                           label = T("Status"),
                           # Removed to allow single column imports of Cases
                           #requires = IS_NOT_EMPTY(),
                           ),
                     Field("is_default", "boolean",
                           default = False,
                           label = T("Default Status"),
                           ),
                     s3_comments(),
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
                  # Automatic since unique=True
                  #deduplicate = S3Duplicate(primary = ("code",)),
                  onaccept = self.case_status_onaccept,
                  )

        # Reusable field
        represent = S3Represent(lookup=tablename)
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
        default_organisation = settings.get_org_default_organisation()
        default_site = settings.get_org_default_site()
        permitted_facilities = current.auth.permitted_facilities(redirect_on_error=False)

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
                     person_id(empty = False,
                               ondelete = "CASCADE",
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
                     s3_date("valid_until",
                             label = T("Valid until"),
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
                                     represent = self.org_site_represent,
                                     updateable = True,
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
                  onaccept = self.case_onaccept,
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
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return {"dvr_case_id": lambda **attr: dummy("case_id"),
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
    @staticmethod
    def case_onaccept(form):
        """
            Case onaccept routine:
            - auto-create active appointments

            @param form: the FORM
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

        # Get the person ID
        if "person_id" in form_vars:
            person_id = form_vars.person_id
        else:
            table = s3db.dvr_case
            query = (table.id == record_id)
            row = db(query).select(table.person_id,
                                   limitby = (0, 1)).first()
            if not row:
                return
            person_id = row.person_id

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

        return {"dvr_need_id": lambda **attr: dummy("need_id"),
                }

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
        define_table = self.define_table
        configure = self.configure

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
                     self.org_organisation_id(label=T("Referral Agency"),
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
                                          options = lambda: get_s3_filter_opts("dvr_need"),
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
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        configure = self.configure

        # ---------------------------------------------------------------------
        # Case Appointment Type
        #
        tablename = "dvr_case_appointment_type"
        define_table(tablename,
                     Field("name", length=64, notnull=True, unique=True,
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("active", "boolean",
                           default = True,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Appointment Type"),
            title_display = T("Appointment Type Details"),
            title_list = T("Appointment Types"),
            title_update = T("Edit Appointment Types"),
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
                           represent = S3Represent(options=appointment_status_opts,
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
        define_table = self.define_table
        configure = self.configure

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

        return {"dvr_beneficiary_type_id": lambda **attr: dummy("beneficiary_type_id"),
                }


# =============================================================================
class DVRCaseEconomyInformationModel(S3Model):
    """ Model for Household Economy Information """

    names = ("dvr_economy",
             "dvr_housing_type",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        configure = self.configure

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
            msg_list_empty = T("No Housing Types currently registered")
            )

        # Represent for reference
        housing_type_represent = S3Represent(lookup = "dvr_housing_type",
                                             translate = True,
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
                     s3_currency(),
                     s3_comments(),
                     *s3_meta_fields())

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

        list_fields = ["housing_type_id",
                       "monthly_costs",
                       "comments",
                       ]

        # Table configuration
        configure(tablename,
                  list_fields = list_fields,
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
def dvr_case_status_filter_opts():
    """
        Get filter options for case status, ordered by workflow position

        @return: OrderedDict of options

        @note: set sort=False for filter widget to retain this order
    """

    table = current.s3db.dvr_case_status
    query = (table.deleted != True)
    rows = current.db(query).select(table.id,
                                    table.name,
                                    orderby = "workflow_position",
                                    )

    if not rows:
        return {}

    T = current.T
    return OrderedDict((row.id, T(row.name)) for row in rows)

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
                                    represent=True,
                                    ).rows[0]
            case_number = lambda row: case["dvr_case.reference"]
            case_type = lambda row: case["dvr_case.case_type_id"]
            name = lambda row: s3_fullname(row)

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
                                                         table=resource.table,
                                                         record=record,
                                                         )

    return rheader

# END =========================================================================
