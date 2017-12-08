# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template settings: 'Skeleton' designed to be copied to quickly create
                           custom templates

        All settings which are to configure a specific template are located
        here. Deployers should ideally not need to edit any other files outside
        of their template folder.
    """

    T = current.T

    settings.base.system_name = T("Sahana First Response")
    settings.base.system_name_short = T("SAFIRE")

    # PrePopulate data
    #settings.base.prepopulate = ("skeleton", "default/users")
    settings.base.prepopulate += ("SAFIRE", "default/users", "SAFIRE/Demo")

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "SAFIRE"

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
    #settings.gis.countries = ("US",)
    # Uncomment to display the Map Legend as a floating DIV
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
    #    ("ar", "Arabic"),
    #    ("bs", "Bosnian"),
    #    #("dv", "Divehi"), # Maldives
    #    ("en", "English"),
    #    ("fr", "French"),
    #    ("de", "German"),
    #    ("el", "Greek"),
    #    ("es", "Spanish"),
    #    #("id", "Bahasa Indonesia"),
    #    ("it", "Italian"),
    #    ("ja", "Japanese"),
    #    ("km", "Khmer"), # Cambodia
    #    ("ko", "Korean"),
    #    #("lo", "Lao"),
    #    #("mg", "Malagasy"),
    #    ("mn", "Mongolian"),
    #    #("ms", "Malaysian"),
    #    ("my", "Burmese"), # Myanmar
    #    ("ne", "Nepali"),
    #    ("prs", "Dari"), # Afghan Persian
    #    ("ps", "Pashto"), # Afghanistan, Pakistan
    #    ("pt", "Portuguese"),
    #    ("pt-br", "Portuguese (Brazil)"),
    #    ("ru", "Russian"),
    #    ("tet", "Tetum"),
    #    #("si", "Sinhala"), # Sri Lanka
    #    #("ta", "Tamil"), # India, Sri Lanka
    #    ("th", "Thai"),
    #    ("tl", "Tagalog"), # Philippines
    #    ("tr", "Turkish"),
    #    ("ur", "Urdu"), # Pakistan
    #    ("vi", "Vietnamese"),
    #    ("zh-cn", "Chinese (Simplified)"), # Mainland China
    #    ("zh-tw", "Chinese (Taiwan)"),
    #])
    # Default language for Language Toolbar (& GIS Locations in future)
    #settings.L10n.default_language = "en"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    #settings.L10n.utc_offset = "+0100"
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

    settings.security.policy = 5 # Controller, Function & Table ACLs

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
        #("translate", Storage(
        #    name_nice = T("Translation Functionality"),
        #    #description = "Selective translation of strings based on module.",
        #    module_type = None,
        #)),
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
        #("vol", Storage(
        #    name_nice = T("Volunteers"),
        #    #description = "Human Resources Management",
        #    restricted = True,
        #    module_type = 2,
        #)),
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
        #("inv", Storage(
        #    name_nice = T("Warehouses"),
        #    #description = "Receiving and Sending Items",
        #    restricted = True,
        #    module_type = 4
        #)),
        ("asset", Storage(
            name_nice = "Assets",
            #description = "Recording and Assigning Assets",
            restricted = True,
            module_type = 5,
        )),
        # Vehicle depends on Assets
        ("vehicle", Storage(
            name_nice = "Vehicles",
            #description = "Manage Vehicles",
            restricted = True,
            module_type = 10,
        )),
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
        #("stats", Storage(
        #    name_nice = T("Statistics"),
        #    #description = "Manages statistics",
        #    restricted = True,
        #    module_type = None,
        #)),
    ])

    # -------------------------------------------------------------------------
    # Events
    # -------------------------------------------------------------------------
    def event_rheader(r):
        rheader = None

        record = r.record
        if record and r.representation == "html":

            from gluon import DIV, TABLE, TR, TH
            from s3 import s3_rheader_tabs

            name = r.name
            if name == "incident":
                # Incident Controller
                tabs = [(T("Incident Details"), None),
                        #(T("Tasks"), "task"),
                        #(T("Human Resources"), "human_resource"),
                        #(T("Equipment"), "asset"),
                        (T("Action Plan"), "plan"),
                        (T("Incident Reports"), "incident_report"),
                        ]

                rheader_tabs = s3_rheader_tabs(r, tabs)

                incident_type_id = record.incident_type_id
                # Dropdown of Scenarios to select
                stable = current.s3db.event_scenario
                query = (stable.incident_type_id == incident_type_id) & \
                        (stable.deleted == False)
                scenarios = current.db(query).select(stable.id,
                                                     stable.name,
                                                     )
                if len(scenarios):
                    from gluon import SELECT, OPTION
                    dropdown = SELECT(_id="scenarios")
                    dropdown["_data-incident_id"] = r.id
                    dappend = dropdown.append
                    dappend(OPTION(T("Select Scenario")))
                    for s in scenarios:
                        dappend(OPTION(s.name, _value=s.id))
                    scenarios = TR(TH("%s: " % T("Scenario")),
                                   dropdown,
                                   )
                    s3 = current.response.s3
                    script = "/%s/static/themes/SAFIRE/js/incident_profile.js" % r.application
                    if script not in s3.scripts:
                        s3.scripts.append(script)
                        s3.js_global.append('''i18n.scenarioConfirm="%s"''' % T("Populate Incident with Tasks, Positions and Equipment from the Scenario?"))
                else:
                    scenarios = ""

                if record.exercise:
                    exercise = TH(T("EXERCISE"))
                else:
                    exercise = TH()
                if record.closed:
                    closed = TH(T("CLOSED"))
                else:
                    closed = TH()
                table = r.table
                rheader = DIV(TABLE(TR(exercise),
                                    TR(TH("%s: " % table.name.label),
                                       record.name,
                                       ),
                                    TR(TH("%s: " % table.incident_type_id.label),
                                       table.incident_type_id.represent(incident_type_id),
                                       ),
                                    TR(TH("%s: " % table.person_id.label),
                                       table.person_id.represent(record.person_id),
                                       ),
                                    scenarios,
                                    TR(TH("%s: " % table.location_id.label),
                                       table.location_id.represent(record.location_id),
                                       ),
                                    TR(TH("%s: " % table.comments.label),
                                       record.comments,
                                       ),
                                    TR(TH("%s: " % table.date.label),
                                       table.date.represent(record.date),
                                       ),
                                    TR(closed),
                                    ), rheader_tabs)

            elif name == "scenario":
                # Scenarios Controller
                tabs = [(T("Scenario Details"), None),
                        #(T("Tasks"), "task"),
                        #(T("Human Resources"), "human_resource"),
                        #(T("Equipment"), "asset"),
                        (T("Action Plan"), "plan"),
                        (T("Incident Reports"), "incident_report"),
                        ]

                rheader_tabs = s3_rheader_tabs(r, tabs)

                table = r.table
                rheader = DIV(TABLE(TR(TH("%s: " % table.incident_type_id.label),
                                       table.incident_type_id.represent(record.incident_type_id),
                                       ),
                                    TR(TH("%s: " % table.name.label),
                                       record.name,
                                       ),
                                    TR(TH("%s: " % table.comments.label),
                                       record.comments,
                                       ),
                                    ), rheader_tabs)

        return rheader

    # -------------------------------------------------------------------------
    def customise_event_incident_report_controller(**attr):

        from gluon import A, URL

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard postp
            if callable(standard_prep):
                result = standard_prep(r)

            if r.method in (None, "create"):
                current.s3db.gis_location.addr_street.label = T("Street Address or Location Details")
                from s3 import S3SQLCustomForm
                crud_form = S3SQLCustomForm((T("What is it?"), "name"),
                                            "incident_type_id",
                                            (T("Who am I speaking with?"), "reported_by"),
                                            (T("How can we contact you?"), "contact"),
                                            (T("Where did this Incident take place?"), "location_id"),
                                            (T("Explain the Situation?"), "description"),
                                            (T("What are your immediate needs?"), "needs"),
                                            )
                r.resource.configure(create_next = URL(args=["[id]", "assign"]),
                                     crud_form = crud_form,
                                     )

            return True
        s3.prep = custom_prep

        # No sidebar menu
        current.menu.options = None
        req_args = current.request.args
        if len(req_args) > 1 and req_args[1] == "assign":
            attr["rheader"] = A(T("New Incident"),
                                _class="action-btn",
                                _href=URL(c="event", f="incident",
                                          args=["create"],
                                          vars={"incident_report_id": req_args[0]},
                                          ),
                                )

        return attr

    settings.customise_event_incident_report_controller = customise_event_incident_report_controller

    # -------------------------------------------------------------------------
    def customise_event_incident_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3

        # Load default model, so we can over-ride
        s3db.event_incident

        from gluon import URL
        s3db.configure("event_incident",
                       create_next = URL(c="event", f="incident",
                                         args=["[id]", "plan"]),
                       )

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard postp
            if callable(standard_prep):
                result = standard_prep(r)

            if r.method == "create":
                incident_report_id = r.get_vars.get("incident_report_id")
                if incident_report_id:
                    if r.http == "GET":
                        from s3 import s3_truncate
                        rtable = s3db.event_incident_report
                        incident_report = current.db(rtable.id == incident_report_id).select(rtable.name,
                                                                                             rtable.incident_type_id,
                                                                                             rtable.location_id,
                                                                                             limitby = (0, 1),
                                                                                             ).first()
                        table = r.table
                        table.name.default = s3_truncate(incident_report.name, 64)
                        table.incident_type_id.default = incident_report.incident_type_id
                        table.location_id.default = incident_report.location_id

                    elif r.http == "POST":
                        def create_onaccept(form):
                            s3db.event_incident_report_incident.insert(incident_id = form.vars.id,
                                                                       incident_report_id = incident_report_id,
                                                                       )

                        r.resource.configure(create_onaccept = create_onaccept,
                                             )

            return True
        s3.prep = custom_prep

        # No sidebar menu
        current.menu.options = None
        attr["rheader"] = event_rheader

        return attr

    settings.customise_event_incident_controller = customise_event_incident_controller

    # -------------------------------------------------------------------------
    def customise_event_asset_resource(r, tablename):

        table = current.s3db.event_asset
        table.item_id.label = T("Item Type")
        table.asset_id.label = T("Specific Item")
        # DateTime
        from gluon import IS_EMPTY_OR
        from s3 import IS_UTC_DATETIME, S3CalendarWidget, S3DateTime
        for f in (table.start_date, table.end_date):
            f.requires = IS_EMPTY_OR(IS_UTC_DATETIME())
            f.represent = lambda dt: S3DateTime.datetime_represent(dt, utc=True)
            f.widget = S3CalendarWidget(timepicker = True)

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Equipment"),
            title_display = T("Equipment Details"),
            title_list = T("Equipment"),
            title_update = T("Edit Equipment"),
            label_list_button = T("List Equipment"),
            label_delete_button = T("Remove Equipment from this incident"),
            msg_record_created = T("Equipment added"),
            msg_record_modified = T("Equipment updated"),
            msg_record_deleted = T("Equipment removed"),
            msg_list_empty = T("No Equipment currently registered for this incident"))

    settings.customise_event_asset_resource = customise_event_asset_resource

    # -------------------------------------------------------------------------
    def customise_event_human_resource_resource(r, tablename):

        table = current.s3db.event_human_resource
        # DateTime
        from gluon import IS_EMPTY_OR
        from s3 import IS_UTC_DATETIME, S3CalendarWidget, S3DateTime
        for f in (table.start_date, table.end_date):
            f.requires = IS_EMPTY_OR(IS_UTC_DATETIME())
            f.represent = lambda dt: S3DateTime.datetime_represent(dt, utc=True)
            f.widget = S3CalendarWidget(timepicker = True)

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Person"),
            title_display = T("Person Details"),
            title_list = T("Personnel"),
            title_update = T("Edit Person"),
            label_list_button = T("List Personnel"),
            label_delete_button = T("Remove Person from this incident"),
            msg_record_created = T("Person added"),
            msg_record_modified = T("Person updated"),
            msg_record_deleted = T("Person removed"),
            msg_list_empty = T("No Persons currently registered for this incident"))

    settings.customise_event_human_resource_resource = customise_event_human_resource_resource

    # -------------------------------------------------------------------------
    def customise_event_scenario_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard postp
            if callable(standard_prep):
                result = standard_prep(r)

            if r.method == "create"and r.http == "POST":
                from gluon import URL
                r.resource.configure(create_next = URL(c="event", f="scenario",
                                                       args=["[id]", "plan"]),
                                     )

            return True
        s3.prep = custom_prep

        # No sidebar menu
        current.menu.options = None
        attr["rheader"] = event_rheader

        return attr

    settings.customise_event_scenario_controller = customise_event_scenario_controller

    # -------------------------------------------------------------------------
    def customise_event_scenario_asset_resource(r, tablename):

        table = current.s3db.event_scenario_asset
        table.item_id.label = T("Item Type")
        table.asset_id.label = T("Specific Item")

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Equipment"),
            title_display = T("Equipment Details"),
            title_list = T("Equipment"),
            title_update = T("Edit Equipment"),
            label_list_button = T("List Equipment"),
            label_delete_button = T("Remove Equipment from this incident"),
            msg_record_created = T("Equipment added"),
            msg_record_modified = T("Equipment updated"),
            msg_record_deleted = T("Equipment removed"),
            msg_list_empty = T("No Equipment currently registered for this incident"))

    settings.customise_event_scenario_asset_resource = customise_event_scenario_asset_resource

    # -------------------------------------------------------------------------
    def customise_event_scenario_human_resource_resource(r, tablename):

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Person"),
            title_display = T("Person Details"),
            title_list = T("Personnel"),
            title_update = T("Edit Person"),
            label_list_button = T("List Personnel"),
            label_delete_button = T("Remove Person from this incident"),
            msg_record_created = T("Person added"),
            msg_record_modified = T("Person updated"),
            msg_record_deleted = T("Person removed"),
            msg_list_empty = T("No Persons currently registered for this incident"))

    settings.customise_event_scenario_human_resource_resource = customise_event_scenario_human_resource_resource

    # -------------------------------------------------------------------------
    # HRM
    # -------------------------------------------------------------------------
    settings.hrm.job_title_deploy = True

    # -------------------------------------------------------------------------
    def customise_hrm_job_title_resource(r, tablename):

        #if r.controller == "event":
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Position"),
            title_display = T("Position Details"),
            title_list = T("Positions"),
            title_update = T("Edit Position"),
            label_list_button = T("List Positions"),
            label_delete_button = T("Remove Position"),
            msg_record_created = T("Position added"),
            msg_record_modified = T("Position updated"),
            msg_record_deleted = T("Position removed"),
            msg_list_empty = T("No Positions currently registered"))

    settings.customise_hrm_job_title_resource = customise_hrm_job_title_resource

# END =========================================================================