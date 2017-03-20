# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        STDM: Social Tenure Domain Model
        http://stdm.gltn.net/
    """

    T = current.T

    settings.base.system_name = T("Social Tenure Domain Model")
    settings.base.system_name_short = T("STDM")

    # PrePopulate data
    settings.base.prepopulate += ("STDM", "default/users", "STDM/Demo")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "STDM"
    settings.ui.menu_logo = "/%s/static/themes/STDM/img/logo.png" % current.request.application

    # Authentication settings
    # Should users be allowed to register themselves?
    settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    #settings.auth.registration_requests_organisation = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    #settings.gis.countries = ("US",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True
    # Uncomment to modify the Simplify Tolerance
    settings.gis.simplify_tolerance = 0
    # Uncomment this for highly-zoomed maps showing buildings
    settings.gis.precision = 5

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar & GIS Locations)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
    #    ("ar", "العربية"),
    #    ("bs", "Bosanski"),
        ("en", "English"),
    #    ("fr", "Français"),
    #    ("de", "Deutsch"),
    #    ("el", "ελληνικά"),
        ("es", "Español"),
    #    ("it", "Italiano"),
    #    ("ja", "日本語"),
    #    ("km", "ភាសាខ្មែរ"),
    #    ("ko", "한국어"),
        ("ne", "नेपाली"),          # Nepali
        ("prs", "دری"), # Dari
    #    ("ps", "پښتو"), # Pashto
    #    ("pt", "Português"),
    #    ("pt-br", "Português (Brasil)"),
    #    ("ru", "русский"),
    #    ("tet", "Tetum"),
    #    ("tl", "Tagalog"),
    #    ("tr", "Türkçe"),
    #    ("ur", "اردو"),
    #    ("vi", "Tiếng Việt"),
    #    ("zh-cn", "中文 (简体)"),
    #    ("zh-tw", "中文 (繁體)"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    #settings.L10n.default_language = "en"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    #settings.L10n.utc_offset = "+0100"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
    # Uncomment this to Translate Layer Names
    #settings.L10n.translate_gis_layer = True
    # Uncomment this to Translate Location Names
    settings.L10n.translate_gis_location = True
    # Uncomment this for Alternate Location Names
    settings.L10n.name_alt_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    #settings.L10n.translate_org_organisation = True
    # Finance settings
    #settings.fin.currencies = {
    #    "EUR" : "Euros",
    #    "GBP" : "Great British Pounds",
    #    "USD" : "United States Dollars",
    #}
    #settings.fin.currency_default = "USD"

    # Email isn't required
    settings.pr.request_email = False
    #settings.hrm.email_required = False

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
    settings.security.policy = 4 # Controller & Function ACLs

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        s3db = current.s3db

        list_fields = ["first_name",
                       "middle_name",
                       "last_name",
                       (T("National ID"), "national_id.value"),
                       "gender",
                       "date_of_birth",
                       "person_details.marital_status",
                       (T("Telephone"), "phone.value"),
                       (T("Address"), "address.location_id$addr_street"),
                       # @ToDo: Residence Area...which is Lx
                       ]
        if current.auth.s3_has_role("INFORMAL_SETTLEMENT"):
            list_fields.insert(7, (T("Household Relation"), "group_membership.role_id"))

        from s3 import S3LocationSelector, S3SQLCustomForm, S3SQLInlineComponent

        s3db.pr_address.location_id.widget = S3LocationSelector(show_address = True,
                                                                #show_postcode = False,
                                                                show_map = False,
                                                                )

        crud_form = S3SQLCustomForm("first_name",
                                    "middle_name",
                                    "last_name",
                                    S3SQLInlineComponent("identity",
                                                         label = T("National ID"),
                                                         fields = [("", "value")],
                                                         filterby = dict(field = "type",
                                                                         options = 2,
                                                                         ),
                                                         multiple = False,
                                                         ),
                                    "gender",
                                    "date_of_birth",
                                    "person_details.marital_status",
                                    S3SQLInlineComponent("contact",
                                                         label = T("Telephone"),
                                                         fields = [("", "value")],
                                                         filterby = dict(field = "contact_method",
                                                                         options = "SMS",
                                                                         ),
                                                         multiple = False,
                                                         ),
                                    S3SQLInlineComponent("address",
                                                         label = T("Address"),
                                                         fields = [("", "location_id")],
                                                         multiple = False,
                                                         ),
                                    "comments",
                                    )

        s3db.configure("pr_person",
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3 = current.response.s3
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                if not standard_prep(r):
                    return False

            if r.component_name == "tenure_relationship":

                list_fields = ["tenure_id$spatial_unit_id",
                               "tenure_type_id",
                               ]

                current.s3db.configure("stdm_tenure_relationship",
                                       # No decent CRUD form possible
                                       insertable = False,
                                       list_fields = list_fields,
                                       )

            return True
        s3.prep = custom_prep

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -------------------------------------------------------------------------
    def customise_pr_group_resource(r, tablename):

        list_fields = [(T("Name"), "name"),
                       "comments",
                       ]

        from s3 import S3SQLCustomForm
        crud_form = S3SQLCustomForm((T("Name"), "name"),
                                    "comments",
                                    )

        current.s3db.configure("pr_group",
                               crud_form = crud_form,
                               list_fields = list_fields,
                               )

    settings.customise_pr_group_resource = customise_pr_group_resource

    # -------------------------------------------------------------------------
    def customise_pr_group_controller(**attr):

        s3 = current.response.s3
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                if not standard_prep(r):
                    return False

            if r.component_name == "tenure_relationship":

                list_fields = ["tenure_id$spatial_unit_id",
                               "tenure_type_id",
                               ]

                current.s3db.configure("stdm_tenure_relationship",
                                       # No decent CRUD form possible
                                       insertable = False,
                                       list_fields = list_fields,
                                       )

            return True
        s3.prep = custom_prep

        return attr

    settings.customise_pr_group_controller = customise_pr_group_controller

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
        #("tour", Storage(
        #    name_nice = T("Guided Tour Functionality"),
        #    module_type = None,
        #)),
        #("translate", Storage(
        #    name_nice = T("Translation Functionality"),
        #    #description = "Selective translation of strings based on module.",
        #    module_type = None,
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
        ("stdm", Storage(
            name_nice = T("Tenure"),
            #description = "Social Tenure Domain Model",
            restricted = True,
            module_type = 10,
        )),
        #("project", Storage(
        #    name_nice = T("Projects"),
        #    #description = "Tracking of Projects, Activities and Tasks",
        #    restricted = True,
        #    module_type = 2
        #)),
        #("stats", Storage(
        #    name_nice = T("Statistics"),
        #    #description = "Manages statistics",
        #    restricted = True,
        #    module_type = None,
        #)),
    ])

# END =========================================================================