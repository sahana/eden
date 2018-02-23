# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template settings for RGIMS:
        Relief Goods and Inventory Management System

        http://eden.sahanafoundation.org/wiki/Deployments/Philippines/RGIMS
    """

    T = current.T

    settings.base.system_name = "Relief Goods Inventory & Monitoring System"
    settings.base.system_name_short = "RGIMS"

    # Pre-Populate
    settings.base.prepopulate += ("historic/RGIMS", "default/users")

    # Theme
    settings.base.theme = "historic.RGIMS"

    # Uncomment to Hide the language toolbar
    settings.L10n.display_toolbar = False
    # Default timezone for users
    settings.L10n.utc_offset = "+0800"

    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."

    # Finance settings
    settings.fin.currencies = {
        "USD" : "United States Dollars",
        "EUR" : "Euros",
        "PHP" : "Philippine Pesos",
    }
    settings.fin.currency_default = "PHP"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    settings.gis.countries= ("PH",)

    # Security Policy
    settings.security.policy = 6 # Warehouse-specific restrictions
    settings.security.map = True

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

    # Enable this for a UN-style deployment
    settings.ui.cluster = True
    # Enable this to use the label 'Camp' instead of 'Shelter'
    settings.ui.camp = True

    # Requests
    settings.req.use_commit = False
    settings.req.req_form_name = "Request Issue Form"
    settings.req.req_shortname = "RIS"
    # Restrict the type of requests that can be made, valid values in the
    # list are ["Stock", "People", "Other"]. If this is commented out then
    # all types will be valid.
    settings.req.req_type = ["Stock"]

    # Inventory Management
    settings.inv.send_form_name = "Tally Out Sheet"
    settings.inv.send_short_name = "TOS"
    settings.inv.send_ref_field_name = "Tally Out Number"
    settings.inv.recv_form_name = "Acknowledgement Receipt for Donations Received Form"
    settings.inv.recv_shortname = "ARDR"
    settings.inv.recv_type = {
        #0: T("-"),
        #1: T("Other Warehouse"),
        32: T("Donation"),
        33: T("Foreign Donation"),
        34: T("Local Purchases"),
        35: T("Confiscated Goods from Bureau Of Customs")
        }

    # Comment/uncomment modules here to disable/enable them
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
                module_type = 10
            )),
        # All modules below here should be possible to disable safely
        ("hrm", Storage(
                name_nice = T("Staff"),
                #description = "Human Resources Management",
                restricted = True,
                module_type = 10,
            )),
        #("cms", Storage(
        #      name_nice = T("Content Management"),
        #      #description = "Content Management System",
        #      restricted = True,
        #      module_type = 10,
        #  )),
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
                name_nice = T("Supply Chain Management"),
                #description = "Used within Inventory Management, Request Management and Asset Management",
                restricted = True,
                module_type = None, # Not displayed
            )),
        ("inv", Storage(
                name_nice = T("Warehouses"),
                #description = "Receiving and Sending Items",
                restricted = True,
                module_type = 1
            )),
        #("proc", Storage(
        #        name_nice = T("Procurement"),
        #        #description = "Ordering & Purchasing of Goods & Services",
        #        restricted = True,
        #        module_type = 10
        #    )),
        ("asset", Storage(
                name_nice = T("Assets"),
                #description = "Recording and Assigning Assets",
                restricted = True,
                module_type = 10,
            )),
        # Vehicle depends on Assets
        #("vehicle", Storage(
        #        name_nice = T("Vehicles"),
        #        #description = "Manage Vehicles",
        #        restricted = True,
        #        module_type = 10,
        #    )),
        ("req", Storage(
            name_nice = T("Requests"),
            #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
            restricted = True,
            module_type = 2,
        )),
        #("project", Storage(
        #        name_nice = T("Projects"),
        #        #description = "Tracking of Projects, Activities and Tasks",
        #        restricted = True,
        #        module_type = 10
        #    )),
        #("survey", Storage(
        #        name_nice = T("Surveys"),
        #        #description = "Create, enter, and manage surveys.",
        #        restricted = True,
        #        module_type = 10,
        #    )),
        #("cr", Storage(
        #        name_nice = T("Shelters"),
        #        #description = "Tracks the location, capacity and breakdown of victims in Shelters",
        #        restricted = True,
        #       module_type = 10
        #    )),
        #("hms", Storage(
        #        name_nice = T("Hospitals"),
        #        #description = "Helps to monitor status of hospitals",
        #        restricted = True,
        #        module_type = 10
        #    )),
        #("irs", Storage(
        #        name_nice = T("Incidents"),
        #        #description = "Incident Reporting System",
        #        restricted = False,
        #        module_type = 10
        #    )),
    ])

# END =========================================================================
