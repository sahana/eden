# -*- coding: utf-8 -*-

"""
    Inventory Management

    A module to record Inventories of Items at Sites,
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

# =============================================================================
def warehouse():
    """
        RESTful CRUD controller
    """

    # Defined in the model for forwards from org/site controller
    from s3db.inv import inv_warehouse_controller
    return inv_warehouse_controller()

# -----------------------------------------------------------------------------
def warehouse_type():
    """
        RESTful CRUD controller
    """

    return s3_rest_controller()

# =============================================================================
def inv_item():
    """ REST Controller """

    # Import pre-process
    def import_prep(tree):
        """
            Process option to Delete all Stock records of the Organisation/Branch
            before processing a new data import
        """
        if s3.import_replace and tree is not None:
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
                    resource = s3db.resource("inv_inv_item",
                                             filter = query,
                                             )
                    # Use cascade = True so that the deletion gets
                    # rolled back if the import fails:
                    resource.delete(format = "xml",
                                    cascade = True,
                                    )

    s3.import_prep = import_prep

    def prep(r):
        #if r.method != "report":
        #    s3.dataTable_group = 1
        if r.component:
            #component_name = r.component_name
            if r.component_name == "adj_item":
                s3db.configure("inv_adj_item",
                               deletable = False,
                               editable = False,
                               insertable = False,
                               )
            # We can't update this dynamically
            #elif component_name == "bin":
            #    s3db.inv_inv_item_bin.quantity.requires = IS_INT_IN_RANGE(0, r.record.quantity)
        else:
            tablename = "inv_inv_item"
            s3.crud_strings[tablename].msg_list_empty = T("No Stock currently registered")

            if r.method == "report":
                # Quantity 0 can still be used for managing Stock Replenishment
                s3.filter = (r.table.quantity != 0)

            report = get_vars.get("report")
            if report == "mon":
                # Monetization Report
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

            if r.interactive and \
               r.method in (None, "update", "summary") and \
               settings.get_inv_direct_stock_edits():
                # Limit to Bins from this site
                # Validate Bin Quantities
                if s3.debug:
                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_item.js" % r.application)
                else:
                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_item.min.js" % r.application)

                record = r.record
                if record:
                    site_id = record.site_id
                    ibtable = s3db.inv_inv_item_bin
                    # We can't update this dynamically
                    #ibtable.quantity.requires = IS_INT_IN_RANGE(0, r.record.quantity)
                    sum_field = ibtable.quantity.sum()
                    binned = db(ibtable.inv_item_id == r.id).select(sum_field,
                                                                    limitby = (0, 1),
                                                                    orderby = sum_field,
                                                                    ).first()[sum_field]
                    if binned:
                        # This is in the current Pack units
                        binned = '''
S3.supply.binnedQuantity=%s''' % binned
                    else:
                        binned = ""
                    # Need to transmit the current item_pack_id as not included in the IS_ONE_OF_EMPTY_SELECT widget
                    # Also send the current pack details to avoid an AJAX call
                    item_id = record.item_id
                    ptable = s3db.supply_item_pack
                    rows = db(ptable.item_id == item_id).select(ptable.id,
                                                                ptable.name,
                                                                ptable.quantity,
                                                                )

                    # Simplify format
                    packs = {item_id: [{"i": row.id,
                                        "n": row.name,
                                        "q": row.quantity,
                                        } for row in rows],
                             }

                    SEPARATORS = (",", ":")
                    packs = json.dumps(packs, separators=SEPARATORS)
                    s3.js_global.append('''S3.supply.packs=%s
S3.supply.itemPackID=%s%s''' % (packs,
                                record.item_pack_id,
                                binned,
                                ))
                    f = ibtable.layout_id
                    f.widget.filter = (s3db.org_site_layout.site_id == site_id)
                    f.comment.args = [site_id, "layout", "create"]
                    # We can't update this dynamically
                    #f.requires.other.set_filter(filterby = "site_id",
                    #                            filter_opts = [site_id],
                    #                            )

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and \
           r.component_name == "adj_item":
            # Add Button for New Adjustment
            _href = URL(c="inv", f="adj",
                        vars = {"item": r.id,
                                "site": r.record.site_id,
                                },
                        )
            from s3 import crud_button
            add_btn = crud_button(label = T("New Adjustment"),
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
                              # Not actioned:
                              #pdf_orderby = "expiry_date, supply_org_id",
                              replace_option = T("Remove existing data before import"),
                              rheader = inv_rheader,
                              )

# -----------------------------------------------------------------------------
def inv_item_bin():
    """
        RESTful CRUD controller
        - just used for options.s3json lookups
    """

    s3.prep = lambda r: \
        r.representation == "s3json" and r.method == "options"

    return s3_rest_controller()

# =============================================================================
def adj():
    """
        RESTful CRUD controller for Stock Adjustments
    """

    from s3db.inv import inv_adj_close
    s3db.set_method("inv", "adj",
                    method = "close",
                    action = inv_adj_close,
                    )

    def prep(r):
        if r.interactive:
            if r.component:
                if r.component_name == "adj_item":
                    adj_status = r.record.status
                    if adj_status:
                        s3db.configure("inv_adj_item",
                                       editable = False,
                                       insertable = False,
                                       )
                    else:
                        # Limit to Bins from this site
                        from s3db.org import org_site_layout_config
                        org_site_layout_config(r.record.site_id, s3db.inv_adj_item_bin.layout_id)

                        # Validate Bin Quantities
                        if s3.debug:
                            s3.scripts.append("/%s/static/scripts/S3/s3.inv_adj_item.js" % r.application)
                        else:
                            s3.scripts.append("/%s/static/scripts/S3/s3.inv_adj_item.min.js" % r.application)

                        if r.component_id:
                            aitable = s3db.inv_adj_item
                            if adj_status == 0:
                                aitable.reason.writable = True
                            record = db(aitable.id == r.component_id).select(aitable.inv_item_id,
                                                                             aitable.old_quantity,
                                                                             limitby = (0, 1),
                                                                             ).first()
                            if record.inv_item_id:
                                aitable.item_id.writable = False
                                aitable.item_id.comment = None
                                aitable.item_pack_id.writable = False

                            abtable = s3db.inv_adj_item_bin
                            sum_field = abtable.quantity.sum()
                            binned = db(abtable.adj_item_id == r.component_id).select(sum_field,
                                                                                      limitby = (0, 1),
                                                                                      orderby = sum_field,
                                                                                      ).first()[sum_field]
                            if binned:
                                s3.js_global.append('''S3.supply.binnedQuantity=%s
S3.supply.oldQuantity=%s''' % (binned, record.old_quantity))

                elif r.component_name == "image":
                    doc_table = s3db.doc_image
                    doc_table.organisation_id.readable = doc_table.organisation_id.writable = False
                    doc_table.person_id.readable = doc_table.person_id.writable = False
                    doc_table.location_id.readable = doc_table.location_id.writable = False
            else:
                #No Component
                table = s3db.inv_adj
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
                        inv_item_id = get_vars.item
                        inv_item_table = s3db.inv_inv_item
                        inv_item = db(inv_item_table.id == inv_item_id).select(inv_item_table.id,
                                                                               inv_item_table.item_id,
                                                                               inv_item_table.item_pack_id,
                                                                               inv_item_table.quantity,
                                                                               inv_item_table.currency,
                                                                               inv_item_table.status,
                                                                               inv_item_table.pack_value,
                                                                               inv_item_table.expiry_date,
                                                                               inv_item_table.owner_org_id,
                                                                               limitby = (0, 1),
                                                                               ).first()
                        inv_bin_table = s3db.inv_inv_item_bin
                        bins = db(inv_bin_table.inv_item_id == inv_item_id).select(inv_bin_table.layout_id,
                                                                                   inv_bin_table.quantity,
                                                                                   )
                        item_id = inv_item.item_id
                        adj_id = table.insert(adjuster_id = auth.s3_logged_in_person(),
                                              site_id = get_vars.site,
                                              adjustment_date = request.utcnow,
                                              status = 0,
                                              category = 1,
                                              comments = "Adjust %s" % inv_item_table.item_id.represent(item_id, show_link=False),
                                              )
                        adj_bin_table = s3db.inv_adj_item_bin
                        adj_item_table = s3db.inv_adj_item
                        adj_item_id = adj_item_table.insert(reason = 0, # Unknown
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
                                                            old_owner_org_id = inv_item.owner_org_id,
                                                            new_owner_org_id = inv_item.owner_org_id,
                                                            )
                        for row in bins:
                            adj_bin_table.insert(adj_item_id = adj_item_id,
                                                 layout_id = row.layout_id,
                                                 quantity = row.quantity,
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
def adj_item_bin():
    """
        RESTful CRUD controller for Adjustment Item Bins
        - just used for options.s3json lookups
    """

    s3.prep = lambda r: \
        r.representation == "s3json" and r.method == "options"

    return s3_rest_controller()

# =============================================================================
def kitting():
    """
        RESTful CRUD controller for Kitting
    """

    from s3db.inv import inv_rheader
    return s3_rest_controller(rheader = inv_rheader)

# =============================================================================
def recv():
    """ RESTful CRUD controller """

    from s3db.inv import inv_recv_controller
    return inv_recv_controller()

# -----------------------------------------------------------------------------
def recv_item_bin():
    """
        RESTful CRUD controller
        - just used for options.s3json lookups
    """

    s3.prep = lambda r: \
        r.representation == "s3json" and r.method == "options"

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def send():
    """ RESTful CRUD controller """

    from s3db.inv import inv_send_controller
    return inv_send_controller()

# -----------------------------------------------------------------------------
def send_item_bin():
    """
        RESTful CRUD controller
        - just used for options.s3json lookups
    """

    s3.prep = lambda r: \
        r.representation == "s3json" and r.method == "options"

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def track_item():
    """ RESTful CRUD controller """

    table = s3db.inv_track_item

    # Only used for Read-only Reports
    s3db.configure("inv_track_item",
                   deletable = False,
                   editable = False,
                   insertable = False,
                   )

    viewing = get_vars.get("viewing")
    if viewing:
        # Track Shipment
        dummy, item_id = viewing.split(".")
        if item_id != "None":
            s3.filter = (table.send_inv_item_id == item_id ) | \
                        (table.recv_inv_item_id == item_id)

        list_fields = None # Configure later (DRY)

    else:
        report = get_vars.get("report")
        if report == "rel":
            # Summary of Releases
            s3.crud_strings["inv_track_item"] = Storage(title_list = T("Summary of Releases"),
                                                        subtitle_list = T("Summary Details"),
                                                        )

            s3.filter = (FS("send_id") != None)

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
                           orderby = "inv_send.site_id",
                           sort = True
                           )

        elif report == "inc":
            # Summary of Incoming Supplies
            s3.crud_strings["inv_track_item"] = Storage(title_list = T("Summary of Incoming Supplies"),
                                                        subtitle_list = T("Summary Details"),
                                                        )

            s3.filter = (FS("recv_id") != None)

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
                           ]

            s3db.configure("inv_track_item",
                           orderby = "inv_recv.recipient_id",
                           )

        elif report == "util":
            # Utilization Report
            s3.crud_strings["inv_track_item"] = Storage(title_list = T("Utilization Report"),
                                                        subtitle_list = T("Utilization Details"),
                                                        )

            s3.filter = (FS("item_id") != None)

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

        elif report == "exp":
            # Expiration Report
            s3.crud_strings["inv_track_item"] = Storage(title_list = T("Expiration Report"),
                                                        subtitle_list = T("Expiration Details"),
                                                        )

            s3.filter = (FS("expiry_date") != None)

            list_fields = ["recv_inv_item_id$site_id",
                          (T("Item/Description"), "item_id"),
                          (T("Expiration Date"), "expiry_date"),
                          (T("Source"), "supply_org_id"),
                          (T("Unit"), "item_pack_id"),
                          (T("Quantity"), "quantity"),
                          (T("Unit Cost"), "pack_value"),
                          (T("Total Cost"), "total_value"),
                          ]
        else:
            list_fields = None # Configure later (DRY)

    if not list_fields:
        list_fields = ["status",
                       "item_source_no",
                       "item_id",
                       "item_pack_id",
                       "send_id",
                       "recv_id",
                       "quantity",
                       (T("Total Weight (kg)"), "total_weight"),
                       (T("Total Volume (m3)"), "total_volume"),
                       "bin.layout_id",
                       "return_quantity",
                       "recv_quantity",
                       "recv_bin.layout_id",
                       "owner_org_id",
                       "supply_org_id",
                       ]

        if settings.get_inv_track_pack_values():
            list_fields.insert(10, "pack_value")
            list_fields.insert(10, "currency")

    s3db.configure("inv_track_item",
                   list_fields = list_fields,
                   )

    from s3db.inv import inv_rheader
    return s3_rest_controller(rheader = inv_rheader)

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

    from s3db.inv import inv_req_controller
    return inv_req_controller()

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
            msg_list_empty = T("No Request Templates"),
            )

    from s3db.inv import inv_req_controller
    return inv_req_controller(template = True)

# =============================================================================
def req_item():
    """
        RESTful CRUD controller for Request Items

        TODO:
            Filter out fulfilled Items?
    """

    # Filter out Template Items
    #if request.function != "fema":
    s3.filter = (FS("req_id$is_template") == False)

    # Custom Methods
    from s3db.inv import inv_req_item_inv_item, inv_req_item_order

    set_method = s3db.set_method

    set_method("inv", "req_item",
               method = "inv_item",
               action = inv_req_item_inv_item
               )

    set_method("inv", "req_item",
               method = "order",
               action = inv_req_item_order
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

    def postp(r, output):
        if r.interactive and \
           not r.component and \
           r.method != "import":
         if settings.get_inv_req_prompt_match():
            s3_action_buttons(r, deletable=False)
            req_item_inv_item_btn = {"label": s3_str(T("Request from Facility")),
                                     "url": URL(c = "inv",
                                                f = "req_item",
                                                args = ["[id]", "inv_item"],
                                                ),
                                     "_class": "action-btn",
                                     }
            s3.actions.append(req_item_inv_item_btn)

        return output
    s3.postp = postp

    return s3_rest_controller("inv", "req_item")

# =============================================================================
def commit():
    """
        RESTful CRUD controller for Commits
    """

    from s3db.inv import inv_commit_send
    s3db.set_method("inv", "commit",
                    method = "send",
                    action = inv_commit_send,
                    )

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
                table.site_id.comment = A(T("Set as default Site"),
                                          _id = "inv_commit_site_id_link",
                                          _target = "_blank",
                                          _href = URL(c = "default",
                                                      f = "user",
                                                      args = ["profile"],
                                                      ),
                                          )

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
                                                          "comments",
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
                                   "url": URL(f = "commit",
                                              args = ["[id]", "send"],
                                              ),
                                   "_class": "action-btn send-btn dispatch",
                                   })
                # Convert to POST
                if s3.debug:
                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_commit.js" % appname)
                else:
                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_commit.min.js" % appname)

        return output
    s3.postp = postp

    return s3_rest_controller(rheader = commit_rheader)

# -----------------------------------------------------------------------------
def commit_rheader(r):
    """ Resource Header for Commitments """

    if r.representation == "html":
        record = r.record
        if record and r.name == "commit":

            from s3 import S3DateTime
            s3_date_represent = S3DateTime.date_represent

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
                            _href = URL(f = "commit",
                                        args = [record.id,
                                                "send",
                                                ],
                                        ),
                            _id = "commit-send",
                            _class = "action-btn"
                            )
            # Convert to POST
            if s3.debug:
                s3.scripts.append("/%s/static/scripts/S3/s3.inv_req_rheader.js" % appname)
            else:
                s3.scripts.append("/%s/static/scripts/S3/s3.inv_req_rheader.min.js" % appname)
            s3.rfooter = TAG[""](prepare_btn)

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
                request.args = [str(exists.id), "log"]

    def postp(r, output):
        if r.id:
            # Don't render any Action Buttons
            s3.actions = []
        else:
            url = URL(args = ["[id]", "log"])
            s3_action_buttons(r,
                              deletable = False,
                              read_url = url,
                              update_url = url,
                              )
        return output
    s3.postp = postp

    from s3db.inv import inv_rheader
    return s3_rest_controller(rheader = inv_rheader)

# =============================================================================
def minimum():
    """
        RESTful CRUD Controller for Stock Minimums
    """

    return s3_rest_controller()

# =============================================================================
def order_item():
    """
        RESTful CRUD Controller for Order Items
    """

    return s3_rest_controller()

# =============================================================================
def package():
    """
        RESTful CRUD Controller for Packages (Boxes & Pallets)
    """

    if s3.debug:
        s3.scripts.append("/%s/static/scripts/S3/s3.inv_package.js" % appname)
    else:
        s3.scripts.append("/%s/static/scripts/S3/s3.inv_package.min.js" % appname)

    return s3_rest_controller()

# =============================================================================
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
                                     args = ["[id]", "read"],
                                     ),
                   )

    from s3db.org import org_facility_controller
    return org_facility_controller()

# -----------------------------------------------------------------------------
def facility_type():
    return s3_rest_controller("org")

# =============================================================================
def project():
    """
        Simpler version of Projects for use within Inventory module
    """

    # Load default Model
    s3db.project_project

    from s3 import S3SQLCustomForm
    crud_form = S3SQLCustomForm("organisation_id",
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
                                     args = ["[id]", "read"],
                                     ),
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
                                     args = ["[id]", "read"],
                                     ),
                   )

    # NB Type gets defaulted in the Custom CRUD form
    # - user needs create permissions for org_organisation_organisation_type
    from s3db.org import org_organisation_controller
    return org_organisation_controller()

# -----------------------------------------------------------------------------
def req_match():
    """ 
        Match Requests
        - a Tab for Sites to show what Requests they could potentially match
    """

    from s3db.inv import inv_req_match
    return inv_req_match()

# -----------------------------------------------------------------------------
def incoming():
    """
        Incoming Shipments for Sites

        Would be used from inv_req_rheader when looking at Transport Status
    """

    # NB This function doesn't currently exist!
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

    from s3db.inv import SHIP_STATUS_RECEIVED

    rtable = s3db.inv_recv
    ittable = s3db.inv_track_item

    query = (ittable.req_item_id == req_item_id) & \
            (rtable.id == ittable.recv_id) & \
            (rtable.status == SHIP_STATUS_RECEIVED)
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

    from s3db.inv import SHIP_STATUS_SENT, SHIP_STATUS_RECEIVED

    istable = s3db.inv_send
    ittable = s3db.inv_track_item

    query = (ittable.req_item_id == req_item_id) & \
            (istable.id == ittable.send_id) & \
            ((istable.status == SHIP_STATUS_SENT) | \
             (istable.status == SHIP_STATUS_RECEIVED))
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
