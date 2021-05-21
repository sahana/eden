# -*- coding: utf-8 -*-

"""
    Application Template for Rhineland-Palatinate (RLP) Crisis Management
    - used to manage Personnel Tests for COVID-19 response

    @license MIT
"""

from collections import OrderedDict

from gluon import current, URL, A, DIV, TAG, \
                  IS_EMPTY_OR, IS_IN_SET, IS_INT_IN_RANGE, IS_NOT_EMPTY

from gluon.storage import Storage

from s3 import FS, IS_FLOAT_AMOUNT, ICON, IS_ONE_OF, S3Represent, s3_str
from s3dal import original_tablename

from .rlpgeonames import rlp_GeoNames

LSJV = "Landesamt für Soziales, Jugend und Versorgung"
SCHOOLS = "Schulen"
TESTSTATIONS = "COVID-19 Teststellen"
GOVERNMENT = "Regierungsstellen"

ISSUER_ORG_TYPE = "pe_id$pe_id:org_organisation.org_organisation_organisation_type.organisation_type_id"

ALLOWED_FORMATS = ("html", "iframe", "popup", "aadata", "json")
# =============================================================================
def config(settings):

    T = current.T

    purpose = {"event": "COVID-19"}
    settings.base.system_name = T("%(event)s Testing") % purpose
    settings.base.system_name_short = T("%(event)s Testing") % purpose

    # PrePopulate data
    settings.base.prepopulate += ("RLPPTM",)
    settings.base.prepopulate_demo.append("RLPPTM/Demo")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "RLP"
    settings.base.theme_layouts = "RLPPTM"

    # Custom XSLT transformation stylesheets
    settings.base.xml_formats = {"wws": "RLPPTM"}

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
    settings.auth.privileged_roles = {"DISEASE_TEST_READER": "ORG_GROUP_ADMIN",
                                      "PROGRAM_ACCOUNTANT": "PROGRAM_ACCOUNTANT",
                                      "PROGRAM_MANAGER": "ORG_GROUP_ADMIN",
                                      "PROVIDER_ACCOUNTANT": "PROVIDER_ACCOUNTANT",
                                      "SUPPLY_COORDINATOR": "SUPPLY_COORDINATOR",
                                      "VOUCHER_ISSUER": "VOUCHER_ISSUER",
                                      "VOUCHER_PROVIDER": "VOUCHER_PROVIDER",
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
    settings.L10n.thousands_separator = " "
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
    settings.project.multiple_organisations = True

    # -------------------------------------------------------------------------
    settings.fin.voucher_personalize = "dob"
    settings.fin.voucher_eligibility_types = True
    settings.fin.voucher_invoice_status_labels = {"VERIFIED": None,
                                                  "APPROVED": None,
                                                  "PAID": "Payment Ordered",
                                                  }
    settings.fin.voucher_claim_paid_label = "Payment Ordered"

    # -------------------------------------------------------------------------
    settings.req.req_type = ("Stock",)
    settings.req.type_inv_label = ("Equipment")

    settings.req.copyable = False
    settings.req.recurring = False

    settings.req.req_shortname = "BANF"
    settings.req.requester_label = "Orderer"
    settings.req.date_editable = False
    settings.req.status_writable = False

    settings.req.pack_values = False
    settings.req.inline_forms = True
    settings.req.use_commit = False

    settings.req.items_ask_purpose = False
    settings.req.prompt_match = False

    # -------------------------------------------------------------------------
    settings.inv.track_pack_values = False
    settings.inv.send_show_org = False

    # -------------------------------------------------------------------------
    settings.supply.catalog_default = "Material für Teststellen"
    settings.supply.catalog_multi = False

    # -------------------------------------------------------------------------
    # UI Settings
    settings.ui.calendar_clear_icon = True

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
        #elif tablename == "fin_voucher_claim":
        #
        #    # Claims are owned by the provider PE (default ok)
        #    realm_entity = 0
        #
        elif tablename == "fin_voucher_invoice":

            # Invoices are owned by the accountant organization of the billing
            table = s3db.table(tablename)
            btable = s3db.fin_voucher_billing
            query = (table._id == row.id) & \
                    (btable.id == table.billing_id)
            billing = db(query).select(btable.organisation_id,
                                       btable.realm_entity,
                                       limitby = (0, 1),
                                       ).first()
            if billing:
                organisation_id = billing.organisation_id
                if organisation_id:
                    realm_entity = s3db.pr_get_pe_id("org_organisation",
                                                     organisation_id,
                                                     )
                else:
                    realm_entity = billing.realm_entity

        elif tablename in ("fin_voucher_billing",
                           "fin_voucher_transaction",
                           ):

            # Billings and transactions inherit realm-entity of the program
            table = s3db.table(tablename)
            ptable = s3db.fin_voucher_program
            query = (table._id == row.id) & \
                    (ptable.id == table.program_id)
            program = db(query).select(ptable.realm_entity,
                                       limitby = (0, 1),
                                       ).first()
            if program:
                realm_entity = program.realm_entity

        elif tablename in ("inv_send", "inv_recv"):
            # Shipments inherit realm-entity from the sending/receiving site
            table = s3db.table(tablename)
            stable = s3db.org_site
            query = (table._id == row.id) & \
                    (stable.site_id == table.site_id)
            site = db(query).select(stable.realm_entity,
                                    limitby = (0, 1),
                                    ).first()
            if site:
                realm_entity = site.realm_entity

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

        s3db = current.s3db

        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

        record = r.record
        if r.tablename == "cms_series" and \
           record and record.name == "Announcements":
            table = s3db.cms_post
            field = table.priority
            field.readable = field.writable = True

            crud_fields = ["name",
                           "body",
                           "priority",
                           "date",
                           "expired",
                           S3SQLInlineLink("roles",
                                           label = T("Roles"),
                                           field = "group_id",
                                           ),
                           ]
            list_fields = ["date",
                           "priority",
                           "name",
                           "body",
                           "post_role.group_id",
                           "expired",
                           ]
            orderby = "cms_post.date desc"
        else:
            crud_fields = ["name",
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
                           ]
            list_fields = ["post_module.module",
                           "post_module.resource",
                           "name",
                           "date",
                           "comments",
                           ]
            orderby = "cms_post.name"

        s3db.configure("cms_post",
                       crud_form = S3SQLCustomForm(*crud_fields),
                       list_fields = list_fields,
                       orderby = orderby,
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
    def customise_doc_document_resource(r, tablename):

        if r.controller == "org" or r.function == "organisation":

            s3db = current.s3db
            table = s3db.doc_document

            # Hide URL field
            field = table.url
            field.readable = field.writable = False

            # Custom label for date-field
            field = table.date
            field.label = T("Uploaded on")
            field.default = r.utcnow.date()
            field.writable = False

            # Custom label for name-field
            field = table.name
            field.label = T("Title")

            # List fields
            list_fields = ["name",
                           "file",
                           "date",
                           "comments",
                           ]
            s3db.configure("doc_document",
                           list_fields = list_fields,
                           )

    settings.customise_doc_document_resource = customise_doc_document_resource

    # -------------------------------------------------------------------------
    def customise_disease_case_diagnostics_resource(r, tablename):

        db = current.db
        s3db = current.s3db

        table = s3db.disease_case_diagnostics

        from .helpers import get_stats_projects
        report_results = get_stats_projects()

        if not report_results: # or current.auth.s3_has_role("ADMIN"):
            s3db.configure("disease_case_diagnostics",
                           insertable = False,
                           )

        if r.interactive and report_results and r.method != "report":

            # Enable project link and make it mandatory
            field = table.project_id
            field.readable = True

            ptable = s3db.project_project
            if len(report_results) == 1:
                project_id = report_results[0]
                dbset = db(ptable.id == project_id)
                field.default = project_id
                field.writable = False
            else:
                dbset = ptable.id.belongs(report_results)
                field.writable = True
            field.requires = IS_ONE_OF(dbset, "project_project.id",
                                       field.represent,
                                       )

            field.comment = None

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
        field.default = "POS"
        field.requires = IS_IN_SET(result_options,
                                   zero = None,
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

        auth = current.auth
        has_role = auth.s3_has_role

        s3db = current.s3db
        table = s3db.fin_voucher

        # Determine form mode
        resource = r.resource
        group_voucher = resource.tablename == "fin_voucher" and \
                        r.get_vars.get("g") == "1"

        # Customise fields
        field = table.pe_id
        field.label = T("Issuer##fin")

        from s3 import S3WithIntro
        field = table.bearer_dob
        if group_voucher:
            label = T("Group Representative Date of Birth")
            intro = "GroupDoBIntro"
        else:
            label = T("Beneficiary Date of Birth")
            intro = "BearerDoBIntro"
        field.label = label
        field.widget = S3WithIntro(field.widget,
                                   intro = ("fin",
                                            "voucher",
                                            intro,
                                            ),
                                   )
        if not has_role("VOUCHER_ISSUER"):
            field.readable = field.writable = False

        field = table.initial_credit
        field.label = T("Number of Beneficiaries")
        if group_voucher:
            field.default = None
            field.requires = IS_INT_IN_RANGE(1, 51,
                                error_message = T("Enter the number of beneficiaries (max %(max)s)"),
                                )
            field.readable = field.writable = True

        field = table.comments
        field.label = T("Memoranda")
        field.comment = DIV(_class="tooltip",
                            _title="%s|%s" % (T("Memoranda"),
                                              T("Notes of the Issuer"),
                                              ),
                            )
        if not has_role("VOUCHER_PROVIDER"):
            field.readable = field.writable = False

        # Custom list fields
        if has_role("VOUCHER_ISSUER"):
            list_fields = ["program_id",
                           "signature",
                           (T("Beneficiary/Representative Date of Birth"), "bearer_dob"),
                           "initial_credit",
                           "credit_spent",
                           (T("Status"), "status"),
                           "date",
                           #"valid_until",
                           "comments",
                           ]
        else:
            list_fields = ["program_id",
                           "signature",
                           (T("Status"), "status"),
                           "pe_id",
                           #(T("Issuer Type"), ISSUER_ORG_TYPE),
                           "eligibility_type_id",
                           "initial_credit",
                           "credit_spent",
                           "date",
                           #"valid_until",
                           ]

        # Report Options
        if r.method == "report":
            facts = ((T("Credit Redeemed"), "sum(credit_spent)"),
                     (T("Credit Issued"), "sum(initial_credit)"),
                     (T("Remaining Credit"), "sum(balance)"),
                     (T("Number of Vouchers"), "count(id)"),
                     )
            axes = [ISSUER_ORG_TYPE,
                    "eligibility_type_id",
                    "program_id",
                    "status",
                    "pe_id",
                    ]
            report_options = {
                "rows": axes,
                "cols": axes,
                "fact": facts,
                "defaults": {"rows": axes[0],
                             "cols": axes[1],
                             "fact": facts[0],
                             "totals": True,
                             },
                }
            s3db.configure("fin_voucher",
                           report_options = report_options,
                           )

        s3db.configure("fin_voucher",
                       list_fields = list_fields,
                       orderby = "fin_voucher.date desc",
                       )

    settings.customise_fin_voucher_resource = customise_fin_voucher_resource

    # -------------------------------------------------------------------------
    def customise_fin_voucher_controller(**attr):

        s3 = current.response.s3

        # Enable bigtable features
        settings.base.bigtable = True

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

            is_program_manager = current.auth.s3_has_role("PROGRAM_MANAGER")

            db = current.db
            s3db = current.s3db

            # Check which programs and organisations the user can issue vouchers for
            program_ids, org_ids, pe_ids = s3db.fin_voucher_permitted_programs(mode="issuer")

            resource = r.resource
            table = resource.table

            if program_ids and org_ids:
                etypes = s3db.fin_voucher_eligibility_types(program_ids, org_ids)
                program_ids = list(etypes.keys())

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
                # Default the program selector if only one program can be chosen
                if len(program_ids) == 1:
                    program_id = program_ids[0]
                    field.default = program_id
                    field.writable = False

                # Limit the eligibility type selector to applicable types
                allow_empty = False
                if len(program_ids) == 1:
                    etype_ids = etypes[program_ids[0]]
                else:
                    etype_ids = []
                    for item in etypes.values():
                        if item:
                            etype_ids += item
                        else:
                            allow_empty = True
                    etype_ids = list(set(etype_ids)) if etype_ids else None

                field = table.eligibility_type_id
                if etype_ids is None:
                    # No selectable eligibility types => hide selector
                    field.readable = field.writable = False
                elif len(etype_ids) == 1 and not allow_empty:
                    # Only one type selectable => default
                    field.default = etype_ids[0]
                    field.writable = False
                else:
                    # Multiple types selectable
                    ttable = s3db.fin_voucher_eligibility_type
                    etset = db(ttable.id.belongs(etype_ids))
                    field.requires = IS_ONE_OF(etset, "fin_voucher_eligibility_type.id",
                                               field.represent,
                                               sort = True,
                                               )
                    if allow_empty:
                        field.requires = IS_EMPTY_OR(field.requires)

                # Limit the issuer selector to permitted entities
                etable = s3db.pr_pentity
                field = table.pe_id
                dbset = db(etable.pe_id.belongs(pe_ids))
                field.requires = IS_ONE_OF(dbset, "pr_pentity.pe_id",
                                           field.represent,
                                           )
                # Hide the issuer selector if only one entity can be chosen
                if len(pe_ids) == 1:
                    field.default = pe_ids[0]
                    field.readable = field.writable = False

            if r.interactive:

                if r.get_vars.get("g") == "1":
                    s3.crud_strings["fin_voucher"]["label_create"] = T("Create Group Voucher")

                # Hide valid_until from create-form (will be set onaccept)
                field = table.valid_until
                field.readable = bool(r.record)
                field.writable = False

                # Always show number of beneficiaries
                if r.record:
                    field = table.initial_credit
                    field.readable = True

                # Filter Widgets
                from s3 import S3DateFilter, S3TextFilter
                text_fields = ["signature", "comments", "program_id$name"]
                if is_program_manager:
                    text_fields.append("pe_id$pe_id:org_organisation.name")
                filter_widgets = [
                    S3TextFilter(text_fields,
                                 label = T("Search"),
                                 ),
                    S3DateFilter("date",
                                 ),
                    ]
                if is_program_manager:
                    from s3 import S3OptionsFilter, s3_get_filter_opts
                    filter_widgets.extend([
                        S3OptionsFilter("eligibility_type_id",
                                        hidden = True,
                                        label = T("Type of Eligibility"),
                                        ),
                        S3OptionsFilter(ISSUER_ORG_TYPE,
                                        hidden = True,
                                        label = T("Issuer Type"),
                                        options = lambda: s3_get_filter_opts("org_organisation_type"),
                                        ),
                        ])
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

        auth = current.auth
        has_role = auth.s3_has_role

        s3db = current.s3db
        table = s3db.fin_voucher_debit

        # Determine form mode
        resource = r.resource
        group_voucher = resource.tablename == "fin_voucher_debit" and \
                        r.get_vars.get("g") == "1"

        # Customise fields
        field = table.comments
        field.label = T("Memoranda")
        field.comment = DIV(_class="tooltip",
                            _title="%s|%s" % (T("Memoranda"),
                                              T("Notes of the Provider"),
                                              ),
                            )
        if not has_role("VOUCHER_PROVIDER"):
            field.readable = field.writable = False

        field = table.bearer_dob
        if group_voucher:
            label = T("Group Representative Date of Birth")
        else:
            label = T("Beneficiary Date of Birth")
        field.label = label
        if not has_role("VOUCHER_PROVIDER"):
            field.readable = field.writable = False

        field = table.quantity
        if group_voucher:
            field.default = None
            field.requires = IS_INT_IN_RANGE(1,
                                error_message = T("Enter the service quantity"),
                                )
            field.readable = field.writable = True

        field = table.balance
        field.label = T("Remaining Compensation Claims")

        # Custom list_fields
        list_fields = [(T("Date"), "date"),
                       "program_id",
                       "voucher_id$signature",
                       "quantity",
                       "status",
                       ]
        if current.auth.s3_has_roles(("PROGRAM_MANAGER", "PROGRAM_ACCOUNTANT")):
            # Include issuer and provider
            list_fields[3:3] = ["voucher_id$pe_id",
                                "pe_id",
                                ]
        if has_role("VOUCHER_PROVIDER"):
            # Include provider notes
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
            field = table.created_by
            field.represent = s3db.auth_UserRepresent(show_name = True,
                                                      show_email = False,
                                                      )
            facts = ((T("Total Services Rendered"), "sum(quantity)"),
                     (T("Number of Accepted Vouchers"), "count(id)"),
                     (T("Remaining Compensation Claims"), "sum(balance)"),
                     )
            axes = ["program_id",
                    "status",
                    ]
            has_role = auth.s3_has_role
            if has_role("PROGRAM_MANAGER"):
                axes.insert(0, "pe_id")
            if has_role("VOUCHER_PROVIDER"):
                axes.append((T("User"), "created_by"))
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

        # Enable bigtable features
        settings.base.bigtable = True

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            db = current.db
            s3db = current.s3db

            resource = r.resource

            # Catch inappropriate cancel-attempts
            record = r.record
            if record and not r.component and r.method == "cancel":
                from .helpers import can_cancel_debit
                if not can_cancel_debit(record):
                    r.unauthorised()

            has_role = current.auth.s3_has_role
            if has_role("PROGRAM_ACCOUNTANT") and not has_role("PROGRAM_MANAGER"):

                # PROGRAM_ACCOUNTANT can only see debits where they are assigned
                # for the billing process
                from .helpers import get_role_realms
                role_realms = get_role_realms("PROGRAM_ACCOUNTANT")
                if role_realms is not None:
                    query = FS("billing_id$organisation_id$pe_id").belongs(role_realms)
                    resource.add_filter(query)

                # PROGRAM_ACCOUNTANT does not (need to) see cancelled debits
                resource.add_filter(FS("cancelled") == False)

            # Check which programs and organisations the user can accept vouchers for
            program_ids, org_ids, pe_ids = s3db.fin_voucher_permitted_programs(
                                                        mode = "provider",
                                                        partners_only = True,
                                                        )
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

                # Always show quantity
                if record:
                    field = table.quantity
                    field.readable = True

            if r.interactive:

                if r.get_vars.get("g") == "1":
                    s3.crud_strings["fin_voucher_debit"]["label_create"] = T("Accept Group Voucher")

            return result
        s3.prep = prep

        # Custom rheader
        from .rheaders import rlpptm_fin_rheader
        attr["rheader"] = rlpptm_fin_rheader

        return attr

    settings.customise_fin_voucher_debit_controller = customise_fin_voucher_debit_controller

    # -------------------------------------------------------------------------
    def customise_fin_voucher_program_resource(r, tablename):

        table = current.s3db.fin_voucher_program

        represent = lambda v, row=None: -v if v else current.messages["NONE"]

        field = table.credit
        field.label = T("Pending Credits")
        field.represent = represent

        field = table.compensation
        field.label = T("Pending Compensation Claims")
        field.represent = represent

    settings.customise_fin_voucher_program_resource = customise_fin_voucher_program_resource

    # -------------------------------------------------------------------------
    def customise_fin_voucher_program_controller(**attr):

        s3 = current.response.s3

        # Enable bigtable features
        settings.base.bigtable = True

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            resource = r.resource

            has_role = current.auth.s3_has_role
            if has_role("PROGRAM_ACCOUNTANT") and not has_role("PROGRAM_MANAGER"):

                # PROGRAM_ACCOUNTANT can only see programs where they are
                # assigned for a billing process
                from .helpers import get_role_realms
                role_realms = get_role_realms("PROGRAM_ACCOUNTANT")
                if role_realms is not None:
                    query = FS("voucher_billing.organisation_id$pe_id").belongs(role_realms)
                    resource.add_filter(query)

            return result
        s3.prep = prep

        return attr

    settings.customise_fin_voucher_program_controller = customise_fin_voucher_program_controller

    # -------------------------------------------------------------------------
    def billing_onaccept(form):
        """
            Custom onaccept of billing:
            - make sure all invoices are owned by the accountant
              organisation (as long as they are the accountants in charge)
        """

        # Get record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        db = current.db
        s3db = current.s3db

        # Get the billing/program organisations
        table = s3db.fin_voucher_billing
        ptable = s3db.fin_voucher_program
        left = ptable.on((ptable.id == table.program_id) & \
                         (ptable.deleted == False))
        query = (table.id == record_id)
        row = db(query).select(table.id,
                               table.organisation_id,
                               ptable.organisation_id,
                               left = left,
                               limitby = (0, 1),
                               ).first()
        if not row:
            return

        # Identify the organisation to own the invoices under this process
        billing = row.fin_voucher_billing
        organisation_id = billing.organisation_id
        if not organisation_id:
            organisation_id = row.fin_voucher_program.organisation_id

        # Update the realm entity as needed
        if organisation_id:
            pe_id = s3db.pr_get_pe_id("org_organisation", organisation_id)
            itable = s3db.fin_voucher_invoice
            query = (itable.billing_id == billing.id) & \
                    (itable.realm_entity != pe_id) & \
                    (itable.deleted == False)
            current.auth.set_realm_entity(itable,
                                          query,
                                          entity = pe_id,
                                          force_update = True,
                                          )

            # Re-assign pending invoices
            from .helpers import assign_pending_invoices
            assign_pending_invoices(billing.id,
                                    organisation_id = organisation_id,
                                    )

    # -------------------------------------------------------------------------
    def customise_fin_voucher_billing_resource(r, tablename):

        s3db = current.s3db
        table = current.s3db.fin_voucher_billing

        # Color-coded representation of billing process status
        from s3 import S3PriorityRepresent
        field = table.status
        try:
            status_opts = field.represent.options
        except AttributeError:
            pass
        else:
            field.represent = S3PriorityRepresent(status_opts,
                                                  {"SCHEDULED": "lightblue",
                                                   "IN PROGRESS": "amber",
                                                   "ABORTED": "black",
                                                   "COMPLETE": "green",
                                                   }).represent

        # Custom onaccept to maintain realm-assignment of invoices
        # when accountant organisation changes
        s3db.add_custom_callback("fin_voucher_billing",
                                 "onaccept",
                                 billing_onaccept,
                                 )

    settings.customise_fin_voucher_billing_resource = customise_fin_voucher_billing_resource

    # -------------------------------------------------------------------------
    def claim_create_onaccept(form):
        """
            Custom create-onaccept for claim to notify the provider
            accountant about the new claim
        """

        # Get record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        db = current.db
        s3db = current.s3db

        table = s3db.fin_voucher_claim
        btable = s3db.fin_voucher_billing
        ptable = s3db.fin_voucher_program
        join = [ptable.on(ptable.id == table.program_id),
                btable.on(btable.id == table.billing_id),
                ]
        query = (table.id == record_id)
        row = db(query).select(table.id,
                               table.program_id,
                               table.billing_id,
                               table.pe_id,
                               table.status,
                               btable.date,
                               ptable.name,
                               ptable.organisation_id,
                               join = join,
                               limitby = (0, 1),
                               ).first()
        if not row:
            return
        program = row.fin_voucher_program
        billing = row.fin_voucher_billing
        claim = row.fin_voucher_claim

        if claim.status != "NEW":
            return

        error = None

        # Look up the provider organisation
        pe_id = claim.pe_id
        otable = s3db.org_organisation
        provider = db(otable.pe_id == pe_id).select(otable.id,
                                                    otable.name,
                                                    limitby = (0, 1),
                                                    ).first()

        from .helpers import get_role_emails
        provider_accountants = get_role_emails("PROVIDER_ACCOUNTANT", pe_id)
        if not provider_accountants:
            error = "No provider accountant found"

        if not error:
            # Lookup the template variables
            base_url = current.deployment_settings.get_base_public_url()
            appname = current.request.application
            data = {"program": program.name,
                    "date": btable.date.represent(billing.date),
                    "organisation": provider.name,
                    "url": "%s/%s/fin/voucher_claim/%s" % (base_url, appname, claim.id),
                    }

            # Send the email notification
            from .notifications import CMSNotifications
            error = CMSNotifications.send(provider_accountants,
                                          "ClaimNotification",
                                          data,
                                          module = "fin",
                                          resource = "voucher_claim",
                                          )
        if error:
            # Inform the program manager that the provider could not be notified
            msg = T("%(name)s could not be notified of new compensation claim: %(error)s") % \
                  {"name": provider.name, "error": error}
            program_managers = get_role_emails("PROGRAM_MANAGER",
                                               organisation_id = program.organisation_id,
                                               )
            if program_managers:
                current.msg.send_email(to = program_managers,
                                       subject = T("Provider Notification Failed"),
                                       message = msg,
                                       )
            current.log.error(msg)
        else:
            current.log.debug("Provider '%s' notified about new compensation claim" % provider.name)

    # -------------------------------------------------------------------------
    def customise_fin_voucher_claim_resource(r, tablename):

        auth = current.auth
        s3db = current.s3db

        table = s3db.fin_voucher_claim

        is_provider_accountant = auth.s3_has_role("PROVIDER_ACCOUNTANT")

        if not is_provider_accountant:
            # Hide comments
            field = table.comments
            field.readable = field.writable = False

        # Color-coded representation of claim status
        from s3 import S3PriorityRepresent
        field = table.status
        try:
            status_opts = field.represent.options
        except AttributeError:
            pass
        else:
            field.represent = S3PriorityRepresent(status_opts,
                                                  {"NEW": "lightblue",
                                                   "CONFIRMED": "blue",
                                                   "INVOICED": "amber",
                                                   "PAID": "green",
                                                   }).represent

        # Custom list fields
        list_fields = [#"refno",
                       "date",
                       "program_id",
                       #"pe_id",
                       "vouchers_total",
                       "quantity_total",
                       "amount_receivable",
                       "currency",
                       "status",
                       ]
        if is_provider_accountant:
            list_fields.insert(0, "refno")
            text_fields = ["refno",
                           "comments",
                           ]
        else:
            list_fields.insert(2, "pe_id")
            text_fields = ["pe_id$pe_id:org_organisation.name",
                           ]

        # Filter widgets
        from s3 import S3TextFilter, S3OptionsFilter, s3_get_filter_opts
        filter_widgets = [S3TextFilter(text_fields,
                                       label = T("Search"),
                                       ),
                          S3OptionsFilter("program_id",
                                          options = lambda: s3_get_filter_opts("fin_voucher_program"),
                                          ),
                          ]

        s3db.configure("fin_voucher_claim",
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

        # PDF export method
        from .helpers import ClaimPDF
        s3db.set_method("fin", "voucher_claim",
                        method = "record",
                        action = ClaimPDF,
                        )

        s3db.add_custom_callback("fin_voucher_claim",
                                 "onaccept",
                                 claim_create_onaccept,
                                 method = "create",
                                 )

    settings.customise_fin_voucher_claim_resource = customise_fin_voucher_claim_resource

    # -------------------------------------------------------------------------
    def customise_fin_voucher_claim_controller(**attr):

        s3 = current.response.s3

        s3db = current.s3db

        # Custom prep
        standard_prep = s3.prep
        def prep(r):

            # Block all non-interactive update attempts
            if not r.interactive and r.http != "GET":
                r.error(403, current.ERROR.NOT_PERMITTED)

            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            # Check which programs and organisations the user can accept vouchers for
            program_ids, org_ids = s3db.fin_voucher_permitted_programs(mode = "provider",
                                                                       partners_only = True,
                                                                       c = "fin",
                                                                       f = "voucher_debit",
                                                                       )[:2]
            if not program_ids or not org_ids:
                s3db.configure("fin_voucher_debit",
                               insertable = False,
                               )

            return result
        s3.prep = prep

        standard_postp = s3.postp
        def custom_postp(r, output):

            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if not r.component and isinstance(output, dict):
                record = r.record
                if record and r.method in (None, "update", "read"):

                    # Hint that the user need to confirm the claim
                    if record.status == "NEW" and \
                       all(record[fn] for fn in ("account_holder", "account_number")):
                        current.response.warning = T('You must change the status to "confirmed" before an invoice can be issued')

                    # Custom CRUD buttons
                    if "buttons" not in output:
                        buttons = output["buttons"] = {}
                    else:
                        buttons = output["buttons"]

                    # PDF-button
                    pdf_download = A(T("Download PDF"),
                                     _href = "/%s/fin/voucher_claim/%s/record.pdf" % \
                                             (r.application, record.id),
                                     _class="action-btn",
                                     )

                    # Render in place of the delete-button
                    buttons["delete_btn"] = TAG[""](pdf_download,
                                                    )
            return output
        s3.postp = custom_postp

        return attr

    settings.customise_fin_voucher_claim_controller = customise_fin_voucher_claim_controller

    # -------------------------------------------------------------------------
    def invoice_onsettled(invoice):
        """
            Callback to notify the provider that an invoice has been settled

            @param invoice: the invoice (Row)
        """

        db = current.db
        s3db = current.s3db

        # Look up claim, invoice number, program and billing
        btable = s3db.fin_voucher_billing
        ctable = s3db.fin_voucher_claim
        itable = s3db.fin_voucher_invoice
        ptable = s3db.fin_voucher_program
        join = [ptable.on(ptable.id == ctable.program_id),
                btable.on(btable.id == ctable.billing_id),
                itable.on(itable.id == ctable.invoice_id),
                ]
        query = (ctable.invoice_id == invoice.id) & \
                (ctable.deleted == False)
        row = db(query).select(ctable.id,
                               ctable.program_id,
                               ctable.billing_id,
                               ctable.pe_id,
                               btable.date,
                               itable.invoice_no,
                               ptable.name,
                               ptable.organisation_id,
                               join = join,
                               limitby = (0, 1),
                               ).first()
        if not row:
            return
        program = row.fin_voucher_program
        billing = row.fin_voucher_billing
        claim = row.fin_voucher_claim
        invoice_no = row.fin_voucher_invoice.invoice_no

        error = None

        # Look up the provider organisation
        pe_id = claim.pe_id
        otable = s3db.org_organisation
        provider = db(otable.pe_id == pe_id).select(otable.id,
                                                    otable.name,
                                                    limitby = (0, 1),
                                                    ).first()

        from .helpers import get_role_emails
        provider_accountants = get_role_emails("PROVIDER_ACCOUNTANT", pe_id)
        if not provider_accountants:
            error = "No provider accountant found"

        if not error:
            # Lookup the template variables
            base_url = current.deployment_settings.get_base_public_url()
            appname = current.request.application
            data = {"program": program.name,
                    "date": btable.date.represent(billing.date),
                    "invoice": invoice_no,
                    "organisation": provider.name,
                    "url": "%s/%s/fin/voucher_claim/%s" % (base_url, appname, claim.id),
                    }

            # Send the email notification
            from .notifications import CMSNotifications
            error = CMSNotifications.send(provider_accountants,
                                          "InvoiceSettled",
                                          data,
                                          module = "fin",
                                          resource = "voucher_invoice",
                                          )
        if error:
            msg = "%s could not be notified about invoice settlement: %s"
            current.log.error(msg % (provider.name, error))
        else:
            msg = "%s notified about invoice settlement"
            current.log.debug(msg % provider.name)

    # -------------------------------------------------------------------------
    def invoice_create_onaccept(form):
        """
            Custom create-onaccept to assign a new invoice to an
            accountant
        """

        # Get record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        # Look up the billing ID
        table = current.s3db.fin_voucher_invoice
        query = (table.id == record_id)
        invoice = current.db(query).select(table.billing_id,
                                           limitby = (0, 1),
                                           ).first()

        if invoice:
            # Assign the invoice
            from .helpers import assign_pending_invoices
            assign_pending_invoices(invoice.billing_id,
                                    invoice_id = record_id,
                                    )

    # -------------------------------------------------------------------------
    def customise_fin_voucher_invoice_resource(r, tablename):

        auth = current.auth
        s3db = current.s3db

        table = s3db.fin_voucher_invoice

        # Color-coded representation of invoice status
        from s3 import S3PriorityRepresent
        field = table.status
        try:
            status_opts = field.requires.options()
        except AttributeError:
            status_opts = []
        else:
            field.represent = S3PriorityRepresent(status_opts,
                                                  {"NEW": "lightblue",
                                                   "APPROVED": "blue",
                                                   "REJECTED": "red",
                                                   "PAID": "green",
                                                   })

        is_accountant = auth.s3_has_role("PROGRAM_ACCOUNTANT")

        # Personal work list?
        if is_accountant and r.get_vars.get("mine") == "1":
            title_list = T("My Work List")
            default_status = ["NEW", "REJECTED"]
            default_hr = current.auth.s3_logged_in_human_resource()
        else:
            title_list = T("All Invoices")
            default_status = default_hr = None
        current.response.s3.crud_strings["fin_voucher_invoice"].title_list = title_list

        # Lookup method for HR filter options
        if is_accountant:
            def hr_filter_opts():
                hresource = s3db.resource("hrm_human_resource")
                rows = hresource.select(["id", "person_id"], represent=True).rows
                return {row["hrm_human_resource.id"]:
                        row["hrm_human_resource.person_id"] for row in rows}
        else:
            hr_filter_opts = None

        # Filter widgets
        from s3 import S3DateFilter, S3OptionsFilter, S3TextFilter
        if r.interactive:
            filter_widgets = [S3TextFilter(["invoice_no",
                                            "refno",
                                            ],
                                           label = T("Search"),
                                           ),
                              S3OptionsFilter("status",
                                              default = default_status,
                                              options = OrderedDict(status_opts),
                                              sort = False,
                                              ),
                              S3OptionsFilter("human_resource_id",
                                              default = default_hr,
                                              options = hr_filter_opts,
                                              ),
                              S3DateFilter("date",
                                           hidden = True,
                                           ),
                              S3OptionsFilter("pe_id",
                                              hidden = True,
                                              ),
                              S3OptionsFilter("pe_id$pe_id:org_organisation.facility.location_id$L2",
                                              hidden = True,
                                              ),
                              ]
            s3db.configure("fin_voucher_invoice",
                           filter_widgets = filter_widgets,
                           )

        # Custom create-onaccept to assign the invoice
        s3db.add_custom_callback("fin_voucher_invoice",
                                 "onaccept",
                                 invoice_create_onaccept,
                                 method = "create",
                                 )

        # PDF export method
        from .helpers import InvoicePDF
        s3db.set_method("fin", "voucher_invoice",
                        method = "record",
                        action = InvoicePDF,
                        )

        # Callback when invoice is settled
        s3db.configure("fin_voucher_invoice",
                       onsettled = invoice_onsettled,
                       )

    settings.customise_fin_voucher_invoice_resource = customise_fin_voucher_invoice_resource

    # -------------------------------------------------------------------------
    def customise_fin_voucher_invoice_controller(**attr):

        s3 = current.response.s3

        # Enable bigtable features
        settings.base.bigtable = True

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
                                     _href = "/%s/fin/voucher_invoice/%s/record.pdf" % \
                                             (r.application, r.record.id),
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

    settings.customise_fin_voucher_invoice_controller = customise_fin_voucher_invoice_controller

    # -------------------------------------------------------------------------
    def add_org_tags():
        """
            Add organisation tags as filtered components,
            for embedding in form, filtering and as report axis
        """

        s3db = current.s3db

        s3db.add_components("org_organisation",
                            org_organisation_tag = ({"name": "requester",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "REQUESTER"},
                                                     "multiple": False,
                                                     },
                                                    ),
                            )

    # -------------------------------------------------------------------------
    def organisation_create_onaccept(form):

        # Get record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        from .helpers import add_organisation_default_tags
        add_organisation_default_tags(record_id)

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        s3db = current.s3db

        # Add binary organisation tags
        add_org_tags()

        # Reports configuration
        if r.method == "report":
            axes = ["facility.location_id$L3",
                    "facility.location_id$L2",
                    "facility.location_id$L1",
                    "facility.service_site.service_id",
                    (T("Project"), "project.name"),
                    (T("Organization Group"), "group_membership.group_id"),
                    ]

            report_options = {
                "rows": axes,
                "cols": axes,
                "fact": [(T("Number of Organizations"), "count(id)"),
                         (T("Number of Facilities"), "count(facility.id)"),
                        ],
                "defaults": {"rows": "facility.location_id$L2",
                             "cols": None,
                             "fact": "count(id)",
                             "totals": True,
                             },
                }

            s3db.configure(tablename,
                           report_options = report_options,
                           )

        # Custom onaccept to create default tags
        s3db.add_custom_callback("org_organisation",
                                 "onaccept",
                                 organisation_create_onaccept,
                                 method = "create",
                                 )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        s3 = current.response.s3

        # Enable bigtable features
        settings.base.bigtable = True

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            auth = current.auth
            s3db = current.s3db

            resource = r.resource

            is_org_group_admin = auth.s3_has_role("ORG_GROUP_ADMIN")

            # Configure binary tags
            from .helpers import configure_binary_tags
            configure_binary_tags(resource, ("requester",))

            # Add invite-method for ORG_GROUP_ADMIN role
            from .helpers import InviteUserOrg
            s3db.set_method("org", "organisation",
                            method = "invite",
                            action = InviteUserOrg,
                            )

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

            record = r.record
            if not r.component:
                if r.interactive:

                    ltable = s3db.project_organisation
                    field = ltable.project_id
                    field.represent = S3Represent(lookup="project_project")

                    from s3 import S3SQLCustomForm, \
                                   S3SQLInlineComponent, \
                                   S3SQLInlineLink, \
                                   S3OptionsFilter, \
                                   S3TextFilter, \
                                   s3_get_filter_opts

                    # Custom form
                    if is_org_group_admin:
                        user = auth.user
                        if record and user:
                            # Only OrgGroupAdmins managing this organisation can change
                            # its org group membership (=organisation must be within realm):
                            realm = user.realms.get(auth.get_system_roles().ORG_GROUP_ADMIN)
                            groups_readonly = realm is not None and record.pe_id not in realm
                        else:
                            groups_readonly = False

                        groups = S3SQLInlineLink("group",
                                                 field = "group_id",
                                                 label = T("Organization Group"),
                                                 multiple = False,
                                                 readonly = groups_readonly,
                                                 )
                        projects = S3SQLInlineLink("project",
                                                   field = "project_id",
                                                   label = T("Project Partner for"),
                                                   cols = 1,
                                                   )
                        requester = (T("Can order equipment"), "requester.value")
                        types = S3SQLInlineLink("organisation_type",
                                                field = "organisation_type_id",
                                                search = False,
                                                label = T("Type"),
                                                multiple = settings.get_org_organisation_types_multiple(),
                                                widget = "multiselect",
                                                )
                    else:
                        groups = projects = requester = types = None

                    crud_fields = [groups,
                                   projects,
                                   requester,
                                   "name",
                                   "acronym",
                                   types,
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
                                   "logo",
                                   "comments",
                                   ]

                    # Filters
                    text_fields = ["name", "acronym", "website", "phone"]
                    if is_org_group_admin:
                        text_fields.append("email.value")
                    filter_widgets = [S3TextFilter(text_fields,
                                                   label = T("Search"),
                                                   ),
                                      ]
                    if is_org_group_admin:
                        filter_widgets.extend([
                            S3OptionsFilter(
                                "group__link.group_id",
                                label = T("Group"),
                                options = lambda: s3_get_filter_opts("org_group"),
                                ),
                            S3OptionsFilter(
                                "organisation_type__link.organisation_type_id",
                                label = T("Type"),
                                options = lambda: s3_get_filter_opts("org_organisation_type"),
                                ),
                            ])

                    resource.configure(crud_form = S3SQLCustomForm(*crud_fields),
                                       filter_widgets = filter_widgets,
                                       )

                # Custom list fields
                list_fields = [#"group__link.group_id",
                               "name",
                               "acronym",
                               #"organisation_type__link.organisation_type_id",
                               "website",
                               "phone",
                               #"email.value"
                               ]
                if is_org_group_admin:
                    list_fields.insert(2, (T("Type"), "organisation_type__link.organisation_type_id"))
                    list_fields.insert(0, (T("Organization Group"), "group__link.group_id"))
                    list_fields.append((T("Email"), "email.value"))
                r.resource.configure(list_fields = list_fields,
                                     )

            elif r.component_name == "facility":
                if r.component_id and \
                   (is_org_group_admin or \
                    record and auth.s3_has_role("ORG_ADMIN", for_pe=record.pe_id)):
                    # Expose obsolete-flag
                    ctable = r.component.table
                    field = ctable.obsolete
                    field.readable = field.writable = True

            return result
        s3.prep = prep

        # Custom rheader
        from .rheaders import rlpptm_org_rheader
        attr = dict(attr)
        attr["rheader"] = rlpptm_org_rheader

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_org_organisation_type_resource(r, tablename):

        db = current.db
        s3db = current.s3db

        s3db.add_components("org_organisation_type",
                            org_organisation_type_tag = ({"name": "group",
                                                          "joinby": "organisation_type_id",
                                                          "filterby": {"tag": "OrgGroup"},
                                                          "multiple": False,
                                                          },
                                                         {"name": "commercial",
                                                          "joinby": "organisation_type_id",
                                                          "filterby": {"tag": "Commercial"},
                                                          "multiple": False,
                                                          },
                                                         ),
                            )

        if r.tablename == "org_organisation_type":

            T = current.T

            resource = r.resource
            component = resource.components.get("group")
            if component:

                # Look up organisation group names
                gtable = s3db.org_group
                groups = db(gtable.deleted == False).select(gtable.name,
                                                            cache = s3db.cache,
                                                            )
                options = [group.name for group in groups]

                # Configure them as options for the OrgGroup tag
                ctable = component.table
                field = ctable.value
                field.label = T("Organization Group")
                field.requires = IS_EMPTY_OR(IS_IN_SET(options))

            # Configure binary tag representation
            from .helpers import configure_binary_tags
            configure_binary_tags(r.resource, ("commercial",))

            # Custom form
            from s3 import S3SQLCustomForm
            crud_form = S3SQLCustomForm("name",
                                        "group.value",
                                        (T("Commercial Providers"), "commercial.value"),
                                        "comments",
                                        )

            # Include tags in list view
            list_fields = ["id",
                           "name",
                           "group.value",
                           (T("Commercial Providers"), "commercial.value"),
                           "comments",
                           ]

            resource.configure(crud_form = crud_form,
                               list_fields = list_fields,
                               )

    settings.customise_org_organisation_type_resource = customise_org_organisation_type_resource

    # -------------------------------------------------------------------------
    def facility_create_onaccept(form):

        # Get record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        from .helpers import add_facility_default_tags
        add_facility_default_tags(record_id)

    # -------------------------------------------------------------------------
    def facility_postprocess(form):

        # Get record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        # Lookup site_id
        table = current.s3db.org_facility
        row = current.db(table.id == record_id).select(table.site_id,
                                                       limitby = (0, 1),
                                                       ).first()
        if row and row.site_id:
            # Update approval workflow
            from .helpers import facility_approval_workflow
            facility_approval_workflow(row.site_id)

    # -------------------------------------------------------------------------
    def customise_org_facility_resource(r, tablename):

        auth = current.auth
        s3db = current.s3db

        is_org_group_admin = current.auth.s3_has_role("ORG_GROUP_ADMIN")

        # Approval workflow tags as filtered components (for embedding in form)
        add_org_tags()
        s3db.add_components("org_site",
                            org_site_tag = (# Approval workflow status
                                            {"name": "status",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "STATUS"},
                                             "multiple": False,
                                             },
                                            # MPAV qualification
                                            {"name": "mpav",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "MPAV"},
                                             "multiple": False,
                                             },
                                            # Hygiene concept
                                            {"name": "hygiene",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "HYGIENE"},
                                             "multiple": False,
                                             },
                                            # Facility layout
                                            {"name": "layout",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "LAYOUT"},
                                             "multiple": False,
                                             },
                                            # In public registry
                                            {"name": "public",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "PUBLIC"},
                                             "multiple": False,
                                             },
                                            ),
                            )

        # Custom onaccept to add default tags
        s3db.add_custom_callback("org_facility",
                                 "onaccept",
                                 facility_create_onaccept,
                                 method = "create",
                                 )

        # Configure fields
        in_org_controller = r.tablename == "org_organisation"
        from s3 import (S3SQLCustomForm,
                        S3SQLInlineLink,
                        S3SQLInlineComponent,
                        S3LocationFilter,
                        S3LocationSelector,
                        S3OptionsFilter,
                        S3TextFilter,
                        S3WithIntro,
                        s3_get_filter_opts,
                        s3_text_represent,
                        )

        table = s3db.org_facility

        # Custom representation of organisation_id including type
        field = table.organisation_id
        from .helpers import OrganisationRepresent
        field.represent = OrganisationRepresent()
        field.comment = None

        # Configure location selector incl. Geocoder
        field = table.location_id
        # Address/Postcode are required
        # - except for OrgGroupAdmin, who need to be able to
        #   update the record even when this detail is missing
        address_required = not is_org_group_admin
        field.widget = S3LocationSelector(levels = ("L1", "L2", "L3", "L4"),
                                          required_levels = ("L1", "L2", "L3"),
                                          show_address = True,
                                          show_postcode = True,
                                          address_required = address_required,
                                          postcode_required = address_required,
                                          show_map = True,
                                          )
        current.response.s3.scripts.append("/%s/static/themes/RLP/js/geocoderPlugin.js" % r.application)

        # Custom tooltip for comments field
        field = table.comments
        if in_org_controller:
            field.comment = DIV(_class="tooltip",
                                _title="%s|%s" % (T("Comments"),
                                                  T("Additional information and advice regarding facility and services"),
                                                  ),
                                )
        else:
            field.writable = False
            field.comment = None

        # Custom label for obsolete-Flag
        field = table.obsolete
        field.label = T("Defunct")
        field.represent = lambda v, row=None: ICON("remove") if v else ""
        field.comment = DIV(_class="tooltip",
                            _title="%s|%s" % (T("Defunct"),
                                              T("Please mark this field when the facility is no longer in operation"),
                                              ),
                            )

        # Opening times are mandatory
        # - except for OrgGroupAdmin, who need to be able to
        #   update the record even when this detail is missing
        if not is_org_group_admin:
            field = table.opening_times
            field.requires = IS_NOT_EMPTY()

        # Custom representation of service links
        stable = s3db.org_service_site
        field = stable.service_id
        from .helpers import ServiceListRepresent
        field.represent = ServiceListRepresent(lookup = "org_service",
                                               show_link = False,
                                               )

        # Expose site details
        dtable = s3db.org_site_details
        field = dtable.booking_mode_id
        field.readable = True
        field.writable = in_org_controller

        field = dtable.service_mode_id
        field.readable = True
        field.writable = in_org_controller
        requires = field.requires
        if isinstance(requires, IS_EMPTY_OR):
            field.requires = requires.other

        field = dtable.authorisation_advice
        field.label = T("Advice")
        css = "approve-workflow"
        field.represent = lambda v, row=None: \
                            s3_text_represent(v,
                                truncate = False,
                                _class = ("%s workflow-advice" % css) if v else css,
                                )
        field.readable = True
        if is_org_group_admin:
            field.comment = DIV(_class="tooltip",
                                _title="%s|%s" % (T("Advice"),
                                                  T("Instructions/advice for the test station how to proceed with regard to authorization"),
                                                  ),
                                )
            field.writable = True
        else:
            field.writable = False

        # Custom list fields
        list_fields = ["name",
                       #"organisation_id",
                       (T("Telephone"), "phone1"),
                       "email",
                       (T("Opening Hours"), "opening_times"),
                       "service_site.service_id",
                       "location_id$addr_street",
                       "location_id$addr_postcode",
                       "location_id$L4",
                       "location_id$L3",
                       "location_id$L2",
                       ]
        if is_org_group_admin and r.get_vars.get("$$pending") == "1":
            list_fields.insert(1, "organisation_id")
        elif in_org_controller:
            list_fields.append("obsolete")

        # Custom filter widgets
        text_fields = ["name",
                       "location_id$L2",
                       "location_id$L3",
                       "location_id$L4",
                       "location_id$addr_postcode",
                       ]

        filter_widgets = [
            S3TextFilter(text_fields,
                         label = T("Search"),
                         ),
            S3LocationFilter("location_id",
                             levels = ("L1", "L2", "L3", "L4"),
                             bigtable = True,
                             translate = False,
                             ),
            S3OptionsFilter("service_site.service_id",
                            label = T("Services"),
                            options = lambda: s3_get_filter_opts("org_service"),
                            cols = 1,
                            hidden = True,
                            ),
            ]
        if is_org_group_admin:
            binary_tag_opts = OrderedDict([("Y", T("Yes")), ("N", T("No"))])
            filter_widgets.extend([
                S3OptionsFilter("organisation_id$requester.value",
                                label = T("Can order equipment"),
                                options = binary_tag_opts,
                                hidden = True,
                                ),
                S3OptionsFilter("organisation_id$organisation_type__link.organisation_type_id",
                                hidden = True,
                                options = lambda: s3_get_filter_opts("org_organisation_type",
                                                                     translate = True,
                                                                     ),
                                ),
                ])
            if r.method == "report":
                filter_widgets.extend([
                    S3OptionsFilter("organisation_id$project_organisation.project_id",
                                    options = lambda: s3_get_filter_opts("project_project"),
                                    hidden = True,
                                    ),
                    S3OptionsFilter("public.value",
                                    label = T("In Public Registry"),
                                    options = binary_tag_opts,
                                    hidden = True,
                                    ),
                    ])

        # Custom CRUD form
        visible_tags = subheadings = postprocess = None
        record = r.record
        public_view = r.tablename == "org_facility" and \
                        (not record or
                         not auth.s3_has_permission("update", r.table, record_id=record.id))
        if public_view:
            crud_fields = ["name",
                           S3SQLInlineLink(
                                "facility_type",
                                label = T("Facility Type"),
                                field = "facility_type_id",
                                widget = "groupedopts",
                                cols = 3,
                                ),
                           "location_id",
                           (T("Opening Hours"), "opening_times"),
                           "site_details.service_mode_id", # not showing - why?
                           S3SQLInlineLink(
                                "service",
                                label = T("Services"),
                                field = "service_id",
                                widget = "groupedopts",
                                cols = 1,
                                ),
                           (T("Telephone"), "phone1"),
                           "email",
                           "website",
                           (T("Appointments via"), "site_details.booking_mode_id"), # not showing - why?
                           "comments",
                           ]
        else:
            organisation = obsolete = services = documents = None

            resource = r.resource
            if r.tablename == "org_facility":
                # Primary controller
                fresource = resource
                record_id = r.id
                obsolete = None
            elif r.tablename == "org_organisation" and \
                 r.component_name == "facility":
                # Facility tab of organisation
                fresource = resource.components.get("facility")
                record_id = r.component_id
                obsolete = "obsolete"
            else:
                # Other view
                fresource = record_id = None
                obsolete = None

            if fresource:
                table = fresource.table

                # Inline service selector and documents
                services = S3SQLInlineLink(
                                "service",
                                label = T("Services"),
                                field = "service_id",
                                widget = "groupedopts",
                                cols = 1,
                                )
                documents = S3SQLInlineComponent(
                                "document",
                                name = "file",
                                label = T("Documents"),
                                fields = ["name", "file", "comments"],
                                filterby = {"field": "file",
                                            "options": "",
                                            "invert": True,
                                            },
                                )

                from .helpers import configure_workflow_tags
                if is_org_group_admin:
                    # Show organisation
                    organisation = "organisation_id"

                    # Workflow tags
                    if record_id:
                        visible_tags = configure_workflow_tags(fresource,
                                                               role = "approver",
                                                               record_id = record_id,
                                                               )
                else:
                    # Add Intros for services and documents
                    services = S3WithIntro(services,
                                           intro = ("org",
                                                    "facility",
                                                    "SiteServiceIntro",
                                                    ),
                                           )
                    documents = S3WithIntro(documents,
                                            intro = ("org",
                                                     "facility",
                                                     "SiteDocumentsIntro",
                                                     ),
                                            )
                    # Workflow tags
                    if record_id:
                        visible_tags = configure_workflow_tags(fresource,
                                                               role = "applicant",
                                                               record_id = record_id,
                                                               )

            crud_fields = [organisation,
                           # -- Facility
                           "name",
                           S3SQLInlineLink(
                                "facility_type",
                                label = T("Facility Type"),
                                field = "facility_type_id",
                                widget = "groupedopts",
                                cols = 3,
                                ),
                           # -- Address
                           "location_id",
                           # -- Service Offer
                           (T("Opening Hours"), "opening_times"),
                           "site_details.service_mode_id",
                           services,
                           # -- Appointments and Contact
                           (T("Telephone"), "phone1"),
                           "email",
                           "website",
                           (T("Appointments via"), "site_details.booking_mode_id"),
                           "comments",
                           # -- Administrative
                           documents,
                           obsolete,
                           ]
            subheadings = {"name": T("Facility"),
                           "location_id": T("Address"),
                           "opening_times": T("Service Offer"),
                           "phone1": T("Contact and Appointments"),
                           "filedocument": T("Administrative"),
                           }

            if visible_tags:
                # Append workflow tags in separate section
                crud_fields.extend(visible_tags)
                fname = visible_tags[0][1].replace(".", "_")
                subheadings[fname] = T("Approval and Publication")

                # Add postprocess to update workflow statuses
                postprocess = facility_postprocess

        s3db.configure(tablename,
                       crud_form = S3SQLCustomForm(*crud_fields,
                                                   postprocess = postprocess,
                                                   ),
                       subheadings = subheadings,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

        # Report options
        if r.method == "report":
            axes = ["organisation_id",
                    "location_id$L3",
                    "location_id$L2",
                    "location_id$L1",
                    "service_site.service_id",
                    (T("Project"), "organisation_id$project.name"),
                    (T("Organization Group"), "organisation_id$group_membership.group_id"),
                    (T("Requested Items"), "req.req_item.item_id"),
                    ]

            report_options = {
                "rows": axes,
                "cols": axes,
                "fact": [(T("Number of Facilities"), "count(id)"),
                         (T("List of Facilities"), "list(name)"),
                        ],
                "defaults": {"rows": "location_id$L2",
                             "cols": None,
                             "fact": "count(id)",
                             "totals": True,
                             },
                }

            s3db.configure(tablename,
                           report_options = report_options,
                           )

    settings.customise_org_facility_resource = customise_org_facility_resource

    # -------------------------------------------------------------------------
    def customise_org_facility_controller(**attr):

        s3 = current.response.s3

        auth = current.auth
        is_org_group_admin = auth.s3_has_role("ORG_GROUP_ADMIN")

        # Load model for default CRUD strings
        current.s3db.table("org_facility")

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            s3db = current.s3db

            resource = r.resource
            table = resource.table
            record = r.record

            if not record:
                # Filter out defunct facilities
                resource.add_filter(FS("obsolete") == False)

                # Open read-view first, even if permitted to edit
                settings.ui.open_read_first = True

                if is_org_group_admin and r.method == "report":

                    s3.crud_strings.org_facility.title_report = T("Facilities Statistics")

                else:

                    # Filter by public-tag
                    get_vars = r.get_vars
                    pending = get_vars.get("$$pending")
                    if is_org_group_admin and pending == "1":
                        resource.add_filter(FS("public.value") == "N")
                        s3.crud_strings.org_facility.title_list = T("Unapproved Test Stations")

                    else:
                        resource.add_filter(FS("public.value") == "Y")
                        s3.crud_strings.org_facility.title_list = T("Find Test Station")

                        # No Side Menu
                        current.menu.options = None

                        # Filter list by project code
                        # - re-use last used $$code filter of this session
                        # - default to original subset for consistency in bookmarks/links
                        session_s3 = current.session.s3
                        default_filter = session_s3.get("rlp_facility_filter", "TESTS-SCHOOLS")
                        code = r.get_vars.get("$$code", default_filter)
                        if code:
                            session_s3.rlp_facility_filter = code
                            query = FS("~.organisation_id$project.code") == code
                            resource.add_filter(query)
                            if code == "TESTS-SCHOOLS":
                                s3.crud_strings.org_facility.title_list = T("Test Stations for School and Child Care Staff")
                            elif code == "TESTS-PUBLIC":
                                s3.crud_strings.org_facility.title_list = T("Test Stations for Everybody")

            elif r.representation == "plain":
                # Bypass REST method, return map popup directly
                from .helpers import facility_map_popup
                result = {"bypass": True,
                          "output": facility_map_popup(record),
                          }
            else:
                # Read view

                # No facility details editable here except comments
                for fn in table.fields:
                    if fn != "comments":
                        table[fn].writable = False

                # No side menu except for OrgGroupAdmin
                if not is_org_group_admin:
                    current.menu.options = None

                if not is_org_group_admin and \
                   not auth.s3_has_role("ORG_ADMIN", for_pe=record.pe_id):

                    s3.hide_last_update = True

                    field = table.obsolete
                    field.readable = field.writable = False

                    field = table.organisation_id
                    field.represent = s3db.org_OrganisationRepresent(show_link=False)

            resource.configure(summary = ({"name": "table",
                                           "label": "Table",
                                           "widgets": [{"method": "datatable"}]
                                           },
                                          {"name": "map",
                                           "label": "Map",
                                           "widgets": [{"method": "map", "ajax_init": True}],
                                           },
                                          ),
                               insertable = False,
                               deletable = False,
                               )

            return result
        s3.prep = prep

        standard_postp = s3.postp
        def postp(r, output):

            if r.representation == "plain" and r.record:
                # Prevent standard postp rewriting output
                pass
            elif callable(standard_postp):
                output = standard_postp(r, output)

            if not is_org_group_admin and \
               r.record and isinstance(output, dict):
                # Override list-button to go to summary
                buttons = output.get("buttons")
                if isinstance(buttons, dict) and "list_btn" in buttons:
                    from s3 import S3CRUD
                    summary = r.url(method="summary", id="", component="")
                    buttons["list_btn"] = S3CRUD.crud_button(label = T("List Facilities"),
                                                             _href = summary,
                                                             )
            return output
        s3.postp = postp

        # No rheader
        attr["rheader"] = None

        return attr

    settings.customise_org_facility_controller = customise_org_facility_controller

    # -------------------------------------------------------------------------
    def customise_project_project_resource(r, tablename):

        s3db = current.s3db

        # Expose code field
        table = s3db.project_project
        field = table.code
        field.readable = field.writable = True

        # Tags as filtered components (for embedding in form)
        s3db.add_components("project_project",
                            project_project_tag = ({"name": "apply",
                                                    "joinby": "project_id",
                                                    "filterby": {"tag": "APPLY"},
                                                    "multiple": False,
                                                    },
                                                   {"name": "stats",
                                                    "joinby": "project_id",
                                                    "filterby": {"tag": "STATS"},
                                                    "multiple": False,
                                                    },
                                                   ),
                            )

        from s3 import S3SQLCustomForm, \
                       S3TextFilter, \
                       S3OptionsFilter

        # Custom CRUD Form
        crud_fields = ["organisation_id",
                       "name",
                       (T("Code"), "code"),
                       "description",
                       (T("Provider Self-Registration"), "apply.value"),
                       (T("Test Results Statistics"), "stats.value"),
                       "comments",
                       ]

        # Custom list fields
        list_fields = ["id",
                       "organisation_id",
                       "name",
                       (T("Code"), "code"),
                       ]

        # Custom filters
        filter_widgets = [S3TextFilter(["name",
                                        "code",
                                        ],
                                       label = T("Search"),
                                       ),
                          S3OptionsFilter("organisation_id",
                                          ),
                          ]

        s3db.configure("project_project",
                       crud_form = S3SQLCustomForm(*crud_fields),
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_project_project_resource = customise_project_project_resource

    # -------------------------------------------------------------------------
    def customise_project_project_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            resource = r.resource

            # Configure binary tags
            from .helpers import configure_binary_tags
            configure_binary_tags(resource, ("apply", "stats"))

            if r.component_name == "organisation":

                table = r.component.table
                field = table.amount
                field.readable = field.writable = False

                field = table.currency
                field.readable = field.writable = False

            return result
        s3.prep = prep

        # Custom rheader
        from .rheaders import rlpptm_project_rheader
        attr["rheader"] = rlpptm_project_rheader

        return attr

    settings.customise_project_project_controller = customise_project_project_controller

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

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
    def customise_inv_recv_resource(r, tablename):

        s3db = current.s3db

        table = s3db.inv_recv

        # Custom label for req_ref
        from .requests import ShipmentCodeRepresent
        field = table.req_ref
        field.label = T("Order No.")
        field.represent = ShipmentCodeRepresent("req_req", "req_ref")

        # We don't use send_ref
        #field = table.send_ref
        #field.represent = lambda v, row=None: B(v if v else "-")

        # Don't show type in site representation
        field = table.site_id
        field.represent = s3db.org_SiteRepresent(show_link = True,
                                                 show_type = False,
                                                 )

        # Custom label for from_site_id, don't show link or type
        field = table.from_site_id
        field.label = T("Distribution Center")
        field.readable = True
        field.writable = False
        field.represent = s3db.org_SiteRepresent(show_link = False,
                                                 show_type = False,
                                                 )

        # Color-coded status representation
        from s3 import S3PriorityRepresent
        field = table.status
        status_opts = s3db.inv_ship_status
        status_labels = s3db.inv_shipment_status_labels
        field.represent = S3PriorityRepresent(status_labels,
                                              {status_opts["IN_PROCESS"]: "lightblue",
                                               status_opts["RECEIVED"]: "green",
                                               status_opts["SENT"]: "amber",
                                               status_opts["CANCEL"]: "black",
                                               status_opts["RETURNING"]: "red",
                                               }).represent

        if r.tablename == "inv_recv" and not r.component:
            if r.interactive:
                from s3 import S3SQLCustomForm
                crud_fields = ["req_ref",
                               #"send_ref",
                               "site_id",
                               "from_site_id",
                               "status",
                               "recipient_id",
                               "date",
                               "comments",
                               ]
                s3db.configure("inv_recv",
                               crud_form = S3SQLCustomForm(*crud_fields),
                               )

            list_fields = ["req_ref",
                           #"send_ref",
                           "site_id",
                           "from_site_id",
                           "date",
                           "status",
                           ]

            s3db.configure("inv_recv",
                        list_fields = list_fields,
                        )

    settings.customise_inv_recv_resource = customise_inv_recv_resource

    # -------------------------------------------------------------------------
    def customise_inv_recv_controller(**attr):

        db = current.db

        auth = current.auth
        s3db = current.s3db

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            resource = r.resource
            table = resource.table

            component = r.component

            if not component:

                # Hide unused fields
                unused = ("type",
                          "organisation_id",
                          "purchase_ref",
                          "recv_ref",
                          )
                for fn in unused:
                    field = table[fn]
                    field.readable = field.writable = False

                field = table.recipient_id
                field.widget = None
                record = r.record
                if record and record.recipient_id:
                    accepted_recipients = {record.recipient_id}
                else:
                    accepted_recipients = set()
                user_person_id = auth.s3_logged_in_person()
                if user_person_id:
                    field.default = user_person_id
                    accepted_recipients.add(user_person_id)
                dbset = db(s3db.pr_person.id.belongs(accepted_recipients))
                field.requires = IS_ONE_OF(dbset, "pr_person.id", field.represent)

                if r.interactive:
                    from .requests import recv_filter_widgets
                    resource.configure(filter_widgets = recv_filter_widgets())

            elif component.tablename == "inv_track_item":

                itable = component.table

                field = itable.item_id
                field.writable = False

                # Use custom form
                from s3 import S3SQLCustomForm
                crud_fields = ["item_id",
                               "item_pack_id",
                               "quantity",
                               "recv_quantity"
                               ]

                # Custom list fields
                list_fields = ["item_id",
                               "item_pack_id",
                               "quantity",
                               "recv_quantity",
                               "status",
                               ]

                component.configure(crud_form = S3SQLCustomForm(*crud_fields),
                                    list_fields = list_fields,
                                    )
            return result
        s3.prep = prep

        from .rheaders import rlpptm_inv_rheader
        attr["rheader"] = rlpptm_inv_rheader

        return attr

    settings.customise_inv_recv_controller = customise_inv_recv_controller

    # -------------------------------------------------------------------------
    def customise_inv_send_resource(r, tablename):

        db = current.db
        s3db = current.s3db

        table = s3db.inv_send

        from .requests import ShipmentCodeRepresent

        # Custom representation of req_ref
        field = table.req_ref
        field.label = T("Order No.")
        if r.representation == "wws":
            field.represent = lambda v, row=None: v if v else "-"
        else:
            field.represent = ShipmentCodeRepresent("req_req", "req_ref")

        # Sending site is required, must not be obsolete, +custom label
        field = table.site_id
        field.label = T("Distribution Center")
        field.requires = IS_ONE_OF(db, "org_site.site_id",
                                   field.represent,
                                   instance_types = ("inv_warehouse",),
                                   not_filterby = "obsolete",
                                   not_filter_opts = (True,),
                                   )
        field.represent = s3db.org_SiteRepresent(show_link = False,
                                                 show_type = False,
                                                 )

        # Recipient site is required, must be org_facility
        field = table.to_site_id
        field.requires = IS_ONE_OF(db, "org_site.site_id",
                                   field.represent,
                                   instance_types = ("org_facility",),
                                   sort = True,
                                   )
        field.represent = s3db.org_SiteRepresent(show_link = True,
                                                 show_type = False,
                                                 )

        # Color-coded status representation
        from s3 import S3PriorityRepresent
        field = table.status
        status_opts = s3db.inv_ship_status
        status_labels = s3db.inv_shipment_status_labels
        field.represent = S3PriorityRepresent(status_labels,
                                              {status_opts["IN_PROCESS"]: "lightblue",
                                               status_opts["RECEIVED"]: "green",
                                               status_opts["SENT"]: "amber",
                                               status_opts["CANCEL"]: "black",
                                               status_opts["RETURNING"]: "red",
                                               }).represent

        # We don't use send_ref
        field = table.send_ref
        field.readable = field.writable = False
        #field.represent = ShipmentCodeRepresent("inv_send", "send_ref",
        #                                        show_link = False,
        #                                        )

        list_fields = ["id",
                       "req_ref",
                       #"send_ref",
                       "date",
                       "site_id",
                       "to_site_id",
                       "status",
                       ]

        s3db.configure("inv_send",
                       list_fields = list_fields,
                       )

        # Do not check for site_id (unused)
        s3db.clear_config("inv_send", "onvalidation")

        if r.method == "report":
            axes = [(T("Orderer"), "to_site_id"),
                    "to_site_id$location_id$L3",
                    "to_site_id$location_id$L2",
                    "to_site_id$location_id$L1",
                    (T("Shipment Items"), "track_item.item_id"),
                    (T("Distribution Center"), "site_id"),
                    "status",
                    ]

            report_options = {
                "rows": axes,
                "cols": axes,
                "fact": [(T("Number of Shipments"), "count(id)"),
                         (T("Number of Items"), "count(track_item.id)"),
                         (T("Sent Quantity"), "sum(track_item.quantity)"),
                        ],
                "defaults": {"rows": "track_item.item_id",
                             "cols": "status",
                             "fact": "sum(track_item.quantity)",
                             "totals": True,
                             },
                }

            s3db.configure(tablename,
                           report_options = report_options,
                           )

    settings.customise_inv_send_resource = customise_inv_send_resource

    # -------------------------------------------------------------------------
    def customise_inv_send_controller(**attr):

        db = current.db

        auth = current.auth
        s3db = current.s3db

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            resource = r.resource
            table = resource.table

            record = r.record
            component = r.component

            if r.method == "report":
                s3.crud_strings[resource.tablename].title_report = T("Shipments Statistics")

            if not component:

                # Hide unused fields
                unused = (#"site_id",
                          "organisation_id",
                          "type",
                          "driver_name",
                          "driver_phone",
                          "vehicle_plate_no",
                          "time_out",
                          "delivery_date",
                          )
                for fn in unused:
                    field = table[fn]
                    field.readable = field.writable = False

                # Shipment reference must be editable while the shipment
                # is still editable (but we don't use send_ref at all currently)
                field.readable = field.writable = False
                #field = table.send_ref
                #field.readable = field.writable = True
                #field.requires = IS_NOT_ONE_OF(db, "inv_send.send_ref",
                #                               error_message = T("Specify a unique reference number"),
                #                               )

                # Request number, on the other hand, should not be editable
                field = table.req_ref
                field.readable = bool(record)
                field.writable = False

                # Sender is always the current user
                # => allow editing only if sender_id is missing
                field = table.sender_id
                field.widget = None
                record = r.record
                if record and record.sender_id:
                    accepted_senders = {record.sender_id}
                else:
                    accepted_senders = set()
                user_person_id = auth.s3_logged_in_person()
                if user_person_id:
                    field.default = user_person_id
                    accepted_senders.add(user_person_id)
                dbset = db(s3db.pr_person.id.belongs(accepted_senders))
                field.requires = IS_ONE_OF(dbset, "pr_person.id", field.represent)

                # Recipient should already have been set from request
                # => allow editing only that hasn't happened yet
                field = table.recipient_id
                # TODO allow editing but look up acceptable recipients
                #      from organisation of the receiving site
                field.writable = False
                field.readable = record and record.recipient_id
                field.widget = None

                if r.interactive:
                    from .requests import send_filter_widgets
                    resource.configure(filter_widgets = send_filter_widgets())

            elif component.tablename == "inv_track_item":

                itable = component.table

                field = itable.item_id
                field.readable = field.writable = True

                if r.component_id:
                    # If this item is linked to a request item, don't allow
                    # to switch to another supply item
                    query = (itable.id == r.component_id)
                    item = db(query).select(itable.req_item_id,
                                            limitby = (0, 1),
                                            ).first()
                    if item and item.req_item_id:
                        field.writable = False

                    # ...however, the item quantity can still be adjusted
                    # => override IS_AVAILABLE_QUANTITY here as we don't
                    #    have an inventory item to check against
                    field = itable.quantity
                    field.requires = IS_FLOAT_AMOUNT(0)

                # Use custom form
                from s3 import S3SQLCustomForm
                crud_fields = ["item_id",
                               "item_pack_id",
                               "quantity",
                               ]

                # Custom list fields
                list_fields = ["item_id",
                               "item_pack_id",
                               "quantity",
                               "recv_quantity",
                               "status",
                               ]

                component.configure(crud_form = S3SQLCustomForm(*crud_fields),
                                    list_fields = list_fields,
                                    )

            if r.interactive and not record and auth.s3_has_role("SUPPLY_COORDINATOR"):
                # Configure WWS export format
                export_formats = list(settings.get_ui_export_formats())
                export_formats.append(("wws", "fa fa-shopping-cart", T("CoronaWWS")))
                s3.formats["wws"] = r.url(method="", vars={"mcomponents": "track_item"})
                settings.ui.export_formats = export_formats

            return result
        s3.prep = prep

        standard_postp = s3.postp
        def postp(r, output):

            # Call standard postp if on component tab
            if r.component and callable(standard_postp):
                output = standard_postp(r, output)

            if r.representation == "wws":
                # Deliver as attachment rather than as page content
                from gluon.contenttype import contenttype

                now = current.request.utcnow.strftime("%Y%m%d%H%M%S")
                filename = "ship%s.wws" % now
                disposition = "attachment; filename=\"%s\"" % filename

                response = current.response
                response.headers["Content-Type"] = contenttype(".xml")
                response.headers["Content-disposition"] = disposition

            return output
        s3.postp = postp

        from .rheaders import rlpptm_inv_rheader
        attr["rheader"] = rlpptm_inv_rheader

        return attr

    settings.customise_inv_send_controller = customise_inv_send_controller

    # -------------------------------------------------------------------------
    def inv_track_item_onaccept(form):
        """
           Custom-onaccept for inv_track_item
           - based on standard inv_track_item_onaccept, but without the
             stock item updates and adjustments
        """

        # Get record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        db = current.db
        s3db = current.s3db

        # Look up the track item record if not in form
        ttable = s3db.inv_track_item
        try:
            record = form.record
        except AttributeError:
            record = None
        if not record:
            record = db(ttable.id == record_id).select(ttable.id,
                                                       ttable.status,
                                                       ttable.req_item_id,
                                                       ttable.recv_quantity,
                                                       ttable.item_pack_id,
                                                       limitby = (0, 1),
                                                       ).first()
        if not record:
            return

        # Set send_ref in recv_record
        send_id = form_vars.get("send_id")
        recv_id = form_vars.get("recv_id")
        recv_update = {}

        if send_id and recv_id:
            # Get the send_ref
            stable = s3db.inv_send
            send = db(stable.id == send_id).select(stable.send_ref,
                                                   limitby = (0, 1)
                                                   ).first().send_ref
            # Note the send_ref for recv-update (we do that later)
            recv_update["send_ref"] = send.send_ref

        # Update the request
        rrtable = s3db.req_req
        ritable = s3db.req_req_item
        iptable = db.supply_item_pack

        # If this item is linked to a request, then copy the req_ref to the send item
        req_item_id = record.req_item_id
        req = req_item = None
        if req_item_id:

            # Look up the request item
            left = rrtable.on(rrtable.id == ritable.req_id)
            row = db(ritable.id == req_item_id).select(ritable.id,
                                                       ritable.quantity_fulfil,
                                                       ritable.item_pack_id,
                                                       rrtable.id,
                                                       rrtable.req_ref,
                                                       left = left,
                                                       limitby = (0, 1),
                                                       ).first()
            if row:
                req = row.req_req
                req_item = row.req_req_item
                recv_update["req_ref"] = req.req_ref

        # Update the recv-record with send and req references
        if recv_id and recv_update:
            rtable = s3db.inv_recv
            db(rtable.id == recv_id).update(**recv_update)

        # When item status is UNLOADING, update the request
        from s3db.inv import TRACK_STATUS_UNLOADING, TRACK_STATUS_ARRIVED
        recv_quantity = record.recv_quantity
        if record.status == TRACK_STATUS_UNLOADING:

            if req_item and recv_quantity:
                # Update the fulfilled quantity of the req item
                req_pack_id = req_item.item_pack_id
                rcv_pack_id = record.item_pack_id
                query = iptable.id.belongs((req_pack_id, rcv_pack_id))
                packs = db(query).select(iptable.id,
                                         iptable.quantity,
                                         limitby = (0, 2),
                                         ).as_dict(key="id")
                req_pack_quantity = packs.get(req_pack_id)
                rcv_pack_quantity = packs.get(rcv_pack_id)

                if req_pack_quantity and rcv_pack_quantity:
                    quantity_fulfil = s3db.supply_item_add(req_item.quantity_fulfil,
                                                           req_pack_quantity,
                                                           recv_quantity,
                                                           rcv_pack_quantity,
                                                           )
                    req_item.update_record(quantity_fulfil = quantity_fulfil)

                # Update the request status
                s3db.req_update_status(req.id)

            # Update the track item status to ARRIVED
            db(ttable.id == record_id).update(status = TRACK_STATUS_ARRIVED)

    # -------------------------------------------------------------------------
    def customise_inv_track_item_resource(r, tablename):

        s3db = current.s3db

        table = s3db.inv_track_item

        # Item selector using dropdown not autocomplete
        field = table.item_id
        field.widget = None
        field.comment = None

        field = table.send_id
        field.label = T("Shipment")
        field.represent = S3Represent(lookup = "inv_send",
                                      fields = ["req_ref"],
                                      #fields = ["send_ref"], # we don't use send_ref
                                      show_link = True,
                                      )

        # Custom label for Pack
        field = table.item_pack_id
        field.label = T("Order Unit")

        # Custom list fields
        resource = r.resource
        if resource.tablename == "supply_item":

            # Custom form for record view (read-only)
            field = table.recv_quantity
            field.readable = True
            from s3 import S3SQLCustomForm
            crud_form = S3SQLCustomForm("item_id",
                                        "send_id",
                                        "item_pack_id",
                                        "quantity",
                                        "recv_quantity",
                                        "status",
                                        )

            # List fields
            list_fields = ["item_id",
                           "send_id",
                           "send_id$date",
                           "send_id$to_site_id",
                           "item_pack_id",
                           "quantity",
                           "recv_quantity",
                           "status",
                           ]

            # Reconfigure - always r/o in this view
            s3db.configure("inv_track_item",
                           crud_form = crud_form,
                           list_fields = list_fields,
                           insertable = False,
                           editable = False,
                           deletable = False,
                           )

        # Override standard-onaccept to prevent inventory updates
        s3db.configure("inv_track_item",
                       onaccept = inv_track_item_onaccept,
                       )

    settings.customise_inv_track_item_resource = customise_inv_track_item_resource

    # -------------------------------------------------------------------------
    def customise_inv_warehouse_resource(r, tablename):

        T = current.T

        s3db = current.s3db

        table = s3db.inv_warehouse

        # Remove Add-links for organisation and warehouse type
        field = table.organisation_id
        field.comment = None
        field = table.warehouse_type_id
        field.comment = None

        # Custom label, represent and tooltip for obsolete-flag
        field = table.obsolete
        field.readable = field.writable = True
        field.label = T("Defunct")
        field.represent = lambda v, row=None: ICON("remove") if v else ""
        field.comment = DIV(_class="tooltip",
                            _title="%s|%s" % (T("Defunct"),
                                              T("Please mark this field when the facility is no longer in operation"),
                                              ),
                            )

        if r.interactive:

            # Configure location selector and geocoder
            from s3 import S3LocationSelector
            field = table.location_id
            field.widget = S3LocationSelector(levels = ("L1", "L2", "L3", "L4"),
                                              required_levels = ("L1", "L2", "L3"),
                                              show_address = True,
                                              show_postcode = True,
                                              show_map = True,
                                              )
            current.response.s3.scripts.append("/%s/static/themes/RLP/js/geocoderPlugin.js" % r.application)

            # Custom CRUD-Form
            from s3 import S3SQLCustomForm
            crud_fields = ["organisation_id",
                           "name",
                           "code",
                           "warehouse_type_id",
                           "location_id",
                           "email",
                           "phone1",
                           "phone2",
                           "comments",
                           "obsolete",
                           ]

            s3db.configure("inv_warehouse",
                           crud_form = S3SQLCustomForm(*crud_fields),
                           )

        # Custom list fields
        list_fields = ["organisation_id",
                       "name",
                       "code",
                       "warehouse_type_id",
                       "location_id",
                       "email",
                       "phone1",
                       "obsolete",
                       ]
        s3db.configure("inv_warehouse",
                       list_fields = list_fields,
                       deletable = False,
                       )

    settings.customise_inv_warehouse_resource = customise_inv_warehouse_resource

    # -------------------------------------------------------------------------
    def customise_inv_warehouse_controller(**attr):

        s3 = current.response.s3

        #standard_postp = s3.postp
        #def postp(r, output):
        #    if callable(standard_postp):
        #        output = standard_postp(r, output)
        #    return output
        #s3.postp = postp

        # Override standard postp
        s3.postp = None

        from .rheaders import rlpptm_inv_rheader
        attr["rheader"] = rlpptm_inv_rheader

        return attr

    settings.customise_inv_warehouse_controller = customise_inv_warehouse_controller

    # -------------------------------------------------------------------------
    def customise_req_req_resource(r, tablename):

        db = current.db

        auth = current.auth
        s3db = current.s3db

        table = s3db.req_req

        field = table.req_ref
        field.label = T("Order No.")
        #field.represent = lambda v, row=None: v if v else "-"

        # Don't show facility type
        field = table.site_id
        field.represent = s3db.org_SiteRepresent(show_link = True,
                                                 show_type = False,
                                                 )

        if auth.s3_has_role("SUPPLY_COORDINATOR"):
            # Custom method to register a shipment
            from .requests import RegisterShipment
            s3db.set_method("req", "req",
                            method = "ship",
                            action = RegisterShipment,
                            )
            # Show contact details for requester
            from .helpers import ContactRepresent
            field = table.requester_id
            field.represent = ContactRepresent(show_email = True,
                                               show_phone = True,
                                               show_link = False,
                                               )
        else:
            # Simpler represent of requester, no link
            field = table.requester_id
            field.represent = s3db.pr_PersonRepresent(show_link = False,
                                                      )

        # Filter out obsolete items
        ritable = s3db.req_req_item
        sitable = s3db.supply_item
        field = ritable.item_id
        dbset = db((sitable.obsolete == False) | (sitable.obsolete == None))
        field.requires = IS_ONE_OF(dbset, "supply_item.id",
                                   field.represent,
                                   sort = True,
                                   )

        # Customise error message for ordered quantity
        field = ritable.quantity
        field.requires = IS_FLOAT_AMOUNT(minimum = 1.0,
                                         error_message = T("Minimum quantity is %(min)s"),
                                         )

        # Custom label for Pack
        field = ritable.item_pack_id
        field.label = T("Order Unit")

        if r.method == "report":
            axes = [(T("Orderer"), "site_id"),
                    "site_id$location_id$L3",
                    "site_id$location_id$L2",
                    "site_id$location_id$L1",
                    (T("Requested Items"), "req_item.item_id"),
                    "transit_status",
                    "fulfil_status",
                    ]

            report_options = {
                "rows": axes,
                "cols": axes,
                "fact": [(T("Number of Requests"), "count(id)"),
                         (T("Number of Items"), "count(req_item.id)"),
                         (T("Requested Quantity"), "sum(req_item.quantity)"),
                        ],
                "defaults": {"rows": "site_id$location_id$L2",
                             "cols": None,
                             "fact": "count(id)",
                             "totals": True,
                             },
                }

            s3db.configure(tablename,
                           report_options = report_options,
                           )

    settings.customise_req_req_resource = customise_req_req_resource

    # -------------------------------------------------------------------------
    def customise_req_req_controller(**attr):

        db = current.db
        s3db = current.s3db
        auth = current.auth

        has_role = auth.s3_has_role

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):

            r.get_vars["type"] = "1"

            is_supply_coordinator = has_role("SUPPLY_COORDINATOR")

            # User must be either SUPPLY_COORDINATOR or ORG_ADMIN of a
            # requester organisation to access this controller
            if not is_supply_coordinator:
                from .requests import get_managed_requester_orgs
                requester_orgs = get_managed_requester_orgs(cache=False)
                if not requester_orgs:
                    r.unauthorised()
            else:
                requester_orgs = None

            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            resource = r.resource
            table = resource.table

            # Date is only writable for ADMIN
            field = table.date
            field.default = current.request.utcnow
            field.writable = has_role("AMDIN")

            record = r.record
            if record:
                # Check if there is any shipment for this request
                ritable = s3db.req_req_item
                titable = s3db.inv_track_item
                join = titable.on((titable.req_item_id == ritable.id) & \
                                  (titable.deleted == False))
                query = (ritable.req_id == r.id) & \
                        (ritable.deleted == False)
                item = db(query).select(titable.id, join=join, limitby=(0, 1)).first()

                if item:
                    # Cannot edit the request
                    resource.configure(editable = False, deletable = False)
                    if r.component_name == "req_item":
                        # ...nor its items
                        r.component.configure(insertable = False,
                                              editable = False,
                                              deletable = False,
                                              )
            if not r.component:
                if r.interactive:
                    # Hide priority, date_required and date_recv
                    field = table.priority
                    field.readable = field.writable = False
                    field = table.date_required
                    field.readable = field.writable = False
                    field = table.date_recv
                    field.readable = field.writable = False

                    if not is_supply_coordinator:
                        # Limit to sites of managed requester organisations
                        stable = s3db.org_site
                        dbset = db((stable.organisation_id.belongs(requester_orgs)) & \
                                   (stable.obsolete == False))
                        field = table.site_id
                        field.requires = IS_ONE_OF(dbset, "org_site.site_id",
                                                   field.represent,
                                                   )
                        # If only one site selectable, set default and make r/o
                        sites = dbset.select(stable.site_id, limitby=(0, 2))
                        if len(sites) == 1:
                            field.default = sites.first().site_id
                            field.writable = False
                        elif not sites:
                            resource.configure(insertable = False)
                    else:
                        resource.configure(insertable = False)

                    # Requester is always the current user
                    # => set as default and make r/o
                    user_person_id = auth.s3_logged_in_person()
                    if user_person_id:
                        field = table.requester_id
                        field.default = user_person_id
                        field.writable = False

                    from .requests import req_filter_widgets
                    resource.configure(filter_widgets = req_filter_widgets(),
                                       )

                # Custom list fields
                list_fields = ["id",
                               "req_ref",
                               "date",
                               "site_id",
                               (T("Details"), "details"),
                               "transit_status",
                               "fulfil_status",
                               ]

                # Reconfigure table
                resource.configure(list_fields = list_fields,
                                   )

                # Custom callback for inline items
                s3db.add_custom_callback("req_req_item",
                                         "onaccept",
                                         req_req_item_create_onaccept,
                                         method = "create",
                                         )
            return result
        s3.prep = prep

        standard_postp = s3.postp
        def postp(r, output):

            # Call standard postp if on component tab
            if r.component and callable(standard_postp):
                output = standard_postp(r, output)

            resource = r.resource

            table = resource.table
            from s3db.req import REQ_STATUS_COMPLETE, REQ_STATUS_CANCEL
            request_complete = (REQ_STATUS_COMPLETE, REQ_STATUS_CANCEL)

            istable = s3db.inv_send

            from s3db.inv import SHIP_STATUS_IN_PROCESS, SHIP_STATUS_SENT
            shipment_in_process = (SHIP_STATUS_IN_PROCESS, SHIP_STATUS_SENT)

            record = r.record
            if r.interactive and isinstance(output, dict):

                # Add register-shipment action button(s)
                ritable = s3db.req_req_item

                ship_btn_label = s3_str(T("Register Shipment"))
                inject_script = False
                if record:
                    # Single record view
                    if not r.component and has_role("SUPPLY_COORDINATOR"):
                        query = (ritable.req_id == record.id) & \
                                (ritable.deleted == False)
                        item = db(query).select(ritable.id, limitby=(0, 1)).first()
                        if item and record.fulfil_status not in request_complete:
                            query = (istable.req_ref == record.req_ref) & \
                                    (istable.status.belongs(shipment_in_process)) & \
                                    (istable.deleted == False)
                            shipment = db(query).select(istable.id, limitby=(0, 1)).first()
                        else:
                            shipment = None
                        if item and not shipment:
                            from .requests import is_active
                            site_active = is_active(record.site_id)
                        else:
                            site_active = True
                        if item and not shipment and site_active:
                            ship_btn = A(T("Register Shipment"),
                                         _class = "action-btn ship-btn",
                                         _db_id = str(record.id),
                                         )
                            inject_script = True
                        else:
                            warn = None
                            if not item:
                                warn = reason = T("Requests contains no items")
                            elif not site_active:
                                warn = reason = T("Requesting site no longer active")
                            else:
                                reason = T("Shipment already in process")
                            if warn:
                                current.response.warning = warn
                            ship_btn = A(T("Register Shipment"),
                                         _class = "action-btn",
                                         _disabled = "disabled",
                                         _title = reason,
                                         )
                        if "buttons" not in output:
                            buttons = output["buttons"] = {}
                        else:
                            buttons = output["buttons"]
                        delete_btn = buttons.get("delete_btn")

                        b = [delete_btn, ship_btn] if delete_btn else [ship_btn]
                        buttons["delete_btn"] = TAG[""](*b)

                elif not r.component and not r.method:
                    # Datatable
                    stable = s3db.org_site

                    # Default action buttons (except delete)
                    from s3 import S3CRUD
                    S3CRUD.action_buttons(r, deletable =False)

                    if has_role("SUPPLY_COORDINATOR"):
                        # Can only register shipments for unfulfilled requests with
                        # no shipment currently in process or in transit, and the
                        # requesting site still active, and at least one requested item
                        left = istable.on((istable.req_ref == table.req_ref) & \
                                          (istable.status.belongs(shipment_in_process)) & \
                                          (istable.deleted == False))
                        join = [stable.on((stable.site_id == table.site_id) & \
                                          (stable.obsolete == False)),
                                ritable.on((ritable.req_id == table.id) & \
                                           (ritable.deleted == False)),
                                ]
                        query = (table.fulfil_status != REQ_STATUS_COMPLETE) & \
                                (table.fulfil_status != REQ_STATUS_CANCEL) & \
                                (istable.id == None)
                        rows = db(query).select(table.id, groupby=table.id, join=join, left=left)
                        restrict = [str(row.id) for row in rows]

                        # Register-shipment button
                        enabled = {"label": ship_btn_label,
                                   "_class": "action-btn ship-btn",
                                   "restrict": restrict,
                                   }
                        s3.actions.append(enabled)

                        # Disabled shipment-button to indicate why the action
                        # is currently disabled
                        disabled = {"label": ship_btn_label,
                                    "_class": "action-btn",
                                    "_title": s3_str(T("Shipment already in process, or not possible")),
                                    "_disabled": "disabled",
                                    "exclude": restrict,
                                    }
                        s3.actions.append(disabled)

                        # Do inject script
                        inject_script = True

                    if auth.s3_has_permission("delete", table):
                        # Requests can only be deleted while no shipment for them
                        # has been registered yet:
                        left = istable.on((istable.req_ref == table.req_ref) & \
                                          (istable.deleted == False))
                        query = auth.s3_accessible_query("delete", table) & \
                                (istable.id == None)
                        rows = db(query).select(table.id, left=left)

                        # Delete-button
                        if rows:
                            delete = {"label": s3_str(s3.crud_labels.DELETE),
                                      "url": URL(c="req", f="req", args=["[id]", "delete"]),
                                      "_class": "delete-btn",
                                      "restrict": [str(row.id) for row in rows],
                                      }
                            s3.actions.append(delete)

                if inject_script:
                    # Confirmation question
                    confirm = '''i18n.req_register_shipment="%s"''' % \
                              T("Do you want to register a shipment for this request?")
                    s3.js_global.append(confirm)

                    # Inject script for action
                    script = "/%s/static/themes/RLP/js/ship.js" % r.application
                    if script not in s3.scripts:
                        s3.scripts.append(script)

            return output
        s3.postp = postp

        from .rheaders import rlpptm_req_rheader
        attr["rheader"] = rlpptm_req_rheader

        return attr

    settings.customise_req_req_controller = customise_req_req_controller

    # -------------------------------------------------------------------------
    def req_req_item_create_onaccept(form):
        """
            Custom callback to prevent duplicate request items:
            - if the same request contains another req_item with the same
              item_id and item_pack_id that is not yet referenced by a
              shipment item, then merge the quantities and delete this
              one
        """

        # Get record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        db = current.db
        s3db = current.s3db

        table = s3db.req_req_item
        titable = s3db.inv_track_item

        left = titable.on((titable.req_item_id == table.id) & \
                          (titable.deleted == False))

        query = (table.id == record_id)
        record = db(query).select(table.id,
                                  table.req_id,
                                  table.item_id,
                                  table.item_pack_id,
                                  table.quantity,
                                  titable.id,
                                  left = left,
                                  limitby = (0, 1),
                                  ).first()
        if record and not record.inv_track_item.id:
            this = record.req_req_item
            query = (table.req_id == this.req_id) & \
                    (table.id != this.id) & \
                    (table.item_id == this.item_id) & \
                    (table.item_pack_id == this.item_pack_id) & \
                    (titable.id == None)
            other = db(query).select(table.id,
                                     table.quantity,
                                     left = left,
                                     limitby = (0, 1),
                                     ).first()
            if other:
                resource = s3db.resource("req_req_item", id=this.id)
                deleted = resource.delete()
                if deleted:
                    other.update_record(quantity = other.quantity + this.quantity)

    # -------------------------------------------------------------------------
    def customise_req_req_item_resource(r, tablename):

        s3db = current.s3db

        table = s3db.req_req_item

        quantities = ("quantity_transit",
                      "quantity_fulfil",
                      )
        for fn in quantities:
            field = table[fn]
            field.represent = lambda v: v if v is not None else "-"

        resource = r.resource
        if resource.tablename == "supply_item":
            from .requests import ShipmentCodeRepresent
            rtable = s3db.req_req
            field = rtable.req_ref
            field.represent = ShipmentCodeRepresent("req_req", "req_ref")

            list_fields = ["item_id",
                           "req_id$req_ref",
                           "req_id$site_id",
                           "item_pack_id",
                           "quantity",
                           "quantity_transit",
                           "quantity_fulfil",
                           ]
            s3db.configure("req_req_item",
                           list_fields = list_fields,
                           insertable = False,
                           editable = False,
                           deletable = False,
                           )

        # Use drop-down for supply item, not autocomplete
        field = table.item_id
        field.widget = None

        # Custom label for Pack
        field = table.item_pack_id
        field.label = T("Order Unit")

        s3db.add_custom_callback("req_req_item",
                                 "onaccept",
                                 req_req_item_create_onaccept,
                                 method = "create",
                                 )

    settings.customise_req_req_item_resource = customise_req_req_item_resource

    # -------------------------------------------------------------------------
    def customise_supply_item_resource(r, tablename):

        s3db = current.s3db

        table = s3db.supply_item

        unused = ("item_category_id",
                  "brand_id",
                  "kit",
                  "model",
                  "year",
                  "weight",
                  "length",
                  "width",
                  "height",
                  "volume",
                  )
        for fn in unused:
            field = table[fn]
            field.readable = field.writable = False

        # Code is required
        field = table.code
        field.requires = [IS_NOT_EMPTY(), field.requires]

        # Use a localized default for um
        field = table.um
        field.default = s3_str(T("piece"))

        # Expose obsolete-flag
        field = table.obsolete
        field.label = T("Not orderable")
        field.readable = field.writable = True
        field.represent = lambda v, row=None: ICON("remove") if v else ""

        # Filter widgets
        from s3 import S3TextFilter
        filter_widgets = [S3TextFilter(["name",
                                        "code",
                                        "comments",
                                        ],
                                       label = T("Search"),
                                       ),
                          ]
        s3db.configure("supply_item",
                       filter_widgets = filter_widgets,
                       )

    settings.customise_supply_item_resource = customise_supply_item_resource

    # -------------------------------------------------------------------------
    def customise_supply_item_controller(**attr):

        s3db = current.s3db

        s3db.add_components("supply_item",
                            inv_track_item = "item_id",
                            )

        from .rheaders import rlpptm_supply_rheader
        attr["rheader"] = rlpptm_supply_rheader

        return attr

    settings.customise_supply_item_controller = customise_supply_item_controller

    # -------------------------------------------------------------------------
    def shipping_code(prefix, site_id, field):

        # We hide the send_ref from the user, but still auto-generate one
        #if prefix == "WB":
        #    # Do not generate waybill numbers, but ask them from the user
        #    return None

        db = current.db
        if site_id:
            code = "%s-%s-" % (prefix, site_id)
        else:
            code = "%s-#-" % prefix

        number = 0
        if field:
            query = (field.like("%s%%" % code))
            ref_row = db(query).select(field,
                                       limitby = (0, 1),
                                       orderby = ~field
                                       ).first()
            if ref_row:
                ref = ref_row[field]
                try:
                    number = int(ref[-6:])
                except (ValueError, TypeError):
                    pass

        return "%s%06d" % (code, number + 1)

    settings.supply.shipping_code = shipping_code

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
        ("req", Storage(
            name_nice = T("Requests"),
            #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
            module_type = 10,
        )),
        ("inv", Storage(
            name_nice = T("Warehouses"),
            #description = "Receiving and Sending Items",
            module_type = 4
        )),
        ("supply", Storage(
            name_nice = T("Supply Chain Management"),
            #description = "Used within Inventory Management, Request Management and Asset Management",
            module_type = None, # Not displayed
        )),
    ])

# END =========================================================================
