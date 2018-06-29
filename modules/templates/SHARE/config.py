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
    def req_need_status_update(need_id):
        """
            Update the Need's fulfilment Status
        """

        db = current.db
        s3db = current.s3db

        # Read the Need details
        nitable = s3db.req_need_item
        iptable = s3db.supply_item_pack
        query = (nitable.need_id == need_id) & \
                (nitable.deleted == False) & \
                (nitable.item_pack_id == iptable.id)
        need_items = db(query).select(nitable.id,
                                      nitable.item_id,
                                      nitable.quantity,
                                      iptable.quantity,
                                      )
        items = {}
        for item in need_items:
            pack_qty = item["supply_item_pack.quantity"]
            item = item["req_need_item"]
            quantity = item.quantity
            if quantity:
                quantity = quantity * pack_qty
            items[item.item_id] = {"id": item.id,
                                   "quantity": quantity or 0,
                                   "quantity_committed": 0,
                                   "quantity_delivered": 0,
                                   }

        ndtable = s3db.req_need_demographic
        query = (ndtable.need_id == need_id) & \
                (ndtable.deleted == False)
        need_demographics = db(query).select(ndtable.parameter_id,
                                             ndtable.id,
                                             ndtable.value,
                                             )
        demographics = {}
        for demographic in need_demographics:
            demographics[demographic.parameter_id] = {"id": demographic.id,
                                                      "value": demographic.value or 0,
                                                      "value_committed": 0,
                                                      "value_reached": 0,
                                                      }

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

        # Read the details of all Activities linked to this Need
        atable = s3db.project_activity
        natable = s3db.req_need_activity
        query = (natable.need_id == need_id) & \
                (natable.activity_id == atable.id) & \
                (atable.deleted == False)
        activities = db(query).select(atable.id,
                                      atable.status_id,
                                      )
        aitable = s3db.project_activity_item
        adtable = s3db.project_activity_demographic
        for activity in activities:
            activity_id = activity.id
            status_id = activity.status_id
            query = (aitable.activity_id == activity_id) & \
                    (aitable.deleted == False) & \
                    (aitable.item_pack_id == iptable.id)
            rows = db(query).select(aitable.item_id,
                                    aitable.target_value,
                                    aitable.value,
                                    iptable.quantity,
                                    )
            for row in rows:
                pack_qty = row["supply_item_pack.quantity"]
                row = row["project_activity_item"]
                item_id = row.item_id
                if item_id in items:
                    item = items[item_id]
                    if status_id != CANCELLED:
                        target_value = row.target_value
                        if target_value:
                            item["quantity_committed"] += target_value * pack_qty
                    value = row.value
                    if value:
                        item["quantity_delivered"] += value * pack_qty
                else:
                    # Ignore Items in Activity which don't match Need
                    continue
            query = (adtable.activity_id == activity_id) & \
                    (adtable.deleted == False)
            rows = db(query).select(adtable.parameter_id,
                                    adtable.target_value,
                                    adtable.value,
                                    )
            for row in rows:
                parameter_id = row.parameter_id
                if parameter_id in demographics:
                    demographic = demographics[parameter_id]
                    if status_id != CANCELLED:
                        target_value = row.target_value
                        if target_value:
                            demographic["value_committed"] += target_value
                    value = row.value
                    if value:
                        demographic["value_reached"] += value
                else:
                    # Ignore Demographics in Activity which don't match Need
                    continue

        # Calculate Need values & Update
        statuses = []
        sappend = statuses.append
        for item_id in items:
            item = items[item_id]
            quantity_requested = item["quantity"]
            quantity_committed = item["quantity_committed"]
            quantity_uncommitted = max(quantity_requested - quantity_committed, 0)
            quantity_delivered = item["quantity_delivered"]
            if quantity_delivered >= quantity_requested:
                status = 3
            elif quantity_uncommitted <= 0:
                status = 2
            elif quantity_committed > 0:
                status = 1
            else:
                status = 0
            sappend(status)
            db(nitable.id == item["id"]).update(quantity_committed = quantity_committed,
                                                quantity_uncommitted = quantity_uncommitted,
                                                quantity_delivered = quantity_delivered,
                                                )

        for parameter_id in demographics:
            demographic = demographics[parameter_id]
            value_requested = demographic["value"]
            value_committed = demographic["value_committed"]
            value_uncommitted = max(value_requested - value_committed, 0)
            value_reached = demographic["value_reached"]
            if value_reached >= value_requested:
                status = 3
            elif value_uncommitted <= 0:
                status = 2
            elif value_committed > 0:
                status = 1
            else:
                status = 0
            sappend(status)
            db(ndtable.id == demographic["id"]).update(value_committed = value_committed,
                                                       value_uncommitted = value_uncommitted,
                                                       value_reached = value_reached,
                                                       )

        if 1 in statuses:
            # 1 or more items/people are only partially committed
            status = 1
        elif 0 in statuses:
            if 2 in statuses or 3 in statuses:
                # Some items/people are not committed, but others are
                status = 1
            else:
                # No items/people have been committed
                status = 0
        elif 2 in statuses:
            # All Items/People are Committed, but at least some are not delivered/reached
            status = 2
        elif 3 in statuses:
            # All Items/People are Delivered/Reached
            status = 3
        else:
            # No Items/People: assume partial
            status = 1

        ntable = s3db.req_need
        need = db(ntable.id == need_id).select(ntable.id,
                                               ntable.status,
                                               limitby = (0, 1)
                                               ).first()
        if need.status != status:
            need.update_record(status = status)

    # -------------------------------------------------------------------------
    def project_activity_ondelete(row):
        """
            Ensure that the Need (if-any) has the correct Status
        """

        import json

        db = current.db
        s3db = current.s3db

        activity_id = row.get("id")

        # Lookup the Need
        need_id = None
        natable = s3db.req_need_activity
        deleted_links = db(natable.deleted == True).select(natable.deleted_fk)
        for link in deleted_links:
            deleted_fk = json.loads(link.deleted_fk)
            if activity_id == deleted_fk["activity_id"]:
                need_id = deleted_fk["need_id"]
                break

        if not need_id:
            return

        # Check that the Need hasn't been deleted
        ntable = s3db.req_need
        need = db(ntable.id == need_id).select(ntable.deleted,
                                               limitby = (0, 1)
                                               ).first()

        if need and not need.deleted:
            req_need_status_update(need_id)

    # -------------------------------------------------------------------------
    def project_activity_postprocess(form):
        """
            Ensure that the Need (if-any) has the correct Status
        """

        s3db = current.s3db

        activity_id = form.vars.id

        # Lookup the Need
        ntable = s3db.req_need
        natable = s3db.req_need_activity
        query = (natable.activity_id == activity_id) & \
                (natable.need_id == ntable.id) & \
                (ntable.deleted == False)
        need = current.db(query).select(ntable.id,
                                        limitby = (0, 1)
                                        ).first()

        if need:
            req_need_status_update(need.id)

    # -------------------------------------------------------------------------
    def customise_project_activity_resource(r, tablename):

        db = current.db
        s3db = current.s3db

        # Custom Filtered Components
        s3db.add_components(tablename,
                            project_activity_organisation = (# Agency
                                                             {"name": "agency",
                                                              "joinby": "activity_id",
                                                              "filterby": {"role": 1,
                                                                           },
                                                              #"multiple": False,
                                                              },
                                                             # Partners
                                                             {"name": "partner",
                                                              "joinby": "activity_id",
                                                              "filterby": {"role": 2,
                                                                           },
                                                              #"multiple": False,
                                                              },
                                                             # Donors
                                                             {"name": "donor",
                                                              "joinby": "activity_id",
                                                              "filterby": {"role": 3,
                                                                           },
                                                              #"multiple": False,
                                                              },
                                                             ),
                            project_activity_tag = (# Modality
                                                    {"name": "modality",
                                                     "joinby": "activity_id",
                                                     "filterby": {"tag": "modality",
                                                                  },
                                                     "multiple": False,
                                                     },
                                                    # Number
                                                    #{"name": "number",
                                                    # "joinby": "activity_id",
                                                    # "filterby": {"tag": "number",
                                                    #              },
                                                    # "multiple": False,
                                                    # },
                                                    )
                            )

        from s3 import S3LocationFilter, S3OptionsFilter, \
                       S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

        # Individual settings for specific tag components
        from gluon import IS_EMPTY_OR, IS_IN_SET
        components_get = s3db.resource(tablename).components.get

        donor = components_get("donor")
        donor.table.organisation_id.default = None

        partner = components_get("partner")
        partner.table.organisation_id.default = None

        modality = components_get("modality")
        modality.table.value.requires = IS_EMPTY_OR(IS_IN_SET(("Cash", "In-kind")))

        #number = components_get("number")
        #number.table.value.requires = IS_EMPTY_OR(IS_INT_IN_RANGE())

        #sdtable = s3db.stats_demographic
        #demographics = db(sdtable.deleted == False).select(sdtable.name)
        #demographics = [d.name for d in demographics]
        #s3db.project_activity_data.unit.requires = IS_EMPTY_OR(IS_IN_SET(demographics))

        crud_fields = [S3SQLInlineLink("event",
                                       field = "event_id",
                                       label = T("Disaster"),
                                       multiple = False,
                                       #required = True,
                                       ),
                       S3SQLInlineComponent("agency",
                                            name = "agency",
                                            label = T("Agency"),
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
                       S3SQLInlineLink("sector",
                                       field = "sector_id",
                                       filter = False,
                                       label = T("Sector"),
                                       multiple = False,
                                       ),
                       (T("Summary of Activity"), "name"),
                       S3SQLInlineComponent("modality",
                                            name = "modality",
                                            label = T("Modality"),
                                            fields = [("", "value"),],
                                            multiple = False,
                                            ),
                       #S3SQLInlineComponent("number",
                       #                     name = "number",
                       #                     label = T("Number of Items/Kits/Activities"),
                       #                     fields = [("", "value"),],
                       #                     multiple = False,
                       #                     ),
                       (T("Activity Date (Planned/Start Date)"), "date"),
                       (T("Activity Date (Completion Date)"), "end_date"),
                       #S3SQLInlineComponent("activity_data",
                       #                     label = T("People / Households"),
                       #                     fields = [(T("Type"), "unit"),
                       #                               (T("Number Targeted"), "target_value"),
                       #                               (T("Number Reached"), "value"),
                       #                               ],
                       #                     #multiple = False,
                       #                     ),
                       S3SQLInlineComponent("activity_demographic",
                                            label = T("Beneficiaries"),
                                            #link = False,
                                            fields = [(T("Type"), "parameter_id"),
                                                      #(T("Estimated Delivery Time"), "timeframe"),
                                                      (T("Number Planned"), "target_value"),
                                                      (T("Number Reached"), "value"),
                                                      ],
                                            #multiple = False,
                                            ),
                       S3SQLInlineComponent("activity_item",
                                            label = T("Items"),
                                            fields = ["item_category_id",
                                                      "item_id",
                                                      (T("Unit"), "item_pack_id"),
                                                      (T("Estimated Delivery Time"), "timeframe"),
                                                      (T("Number Planned"), "target_value"),
                                                      (T("Number Distributed"), "value"),
                                                      ],
                                            #multiple = False,
                                            ),
                       (T("Activity Status"), "status_id"),
                       "comments",
                       ]

        from controllers import req_NeedRepresent
        natable = s3db.req_need_activity
        #f = natable.need_id
        #f.represent = req_NeedRepresent()
        natable.need_id.represent = req_NeedRepresent()

        if r.id and r.resource.tablename == tablename:
            need_link = db(natable.activity_id == r.id).select(natable.need_id,
                                                               limitby = (0, 1)
                                                               ).first()
            if need_link:
                # This hides the widget from Update forms instead of just rendering read-only!
                #f.writable = False
                crud_fields.append(S3SQLInlineLink("need",
                                                   field = "need_id",
                                                   label = T("Need"),
                                                   multiple = False,
                                                   readonly = True,
                                                   ))

        crud_form = S3SQLCustomForm(*crud_fields,
                                    postprocess = project_activity_postprocess)

        filter_widgets = [S3OptionsFilter("agency.organisation_id",
                                          label = T("Agency"),
                                          ),
                          S3OptionsFilter("sector_activity.sector_id"),
                          S3LocationFilter("location_id",
                                           # These levels are for SHARE/LK
                                           levels = ("L2", "L3", "L4"),
                                           ),
                          S3OptionsFilter("event.event_type_id",
                                          hidden = True,
                                          ),
                          # @ToDo: Filter this list dynamically based on Event Type:
                          S3OptionsFilter("event__link.event_id",
                                          hidden = True,
                                          ),
                          S3OptionsFilter("status_id",
                                          cols = 4,
                                          label = T("Status"),
                                          hidden = True,
                                          ),
                          ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = [(T("Agency"), "agency.organisation_id"),
                                      (T("Implementing Partner"), "partner.organisation_id"),
                                      (T("District"), "location_id$L1"),
                                      (T("DS Division"), "location_id$L2"),
                                      (T("GN Division"), "location_id$L3"),
                                      (T("Sector"), "sector_activity.sector_id"),
                                      (T("Summary of Activity"), "name"),
                                      (T("Activity Status"), "status_id"),
                                      (T("Modality"), "modality.value"),
                                      (T("Activity Date (Planned/Start Date)"), "date"),
                                      (T("Activity Date (Completion Date)"), "end_date"),
                                      #(T("People / Households"), "activity_data.unit"),
                                      #(T("Total Number of People/HH Targeted"), "activity_data.target_value"),
                                      (T("People / Households"), "activity_demographic.parameter_id"),
                                      (T("Total Number of People/HH Reached"), "activity_demographic.value"),
                                      (T("Donor"), "donor.organisation_id"),
                                      (T("Needs"), "need__link.need_id"),
                                      "comments",
                                      ],
                       ondelete = project_activity_ondelete,
                       )

    settings.customise_project_activity_resource = customise_project_activity_resource

    # -------------------------------------------------------------------------
    def customise_project_activity_controller(**attr):

        s3 = current.response.s3

        # Custom postp
        standard_postp = s3.postp
        def postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive:
                # Inject the javascript to handle dropdown filtering
                # - normnally injected through AddResourceLink, but this isn't there in Inline widget
                # - we also need to turn the trigger & target into dicts
                s3.scripts.append("/%s/static/themes/SHARE/js/supply.js" % r.application)

            return output
        s3.postp = postp

        return attr

    settings.customise_project_activity_controller = customise_project_activity_controller

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

        from s3 import s3_comments_widget, s3_yes_no_represent, \
                       S3LocationFilter, S3OptionsFilter, S3TextFilter, \
                       S3LocationSelector, \
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

        f = s3db.req_need.status
        f.requires = IS_EMPTY_OR(IS_IN_SET(req_status_opts, zero = None))
        #f.represent = lambda opt: req_status_opts.get(opt, current.messages.UNKNOWN_OPT)
        f.represent = S3Represent(options = req_status_opts)

        # These levels are for SHARE/LK
        s3db.req_need.location_id.widget = S3LocationSelector(levels = ("L1", "L2"),
                                                              required_levels = ("L1", "L2"),
                                                              show_map = False)

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
                                            )
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        issue = components_get("issue")
        f = issue.table.value
        f.widget = lambda f, v: \
            s3_comments_widget(f, v, _placeholder = "e.g. drinking water")

        verified = components_get("verified")
        f = verified.table.value
        f.represent = s3_yes_no_represent
        f.requires = IS_EMPTY_OR(IS_IN_SET((True, False)))
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
            table = s3db.req_need_item
            table.quantity.label = T("Quantity Requested")
            table.quantity_committed.readable = True
            table.quantity_uncommitted.readable = True
            table.quantity_delivered.readable = True
            need_item = S3SQLInlineComponent("need_item",
                                             label = T("Items Needed"),
                                             fields = ["item_category_id",
                                                       "item_id",
                                                       (T("Unit"), "item_pack_id"),
                                                       (T("Needed within Timeframe"), "timeframe"),
                                                       "quantity",
                                                       "quantity_committed",
                                                       "quantity_uncommitted",
                                                       "quantity_delivered",
                                                       #(T("Urgency"), "priority"),
                                                       "comments",
                                                       ],
                                             )
            table = s3db.req_need_demographic
            table.value.label = T("Number in Need")
            table.value_committed.readable = True
            table.value_uncommitted.readable = True
            table.value_reached.readable = True
            demographic = S3SQLInlineComponent("need_demographic",
                                               label = T("People Affected"),
                                               fields = [(T("Type"), "parameter_id"),
                                                         #(T("Needed within Timeframe"), "timeframe"),
                                                         "value",
                                                         "value_committed",
                                                         "value_uncommitted",
                                                         "value_reached",
                                                         "comments",
                                                         ],
                                               )
        else:
            # Create
            org_readonly = organisation_id is not None
            need_item = S3SQLInlineComponent("need_item",
                                             label = T("Items Needed"),
                                             fields = ["item_category_id",
                                                       "item_id",
                                                       (T("Unit"), "item_pack_id"),
                                                       (T("Needed within Timeframe"), "timeframe"),
                                                       "quantity",
                                                       #(T("Urgency"), "priority"),
                                                       "comments",
                                                       ],
                                             )
            demographic = S3SQLInlineComponent("need_demographic",
                                               label = T("People Affected"),
                                               fields = [(T("Type"), "parameter_id"),
                                                         #(T("Needed within Timeframe"), "timeframe"),
                                                         "value",
                                                         "comments",
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
                       S3SQLInlineLink("sector",
                                       field = "sector_id",
                                       filter = False,
                                       label = T("Sector"),
                                       multiple = False,
                                       ),
                       "name",
                       (T("Issue"), "issue.value"),
                       demographic,
                       need_item,
                       S3SQLInlineComponent("document",
                                            label = T("Attachment"),
                                            fields = [("", "file")],
                                            # multiple = True has reliability issues in at least Chrome
                                            multiple = False,
                                            ),
                       (T("Verified by government official"), "verified.value"),
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

        filter_widgets = [S3TextFilter(["req_number.value",
                                        "need_item.item_id$name",
                                        # These levels are for SHARE/LK
                                        #"location_id$L1",
                                        "location_id$L2",
                                        #"location_id$L3",
                                        #"location_id$L4",
                                        "name",
                                        "comments",
                                        ],
                                       label = T("Search"),
                                       comment = T("Search for a Need by Request Number, Item, Location, Summary or Comments"),
                                       ),
                          S3LocationFilter("location_id",
                                           # These levels are for SHARE/LK
                                           levels = ("L2", "L3", "L4"),
                                           ),
                          S3OptionsFilter("need_item.item_id"),
                          S3OptionsFilter("status",
                                          cols = 3,
                                          label = T("Status"),
                                          ),
                          S3OptionsFilter("event.event_type_id",
                                          hidden = True,
                                          ),
                          # @ToDo: Filter this list dynamically based on Event Type:
                          S3OptionsFilter("event__link.event_id"),
                          S3OptionsFilter("sector__link.sector_id",
                                          hidden = True,
                                          ),
                          S3OptionsFilter("organisation__link.organisation_id",
                                          hidden = True,
                                          ),
                          S3OptionsFilter("verified.value",
                                          cols = 2,
                                          label = T("Verified"),
                                          hidden = True,
                                          ),
                          ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = [(T("Disaster"), "event__link.event_id"),
                                      "date",
                                      "organisation__link.organisation_id",
                                      # These levels/Labels are for SHARE/LK
                                      (T("District"), "location_id$L2"),
                                      #(T("DS"), "location_id$L3"),
                                      (T("Status"), "status"),
                                      "need_item.item_id",
                                      "sector__link.sector_id",
                                      (T("Urgency"), "priority"),
                                      #"name",
                                      (T("Request Number"), "req_number.value"),
                                      (T("Commits"), "activity__link.activity_id"),
                                      (T("Verified"), "verified.value"),
                                      (T("GN"), "location_id$L4"),
                                      ],
                       )

    settings.customise_req_need_resource = customise_req_need_resource

    # -------------------------------------------------------------------------
    def req_need_commit(r, **attr):
        """
            Custom method to Commit to a Need by creating an Activity
        """

        # Create Activity with values from Need
        need_id = r.id

        db = current.db
        s3db = current.s3db
        ntable = s3db.req_need
        ntable_id = ntable.id
        netable = s3db.event_event_need
        nstable = s3db.req_need_sector
        left = [netable.on(netable.need_id == ntable_id),
                nstable.on(nstable.need_id == ntable_id),
                ]
        need = db(ntable_id == need_id).select(ntable.name,
                                               ntable.location_id,
                                               netable.event_id,
                                               nstable.sector_id,
                                               left = left,
                                               limitby = (0, 1)
                                               ).first()

        atable = s3db.project_activity
        activity_id = atable.insert(name = need["req_need.name"],
                                    location_id = need["req_need.location_id"],
                                    )
        organisation_id = current.auth.user.organisation_id
        if organisation_id:
            s3db.project_activity_organisation.insert(activity_id = activity_id,
                                                      organisation_id = organisation_id,
                                                      role = 1,
                                                      )

        event_id = need["event_event_need.event_id"]
        if event_id:
            aetable = s3db.event_activity
            aetable.insert(activity_id = activity_id,
                           event_id = event_id,
                           )

        sector_id = need["req_need_sector.sector_id"]
        if sector_id:
            astable = s3db.project_sector_activity
            astable.insert(activity_id = activity_id,
                           sector_id = sector_id,
                           )

        nitable = s3db.req_need_item
        query = (nitable.need_id == need_id) & \
                (nitable.deleted == False)
        items = db(query).select(nitable.item_category_id,
                                 nitable.item_id,
                                 nitable.item_pack_id,
                                 nitable.timeframe,
                                 nitable.quantity,
                                 )
        if items:
            iinsert = s3db.project_activity_item.insert
            for item in items:
                iinsert(activity_id = activity_id,
                        item_category_id = item.item_category_id,
                        item_id = item.item_id,
                        item_pack_id = item.item_pack_id,
                        timeframe = item.timeframe,
                        target_value = item.quantity,
                        )

        ndtable = s3db.req_need_demographic
        query = (ndtable.need_id == need_id) & \
                (ndtable.deleted == False)
        demographics = db(query).select(ndtable.parameter_id,
                                        #ndtable.timeframe,
                                        ndtable.value,
                                        )
        if demographics:
            dinsert = s3db.project_activity_demographic.insert
            for demographic in demographics:
                dinsert(activity_id = activity_id,
                        parameter_id = demographic.parameter_id,
                        #timeframe = demographic.timeframe,
                        target_value = demographic.value,
                        )

        # Link to Need
        s3db.req_need_activity.insert(activity_id = activity_id,
                                      need_id = need_id,
                                      )

        # Update Need to show Fulfilled
        ntable = s3db.req_need
        need = current.db(ntable.id == need_id).select(ntable.id,
                                                       ntable.status,
                                                       limitby = (0, 1)
                                                       ).first()
        if need.status in (0, 1):
            # Set to Fully Committed
            need.update_record(status = 2)

        # Redirect to Update
        from gluon import redirect
        redirect(URL(c= "project", f="activity",
                     args = [activity_id, "update"],
                     ))

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

        # Custom commit method to create an Activity from a Need
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
                # - normnally injected through AddResourceLink, but this isn't there in Inline widget
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
                    else:
                        from s3 import S3CRUD, s3_str
                        # Normal Action Buttons
                        S3CRUD.action_buttons(r)
                        # Custom Action Buttons
                        s3.actions += [{"label": s3_str(T("Commit")),
                                        "_class": "action-btn",
                                        "url": URL(args=["[id]", "commit"]),
                                        }
                                       ]

            return output
        s3.postp = postp

        attr["rheader"] = req_need_rheader

        return attr

    settings.customise_req_need_controller = customise_req_need_controller

# END =========================================================================
