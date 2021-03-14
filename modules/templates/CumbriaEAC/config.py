# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Cumbria Emergency Assistance Centres
    """

    T = current.T

    settings.base.system_name = T("Cumbria Emergency Assistance Centres")
    settings.base.system_name_short = T("EAC")

    # PrePopulate data
    settings.base.prepopulate += ("CumbriaEAC",)
    #settings.base.prepopulate_demo += ("CumbriaEAC/Demo",)

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "CCC"
    # Custom Logo
    #settings.ui.menu_logo = "/%s/static/themes/CumbriaEAC/img/logo.png" % current.request.application

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    #settings.auth.registration_requests_organisation = True
    # Required for access to default realm permissions
    #settings.auth.registration_link_user_to = ["staff"]
    #settings.auth.registration_link_user_to_default = ["staff"]

    # Consent Tracking
    settings.auth.consent_tracking = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    #settings.gis.countries = ("US",)
    # Uncomment to display the Map Legend as a floating DIV, so that it is visible on Summary Map
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # Use GetAddress.io to lookup Addresses from Postcode
    settings.gis.postcode_to_address = "getaddress"

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages = OrderedDict([
        ("en-gb", "English"),
    ])
    # Default Language
    settings.L10n.default_language = "en-gb"
    # Uncomment to Hide the language toolbar
    settings.L10n.display_toolbar = False

    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","

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
        # HRM is required for access to default realm permissions
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
        #("doc", Storage(
        #    name_nice = T("Documents"),
        #    #description = "A library of digital resources, such as photos, documents and reports",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("msg", Storage(
        #    name_nice = T("Messaging"),
        #    #description = "Sends & Receives Alerts via Email & SMS",
        #    restricted = True,
        #    # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
        #    module_type = None,
        #)),
        #("supply", Storage(
        #    name_nice = T("Supply Chain Management"),
        #    #description = "Used within Inventory Management, Request Management and Asset Management",
        #    restricted = True,
        #    module_type = None, # Not displayed
        #)),
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
        #("project", Storage(
        #    name_nice = T("Projects"),
        #    #description = "Tracking of Projects, Activities and Tasks",
        #    restricted = True,
        #    module_type = 2
        #)),
        ("cr", Storage(
            name_nice = T("Shelters"),
            #description = "Tracks the location, capacity and breakdown of victims in Shelters",
            restricted = True,
            module_type = 10
        )),
        #("hms", Storage(
        #    name_nice = T("Hospitals"),
        #    #description = "Helps to monitor status of hospitals",
        #    restricted = True,
        #    module_type = 10
        #)),
        ("br", Storage(
           name_nice = T("Beneficiary Registry"),
           #description = "Allow affected individuals & households to register to receive compensation and distributions",
           restricted = True,
           module_type = 10,
        )),
        #("event", Storage(
        #    name_nice = T("Events"),
        #    #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("transport", Storage(
        #   name_nice = T("Transport"),
        #   restricted = True,
        #   module_type = 10,
        #)),
        #("stats", Storage(
        #    name_nice = T("Statistics"),
        #    #description = "Manages statistics",
        #    restricted = True,
        #    module_type = None,
        #)),
    ])

    # -------------------------------------------------------------------------
    # Beneficiary Registry
    # Terminology to use when referring to cases (Beneficiary|Client|Case)
    settings.br.case_terminology = "Client" # Evacuee
    # Disable assignment of cases to staff
    settings.br.case_manager = False
    # Expose fields to track home address in case file
    settings.br.case_address = True
    # Disable tracking of case activities
    settings.br.case_activities = False
    # Disable tracking of individual assistance measures
    settings.br.manage_assistance = False

    # -------------------------------------------------------------------------
    # Shelters
    # Uncomment to use a dynamic population estimation by calculations based on registrations
    settings.cr.shelter_population_dynamic = True

    # -------------------------------------------------------------------------
    def eac_person_anonymize():
        """ Rules to anonymise a person """

        auth = current.auth

        ANONYMOUS = "-"
        anonymous_email = uuid4().hex

        if current.request.controller == "br":
            title = "Name, Contacts, Address, Case Details"
        else:
            title = "Name, Contacts, Address, Additional Information, User Account"

        rules = [{"name": "default",
                  "title": title,
                  "fields": {"first_name": ("set", ANONYMOUS),
                             "middle_name": ("set", ANONYMOUS),
                             "last_name": ("set", ANONYMOUS),
                             #"pe_label": anonymous_id,
                             #"date_of_birth": current.s3db.pr_person_obscure_dob,
                             "date_of_birth": "remove",
                             "comments": "remove",
                             },
                  "cascade": [("pr_contact", {"key": "pe_id",
                                              "match": "pe_id",
                                              "fields": {"contact_description": "remove",
                                                         "value": ("set", ""),
                                                         "comments": "remove",
                                                         },
                                              "delete": True,
                                              }),
                              ("pr_contact_emergency", {"key": "pe_id",
                                                        "match": "pe_id",
                                                        "fields": {"name": ("set", ANONYMOUS),
                                                                   "relationship": "remove",
                                                                   "phone": "remove",
                                                                   "comments": "remove",
                                                                   },
                                                        "delete": True,
                                                        }),
                              ("pr_address", {"key": "pe_id",
                                              "match": "pe_id",
                                              "fields": {"location_id": current.s3db.pr_address_anonymise,
                                                         "comments": "remove",
                                                         },
                                              }),
                              #("pr_person_details", {"key": "person_id",
                              #                       "match": "id",
                              #                       "fields": {"education": "remove",
                              #                                  "occupation": "remove",
                              #                                  },
                              #                       }),
                              ("pr_person_tag", {"key": "person_id",
                                                 "match": "id",
                                                 "fields": {"value": ("set", ANONYMOUS),
                                                            },
                                                 "delete": True,
                                                 }),
                              ("br_case", {"key": "person_id",
                                           "match": "id",
                                           "fields": {"comments": "remove",
                                                      },
                                           "cascade": [("br_note", {"key": "id",
                                                                    "match": "case_id",
                                                                    "fields": {"note": "remove",
                                                                               },
                                                                    "delete": True,
                                                                    }),
                                                       ],
                                           }),
                              ("hrm_human_resource", {"key": "person_id",
                                                      "match": "id",
                                                      "fields": {"status": ("set", 2),
                                                                 #"site_id": "remove",
                                                                 "comments": "remove",
                                                                 },
                                                      "delete": True,
                                                      "cascade": [("hrm_human_resource_tag", {"key": "human_resource_id",
                                                                                              "match": "id",
                                                                                              "fields": {"value": ("set", ANONYMOUS),
                                                                                                         },
                                                                                              "delete": True,
                                                                                              }),
                                                                  ],
                                                      }),
                              ("pr_person_user", {"key": "pe_id",
                                                  "match": "pe_id",
                                                  "cascade": [("auth_user", {"key": "id",
                                                                             "match": "user_id",
                                                                             "fields": {"id": auth.s3_anonymise_roles,
                                                                                        "first_name": ("set", "-"),
                                                                                        "last_name": "remove",
                                                                                        "email": ("set", anonymous_email),
                                                                                        "organisation_id": "remove",
                                                                                        "password": auth.s3_anonymise_password,
                                                                                        "deleted": ("set", True),
                                                                                        },
                                                                             }),
                                                              ],
                                                  "delete": True,
                                                  }),
                              ],
                  "delete": True,
                  },
                 ]

        return rules

    # -------------------------------------------------------------------------
    def eac_rheader(r):
        """
            Custom rheaders
        """

        if r.representation != "html":
            # RHeaders only used in interactive views
            return None

        # Need to use this format as otherwise req_match?viewing=org_office.x
        # doesn't have an rheader
        from s3 import s3_rheader_resource, s3_rheader_tabs
        tablename, record = s3_rheader_resource(r)

        if record is None:
            # List or Create form: rheader makes no sense here
            return None

        from gluon import DIV, TABLE, TR, TH

        T = current.T

        if tablename == "cr_shelter":

            tabs = [(T("Basic Details"), None),
                    (T("Staff"), "human_resource"),
                    (T("Evacuees"), "shelter_registration"),
                    #(T("Friends/Family"), "shelter_registration"),
                    ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table
            location_id = table.location_id
            rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                                   record.name,
                                   ),
                                TR(TH("%s: " % location_id.label),
                                   location_id.represent(record.location_id),
                                   ),
                                ),
                          rheader_tabs)

        return rheader

    # -------------------------------------------------------------------------
    def customise_cr_shelter_resource(r, tablename):
        """
        """

        from s3 import S3SQLCustomForm, S3LocationSelector, \
                       S3TextFilter, S3LocationFilter, S3OptionsFilter, S3RangeFilter

        s3db = current.s3db

        table = s3db.cr_shelter
        table.population_day.label = T("Occupancy")
        table.location_id.widget = S3LocationSelector(levels = ("L3", "L4"),
                                                      #levels = ("L2", "L3", "L4"),
                                                      required_levels = ("L3",),
                                                      show_address = True,
                                                      #show_map = False,
                                                      )

        crud_form = S3SQLCustomForm("name",
                                    "location_id",
                                    "phone",
                                    "capacity_day",
                                    "status",
                                    "comments",
                                    "obsolete",
                                    )

        filter_widgets = [
                S3TextFilter(["name",
                              "comments",
                              "location_id$L3",
                              "location_id$L4",
                              "location_id$addr_street",
                              "location_id$addr_postcode",
                              ],
                             label = T("Search"),
                             #_class = "filter-search",
                             ),
                S3LocationFilter("location_id",
                                 label = T("Location"),
                                 levels = ("L3", "L4"),
                                 ),
                S3OptionsFilter("status",
                                label = T("Status"),
                                options = {1 : T("Closed"),
                                           2 : T("Open##the_shelter_is"),
                                           None : T("Unspecified"),
                                           },
                                none = True,
                                ),
                S3RangeFilter("capacity_day",
                              label = T("Total Capacity"),
                              ),
                S3RangeFilter("available_capacity_day",
                              label = T("Available Capacity"),
                              ),
                ]

        list_fields = ["name",
                       "status",
                       "capacity_day",
                       "population_day",
                       "location_id$L3",
                       "location_id$L4",
                       "location_id$addr_street",
                       ]

        report_fields = ["name",
                         "status",
                         "capacity_day",
                         "population_day",
                         "location_id$L3",
                         "location_id$L4",
                         ]

        s3db.configure(tablename,
                       create_next = None, # Don't redirect to People Registration after creation
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       report_options = Storage(
                        rows = report_fields,
                        cols = report_fields,
                        fact = report_fields,
                        defaults = Storage(rows = "location_id$L4", # Lowest-level of hierarchy
                                           cols = "status",
                                           fact = "count(name)",
                                           totals = True,
                                           )
                        ),
                       )

    settings.customise_cr_shelter_resource = customise_cr_shelter_resource

    # -----------------------------------------------------------------------------
    def customise_cr_shelter_controller(**attr):

        attr["rheader"] = eac_rheader

        return attr

    settings.customise_cr_shelter_controller = customise_cr_shelter_controller

# END =========================================================================
