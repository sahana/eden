# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Volunteer Managament application
        designed to be used along with a location template &, if-required, a custom template
    """

    T = current.T

    settings.base.system_name = T("Sahana Volunteer Management")
    settings.base.system_name_short = T("Sahana VMS")

    # PrePopulate data
    settings.base.prepopulate += ("VM",)
    #settings.base.prepopulate_demo += ("VM/Demo",)

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    #settings.auth.registration_requests_organisation = True
    settings.auth.registration_requests_mobile_phone = True
    # Uncomment this to direct newly-registered users to their volunteer page to be able to add extra details
    # NB This requires Verification/Approval to be Off
    # @ToDo: Extend to all optional Profile settings: Homepage, Twitter, Facebook, Mobile Phone, Image
    #settings.auth.registration_volunteer = True
    # Terms of Service to be able to Register on the system
    # https://termsfeed.com/terms-conditions/generator/
    # uses <template>/views/tos.html
    #settings.auth.terms_of_service = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"

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
    #
    #settings.security.policy = 7 # Organisation-ACLs

    # Options: @ToDo: make these configurable via Setup Wizard
    settings.hrm.unavailability = True
    settings.org.facility_shifts = True

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
        ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 2,
        )),
        ("vol", Storage(
            name_nice = T("Volunteers"),
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
        #("dvr", Storage(
        #   name_nice = T("Disaster Victim Registry"),
        #   #description = "Allow affected individuals & households to register to receive compensation and distributions",
        #   restricted = True,
        #   module_type = 10,
        #)),
        #("po", Storage(
        #   name_nice = T("Project Outreach"),
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

    # -----------------------------------------------------------------------------
    def customise_hrm_shift_controller(**attr):

        s3 = current.response.s3

        # Custom postp
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)

            if r.method == "assign":

                s3db = current.s3db
                f = s3db.org_site_shift.site_id
                f.label = T("Site")
                f.represent = s3db.org_site_represent
                s3db.hrm_human_resource_shift.human_resource_id.label = T("Currently Assigned")

                # Default Filters
                tablename = "hrm_human_resource"
                from s3 import s3_set_default_filter
                record = r.record
                job_title_id = record.job_title_id
                if job_title_id:
                    s3_set_default_filter("~.job_title_id",
                                          job_title_id,
                                          tablename = tablename)
                skill_id = record.skill_id
                if skill_id:
                    s3_set_default_filter("competency.skill_id",
                                          skill_id,
                                          tablename = tablename)
                # NB Availability Filter is custom,
                # so needs the pr_availability_filter applying manually to take effect
                s3_set_default_filter("available",
                                      {"ge": record.start_date,
                                       "le": record.end_date,
                                       },
                                      tablename = tablename)

            return True

        s3.prep = prep

        return attr

    settings.customise_hrm_shift_controller = customise_hrm_shift_controller

# END =========================================================================