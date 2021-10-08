# -*- coding: utf-8 -*-

"""
    Inventory Management

    A module to record inventories of items at a locations (sites),
    including Warehouses, Offices, Shelters & Hospitals
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return settings.customise_home(c, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the Warehouse Summary View
    s3_redirect_default(URL(f="warehouse",
                            args = "summary",
                            ))

# -----------------------------------------------------------------------------
def index2():
    """
        Alternative Application Home page
        - custom View
    """

    # Need CRUD String
    table = s3db.table("cr_shelter", None)

    module_name = settings.modules[c].get("name_nice")
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
                                   start = start,
                                   limit = limit,
                                   orderby = orderby,
                                   count = True,
                                   represent = True,
                                   )
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
                                     dt_ajax_url = URL(c = "inv",
                                                       f = "index2",
                                                       extension = "aadata",
                                                       vars = {"id":"warehouse_list_1"},
                                                       ),
                                     dt_group = 2,
                                     dt_searching = "true",
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
                                       limit = None,
                                       orderby = orderby,
                                       count = True
                                       )
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
                                       orderby = orderby,
                                       start = start,
                                       limit = limit,
                                       represent = True,
                                       )
                rfields = data["rfields"]
                rows = data["rows"]
                dt = S3DataTable(rfields,
                                 rows,
                                 orderby = orderby,
                                 )
                custom_actions = [{"label": s3_str(T("Warehouse")),
                                   "_class": "action-icon",
                                   "img": "/%s/static/img/markers/gis_marker.image.Agri_Commercial_Food_Distribution_Center_S1.png" % appname,
                                   "url": URL(c = "inv",
                                              f = "warehouse",
                                              args = ["[id]", "update"]
                                              )
                                   },
                                  ]
                dt.defaultActionButtons(resource, custom_actions)
                if representation == "html":
                    rows = current.db(table.quantity < 100.0).select(table.id, table.quantity)
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
                                        dt_action_col = -1,
                                        dt_ajax_url = URL(c = "inv",
                                                          f = "index2",
                                                          extension = "aadata",
                                                          vars = {"id":"inventory_list_1"},
                                                          ),
                                        dt_bulk_actions = "Adjust",
                                        dt_group = [1, 2],
                                        dt_group_totals = [formatted_site_list],
                                        dt_searching = "true",
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
                                        dt_action_col = -1,
                                        dt_bulk_actions = "Adjust",
                                        dt_group_totals = [formatted_site_list],
                                        )
                    return inventory
                else:
                    # Probably not the way to do it.... but
                    s3db.configure("inv_inv_item",
                                   list_fields = list_fields,
                                   report_groupby = "site_id",
                                   pdf_groupby = "site_id",
                                   )
                    s3.filter = filter
                    r = s3base.s3_request("inv", "inv_item",
                                          vars = {"orderby" : orderby},
                                          )
                    r.resource = resource
                    output = r(pdf_groupby = "site_id",
                               dt_group = 1,
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
                                   limit = None,
                                   orderby = orderby,
                                   count = True,
                                   represent = True
                                   )
            rows = data["rows"]
            rfields = data["rfields"]
            numrows = data["numrows"]
            dt = S3DataTable(rfields, rows)
            dt.defaultActionButtons(resource)
            if representation == "html":
                supply_items = dt.html(numrows,
                                       numrows,
                                       "supply_list_1",
                                       dt_action_col = 1,
                                       dt_ajax_url = URL(c = "inv",
                                                         f = "index2",
                                                         extension = "aadata",
                                                         vars = {"id": "supply_list_1"},
                                                         ),
                                       dt_pageLength = 10,
                                       )
            else:
                supply_items = dt.json(numrows,
                                       numrows,
                                       "supply_list_1",
                                       int(get_vars.draw),
                                       dt_action_col = 1,
                                       )
                return supply_items
        r = s3base.s3_request(prefix = "inv",
                              name = "inv_item",
                              )
        return {"module_name": module_name,
                "warehouses": warehouses,
                "inventory": inventory,
                "supply_items": supply_items,
                "r": r,
                }
        # End of TEST CODE
    return {"module_name": module_name,
            }

# =============================================================================
def warehouse():
    """
        RESTful CRUD controller
    """

    request_args = request.args
    if "viewing" in get_vars:
        viewing = get_vars.viewing
        tn, record_id = viewing.split(".", 1)
        if tn == "inv_warehouse":
            request_args.insert(0, record_id)

    # CRUD pre-process
    def prep(r):

        if r.component:
            component_name = r.component_name
            if component_name == "inv_item":
                # Filter out items which are already in this inventory
                from s3db.inv import inv_prep
                inv_prep(r)
                # Remove the Site Name from the list_fields
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
                from s3db.inv import inv_prep
                inv_prep(r)

                # Configure which fields in inv_recv are readable/writable
                # depending on status
                recvtable = s3db.inv_recv
                if r.component_id:
                    record = db(recvtable.id == r.component_id).select(recvtable.status,
                                                                       limitby = (0, 1),
                                                                       ).first()
                    from s3db.inv import inv_recv_attr
                    inv_recv_attr(record.status)
                else:
                    from s3db.inv import inv_recv_attr, inv_ship_status
                    inv_recv_attr(inv_ship_status["IN_PROCESS"])
                    recvtable.recv_ref.readable = False
                    if r.method and r.method != "read":
                        # Don't want to see in Create forms
                        recvtable.status.readable = False

            elif component_name == "send":
                # Filter out items which are already in this inventory
                from s3db.inv import inv_prep
                inv_prep(r)

            elif component_name == "human_resource":
                from s3db.org import org_site_staff_config
                org_site_staff_config(r)

            elif component_name == "layout" and \
                 r.method != "hierarchy":
                from s3db.org import org_site_layout_config
                org_site_layout_config(r.record.site_id)

            elif component_name == "req":
                if r.method != "update" and r.method != "read":
                    # Hide fields which don't make sense in a Create form
                    # inc list_create (list_fields over-rides)
                    from s3db.inv import inv_req_create_form_mods
                    inv_req_create_form_mods(r)

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
                # Stay within Site tab
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
                read_url = URL(f="warehouse",
                               args = ["[id]", "inv_item"],
                               )
                update_url = URL(f="warehouse",
                                 args = ["[id]", "inv_item"],
                                 )
                s3_action_buttons(r,
                                  read_url = read_url,
                                  update_url = update_url)
        else:
            cname = r.component_name
            if cname == "human_resource":
                # Modify action button to open staff instead of human_resource
                read_url = URL(c="hrm", f="staff",
                               args = ["[id]"],
                               )
                update_url = URL(c="hrm", f="staff",
                                 args = ["[id]", "update"],
                                 )
                s3_action_buttons(r,
                                  read_url = read_url,
                                  #delete_url = delete_url,
                                  update_url = update_url,
                                  )

        # Handled via insertable
        #if isinstance(output, dict) and \
        #   "add_btn" in output:
        #    del output["add_btn"]
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

    from s3db.inv import inv_rheader
    return s3_rest_controller(#hide_filter = {"inv_item": False,
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
                              rheader = inv_rheader,
                              )

# -----------------------------------------------------------------------------
def warehouse_type():
    """
        RESTful CRUD controller
    """

    return s3_rest_controller()

# =============================================================================
def inv_item():
    """ REST Controller """

    # Tab already has correct URL:
    # If this url has a viewing track items then redirect to track_movement
    #viewing = get_vars.get("viewing", None)
    #if viewing:
    #    tn, record_id = viewing.split(".", 1)
    #    if tn == "inv_track_item":
    #        table = s3db.inv_track_item
    #        record = db(table.id == record_id).select(table.item_id,
    #                                                  limitby = (0, 1),
    #                                                  ).first()
    #        redirect(URL(c = "inv",
    #                     f = "track_movement",
    #                     args = [],
    #                     vars = {"viewing" : "%s.%s" % ("inv_inv_item", record.item_id)}
    #                     ))

    #tablename = "inv_inv_item"
    # Load model to be able to override CRUD string(s)
    #table = s3db[tablename]

    if settings.get_inv_direct_stock_edits():
        # Limit site_id to sites the user has permissions for
        auth.permitted_facilities(table = s3db.inv_inv_item,
                                  error_msg = T("You do not have permission for any site to add an inventory item."))

    # This is done via track_movement:
    #if len(request.args) > 1 and request.args[1] == "track_item":
    #    # remove CRUD generated buttons in the tabs
    #    s3db.configure("inv_track_item",
    #                   editable = False,
    #                   deletable = False,
    #                   insertable = False,
    #                   )

    def prep(r):
        #if r.method != "report":
        #    s3.dataTable_group = 1
        if r.component:
            if r.component_name == "adj_item":
                s3db.configure("inv_adj_item",
                               deletable = False,
                               editable = False,
                               insertable = False,
                               )
        else:
            if settings.get_inv_direct_stock_edits():
                # Limit to Bins from this site
                if s3.debug:
                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_item.js" % r.application)
                else:
                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_item.min.js" % r.application)
                if r.record:
                    site_id = r.record.site_id
                    f = r.table.layout_id
                    # We can't update this dynamically
                    #f.requires.other.set_filter(filterby = "site_id",
                    #                            filter_opts = [site_id],
                    #                            )
                    f.widget.filter = (s3db.org_site_layout.site_id == site_id)
                    f.comment.args = [site_id, "layout", "create"]

            tablename = "inv_inv_item"
            s3.crud_strings[tablename].msg_list_empty = T("No Stock currently registered")

            if r.method == "report":
                # Quantity 0 can still be used for managing Stock Replenishment
                s3.filter = (r.table.quantity != 0)

            report = get_vars.get("report")
            if report == "mon":
                s3.crud_strings[tablename].update({"title_list": T("Monetization Report"),
                                                   "subtitle_list": T("Monetization Details"),
                                                   #"msg_list_empty": T("No Stock currently registered"),
                                                   })
                s3db.configure(tablename,
                               list_fields = [(T("Donor"), "supply_org_id"),
                                              (T("Items/Description"), "item_id"),
                                              (T("Quantity"), "quantity"),
                                              (T("Unit"), "item_pack_id"),
                                              (T("Unit Value"), "pack_value"),
                                              (T("Total Value"), "total_value"),
                                              (T("Remarks"), "comments"),
                                              "status",
                                              ]
                               )
            # Already done in the model:
            #else:
            #    s3db.configure(tablename,
            #                   insertable = settings.get_inv_direct_stock_edits(),
            #                   list_fields = ["site_id",
            #                                  "item_id",
            #                                  "item_id$code",
            #                                  "item_id$item_category_id",
            #                                  "quantity",
            #                                  "pack_value",
            #                                  #(T("Total Value"), "total_value"),
            #                                  ]
            #                   )

        return True
    s3.prep = prep

    # Import pre-process
    def import_prep(data):
        """
            Process option to Delete all Stock records of the Organisation/Branch
            before processing a new data import
        """
        if s3.import_replace:
            resource, tree = data
            if tree is not None:
                xml = current.xml
                tag = xml.TAG
                att = xml.ATTRIBUTE

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

    def postp(r, output):
        if r.interactive and \
           r.component_name == "adj_item":
            # Add Button for New Adjustment
            _href = URL(c="inv", f="adj",
                        vars = {"item": r.id,
                                "site": r.record.site_id,
                                },
                        )
            add_btn = s3base.S3CRUD.crud_button(label = T("New Adjustment"),
                                                _href = _href,
                                                _id = "add-btn",
                                                )
            if settings.ui.formstyle == "bootstrap":
                add_btn.add_class("btn btn-primary")
            else:
                add_btn.add_class("action-btn")
            output["buttons"] = {"add_btn": add_btn,
                                 }
        return output
    s3.postp = postp

    from s3db.inv import inv_rheader
    return s3_rest_controller(#csv_extra_fields = [{"label": "Organisation",
                              #                     "field": s3db.org_organisation_id(comment = None)
                              #                     },
                              #                    ],
                              pdf_orientation = "Landscape",
                              pdf_table_autogrow = "B",
                              pdf_groupby = "site_id, item_id",
                              pdf_orderby = "expiry_date, supply_org_id",
                              replace_option = T("Remove existing data before import"),
                              rheader = inv_rheader,
                              )

# =============================================================================
def recv():
    """ RESTful CRUD controller """

    from s3db.inv import inv_recv_controller
    return inv_recv_controller()

# -----------------------------------------------------------------------------
def send():
    """ RESTful CRUD controller """

    from s3db.inv import inv_send_controller
    return inv_send_controller()

# -----------------------------------------------------------------------------
def track_item():
    """ RESTful CRUD controller """

    table = s3db.inv_track_item

    s3db.configure("inv_track_item",
                   deletable = False,
                   editable = False,
                   insertable = False,
                   )

    report = get_vars.get("report")
    if report == "rel":
        # Summary of Releases
        s3.crud_strings["inv_track_item"] = Storage(title_list = T("Summary of Releases"),
                                                    subtitle_list = T("Summary Details"),
                                                    )
        list_fields = [#"send_id",
                       #"req_item_id",
                       (T("Date Released"), "send_id$date"),
                       (T("Beneficiary"), "send_id$site_id"),
                       (settings.get_inv_send_shortname(), "send_id$send_ref"),
                       (T("Items/Description"), "item_id"),
                       (T("Source"), "supply_org_id"),
                       (T("Unit"), "item_pack_id"),
                       (T("Quantity"), "quantity"),
                       (T("Unit Cost"), "pack_value"),
                       (T("Total Cost"), "total_value"),
                       ]
        if settings.get_inv_send_req():
            list_fields.insert(3, (settings.get_inv_req_shortname(), "send_id$req.req_ref"))
        elif settings.get_inv_send_req_ref():
            list_fields.insert(3, (settings.get_inv_req_shortname(), "send_id$req_ref"))

        s3db.configure("inv_track_item",
                       list_fields = list_fields,
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
                       list_fields = [(T("Date Received"), "recv_id$date"),
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

        list_fields = [(T("Item/Description"), "item_id$name"),
                       (T("Beneficiary"), "send_id$site_id"),
                       (settings.get_inv_send_shortname(), "send_id$send_ref"),
                       (T("Items/Description"), "item_id"),
                       (T("Source"), "supply_org_id"),
                       (T("Unit"), "item_pack_id"),
                       (T("Quantity"), "quantity"),
                       (T("Unit Cost"), "pack_value"),
                       (T("Total Cost"), "total_value"),
                       ]
        if settings.get_inv_send_req():
            list_fields.insert(3, (settings.get_inv_req_shortname(), "send_id$req.req_ref"))
        elif settings.get_inv_send_req_ref():
            list_fields.insert(3, (settings.get_inv_req_shortname(), "send_id$req_ref"))

        s3db.configure("inv_track_item",
                       list_fields = list_fields,
                       )

        s3.filter = (FS("item_id") != None)

    elif report == "exp":
        # Expiration Report
        s3.crud_strings["inv_track_item"] = Storage(title_list = T("Expiration Report"),
                                                    subtitle_list = T("Expiration Details"),
                                                    )

        s3db.configure("inv_track_item",
                       list_fields = ["recv_inv_item_id$site_id",
                                      (T("Item/Description"), "item_id"),
                                      (T("Expiration Date"), "expiry_date"),
                                      (T("Source"), "supply_org_id"),
                                      (T("Unit"), "item_pack_id"),
                                      (T("Quantity"), "quantity"),
                                      (T("Unit Cost"), "pack_value"),
                                      (T("Total Cost"), "total_value"),
                                      ],
                       )

        s3.filter = (FS("expiry_date") != None)

    from s3db.inv import inv_rheader
    return s3_rest_controller(rheader = inv_rheader)

# -----------------------------------------------------------------------------
def track_movement():
    """ REST Controller """

    table = s3db.inv_track_item

    s3db.configure("inv_track_item",
                   deletable = False,
                   editable = False,
                   insertable = False,
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

    from s3db.inv import inv_rheader
    return s3_rest_controller("inv", "track_item",
                              rheader = inv_rheader,
                              )

# =============================================================================
def req():
    """
        REST Controller for Inventory Requisitions
    """

    # Don't show Templates
    from s3 import FS
    s3.filter = (FS("is_template") == False)

    # Hide completed Requisitions by default
    from s3 import s3_set_default_filter
    if settings.get_inv_req_workflow():
        # 1: Draft
        # 2: Submitted
        # 3: Approved
        s3_set_default_filter("~.workflow_status",
                              [1, 2, 3],
                              tablename = "inv_req")
    else:
        # REQ_STATUS_NONE     = 0
        # REQ_STATUS_PARTIAL  = 1
        s3_set_default_filter("~.fulfil_status",
                              [0, 1],
                              tablename = "inv_req")
                          

    return req_controller()

# -----------------------------------------------------------------------------
def req_template():
    """
        REST Controller for Inventory Requisition Templates
    """

    # Hide fields which aren't relevant to templates
    table = s3db.inv_req
    field = table.is_template
    field.default = True
    field.readable = field.writable = False
    s3.filter = (field == True)

    settings.inv.req_prompt_match = False

    if "req_item" in request.args:
        # List fields for req_item
        table = s3db.inv_req_item
        list_fields = ["item_id",
                       "item_pack_id",
                       "quantity",
                       "comments",
                       ]
        s3db.configure("inv_req_item",
                       list_fields = list_fields,
                       )

    else:
        # Main Req
        fields = ["req_ref",
                  "date",
                  "date_required",
                  "date_required_until",
                  "date_recv",
                  "recv_by_id",
                  "cancel",
                  "commit_status",
                  "transit_status",
                  "fulfil_status",
                  ]
        for fieldname in fields:
            field = table[fieldname]
            field.readable = field.writable = False
        table.purpose.label = T("Details")
        list_fields = ["site_id"
                       "priority",
                       "purpose",
                       "comments",
                       ]
        s3db.configure("inv_req",
                       list_fields = list_fields,
                       )

        # CRUD strings
        s3.crud_strings["inv_req"] = Storage(
            label_create = T("Create Request Template"),
            title_display = T("Request Template Details"),
            title_list = T("Request Templates"),
            title_update = T("Edit Request Template"),
            label_list_button = T("List Request Templates"),
            label_delete_button = T("Delete Request Template"),
            msg_record_created = T("Request Template Added"),
            msg_record_modified = T("Request Template Updated"),
            msg_record_deleted = T("Request Template Deleted"),
            msg_list_empty = T("No Request Templates"))

    return req_controller(template = True)

# -----------------------------------------------------------------------------
def marker_fn(record):
    """
        Function to decide which Marker to use for Inventory Requisitions Map
    """

    # Base Icon based on Type
    marker = "asset"

    # Colour code by priority
    priority = record.priority
    if priority == 3:
        # High
        marker = "%s_red" % marker
    elif priority == 2:
        # Medium
        #marker = "%s_orange" % marker
        marker = "%s_yellow" % marker
    #elif priority == 1:
    #    # Low
    #    marker = "%s_yellow" % marker

    mtable = db.gis_marker
    marker = db(mtable.name == marker).select(mtable.image,
                                              mtable.height,
                                              mtable.width,
                                              cache = s3db.cache,
                                              limitby = (0, 1),
                                              ).first()
    return marker

# -----------------------------------------------------------------------------
def req_controller(template = False):
    """ REST Controller """

    REQ_STATUS_PARTIAL  = 1
    REQ_STATUS_COMPLETE = 2

    def prep(r):

        table = r.table

        record = r.record
        use_workflow = settings.get_inv_req_workflow()
        workflow_status = record.workflow_status if record else None

        if r.interactive:
            inv_item_id = get_vars.get("inv_item_id")
            if inv_item_id:
                # Called from action buttons on req/req_item_inv_item/x page
                req_item_id = get_vars.get("req_item_id")
                if not auth.s3_has_permission("update", "inv_req_item", record_id=req_item_id):
                    r.unauthorised()
                # Set the req_item.site_id (Requested From)
                iitable = s3db.inv_inv_item
                inv_item = db(iitable.id == inv_item_id).select(iitable.site_id,
                                                                iitable.item_id,
                                                                limitby = (0, 1),
                                                                ).first()
                site_id = inv_item.site_id
                # @ToDo: Avoid DB updates in GETs
                #        - JS to catch the GET & convert to POST (like searchRewriteAjaxOptions in s3.filter.js)
                db(s3db.inv_req_item.id == req_item_id).update(site_id = site_id)
                onaccepts = s3db.get_config("inv_req_item", "onaccept")
                if onaccepts:
                    record = Storage(id = req_item_id,
                                     req_id = r.id,
                                     site_id = site_id,
                                     )
                    form = Storage(vars = record)
                    if not isinstance(onaccepts, (list, tuple)):
                        onaccepts = [onaccepts]
                    [onaccept(form) for onaccept in onaccepts]

                from s3db.org import org_SiteRepresent
                from s3db.supply import supply_ItemRepresent
                response.confirmation = T("%(item)s requested from %(site)s") % \
                    {"item": supply_ItemRepresent()(inv_item.item_id),
                     "site": org_SiteRepresent()(site_id)
                     }
            elif "req.site_id" in get_vars:
                # Called from 'Make new request' button on [siteinstance]/req page
                table.site_id.default = get_vars.get("req.site_id")
                table.site_id.writable = False
                if r.http == "POST":
                    del r.get_vars["req.site_id"]

            table.date_recv.readable = table.date_recv.writable = True

            if settings.get_inv_req_ask_purpose():
                table.purpose.label = T("What the Items will be used for")
            table.site_id.label = T("Deliver To")
            table.request_for_id.label = T("Deliver To")
            # Keep consistency, don't change
            #table.requester_id.label = T("Site Contact")
            table.recv_by_id.label = T("Delivered To")

            if r.component:
                if r.component_name == "document":
                    s3.crud.submit_button = T("Add")
                    # Simplify a little
                    table = s3db.doc_document
                    table.url.readable = table.url.writable = False
                    table.date.readable = table.date.writable = False
                    # @ToDo: Fix for Link Table
                    #table.date.default = r.record.date
                    #if r.record.site_id:
                    #    stable = db.org_site
                    #    query = (stable.id == r.record.site_id)
                    #    site = db(query).select(stable.location_id,
                    #                            stable.organisation_id,
                    #                            limitby = (0, 1),
                    #                            ).first()
                    #    if site:
                    #        table.location_id.default = site.location_id
                    #        table.organisation_id.default = site.organisation_id

                elif r.component_name == "req_item":
                    ctable = r.component.table
                    ctable.site_id.writable = ctable.site_id.readable = False
                    if not settings.get_inv_req_item_quantities_writable():
                        ctable.quantity_commit.readable = \
                        ctable.quantity_commit.writable = False
                        ctable.quantity_transit.readable = \
                        ctable.quantity_transit.writable = False
                        ctable.quantity_fulfil.readable = \
                        ctable.quantity_fulfil.writable = False
                    if use_workflow and workflow_status in (3, 4, 5): # Approved, Completed, Cancelled
                        # Lock all fields
                        s3db.configure("inv_req_item",
                                       deletable = False,
                                       editable = False,
                                       insertable = False,
                                       )

                elif r.component.alias == "job":
                    s3task.configure_tasktable_crud(
                        function = "inv_req_add_from_template",
                        args = [r.id],
                        vars = {"user_id": 0 if auth.user is None else auth.user.id},
                        period = 86400, # seconds, so 1 day
                        )
                    db.scheduler_task.timeout.writable = False
            else:
                if r.id:
                    table.is_template.readable = table.is_template.writable = False

                keyvalue = settings.get_ui_auto_keyvalue()
                if keyvalue:
                    # What Keys do we have?
                    kvtable = s3db.inv_req_tag
                    keys = db(kvtable.deleted == False).select(kvtable.tag,
                                                               distinct = True,
                                                               )
                    if keys:
                        tablename = "inv_req"
                        crud_fields = [f for f in table.fields if table[f].readable]
                        cappend = crud_fields.append
                        add_component = s3db.add_components
                        list_fields = s3db.get_config(tablename,
                                                      "list_fields")
                        lappend = list_fields.append
                        for key in keys:
                            tag = key.tag
                            label = T(tag.title())
                            cappend(S3SQLInlineComponent("tag",
                                                         label = label,
                                                         name = tag,
                                                         multiple = False,
                                                         fields = [("", "value")],
                                                         filterby = {"field": "tag",
                                                                     "options": tag,
                                                                     },
                                                         ))
                            add_component(tablename,
                                          org_organisation_tag = {"name": tag,
                                                                  "joinby": "req_id",
                                                                  "filterby": "tag",
                                                                  "filterfor": (tag,),
                                                                  },
                                          )
                            lappend((label, "%s.value" % tag))
                        crud_form = S3SQLCustomForm(*crud_fields)
                        s3db.configure(tablename,
                                       crud_form = crud_form,
                                       )

                method = r.method
                if method is None:
                    method = "update" if r.id else "create"
                if method == "create":
                    # Hide fields which don't make sense in a Create form
                    # - includes one embedded in list_create
                    # - list_fields over-rides, so still visible within list itself
                    from s3db.inv import inv_req_create_form_mods
                    inv_req_create_form_mods(r)

                    if settings.get_inv_req_inline_forms():
                        # Use inline form
                        from s3db.inv import inv_req_inline_form
                        inv_req_inline_form(method)

                    # Get the default Facility for this user
                    # Use site_id in User Profile
                    if auth.is_logged_in() and not table.site_id.default:
                        table.site_id.default = auth.user.site_id

                elif method in ("update", "read"):
                    if settings.get_inv_req_inline_forms():
                        # Use inline form
                        from s3db.inv import inv_req_inline_form
                        inv_req_inline_form(method)
                    if use_workflow and workflow_status in (1, 2, 5): # Draft, Submitted, Cancelled
                        # Hide individual statuses
                        table = db.inv_req
                        table.commit_status.readable = table.commit_status.writable = False
                        table.transit_status.readable = table.transit_status.writable = False
                        table.fulfil_status.readable = table.fulfil_status.writable = False
                    if method != "read":
                        s3.scripts.append("/%s/static/scripts/S3/s3.req_update.js" % appname)
                        if use_workflow and workflow_status in (3, 4, 5): # Approved, Completed, Cancelled
                            # Lock all fields
                            s3db.configure("inv_req",
                                           editable = False,
                                           )
                    if use_workflow and workflow_status not in (1, 2, 5, None): # Draft, Submitted, Cancelled or Legacy
                        # Block Delete
                        s3db.configure("inv_req",
                                       deletable = False,
                                       )

                elif method == "map":
                    # Tell the client to request per-feature markers
                    s3db.configure("inv_req",
                                   marker_fn = marker_fn,
                                   )

        elif r.representation == "plain":
            # Map Popups
            pass

        elif r.representation == "geojson":
            # Default anyway
            # from s3db.inv import inv_ReqRefRepresent
            #table.req_ref.represent = inv_ReqRefRepresent()
            # Load these models now as they'll be needed when we encode
            mtable = s3db.gis_marker
            s3db.configure("inv_req",
                           marker_fn = marker_fn,
                           )

        if r.component:
            if r.component_name == "req_item":
                record = r.record
                if record: # Check as options.s3json checks the component without a record
                    if s3.debug:
                        s3.scripts.append("/%s/static/scripts/S3/s3.inv_req_item.js" % r.application)
                    else:
                        s3.scripts.append("/%s/static/scripts/S3/s3.inv_req_item.min.js" % r.application)
                    # Prevent Adding/Deleting Items from Requests which are complete, closed or cancelled
                    # @ToDo: deployment_setting to determine which exact rule to apply?
                    if record.fulfil_status == REQ_STATUS_COMPLETE or \
                       record.transit_status == REQ_STATUS_COMPLETE or \
                       record.req_status == REQ_STATUS_COMPLETE or \
                       record.fulfil_status == REQ_STATUS_PARTIAL or \
                       record.transit_status == REQ_STATUS_PARTIAL or \
                       record.req_status == REQ_STATUS_PARTIAL or \
                       record.closed or \
                       record.cancel:
                        s3db.configure("inv_req_item",
                                       deletable = False,
                                       insertable = False,
                                       )

            elif r.component_name == "commit":

                table = r.component.table
                record = r.record
                record_id = record.id

                stable = s3db.org_site

                commit_status = record.commit_status
                if (commit_status == 2) and settings.get_inv_req_restrict_on_complete():
                    # Restrict from committing to completed requests
                    insertable = False
                else:
                    # Allow commitments to be added when doing so as a component
                    insertable = True

                # Limit site_id to permitted sites which have not
                # yet committed to this request
                current_site = None
                if r.component_id:
                    query = (table.id == r.component_id) & \
                            (table.deleted == False)
                    commit = db(query).select(table.site_id,
                                              limitby = (0, 1),
                                              ).first()
                    if commit:
                        current_site = commit.site_id

                allowed_sites = auth.permitted_facilities(redirect_on_error=False)
                if current_site and current_site not in allowed_sites:
                    table.site_id.writable = False
                else:
                    # Committing sites
                    query = (table.req_id == record_id) & \
                            (table.deleted == False)
                    commits = db(query).select(table.site_id)
                    committing_sites = set(c.site_id for c in commits)

                    # Acceptable sites
                    acceptable = set(allowed_sites) - committing_sites
                    if current_site:
                        acceptable.add(current_site)
                    if acceptable:
                        query = (stable.site_id.belongs(acceptable)) & \
                                (stable.deleted == False)
                        sites = db(query).select(stable.id,
                                                 stable.code,
                                                 orderby = stable.code,
                                                 )
                        site_opts = OrderedDict((s.id, s.code) for s in sites)
                        table.site_id.requires = IS_IN_SET(site_opts)
                    else:
                        if r.method == "create":
                            # Can't commit if we have no acceptable sites
                            # TODO do not redirect if site is not required,
                            #      e.g. org-only commits of skills
                            error_msg = T("You do not have permission for any facility to make a commitment.")
                            current.session.error = error_msg
                            redirect(r.url(component="", method=""))
                        else:
                            insertable = False

                s3db.configure(table,
                               # Don't want filter_widgets in the component view
                               filter_widgets = None,
                               insertable = insertable,
                               )

                if r.interactive:
                    # Dropdown not Autocomplete
                    itable = s3db.inv_commit_item
                    itable.req_item_id.widget = None
                    itable.req_item_id.requires = \
                                    IS_ONE_OF(db, "inv_req_item.id",
                                              s3db.inv_req_item_represent,
                                              filterby = "req_id",
                                              filter_opts = [r.id],
                                              orderby = "inv_req_item.id",
                                              sort = True,
                                              )
                    s3.jquery_ready.append('''
$.filterOptionsS3({
 'trigger':{'alias':'commit_item','name':'req_item_id'},
 'target':{'alias':'commit_item','name':'item_pack_id'},
 'scope':'row',
 'lookupPrefix':'req',
 'lookupResource':'req_item_packs',
 'lookupKey':'req_item_id',
 'lookupField':'id',
 'msgNoRecords':i18n.no_packs,
 'fncPrep':S3.supply.fncPrepItem,
 'fncRepresent':S3.supply.fncRepresentItem
})''')
                    # Custom Form
                    s3forms = s3base.s3forms
                    crud_form = s3forms.S3SQLCustomForm(
                            "site_id",
                            "date",
                            "date_available",
                            "committer_id",
                            s3forms.S3SQLInlineComponent(
                                "commit_item",
                                label = T("Items"),
                                fields = ["req_item_id",
                                          "item_pack_id",
                                          "quantity",
                                          "comments"
                                          ]
                            ),
                            "comments",
                        )
                    s3db.configure("inv_commit",
                                   crud_form = crud_form,
                                   )
                    # Redirect to the Items tab after creation
                    #s3db.configure(table,
                    #               create_next = URL(c="inv", f="commit",
                    #                                 args=["[id]", "commit_item"]),
                    #               update_next = URL(c="inv", f="commit",
                    #                                 args=["[id]", "commit_item"]))

                
        else:
            # Not r.component
            # Limit site_id to facilities the user has permissions for
            # @ToDo: Non-Item requests shouldn't be bound to a Facility?
            auth.permitted_facilities(table=r.table,
                                      error_msg=T("You do not have permission for any facility to make a request."))
            if r.id:
                # Prevent Deleting Requests which are complete or closed
                record = r.record
                if record.fulfil_status == REQ_STATUS_COMPLETE or \
                   record.transit_status == REQ_STATUS_COMPLETE or \
                   record.req_status == REQ_STATUS_COMPLETE or \
                   record.fulfil_status == REQ_STATUS_PARTIAL or \
                   record.transit_status == REQ_STATUS_PARTIAL or \
                   record.req_status == REQ_STATUS_PARTIAL or \
                   record.closed:
                    s3db.configure("inv_req",
                                   deletable = False,
                                   )

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):

        if r.interactive:
            if r.method is None:
                # Customise Action Buttons
                if r.component:
                    s3_action_buttons(r, deletable = s3db.get_config(r.component.tablename, "deletable"))
                    if r.component_name == "req_item" and \
                       settings.get_inv_req_prompt_match():
                        s3.actions.append(
                            {"label": s3_str(T("Request from Facility")),
                             "url": URL(c = "inv",
                                        f = "req_item_inv_item",
                                        args = ["[id]"],
                                        ),
                             "_class": "action-btn",
                             })

                    elif r.component_name == "commit":
                        if "form" in output:
                            # User has Write access
                            req_id = r.record.id
                            ctable = s3db.inv_commit
                            query = (ctable.deleted == False) & \
                                    (ctable.req_id == req_id)
                            exists = current.db(query).select(ctable.id,
                                                              limitby = (0, 1),
                                                              )
                            if not exists:
                                s3.rfooter = A(T("Commit All"),
                                               _href = URL(args = [req_id,
                                                                   "commit_all",
                                                                   ]),
                                               _class = "action-btn",
                                               _id = "commit-btn",
                                               )
                                s3.jquery_ready.append('''S3.confirmClick('#commit-btn','%s')''' \
                                                % T("Do you want to commit to this request?"))
                            # Items
                            s3.actions.append({"label": s3_str(T("Prepare Shipment")),
                                               "url": URL(c = "inv",
                                                          f = "send_commit",
                                                          args = ["[id]"],
                                                          ),
                                               "_class": "action-btn send-btn",
                                               })
                            s3.jquery_ready.append('''S3.confirmClick('.send-btn','%s')''' \
                                        % T("Are you sure you want to send this shipment?"))

                    elif r.component.alias == "job":
                        record_id = r.id
                        s3.actions = [{"label": s3_str(T("Open")),
                                       "url": URL(c="inv",
                                                  f="req_template",
                                                  args = [record_id, "job", "[id]"],
                                                  ),
                                       "_class": "action-btn",
                                       },
                                      {"label": s3_str(T("Reset")),
                                       "url": URL(c="inv",
                                                  f="req_template",
                                                  args = [record_id, "job", "[id]", "reset"],
                                                  ),
                                       "_class": "action-btn",
                                       },
                                      {"label": s3_str(T("Run Now")),
                                       "url": URL(c="inv",
                                                  f="req_template",
                                                  args = [record_id, "job", "[id]", "run"],
                                                  ),
                                       "_class": "action-btn",
                                       },
                                      ]

                else:
                    # No Component
                    if r.http == "POST":
                        # Create form
                        # @ToDo: DRY
                        if not settings.get_inv_req_inline_forms():
                            form_vars = output["form"].vars
                            # Stock: Open Tab for Items
                            r.next = URL(args = [form_vars.id, "req_item"])
                    else:
                        s3_action_buttons(r, deletable =False)
                        if not template and settings.get_inv_use_commit():
                            # This is appropriate to both Items and People
                            s3.actions.append({"label": s3_str(T("Commit")),
                                               "url": URL(c = "inv",
                                                          f = "req",
                                                          args = ["[id]", "commit_all"],
                                                          ),
                                               "_class": "action-btn commit-btn",
                                               })
                            s3.jquery_ready.append('''S3.confirmClick('.commit-btn','%s')''' \
                                            % T("Do you want to commit to this request?"))
                        #s3.actions.append({"label": s3_str(T("View Items")),
                        #                   "url": URL(c = "inv",
                        #                              f = "req",
                        #                              args = ["[id]", "req_item"],
                        #                              ),
                        #                   "_class": "action-btn",
                        #                   })
                        if settings.get_inv_req_copyable():
                            s3.actions.append({"label": s3_str(T("Copy")),
                                               "url": URL(c = "inv",
                                                          f = "req",
                                                          args = ["[id]", "copy_all"],
                                                          ),
                                               "_class": "action-btn copy_all",
                                               })
                            s3.jquery_ready.append('''S3.confirmClick('.copy_all','%s')''' % \
                                T("Are you sure you want to create a new request as a copy of this one?"))
                        if not template:
                            if settings.get_inv_use_commit():
                                s3.actions.append({"label": s3_str(T("Send")),
                                                   "url": URL(c = "inv",
                                                              f = "req",
                                                              args = ["[id]", "commit_all", "send"],
                                                              ),
                                                   "_class": "action-btn send-btn dispatch",
                                                   })
                                s3.jquery_ready.append('''S3.confirmClick('.send-btn','%s')''' % \
                                    T("Are you sure you want to commit to this request and send a shipment?"))
                            elif auth.user and auth.user.site_id:
                                s3.actions.append({# Better to force users to go through the Check process
                                                   #"label": s3_str(T("Send")),
                                                   #"url": URL(c = "inv",
                                                   #           f = "send_req",
                                                   #           args = ["[id]"],
                                                   #           vars = {"site_id": auth.user.site_id},
                                                   #           ),
                                                   "label": s3_str(T("Check")),
                                                   "url": URL(c = "inv",
                                                              f = "req",
                                                              args = ["[id]", "check"],
                                                              ),
                                                   "_class": "action-btn send-btn dispatch",
                                                   })
                                s3.jquery_ready.append('''S3.confirmClick('.send-btn','%s')''' % \
                                    T("Are you sure you want to send a shipment for this request?"))

                        # Add delete button for those records which are not completed
                        # @ToDo: Handle icons
                        table = r.table
                        query = (table.fulfil_status != REQ_STATUS_COMPLETE) & \
                                (table.transit_status != REQ_STATUS_COMPLETE) & \
                                (table.req_status != REQ_STATUS_COMPLETE) & \
                                (table.fulfil_status != REQ_STATUS_PARTIAL) & \
                                (table.transit_status != REQ_STATUS_PARTIAL) & \
                                (table.req_status != REQ_STATUS_PARTIAL)
                        rows = db(query).select(table.id)
                        restrict = [str(row.id) for row in rows]
                        s3.actions.append({"label": s3_str(s3.crud_labels.DELETE),
                                           "url": URL(c = "inv",
                                                      f = "req",
                                                      args = ["[id]", "delete"],
                                                      ),
                                           "_class": "delete-btn",
                                           "restrict": restrict,
                                           })

            elif r.method == "create" and r.http == "POST":
                # Create form
                # @ToDo: DRY
                if not settings.get_inv_req_inline_forms():
                    form_vars = output["form"].vars
                    # Stock: Open Tab for Items
                    r.next = URL(args = [form_vars.id, "req_item"])

        return output
    s3.postp = postp

    from s3db.inv import inv_req_rheader
    return s3_rest_controller("inv", "req",
                              rheader = inv_req_rheader,
                              )

# =============================================================================
def req_item():
    """
        RESTful CRUD controller for Request Items

        @ToDo: Filter out fulfilled Items?
    """

    # Filter out Template Items
    #if request.function != "fema":
    s3.filter = (FS("req_id$is_template") == False)

    def order_item(r, **attr):
        """
            Create an inv_order_item from a inv_req_item
        """

        record = r.record
        req_id = record.req_id

        s3db.inv_order_item.insert(req_item_id = record.id,
                                   req_id = req_id,
                                   item_id = record.item_id,
                                   item_pack_id = record.item_pack_id,
                                   quantity = record.quantity,
                                   )

        session.confirmation = T("Item added to your list of Purchases")
        # Redirect back to the Request's Items tab
        redirect(URL(c="inv", f="req",
                     args = [req_id, "req_item"]
                     ))

    s3db.set_method("inv", "req_item",
                    method = "order",
                    action = order_item
                    )

    def prep(r):

        if r.interactive or r.representation == "aadata":

            list_fields = s3db.get_config("inv_req_item", "list_fields")
            list_fields.insert(1, "req_id$site_id")
            levels = gis.get_relevant_hierarchy_levels()
            levels.reverse()
            for level in levels:
                lfield = "req_id$site_id$location_id$%s" % level
                list_fields.insert(1, lfield)
            s3db.configure("inv_req_item",
                           insertable = False,
                           list_fields = list_fields,
                           )

            s3.crud_strings["inv_req_item"].title_list = T("Requested Items")
            if r.method != None and r.method != "update" and r.method != "read":
                # Hide fields which don't make sense in a Create form
                # - includes one embedded in list_create
                # - list_fields over-rides, so still visible within list itself
                if not settings.get_inv_req_item_quantities_writable():
                    table = r.table
                    table.quantity_commit.readable = \
                    table.quantity_commit.writable = False
                    table.quantity_transit.readable = \
                    table.quantity_transit.writable = False
                    table.quantity_fulfil.readable = \
                    table.quantity_fulfil.writable = False

        return True
    s3.prep = prep

    output = s3_rest_controller("inv", "req_item")

    if settings.get_inv_req_prompt_match():
        req_item_inv_item_btn = {"label": s3_str(T("Request from Facility")),
                                 "url": URL(c = "inv",
                                            f = "req_item_inv_item",
                                            args = ["[id]"],
                                            ),
                                 "_class": "action-btn",
                                 }
        if s3.actions:
            s3.actions.append(req_item_inv_item_btn)
        else:
            s3.actions = [req_item_inv_item_btn]

    return output

# -----------------------------------------------------------------------------
def req_item_inv_item():
    """
        Shows the inventory items which match a requested item
    """

    req_item_id  = request.args[0]
    request.args = []
    ritable = s3db.inv_req_item
    req_item = db(ritable.id == req_item_id).select(ritable.req_id,
                                                    ritable.item_id,
                                                    ritable.quantity,
                                                    ritable.quantity_commit,
                                                    ritable.quantity_transit,
                                                    ritable.quantity_fulfil,
                                                    limitby = (0, 1),
                                                    ).first()
    req_id = req_item.req_id
    rtable = s3db.inv_req
    req = db(rtable.id == req_id).select(rtable.site_id,
                                         rtable.requester_id,
                                         rtable.date,
                                         rtable.date_required,
                                         rtable.priority,
                                         limitby = (0, 1),
                                         ).first()
    site_id = req.site_id

    output = {}

    output["title"] = T("Request Stock from Available Warehouse")
    output["req_btn"] = A(T("Return to Request"),
                          _href = URL(c="inv", f="req",
                                      args = [req_id, "req_item"]
                                      ),
                          _class = "action-btn"
                          )

    output["req_item"] = TABLE(TR(TH( "%s: " % T("Requested By") ),
                                  rtable.site_id.represent(site_id),
                                  TH( "%s: " % T("Item")),
                                  ritable.item_id.represent(req_item.item_id),
                                  ),
                               TR(TH( "%s: " % T("Requester") ),
                                  rtable.requester_id.represent(req.requester_id),
                                  TH( "%s: " % T("Quantity")),
                                  req_item.quantity,
                                  ),
                               TR(TH( "%s: " % T("Date Requested") ),
                                  rtable.date.represent(req.date),
                                  TH( T("Quantity Committed")),
                                  req_item.quantity_commit,
                                  ),
                               TR(TH( "%s: " % T("Date Required") ),
                                  rtable.date_required.represent(req.date_required),
                                  TH( "%s: " % T("Quantity in Transit")),
                                  req_item.quantity_transit,
                                  ),
                               TR(TH( "%s: " % T("Priority") ),
                                  rtable.priority.represent(req.priority),
                                  TH( "%s: " % T("Quantity Fulfilled")),
                                  req_item.quantity_fulfil,
                                  )
                               )

    s3.no_sspag = True # pagination won't work with 2 datatables on one page @todo: test

    itable = s3db.inv_inv_item
    # Get list of matching inventory items
    s3.filter = (itable.item_id == req_item.item_id) & \
                (itable.site_id != site_id)
    # Tweak CRUD String for this context
    s3.crud_strings["inv_inv_item"].msg_list_empty = T("No Inventories currently have this item in stock")

    inv_items = s3_rest_controller("inv", "inv_item")
    output["items"] = inv_items["items"]

    if settings.get_supply_use_alt_name():
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
    else:
        output["items_alt"] = None

    if settings.get_inv_req_order_item():
        output["order_btn"] = A(T("Order Item"),
                                _href = URL(c="inv", f="req_item",
                                            args = [req_item_id, "order"]
                                            ),
                                _class = "action-btn"
                                )
    else:
        output["order_btn"] = None

    s3.actions = [{"label": s3_str(T("Request From")),
                   "url": URL(c = "inv",
                              f = "req",
                              args = [req_id, "req_item"],
                              vars = {"inv_item_id": "[id]",
                                      # Not going to this record as we want the list of items next without a redirect
                                      "req_item_id": req_item_id,
                                      },
                              ),
                   "_class": "action-btn",
                   }
                  ]

    response.view = "inv/req_item_inv_item.html"
    return output

# =============================================================================
def commit():
    """
        RESTful CRUD controller for Commits
    """

    def prep(r):
        if r.interactive and r.record:
            # Commitments created through UI should be done via components
            if r.component:
                if r.component_name == "commit_item":
                    # Dropdown not Autocomplete
                    s3db.inv_commit_item.req_item_id.widget = None

                    # Limit commit items to items from the request
                    s3db.inv_commit_item.req_item_id.requires = \
                        IS_ONE_OF(db, "inv_req_item.id",
                                  s3db.inv_req_item_represent,
                                  filterby = "req_id",
                                  filter_opts = [r.record.req_id],
                                  orderby = "inv_req_item.id",
                                  sort = True,
                                  )
            else:
                # No Component
                table = r.table
                s3.crud.submit_button = T("Save Changes")
                # Limit site_id to facilities the user has permissions for
                auth.permitted_facilities(table = table,
                                          error_msg = T("You do not have permission for any facility to make a commitment.") )

                table.site_id.comment = A(T("Set as default Site"),
                                          _id = "inv_commit_site_id_link",
                                          _target = "_blank",
                                          _href = URL(c = "default",
                                                      f = "user",
                                                      args = ["profile"]
                                                      ))

                jappend = s3.jquery_ready.append
                jappend('''
$('#inv_commit_site_id_link').click(function(){
 var site_id=$('#inv_commit_site_id').val()
 if(site_id){
  var url = $('#inv_commit_site_id_link').attr('href')
  var exists=url.indexOf('?')
  if(exists=='-1'){
   $('#inv_commit_site_id_link').attr('href',url+'?site_id='+site_id)
  }
 }
 return true
})''')
                # Dropdown not Autocomplete
                s3db.inv_commit_item.req_item_id.widget = None

                # Options updater for inline items
                jappend('''
$.filterOptionsS3({
 'trigger':{'alias':'commit_item','name':'req_item_id'},
 'target':{'alias':'commit_item','name':'item_pack_id'},
 'scope':'row',
'lookupPrefix':'req',
'lookupResource':'req_item_packs',
'lookupKey':'req_item_id',
'lookupField':'id',
'msgNoRecords':i18n.no_packs,
'fncPrep':S3.supply.fncPrepItem,
'fncRepresent':S3.supply.fncRepresentItem
})''')
                # Custom Form
                from s3 import S3SQLCustomForm, S3SQLInlineComponent
                crud_form = S3SQLCustomForm("site_id",
                                            "date",
                                            "date_available",
                                            "committer_id",
                                            S3SQLInlineComponent(
                                                "commit_item",
                                                label = T("Items"),
                                                fields = ["req_item_id",
                                                          "item_pack_id",
                                                          "quantity",
                                                          "comments"
                                                          ]
                                                ),
                                            "comments",
                                            )
                s3db.configure("inv_commit",
                               crud_form = crud_form,
                               )

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                # Items
                s3_action_buttons(r)
                s3.actions.append({"label": s3_str(T("Prepare Shipment")),
                                   "url": URL(f = "send_commit",
                                              args = ["[id]"],
                                              ),
                                   "_class": "action-btn send-btn dispatch",
                                   })
                confirm = T("Are you sure you want to send this shipment?")
                s3.jquery_ready.append('''S3.confirmClick('.send-btn','%s')''' % confirm)

        return output
    s3.postp = postp

    return s3_rest_controller(rheader = commit_rheader)

# -----------------------------------------------------------------------------
def commit_rheader(r):
    """ Resource Header for Commitments """

    if r.representation == "html":
        record = r.record
        if record and r.name == "commit":

            s3_date_represent = s3base.S3DateTime.date_represent

            tabs = [(T("Edit Details"), None),
                    (T("Items"), "commit_item"),
                    ]

            table = r.table
            #req_record = db.inv_req[record.req_id]
            #req_date = req_record.date
            rheader = DIV(TABLE(TR(TH("%s: " % table.req_id.label),
                                   table.req_id.represent(record.req_id),
                                   ),
                                TR(TH("%s: " % T("Committing Warehouse")),
                                   s3db.org_site_represent(record.site_id),
                                   TH("%s: " % T("Commit Date")),
                                   s3_date_represent(record.date),
                                   ),
                                TR(TH("%s: " % table.comments.label),
                                   TD(record.comments or "", _colspan=3)
                                   ),
                                ),
                            )
            prepare_btn = A(T("Prepare Shipment"),
                            _href = URL(f = "send_commit",
                                        args = [record.id]
                                        ),
                            _id = "send-commit",
                            _class = "action-btn"
                            )

            s3.rfooter = TAG[""](prepare_btn)

            #send_btn = A(T("Send Commitment as Shipment"),
            #             _href = URL(f = "send_commit",
            #                         args = [record.id]
            #                         ),
            #             _id = "send-commit",
            #             _class = "action-btn"
            #             )

            #send_btn_confirm = SCRIPT("S3.confirmClick('#send-commit', '%s')" %
            #                          T("Do you want to send these Committed items?") )
            #s3.rfooter = TAG[""](send_btn,send_btn_confirm)
            #rheader.append(send_btn)
            #rheader.append(send_btn_confirm)

            rheader_tabs = s3_rheader_tabs(r, tabs)
            rheader.append(rheader_tabs)

            return rheader
    return None

# -----------------------------------------------------------------------------
def commit_item():
    """
        RESTful CRUD controller for Commit Items
    """

    return s3_rest_controller()

# =============================================================================
def adj():
    """
        RESTful CRUD controller for Stock Adjustments
    """

    table = s3db.inv_adj

    # Limit site_id to sites the user has permissions for
    error_msg = T("You do not have permission to adjust the stock level in this warehouse.")
    auth.permitted_facilities(table = table,
                              error_msg = error_msg)

    def prep(r):
        if r.interactive:
            if r.component:
                if r.component_name == "adj_item":
                    aitable = s3db.inv_adj_item
                    adj_status = r.record.status
                    if adj_status:
                        s3db.configure("inv_adj_item",
                                       deletable = False,
                                       editable = False,
                                       insertable = False,
                                       )
                    if r.component_id:
                        if adj_status == 0:
                            aitable.reason.writable = True
                        record = db(aitable.id == r.component_id).select(aitable.inv_item_id,
                                                                         limitby = (0, 1),
                                                                         ).first()
                        if record.inv_item_id:
                            aitable.item_id.writable = False
                            aitable.item_id.comment = None
                            aitable.item_pack_id.writable = False

                    # Limit to Bins from this site
                    from s3db.org import org_site_layout_config
                    org_site_layout_config(r.record.site_id, aitable.layout_id)

                elif r.component_name == "image":
                    doc_table = s3db.doc_image
                    doc_table.organisation_id.readable = doc_table.organisation_id.writable = False
                    doc_table.person_id.readable = doc_table.person_id.writable = False
                    doc_table.location_id.readable = doc_table.location_id.writable = False
            else:
                if r.record:
                    if r.record.status:
                        # Don't allow modifying completed adjustments
                        #table.adjuster_id.writable = False
                        #table.comments.writable = False
                        s3db.configure("inv_adj",
                                       deletable = False,
                                       editable = False,
                                       )
                    else:
                        # Don't allow switching Site after Adjustment created as the Items in the Adjustment match the original Site
                        table.site_id.writable = False
                else:
                    if "item" in get_vars and "site" in get_vars:
                        # Create a adj record with a single adj_item record
                        # e.g. coming from New Adjustment button on inv/inv_item/x/adj_item tab
                        # e.g. coming from Adjust Stock Item button on inv/site/inv_item/x tab
                        # @ToDo: This should really be a POST, not a GET
                        inv_item_table = s3db.inv_inv_item
                        inv_item = db(inv_item_table.id == get_vars.item).select(inv_item_table.id,
                                                                                 inv_item_table.item_id,
                                                                                 inv_item_table.item_pack_id,
                                                                                 inv_item_table.quantity,
                                                                                 inv_item_table.currency,
                                                                                 inv_item_table.status,
                                                                                 inv_item_table.pack_value,
                                                                                 inv_item_table.expiry_date,
                                                                                 inv_item_table.layout_id,
                                                                                 inv_item_table.owner_org_id,
                                                                                 limitby = (0, 1),
                                                                                 ).first()
                        item_id = inv_item.item_id
                        adj_id = table.insert(adjuster_id = auth.s3_logged_in_person(),
                                              site_id = get_vars.site,
                                              adjustment_date = request.utcnow,
                                              status = 0,
                                              category = 1,
                                              comments = "Adjust %s" % inv_item_table.item_id.represent(item_id, show_link=False),
                                              )
                        adjitemtable = s3db.inv_adj_item
                        adj_item_id = adjitemtable.insert(reason = 0,
                                                          adj_id = adj_id,
                                                          inv_item_id = inv_item.id, # original source inv_item
                                                          item_id = item_id, # the supply item
                                                          item_pack_id = inv_item.item_pack_id,
                                                          old_quantity = inv_item.quantity,
                                                          currency = inv_item.currency,
                                                          old_status = inv_item.status,
                                                          new_status = inv_item.status,
                                                          old_pack_value = inv_item.pack_value,
                                                          new_pack_value = inv_item.pack_value,
                                                          expiry_date = inv_item.expiry_date,
                                                          layout_id = inv_item.layout_id,
                                                          old_owner_org_id = inv_item.owner_org_id,
                                                          new_owner_org_id = inv_item.owner_org_id,
                                                          )
                        redirect(URL(c = "inv",
                                     f = "adj",
                                     args = [adj_id,
                                             "adj_item",
                                             adj_item_id,
                                             "update",
                                             ]
                                     ))
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

    from s3db.inv import inv_adj_rheader
    return s3_rest_controller(rheader = inv_adj_rheader)

# -----------------------------------------------------------------------------
def adj_item():
    """
        RESTful CRUD controller for Adjustment Items
        - just used for options.s3json lookups
    """

    s3.prep = lambda r: \
        r.representation == "s3json" and r.method == "options"

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def kitting():
    """
        RESTful CRUD controller for Kitting
    """

    from s3db.inv import inv_rheader
    return s3_rest_controller(rheader = inv_rheader)

# -----------------------------------------------------------------------------
def stock_card():
    """
        RESTful CRUD controller for Stock Cards
    """

    viewing = get_vars.get("viewing")
    if viewing:
        get_vars.pop("viewing")
        inv_item_id = viewing.split("inv_inv_item.")[1]
        table = s3db.inv_inv_item
        inv_item = db(table.id == inv_item_id).select(table.site_id,
                                                      table.item_id,
                                                      table.item_source_no,
                                                      table.expiry_date,
                                                      limitby = (0, 1),
                                                      ).first()
        if inv_item:
            item_source_no = inv_item.item_source_no
            table = s3db.inv_stock_card
            query = (table.site_id == inv_item.site_id) & \
                    (table.item_id == inv_item.item_id) & \
                    (table.item_source_no == item_source_no) & \
                    (table.expiry_date == inv_item.expiry_date)
            exists = db(query).select(table.id,
                                      limitby = (0, 1),
                                      ).first()
            if exists:
                request.args = [str(exists.id), "stock_log"]

    def postp(r, output):
        # Don't render any Action Buttons
        # @ToDo: Also remove ID column...can't see how currently
        s3.actions = []
        return output
    s3.postp = postp


    from s3db.inv import inv_rheader
    return s3_rest_controller(rheader = inv_rheader)

# -----------------------------------------------------------------------------
def minimum():
    """
        RESTful CRUD Controller for Stock Minimums
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def order_item():
    """
        RESTful CRUD Controller for Order Items
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def package():
    """
        RESTful CRUD Controller for Packages (Boxes & Pallets)
    """

    if s3.debug:
        s3.scripts.append("/%s/static/scripts/S3/s3.inv_package.js" % appname)
    else:
        s3.scripts.append("/%s/static/scripts/S3/s3.inv_package.min.js" % appname)

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def req_approver():
    """
        RESTful CRUD Controller for Requisition Approvers
    """

    # We need a more complex control: leave to template
    #if not auth.s3_has_role("ADMIN"):
    #    s3.filter = auth.filter_by_root_org(s3db.req_approver)

    return s3_rest_controller()

# =============================================================================
def facility():
    # Open record in this controller after creation
    s3db.configure("org_facility",
                   create_next = URL(c="inv", f="facility",
                                     args = ["[id]", "read"]),
                   )

    from s3db.org import org_facility_controller
    return org_facility_controller()

# -----------------------------------------------------------------------------
def facility_type():
    return s3_rest_controller("org")

# -----------------------------------------------------------------------------
def project():
    """
        Simpler version of Projects for use within Inventory module
    """

    # Load default Model
    s3db.project_project

    crud_form = s3base.S3SQLCustomForm("organisation_id",
                                       "code",
                                       "name",
                                       "end_date",
                                       )

    list_fields = ["organisation_id",
                   "code",
                   "name",
                   "end_date",
                   ]

    s3db.configure("project_project",
                   crud_form = crud_form,
                   filter_widgets = None,
                   list_fields = list_fields,
                   )

    return s3_rest_controller("project")

# -----------------------------------------------------------------------------
def project_req():
    """
        RESTful CRUD controller
        - just used for options.s3json lookups
    """

    s3.prep = lambda r: \
        r.representation == "s3json" and r.method == "options"

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def donor():
    """
        Filtered version of the organisation() REST controller
    """

    # @ToDo: This should be a deployment setting
    get_vars["organisation_type.name"] = \
        "Academic,Bilateral,Government,Intergovernmental,NGO,UN agency"

    # Load model (including normal CRUD strings)
    table = s3db.org_organisation

    # Modify CRUD Strings
    s3.crud_strings.org_organisation = Storage(
        label_create = T("Create Donor"),
        title_display = T("Donor Details"),
        title_list = T("Donors"),
        title_update = T("Edit Donor"),
        title_upload = T("Import Donors"),
        label_list_button = T("List Donors"),
        label_delete_button = T("Delete Donor"),
        msg_record_created = T("Donor added"),
        msg_record_modified = T("Donor updated"),
        msg_record_deleted = T("Donor deleted"),
        msg_list_empty = T("No Donors currently registered")
        )

    # Open record in this controller after creation
    s3db.configure("org_organisation",
                   create_next = URL(c="inv", f="donor",
                                     args = ["[id]", "read"]),
                   )

    # NB Type gets defaulted in the Custom CRUD form
    # - user needs create permissions for org_organisation_organisation_type
    from s3db.org import org_organisation_controller
    return org_organisation_controller()

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

    # NB Type gets defaulted in the Custom CRUD form
    # - user needs create permissions for org_organisation_organisation_type
    from s3db.org import org_organisation_controller
    return org_organisation_controller()

# =============================================================================
def commit_req():
    """
        Function to commit items for a Request
        - i.e. copy data from a req into a commitment
        arg: req_id
        vars: site_id

        @ToDo: Rewrite as Method
    """

    req_id = request.args[0]
    site_id = request.vars.get("site_id")

    # User must have permissions over facility which is sending
    (prefix, resourcename, id) = s3db.get_instance(s3db.org_site, site_id)
    if not site_id or not auth.s3_has_permission("update",
                                                 "%s_%s" % (prefix,
                                                            resourcename,
                                                            ),
                                                 record_id = id
                                                 ):
        session.error = T("You do not have permission to make this commitment.")
        redirect(URL(c="inv", f="req",
                     args = [req_id],
                     ))

    # Create a new commit record
    commit_id = s3db.inv_commit.insert(date = request.utcnow,
                                       req_id = req_id,
                                       site_id = site_id,
                                       )

    # Only select items which are in the warehouse
    ritable = s3db.inv_req_item
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
                                 iitable.item_pack_id,
                                 )

    citable = s3db.inv_commit_item
    for req_item in req_items:
        req_pack_quantity = req_item.inv_req_item.pack_quantity()
        req_item_quantity = req_item.inv_req_item.quantity * req_pack_quantity

        inv_item_quantity = req_item.inv_inv_item.quantity * \
                            req_item.inv_inv_item.pack_quantity()

        if inv_item_quantity > req_item_quantity:
            commit_item_quantity = req_item_quantity
        else:
            commit_item_quantity = inv_item_quantity
        commit_item_quantity = commit_item_quantity / req_pack_quantity

        if commit_item_quantity:
            req_item_id = req_item.inv_req_item.id

            commit_item = {"commit_id": commit_id,
                           "req_item_id": req_item_id,
                           "item_pack_id": req_item.inv_req_item.item_pack_id,
                           "quantity": commit_item_quantity,
                           }

            commit_item_id = citable.insert(**commit_item)
            commit_item["id"] = commit_item_id

            s3db.onaccept("inv_commit_item", commit_item)

    # Redirect to commit
    redirect(URL(c="inv", f="commit",
                 args = [commit_id, "commit_item"],
                 ))

# -----------------------------------------------------------------------------
def send_commit():
    """
        Send a Shipment containing all items in a Commitment

        @ToDo: Rewrite as Method
    """

    from s3db.inv import inv_send_commit
    return inv_send_commit()

# -----------------------------------------------------------------------------
def req_match():
    """ Match Requests """

    from s3db.inv import inv_req_match
    return inv_req_match()

# -----------------------------------------------------------------------------
def send_req():
    """
        Function to send items for a Request.
        - i.e. copy data from a req into a send
        arg: req_id
        vars: site_id

        Currently not exposed to UI
        - deemed better to force users through Check process

        @ToDo: Rewrite as Method
    """

    req_id = request.args[0]
    site_id = request.vars.get("site_id", None)
    table = s3db.inv_req
    r_req = db(table.id == req_id).select(#table.req_ref, # req_ref is for external Request systems
                                          table.requester_id,
                                          table.site_id,
                                          limitby = (0, 1),
                                          ).first()

    # User must have permissions over facility which is sending
    (prefix, resourcename, id) = s3db.get_instance(db.org_site, site_id)
    if not site_id or not auth.s3_has_permission("update",
                                                 "%s_%s" % (prefix,
                                                            resourcename,
                                                            ),
                                                 record_id = id,
                                                 ):
        session.error = T("You do not have permission to send this shipment.")
        redirect(URL(c="inv", f="req",
                     args = [req_id],
                     ))

    ritable = s3db.inv_req_item
    iitable = s3db.inv_inv_item
    sendtable = s3db.inv_send
    tracktable = s3db.inv_track_item
    siptable = s3db.supply_item_pack

    # Get the items for this request that have not been fulfilled or in transit
    sip_id_field = siptable.id
    sip_quantity_field = siptable.quantity
    query = (ritable.req_id == req_id) & \
            (ritable.quantity_transit < ritable.quantity) & \
            (ritable.deleted == False) & \
            (ritable.item_pack_id == sip_id_field)
    req_items = db(query).select(ritable.id,
                                 ritable.quantity,
                                 ritable.quantity_transit,
                                 ritable.quantity_fulfil,
                                 ritable.item_id,
                                 sip_quantity_field,
                                 )

    if not req_items:
        # Can't use site_name as gluon/languages.py def translate has a str() which can give a Unicode error
        #site_name = s3db.org_site_represent(site_id, show_link=False)
        session.warning = \
            T("This request has no items outstanding!")

        # Redirect to view the list of items in the Request
        redirect(URL(c="inv", f="req",
                     args = [req_id, "req_item"])
                 )

    # Create a new send record
    from s3db.supply import supply_get_shipping_code as get_shipping_code
    code = get_shipping_code(settings.get_inv_send_shortname(),
                             site_id,
                             sendtable.send_ref
                             )
    from s3db.inv import inv_ship_status
    send_id = sendtable.insert(send_ref = code,
                               #req_ref = r_req.req_ref,
                               sender_id = auth.s3_logged_in_person(),
                               site_id = site_id,
                               date = request.utcnow,
                               recipient_id = r_req.requester_id,
                               to_site_id = r_req.site_id,
                               status = inv_ship_status["IN_PROCESS"],
                               )
    s3db.inv_send_req.insert(send_id = send_id,
                             req_id = req_id,
                             )

    # Loop through each request item and find matches in the site inventory
    # - don't match items which are expired or in bad condition
    from s3db.inv import inv_tracking_status, inv_remove
    IN_PROCESS = inv_tracking_status["IN_PROCESS"]
    insert = tracktable.insert
    ii_item_id_field = iitable.item_id
    ii_quantity_field = iitable.quantity
    ii_expiry_field = iitable.expiry_date
    ii_purchase_field = iitable.purchase_date
    iifields = [iitable.id,
                ii_item_id_field,
                ii_quantity_field,
                iitable.item_pack_id,
                iitable.pack_value,
                iitable.currency,
                ii_expiry_field,
                ii_purchase_field,
                iitable.layout_id,
                iitable.owner_org_id,
                iitable.supply_org_id,
                sip_quantity_field,
                iitable.item_source_no,
                ]
    bquery = (ii_quantity_field > 0) & \
             (iitable.site_id == site_id) & \
             (iitable.deleted == False) & \
             (iitable.item_pack_id == sip_id_field) & \
             ((iitable.expiry_date >= request.now) | ((iitable.expiry_date == None))) & \
             (iitable.status == 0)
    orderby = ii_expiry_field | ii_purchase_field

    no_match = True

    for ritem in req_items:
        rim = ritem.inv_req_item
        rim_id = rim.id
        query = bquery & \
                (ii_item_id_field == rim.item_id)
        inv_items = db(query).select(*iifields,
                                     orderby = orderby
                                     )

        if len(inv_items) == 0:
            continue
        no_match = False
        one_match = len(inv_items) == 1
        # Get the Quantity Needed
        quantity_shipped = max(rim.quantity_transit, rim.quantity_fulfil)
        quantity_needed = (rim.quantity - quantity_shipped) * ritem.supply_item_pack.quantity
        # Insert the track item records
        # If there is more than one item match then we select the stock with the oldest expiry date first
        # then the oldest purchase date first
        # then a complete batch, if-possible
        iids = []
        append = iids.append
        for item in inv_items:
            if not quantity_needed:
                break
            iitem = item.inv_inv_item
            if one_match:
                # Remove this total from the warehouse stock
                send_item_quantity = inv_remove(iitem, quantity_needed)
                quantity_needed -= send_item_quantity
                append(iitem.id)
            else:
                quantity_available = iitem.quantity * item.supply_item_pack.quantity
                if iitem.expiry_date:
                    # We take first from the oldest expiry date
                    send_item_quantity = min(quantity_needed, quantity_available)
                    # Remove this total from the warehouse stock
                    send_item_quantity = inv_remove(iitem, send_item_quantity)
                    quantity_needed -= send_item_quantity
                    append(iitem.id)
                elif iitem.purchase_date:
                    # We take first from the oldest purchase date for non-expiring stock
                    send_item_quantity = min(quantity_needed, quantity_available)
                    # Remove this total from the warehouse stock
                    send_item_quantity = inv_remove(iitem, send_item_quantity)
                    quantity_needed -= send_item_quantity
                    append(iitem.id)
                elif quantity_needed <= quantity_available:
                    # Assign a complete batch together if possible
                    # Remove this total from the warehouse stock
                    send_item_quantity = inv_remove(iitem, quantity_needed)
                    quantity_needed = 0
                    append(iitem.id)
                else:
                    # Try again on the second loop, if-necessary
                    continue

            insert(send_id = send_id,
                   send_inv_item_id = iitem.id,
                   item_id = iitem.item_id,
                   req_item_id = rim_id,
                   item_pack_id = iitem.item_pack_id,
                   quantity = send_item_quantity,
                   recv_quantity = send_item_quantity,
                   status = IN_PROCESS,
                   pack_value = iitem.pack_value,
                   currency = iitem.currency,
                   layout_id = iitem.layout_id,
                   expiry_date = iitem.expiry_date,
                   owner_org_id = iitem.owner_org_id,
                   supply_org_id = iitem.supply_org_id,
                   item_source_no = iitem.item_source_no,
                   #comments = comment,
                   )
        # 2nd pass
        for item in inv_items:
            if not quantity_needed:
                break
            iitem = item.inv_inv_item
            if iitem.id in iids:
                continue
            # We have no way to know which stock we should take 1st, so show all with quantity 0 & let the user decide
            send_item_quantity = 0
            insert(send_id = send_id,
                   send_inv_item_id = iitem.id,
                   item_id = iitem.item_id,
                   req_item_id = rim_id,
                   item_pack_id = iitem.item_pack_id,
                   quantity = send_item_quantity,
                   status = IN_PROCESS,
                   pack_value = iitem.pack_value,
                   currency = iitem.currency,
                   layout_id = iitem.layout_id,
                   expiry_date = iitem.expiry_date,
                   owner_org_id = iitem.owner_org_id,
                   supply_org_id = iitem.supply_org_id,
                   item_source_no = iitem.item_source_no,
                   #comments = comment,
                   )

    if no_match:
        # Can't use %(site_name)s as gluon/languages.py def translate has a str() which can give a Unicode error
        #site_name = s3db.org_site_represent(site_id, show_link=False)
        session.warning = \
            T("This site has no items exactly matching this request. There may still be other items in stock which can fulfill this request!")

    # Redirect to view the list of items in the Send
    redirect(URL(c="inv", f="send",
                 args = [send_id, "track_item"],
                 )
             )

# -----------------------------------------------------------------------------
def send_returns():
    """
        This will return a shipment that has been sent

        @ToDo: Rewrite as Method
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
                                                  limitby = (0, 1),
                                                  ).first()
    inv_ship_status = s3db.inv_ship_status
    if send_record.status == inv_ship_status["IN_PROCESS"]:
        session.error = T("This shipment has not been sent - it cannot be returned because it can still be edited.")

    if session.error:
        redirect(URL(c="inv", f="send",
                     args = [send_id],
                     ))

    rtable = s3db.inv_recv
    tracktable = s3db.inv_track_item

    # Okay no error so far, change the status to Returning
    #ADMIN = auth.get_system_roles().ADMIN
    db(stable.id == send_id).update(status = inv_ship_status["RETURNING"],
                                    #owned_by_user = None,
                                    #owned_by_group = ADMIN,
                                    )
    recv_row = db(tracktable.send_id == send_id).select(tracktable.recv_id,
                                                        limitby = (0, 1),
                                                        ).first()
    if recv_row:
        recv_id = recv_row.recv_id
        db(rtable.id == recv_id).update(date = request.utcnow,
                                        status = inv_ship_status["RETURNING"],
                                        #owned_by_user = None,
                                        #owned_by_group = ADMIN,
                                        )
    # Set all track items to status of returning
    from s3db.inv import inv_tracking_status
    db(tracktable.send_id == send_id).update(status = inv_tracking_status["RETURNING"])
    session.confirmation = T("Sent Shipment has returned, indicate how many items will be returned to Warehouse.")

    redirect(URL(c="inv", f="send",
                 args = [send_id, "track_item"],
                 ))

# -----------------------------------------------------------------------------
def return_process():
    """
        Return some stock from a shipment back into the warehouse

        @ToDo: Rewrite as Method
    """

    try:
        send_id = request.args[0]
    except:
        redirect(f="send")

    stable = s3db.inv_send
    if not auth.s3_has_permission("update", stable, record_id=send_id):
        session.error = T("You do not have permission to return this sent shipment.")

    send_record = db(stable.id == send_id).select(stable.status,
                                                  stable.site_id,
                                                  limitby = (0, 1),
                                                  ).first()
    from s3db.inv import inv_ship_status
    if send_record.status != inv_ship_status["RETURNING"]:
        session.error = T("This shipment has not been returned.")

    if session.error:
        redirect(URL(c="inv", f="send",
                     args = [send_id],
                     ))

    invtable = s3db.inv_inv_item
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
        db(tracktable.id == track_item.id).update(recv_quantity = track_item.quantity - return_qnty)
        if return_qnty:
            db(invtable.id == send_inv_id).update(quantity = invtable.quantity + return_qnty)

    #ADMIN = auth.get_system_roles().ADMIN
    db(stable.id == send_id).update(status = inv_ship_status["RECEIVED"],
                                    #owned_by_user = None,
                                    #owned_by_group = ADMIN,
                                    )
    recv_row = db(tracktable.send_id == send_id).select(tracktable.recv_id,
                                                        limitby = (0, 1),
                                                        ).first()
    if recv_row:
        recv_id = recv_row.recv_id
        db(s3db.inv_recv.id == recv_id).update(date = request.utcnow,
                                               status = inv_ship_status["RECEIVED"],
                                               #owned_by_user = None,
                                               #owned_by_group = ADMIN,
                                               )

    # Change the status for all track items in this shipment to Received
    from s3db.inv import inv_tracking_status
    db(tracktable.send_id == send_id).update(status = inv_tracking_status["RECEIVED"])

    if settings.get_inv_warehouse_free_capacity_calculated():
        # Update the Warehouse Free capacity
        from s3db.inv import inv_warehouse_free_capacity
        inv_warehouse_free_capacity(send_record.site_id)

    redirect(URL(f = "send",
                 args = [send_id],
                 ))

# -----------------------------------------------------------------------------
def send_cancel():
    """
        This will cancel a shipment that has been sent

        @ToDo: Rewrite as Method
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
                                                  stable.site_id,
                                                  limitby = (0, 1),
                                                  ).first()

    inv_ship_status = s3db.inv_ship_status
    if send_record.status != inv_ship_status["SENT"]:
        session.error = T("This shipment has not been sent - it has NOT been canceled because it can still be edited.")

    if session.error:
        redirect(URL(c="inv", f="send",
                     args = [send_id],
                     ))

    rtable = s3db.inv_recv
    tracktable = s3db.inv_track_item

    # Okay no error so far, let's delete that baby
    # Change the send and recv status to cancelled
    #ADMIN = auth.get_system_roles().ADMIN
    db(stable.id == send_id).update(status = inv_ship_status["CANCEL"],
                                    #owned_by_user = None,
                                    #owned_by_group = ADMIN,
                                    )
    recv_row = db(tracktable.send_id == send_id).select(tracktable.recv_id,
                                                        limitby = (0, 1),
                                                        ).first()
    if recv_row:
        recv_id = recv_row.recv_id
        db(rtable.id == recv_id).update(date = request.utcnow,
                                        status = inv_ship_status["CANCEL"],
                                        #owned_by_user = None,
                                        #owned_by_group = ADMIN,
                                        )

    # Change the track items status to canceled and then delete them
    # If they are linked to a request then the in transit total will also be reduced
    # Records can only be deleted if the status is In Process (or preparing)
    # so change the status before we delete
    tracking_status = s3db.inv_tracking_status
    db(tracktable.send_id == send_id).update(status = tracking_status["IN_PROCESS"])
    track_rows = db(tracktable.send_id == send_id).select(tracktable.id)
    from s3db.inv import inv_track_item_deleting
    for track_item in track_rows:
        inv_track_item_deleting(track_item.id)
    # Now change the status to (cancelled)
    db(tracktable.send_id == send_id).update(status = tracking_status["CANCEL"])

    if settings.get_inv_warehouse_free_capacity_calculated():
        # Update the Warehouse Free capacity
        from s3db.inv import inv_warehouse_free_capacity
        inv_warehouse_free_capacity(send_record.site_id)

    session.confirmation = T("Sent Shipment canceled and items returned to Warehouse")

    redirect(URL(f = "send",
                 args = [send_id],
                 ))

# -----------------------------------------------------------------------------
def recv_cancel():
    """
        Cancel a Received Shipment

        @ToDo: Rewrite as Method
        @todo what to do if the quantity cancelled doesn't exist?
    """

    try:
        recv_id = request.args[0]
    except:
        redirect(URL(f="recv"))

    rtable = s3db.inv_recv
    if not auth.s3_has_permission("delete", rtable, record_id=recv_id):
        session.error = T("You do not have permission to cancel this received shipment.")
        redirect(URL(c="inv", f="recv",
                     args = [recv_id],
                     ))

    recv_record = db(rtable.id == recv_id).select(rtable.status,
                                                  rtable.site_id,
                                                  limitby = (0, 1),
                                                  ).first()

    from s3db.inv import inv_ship_status
    if recv_record.status != inv_ship_status["RECEIVED"]:
        session.error = T("This shipment has not been received - it has NOT been canceled because it can still be edited.")
        redirect(URL(c="inv", f="recv", args=[recv_id]))

    stable = s3db.inv_send
    tracktable = s3db.inv_track_item
    inv_item_table = s3db.inv_inv_item
    ritable = s3db.inv_req_item
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
    from s3db.inv import inv_req_update_status
    for track_item in track_rows:
        # If this is linked to a request
        # then remove these items from the quantity in fulfil
        if track_item.req_item_id:
            req_id = track_item.req_item_id
            req_item = db(ritable.id == req_id).select(ritable.quantity_fulfil,
                                                       ritable.item_pack_id,
                                                       limitby = (0, 1),
                                                       ).first()
            req_quantity = req_item.quantity_fulfil
            # @ToDo: Optimise by reading these 2 in a single DB query
            req_pack_quantity = db(siptable.id == req_item.item_pack_id).select(siptable.quantity,
                                                                                limitby = (0, 1),
                                                                                ).first().quantity
            track_pack_quantity = db(siptable.id == track_item.item_pack_id).select(siptable.quantity,
                                                                                    limitby = (0, 1),
                                                                                    ).first().quantity
            quantity_fulfil = s3db.supply_item_add(req_quantity,
                                                   req_pack_quantity,
                                                   - track_item.recv_quantity,
                                                   track_pack_quantity
                                                   )
            db(ritable.id == req_id).update(quantity_fulfil = quantity_fulfil)
            inv_req_update_status(req_id)

    # Now set the recv record to cancelled and the send record to sent
    #ADMIN = auth.get_system_roles().ADMIN
    db(rtable.id == recv_id).update(date = request.utcnow,
                                    status = inv_ship_status["CANCEL"],
                                    #owned_by_user = None,
                                    #owned_by_group = ADMIN
                                    )
    if send_id != None:
        # The sent record is now set back to SENT so the source warehouse can
        # now cancel this record to get the stock back into their warehouse.
        # IMPORTANT reports need to locate this record otherwise it can be
        # a mechanism to circumvent the auditing of stock
        db(stable.id == send_id).update(status = inv_ship_status["SENT"],
                                        #owned_by_user = None,
                                        #owned_by_group = ADMIN
                                        )

    if settings.get_inv_warehouse_free_capacity_calculated():
        # Update the Warehouse Free capacity
        from s3db.inv import inv_warehouse_free_capacity
        inv_warehouse_free_capacity(recv_record.site_id)

    redirect(URL(c="inv", f="recv",
                 args = [recv_id]
                 ))

# -----------------------------------------------------------------------------
def incoming():
    """
        Incoming Shipments for Sites

        Used from Requests rheader when looking at Transport Status
    """

    # @ToDo: Create this function!
    from s3db.inv import inv_incoming
    return inv_incoming()

# =============================================================================
def inv_item_packs():
    """
        Called by filterOptionsS3 to provide the pack options for a
            particular Item

        Access via the .json representation to avoid work rendering menus, etc
    """

    try:
        inv_item_id = request.args[0]
    except:
        raise HTTP(400, current.xml.json_message(False, 400, "No value provided!"))

    table = s3db.inv_inv_item
    ptable = db.supply_item_pack
    query = (table.id == inv_item_id) & \
            (table.item_id == ptable.item_id)
    packs = db(query).select(ptable.id,
                             ptable.name,
                             ptable.quantity,
                             )

    SEPARATORS = (",", ":")
    output = json.dumps(packs.as_list(), separators=SEPARATORS)

    response.headers["Content-Type"] = "application/json"
    return output

# -----------------------------------------------------------------------------
def req_item_packs():
    """
        Called by S3OptionsFilter to provide the pack options for a Requisition Item

        Access via the .json representation to avoid work rendering menus, etc
    """

    req_item_id = None
    args = request.args
    if len(args) == 1 and args[0].isdigit():
        req_item_id = args[0]
    else:
        for v in request.vars:
            if "." in v and v.split(".", 1)[1] == "req_item_id":
                req_item_id = request.vars[v]
                break

    table = s3db.supply_item_pack
    ritable = s3db.inv_req_item
    query = (ritable.id == req_item_id) & \
            (ritable.item_id == table.item_id)
    rows = db(query).select(table.id,
                            table.name,
                            table.quantity,
                            )

    SEPARATORS = (",", ":")
    output = json.dumps(rows.as_list(), separators=SEPARATORS)

    response.headers["Content-Type"] = "application/json"
    return output

# -----------------------------------------------------------------------------
def inv_item_quantity():
    """
        Called from s3.inv_send_item.js to
        - provide the pack options for a particular item
        - lookup all Packs & Pack Quantities (to replace the filterOptionsS3 AJAX call to inv_item_packs)

        Access via the .json representation to avoid work rendering menus, etc
    """

    try:
        inv_item_id = request.args[0]
    except:
        raise HTTP(400, current.xml.json_message(False, 400, "No value provided!"))

    table = s3db.inv_inv_item
    ptable = db.supply_item_pack
    inv_query = (table.id == inv_item_id)

    query = inv_query & \
            (table.item_pack_id == ptable.id)
    inv_item = db(query).select(table.quantity,
                                ptable.quantity,
                                limitby = (0, 1),
                                ).first()

    query = inv_query & \
            (table.item_id == ptable.item_id)
    packs = db(query).select(ptable.id,
                             ptable.name,
                             ptable.quantity,
                             )

    data = {"quantity": inv_item["inv_inv_item.quantity"] * inv_item["supply_item_pack.quantity"],
            "packs": packs.as_list(),
            }
    SEPARATORS = (",", ":")
    output = json.dumps(data, separators=SEPARATORS)

    response.headers["Content-Type"] = "application/json"
    return output

# -----------------------------------------------------------------------------
def commit_item_json():
    """
        Used by s3.supply.js for the ajax_more quantity represent of req_items

        Access via the .json representation to avoid work rendering menus, etc
    """

    try:
        req_item_id = request.args[0]
    except:
        raise HTTP(400, current.xml.json_message(False, 400, "No value provided!"))

    stable = s3db.org_site
    ctable = s3db.inv_commit
    itable = s3db.inv_commit_item

    query = (itable.req_item_id == req_item_id) & \
            (ctable.id == itable.commit_id) & \
            (ctable.site_id == stable.id)
    records = db(query).select(ctable.id,
                               ctable.date,
                               stable.name,
                               itable.quantity,
                               orderby = db.inv_commit.date,
                               )

    output = [{"id": s3_str(T("Committed")),
               "quantity": "#",
               }]
    for row in records:
        quantity = row["inv_commit_item.quantity"]
        name = row["org_site.name"]
        row = row["inv_commit"]
        output.append({"id": row.id,
                       "date": row.date.date().isoformat(),
                       "quantity": quantity,
                       "name": name,
                       })

    SEPARATORS = (",", ":")
    output = json.dumps(output, separators=SEPARATORS)

    response.headers["Content-Type"] = "application/json"
    return output

# -----------------------------------------------------------------------------
def recv_item_json():
    """
       Used by s3.supply.js for the ajax_more quantity represent of req_items

       Access via the .json representation to avoid work rendering menus, etc
    """

    try:
        req_item_id = request.args[0]
    except:
        raise HTTP(400, current.xml.json_message(False, 400, "No value provided!"))

    from s3db.inv import inv_ship_status

    rtable = s3db.inv_recv
    ittable = s3db.inv_track_item

    query = (ittable.req_item_id == req_item_id) & \
            (rtable.id == ittable.recv_id) & \
            (rtable.status == inv_ship_status["RECEIVED"])
    rows = db(query).select(rtable.id,
                            rtable.date,
                            rtable.recv_ref,
                            ittable.quantity,
                            )

    output = [{"id": s3_str(T("Received")),
               "quantity": "#",
               }]
    for row in rows:
        quantity = row["inv_track_item.quantity"]
        row = row["inv_recv"]
        output.append({"id": row.id,
                       "date": row.date.date().isoformat(),
                       "quantity": quantity,
                       "name": row.recv_ref,
                       })

    SEPARATORS = (",", ":")
    output = json.dumps(output, separators=SEPARATORS)

    response.headers["Content-Type"] = "application/json"
    return output

# -----------------------------------------------------------------------------
def send_item_json():
    """
       Used by s3.supply.js for the ajax_more quantity represent of req_items

       Access via the .json representation to avoid work rendering menus, etc
    """

    try:
        req_item_id = request.args[0]
    except:
        raise HTTP(400, current.xml.json_message(False, 400, "No value provided!"))

    from s3db.inv import inv_ship_status

    istable = s3db.inv_send
    ittable = s3db.inv_track_item

    query = (ittable.req_item_id == req_item_id) & \
            (istable.id == ittable.send_id) & \
            ((istable.status == inv_ship_status["SENT"]) | \
             (istable.status == inv_ship_status["RECEIVED"]))
    rows = db(query).select(istable.id,
                            istable.send_ref,
                            istable.date,
                            ittable.quantity,
                            )

    output = [{"id": s3_str(T("Sent")),
               "quantity": "#",
               }]
    for row in rows:
        quantity = row["inv_track_item.quantity"]
        row = row["inv_send"]
        output.append({"id": row.id,
                       "date": row.date.date().isoformat(),
                       "quantity": quantity,
                       "name": row.send_ref,
                       })

    SEPARATORS = (",", ":")
    output = json.dumps(output, separators=SEPARATORS)

    response.headers["Content-Type"] = "application/json"
    return output

# END =========================================================================
