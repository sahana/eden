# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current, URL
from gluon.storage import Storage

def config(settings):
    """
        Settings for the SHARE Teamplate
    """

    T = current.T

    settings.base.system_name = T("Humanitarian Country Team (HCT) Relief and Rehabilitation System")
    settings.base.system_name_short = T("SHARE")

    # UI Settings
    settings.ui.menu_logo = URL(c = "static",
                                f = "themes",
                                args = ["SHARE", "sharemenulogo.png"],
                                )

    # PrePopulate data
    settings.base.prepopulate += ("SHARE", "default/users")

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "SHARE"

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True
    #settings.auth.registration_organisation_required = True
    #settings.auth.registration_requests_site = True

    settings.auth.registration_link_user_to = {"staff": T("Staff"),
                                               "volunteer": T("Volunteer"),
                                               #"member": T("Member")
                                               }

    def registration_organisation_default(default):
        auth = current.auth
        has_role = auth.s3_has_role
        if has_role("ORG_ADMIN") and not has_role("ADMIN"):
            return auth.user.organisation_id
        else:
            return default

    settings.auth.registration_organisation_default = registration_organisation_default

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    #settings.gis.countries = ("US",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # L10n settings
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

    settings.security.policy = 6 # Controller, Function, Table ACLs and Entity Realm

    # -------------------------------------------------------------------------
    # Events
    settings.event.label = "Disaster"

    # -------------------------------------------------------------------------
    # Messaging
    settings.msg.parser = "SAMBRO" # for parse_tweet

    # -------------------------------------------------------------------------
    # Organisations
    settings.org.sector = True
    # Show Organisation Types in the rheader
    settings.org.organisation_type_rheader = True

    # -------------------------------------------------------------------------
    # Projects
    settings.project.activity_sectors = True
    # Links to Filtered Components for Donors & Partners
    settings.project.organisation_roles = {
        1: T("Agency"),
        2: T("Implementing Partner"),
        3: T("Donor"),
    }

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # Modules menu is defined in modules/eden/menu.py
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
            name_nice = "Home",
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None  # This item is not shown in the menu
        )),
        ("admin", Storage(
            name_nice = "Administration",
            #description = "Site Administration",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        ("appadmin", Storage(
            name_nice = "Administration",
            #description = "Site Administration",
            restricted = True,
            module_type = None  # No Menu
        )),
        ("errors", Storage(
            name_nice = "Ticket Viewer",
            #description = "Needed for Breadcrumbs",
            restricted = False,
            module_type = None  # No Menu
        )),
        ("sync", Storage(
            name_nice = "Synchronization",
            #description = "Synchronization",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        #("tour", Storage(
        #    name_nice = T("Guided Tour Functionality"),
        #    module_type = None,
        #)),
        ("translate", Storage(
            name_nice = T("Translation Functionality"),
            #description = "Selective translation of strings based on module.",
            module_type = None,
        )),
        ("gis", Storage(
            name_nice = "Map",
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 6,     # 6th item in the menu
        )),
        ("pr", Storage(
            name_nice = "Person Registry",
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
        ("org", Storage(
            name_nice = "Organizations",
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 1
        )),
        ("hrm", Storage(
            name_nice = "Staff",
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
          name_nice = "Content Management",
          #description = "Content Management System",
          restricted = True,
          module_type = 10,
        )),
        ("doc", Storage(
            name_nice = "Documents",
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
            module_type = 10,
        )),
        ("msg", Storage(
            name_nice = "Messaging",
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
        ("supply", Storage(
            name_nice = "Supply Chain Management",
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
        ("asset", Storage(
            name_nice = "Assets",
            #description = "Recording and Assigning Assets",
            restricted = True,
            module_type = 5,
        )),
        # Vehicle depends on Assets
        #("vehicle", Storage(
        #    name_nice = "Vehicles",
        #    #description = "Manage Vehicles",
        #    restricted = True,
        #    module_type = 10,
        #)),
        ("req", Storage(
            name_nice = "Requests",
            #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
            restricted = True,
            module_type = 10,
        )),
        ("project", Storage(
            name_nice = "Tasks",
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
        #("dvr", Storage(
        #   name_nice = T("Disaster Victim Registry"),
        #   #description = "Allow affected individuals & households to register to receive compensation and distributions",
        #   restricted = True,
        #   module_type = 10,
        #)),
        ("event", Storage(
            name_nice = "Events",
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

    # -------------------------------------------------------------------------
    def customise_msg_twitter_channel_resource(r, tablename):

        s3db = current.s3db
        def onaccept(form):
            # Normal onaccept
            s3db.msg_channel_onaccept(form)
            _id = form.vars.id
            db = current.db
            table = db.msg_twitter_channel
            channel_id = db(table.id == _id).select(table.channel_id,
                                                    limitby=(0, 1)).first().channel_id
            # Link to Parser
            table = s3db.msg_parser
            _id = table.insert(channel_id=channel_id, function_name="parse_tweet", enabled=True)
            s3db.msg_parser_enable(_id)

            async = current.s3task.async
            # Poll
            async("msg_poll", args=["msg_twitter_channel", channel_id])

            # Parse
            async("msg_parse", args=[channel_id, "parse_tweet"])

        s3db.configure(tablename,
                       create_onaccept = onaccept,
                       )

    settings.customise_msg_twitter_channel_resource = customise_msg_twitter_channel_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink, s3_comments_widget

        s3db = current.s3db
        s3db.org_organisation_tag.value.widget = s3_comments_widget

        crud_form = S3SQLCustomForm("name",
                                    "acronym",
                                    S3SQLInlineLink(
                                        "organisation_type",
                                        field = "organisation_type_id",
                                        # Default 10 options just triggers which adds unnecessary complexity to a commonly-used form & commonly an early one (create Org when registering)
                                        filter = False,
                                        label = T("Type"),
                                        multiple = False,
                                        widget = "multiselect",
                                    ),
                                    S3SQLInlineLink("sector",
                                       columns = 4,
                                       label = T("Sectors"),
                                       field = "sector_id",
                                       ),
                                    S3SQLInlineLink("service",
                                       columns = 4,
                                       label = T("Services"),
                                       field = "service_id",
                                       ),
                                    "country",
                                    "phone",
                                    "website",
                                    "logo",
                                    (T("About"), "comments"),
                                    S3SQLInlineComponent("tag",
                                       label = T("Vision"),
                                       fields = [("", "value")],
                                       filterby = {"field": "tag",
                                                   "options": "vision",
                                                   },
                                       multiple = False,
                                       ),
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_org_sector_controller(**attr):

        s3db = current.s3db
        tablename = "org_sector"

        # Just 1 set of sectors / sector leads nationally
        # @ToDo: Deployment Setting
        #f = s3db.org_sector.location_id
        #f.readable = f.writable = False

        # Custom Component for Sector Leads
        s3db.add_components(tablename,
                            org_sector_organisation = {"name": "sector_lead",
                                                       "joinby": "sector_id",
                                                       "filterby": {"lead": True,
                                                                    },
                                                       },
                            )
                                              
        from s3 import S3SQLCustomForm, S3SQLInlineComponent
        crud_form = S3SQLCustomForm("name",
                                    "abrv",
                                    "comments",
                                    S3SQLInlineComponent("sector_organisation",
                                                         label = T("Lead Organization(s)"),
                                                         fields = [("", "organisation_id"),],
                                                         filterby = ({"field": "lead",
                                                                      "options": True,
                                                                      },),
                                                         ),
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = ["name",
                                      "abrv",
                                      (T("Lead Organization(s)"), "sector_lead.organisation_id"),
                                      ],
                       )

        return attr
        
    settings.customise_org_sector_controller = customise_org_sector_controller

    # -------------------------------------------------------------------------
    def customise_project_activity_controller(**attr):

        s3db = current.s3db
        tablename = "project_activity"

        # Custom Components for Agency, Partners & Donors
        s3db.add_components(tablename,
                           org_organisation = (# Agency
                                               {"name": "agency",
                                                "link": "project_activity_organisation",
                                                "joinby": "activity_id",
                                                "key": "organisation_id",
                                                "actuate": "hide",
                                                "filterby": {"role": 1,
                                                             },
                                                },
                                               # Partners
                                               {"name": "partner",
                                                "link": "project_activity_organisation",
                                                "joinby": "activity_id",
                                                "key": "organisation_id",
                                                "actuate": "hide",
                                                "filterby": {"role": 2,
                                                             },
                                                },
                                               # Donors
                                               {"name": "donor",
                                                "link": "project_activity_organisation",
                                                "joinby": "activity_id",
                                                "key": "organisation_id",
                                                "actuate": "hide",
                                                "filterby": {"role": 3,
                                                             },
                                                },
                                               )
                            )
                                              
        from s3 import S3SQLCustomForm, S3SQLInlineComponent
        crud_form = S3SQLCustomForm(S3SQLInlineComponent("activity_organisation",
                                                         label = T("Agency"),
                                                         fields = [("", "organisation_id"),],
                                                         filterby = ({"field": "role",
                                                                      "options": 1,
                                                                      },),
                                                         multiple = False,
                                                         ),
                                    S3SQLInlineComponent("activity_organisation",
                                                         label = T("Implementing Partner"),
                                                         fields = [("", "organisation_id"),],
                                                         filterby = ({"field": "role",
                                                                      "options": 2,
                                                                      },),
                                                         #multiple = False,
                                                         ),
                                    S3SQLInlineComponent("activity_organisation",
                                                         label = T("Donor"),
                                                         fields = [("", "organisation_id"),],
                                                         filterby = ({"field": "role",
                                                                      "options": 3,
                                                                      },),
                                                         #multiple = False,
                                                         ),
                                    "location_id",
                                    S3SQLInlineComponent("sector_activity",
                                                         label = T("Sector"),
                                                         fields = [("", "sector_id"),],
                                                         multiple = False,
                                                         ),
                                    (T("Relief Items/Activity"), "name"),
                                    #(T("Modality)", ""),
                                    #(T("Number of Items/Kits)", ""),
                                    #(T("Number of Activities)", ""),
                                    (T("Activity Date (Planned/Start Date)"), "date"),
                                    (T("Activity Date (Completion Date)"), "end_date"),
                                    #(T("People / Households"), ""),
                                    #(T("Total Number People/Hh Targeted"), ""),
                                    #(T("Total Number Of People/HH Reached"), ""),
                                    (T("Activity Status"), "status_id"),
                                    "comments",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = [(T("Agency"), "agency.organisation_id"),
                                      (T("Implementing Partner"), "partner.organisation_id"),
                                      (T("Donor"), "donor.organisation_id"),
                                      (T("District"), "location_id$L1"),
                                      (T("DS Division"), "location_id$L2"),
                                      (T("GN Division"), "location_id$L3"),
                                      (T("Sector"), "sector_activity.sector_id"),
                                      (T("Relief Items/Activity"), "name"),
                                      (T("Activity Date (Planned/Start Date)"), "date"),
                                      (T("Activity Date (Completion Date)"), "end_date"),
                                      (T("Activity Status"), "status_id"),
                                      "comments",
                                      ],
                       )

        return attr
        
    settings.customise_project_activity_controller = customise_project_activity_controller

# END =========================================================================
