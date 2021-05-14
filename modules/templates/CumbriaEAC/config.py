# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

from s3 import S3CRUD

def config(settings):
    """
        Cumbria Emergency Assistance Centres
    """

    T = current.T

    settings.base.system_name = T("Cumbria Emergency Assistance Centres")
    settings.base.system_name_short = T("Cumbria EACs")

    # PrePopulate data
    settings.base.prepopulate += ("CumbriaEAC",)
    settings.base.prepopulate_demo += ("CumbriaEAC/Demo",)

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "CumbriaEAC"
    # Custom Logo
    #settings.ui.menu_logo = "/%s/static/themes/CumbriaEAC/img/logo.png" % current.request.application

    # Authentication settings
    # Should users be allowed to register themselves?
    settings.security.self_registration = False
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
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # Use GetAddress.io to lookup Addresses from Postcode
    settings.gis.postcode_to_address = "getaddress"

    # Permanent Address/NoK can be in any country
    settings.gis.countries = []

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

    settings.ui.export_formats = ("xls",)

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
        #("br", Storage(
        #   name_nice = T("Beneficiary Registry"),
        #   #description = "Allow affected individuals & households to register to receive compensation and distributions",
        #   restricted = True,
        #   module_type = 10,
        #)),
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
    # Beneficiary Registry (Not Used)
    # Terminology to use when referring to cases (Beneficiary|Client|Case)
    #settings.br.case_terminology = "Client" # Evacuee
    # Disable assignment of cases to staff
    #settings.br.case_manager = False
    # Expose fields to track home address in case file
    #settings.br.case_address = True
    # Disable tracking of case activities
    #settings.br.case_activities = False
    # Disable tracking of individual assistance measures
    #settings.br.manage_assistance = False

    # -------------------------------------------------------------------------
    # Shelters
    # Uncomment to use a dynamic population estimation by calculations based on registrations
    settings.cr.shelter_population_dynamic = True

    cr_shelter_status_opts = {1 : T("Closed"), # Nominated Centres
                              #2 : T("Open##the_shelter_is"),
                              3 : T("Green"),
                              4 : T("Amber"),
                              5 : T("Red"),
                              6 : T("Closed"), # Community Centres
                              }

    # -------------------------------------------------------------------------
    # Human Resources
    settings.hrm.org_required = False
    # Minimise Profile (not needed as we override Tabs in eac_rheader)
    #settings.hrm.staff_experience = False
    #settings.hrm.use_certificates = False
    #settings.hrm.use_credentials = False
    #settings.hrm.use_description = None
    #settings.hrm.use_id = None
    #settings.hrm.use_skills = None
    #settings.hrm.teams = None
    #settings.hrm.use_trainings = False

    # -------------------------------------------------------------------------
    # Messaging
    settings.msg.require_international_phone_numbers = False

    # -------------------------------------------------------------------------
    # Persons
    settings.pr.hide_third_gender = False
    settings.L10n.mandatory_lastname = True
    settings.pr.editable_fields = ["mobile_phone",
                                   "car",
                                   ]

    # -------------------------------------------------------------------------
    def eac_person_anonymize():
        """ Rules to anonymise a person """

        #auth = current.auth

        ANONYMOUS = "-"
        #anonymous_email = uuid4().hex

        title = "Name, Contacts, Address, Additional Information"

        rules = [{"name": "default",
                  "title": title,
                  "fields": {"first_name": ("set", ANONYMOUS),
                             "middle_name": ("set", ANONYMOUS),
                             "last_name": ("set", ANONYMOUS),
                             "pe_label": "remove",
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
                              #("br_case", {"key": "person_id",
                              #             "match": "id",
                              #             "fields": {"comments": "remove",
                              #                        },
                              #             "cascade": [("br_note", {"key": "id",
                              #                                      "match": "case_id",
                              #                                      "fields": {"note": "remove",
                              #                                                 },
                              #                                      "delete": True,
                              #                                      }),
                              #                         ],
                              #             }),
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
                              #("pr_person_user", {"key": "pe_id",
                              #                    "match": "pe_id",
                              #                    "cascade": [("auth_user", {"key": "id",
                              #                                               "match": "user_id",
                              #                                               "fields": {"id": auth.s3_anonymise_roles,
                              #                                                          "first_name": ("set", "-"),
                              #                                                          "last_name": "remove",
                              #                                                          "email": ("set", anonymous_email),
                              #                                                          "organisation_id": "remove",
                              #                                                          "password": auth.s3_anonymise_password,
                              #                                                          "deleted": ("set", True),
                              #                                                          },
                              #                                               }),
                              #                                ],
                              #                    "delete": True,
                              #                    }),
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

            if r.method == "create":
                # The dedicated check-in pages shouldn't have an rheader to clutter things up
                return None

            status = record.status
            if status in (1, 6):
                # Closed...cannot register Staff/Clients
                closed = True
                tabs = [(T("Shelter Details"), None),
                        (T("Event Log"), "event"),
                        ]
            else:
                # Open
                closed = False
                tabs = [(T("Shelter Details"), None),
                        (T("Staff"), "human_resource_site"),
                        (T("Clients"), "client"),
                        (T("Event Log"), "event"),
                        ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table
            location_id = table.location_id
            status_field = table.status
            button = ""
            if closed:
                occupancy = ""
                # Is there any unarchived data to Export?
                etable = current.s3db.org_site_event
                query = (etable.site_id == record.site_id) & \
                        (etable.archived == False)
                unarchived = current.db(query).select(etable.id,
                                                      limitby = (0, 1)
                                                      ).first()
                if unarchived:
                    # Add Export Button
                    from gluon import A, URL
                    button = A(T("Export"),
                               _href = URL(args = [r.id, "export.xls"]),
                               _class = "action-btn",
                               )
                # Is there any unanonymised data?
                # @ToDo: Add Anonymise Button
            else:
                occupancy = TR(TH("%s: " % table.population_day.label),
                               "%s / %s" % (record.population_day, record.capacity_day),
                               )
            rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                                   record.name,
                                   ),
                                TR(TH("%s: " % location_id.label),
                                   location_id.represent(record.location_id),
                                   ),
                                TR(TH("%s: " % status_field.label),
                                   status_field.represent(status),
                                   ),
                                occupancy,
                                button,
                                ),
                          rheader_tabs)

        elif tablename == "pr_person":

            tabs = [(T("Person Details"), None),
                    (T("Event Log"), "site_event"),
                    ]

            if r.controller in ("hrm", "default"):
                hrtable = current.s3db.hrm_human_resource
                hr = current.db(hrtable.person_id == record.id).select(hrtable.organisation_id,
                                                                       limitby = (0, 1)
                                                                       ).first()
                if hr:
                    org = TR(TH("%s: " % T("Organization")),
                             hrtable.organisation_id.represent(hr.organisation_id),
                             )
                else:
                    org = ""
            else:
                org = ""
                if current.auth.s3_has_role("POLICE", include_admin=False):
                    # Only show NoK tab if it already has data (this role cannot create)
                    table = current.s3db.pr_person_relation
                    nok = current.db(table.parent_id == record.id).select(table.id,
                                                                          limitby = (0, 1)
                                                                          ).first()
                    if nok:
                        tabs.insert(1, (T("Next of Kin"), "nok"))
                else:
                    tabs.insert(1, (T("Next of Kin"), "nok"))
                #tabs.insert(2, (T("Household"), None, {}, "household"))
                tabs.insert(2, (T("Household"), "household"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            from s3 import s3_fullname

            rheader = DIV(TABLE(TR(TH("%s: " % T("Name")),
                                   s3_fullname(record),
                                   ),
                                org,
                                ),
                          rheader_tabs)

        return rheader

    # -------------------------------------------------------------------------
    def cr_shelter_onvalidation(form):
        """
            Ensure that the correct closed Status is used for the Shelter Type
        """

        form_vars = form.vars
        form_vars_get = form_vars.get

        status = form_vars_get("status")
        if status not in ("1", "6"):
            # Shelter is Open
            obsolete = form_vars_get("obsolete")
            if obsolete:
                # Cannot open an Unavailable Shelter
                form.errors.obsolete = T("Cannot open an Unavailable Shelter")
            return

        # Shelter is Closed: Ensure we use the correct one

        # Look up the Shelter Type
        shelter_type_id = form_vars_get("shelter_type_id")
        ttable = current.s3db.cr_shelter_type
        shelter_type = current.db(ttable.id == shelter_type_id).select(ttable.name,
                                                                       limitby = (0, 1)
                                                                       ).first()
        type_name = shelter_type.name
        if type_name == "Nominated":
            form_vars.status = 1
        elif type_name == "Community":
            form_vars.status = 6

    # -------------------------------------------------------------------------
    def customise_cr_shelter_resource(r, tablename):

        from gluon import DIV, IS_EMPTY_OR, IS_IN_SET, IS_LENGTH, IS_NOT_EMPTY, IS_NOT_IN_DB

        from s3 import S3Represent, S3SQLCustomForm, S3LocationSelector, \
                       S3TextFilter, S3LocationFilter, S3OptionsFilter, S3RangeFilter

        s3db = current.s3db

        current.messages.OBSOLETE = T("Unavailable")

        # Only have a single Status option visible
        shelter_status_opts = dict(cr_shelter_status_opts)
        if r.record and r.record.status == 6:
            del shelter_status_opts[1]
        elif r.interactive and not current.auth.override:
            del shelter_status_opts[6]

        table = s3db.cr_shelter
        table.name.requires = [IS_NOT_EMPTY(),
                               IS_LENGTH(64),
                               IS_NOT_IN_DB(current.db, "cr_shelter.name"),
                               ]
        f = table.shelter_type_id
        f.label = T("Type")
        f.comment = None # No inline Create
        f = s3db.cr_shelter_service_shelter.service_id
        f.label = T("Service")
        f.requires = IS_EMPTY_OR(f.requires)
        f.comment = None # No inline Create
        f = table.status
        f.default = 3 # Green
        f.requires = IS_IN_SET(shelter_status_opts)
        if r.extension == "geojson":
            # GeoJSON should have smaller numbers which are also distinguishable across the 2x closed statuses
            f.represent = None
        else:
            f.represent = S3Represent(options = shelter_status_opts)
        table.population_day.label = T("Occupancy")
        table.obsolete.label = T("Unavailable")
        table.obsolete.comment = DIV(_class="tooltip",
                                     _title="%s|%s" % (T("Unavailable"),
                                                       T("Site is temporarily unavailable (e.g. for building works) & so should be hidden from the map"),
                                                       ))
        table.location_id.widget = S3LocationSelector(levels = ("L2", "L3", "L4"),
                                                      required_levels = ("L2", "L3"),
                                                      show_address = True,
                                                      )

        # Redefine as multiple=False
        s3db.add_components("cr_shelter",
                            cr_shelter_service_shelter = {"joinby": "shelter_id",
                                                          "multiple": False,
                                                          }
                            )

        # Filtered components
        s3db.add_components("org_site",
                            org_site_tag = ({"name": "red_bag",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "red_bag"},
                                             "multiple": False,
                                             },
                                            {"name": "wifi",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "wifi"},
                                             "multiple": False,
                                             },
                                            {"name": "catering",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "catering"},
                                             "multiple": False,
                                             },
                                            ),
                            )

        from s3 import S3TagCheckboxWidget

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        red_bag = components_get("red_bag")
        f = red_bag.table.value
        f.requires = IS_EMPTY_OR(IS_IN_SET(("Yes", "No"), zero= T("Unknown")))

        wifi = components_get("wifi")
        f = wifi.table.value
        f.requires = IS_EMPTY_OR(IS_IN_SET(("Yes", "No"), zero= T("Unknown")))

        crud_form = S3SQLCustomForm("name",
                                    "status",
                                    "shelter_service_shelter.service_id",
                                    "shelter_type_id",
                                    "location_id",
                                    "phone",
                                    "capacity_day",
                                    (T("Red Bag Lite"), "red_bag.value"),
                                    (T("WiFi available"), "wifi.value"),
                                    (T("Catering"), "catering.value"),
                                    "comments",
                                    "obsolete",
                                    )

        cr_shelter_status_opts[1] = T("Closed (Nominated)")
        cr_shelter_status_opts[6] = T("Closed (Community)")
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
                S3OptionsFilter("shelter_type_id",
                                ),
                S3OptionsFilter("shelter_service_shelter.service_id",
                                ),
                S3OptionsFilter("status",
                                label = T("Status"),
                                options = cr_shelter_status_opts,
                                ),
                S3RangeFilter("capacity_day",
                              label = T("Total Capacity"),
                              ),
                S3RangeFilter("available_capacity_day",
                              label = T("Available Capacity"),
                              ),
                ]

        list_fields = ["name",
                       "shelter_type_id",
                       "shelter_service_shelter.service_id",
                       "status",
                       "capacity_day",
                       "population_day",
                       "location_id$L3",
                       "location_id$L4",
                       "location_id$addr_street",
                       (T("Red Bag Lite"), "red_bag.value"),
                       (T("WiFi available"), "wifi.value"),
                       (T("Catering"), "catering.value"),
                       ]

        report_fields = ["name",
                         "shelter_type_id",
                         "shelter_service_shelter.service_id",
                         "status",
                         "capacity_day",
                         "population_day",
                         "location_id$L3",
                         "location_id$L4",
                         (T("Red Bag Lite"), "red_bag.value"),
                         (T("WiFi available"), "wifi.value"),
                         (T("Catering"), "catering.value"),
                         ]

        s3db.configure(tablename,
                       create_next = None, # Don't redirect to People Registration after creation
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       onvalidation = cr_shelter_onvalidation,
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

        from gluon import URL
        from s3 import s3_set_default_filter

        s3db = current.s3db
        response = current.response

        # Exclude Closed Shelters by default
        s3_set_default_filter("~.status", [3, 4, 5], tablename="cr_shelter")

        # Exclude Checked-out Clients by default
        s3_set_default_filter("client.shelter_registration.registration_status", [2], tablename="pr_person")

        s3 = response.s3

        # Custom Methods
        def client_checkout(r, **attr):

            from gluon import SQLFORM

            person_id = r.component_id

            class REPLACE_TEXT(object):
                def __call__(self, value):
                    error = None
                    value = "Client going to: %s" % value
                    return (value, None)

            # Add Event Log entry
            table = s3db.org_site_event
            f = table.site_id
            f.readable = f.writable = False
            f = table.site_id
            f.readable = f.writable = False
            f.default = r.record.site_id
            f = table.person_id
            f.readable = f.writable = False
            f.default = person_id
            f = table.event
            f.readable = f.writable = False
            f.default = 3 # Checked-Out
            table.date.readable = table.date.writable = False
            table.status.readable = table.status.writable = False
            table.comments.label = T("Going To")
            table.comments.requires = REPLACE_TEXT()

            form = SQLFORM(table)

            if form.accepts(r.post_vars, current.session):
                # Update Shelter Registration
                current.db(s3db.cr_shelter_registration.person_id == person_id).update(registration_status = 3,# Checked-Out
                                                                                       check_out_date = r.now,
                                                                                       )
                # Update Shelter Population
                s3db.cr_update_shelter_population(r.id)
                # response.confirmation triggers the popup close (although not actually seen by user)
                response.confirmation = T("Client checked-out successfully!")

            response.view = "popup.html"
            return {"form": form}

        def staff_checkout(r, **attr):
            db = current.db
            component_id = r.component_id
            ltable = s3db.hrm_human_resource_site
            htable = s3db.hrm_human_resource
            query = (ltable.id == component_id) & \
                    (ltable.human_resource_id == htable.id)
            staff = db(query).select(htable.id,
                                     htable.person_id,
                                     limitby = (0, 1)
                                     ).first()
            # Remove Link
            db(ltable.id == component_id).delete()
            # Clear site_id
            staff.update_record(site_id = None)
            # Add Event Log entry
            s3db.org_site_event.insert(site_id = r.record.site_id,
                                       person_id = staff.person_id,
                                       event = 3, # Checked-Out
                                       comments = "Staff",
                                       )
            # Redirect
            current.session.confirmation = T("Staff checked-out successfully!")
            from gluon import redirect
            redirect(URL(c="cr", f="shelter",
                         args = [r.id,
                                 "human_resource_site",
                                 ],
                         ))

        def shelter_export(r, **attr):
            shelter_id = r.id
            record = r.record
            if record.status not in (1, 6):
                current.session.error = T("Cannot Export Data for a Shelter unless it is Closed")
                # Redirect to Normal page
                from gluon import redirect
                redirect(URL(args = [shelter_id]))

            # Export all the data for the Shelter
            from s3.codecs.xls import S3XLS
            try:
                import xlwt
            except ImportError:
                error = S3XLS.ERROR.XLWT_ERROR
                current.log.error(error)
                raise HTTP(503, body=error)
            try:
                from xlrd.xldate import xldate_from_date_tuple, \
                                        xldate_from_datetime_tuple
            except ImportError:
                error = S3XLS.ERROR.XLRD_ERROR
                current.log.error(error)
                raise HTTP(503, body=error)

            shelter_name = record.name
            # Log in Site Log
            etable = s3db.org_site_event
            etable.insert(site_id = record.site_id,
                          event = 5, # Data Export
                          comments = "Shelter",
                          )
            # Log in Global Log
            settings.security.audit_write = True
            from s3 import S3Audit
            S3Audit().__init__()
            s3db.s3_audit.insert(timestmp = r.now,
                                 user_id = current.auth.user.id,
                                 method = "Data Export",
                                 representation = shelter_name,
                                 )
            # Extract Data
            db = current.db
            # Event Log
            logs = db(etable.archived == False).select(etable.date,
                                                       etable.created_by,
                                                       etable.event,
                                                       etable.comments,
                                                       etable.person_id,
                                                       etable.status,
                                                       )
            client_ids = []
            cappend = client_ids.append
            staff_ids = []
            sappend = staff_ids.append
            for row in logs:
                if row.event != 2:
                    # Only interested in check-ins
                    continue
                if row.comments == "Staff":
                    sappend(row.person_id)
                else:
                    cappend(row.person_id)
            # Clients
            ptable = s3db.pr_person
            clients = db(ptable.id.belongs(client_ids)).select(ptable.id,
                                                               ptable.pe_label,
                                                               ptable.first_name,
                                                               ptable.middle_name,
                                                               ptable.last_name,
                                                               ptable.date_of_birth,
                                                               ptable.gender,
                                                               )
            # Staff
            htable = s3db.hrm_human_resource
            query = (ptable.id.belongs(set(staff_ids))) & \
                    (ptable.id == htable.person_id)
            staff = db(query).select(ptable.id,
                                     ptable.first_name,
                                     ptable.last_name,
                                     htable.organisation_id,
                                     )

            #session = current.session
            #session.confirmation = T("Data Exported")
            #session.information = T("Data Anonymization Scheduled")

            # Create the workbook
            book = xlwt.Workbook(encoding="utf-8")
            styles = S3XLS._styles(use_colour = True,
                                   evenodd = True)
            header_style = styles["header"]
            odd_style = styles["odd"]
            even_style = styles["even"]

            # Clients Sheet
            sheet = book.add_sheet("Clients")
            header_row = sheet.row(0)
            header_row.write(0, "ID", header_style)
            header_row.write(1, "Reception Centre Ref", header_style)
            header_row.write(2, "Last Name", header_style)
            header_row.write(3, "Middle Name", header_style)
            header_row.write(4, "First Name", header_style)
            header_row.write(5, "Sex", header_style)
            header_row.write(6, "Date of Birth", header_style)
            row_index = 0
            for row in clients:
                current_row = sheet.row(row_index)
                style = even_style if row_index % 2 == 0 else odd_style
                col_index = 0
                for field in ("id",
                              "pe_label",
                              "last_name",
                              "middle_name",
                              "first_name",
                              "gender",
                              "date_of_birth",
                              ):
                    current_row.write(col_index, row[field], style)
                    col_index += 1
                row_index += 1

            # Staff Sheet
            sheet = book.add_sheet("Staff")
            header_row = sheet.row(0)
            header_row.write(0, "ID", header_style)
            header_row.write(1, "Organisation", header_style)
            header_row.write(2, "Last Name", header_style)
            header_row.write(3, "First Name", header_style)
            col_index = 0

            # Log Sheet
            sheet = book.add_sheet("Log")
            header_row = sheet.row(0)
            header_row.write(0, "Date", header_style)
            header_row.write(1, "User", header_style)
            header_row.write(2, "Event", header_style)
            header_row.write(3, "Comments", header_style)
            header_row.write(4, "Person", header_style)
            header_row.write(5, "Status", header_style)
            col_index = 0

            # Write output
            from s3compat import BytesIO
            output = BytesIO()
            book.save(output)
            output.seek(0)

            # Response headers
            from gluon.contenttype import contenttype
            filename = "%s.xls" % shelter_name
            disposition = "attachment; filename=\"%s\"" % filename
            response = current.response
            response.headers["Content-Type"] = contenttype(".xls")
            response.headers["Content-disposition"] = disposition

            return output.read()

        def shelter_manage(r, **attr):
            shelter_id = r.id
            # Set this shelter into the session
            current.session.s3.shelter_id = shelter_id
            # Redirect to Normal page
            from gluon import redirect
            redirect(URL(args = [shelter_id]))

        def staff_redirect(r, **attr):
            # Redirect to Staff record
            ltable = s3db.hrm_human_resource_site
            htable = s3db.hrm_human_resource
            query = (ltable.id == r.component_id) & \
                    (ltable.human_resource_id == htable.id)
            staff = current.db(query).select(htable.person_id,
                                             limitby = (0, 1)
                                             ).first()
            from gluon import redirect
            redirect(URL(c="hrm", f="person",
                         args = [staff.person_id],
                         ))

        set_method = s3db.set_method

        set_method("cr", "shelter",
                   component_name = "client",
                   method = "checkout",
                   action = client_checkout)

        set_method("cr", "shelter",
                   component_name = "human_resource_site",
                   method = "checkout",
                   action = staff_checkout)

        set_method("cr", "shelter",
                   method = "export",
                   action = shelter_export)

        set_method("cr", "shelter",
                   method = "manage",
                   action = shelter_manage)

        set_method("cr", "shelter",
                   component_name = "human_resource_site",
                   method = "redirect",
                   action = staff_redirect)

        s3db.add_components("cr_shelter",
                            pr_person = {"name": "client",
                                         "link": "cr_shelter_registration",
                                         "joinby": "shelter_id",
                                         "key": "person_id",
                                         "actuate": "replace",
                                         }
                            )

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if current.auth.s3_has_role("SHELTER_ADMIN"):
                # Consistent Header across tabs
                s3.crud_strings["cr_shelter"].title_display = T("Manage Shelter")

            if r.component_name == "human_resource_site":
                if not r.interactive:
                    auth = current.auth
                    output_format = auth.permission.format
                    if output_format not in ("aadata", "json", "xls"):
                        # Block Exports
                        return False
                    if output_format == "xls":
                        # Add Site Event Log
                        s3db.org_site_event.insert(site_id = r.record.site_id,
                                                   event = 5, # Data Export
                                                   comments = "Staff",
                                                   )
                        # Log in Global Log
                        settings.security.audit_write = True
                        from s3 import S3Audit
                        S3Audit().__init__()
                        s3db.s3_audit.insert(timestmp = r.now,
                                             user_id = auth.user.id,
                                             method = "Data Export",
                                             representation = "Staff",
                                             )

                if r.method == "create":
                    s3.crud_strings["cr_shelter"].title_display = T("Check-in Staff to %(shelter)s") % \
                                                                            {"shelter": r.record.name}

                # Filtered components
                s3db.add_components("pr_person",
                                    pr_person_tag = ({"name": "car",
                                                      "joinby": "person_id",
                                                      "filterby": {"tag": "car"},
                                                      "multiple": False,
                                                      },
                                                     ),
                                    )

                # Assigning Staff Checks them in
                def staff_check_in(form):

                    db = current.db
                    form_vars_get = form.vars.get
                    human_resource_id = form_vars_get("human_resource_id")

                    htable = s3db.hrm_human_resource
                    staff = db(htable.id == human_resource_id).select(htable.id,
                                                                      htable.person_id,
                                                                      limitby = (0, 1)
                                                                      ).first()

                    # Set the site_id in the Staff record
                    site_id = r.record.site_id
                    staff.update_record(site_id = site_id)

                    # Delete old hrm_human_resource_site records
                    ltable = s3db.hrm_human_resource_site
                    query = (ltable.human_resource_id == human_resource_id) & \
                            (ltable.id != form_vars_get("id"))
                    db(query).delete()

                    # Add Site Event Log
                    s3db.org_site_event.insert(site_id = site_id,
                                               person_id = staff.person_id,
                                               event = 2, # Checked-In
                                               comments = "Staff",
                                               )

                s3db.add_custom_callback("hrm_human_resource_site",
                                         "create_onaccept",
                                         staff_check_in,
                                         )

            elif r.component_name == "human_resource":
                # UNUSED
                if not r.interactive:
                    output_format = current.auth.permission.format
                    if output_format not in ("aadata", "json", "xls"):
                        # Block Exports
                        return False
                    if output_format == "xls":
                        # Add Site Event Log
                        s3db.org_site_event.insert(site_id = r.record.site_id,
                                                   event = 5, # Data Export
                                                   comments = "Staff",
                                                   )
                        # Log in Global Log
                        settings.security.audit_write = True
                        from s3 import S3Audit
                        S3Audit().__init__()
                        s3db.s3_audit.insert(timestmp = r.now,
                                             user_id = auth.user.id,
                                             method = "Data Export",
                                             representation = "Staff",
                                             )

                # Filtered components
                s3db.add_components("pr_person",
                                    pr_person_tag = ({"name": "car",
                                                      "joinby": "person_id",
                                                      "filterby": {"tag": "car"},
                                                      "multiple": False,
                                                      },
                                                     ),
                                    )

                # Override the defaulting/hiding of Organisation
                f = r.component.table.organisation_id
                f.default = None
                f.readable = f.writable = True

                # Adding Staff here Checks them in
                def staff_check_in(form):
                    s3db.org_site_event.insert(site_id = r.record.site_id,
                                               person_id = form.vars.get("person_id"),
                                               event = 2, # Checked-In
                                               comments = "Staff",
                                               )
                s3db.add_custom_callback("hrm_human_resource",
                                         "create_onaccept",
                                         staff_check_in,
                                         )

            elif r.component_name == "client":
                if not r.interactive:
                    output_format = current.auth.permission.format
                    if output_format not in ("aadata", "json", "xls"):
                        # Block Exports
                        return False
                    if output_format == "xls":
                        # Add Site Event Log
                        s3db.org_site_event.insert(site_id = r.record.site_id,
                                                   event = 5, # Data Export
                                                   comments = "Clients",
                                                   )
                        # Log in Global Log
                        settings.security.audit_write = True
                        from s3 import S3Audit
                        S3Audit().__init__()
                        s3db.s3_audit.insert(timestmp = r.now,
                                             user_id = auth.user.id,
                                             method = "Data Export",
                                             representation = "Clients",
                                             )

                if r.method == "create":
                    s3.crud_strings["cr_shelter"].title_display = T("Register Client to %(shelter)s") % \
                                                                            {"shelter": r.record.name}

                from s3 import S3TextFilter, S3OptionsFilter, S3DateFilter

                filter_widgets = [#S3TextFilter(["first_name",
                                  #              "middle_name",
                                  #              "first_name",
                                  #              "pe_label",
                                  #              "holmes.value",
                                  #              ],
                                  #             label = T("Search"),
                                  #             #_class = "filter-search",
                                  #             ),
                                  S3OptionsFilter("shelter_registration.registration_status",
                                                  label = T("Status"),
                                                  options = {#1: T("Planned"),
                                                             2: T("Checked-in"),
                                                             3: T("Checked-out"),
                                                             },
                                                  ),
                                  #S3OptionsFilter("age_group",
                                  #                label = T("Age"),
                                  #                hidden = True,
                                  #                ),
                                  #S3OptionsFilter("gender",
                                  #                hidden = True,
                                  #                ),
                                  #S3OptionsFilter("person_details.nationality",
                                  #                hidden = True,
                                  #                ),
                                  #S3OptionsFilter("pets.value",
                                  #                label = T("Pets"),
                                  #                hidden = True,
                                  #                ),
                                  #S3DateFilter("shelter_registration.check_in_date",
                                  #             #hide_time = True,
                                  #             hidden = True,
                                  #             ),
                                  #S3DateFilter("shelter_registration.check_out_date",
                                  #             #hide_time = True,
                                  #             hidden = True,
                                  #             ),
                                  ]
                s3db.configure("pr_person",
                               filter_widgets = filter_widgets,
                               )

                # Registering Client Checks them in
                def client_check_in(form):
                    form_vars_get = form.vars.get
                    person_id = form_vars_get("person_id")
                    site_id = r.record.site_id

                    # Delete old cr_shelter_registration records
                    ltable = s3db.cr_shelter_registration
                    query = (ltable.person_id == person_id) & \
                            (ltable.id != form_vars_get("id"))
                    current.db(query).delete()

                    # Update Shelter Population
                    s3db.cr_update_shelter_population(r.id)

                    # Add Site Event Log
                    s3db.org_site_event.insert(site_id = site_id,
                                               person_id = person_id,
                                               event = 2, # Checked-In
                                               comments = "Client",
                                               )

                s3db.add_custom_callback("cr_shelter_registration",
                                         "create_onaccept",
                                         client_check_in,
                                         )
            else:
                s3.crud_strings["cr_shelter"].title_update = T("Manage Shelter")

            return result
        s3.prep = prep

        # Custom postp
        standard_postp = s3.postp
        def postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.component_name == "human_resource_site":

                #from gluon import URL
                from s3 import s3_str#, S3CRUD

                # Normal Action Buttons
                S3CRUD.action_buttons(r,
                                      read_url = URL(c = "cr",
                                                     f = "shelter",
                                                     args = [r.id,
                                                             "human_resource_site",
                                                             "[id]",
                                                             "redirect",
                                                             ],
                                                     ),
                                      update_url = URL(c = "cr",
                                                       f = "shelter",
                                                       args = [r.id,
                                                               "human_resource_site",
                                                               "[id]",
                                                               "redirect",
                                                               ],
                                                       ),
                                      deletable = False)

                # Custom Action Buttons
                s3.actions += [{"label": s3_str(T("Check-Out")),
                                "url": URL(c = "cr",
                                           f = "shelter",
                                           args = [r.id,
                                                   "human_resource_site",
                                                   "[id]",
                                                   "checkout",
                                                   ],
                                           ),
                                "_class": "action-btn",
                                },
                               ]

            elif r.component_name == "client":

                #from gluon import URL
                from s3 import s3_str#, S3CRUD

                # Normal Action Buttons
                S3CRUD.action_buttons(r,
                                      read_url = URL(c = "pr",
                                                     f = "person",
                                                     args = "[id]",
                                                     ),
                                      update_url = URL(c = "pr",
                                                       f = "person",
                                                       args = "[id]",
                                                       ),
                                      deletable = False)

                # Custom Action Buttons
                s3.actions += [{"label": s3_str(T("Check-Out")),
                                "url": URL(c = "cr",
                                           f = "shelter",
                                           args = [r.id,
                                                   "client",
                                                   "[id]",
                                                   "checkout.popup",
                                                   ],
                                           vars = {"refresh": "datatable",
                                                   }
                                           ),
                                "_class": "action-btn s3_modal",
                                },
                               ]

            return output
        s3.postp = postp

        attr["rheader"] = eac_rheader

        if "client" in current.request.args:
            attr["hide_filter"] = False

        return attr

    settings.customise_cr_shelter_controller = customise_cr_shelter_controller

    # -------------------------------------------------------------------------
    def customise_cr_shelter_registration_resource(r, tablename):

        #from s3 import S3AddPersonWidget

        s3db = current.s3db
        table = s3db.cr_shelter_registration
        #table.person_id.widget = S3AddPersonWidget(pe_label = True)
        f = table.registration_status
        f.default = 2 # Checked-in
        #f.readable = f.writable = False
        #table.check_out_date.readable = table.check_out_date.writable = False
        #table.comments.readable = table.comments.writable = False

        if r.method == "import":
            # Importing Clients adds Event Log entries
            def import_event_log(form):

                form_vars_get = form.vars.get
                person_id = form_vars_get("person_id")
                shelter_id = form_vars_get("shelter_id")

                stable = s3db.cr_shelter
                shelter = current.db(stable.id == shelter_id).select(stable.site_id,
                                                                     limitby = (0, 1)
                                                                     ).first()
                site_id = shelter.site_id

                # Add Site Event Log
                s3db.org_site_event.insert(site_id = site_id,
                                           person_id = person_id,
                                           event = 2, # Checked-In
                                           comments = "Client",
                                           )

            s3db.add_custom_callback("cr_shelter_registration",
                                     "create_onaccept",
                                     import_event_log,
                                     )

    settings.customise_cr_shelter_registration_resource = customise_cr_shelter_registration_resource

    # -----------------------------------------------------------------------------
    def customise_cr_shelter_registration_controller(**attr):

        attr["csv_template"] = ("../../themes/CumbriaEAC/xls", "Client_Registration.xlsm")

        return attr

    settings.customise_cr_shelter_registration_controller = customise_cr_shelter_registration_controller

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_resource(r, tablename):

        from s3 import S3AddPersonWidget, S3SQLCustomForm, \
                       S3TextFilter, S3LocationFilter, S3OptionsFilter

        s3db = current.s3db

        settings.pr.request_dob = False
        settings.pr.request_email = False
        settings.pr.request_gender = False
        settings.pr.request_tags = [(T("Car Registration"), "car"),
                                    ]

        table = s3db.hrm_human_resource
        table.person_id.widget = S3AddPersonWidget(controller = "hrm")
        table.site_id.label = T("Shelter")

        crud_form = S3SQLCustomForm("organisation_id",
                                    "site_id",
                                    "person_id",
                                    "comments",
                                    )

        filter_widgets = [
                S3TextFilter(["person_id$first_name",
                              #"person_id$middle_name",
                              "person_id$first_name",
                              "comments",
                              "organisation_id",
                              "site_id",
                              "location_id$L3",
                              "location_id$L4",
                              "person_id$car.value",
                              ],
                             label = T("Search"),
                             #_class = "filter-search",
                             ),
                S3LocationFilter("location_id",
                                 label = T("Location"),
                                 levels = ("L3", "L4"),
                                 ),
                S3OptionsFilter("organisation_id",
                                ),
                S3OptionsFilter("site_id",
                                ),
                ]

        if r.controller == "cr":
            list_fields = ["person_id",
                           "organisation_id",
                           (T("Phone"),"phone.value"),
                           (T("Car"),"person_id$car.value"),
                           ]
        else:
            list_fields = ["person_id",
                           "organisation_id",
                           "site_id",
                           "location_id$L3",
                           "location_id$L4",
                           (T("Phone"),"phone.value"),
                           (T("Car"),"person_id$car.value"),
                           ]

        report_fields = ["organisation_id",
                         "site_id",
                         "location_id$L3",
                         "location_id$L4",
                         ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       report_options = Storage(
                        rows = report_fields,
                        cols = report_fields,
                        fact = report_fields,
                        defaults = Storage(rows = "location_id$L4", # Lowest-level of hierarchy
                                           cols = "organisation_id",
                                           fact = "count(person_id)",
                                           totals = True,
                                           )
                        ),
                       )

    settings.customise_hrm_human_resource_resource = customise_hrm_human_resource_resource

    # -----------------------------------------------------------------------------
    def customise_hrm_human_resource_controller(**attr):

        s3 = current.response.s3

        # Filtered components
        current.s3db.add_components("pr_person",
                                    pr_person_tag = ({"name": "car",
                                                      "joinby": "person_id",
                                                      "filterby": {"tag": "car"},
                                                      "multiple": False,
                                                      },
                                                     ),
                                    )

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            if not r.interactive:
                output_format = current.auth.permission.format
                if output_format not in ("aadata", "json", "xls"):
                    # Block Exports
                    return False
                if output_format == "xls":
                    # Log
                    settings.security.audit_write = True
                    from s3 import S3Audit
                    S3Audit().__init__()
                    s3db.s3_audit.insert(timestmp = r.now,
                                         user_id = auth.user.id,
                                         method = "Data Export",
                                         representation = "Staff",
                                         )

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True
            return result
        s3.prep = prep

        return attr

    settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_site_resource(r, tablename):

        from s3 import S3AddPersonWidget, S3SQLCustomForm

        s3db = current.s3db

        settings.pr.request_dob = False
        settings.pr.request_email = False
        settings.pr.request_gender = False
        settings.pr.request_tags = [(T("Car Registration"), "car"),
                                    ]

        table = s3db.hrm_human_resource_site
        table.human_resource_id.widget = S3AddPersonWidget(controller = "hrm")

        crud_form = S3SQLCustomForm("human_resource_id",
                                    )

        list_fields = ["human_resource_id$person_id",
                       "human_resource_id$organisation_id",
                       (T("Phone"),"human_resource_id$phone.value"),
                       (T("Car"),"human_resource_id$person_id$car.value"),
                       ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )

    settings.customise_hrm_human_resource_site_resource = customise_hrm_human_resource_site_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        from s3 import S3SQLCustomForm

        s3db = current.s3db

        crud_form = S3SQLCustomForm("name",
                                    "comments",
                                    )

        list_fields = ["name",
                       ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       filter_widgets = None,
                       list_fields = list_fields,
                       )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_org_site_event_resource(r, tablename):

        from s3 import S3Represent

        s3db = current.s3db

        table = s3db.org_site_event
        table.status.represent = S3Represent(options = cr_shelter_status_opts)
        table.created_by.readable = True

        s3db.configure(tablename,
                       list_fields = ["date",
                                      (T("User"), "created_by"),
                                      "event",
                                      "comments",
                                      "person_id",
                                      "status",
                                      ],
                       )

    settings.customise_org_site_event_resource = customise_org_site_event_resource

    # -------------------------------------------------------------------------
    def customise_s3_audit_resource(r, tablename):

        current.s3db.configure(tablename,
                               list_fields = [(T("Date"), "timestmp"),
                                              (T("User"), "user_id"),
                                              (T("Event"), "method"),
                                              (T("Comments"), "representation"),
                                              ],
                               )

    settings.customise_s3_audit_resource = customise_s3_audit_resource

    # -------------------------------------------------------------------------
    def pr_household_postprocess(form, parent_id):

        db = current.db
        s3db = current.s3db

        # Lookup Parent Address
        atable = s3db.pr_address
        ptable = s3db.pr_person
        query = (ptable.id == parent_id) & \
                (ptable.pe_id == atable.pe_id)
        address = db(query).select(atable.location_id,
                                   limitby = (0, 1)
                                   ).first()

        # Set this same address for this person
        atable.insert(pe_id = form.vars.pe_id,
                      location_id = address.location_id,
                      )

    # -------------------------------------------------------------------------
    def xls_title_row(sheet):
        """
            Custom XLS Title Row for clients
        """

        length = 1

        if sheet is not None:

            import xlwt

            from s3 import s3_unicode

            style = xlwt.XFStyle()
            style.font.bold = True
            style.pattern.pattern = style.pattern.SOLID_PATTERN
            style.alignment.horz = style.alignment.HORZ_CENTER
            style.pattern.pattern_fore_colour = 0x18 # periwinkle
            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1
            style.borders = borders

            labels = ((0, 8, s3_unicode(T("Client"))),
                      (9, 12, s3_unicode(T("Shelter"))),
                      (13, 17, s3_unicode(T("Next of Kin"))),
                      )

            for start_col, end_col, label in labels:

                # Write the label in merged cells
                sheet.write_merge(0, 0, start_col, end_col, label, style)

        return length

    # -------------------------------------------------------------------------
    def postprocess_select(records, rfields=None, represent=False, as_rows=False):
        """
            Post-process resource.select of pr_person to populate fields which
            cannot be expressed as components due to conflict between the master
            pr_person & the NoK pr_person

            @param records: list of selected data
            @param rfields: list of S3ResourceFields in the records
            @param represent: records contain represented data
            @param as_rows: records are bare Rows rather than extracted
                            Storage
        """

        db = current.db
        s3db = current.s3db
        ptable = s3db.pr_person

        person_ids = set(records.keys())

        # Lookup Next of Kin
        table = s3db.pr_person_relation
        query = (table.parent_id.belongs(person_ids))
        rows = db(query).select(table.parent_id,
                                table.person_id,
                                )
        noks = [row.person_id for row in rows]
        nok_lookup = {row.parent_id: row.person_id for row in rows}
        nok_lookup_get = nok_lookup.get

        # Lookup NoK Relationships
        table = s3db.pr_person_tag
        query = (table.person_id.belongs(noks)) & \
                (table.tag == "relationship")
        rows = db(query).select(table.person_id,
                                table.value,
                                )
        relationships = {row.person_id: row.value for row in rows}
        relationships_get = relationships.get

        # Lookup NoK Phones
        table = s3db.pr_contact
        query = (ptable.id.belongs(noks)) & \
                (ptable.pe_id == table.pe_id) & \
                (table.contact_method == "SMS")
        rows = db(query).select(ptable.id,
                                table.value,
                                )
        phones = {row["pr_person.id"]: row["pr_contact.value"] for row in rows}
        phones_get = phones.get

        # Lookup NoK Addresses
        table = s3db.pr_address
        query = (ptable.id.belongs(noks)) & \
                (ptable.pe_id == table.pe_id)
        rows = db(query).select(ptable.id,
                                table.location_id,
                                )
        if represent:
            address_location_ids = {}
            address_locations = {}
            address_locations_get = address_locations.get
            location_ids = [row["pr_address.location_id"] for row in rows]
            locations = table.location_id.represent.bulk(location_ids, show_link=False)
            locations_get = locations.get
            for row in rows:
                location_id = row["pr_address.location_id"]
                person_id = row["pr_person.id"]
                address_location_ids[person_id] = location_id
                address_locations[person_id] = locations_get(location_id)
        else:
            address_location_ids = {row["pr_person.id"]: row["pr_address.location_id"] for row in rows}
        address_location_ids_get = address_location_ids.get

        NONE = current.messages["NONE"]

        for person_id in person_ids:

            row = records[person_id]
            
            nok = nok_lookup_get(person_id)

            colname = "pr_person.nok_relationship"
            value = relationships_get(nok, NONE)
            if colname in row:
                row[colname] = value
            raw = row.get("_row")
            if raw:
                raw[colname] = value

            colname = "pr_person.nok_phone"
            value = phones_get(nok, NONE)
            if colname in row:
                row[colname] = value
            raw = row.get("_row")
            if raw:
                raw[colname] = value

            colname = "pr_person.nok_address"
            value = address_location_ids_get(nok, NONE)
            if colname in row:
                row[colname] = address_locations_get(nok, NONE) if represent else value
            raw = row.get("_row")
            if raw:
                raw[colname] = value

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        if r.controller == "hrm" or \
           r.component_name == "nok":
            # Done in prep
            return

        from gluon import IS_EMPTY_OR, IS_IN_SET

        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3LocationSelector, \
                       S3TextFilter, S3DateFilter, S3LocationFilter, S3OptionsFilter

        s3db = current.s3db
        s3 = current.response.s3

        household = True if r.method == "household" else False

        if household:
            s3.crud_strings["pr_person"] = Storage(
                label_create = T("Register another Household Member"),
                title_list = T("Household Members"),
                msg_list_empty = T("No Household Members currently registered")
                )
        else:
            s3.crud_strings["pr_person"] = Storage(
                label_create = T("Register a Client"),
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

        ptable = s3db.pr_person
        f = ptable.pe_label
        f.label = T("Reception Centre Ref")
        f.comment = None

        if household:
            # Address defaulted
            postprocess = lambda form: pr_household_postprocess(form, r.id)
        else:
            # Address asked for interactively
            postprocess = None
            s3db.pr_address.location_id.widget = S3LocationSelector(levels = ("L0", "L1", "L2", "L3", "L4"),
                                                                    required_levels = ("L0",),
                                                                    show_address = True,
                                                                    #address_required = True,
                                                                    #show_postcode = True,
                                                                    #postcode_required = True,
                                                                    show_map = False,
                                                                    )

        if current.auth.permission.format == "xls" and \
           r.method != "report":
            # Custom XLS Title Row
            settings.base.xls_title_row = xls_title_row

            # Filtered components
            s3db.add_components("pr_person",
                                pr_address = ({"name": "current_address",
                                               "joinby": "pe_id",
                                               "filterby": {"type": 1},
                                               "multiple": False,
                                               "pkey": "pe_id",
                                               },
                                              {"name": "permanent_address",
                                               "joinby": "pe_id",
                                               "filterby": {"type": 2},
                                               "multiple": False,
                                               "pkey": "pe_id",
                                               },
                                              ),
                                pr_person_tag = ({"name": "holmes",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "holmes"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "relationship",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "relationship"},
                                                  "multiple": False,
                                                  },
                                                 ),
                                )

            list_fields = [(T("Holmes Ref"), "holmes.value"),
                           "last_name",
                           "first_name",
                           "gender",
                           "date_of_birth",
                           "person_details.nationality",
                           (T("Phone"), "phone.value"),
                           (T("Current Address"), "current_address.location_id"),
                           (T("Permanent Address"), "permanent_address.location_id"),
                           "pe_label",
                           "shelter_registration.shelter_id",
                           "shelter_registration.check_in_date",
                           "shelter_registration.check_out_date",
                           "nok.last_name",
                           "nok.first_name",
                           (T("Relationship"), "nok_relationship"), # Fake Selector - to be populated in postprocess_select
                           (T("Phone"), "nok_phone"),
                           (T("Address"), "nok_address"),
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           postprocess_select = postprocess_select,
                           )

        else:
            # Filtered components
            s3db.add_components("pr_person",
                                pr_person_tag = ({"name": "holmes",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "holmes"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "location",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "location"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "language",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "language"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "pets",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "pets"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "pets_details",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "pets_details"},
                                                  "multiple": False,
                                                  },
                                                 #{"name": "medical",
                                                 # "joinby": "person_id",
                                                 # "filterby": {"tag": "medical"},
                                                 # "multiple": False,
                                                 # },
                                                 {"name": "disability",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "disability"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "dietary",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "dietary"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "gp",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "gp"},
                                                  "multiple": False,
                                                  },
                                                 ),
                                )

            from s3 import S3TagCheckboxWidget, s3_comments_widget

            # Individual settings for specific tag components
            components_get = s3db.resource(tablename).components.get

            pets = components_get("pets")
            f = pets.table.value
            f.requires = IS_EMPTY_OR(IS_IN_SET(("Y", "N")))
            f.represent = lambda v: T("yes") if v == "Y" else T("no")
            f.widget = S3TagCheckboxWidget(on="Y", off="N")
            f.default = "N"

            #medical = components_get("medical")
            #medical.table.value.widget = s3_comments_widget
            s3db.pr_physical_description.medical_conditions.widget = s3_comments_widget

            if current.auth.s3_has_role("POLICE", include_admin=False):
                # Only the Holmes Ref is editable
                ptable.pe_label.writable = False
                ptable.first_name.writable = False
                ptable.first_name.comment = None
                ptable.middle_name.writable = False
                ptable.last_name.writable = False
                ptable.gender.writable = False
                ptable.date_of_birth.writable = False
                ptable.comments.writable = False
                pets.table.value.writable = False
                location = components_get("location")
                location.table.value.writable = False
                language = components_get("language")
                language.table.value.writable = False
                pets_details = components_get("pets_details")
                pets_details.table.value.writable = False
                disability = components_get("disability")
                disability.table.value.writable = False
                dietary = components_get("dietary")
                dietary.table.value.writable = False
                gp = components_get("gp")
                gp.table.value.writable = False

            crud_fields = ["pe_label",
                           "first_name",
                           "middle_name",
                           "last_name",
                           "gender",
                           "date_of_birth",
                           S3SQLInlineComponent("address",
                                                name = "perm_address",
                                                label = T("Permanent Address (if different)"),
                                                multiple = False,
                                                fields = [("", "location_id")],
                                                filterby = {"field": "type",
                                                            "options": 2, # Permanent Home Address
                                                            },
                                                ),
                           (T("Location at Time of Incident"), "location.value"),
                           # Not a multiple=False component
                           #(T("Phone"), "phone.value"),
                           S3SQLInlineComponent(
                               "phone",
                               name = "phone",
                               label = T("Mobile Phone"),
                               multiple = False,
                               fields = [("", "value")],
                               #filterby = {"field": "contact_method",
                               #            "options": "SMS",
                               #            },
                           ),
                           S3SQLInlineComponent(
                               "email",
                               name = "email",
                               label = T("Email"),
                               multiple = False,
                               fields = [("", "value")],
                               #filterby = {"field": "contact_method",
                               #            "options": "EMAIL",
                               #            },
                           ),
                           (T("Pets"), "pets.value"),
                           (T("Details of Pets"), "pets_details.value"),
                           #(T("Medical Details"), "medical.value"),
                           (T("Medical Details"), "physical_description.medical_conditions"),
                           (T("Disability Details"), "disability.value"),
                           (T("Dietary Needs"), "dietary.value"),
                           (T("GP"), "gp.value"),
                           (T("Communication and Language Needs"), "language.value"),
                           "person_details.nationality",
                           "physical_description.ethnicity",
                           "person_details.religion",
                           "comments",
                           ]

            if not household:
                crud_fields.insert(6, S3SQLInlineComponent("address",
                                                           name = "address",
                                                           label = T("Current Address"),
                                                           multiple = False,
                                                           fields = [("", "location_id")],
                                                           filterby = {"field": "type",
                                                                       "options": 1, # Current Home Address
                                                                       },
                                                           ))

            if r.id and r.tablename == "pr_person":
                crud_fields.insert(1, (T("Holmes Ref"), "holmes.value"))

            crud_form = S3SQLCustomForm(*crud_fields,
                                        postprocess = postprocess
                                        )

            import json

            # Compact JSON encoding
            SEPARATORS = (",", ":")

            current.response.s3.jquery_ready.append('''S3.showHidden('%s',%s,'%s')''' % \
                ("sub_pets_value", json.dumps(["sub_pets_details_value"], separators=SEPARATORS), "pr_person"))

            filter_widgets = [
                    S3TextFilter(["first_name",
                                  "middle_name",
                                  "last_name",
                                  "pe_label",
                                  "holmes.value",
                                  ],
                                 label = T("Search"),
                                 #_class = "filter-search",
                                 ),
                    S3LocationFilter("location_id",
                                     label = T("Location"),
                                     levels = ("L3", "L4"),
                                     ),
                    S3OptionsFilter("shelter_registration.shelter_id",
                                    ),
                    S3OptionsFilter("age_group",
                                    label = T("Age"),
                                    hidden = True,
                                    ),
                    S3OptionsFilter("gender",
                                    hidden = True,
                                    ),
                    S3OptionsFilter("person_details.nationality",
                                    hidden = True,
                                    ),
                    S3OptionsFilter("pets.value",
                                    label = T("Pets"),
                                    hidden = True,
                                    ),
                    S3DateFilter("shelter_registration.check_in_date",
                                 #hide_time = True,
                                 hidden = True,
                                 ),
                    S3DateFilter("shelter_registration.check_out_date",
                                 #hide_time = True,
                                 hidden = True,
                                 ),
                    ]

            list_fields = ["last_name",
                           "first_name",
                           "shelter_registration.check_in_date",
                           "shelter_registration.check_out_date",
                           "pe_label",
                           "gender",
                           (T("Age"), "age"),
                           ]
            if r.controller == "pr":
                list_fields.insert(2, "shelter_registration.shelter_id")

            report_fields = ["gender",
                             "age_group",
                             "person_details.nationality",
                             "physical_description.ethnicity",
                             "shelter_registration.shelter_id",
                             "location_id$L3",
                             "location_id$L4",
                             ]

            from gluon import URL

            s3db.configure(tablename,
                           # Open Next of Kin tab after registration
                           create_next = URL(c="pr", f="person",
                                             args = ["[id]", "nok"],
                                             ),
                           crud_form = crud_form,
                           filter_widgets = filter_widgets,
                           listadd = True, #if household else False,
                           list_fields = list_fields,
                           report_options = Storage(
                            rows = report_fields,
                            cols = report_fields,
                            fact = report_fields,
                            defaults = Storage(rows = "location_id$L4", # Lowest-level of hierarchy
                                               cols = "age_group",
                                               fact = "count(id)",
                                               totals = True,
                                               )
                            ),
                           summary = ({"name": "table",
                                       "label": "Table",
                                       "widgets": [{"method": "datatable"}]
                                       },
                                      {"name": "report",
                                       "label": "Report",
                                       "widgets": [{"method": "report", "ajax_init": True}],
                                       },
                                      ),
                           )

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -----------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        auth = current.auth
        s3db = current.s3db
        s3 = current.response.s3

        output_format = auth.permission.format

        # Redefine as multiple=False
        s3db.add_components("pr_person",
                            pr_person = {"name": "nok",
                                         "link": "pr_person_relation",
                                         "joinby": "parent_id",
                                         "key": "person_id",
                                         "actuate": "replace",
                                         "multiple": False,
                                         },
                            )

        # Custom Method
        s3db.set_method("pr", "person",
                        method = "household",
                        action = pr_Household())

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            if not r.interactive:
                if output_format not in ("aadata", "json", "xls"):
                    # Block Exports
                    return False
                if output_format == "xls":
                    # Log
                    settings.security.audit_write = True
                    from s3 import S3Audit
                    S3Audit().__init__()
                    s3db.s3_audit.insert(timestmp = r.now,
                                         user_id = auth.user.id,
                                         method = "Data Export",
                                         representation = "Clients",
                                         )

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.component_name == "site_event":
                f = s3db.org_site_event.site_id
                f.label = T("Shelter")
                f.readable = True
                f.represent = s3db.org_SiteRepresent(show_type = False)

                return result

            elif r.component_name == "nok":
                # Next of Kin
                s3.crud_strings["pr_person"].title_update = ""
                
                from gluon import IS_NOT_EMPTY
                from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3LocationSelector

                s3db.pr_address.location_id.widget = S3LocationSelector(levels = ("L0", "L1", "L2", "L3", "L4"),
                                                                        required_levels = ("L0",),
                                                                        show_address = True,
                                                                        #address_required = True,
                                                                        #show_postcode = True,
                                                                        #postcode_required = True,
                                                                        show_map = False,
                                                                        )

                # Filtered components
                s3db.add_components("pr_person",
                                    pr_person_tag = ({"name": "relationship",
                                                      "joinby": "person_id",
                                                      "filterby": {"tag": "relationship"},
                                                      "multiple": False,
                                                      },
                                                     ),
                                    )
                # Individual settings for specific tag components
                components_get = s3db.resource("pr_person").components.get

                relationship = components_get("relationship")
                relationship.table.value.requires = IS_NOT_EMPTY() # Mandatory as used in filters

                crud_form = S3SQLCustomForm("first_name",
                                            #"middle_name",
                                            "last_name",
                                            (T("Relationship"), "relationship.value"),
                                            # Not a multiple=False component
                                            #(T("Phone"), "phone.value"),
                                            S3SQLInlineComponent(
                                                "phone",
                                                name = "phone",
                                                label = T("Mobile Phone"),
                                                multiple = False,
                                                fields = [("", "value")],
                                                #filterby = {"field": "contact_method",
                                                #            "options": "SMS",
                                                #            },
                                            ),
                                            S3SQLInlineComponent(
                                                "address",
                                                name = "address",
                                                label = T("Address"),
                                                multiple = False,
                                                fields = [("", "location_id")],
                                                filterby = {"field": "type",
                                                            "options": 1, # Current Home Address
                                                            },
                                            ),
                                            "comments",
                                            )

                s3db.configure("pr_person",
                               crud_form = crud_form,
                               deletable = False,
                               )

                return result

            elif r.controller in ("hrm", "default"):
                
                from s3 import S3SQLCustomForm, S3SQLInlineComponent

                if r.method == "lookup":
                    settings.pr.request_dob = False
                    settings.pr.request_email = False
                    settings.pr.request_gender = False
                    settings.pr.request_tags = [(T("Car Registration"), "car"),
                                                ]

                # Filtered components
                s3db.add_components("pr_person",
                                    pr_person_tag = ({"name": "car",
                                                      "joinby": "person_id",
                                                      "filterby": {"tag": "car"},
                                                      "multiple": False,
                                                      },
                                                     ),
                                    )

                crud_form = S3SQLCustomForm(S3SQLInlineComponent(
                                                "human_resource",
                                                name = "human_resource",
                                                label = T("Organization"),
                                                multiple = False,
                                                fields = [("", "organisation_id")],
                                            ),
                                            "first_name",
                                            #"middle_name",
                                            "last_name",
                                            # Not a multiple=False component
                                            #(T("Phone"), "phone.value"),
                                            S3SQLInlineComponent(
                                                "phone",
                                                name = "phone",
                                                label = T("Mobile Phone"),
                                                multiple = False,
                                                fields = [("", "value")],
                                                #filterby = {"field": "contact_method",
                                                #            "options": "SMS",
                                                #            },
                                            ),
                                            (T("Car Registration"), "car.value"),
                                            "comments",
                                            )

                s3db.configure("pr_person",
                               crud_form = crud_form,
                               )

                return result

            if r.method == "household" and r.http == "POST":
                # Is Person checked-in?
                person_id = r.id
                db = current.db
                ltable = s3db.cr_shelter_registration
                query = (ltable.person_id == person_id) & \
                        (ltable.deleted != True)
                registration = db(query).select(ltable.shelter_id,
                                                limitby = (0, 1)
                                                ).first()
                if registration:
                    # Registering Client Checks them in
                    def household_check_in(form):

                        shelter_id = registration.shelter_id
                        person_id = form.vars.id

                        stable = s3db.cr_shelter
                        shelter = db(stable.id == shelter_id).select(stable.site_id,
                                                                     limitby = (0, 1)
                                                                     ).first()
                        site_id = shelter.site_id

                        # Add cr_shelter_registration record
                        ltable.insert(person_id = person_id,
                                      shelter_id = shelter_id,
                                      check_in_date = current.request.utcnow,
                                      registration_status = 2,
                                      )

                        # Update Shelter Population
                        s3db.cr_update_shelter_population(shelter_id)

                        # Add Site Event Log
                        s3db.org_site_event.insert(site_id = site_id,
                                                   person_id = person_id,
                                                   event = 2, # Checked-In
                                                   comments = "Client",
                                                   )

                    s3db.add_custom_callback("pr_person",
                                             "create_onaccept",
                                             household_check_in,
                                             )

            from s3 import FS

            resource = r.resource

            # Filter out Users
            resource.add_filter(FS("user.id") == None)

            # Filter out Staff
            resource.add_filter(FS("human_resource.id") == None)

            # Filter out Next of Kin
            s3db.add_components("pr_person",
                                pr_person_tag = ({"name": "relationship",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "relationship"},
                                                  "multiple": False,
                                                  },
                                                 ),
                                )
            resource.add_filter(FS("relationship.id") == None)

            return result
        s3.prep = prep

        # Custom postp
        standard_postp = s3.postp
        def postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.method == "household":

                action_methods = list(s3.action_methods)
                action_methods.append("household")
                s3.action_methods = action_methods

                from gluon import URL
                #from s3 import s3_str#, S3CRUD

                # Normal Action Buttons
                S3CRUD.action_buttons(r,
                                      read_url = URL(c = "pr",
                                                     f = "person",
                                                     args = ["[id]"],
                                                     ),
                                      update_url = URL(c = "pr",
                                                       f = "person",
                                                       args = ["[id]"],
                                                       ),
                                      deletable = False)

            return output
        s3.postp = postp

        attr["rheader"] = eac_rheader
        if output_format == "xls":
            attr["evenodd"] = True
            attr["use_colour"] = True

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

# =============================================================================
class pr_Household(S3CRUD):
    """
        A Household are people who share a common Current Address
        - e.g. family or students sharing
        - handled on-site as a set of forms stapled together
    """

    # -------------------------------------------------------------------------
    def __call__(self, r, method=None, widget_id=None, **attr):
        """
            Entry point for the REST interface

            @param r: the S3Request
            @param method: the method established by the REST interface
            @param widget_id: widget ID
            @param attr: dict of parameters for the method handler

            @return: output object to send to the view
        """

        # Environment of the request
        self.request = r

        # Settings
        response = current.response
        self.download_url = response.s3.download_url

        # Init
        self.next = None

        # Override request method
        self.method = "list"

        self.record_id = None

        s3db = current.s3db
        ptable = s3db.pr_person
        atable = s3db.pr_address
        gtable = s3db.gis_location
        query = (ptable.id == r.id) & \
                (ptable.pe_id == atable.pe_id) & \
                (atable.type == 1) & \
                (atable.location_id == gtable.id) & \
                (gtable.level == None)
        address = current.db(query).select(atable.location_id,
                                           limitby = (0, 1)
                                           ).first()
        if not address:
            from gluon import redirect, URL
            current.session.warning = current.T("Client has no Current Address to share with a Household!")
            redirect(URL(args = r.id))

        address_filter = (ptable.id != r.id) & \
                         (ptable.pe_id == atable.pe_id) & \
                         (atable.location_id == address.location_id)

        resource = current.s3db.resource("pr_person", filter=address_filter)

        self.prefix = resource.prefix
        self.name = resource.name
        self.tablename = resource.tablename
        self.table = resource.table
        self.resource = resource

        if self.method == "_init":
            return None

        self.hide_filter = True

        # Apply method
        output = self.apply_method(r, **attr)

        # Redirection
        if self.next and resource.lastid:
            self.next = str(self.next)
            placeholder = "%5Bid%5D"
            self.next = self.next.replace(placeholder, resource.lastid)
            placeholder = "[id]"
            self.next = self.next.replace(placeholder, resource.lastid)
        if not response.error:
            r.next = self.next

        # Add additional view variables (e.g. rheader)
        self._extend_view(output, r, **attr)

        return output

# END =========================================================================
