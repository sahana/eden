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
           "DVRCaseBeneficiaryModel",
           "DVRHousingInformationModel",
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
             "dvr_case_status_opts",
             "dvr_case_type",
             )

    def model(self):

        T = current.T
        db = current.db

        #UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        configure = self.configure

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
        # Case
        #
        #dvr_damage_opts = {
        #    1: T("Very High"),
        #    2: T("High"),
        #    3: T("Medium"),
        #    4: T("Low"),
        #}

        # Case status options
        # => tuple list to enforce widget order
        case_status_opts = (("PENDING", T("Pending")),
                            ("OPEN", T("Open")),
                            ("CLOSED", T("Closed")),
                            )

        # Case priority options
        # => tuple list to enforce widget order
        # => numeric key so it can be sorted by
        case_priority_opts = ((3, T("High")),
                              (2, T("Medium")),
                              (1, T("Low")),
                              )

        SITE = current.deployment_settings.get_org_site_label()
        permitted_facilities = current.auth.permitted_facilities(redirect_on_error=False)

        tablename = "dvr_case"
        define_table(tablename,
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
                     s3_date(label = T("Registration Date"),
                             default = "now",
                             empty = False,
                             ),
                     Field("status",
                           default = "OPEN",
                           label = T("Status"),
                           represent = S3Represent(options=dict(case_status_opts)),
                           requires = IS_IN_SET(case_status_opts,
                                                sort = False,
                                                zero = None,
                                                ),
                           ),
                     Field("priority", "integer",
                           default = 2,
                           label = T("Priority"),
                           represent = S3Represent(options=dict(case_priority_opts)),
                           requires = IS_IN_SET(case_priority_opts,
                                                sort = False,
                                                zero = None,
                                                ),
                           ),
                     self.org_organisation_id(),
                     self.super_link("site_id", "org_site",
                                     filterby = "site_id",
                                     filter_opts = permitted_facilities,
                                     label = SITE,
                                     readable = True,
                                     writable = True,
                                     represent = self.org_site_represent,
                                     updateable = True,
                                     ),
                     self.pr_person_id(
                        # @ToDo: Modify this to update location_id if the selected
                        #        person has a Home Address already
                        comment = None,
                        represent = self.pr_PersonRepresent(show_link=True),
                        requires = IS_ADD_PERSON_WIDGET2(),
                        widget = S3AddPersonWidget2(controller="pr"),
                        ondelete = "CASCADE",
                        ),
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
                            dvr_need =  {"link": "dvr_case_need",
                                         "joinby": "case_id",
                                         "key": "need_id",
                                         },
                            dvr_case_activity = "case_id",
                            dvr_housing = {"joinby": "case_id",
                                           "multiple": False,
                                           },
                            dvr_beneficiary_data = "case_id",
                            # Not valid for write:
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

        # CRUD form
        crud_form = S3SQLCustomForm("reference",
                                    "organisation_id",
                                    "date",
                                    "status",
                                    "person_id",
                                    # Not valid for write:
                                    #S3SQLInlineComponent("current_address",
                                    #                     label = T("Current Address"),
                                    #                     fields = [("", "location_id"),
                                    #                               ],
                                    #                     default = {"type": 1}, # Current Home Address
                                    #                     link = False,
                                    #                     multiple = False,
                                    #                     ),
                                    #S3SQLInlineComponent("permanent_address",
                                    #                     comment = T("If Displaced"),
                                    #                     label = T("Normal Address"),
                                    #                     fields = [("", "location_id"),
                                    #                               ],
                                    #                     default = {"type": 2}, # Permanent Home Address
                                    #                     link = False,
                                    #                     multiple = False,
                                    #                     ),
                                    S3SQLInlineLink("need",
                                                    field = "need_id",
                                                    ),
                                    "comments",
                                    )

        # Report options
        axes = ["organisation_id",
                "case_need.need_id",
                ]
        levels = current.gis.get_relevant_hierarchy_levels()
        for level in levels:
            axes.append("current_address.location_id$%s" % level)
        highest_lx = "current_address.location_id$%s" % levels[0]

        facts = [(T("Number of Cases"), "count(id)"),
                 ]

        report_options = {"rows": axes,
                          "cols": axes,
                          "fact": facts,
                          "defaults": {"rows": "case_need.need_id",
                                       "cols": highest_lx,
                                       "fact": facts[0],
                                       "totals": True,
                                       },
                          }

        # Table configuration
        configure(tablename,
                  crud_form = crud_form,
                  report_options = report_options,
                  onvalidation = self.case_onvalidation,
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
        # Pass names back to global scope (s3.*)
        #
        return {"dvr_case_id": case_id,
                "dvr_case_status_opts": case_status_opts,
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
                "dvr_case_status_opts": {},
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def case_onvalidation(form):
        """
            Ensure case numbers are unique within the organisation

            @param form: the FORM
        """

        db = current.db
        s3db = current.s3db

        # Read form data
        form_vars = form.vars
        record_id = form_vars.id if "id" in form_vars else None
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
                     # Beneficiary (component link):
                     # @todo: populate from case and hide in case perspective
                     self.pr_person_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     self.dvr_case_id(empty = False,
                                      label = T("Case Number"),
                                      ondelete = "CASCADE",
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

        list_fields = ["start_date",
                       "need_id",
                       "need_details",
                       "referral_details",
                       "followup",
                       "followup_date",
                       "completed",
                       ]

        # Table configuration
        configure(tablename,
                  list_fields = list_fields,
                  orderby = "dvr_case_activity.start_date desc",
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
class DVRHousingInformationModel(S3Model):
    """ Model for Housing Information """

    names = ("dvr_housing",
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
        # Housing Information
        #
        tablename = "dvr_housing"
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
            label_create = T("Create Housing Information"),
            title_display = T("Housing Information"),
            title_list = T("Housing Information"),
            title_update = T("Edit Housing Information"),
            label_list_button = T("List Housing Information"),
            label_delete_button = T("Delete Housing Information"),
            msg_record_created = T("Housing Information added"),
            msg_record_modified = T("Housing Information updated"),
            msg_record_deleted = T("Housing Information deleted"),
            msg_list_empty = T("No Housing Information currently registered"),
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
def dvr_rheader(r, tabs=[]):
    """ DVR module resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename = r.tablename
    record = r.record

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "pr_person":

            if not tabs:
                tabs = [(T("Basic Details"), ""),
                        (T("Activities"), "case_activity"),
                        (T("Beneficiaries"), "beneficiary_data"),
                        (T("Housing"), "housing"),
                        ]

            case = r.resource.select(["dvr_case.reference",
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

        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    return rheader

# END =========================================================================
