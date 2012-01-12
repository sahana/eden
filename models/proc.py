# -*- coding: utf-8 -*-
"""
    Procurement

    A module to handle Procurement

    Currently handles
        Suppliers
        Planned Procurements

    @ToDo: Extend to
        Purchase Requests (PRs)
        Purchase Orders (POs)
"""

if deployment_settings.has_module("proc"):

    # Component definitions should be outside conditional model loads
    s3mgr.model.add_component("proc_plan",
                              proc_supplier="supplier_id")

    s3mgr.model.add_component("proc_plan_item",
                              proc_plan="plan_id")

    # ---------------------------------------------------------------------
    def proc_tables():
        """ Load the Procurement Tables when needed """

        module = "proc"

        location_id = s3db.gis_location_id

        # Procurement depends on Supply Items/Packs
        s3mgr.load("supply_item")
        item_id = response.s3.item_id
        supply_item_id = response.s3.supply_item_id
        item_pack_id = response.s3.item_pack_id
        item_pack_virtualfields = response.s3.item_pack_virtualfields

        # =====================================================================
        # Suppliers
        #
        tablename = "proc_supplier"
        table = db.define_table(tablename,
                                Field("name", notnull=True, unique=True,
                                      length=128,
                                      label = T("Name")),
                                location_id(),
                                Field("phone", label = T("Phone"),
                                      requires = IS_NULL_OR(s3_phone_requires)),
                                # @ToDo: Make this a component?
                                Field("contact", label = T("Contact")),
                                Field("website", label = T("Website"),
                                      requires = IS_NULL_OR(IS_URL()),
                                      represent = s3_url_represent),
                                s3_comments(),
                                *(address_fields() + s3_meta_fields()))

        # CRUD strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Supplier"),
            title_display = T("Supplier Details"),
            title_list = T("List Suppliers"),
            title_update = T("Edit Supplier"),
            title_search = T("Search Suppliers"),
            subtitle_create = T("Add Supplier"),
            subtitle_list = T("Suppliers"),
            label_list_button = T("List Suppliers"),
            label_create_button = T("Add Supplier"),
            label_delete_button = T("Delete Supplier"),
            msg_record_created = T("Supplier added"),
            msg_record_modified = T("Supplier updated"),
            msg_record_deleted = T("Supplier deleted"),
            msg_list_empty = T("No Suppliers currently registered"))

        def proc_supplier_represent(id):
            if not id:
                return NONE
            table = db.proc_supplier
            query = (table.id == id)
            record = db(query).select(table.name,
                                      limitby=(0, 1)).first()
            if record:
                return record.name
            else:
                return UNKNOWN

        # Reusable Field
        supplier_id = S3ReusableField("supplier_id", db.proc_supplier, sortby="name",
                    requires = IS_NULL_OR(IS_ONE_OF(db, "proc_supplier.id",
                                                    "%(name)s",
                                                    sort=True)),
                    represent = proc_supplier_represent,
                    label = T("Supplier"),
                    comment = DIV(A(T("Add Supplier"),
                                    _class="colorbox",
                                    _href=URL(c="proc", f="supplier",
                                              args="create",
                                              vars=dict(format="popup")),
                                    _target="top",
                                    _title=T("Add Supplier"))
                              ),
                    ondelete = "RESTRICT")

        # =====================================================================
        # Planned Procurements
        #
        proc_shipping_opts = { 0:NONE,
                               1:"Air",
                               2:"Rail",
                               3:"Road",
                               4:"Sea"
                             }

        tablename = "proc_plan"
        table = db.define_table(tablename,
                                super_link("site_id", "org_site",
                                           #label = T("Inventory"),
                                           label = T("Office"),
                                           default = auth.user.site_id if auth.is_logged_in() else None,
                                           readable = True,
                                           writable = True,
                                           empty = False,
                                           # Comment these to use a Dropdown & not an Autocomplete
                                           #widget = S3SiteAutocompleteWidget(),
                                           #comment = DIV(_class="tooltip",
                                           #              _title="%s|%s" % (T("Inventory"),
                                           #                                T("Enter some characters to bring up a list of possible matches"))),
                                           represent=s3db.org_site_represent),
                                # @ToDo: Link the Plan to a Project or Activity (if that module is enabled)
                                #project_id(),
                                Field("order_date",
                                      "date",
                                      label = T("Order Date"),
                                      represent = s3_date_represent),
                                Field("eta",
                                      "date",
                                      label = T("Date Expected"),
                                      represent = s3_date_represent),
                                # @ToDo: Do we want more than 1 supplier per Plan?
                                supplier_id(),
                                Field("shipping",
                                      "integer",
                                      requires = IS_NULL_OR(IS_IN_SET(proc_shipping_opts)),
                                      represent = lambda opt: proc_shipping_opts.get(opt, UNKNOWN_OPT),
                                      label = T("Shipping Method"),
                                      default = 0,
                                      ),
                                # @ToDo: Add estimated shipping costs
                                s3_comments(),
                                *s3_meta_fields())

        # CRUD strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Procurement Plan"),
            title_display = T("Procurement Plan Details"),
            title_list = T("List Procurement Plans"),
            title_update = T("Edit Procurement Plan"),
            title_search = T("Search Procurement Plans"),
            subtitle_create = T("Add Procurement Plan"),
            subtitle_list = T("Procurement Plans"),
            label_list_button = T("List Procurement Plans"),
            label_create_button = T("Add Procurement Plan"),
            label_delete_button = T("Delete Procurement Plan"),
            msg_record_created = T("Procurement Plan added"),
            msg_record_modified = T("Procurement Plan updated"),
            msg_record_deleted = T("Procurement Plan deleted"),
            msg_list_empty = T("No Procurement Plans currently registered"))

        # ---------------------------------------------------------------------
        # Redirect to the Items tabs after creation
        plan_item_url = URL(c="default", f="plan", args=["[id]",
                                                         "plan_item"])
        s3mgr.configure(tablename,
                        # @ToDo: Move these to controller r.interactive?
                        create_next = plan_item_url,
                        update_next = plan_item_url)

        # ---------------------------------------------------------------------
        def plan_rheader(r):
            """ Resource Header for Planned Procurements """

            if r.representation == "html":
                plan = r.record
                if plan:
                    tabs = [
                            (T("Edit Details"), None),
                            (T("Items"), "plan_item"),
                           ]
                    rheader_tabs = s3_rheader_tabs(r, tabs)
                    rheader = DIV(TABLE(TR( TH("%s: " % T("Facility")),
                                            s3db.org_site_represent(plan.site_id),
                                          ),
                                        TR( TH("%s: " % T("Order Date")),
                                            s3_date_represent(plan.order_date),
                                          ),
                                        TR( TH("%s: " % T("Date Expected")),
                                            s3_date_represent(plan.eta),
                                          ),
                                        TR( TH("%s: " % T("Shipping Method")),
                                            proc_shipping_opts.get(plan.eta, NONE),
                                          ),
                                       ),
                                  rheader_tabs
                                 )
                    return rheader
            return None

        # ---------------------------------------------------------------------
        def proc_plan_represent(id):
            if not id:
                return NONE
            table = db.proc_plan
            query = (table.id == id)
            record = db(query).select(table.site_id,
                                      table.order_date,
                                      limitby=(0, 1)).first()
            if record:
                return "%s (%s)" % (s3db.org_site_represent(record.site_id),
                                    record.order_date)
            else:
                return UNKNOWN

        plan_id = S3ReusableField("plan_id", db.proc_plan, sortby="date",
                                  requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                  "proc_plan.id",
                                                                  proc_plan_represent,
                                                                  orderby="proc_plan.date",
                                                                  sort=True)),
                                  represent = proc_plan_represent,
                                  label = T("Procurement Plan"),
                                  ondelete = "CASCADE")

        # =====================================================================
        # Procurement Plan Items
        #
        tablename = "proc_plan_item"
        table = db.define_table(tablename,
                                plan_id(),
                                item_id,
                                supply_item_id(),
                                item_pack_id(),
                                Field("quantity",
                                      "double",
                                      label = T("Quantity"),
                                      notnull = True),
                                Field("pack_value",
                                       "double",
                                       readable=False,
                                       writable=False,
                                       label = T("Value per Pack")),
                                # @ToDo: Move this into a Currency Widget for the pack_value field
                                currency_type("currency",
                                              readable=False,
                                              writable=False),
                                #Field("pack_quantity",
                                #      "double",
                                #      compute = record_pack_quantity), # defined in 06_supply
                                s3_comments(),
                                *s3_meta_fields())

        # CRUD strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Item to Procurement Plan"),
            title_display = T("Procurement Plan Item Details"),
            title_list = T("List Items in Procurement Plan"),
            title_update = T("Edit Procurement Plan Item"),
            title_search = T("Search Procurement Plan Items"),
            subtitle_create = T("Add Item to Procurement Plan"),
            subtitle_list = T("Procurement Plan Items"),
            label_list_button = T("List Items in Procurement Plan"),
            label_create_button = T("Add Item to Procurement Plan"),
            label_delete_button = T("Remove Item from Procurement Plan"),
            msg_record_created = T("Item added to Procurement Plan"),
            msg_record_modified = T("Procurement Plan Item updated"),
            msg_record_deleted = T("Item removed from Procurement Plan"),
            msg_list_empty = T("No Items currently registered in this Procurement Plan"))

        # ---------------------------------------------------------------------
        # Item Search Method
        #
        plan_item_search = s3base.S3Search(
            # Advanced Search only
            advanced=(s3base.S3SearchSimpleWidget(
                        name="proc_plan_item_search_text",
                        label=T("Search"),
                        comment=T("Search for an item by text."),
                        field=[ "item_id$name",
                                #"item_id$category_id$name",
                                # Requires VirtualFields
                                #"site_id$name"
                                ]
                      ),
                      # Requires VirtualFields
                      #s3base.S3SearchOptionsWidget(
                      #  name="proc_plan_search_site",
                      #  label=T("Facility"),
                      #  field=["site_id"],
                      #  represent ="%(name)s",
                      #  comment=T("If none are selected, then all are searched."),
                      #  cols = 2
                      #),
                      #s3base.S3SearchMinMaxWidget(
                      #  name="proc_plan_search_order_date",
                      #  method="range",
                      #  label=T("Order Date"),
                      #  field=["order_date"]
                      #),
                      #s3base.S3SearchMinMaxWidget(
                      #  name="proc_plan_search_eta",
                      #  method="range",
                      #  label=T("Date Expected"),
                      #  field=["eta"]
                      #)
            ))

        # ---------------------------------------------------------------------
        s3mgr.configure(tablename,
                        super_entity = "supply_item_entity",
                        search_method = plan_item_search,
                        #report_groupby = db.proc_plan.site_id,
                        report_hide_comments = True)

        # Pass variables back to global scope (response.s3.*)
        return dict(
                plan_rheader = plan_rheader,
            )

    # Provide a handle to this load function
    s3mgr.loader(proc_tables,
                 "proc_supplier",
                 "proc_plan",
                 "proc_plan_item")

# END =========================================================================

