# -*- coding: utf-8 -*-

#from collections import OrderedDict

#from gluon import current, URL
#from gluon.storage import Storage

def config(settings):
    """
        Settings for Seychelles's extensions to the core SaFiRe template.
    """

    #T = current.T

    #settings.security.policy = 6 # Controller, Function, Table ACLs and Entity Realm

    # Send Task Notifications by SMS, not Email
    settings.event.task_notification = "SMS"

    # -------------------------------------------------------------------------
    # Events
    # - customise to use Severity & Level
    # -------------------------------------------------------------------------
    def event_rheader(r):
        rheader = None

        record = r.record
        if record and r.representation == "html":

            from gluon import A, DIV, TABLE, TR, TH
            from s3 import s3_rheader_tabs

            name = r.name
            if name == "incident":
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
                        dropdown = SELECT(_id="scenarios")
                        dropdown["_data-incident_id"] = record_id
                        dappend = dropdown.append
                        dappend(OPTION(T("Select Scenario")))
                        for s in scenarios:
                            dappend(OPTION(s.name, _value=s.id))
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

                if record.event_id or r.method == "event" or not editable:
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

        return rheader

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
                r.resource.configure(create_next = URL(args=["[id]", "assign"]),
                                     crud_form = crud_form,
                                     )

            return True
        s3.prep = custom_prep

        # No sidebar menu
        current.menu.options = None
        req_args = current.request.args
        if len(req_args) > 1 and req_args[1] == "assign":
            if settings.get_incident_label(): # == "Ticket"
                label = T("New Ticket")
            else:
                label = T("New Incident")
            attr["rheader"] = A(label,
                                _class = "action-btn",
                                _href = URL(c="event", f="incident",
                                            args = ["create"],
                                            vars = {"incident_report_id": req_args[0]},
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
                                                                      limitby = (0, 1)
                                                                      ).first().name
            if incident_type == "Chemical Hazard":
                itable = s3db.event_incident
                db(itable.id == incident_id).update(level = 3)
                current.response.warning = T("Chemical Hazard Incident so Level raised to 3")

        # Alert Lead Agency
        organisation_id = form_vars_get("organisation_id")
        if organisation_id:
            otable = s3db.org_organisation_tag
            query = (otable.organisation_id == organisation_id) & \
                    (otable.tag == "duty")
            duty = db(query).select(otable.value,
                                    limitby = (0, 1)
                                    ).first()
            if duty:
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
        f = table.severity
        f.readable = f.writable = True
        f = table.level
        f.readable = f.writable = True
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

# END =========================================================================
