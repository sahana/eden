# -*- coding: utf-8 -*-

"""
    Inventory Management

    A module to record inventories of items at a locations (sites),
    including Warehouses, Offices, Shelters & Hospitals
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return settings.customise_home(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the Warehouse Summary View
    s3_redirect_default(URL(f="warehouse", args="summary"))

# -----------------------------------------------------------------------------
def index2():
    """
        Alternative Application Home page
        - custom View
    """

    # Need CRUD String
    table = s3db.table("cr_shelter", None)

    module_name = settings.modules[module].name_nice
    response.title = module_name
    response.view = "inv/index.html"
    if s3.debug:
        # Start of TEST CODE for multiple dataTables,
        #this also required views/inv/index.html to be modified
        from s3.s3data import S3DataTable
        representation = request.extension
        if representation == "html" or get_vars.id == "warehouse_list_1":
            resource = s3db.resource("inv_warehouse")
            totalrows = resource.count()
            list_fields = ["id",
                           "name",
                           "organisation_id",
                           ]
            orderby = "inv_warehouse.name asc"
            if representation == "aadata":
                query, orderby, left = resource.datatable_filter(list_fields, get_vars)
                if orderby is None:
                    orderby = default_orderby
            start = int(get_vars.displayStart) if get_vars.displayStart else 0
            limit = int(get_vars.pageLength) if get_vars.pageLength else s3.ROWSPERPAGE
            data = resource.select(list_fields,
                                   start=start,
                                   limit=limit,
                                   orderby=orderby,
                                   count=True,
                                   represent=True)
            filteredrows = data["numrows"]
            if totalrows is None:
                totalrows = filteredrows
            rfields = data["rfields"]
            rows = data["rows"]
            dt = S3DataTable(rfields, rows)
            dt.defaultActionButtons(resource)
            if representation == "html":
                warehouses = dt.html(totalrows,
                                     filteredrows,
                                     "warehouse_list_1",
                                     dt_ajax_url=URL(c="inv",
                                                  f="index2",
                                                  extension="aadata",
                                                  vars={"id":"warehouse_list_1"},
                                                  ),
                                     dt_group=2,
                                     dt_searching="true",
                                     )
            else:
                warehouse = dt.json(totalrows,
                                    filteredrows,
                                    "warehouse_list_1",
                                    int(get_vars.draw),
                                    )
                return warehouse
        # Second Table
        if representation == "html" or get_vars.id == "inventory_list_1":
            if "Adjust" in request.post_vars:
                if request.post_vars.selected == "":
                    inventory = "Well you could have selected something :("
                else:
                    inventory = "Adjustment not currently supported... :-) you selected the following items: %s" % request.post_vars.selected
            else:
                resource = s3db.resource("inv_inv_item")
                totalrows = resource.count()
                table = resource.table
                stable = s3db.supply_item
                list_fields = ["id",
                               "site_id",
                               "item_id$name",
                               "quantity",
                               "pack_value",
                               "total_value",
                               ]
                orderby = "inv_inv_item.site_id asc"
                if representation == "aadata":
                    query, orderby, left = resource.datatable_filter(list_fields, get_vars)
                    if orderby is None:
                        orderby = default_orderby
                site_list = {}
                data = resource.select(list_fields,
                                       limit=None,
                                       orderby=orderby,
                                       count=True)
                filteredrows = data["numrows"]
                if totalrows is None:
                    totalrows = filteredrows
                rows = data["rows"]
                for row in rows:
                    site_id = row["inv_inv_item.site_id"]
                    if site_id not in site_list:
                        site_list[site_id] = 1
                    else:
                        site_list[site_id] += 1
                formatted_site_list = {}
                repr = table.site_id.represent
                for (key,value) in site_list.items():
                    formatted_site_list[str(repr(key))] = value
                if isinstance(orderby, bool):
                    orderby = [table.site_id, stable.name, ~table.quantity]
                start = int(get_vars.displayStart) if get_vars.displayStart else 0
                limit = int(get_vars.pageLength) if get_vars.pageLength else s3.ROWSPERPAGE
                data = resource.select(list_fields,
                                       orderby=orderby,
                                       start=start,
                                       limit=limit,
                                       represent=True)
                rfields = data["rfields"]
                rows = data["rows"]
                dt = S3DataTable(rfields,
                                 rows,
                                 orderby=orderby,
                                 )
                custom_actions = [dict(label=str(T("Warehouse")),
                                  _class="action-icon",
                                  img="/%s/static/img/markers/gis_marker.image.Agri_Commercial_Food_Distribution_Center_S1.png" % appname,
                                  url=URL(c="inv", f="warehouse",
                                          args=["[id]", "update"]
                                          )
                                  ),
                                 ]
                dt.defaultActionButtons(resource, custom_actions)
                if representation == "html":
                    rows = current.db(table.quantity<100.0).select(table.id, table.quantity)
                    errorList = []
                    warningList = []
                    alertList = []
                    for row in rows:
                        if row.quantity < 0.0:
                            errorList.append(row.id)
                        elif row.quantity == 0.0:
                            warningList.append(row.id)
                        else:
                            alertList.append(row.id)
                    inventory = dt.html(totalrows,
                                        filteredrows,
                                        "inventory_list_1",
                                        dt_action_col=-1,
                                        dt_ajax_url=URL(c="inv",
                                                     f="index2",
                                                     extension="aadata",
                                                     vars={"id":"inventory_list_1"},
                                                     ),
                                        dt_bulk_actions = "Adjust",
                                        dt_group=[1,2],
                                        dt_group_totals=[formatted_site_list],
                                        dt_searching="true",
                                        dt_styles = {"dtdisable": errorList,
                                                     "dtwarning": warningList,
                                                     "dtalert": alertList,
                                                     },
                                        #dt_text_maximum_len = 10,
                                        #dt_text_condense_len = 8,
                                        #dt_group_space = True,
                                        dt_shrink_groups = "accordion",
                                        #dt_shrink_groups = "individual",
                                        )

                    s3.actions = None
                elif representation == "aadata":
                    inventory = dt.json(totalrows,
                                        filteredrows,
                                        "inventory_list_1",
                                        int(get_vars.draw),
                                        dt_action_col=-1,
                                        dt_bulk_actions = "Adjust",
                                        dt_group_totals=[formatted_site_list],
                                        )
                    return inventory
                else:
                    # Probably not the way to do it.... but
                    s3db.configure("inv_inv_item",
                                   list_fields=list_fields,
                                   report_groupby="site_id",
                                   pdf_groupby="site_id",
                                   )
                    s3.filter = filter
                    r = s3_request("inv", "inv_item",
                                   vars={"orderby" : orderby})
                    r.resource = resource
                    output = r(
                               pdf_groupby='site_id',
                               dt_group=1,
                               )
                    return output
        # Third table
        if representation == "html" or get_vars.id == "supply_list_1":
            resource = s3db.resource("supply_item")
            list_fields = ["id",
                           "name",
                           "um",
                           "model",
                           ]
            orderby = "inv_inv_item.site_id asc"
            if representation == "aadata":
                query, orderby, left = resource.datatable_filter(list_fields, get_vars)
                if orderby is None:
                    orderby = default_orderby
            data = resource.select(list_fields,
                                   limit=None,
                                   orderby=orderby,
                                   count=True,
                                   represent=True)
            rows = data["rows"]
            rfields = data["rfields"]
            numrows = data["numrows"]
            dt = S3DataTable(rfields, rows)
            dt.defaultActionButtons(resource)
            if representation == "html":
                supply_items = dt.html(numrows,
                                       numrows,
                                       "supply_list_1",
                                       dt_action_col=1,
                                       dt_ajax_url=URL(c="inv",
                                                       f="index2",
                                                       extension="aadata",
                                                       vars={"id": "supply_list_1"},
                                                       ),
                                       dt_pageLength=10,
                                       )
            else:
                supply_items = dt.json(numrows,
                                       numrows,
                                       "supply_list_1",
                                       int(get_vars.draw),
                                       dt_action_col=1,
                                       )
                return supply_items
        r = s3_request(prefix = "inv", name = "inv_item")
        return dict(module_name=module_name,
                    warehouses = warehouses,
                    inventory = inventory,
                    supply_items = supply_items,
                    r = r,
                    )
        # End of TEST CODE
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def warehouse():
    """
        RESTful CRUD controller
    """

    request_args = request.args
    if "viewing" in get_vars:
        viewing = get_vars.viewing
        tn, id = viewing.split(".", 1)
        if tn == "inv_warehouse":
            request_args.insert(0, id)

    # CRUD pre-process
    def prep(r):

        if r.component:
            component_name = r.component_name
            if component_name == "inv_item":
                # Filter out items which are already in this inventory
                s3db.inv_prep(r)
                # Remove the Warehouse Name from the list_fields
                list_fields = s3db.get_config("inv_inv_item", "list_fields")
                try:
                    list_fields.remove("site_id")
                    s3db.configure("inv_inv_item",
                                   list_fields = list_fields,
                                   )
                except:
                    pass

            elif component_name == "recv":
                # Filter out items which are already in this inventory
                s3db.inv_prep(r)

                # Configure which fields in inv_recv are readable/writable
                # depending on status
                recvtable = s3db.inv_recv
                if r.component_id:
                    record = db(recvtable.id == r.component_id).select(recvtable.status,
                                                                       limitby=(0, 1)
                                                                       ).first()
                    set_recv_attr(record.status)
                else:
                    set_recv_attr(s3db.inv_ship_status["IN_PROCESS"])
                    recvtable.recv_ref.readable = False
                    if r.method and r.method != "read":
                        # Don't want to see in Create forms
                        recvtable.status.readable = False

            elif component_name == "send":
                # Filter out items which are already in this inventory
                s3db.inv_prep(r)

            elif component_name == "human_resource":
                s3db.org_site_staff_config(r)

            elif component_name == "req":
                s3db.req_prep(r)
                if r.method != "update" and r.method != "read":
                    # Hide fields which don't make sense in a Create form
                    # inc list_create (list_fields over-rides)
                    s3db.req_create_form_mods()

            elif component_name == "asset":
                # Default/Hide the Organisation & Site fields
                record = r.record
                atable = s3db.asset_asset
                field = atable.organisation_id
                field.default = record.organisation_id
                field.readable = field.writable = False
                field = atable.site_id
                field.default = record.site_id
                field.readable = field.writable = False
                # Stay within Warehouse tab
                s3db.configure("asset_asset",
                               create_next = None,
                               )

        elif r.id:
            r.table.obsolete.readable = r.table.obsolete.writable = True

        # "show_obsolete" var option can be added (btn?) later to
        # disable this filter
        if r.method in [None, "list"] and \
            not r.vars.get("show_obsolete", False):
            r.resource.add_filter(db.inv_warehouse.obsolete != True)

        if r.representation == "xls":
            list_fields = r.resource.get_config("list_fields")
            list_fields += ["location_id$lat",
                            "location_id$lon",
                            "location_id$inherited",
                            ]

        return True
    s3.prep = prep

    # CRUD post-process
    def postp(r, output):
        if r.interactive and not r.component and r.method != "import":
            if auth.s3_has_permission("read", "inv_inv_item"):
                # Change Action buttons to open Stock Tab by default
                read_url = URL(f="warehouse", args=["[id]", "inv_item"])
                update_url = URL(f="warehouse", args=["[id]", "inv_item"])
                s3_action_buttons(r,
                                  read_url = read_url,
                                  update_url = update_url)
        else:
            cname = r.component_name
            if cname == "human_resource":
                # Modify action button to open staff instead of human_resource
                read_url = URL(c="hrm", f="staff", args=["[id]"])
                update_url = URL(c="hrm", f="staff", args=["[id]", "update"])
                s3_action_buttons(r, read_url = read_url,
                                  #delete_url = delete_url,
                                  update_url = update_url)

        if "add_btn" in output:
            del output["add_btn"]
        return output
    s3.postp = postp

    if "extra_data" in get_vars:
        resourcename = "inv_item"
    else:
        resourcename = "warehouse"
    csv_stylesheet = "%s.xsl" % resourcename

    if len(request_args) > 1 and request_args[1] in ("req", "send", "recv"):
        # Sends/Receives should break out of Component Tabs
        # To allow access to action buttons in inv_recv rheader
        native = True
    else:
        native = False

    output = s3_rest_controller(module, resourcename,
                                #hide_filter = {"inv_item": False,
                                #               "_default": True,
                                #               },
                                # Extra fields for CSV uploads:
                                #csv_extra_fields = [
                                #         dict(label="Organisation",
                                #         field=s3db.org_organisation_id(comment=None))
                                #]
                                csv_stylesheet = csv_stylesheet,
                                csv_template = resourcename,
                                native = native,
                                rheader = s3db.inv_rheader,
                                )
    return output

# -----------------------------------------------------------------------------
def warehouse_type():
    """
        RESTful CRUD controller
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def supplier():
    """
        Filtered version of the organisation() REST controller
    """

    get_vars["organisation_type.name"] = "Supplier"

    # Load model (including normal CRUD strings)
    table = s3db.org_organisation

    # Modify CRUD Strings
    s3.crud_strings.org_organisation = Storage(
        label_create = T("Create Supplier"),
        title_display = T("Supplier Details"),
        title_list = T("Suppliers"),
        title_update = T("Edit Supplier"),
        title_upload = T("Import Suppliers"),
        label_list_button = T("List Suppliers"),
        label_delete_button = T("Delete Supplier"),
        msg_record_created = T("Supplier added"),
        msg_record_modified = T("Supplier updated"),
        msg_record_deleted = T("Supplier deleted"),
        msg_list_empty = T("No Suppliers currently registered")
        )


    # Open record in this controller after creation
    s3db.configure("org_organisation",
                   create_next = URL(c="inv", f="supplier",
                                     args = ["[id]", "read"]),
                   )

    return s3db.org_organisation_controller()

# =============================================================================
def inv_item():
    """ REST Controller """

    # If this url has a viewing track items then redirect to track_movement
    viewing = get_vars.get("viewing", None)
    if viewing:
        tn, id = viewing.split(".", 1)
        if tn == "inv_track_item":
            table = s3db.inv_track_item
            record = db(table.id == id).select(table.item_id,
                                               limitby=(0, 1)).first()
            redirect(URL(c = "inv",
                         f = "track_movement",
                         args = [],
                         vars = {"viewing" : "%s.%s" % ("inv_inv_item", record.item_id)}
                         ))

    tablename = "inv_inv_item"
    # Load model to be able to override CRUD string(s)
    table = s3db[tablename]

    # Limit site_id to sites the user has permissions for
    auth.permitted_facilities(table=table,
                              error_msg=T("You do not have permission for any site to add an inventory item."))

    s3.crud_strings[tablename].msg_list_empty = T("No Stock currently registered")

    report = get_vars.get("report")
    if report == "mon":
            s3.crud_strings[tablename].update(dict(
                title_list = T("Monetization Report"),
                subtitle_list = T("Monetization Details"),
                #msg_list_empty = T("No Stock currently registered"),
              ))
            s3db.configure(tablename,
                           list_fields = ["id",
                                          (T("Donor"), "supply_org_id"),
                                          (T("Items/Description"), "item_id"),
                                          (T("Quantity"), "quantity"),
                                          (T("Unit"), "item_pack_id"),
                                          (T("Unit Value"), "pack_value"),
                                          (T("Total Value"), "total_value"),
                                          (T("Remarks"), "comments"),
                                          "status",
                                          ]
                           )
    else:
        s3db.configure(tablename,
                       insertable = settings.get_inv_direct_stock_edits(),
                       list_fields = ["id",
                                      "site_id",
                                      "item_id",
                                      "item_id$code",
                                      "item_id$item_category_id",
                                      "quantity",
                                      "pack_value",
                                      #(T("Total Value"), "total_value"),
                                      ]
                       )

    if len(request.args) > 1 and request.args[1] == "track_item":
        # remove CRUD generated buttons in the tabs
        s3db.configure("inv_track_item",
                       create=False,
                       listadd=False,
                       editable=False,
                       deletable=False,
                       )
    else:
        s3.filter = (table.quantity != 0)

    def prep(r):
        if r.method != "report":
            s3.dataTable_group = 1
        return True
    s3.prep = prep

    # Import pre-process
    def import_prep(data):
        """
            Deletes all Stock records of the organisation/branch
            before processing a new data import
        """
        resource, tree = data
        xml = current.xml
        tag = xml.TAG
        att = xml.ATTRIBUTE
        if s3.importerReplace:
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
                            org_name = json.loads(xml.xml_decode(org_name))
                        except:
                            pass
                    if org_name:
                        query = (otable.name == org_name) & \
                                (stable.organisation_id == otable.id) & \
                                (itable.site_id == stable.id)
                        resource = s3db.resource("inv_inv_item", filter=query)
                        # Use cascade=True so that the deletion gets
                        # rolled back if the import fails:
                        resource.delete(format="xml", cascade=True)
            resource.skip_import = True
    s3.import_prep = import_prep
    # Upload for configuration (add replace option)
    s3.importerPrep = lambda: dict(ReplaceOption=T("Remove existing data before import"))

    output = s3_rest_controller(#csv_extra_fields = [dict(label="Organisation",
                                #                         field=s3db.org_organisation_id(comment=None))
                                #                    ],
                                pdf_orientation = "Landscape",
                                pdf_table_autogrow = "B",
                                pdf_groupby = "site_id, item_id",
                                pdf_orderby = "expiry_date, supply_org_id",
                                rheader=s3db.inv_rheader,
                                )

    if "add_btn" in output and not settings.get_inv_direct_stock_edits():
        del output["add_btn"]

    return output

# -----------------------------------------------------------------------------
def track_movement():
    """ REST Controller """

    table = s3db.inv_track_item

    s3db.configure("inv_track_item",
                   create = False,
                   deletable = False,
                   editable = False,
                   listadd = False,
                   )

    def prep(r):
        if r.interactive:
            if "viewing" in get_vars:
                dummy, item_id = get_vars.viewing.split(".")
                if item_id != "None":
                    query = (table.send_inv_item_id == item_id ) | \
                            (table.recv_inv_item_id == item_id)
                    r.resource.add_filter(query)
        return True
    s3.prep = prep

    output = s3_rest_controller("inv", "track_item",
                                rheader = s3db.inv_rheader,
                                )
    if "add_btn" in output:
        del output["add_btn"]

    return output

# -----------------------------------------------------------------------------
def inv_item_quantity():
    """


        Access via the .json representation to avoid work rendering menus, etc
    """

    try:
        item_id = request.args[0]
    except:
        raise HTTP(400, current.xml.json_message(False, 400, "No value provided!"))

    table = s3db.inv_inv_item
    ptable = db.supply_item_pack
    query = (table.id == item_id) & \
            (table.item_pack_id == ptable.id)
    record = db(query).select(table.quantity,
                              ptable.quantity,
                              limitby=(0, 1)).first()

    d = {"iquantity" : record.inv_inv_item.quantity,
         "pquantity" : record.supply_item_pack.quantity,
         }
    output = json.dumps(d)

    response.headers["Content-Type"] = "application/json"
    return output

# -----------------------------------------------------------------------------
def inv_item_packs():
    """
        Called by S3OptionsFilter to provide the pack options for a
            particular Item

        Access via the .json representation to avoid work rendering menus, etc
    """

    try:
        item_id = request.args[0]
    except:
        raise HTTP(400, current.xml.json_message(False, 400, "No value provided!"))

    table = s3db.inv_inv_item
    ptable = db.supply_item_pack
    query = (table.id == item_id) & \
            (table.item_id == ptable.item_id)
    records = db(query).select(ptable.id,
                               ptable.name,
                               ptable.quantity)
    output = records.json()

    response.headers["Content-Type"] = "application/json"
    return output

# =============================================================================
def send():
    """ RESTful CRUD controller """

    return s3db.inv_send_controller()

# ==============================================================================
def send_commit():
    """
        Send a Shipment containing all items in a Commitment
    """

    return s3db.req_send_commit()

# -----------------------------------------------------------------------------
def send_process():
    """ Process a Shipment """

    return s3db.inv_send_process()

# -----------------------------------------------------------------------------
def send_returns():
    """
        This will cancel a shipment that has been sent

        @todo need to roll back commitments
    """

    try:
        send_id = request.args[0]
    except:
        redirect(f="send")

    stable = s3db.inv_send
    if not auth.s3_has_permission("update", stable, record_id=send_id):
        session.error = T("You do not have permission to return this sent shipment.")

    send_record = db(stable.id == send_id).select(stable.status,
                                                  limitby=(0, 1)
                                                  ).first()
    inv_ship_status = s3db.inv_ship_status
    if send_record.status == inv_ship_status["IN_PROCESS"]:
        session.error = T("This shipment has not been sent - it cannot be returned because it can still be edited.")

    if session.error:
        redirect(URL(c="inv", f="send",
                     args=[send_id]))

    rtable = s3db.inv_recv
    tracktable = s3db.inv_track_item

    # Okay no error so far, change the status to Returning
    ADMIN = auth.get_system_roles().ADMIN
    stable[send_id] = dict(status = inv_ship_status["RETURNING"],
                           owned_by_user = None,
                           owned_by_group = ADMIN)
    recv_row = db(tracktable.send_id == send_id).select(tracktable.recv_id,
                                                        limitby = (0, 1)).first()
    if recv_row:
        recv_id = recv_row.recv_id
        rtable[recv_id] = dict(date = request.utcnow,
                               status = inv_ship_status["RETURNING"],
                               owned_by_user = None,
                               owned_by_group = ADMIN)
    # Set all track items to status of returning
    db(tracktable.send_id == send_id).update(status = s3db.inv_tracking_status["RETURNING"])
    session.confirmation = T("Sent Shipment has returned, indicate how many items will be returned to Warehouse.")

    redirect(URL(c="inv", f="send",
                 args=[send_id, "track_item"]))

# -----------------------------------------------------------------------------
def return_process():
    """
        Return some stock from a shipment back into the warehouse
    """

    try:
        send_id = request.args[0]
    except:
        redirect(f="send")

    stable = s3db.inv_send
    if not auth.s3_has_permission("update", stable, record_id=send_id):
        session.error = T("You do not have permission to return this sent shipment.")

    send_record = db(stable.id == send_id).select(stable.status,
                                                  limitby=(0, 1)
                                                  ).first()
    inv_ship_status = s3db.inv_ship_status
    if send_record.status != inv_ship_status["RETURNING"]:
        session.error = T("This shipment has not been returned.")

    if session.error:
        redirect(URL(c="inv", f="send",
                     args=[send_id]))

    invtable = s3db.inv_inv_item
    rtable = s3db.inv_recv
    tracktable = s3db.inv_track_item

    # Okay no error so far, let's move the goods back into the warehouse
    # and then change the status to received
    # Update Receive record & lock for editing
    # Move each item to the site
    track_rows = db(tracktable.send_id == send_id).select(tracktable.id,
                                                          tracktable.quantity,
                                                          tracktable.return_quantity,
                                                          tracktable.send_inv_item_id,
                                                          )
    for track_item in track_rows:
        send_inv_id = track_item.send_inv_item_id
        return_qnty = track_item.return_quantity
        if return_qnty == None:
            return_qnty = 0
        # update the receive quantity in the tracking record
        tracktable[track_item.id] = dict(recv_quantity = track_item.quantity - return_qnty)
        if return_qnty:
            db(invtable.id == send_inv_id).update(quantity = invtable.quantity + return_qnty)

    ADMIN = auth.get_system_roles().ADMIN
    stable[send_id] = dict(status = inv_ship_status["RECEIVED"],
                           owned_by_user = None,
                           owned_by_group = ADMIN)
    recv_row = db(tracktable.send_id == send_id).select(tracktable.recv_id,
                                                        limitby = (0, 1)).first()
    if recv_row:
        recv_id = recv_row.recv_id
        rtable[recv_id] = dict(date = request.utcnow,
                               status = inv_ship_status["RECEIVED"],
                               owned_by_user = None,
                               owned_by_group = ADMIN)

    # Change the status for all track items in this shipment to Received
    db(tracktable.send_id == send_id).update(status = s3db.inv_tracking_status["RECEIVED"])

    redirect(URL(f = "send",
                 args = [send_id]))

# -----------------------------------------------------------------------------
def send_cancel():
    """
        This will cancel a shipment that has been sent

        @todo need to roll back commitments
    """

    try:
        send_id = request.args[0]
    except:
        redirect(f="send")

    stable = s3db.inv_send
    if not auth.s3_has_permission("delete", stable, record_id=send_id):
        session.error = T("You do not have permission to cancel this sent shipment.")

    send_record = db(stable.id == send_id).select(stable.status,
                                                  limitby=(0, 1)).first()

    inv_ship_status = s3db.inv_ship_status
    if send_record.status != inv_ship_status["SENT"]:
        session.error = T("This shipment has not been sent - it has NOT been canceled because it can still be edited.")

    if session.error:
        redirect(URL(c="inv", f="send",
                     args=[send_id]))

    rtable = s3db.inv_recv
    tracktable = s3db.inv_track_item

    # Okay no error so far, let's delete that baby
    # Change the send and recv status to cancelled
    ADMIN = auth.get_system_roles().ADMIN
    db(stable.id == send_id).update(status = inv_ship_status["CANCEL"],
                                    owned_by_user = None,
                                    owned_by_group = ADMIN)
    recv_row = db(tracktable.send_id == send_id).select(tracktable.recv_id,
                                                        limitby = (0, 1)).first()
    if recv_row:
        recv_id = recv_row.recv_id
        db(rtable.id == recv_id).update(date = request.utcnow,
                                        status = inv_ship_status["CANCEL"],
                                        owned_by_user = None,
                                        owned_by_group = ADMIN)


    # Change the track items status to canceled and then delete them
    # If they are linked to a request then the in transit total will also be reduced
    # Records can only be deleted if the status is In Process (or preparing)
    # so change the status before we delete
    tracking_status = s3db.inv_tracking_status
    db(tracktable.send_id == send_id).update(status = tracking_status["IN_PROCESS"])
    track_rows = db(tracktable.send_id == send_id).select(tracktable.id)
    for track_item in track_rows:
        s3db.inv_track_item_deleting(track_item.id)
    # Now change the status to (cancelled)
    db(tracktable.send_id == send_id).update(status = tracking_status["CANCEL"])

    session.confirmation = T("Sent Shipment canceled and items returned to Warehouse")

    redirect(URL(f = "send",
                 args = [send_id]))

# =============================================================================
def set_recv_attr(status):
    """
        Set field attributes for inv_recv table
    """

    recvtable = s3db.inv_recv
    ship_status = s3db.inv_ship_status
    recvtable.sender_id.readable = recvtable.sender_id.writable = False
    recvtable.grn_status.readable = recvtable.grn_status.writable = False
    recvtable.cert_status.readable = recvtable.cert_status.writable = False
    recvtable.eta.readable = False
    recvtable.req_ref.writable = True
    if status == ship_status["IN_PROCESS"]:
        recvtable.send_ref.writable = True
        recvtable.recv_ref.readable = False
        recvtable.sender_id.readable = False
    else:
        # Make all fields writable False
        for field in recvtable.fields:
            recvtable[field].writable = False
    if status == ship_status["SENT"]:
        recvtable.date.writable = True
        recvtable.recipient_id.readable = recvtable.recipient_id.writable = True
        recvtable.comments.writable = True

# -----------------------------------------------------------------------------
def recv():
    """ RESTful CRUD controller """

    recvtable = s3db.inv_recv

    # Limit site_id to sites the user has permissions for
    if settings.get_inv_shipment_name() == "order":
        error_msg = T("You do not have permission for any facility to add an order.")
    else:
        error_msg = T("You do not have permission for any facility to receive a shipment.")
    auth.permitted_facilities(table=recvtable, error_msg=error_msg)

    tracktable = s3db.inv_track_item
    atable = s3db.inv_adj_item

    # The inv_recv record might be created when the shipment is send and so it
    # might not have the recipient identified. If it is null then set it to
    # the person who is logged in (the default)
    id = request.args(0)
    if id and isinstance(id, int):
        record = db(recvtable.id == id).select(recvtable.recipient_id,
                                               limitby=(0, 1)).first()
        try:
            if record.recipient_id is None:
                db(recvtable.id == id).update(recipient_id = auth.s3_logged_in_person())
        except:
            pass

    status = s3db.inv_ship_status
    SHIP_STATUS_IN_PROCESS = status["IN_PROCESS"]
    SHIP_STATUS_SENT = status["SENT"]
    SHIP_STATUS_RECEIVED = status["RECEIVED"]
    SHIP_STATUS_CANCEL = status["CANCEL"]

    status = s3db.inv_tracking_status
    TRACK_STATUS_UNKNOWN    = status["UNKNOWN"]
    TRACK_STATUS_PREPARING  = status["IN_PROCESS"]
    TRACK_STATUS_TRANSIT    = status["SENT"]
    TRACK_STATUS_UNLOADING  = status["UNLOADING"]
    TRACK_STATUS_ARRIVED    = status["RECEIVED"]
    TRACK_STATUS_CANCELED   = status["CANCEL"]

    def set_track_attr(status):
        # By default Make all fields writable False
        for field in tracktable.fields:
            tracktable[field].writable = False
        # Hide some fields
        tracktable.send_id.readable = False
        tracktable.recv_id.readable = False
        tracktable.bin.readable = False
        tracktable.adj_item_id.readable = False
        tracktable.recv_quantity.readable = True
        if status == TRACK_STATUS_PREPARING:
            # Show some fields
            tracktable.item_source_no.writable = True
            tracktable.item_id.writable = True
            tracktable.item_pack_id.writable = True
            tracktable.quantity.writable = True
            tracktable.currency.writable = True
            tracktable.pack_value.writable = True
            tracktable.expiry_date.writable = True
            tracktable.recv_bin.writable = True
            tracktable.owner_org_id.writable = True
            tracktable.supply_org_id.writable = True
            tracktable.inv_item_status.writable = True
            tracktable.comments.writable = True
            tracktable.recv_quantity.readable = False
            # Hide some fields
            tracktable.send_inv_item_id.readable = False
            # Change some labels - NO - use consistent labels
            #tracktable.quantity.label = T("Quantity Delivered")
            tracktable.recv_bin.label = T("Bin")
        elif status == TRACK_STATUS_TRANSIT:
            # Hide the values that will be copied from the inv_inv_item record
            tracktable.send_inv_item_id.readable = False
            tracktable.send_inv_item_id.writable = False
            tracktable.item_source_no.readable = True
            tracktable.item_source_no.writable = False
            # Display the values that can only be entered on create
            tracktable.recv_quantity.writable = True
            tracktable.recv_bin.readable = True
            tracktable.recv_bin.writable = True
            tracktable.comments.writable = True
            # This is a received purchase so change the label to reflect this - NO - use consistent labels
            #tracktable.quantity.label =  T("Quantity Delivered")
        elif status == TRACK_STATUS_ARRIVED:
            tracktable.item_source_no.readable = True
            tracktable.item_source_no.writable = False
            tracktable.item_id.writable = False
            tracktable.send_inv_item_id.writable = False
            tracktable.item_pack_id.writable = False
            tracktable.quantity.writable = False
            tracktable.currency.writable = False
            tracktable.pack_value.writable = False
            tracktable.expiry_date.writable = False
            tracktable.owner_org_id.writable = False
            tracktable.supply_org_id.writable = False
            tracktable.recv_bin.readable = True
            tracktable.recv_bin.writable = True

    def prep(r):
        record = r.record
        if record and \
           record.status not in (SHIP_STATUS_IN_PROCESS, SHIP_STATUS_SENT):
            # Now that the shipment has been sent
            # lock the record so that it can't be meddled with
            s3db.configure("inv_recv",
                           create = False,
                           deletable = False,
                           editable = False,
                           listadd = False,
                           )
        component = r.component
        if record and component and component.name == "track_item":
            # Can only create or delete track items for a recv record
            # if the status is preparing:
            if r.method == "create" or r.method == "delete":
                if record.status != SHIP_STATUS_IN_PROCESS:
                    return False

            # Configure which fields in track_item are readable/writable
            # depending on status:
            if r.component_id:
                track_record = db(tracktable.id == r.component_id).select(tracktable.status,
                                                                          limitby=(0, 1)
                                                                          ).first()
                set_track_attr(track_record.status)
            else:
                set_track_attr(TRACK_STATUS_PREPARING)
                tracktable.status.readable = False

            # Adjust CRUD strings
            if record.status == SHIP_STATUS_IN_PROCESS:
                s3.crud_strings.inv_recv.title_update = \
                s3.crud_strings.inv_recv.title_display = T("Process Received Shipment")

            # Default the Supplier/Donor to the Org sending the shipment
            tracktable.supply_org_id.default = record.organisation_id
        else:
            # Configure which fields in inv_recv are readable/writable
            # depending on status
            if r.id:
                record = db(recvtable.id == r.id).select(recvtable.status,
                                                         limitby=(0, 1)
                                                         ).first()
                set_recv_attr(record.status)
            else:
                set_recv_attr(SHIP_STATUS_IN_PROCESS)
                recvtable.recv_ref.readable = False
                if r.method and r.method != "read":
                    # Don't want to see in Create forms
                    recvtable.status.readable = False
        return True
    s3.prep = prep

    if len(request.args) > 1 and request.args[1] == "track_item":
        record = db(recvtable.id == request.args[0]).select(recvtable.status,
                                                            limitby=(0, 1)
                                                            ).first()
        status = record.status if record else None
        if status == SHIP_STATUS_SENT:
            list_fields = ["id",
                           "status",
                           "item_id",
                           "item_pack_id",
                           "quantity",
                           "currency",
                           "pack_value",
                           "recv_quantity",
                           "recv_bin",
                           "owner_org_id",
                           "supply_org_id",
                           ]
            s3db.configure("inv_track_item",
                           # Remove CRUD generated buttons in the tabs
                           create = False,
                           deletable = False,
                           editable = True,
                           listadd = False,
                           list_fields = list_fields,
                           )
        elif status:
            # Remove CRUD generated buttons in the tabs
            s3db.configure("inv_track_item",
                           create = False,
                           deletable = False,
                           editable = False,
                           listadd = False,
                           )

    output = s3_rest_controller(rheader = s3db.inv_recv_rheader,
                                )
    return output

# -----------------------------------------------------------------------------
def req_items_for_inv(site_id, quantity_type):
    """
        Used by recv_process & send_process
        returns a dict of unique req items (with min  db.req_req.date_required | db.req_req.date)
        key = item_id
        @param site_id: The inventory to find the req_items from
        @param quantity_type: str ("commit", "transit" or "fulfil) The
                              quantity type which will be used to determine if this item is still outstanding
    """

    if not settings.has_module("req"):
        return Storage()

    table = s3db.req_req
    itable = s3db.req_req_item
    query = (table.site_id == site_id) & \
            (table.id == itable.req_id) & \
            (itable.item_pack_id == itable.item_pack_id) & \
            (itable["quantity_%s" % quantity_type] < itable.quantity) & \
            (table.cancel == False) & \
            (table.deleted == False) & \
            (itable.deleted == False)
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
def req_item_in_shipment(shipment_item,
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

    try:
        recv_id = long(request.args[0])
    except (IndexError, ValueError):
        # recv_id missing from URL or invalid
        redirect(URL(f="recv"))

    rtable = s3db.inv_recv

    if not auth.s3_has_permission("update", rtable, record_id=recv_id):
        session.error = T("You do not have permission to receive this shipment.")
        redirect(URL(c="inv", f="recv", args=[recv_id]))

    recv_record = db(rtable.id == recv_id).select(rtable.date,
                                                  rtable.status,
                                                  rtable.site_id,
                                                  rtable.recv_ref,
                                                  limitby=(0, 1),
                                                  ).first()

    # Check status
    status = recv_record.status
    inv_ship_status = s3db.inv_ship_status
    if status == inv_ship_status["RECEIVED"]:
        session.error = T("This shipment has already been received.")
        redirect(URL(c="inv", f="recv", args=[recv_id]))

    elif status == inv_ship_status["CANCEL"]:
        session.error = T("This shipment has already been received & subsequently canceled.")
        redirect(URL(c="inv", f="recv", args=[recv_id]))

    # Update Receive record & lock for editing
    ADMIN = auth.get_system_roles().ADMIN
    data = {"status": inv_ship_status["RECEIVED"],
            "owned_by_user": None,
            "owned_by_group": ADMIN,
            }

    if not recv_record.recv_ref:
        # No recv_ref yet? => add one now
        code = s3db.supply_get_shipping_code(settings.get_inv_recv_shortname(),
                                             recv_record.site_id,
                                             s3db.inv_recv.recv_ref,
                                             )
        data["recv_ref"] = code

    if not recv_record.date:
        # Date not set? => set to now
        data["date"] = request.utcnow

    db(rtable.id == recv_id).update(**data)

    # Update the Send record & lock for editing
    stable = db.inv_send
    tracktable = db.inv_track_item
    send_row = db(tracktable.recv_id == recv_id).select(tracktable.send_id,
                                                        limitby=(0, 1)).first()
    if send_row:
        send_id = send_row.send_id
        db(stable.id == send_id).update(status = inv_ship_status["RECEIVED"],
                                        owned_by_user = None,
                                        owned_by_group = ADMIN,
                                        )

    # Change the status for all track items in this shipment to Unloading
    # the onaccept will then move the values into the site, update any request
    # record, create any adjustment if needed and change the status to Arrived
    db(tracktable.recv_id == recv_id).update(status = 3)

    # Move each item to the site
    track_rows = db(tracktable.recv_id == recv_id).select()
    for track_item in track_rows:
        row = Storage(track_item)
        s3db.inv_track_item_onaccept(Storage(vars = Storage(id=row.id),
                                             record = row,
                                             ))

    # Done => confirmation message, open the record
    session.confirmation = T("Shipment Items Received")
    redirect(URL(c="inv", f="recv", args=[recv_id]))

# -----------------------------------------------------------------------------
def recv_cancel():
    """
        Cancel a Received Shipment

        @todo what to do if the quantity cancelled doesn't exist?
    """

    try:
        recv_id = request.args[0]
    except:
        redirect(URL(f="recv"))

    rtable = s3db.inv_recv
    if not auth.s3_has_permission("delete", rtable, record_id=recv_id):
        session.error = T("You do not have permission to cancel this received shipment.")
        redirect(URL(c="inv", f="recv", args=[recv_id]))

    recv_record = db(rtable.id == recv_id).select(rtable.status,
                                                  limitby=(0, 1)).first()

    inv_ship_status = s3db.inv_ship_status
    if recv_record.status != inv_ship_status["RECEIVED"]:
        session.error = T("This shipment has not been received - it has NOT been canceled because it can still be edited.")
        redirect(URL(c="inv", f="recv", args=[recv_id]))

    stable = s3db.inv_send
    tracktable = s3db.inv_track_item
    inv_item_table = s3db.inv_inv_item
    ritable = s3db.req_req_item
    siptable = s3db.supply_item_pack

    # Go through each item in the shipment remove them from the site store
    # and put them back in the track item record
    query = (tracktable.recv_id == recv_id) & \
            (tracktable.deleted == False)
    recv_items = db(query).select(tracktable.recv_inv_item_id,
                                  tracktable.recv_quantity,
                                  tracktable.send_id,
                                  )
    send_id = None
    for recv_item in recv_items:
        inv_item_id = recv_item.recv_inv_item_id
        # This assumes that the inv_item has the quantity
        quantity = inv_item_table.quantity - recv_item.recv_quantity
        if quantity == 0:
            db(inv_item_table.id == inv_item_id).delete()
        else:
            db(inv_item_table.id == inv_item_id).update(quantity = quantity)
        db(tracktable.recv_id == recv_id).update(status = 2) # In transit
        # @todo potential problem in that the send id should be the same for all track items but is not explicitly checked
        if send_id is None and recv_item.send_id is not None:
            send_id = recv_item.send_id
    track_rows = db(tracktable.recv_id == recv_id).select(tracktable.req_item_id,
                                                          tracktable.item_pack_id,
                                                          tracktable.recv_quantity,
                                                          )
    for track_item in track_rows:
        # If this is linked to a request
        # then remove these items from the quantity in fulfil
        if track_item.req_item_id:
            req_id = track_item.req_item_id
            req_item = db(ritable.id == req_id).select(ritable.quantity_fulfil,
                                                       ritable.item_pack_id,
                                                       limitby=(0, 1)).first()
            req_quantity = req_item.quantity_fulfil
            # @ToDo: Optimise by reading these 2 in a single DB query
            req_pack_quantity = db(siptable.id == req_item.item_pack_id).select(siptable.quantity,
                                                                                limitby=(0, 1)
                                                                                ).first().quantity
            track_pack_quantity = db(siptable.id == track_item.item_pack_id).select(siptable.quantity,
                                                                                    limitby=(0, 1)
                                                                                    ).first().quantity
            quantity_fulfil = s3db.supply_item_add(req_quantity,
                                                   req_pack_quantity,
                                                   - track_item.recv_quantity,
                                                   track_pack_quantity
                                                  )
            db(ritable.id == req_id).update(quantity_fulfil = quantity_fulfil)
            s3db.req_update_status(req_id)

    # Now set the recv record to cancelled and the send record to sent
    ADMIN = auth.get_system_roles().ADMIN
    db(rtable.id == recv_id).update(date = request.utcnow,
                                    status = inv_ship_status["CANCEL"],
                                    owned_by_user = None,
                                    owned_by_group = ADMIN)
    if send_id != None:
        # The sent record is now set back to SENT so the source warehouse can
        # now cancel this record to get the stock back into their warehouse.
        # IMPORTANT reports need to locate this record otherwise it can be
        # a mechanism to circumvent the auditing of stock
        db(stable.id == send_id).update(status = inv_ship_status["SENT"],
                                        owned_by_user = None,
                                        owned_by_group = ADMIN)
    redirect(URL(c="inv", f="recv",
                 args=[recv_id]))

# =============================================================================
def track_item():
    """ RESTful CRUD controller """

    table = s3db.inv_track_item

    s3db.configure("inv_track_item",
                   create = False,
                   deletable = False,
                   editable = False,
                   insertable = False,
                   listadd = False,
                   )

    report = get_vars.get("report")
    if report == "rel":
        # Summary of Releases
        s3.crud_strings["inv_track_item"] = Storage(title_list = T("Summary of Releases"),
                                                    subtitle_list = T("Summary Details"),
                                                    )
        s3db.configure("inv_track_item",
                       list_fields = ["id",
                                      #"send_id",
                                      #"req_item_id",
                                      (T("Date Released"), "send_id$date"),
                                      (T("Beneficiary"), "send_id$site_id"),
                                      (settings.get_inv_send_shortname(), "send_id$send_ref"),
                                      (settings.get_req_shortname(), "send_id$req_ref"),
                                      (T("Items/Description"), "item_id"),
                                      (T("Source"), "supply_org_id"),
                                      (T("Unit"), "item_pack_id"),
                                      (T("Quantity"), "quantity"),
                                      (T("Unit Cost"), "pack_value"),
                                      (T("Total Cost"), "total_value"),
                                     ],
                       orderby = "inv_send.site_id",
                       sort = True
                      )
        s3.filter = (FS("send_id") != None)

    elif report == "inc":
        # Summary of Incoming Supplies
        s3.crud_strings["inv_track_item"] = Storage(title_list = T("Summary of Incoming Supplies"),
                                                    subtitle_list = T("Summary Details"),
                                                    )

        s3db.configure("inv_track_item",
                       list_fields = ["id",
                                      (T("Date Received"), "recv_id$date"),
                                      (T("Received By"), "recv_id$recipient_id"),
                                      (settings.get_inv_send_shortname(), "recv_id$send_ref"),
                                      (settings.get_inv_recv_shortname(), "recv_id$recv_ref"),
                                      (settings.get_proc_shortname(), "recv_id$purchase_ref"),
                                      (T("Item/Description"), "item_id"),
                                      (T("Unit"), "item_pack_id"),
                                      (T("Quantity"), "quantity"),
                                      (T("Unit Cost"), "pack_value"),
                                      (T("Total Cost"), "total_value"),
                                      (T("Source"), "supply_org_id"),
                                      (T("Remarks"), "comments"),
                                      ],
                        orderby = "inv_recv.recipient_id",
                        )
        s3.filter = (FS("recv_id") != None)

    elif report == "util":
        # Utilization Report
        s3.crud_strings["inv_track_item"] = Storage(title_list = T("Utilization Report"),
                                                    subtitle_list = T("Utilization Details"),
                                                    )

        s3db.configure("inv_track_item",
                       list_fields = ["id",
                                      (T("Item/Description"), "item_id$name"),
                                      (T("Beneficiary"), "send_id$site_id"),
                                      (settings.get_inv_send_shortname(), "send_id$send_ref"),
                                      (settings.get_req_shortname(), "send_id$req_ref"),
                                      (T("Items/Description"), "item_id"),
                                      (T("Source"), "supply_org_id"),
                                      (T("Unit"), "item_pack_id"),
                                      (T("Quantity"), "quantity"),
                                      (T("Unit Cost"), "pack_value"),
                                      (T("Total Cost"), "total_value"),
                                      ]
                       )

        s3.filter = (FS("item_id") != None)

    elif report == "exp":
        # Expiration Report
        s3.crud_strings["inv_track_item"] = Storage(title_list = T("Expiration Report"),
                                                    subtitle_list = T("Expiration Details"),
                                                    )

        s3db.configure("inv_track_item",
                       list_fields = ["id",
                                      "recv_inv_item_id$site_id",
                                      (T("Item/Description"), "item_id"),
                                      (T("Expiration Date"), "expiry_date"),
                                      (T("Source"), "supply_org_id"),
                                      (T("Unit"), "item_pack_id"),
                                      (T("Quantity"), "quantity"),
                                      (T("Unit Cost"), "pack_value"),
                                      (T("Total Cost"), "total_value"),
                                      ]
                       )
        s3.filter = (FS("expiry_date") != None)

    output = s3_rest_controller(rheader = s3db.inv_rheader,
                                )
    return output

# =============================================================================
def adj():
    """ RESTful CRUD controller """

    table = s3db.inv_adj

    # Limit site_id to sites the user has permissions for
    error_msg = T("You do not have permission to adjust the stock level in this warehouse.")
    auth.permitted_facilities(table=table, error_msg=error_msg)

    def prep(r):
        if r.interactive:
            if r.component:
                if r.component_name == "adj_item":
                    if r.component_id:
                        aitable = s3db.inv_adj_item
                        if r.record.status == 0:
                            aitable.reason.writable = True
                        record = db(aitable.id == r.component_id).select(aitable.inv_item_id,
                                                                         limitby=(0, 1)
                                                                         ).first()
                        if record.inv_item_id:
                            aitable.item_id.writable = False
                            aitable.item_id.comment = None
                            aitable.item_pack_id.writable = False
                elif r.component_name == "image":
                    doc_table = s3db.doc_image
                    doc_table.organisation_id.readable = doc_table.organisation_id.writable = False
                    doc_table.person_id.readable = doc_table.person_id.writable = False
                    doc_table.location_id.readable = doc_table.location_id.writable = False
            else:
                # if an adjustment has been selected and it has been completed
                # then make the fields read only
                if r.record and r.record.status:
                    table.adjuster_id.writable = False
                    table.site_id.writable = False
                    table.comments.writable = False
                else:
                    if "item" in get_vars and "site" in get_vars:
                        # create a adj record with a single adj_item record
                        adj_id = table.insert(adjuster_id = auth.s3_logged_in_person(),
                                              site_id = get_vars.site,
                                              adjustment_date = request.utcnow,
                                              status = 0,
                                              category = 1,
                                              comments = "Single item adjustment"
                                              )
                        inv_item_table = s3db.inv_inv_item
                        inv_item = inv_item_table[get_vars.item]
                        adjitemtable = s3db.inv_adj_item
                        adj_item_id = adjitemtable.insert(reason = 0,
                                    adj_id = adj_id,
                                    inv_item_id = inv_item.id, # original source inv_item
                                    item_id = inv_item.item_id, # the supply item
                                    item_pack_id = inv_item.item_pack_id,
                                    old_quantity = inv_item.quantity,
                                    currency = inv_item.currency,
                                    old_status = inv_item.status,
                                    new_status = inv_item.status,
                                    old_pack_value = inv_item.pack_value,
                                    new_pack_value = inv_item.pack_value,
                                    expiry_date = inv_item.expiry_date,
                                    bin = inv_item.bin,
                                    old_owner_org_id = inv_item.owner_org_id,
                                    new_owner_org_id = inv_item.owner_org_id,
                                   )
                        redirect(URL(c = "inv",
                                     f = "adj",
                                     args = [adj_id,
                                             "adj_item",
                                             adj_item_id,
                                             "update"]))
                    else:
                        table.comments.default = "Complete Stock Adjustment"
                        if "site" in get_vars:
                            table.site_id.writable = True
                            table.site_id.default = get_vars.site
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            s3_action_buttons(r, deletable=False)
        return output
    s3.postp = postp

    args = request.args
    if len(args) > 1 and args[1] == "adj_item" and \
       table[args[0]].status:
        # remove CRUD generated buttons in the tabs
        s3db.configure("inv_adj_item",
                       create = False,
                       deletable = False,
                       editable = False,
                       listadd = False,
                       )

    output = s3_rest_controller(rheader = s3db.inv_adj_rheader,
                                )
    return output

# -----------------------------------------------------------------------------
def adj_close():
    """ RESTful CRUD controller """

    try:
        adj_id = request.args[0]
    except:
        redirect(URL(f="adj"))

    atable = s3db.inv_adj

    # Limit site_id to sites the user has permissions for
    error_msg = T("You do not have permission to adjust the stock level in this warehouse.")
    auth.permitted_facilities(table=atable, error_msg=error_msg)

    adj_rec = db(atable.id == adj_id).select(atable.status,
                                             atable.site_id,
                                             limitby=(0, 1)).first()
    if adj_rec.status != 0:
        session.error = T("This adjustment has already been closed.")

    if session.error:
        redirect(URL(c="inv", f="adj",
                     args=[adj_id]))

    aitable = s3db.inv_adj_item
    inv_item_table = s3db.inv_inv_item

    site_id = adj_rec.site_id
    # Go through all the adj_items
    query = (aitable.adj_id == adj_id) & \
            (aitable.deleted == False)
    adj_items = db(query).select()
    for adj_item in adj_items:
        if adj_item.inv_item_id is None:
            # Create a new stock item
            inv_item_id = inv_item_table.insert(site_id = site_id,
                                                item_id = adj_item.item_id,
                                                item_pack_id = adj_item.item_pack_id,
                                                currency = adj_item.currency,
                                                bin = adj_item.bin,
                                                pack_value = adj_item.old_pack_value,
                                                expiry_date = adj_item.expiry_date,
                                                quantity = adj_item.new_quantity,
                                                owner_org_id = adj_item.old_owner_org_id,
                                               )
            # Add the inventory item id to the adjustment record
            db(aitable.id == adj_item.id).update(inv_item_id = inv_item_id)
        elif adj_item.new_quantity is not None:
            # Update the existing stock item
            db(inv_item_table.id == adj_item.inv_item_id).update(item_pack_id = adj_item.item_pack_id,
                                                                 bin = adj_item.bin,
                                                                 pack_value = adj_item.old_pack_value,
                                                                 expiry_date = adj_item.expiry_date,
                                                                 quantity = adj_item.new_quantity,
                                                                 owner_org_id = adj_item.new_owner_org_id,
                                                                 status = adj_item.new_status,
                                                                )
    # Change the status of the adj record to Complete
    db(atable.id == adj_id).update(status=1)
    # Go to the Inventory of the Site which has adjusted these items
    (prefix, resourcename, id) = s3db.get_instance(s3db.org_site,
                                                   site_id)
    redirect(URL(c = prefix,
                 f = resourcename,
                 args = [id, "inv_item"]))

# =============================================================================
def recv_item_json():
    """
       Used by s3.supply.js

       Access via the .json representation to avoid work rendering menus, etc
    """

    try:
        item_id = request.args[0]
    except:
        raise HTTP(400, current.xml.json_message(False, 400, "No value provided!"))

    stable = s3db.org_site
    rtable = s3db.inv_recv
    ittable = s3db.inv_track_item

    rtable.date.represent = lambda dt: dt[:10]

    query = (ittable.req_item_id == item_id) & \
            (rtable.id == ittable.recv_id) & \
            (rtable.site_id == stable.id) & \
            (rtable.status == s3db.inv_ship_status["RECEIVED"]) & \
            (ittable.deleted == False)
    records = db(query).select(rtable.id,
                               rtable.date,
                               stable.name,
                               ittable.quantity)

    output = "[%s,%s" % (json.dumps(dict(id = str(T("Received")),
                                         quantity = "#"
                                         )),
                         records.json()[1:])

    response.headers["Content-Type"] = "application/json"
    return output

# -----------------------------------------------------------------------------
def send_item_json():
    """
       Used by s3.supply.js

       Access via the .json representation to avoid work rendering menus, etc
    """

    try:
        item_id = request.args[0]
    except:
        raise HTTP(400, current.xml.json_message(False, 400, "No value provided!"))

    stable = s3db.org_site
    istable = s3db.inv_send
    ittable = s3db.inv_track_item
    inv_ship_status = s3db.inv_ship_status

    istable.date.represent = lambda dt: dt[:10]

    query = (ittable.req_item_id == item_id) & \
            (istable.id == ittable.send_id) & \
            (istable.site_id == stable.id) & \
            ((istable.status == inv_ship_status["SENT"]) | \
             (istable.status == inv_ship_status["RECEIVED"])) & \
            (ittable.deleted == False)
    records = db(query).select(istable.id,
                               istable.date,
                               stable.name,
                               ittable.quantity)

    output = "[%s,%s" % (json.dumps(dict(id = str(T("Sent")),
                                         quantity = "#"
                                         )),
                         records.json()[1:])

    response.headers["Content-Type"] = "application/json"
    return output

# -----------------------------------------------------------------------------
def kitting():

    return s3_rest_controller(rheader = s3db.inv_rheader,
                              )

# -----------------------------------------------------------------------------
def facility():
    # Open record in this controller after creation
    s3db.configure("org_facility",
                   create_next = URL(c="inv", f="facility",
                                     args = ["[id]", "read"]),
                   )

    return s3db.org_facility_controller()

# -----------------------------------------------------------------------------
def facility_type():
    return s3_rest_controller("org")

# -----------------------------------------------------------------------------
def incoming():
    """
        Incoming Shipments for Sites

        Used from Requests rheader when looking at Transport Status
    """

    # @ToDo: Create this function!
    return s3db.inv_incoming()

# -----------------------------------------------------------------------------
def req_match():
    """ Match Requests """

    return s3db.req_match()

# END =========================================================================
