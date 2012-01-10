# -*- coding: utf-8 -*-

"""
    Request Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @author: Fran Boon
    @date-created: 2010-09-02
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

s3_menu(module)

# Load Models
# (events loaded automatically, if-enabled)
s3mgr.load("req_req")
req_create_form_mods = response.s3.req_create_form_mods
req_priority_represent = response.s3.req_priority_represent

req_item_inv_item_btn = dict(url = URL(c = "req",
                                       f = "req_item_inv_item",
                                       args = ["[id]"]
                                      ),
                             _class = "action-btn",
                             label = str(T("Find")), # Change to Fulfil? Match?
                             )

# -----------------------------------------------------------------------------
def index():
    """
        Application Home page
        - custom View
    """

    module_name = deployment_settings.modules[module].name_nice
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

    # Defined in the Model for use from Multiple Controllers for unified menus
    return response.s3.req_controller()

# =============================================================================
def req_item():
    """ REST Controller """

    # Load Model & resolver
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    s3mgr.configure(tablename,
                    insertable=False)

    def prep(r):
        if r.interactive:
            if r.method != None and r.method != "update" and r.method != "read":
                # Hide fields which don't make sense in a Create form
                # - includes one embedded in list_create
                # - list_fields over-rides, so still visible within list itself
                response.s3.req_hide_quantities(r.table)

        return True
    response.s3.prep = prep

    output = s3_rest_controller()

    if response.s3.actions:
        response.s3.actions += [req_item_inv_item_btn]
    else:
        response.s3.actions = [req_item_inv_item_btn]

    return output

# -----------------------------------------------------------------------------
def req_item_packs():
    """
        Called by S3FilterFieldChange to provide the pack options for a
            particular Item
    """
    table = db.supply_item_pack
    query = (db.req_req_item.id == request.args[0]) & \
            (db.req_req_item.item_id == table.item_id)

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
    s3mgr.load("inv_inv_item")

    req_item_id  = request.args[0]
    request.args = [] #
    req_item = db.req_req_item[req_item_id]
    req = db.req_req[req_item.req_id]

    output = {}

    output["title"] = T("Request Item from Available Inventory")
    output["req_btn"] = A( T("Return to Request"),
                           _href = URL( c = "req",
                                        f = "req",
                                        args = [req_item.req_id, "req_item"]
                                        ),
                           _class = "action-btn"
                           )

    output["req_item"] = TABLE( TR(
                                    TH( "%s: " % T("Requested By") ),
                                    s3db.org_site_represent(req.site_id),
                                    TH( "%s: " % T("Item")),
                                    response.s3.inv_item_represent(req_item.item_id),
                                   ),
                                TR(
                                    TH( "%s: " % T("Requester") ),
                                    s3db.pr_person_represent(req.requester_id),
                                    TH( "%s: " % T("Quantity")),
                                    req_item.quantity,
                                   ),
                                TR(
                                    TH( "%s: " % T("Date Requested") ),
                                    req.date,
                                    TH( T("Quantity Committed")),
                                    req_item.quantity_commit,
                                   ),
                                TR(
                                    TH( "%s: " % T("Date Required") ),
                                    req.date_required,
                                    TH( "%s: " % T("Quantity in Transit")),
                                    req_item.quantity_transit,
                                   ),
                                TR(
                                    TH( "%s: " % T("Priority") ),
                                    req_priority_represent(req.priority),
                                    TH( "%s: " % T("Quantity Fulfilled")),
                                    req_item.quantity_fulfil,
                                   )
                               )

    response.s3.no_sspag = True # pagination won't work with 2 datatables on one page @todo: test

    # Get list of matching inventory items
    response.s3.filter = (db.inv_inv_item.item_id == req_item.item_id)
    # Tweak CRUD String for this context
    s3.crud_strings["inv_inv_item"].msg_list_empty = T("No Inventories currently have this item in stock")
    inv_items = s3_rest_controller("inv", "inv_item")
    output["items"] = inv_items["items"]

    # Get list of alternative inventory items
    atable = db.supply_item_alt
    query = (atable.item_id == req_item.item_id ) & \
            (atable.deleted == False )
    alt_item_rows = db(query).select(atable.alt_item_id)
    alt_item_ids = [alt_item_row.alt_item_id for alt_item_row in alt_item_rows]

    if alt_item_ids:
        response.s3.filter = (db.inv_inv_item.item_id.belongs(alt_item_ids))
        inv_items_alt = s3_rest_controller("inv", "inv_item")
        output["items_alt"] = inv_items_alt["items"]
    else:
        output["items_alt"] = T("No Inventories currently have suitable alternative items in stock")

    response.view = "req/req_item_inv_item.html"
    response.s3.actions = [dict(url = URL(c = request.controller,
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

    # Defined in the Model for use from Multiple Controllers for unified menus
    return response.s3.req_skill_controller()

# =============================================================================
def commit():
    """ REST Controller """

    # Check if user is affiliated to an Organisation
    if not is_affiliated():
        tablename = "req_commit_person"
        table = db[tablename]
        # Unaffiliated people can't commit on behalf of others
        table.person_id.writable = False
        # & can only make single-person commitments
        # (This should have happened in the main commitment)
        s3mgr.configure(tablename,
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
                    auth.permission.permitted_facilities(table=table,
                                                         error_msg=T("You do not have permission for any facility to make a commitment.") )

                else:
                    # Non-Item commits can have an Organisation
                    # Limit organisation_id to organisations the user has permissions for
                    auth.permission.permitted_organisations(table=r.table,
                                                            redirect_on_error=False)
                    table.organisation_id.readable = True
                    table.organisation_id.writable = True
                    # Non-Item commits shouldn't have a From Inventory
                    # @ToDo: Assets do?
                    table.site_id.readable = False
                    table.site_id.writable = False

        if r.component:
            req_id = r.record.req_id
            if r.component.name == "item":
                # Limit commit items to items from the request
                db.req_commit_item.req_item_id.requires = \
                    IS_ONE_OF(db,
                              "req_req_item.id",
                              response.s3.req_item_represent,
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
                #              response.s3.req_skill_represent,
                #              orderby = "req_req_skill.id",
                #              filterby = "req_id",
                #              filter_opts = [req_id],
                #              sort=True
                #              )
        return True

    response.s3.prep = prep

    rheader = commit_rheader

    output = s3_rest_controller(module, resourcename, rheader=rheader)

    return output

# -----------------------------------------------------------------------------
def commit_rheader(r):
    """ Resource Header for Commitments """

    if r.representation == "html":
        record = r.record
        if record and r.name == "commit":
            tabs = [(T("Edit Details"), None)]
            type = record.type and int(record.type)

            if type == 1:
                tabs.append((T("Items"), "commit_item"))

                #req_record = db.req_req[record.req_id]
                #req_date = req_record.date
                rheader = DIV( TABLE( TR( TH( "%s: " % T("Request")),
                                          response.s3.req_represent(record.req_id),
                                         ),
                                      TR( TH( "%s: " % T("Committing Inventory")),
                                          s3db.org_site_represent(record.site_id),
                                          TH( "%s: " % T("Commit Date")),
                                          s3_date_represent(record.date),
                                          ),
                                      TR( TH( "%s: " % T("Comments")),
                                          TD(record.comments, _colspan=3)
                                          ),
                                         ),
                                        )

                send_btn = A( T("Send Commitment as Shipment"),
                              _href = URL(c = "inv",
                                          f = "send_commit",
                                          args = [record.id]
                                          ),
                              _id = "send_commit",
                              _class = "action-btn"
                              )

                send_btn_confirm = SCRIPT("S3ConfirmClick('#send_commit', '%s')" %
                                          T("Do you want to send these Committed items?") )
                response.s3.rfooter = TAG[""](send_btn,send_btn_confirm)
                #rheader.append(send_btn)
                #rheader.append(send_btn_confirm)

            elif type == 3:
                tabs.append((T("People"), "commit_person"))

                #req_record = db.req_req[record.req_id]
                #req_date = req_record.date
                organisation_represent = s3db.org_organisation_represent
                rheader = DIV( TABLE( TR( TH( "%s: " % T("Request")),
                                          response.s3.req_represent(record.req_id),
                                         ),
                                      TR( TH( "%s: " % T("Committing Organization")),
                                          organisation_represent(record.organisation_id),
                                          TH( "%s: " % T("Commit Date")),
                                          s3_date_represent(record.date),
                                          ),
                                      TR( TH( "%s: " % T("Comments")),
                                          TD(record.comments, _colspan=3)
                                          ),
                                         ),
                                        )
            else:
                # Other (& Assets/Shelter)
                rheader = DIV( TABLE( TR( TH( "%s: " % T("Request")),
                                          response.s3.req_represent(record.req_id),
                                         ),
                                      TR( TH( "%s: " % T("Committing Person")),
                                          s3db.pr_person_represent(record.committer_id),
                                          TH( "%s: " % T("Commit Date")),
                                          s3_date_represent(record.date),
                                          ),
                                      TR( TH( "%s: " % T("Comments")),
                                          TD(record.comments, _colspan=3)
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

    output = s3_rest_controller()
    return output

# =============================================================================
def commit_req():
    """
        function to commit items according to a request.
        copy data from a req into a commitment
        arg: req_id
        vars: site_id
    """

    req_id = request.args[0]
    r_req = db.req_req[req_id]
    site_id = request.vars.get("site_id")

    s3mgr.load("inv_inv_item")

    # User must have permissions over facility which is sending
    (prefix, resourcename, id) = s3mgr.model.get_instance(db.org_site,
                                                          site_id)
    if not site_id or not auth.s3_has_permission("update",
                                              db["%s_%s" % (prefix,
                                                            resourcename)],
                                              record_id=id):
        session.error = T("You do not have permission to make this commitment.")
        redirect(URL(c = "req",
                     f = "req",
                     args = [req_id],
                     ))

    # Create a new commit record
    commit_id = db.req_commit.insert( date = request.utcnow,
                                      req_id = req_id,
                                      site_id = site_id,
                                      type = r_req.type)

    # Only select items which are in the warehouse
    ritable = db.req_req_item
    iitable = db.inv_inv_item
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
            commit_item_id = db.req_commit_item.insert( commit_id = commit_id,
                                                        req_item_id = req_item.req_req_item.id,
                                                        item_pack_id = req_item.req_req_item.item_pack_id,
                                                        quantity = commit_item_quantity
                                                       )

            # Update the req_item.commit_quantity  & req.commit_status
            s3mgr.store_session("req", "commit_item", commit_item_id)
            response.s3.commit_item_onaccept(None)

    # Redirect to commit
    redirect(URL(c = "req",
                 f = "commit",
                 args = [commit_id, "commit_item"]))

# =============================================================================
def send_req():
    """
        function to send items according to a request.
        copy data from a req into a send
        arg: req_id
        vars: site_id
    """

    req_id = request.args[0]
    r_req = db.req_req[req_id]
    site_id = request.vars.get("site_id")

    s3mgr.load("inv_inv_item")
    s3mgr.load("inv_send")
    s3mgr.load("inv_send_item")

    # User must have permissions over facility which is sending
    (prefix, resourcename, id) = s3mgr.model.get_instance(db.org_site,
                                                          site_id)
    if not site_id or not auth.s3_has_permission("update",
                                                 db["%s_%s" % (prefix,
                                                               resourcename)],
                                                 record_id=id):
        session.error = T("You do not have permission to send this shipment.")
        redirect(URL(c = "req",
                     f = "req",
                     args = [req_id]))

    to_location_id = db.org_site[r_req.site_id].location_id

    # Create a new send record
    send_id = db.inv_send.insert( date = request.utcnow,
                                  site_id = site_id,
                                  to_location_id = to_location_id)

    # Only select items which are in the warehouse
    ritable = db.req_req_item
    iitable = db.inv_inv_item
    query = (ritable.req_id == req_id) & \
            (ritable.quantity_fulfil < ritable.quantity) & \
            (iitable.site_id == site_id) & \
            (ritable.item_id == iitable.item_id) & \
            (ritable.deleted == False)  & \
            (db.inv_inv_item.deleted == False)
    req_items = db(query).select(ritable.id,
                                 ritable.quantity,
                                 ritable.item_pack_id,
                                 iitable.id,
                                 iitable.item_id,
                                 iitable.quantity,
                                 iitable.item_pack_id)

    for req_item in req_items:
        req_item_quantity = req_item.req_req_item.quantity * \
                            req_item.req_req_item.pack_quantity

        inv_item_quantity = req_item.inv_inv_item.quantity * \
                            req_item.inv_inv_item.pack_quantity

        if inv_item_quantity > req_item_quantity:
            send_item_quantity = req_item_quantity
        else:
            send_item_quantity = inv_item_quantity
        send_item_quantity = send_item_quantity / req_item.req_req_item.pack_quantity

        if send_item_quantity:
            send_item_id = db.inv_send_item.insert( send_id = send_id,
                                                    inv_item_id = req_item.inv_inv_item.id,
                                                    req_item_id = req_item.req_req_item.id,
                                                    item_pack_id = req_item.req_req_item.item_pack_id,
                                                    quantity = send_item_quantity)

    # Redirect to commit
    redirect(URL(c = "inv",
                 f = "send",
                 args = [send_id, "send_item"]))

# =============================================================================
def commit_item_json():
    ctable = db.req_commit
    itable = db.req_commit_item
    stable = db.org_site
    #ctable.date.represent = lambda dt: dt[:10]
    query = (itable.req_item_id == request.args[0]) & \
            (ctable.id == itable.commit_id) & \
            (ctable.site_id == stable.id) & \
            (itable.deleted == False)
    records =  db(query).select(ctable.id,
                                ctable.date,
                                stable.name,
                                itable.quantity,
                                orderby = db.req_commit.date)

    json_str = "[%s,%s" % ( json.dumps(dict(id = str(T("Committed")),
                                            quantity = "#")),
                            records.json()[1:])

    response.headers["Content-Type"] = "application/json"
    return json_str

# END =========================================================================
