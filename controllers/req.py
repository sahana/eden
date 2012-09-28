# -*- coding: utf-8 -*-

"""
    Request Management
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """
        Application Home page
        - custom View
    """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def is_affiliated():
    """
        Check if User is affiliated to an Organisation
        @ToDo: Move this elsewhere
    """

    if not auth.is_logged_in():
        return False
    elif s3_has_role(ADMIN):
        return True
    else:
        table = auth.settings.table_user
        query = (table.id == auth.user.id)
        auth_user = db(query).select(table.organisation_id,
                                     limitby=(0, 1)).first()
        if auth_user and auth_user.organisation_id:
            return True
        else:
            return False

# =============================================================================
def create():
    """ Redirect to req/create """

    redirect(URL(f="req", args="create"))

# -----------------------------------------------------------------------------
def req():
    """ REST Controller """

    req_table = s3db.req_req

    # Set the req_item site_id (Requested From), called from action buttons on req/req_item_inv_item/x page
    if "req_item_id" in request.vars and "inv_item_id" in request.vars:
        inv_item = s3db.inv_inv_item[request.vars.inv_item_id]
        site_id = inv_item.site_id
        item_id = inv_item.item_id
        s3db.req_req_item[request.vars.req_item_id] = dict(site_id = site_id)
        response.confirmation = T("%(item)s requested from %(site)s" % {"item":s3db.supply_item_represent(item_id, show_link = False),
                                                                        "site":s3db.org_site_represent(site_id, show_link=False)
                                                                        })

    def prep(r):

        s3db.req_prep(r)

        # Remove type from list_fields
        list_fields = s3db.get_config("req_req", "list_fields")
        try:
            list_fields.remove("type")
        except:
             # It has already been removed.
             # This can happen if the req controller is called
             # for a second time, such as when printing reports
            pass
        s3db.configure("req_req", list_fields=list_fields)

        if r.interactive:
            # Set Fields and Labels depending on type
            type = ( r.record and r.record.type ) or \
                   ( request.vars and request.vars.type )
            if type:
                type = int(type)
                req_table.type.default = int(type)

                # This prevents the type from being edited AFTER it is set
                req_table.type.readable = False
                req_table.type.writable = False

                crud_strings = settings.get_req_req_crud_strings(type)
                if crud_strings:
                    s3.crud_strings["req_req"] = crud_strings

                # Filter the query based on type
                if s3.filter:
                    s3.filter = s3.filter & \
                                         (s3db.req_req.type == type)
                else:
                    s3.filter = (s3db.req_req.type == type)

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
                    s3db.configure(s3db.req_req,
                                   create_next = URL(c="req", f="req",
                                                     args=["[id]", "req_item"])
                                   )
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
            s3db.configure(table,
                            listadd = True)

            type = r.record.type
            if type == 1: # Items
                # Limit site_id to facilities the user has permissions for
                auth.permitted_facilities(table=r.table,
                                          error_msg=T("You do not have permission for any facility to make a commitment."))
                if r.interactive:
                    # Redirect to the Items tab after creation
                    s3db.configure(table,
                                   create_next = URL(c="req", f="commit",
                                                     args=["[id]", "commit_item"]),
                                   update_next = URL(c="req", f="commit",
                                                     args=["[id]", "commit_item"]))
            else:
                # Non-Item commits can have an Organisation
                # Check if user is affiliated to an Organisation
                if is_affiliated():
                    # Limit organisation_id to organisations the user has permissions for
                    auth.permitted_organisations(table=r.table,
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
                    s3db.configure(table,
                                   create_next = URL(c="req", f="commit",
                                                     args=["[id]", "commit_person"]),
                                   update_next = URL(c="req", f="commit",
                                                     args=["[id]", "commit_person"])
                                   )
        else:
            # Limit site_id to facilities the user has permissions for
            # @ToDo: Non-Item requests shouldn't be bound to a Facility?
            auth.permitted_facilities(table=r.table,
                                      error_msg=T("You do not have permission for any facility to make a request."))

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):

        if r.interactive:
            s3_action_buttons(r)
            if not r.component:
                if deployment_settings.get_req_use_commit():
                    # This is appropriate to all
                    s3.actions.append(
                        dict(url = URL(c="req", f="req",
                                       args=["[id]", "commit", "create"]),
                             _class = "action-btn",
                             label = str(T("Commit"))
                            )
                        )
                # This is only appropriate for item requests
                query = (r.table.type == 1)
                rows = db(query).select(r.table.id)
                restrict = [str(row.id) for row in rows]
                s3.actions.append(
                    dict(url = URL(c="req", f="req",
                                   args=["[id]", "req_item"]),
                         _class = "action-btn",
                         label = str(T("View Items")),
                         restrict = restrict
                        )
                    )
            elif r.component.name == "req_item":
                req_item_inv_item_btn = dict(url = URL(c = "req",
                                                       f = "req_item_inv_item",
                                                       args = ["[id]"]
                                                      ),
                                             _class = "action-btn",
                                             label = str(T("Request from Facility")),
                                             )
                s3.actions.append(req_item_inv_item_btn)
            elif r.component.name == "req_skill":
                pass
            else:
                # We don't yet have other components
                pass

        return output
    s3.postp = postp

    output = s3_rest_controller("req", "req",
                                rheader=eden.req.req_rheader)

    return output

# =============================================================================
def req_item():
    """ REST Controller """

    s3db.configure("req_req_item",
                   insertable=False)

    def prep(r):
        if r.interactive:
            if r.method != None and r.method != "update" and r.method != "read":
                # Hide fields which don't make sense in a Create form
                # - includes one embedded in list_create
                # - list_fields over-rides, so still visible within list itself
                s3db.req_hide_quantities(r.table)

        return True
    s3.prep = prep

    output = s3_rest_controller()

    req_item_inv_item_btn = dict(url = URL(c="req", f="req_item_inv_item",
                                           args=["[id]"]),
                                _class = "action-btn",
                                label = str(T("Request from Facility")),
                               )
    if s3.actions:
        s3.actions += [req_item_inv_item_btn]
    else:
        s3.actions = [req_item_inv_item_btn]

    return output

# -----------------------------------------------------------------------------
def req_item_packs():
    """
        Called by S3FilterFieldChange to provide the pack options for a
            particular Item
    """

    table = s3db.supply_item_pack
    ritable = s3db.req_req_item
    query = (ritable.id == request.args[0]) & \
            (ritable.item_id == table.item_id)

    response.headers["Content-Type"] = "application/json"
    return db(query).select(table.id,
                            table.name,
                            table.quantity).json()

# -----------------------------------------------------------------------------
def req_item_inv_item():
    """
        Shows the inventory items which match a requested item
        @ToDo: Make this page a component of req_item
    """

    req_item_id  = request.args[0]
    request.args = [] #
    ritable = s3db.req_req_item
    req_item = ritable[req_item_id]
    rtable = s3db.req_req
    req = rtable[req_item.req_id]

    output = {}

    output["title"] = T("Request Stock from Available Warehouse")
    output["req_btn"] = A(T("Return to Request"),
                          _href = URL(c="req", f="req",
                                      args=[req_item.req_id, "req_item"]),
                          _class = "action-btn"
                          )

    output["req_item"] = TABLE( TR(
                                    TH( "%s: " % T("Requested By") ),
                                    rtable.site_id.represent(req.site_id),
                                    TH( "%s: " % T("Item")),
                                    ritable.item_id.represent(req_item.item_id),
                                   ),
                                TR(
                                    TH( "%s: " % T("Requester") ),
                                    rtable.requester_id.represent(req.requester_id),
                                    TH( "%s: " % T("Quantity")),
                                    req_item.quantity,
                                   ),
                                TR(
                                    TH( "%s: " % T("Date Requested") ),
                                    rtable.date.represent(req.date),
                                    TH( T("Quantity Committed")),
                                    req_item.quantity_commit,
                                   ),
                                TR(
                                    TH( "%s: " % T("Date Required") ),
                                    rtable.date_required.represent(req.date_required),
                                    TH( "%s: " % T("Quantity in Transit")),
                                    req_item.quantity_transit,
                                   ),
                                TR(
                                    TH( "%s: " % T("Priority") ),
                                    rtable.priority.represent(req.priority),
                                    TH( "%s: " % T("Quantity Fulfilled")),
                                    req_item.quantity_fulfil,
                                   )
                               )

    s3.no_sspag = True # pagination won't work with 2 datatables on one page @todo: test

    itable = s3db.inv_inv_item
    # Get list of matching inventory items
    s3.filter = (itable.item_id == req_item.item_id)
    # Tweak CRUD String for this context
    s3.crud_strings["inv_inv_item"].msg_list_empty = T("No Inventories currently have this item in stock")

    inv_items = s3_rest_controller("inv", "inv_item")
    output["items"] = inv_items["items"]

    if current.deployment_settings.get_supply_use_alt_name():
        # Get list of alternative inventory items
        atable = s3db.supply_item_alt
        query = (atable.item_id == req_item.item_id ) & \
                (atable.deleted == False )
        alt_item_rows = db(query).select(atable.alt_item_id)
        alt_item_ids = [alt_item_row.alt_item_id for alt_item_row in alt_item_rows]

        if alt_item_ids:
            s3.filter = (itable.item_id.belongs(alt_item_ids))
            inv_items_alt = s3_rest_controller("inv", "inv_item")
            output["items_alt"] = inv_items_alt["items"]
        else:
            output["items_alt"] = T("No Inventories currently have suitable alternative items in stock")

    response.view = "req/req_item_inv_item.html"
    s3.actions = [dict(url = URL(c = request.controller,
                                          f = "req",
                                          args = [req_item.req_id, "req_item"],
                                          vars = dict(req_item_id = req_item_id,
                                                      inv_item_id = "[id]")
                                         ),
                                _class = "action-btn",
                                label = str(T("Request From")),
                                )]

    return output

# =============================================================================
def req_skill():
    """ REST Controller """

    tablename = "req_req_skill"
    table = s3db[tablename]

    s3db.configure(tablename,
                   insertable=False)

    def prep(r):
        if r.interactive:
            if r.method != "update" and r.method != "read":
                # Hide fields which don't make sense in a Create form
                # - includes one embedded in list_create
                # - list_fields over-rides, so still visible within list itself
                s3db.req_hide_quantities(r.table)

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            response.s3.actions = [
                dict(url = URL(c="req", f="req",
                               args=["req_skill", "[id]"]),
                     _class = "action-btn",
                     label = str(READ)
                    )
                ]
        return output
    s3.postp = postp

    output = s3_rest_controller("req", "req_skill")

    return output

# =============================================================================
def commit():
    """ REST Controller """

    # Check if user is affiliated to an Organisation
    if not is_affiliated():
        tablename = "req_commit_person"
        table = s3db[tablename]
        # Unaffiliated people can't commit on behalf of others
        table.person_id.writable = False
        # & can only make single-person commitments
        # (This should have happened in the main commitment)
        s3db.configure(tablename,
                       insertable=False)

    def prep(r):

        if r.interactive:
            # Commitments created through UI should be done via components
            # @ToDo: Block Direct Create attempts
            table = r.table
            #table.req_id.default = request.vars["req_id"]
            #table.req_id.writable = False

            if r.record:
                if r.record.type == 1: # Items
                    # Limit site_id to facilities the user has permissions for
                    auth.permitted_facilities(table=table,
                                              error_msg=T("You do not have permission for any facility to make a commitment.") )

                else:
                    # Non-Item commits can have an Organisation
                    # Limit organisation_id to organisations the user has permissions for
                    auth.permitted_organisations(table=r.table, redirect_on_error=False)
                    table.organisation_id.readable = True
                    table.organisation_id.writable = True
                    # Non-Item commits shouldn't have a From Inventory
                    # @ToDo: Assets do?
                    table.site_id.readable = False
                    table.site_id.writable = False

        if r.component:
            req_id = r.record.req_id
            if r.component.name == "commit_item":
                # Limit commit items to items from the request
                s3db.req_commit_item.req_item_id.requires = \
                    IS_ONE_OF(db,
                              "req_req_item.id",
                              s3db.req_item_represent,
                              orderby = "req_req_item.id",
                              filterby = "req_id",
                              filter_opts = [req_id],
                              sort=True
                              )
            elif r.component.name == "person":
                pass
                # Limit commit skills to skills from the request
                #db.req_commit_skill.req_skill_id.requires = \
                #    IS_ONE_OF(db,
                #              "req_req_skill.id",
                #              s3db.req_skill_represent,
                #              orderby = "req_req_skill.id",
                #              filterby = "req_id",
                #              filter_opts = [req_id],
                #              sort=True
                #              )
        return True

    s3.prep = prep

    rheader = commit_rheader

    output = s3_rest_controller(module, resourcename, rheader=rheader)

    return output

# -----------------------------------------------------------------------------
def commit_rheader(r):
    """ Resource Header for Commitments """

    if r.representation == "html":
        record = r.record
        if record and r.name == "commit":

            s3_date_represent = s3base.S3DateTime.date_represent

            tabs = [(T("Edit Details"), None)]
            type = record.type and int(record.type)

            table = r.table
            if type == 1:
                tabs.append((T("Items"), "commit_item"))

                #req_record = db.req_req[record.req_id]
                #req_date = req_record.date
                rheader = DIV( TABLE( TR( TH( "%s: " % table.req_id.label),
                                          table.req_id.represent(record.req_id),
                                         ),
                                      TR( TH( "%s: " % T("Committing Warehouse")),
                                          s3db.org_site_represent(record.site_id),
                                          TH( "%s: " % T("Commit Date")),
                                          s3_date_represent(record.date),
                                          ),
                                      TR( TH( "%s: " % table.comments.label),
                                          TD(record.comments, _colspan=3)
                                          ),
                                         ),
                                        )
                prepare_btn = A( T("Send Commitment"),
                              _href = URL(c = "inv",
                                          f = "send_commit",
                                          args = [record.id]
                                          ),
                              _id = "send_commit",
                              _class = "action-btn"
                              )

                s3.rfooter = TAG[""](prepare_btn)

#                send_btn = A( T("Send Commitment as Shipment"),
#                              _href = URL(c = "inv",
#                                          f = "send_commit",
#                                          args = [record.id]
#                                          ),
#                              _id = "send_commit",
#                              _class = "action-btn"
#                              )
#
#                send_btn_confirm = SCRIPT("S3ConfirmClick('#send_commit', '%s')" %
#                                          T("Do you want to send these Committed items?") )
#                s3.rfooter = TAG[""](send_btn,send_btn_confirm)
                #rheader.append(send_btn)
                #rheader.append(send_btn_confirm)

            elif type == 3:
                tabs.append((T("People"), "commit_person"))

                #req_record = db.req_req[record.req_id]
                #req_date = req_record.date
                organisation_represent = s3db.org_organisation_represent
                rheader = DIV( TABLE( TR( TH( "%s: " % table.req_id.label),
                                          table.req_id.represent(record.req_id),
                                         ),
                                      TR( TH( "%s: " % T("Committing Organization")),
                                          organisation_represent(record.organisation_id),
                                          TH( "%s: " % T("Commit Date")),
                                          s3_date_represent(record.date),
                                          ),
                                      TR( TH( "%s: " % table.comments.label),
                                          TD(record.comments, _colspan=3)
                                          ),
                                         ),
                                        )
            else:
                # Other (& Assets/Shelter)
                rheader = DIV( TABLE( TR( TH( "%s: " % table.req_id.label),
                                          table.req_id.represent(record.req_id),
                                         ),
                                      TR( TH( "%s: " % T("Committing Person")),
                                          s3db.pr_person_represent(record.committer_id),
                                          TH( "%s: " % T("Commit Date")),
                                          s3_date_represent(record.date),
                                          ),
                                      TR( TH( "%s: " % table.comments.label),
                                          TD(record.comments or "", _colspan=3)
                                          ),
                                         ),
                                        )

            rheader_tabs = s3_rheader_tabs(r,
                                           tabs)
            rheader.append(rheader_tabs)

            return rheader
    return None

# =============================================================================
def commit_item():
    """ REST Controller """

    return s3_rest_controller()

# =============================================================================
def commit_req():
    """
        function to commit items according to a request.
        copy data from a req into a commitment
        arg: req_id
        vars: site_id
    """

    req_id = request.args[0]
    r_req = s3db.req_req[req_id]
    site_id = request.vars.get("site_id")

    # User must have permissions over facility which is sending
    (prefix, resourcename, id) = s3db.get_instance(s3db.org_site, site_id)
    if not site_id or not auth.s3_has_permission("update",
                                                 "%s_%s" % (prefix,
                                                            resourcename),
                                                 record_id=id):
        session.error = T("You do not have permission to make this commitment.")
        redirect(URL(c="req", f="req",
                     args=[req_id]))

    # Create a new commit record
    commit_id = s3db.req_commit.insert(date = request.utcnow,
                                       req_id = req_id,
                                       site_id = site_id,
                                       type = r_req.type
                                       )

    # Only select items which are in the warehouse
    ritable = s3db.req_req_item
    iitable = s3db.inv_inv_item
    query = (ritable.req_id == req_id) & \
            (ritable.quantity_fulfil < ritable.quantity) & \
            (iitable.site_id == site_id) & \
            (ritable.item_id == iitable.item_id) & \
            (ritable.deleted == False)  & \
            (iitable.deleted == False)
    req_items = db(query).select(ritable.id,
                                 ritable.quantity,
                                 ritable.item_pack_id,
                                 iitable.item_id,
                                 iitable.quantity,
                                 iitable.item_pack_id)

    citable = s3db.req_commit_item
    for req_item in req_items:
        req_item_quantity = req_item.req_req_item.quantity * \
                            req_item.req_req_item.pack_quantity

        inv_item_quantity = req_item.inv_inv_item.quantity * \
                            req_item.inv_inv_item.pack_quantity

        if inv_item_quantity > req_item_quantity:
            commit_item_quantity = req_item_quantity
        else:
            commit_item_quantity = inv_item_quantity
        commit_item_quantity = commit_item_quantity / req_item.req_req_item.pack_quantity

        if commit_item_quantity:
            commit_item_id = citable.insert(commit_id = commit_id,
                                            req_item_id = req_item.req_req_item.id,
                                            item_pack_id = req_item.req_req_item.item_pack_id,
                                            quantity = commit_item_quantity
                                            )

            # Update the req_item.commit_quantity  & req.commit_status
            s3mgr.store_session("req", "commit_item", commit_item_id)
            s3db.req_commit_item_onaccept(None)

    # Redirect to commit
    redirect(URL(c="req", f="commit",
                 args=[commit_id, "commit_item"]))

# =============================================================================
def send_req():
    """
        function to send items according to a request.
        copy data from a req into a send
        arg: req_id
        vars: site_id
    """

    ritable = s3db.req_req_item
    iitable = s3db.inv_inv_item
    sendtable = s3db.inv_send
    tracktable = s3db.inv_track_item
    siptable = s3db.supply_item_pack

    req_id = request.args[0]
    r_req = s3db.req_req[req_id]
    site_id = request.vars.get("site_id")

    # User must have permissions over facility which is sending
    (prefix, resourcename, id) = s3db.get_instance(db.org_site, site_id)
    if not site_id or not auth.s3_has_permission("update",
                                                 "%s_%s" % (prefix,
                                                            resourcename),
                                                 record_id=id):
        session.error = T("You do not have permission to send this shipment.")
        redirect(URL(c="req", f="req",
                     args = [req_id]))

    # Create a new send record
    code = s3db.inv_get_shipping_code("WB",
                                      site_id,
                                      s3db.inv_send.send_ref
                                     )
    send_id = sendtable.insert(send_ref = code,
                               req_ref = r_req.req_ref,
                               sender_id = auth.s3_logged_in_person(),
                               site_id = site_id,
                               date = request.utcnow,
                               recipient_id = r_req.requester_id,
                               to_site_id = r_req.site_id,
                               status = s3db.inv_ship_status["IN_PROCESS"],
                              )

    # Get the items for this request that have not been fulfilled (in transit)
    query = (ritable.req_id == req_id) & \
            (ritable.quantity_transit < ritable.quantity) & \
            (ritable.deleted == False)
    req_items = db(query).select(ritable.id,
                                 ritable.quantity,
                                 ritable.quantity_transit,
                                 ritable.item_id,
                                 ritable.item_pack_id,
                                )

    # loop through each request item and find matched in the site inventory
    for req_i in req_items:
        query = (iitable.item_id == req_i.item_id) & \
                (iitable.quantity > 0) & \
                (iitable.site_id == site_id) & \
                (iitable.deleted == False)
        inv_items = db(query).select(iitable.id,
                                     iitable.item_id,
                                     iitable.quantity,
                                     iitable.item_pack_id,
                                     iitable.pack_value,
                                     iitable.currency,
                                     iitable.expiry_date,
                                     iitable.bin,
                                     iitable.owner_org_id,
                                     iitable.supply_org_id,
                                    )
        # if their is a single match then set up a tracktable record
        # get the request pack_quantity
        req_p_qnty = siptable[req_i.item_pack_id].quantity
        req_qnty = req_i.quantity
        req_qnty_in_t = req_i.quantity_transit
        req_qnty_wanted = (req_qnty - req_qnty_in_t) * req_p_qnty
        # insert the track item records
        # if their is more than one item match then set the quantity to 0
        # and add the quantity requested in the comments
        for inv_i in inv_items:
            # get inv_item.pack_quantity
            if len(inv_items) == 1:
                # Remove this total from the warehouse stock
                send_item_quantity = s3db.inv_remove(inv_i, req_qnty_wanted)
            else:
                send_item_quantity = 0
            comment = "%d items needed to match total request" % req_qnty_wanted
            tracktable.insert(send_id = send_id,
                              send_inv_item_id = inv_i.id,
                              item_id = inv_i.item_id,
                              req_item_id = req_i.id,
                              item_pack_id = inv_i.item_pack_id,
                              quantity = send_item_quantity,
                              status = s3db.inv_tracking_status["IN_PROCESS"],
                              pack_value = inv_i.pack_value,
                              currency = inv_i.currency,
                              bin = inv_i.bin,
                              expiry_date = inv_i.expiry_date,
                              owner_org_id = inv_i.owner_org_id,
                              supply_org_id = inv_i.supply_org_id,
                              comments = comment,
                             )
    # Redirect to commit
    redirect(URL(c = "inv",
                 f = "send",
                 args = [send_id, "track_item"]))

# =============================================================================
def commit_item_json():
    """
    """

    ctable = s3db.req_commit
    itable = s3db.req_commit_item
    stable = s3db.org_site
    #ctable.date.represent = lambda dt: dt[:10]
    query = (itable.req_item_id == request.args[0]) & \
            (ctable.id == itable.commit_id) & \
            (ctable.site_id == stable.id) & \
            (itable.deleted == False)
    records = db(query).select(ctable.id,
                               ctable.date,
                               stable.name,
                               itable.quantity,
                               orderby = db.req_commit.date)

    json_str = '''[%s,%s''' % (json.dumps(dict(id = str(T("Committed")),
                                               quantity = "#")),
                               records.json()[1:])

    response.headers["Content-Type"] = "application/json"
    return json_str

# END =========================================================================
