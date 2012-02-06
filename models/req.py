# -*- coding: utf-8 -*-

"""
    Request Management

    A module to record requests & commitments for:
     - inventory items
     - people (actually request skills, but commit people)
     - assets
     - other

     @ToDo: Link to Tasks via link table (optional way of working)
"""


req_item_inv_item_btn = dict(url = URL(c = "req",
                                           f = "req_item_inv_item",
                                           args = ["[id]"]
                                        ),
                                 _class = "action-btn",
                                 label = str(T("Find")), # Change to Fulfil? Match?
                                )

# -----------------------------------------------------------------------------
# Defined in the Model for use from Multiple Controllers for unified menus
#
def req_controller():
    """
        Request Controller
    """

    req_table = s3db.req_req

    # Set the req_item site_id (Requested From)
    # @ToDo: What does this do? Where does it get called from?
    if "req_item_id" in request.vars and "inv_item_id" in request.vars:
        site_id = s3db.inv_inv_item[request.vars.inv_item_id].site_id
        s3db.req_req_item[request.vars.req_item_id] = dict(site_id = site_id)

    default_type = request.vars.default_type
    if default_type:
        type_field = req_table.type
        type_field.default = int(default_type)
        type_field.writable = False

    def prep(r):

        # Remove type from list_fields
        list_fields = s3mgr.model.get_config("req_req",
                                             "list_fields")
        try:
            list_fields.remove("type")
        except:
             # It has already been removed.
             # This can happen if the req controller is called
             # for a second time, such as when printing reports
            pass
        s3mgr.configure(tablename, list_fields=list_fields)

        if r.interactive:
            # Set Fields and Labels depending on type
            type = ( r.record and r.record.type ) or \
                   ( request.vars and request.vars.default_type )
            if type:
                type = int(type)
                req_table.type.default = int(type)

                # This prevents the type from being edited AFTER it is set
                req_table.type.readable = False
                req_table.type.writable = False

                crud_strings = deployment_settings.get_req_req_crud_strings(type)
                if crud_strings:
                    s3.crud_strings["req_req"] = crud_strings

                # Filter the query based on type
                if response.s3.filter:
                    response.s3.filter = response.s3.filter & \
                                         (s3db.req_req.type == type)
                else:
                    response.s3.filter = (s3db.req_req.type == type)

            # @ToDo: apply these changes via JS for the create form where type is edittable
            if type == 1: # Item
                req_table.date_recv.readable = True
                req_table.date_recv.writable = True
                req_table.date_recv.readable = True
                req_table.date_recv.writable = True

                req_table.purpose.label = T("What the Items will be used for")
                req_table.site_id.label =T("Deliver To")
                req_table.request_for_id.label = T("Deliver To")
                req_table.recv_by_id.label = T("Delivered To")

            if type == 3: # Person
                req_table.date_required_until.readable = True
                req_table.date_required_until.writable = True

                req_table.purpose.label = T("Task Details")
                req_table.site_id.label =  T("Report To")
                req_table.request_for_id.label = T("Report To")
                req_table.recv_by_id.label = T("Reported To")

            if r.method != "update" and r.method != "read":
                if not r.component:
                    # Hide fields which don't make sense in a Create form
                    # - includes one embedded in list_create
                    # - list_fields over-rides, so still visible within list itself
                    s3db.req_create_form_mods()

                    # Get the default Facility for this user
                    # @ToDo: Use site_id in User Profile (like current organisation_id)
                    if deployment_settings.has_module("hrm"):
                        hrtable = s3db.hrm_human_resource
                        query = (hrtable.person_id == s3_logged_in_person())
                        site = db(query).select(hrtable.site_id,
                                                limitby=(0, 1)).first()
                        if site:
                            r.table.site_id.default = site.site_id

                elif r.component.name == "document":
                    s3.crud.submit_button = T("Add")
                    table = r.component.table
                    # @ToDo: Fix for Link Table
                    #table.date.default = r.record.date
                    #if r.record.site_id:
                    #    stable = db.org_site
                    #    query = (stable.id == r.record.site_id)
                    #    site = db(query).select(stable.location_id,
                    #                            stable.organisation_id,
                    #                            limitby=(0, 1)).first()
                    #    if site:
                    #        table.location_id.default = site.location_id
                    #        table.organisation_id.default = site.organisation_id

                elif r.component.name == "req_item":
                    table = r.component.table
                    table.site_id.writable = table.site_id.readable = False
                    s3db.req_hide_quantities(table)

                elif r.component.name == "req_skill":
                    s3db.req_hide_quantities(r.component.table)

        if r.component and r.component.name == "commit":
            table = r.component.table
            # Allow commitments to be added when doing so as a component
            s3mgr.configure(table,
                            listadd = True)

            type = r.record.type
            if type == 1: # Items
                # Limit site_id to facilities the user has permissions for
                auth.permission.permitted_facilities(table=r.table,
                                                     error_msg=T("You do not have permission for any facility to make a commitment."))
                if r.interactive:
                    # Redirect to the Items tab after creation
                    s3mgr.configure(table,
                                    create_next = URL(c="req", f="commit",
                                                      args=["[id]", "commit_item"]),
                                    update_next = URL(c="req", f="commit",
                                                      args=["[id]", "commit_item"]))
            else:
                # Non-Item commits can have an Organisation
                # Check if user is affiliated to an Organisation
                if is_affiliated():
                    # Limit organisation_id to organisations the user has permissions for
                    auth.permission.permitted_organisations(table=r.table,
                                                            redirect_on_error=False)
                    table.organisation_id.readable = True
                    table.organisation_id.writable = True
                else:
                    # Unaffiliated people can't commit on behalf of others
                    r.component.table.committer_id.writable = False
                    r.component.table.committer_id.comment = None

                # Non-Item commits shouldn't have a From Inventory
                # @ToDo: Assets do?
                table.site_id.readable = False
                table.site_id.writable = False
                if r.interactive and r.record.type == 3: # People
                    # Redirect to the Persons tab after creation
                    s3mgr.configure(table,
                                    create_next = URL(c="req", f="commit",
                                                      args=["[id]", "commit_person"]),
                                    update_next = URL(c="req", f="commit",
                                                      args=["[id]", "commit_person"]))
        else:
            # Limit site_id to facilities the user has permissions for
            # @ToDo: Non-Item requests shouldn't be bound to a Facility?
            auth.permission.permitted_facilities(table=r.table,
                                                 error_msg=T("You do not have permission for any facility to make a request."))

        return True
    response.s3.prep = prep

    # Post-process
    def postp(r, output):

        if r.interactive:
            s3_action_buttons(r)
            if not r.component:
                if deployment_settings.get_req_use_commit():
                    # This is appropriate to all
                    response.s3.actions.append(
                        dict(url = URL(c = "req",
                                       f = "req",
                                       args = ["[id]", "commit", "create"]),
                             _class = "action-btn",
                             label = str(T("Commit"))
                            )
                        )
                # This is only appropriate for item requests
                query = (r.table.type == 1)
                rows = db(query).select(r.table.id)
                restrict = [str(row.id) for row in rows]
                response.s3.actions.append(
                    dict(url = URL(c = "req",
                                   f = "req",
                                   args = ["[id]", "req_item"]),
                         _class = "action-btn",
                         label = str(T("View Items")),
                         restrict = restrict
                        )
                    )
            elif r.component.name == "req_item":
                response.s3.actions.append(req_item_inv_item_btn)
            elif r.component.name == "req_skill":
                pass
            else:
                # We don't yet have other components
                pass

        return output
    response.s3.postp = postp

    output = s3_rest_controller("req", "req",
                                rheader=eden.req.req_rheader)

    return output

# ---------------------------------------------------------------------
def req_skill_controller():
    """
        Request Skills Controller
    """

    tablename = "req_req_skill"
    table = s3db[tablename]

    s3mgr.configure(tablename,
                    insertable=False)

    def prep(r):
        if r.interactive:
            if r.method != "update" and r.method != "read":
                # Hide fields which don't make sense in a Create form
                # - includes one embedded in list_create
                # - list_fields over-rides, so still visible within list itself
                s3db.req_hide_quantities(r.table)

        return True
    response.s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            response.s3.actions = [
                dict(url = URL(c = "req",
                               f = "req",
                               args = ["req_skill", "[id]"]),
                     _class = "action-btn",
                     label = str(READ)
                    )
                ]

        return output
    response.s3.postp = postp

    output = s3_rest_controller("req", "req_skill")

    return output

# ---------------------------------------------------------------------
def req_match():
    """
        Function to be called from controller functions to display all
        requests as a tab for a site.
        @ToDo: Filter out requests from this site
    """

    output = dict()

    if "viewing" not in request.vars:
        return output
    else:
        viewing = request.vars.viewing
    if "." in viewing:
        tablename, id = viewing.split(".", 1)
    else:
        return output
    site_id = s3db[tablename][id].site_id
    response.s3.actions = [dict(url = URL(c = "req",
                                          f = "req",
                                          args = ["[id]","check"],
                                          vars = {"site_id": site_id}
                                         ),
                                _class = "action-btn",
                                label = str(T("Check")),
                                ),
                           dict(url = URL(c = "req",
                                          f = "commit_req",
                                          args = ["[id]"],
                                          vars = {"site_id": site_id}
                                         ),
                                _class = "action-btn",
                                label = str(T("Commit")),
                                ),
                           dict(url = URL(c = "req",
                                          f = "send_req",
                                          args = ["[id]"],
                                          vars = {"site_id": site_id}
                                         ),
                                _class = "action-btn",
                                label = str(T("Send")),
                                )
                           ]

    rheader_dict = dict(org_office = s3db.org_rheader)
    if deployment_settings.has_module("cr"):
        rheader_dict["cr_shelter"] = response.s3.shelter_rheader
    if deployment_settings.has_module("hms"):
        rheader_dict["hms_hospital"] = s3db.hms_hospital_rheader

    s3mgr.configure("req_req", insertable=False)
    output = s3_rest_controller("req", "req",
                                method = "list",
                                rheader = rheader_dict[tablename])

    if tablename == "org_office" and isinstance(output, dict):
        output["title"] = T("Warehouse Details")

    return output

# END =========================================================================