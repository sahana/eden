# -*- coding: utf-8 -*-

"""
    Event Module - Controllers

    http://eden.sahanafoundation.org/wiki/BluePrintScenario
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def create():
    """ Redirect to event/create """
    redirect(URL(f="event", args="create"))

# -----------------------------------------------------------------------------
def event():
    """
        RESTful CRUD controller
    """

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component:
                if r.component.name == "req":
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        # inc list_create (list_fields over-rides)
                        s3db.req_create_form_mods()

            elif r.method != "update" and r.method != "read":
                # Create or ListCreate
                r.table.closed.writable = r.table.closed.readable = False

            elif r.method == "update":
                # Can't change details after event activation
                r.table.exercise.writable = False
                r.table.exercise.comment = None
                r.table.zero_hour.writable = False

        return True
    s3.prep = prep

    output = s3_rest_controller(rheader=event_rheader)
    return output

# -----------------------------------------------------------------------------
def incident_type():
    """
        RESTful CRUD controller
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def incident():
    """
        RESTful CRUD controller
    """

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component:
                if r.component.name == "config":
                    s3db.configure("gis_config",
                                   deletable=False)
                    s3.crud.submit_button = T("Update")
                elif r.component.name == "human_resource":
                    s3db.configure("event_human_resource",
                                   list_fields=["human_resource_id"])
                    s3.crud.submit_button = T("Assign")
                    s3mgr.LABEL["DELETE"] = T("Remove")
                elif r.component.name == "asset":
                    s3db.configure("event_asset",
                                   list_fields=["asset_id"])
                    s3.crud.submit_button = T("Assign")
                    s3mgr.LABEL["DELETE"] = T("Remove")
                else:
                    s3.crud.submit_button = T("Assign")
                    s3mgr.LABEL["DELETE"] = T("Remove")

            elif r.method != "update" and r.method != "read":
                # Create or ListCreate
                r.table.closed.writable = r.table.closed.readable = False

            elif r.method == "update":
                # Can't change details after event activation
                r.table.scenario_id.writable = False
                r.table.exercise.writable = False
                r.table.exercise.comment = None
                r.table.zero_hour.writable = False

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):

        if r.interactive:
            if r.component:
                if r.component.name == "human_resource":
                    update_url = URL(c="hrm", f="human_resource", args=["[id]"])
                    s3.crud.action_buttons(r, update_url=update_url)
                    if "msg" in settings.modules:
                        s3.crud.action_button(url = URL(f="compose",
                                                        vars = {"hrm_id": "[id]"}),
                                              _class = "action-btn",
                                              label = str(T("Send Notification")))
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=event_rheader)
    return output

# -----------------------------------------------------------------------------
def event_rheader(r):
    """ Resource headers for component views """

    rheader = None

    if r.representation == "html":

        if r.name == "event":
            # Event Controller
            tabs = [(T("Event Details"), None)]
            if settings.has_module("req"):
                tabs.append((T("Requests"), "req"))
            rheader_tabs = s3_rheader_tabs(r, tabs)

            event = r.record
            if event:
                if event.exercise:
                    exercise = TH(T("EXERCISE"))
                else:
                    exercise = TH()
                if event.closed:
                    closed = TH(T("CLOSED"))
                else:
                    closed = TH()
                rheader = DIV(TABLE(TR(exercise),
                                    TR(TH("%s: " % T("Name")),
                                       event.name),
                                       TH("%s: " % T("Comments")),
                                       event.comments,
                                    TR(TH("%s: " % T("Zero Hour")),
                                       event.zero_hour),
                                    TR(closed),
                                    ), rheader_tabs)

        if r.name == "incident":
            # Incident Controller
            tabs = [(T("Incident Details"), None)]
            if deployment_settings.has_module("project"):
                tabs.append((T("Tasks"), "task"))
            if deployment_settings.has_module("hrm"):
                tabs.append((T("Human Resources"), "human_resource"))
            if deployment_settings.has_module("asset"):
                tabs.append((T("Assets"), "asset"))
            tabs.append((T("Facilities"), "site"))
            tabs.append((T("Map Configuration"), "config"))
            rheader_tabs = s3_rheader_tabs(r, tabs)

            record = r.record
            if record:
                if record.exercise:
                    exercise = TH(T("EXERCISE"))
                else:
                    exercise = TH()
                if record.closed:
                    closed = TH(T("CLOSED"))
                else:
                    closed = TH()
                rheader = DIV(TABLE(TR(exercise),
                                    TR(TH("%s: " % T("Name")),
                                       record.name),
                                       TH("%s: " % T("Comments")),
                                       record.comments,
                                    TR(TH("%s: " % T("Zero Hour")),
                                       record.zero_hour),
                                    TR(closed),
                                    ), rheader_tabs)

    return rheader

# -----------------------------------------------------------------------------
def person():
    """ Person controller for AddPersonWidget """

    def prep(r):
        if r.representation != "s3json":
            # Do not serve other representations here
            return False
        else:
            s3mgr.show_ids = True
        return True
    s3.prep = prep

    return s3_rest_controller("pr", "person")

# -----------------------------------------------------------------------------
def compose():
    """ Send message to people/teams """

    vars = request.vars

    if "hrm_id" in vars:
        id = vars.hrm_id
        fieldname = "hrm_id"
        table = s3db.pr_person
        htable = s3db.hrm_human_resource
        pe_id_query = (htable.id == id) & \
                      (htable.person_id == table.id)
        title = T("Send a message to this person")
    else:
        session.error = T("Record not found")
        redirect(URL(f="index"))

    pe = db(pe_id_query).select(table.pe_id,
                                limitby=(0, 1)).first()
    if not pe:
        session.error = T("Record not found")
        redirect(URL(f="index"))

    pe_id = pe.pe_id

    # Get the individual's communications options & preference
    table = s3db.pr_contact
    contact = db(table.pe_id == pe_id).select(table.contact_method,
                                              orderby="priority",
                                              limitby=(0, 1)).first()
    if contact:
        s3db.msg_outbox.pr_message_method.default = contact.contact_method
    else:
        session.error = T("No contact method found")
        redirect(URL(f="index"))

    # URL to redirect to after message sent
    url = URL(c=module,
              f="compose",
              vars={fieldname: id})

    # Create the form
    output = msg.compose(recipient = pe_id,
                         url = url)

    output["title"] = title
    response.view = "msg/compose.html"
    return output

# END =========================================================================
