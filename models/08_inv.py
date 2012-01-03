# -*- coding: utf-8 -*-
"""
    Inventory Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16

    A module to record inventories of items at a location (site)
"""

if deployment_settings.has_module("inv"):

    inv_recv_type = { 0:NONE,
                      1:"Another Inventory",
                      2:"Donation",
                      3:"Supplier" }

    SHIP_STATUS_IN_PROCESS = 0
    SHIP_STATUS_RECEIVED   = 1
    SHIP_STATUS_SENT       = 2
    SHIP_STATUS_CANCEL     = 3

    shipment_status = { SHIP_STATUS_IN_PROCESS: T("In Process"),
                        SHIP_STATUS_RECEIVED:   T("Received"),
                        SHIP_STATUS_SENT:       T("Sent"),
                        SHIP_STATUS_CANCEL:     T("Canceled") }

    SHIP_DOC_PENDING  = 0
    SHIP_DOC_COMPLETE = 1
    ship_doc_status = { SHIP_DOC_PENDING: T("Pending"),
                        SHIP_DOC_COMPLETE: T("Complete") }

    # Component definitions should be outside conditional model loads
    s3mgr.model.add_component("inv_inv_item",
                              org_site=super_key(db.org_site),
                              supply_item="item_id",
                              supply_item_pack="item_pack_id")

    # Recv as a component of Sites
    s3mgr.model.add_component("inv_recv",
                              org_site=super_key(db.org_site))

    s3mgr.model.add_component("inv_recv_item",
                              inv_recv="recv_id",
                              supply_item="item_id")

    # Inv Send added as a component of Facilities
    s3mgr.model.add_component("inv_send",
                              org_site=super_key(db.org_site))

    s3mgr.model.add_component("inv_send_item",
                              inv_send="send_id",
                              inv_inv_item="inv_item_id")

    # ---------------------------------------------------------------------
    def inv_tables():
        """ Load the Inventory Tables when needed """

        module = "inv"

        # Inventory depends on Supply Items/Packs
        s3mgr.load("supply_item")
        item_id = response.s3.item_id
        supply_item_id = response.s3.supply_item_id
        item_pack_id = response.s3.item_pack_id
        item_pack_virtualfields = response.s3.item_pack_virtualfields
        s3mgr.load("req_req_item")
        req_item_id = response.s3.req_item_id

        # =====================================================================
        # Inventory Item
        #
        resourcename = "inv_item"
        tablename = "inv_inv_item"
        table = db.define_table(tablename,
                                super_link("site_id", "org_site",
                                           label = T("Inventory"),
                                           default = auth.user.site_id if auth.is_logged_in() else None,
                                           readable = True,
                                           writable = True,
                                           empty = False,
                                           # Comment these to use a Dropdown & not an Autocomplete
                                           #widget = S3SiteAutocompleteWidget(),
                                           #comment = DIV(_class="tooltip",
                                           #              _title="%s|%s" % (T("Inventory"),
                                           #                                T("Enter some characters to bring up a list of possible matches"))),
                                           represent=org_site_represent),
                                # @ToDo: Allow items to be located to a specific bin within the warehouse
                                #Field("bin"),
                                item_id,
                                supply_item_id(),
                                item_pack_id(),
                                Field("quantity",
                                      "double",
                                      label = T("Quantity"),
                                      notnull = True),
                                Field("pack_value",
                                       "double",
                                       label = T("Value per Pack")),
                                # @ToDo: Move this into a Currency Widget for the pack_value field
                                currency_type("currency"),
                                #Field("pack_quantity",
                                #      "double",
                                #      compute = record_pack_quantity), # defined in 06_supply
                                Field("expiry_date",
                                      "date",
                                      label = T("Expiry Date"),
                                      represent = s3_date_represent),
                                # @ToDo: Allow items to be marked as 'still on the shelf but allocated to an outgoing shipment'
                                #Field("status"),
                                s3_comments(),
                                *s3_meta_fields())

        table.virtualfields.append(item_pack_virtualfields(tablename = "inv_inv_item"))

        # CRUD strings
        INV_ITEM = T("Inventory Item")
        ADD_INV_ITEM = T("Add Item to Inventory")
        LIST_INV_ITEMS = T("List Items in Inventory")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_INV_ITEM,
            title_display = T("Inventory Item Details"),
            title_list = LIST_INV_ITEMS,
            title_update = T("Edit Inventory Item"),
            title_search = T("Search Inventory Items"),
            subtitle_create = ADD_INV_ITEM,
            subtitle_list = T("Inventory Items"),
            label_list_button = LIST_INV_ITEMS,
            label_create_button = ADD_INV_ITEM,
            label_delete_button = T("Remove Item from Inventory"),
            msg_record_created = T("Item added to Inventory"),
            msg_record_modified = T("Inventory Item updated"),
            msg_record_deleted = T("Item removed from Inventory"),
            msg_list_empty = T("No Items currently registered in this Inventory"))

        def inv_item_represent(id):
            itable = db.inv_inv_item
            stable = db.supply_item
            query = (itable.id == id) & \
                    (itable.item_id == stable.id)
            record = db(query).select(stable.name,
                                      limitby = (0, 1)).first()
            if record:
                return record.name
            else:
                return None

        # Reusable Field
        inv_item_id = S3ReusableField("inv_item_id", db.inv_inv_item,
                                      requires = IS_ONE_OF(db,
                                                           "inv_inv_item.id",
                                                           inv_item_represent,
                                                           orderby="inv_inv_item.id",
                                                           sort=True),
                                      represent = inv_item_represent,
                                      label = INV_ITEM,
                                      comment = DIV( _class="tooltip",
                                                     _title="%s|%s" % (INV_ITEM,
                                                                       T("Select Items from this Inventory"))),
                                      ondelete = "CASCADE",
                                      script =
SCRIPT("""
$(document).ready(function() {
    S3FilterFieldChange({
        'FilterField':    'inv_item_id',
        'Field':          'item_pack_id',
        'FieldResource':  'item_pack',
        'FieldPrefix':    'supply',
        'url':             S3.Ap.concat('/inv/inv_item_packs/'),
        'msgNoRecords':    S3.i18n.no_packs,
        'fncPrep':         fncPrepItem,
        'fncRepresent':    fncRepresentItem
    });
});"""),
                                )

        # ---------------------------------------------------------------------
        # Item Search Method
        #
        inv_item_search = s3base.S3Search(
            # Advanced Search only
            advanced=(s3base.S3SearchSimpleWidget(
                        name="inv_item_search_text",
                        label=T("Search"),
                        comment=T("Search for an item by text."),
                        field=[ "item_id$name",
                                #"item_id$category_id$name",
                                #"site_id$name"
                                ]
                      ),
                      s3base.S3SearchOptionsWidget(
                        name="recv_search_site",
                        label=T("Facility"),
                        field=["site_id"],
                        represent ="%(name)s",
                        comment=T("If none are selected, then all are searched."),
                        cols = 2
                      ),
                      s3base.S3SearchMinMaxWidget(
                        name="inv_item_search_expiry_date",
                        method="range",
                        label=T("Expiry Date"),
                        field=["expiry_date"]
                      )
            ))

        # ---------------------------------------------------------------------
        s3mgr.configure(tablename,
                        super_entity = "supply_item_entity",
                        search_method = inv_item_search,
                        report_groupby = db.inv_inv_item.site_id,
                        report_hide_comments = True)

        # ---------------------------------------------------------------------
        def inv_item_controller():

            """ RESTful CRUD controller """

            table = db.inv_inv_item

            # Limit site_id to sites the user has permissions for
            auth.permission.permitted_facilities(table=table,
                                                 error_msg=T("You do not have permission for any site to add an inventory item."))

            return s3_rest_controller("inv", "inv_item")

        # =====================================================================
        # Received (In/Receive / Donation / etc)
        #
        """
        inv_recv_type = { 0:NONE,
                          1:"Another Inventory",
                          2:"Donation",
                          3:"Supplier" }

        SHIP_STATUS_IN_PROCESS = 0
        SHIP_STATUS_RECEIVED   = 1
        SHIP_STATUS_SENT       = 2
        SHIP_STATUS_CANCEL     = 3

        shipment_status = { SHIP_STATUS_IN_PROCESS : T("In Process"),
                            SHIP_STATUS_RECEIVED   : T("Received"),
                            SHIP_STATUS_SENT       : T("Sent"),
                            SHIP_STATUS_CANCEL     : T("Canceled") }

        SHIP_DOC_PENDING  = 0
        SHIP_DOC_COMPLETE = 1
        ship_doc_status = { SHIP_DOC_PENDING  : T("Pending"),
                            SHIP_DOC_COMPLETE : T("Complete") }
        """

        radio_widget = lambda field, value: \
                                RadioWidget().widget(field, value, cols = 2)

        resourcename = "recv"
        tablename = "inv_recv"
        table = db.define_table(tablename,
                                Field("eta",
                                      "date",
                                      label = T("Date Expected"),
                                      represent = s3_date_represent
                                      ),
                                Field("date",
                                      "date",
                                      label = T("Date Received"),
                                      writable = False,
                                      represent = s3_date_represent
                                      #readable = False # unless the record is locked
                                      ),
                                Field("type",
                                      "integer",
                                      requires = IS_NULL_OR(IS_IN_SET(inv_recv_type)),
                                      represent = lambda opt: inv_recv_type.get(opt, UNKNOWN_OPT),
                                      label = T("Type"),
                                      default = 0,
                                      ),
                                person_id(name = "recipient_id",
                                          label = T("Received By"),
                                          default = s3_logged_in_person()),
                                super_link("site_id", "org_site",
                                           label=T("By Facility"),
                                           default = auth.user.site_id if auth.is_logged_in() else None,
                                           readable = True,
                                           writable = True,
                                           # Comment these to use a Dropdown & not an Autocomplete
                                           #widget = S3SiteAutocompleteWidget(),
                                           #comment = DIV(_class="tooltip",
                                           #              _title="%s|%s" % (T("By Inventory"),
                                           #                                T("Enter some characters to bring up a list of possible matches"))),
                                           represent=org_site_represent),
                                Field("from_site_id",
                                       db.org_site,
                                       label = T("From Facility"),
                                       requires = IS_ONE_OF(db,
                                                            "org_site.site_id",
                                                             lambda id: org_site_represent(id, link = False),
                                                             sort=True,
                                                            ),
                                       represent =  org_site_represent
                                      ),
                                #location_id("from_location_id",
                                #            label = T("From Location")),
                                #organisation_id(#"from_organisation_id",
                                #                label = T("From Organization"),
                                                #comment = from_organisation_comment
                                #                comment = organisation_comment),
                                #Field("from_person"), # Text field, because lookup to pr_person record is unnecessarily complex workflow
                                person_id(name = "sender_id",
                                          label = T("Sent By Person"),
                                          ),
                                Field("status",
                                      "integer",
                                      requires = IS_NULL_OR(IS_IN_SET(shipment_status)),
                                      represent = lambda opt: shipment_status.get(opt, UNKNOWN_OPT),
                                      default = SHIP_STATUS_IN_PROCESS,
                                      label = T("Status"),
                                      writable = False,
                                      ),
                                Field("grn_status",
                                      "integer",
                                      requires = IS_NULL_OR(IS_IN_SET(ship_doc_status)),
                                      represent = lambda opt: ship_doc_status.get(opt, UNKNOWN_OPT),
                                      default = SHIP_DOC_PENDING,
                                      widget = radio_widget,
                                      label = T("GRN Status"),
                                      comment = DIV( _class="tooltip",
                                                     _title="%s|%s" % (T("GRN Status"),
                                                                       T("Has the GRN (Goods Received Note) been completed?"))),
                                      ),
                                Field("cert_status",
                                      "integer",
                                      requires = IS_NULL_OR(IS_IN_SET(ship_doc_status)),
                                      represent = lambda opt: ship_doc_status.get(opt, UNKNOWN_OPT),
                                      default = SHIP_DOC_PENDING,
                                      widget = radio_widget,
                                      label = T("Certificate Status"),
                                      comment = DIV( _class="tooltip",
                                                     _title="%s|%s" % (T("Certificate Status"),
                                                                       T("Has the Certificate for receipt of the shipment been given to the sender?"))),
                                      ),
                                s3_comments(),
                                *s3_meta_fields())

        # ---------------------------------------------------------------------
        def inv_recv_represent(id):
            # @ToDo: 'From Organisation' is great for Donations
            # (& Procurement if we make Suppliers Organisations), but isn't useful
            # for shipments between facilities within a single Org where
            # 'From Facility' could be more appropriate
            if id:
                table = db.inv_recv
                inv_recv_row = db(table.id == id).select(table.date,
                                                         table.from_site_id,
                                                         #table.organisation_id,
                                                         limitby=(0, 1)).first()
                return SPAN( org_site_represent( inv_recv_row.from_site_id),
                             #"(", organisation_represent( inv_recv_row.organisation_id), ")",
                             " - ",
                             inv_recv_row.date
                            )
            else:
                return NONE

        # ---------------------------------------------------------------------
        # Reusable Field
        if deployment_settings.get_inv_shipment_name() == "order":
            recv_id_label = T("Order")
        else:
            recv_id_label = T("Receive Shipment")
        recv_id = S3ReusableField("recv_id", db.inv_recv, sortby="date",
                                  requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                  "inv_recv.id",
                                                                  inv_recv_represent,
                                                                  orderby="inv_recv.date",
                                                                  sort=True)),
                                  represent = inv_recv_represent,
                                  label = recv_id_label,
                                  #comment = DIV(A(ADD_DISTRIBUTION, _class="colorbox", _href=URL(c="inv", f="distrib", args="create", vars=dict(format="popup")), _target="top", _title=ADD_DISTRIBUTION),
                                  #          DIV( _class="tooltip", _title=T("Distribution") + "|" + T("Add Distribution."))),
                                  ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Recv Search Method
        #
        if deployment_settings.get_inv_shipment_name() == "order":
            recv_search_comment = T("Search for an order by looking for text in any field.")
            recv_search_date_field = "eta"
            recv_search_date_comment = T("Search for an order expected between these dates")
        else:
            recv_search_comment = T("Search for a shipment by looking for text in any field.")
            recv_search_date_field = "date"
            recv_search_date_comment = T("Search for a shipment received between these dates")
        recv_search = s3base.S3Search(
            simple=(s3base.S3SearchSimpleWidget(
                        name="recv_search_text_simple",
                        label=T("Search"),
                        comment=recv_search_comment,
                        field=[ "from_person",
                                "comments",
                                #"organisation_id$name",
                                #"organisation_id$acronym",
                                "from_site_id$name",
                                "recipient_id$first_name",
                                "recipient_id$middle_name",
                                "recipient_id$last_name",
                                "site_id$name"
                                ]
                      )),
            advanced=(s3base.S3SearchSimpleWidget(
                        name="recv_search_text_advanced",
                        label=T("Search"),
                        comment=recv_search_comment,
                        field=[ "from_person",
                                "comments",
                                #"organisation_id$name",
                                #"organisation_id$acronym",
                                "from_site_id$name",
                                "recipient_id$first_name",
                                "recipient_id$middle_name",
                                "recipient_id$last_name",
                                "site_id$name"
                                ]
                      ),
                      s3base.S3SearchMinMaxWidget(
                        name="recv_search_date",
                        method="range",
                        label=table[recv_search_date_field].label,
                        comment=recv_search_date_comment,
                        field=[recv_search_date_field]
                      ),
                      s3base.S3SearchOptionsWidget(
                        name="recv_search_site",
                        label=T("Facility"),
                        field=["site_id"],
                        represent ="%(name)s",
                        cols = 2
                      ),
                      s3base.S3SearchOptionsWidget(
                        name="recv_search_status",
                        label=T("Status"),
                        field=["status"],
                        cols = 2
                      ),
                      s3base.S3SearchOptionsWidget(
                        name="recv_search_grn",
                        label=T("GRN Status"),
                        field=["grn_status"],
                        cols = 2
                      ),
                      s3base.S3SearchOptionsWidget(
                        name="recv_search_cert",
                        label=T("Certificate Status"),
                        field=["grn_status"],
                        cols = 2
                      ),
            ))

        # ---------------------------------------------------------------------
        # Redirect to the Items tabs after creation
        recv_item_url = URL(c="inv", f="recv", args=["[id]",
                                                     "recv_item"])
        # ---------------------------------------------------------------------
        s3mgr.configure(tablename,
                        # @ToDo: Move these to controller r.interactive?
                        create_next = recv_item_url,
                        update_next = recv_item_url,
                        search_method = recv_search)

        # ---------------------------------------------------------------------
        def inv_recv_rheader(r):
            """ Resource Header for Receiving """

            if r.representation == "html" and r.name == "recv":
                recv_record = r.record
                if recv_record:
                    rheader = DIV( TABLE(
                                       TR( TH( "%s: " % T("Date Expected")),
                                           recv_record.eta or NONE,
                                           TH("%s: " % T("Status")),
                                           shipment_status.get(recv_record.status, UNKNOWN_OPT),
                                          ),
                                       TR( TH( "%s: " % T("Date Received")),
                                           recv_record.date or NONE,
                                          ),
                                       TR( TH( "%s: " % T("By Facility")),
                                           org_site_represent(recv_record.site_id),
                                          ),
                                       TR( TH( "%s: " % T("From Location")),
                                           org_site_represent(recv_record.from_site_id),
                                           #TH( "%s: " % T("From Organization")),
                                           #organisation_represent(recv_record.organisation_id),
                                          ),
                                       TR( TH( "%s: " % T("Sent By Person")),
                                           s3_fullname(recv_record.sender_id),
                                           TH( "%s: " % T("Received By Person")),
                                           s3_fullname(recv_record.recipient_id),
                                          ),
                                       TR( TH( "%s: " % T("Comments")),
                                           TD(recv_record.comments, _colspan=2),
                                          ),
                                         )
                                    )
                    response.s3.rfooter = TAG[""]()

                    if recv_record.status == SHIP_STATUS_IN_PROCESS:
                        if auth.s3_has_permission("update",
                                                  db.inv_recv,
                                                  record_id=recv_record.id):
                            recv_btn = A( T("Receive Shipment"),
                                          _href = URL(c = "inv",
                                                      f = "recv_process",
                                                      args = [recv_record.id]
                                                      ),
                                          _id = "recv_process",
                                          _class = "action-btn"
                                          )

                            recv_btn_confirm = SCRIPT("S3ConfirmClick('#recv_process', '%s')"
                                                      % T("Do you want to receive this shipment?") )
                            response.s3.rfooter.append(recv_btn)
                            response.s3.rfooter.append(recv_btn_confirm)
                    else:
                        grn_btn = A( T("Goods Received Note"),
                                      _href = URL(#c = "inv",
                                                  f = "recv",
                                                  args = [recv_record.id, "form.pdf"]
                                                  ),
                                      _class = "action-btn"
                                      )
                        response.s3.rfooter.append(grn_btn)
                        dc_btn = A( T("Donation Certificate"),
                                      _href = URL(#c = "inv",
                                                  f = "recv",
                                                  args = [recv_record.id, "cert.pdf"]
                                                  ),
                                      _class = "action-btn"
                                      )
                        response.s3.rfooter.append(dc_btn)

                        if recv_record.status != SHIP_STATUS_CANCEL:
                            if auth.s3_has_permission("delete",
                                                      db.inv_recv,
                                                      record_id=recv_record.id):
                                cancel_btn = A( T("Cancel Shipment"),
                                                _href = URL(c = "inv",
                                                            f = "recv_cancel",
                                                            args = [recv_record.id]
                                                            ),
                                                _id = "recv_cancel",
                                                _class = "action-btn"
                                                )

                                cancel_btn_confirm = SCRIPT("S3ConfirmClick('#recv_cancel', '%s')"
                                                             % T("Do you want to cancel this received shipment? The items will be removed from the Inventory. This action CANNOT be undone!") )
                                response.s3.rfooter.append(cancel_btn)
                                response.s3.rfooter.append(cancel_btn_confirm)

                    rheader_tabs = s3_rheader_tabs( r,
                                                     [(T("Edit Details"), None),
                                                      (T("Items"), "recv_item"),
                                                      ]
                                                     )
                    rheader.append(rheader_tabs)

                    return rheader
            return None

        # ---------------------------------------------------------------------
        def inv_recv_controller():
            """ RESTful CRUD controller """

            table = db.inv_recv

            # Limit site_id to sites the user has permissions for
            if deployment_settings.get_inv_shipment_name() == "order":
                error_msg = T("You do not have permission for any facility to add an order.")
            else:
                error_msg = T("You do not have permission for any facility to receive a shipment.")
            auth.permission.permitted_facilities(table=table,
                                                 error_msg=error_msg)

            def prep(r):
                # If component view
                if r.record:
                    if r.record.status == SHIP_STATUS_IN_PROCESS:
                        s3.crud_strings.inv_recv.title_update = \
                        s3.crud_strings.inv_recv.title_display = T("Process Received Shipment")
                return True

            response.s3.prep = prep

            output = s3_rest_controller("inv", "recv",
                                        rheader=inv_recv_rheader)
            return output
        # ---------------------------------------------------------------------
        def inv_recv_form (r, **attr):
            """ Generate a PDF of a GRN (Goods Received Note) """
            table = db.inv_recv
            table.date.readable = True
            table.site_id.readable = True
            table.site_id.label = T("By Inventory")
            table.site_id.represent = org_site_represent
            return s3_component_form(r,
                                     componentname = "recv_item",
                                     formname = T("Goods Received Note"),
                                     filename = T("GRN"),
                                     **attr)

        s3mgr.model.set_method(module, resourcename,
                               method="form", action=inv_recv_form)

        # ---------------------------------------------------------------------
        def inv_recv_donation_cert (r, **attr):
            """ Generate a PDF of a Donation certificate """
            table = db.inv_recv
            table.date.readable = True
            table.type.readable = False
            table.site_id.readable = True
            table.site_id.label = T("By Inventory")
            table.site_id.represent = org_site_represent
            return s3_component_form(r,
                                     componentname = "recv_item",
                                     formname = T("Donation Certificate"),
                                     filename = T("DC"),
                                     **attr)

        s3mgr.model.set_method(module, resourcename,
                               method="cert", action=inv_recv_donation_cert )

        # =====================================================================
        # In (Receive / Donation / etc) Items
        #
        resourcename = "recv_item"
        tablename = "inv_recv_item"
        table = db.define_table(tablename,
                                recv_id(),
                                item_id,
                                supply_item_id(),
                                item_pack_id(),
                                Field("quantity", "double",
                                      label = T("Quantity"),
                                      notnull = True),
                                s3_comments(),
                                req_item_id(readable = False,
                                            writable = False),
                                *s3_meta_fields())

        # pack_quantity virtual field
        table.virtualfields.append(item_pack_virtualfields(tablename = tablename))

        # CRUD strings
        if deployment_settings.get_inv_shipment_name() == "order":
            ADD_RECV_ITEM = T("Add Item to Order")
            LIST_RECV_ITEMS = T("List Order Items")
            s3.crud_strings[tablename] = Storage(
                title_create = ADD_RECV_ITEM,
                title_display = T("Order Item Details"),
                title_list = LIST_RECV_ITEMS,
                title_update = T("Edit Order Item"),
                title_search = T("Search Order Items"),
                subtitle_create = T("Add New Item to Order"),
                subtitle_list = T("Order Items"),
                label_list_button = LIST_RECV_ITEMS,
                label_create_button = ADD_RECV_ITEM,
                label_delete_button = T("Remove Item from Order"),
                msg_record_created = T("Item added to order"),
                msg_record_modified = T("Order Item updated"),
                msg_record_deleted = T("Item removed from order"),
                msg_list_empty = T("No Order Items currently registered"))
        else:
            ADD_RECV_ITEM = T("Add Item to Shipment")
            LIST_RECV_ITEMS = T("List Received Items")
            s3.crud_strings[tablename] = Storage(
                title_create = ADD_RECV_ITEM,
                title_display = T("Received Item Details"),
                title_list = LIST_RECV_ITEMS,
                title_update = T("Edit Received Item"),
                title_search = T("Search Received Items"),
                subtitle_create = T("Add New Received Item"),
                subtitle_list = T("Shipment Items"),
                label_list_button = LIST_RECV_ITEMS,
                label_create_button = ADD_RECV_ITEM,
                label_delete_button = T("Remove Item from Shipment"),
                msg_record_created = T("Item added to shipment"),
                msg_record_modified = T("Received Item updated"),
                msg_record_deleted = T("Item removed from shipment"),
                msg_list_empty = T("No Received Items currently registered"))

        # ---------------------------------------------------------------------
        s3mgr.configure(tablename,
                        super_entity = "supply_item_entity",
                        )

        # =====================================================================
        # Send (Outgoing / Dispatch / etc)
        #
        resourcename = "send"
        tablename = "inv_send"
        table = db.define_table(tablename,
                                Field( "date",
                                       "date",
                                       label = T("Date Sent"),
                                       writable = False,
                                       represent = lambda date: date or NONE),
                                person_id(name = "sender_id",
                                          label = T("Sent By"),
                                          default = s3_logged_in_person()),
                                super_link("site_id", "org_site",
                                           label = T("From Inventory"),
                                           default = auth.user.site_id if auth.is_logged_in() else None,
                                           readable = True,
                                           writable = True,
                                           # Comment these to use a Dropdown & not an Autocomplete
                                           #widget = S3SiteAutocompleteWidget(),
                                           #comment = DIV(_class="tooltip",
                                           #              _title="%s|%s" % (T("From Inventory"),
                                           #                                T("Enter some characters to bring up a list of possible matches"))),
                                           represent=org_site_represent),
                                Field( "delivery_date",
                                       "date",
                                       label = T("Est. Delivery Date"),
                                       represent = lambda date: date or NONE),
                                Field("to_site_id",
                                       db.org_site,
                                       label = T("To Facility"),
                                       requires = IS_ONE_OF(db,
                                                            "org_site.site_id",
                                                             lambda id: org_site_represent(id, link = False),
                                                             sort=True,
                                                            ),
                                       represent =  org_site_represent
                                      ),
                                #location_id( "to_location_id",
                                #             label = T("To Location") ),
                                Field("status",
                                      "integer",
                                      requires = IS_NULL_OR(IS_IN_SET(shipment_status)),
                                      represent = lambda opt: shipment_status.get(opt, UNKNOWN_OPT),
                                      default = SHIP_STATUS_IN_PROCESS,
                                      label = T("Status"),
                                      writable = False,
                                      ),
                                person_id(name = "recipient_id",
                                          label = T("To Person")),
                                s3_comments(),
                                *s3_meta_fields())

        # ---------------------------------------------------------------------
        # CRUD strings
        ADD_SEND = T("Send Shipment")
        LIST_SEND = T("List Sent Shipments")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_SEND,
            title_display = T("Sent Shipment Details"),
            title_list = LIST_SEND,
            title_update = T("Shipment to Send"),
            title_search = T("Search Sent Shipments"),
            subtitle_create = ADD_SEND,
            subtitle_list = T("Sent Shipments"),
            label_list_button = LIST_SEND,
            label_create_button = ADD_SEND,
            label_delete_button = T("Delete Sent Shipment"),
            msg_record_created = T("Shipment Created"),
            msg_record_modified = T("Sent Shipment updated"),
            msg_record_deleted = T("Sent Shipment canceled"),
            msg_list_empty = T("No Sent Shipments"))

        # ---------------------------------------------------------------------
        def inv_send_represent(id):
            if id:
                table = db.inv_send
                send_row = db(table.id == id).select(table.date,
                                                     table.to_site_id,
                                                     limitby=(0, 1)).first()
                return SPAN( org_site_represent( send_row.to_site_id),
                             " - ",
                            send_row.date)
            else:
                return NONE

        # ---------------------------------------------------------------------
        # Reusable Field
        send_id = S3ReusableField( "send_id", db.inv_send, sortby="date",
                                   requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                   "inv_send.id",
                                                                   inv_send_represent,
                                                                   orderby="inv_send_id.date",
                                                                   sort=True)),
                                   represent = inv_send_represent,
                                   label = T("Send Shipment"),
                                   ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Inv Send Incoming as a simulated "component" of Inventory Store
        def inv_incoming():
            """
                Pipeline Report showing the inbound shipments which haven't yet been received
                Allows easy access to Receive these shipments into the Inventory

                @ToDo: Provide a function to allow adding new expected shipments which are coming ex-system
                       - this would be adding a Sent Shipment with us as Destination, not Source
            """
            tablename, id = request.vars.viewing.split(".")
            record = db[tablename][id]
            to_site_id = record.site_id
            site_id = record.site_id

            rheader_dict = dict(org_office = office_rheader)
            if deployment_settings.has_module("cr"):
                rheader_dict["cr_shelter"] = response.s3.shelter_rheader
            if deployment_settings.has_module("hms"):
                rheader_dict["hms_hospital"] = hms_hospital_rheader

            response.s3.filter = (db.inv_send.status == SHIP_STATUS_SENT) & \
                                 (db.inv_send.to_site_id == to_site_id)

            s3mgr.configure("inv_send", insertable=False)

            response.s3.actions = [dict(url = URL(c="inv", f="send",
                                                  args = ["[id]", "send_item"],
                                                  vars = dict(site_id = site_id)
                                                  ),
                                        _class = "action-btn",
                                        label = str(T("Review"))),
                                   dict(url = URL(c="inv", f="recv_sent",
                                                  args = ["[id]"],
                                                  vars = dict(site_id = site_id)
                                                   ),
                                        _class = "action-btn",
                                        label = "%s    " % T("Process")),
                                   ]

            # @ToDo: Probably need to adjust some more CRUD strings:
            s3.crud_strings["inv_send"].update(
                msg_record_modified = T("Incoming Shipment updated"),
                msg_record_deleted = T("Incoming Shipment canceled"),
                msg_list_empty = T("No Incoming Shipments"))

            output = s3_rest_controller("inv", "send",
                                        method = "list",
                                        rheader = rheader_dict[tablename],
                                        title = s3.crud_strings[tablename]["title_display"])

            return output
        # ---------------------------------------------------------------------
        # Redirect to the Items tabs after create & update
        url_send_items = URL(c="inv", f="send", args=["[id]",
                                                                 "send_item"])
        s3mgr.configure(tablename,
                        create_next = url_send_items,
                        update_next = url_send_items)

        # send set as a component of Sites in controller, depending if it
        # is outgoing or incoming
        # ---------------------------------------------------------------------
        def inv_send_form (r, **attr):
            """ Generate a PDF of a Consignment Note """
            db.inv_recv.date.readable = True
            return s3_component_form(r,
                                     componentname = "send_item",
                                     formname = T("Consignment Note"),
                                     filename = "CN",
                                     **attr)

        s3mgr.model.set_method(module, resourcename,
                               method="form", action=inv_send_form )

        # ---------------------------------------------------------------------
        def inv_send_rheader(r):
            """ Resource Header for Send """

            if r.representation == "html" and r.name == "send":
                send_record = r.record
                if send_record:
                    rheader = DIV( TABLE(
                                       TR( TH("%s: " % T("Date")),
                                           send_record.date,
                                           TH("%s: " % T("Est. Delivery Date")),
                                           send_record.delivery_date or NONE,
                                          ),
                                       TR( TH("%s: " % T("From")),
                                           org_site_represent(send_record.site_id),
                                           TH("%s: " % T("To")),
                                           org_site_represent(send_record.to_site_id),
                                          ),
                                       TR( TH("%s: " % T("Status")),
                                           shipment_status.get(send_record.status, UNKNOWN_OPT),
                                           TH("%s: " % T("Comments")),
                                           TD(send_record.comments, _colspan=3)
                                          )
                                         )
                                    )
                    response.s3.rfooter = TAG[""]()

                    if send_record.status == SHIP_STATUS_IN_PROCESS:
                        if auth.s3_has_permission("update",
                                                  db.inv_send,
                                                  record_id=send_record.id):
                            send_btn = A( T("Send Shipment"),
                                          _href = URL(c = "inv",
                                                      f = "send_process",
                                                      args = [send_record.id]
                                                      ),
                                          _id = "send_process",
                                          _class = "action-btn"
                                          )

                            send_btn_confirm = SCRIPT("S3ConfirmClick('#send_process', '%s')"
                                                      % T("Do you want to send this shipment?") )
                            response.s3.rfooter.append(send_btn)
                            response.s3.rfooter.append(send_btn_confirm)
                    else:
                        cn_btn = A( T("Consignment Note"),
                                      _href = URL(#c = "inv",
                                                  f = "send",
                                                  args = [send_record.id, "form.pdf"]
                                                  ),
                                      _class = "action-btn"
                                      )
                        response.s3.rfooter.append(cn_btn)

                        if send_record.status != SHIP_STATUS_CANCEL:
                            if send_record.status == SHIP_STATUS_SENT:
                                if "site_id" in request.vars and \
                                    auth.s3_has_permission("update",
                                                           db.org_site,
                                                           record_id=request.vars.site_id):
                                    receive_btn = A( T("Process Received Shipment"),
                                                    _href = URL(c = "inv",
                                                                f = "recv_sent",
                                                                args = [send_record.id],
                                                                vars = request.vars
                                                                ),
                                                    _id = "send_receive",
                                                    _class = "action-btn",
                                                    _title = "Receive this shipment"
                                                    )

                                    #receive_btn_confirm = SCRIPT("S3ConfirmClick('#send_receive', '%s')"
                                    #                             % T("Receive this shipment?") )
                                    response.s3.rfooter.append(receive_btn)
                                    #rheader.append(receive_btn_confirm)
                                if auth.s3_has_permission("update",
                                                          db.inv_send,
                                                          record_id=send_record.id):
                                    if "received" in request.vars:
                                        db.inv_send[send_record.id] = \
                                            dict(status = SHIP_STATUS_RECEIVED)
                                    else:
                                        receive_btn = A( T("Confirm Shipment Received"),
                                                        _href = URL(#c = "inv",
                                                                    f = "send",
                                                                    args = [send_record.id],
                                                                    vars = dict(received = True),
                                                                    ),
                                                        _id = "send_receive",
                                                        _class = "action-btn",
                                                        _title = "Only use this button to confirm that the shipment has been received by the destination, if the destination will not enter this information into the system directly"
                                                        )

                                        receive_btn_confirm = SCRIPT("S3ConfirmClick('#send_receive', '%s')"
                                                                     % T("This shipment will be confirmed as received.") )
                                        response.s3.rfooter.append(receive_btn)
                                        response.s3.rfooter.append(receive_btn_confirm)
                                if auth.s3_has_permission("delete",
                                                          db.inv_send,
                                                          record_id=send_record.id):
                                    cancel_btn = A( T("Cancel Shipment"),
                                                    _href = URL(c = "inv",
                                                                f = "send_cancel",
                                                                args = [send_record.id]
                                                                ),
                                                    _id = "send_cancel",
                                                    _class = "action-btn"
                                                    )

                                    cancel_btn_confirm = SCRIPT("S3ConfirmClick('#send_cancel', '%s')"
                                                                 % T("Do you want to cancel this sent shipment? The items will be returned to the Inventory. This action CANNOT be undone!") )
                                    response.s3.rfooter.append(cancel_btn)
                                    response.s3.rfooter.append(cancel_btn_confirm)

                    rheader.append(s3_rheader_tabs( r,
                                                     [(T("Edit Details"), None),
                                                      (T("Items"), "send_item"),
                                                      ]
                                                    ))
                    return rheader
            return None

        # ---------------------------------------------------------------------
        def inv_send_controller():
            """ RESTful CRUD controller """

            table = db.inv_send

            # Limit site_id to sites the user has permissions for
            auth.permission.permitted_facilities(table=table,
                                                 error_msg=T("You do not have permission for any facility to send a shipment."))

            # Set Validator for checking against the number of items in the warehouse
            if (request.vars.inv_item_id):
                db.inv_send_item.quantity.requires = QUANTITY_INV_ITEM(db,
                                                                       request.vars.inv_item_id,
                                                                       request.vars.item_pack_id)

            def prep(r):
                # Default to the Search tab in the location selector
                response.s3.gis.tab = "search"

                # If component view
                if r.record:
                    if r.record.get("site_id"):
                        # Restrict to items from this warehouse only
                        db.inv_send_item.inv_item_id.requires = IS_ONE_OF(db,
                                                                          "inv_inv_item.id",
                                                                          response.s3.inv_item_represent,
                                                                          orderby="inv_inv_item.id",
                                                                          sort=True,
                                                                          filterby = "site_id",
                                                                          filter_opts = [r.record.site_id]
                                                                         )
                    if r.record.status == SHIP_STATUS_IN_PROCESS:
                        s3.crud_strings.inv_send.title_update = \
                        s3.crud_strings.inv_send.title_display = T("Process Shipment to Send")
                    elif "site_id" in request.vars and r.record.status == SHIP_STATUS_SENT:
                        s3.crud_strings.inv_send.title_update = \
                        s3.crud_strings.inv_send.title_display = T("Review Incoming Shipment to Receive")

                return True

            response.s3.prep = prep

            output = s3_rest_controller("inv", "send",
                                        rheader=inv_send_rheader)
            return output

        # =====================================================================
        # Send (Outgoing / Dispatch / etc) Items
        #
        log_sent_item_status = { 0: NONE,
                                 1: "Insufficient Quantity" }

        resourcename = "send_item"
        tablename = "inv_send_item"
        table = db.define_table(tablename,
                                send_id(),
                                inv_item_id(),
                                item_pack_id(),
                                Field("quantity", "double",
                                      notnull = True),
                                s3_comments(),
                                Field("status",
                                      "integer",
                                      requires = IS_NULL_OR(IS_IN_SET(log_sent_item_status)),
                                      represent = lambda opt: log_sent_item_status[opt] if opt else log_sent_item_status[0],
                                      writable = False),
                                req_item_id(readable = False,
                                            writable = False),
                                *s3_meta_fields())

        # pack_quantity virtual field
        table.virtualfields.append(item_pack_virtualfields(tablename = tablename))

        # CRUD strings
        ADD_SEND_ITEM = T("Add Item to Shipment")
        LIST_SEND_ITEMS = T("List Sent Items")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_SEND_ITEM,
            title_display = T("Sent Item Details"),
            title_list = LIST_SEND_ITEMS,
            title_update = T("Edit Sent Item"),
            title_search = T("Search Sent Items"),
            subtitle_create = T("Add New Sent Item"),
            subtitle_list = T("Shipment Items"),
            label_list_button = LIST_SEND_ITEMS,
            label_create_button = ADD_SEND_ITEM,
            label_delete_button = T("Delete Sent Item"),
            msg_record_created = T("Item Added to Shipment"),
            msg_record_modified = T("Sent Item updated"),
            msg_record_deleted = T("Sent Item deleted"),
            msg_list_empty = T("No Sent Items currently registered"))

        # ---------------------------------------------------------------------
        def inv_send_item_onaccept(form):
            try:
                # Clear insufficient quantity status
                db.inv_send_item[form.vars.id] = dict(status = 0)
            except:
                pass

        # Update owned_by_role to the send's owned_by_role
        s3mgr.configure(tablename,
                        onaccept = inv_send_item_onaccept)

        # =====================================================================
        # Inventory Controller Helper functions
        # ---------------------------------------------------------------------
        def inv_prep(r):
            if r.component:
                if r.component.name == "inv_item":
                    table = db.inv_inv_item
                    # Filter out items which are already in this inventory
                    query = (table.site_id == r.record.site_id) & \
                            (table.deleted == False)
                    inv_item_rows =  db(query).select(table.item_id)
                    item_ids = [row.item_id for row in inv_item_rows]

                    # Ensure that the current item CAN be selected
                    if r.method == "update":
                        item_ids.remove(table[r.args[2]].item_id)
                    table.item_id.requires.set_filter(not_filterby = "id",
                                                      not_filter_opts = item_ids)

                elif r.component.name == "send":
                    # Default to the Search tab in the location selector
                    response.s3.gis.tab = "search"
                    if request.get_vars.get("select", "sent") == "incoming":
                        # Display only incoming shipments which haven't been received yet
                        filter = (db.inv_send.status == SHIP_STATUS_SENT)
                        #r.resource.add_component_filter("send", filter)

        # ---------------------------------------------------------------------
        # Session dictionary to indicate if a site inv should be shown
        if session.s3.show_inv == None:
            session.s3.show_inv = {}

        def inv_tabs(r):
            """
                Add an expandable set of Tabs for a Site's Inventory Tasks

                @ToDo: Make these Expand/Contract without a server-side call
            """
            if deployment_settings.has_module("inv") and \
                auth.s3_has_permission("read", db.inv_inv_item):
                collapse_tabs = deployment_settings.get_inv_collapse_tabs()
                if collapse_tabs and not \
                    (r.tablename == "org_office" and r.record.type == 5): # 5 = Warehouse
                    # Test if the tabs are collapsed
                    show_collapse = True
                    show_inv = r.get_vars.show_inv
                    if show_inv == "True":
                        show_inv = True
                    elif show_inv == "False":
                        show_inv = False
                    else:
                        show_inv = None
                    if show_inv == True or show_inv == False:
                        session.s3.show_inv["%s_%s" %  (r.name, r.id)] = show_inv
                    else:
                        show_inv = session.s3.show_inv.get("%s_%s" %  (r.name, r.id))
                else:
                    show_inv = True
                    show_collapse = False

                if show_inv:
                    if deployment_settings.get_inv_shipment_name() == "order":
                        recv_tab = T("Orders")
                    else:
                        recv_tab = T("Receive")
                    inv_tabs = [(T("Inventory Items"), "inv_item"),
                                (T("Incoming"), "incoming/"),
                                (recv_tab, "recv"),
                                (T("Send"), "send", dict(select="sent")),
                                ]
                    if deployment_settings.has_module("proc"):
                        inv_tabs.append((T("Planned Procurements"), "plan"))
                    if show_collapse:
                        inv_tabs.append(("- %s" % T("Inventory"),
                                         None, dict(show_inv="False")))
                else:
                    inv_tabs = [("+ %s" % T("Inventory"), "inv_item",
                                dict(show_inv="True"))]
                return inv_tabs
            else:
                return []

#        def inv_warehouse_import(r, **attr):
#            if r.representation == "html":
#                response.view = "inv/warehouse_upload_csv.html"
#                output = dict()
#                return output
#
#        s3mgr.model.set_method("org", "office",
#                               method="import", action=inv_warehouse_import )

        # Pass variables back to global scope (response.s3.*)
        return dict(
            inv_item_represent = inv_item_represent,
            inv_prep = inv_prep,
            inv_incoming = inv_incoming,
            inv_tabs = inv_tabs,
            inv_item_controller = inv_item_controller,
            inv_send_controller = inv_send_controller,
            inv_recv_controller = inv_recv_controller
            )

    # Provide a handle to this load function
    s3mgr.loader(inv_tables,
                 "inv_inv_item",
                 "inv_recv",
                 "inv_recv_item",
                 "inv_send",
                 "inv_send_item")

# END =========================================================================

