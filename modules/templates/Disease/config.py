# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Disease Tracking
    """

    T = current.T

    settings.base.system_name = T("Sahana Disease Tracking")
    #settings.base.system_name_short = T("Sahana")

    # PrePopulate data
    settings.base.prepopulate += ("Disease",)
    #settings.base.prepopulate_demo += ("Disease/Demo",)

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "skeleton"
    # Custom Logo
    #settings.ui.menu_logo = "/%s/static/themes/<templatename>/img/logo.png" % current.request.application

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    settings.auth.registration_requires_approval = True
    # Required for access to default realm permissions
    #settings.auth.registration_link_user_to = ["staff"]
    #settings.auth.registration_link_user_to_default = ["staff"]

    settings.auth.registration_requests_organisation = True
    settings.auth.registration_requests_site = True

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

    # Default language for Language Toolbar (& GIS Locations in future)
    #settings.L10n.default_language = "en"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    #settings.L10n.timezone = "Europe/Berlin"
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
    #settings.fin.currencies = {
    #    "EUR" : "Euros",
    #    "GBP" : "Great British Pounds",
    #    "USD" : "United States Dollars",
    #}
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
    settings.security.policy = 7 # Organisation-ACLs with Hierarchy

    def rgims_realm_entity(table, row):
        """
            Assign a Realm Entity to records
        """

        tablename = table._tablename
        if tablename not in ("inv_recv", "inv_send"):
            # Normal lookup
            return 0

        # For these tables we need to assign the site_id's realm not organisation_id's
        db = current.db
        stable = db.org_site
        record = db(stable.site_id == row.site_id).select(stable.realm_entity,
                                                          limitby=(0, 1)
                                                          ).first()
        if record:
            return record.realm_entity

        # Normal lookup
        return 0

    settings.auth.realm_entity = rgims_realm_entity

    settings.req.req_type = ["Stock"]

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
        ("med", Storage(
            name_nice = T("Hospitals"),
            #description = "Helps to monitor status of hospitals",
            restricted = True,
            module_type = 2,
        )),
        ("disease", Storage(
            name_nice = T("Disease Tracking"),
            #description = "Helps to monitor status of cases",
            restricted = True,
            module_type = 1,
        )),
        ("stats", Storage(
            name_nice = T("Statistics"),
            #description = "Manages statistics",
            restricted = True,
            module_type = None,
        )),
        # HRM is required for access to default realm permissions
        ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 10,
        )),
        ("supply", Storage(
            name_nice = T("Supply Chain Management"),
            #description = "Used within Inventory Management, Request Management and Asset Management",
            restricted = True,
            module_type = None, # Not displayed
        )),
        ("inv", Storage(
            name_nice = T("Warehouses"),
            #description = "Receiving and Sending Items",
            restricted = True,
            module_type = 10,
        )),
        ("req", Storage(
            name_nice = T("Requests"),
            #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
            restricted = True,
            module_type = 3,
        )),
        #("vol", Storage(
        #    name_nice = T("Volunteers"),
        #    #description = "Human Resources Management",
        #    restricted = True,
        #    module_type = 2,
        #)),
        #("msg", Storage(
        #    name_nice = T("Messaging"),
        #    #description = "Sends & Receives Alerts via Email & SMS",
        #    restricted = True,
        #    # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
        #    module_type = None,
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
        #("project", Storage(
        #    name_nice = T("Projects"),
        #    #description = "Tracking of Projects, Activities and Tasks",
        #    restricted = True,
        #    module_type = 2
        #)),
        #("cr", Storage(
        #    name_nice = T("Shelters"),
        #    #description = "Tracks the location, capacity and breakdown of victims in Shelters",
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
    ])

    # -----------------------------------------------------------------------------
    def customise_med_hospital_resource(r, tablename):

        if r.representation == "geojson":
            # Don't represent the facility_status as numbers are smaller to xmit
            current.s3db.med_status.facility_status.represent = None
            return

        # Limit options to just those used & relabel them for context
        med_facility_type_opts = {
            1: T("Hospital"),
            #2: T("Field Hospital"),
            #3: T("Specialized Hospital"),
            #11: T("Health center"),
            #12: T("Health center with beds"),
            #13: T("Health center without beds"),
            #21: T("Dispensary"),
            #31: T("Long-term care"),
            #41: T("Emergency Treatment Centre"),
            41: T("ETC"),
            42: T("Triage"),
            43: T("Holding Center"),
            44: T("Transit Center"),
            #98: T("Other"),
            99: T("Unknown"),
        }

        med_facility_status_opts = {
            #1: T("Normal"),
            1: T("Functioning"),
            #2: T("Compromised"),
            #3: T("Evacuating"),
            4: T("Closed"),
            5: T("Pending"),
            #99: T("No Response")
        }

        from gluon import IS_EMPTY_OR, IS_IN_SET
        from s3 import S3Represent

        s3db = current.s3db

        field = s3db.med_hospital.facility_type
        field.represent = S3Represent(options = med_facility_type_opts)
        field.requires = IS_EMPTY_OR(IS_IN_SET(med_facility_type_opts))

        field = s3db.med_status.facility_status
        field.represent = S3Represent(options = med_facility_status_opts)
        field.requires = IS_EMPTY_OR(IS_IN_SET(med_facility_status_opts))

    settings.customise_med_hospital_resource = customise_med_hospital_resource

    # -----------------------------------------------------------------------------
    def customise_disease_stats_data_resource(r, tablename):

        s3db = current.s3db
        # Load model & set defaults
        table = s3db.disease_stats_data

        # Add a TimePlot tab to summary page
        summary = settings.get_ui_summary()
        settings.ui.summary = list(summary) + [{"name": "timeplot",
                                                "label": "Progression",
                                                "widgets": [{"method": "timeplot",
                                                             "ajax_init": True,
                                                             }
                                                            ],
                                                }]

        # Default parameter filter
        def default_parameter_filter(selector, tablename=None):
            ptable = s3db.stats_parameter
            query = (ptable.deleted == False) & \
                    (ptable.name == "Cases")
            row = current.db(query).select(ptable.parameter_id,
                                           limitby = (0, 1)
                                           ).first()
            if row:
                return row.parameter_id
            else:
                return None

        # Set filter defaults
        resource = r.resource
        filter_widgets = resource.get_config("filter_widgets", [])
        for filter_widget in filter_widgets:
            if filter_widget.field == "parameter_id":
                filter_widget.opts.default = default_parameter_filter
            elif filter_widget.field == "location_id$level":
                filter_widget.opts.default = "L2"

    settings.customise_disease_stats_data_resource = customise_disease_stats_data_resource

    # -----------------------------------------------------------------------------
    def customise_stats_demographic_data_resource(r, tablename):

        s3db = current.s3db
        # Load model & set defaults
        table = s3db.stats_demographic_data

        # Default parameter filter
        def default_parameter_filter(selector, tablename=None):
            ptable = s3db.stats_parameter
            query = (ptable.deleted == False) & \
                    (ptable.name == "Population Total")
            row = current.db(query).select(ptable.parameter_id,
                                           limitby = (0, 1)
                                           ).first()
            if row:
                return row.parameter_id
            else:
                return None

        # Set filter defaults
        resource = r.resource
        filter_widgets = resource.get_config("filter_widgets", [])
        for filter_widget in filter_widgets:
            if filter_widget.field == "parameter_id":
                filter_widget.opts.default = default_parameter_filter
            elif filter_widget.field == "location_id$level":
                filter_widget.opts.default = "L2"

    settings.customise_stats_demographic_data_resource = customise_stats_demographic_data_resource

# END =========================================================================
