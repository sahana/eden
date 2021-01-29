# -*- coding: utf-8 -*-

"""
    Application Template for Rhineland-Palatinate (RLP) Crisis Management
    - used to manage Personnel Tests for COVID-19 response

    @license MIT
"""

from collections import OrderedDict

from gluon import current, URL, A, DIV, IS_EMPTY_OR, IS_IN_SET, TAG
from gluon.storage import Storage

from s3 import FS, IS_ONE_OF, S3Represent, s3_str
from s3dal import original_tablename

from .rlpgeonames import rlp_GeoNames

LSJV = "Landesamt für Soziales, Jugend und Versorgung"
SCHOOLS = "Schulen"
TESTSTATIONS = "COVID-19 Teststellen"

ALLOWED_FORMATS = ("html", "iframe", "popup", "aadata", "json")

# =============================================================================
def config(settings):

    T = current.T

    purpose = {"event": "COVID-19"}
    settings.base.system_name = T("%(event)s Personnel Testing") % purpose
    settings.base.system_name_short = T("%(event)s Personnel Testing") % purpose

    # PrePopulate data
    settings.base.prepopulate += ("RLPPTM",)
    settings.base.prepopulate_demo.append("RLPPTM/Demo")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "RLP"
    settings.base.theme_layouts = "RLPPTM"
    # Custom Logo
    #settings.ui.menu_logo = "/%s/static/themes/<templatename>/img/logo.png" % current.request.application

    # Authentication settings
    # No self-registration
    settings.security.self_registration = False
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do not send standard welcome emails (using custom function)
    settings.auth.registration_welcome_email = False
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True
    # Required for access to default realm permissions
    settings.auth.registration_link_user_to = ["staff"]
    settings.auth.registration_link_user_to_default = ["staff"]
    # Disable password-retrieval feature
    settings.auth.password_retrieval = True

    settings.auth.realm_entity_types = ("org_group", "org_organisation")
    settings.auth.privileged_roles = {"PROGRAM_MANAGER": "ORG_GROUP_ADMIN",
                                      "VOUCHER_ISSUER": "VOUCHER_ISSUER",
                                      "VOUCHER_PROVIDER": "VOUCHER_PROVIDER",
                                      "DISEASE_TEST_READER": "ORG_GROUP_ADMIN",
                                      }

    settings.auth.password_min_length = 8
    settings.auth.consent_tracking = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    settings.gis.countries = ("DE",)
    #gis_levels = ("L1", "L2", "L3")
    # Uncomment to display the Map Legend as a floating DIV, so that it is visible on Summary Map
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # Use custom geocoder
    settings.gis.geocode_service = rlp_GeoNames

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar, GIS Locations, etc)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
       ("de", "German"),
       ("en", "English"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    settings.L10n.default_language = "de"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    settings.L10n.timezone = "Europe/Berlin"
    # Default date/time formats
    settings.L10n.date_format = "%d.%m.%Y"
    settings.L10n.time_format = "%H:%M"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
    # Uncomment this to Translate Layer Names
    #settings.L10n.translate_gis_layer = True
    # Uncomment this to Translate Location Names
    #settings.L10n.translate_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    #settings.L10n.translate_org_organisation = True
    # Finance settings
    settings.fin.currencies = {
        "EUR" : "Euros",
    #    "GBP" : "Great British Pounds",
    #    "USD" : "United States Dollars",
    }
    settings.fin.currency_default = "EUR"

    # Do not require international phone number format
    settings.msg.require_international_phone_numbers = False

    # Security Policy
    # http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table ACLs and Entity Realm
    # 7: Apply Controller, Function, Table ACLs and Entity Realm + Hierarchy
    # 8: Apply Controller, Function, Table ACLs, Entity Realm + Hierarchy and Delegations
    #
    settings.security.policy = 7

    # -------------------------------------------------------------------------
    settings.pr.hide_third_gender = False
    settings.pr.separate_name_fields = 2
    settings.pr.name_format= "%(last_name)s, %(first_name)s"

    settings.pr.availability_json_rules = True

    # -------------------------------------------------------------------------
    settings.hrm.record_tab = False
    settings.hrm.staff_experience = False
    settings.hrm.teams = False
    settings.hrm.use_address = False
    settings.hrm.use_id = False
    settings.hrm.use_skills = False
    settings.hrm.use_certificates = False
    settings.hrm.use_credentials = False
    settings.hrm.use_description = False
    settings.hrm.use_trainings = False

    # -------------------------------------------------------------------------
    settings.org.projects_tab = False
    settings.org.default_organisation = LSJV

    # -------------------------------------------------------------------------
    settings.fin.voucher_personalize = "dob"

    # -------------------------------------------------------------------------
    # Realm Rules
    #
    def rlpptm_realm_entity(table, row):
        """
            Assign a Realm Entity to records
        """

        db = current.db
        s3db = current.s3db

        realm_entity = 0 # = use default
        tablename = original_tablename(table)

        #if tablename in ("org_group",
        #                 "org_organisation",
        #                 "org_facility",
        #                 "org_office",
        #                 ):
        #    # These entities own themselves by default, and form
        #    # a OU hierarchy (default ok)
        #    realm_entity = 0
        #
        #elif tablename == "pr_person":
        #
        #    # Persons are owned by the org employing them (default ok)
        #    realm_entity = 0
        #
        if tablename == "disease_case_diagnostics":

            # Test results are owned by the user organisation
            user = current.auth.user
            organisation_id = user.organisation_id if user else None
            if not organisation_id:
                # Fall back to default organisation
                organisation_id = settings.get_org_default_organisation()
            if organisation_id:
                realm_entity = s3db.pr_get_pe_id("org_organisation",
                                                 organisation_id,
                                                 )

        #elif tablename == "fin_voucher_program":
        #
        #    # Voucher programs are owned by the organisation managing
        #    # them (default ok)
        #    realm_entity = 0
        #
        #elif tablename == "fin_voucher":
        #
        #    # Vouchers are owned by the issuer PE (default ok)
        #    realm_entity = 0
        #
        #elif tablename == "fin_voucher_debit":
        #
        #    # Debits are owned by the provider PE (default ok)
        #    realm_entity = 0
        #
        elif tablename == "fin_voucher_transaction":

            # Vouchers inherit the realm-entity from the program
            table = s3db.table(tablename)
            ptable = s3db.fin_voucher_program
            query = (table._id == row.id) & \
                    (ptable.id == table.program_id)
            program = db(query).select(ptable.realm_entity,
                                       limitby = (0, 1),
                                       ).first()
            if program:
                realm_entity = program.realm_entity


        return realm_entity

    settings.auth.realm_entity = rlpptm_realm_entity

    # -------------------------------------------------------------------------
    def consent_check():
        """
            Check pending consent at login
        """

        auth = current.auth

        person_id = auth.s3_logged_in_person()
        if not person_id:
            return None

        has_role = auth.s3_has_role
        if has_role("ADMIN"):
            required = None
        elif has_role("VOUCHER_ISSUER"):
            required = ["STORE", "RULES_ISS"]
        else:
            required = None

        if required:
            consent = current.s3db.auth_Consent(required)
            pending = consent.pending_responses(person_id)
        else:
            pending = None

        return pending

    settings.auth.consent_check = consent_check

    # -------------------------------------------------------------------------
    def customise_auth_user_resource(r, tablename):
        """
            Configure custom approvals function

        """

        auth = current.auth

        def approve_user(r, **args):

            from gluon import redirect

            db = current.db
            user = db(db.auth_user.id == r.id).select(limitby = (0, 1)
                                                      ).first()
            org_group_id = user.org_group_id
            if org_group_id:
                # Check if this is a COVID-19 Test Station
                ogtable = current.s3db.org_group
                org_group = db(ogtable.id == org_group_id).select(ogtable.name,
                                                                  limitby = (0, 1)
                                                                  ).first()
                if org_group and org_group.name == TESTSTATIONS:
                    # Custom Approval process
                    redirect(URL(c= "default", f="index", args=["approve", r.id]))

            # Default Approval
            auth.s3_approve_user(user)
            current.session.confirmation = T("User Account has been Approved")
            redirect(URL(args=[r.id, "roles"]))

        current.s3db.configure("auth_user",
                               approve_user = approve_user,
                               )

    settings.customise_auth_user_resource = customise_auth_user_resource

    # -------------------------------------------------------------------------
    def customise_cms_post_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3SQLInlineComponent

        crud_form = S3SQLCustomForm("name",
                                    "body",
                                    "date",
                                    S3SQLInlineComponent("document",
                                                         name = "file",
                                                         label = T("Attachments"),
                                                         fields = ["file", "comments"],
                                                         filterby = {"field": "file",
                                                                     "options": "",
                                                                     "invert": True,
                                                                     },
                                                         ),
                                    "comments",
                                    )

        current.s3db.configure("cms_post",
                               crud_form = crud_form,
                               list_fields = ["post_module.module",
                                              "post_module.resource",
                                              "name",
                                              "date",
                                              "comments",
                                              ],
                               )

    settings.customise_cms_post_resource = customise_cms_post_resource

    # -----------------------------------------------------------------------------
    def customise_cms_post_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            table = r.table
            context = r.get_vars.get("resource")
            if context == "Privacy":
                page = URL(c="default", f="index", args=["privacy"])
                r.resource.configure(create_next = page,
                                     update_next = page,
                                     )
                table.name.default = "Privacy Notice"
            elif context == "Legal":
                page = URL(c="default", f="index", args=["legal"])
                r.resource.configure(create_next = page,
                                     update_next = page,
                                     )
                table.name.default = "Legal Notice"
            return result
        s3.prep = prep

        return attr

    settings.customise_cms_post_controller = customise_cms_post_controller

    # -------------------------------------------------------------------------
    def customise_disease_case_diagnostics_resource(r, tablename):

        db = current.db
        s3db = current.s3db

        table = s3db.disease_case_diagnostics

        if r.interactive and r.method != "report":
            # Enable project link and make it mandatory
            field = table.project_id
            field.readable = field.writable = True
            field.comment = None
            requires = field.requires
            if isinstance(requires, (list, tuple)):
                requires = requires[0]
            if isinstance(requires, IS_EMPTY_OR):
                field.requires = requires.other

            # If there is only one project, default the selector + make r/o
            ptable = s3db.project_project
            rows = db(ptable.deleted == False).select(ptable.id,
                                                      cache = s3db.cache,
                                                      limitby = (0, 2),
                                                      )
            if len(rows) == 1:
                field.default = rows[0].id
                field.writable = False

            # Enable disease link and make it mandatory
            field = table.disease_id
            field.readable = field.writable = True
            field.comment = None
            requires = field.requires
            if isinstance(requires, (list, tuple)):
                requires = requires[0]
            if isinstance(requires, IS_EMPTY_OR):
                field.requires = requires.other

            # If there is only one disease, default the selector + make r/o
            dtable = s3db.disease_disease
            rows = db(dtable.deleted == False).select(dtable.id,
                                                      cache = s3db.cache,
                                                      limitby = (0, 2),
                                                      )
            if len(rows) == 1:
                field.default = rows[0].id
                field.writable = False

            # Default result date
            field = table.result_date
            field.default = current.request.utcnow.date()

        # Formal test types
        # TODO move to lookup table?
        type_options = (("LFD", T("LFD Antigen Test")),
                        ("PCR", T("PCR Test")),
                        ("SER", T("Serum Antibody Test")),
                        ("OTH", T("Other")),
                        )
        field = table.test_type
        field.default = "LFD"
        field.writable = False # fixed for now
        field.requires = IS_IN_SET(type_options,
                                   zero = "",
                                   sort = False,
                                   )
        field.represent = S3Represent(options=dict(type_options))

        # Formal results
        result_options = (("NEG", T("Negative")),
                          ("POS", T("Positive")),
                          ("INC", T("Inconclusive")),
                          )
        field = table.result
        field.requires = IS_IN_SET(result_options,
                                   zero = "",
                                   sort = False,
                                   )
        field.represent = S3Represent(options=dict(result_options))

        # Custom list_fields
        list_fields = ["project_id",
                       "disease_id",
                       "test_type",
                       "result_date",
                       "result",
                       ]

        # Custom form
        from s3 import S3SQLCustomForm
        crud_form = S3SQLCustomForm("project_id",
                                    "disease_id",
                                    "test_type",
                                    "result_date",
                                    "result",
                                    )

        # Filters
        from s3 import S3DateFilter, S3OptionsFilter
        filter_widgets = [S3DateFilter("result_date",
                                       label = T("Date"),
                                       ),
                          S3OptionsFilter("disease_id", hidden=True),
                          S3OptionsFilter("project_id", hidden=True),
                          S3OptionsFilter("test_type",
                                          options = OrderedDict(type_options),
                                          hidden = True,
                                          ),
                          S3OptionsFilter("result",
                                          options = OrderedDict(result_options),
                                          hidden = True,
                                          ),
                          ]

        # Report options
        facts = ((T("Number of Tests"), "count(id)"),
                 )
        axes = ["result",
                "test_type",
                "disease_id",
                "project_id",
                ]
        report_options = {
            "rows": axes,
            "cols": axes,
            "fact": facts,
            "defaults": {"rows": axes[1],
                         "cols": axes[0],
                         "fact": facts[0],
                         "totals": True,
                         },
            }

        s3db.configure("disease_case_diagnostics",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       report_options = report_options,
                       )

        crud_strings = current.response.s3.crud_strings
        crud_strings["disease_case_diagnostics"] = Storage(
            label_create = T("Register Test Result"),
            title_display = T("Test Result"),
            title_list = T("Test Results"),
            title_update = T("Edit Test Result"),
            title_upload = T("Import Test Results"),
            label_list_button = T("List Test Results"),
            label_delete_button = T("Delete Test Result"),
            msg_record_created = T("Test Result added"),
            msg_record_modified = T("Test Result updated"),
            msg_record_deleted = T("Test Result deleted"),
            msg_list_empty = T("No Test Results currently registered"))

    settings.customise_disease_case_diagnostics_resource = customise_disease_case_diagnostics_resource

    # -------------------------------------------------------------------------
    def customise_fin_voucher_resource(r, tablename):

        s3db = current.s3db

        table = s3db.fin_voucher

        # Customise fields
        field = table.comments
        field.label = T("Memoranda")
        field.comment = DIV(_class="tooltip",
                            _title="%s|%s" % (T("Memoranda"),
                                              T("Notes of the Issuer"),
                                              ),
                            )

        field = table.balance
        field.label = T("Status")
        field.represent = lambda v: T("Issued##fin") if v > 0 else T("Redeemed##fin")

        # Custom list fields
        list_fields = ["program_id",
                       "signature",
                       #"bearer_dob",
                       "balance",
                       "date",
                       "valid_until",
                       #"comments",
                       ]
        if current.auth.s3_has_role("VOUCHER_ISSUER"):
            if settings.get_fin_voucher_personalize() == "dob":
                list_fields.insert(2, "bearer_dob")
            list_fields.append("comments")

        s3db.configure("fin_voucher",
                       list_fields = list_fields,
                       )

    settings.customise_fin_voucher_resource = customise_fin_voucher_resource

    # -------------------------------------------------------------------------
    def customise_fin_voucher_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            # Restrict data formats
            settings.ui.export_formats = None
            representation = r.representation
            if representation not in ALLOWED_FORMATS and \
               not(r.record and representation == "card"):
                r.error(403, current.ERROR.NOT_PERMITTED)

            db = current.db
            s3db = current.s3db

            # Check which programs and organisations the user can issue vouchers for
            program_ids, org_ids, pe_ids = s3db.fin_voucher_permitted_programs(mode="issuer")

            resource = r.resource
            table = resource.table

            if not program_ids or not org_ids:
                # User is not permitted to issue vouchers for any programs/issuers
                resource.configure(insertable = False)

            else:
                # Limit the program selector to permitted+active programs
                field = table.program_id
                ptable = s3db.fin_voucher_program
                dbset = db(ptable.id.belongs(program_ids))
                field.requires = IS_ONE_OF(dbset, "fin_voucher_program.id",
                                           field.represent,
                                           sort = True,
                                           )
                # Hide the program selector if only one program can be chosen
                rows = dbset.select(ptable.id, limitby=(0, 2))
                if len(rows) == 1:
                    field.default = rows.first().id
                    field.writable = False

                # Limit the issuer selector to permitted entities
                etable = s3db.pr_pentity
                field = table.pe_id
                dbset = db(etable.pe_id.belongs(pe_ids))
                field.requires = IS_ONE_OF(dbset, "pr_pentity.pe_id",
                                            field.represent,
                                            )
                # Hide the issuer selector if only one entity can be chosen
                rows = dbset.select(etable.pe_id, limitby=(0, 2))
                if len(rows) == 1:
                    field.default = rows.first().pe_id
                    field.readable = field.writable = False

            if r.interactive:

                # Hide valid_until from create-form (will be set onaccept)
                field = table.valid_until
                field.readable = bool(r.record)
                field.writable = False

                # Filter Widgets
                from s3 import S3DateFilter, S3TextFilter
                filter_widgets = [
                    S3TextFilter(["signature",
                                  "comments",
                                  "program_id$name",
                                  ],
                                 label = T("Search"),
                                 ),
                    S3DateFilter("date",
                                 ),
                    ]
                resource.configure(filter_widgets = filter_widgets,
                                   )

            elif r.representation == "card":
                # Configure ID card layout
                from .vouchers import VoucherCardLayout
                resource.configure(pdf_card_layout = VoucherCardLayout,
                                    pdf_card_suffix = lambda record: \
                                        s3_str(record.signature) \
                                        if record and record.signature else None,
                                    )
            return result
        s3.prep = prep

        standard_postp = s3.postp
        def custom_postp(r, output):

            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if not r.component and isinstance(output, dict):
                if r.record and r.method in (None, "update", "read"):

                    # Custom CRUD buttons
                    if "buttons" not in output:
                        buttons = output["buttons"] = {}
                    else:
                        buttons = output["buttons"]

                    # PDF-button
                    pdf_download = A(T("Download PDF"),
                                     _href = "/%s/fin/voucher/%s.card" % (r.application, r.record.id),
                                     _class="action-btn",
                                     )

                    # Render in place of the delete-button
                    buttons["delete_btn"] = TAG[""](pdf_download,
                                                    )
            return output
        s3.postp = custom_postp

        # Custom rheader
        from .rheaders import rlpptm_fin_rheader
        attr["rheader"] = rlpptm_fin_rheader

        return attr

    settings.customise_fin_voucher_controller = customise_fin_voucher_controller

    # -------------------------------------------------------------------------
    def customise_fin_voucher_debit_resource(r, tablename):

        s3db = current.s3db

        table = s3db.fin_voucher_debit

        # Customise fields
        field = table.comments
        field.label = T("Memoranda")
        field.comment = DIV(_class="tooltip",
                            _title="%s|%s" % (T("Memoranda"),
                                              T("Notes of the Provider"),
                                              ),
                            )

        field = table.balance
        field.label = T("Status")
        field.represent = lambda v: T("Redeemed##fin") if v > 0 else T("Compensated##fin")

        # Custom list_fields
        list_fields = [(T("Date"), "date"),
                        "program_id",
                        "voucher_id$signature",
                        "balance",
                        ]
        if current.auth.s3_has_role("PROGRAM_MANAGER"):
            list_fields[3:3] = ["voucher_id$pe_id",
                                "pe_id",
                                ]
        if current.auth.s3_has_role("VOUCHER_PROVIDER"):
            list_fields.append("comments")

        s3db.configure("fin_voucher_debit",
                       list_fields = list_fields,
                       )

        # Filters
        if r.interactive:
            from s3 import S3DateFilter, S3TextFilter
            filter_widgets = [S3TextFilter(["program_id$name",
                                            "signature",
                                            ],
                                        label = T("Search"),
                                        ),
                            S3DateFilter("date",
                                        label = T("Date"),
                                        ),
                            ]
            s3db.configure("fin_voucher_debit",
                           filter_widgets = filter_widgets,
                           )

        # Report options
        if r.method == "report":
            facts = ((T("Number of Accepted Vouchers"), "count(id)"),
                    )
            axes = ["program_id",
                    "balance",
                    ]
            if current.auth.s3_has_role("PROGRAM_MANAGER"):
                axes.insert(0, "pe_id")
            report_options = {
                "rows": axes,
                "cols": axes,
                "fact": facts,
                "defaults": {"rows": axes[0],
                            "cols": None,
                            "fact": facts[0],
                            "totals": True,
                            },
                }
            s3db.configure("fin_voucher_debit",
                           report_options = report_options,
                           )

    settings.customise_fin_voucher_debit_resource = customise_fin_voucher_debit_resource

    # -------------------------------------------------------------------------
    def customise_fin_voucher_debit_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            db = current.db
            s3db = current.s3db

            # Check which programs and organisations the user can accept vouchers for
            program_ids, org_ids, pe_ids = s3db.fin_voucher_permitted_programs(mode="provider")

            resource = r.resource
            table = resource.table

            if not program_ids or not org_ids:
                # User is not permitted to accept vouchers for any programs/providers
                resource.configure(insertable = False)

            else:
                # Limit the program selector to permitted programs
                field = table.program_id
                ptable = s3db.fin_voucher_program
                dbset = db(ptable.id.belongs(program_ids))
                field.requires = IS_ONE_OF(dbset, "fin_voucher_program.id",
                                           field.represent,
                                           sort = True,
                                           )
                # Hide the program selector if only one program can be chosen
                rows = dbset.select(ptable.id, limitby=(0, 2))
                if len(rows) == 1:
                    field.default = rows.first().id
                    field.writable = False

                # Limit the provider selector to permitted entities
                etable = s3db.pr_pentity
                field = table.pe_id
                dbset = db(etable.pe_id.belongs(pe_ids))
                field.requires = IS_ONE_OF(dbset, "pr_pentity.pe_id",
                                           field.represent,
                                           )
                # Hide the provider selector if only one entity can be chosen
                rows = dbset.select(etable.pe_id, limitby=(0, 2))
                if len(rows) == 1:
                    field.default = rows.first().pe_id
                    field.readable = field.writable = False

            return result
        s3.prep = prep

        # Custom rheader
        from .rheaders import rlpptm_fin_rheader
        attr["rheader"] = rlpptm_fin_rheader

        return attr

    settings.customise_fin_voucher_debit_controller = customise_fin_voucher_debit_controller

    # -------------------------------------------------------------------------
    def customise_org_facility_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3SQLInlineLink, \
                       S3LocationSelector, S3LocationFilter, S3TextFilter

        s3db = current.s3db

        s3db.org_facility.location_id.widget = S3LocationSelector(levels = ("L1", "L2", "L3", "L4"),
                                                                  required_levels = ("L1", "L2", "L3"),
                                                                  show_address = True,
                                                                  show_postcode = True,
                                                                  show_map = True,
                                                                  )

        # Geocoder
        current.response.s3.scripts.append("/%s/static/themes/RLP/js/geocoderPlugin.js" % r.application)

        text_fields = ["name",
                       #"code",
                       #"comments",
                       #"organisation_id$name",
                       #"organisation_id$acronym",
                       #"location_id$L1",
                       "location_id$L2",
                       "location_id$L3",
                       "location_id$L4",
                       ]

        filter_widgets = [
            S3TextFilter(text_fields,
                         label = T("Search"),
                         #_class = "filter-search",
                         ),
            S3LocationFilter("location_id",
                             #label = T("Location"),
                             levels = ("L1", "L2", "L3", "L4"),
                             ),
            ]

        crud_fields = ["name",
                       S3SQLInlineLink(
                              "facility_type",
                              label = T("Facility Type"),
                              field = "facility_type_id",
                              widget = "groupedopts",
                              cols = 3,
                        ),
                       #"organisation_id",
                       "location_id",
                       (T("Telephone"), "phone1"),
                       (T("Opening Hours"), "opening_times"),
                       #"obsolete",
                       "comments",
                       ]

        list_fields = ["name",
                       #"site_facility_type.facility_type_id",
                       (T("Telephone"), "phone1"),
                       (T("Opening Hours"), "opening_times"),
                       "location_id$addr_street",
                       "location_id$addr_postcode",
                       "location_id$L4",
                       "location_id$L3",
                       "location_id$L2",
                       #"location_id$L1",
                       #"organisation_id",
                       #"obsolete",
                       #"comments",
                       ]

        s3db.configure(tablename,
                       crud_form = S3SQLCustomForm(*crud_fields),
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_org_facility_resource = customise_org_facility_resource

    # -------------------------------------------------------------------------
    def customise_org_facility_controller(**attr):

        s3 = current.response.s3

        # Load model for default CRUD strings
        current.s3db.table("org_facility")

        s3.crud_strings.org_facility.title_list = T("Find Test Station")

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            record = r.record
            if record:
                s3db = current.s3db
                auth = current.auth
                if not auth.s3_has_role("ORG_GROUP_ADMIN") and \
                   not auth.s3_has_role("ORG_ADMIN", for_pe=record.pe_id):
                    s3.hide_last_update = True

                    table = r.resource.table

                    field = table.obsolete
                    field.readable = field.writable = False

                    field = table.organisation_id
                    field.represent = s3db.org_OrganisationRepresent(show_link=False)

            settings.ui.summary = ({"name": "table",
                                    "label": "Table",
                                    "widgets": [{"method": "datatable"}]
                                    },
                                   {"name": "map",
                                    "label": "Map",
                                    "widgets": [{"method": "map", "ajax_init": True}],
                                    },
                                   )

            return result
        s3.prep = prep

        # Custom rheader
        #from .rheaders import rlpptm_org_rheader
        #attr = dict(attr)
        #attr["rheader"] = rlpptm_org_rheader
        attr["rheader"] = None

        # No Side Menu
        current.menu.options = None

        return attr

    settings.customise_org_facility_controller = customise_org_facility_controller

    # -------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            auth = current.auth
            s3db = current.s3db

            is_org_group_admin = auth.s3_has_role("ORG_GROUP_ADMIN")

            # Add invite-method for ORG_GROUP_ADMIN role
            from .helpers import rlpptm_InviteUserOrg
            s3db.set_method("org", "organisation",
                            method = "invite",
                            action = rlpptm_InviteUserOrg,
                            )

            resource = r.resource
            get_vars = r.get_vars
            mine = get_vars.get("mine")
            if mine == "1":
                # Filter to managed orgs
                managed_orgs = auth.get_managed_orgs()
                if managed_orgs is True:
                    query = None
                elif managed_orgs is None:
                    query = FS("id") == None
                else:
                    query = FS("pe_id").belongs(managed_orgs)
                if query:
                    resource.add_filter(query)
            else:
                # Filter by org_group_membership
                org_group_id = get_vars.get("g")
                if org_group_id:
                    if isinstance(org_group_id, list):
                        query = FS("group.id").belongs(org_group_id)
                    else:
                        query = FS("group.id") == org_group_id
                    resource.add_filter(query)

            if not r.component:
                if r.interactive:
                    from s3 import S3SQLCustomForm, \
                                   S3SQLInlineComponent, \
                                   S3SQLInlineLink

                    # Custom form
                    crud_fields = ["name",
                                   "acronym",
                                   # TODO Activate after correct type prepop
                                   #S3SQLInlineLink(
                                   #     "organisation_type",
                                   #     field = "organisation_type_id",
                                   #     search = False,
                                   #     label = T("Type"),
                                   #     multiple = settings.get_org_organisation_types_multiple(),
                                   #     widget = "multiselect",
                                   #     ),
                                   #"country",
                                   S3SQLInlineComponent(
                                        "contact",
                                        fields = [("", "value")],
                                        filterby = {"field": "contact_method",
                                                    "options": "EMAIL",
                                                    },
                                        label = T("Email"),
                                        multiple = False,
                                        name = "email",
                                        ),
                                   "phone",
                                   "website",
                                   #"year",
                                   "logo",
                                   "comments",
                                   ]
                    if is_org_group_admin:
                        crud_fields.insert(0, S3SQLInlineLink(
                                                    "group",
                                                    field = "group_id",
                                                    label = T("Organization Group"),
                                                    multiple = False,
                                                    ))

                    # Filters
                    from s3 import S3OptionsFilter, S3TextFilter, s3_get_filter_opts
                    text_fields = ["name", "acronym", "website", "phone"]
                    if is_org_group_admin:
                        text_fields.append("email.value")
                    filter_widgets = [S3TextFilter(text_fields,
                                                   label = T("Search"),
                                                   ),
                                      ]
                    if is_org_group_admin:
                        filter_widgets.append(S3OptionsFilter("group__link.group_id",
                                                              label = T("Group"),
                                                              options = lambda: s3_get_filter_opts("org_group"),
                                                              ))

                    resource.configure(crud_form = S3SQLCustomForm(*crud_fields),
                                       filter_widgets = filter_widgets,
                                       )

                # Custom list fields
                list_fields = [#"group__link.group_id",
                               "name",
                               "acronym",
                               # TODO Activate after correct type prepop
                               #"organisation_type__link.organisation_type_id",
                               "website",
                               "phone",
                               #"email.value"
                               ]
                if is_org_group_admin:
                    list_fields.insert(0, (T("Organization Group"), "group__link.group_id"))
                    list_fields.append((T("Email"), "email.value"))
                r.resource.configure(list_fields = list_fields,
                                     )

            return result
        s3.prep = prep

        # Custom rheader
        from .rheaders import rlpptm_org_rheader
        attr = dict(attr)
        attr["rheader"] = rlpptm_org_rheader

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            from gluon import IS_NOT_EMPTY
            from s3 import S3SQLCustomForm, \
                           StringTemplateParser

            # Determine order of name fields
            NAMES = ("first_name", "middle_name", "last_name")
            keys = StringTemplateParser.keys(settings.get_pr_name_format())
            name_fields = [fn for fn in keys if fn in NAMES]

            if r.controller == "default":
                # Personal profile (default/person)
                if not r.component:

                    # Last name is required
                    table = r.resource.table
                    table.last_name.requires = IS_NOT_EMPTY()

                    # Custom Form
                    crud_fields = name_fields
                    r.resource.configure(crud_form = S3SQLCustomForm(*crud_fields),
                                         deletable = False,
                                         )
            return result
        s3.prep = prep

        # Custom rheader
        if current.request.controller == "default":
            from .rheaders import rlpptm_profile_rheader
            attr["rheader"] = rlpptm_profile_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # Modules menu is defined in modules/eden/menu.py
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
            name_nice = T("Home"),
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None, # This item is not shown in the menu
        )),
        ("admin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        ("appadmin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            module_type = None, # No Menu
        )),
        ("errors", Storage(
            name_nice = T("Ticket Viewer"),
            #description = "Needed for Breadcrumbs",
            restricted = False,
            module_type = None, # No Menu
        )),
        #("sync", Storage(
        #    name_nice = T("Synchronization"),
        #    #description = "Synchronization",
        #    restricted = True,
        #    access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        #    module_type = None  # This item is handled separately for the menu
        #)),
        ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 6,
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10,
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 1,
        )),
        # HRM is required for access to default realm permissions
        ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 2,
        )),
        ("cms", Storage(
            name_nice = T("Content Management"),
            #description = "Content Management System",
            restricted = True,
            module_type = 10,
        )),
        ("doc", Storage(
            name_nice = T("Documents"),
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
            module_type = 10,
        )),
        ("msg", Storage(
            name_nice = T("Messaging"),
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            module_type = None,
        )),
        ("project", Storage(
            name_nice = T("Projects"),
            #description = "Tracking of Projects, Activities and Tasks",
            restricted = True,
            module_type = None,
        )),
        ("fin", Storage(
            name_nice = T("Finance"),
            #description = "Finance Management / Accounting",
            restricted = True,
            module_type = None,
        )),
        ("disease", Storage(
            name_nice = T("Disease Tracking"),
            #description = "Helps to track cases and trace contacts in disease outbreaks",
            restricted = True,
            module_type = None,
        )),
    ])

# END =========================================================================
