# -*- coding: utf-8 -*-

"""
    Event Module - Controllers

    http://eden.sahanafoundation.org/wiki/BluePrintScenario
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def create():
    """ Redirect to event/create """
    redirect(URL(f="event", args="create"))

# =============================================================================
# Events
# =============================================================================
def event():

    """
        RESTful CRUD controller

        An Event is an instantiation of a template
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
                elif r.component.name == "config":
                    s3mgr.configure("gis_config",
                                    deletable=False)
                    s3.crud.submit_button = T("Update")
                elif r.component.name == "human_resource":
                    s3mgr.configure("event_human_resource",
                                    list_fields=["human_resource_id"])
                    s3.crud.submit_button = T("Assign")
                elif r.component.name == "asset":
                    s3mgr.configure("event_asset",
                                    list_fields=["asset_id"])
                    s3.crud.submit_button = T("Assign")
                else:
                    s3.crud.submit_button = T("Assign")

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
    response.s3.prep = prep

    # Post-process
    def postp(r, output):

        if r.interactive:
            if r.component:
                if r.component.name == "asset":
                    s3mgr.LABEL["DELETE"]=T("Remove")

                elif r.component.name == "human_resource":
                    s3mgr.LABEL["DELETE"]=T("Remove")
                    if "msg" in deployment_settings.modules:
                        update_url = URL(c="hrm", f="human_resource", args=["[id]"])
                        s3mgr.crud.action_buttons(r, update_url=update_url)
                        s3mgr.crud.action_button(url = URL(f="compose",
                                                           vars = {"hrm_id": "[id]"}),
                                                 _class = "action-btn",
                                                 label = str(T("Send Notification")))

                elif r.component.name == "site":
                    s3mgr.LABEL["DELETE"]=T("Remove")

                elif r.component.name == "task":
                    s3mgr.LABEL["DELETE"]=T("Remove")

                elif r.component.name == "activity":
                    s3mgr.LABEL["DELETE"]=T("Remove")

        return output
    response.s3.postp = postp

    output = s3_rest_controller("event", resourcename,
                                rheader=event_rheader)
    return output

# -----------------------------------------------------------------------------
def event_rheader(r):
    """ Resource headers for component views """

    rheader = None

    if r.representation == "html":

        if r.name == "event":
            # Event Controller
            tabs = [(T("Event Details"), None)]
            if deployment_settings.has_module("project"):
                tabs.append((T("Tasks"), "task"))
            if deployment_settings.has_module("hrm"):
                tabs.append((T("Human Resources"), "human_resource"))
            if deployment_settings.has_module("asset"):
                tabs.append((T("Assets"), "asset"))
            tabs.append((T("Facilities"), "site"))
            if deployment_settings.has_module("req"):
                tabs.append((T("Requests"), "req"))
            #if deployment_settings.has_module("project"):
            #    tabs.append((T("Activities"), "activity"))
            tabs.append((T("Map Configuration"), "config"))
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

    return rheader

# =============================================================================
def person():
    """ Person controller for AddPersonWidget """

    def prep(r):
        if r.representation != "s3json":
            # Do not serve other representations here
            return False
        else:
            s3mgr.show_ids = True
        return True
    response.s3.prep = prep

    return s3_rest_controller("pr", "person")

# =============================================================================
# Messaging
# =============================================================================

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

# =============================================================================
# Components - no longer needed with new link-table support?
# =============================================================================
def asset():
    """ RESTful CRUD controller """

    # Load the Models
    s3mgr.load("event_event")

    # Parse the Request
    r = s3mgr.parse_request()

    link = request.vars.get("link", None)

    # Pre-Process
    if r.id and link:
        # Go back to the asset list of the scenario/event after removing the asset
        s3mgr.configure(r.tablename,
                        delete_next=URL(link,
                                        args=[r.record["%s_id" % link],
                                              "asset"]))

    edit_btn = None
    if link:
        if r.method in ("update", None) and r.id:
            # Store the edit & delete buttons
            edit_btn = A(T("Edit"),
                         _href=r.url(method="update",
                                     representation="html"),
                         _target="_blank")
            delete_btn=A(T("Remove this asset from this event"),
                         _href=r.url(method="delete",
                                     representation="html"),
                         _class="delete-btn")
            # Switch to the other request
            asset_id = r.record.asset_id
            r = s3base.S3Request(s3mgr,
                                 c="asset", f="asset",
                                 args=[str(asset_id)],
                                 extension=auth.permission.format)
    # Execute the request
    output = r()

    # Post-Process
    s3_action_buttons(r)

    # Restore the edit & delete buttons with the correct ID
    if r.representation == "plain" and edit_btn:
        output.update(edit_btn=edit_btn)
    elif r.interactive and "delete_btn" in output:
        output.update(delete_btn=delete_btn)

    return output

# -----------------------------------------------------------------------------
def human_resource():
    """ RESTful CRUD controller """

    # Load the Models
    s3mgr.load("event_event")

    # Parse the Request
    r = s3mgr.parse_request()

    link = request.vars.get("link", None)

    # Pre-Process
    if r.id and link:
        # Go back to the human_resource list of the scenario/event after removing the human_resource
        s3mgr.configure(r.tablename,
                        delete_next=URL(link,
                                        args=[r.record["%s_id" % link],
                                              "human_resource"]))

    edit_btn = None
    if link:
        if r.method in ("update", None) and r.id:
            # Store the edit & delete buttons
            edit_btn = A(T("Edit"),
                         _href=r.url(method="update",
                                     representation="html"),
                         _target="_blank")
            delete_btn=A(T("Remove this human resource from this event"),
                         _href=r.url(method="delete",
                                     representation="html"),
                         _class="delete-btn")
            # Switch to the other request
            hrm_id = r.record.human_resource_id
            r = s3base.S3Request(s3mgr,
                                 c="hrm", f="human_resource",
                                 args=[str(hrm_id)],
                                 extension=auth.permission.format)
    # Execute the request
    output = r()

    # Post-Process
    s3_action_buttons(r)

    # Restore the edit & delete buttons with the correct ID
    if r.representation == "plain" and edit_btn:
        output.update(edit_btn=edit_btn)
    elif r.interactive and "delete_btn" in output:
        output.update(delete_btn=delete_btn)

    return output

# -----------------------------------------------------------------------------
def site():
    """ RESTful CRUD controller """

    # Load the Models
    s3mgr.load("event_event")

    # Parse the Request
    r = s3mgr.parse_request()

    link = request.vars.get("link", None)

    # Pre-Process
    if r.id and link:
        # Go back to the facility list of the scenario/event after removing the facility
        s3mgr.configure(r.tablename,
                        delete_next=URL(link,
                                        args=[r.record["%s_id" % link],
                                              "site"]))

    edit_btn = None
    if link:
        if r.method in ("update", None) and r.id:
            # Store the edit & delete buttons
            edit_btn = A(T("Edit"),
                         _href=r.url(method="update",
                                     representation="html"),
                         _target="_blank")
            delete_btn=A(T("Remove this facility from this event"),
                         _href=r.url(method="delete",
                                     representation="html"),
                         _class="delete-btn")
            # Switch to the other request
            site_id = r.record.site_id
            r = s3base.S3Request(s3mgr,
                                 c="org", f="site",
                                 args=[str(site_id)],
                                 extension=auth.permission.format)
    # Execute the request
    output = r()

    # Post-Process
    s3_action_buttons(r)

    # Restore the edit & delete buttons with the correct ID
    if r.representation == "plain" and edit_btn:
        output.update(edit_btn=edit_btn)
    elif r.interactive and "delete_btn" in output:
        output.update(delete_btn=delete_btn)

    return output

# -----------------------------------------------------------------------------
def task():
    """ RESTful CRUD controller """

    # Load the Models
    s3mgr.load("event_event")

    # Parse the Request
    r = s3mgr.parse_request()

    link = request.vars.get("link", None)

    # Pre-Process
    if r.id and link:
        # Go back to the task list of the scenario/event after removing the task
        s3mgr.configure(r.tablename,
                        delete_next=URL(link,
                                        args=[r.record["%s_id" % link],
                                              "task"]))

    edit_btn = None
    if link:
        if r.method in ("update", None) and r.id:
            # Store the edit & delete buttons
            edit_btn = A(T("Edit"),
                         _href=r.url(method="update",
                                     representation="html"),
                         _target="_blank")
            delete_btn=A(T("Remove this task from this event"),
                         _href=r.url(method="delete",
                                     representation="html"),
                         _class="delete-btn")
            # Switch to the other request
            task_id = r.record.task_id
            r = s3base.S3Request(s3mgr,
                                 c="project", f="task",
                                 args=[str(task_id)],
                                 extension=auth.permission.format)
    # Execute the request
    output = r()

    # Post-Process
    s3_action_buttons(r)

    # Restore the edit & delete buttons with the correct ID
    if r.representation == "plain" and edit_btn:
        output.update(edit_btn=edit_btn)
    elif r.interactive and "delete_btn" in output:
        output.update(delete_btn=delete_btn)

    return output

# END =========================================================================

