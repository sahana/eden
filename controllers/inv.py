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
    """
        Application Home page
        - custom View
    """

    # Need CRUD String
    table = s3db.table("cr_shelter", None)

    module_name = settings.modules[module].name_nice
    response.title = module_name
    if s3.debug:
        # Start of TEST CODE for multiple dataTables,
        #this also required views/inv/index.html to be modified
        from s3.s3utils import S3DataTable
        request = current.request
        vars = current.request.get_vars
        if request.extension == "html" or request.vars.id == "warehouse_list_1":
            resource = s3db.resource("inv_warehouse")
            totalrows = resource.count()
            list_fields = ["id",
                           "name",
                           "organisation_id",
                           ]
            start = int(vars.iDisplayStart) if vars.iDisplayStart else 0
            limit = int(vars.iDisplayLength) if vars.iDisplayLength else s3mgr.ROWSPERPAGE
            rfields = resource.resolve_selectors(list_fields)[0]
            (orderby, filter) = S3DataTable.getControlData(rfields, current.request.vars)
            resource.add_filter(filter)
            filteredrows = resource.count()
            rows = resource.select(list_fields,
                                   orderby="organisation_id",
                                   start=start,
                                   limit=limit,
                                   )
            data = resource.extract(rows,
                                    list_fields,
                                    represent=True,
                                    )
            dt = S3DataTable(rfields, data)
            dt.defaultActionButtons(resource)
            if request.extension == "html":
                warehouses = dt.html(totalrows,
                                     filteredrows,
                                     "warehouse_list_1",
                                     dt_bFilter="true",
                                     dt_group=2,
                                     dt_ajax_url=URL(c="inv",
                                                  f="index",
                                                  extension="aadata",
                                                  vars={"id":"warehouse_list_1"},
                                                  ),
                                     )
            else:
                warehouse = dt.json(totalrows,
                                    filteredrows,
                                    "warehouse_list_1",
                                    int(request.vars.sEcho),
                                    )
                return warehouse
        # Second Table
        if request.extension == "html" or request.vars.id == "inventory_list_1":
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
                rfields = resource.resolve_selectors(list_fields)[0]
                (orderby, filter) = S3DataTable.getControlData(rfields, current.request.vars)
                resource.add_filter(filter)
                (rfields, joins, left, distinct) = resource.resolve_selectors(list_fields)
                site_list = {}
                rows = resource.select(list_fields,
                                       limit=resource.count())
                filteredrows = len(rows.records)
                for row in rows:
                    site_id = row.inv_inv_item.site_id
                    if site_id not in site_list:
                        site_list[site_id] = 1
                    else:
                        site_list[site_id] += 1
                formatted_site_list = {}
                repr = table.site_id.represent
                for (key,value) in site_list.items():
                    formatted_site_list[str(repr(key))] = value
                if isinstance(orderby, bool):
                    orderby = table.site_id | stable.name | ~table.quantity
                start = int(vars.iDisplayStart) if vars.iDisplayStart else 0
                limit = int(vars.iDisplayLength) if vars.iDisplayLength else s3mgr.ROWSPERPAGE
                rows = resource.select(list_fields,
                                       orderby=orderby,
                                       start=start,
                                       limit=limit,
                                       )
                data = resource.extract(rows,
                                        list_fields,
                                        represent=True,
                                        )
                dt = S3DataTable(rfields,
                                 data,
                                 orderby=orderby,
                                 )
                custom_actions = [dict(label=str(T("Warehouse")),
                                  _class="action-icon",
                                  icon="/%s/static/img/markers/gis_marker.image.Agri_Commercial_Food_Distribution_Center_S1.png" % appname,
                                  url=URL(c="inv", f="warehouse",
                                          args=["[id]", "update"]
                                          )
                                  ),
                                 ]
                dt.defaultActionButtons(resource, custom_actions)
                if request.extension == "html":
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
                                        dt_bFilter="true",
                                        dt_group=[1,2],
                                        dt_group_totals=[formatted_site_list],
                                        dt_action_col=-1,
                                        dt_ajax_url=URL(c="inv",
                                                     f="index",
                                                     extension="aadata",
                                                     vars={"id":"inventory_list_1"},
                                                     ),
                                        dt_bulk_actions = "Adjust",
                                        dt_styles = {"dtdisable": errorList,
                                                     "dtwarning": warningList,
                                                     "dtalert": alertList,
                                                     },
                                        #dt_text_maximum_len = 10,
                                        #dt_text_condense_len = 8,
                                        #dt_group_space = "true",
                                        dt_shrink_groups = "accordion",
                                        #dt_shrink_groups = "individual",
                                        )

                    s3.actions = None
                elif request.extension == "aadata":
                    inventory = dt.json(totalrows,
                                        filteredrows,
                                        "inventory_list_1",
                                        int(request.vars.sEcho),
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
        if request.extension == "html" or request.vars.id == "supply_list_1":
            resource = s3db.resource("supply_item")
            totalrows = displayrows = resource.count()
            list_fields = ["id",
                           "name",
                           "um",
                           "model",
                           ]
            limit = int(vars.iDisplayLength) if vars.iDisplayLength else s3mgr.ROWSPERPAGE
            rows = resource.select(list_fields,
                                   start=0,
                                   limit=resource.count(),
                                   )
            data = resource.extract(rows,
                                    list_fields,
                                    represent=True,
                                    )
            rfields = resource.resolve_selectors(list_fields)[0]
            dt = S3DataTable(rfields, data)
            dt.defaultActionButtons(resource)
            if request.extension == "html":
                supply_items = dt.html(totalrows,
                                       displayrows,
                                       "supply_list_1",
                                       dt_displayLength=10,
                                       dt_action_col=1,
                                       dt_ajax_url=URL(c="inv",
                                                       f="index",
                                                       extension="aadata",
                                                       vars={"id": "supply_list_1"},
                                                       ),
                                       )
            else:
                supply_items = dt.json(totalrows,
                                       displayrows,
                                       "supply_list_1",
                                       int(request.vars.sEcho),
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

    if "viewing" in request.get_vars:
        viewing = request.get_vars.viewing
        tn, id = viewing.split(".", 1)
        if tn == "inv_warehousec":
            request.args.insert(0, id)

    # CRUD pre-process
    def prep(r):
        
        if r.id:
            r.table.obsolete.readable = r.table.obsolete.writable = True

        if r.component:
            if r.component.name == "inv_item":
                # Filter out items which are already in this inventory
                s3db.inv_prep(r)
                # Remove the Warehouse Name from the list_fields
                list_fields = s3db.get_config("inv_inv_item", "list_fields")
                try:
                    list_fields.remove("site_id")
                    s3db.configure("inv_inv_item", list_fields=list_fields)
                except:
                    pass

            elif r.component.name == "recv" or \
                 r.component.name == "send":
                # Filter out items which are already in this inventory
                s3db.inv_prep(r)

            elif r.component.name == "human_resource":
                # Filter out people which are already staff for this warehouse
                s3base.s3_filter_staff(r)
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
            r.resource.add_filter(s3db.inv_warehouse.obsolete != True)
        return True
    s3.prep = prep

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
    s3.postp = postp

    if "extra_data" in request.get_vars:
        resourcename = "inv_item"
    else:
        resourcename = "warehouse"
    csv_stylesheet = "%s.xsl" % resourcename

    output = s3_rest_controller(module, resourcename,
                                rheader=s3db.inv_warehouse_rheader,
                                csv_template = resourcename,
                                csv_stylesheet = csv_stylesheet,
                                # Extra fields for CSV uploads:
                                #csv_extra_fields = [
                                #         dict(label="Organisation",
                                #         field=s3db.org_organisation_id(comment=None))
                                #]
                                )
    if "add_btn" in output:
        del output["add_btn"]
    return output

# -----------------------------------------------------------------------------
def supplier():
    current.request.get_vars["organisation.organisation_type_id$name"] = "Supplier"
    return s3db.org_organisation_controller()

# =============================================================================
def inv_item():
    """ REST Controller """

    tablename = "inv_inv_item"
    # Load model to be able to override CRUD string(s)
    table = s3db[tablename]
    s3.crud_strings[tablename].msg_list_empty = T("No Stock currently registered")

    if "report" in request.get_vars and \
       request.get_vars.report == "mon":
            s3.crud_strings[tablename].update(dict(
                title_list = T("Monetization Report"),
                subtitle_list = T("Monetization Details"),
                msg_list_empty = T("No Stock currently registered"),
                title_search = T("Monetization Report"),
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
                       insertable=False,
                       list_fields = ["id",
                                      "site_id",
                                      "item_id",
                                      (T("Item Code"), "item_code"),
                                      (T("Category"), "item_category"),
                                      "quantity",
                                      "pack_value",
                                      #(T("Total Value"), "total_value"),
                                      ]
                       )

    # Upload for configuration (add replace option)
    s3.importerPrep = lambda: dict(ReplaceOption=T("Remove existing data before import"))

    # if this url has a viewing track items then redirect to track_movement
    if "viewing" in request.get_vars:
        viewing = request.get_vars.viewing
        tn, id = viewing.split(".", 1)
        if tn == "inv_track_item":
            record = s3db.inv_track_item[id]
            redirect(URL(c = "inv",
                         f = "track_movement",
                         args = [],
                         vars = {"viewing" : "%s.%s" % ("inv_inv_item", record.item_id)}
                        )
                     )
    def prep(r):
        if r.method != "search" and r.method != "report":
            s3.dataTable_group = 1
        return True
    s3.prep = prep

    # Import pre-process
    def import_prep(data):
        """
            Deletes all Stock records of the organisation
            before processing a new data import, used for the import_prep
            hook in s3mgr
        """
        request = current.request
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
                        ondelete = s3db.get_config("inv_inv_item", "ondelete")
                        resource.delete(ondelete=ondelete, format="xml")
            resource.skip_import = True
    s3mgr.import_prep = import_prep


    # Limit site_id to sites the user has permissions for
    auth.permitted_facilities(table=table,
                              error_msg=T("You do not have permission for any site to add an inventory item."))

    if len(request.args) > 1 and request.args[1] == "track_item":
        # remove CRUD generated buttons in the tabs
        s3db.configure("inv_track_item",
                       create=False,
                       listadd=False,
                       editable=False,
                       deletable=False,
                       )

    output = s3_rest_controller(rheader=s3db.inv_warehouse_rheader,
                                #csv_extra_fields = [dict(label="Organisation",
                                #                         field=s3db.org_organisation_id(comment=None))
                                #                    ],
                                pdf_paper_alignment = "Landscape",
                                pdf_table_autogrow = "B",
                                pdf_groupby = "site_id, item_id",
                                pdf_orderby = "expiry_date, supply_org_id",
                                )
    if "add_btn" in output:
        del output["add_btn"]
    return output

# -----------------------------------------------------------------------------
def track_movement():
    """ REST Controller """

    table = s3db.inv_track_item

    s3db.configure("inv_track_item",
                   create=False,
                   listadd=False,
                   editable=False,
                   deletable=False,
                   )

    def prep(r):
        if r.interactive:
            if "viewing" in request.vars:
                dummy, item_id = request.vars.viewing.split(".")
                filter = (table.send_inv_item_id == item_id ) | \
                         (table.recv_inv_item_id == item_id)
                s3.filter = filter
        return True
    s3.prep = prep

    output = s3_rest_controller("inv", "track_item",
                                rheader=s3db.inv_warehouse_rheader,
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

    sendtable = s3db.inv_send
    tracktable = s3db.inv_track_item

    # Limit site_id to sites the user has permissions for
    error_msg = T("You do not have permission for any facility to send a shipment.")
    auth.permitted_facilities(table=sendtable, error_msg=error_msg)

    # Set Validator for checking against the number of items in the warehouse
    vars = request.vars
    if (vars.send_inv_item_id):
        if not vars.item_pack_id:
            vars.item_pack_id = s3db.inv_inv_item[vars.send_inv_item_id].item_pack_id
        s3db.inv_track_item.quantity.requires = QUANTITY_INV_ITEM(db,
                                                                 vars.send_inv_item_id,
                                                                 vars.item_pack_id)

    SHIP_STATUS_IN_PROCESS = s3db.inv_ship_status["IN_PROCESS"]
    SHIP_STATUS_SENT = s3db.inv_ship_status["SENT"]
    SHIP_STATUS_RECEIVED = s3db.inv_ship_status["RECEIVED"]
    SHIP_STATUS_CANCEL = s3db.inv_ship_status["CANCEL"]
    SHIP_STATUS_RETURNING  = s3db.inv_ship_status["RETURNING"]

    def set_send_attr(status):
        sendtable.send_ref.writable = False
        if status == SHIP_STATUS_IN_PROCESS:
            sendtable.send_ref.readable = False
        else:
            # Make all fields writable False
            for field in sendtable.fields:
                sendtable[field].writable = False

    TRACK_STATUS_UNKNOWN    = s3db.inv_tracking_status["UNKNOWN"]
    TRACK_STATUS_PREPARING  = s3db.inv_tracking_status["IN_PROCESS"]
    TRACK_STATUS_TRANSIT    = s3db.inv_tracking_status["SENT"]
    TRACK_STATUS_UNLOADING  = s3db.inv_tracking_status["UNLOADING"]
    TRACK_STATUS_ARRIVED    = s3db.inv_tracking_status["RECEIVED"]
    TRACK_STATUS_CANCELED   = s3db.inv_tracking_status["CANCEL"]
    TRACK_STATUS_RETURNING  = s3db.inv_tracking_status["RETURNING"]

    def set_track_attr(status):
        # By default Make all fields writable False
        for field in tracktable.fields:
            tracktable[field].writable = False
        # Hide some fields
        tracktable.send_id.readable = False
        tracktable.recv_id.readable = False
        tracktable.bin.readable = False
        tracktable.item_id.readable = False
        tracktable.recv_quantity.readable = False
        tracktable.return_quantity.readable = False
        tracktable.expiry_date.readable = False
        tracktable.owner_org_id.readable = False
        tracktable.supply_org_id.readable = False
        tracktable.adj_item_id.readable = False
        if status == TRACK_STATUS_PREPARING:
            # show some fields
            tracktable.send_inv_item_id.writable = True
            tracktable.item_pack_id.writable = True
            tracktable.quantity.writable = True
            tracktable.comments.writable = True
            # hide some fields
            tracktable.currency.readable = False
            tracktable.pack_value.readable = False
            tracktable.item_source_no.readable = False
            tracktable.inv_item_status.readable = False
        elif status == TRACK_STATUS_ARRIVED:
            # Shipment arrived display some extra fields at the destination
            tracktable.item_source_no.readable = True
            tracktable.recv_quantity.readable = True
            tracktable.return_quantity.readable = True
            tracktable.recv_bin.readable = True
            tracktable.currency.readable = True
            tracktable.pack_value.readable = True
        elif status == TRACK_STATUS_RETURNING:
            tracktable.return_quantity.readable = True
            tracktable.return_quantity.writable = True
            tracktable.currency.readable = True
            tracktable.pack_value.readable = True

    def prep(r):
        # Default to the Search tab in the location selector
        s3.gis.tab = "search"
        record = sendtable[r.id]
        if record and record.status != SHIP_STATUS_IN_PROCESS:
            # now that the shipment has been sent
            # lock the record so that it can't be meddled with
            s3db.configure("inv_send",
                            create=False,
                            listadd=False,
                            editable=False,
                            deletable=False,
                           )

        if r.component:
            if record.status == SHIP_STATUS_RECEIVED or \
               record.status == SHIP_STATUS_CANCEL:
                list_fields = ["id",
                               "status",
                               "item_id",
                               "item_pack_id",
                               "bin",
                               "quantity",
                               "currency",
                               "pack_value",
                               "recv_quantity",
                               "return_quantity",
                               "owner_org_id",
                               "supply_org_id",
                               "inv_item_status",
                               "comments",
                              ]
            elif record.status == SHIP_STATUS_RETURNING:
                list_fields = ["id",
                               "status",
                               "item_id",
                               "item_pack_id",
                               "quantity",
                               "currency",
                               "pack_value",
                               "return_quantity",
                               "bin",
                               "owner_org_id",
                               "supply_org_id",
                               "inv_item_status",
                              ]
            else:
                list_fields = ["id",
                               "status",
                               "item_id",
                               "item_pack_id",
                               "quantity",
                               "currency",
                               "pack_value",
                               "bin",
                               "owner_org_id",
                               "supply_org_id",
                               "inv_item_status",
                              ]
            s3db.configure("inv_track_item",
                            list_fields=list_fields,
                           )

            # Can only create or delete track items for a send record if the status is preparing
            if r.method == "create" or r.method == "delete":
                if record.status != SHIP_STATUS_IN_PROCESS:
                    return False
            if r.method == "delete":
                return s3.inv_track_item_deleting(r.component_id)
            if r.record.get("site_id"):
                # Restrict to items from this warehouse only
                tracktable.send_inv_item_id.requires = IS_ONE_OF(db,
                                                         "inv_inv_item.id",
                                                         s3db.inv_item_represent,
                                                         orderby="inv_inv_item.id",
                                                         sort=True,
                                                         filterby = "site_id",
                                                         filter_opts = [r.record.site_id]
                                                        )
            # Hide the values that will be copied from the inv_inv_item record
            if r.component_id:
                track_record = tracktable[r.component_id]
                set_track_attr(track_record.status)
                # if the track record is linked to a request item then
                # the stock item has already been selected so make it read only
                if track_record and track_record.get("req_item_id"):
                    tracktable.send_inv_item_id.writable = False
                    tracktable.item_pack_id.writable = False
                    stock_qnty = track_record.send_inv_item_id.quantity
                    tracktable.quantity.comment = T("%d in stock" % stock_qnty)
                    tracktable.quantity.requires = QUANTITY_INV_ITEM(db,
                                                                 track_record.send_inv_item_id,
                                                                 track_record.item_pack_id)
                # Hide the item id
                tracktable.item_id.readable = False
            else:
                set_track_attr(TRACK_STATUS_PREPARING)
            if r.interactive:
                if r.record.status == SHIP_STATUS_IN_PROCESS:
                    s3.crud_strings.inv_send.title_update = \
                    s3.crud_strings.inv_send.title_display = T("Process Shipment to Send")
                elif "site_id" in request.vars and r.record.status == SHIP_STATUS_SENT:
                    s3.crud_strings.inv_send.title_update = \
                    s3.crud_strings.inv_send.title_display = T("Review Incoming Shipment to Receive")
        else:
            if request.get_vars.received:
                # Set the items to being received
                sendtable[r.id] = dict(status = SHIP_STATUS_RECEIVED)
                db(tracktable.send_id == r.id).update(status = TRACK_STATUS_ARRIVED)
                response.message = T("Shipment received")
            # else set the inv_send attributes
            elif r.id:
                record = sendtable[r.id]
                set_send_attr(record.status)
            else:
                set_send_attr(SHIP_STATUS_IN_PROCESS)
                sendtable.send_ref.readable = False
        return True

    if len(request.args) > 1 and request.args[1] == "track_item":
        # Shouldn't fail but...
        # if user enters the send id then it could so wrap in a try...
        try:
            status = sendtable[request.args[0]].status
        except:
            status = None
        if status:
            editable = False
            if status == SHIP_STATUS_RETURNING:
                editable = True
            # remove CRUD generated buttons in the tabs
            s3db.configure("inv_track_item",
                            create=False,
                            listadd=False,
                            editable=editable,
                            deletable=False,
                           )


    s3.prep = prep
    output = s3_rest_controller(rheader=s3.inv_send_rheader)
    return output

# ==============================================================================
def send_commit():
    """
    """

    # Get the commit record
    try:
        commit_id = request.args[0]
    except:
        redirect(URL(c="req",
                     f="commit"))

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
                                req_item_id = row.req_req_item.id
                                )
        track_table(track_table.id == id).update(tracking_no = "TN:%6d" % (10000 + id))
    # redirect to inv_send for the send id just created
    redirect(URL(c = "inv",
                 f = "send",
                 args = [send_id, "track_item"]))

# -----------------------------------------------------------------------------
def send_process():
    """ Send a Shipment """

    try:
        send_id = request.args[0]
    except:
        redirect(URL(c="inv",
                     f="send"))

    stable = s3db.inv_send
    tracktable = s3db.inv_track_item
    siptable = s3db.supply_item_pack
    rrtable = s3db.req_req
    ritable = s3db.req_req_item

    if not auth.s3_has_permission("update",
                                  stable,
                                  record_id=send_id):
        session.error = T("You do not have permission to send this shipment.")

    send_record = stable[send_id]

    if send_record.status != eden.inv.inv_ship_status["IN_PROCESS"]:
        session.error = T("This shipment has already been sent.")

    # Get the track items that are part of this shipment
    query = (tracktable.send_id == send_id ) & \
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
    req_ref = send_record.req_ref
    query = (rrtable.req_ref == req_ref)
    req_rec = db(query).select(rrtable.id, limitby = (0, 1)).first()
    if req_rec:
        req_id = req_rec.id
        for track_item in track_items:
            if track_item.req_item_id:
                req_i = ritable[track_item.req_item_id]
                req_p_qnty = siptable[req_i.item_pack_id].quantity
                t_qnty = track_item.quantity
                t_pack_id = track_item.item_pack_id
                inv_p_qnty = siptable[t_pack_id].quantity
                transit_quantity = t_qnty * inv_p_qnty / req_p_qnty
                db(ritable.id == track_item.req_item_id).update(quantity_transit = ritable.quantity_transit + transit_quantity)
        s3db.req_update_status(req_id)
    # Create a Receive record
    rtable = s3db.inv_recv
    recv_id = rtable.insert(sender_id = send_record.sender_id,
                            send_ref = send_record.send_ref,
                            req_ref = send_record.req_ref,
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
    redirect(URL(c = "inv",
                 f = "send",
                 args = [send_id, "track_item"]))

# -----------------------------------------------------------------------------
def send_returns():
    """
        This will cancel a shipment that has been sent

        @todo need to roll back commitments
    """

    send_id = request.args[0]
    stable = s3db.inv_send
    rtable = s3db.inv_recv
    tracktable = s3db.inv_track_item
    if not auth.s3_has_permission("update",
                                  stable,
                                  record_id=send_id):
        session.error = T("You do not have permission to return this sent shipment.")

    send_record = stable[send_id]
    if send_record.status == eden.inv.inv_ship_status["IN_PROCESS"]:
        session.error = T("This shipment has not been sent - it cannot be returned because it can still be edited.")

    if session.error:
        redirect(URL(c = "inv",
                     f = "send",
                     args = [send_id],
                     )
                 )

    # Okay no error so far, change the status to Returning
    stable[send_id] = dict(date = request.utcnow,
                           status = eden.inv.inv_ship_status["RETURNING"],
                           owned_by_user = None,
                           owned_by_group = ADMIN)
    recv_row = db(tracktable.send_id == send_id).select(tracktable.recv_id,
                                                        limitby = (0, 1)).first()
    if recv_row:
        recv_id = recv_row.recv_id
        rtable[recv_id] = dict(date = request.utcnow,
                               status = eden.inv.inv_ship_status["RETURNING"],
                               owned_by_user = None,
                               owned_by_group = ADMIN)
    # Set all track items to status of returning
    db(tracktable.send_id == send_id).update(status = eden.inv.inv_tracking_status["RETURNING"])
    session.confirmation = T("Sent Shipment has returned, indicate how many items will be returned to Warehouse.")

    redirect(URL(c = "inv",
                 f = "send",
                 args = [send_id, "track_item"]))
# -----------------------------------------------------------------------------
def return_process():
    """
        Return some stock from a shipment back into the warehouse
    """

    send_id = request.args[0]
    invtable = s3db.inv_inv_item
    stable = s3db.inv_send
    rtable = s3db.inv_recv
    tracktable = s3db.inv_track_item
    if not auth.s3_has_permission("update",
                                  stable,
                                  record_id=send_id):
        session.error = T("You do not have permission to return this sent shipment.")

    send_record = stable[send_id]
    if send_record.status != eden.inv.inv_ship_status["RETURNING"]:
        session.error = T("This shipment has not been returned.")

    if session.error:
        redirect(URL(c = "inv",
                     f = "send",
                     args = [send_id],
                     )
                 )

    # Okay no error so far, let's move the goods back into the warehouse
    # and then change the status to received
    # Update Receive record & lock for editing
    # Move each item to the site
    track_rows = db(tracktable.send_id == send_id).select()
    for track_item in track_rows:
        send_inv_id = track_item.send_inv_item_id
        return_qnty = track_item.return_quantity
        if return_qnty == None:
            return_qnty = 0
        # update the receive quantity in the tracking record
        tracktable[track_item.id] = dict (recv_quantity = track_item.quantity - return_qnty)
        if return_qnty:
            db(invtable.id == send_inv_id).update(quantity = invtable.quantity + return_qnty)


    stable[send_id] = dict(date = request.utcnow,
                           status = eden.inv.inv_ship_status["RECEIVED"],
                           owned_by_user = None,
                           owned_by_group = ADMIN)
    recv_row = db(tracktable.send_id == send_id).select(tracktable.recv_id,
                                                        limitby = (0, 1)).first()
    if recv_row:
        recv_id = recv_row.recv_id
        rtable[recv_id] = dict(date = request.utcnow,
                               status = eden.inv.inv_ship_status["RECEIVED"],
                               owned_by_user = None,
                               owned_by_group = ADMIN)
    # Change the status for all track items in this shipment to Received
    db(tracktable.send_id == send_id).update(status = eden.inv.inv_tracking_status["RECEIVED"])

    redirect(URL(c = "inv",
                 f = "send",
                 args = [send_id]))

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
    # Records can only be deleted if the status is In Process (or preparing)
    # so change the status before we delete
    db(tracktable.send_id == send_id).update(status = eden.inv.inv_tracking_status["IN_PROCESS"])
    track_rows = db(tracktable.send_id == send_id).select(tracktable.id)
    for track_item in track_rows:
        s3.inv_track_item_deleting(track_item.id)
    # Now change the status to (cancelled)
    db(tracktable.send_id == send_id).update(status = eden.inv.inv_tracking_status["CANCEL"])

    session.confirmation = T("Sent Shipment canceled and items returned to Warehouse")

    redirect(URL(c = "inv",
                 f = "send",
                 args = [send_id]))

# =============================================================================
def recv():
    """ RESTful CRUD controller """

    recvtable = s3db.inv_recv
    tracktable = s3db.inv_track_item
    atable = s3db.inv_adj_item

    # Limit site_id to sites the user has permissions for
    if settings.get_inv_shipment_name() == "order":
        error_msg = T("You do not have permission for any facility to add an order.")
    else:
        error_msg = T("You do not have permission for any facility to receive a shipment.")
    auth.permitted_facilities(table=recvtable, error_msg=error_msg)

    # The inv_recv record might be created when the shipment is send and so it
    # might not have the recipient identified. If it is null then set it to
    # the person who is logged in (the default)
    id = request.args(0)
    if id:
        try:
            if recvtable[id].recipient_id == None:
                db(recvtable.id == id).update(recipient_id = auth.s3_logged_in_person())
        except:
            pass

    status = s3db.inv_ship_status
    SHIP_STATUS_IN_PROCESS = status["IN_PROCESS"]
    SHIP_STATUS_SENT = status["SENT"]
    SHIP_STATUS_RECEIVED = status["RECEIVED"]
    SHIP_STATUS_CANCEL = status["CANCEL"]

    def set_recv_attr(status):
        recvtable.sender_id.readable = False
        recvtable.sender_id.writable = False
        recvtable.grn_status.readable = False
        recvtable.grn_status.writable = False
        recvtable.cert_status.readable = False
        recvtable.cert_status.writable = False
        recvtable.eta.readable = False
        recvtable.req_ref.writable = True
        if status == SHIP_STATUS_IN_PROCESS:
            recvtable.send_ref.writable = True
            recvtable.recv_ref.readable = False
            recvtable.sender_id.readable = False
        else:
            # Make all fields writable False
            for field in recvtable.fields:
                recvtable[field].writable = False
        if status == SHIP_STATUS_SENT:
            recvtable.recipient_id.readable = True
            recvtable.recipient_id.writable = True
            recvtable.comments.writable = True

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
            # show some fields
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
            # hide some fields
            tracktable.send_inv_item_id.readable = False
            # change some labels - NO - use consistent labels
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
        if (record and
            (record.status != SHIP_STATUS_IN_PROCESS and
             record.status != SHIP_STATUS_SENT)):
            # now that the shipment has been sent
            # lock the record so that it can't be meddled with
            s3db.configure("inv_recv",
                            create=False,
                            listadd=False,
                            editable=False,
                            deletable=False,
                           )
        if r.component and r.component.name == "track_item":
            # Set the track_item attributes
            # Can only create or delete track items for a recv record if the status is preparing
            if r.method == "create" or r.method == "delete":
                if record.status != SHIP_STATUS_IN_PROCESS:
                    return False
            if r.component_id:
                track_record = tracktable[r.component_id]
                set_track_attr(track_record.status)
            else:
                set_track_attr(TRACK_STATUS_PREPARING)
                tracktable.status.readable = False

            if r.record and r.record.status == SHIP_STATUS_IN_PROCESS:
                s3.crud_strings.inv_recv.title_update = \
                s3.crud_strings.inv_recv.title_display = T("Process Received Shipment")
                
            # Default the Supplier/Donor to the Org sending the shipment
            tracktable.supply_org_id.default = record.organisation_id
        else:
            # Set the recv attributes
            if r.id:
                record = recvtable[r.id]
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
        status = recvtable[request.args[0]].status
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
                            list_fields=list_fields,
                           )
        if status:
            # remove CRUD generated buttons in the tabs
            s3db.configure("inv_track_item",
                            create=False,
                            listadd=False,
                            editable=False,
                            deletable=False,
                           )
            if recvtable[request.args[0]].status == 2:
                s3db.configure("inv_track_item",
                                editable=True,
                               )

    output = s3_rest_controller(rheader=s3db.inv_recv_rheader)
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

    try:
        recv_id = request.args[0]
    except:
        redirect(URL(f="recv"))

    atable = s3db.inv_adj
    rtable = s3db.inv_recv
    stable = s3db.inv_send
    tracktable = s3db.inv_track_item
    siptable = s3db.supply_item_pack
    rrtable = s3db.req_req
    ritable = s3db.req_req_item

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
    code = s3db.inv_get_shipping_code(settings.get_inv_recv_shortname(),
                                      recv_record.site_id,
                                      s3db.inv_recv.recv_ref)
    rtable[recv_id] = dict(date = request.utcnow,
                           recv_ref = code,
                           status = eden.inv.inv_ship_status["RECEIVED"],
                           owned_by_user = None,
                           owned_by_group = ADMIN)
    send_row = db(tracktable.recv_id == recv_id).select(tracktable.send_id,
                                                        limitby=(0, 1)).first()
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
    # Move each item to the site
    track_rows = db(tracktable.recv_id == recv_id).select()
    for track_item in track_rows:
        row=Storage(track_item)
        s3.inv_track_item_onaccept(Storage(vars=Storage(id=row.id),
                                           record = row,
                                           )
                                  )

    session.confirmation = T("Shipment Items Received")
    redirect(URL(c = "inv",
                 f = "recv",
                 args = [recv_id]))

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
    stable = s3db.inv_send
    tracktable = s3db.inv_track_item
    inv_item_table = s3db.inv_inv_item
    ritable = s3db.req_req_item
    siptable = s3db.supply_item_pack
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
        inv_item_id = recv_item.recv_inv_item_id
        # This assumes that the inv_item has the quantity
        quantity = inv_item_table.quantity - recv_item.recv_quantity
        db(inv_item_table.id == inv_item_id).update(quantity = quantity)
        db(tracktable.recv_id == recv_id).update(status = 2) # In transit
        # @todo potential problem in that the send id should be the same for all track items but is not explicitly checked
        if send_id == None and recv_item.send_id != None:
            send_id = recv_item.send_id
    track_rows = db(tracktable.recv_id == recv_id).select()
    for track_item in track_rows:
        # if this is linked to a request
        # then remove these items from the quantity in fulfil
        if track_item.req_item_id:
            req_id = track_item.req_item_id
            req_item = ritable[req_id]
            req_quantity = req_item.quantity_fulfil
            req_pack_quantity = siptable[req_item.item_pack_id].quantity
            track_pack_quantity = siptable[track_item.item_pack_id].quantity
            quantity_fulfil = s3db.supply_item_add(req_quantity,
                                                   req_pack_quantity,
                                                   - track_item.recv_quantity,
                                                   track_pack_quantity
                                                  )
            db(ritable.id == req_id).update(quantity_fulfil = quantity_fulfil)
            s3db.req_update_status(req_id)
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

# =============================================================================
def track_item():
    """ RESTful CRUD controller """

    table = s3db.inv_track_item

    s3db.configure("inv_track_item",
                   create=False,
                   listadd=False,
                   insertable=False,
                   editable=False,
                   deletable=False,
                   )

    vars = request.get_vars
    if "report" in vars:
        if vars.report == "rel":
            s3.crud_strings["inv_track_item"] = Storage(
                                                        title_list = T("Summary of Releases"),
                                                        subtitle_list = T("Summary Details"),
                                                        title_search = T("Summary of Releases"),
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
                            orderby = "site_id",
                            sort = True
                            )
            s3.filter = (table.send_id != None)

        elif vars.report == "inc":
            s3.crud_strings["inv_track_item"] = Storage(
                                                        title_list = T("Summary of Incoming Supplies"),
                                                        subtitle_list = T("Summary Details"),
                                                        title_search = T("Summary of Incoming Supplies"),
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
                            orderby = "recipient_id",
                            )
            s3.filter = (table.recv_id != None)

        elif vars.report == "util":
            s3.crud_strings["inv_track_item"] = Storage(
                                                        title_list = T("Utilization Report"),
                                                        subtitle_list = T("Utilization Details"),
                                                        title_search = T("Utilization Report"),
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

            s3.filter = (table.item_id != None)

        elif vars.report == "exp":
            s3.crud_strings["inv_track_item"] = Storage(
                                                        title_list = T("Expiration Report"),
                                                        subtitle_list = T("Expiration Details"),
                                                        title_search = T("Expiration Report"),
                                                        )

            s3db.configure("inv_track_item",
                            list_fields = ["id",
                                           (T("Item/Description"), "item_id"),
                                           (T("Expiration Date"), "expiry_date"),
                                           (T("Source"), "supply_org_id"),
                                           (T("Unit"), "item_pack_id"),
                                           (T("Quantity"), "quantity"),
                                           (T("Unit Cost"), "pack_value"),
                                           (T("Total Cost"), "total_value"),
                                           ]
                            )
            s3.filter = (table.expiry_date != None)

    output = s3_rest_controller(rheader=s3db.inv_warehouse_rheader)
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
                if r.component_id:
                    aitable = s3db.inv_adj_item
                    if r.record.status == 0:
                        aitable.reason.writable = True
                    record = aitable[r.component_id]
                    if record.inv_item_id:
                        aitable.item_id.writable = False
                        aitable.item_id.comment = None
                        aitable.item_pack_id.writable = False
            else:
                # if an adjustment has been selected and it has been completed
                # then make the fields read only
                if r.record and r.record.status:
                    table.adjuster_id.writable = False
                    table.site_id.writable = False
                    table.comments.writable = False
                else:
                    if "item" in request.vars and "site" in request.vars:
                        # create a adj record with a single adj_item record
                        adj_id = table.insert(adjuster_id = auth.s3_logged_in_person(),
                                              site_id = request.vars.site,
                                              adjustment_date = request.utcnow,
                                              status = 0,
                                              category = 1,
                                              comments = "Single item adjustment"
                                              )
                        inv_item_table = s3db.inv_inv_item
                        inv_item = inv_item_table[request.vars.item]
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
                        if "site" in request.vars:
                            table.site_id.writable = True
                            table.site_id.default = request.vars.site
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            s3_action_buttons(r, deletable=False)
        return output
    s3.postp = postp

    if len(request.args) > 1 and request.args[1] == "adj_item" and table[request.args[0]].status:
        # remove CRUD generated buttons in the tabs
        s3db.configure("inv_adj_item",
                        create=False,
                        listadd=False,
                        editable=False,
                        deletable=False,
                       )

    output = s3_rest_controller(rheader=s3db.inv_adj_rheader)
    return output

# -----------------------------------------------------------------------------
def adj_close():
    """ RESTful CRUD controller """

    try:
        adj_id = request.args[0]
    except:
        redirect(URL(f="adj"))

    atable = s3db.inv_adj
    aitable = s3db.inv_adj_item
    inv_item_table = s3db.inv_inv_item

    # Limit site_id to sites the user has permissions for
    error_msg = T("You do not have permission to adjust the stock level in this warehouse.")
    auth.permitted_facilities(table=atable, error_msg=error_msg)

    adj_rec = atable[adj_id]
    if adj_rec.status != 0:
        session.error = T("This adjustment has already been closed.")

    if session.error:
        redirect(URL(c = "inv",
                     f = "adj",
                     args = [adj_id]))

    # Go through all the adj_items
    query = (aitable.adj_id == adj_id) & \
            (aitable.deleted == False)
    adj_items = db(query).select()
    for adj_item in adj_items:
        if adj_item.inv_item_id == None:
            # Create a new stock item
            inv_item_id = inv_item_table.insert(site_id = adj_rec.site_id,
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
                                                   adj_rec.site_id)
    url = URL(c = prefix,
              f = resourcename,
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

# -----------------------------------------------------------------------------
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
    records = db(query).select(istable.id,
                               istable.date,
                               stable.name,
                               ittable.quantity)

    json_str = "[%s,%s" % ( json.dumps(dict(id = str(T("Sent")),
                                            quantity = "#"
                                            )) ,
                            records.json()[1:])

    response.headers["Content-Type"] = "application/json"
    return json_str

# -----------------------------------------------------------------------------
def kit():
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def facility():
    return s3_rest_controller("org", rheader = s3db.org_facility_rheader)

# -----------------------------------------------------------------------------
def incoming():
    """ Incoming Shipments """

    # Defined in the Model for use from Multiple Controllers for unified menus
    return inv_incoming()

# -----------------------------------------------------------------------------
def req_match():
    """ Match Requests """

    return s3db.req_match()

# END =========================================================================
