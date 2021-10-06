# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current, URL
from gluon.storage import Storage

def config(settings):
    """
        Template settings for SaFiRe: Sahana First Response

        http://eden.sahanafoundation.org/wiki/BluePrint/SAFIRE
    """

    T = current.T

    settings.base.system_name = T("Sahana First Response")
    settings.base.system_name_short = T("SAFIRE")

    # PrePopulate data
    settings.base.prepopulate.append("SAFIRE")
    settings.base.prepopulate_demo.append("SAFIRE/Demo")

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

    settings.auth.registration_link_user_to = {"staff": T("Staff"),
                                               }

    settings.auth.registration_link_user_to_default = ["staff"]

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
    settings.security.policy = 5 # Controller, Function & Table ACLs

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # Modules menu is defined in modules/eden/menu.py
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
            name_nice = "Home",
            restricted = False, # Use ACLs to control access to this module
            #access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None  # This item is not shown in the menu
        )),
        ("admin", Storage(
            name_nice = "Administration",
            #description = "Site Administration",
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        ("appadmin", Storage(
            name_nice = "Administration",
            #description = "Site Administration",
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
            module_type = 6,     # 6th item in the menu
        )),
        ("pr", Storage(
            name_nice = "Person Registry",
            #description = "Central point to record details on People",
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
        ("org", Storage(
            name_nice = "Organizations",
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            module_type = 1
        )),
        ("hrm", Storage(
            name_nice = "Staff",
            #description = "Human Resources Management",
            module_type = 2,
        )),
        ("vol", Storage(
            name_nice = T("Volunteers"),
            #description = "Human Resources Management",
            module_type = 2,
        )),
        ("cms", Storage(
            name_nice = "Content Management",
            #description = "Content Management System",
            module_type = 10,
        )),
        ("doc", Storage(
            name_nice = "Documents",
            #description = "A library of digital resources, such as photos, documents and reports",
            module_type = 10,
        )),
        ("msg", Storage(
            name_nice = "Messaging",
            #description = "Sends & Receives Alerts via Email & SMS",
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
        ("supply", Storage(
            name_nice = "Supply Chain Management",
            #description = "Used within Inventory Management, Request Management and Asset Management",
            module_type = None, # Not displayed
        )),
        ("inv", Storage(
            name_nice = T("Warehouses"),
            #description = "Receiving and Sending Items",
            module_type = 4
        )),
        ("asset", Storage(
            name_nice = "Assets",
            #description = "Recording and Assigning Assets",
            module_type = 5,
        )),
        # Vehicle depends on Assets
        ("vehicle", Storage(
            name_nice = "Vehicles",
            #description = "Manage Vehicles",
            module_type = 10,
        )),
        #("budget", Storage(
        #    name_nice = T("Budgets"),
        #    #description = "Tracks the location, capacity and breakdown of victims in Shelters",
        #    module_type = 10
        #)),
        ("fin", Storage(
            name_nice = T("Finance"),
            module_type = 10
        )),
        ("cr", Storage(
            name_nice = T("Shelters"),
            #description = "Tracks the location, capacity and breakdown of victims in Shelters",
            module_type = 10
        )),
        ("project", Storage(
            name_nice = "Tasks",
            #description = "Tracking of Projects, Activities and Tasks",
            module_type = 2
        )),
        ("req", Storage(
            name_nice = "Requests",
            #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
            module_type = 10,
        )),
        ("hms", Storage(
            name_nice = T("Hospitals"),
            #description = "Helps to monitor status of hospitals",
            module_type = 10
        )),
        #("dvr", Storage(
        #   name_nice = T("Disaster Victim Registry"),
        #   #description = "Allow affected individuals & households to register to receive compensation and distributions",
        #   module_type = 10,
        #)),
        ("event", Storage(
            name_nice = "Events",
            #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
            module_type = 10,
        )),
        #("transport", Storage(
        #   name_nice = T("Transport"),
        #   module_type = 10,
        #)),
        #("stats", Storage(
        #    name_nice = T("Statistics"),
        #    #description = "Manages statistics",
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
    #def customise_cr_shelter_resource(r, tablename):

        #table = current.s3db.cr_shelter

    #settings.customise_cr_shelter_resource = customise_cr_shelter_resource

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
                if r.method == "event":
                    # event_EventAssignMethod
                    if settings.get_event_label(): # == "Disaster"
                        label = T("New Disaster")
                    else:
                        label = T("New Event")
                    return A(label,
                             _class = "action-btn",
                             _href = URL(c="event", f="event",
                                         args = ["create"],
                                         vars = {"incident_id": r.id},
                                         ),
                             )
                if settings.get_incident_label(): # == "Ticket"
                    label = T("Ticket Details")
                else:
                    label = T("Incident Details")
                tabs = [(label, None),
                        #(T("Tasks"), "task"),
                        #(T("Human Resources"), "human_resource"),
                        #(T("Equipment"), "asset"),
                        (T("Action Plan"), "plan"),
                        (T("Incident Reports"), "incident_report"),
                        (T("Logs"), "log"),
                        (T("Expenses"), "expense"),
                        (T("Situation Reports"), "sitrep"),
                        ]

                rheader_tabs = s3_rheader_tabs(r, tabs)

                table = r.table
                record_id = r.id
                incident_type_id = record.incident_type_id

                editable = current.auth.s3_has_permission("UPDATE", "event_incident", record_id)

                if editable and r.method == "plan":
                    # Dropdown of Scenarios to select
                    # @ToDo: Move this to a Popup behind an Action Button, to make it clearer that this isn't a maintained link
                    # @ToDo: Also add 'Clear' button to clear all elements & start from a blank slate
                    stable = current.s3db.event_scenario
                    query = (stable.incident_type_id == incident_type_id) & \
                            (stable.deleted == False)
                    scenarios = current.db(query).select(stable.id,
                                                         stable.name,
                                                         )
                    if len(scenarios) and r.method != "event":
                        from gluon import SELECT, OPTION
                        dropdown = SELECT(_id = "scenarios")
                        dropdown["_data-incident_id"] = record_id
                        dappend = dropdown.append
                        dappend(OPTION(T("Select Scenario")))
                        for s in scenarios:
                            dappend(OPTION(s.name,
                                           _value = s.id,
                                           ))
                        scenarios = TR(TH("%s: " % T("Apply Scenario")),
                                       dropdown,
                                       )
                        s3 = current.response.s3
                        script = "/%s/static/themes/SAFIRE/js/incident_profile.js" % r.application
                        if script not in s3.scripts:
                            s3.scripts.append(script)
                            s3.js_global.append('''i18n.scenarioConfirm="%s"''' % T("Populate Incident with Tasks, Organizations, Positions and Equipment from the Scenario?"))
                    else:
                        scenarios = ""
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

                if record.event_id:
                    event = TR(TH("%s: " % table.event_id.label),
                               table.event_id.represent(record.event_id,
                                                        show_link = True,
                                                        ),
                               )
                elif r.method == "event" or not editable:
                    event = ""
                else:
                    if settings.get_event_label(): # == "Disaster"
                        label = T("Assign to Disaster")
                    else:
                        label = T("Assign to Event")
                    event = A(label,
                              _href = URL(c = "event",
                                          f = "incident",
                                          args = [record_id, "event"],
                                          ),
                              _class = "action-btn"
                              )

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
                                    #TR(TH("%s: " % table.severity.label),
                                    #   table.severity.represent(record.severity),
                                    #   ),
                                    #TR(TH("%s: " % table.level.label),
                                    #   table.level.represent(record.level),
                                    #   ),
                                    TR(TH("%s: " % table.organisation_id.label),
                                       table.organisation_id.represent(record.organisation_id),
                                       ),
                                    TR(TH("%s: " % table.person_id.label),
                                       table.person_id.represent(record.person_id),
                                       ),
                                    scenarios,
                                    TR(TH("%s: " % table.comments.label),
                                       record.comments or current.messages["NONE"],
                                       ),
                                    TR(TH("%s: " % table.date.label),
                                       table.date.represent(record.date),
                                       ),
                                    TR(closed),
                                    event,
                                    ),
                              rheader_tabs,
                              )

            elif name == "incident_report":
                if r.method == "assign":
                    # event_IncidentAssignMethod
                    if settings.get_incident_label(): # == "Ticket"
                        label = T("New Ticket")
                    else:
                        label = T("New Incident")
                    return A(label,
                             _class = "action-btn",
                             _href = URL(c="event", f="incident",
                                         args = ["create"],
                                         vars = {"incident_report_id": r.id},
                                         ),
                             )
                record_id = r.id
                ltable = current.s3db.event_incident_report_incident
                query = (ltable.incident_report_id == record_id)
                link = current.db(query).select(ltable.incident_id,
                                                limitby = (0, 1),
                                                ).first()
                if link:
                    from s3 import S3Represent
                    represent = S3Represent(lookup="event_incident", show_link=True)
                    rheader = DIV(TABLE(TR(TH("%s: " % ltable.incident_id.label),
                                           represent(link.incident_id),
                                           ),
                                        ))
                else:
                    if settings.get_incident_label(): # == "Ticket"
                        label = T("Assign to Ticket")
                    else:
                        label = T("Assign to Incident")
                    rheader = DIV(A(label,
                                    _href = URL(c = "event",
                                                f = "incident_report",
                                                args = [record_id, "assign"],
                                                ),
                                    _class = "action-btn"
                                    ))

            elif name == "event":
                if settings.get_event_label(): # == "Disaster"
                    label = T("Disaster Details")
                else:
                    label = T("Event Details")
                if settings.get_incident_label(): # == "Ticket"
                    INCIDENTS = T("Tickets")
                else:
                    INCIDENTS = T("Incidents")
                tabs = [(label, None),
                        (INCIDENTS, "incident"),
                        ]
                if settings.get_event_impact_tab():
                    tabs.append((T("Impact"), "impact"))
                if settings.get_event_dc_target_tab():
                    tabs.append((T("Assessment Targets"), "target"))
                tabs += [(T("Documents"), "document"),
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
                                    ),
                              rheader_tabs,
                              )

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
                                    TR(TH("%s: " % table.organisation_id.label),
                                       table.organisation_id.represent(record.organisation_id),
                                       ),
                                    TR(TH("%s: " % table.location_id.label),
                                       table.location_id.represent(record.location_id),
                                       ),
                                    TR(TH("%s: " % table.name.label),
                                       record.name,
                                       ),
                                    TR(TH("%s: " % table.comments.label),
                                       record.comments,
                                       ),
                                    ),
                              rheader_tabs,
                              )

        return rheader

    # -------------------------------------------------------------------------
    def customise_dc_target_resource(r, tablename):

        if r.controller in ("event",
                            "hrm", # Training Event Evaluations
                            ):
            return

        s3db = current.s3db

        from s3 import S3DateFilter, S3LocationFilter, S3OptionsFilter, S3SQLCustomForm, S3SQLInlineLink

        crud_form = S3SQLCustomForm(S3SQLInlineLink("event",
                                                    field = "event_id",
                                                    #label = type_label,
                                                    multiple = False,
                                                    ),
                                    "template_id",
                                    "date",
                                    "location_id",
                                    "comments",
                                    )

        filter_widgets = [S3OptionsFilter("event__link.event_id"),
                          S3LocationFilter(),
                          S3DateFilter("date"),
                          ]

        list_fields = ["event__link.event_id",
                       "location_id$L1",
                       "location_id$L2",
                       "name",
                       (T("Reporting Date"), "date"),
                       (T("Reported by"), "created_by"),
                       ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_dc_target_resource = customise_dc_target_resource

    # -------------------------------------------------------------------------
    def customise_event_event_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard postp
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            if r.method == "create":
                incident_id = r.get_vars.get("incident_id")
                if incident_id:
                    # Got here from incident assign => "New Event"
                    # - prepopulate event name from incident title
                    # - copy location from incident
                    # @ToDo: default event_type from incident_type
                    # - onaccept: link the incident to the event
                    s3db = current.s3db
                    if r.http == "GET":
                        itable = s3db.event_incident
                        incident = current.db(itable.id == incident_id).select(itable.name,
                                                                               #itable.incident_type_id,
                                                                               itable.location_id,
                                                                               limitby = (0, 1),
                                                                               ).first()
                        table = r.table
                        table.name.default = incident.name
                        #table.event_type_id.default = incident.incident_type_id
                        s3db.event_event_location.location_id.default = incident.location_id

                    elif r.http == "POST":
                        def create_onaccept(form):
                            current.db(s3db.event_incident.id == incident_id).update(event_id = form.vars.id)

                        s3db.add_custom_callback("event_event",
                                                 "create_onaccept",
                                                 create_onaccept,
                                                 )

            return True
        s3.prep = custom_prep

        # No sidebar menu
        #current.menu.options = None

        attr["rheader"] = event_rheader

        return attr

    settings.customise_event_event_controller = customise_event_event_controller

    # -------------------------------------------------------------------------
    def customise_event_incident_report_resource(r, tablename):

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Log Call"),
            title_display = T("Call Log Details"),
            title_list = T("Call Logs"),
            title_update = T("Edit Call Log"),
            label_list_button = T("List Call Logs"),
            label_delete_button = T("Delete Call Log"),
            msg_record_created = T("Call Log added"),
            msg_record_modified = T("Call Log updated"),
            msg_record_deleted = T("Call Log removed"),
            msg_list_empty = T("No Calls currently logged"),
            )

        from s3 import S3LocationSelector

        current.s3db.event_incident_report.location_id.widget = \
            S3LocationSelector(polygons = True,
                               show_address = True,
                               )

    settings.customise_event_incident_report_resource = customise_event_incident_report_resource

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

            method = r.method
            if method in (None, "create"):
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
                r.resource.configure(create_next = URL(args = ["[id]", "assign"]),
                                     crud_form = crud_form,
                                     )

            return True
        s3.prep = custom_prep

        # No sidebar menu
        current.menu.options = None

        # RHeader
        attr["rheader"] = event_rheader

        return attr

    settings.customise_event_incident_report_controller = customise_event_incident_report_controller

    # -------------------------------------------------------------------------
    def event_incident_create_onaccept(form):
        """
            Alert Lead Agency
        """

        organisation_id = form.vars.get("organisation_id")
        if organisation_id:
            # Alert Lead Agency via their Duty Number
            otable = current.s3db.org_organisation_tag
            query = (otable.organisation_id == organisation_id) & \
                    (otable.tag == "duty")
            duty = current.db(query).select(otable.value,
                                            limitby = (0, 1),
                                            ).first()
            if duty:
                incident_id = form.vars.get("id")
                # @ToDo: i18n
                current.msg.send_sms_via_api(duty.value,
                    "You have been assigned an Incident: %s%s" % (settings.get_base_public_url(),
                                                                  URL(c="event", f= "incident",
                                                                      args = incident_id),
                                                                  ))

    # -------------------------------------------------------------------------
    def customise_event_incident_resource(r, tablename):

        from s3 import S3LocationSelector

        s3db = current.s3db

        table = s3db.event_incident
        table.location_id.widget = S3LocationSelector(polygons = True,
                                                      show_address = True,
                                                      )
        f = table.organisation_id
        f.readable = f.writable = True
        f.label = T("Lead Response Organization")
        if r.method == "plan":
            table.action_plan.label = T("Event Action Plan")
        else:
            f = table.action_plan
            f.readable = f.writable = False

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
                                                 args = ["[id]", "plan"],
                                                 ),
                               )

            method = r.method
            if method == "create":
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

            elif method == "plan" and settings.get_incident_label(): # == "Ticket"
                s3db.event_task
                s3db.event_organisation
                crud_strings = s3.crud_strings
                crud_strings.event_task.msg_list_empty = T("No Tasks currently registered for this ticket")
                crud_strings.event_organisation.msg_list_empty = T("No Organizations currently registered in this ticket")

            return True
        s3.prep = custom_prep

        # No sidebar menu
        current.menu.options = None

        # RHeader
        attr["rheader"] = event_rheader

        return attr

    settings.customise_event_incident_controller = customise_event_incident_controller

    # -------------------------------------------------------------------------
    def customise_event_asset_resource(r, tablename):

        table = current.s3db.event_asset
        table.item_id.label = T("Item Type")
        table.asset_id.label = T("Specific Item")

        if settings.get_incident_label(): # == "Ticket"
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Add Equipment"),
                title_display = T("Equipment Details"),
                title_list = T("Equipment"),
                title_update = T("Edit Equipment"),
                label_list_button = T("List Equipment"),
                label_delete_button = T("Remove Equipment from this ticket"),
                msg_record_created = T("Equipment added"),
                msg_record_modified = T("Equipment updated"),
                msg_record_deleted = T("Equipment removed"),
                msg_list_empty = T("No Equipment currently registered for this ticket"),
                )
        else:
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
                msg_list_empty = T("No Equipment currently registered for this incident"),
                )

    settings.customise_event_asset_resource = customise_event_asset_resource

    # -------------------------------------------------------------------------
    def event_human_resource_onaccept(form, create=True):
        """
            When a Position is assigned to an Incident:
             - set_event_from_incident
             - add Log Entry
             - send Notification
        """

        db = current.db
        s3db = current.s3db

        from s3db.event import event_set_event_from_incident
        event_set_event_from_incident(form, "event_human_resource")

        table = s3db.event_human_resource

        form_vars = form.vars
        form_vars_get = form_vars.get
        link_id = form_vars_get("id")
        incident_id = form_vars_get("incident_id")
        if not incident_id:
            link = db(table.id == link_id).select(table.incident_id,
                                                  limitby = (0, 1),
                                                  ).first()
            incident_id = link.incident_id

        pe_id = None
        if create:
            person_id = form_vars_get("person_id")
            if person_id:
                ptable = s3db.pr_person
                person = db(ptable.id == person_id).select(ptable.pe_id,
                                                           limitby = (0, 1),
                                                           ).first()
                pe_id = person.pe_id

            job_title_id = form_vars_get("job_title_id")
            if job_title_id:
                s3db.event_incident_log.insert(incident_id = incident_id,
                                               name = "Person Requested",
                                               comments = s3db.event_human_resource.job_title_id.represent(job_title_id),
                                               )
        else:
            # Update
            record = form.record
            if record: # Not True for a record merger
                from s3dal import Field
                changed = {}
                for var in form_vars:
                    vvar = form_vars[var]
                    if isinstance(vvar, Field):
                        # modified_by/modified_on
                        continue
                    rvar = record.get(var, "NOT_PRESENT")
                    if rvar != "NOT_PRESENT" and vvar != rvar:
                        f = table[var]
                        if var == "pe_id":
                            pe_id = vvar
                        type_ = f.type
                        if type_ == "integer" or \
                           type_.startswith("reference"):
                            if vvar:
                                vvar = int(vvar)
                            if vvar == rvar:
                                continue
                        represent = table[var].represent
                        if represent:
                            if hasattr(represent, "show_link"):
                                represent.show_link = False
                        else:
                            represent = lambda o: o
                        if rvar:
                            changed[var] = "%s changed from %s to %s" % \
                                (f.label, represent(rvar), represent(vvar))
                        else:
                            changed[var] = "%s changed to %s" % \
                                (f.label, represent(vvar))

                if changed:
                    table = s3db.event_incident_log
                    text = []
                    for var in changed:
                        text.append(changed[var])
                    text = "\n".join(text)
                    table.insert(incident_id = incident_id,
                                 #name = "Person Assigned",
                                 name = "Person Request Updated",
                                 comments = text,
                                 )

        if pe_id:
            # Notify Assignee
            if settings.get_incident_label(): # == "Ticket"
                label = T("Ticket")
            else:
                label = T("Incident")
            # @ToDo: i18n
            current.msg.send_by_pe_id(pe_id,
                                      subject = "",
                                      message = "You have been assigned to an %s: %s%s" % \
                                        (label,
                                         settings.get_base_public_url(),
                                         URL(c="event", f= "incident",
                                             args = [incident_id, "human_resource", link_id]),
                                             ),
                                      contact_method = "SMS"
                                      )

    # -------------------------------------------------------------------------
    def customise_event_human_resource_resource(r, tablename):

        s3db = current.s3db
        table = s3db.event_human_resource
        # DateTime
        from gluon import IS_EMPTY_OR
        from s3 import IS_UTC_DATETIME, S3CalendarWidget, S3DateTime
        for f in (table.start_date, table.end_date):
            f.requires = IS_EMPTY_OR(IS_UTC_DATETIME())
            f.represent = lambda dt: S3DateTime.datetime_represent(dt, utc=True)
            f.widget = S3CalendarWidget(timepicker = True)

        if settings.get_incident_label(): # == "Ticket"
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Add Person"),
                title_display = T("Person Details"),
                title_list = T("Personnel"),
                title_update = T("Edit Person"),
                label_list_button = T("List Personnel"),
                label_delete_button = T("Remove Person from this ticket"),
                msg_record_created = T("Person added"),
                msg_record_modified = T("Person updated"),
                msg_record_deleted = T("Person removed"),
                msg_list_empty = T("No Persons currently registered for this ticket"),
                )
        else:
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
                msg_list_empty = T("No Persons currently registered for this incident"),
                )

        s3db.configure(tablename,
                       # Deliberately over-rides
                       create_onaccept = event_human_resource_onaccept,
                       update_onaccept = lambda form:
                            event_human_resource_onaccept(form, create=False),
                       )

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

            if r.method != "plan":
                f = r.table.action_plan
                f.readable = f.writable = False

            if r.method == "create"and r.http == "POST":
                r.resource.configure(create_next = URL(c="event", f="scenario",
                                                       args = ["[id]", "plan"],
                                                       ),
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

        if settings.get_incident_label(): # == "Ticket"
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Add Equipment"),
                title_display = T("Equipment Details"),
                title_list = T("Equipment"),
                title_update = T("Edit Equipment"),
                label_list_button = T("List Equipment"),
                label_delete_button = T("Remove Equipment from this ticket"),
                msg_record_created = T("Equipment added"),
                msg_record_modified = T("Equipment updated"),
                msg_record_deleted = T("Equipment removed"),
                msg_list_empty = T("No Equipment currently registered for this ticket"),
                )
        else:
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
                msg_list_empty = T("No Equipment currently registered for this incident"),
                )

    settings.customise_event_scenario_asset_resource = customise_event_scenario_asset_resource

    # -------------------------------------------------------------------------
    def customise_event_scenario_human_resource_resource(r, tablename):

        if settings.get_incident_label(): # == "Ticket"
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Add Person"),
                title_display = T("Person Details"),
                title_list = T("Personnel"),
                title_update = T("Edit Person"),
                label_list_button = T("List Personnel"),
                label_delete_button = T("Remove Person from this ticket"),
                msg_record_created = T("Person added"),
                msg_record_modified = T("Person updated"),
                msg_record_deleted = T("Person removed"),
                msg_list_empty = T("No Persons currently registered for this ticket"),
                )
        else:
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
                msg_list_empty = T("No Persons currently registered for this incident"),
                )

    settings.customise_event_scenario_human_resource_resource = customise_event_scenario_human_resource_resource

    # -------------------------------------------------------------------------
    # HRM
    # -------------------------------------------------------------------------
    settings.hrm.job_title_deploy = True
    settings.hrm.org_dependent_job_titles = True

    # -------------------------------------------------------------------------
    # Organisations
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        s3db = current.s3db

        # Custom Components
        s3db.add_components(tablename,
                            org_organisation_tag = (# On-call Duty Number
                                                    {"name": "duty",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "duty",
                                                                  },
                                                     "multiple": False,
                                                     },
                                                    ),
                            )

        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink, \
                       IS_EMPTY_OR, IS_PHONE_NUMBER_MULTI, S3PhoneWidget, s3_phone_represent

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        duty = components_get("duty")
        f = duty.table.value
        f.represent = s3_phone_represent,
        f.requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI())
        f.widget = S3PhoneWidget()

        crud_form = S3SQLCustomForm("name",
                                    "acronym",
                                    S3SQLInlineLink("organisation_type",
                                                    field = "organisation_type_id",
                                                    # Default 10 options just triggers which adds unnecessary complexity to a commonly-used form & commonly an early one (create Org when registering)
                                                    search = False,
                                                    label = T("Type"),
                                                    multiple = False,
                                                    widget = "multiselect",
                                                    ),
                                    "country",
                                    (T("Reception Phone #"), "phone"),
                                    S3SQLInlineComponent("duty",
                                                         label = T("On-call Duty Number"),
                                                         fields = [("", "value")],
                                                         multiple = False,
                                                         ),
                                    "website",
                                    "logo",
                                    "comments",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    # Projects
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    def project_task_onaccept(form, create=True):
        """
            Send Person a Notification when they are assigned to a Task
            Log changes in Incident Log
        """

        if current.request.function == "scenario":
            # Must be a Scenario
            # - don't Log
            # - don't send Notification
            return

        db = current.db
        s3db = current.s3db
        ltable = s3db.event_task

        form_vars = form.vars
        form_vars_get = form_vars.get
        task_id = form_vars_get("id")
        link = db(ltable.task_id == task_id).select(ltable.incident_id,
                                                    limitby = (0, 1),
                                                    ).first()
        if not link:
            # Not attached to an Incident
            # - don't Log
            # - don't send Notification
            return

        incident_id = link.incident_id

        if create:
            pe_id = form_vars_get("pe_id")
            # Log
            name = form_vars_get("name")
            if name:
                s3db.event_incident_log.insert(incident_id = incident_id,
                                               name = "Task Created",
                                               comments = name,
                                               )

        else:
            # Update
            pe_id = None
            record = form.record
            if record: # Not True for a record merger
                from s3dal import Field
                table = s3db.project_task
                changed = {}
                for var in form_vars:
                    vvar = form_vars[var]
                    if isinstance(vvar, Field):
                        # modified_by/modified_on
                        continue
                    if var == "pe_id":
                        pe_id = vvar
                    rvar = record.get(var, "NOT_PRESENT")
                    if rvar != "NOT_PRESENT" and vvar != rvar:
                        f = table[var]
                        type_ = f.type
                        if type_ == "integer" or \
                           type_.startswith("reference"):
                            if vvar:
                                vvar = int(vvar)
                            if vvar == rvar:
                                continue
                        represent = table[var].represent
                        if represent:
                            if hasattr(represent, "show_link"):
                                represent.show_link = False
                        else:
                            represent = lambda o: o
                        if rvar:
                            changed[var] = "%s changed from %s to %s" % \
                                (f.label, represent(rvar), represent(vvar))
                        else:
                            changed[var] = "%s changed to %s" % \
                                (f.label, represent(vvar))

                if changed:
                    table = s3db.event_incident_log
                    text = []
                    for var in changed:
                        text.append(changed[var])
                    text = "\n".join(text)
                    table.insert(incident_id = incident_id,
                                 name = "Task Updated",
                                 comments = text,
                                 )

        if pe_id:
            # Notify Assignee
            # @ToDo: i18n
            message = "You have been assigned a Task: %s%s" % \
                        (settings.get_base_public_url(),
                         URL(c="event", f= "incident",
                             args = [incident_id, "task", task_id]),
                             )
            from s3db.pr import pr_instance_type
            instance_type = pr_instance_type(pe_id)
            if instance_type == "org_organisation":
                # Notify the Duty Number for the Organisation, not everyone in the Organisation!
                otable = s3db.org_organisation
                ottable = s3db.org_organisation_tag
                query = (otable.pe_id == pe_id) & \
                        (ottable.organisation_id == otable.id) & \
                        (ottable.tag == "duty")
                duty = db(query).select(ottable.value,
                                        limitby = (0, 1),
                                        ).first()
                if duty:
                    current.msg.send_sms_via_api(duty.value,
                                                 message,
                                                 )
            else:
                task_notification = settings.get_event_task_notification()
                if task_notification:
                    current.msg.send_by_pe_id(pe_id,
                                              subject = "%s: Task assigned to you" % settings.get_system_name_short(),
                                              message = message,
                                              contact_method = task_notification,
                                              )

    # -------------------------------------------------------------------------
    def customise_project_task_resource(r, tablename):

        s3db = current.s3db

        f = s3db.project_task.source
        f.readable = f.writable = False

        s3db.configure(tablename,
                       # No need to see time log: KISS
                       crud_form = None,
                       # NB We deliberatly over-ride the default one
                       create_onaccept = project_task_onaccept,
                       # In event_ActionPlan()
                       #list_fields = ["priority",
                       #               "name",
                       #               "pe_id",
                       #               "status_id",
                       #               "date_due",
                       #               ],
                       update_onaccept = lambda form:
                                            project_task_onaccept(form, create=False),
                       )

    settings.customise_project_task_resource = customise_project_task_resource

# END =========================================================================
