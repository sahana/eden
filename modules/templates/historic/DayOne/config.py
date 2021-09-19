# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        DayOne Disaster Relief's COVID-19 Response
    """

    T = current.T

    #settings.base.system_name = T("Sahana DayOne")
    #settings.base.system_name_short = T("Sahana")

    # PrePopulate data
    settings.base.prepopulate += ("DayOne",)
    #settings.base.prepopulate_demo += ("DayOne/Demo",)

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "DayOne"
    # Custom Logo
    #settings.ui.menu_logo = "/%s/static/themes/<templatename>/img/logo.png" % current.request.application

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    settings.auth.registration_requires_approval = True
    #settings.auth.registration_requests_organisation = True
    # Required for access to default realm permissions
    #settings.auth.registration_link_user_to = ["staff"]
    #settings.auth.registration_link_user_to_default = ["staff"]

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    settings.gis.countries = ("US",)
    # Uncomment to display the Map Legend as a floating DIV, so that it is visible on Summary Map
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar, GIS Locations, etc)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    #settings.L10n.languages = OrderedDict([
    #    ("en", "English"),
    #    ("es", "Spanish"),
    #])
    # Default language for Language Toolbar (& GIS Locations in future)
    #settings.L10n.default_language = "en"
    # Uncomment to Hide the language toolbar
    settings.L10n.display_toolbar = False
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
    # 8: Apply Controller, Function, Table ACLs, Entity Realm + Hierarchy and Delegations
    
    settings.security.policy = 5 # Table-ACLs

    settings.req.req_type = ["Stock"]
    settings.req.summary = True

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
            module_type = 4
        )),
        ("req", Storage(
            name_nice = T("Requests"),
            #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
            restricted = True,
            module_type = 10,
        )),
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
        ("hms", Storage(
            name_nice = T("Hospitals"),
            #description = "Helps to monitor status of hospitals",
            restricted = True,
            module_type = 10
        )),
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
        ("transport", Storage(
           name_nice = T("Transport"),
           restricted = True,
           module_type = 10,
        )),
        ("fire", Storage(
           name_nice = T("Fire Stations"),
           restricted = True,
           module_type = 10,
        )),
        #("stats", Storage(
        #    name_nice = T("Statistics"),
        #    #description = "Manages statistics",
        #    restricted = True,
        #    module_type = None,
        #)),
    ])

    # -----------------------------------------------------------------------------
    def customise_req_req_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_IN_SET, SPAN
        from s3 import S3DateFilter, S3LocationFilter, S3OptionsFilter, S3Represent, S3TextFilter

        s3db = current.s3db

        req_status_opts = {
            0:  SPAN(T("None"),
                     _class = "req_status_none",
                     ),
            1:  SPAN(T("Partial"),
                     _class = "req_status_partial",
                     ),
            2:  SPAN(T("Complete"),
                     _class = "req_status_complete",
                     ),
        }

        f = s3db.req_req.req_status
        f.readable = f.writable = True
        f.represent = S3Represent(options = req_status_opts)
        f.requires = IS_EMPTY_OR(IS_IN_SET(req_status_opts))

        f = s3db.req_req.security_req
        f.readable = f.writable = True
        f.label = T("Needs Financing?")

        filter_widgets = [
            S3TextFilter([#"committer_id$first_name",
                          #"committer_id$middle_name",
                          #"committer_id$last_name",
                          "req_item.item_id",
                          "site_id$name",
                          "comments",
                          #"req_id$name",
                          #"organisation_id$name"
                          ],
                         label = T("Search"),
                         #comment = T("Search for a commitment by Committer name, Request ID, Site or Organization."),
                         comment = T("Search for a request by Item, Site or Comments"),
                         ),
            S3LocationFilter("site_id$location_id",
                             levels = ("L1", "L2"),
                             ),
            S3OptionsFilter("req_item.item_id",
                            ),
            S3OptionsFilter("req_status",
                            cols = 3,
                            options = req_status_opts,
                            ),
            S3OptionsFilter("security_req",
                            cols = 2,
                            ),
            #S3OptionsFilter("commit_status",
            #                cols = 3,
            #                hidden = True,
            #                ),
            #S3OptionsFilter("transit_status",
            #                cols = 3,
            #                hidden = True,
            #                ),
            #S3OptionsFilter("fulfil_status",
            #                cols = 3,
            #                hidden = True,
            #                ),
            S3OptionsFilter("site_id",
                            hidden = True,
                            ),
            S3OptionsFilter("created_by",
                            label = T("Logged By"),
                            hidden = True,
                            ),
            S3DateFilter("date",
                         # Better to default (easier to customise/consistency)
                         #label = T("Date Requested"),
                         hide_time = True,
                         input_labels = {"ge": "From", "le": "To"},
                         comment = T("Search for requests made between these dates."),
                         hidden = True,
                         ),
            #S3DateFilter("date_required",
            #             # Better to default (easier to customise/consistency)
            #             #label = T("Date Needed By"),
            #             hide_time = True,
            #             input_labels = {"ge": "From", "le": "To"},
            #             comment = T("Search for requests required between these dates."),
            #             hidden = True,
            #             ),
            ]

        list_fields = ["date",
                       "site_id",
                       "req_status",
                       "req_item.item_id",
                       "security_req",
                       ]

        s3db.configure("req_req",
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_req_req_resource = customise_req_req_resource

    # -----------------------------------------------------------------------------
    def customise_req_req_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if not r.component:
                from s3 import S3SQLCustomForm, S3SQLInlineComponent

                s3.crud.submit_button = T("Save")

                s3db = current.s3db

                # Dropdown not Autocomplete
                itable = s3db.req_req_item
                itable.item_id.widget = None
                jquery_ready = s3.jquery_ready
                jquery_ready.append('''
$.filterOptionsS3({
 'trigger':{'alias':'req_item','name':'item_id'},
 'target':{'alias':'req_item','name':'item_pack_id'},
 'scope':'row',
 'lookupPrefix':'supply',
 'lookupResource':'item_pack',
 'msgNoRecords':i18n.no_packs,
 'fncPrep':S3.supply.fncPrepItem,
 'fncRepresent':S3.supply.fncRepresentItem
})''')

                crud_form = S3SQLCustomForm("site_id",
                                            "requester_id",
                                            "date",
                                            S3SQLInlineComponent(
                                                "req_item",
                                                label = T("Items"),
                                                fields = ["item_id",
                                                          "item_pack_id",
                                                          "quantity",
                                                          "comments"
                                                          ]
                                                ),
                                            "security_req",
                                            "req_status",
                                            "comments",
                                            )

                s3db.configure("req_req",
                               crud_form = crud_form,
                               )

            return result
        s3.prep = prep

        return attr

    settings.customise_req_req_controller = customise_req_req_controller

# END =========================================================================
