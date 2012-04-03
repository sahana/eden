# -*- coding: utf-8 -*-

"""
    Inventory Management

    A module to record inventories of items at a locations (sites),
    including Warehouses, Offices, Shelters & Hospitals
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """
        Application Home page
        - custom View
    """

    # Load models
    s3mgr.load("cr_shelter") # Need CRUD String

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# =============================================================================
def office():
    """
        Required to ensure the tabs work from req_match
    """
    return warehouse()

def warehouse():
    """
        RESTful CRUD controller
        Filtered version of the org_office resource
    """

    module = "org"
    resourcename = "office"
    tablename = "org_office"
    table = s3db[tablename]

    s3mgr.load("inv_inv_item")

    if "viewing" in request.get_vars:
        viewing = request.get_vars.viewing
        tn, record = viewing.split(".", 1)
        if tn == "org_office":
            request.args.insert(0, record)

    s3.crud_strings[tablename] = s3.org_warehouse_crud_strings

    # Type is Warehouse
    table.type.default = 5 # Warehouse
    table.type.writable = False

    # Only show warehouses
    response.s3.filter = (table.type == 5)

    # Remove type from list_fields
    list_fields = s3mgr.model.get_config(tablename, "list_fields")
    try:
        list_fields.remove("type")
    except:
        # Already removed
        pass
    s3mgr.configure(tablename, list_fields=list_fields)

    warehouse_search = s3base.S3Search(
        advanced=(s3base.S3SearchSimpleWidget(
                    name="warehouse_search_text",
                    label=T("Search"),
                    comment=T("Search for warehouse by text."),
                    field=["name","comments", "email"]
                  ),
                  s3base.S3SearchOptionsWidget(
                    name="warehouse_search_org",
                    label=T("Organization"),
                    comment=T("Search for warehouse by organization."),
                    field=["organisation_id"],
                    represent ="%(name)s",
                    cols = 3
                  ),
                  s3base.S3SearchLocationHierarchyWidget(
                    name="warehouse_search_location",
                    comment=T("Search for warehouse by location."),
                    represent ="%(name)s",
                    cols = 3
                  ),
                  s3base.S3SearchLocationWidget(
                    name="warehouse_search_map",
                    label=T("Map"),
                  ),
        ))
    s3mgr.configure(tablename,
                    search_method = warehouse_search)

    # CRUD pre-process
    def prep(r):
        if r.interactive and r.tablename == "org_office":

            if r.method != "read":
                # Don't want to see in Create forms
                # inc list_create (list_fields over-rides)
                r.table.obsolete.writable = False
                r.table.obsolete.readable = False
                address_hide(table)
                # Process Base Location
                #s3mgr.configure(table._tablename,
                #                onaccept=address_onaccept)

            if r.component:
                if r.component.name == "inv_item":
                    # Filter out items which are already in this inventory
                    s3db.inv_prep(r)
                    # Remove the Warehouse Name from the list_fields
                    list_fields = s3mgr.model.get_config("inv_inv_item", "list_fields")
                    try:
                        list_fields.remove("site_id")
                        s3mgr.configure("inv_inv_item", list_fields=list_fields)
                    except:
                        pass

                elif r.component.name == "recv" or \
                   r.component.name == "send":
                    # Filter out items which are already in this inventory
                    s3db.inv_prep(r)

                elif r.component.name == "human_resource":
                    # Filter out people which are already staff for this warehouse
                    s3_filter_staff(r)
                    # Cascade the organisation_id from the hospital to the staff
                    htable = s3db.hrm_human_resource
                    htable.organisation_id.default = r.record.organisation_id
                    htable.organisation_id.writable = False

                elif r.component.name == "req":
                    s3db.req_prep(r)
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        # inc list_create (list_fields over-rides)
                        s3db.req_create_form_mods()

        # "show_obsolete" var option can be added (btn?) later to
        # disable this filter
        if r.method in [None, "list"] and \
            not r.vars.get("show_obsolete", False):
            r.resource.add_filter((s3db.org_office.obsolete != True))
        return True
    response.s3.prep = prep

    # CRUD post-process
    def postp(r, output):
        if r.interactive and not r.component and r.method != "import":
            # Change Action buttons to open Stock Tab by default
            read_url = URL(f="warehouse", args=["[id]", "inv_item"])
            update_url = URL(f="warehouse", args=["[id]", "inv_item"])
            s3mgr.crud.action_buttons(r,
                                      read_url=read_url,
                                      update_url=update_url)
        if "add_btn" in output:
            del output["add_btn"]
        return output
    response.s3.postp = postp

    rheader = response.s3.inv_warehouse_rheader

    if "extra_data" in request.get_vars:
        csv_template = "inv_item"
        module = "inv"
        resourcename = "inv_item"
    else:
        csv_template = "warehouse"
    csv_stylesheet = "%s.xsl" % csv_template


    # remove CRUD generated buttons in the tabs
    s3mgr.configure("inv_inv_item",
                    create=False,
                    listadd=False,
                    editable=False,
                    deletable=False,
                   )


    output = s3_rest_controller(module, resourcename,
                                rheader=rheader,
                                csv_template = csv_template,
                                csv_stylesheet = csv_stylesheet,
                                # Extra fields for CSV uploads:
                                csv_extra_fields = [
                                    dict(label="Organisation",
                                         field=s3db.org_organisation_id(comment=None))
                                ])
    if "add_btn" in output:
        del output["add_btn"]
    return output

# =============================================================================
def incoming():
    """ Incoming Shipments """

    # Defined in the Model for use from Multiple Controllers for unified menus
    return inv_incoming()

# =============================================================================
def req_match():
    """ Match Requests """

    return s3db.req_match()

# =============================================================================
def inv_item():
    """ REST Controller """
    table = s3db.inv_inv_item

    # Upload for configuration (add replace option)
    response.s3.importerPrep = lambda: dict(ReplaceOption=T("Remove existing data before import"))

    # Import pre-process
    def import_prep(data):
        """
            Deletes all Stock records of the organisation
            before processing a new data import, used for the import_prep
            hook in s3mgr
        """
        request = current.request
        resource, tree = data
        xml = s3mgr.xml
        tag = xml.TAG
        att = xml.ATTRIBUTE
        if response.s3.importerReplace:
            if tree is not None:
                root = tree.getroot()
                expr = "/%s/%s[@%s='org_organisation']/%s[@%s='name']" % \
                       (tag.root, tag.resource, att.name, tag.data, att.field)
                orgs = root.xpath(expr)
                otable = s3db.org_organisation
                stable = s3db.org_site
                itable = s3db.inv_inv_item
                for org in orgs:
                    org_name = org.get("value", None) or org.text
                    if org_name:
                        try:
                            org_name = json.loads(s3mgr.xml.xml_decode(org_name))
                        except:
                            pass
                    if org_name:
                        query = (otable.name == org_name) & \
                                (stable.organisation_id == otable.id) & \
                                (itable.site_id == stable.id)
                        resource = s3mgr.define_resource("inv", "inv_item", filter=query)
                        ondelete = s3mgr.model.get_config("inv_inv_item", "ondelete")
                        resource.delete(ondelete=ondelete, format="xml")
            resource.skip_import = True
    s3mgr.import_prep = import_prep


    # Limit site_id to sites the user has permissions for
    auth.permission.permitted_facilities(table=table,
                                         error_msg=T("You do not have permission for any site to add an inventory item."))

    if len(request.args) > 1 and request.args[1] == "track_item":
        # remove CRUD generated buttons in the tabs
        s3mgr.configure("inv_track_item",
                        create=False,
                        listadd=False,
                        editable=False,
                        deletable=False,
                       )

    # remove CRUD generated buttons in the tabs
    s3mgr.configure("inv_inv_item",
                    create=False,
                    listadd=False,
                    editable=False,
                    deletable=False,
                   )
    rheader = response.s3.inv_warehouse_rheader
    output =  s3_rest_controller("inv",
                                 "inv_item",
                                 rheader=rheader,
                                 csv_extra_fields = [
                                                     dict(label="Organisation",
                                                          field=s3db.org_organisation_id(comment=None)
                                                          )
                                                     ],
                                 interactive_report = True
                                )
    if "add_btn" in output:
        del output["add_btn"]
    return output

# -----------------------------------------------------------------------------
def track_movement():
    """ REST Controller """
    table = s3db.inv_track_item

    def prep(r):
        if r.interactive:
            if "viewing" in request.vars:
                dummy, item_id = request.vars.viewing.split(".")
            filter = (table.item_id == item_id ) | \
                     (table.send_stock_id == item_id)
            response.s3.filter = filter
        return True

    s3mgr.configure("inv_track_item",
                    create=False,
                    listadd=False,
                    editable=False,
                    deletable=False,
                   )

    response.s3.prep = prep
    rheader = response.s3.inv_warehouse_rheader
    output =  s3_rest_controller("inv",
                                 "track_item",
                                 rheader=rheader,
                                )
    if "add_btn" in output:
        del output["add_btn"]
    return output

# -----------------------------------------------------------------------------
def inv_item_quantity():
    """
    """

    table = s3db.inv_inv_item
    ptable = s3db.supply_item_pack
    query = (table.id == request.args[0]) & \
            (table.item_pack_id == ptable.id)
    record = db(query).select(table.quantity,
                              ptable.quantity,
                              limitby=(0, 1)).first()

    response.headers["Content-Type"] = "application/json"
    return json.dumps(record)

# -----------------------------------------------------------------------------
def inv_item_packs():
    """
        Called by S3FilterFieldChange to provide the pack options for a
            particular Item
    """

    table = s3db.inv_inv_item
    ptable = s3db.supply_item_pack
    query = (table.id == request.args[0]) & \
            (table.item_id == ptable.item_id)
    records = db(query).select(ptable.id,
                               ptable.name,
                               ptable.quantity)

    response.headers["Content-Type"] = "application/json"
    return records.json()

# =============================================================================
def send():
    """ RESTful CRUD controller """
    s3mgr.load("inv_send")
    s3db = current.s3db
    db = current.db
    auth = current.auth
    request = current.request
    response = current.response
    s3 = response.s3

    tablename = "inv_send"
    table = s3db.inv_send


    # Limit site_id to sites the user has permissions for
    error_msg = T("You do not have permission for any facility to send a shipment.")
    auth.permission.permitted_facilities(table=table,
                                         error_msg=error_msg)

    # Set Validator for checking against the number of items in the warehouse
    vars = request.vars
    if (vars.send_stock_id):
        s3db.inv_track_item.quantity.requires = QUANTITY_INV_ITEM(db,
                                                                 vars.send_stock_id,
                                                                 vars.item_pack_id)

    def prep(r):
        # Default to the Search tab in the location selector
        response.s3.gis.tab = "search"

        if r.component:
            # Can only create or delete track items for a send record if the status is preparing
            if r.method == "create" or r.method == "delete":
                record = table[r.id]
                if record.status != 1:
                    return False
            if r.method == "delete":
                return s3.inv_track_item_deleting(r.component_id)
            if r.record.get("site_id"):
                # Restrict to items from this warehouse only
                tracktable = s3db.inv_track_item
                comp_rec = tracktable[r.component_id]
                tracktable.send_stock_id.requires = IS_ONE_OF(db,
                                                         "inv_inv_item.id",
                                                         s3db.inv_item_represent,
                                                         orderby="inv_inv_item.id",
                                                         sort=True,
                                                         filterby = "site_id",
                                                         filter_opts = [r.record.site_id]
                                                        )
                # Hide the values that will be copied from the inv_inv_item record
                if comp_rec and comp_rec.get("req_item_id"):
                    tracktable.item_id.readable = True
                else:
                    tracktable.item_id.readable = False
                tracktable.item_id.writable = False
                tracktable.item_source_no.readable = False
                tracktable.item_source_no.writable = False
                tracktable.expiry_date.readable = False
                tracktable.expiry_date.writable = False
                tracktable.bin.readable = False
                tracktable.bin.writable = False
                tracktable.supply_org_id.readable = False
                tracktable.supply_org_id.writable = False
                # Hide the link to the receive and adjustment records
                tracktable.recv_id.readable = False
                tracktable.recv_id.writable = False
                tracktable.adj_item_id.readable = False
                tracktable.adj_item_id.writable = False
            if r.interactive:
                SHIP_STATUS_IN_PROCESS = s3db.inv_ship_status["IN_PROCESS"]
                SHIP_STATUS_SENT = s3db.inv_ship_status["SENT"]
                if r.record.status == SHIP_STATUS_IN_PROCESS:
                    s3.crud_strings.inv_send.title_update = \
                    s3.crud_strings.inv_send.title_display = T("Process Shipment to Send")
                elif "site_id" in request.vars and r.record.status == SHIP_STATUS_SENT:
                    s3.crud_strings.inv_send.title_update = \
                    s3.crud_strings.inv_send.title_display = T("Review Incoming Shipment to Receive")
        return True

    if len(request.args) > 1 and request.args[1] == "track_item" and table[request.args[0]].status:
        # remove CRUD generated buttons in the tabs
        s3mgr.configure("inv_track_item",
                        create=False,
                        listadd=False,
                        editable=False,
                        deletable=False,
                       )
    response.s3.prep = prep
    output = s3_rest_controller("inv",
                                "send",
                                rheader=s3.inv_send_rheader,
                               )
    return output

# ==============================================================================
def prepare_commit():
    """ RESTful CRUD controller """
    s3mgr.load("inv_send")
    s3db = current.s3db
    db = current.db
    auth = current.auth
    request = current.request
    response = current.response
    s3 = response.s3

    # Get the commit and request records
    if len(request.args) > 0:
        commit_id = request.args[0]
    else:
        redirect(URL(c = "req",
                     f = "commit",
                    )
                )
    req_table = s3db.req_req
    rim_table = s3db.req_req_item
    com_table = s3db.req_commit
    cim_table = s3db.req_commit_item
    send_table = s3db.inv_send
    track_table = s3db.inv_track_item

    query = (com_table.id == commit_id) & \
            (com_table.req_id == req_table.id) & \
            (com_table.deleted == False)
    record = db(query).select(limitby = (0, 1)).first()
    # create a inv_send and link to the commit
    send_id = send_table.insert(sender_id = record.req_commit.committer_id,
                                site_id = record.req_commit.site_id,
                                recipient_id = record.req_req.requester_id,
                                to_site_id = record.req_req.site_id,
                                status = 0)

    # get all of the committed items
    query = (cim_table.commit_id == commit_id) & \
            (cim_table.req_item_id == rim_table.id) & \
            (cim_table.deleted == False)
    records = db(query).select()
    # create inv_track_items for each commit item
    for row in records:
        id = track_table.insert(track_org_id = record.req_commit.organisation_id,
                                send_id = send_id,
                                status = 1,
                                item_id = row.req_req_item.item_id,
                                item_pack_id = row.req_req_item.item_pack_id,
                                quantity = row.req_commit_item.quantity,
                                currency = row.req_req_item.currency,
                                req_item_id = row.req_req_item.id)
        track_table(track_table.id == id).update(tracking_no = "TN:%6d" % (10000 + id))
    # redirect to inv_send for the send id just created
    redirect(URL(c = "inv",
                 f = "send",
                 args = [send_id, "track_item"]))


# -----------------------------------------------------------------------------
def send_process():
    """ Send a Shipment """

    send_id = request.args[0]
    stable = s3db.inv_send
    tracktable = s3db.inv_track_item
    ritable = s3db.req_req_item
    otable = s3db.org_office

    if not auth.s3_has_permission("update",
                                  stable,
                                  record_id=send_id):
        session.error = T("You do not have permission to send this shipment.")

    send_record = stable[send_id]

    if send_record.status != eden.inv.inv_ship_status["IN_PROCESS"]:
        session.error = T("This shipment has already been sent.")

    # Get the track items that are part of this shipment
    query = ( tracktable.send_id == send_id ) & \
            (tracktable.deleted == False)
    track_items = db(query).select()
    if not track_items:
        session.error = T("No items have been selected for shipping.")

    if session.error:
        redirect(URL(c = "inv",
                     f = "send",
                     args = [send_id]))

    # Update Send record & lock for editing
    stable[send_id] = dict(date = request.utcnow,
                           status = eden.inv.inv_ship_status["SENT"],
                           owned_by_user = None,
                           owned_by_group = ADMIN)
    # if this is linked to a request then update the quantity in transit
    for track_item in track_items:
        if track_item.req_item_id:
            db(ritable.id == track_item.req_item_id).update(quantity_transit = ritable.quantity_transit + track_item.quantity)
    # Create a Receive record
    recv_id = s3db.inv_recv.insert(sender_id = send_record.sender_id,
                                   tracking_no = send_record.tracking_no,
                                   from_site_id = send_record.site_id,
                                   eta = send_record.delivery_date,
                                   recipient_id = send_record.recipient_id,
                                   site_id = send_record.to_site_id,
                                   comments = send_record.comments,
                                   status = eden.inv.inv_ship_status["SENT"],
                                   type = 1, # 1:"Another Inventory"
                                  )
    # Change the status for all track items in this shipment to In transit
    # and link to the receive record
    db(tracktable.send_id == send_id).update(status = 2,
                                             recv_id = recv_id)

    session.confirmation = T("Shipment Items sent from Warehouse")
    # Go to the Site which has sent these items
    site_id = send_record.site_id
    (prefix, resourcename, id) = s3mgr.model.get_instance(s3db.org_site,
                                                          site_id)
    query = (otable.id == id)
    otype = db(query).select(otable.type, limitby = (0, 1)).first()
    if otype and otype.type == 5:
        url = URL(c = "inv",
                 f = "warehouse",
                 args = [id, "inv_item"])
    else:
        url = URL(c = "org",
                 f = "office",
                 args = [id, "inv_item"])
    redirect(url)

# -----------------------------------------------------------------------------
def send_cancel():
    """
        This will cancel a shipment that has been sent

        @todo need to roll back commitments
    """

    send_id = request.args[0]
    stable = s3db.inv_send
    rtable = s3db.inv_recv
    tracktable = s3db.inv_track_item
    if not auth.s3_has_permission("delete",
                                  stable,
                                  record_id=send_id):
        session.error = T("You do not have permission to cancel this sent shipment.")

    send_record = stable[send_id]
    if send_record.status != eden.inv.inv_ship_status["SENT"]:
        session.error = T("This shipment has not been sent - it has NOT been canceled because can still be edited.")

    if session.error:
        redirect(URL(c = "inv",
                     f = "send",
                     args = [send_id],
                     )
                 )

    # Okay no error so far, let's delete that baby
    # Change the send and recv status to cancelled
    stable[send_id] = dict(date = request.utcnow,
                           status = eden.inv.inv_ship_status["CANCEL"],
                           owned_by_user = None,
                           owned_by_group = ADMIN)
    recv_row = db(tracktable.send_id == send_id).select(tracktable.recv_id,
                                                        limitby = (0, 1)).first()
    if recv_row:
        recv_id = recv_row.recv_id
        rtable[recv_id] = dict(date = request.utcnow,
                               status = eden.inv.inv_ship_status["CANCEL"],
                               owned_by_user = None,
                               owned_by_group = ADMIN)


    # Change the track items status to canceled and then delete them
    # If they are linked to a request then the in transit total will also be reduced
    # Records can only be deleted if the status is 1 (prepare)
    # so change the status before we delete
    db(tracktable.send_id == send_id).update(status = 1)
    track_rows = db(tracktable.send_id == send_id).select(tracktable.id)
    for track_item in track_rows:
        s3.inv_track_item_deleting(track_item.id)
    # Now change the status to 4 (cancelled)
    db(tracktable.send_id == send_id).update(status = 4)

    session.confirmation = T("Sent Shipment canceled and items returned to Warehouse")

    redirect(URL(c = "inv",
                 f = "send",
                 args = [send_id]))

# =============================================================================
def recv():
    """ RESTful CRUD controller """
    s3mgr.load("inv_recv")
    s3mgr.load("inv_adj_item")
    tablename = "inv_recv"
    table = s3db.inv_recv

    # Limit site_id to sites the user has permissions for
    if deployment_settings.get_inv_shipment_name() == "order":
        error_msg = T("You do not have permission for any facility to add an order.")
    else:
        error_msg = T("You do not have permission for any facility to receive a shipment.")
    auth.permission.permitted_facilities(table=table,
                                         error_msg=error_msg)

    # The inv_recv record might be created when the shipment is send and so it
    # might not have the recipient identified. If it is null then set it to
    # the person who is logged in (the default)
    if len(request.args) > 0:
        try:
            id = request.args[0]
            if table[id].recipient_id == None:
                db(table.id == id).update(recipient_id = auth.s3_logged_in_person())
        except:
            pass

    def prep(r):
        if r.component:
            record = table[r.id]
            # Can only create or delete track items for a recv record if the status is preparing
            if r.method == "create" or r.method == "delete":
                if record.status != 1:
                    return False
            tracktable = s3db.inv_track_item
            # Hide the link to the send and adjustment records
            tracktable.send_id.readable = False
            tracktable.send_id.writable = False
            tracktable.recv_id.readable = False
            tracktable.recv_id.writable = False
            tracktable.bin.readable = False
            tracktable.bin.writable = False
            tracktable.adj_item_id.readable = False
            tracktable.adj_item_id.writable = False

            if r.method == "update" and record.status==2:
                # Hide the values that will be copied from the inv_inv_item record
                tracktable.item_source_no.readable = True
                tracktable.item_source_no.writable = False
                tracktable.item_id.writable = False
                tracktable.send_stock_id.writable = False
                tracktable.item_pack_id.writable = False
                tracktable.quantity.writable = False
                tracktable.currency.writable = False
                tracktable.pack_value.writable = False
                tracktable.expiry_date.writable = False
                tracktable.supply_org_id.writable = False
                tracktable.recv_quantity.readable = True
                tracktable.recv_quantity.writable = True
                tracktable.recv_bin.readable = True
                tracktable.recv_bin.writable = True
            else:
                tracktable = s3db.inv_track_item
                # Hide the values that will be copied from the inv_inv_item record
                tracktable.send_stock_id.readable = False
                tracktable.send_stock_id.writable = False
                # Display the values that can only be entered on create
                tracktable.item_source_no.readable = True
                tracktable.item_source_no.writable = True
                tracktable.recv_quantity.readable = True
                tracktable.recv_bin.readable = True
                tracktable.recv_bin.writable = True

            SHIP_STATUS_IN_PROCESS = s3db.inv_ship_status["IN_PROCESS"]
            if r.record.status == SHIP_STATUS_IN_PROCESS:
                s3.crud_strings.inv_recv.title_update = \
                s3.crud_strings.inv_recv.title_display = T("Process Received Shipment")
        else:
            table.sender_id.readable = False
            table.sender_id.writable = False
            table.from_site_id.readable = False
            table.from_site_id.writable = False
            if r.id:
                record = table[r.id]
                # If this is part of a shipment then lock down the type and site_id
                if record.sender_id != None:
                    table.type.writable = False
                    table.site_id.writable = False
                if record.status == 1:
                    table.recipient_id.writable = False
                    table.date.writable = False

        return True
    response.s3.prep = prep

    if len(request.args) > 1 and request.args[1] == "track_item" and table[request.args[0]].status:
        # remove CRUD generated buttons in the tabs
        s3mgr.configure("inv_track_item",
                        create=False,
                        listadd=False,
                        editable=False,
                        deletable=False,
                       )
        if table[request.args[0]].status == 2:
            s3mgr.configure("inv_track_item",
                            editable=True,
                           )

    output = s3_rest_controller("inv", "recv",
                                rheader=eden.inv.inv_recv_rheader,
                                )
    return output


# -----------------------------------------------------------------------------
def req_items_for_inv(site_id, quantity_type):
    """
        used by recv_process & send_process
        returns a dict of unique req items (with min  db.req_req.date_required | db.req_req.date)
        key = item_id
        @param site_id: The inventory to find the req_items from
        @param quantity_type: str ("commit", "transit" or "fulfil) The
                              quantity type which will be used to determine if this item is still outstanding
    """
    if not deployment_settings.has_module("req"):
        return Storage()

    table = s3db.req_req
    itable = s3db.req_req_item
    query = ( table.site_id == site_id ) & \
            ( table.id == itable.req_id) & \
            ( itable.item_pack_id == itable.item_pack_id) & \
            ( itable["quantity_%s" % quantity_type] < itable.quantity) & \
            ( table.cancel == False ) & \
            ( table.deleted == False ) & \
            ( itable.deleted == False )
    req_items = db(query).select(itable.id,
                                 itable.req_id,
                                 itable.item_id,
                                 itable.quantity,
                                 itable["quantity_%s" % quantity_type],
                                 itable.item_pack_id,
                                 orderby = table.date_required | table.date,
                                 #groupby = itable.item_id
                                )

    # Because groupby doesn't follow the orderby, this will remove any
    # duplicate req_item, using the first record according to the orderby
    # req_items = req_items.as_dict( key = "req_req_item.item_id") <- doensn't work
    # @todo: web2py Rows.as_dict function could be extended to enable this functionality instead
    req_item_ids = []
    unique_req_items = Storage()
    for req_item in req_items:
        if req_item.item_id not in req_item_ids:
            # This item is not already in the dict
            unique_req_items[req_item.item_id] = Storage( req_item.as_dict() )
            req_item_ids.append(req_item.item_id)

    return unique_req_items

# -----------------------------------------------------------------------------
def req_item_in_shipment( shipment_item,
                          shipment_type,
                          req_items,
                         ):
    """
        Checks if a shipment item is in a request and updates req_item
        and the shipment.
    """

    shipment_item_table = "inv_%s_item" % shipment_type
    try:
        item_id = shipment_item[shipment_item_table].item_id
    except:
        item_id = shipment_item.inv_inv_item.item_id

    # Check for req_items
    if item_id in req_items:
        shipment_to_req_type = dict(recv = "fulfil",
                                    send = "transit")
        quantity_req_type = "quantity_%s" % shipment_to_req_type[shipment_type]

        # This item has been requested from this inv
        req_item = req_items[item_id]
        req_item_id = req_item.id

        # Update the req quantity
        # convert the shipment items quantity into the req_tem.quantity_fulfil (according to pack)
        quantity = req_item[quantity_req_type] + \
                   (shipment_item[shipment_item_table].pack_quantity / \
                    req_item.pack_quantity) * \
                    shipment_item[shipment_item_table].quantity
        quantity = min(quantity, req_item.quantity)  #Cap at req. quantity
        s3db.req_req_item[req_item_id] = {quantity_req_type: quantity}

        # Link the shipment_item to the req_item
        s3db[shipment_item_table][shipment_item[shipment_item_table].id] = \
            dict(req_item_id = req_item_id)

        # Flag req record to update status_fulfil
        return req_item.req_id, req_item.id
    else:
        return None, None


# -----------------------------------------------------------------------------
def recv_process():
    """ Receive a Shipment """

    s3mgr.load("inv_adj")
    s3mgr.load("inv_adj_item")
    recv_id = request.args[0]
    rtable = s3db.inv_recv
    stable = s3db.inv_send
    tracktable = s3db.inv_track_item
    ritable = s3db.req_req_item
    otable = s3db.org_office

    if not auth.s3_has_permission("update",
                                  rtable,
                                  record_id=recv_id):
        session.error = T("You do not have permission to receive this shipment.")


    recv_record = rtable[recv_id]

    if recv_record.status == eden.inv.SHIP_STATUS_RECEIVED:
        session.error = T("This shipment has already been received.")

    if recv_record.status == eden.inv.SHIP_STATUS_CANCEL:
        session.error = T("This shipment has already been received & subsequently canceled.")

    if session.error:
        redirect(URL(c = "inv",
                     f = "recv",
                     args = [recv_id]))

    site_id = recv_record.site_id
    # Update Receive record & lock for editing
    rtable[recv_id] = dict(date = request.utcnow,
                           status = eden.inv.inv_ship_status["RECEIVED"],
                           owned_by_user = None,
                           owned_by_group = ADMIN)
    send_row = db(tracktable.recv_id == recv_id).select(tracktable.send_id,
                                                        limitby = (0, 1)).first()
    if send_row:
        send_id = send_row.send_id
        stable[send_id] = dict(date = request.utcnow,
                               status = eden.inv.inv_ship_status["RECEIVED"],
                               owned_by_user = None,
                               owned_by_group = ADMIN)
    # Change the status for all track items in this shipment to Unloading
    # the onaccept will then move the values into the site update any request
    # record, create any adjustment if needed and change the status to Arrived
    db(tracktable.recv_id == recv_id).update(status = 3)

    # Go to the Inventory of the Site which has received these items
    (prefix, resourcename, id) = s3mgr.model.get_instance(s3db.org_site,
                                                          site_id)
    query = (otable.id == id)
    otype = db(query).select(otable.type, limitby = (0, 1)).first()
    if otype and otype.type == 5:
        url = URL(c = "inv",
                 f = "warehouse",
                 args = [id, "inv_item"])
    else:
        url = URL(c = "org",
                 f = "office",
                 args = [id, "inv_item"])
    redirect(url)


# -----------------------------------------------------------------------------
def recv_cancel():
    """
    Cancel a Received Shipment

    @todo what to do if the quantity cancelled doesn't exist?
    """

    recv_id = request.args[0]
    rtable = s3db.inv_recv
    stable = s3db.inv_send
    tracktable = s3db.inv_track_item
    stocktable = s3db.inv_inv_item
    ritable = s3db.req_req_item
    if not auth.s3_has_permission("delete",
                                  rtable,
                                  record_id=recv_id):
        session.error = T("You do not have permission to cancel this received shipment.")


    recv_record = rtable[recv_id]

    if recv_record.status != eden.inv.inv_ship_status["RECEIVED"]:
        session.error = T("This shipment has not been received - it has NOT been canceled because can still be edited.")

    if session.error:
        redirect(URL(c = "inv",
                     f = "recv",
                     args = [recv_id]))

    # Go through each item in the shipment remove them from the site store
    # and put them back in the track item record
    query = (tracktable.recv_id == recv_id) & \
            (tracktable.deleted == False)
    recv_items = db(query).select()
    send_id = None
    for recv_item in recv_items:
        stock_id = recv_item.recv_stock_id
        # This assumes that the inv_item has the quantity
        db(stocktable.id == stock_id).update(quantity = stocktable.quantity - recv_item.quantity)
        db(tracktable.recv_id == recv_id).update(status = 2) # In transit
        # @todo potential problem in that the send id should be the same for all track items but is not explicitly checked
        if send_id == None and recv_item.send_id != None:
            send_id = recv_item.send_id
    track_rows = db(tracktable.recv_id == recv_id).select()
    for track_item in track_rows:
        # if this is linked to a request
        # then remove these items from the quantity in transit
        if track_item.req_item_id:
            db(ritable.id == track_item.req_item_id).update(quantity_fulfil = ritable.quantity_fulfil - track_item.quantity)
    # Now set the recv record to cancelled and the send record to sent
    rtable[recv_id] = dict(date = request.utcnow,
                           status = eden.inv.inv_ship_status["CANCEL"],
                           owned_by_user = None,
                           owned_by_group = ADMIN)
    if send_id != None:
        # The sent record is now set back to SENT the warehouse can now cancel
        # this record to get the stock back into their warehouse.
        # IMPORTANT reports need to locate this record otherwise it can be
        # a mechanism to circumvent the auditing of stock
        stable[send_id] = dict(date = request.utcnow,
                               status = eden.inv.inv_ship_status["SENT"],
                               owned_by_user = None,
                               owned_by_group = ADMIN)
    redirect(URL(c = "inv",
                 f = "recv",
                 args = [recv_id]))





# -----------------------------------------------------------------------------






def recv_sent():
    """ wrapper function to copy data from a shipment which was sent to the warehouse to a recv shipment (will happen at destination WH)
        @ToDo: Consider making obsolete
    """

    send_id = request.args[0]
    # This is more explicit than getting the site_id from the inv_send.to_site_id
    # As there may be multiple sites per location.
    #site_id = request.vars.site_id



    # Flag shipment as received as received
    s3db.inv_send[send_id] = dict(status = eden.inv.inv_ship_status["RECEIVED"])

    # Redirect to rec
    redirect(URL(c = "inv",
                 f = "recv",
                 args = [recv_id, "recv_item"]))
# =============================================================================
def track_item():
    """ RESTful CRUD controller """
    s3mgr.configure("inv_track_item",
                    create=False,
                    listadd=False,
                    editable=False,
                    deletable=False,
                   )

    output = s3_rest_controller("inv",
                                "track_item",
                                rheader=response.s3.inv_warehouse_rheader,
                               )
    return output
# =============================================================================

def adj():
    """ RESTful CRUD controller """
    s3mgr.load("inv_adj")
    s3db = current.s3db
    db = current.db
    auth = current.auth
    request = current.request
    response = current.response
    s3 = response.s3

    tablename = "inv_adj"
    table = s3db.inv_adj

    # Limit site_id to sites the user has permissions for
    error_msg = T("You do not have permission to adjust the stock level in this warehouse.")
    auth.permission.permitted_facilities(table=table,
                                         error_msg=error_msg)

    def prep(r):
        if r.interactive:
            if r.component:
                if r.component_id:
                    aitable = s3db.inv_adj_item
                    if r.record.status == 0:
                        aitable.reason.writable = True
                    record = aitable[r.component_id]
                    if record.inv_item_id:
                        aitable.item_id.writable = False
                        aitable.item_pack_id.writable = False
                        aitable.item_id.writable = False
            else:
                # if an adjustment has been selected and it has been completed
                # then make the fields read only
                if r.record and r.record.status:
                    table.adjuster_id.writable = False
                    table.site_id.writable = False
                    table.comments.writable = False
                else:
                    if "site" in request.vars:
                        table.site_id.writable = False
                        table.site_id.default = request.vars.site
        return True

    response.s3.prep = prep

    if len(request.args) > 1 and request.args[1] == "adj_item" and table[request.args[0]].status:
        # remove CRUD generated buttons in the tabs
        s3mgr.configure("inv_adj_item",
                        create=False,
                        listadd=False,
                        editable=False,
                        deletable=False,
                       )

    output = s3_rest_controller("inv",
                                "adj",
                                rheader=s3.inv_adj_rheader,
                               )
    return output

def adj_close():
    """ RESTful CRUD controller """
    s3mgr.load("inv_adj")
    s3db = current.s3db
    db = current.db
    auth = current.auth
    request = current.request
    response = current.response
    s3 = response.s3
    atable = s3db.inv_adj
    aitable = s3db.inv_adj_item
    stocktable = s3db.inv_inv_item
    otable = s3db.org_office

    # Limit site_id to sites the user has permissions for
    error_msg = T("You do not have permission to adjust the stock level in this warehouse.")
    auth.permission.permitted_facilities(table=table,
                                         error_msg=error_msg)

    adj_id = request.args[0]
    adj_rec = atable[adj_id]
    if adj_rec.status != 0:
        session.error = T("This adjustment has already been closed.")

    if session.error:
        redirect(URL(c = "inv",
                     f = "adj",
                     args = [adj_id]))

    # Go through all the adj_items
    query = ( aitable.adj_id == adj_id ) & \
            (aitable.deleted == False)
    adj_items = db(query).select()
    for adj_item in adj_items:
        # if we don't have a stock item then create it
        if adj_item.inv_item_id == None:
            stock_id = stocktable.insert(site_id = adj_rec.site_id,
                                         item_id = adj_item.item_id,
                                         item_pack_id = adj_item.item_pack_id,
                                         currency = adj_item.currency,
                                         bin = adj_item.bin,
                                         pack_value = adj_item.pack_value,
                                         expiry_date = adj_item.expiry_date,
                                         quantity = adj_item.new_quantity,
                                        )
            # and add the inventory item id to the adjustment record
            db(aitable.id == adj_item.id).update(inv_item_id = stock_id)
        # otherwise copy the details to the stock item
        else:
            db(stocktable.id == adj_item.inv_item_id).update(item_pack_id = adj_item.item_pack_id,
                                                             bin = adj_item.bin,
                                                             pack_value = adj_item.pack_value,
                                                             expiry_date = adj_item.expiry_date,
                                                             quantity = adj_item.new_quantity,
                                                            )
    # Change the status of the adj record to Complete
    db(atable.id == adj_id).update(status=1)
    # Go to the Inventory of the Site which has adjusted these items
    (prefix, resourcename, id) = s3mgr.model.get_instance(s3db.org_site,
                                                          adj_rec.site_id)
    query = (otable.id == id)
    otype = db(query).select(otable.type, limitby = (0, 1)).first()
    if otype and otype.type == 5:
        url = URL(c = "inv",
                 f = "warehouse",
                 args = [id, "inv_item"])
    else:
        url = URL(c = "org",
                 f = "office",
                 args = [id, "inv_item"])
    redirect(url)

# =============================================================================
def recv_item_json():
    """
    """

    stable = s3db.org_site
    rtable = s3db.inv_recv
    ittable = s3db.inv_track_item

    rtable.date.represent = lambda dt: dt[:10]

    query = (ittable.req_item_id == request.args[0]) & \
            (rtable.id == ittable.recv_id) & \
            (rtable.site_id == stable.id) & \
            (rtable.status == eden.inv.inv_ship_status["RECEIVED"]) & \
            (ittable.deleted == False )
    records = db(query).select(rtable.id,
                               rtable.date,
                               stable.name,
                               ittable.quantity)

    json_str = "[%s,%s" % ( json.dumps(dict(id = str(T("Received")),
                                            quantity = "#"
                                            )) ,
                            records.json()[1:])

    response.headers["Content-Type"] = "application/json"
    return json_str

# =============================================================================
def send_item_json():
    """
    """

    stable = s3db.org_site
    istable = s3db.inv_send
    ittable = s3db.inv_track_item

    istable.date.represent = lambda dt: dt[:10]

    query = (ittable.req_item_id == request.args[0]) & \
            (istable.id == ittable.send_id) & \
            (istable.site_id == stable.id) & \
            ((istable.status == eden.inv.inv_ship_status["SENT"]) | \
             (istable.status == eden.inv.inv_ship_status["RECEIVED"])) & \
            (ittable.deleted == False)
    records =  db(query).select(istable.id,
                                istable.date,
                                stable.name,
                                ittable.quantity)

    json_str = "[%s,%s" % ( json.dumps(dict(id = str(T("Sent")),
                                            quantity = "#"
                                            )) ,
                            records.json()[1:])

    response.headers["Content-Type"] = "application/json"
    return json_str

# END =========================================================================
