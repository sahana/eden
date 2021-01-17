# -*- coding: utf-8 -*-

"""
    Application Template for Rhineland-Palatinate (RLP) Crisis Management
    - used to manage Personnel Tests for COVID-19 response

    @license MIT
"""

from collections import OrderedDict

from gluon import current, URL, DIV
from gluon.storage import Storage

from s3 import IS_ONE_OF

from .rlpgeonames import rlp_GeoNames

LSJV = "Landesamt für Soziales, Jugend und Versorgung"
ALLOWED_FORMATS = ("html", "iframe", "popup", "aadata", "json", "xls", "pdf")

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
    settings.auth.privileged_roles = {"PROGRAM_MANAGER": "PROGRAM_MANAGER",
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

            TODO
        """

        #db = current.db
        #s3db = current.s3db

        #tablename = original_tablename(table)

        realm_entity = 0

        return realm_entity

    settings.auth.realm_entity = rlpptm_realm_entity

    # -------------------------------------------------------------------------
    #def customise_auth_user_resource(r, tablename):
    #    """
    #        Configure custom register-onaccept
    #
    #        TODO Differential registration processes for Bearer/Provider orgs
    #    """
    #
    #    from .controllers import register
    #    current.s3db.configure("auth_user",
    #                           register_onaccept = register.register_onaccept,
    #                           )
    #
    #settings.customise_auth_user_resource = customise_auth_user_resource

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
    def customise_fin_voucher_resource(r, tablename):

        s3db = current.s3db

        table = s3db.fin_voucher

        field = table.comments
        field.label = T("Memoranda")
        field.comment = DIV(_class="tooltip",
                            _title="%s|%s" % (T("Memoranda"),
                                              T("Notes of the Issuer"),
                                              ),
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

            db = current.db
            s3db = current.s3db

            # Check which programs and organisations the user can issue vouchers for
            multiple, org_ids, pe_ids = s3db.fin_voucher_permitted_issuers()
            if org_ids or multiple:
                programs = s3db.fin_voucher_permitted_programs(org_ids)
            else:
                programs = None

            resource = r.resource
            if not programs or not org_ids and not multiple:
                # User is not permitted to issue vouchers for any programs/issuers
                resource.configure(insertable = False)

            else:
                table = resource.table

                # Limit the program selector to permitted+active programs
                field = table.program_id
                ptable = s3db.fin_voucher_program
                dbset = db(ptable.id.belongs(programs))
                field.requires = IS_ONE_OF(dbset, "fin_voucher_program.id",
                                           field.represent,
                                           sort = True,
                                           )
                # Hide the program selector if only one program can be chosen
                rows = dbset.select(ptable.id, limitby=(0, 2))
                if len(rows) == 1:
                    field.default = rows.first().id
                    field.writable = False

                if pe_ids:
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

            list_fields = ["program_id",
                            "signature",
                            #"bearer_dob",
                            "balance",
                            "date",
                            "valid_until",
                            "comments",
                            ]
            if settings.get_fin_voucher_personalize() == "dob":
                list_fields.insert(2, "bearer_dob")
            resource.configure(list_fields = list_fields,
                                )

            return result
        s3.prep = prep

        # Custom rheader
        from .rheaders import rlpptm_fin_rheader
        attr["rheader"] = rlpptm_fin_rheader

        return attr

    settings.customise_fin_voucher_controller = customise_fin_voucher_controller

    # -------------------------------------------------------------------------
    def customise_org_facility_controller(**attr):

        s3 = current.response.s3

        # Load model for default CRUD strings
        current.s3db.table("org_facility")

        s3.crud_strings.org_facility.title_map = T("Find Test Station")

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True


            if not r.component:

                from s3 import S3SQLCustomForm, S3SQLInlineLink, \
                               S3LocationFilter, S3TextFilter

                text_fields = ["name",
                               #"code",
                               "comments",
                               "organisation_id$name",
                               "organisation_id$acronym",
                               "location_id$L1",
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
                               "organisation_id",
                               "location_id",
                               (T("Telephone"), "phone1",),
                               (T("Opening Hours"), "opening_times"),
                               "obsolete",
                               "comments",
                               ]
                r.resource.configure(crud_form = S3SQLCustomForm(*crud_fields),
                                     filter_widgets = filter_widgets,
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

            s3db = current.s3db
            #settings = current.deployment_settings

            # Add invite-method for ORG_GROUP_ADMIN role
            from .helpers import rlpptm_InviteUserOrg
            s3db.set_method("org", "organisation",
                            method = "invite",
                            action = rlpptm_InviteUserOrg,
                            )

            if not r.component:
                if r.interactive:
                    from s3 import S3SQLCustomForm, \
                                   S3SQLInlineComponent, \
                                   S3SQLInlineLink
                    crud_fields = [S3SQLInlineLink(
                                        "group",
                                        field = "group_id",
                                        label = T("Organisation Group"),
                                        multiple = False,

                                        ),
                                   "name",
                                   "acronym",
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
                                   #"website",
                                   #"year",
                                   #"logo",
                                   "comments",
                                   ]
                    r.resource.configure(crud_form = S3SQLCustomForm(*crud_fields),
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
            module_type = None  # This item is not shown in the menu
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
            module_type = None  # No Menu
        )),
        ("errors", Storage(
            name_nice = T("Ticket Viewer"),
            #description = "Needed for Breadcrumbs",
            restricted = False,
            module_type = None  # No Menu
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
            module_type = 6,     # 6th item in the menu
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 1
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
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
        ("fin", Storage(
            name_nice = T("Finance"),
            #description = "Finance Management / Accounting",
            restricted = True,
            module_type = None,
        )),
    ])

# END =========================================================================
