# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current, URL
from gluon.storage import Storage

def config(settings):
    """
        Settings for Urgences-Sante's extensions to the core SaFiRe template.
    """

    T = current.T

    settings.ui.menu_logo = "/%s/static/themes/Urgences-Sante/img/logo.png" % current.request.application

    settings.L10n.default_language = "fr"
    settings.L10n.translate_gis_location = True
    settings.L10n.name_alt_gis_location = True
    settings.L10n.translate_org_organisation = True

    # Users should not be allowed to register themselves
    settings.security.self_registration = False

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
                # Over-ride base SAFIRE template to add Notification Tab
                tabs = [(T("Incident Details"), None),
                        #(T("Tasks"), "task"),
                        #(T("Human Resources"), "human_resource"),
                        #(T("Equipment"), "asset"),
                        (T("Action Plan"), "plan"),
                        (T("Incident Reports"), "incident_report"),
                        (T("Logs"), "log"),
                        (T("Expenses"), "expense"),
                        (T("Situation Reports"), "sitrep"),
                        (T("Send Notification"), "dispatch"),
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
                        s3.js_global.append('''i18n.scenarioConfirm="%s"''' % T("Populate Incident with Tasks, Organizations, Positions and Equipment from the Scenario?"))
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
                # Currently unused copy from base SAFIRE template
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
                # Currently unused copy from base SAFIRE template
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
                # Currently unused copy from base SAFIRE template
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
                                    ), rheader_tabs)

        return rheader

    # -------------------------------------------------------------------------
    def customise_event_incident_controller(**attr):
        """
            Copy from base SAFIRE template to use custom rheader
        """

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

# END =========================================================================
