# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current, URL
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
    settings.base.prepopulate += ("SAFIRE",)
    settings.base.prepopulate_demo += ("SAFIRE/Demo",)

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "SAFIRE"

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

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
        ("vehicle", Storage(
            name_nice = "Vehicles",
            #description = "Manage Vehicles",
            restricted = True,
            module_type = 10,
        )),
        #("req", Storage(
        #    name_nice = "Requests",
        #    #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
        #    restricted = True,
        #    module_type = 10,
        #)),
        ("project", Storage(
            name_nice = "Tasks",
            #description = "Tracking of Projects, Activities and Tasks",
            restricted = True,
            module_type = 2
        )),
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
    # CMS
    # -------------------------------------------------------------------------
    settings.cms.richtext = True
    
    # -------------------------------------------------------------------------
    # Organisations
    # -------------------------------------------------------------------------
    settings.org.documents_tab = True
    settings.org.projects_tab = False

    # -------------------------------------------------------------------------
    # Shelters
    # -------------------------------------------------------------------------
    settings.cr.people_registration = False

    # -------------------------------------------------------------------------
    # Events
    # -------------------------------------------------------------------------
    def event_rheader(r):
        rheader = None

        record = r.record
        if record and r.representation == "html":

            from gluon import A, DIV, TABLE, TR, TH
            from s3 import s3_rheader_tabs

            name = r.name
            if name == "incident":
                tabs = [(T("Incident Details"), None),
                        #(T("Tasks"), "task"),
                        #(T("Human Resources"), "human_resource"),
                        #(T("Equipment"), "asset"),
                        (T("Action Plan"), "plan"),
                        (T("Incident Reports"), "incident_report"),
                        (T("Logs"), "log"),
                        (T("Situation Reports"), "sitrep"),
                        ]

                rheader_tabs = s3_rheader_tabs(r, tabs)

                record_id = r.id
                incident_type_id = record.incident_type_id

                # Dropdown of Scenarios to select
                stable = current.s3db.event_scenario
                query = (stable.incident_type_id == incident_type_id) & \
                        (stable.deleted == False)
                scenarios = current.db(query).select(stable.id,
                                                     stable.name,
                                                     )
                if len(scenarios) and r.method != "event":
                    from gluon import SELECT, OPTION
                    dropdown = SELECT(_id="scenarios")
                    dropdown["_data-incident_id"] = record_id
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

                if record.event_id or r.method == "event":
                    event = ""
                else:
                    event = A(T("Assign to Event"),
                                _href = URL(c = "event",
                                            f = "incident",
                                            args = [record_id, "event"],
                                            ),
                                _class = "action-btn"
                                )

                table = r.table
                rheader = DIV(TABLE(TR(exercise),
                                    TR(TH("%s: " % table.name.label),
                                       record.name,
                                       ),
                                    TR(TH("%s: " % table.incident_type_id.label),
                                       table.incident_type_id.represent(incident_type_id),
                                       ),
                                    TR(TH("%s: " % table.location_id.label),
                                       table.location_id.represent(record.location_id),
                                       ),
                                    # @ToDo: Add Zone
                                    TR(TH("%s: " % table.severity.label),
                                       table.severity.represent(record.severity),
                                       ),
                                    TR(TH("%s: " % table.level.label),
                                       table.level.represent(record.level),
                                       ),
                                    TR(TH("%s: " % table.organisation_id.label),
                                       table.organisation_id.represent(record.organisation_id),
                                       ),
                                    TR(TH("%s: " % table.person_id.label),
                                       table.person_id.represent(record.person_id),
                                       ),
                                    scenarios,
                                    TR(TH("%s: " % table.comments.label),
                                       record.comments,
                                       ),
                                    TR(TH("%s: " % table.date.label),
                                       table.date.represent(record.date),
                                       ),
                                    TR(closed),
                                    event,
                                    ), rheader_tabs)

            elif name == "incident_report":
                record_id = r.id
                ltable = current.s3db.event_incident_report_incident
                query = (ltable.incident_report_id == record_id)
                link = current.db(query).select(ltable.incident_id,
                                                limitby = (0, 1)
                                                ).first()
                if link:
                    from s3 import S3Represent
                    represent = S3Represent(lookup="event_incident", show_link=True)
                    rheader = DIV(TABLE(TR(TH("%s: " % ltable.incident_id.label),
                                           represent(link.incident_id),
                                           ),
                                        ))
                else:
                    rheader = DIV(A(T("Assign to Incident"),
                                    _href = URL(c = "event",
                                                f = "incident_report",
                                                args = [record_id, "assign"],
                                                ),
                                    _class = "action-btn"
                                    ))
                    

            elif name == "event":
                tabs = [(T("Event Details"), None),
                        (T("Incidents"), "incident"),
                        (T("Documents"), "document"),
                        (T("Photos"), "image"),
                        ]

                rheader_tabs = s3_rheader_tabs(r, tabs)

                table = r.table
                rheader = DIV(TABLE(TR(TH("%s: " % table.event_type_id.label),
                                       table.event_type_id.represent(record.event_type_id),
                                       ),
                                    TR(TH("%s: " % table.name.label),
                                       record.name,
                                       ),
                                    TR(TH("%s: " % table.start_date.label),
                                       table.start_date.represent(record.start_date),
                                       ),
                                    TR(TH("%s: " % table.comments.label),
                                       record.comments,
                                       ),
                                    ), rheader_tabs)

            elif name == "scenario":
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
    def customise_event_event_controller(**attr):

        #s3 = current.response.s3

        # No sidebar menu
        #current.menu.options = None
        attr["rheader"] = event_rheader

        return attr

    settings.customise_event_event_controller = customise_event_event_controller

    # -------------------------------------------------------------------------
    def customise_event_incident_report_controller(**attr):

        from gluon import A

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard postp
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

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
        else:
            attr["rheader"] = event_rheader

        return attr

    settings.customise_event_incident_report_controller = customise_event_incident_report_controller

    # -------------------------------------------------------------------------
    def event_incident_create_onaccept(form):
        """
            Automate Level based on Type, Zone (intersect from Location) & Severity
            @ToDo: Move this to SAFIRE\SC
        """

        db = current.db
        s3db = current.s3db

        form_vars_get = form.vars.get
        incident_id = form_vars_get("id")

        # If Incident Type is Chemical then level must be > 2
        level = form_vars_get("level")
        if level and int(level) < 3:
            incident_type_id = form_vars_get("incident_type_id")
            ittable = s3db.event_incident_type
            incident_type = db(ittable.id == incident_type_id).select(ittable.name,
                                                                      limitby = (0,1)
                                                                      ).first().name
            if incident_type == "Chemical Hazard":
                itable = s3db.event_incident
                db(itable.id == incident_id).update(level = 3)
                current.response.warning = T("Chemical Hazard Incident so Level raised to 3")

        # Alert Lead Agency
        # @ToDo: This should use a new on-call org KV tag
        organisation_id = form_vars_get("organisation_id")
        if organisation_id:
            otable = s3db.org_organisation
            org = db(otable.id == organisation_id).select(otable.pe_id,
                                                          limitby = (0, 1)
                                                          ).first()
            current.msg.send_by_pe_id(org.pe_id,
                                      subject = "",
                                      message = "You have been assigned an Incident: %s%s" % (settings.get_base_public_url(),
                                                                                              URL(c="event", f= "incident",
                                                                                                  args = incident_id),
                                                                                              ),
                                      contact_method = "SMS")

    # -------------------------------------------------------------------------
    def customise_event_incident_resource(r, tablename):

        s3db = current.s3db

        table = s3db.event_incident
        f = table.severity
        f.readable = f.writable = True
        f = table.level
        f.readable = f.writable = True
        f = table.organisation_id
        f.readable = f.writable = True
        f.label = T("Lead Response Organization")

        if r.interactive:
            s3db.add_custom_callback(tablename,
                                     "create_onaccept",
                                     event_incident_create_onaccept,
                                     )

    settings.customise_event_incident_resource = customise_event_incident_resource

    # -------------------------------------------------------------------------
    def customise_event_incident_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard postp
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            resource = r.resource

            # Redirect to action plan after create
            resource.configure(create_next = URL(c="event", f="incident",
                                                 args = ["[id]", "plan"]),
                               )

            if r.method == "create":
                incident_report_id = r.get_vars.get("incident_report_id")
                if incident_report_id:
                    # Got here from incident report assign => "New Incident"
                    # - prepopulate incident name from report title
                    # - copy incident type and location from report
                    # - onaccept: link the incident report to the incident
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

                        s3db.add_custom_callback("event_incident",
                                                 "create_onaccept",
                                                 create_onaccept,
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
    def event_human_resource_onaccept(form):
        """
            @ToDo: Send Person a Notification when they are assigned to an Incident
                - @ToDo: Add field to the table to keep track of which user has been notified so we can update & notify or not accordingly
        """

        form_vars_get = form.vars.get

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
            #title_list = T("Personnel"),
            title_list = T("Responders"),
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
                if not result:
                    return False

            if r.method == "create"and r.http == "POST":
                r.resource.configure(create_next = URL(c="event", f="scenario",
                                                       args = ["[id]", "plan"]),
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
            #title_list = T("Personnel"),
            title_list = T("Responders"),
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

    # -------------------------------------------------------------------------
    # Projects
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    def project_task_onaccept(form):
        """
            @ToDo: Send Person a Notification when they are assigned to a Task
                - @ToDo: Add field to the table to keep track of which user has been notified so we can update & notify or not accordingly
        """

        form_vars_get = form.vars.get

    # -------------------------------------------------------------------------
    def customise_project_task_resource(r, tablename):

        s3db = current.s3db

        f = s3db.project_task.source
        f.readable = f.writable = False

        # No need to see log time: KISS
        s3db.configure(tablename,
                       crud_form = None,
                       # In event_ActionPlan()
                       #list_fields = ["priority",
                       #               "name",
                       #               "pe_id",
                       #               "status_id",
                       #               "date_due",
                       #               ],
                       )

    settings.customise_project_task_resource = customise_project_task_resource

# END =========================================================================
