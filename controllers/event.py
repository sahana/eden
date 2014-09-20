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
    redirect(URL(f="event"))

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

    def postp(r, output):
        if r.interactive:
            if not r.component:
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('event_event_start_date','event_event_end_date')''')
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader = s3db.event_rheader)
    return output

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
        if r.interactive:
            if r.component:
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
                        s3base.S3CRUD.action_button(url = URL(args = ["compose"],
                                                              vars = {"human_resource.id": "[id]"}),
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
                #location_id = get_vars.get("(location)", None)
                #if location_id:
                #    field = table.location_id
                #    field.default = location_id
                #    field.readable = field.writable = False
                incident_id = get_vars.get("~.(incident)", None)
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

# END =========================================================================
