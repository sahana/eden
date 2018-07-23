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
                                args = ["SHARE", "img", "sharemenulogo.png"],
                                )

    # PrePopulate data
    settings.base.prepopulate += ("SHARE",)

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "SHARE"

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

    # UI Settings
    settings.ui.datatables_responsive = False

    # -------------------------------------------------------------------------
    # Events
    settings.event.label = "Disaster"
    # Uncomment to not use Incidents under Events
    settings.event.incident = False

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
    # Don't use Beneficiaries
    settings.project.activity_beneficiaries = False
    # Don't use Item Catalog for Distributions
    settings.project.activity_items = False
    settings.project.activity_sectors = True
    # Links to Filtered Components for Donors & Partners
    settings.project.organisation_roles = {
        1: T("Agency"),
        2: T("Implementing Partner"),
        3: T("Donor"),
    }

    # -------------------------------------------------------------------------
    # Supply
    # Disable the use of Multiple Item Catalogs
    settings.supply.catalog_multi = False

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
        ("setup", Storage(
            name_nice = T("Setup"),
            #description = "WebSetup",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
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
        # Used just for Statuses
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
    def customise_event_sitrep_resource(r, tablename):

        from s3 import s3_comments_widget

        table = current.s3db.event_sitrep

        table.name.widget = lambda f, v: \
            s3_comments_widget(f, v, _placeholder = "Please provide a brief summary of the Situational Update you are submitting.")

        table.comments.widget = lambda f, v: \
            s3_comments_widget(f, v, _placeholder = "e.g. Any additional relevant information.")

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Situational Update"),
            title_display = T("HCT Activity and Response Report"),
            title_list = T("Situational Updates"),
            title_update = T("Edit Situational Update"),
            title_upload = T("Import Situational Updates"),
            label_list_button = T("List Situational Updates"),
            label_delete_button = T("Delete Situational Update"),
            msg_record_created = T("Situational Update added"),
            msg_record_modified = T("Situational Update updated"),
            msg_record_deleted = T("Situational Update deleted"),
            msg_list_empty = T("No Situational Updates currently registered"))

    settings.customise_event_sitrep_resource = customise_event_sitrep_resource

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

            run_async = current.s3task.async
            # Poll
            run_async("msg_poll", args=["msg_twitter_channel", channel_id])

            # Parse
            run_async("msg_parse", args=[channel_id, "parse_tweet"])

        s3db.configure(tablename,
                       create_onaccept = onaccept,
                       )

    settings.customise_msg_twitter_channel_resource = customise_msg_twitter_channel_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        s3db = current.s3db

        # Custom Components
        s3db.add_components(tablename,
                            org_organisation_tag = (# Request Number
                                                    {"name": "req_number",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "req_number",
                                                                  },
                                                     "multiple": False,
                                                     },
                                                    # Vision
                                                    {"name": "vision",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "vision",
                                                                  },
                                                     "multiple": False,
                                                     },
                                                    ),
                            )

        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink, s3_comments_widget

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        vision = components_get("vision")
        vision.table.value.widget = s3_comments_widget

        crud_form = S3SQLCustomForm("name",
                                    "acronym",
                                    S3SQLInlineLink("organisation_type",
                                                    field = "organisation_type_id",
                                                    # Default 10 options just triggers which adds unnecessary complexity to a commonly-used form & commonly an early one (create Org when registering)
                                                    filter = False,
                                                    label = T("Type"),
                                                    multiple = False,
                                                    widget = "multiselect",
                                                    ),
                                    S3SQLInlineLink("sector",
                                                    columns = 4,
                                                    field = "sector_id",
                                                    label = T("Sectors"),
                                                    ),
                                    #S3SQLInlineLink("service",
                                    #                columns = 4,
                                    #                field = "service_id",
                                    #                label = T("Services"),
                                    #                ),
                                    "country",
                                    "phone",
                                    "website",
                                    "logo",
                                    (T("About"), "comments"),
                                    S3SQLInlineComponent("vision",
                                                         label = T("Vision"),
                                                         fields = [("", "value")],
                                                         multiple = False,
                                                         ),
                                    S3SQLInlineComponent("req_number",
                                                         label = T("Request Number"),
                                                         fields = [("", "value")],
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
                                    S3SQLInlineComponent("sector_lead",
                                                         label = T("Lead Organization(s)"),
                                                         fields = [("", "organisation_id"),],
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
    def req_need_commit(r, **attr):
        """
            Custom method to Commit to a Need by creating an Activity Group
        """

        # Create Activity Group (Response) with values from Need
        need_id = r.id

        db = current.db
        s3db = current.s3db

        ntable = s3db.req_need
        ntable_id = ntable.id
        netable = s3db.event_event_need
        left = [netable.on(netable.need_id == ntable_id),
                ]
        need = db(ntable_id == need_id).select(ntable.name,
                                               ntable.location_id,
                                               netable.event_id,
                                               left = left,
                                               limitby = (0, 1)
                                               ).first()

        nttable = s3db.req_need_tag
        query = (nttable.need_id == need_id) & \
                (nttable.tag.belongs(("address", "contact"))) & \
                (nttable.deleted == False)
        tags = db(query).select(nttable.tag,
                                nttable.value,
                                )
        contact = address = None
        for tag in tags:
            if tag.tag == "address":
                address = tag.value
            elif tag.tag == "contact":
                contact = tag.value

        nrtable = s3db.req_need_response
        need_response_id = nrtable.insert(need_id = need_id,
                                          name = need["req_need.name"],
                                          location_id = need["req_need.location_id"],
                                          contact = contact,
                                          address = address,
                                          )
        organisation_id = current.auth.user.organisation_id
        if organisation_id:
            s3db.req_need_response_organisation.insert(need_response_id = need_response_id,
                                                       organisation_id = organisation_id,
                                                       role = 1,
                                                       )

        event_id = need["event_event_need.event_id"]
        if event_id:
            aetable = s3db.event_event_need_response
            aetable.insert(need_response_id = need_response_id,
                           event_id = event_id,
                           )

        nltable = s3db.req_need_line
        query = (nltable.need_id == need_id) & \
                (nltable.deleted == False)
        lines = db(query).select(nltable.id,
                                 nltable.coarse_location_id,
                                 nltable.location_id,
                                 nltable.sector_id,
                                 nltable.parameter_id,
                                 nltable.value,
                                 nltable.value_uncommitted,
                                 nltable.item_category_id,
                                 nltable.item_id,
                                 nltable.item_pack_id,
                                 nltable.quantity,
                                 nltable.quantity_uncommitted,
                                 nltable.status,
                                 )
        if lines:
            linsert = s3db.req_need_response_line.insert
            for line in lines:
                value_uncommitted = line.value_uncommitted
                if value_uncommitted is None:
                    # No commitments yet so commit to all
                    value = line.value
                else:
                    # Only commit to the remainder
                    value = value_uncommitted
                quantity_uncommitted = line.quantity_uncommitted
                if quantity_uncommitted is None:
                    # No commitments yet so commit to all
                    quantity = line.quantity
                else:
                    # Only commit to the remainder
                    quantity = quantity_uncommitted
                need_line_id = line.id
                linsert(need_response_id = need_response_id,
                        need_line_id = need_line_id,
                        coarse_location_id = line.coarse_location_id,
                        location_id = line.location_id,
                        sector_id = line.sector_id,
                        parameter_id = line.parameter_id,
                        value = value,
                        item_category_id = line.item_category_id,
                        item_id = line.item_id,
                        item_pack_id = line.item_pack_id,
                        quantity = quantity,
                        )
                # Update Need Line status
                req_need_line_status_update(need_line_id)

        # Redirect to Update
        from gluon import redirect
        redirect(URL(c= "req", f="need_response",
                     args = [need_response_id, "update"],
                     ))

    # -------------------------------------------------------------------------
    def req_need_line_commit(r, **attr):
        """
            Custom method to Commit to a Need Line by creating an Activity
        """

        # Create Activity with values from Need Line
        need_line_id = r.id

        db = current.db
        s3db = current.s3db

        nltable = s3db.req_need_line
        query = (nltable.id == need_line_id)
        line = db(query).select(nltable.id,
                                nltable.need_id,
                                nltable.coarse_location_id,
                                nltable.location_id,
                                nltable.sector_id,
                                nltable.parameter_id,
                                nltable.value,
                                nltable.value_uncommitted,
                                nltable.item_category_id,
                                nltable.item_id,
                                nltable.item_pack_id,
                                nltable.quantity,
                                nltable.quantity_uncommitted,
                                nltable.status,
                                limitby = (0, 1)
                                ).first()

        need_id = line.need_id

        ntable = s3db.req_need
        ntable_id = ntable.id
        netable = s3db.event_event_need
        left = [netable.on(netable.need_id == ntable_id),
                ]
        need = db(ntable_id == need_id).select(ntable.name,
                                               ntable.location_id,
                                               netable.event_id,
                                               left = left,
                                               limitby = (0, 1)
                                               ).first()

        nttable = s3db.req_need_tag
        query = (nttable.need_id == need_id) & \
                (nttable.tag.belongs(("address", "contact"))) & \
                (nttable.deleted == False)
        tags = db(query).select(nttable.tag,
                                nttable.value,
                                )
        contact = address = None
        for tag in tags:
            if tag.tag == "address":
                address = tag.value
            elif tag.tag == "contact":
                contact = tag.value

        nrtable = s3db.req_need_response
        need_response_id = nrtable.insert(need_id = need_id,
                                          name = need["req_need.name"],
                                          location_id = need["req_need.location_id"],
                                          contact = contact,
                                          address = address,
                                          )
        organisation_id = current.auth.user.organisation_id
        if organisation_id:
            s3db.req_need_response_organisation.insert(need_response_id = need_response_id,
                                                       organisation_id = organisation_id,
                                                       role = 1,
                                                       )

        event_id = need["event_event_need.event_id"]
        if event_id:
            aetable = s3db.event_event_need_response
            aetable.insert(need_response_id = need_response_id,
                           event_id = event_id,
                           )

        value_uncommitted = line.value_uncommitted
        if value_uncommitted is None:
            # No commitments yet so commit to all
            value = line.value
        else:
            # Only commit to the remainder
            value = value_uncommitted
        quantity_uncommitted = line.quantity_uncommitted
        if quantity_uncommitted is None:
            # No commitments yet so commit to all
            quantity = line.quantity
        else:
            # Only commit to the remainder
            quantity = quantity_uncommitted

        s3db.req_need_response_line.insert(need_response_id = need_response_id,
                                           need_line_id = need_line_id,
                                           coarse_location_id = line.coarse_location_id,
                                           location_id = line.location_id,
                                           sector_id = line.sector_id,
                                           parameter_id = line.parameter_id,
                                           value = value,
                                           item_category_id = line.item_category_id,
                                           item_id = line.item_id,
                                           item_pack_id = line.item_pack_id,
                                           quantity = quantity,
                                           )

        # Update Need Line status
        req_need_line_status_update(need_line_id)

        # Redirect to Update
        from gluon import redirect
        redirect(URL(c= "req", f="need_response",
                     args = [need_response_id, "update"],
                     ))

    # -------------------------------------------------------------------------
    def req_need_line_status_update(need_line_id):
        """
            Update the Need Line's fulfilment Status
        """

        db = current.db
        s3db = current.s3db

        # Read the Line details
        nltable = s3db.req_need_line
        iptable = s3db.supply_item_pack
        query = (nltable.id == need_line_id)
        left = iptable.on(nltable.item_pack_id == iptable.id)
        need_line = db(query).select(nltable.parameter_id,
                                     nltable.value,
                                     nltable.item_id,
                                     nltable.quantity,
                                     iptable.quantity,
                                     left = left,
                                     limitby = (0, 1)
                                     ).first()
        need_pack_qty = need_line["supply_item_pack.quantity"]
        need_line = need_line["req_need_line"]
        need_parameter_id = need_line.parameter_id
        need_value = need_line.value or 0
        need_value_committed = 0
        need_value_reached = 0
        need_quantity = need_line.quantity
        if need_quantity:
            need_quantity = need_quantity * need_pack_qty
        else:
            need_quantity = 0
        need_item_id = need_line.item_id
        need_quantity_committed = 0
        need_quantity_delivered = 0

        # Lookup which Status means 'Cancelled'
        stable = s3db.project_status
        status = db(stable.name == "Cancelled").select(stable.id,
                                                       limitby = (0, 1)
                                                       ).first()
        try:
            CANCELLED = status.id
        except AttributeError:
            # Prepop not done? Name changed?
            current.log.debug("'Cancelled' Status not found")
            CANCELLED = 999999

        # Read the details of all Response Lines linked to this Need Line
        rltable = s3db.req_need_response_line
        iptable = s3db.supply_item_pack
        query = (rltable.need_line_id == need_line_id) & \
                (rltable.deleted == False)
        left = iptable.on(rltable.item_pack_id == iptable.id)
        response_lines = db(query).select(rltable.id,
                                          rltable.parameter_id,
                                          rltable.value,
                                          rltable.value_reached,
                                          rltable.item_id,
                                          iptable.quantity,
                                          rltable.quantity,
                                          rltable.quantity_delivered,
                                          rltable.status_id,
                                          left = left,
                                          )
        for line in response_lines:
            pack_qty = line["supply_item_pack.quantity"]
            line = line["req_need_response_line"]
            if line.status_id == CANCELLED:
                continue
            if line.parameter_id == need_parameter_id:
                value = line.value
                if value:
                    need_value_committed += value
                value_reached = line.value_reached
                if value_reached:
                    need_value_reached += value_reached
            if line.item_id == need_item_id:
                quantity = line.quantity
                if quantity:
                    need_quantity_committed += quantity * pack_qty
                quantity_delivered = line.quantity_delivered
                if quantity_delivered:
                    need_quantity_delivered += quantity_delivered * pack_qty

        # Calculate Need values & Update
        value_uncommitted = max(need_value - need_value_committed, 0)
        quantity_uncommitted = max(need_quantity - need_quantity_committed, 0)
        if (need_quantity_delivered >= need_quantity) and (need_value_reached >= need_value):
            status = 3
        elif (quantity_uncommitted <= 0) and (value_uncommitted <= 0):
            status = 2
        elif (need_quantity_committed > 0) or (need_value_committed > 0):
            status = 1
        else:
            status = 0

        db(nltable.id == need_line_id).update(value_committed = need_value_committed,
                                              value_uncommitted = value_uncommitted,
                                              value_reached = need_value_reached,
                                              quantity_committed = need_quantity_committed,
                                              quantity_uncommitted = quantity_uncommitted,
                                              quantity_delivered = need_quantity_delivered,
                                              status = status,
                                              )

    # -------------------------------------------------------------------------
    def req_need_postprocess(form):

        if form.record:
            # Update form
            return

        need_id = form.vars.id

        db = current.db
        s3db = current.s3db

        # Lookup Organisation
        notable = s3db.req_need_organisation
        org_link = db(notable.need_id == need_id).select(notable.organisation_id,
                                                         limitby = (0, 1),
                                                         ).first()
        if not org_link:
            return

        organisation_id = org_link.organisation_id

        # Lookup Request Number format
        ottable = s3db.org_organisation_tag
        query = (ottable.organisation_id == organisation_id) & \
                (ottable.tag == "req_number")
        tag = db(query).select(ottable.value,
                               limitby = (0, 1),
                               ).first()
        if not tag:
            return

        # Lookup most recently-used value
        nttable = s3db.req_need_tag
        query = (nttable.tag == "req_number") & \
                (nttable.need_id != need_id) & \
                (nttable.need_id == notable.need_id) & \
                (notable.organisation_id == organisation_id)

        need = db(query).select(nttable.value,
                                limitby = (0, 1),
                                orderby = ~nttable.created_on,
                                ).first()
        if need:
            new_number = int(need.value.split("-", 1)[1]) + 1
            req_number = "%s-%s" % (tag.value, str(new_number).zfill(6))
        else:
            req_number = "%s-000001" % tag.value

        nttable.insert(need_id = need_id,
                       tag = "req_number",
                       value = req_number,
                       )

    # -------------------------------------------------------------------------
    def customise_req_need_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_IN_SET, SPAN
        #from gluon.sqlhtml import BooleanWidget

        from s3 import s3_comments_widget, \
                       S3LocationSelector, S3LocationDropdownWidget, \
                       S3Represent, \
                       S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

        db = current.db
        s3db = current.s3db

        req_status_opts = {0: SPAN(T("None"),
                                   _class = "req_status_none",
                                   ),
                           1: SPAN(T("Partially Committed"),
                                   _class = "req_status_partial",
                                   ),
                           2: SPAN(T("Fully Committed"),
                                   _class = "req_status_committed",
                                   ),
                           3: SPAN(T("Complete"),
                                   _class = "req_status_complete",
                                   ),
                           }

        table = s3db.req_need
        f = table.status
        f.requires = IS_EMPTY_OR(IS_IN_SET(req_status_opts, zero = None))
        #f.represent = lambda opt: req_status_opts.get(opt, current.messages.UNKNOWN_OPT)
        f.represent = S3Represent(options = req_status_opts)

        table.name.widget = lambda f, v: \
            s3_comments_widget(f, v, _placeholder = "e.g. 400 families require drinking water in Kegalle DS Division in 1-2 days.")

        table.comments.widget = lambda f, v: \
            s3_comments_widget(f, v, _placeholder = "e.g. Accessibility issues, additional contacts on the ground (if any), any other relevant information.")

		# These levels/labels are for SHARE/LK
        table.location_id.widget = S3LocationSelector(levels = ("L1", "L2"),
                                                      required_levels = ("L1", "L2"),
                                                      show_map = False)

        ltable = s3db.req_need_line
        f = ltable.coarse_location_id
        f.label = T("Division")
        f.widget = S3LocationDropdownWidget(level="L3")
        f = ltable.location_id
        f.label = T("GN")
        f.widget = S3LocationDropdownWidget(level="L4")

        # Custom Filtered Components
        s3db.add_components(tablename,
                            req_need_tag = (# Req Number
                                            {"name": "req_number",
                                             "joinby": "need_id",
                                             "filterby": {"tag": "req_number",
                                                          },
                                             "multiple": False,
                                             },
                                            # Issue
                                            {"name": "issue",
                                             "joinby": "need_id",
                                             "filterby": {"tag": "issue",
                                                          },
                                             "multiple": False,
                                             },
                                            # Verified
                                            {"name": "verified",
                                             "joinby": "need_id",
                                             "filterby": {"tag": "verified",
                                                          },
                                             "multiple": False,
                                             },
                                            # Contact
                                            {"name": "contact",
                                             "joinby": "need_id",
                                             "filterby": {"tag": "contact",
                                                          },
                                             "multiple": False,
                                             },
                                            # Address
                                            {"name": "address",
                                             "joinby": "need_id",
                                             "filterby": {"tag": "address",
                                                          },
                                             "multiple": False,
                                             },
                                            )
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        address = components_get("address")
        f = address.table.value
        f.widget = s3_comments_widget

        contact = components_get("contact")
        f = contact.table.value
        f.widget = lambda f, v: \
            s3_comments_widget(f, v, _placeholder = "of person on the ground e.g. GA, DS")

        issue = components_get("issue")
        f = issue.table.value
        f.widget = lambda f, v: \
            s3_comments_widget(f, v, _placeholder = "e.g. Lack of accessibility and contaminated wells due to heavy rainfall.")

        verified = components_get("verified")
        f = verified.table.value
        from s3 import S3TagCheckboxWidget
        f.requires = IS_IN_SET(("Y", "N"))
        f.default = "N"
        f.represent = lambda v: T("yes") if v == "Y" else T("no")
        f.widget = S3TagCheckboxWidget(on="Y", off="N")

        auth = current.auth
        user = auth.user
        if user and user.organisation_id:
            organisation_id = user.organisation_id
        else:
            organisation_id = None
        if auth.s3_has_role("ADMIN"):
            f.default = True
        else:
            if organisation_id:
                f.default = True
            else:
                f.default = False
                f.writable = False

        if r.id and r.resource.tablename == tablename:
            # Read or Update
            create = False
        else:
            # Create
            create = True

        if not create:
            # Read or Update
            if organisation_id:
                org_readonly = True
            else:
                otable = s3db.req_need_organisation
                org_link = db(otable.need_id == r.id).select(otable.organisation_id,
                                                             limitby = (0, 1)
                                                             ).first()
                if org_link:
                    org_readonly = True
                else:
                    org_readonly = False
            #table = s3db.req_need_item
            #table.quantity.label = T("Quantity Requested")
            #table.quantity_committed.readable = True
            #table.quantity_uncommitted.readable = True
            #table.quantity_delivered.readable = True
            #need_item = S3SQLInlineComponent("need_item",
            #                                 label = T("Items Needed"),
            #                                 fields = ["item_category_id",
            #                                           "item_id",
            #                                           (T("Unit"), "item_pack_id"),
            #                                           (T("Needed within Timeframe"), "timeframe"),
            #                                           "quantity",
            #                                           "quantity_committed",
            #                                           "quantity_uncommitted",
            #                                           "quantity_delivered",
            #                                           #(T("Urgency"), "priority"),
            #                                           "comments",
            #                                           ],
            #                                 )
            #table = s3db.req_need_demographic
            #table.value.label = T("Number in Need")
            #table.value_committed.readable = True
            #table.value_uncommitted.readable = True
            #table.value_reached.readable = True
            #demographic = S3SQLInlineComponent("need_demographic",
            #                                   label = T("People Affected"),
            #                                   fields = [(T("Type"), "parameter_id"),
            #                                             #(T("Needed within Timeframe"), "timeframe"),
            #                                             "value",
            #                                             "value_committed",
            #                                             "value_uncommitted",
            #                                             "value_reached",
            #                                             "comments",
            #                                             ],
            #                                   )
            #ltable.value.label = T("Number in Need")
            ltable.value_committed.readable = True
            ltable.value_uncommitted.readable = True
            ltable.value_reached.readable = True
            #ltable.quantity.label = T("Quantity Requested")
            ltable.quantity_committed.readable = True
            ltable.quantity_uncommitted.readable = True
            ltable.quantity_delivered.readable = True
            line = S3SQLInlineComponent("need_line",
                                        label = "",
                                        fields = ["coarse_location_id",
                                                  "location_id",
                                                  "sector_id",
                                                  (T("People affected"), "parameter_id"),
                                                  "value",
                                                  "value_committed",
                                                  "value_uncommitted",
                                                  "value_reached",
                                                  (T("Item Category"), "item_category_id"),
                                                  "item_id",
                                                  (T("Unit"), "item_pack_id"),
                                                  (T("Item Quantity"), "quantity"),
                                                  (T("Needed within Timeframe"), "timeframe"),
                                                  "quantity_committed",
                                                  "quantity_uncommitted",
                                                  "quantity_delivered",
                                                  #"comments",
                                                  ],
                                        )
        else:
            # Create
            org_readonly = organisation_id is not None
            #need_item = S3SQLInlineComponent("need_item",
            #                                 label = T("Items Needed"),
            #                                 fields = ["item_category_id",
            #                                           "item_id",
            #                                           (T("Unit"), "item_pack_id"),
            #                                           (T("Needed within Timeframe"), "timeframe"),
            #                                           "quantity",
            #                                           #(T("Urgency"), "priority"),
            #                                           "comments",
            #                                           ],
            #                                 )
            #demographic = S3SQLInlineComponent("need_demographic",
            #                                   label = T("People Affected"),
            #                                   fields = [(T("Type"), "parameter_id"),
            #                                             #(T("Needed within Timeframe"), "timeframe"),
            #                                             "value",
            #                                             "comments",
            #                                             ],
            #                                   )
            line = S3SQLInlineComponent("need_line",
                                        label = "",
                                        fields = ["coarse_location_id",
                                                  "location_id",
                                                  "sector_id",
                                                  (T("People affected"), "parameter_id"),
                                                  "value",
                                                  (T("Item Category"), "item_category_id"),
                                                  "item_id",
                                                  (T("Unit"), "item_pack_id"),
                                                  "quantity",
                                                  (T("Needed within Timeframe"), "timeframe"),
                                                  #"comments",
                                                  ],
                                        )

        crud_fields = [S3SQLInlineLink("event",
                                       field = "event_id",
                                       label = T("Disaster"),
                                       multiple = False,
                                       required = True,
                                       ),
                       S3SQLInlineLink("organisation",
                                       field = "organisation_id",
                                       filter = False,
                                       label = T("Organization"),
                                       multiple = False,
                                       readonly = org_readonly,
                                       required = not org_readonly,
                                       ),
                       "location_id",
                       "date",
                       #(T("Urgency"), "priority"),
                       # Moved into Lines
                       #S3SQLInlineLink("sector",
                       #                field = "sector_id",
                       #                filter = False,
                       #                label = T("Sector"),
                       #                multiple = False,
                       #                ),
                       "name",
                       (T("Issue/cause"), "issue.value"),
                       #demographic,
                       #need_item,
                       line,
                       S3SQLInlineComponent("document",
                                            label = T("Attachment"),
                                            fields = [("", "file")],
                                            # multiple = True has reliability issues in at least Chrome
                                            multiple = False,
                                            ),
                       (T("Verified by government official"), "verified.value"),
                       (T("Contact details"), "contact.value"),
                       (T("Address for delivery/affected people"), "address.value"),
                       "comments",
                       ]

        from controllers import project_ActivityRepresent
        natable = s3db.req_need_activity
        #f = natable.activity_id
        #f.represent = project_ActivityRepresent()
        natable.activity_id.represent = project_ActivityRepresent()

        if not create:
            # Read or Update
            req_number = components_get("verified")
            req_number.table.value.writable = False
            crud_fields.insert(2, (T("Request Number"), "req_number.value"))
            crud_fields.insert(-2, "status")
            need_links = db(natable.need_id == r.id).select(natable.activity_id)
            if need_links:
                # This hides the widget from Update forms instead of just rendering read-only!
                #f.writable = False
                crud_fields.append(S3SQLInlineLink("activity",
                                                   field = "activity_id",
                                                   label = T("Commits"),
                                                   readonly = True,
                                                   ))

        crud_form = S3SQLCustomForm(*crud_fields,
                                    postprocess = req_need_postprocess)

        need_line_summary = URL(c="req", f="need_line", args="summary")

        s3db.configure(tablename,
                       create_next = need_line_summary,
                       delete_next = need_line_summary,
                       update_next = need_line_summary,
                       crud_form = crud_form,
                       )

    settings.customise_req_need_resource = customise_req_need_resource

    # -------------------------------------------------------------------------
    def req_need_rheader(r):
        """
            Resource Header for Needs
        """

        if r.representation != "html":
            # RHeaders only used in interactive views
            return None

        record = r.record
        if not record:
            # RHeaders only used in single-record views
            return None

        if r.name == "need":
            # No Tabs (all done Inline)
            tabs = [(T("Basic Details"), None),
                    #(T("Demographics"), "demographic"),
                    #(T("Items"), "need_item"),
                    #(T("Skills"), "need_skill"),
                    #(T("Tags"), "tag"),
                    ]

            from s3 import s3_rheader_tabs
            rheader_tabs = s3_rheader_tabs(r, tabs)

            location_id = r.table.location_id
            from gluon import DIV, TABLE, TR, TH
            rheader = DIV(TABLE(TR(TH("%s: " % location_id.label),
                                   location_id.represent(record.location_id),
                                   )),
                          rheader_tabs)

        else:
            # Not defined, probably using wrong rheader
            rheader = None

        return rheader

    # -------------------------------------------------------------------------
    def customise_req_need_controller(**attr):

        line_id = current.request.get_vars.get("line")
        if line_id:
            from gluon import redirect
            nltable = current.s3db.req_need_line
            line = current.db(nltable.id == line_id).select(nltable.need_id,
                                                            limitby = (0, 1)
                                                            ).first()
            if line:
                redirect(URL(args = [line.need_id],
                             vars = {}))

        # Custom commit method to create an Activity Group from a Need
        current.s3db.set_method("req", "need",
                                method = "commit",
                                action = req_need_commit)

        s3 = current.response.s3

        # Custom postp
        standard_postp = s3.postp
        def postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive:
                # Inject the javascript to handle dropdown filtering
                # - normally injected through AddResourceLink, but this isn't there in Inline widget
                # - we also need to turn the trigger & target into dicts
                s3.scripts.append("/%s/static/themes/SHARE/js/supply.js" % r.application)
                if current.auth.s3_has_permission("create", "project_activity"):
                    if r.id:
                        # Custom RFooter
                        from gluon import A
                        s3.rfooter = A(T("Commit"),
                                       _href = URL(args=[r.id, "commit"]),
                                       _class = "action-btn",
                                       #_id = "commit-btn",
                                       )
                        #s3.jquery_ready.append(
#'''S3.confirmClick('#commit-btn','%s')''' % T("Do you want to commit to this need?"))

            return output
        s3.postp = postp

        attr["rheader"] = req_need_rheader

        return attr

    settings.customise_req_need_controller = customise_req_need_controller

    # -------------------------------------------------------------------------
    def customise_req_need_line_controller(**attr):

        from s3 import S3LocationFilter, S3OptionsFilter, S3TextFilter

        s3db = current.s3db

        # Custom Filtered Components
        s3db.add_components("req_need",
                            req_need_tag = (# Req Number
                                            {"name": "req_number",
                                             "joinby": "need_id",
                                             "filterby": {"tag": "req_number",
                                                          },
                                             "multiple": False,
                                             },
                                            # Verified
                                            {"name": "verified",
                                             "joinby": "need_id",
                                             "filterby": {"tag": "verified",
                                                          },
                                             "multiple": False,
                                             },
                                            ),
                            )

        s3db.add_components("req_need_response",
                            req_need_response_organisation = (# Agency
                                                              {"name": "agency",
                                                               "joinby": "need_response_id",
                                                               "filterby": {"role": 1,
                                                                            },
                                                               #"multiple": False,
                                                               },
                                                              ),
                            )

        filter_widgets = [S3TextFilter(["need_id$req_number.value",
                                        "item_id$name",
                                        # These levels are for SHARE/LK
                                        #"location_id$L1",
                                        "location_id$L2",
                                        #"location_id$L3",
                                        #"location_id$L4",
                                        "need_id$name",
                                        "need_id$comments",
                                        ],
                                       label = T("Search"),
                                       comment = T("Search for a Need by Request Number, Item, Location, Summary or Comments"),
                                       ),
                          S3LocationFilter("location_id",
                                           # These levels are for SHARE/LK
                                           levels = ("L2", "L3", "L4"),
                                           ),
                          S3OptionsFilter("item_id"),
                          S3OptionsFilter("status",
                                          cols = 3,
                                          label = T("Status"),
                                          ),
                          S3OptionsFilter("need_id$event.event_type_id",
                                          hidden = True,
                                          ),
                          # @ToDo: Filter this list dynamically based on Event Type:
                          S3OptionsFilter("need_id$event__link.event_id"),
                          S3OptionsFilter("sector_id",
                                          hidden = True,
                                          ),
                          S3OptionsFilter("need_id$organisation__link.organisation_id",
                                          hidden = True,
                                          ),
                          S3OptionsFilter("need_id$verified.value",
                                          cols = 2,
                                          label = T("Verified"),
                                          hidden = True,
                                          ),
                          ]

        s3db.configure("req_need_line",
                       filter_widgets = filter_widgets,
                       # We create a custom Create Button to create a Need not a Need Line
                       listadd = False,
                       list_fields = [(T("Status"), "status"),
                                      (T("Commits"), "need_response_line.need_response_id$agency.organisation_id"),
                                      "need_id$date",
                                      "need_id$organisation__link.organisation_id",
                                      # These levels/Labels are for SHARE/LK
                                      (T("District"), "need_id$location_id$L2"),
                                      #(T("DS"), "location_id$L3"),
                                      #(T("GN"), "location_id$L4"),
                                      "sector_id",
                                      "parameter_id",
                                      "item_id",
                                      "quantity",
                                      "timeframe",
                                      (T("Request Number"), "need_id$req_number.value"),
                                      ],
                       )

        # Custom commit method to create an Activity from a Need Line
        s3db.set_method("req", "need_line",
                        method = "commit",
                        action = req_need_line_commit)

        s3 = current.response.s3

        s3.crud_strings["req_need_line"] = Storage(
            #label_create = T("Add Needs"),
            title_list = T("Needs"),
            #title_display=T("Needs"),
            #title_update=T("Edit Needs"),
            #title_upload = T("Import Needs"),
            #label_list_button = T("List Needs"),
            #label_delete_button=T("Delete Needs"),
            msg_record_created=T("Needs added"),
            msg_record_modified=T("Needs updated"),
            msg_record_deleted=T("Needs deleted"),
            msg_list_empty = T("No Needs currently registered"),
            )

        # Custom postp
        standard_postp = s3.postp
        def postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.method == "summary":
                from gluon import A, DIV
                from s3 import s3_str
                #from s3 import S3CRUD, s3_str
                # Normal Action Buttons
                #S3CRUD.action_buttons(r)
                # Custom Action Buttons
                auth = current.auth
                deletable = current.db(auth.s3_accessible_query("delete", "req_need_line")).select(s3db.req_need_line.id)
                restrict_d = [str(row.id) for row in deletable]
                s3.actions = [{"label": s3_str(T("Open")),
                               "_class": "action-btn",
                               "url": URL(f="need", vars={"line": "[id]"}),
                               },
                              {"label": s3_str(T("Delete")),
                               "_class": "action-btn",
                               "url": URL(args=["[id]", "delete"]),
                               "restrict": restrict_d,
                               },
                              ]
                if auth.s3_has_permission("create", "req_need_response"):
                    s3.actions.append({"label": s3_str(T("Commit")),
                                       "_class": "action-btn",
                                       "url": URL(args=["[id]", "commit"]),
                                       })

                # Custom Create Button
                add_btn = DIV(DIV(DIV(A(T("Add Needs"),
                                        _class = "action-btn",
                                        _href = URL(f="need", args="create"),
                                        ),
                                      _id = "list-btn-add",
                                      ),
                                  _class = "widget-container",
                                  ),
                              _class = "section-container",
                              )
                output["common"][0] = add_btn

            return output
        s3.postp = postp

        return attr

    settings.customise_req_need_line_controller = customise_req_need_line_controller

    # -------------------------------------------------------------------------
    def req_need_response_postprocess(form):
        """
            Ensure that the Need Lines (if-any) have the correct Status
        """

        s3db = current.s3db

        need_response_id = form.vars.id

        # Lookup the Need Lines
        rltable = s3db.req_need_response_line
        query = (rltable.need_response_id == need_response_id) & \
                (rltable.deleted == False)
        response_lines = current.db(query).select(rltable.need_line_id)

        for line in response_lines:
            need_line_id = line.need_line_id
            if need_line_id:
                req_need_line_status_update(need_line_id)

    # -------------------------------------------------------------------------
    def customise_req_need_response_resource(r, tablename):

        from s3 import s3_comments_widget, \
                       S3LocationDropdownWidget, S3LocationSelector, \
                       S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

        #db = current.db
        s3db = current.s3db

        table = s3db.req_need_response

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Activities"),
            title_list = T("Activities"),
            title_display = T("Activities"),
            title_update = T("Edit Activities"),
            title_upload = T("Import Activities"),
            label_list_button = T("List Activities"),
            label_delete_button = T("Delete Activities"),
            msg_record_created = T("Activities added"),
            msg_record_modified = T("Activities updated"),
            msg_record_deleted = T("Activities deleted"),
            msg_list_empty = T("No Activities currently registered"),
            )

        # These levels/labels are for SHARE/LK
        table.location_id.widget = S3LocationSelector(levels = ("L1", "L2"),
                                                      required_levels = ("L1", "L2"),
                                                      show_map = False)

        ltable = s3db.req_need_response_line
        f = ltable.coarse_location_id
        f.label = T("Division")
        f.widget = S3LocationDropdownWidget(level="L3")
        f = ltable.location_id
        f.label = T("GN")
        f.widget = S3LocationDropdownWidget(level="L4")

        table.comments.widget = lambda f, v: \
            s3_comments_widget(f, v, _placeholder = "e.g. Items changed/replaced within kits, details on partial committments to a need, any other relevant information.")

        # Custom Filtered Components
        s3db.add_components(tablename,
                            req_need_response_organisation = (# Agency
                                                              {"name": "agency",
                                                               "joinby": "need_response_id",
                                                               "filterby": {"role": 1,
                                                                            },
                                                               #"multiple": False,
                                                               },
                                                              # Partners
                                                              {"name": "partner",
                                                               "joinby": "need_response_id",
                                                               "filterby": {"role": 2,
                                                                            },
                                                               #"multiple": False,
                                                               },
                                                              # Donors
                                                              {"name": "donor",
                                                               "joinby": "need_response_id",
                                                               "filterby": {"role": 3,
                                                                            },
                                                               #"multiple": False,
                                                               },
                                                              ),
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        donor = components_get("donor")
        donor.table.organisation_id.default = None

        partner = components_get("partner")
        partner.table.organisation_id.default = None

        crud_fields = [S3SQLInlineLink("event",
                                       field = "event_id",
                                       label = T("Disaster"),
                                       multiple = False,
                                       #required = True,
                                       ),
                       S3SQLInlineComponent("agency",
                                            name = "agency",
                                            label = T("Organization"),
                                            fields = [("", "organisation_id"),],
                                            #multiple = False,
                                            required = True,
                                            ),
                       # @ToDo: MultiSelectWidget is nicer UI but S3SQLInlineLink
                       #        requires the link*ed* table as component (not the
                       #        link table as applied here) and linked components
                       #        cannot currently be filtered by link table fields
                       #        (=> should solve the latter rather than the former)
                       # @ToDo: Fix Create Popups
                       S3SQLInlineComponent("partner",
                                            name = "partner",
                                            label = T("Implementing Partner"),
                                            fields = [("", "organisation_id"),],
                                            ),
                       S3SQLInlineComponent("donor",
                                            name = "donor",
                                            label = T("Donor"),
                                            fields = [("", "organisation_id"),],
                                            ),
                       "location_id",
                       (T("Date"), "date"),
                       (T("Summary of Needs/Activities"), "name"),
                       S3SQLInlineComponent("need_response_line",
                                            label = "",
                                            fields = ["coarse_location_id",
                                                      "location_id",
                                                      "sector_id",
                                                      "modality",
                                                      (T("Activity Date Planned"), "date"),
                                                      (T("Activity Date Completed"), "end_date"),
                                                      (T("Beneficiaries (Type)"), "parameter_id"),
                                                      (T("Beneficiaries Planned"), "value"),
                                                      (T("Beneficiaries Reached"), "value_reached"),
                                                      (T("Item Category"), "item_category_id"),
                                                      "item_id",
                                                      (T("Unit"), "item_pack_id"),
                                                      (T("Quantity Planned"), "quantity"),
                                                      (T("Quantity Delivered"), "quantity_delivered"),
                                                      (T("Activity Status"), "status_id"),
                                                      #"comments",
                                                      ],
                                            #multiple = False,
                                            ),
                       S3SQLInlineComponent("document",
                                            label = T("Attachment"),
                                            fields = [("", "file")],
                                            # multiple = True has reliability issues in at least Chrome
                                            multiple = False,
                                            ),
                       "contact",
                       "address",
                       "comments",
                       ]

        if r.id and r.resource.tablename == tablename and r.record.need_id:
            from controllers import req_NeedRepresent
            f = table.need_id
            f.represent = req_NeedRepresent()
            f.writable = False
            crud_fields.insert(7, "need_id")

        crud_form = S3SQLCustomForm(*crud_fields,
                                    postprocess = req_need_response_postprocess)

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_req_need_response_resource = customise_req_need_response_resource

    # -------------------------------------------------------------------------
    def customise_req_need_response_controller(**attr):

        line_id = current.request.get_vars.get("line")
        if line_id:
            from gluon import redirect
            nltable = current.s3db.req_need_response_line
            line = current.db(nltable.id == line_id).select(nltable.need_response_id,
                                                            limitby = (0, 1)
                                                            ).first()
            if line:
                redirect(URL(args = [line.need_response_id],
                             vars = {}))

        s3 = current.response.s3

        # Custom postp
        standard_postp = s3.postp
        def postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive:
                # Inject the javascript to handle dropdown filtering
                # - normally injected through AddResourceLink, but this isn't there in Inline widget
                # - we also need to turn the trigger & target into dicts
                s3.scripts.append("/%s/static/themes/SHARE/js/supply.js" % r.application)

            return output
        s3.postp = postp

        return attr

    settings.customise_req_need_response_controller = customise_req_need_response_controller

    # -------------------------------------------------------------------------
    def req_need_response_line_ondelete(row):
        """
            Ensure that the Need Line (if-any) has the correct Status
        """

        import json

        db = current.db
        s3db = current.s3db

        response_line_id = row.get("id")

        # Lookup the Need Line
        rltable = s3db.req_need_response_line
        record = db(rltable.id == response_line_id).select(rltable.deleted_fk,
                                                           limitby = (0, 1)
                                                           ).first()
        if not record:
            return

        deleted_fk = json.loads(record.deleted_fk)
        need_line_id = deleted_fk["need_line_id"]

        if not need_line_id:
            return

        # Check that the Need Line hasn't been deleted
        nltable = s3db.req_need_line
        need_line = db(nltable.id == need_line_id).select(nltable.deleted,
                                                          limitby = (0, 1)
                                                          ).first()

        if need_line and not need_line.deleted:
            req_need_line_status_update(need_line_id)

    # -------------------------------------------------------------------------
    def customise_req_need_response_line_resource(r, tablename):

        current.s3db.configure(tablename,
                               ondelete = req_need_response_line_ondelete,
                               )

    settings.customise_req_need_response_line_resource = customise_req_need_response_line_resource

    # -------------------------------------------------------------------------
    def customise_req_need_response_line_controller(**attr):

        from s3 import S3LocationFilter, S3OptionsFilter#, S3TextFilter

        s3db = current.s3db

        # Custom Filtered Components
        s3db.add_components("req_need_response",
                            req_need_response_organisation = (# Agency
                                                              {"name": "agency",
                                                               "joinby": "need_response_id",
                                                               "filterby": {"role": 1,
                                                                            },
                                                               #"multiple": False,
                                                               },
                                                              # Partners
                                                              {"name": "partner",
                                                               "joinby": "need_response_id",
                                                               "filterby": {"role": 2,
                                                                            },
                                                               #"multiple": False,
                                                               },
                                                              # Donors
                                                              {"name": "donor",
                                                               "joinby": "need_response_id",
                                                               "filterby": {"role": 3,
                                                                            },
                                                               #"multiple": False,
                                                               },
                                                              ),
                            )

        filter_widgets = [S3OptionsFilter("need_response_id$agency.organisation_id",
                                          label = T("Agency"),
                                          ),
                          S3OptionsFilter("sector_id"),
                          S3LocationFilter("location_id",
                                           # These levels are for SHARE/LK
                                           levels = ("L2", "L3", "L4"),
                                           ),
                          S3OptionsFilter("need_response_id$event.event_type_id",
                                          hidden = True,
                                          ),
                          # @ToDo: Filter this list dynamically based on Event Type:
                          S3OptionsFilter("need_response_id$event__link.event_id",
                                          hidden = True,
                                          ),
                          S3OptionsFilter("status_id",
                                          cols = 4,
                                          label = T("Status"),
                                          hidden = True,
                                          ),
                          ]

        s3db.configure("req_need_response_line",
                       filter_widgets = filter_widgets,
                       # We create a custom Create Button to create a Need Response not a Need Response Line
                       listadd = False,
                       list_fields = [(T("Disaster"), "need_response_id$event__link.event_id"),
                                      (T("Organization"), "need_response_id$agency.organisation_id"),
                                      (T("Implementing Partner"), "need_response_id$partner.organisation_id"),
                                      (T("Donor"), "need_response_id$donor.organisation_id"),
                                      # These levels/labels are for SHARE/LK
                                      (T("District"), "need_response_id$location_id$L1"),
                                      (T("Division"), "coarse_location_id"),
                                      (T("GN"), "location_id"),
                                      (T("Sector"), "sector_id"),
                                      (T("Item"), "item_id"),
                                      (T("Items Planned"), "quantity"),
                                      (T("Items Delivered"), "quantity_delivered"),
                                      (T("Modality"), "modality"),
                                      (T("Beneficiaries Planned"), "value"),
                                      (T("Beneficiaries Reached"), "value_reached"),
                                      (T("Activity Date (Planned"), "date"),
                                      (T("Activity Status"), "status_id"),
                                      ],
                       )

        s3 = current.response.s3

        s3.crud_strings["req_need_line"] = Storage(
            #label_create = T("Add Activity"),
            title_list = T("Activities"),
            #title_display = T("Activity"),
            #title_update = T("Edit Activity"),
            #title_upload = T("Import Activities"),
            #label_list_button = T("List Activities"),
            #label_delete_button = T("Delete Activity"),
            #msg_record_created = T("Activity added"),
            #msg_record_modified = T("Activity updated"),
            msg_record_deleted = T("Activity deleted"),
            msg_list_empty = T("No Activities currently registered"),
            )

        # Custom postp
        standard_postp = s3.postp
        def postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.method == "summary":
                from gluon import A, DIV
                from s3 import s3_str
                #from s3 import S3CRUD, s3_str
                # Normal Action Buttons
                #S3CRUD.action_buttons(r)
                # Custom Action Buttons
                auth = current.auth
                deletable = current.db(auth.s3_accessible_query("delete", "req_need_response_line")).select(s3db.req_need_response_line.id)
                restrict_d = [str(row.id) for row in deletable]
                s3.actions = [{"label": s3_str(T("Open")),
                               "_class": "action-btn",
                               "url": URL(f="need_response", vars={"line": "[id]"}),
                               },
                              {"label": s3_str(T("Delete")),
                               "_class": "action-btn",
                               "url": URL(args=["[id]", "delete"]),
                               "restrict": restrict_d,
                               },
                              ]

                # Custom Create Button
                add_btn = DIV(DIV(DIV(A(T("Add Activity"),
                                        _class = "action-btn",
                                        _href = URL(f="need_response", args="create"),
                                        ),
                                      _id = "list-btn-add",
                                      ),
                                  _class = "widget-container",
                                  ),
                              _class = "section-container",
                              )
                output["common"][0] = add_btn

            return output
        s3.postp = postp

        return attr

    settings.customise_req_need_response_line_controller = customise_req_need_response_line_controller

# END =========================================================================
