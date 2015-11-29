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

    return s3db.cms_index(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the list of Events
    s3_redirect_default(URL(f="event"))

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
                table = r.table
                table.exercise.writable = False
                table.exercise.comment = None
                table.start_date.writable = False

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.event_rheader)

# -----------------------------------------------------------------------------
def event_type():
    """
        RESTful CRUD controller
    """

    return s3_rest_controller()

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
        if r.interactive or r.representation == "aadata":
            if r.component:
                if r.component.alias == "assign":
                    if not r.method:
                        r.method = "assign"
                    if r.method == "assign":
                        r.custom_action = s3db.hrm_AssignMethod(component="assign")
                if r.component_name == "config":
                    s3db.configure("gis_config",
                                   deletable = False,
                                   )
                    s3.crud.submit_button = T("Update")
                elif r.component_name in ("asset", "human_resource", "organisation", "site"):
                    s3.crud.submit_button = T("Assign")
                    s3.crud_labels["DELETE"] = T("Remove")
                #else:
                #    s3.crud.submit_button = T("Assign")
                #    s3.crud_labels["DELETE"] = T("Remove")

            elif r.method != "update" and r.method != "read":
                # Create or ListCreate
                r.table.closed.writable = r.table.closed.readable = False

            elif r.method == "update":
                # Can't change details after event activation
                table = r.table
                table.scenario_id.writable = False
                table.exercise.writable = False
                table.exercise.comment = None
                table.zero_hour.writable = False

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):

        if r.interactive:
            if r.component:
                if r.component.name == "human_resource":
                    #update_url = URL(c="hrm", f="human_resource", args=["[id]"])
                    #s3_action_buttons(r, update_url=update_url)
                    s3_action_buttons(r)
                    if "msg" in settings.modules:
                        s3base.S3CRUD.action_button(url = URL(f="compose",
                                                              vars = {"hrm_id": "[id]"}),
                                                    _class = "action-btn send",
                                                    label = str(T("Send Notification")))
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader = s3db.event_rheader)
    return output

# -----------------------------------------------------------------------------
def incident_report():
    """
        RESTful CRUD controller
    """

    def prep(r):
        if r.http == "GET":
            if r.method in ("create", "create.popup"):
                # Lat/Lon from Feature?
                # @ToDo: S3PoIWidget() instead to pickup the passed Lat/Lon/WKT
                field = r.table.location_id
                lat = get_vars.get("lat", None)
                if lat is not None:
                    lon = get_vars.get("lon", None)
                    if lon is not None:
                        form_vars = Storage(lat = float(lat),
                                            lon = float(lon),
                                            )
                        form = Storage(vars=form_vars)
                        s3db.gis_location_onvalidation(form)
                        id = s3db.gis_location.insert(**form_vars)
                        field.default = id
                # WKT from Feature?
                wkt = get_vars.get("wkt", None)
                if wkt is not None:
                    form_vars = Storage(wkt = wkt,
                                        )
                    form = Storage(vars = form_vars)
                    s3db.gis_location_onvalidation(form)
                    id = s3db.gis_location.insert(**form_vars)
                    field.default = id

        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def resource():
    """
        RESTful CRUD controller
    """

    def prep(r):
        if r.interactive:
            if r.method in ("create", "update"):
                table = r.table
                if r.method == "create":
                    # Enable Location field
                    field = table.location_id
                    field.readable = field.writable = True

                get_vars = r.get_vars
                # Context from a Profile page?"
                #location_id = get_vars.get("(location)")
                #if location_id:
                #    field = table.location_id
                #    field.default = location_id
                #    field.readable = field.writable = False
                incident_id = get_vars.get("~.(incident)")
                if incident_id:
                    field = table.incident_id
                    field.default = incident_id
                    field.readable = field.writable = False
        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def person():
    """ Person controller for AddPersonWidget """

    def prep(r):
        if r.representation != "s3json":
            # Do not serve other representations here
            return False
        else:
            current.xml.show_ids = True
        return True
    s3.prep = prep

    return s3_rest_controller("pr", "person")

# -----------------------------------------------------------------------------
def group():
    """
        Module-specific controller for Teams

        @note: currently for development/testing/demo purposes only (WIP),
               may be replaced by hrm_group controller in future
    """

    def prep(r):
        # Make the team status visible in list/read views
        if r.interactive or r.representation == "aadata":
            resource = r.resource
            list_fields = ["name",
                           "description",
                           "team_status_team.status_id",
                           "comments",
                           ]
            resource.configure(list_fields = list_fields)
        if r.interactive:
            from s3 import S3SQLCustomForm, S3SQLInlineComponent
            crud_fields = ["name",
                           "description",
                           S3SQLInlineComponent("team_status_team",
                                                fields = [("", "status_id")],
                                                label = T("Status"),
                                                multiple = False,
                                                ),
                           "comments",
                           ]
            crud_form = S3SQLCustomForm(*crud_fields)
            r.resource.configure(crud_form = crud_form)
        return True
    s3.prep = prep

    return s3_rest_controller("pr", "group")

# -----------------------------------------------------------------------------
def team():
    """ Controller for event_team option lookups (popups) """

    # /options.s3json only
    s3.prep = lambda r: r.method == "options" and \
                        r.representation == "s3json"

    return s3_rest_controller("event", "team")

# -----------------------------------------------------------------------------
def team_status():
    """ Team status taxonomy controller (for Admin and lookups) """

    return s3_rest_controller()

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
        s3db.msg_outbox.contact_method.default = contact.contact_method
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
