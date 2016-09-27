# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

SAVE = "Save the Children"

def config(settings):
    """
        Template settings for Save the Children Philippines
    """

    T = current.T

    settings.base.system_name = T("IMS")
    settings.base.system_name_short = T("IMS")

    # PrePopulate data
    #settings.base.prepopulate = ("skeleton", "default/users")
    settings.base.prepopulate += ("SCPHIMS", "default/users")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "SCPHIMS"

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
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
    settings.gis.countries = ("PH",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = False
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

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
    #    ("es", "Español"),
    #    ("it", "Italiano"),
    #    ("ja", "日本語"),
    #    ("km", "ភាសាខ្មែរ"),
    #    ("ko", "한국어"),
    #    ("ne", "नेपाली"),          # Nepali
    #    ("prs", "دری"), # Dari
    #    ("ps", "پښتو"), # Pashto
    #    ("pt", "Português"),
    #    ("pt-br", "Português (Brasil)"),
    #    ("ru", "русский"),
    #    ("tet", "Tetum"),
        ("tl", "Tagalog"),
    #    ("tr", "Türkçe"),
    #    ("ur", "اردو"),
    #    ("vi", "Tiếng Việt"),
    #    ("zh-cn", "中文 (简体)"),
    #    ("zh-tw", "中文 (繁體)"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    #settings.L10n.default_language = "en"
    # Uncomment to Hide the language toolbar
    settings.L10n.display_toolbar = False
    # Default timezone for users
    settings.L10n.utc_offset = "+0800"
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
    #    "EUR" : "Euros",
    #    "GBP" : "Great British Pounds",
        "PHP" : "Philippine Pesos",
        "USD" : "United States Dollars",
    }
    #settings.fin.currency_default = "USD"

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

    settings.security.policy = 5 # Controller, Function & Table ACLs

    # =========================================================================
    # Documents
    #

    def customise_doc_document_resource(r, tablename):

        from s3 import S3LocationSelector, S3SQLCustomForm#, S3SQLInlineComponent

        s3db = current.s3db
        table = s3db.doc_document
        table.organisation_id.readable = table.organisation_id.writable = True
        f = table.location_id
        f.readable = f.writable = True
        f.widget = S3LocationSelector() # No Street Address

        s3db.add_components("doc_document",
                            event_event = "doc_id",
                            )

        crud_form = S3SQLCustomForm("file",
                                    "name",
                                    "url",
                                    "date",
                                    # @ToDo: Have this as an event_id dropdown
                                    #S3SQLInlineComponent("event"),
                                    "organisation_id",
                                    "location_id",
                                    "comments",
                                    )

        # Custom filters
        from s3 import S3DateFilter, \
                       S3LocationFilter, \
                       S3OptionsFilter, \
                       S3TextFilter

        filter_widgets = [
            S3TextFilter(["name",
                          "comments",
                          ],
                         label = T("Search"),
                         comment = T("Search by disaster name or comments. You can use * as wildcard."),
                         ),
            S3OptionsFilter("event.name",
                            label = T("Disaster"),
                            ),
            S3LocationFilter("location_id"),
            S3OptionsFilter("organisation_id"),
            S3DateFilter("date"),
            ]

        list_fields = ["location_id$L1",
                       "location_id$L2",
                       "location_id$L3",
                       "location_id$L4",
                       ]
        if r.controller != "event":
            list_field.append((T("Disaster"), "event.name"))
        list_fields += ["organisation_id",
                        "date",
                        "name",
                        ]

        s3db.configure("doc_document",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_doc_document_resource = customise_doc_document_resource

    def customise_doc_image_resource(r, tablename):

        from s3 import S3LocationSelector, S3SQLCustomForm#, S3SQLInlineComponent

        s3db = current.s3db
        table = s3db.doc_image
        table.location_id.widget = S3LocationSelector() # No Street Address

        s3db.add_components("doc_image",
                            event_event = "doc_id",
                            )

        crud_form = S3SQLCustomForm("file",
                                    "name",
                                    "url",
                                    "date",
                                    # @ToDo: Have this as an event_id dropdown
                                    #S3SQLInlineComponent("event"),
                                    "organisation_id",
                                    "location_id",
                                    "comments",
                                    )

        # Custom filters
        from s3 import S3DateFilter, \
                       S3LocationFilter, \
                       S3OptionsFilter, \
                       S3TextFilter

        filter_widgets = [
            S3TextFilter(["name",
                          "comments",
                          ],
                         label = T("Search"),
                         comment = T("Search by disaster name or comments. You can use * as wildcard."),
                         ),
            S3OptionsFilter("event.name",
                            label = T("Disaster"),
                            ),
            S3LocationFilter("location_id"),
            S3OptionsFilter("organisation_id"),
            S3DateFilter("date"),
            ]

        list_fields = ["location_id$L1",
                       "location_id$L2",
                       "location_id$L3",
                       "location_id$L4",
                       ]
        if r.controller != "event":
            list_field.append((T("Disaster"), "event.name"))
        list_fields += ["organisation_id",
                        "date",
                        "name",
                        ]

        s3db.configure("doc_image",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_doc_image_resource = customise_doc_image_resource

    def customise_doc_sitrep_resource(r, tablename):

        if not current.auth.s3_has_role("AUTHENTICATED"):
            # @ToDo: Just show the External (Public) parts
            pass

    #settings.customise_doc_sitrep_resource = customise_doc_sitrep_resource

    # =========================================================================
    # Beneficiaries
    #
    settings.dvr.label = "Beneficiary"

    def customise_beneficiary_form():
        
        s3db = current.s3db
        otable = s3db.org_organisation
        org = current.db(otable.name == SAVE).select(otable.id,
                                                     cache = s3db.cache,
                                                     limitby = (0, 1),
                                                     ).first()
        try:
            SCI = org.id
        except:
            current.log.error("Cannot find org %s - prepop not done?" % SAVE)
        else:
            s3db.dvr_case.organisation_id.default = SCI

        from s3 import S3SQLCustomForm, S3SQLInlineComponent
        crud_form = S3SQLCustomForm(
                        # @ToDo: Scan this in from barcode on preprinted card
                        "dvr_case.reference",
                        "dvr_case.date",
                        "first_name",
                        "middle_name",
                        "last_name",
                        "date_of_birth",
                        "gender",
                        S3SQLInlineComponent(
                                "contact",
                                fields = [("", "value"),
                                          ],
                                filterby = {"field": "contact_method",
                                            "options": "SMS",
                                            },
                                label = T("Mobile Phone"),
                                multiple = False,
                                name = "phone",
                                ),
                        S3SQLInlineComponent(
                                "contact",
                                fields = [("", "value"),
                                          ],
                                filterby = {"field": "contact_method",
                                            "options": "EMAIL",
                                            },
                                label = T("Email"),
                                multiple = False,
                                name = "email",
                                ),
                        S3SQLInlineComponent(
                                "address",
                                label = T("Current Address"),
                                fields = [("", "location_id"),
                                          ],
                                filterby = {"field": "type",
                                            "options": "1",
                                            },
                                link = False,
                                multiple = False,
                                ),
                        "dvr_case.comments",
                        )

        s3db.configure("pr_person",
                       crud_form = crud_form,
                       )

    def customise_pr_person_resource(r, tablename):

        if r.function == "distribution":
            # Beneficiaries
            customise_beneficiary_form()
            s3db.pr_address.location_id.default = r.record.location_id

    settings.customise_pr_person_resource = customise_pr_person_resource

    def customise_pr_person_controller(**attr):

        s3 = current.response.s3
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                if not standard_prep(r):
                    return False

            if r.controller == "dvr":
                # Beneficiaries
                customise_beneficiary_form()
            return True
        s3.prep = custom_prep

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # =========================================================================
    # Events
    #
    settings.event.label = "Disaster"

    # =========================================================================
    # Projects
    #
    settings.project.mode_3w = True
    settings.project.mode_drr = True

    settings.project.activities = True
    settings.project.hazards = False
    settings.project.hfa = False
    settings.project.themes = False

    settings.project.multiple_organisations = True

    # Custom label for project organisation
    settings.project.organisation_roles = {1: T("Implementing Organization"),
                                           2: T("Partner Organization"),
                                           3: T("Donor"),
                                           }

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
        ("sync", Storage(
            name_nice = T("Synchronization"),
            #description = "Synchronization",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
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
        ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 2,
        )),
        #("vol", Storage(
        #    name_nice = T("Volunteers"),
        #    #description = "Human Resources Management",
        #    restricted = True,
        #    module_type = 2,
        #)),
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
        ("supply", Storage(
            name_nice = T("Distributions"),
            #description = "Used within Inventory Management, Request Management and Asset Management",
            restricted = True,
            module_type = 10,
        )),
        #("inv", Storage(
        #    name_nice = T("Warehouses"),
        #    #description = "Receiving and Sending Items",
        #    restricted = True,
        #    module_type = 4
        #)),
        #("asset", Storage(
        #    name_nice = T("Assets"),
        #    #description = "Recording and Assigning Assets",
        #    restricted = True,
        #    module_type = 5,
        #)),
        # Vehicle depends on Assets
        #("vehicle", Storage(
        #    name_nice = T("Vehicles"),
        #    #description = "Manage Vehicles",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("req", Storage(
        #    name_nice = T("Requests"),
        #    #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
        #    restricted = True,
        #    module_type = 10,
        #)),
        ("project", Storage(
            name_nice = T("4W"),
            #description = "Tracking of Projects, Activities and Tasks",
            restricted = True,
            module_type = 2
        )),
        #("cr", Storage(
        #    name_nice = T("Shelters"),
        #    #description = "Tracks the location, capacity and breakdown of victims in Shelters",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("hms", Storage(
        #    name_nice = T("Hospitals"),
        #    #description = "Helps to monitor status of hospitals",
        #    restricted = True,
        #    module_type = 10
        #)),
        ("dc", Storage(
            name_nice = T("Assessments"),
            restricted = True,
            module_type = 10,
        )),
        ("dvr", Storage(
           name_nice = T("Beneficiaries"),
           #description = "Allow affected individuals & households to register to receive compensation and distributions",
           restricted = True,
           module_type = 10,
        )),
        ("event", Storage(
            name_nice = T("Events"),
            #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
            restricted = True,
            module_type = 10,
        )),
        #("transport", Storage(
        #   name_nice = T("Transport"),
        #   restricted = True,
        #   module_type = 10,
        #)),
        ("stats", Storage(
            name_nice = T("Statistics"),
            #description = "Manages statistics",
            restricted = True,
            module_type = None,
        )),
    ])

# END =========================================================================