# -*- coding: utf-8 -*-

""" Sahana Eden Inventory Model

    @copyright: 2009-2012 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ["S3InventoryModel",
           "S3IncomingModel",
           "S3DistributionModel",
           "inv_tabs",
           "inv_recv_rheader",
           "inv_send_rheader",
           "inv_ship_status",
          ]

from gluon import *
from gluon.sqlhtml import RadioWidget
from gluon.storage import Storage
from ..s3 import *

SHIP_STATUS_IN_PROCESS = 0
SHIP_STATUS_RECEIVED   = 1
SHIP_STATUS_SENT       = 2
SHIP_STATUS_CANCEL     = 3

# To pass to global scope
inv_ship_status = {
                    "IN_PROCESS" : SHIP_STATUS_IN_PROCESS,
                    "RECEIVED"   : SHIP_STATUS_RECEIVED,
                    "SENT"       : SHIP_STATUS_SENT,
                    "CANCEL"     : SHIP_STATUS_CANCEL,
                }

T = current.T
shipment_status = { SHIP_STATUS_IN_PROCESS: T("In Process"),
                    SHIP_STATUS_RECEIVED:   T("Received"),
                    SHIP_STATUS_SENT:       T("Sent"),
                    SHIP_STATUS_CANCEL:     T("Canceled") }

SHIP_DOC_PENDING  = 0
SHIP_DOC_COMPLETE = 1

# =============================================================================
class S3InventoryModel(S3Model):
    """
        Inventory Management

        A module to record inventories of items at a location (site)
    """

    names = ["inv_inv_item",
             "inv_item_id",
             "inv_item_represent",
             "inv_prep",
            ]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        s3 = current.response.s3
        settings = current.deployment_settings

        currency_type = s3.currency_type
        org_site_represent = self.org_site_represent
        item_id = self.supply_item_entity_id
        supply_item_id = self.supply_item_id
        item_pack_id = self.supply_item_pack_id
        item_pack_virtualfields = self.supply_item_pack_virtualfields

        s3_date_format = settings.get_L10n_date_format()
        s3_date_represent = lambda dt: S3DateTime.date_represent(dt, utc=True)

        # =====================================================================
        # Inventory Item
        #
        tablename = "inv_inv_item"
        table = self.define_table(tablename,
                                  self.super_link("site_id", "org_site",
                                                  label = T("Warehouse"),
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
                                  Field("expiry_date", "date",
                                        label = T("Expiry Date"),
                                        requires = IS_NULL_OR(IS_DATE(format = s3_date_format)),
                                        represent = s3_date_represent,
                                        widget = S3DateWidget()
                                        ),
                                  # @ToDo: Allow items to be marked as 'still on the shelf but allocated to an outgoing shipment'
                                  #Field("status"),
                                  s3.comments(),
                                  *s3.meta_fields())

        table.virtualfields.append(item_pack_virtualfields(tablename=tablename))

        # CRUD strings
        INV_ITEM = T("Warehouse Stock")
        ADD_INV_ITEM = T("Add Stock to Warehouse")
        LIST_INV_ITEMS = T("List Stock in Warehouse")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_INV_ITEM,
            title_display = T("Warehouse Stock Details"),
            title_list = LIST_INV_ITEMS,
            title_update = T("Edit Warehouse Stock"),
            title_search = T("Search Warehouse Stock"),
            title_upload = T("Import Warehouse Stock"),
            subtitle_create = ADD_INV_ITEM,
            subtitle_list = T("Warehouse Stock"),
            label_list_button = LIST_INV_ITEMS,
            label_create_button = ADD_INV_ITEM,
            label_delete_button = T("Remove Stock from Warehouse"),
            msg_record_created = T("Stock added to Warehouse"),
            msg_record_modified = T("Warehouse Stock updated"),
            msg_record_deleted = T("Stock removed from Warehouse"),
            msg_list_empty = T("No Stock currently registered in this Warehouse"))

        # Reusable Field
        inv_item_id = S3ReusableField("inv_item_id", db.inv_inv_item,
                                      requires = IS_ONE_OF(db,
                                                           "inv_inv_item.id",
                                                           self.inv_item_represent,
                                                           orderby="inv_inv_item.id",
                                                           sort=True),
                                      represent = self.inv_item_represent,
                                      label = INV_ITEM,
                                      comment = DIV( _class="tooltip",
                                                     _title="%s|%s" % (INV_ITEM,
                                                                       T("Select Stock from this Warehouse"))),
                                      ondelete = "CASCADE",
                                      script = SCRIPT("""
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

        report_filter = [
                         S3SearchSimpleWidget(
                             name="inv_item_search_text",
                             label=T("Search"),
                             comment=T("Search for an item by text."),
                             field=[ "item_id$name",
                                     #"item_id$category_id$name",
                                     #"site_id$name"
                                    ]
                             ),
                          S3SearchOptionsWidget(
                              name="recv_search_site",
                              label=T("Facility"),
                              field=["site_id"],
                              represent ="%(name)s",
                              comment=T("If none are selected, then all are searched."),
                              cols = 2
                              ),
                          S3SearchMinMaxWidget(
                              name="inv_item_search_expiry_date",
                              method="range",
                              label=T("Expiry Date"),
                              field=["expiry_date"]
                              )
                         ]

        # Item Search Method (Advanced Search only)
        inv_item_search = S3Search(advanced=report_filter)

        self.configure(tablename,
                       super_entity = "supply_item_entity",
                       search_method = inv_item_search,
                       report_filter = report_filter,
                       report_rows = ["item_id"],
                       report_cols = ["site_id"],
                       report_fact = ["quantity"],
                       report_method=["sum"],
                       report_groupby = self.inv_inv_item.site_id,
                       report_hide_comments = True
                       )

        # Component
        self.add_component("inv_send_item",
                           inv_inv_item="inv_item_id")

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                    inv_item_id = inv_item_id,
                    inv_item_represent = self.inv_item_represent,
                    inv_prep = self.inv_prep,
                )
    # ---------------------------------------------------------------------
    @staticmethod
    def inv_prep(r):
        """
            Used in site REST controllers to Filter out items which are
            already in this inventory
        """

        if r.component:

            db = current.db
            s3db = current.s3db

            if r.component.name == "inv_item":
                table = s3db.inv_inv_item
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
                current.response.s3.gis.tab = "search"
                if current.request.get_vars.get("select", "sent") == "incoming":
                    # Display only incoming shipments which haven't been received yet
                    filter = (s3db.inv_send.status == SHIP_STATUS_SENT)
                    #r.resource.add_component_filter("send", filter)

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_item_represent(id):
        """
        """

        db = current.db
        s3db = current.s3db

        itable = s3db.inv_inv_item
        stable = s3db.supply_item
        query = (itable.id == id) & \
                (itable.item_id == stable.id)
        record = db(query).select(stable.name,
                                  limitby = (0, 1)).first()
        if record:
            return record.name
        else:
            return None


# =============================================================================
class S3IncomingModel(S3Model):
    """
        A module to record Incoming items to an Inventory:
        - Donations, Purchases, Stock Transfers
    """

    names = ["inv_recv",
             "inv_recv_item",
            ]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        s3 = current.response.s3
        settings = current.deployment_settings

        person_id = self.pr_person_id
        #location_id = self.gis_location_id
        #organisation_id = self.org_organisation_id
        #organisation_represent = self.org_organisation_represent
        org_site_represent = self.org_site_represent
        item_id = self.supply_item_entity_id
        supply_item_id = self.supply_item_id
        item_pack_id = self.supply_item_pack_id
        item_pack_virtualfields = self.supply_item_pack_virtualfields
        req_item_id = self.req_item_id

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        s3_date_format = settings.get_L10n_date_format()
        s3_date_represent = lambda dt: S3DateTime.date_represent(dt, utc=True)

        # =====================================================================
        # Received (In/Receive / Donation / etc)
        #
        inv_recv_type = { 0: NONE,
                          1: T("Another Stock"),
                          2: T("Donation"),
                          3: T("Supplier"),
                        }

        ship_doc_status = { SHIP_DOC_PENDING  : T("Pending"),
                            SHIP_DOC_COMPLETE : T("Complete") }

        radio_widget = lambda field, value: \
                                RadioWidget().widget(field, value, cols = 2)

        tablename = "inv_recv"
        table = self.define_table(tablename,
                                  Field("eta", "date",
                                        label = T("Date Expected"),
                                        requires = IS_NULL_OR(IS_DATE(format = s3_date_format)),
                                        represent = s3_date_represent,
                                        widget = S3DateWidget()
                                        ),
                                  Field("date", "date",
                                        label = T("Date Received"),
                                        writable = False,
                                        requires = IS_NULL_OR(IS_DATE(format = s3_date_format)),
                                        represent = s3_date_represent,
                                        widget = S3DateWidget(),
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
                                            default = auth.s3_logged_in_person(),
                                            comment = self.pr_person_comment(child="recipient_id")),
                                  self.super_link("site_id", "org_site",
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
                                        self.org_site,
                                        label = T("From Facility"),
                                        requires = IS_ONE_OF(db,
                                                             "org_site.site_id",
                                                             lambda id: org_site_represent(id, link = False),
                                                             sort=True,
                                                            ),
                                        represent = org_site_represent
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
                                            comment = self.pr_person_comment(child="sender_id"),
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
                                  s3.comments(),
                                  *s3.meta_fields())

        # Reusable Field
        if settings.get_inv_shipment_name() == "order":
            recv_id_label = T("Order")
        else:
            recv_id_label = T("Receive Shipment")
        recv_id = S3ReusableField("recv_id", db.inv_recv, sortby="date",
                                  requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                  "inv_recv.id",
                                                                  self.inv_recv_represent,
                                                                  orderby="inv_recv.date",
                                                                  sort=True)),
                                  represent = self.inv_recv_represent,
                                  label = recv_id_label,
                                  #comment = DIV(A(ADD_DISTRIBUTION, _class="colorbox", _href=URL(c="inv", f="distrib", args="create", vars=dict(format="popup")), _target="top", _title=ADD_DISTRIBUTION),
                                  #          DIV( _class="tooltip", _title=T("Distribution") + "|" + T("Add Distribution."))),
                                  ondelete = "CASCADE")

        # Search Method
        if settings.get_inv_shipment_name() == "order":
            recv_search_comment = T("Search for an order by looking for text in any field.")
            recv_search_date_field = "eta"
            recv_search_date_comment = T("Search for an order expected between these dates")
        else:
            recv_search_comment = T("Search for a shipment by looking for text in any field.")
            recv_search_date_field = "date"
            recv_search_date_comment = T("Search for a shipment received between these dates")
        recv_search = S3Search(
            simple=(S3SearchSimpleWidget(
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
            advanced=(S3SearchSimpleWidget(
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
                      S3SearchMinMaxWidget(
                        name="recv_search_date",
                        method="range",
                        label=table[recv_search_date_field].label,
                        comment=recv_search_date_comment,
                        field=[recv_search_date_field]
                      ),
                      S3SearchOptionsWidget(
                        name="recv_search_site",
                        label=T("Facility"),
                        field=["site_id"],
                        represent ="%(name)s",
                        cols = 2
                      ),
                      S3SearchOptionsWidget(
                        name="recv_search_status",
                        label=T("Status"),
                        field=["status"],
                        cols = 2
                      ),
                      S3SearchOptionsWidget(
                        name="recv_search_grn",
                        label=T("GRN Status"),
                        field=["grn_status"],
                        cols = 2
                      ),
                      S3SearchOptionsWidget(
                        name="recv_search_cert",
                        label=T("Certificate Status"),
                        field=["grn_status"],
                        cols = 2
                      ),
            ))

        self.configure(tablename,
                       search_method = recv_search)

        # Component
        self.add_component("inv_recv_item",
                           inv_recv="recv_id")

        # Print Forms
        self.set_method(tablename,
                        method="form",
                        action=self.inv_recv_form)

        self.set_method(tablename,
                        method="cert",
                        action=self.inv_recv_donation_cert )

        # =====================================================================
        # In (Receive / Donation / etc) Items
        #
        tablename = "inv_recv_item"
        table = self.define_table(tablename,
                                  recv_id(),
                                  item_id,
                                  supply_item_id(),
                                  item_pack_id(),
                                  Field("quantity", "double",
                                        label = T("Quantity"),
                                        notnull = True),
                                  s3.comments(),
                                  req_item_id(readable = False,
                                              writable = False),
                                  *s3.meta_fields())

        self.configure(tablename,
                       super_entity = "supply_item_entity")

        # pack_quantity virtual field
        table.virtualfields.append(item_pack_virtualfields(tablename=tablename))

        # CRUD strings
        if settings.get_inv_shipment_name() == "order":
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
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                )

    # ---------------------------------------------------------------------
    def inv_recv_represent(id):
        """
            @ToDo: 'From Organisation' is great for Donations
            (& Procurement if we make Suppliers Organisations), but isn't useful
            for shipments between facilities within a single Org where
            'From Facility' could be more appropriate
        """

        if id:

            db = current.db
            s3db = current.s3db

            table = s3db.inv_recv
            inv_recv_row = db(table.id == id).select(table.date,
                                                     table.from_site_id,
                                                     #table.organisation_id,
                                                     limitby=(0, 1)).first()
            return SPAN(table.from_site_id.represent(inv_recv_row.from_site_id),
                        #"(", table.organisation_id.represent( inv_recv_row.organisation_id), ")",
                        " - ",
                        table.date.represent(inv_recv_row.date)
                        )
        else:
            return current.messages.NONE

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_recv_form (r, **attr):
        """
            Generate a PDF of a GRN (Goods Received Note)
        """

        T = current.T
        s3db = current.s3db

        table = s3db.inv_recv
        table.date.readable = True
        table.site_id.readable = True
        table.site_id.label = T("By Warehouse")
        table.site_id.represent = s3db.org_site_represent

        exporter = S3PDF()
        return exporter(r,
                        componentname = "recv_item",
                        formname = T("Goods Received Note"),
                        filename = T("GRN"),
                        **attr
                       )

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_recv_donation_cert (r, **attr):
        """
            Generate a PDF of a Donation certificate
        """

        s3db = current.s3db

        table = s3db.inv_recv
        table.date.readable = True
        table.type.readable = False
        table.site_id.readable = True
        table.site_id.label = T("By Warehouse")
        table.site_id.represent = s3dborg_site_represent

        exporter = S3PDF()
        return exporter(r,
                        componentname = "recv_item",
                        formname = T("Donation Certificate"),
                        filename = T("DC"),
                        **attr
                       )


# =============================================================================
class S3DistributionModel(S3Model):
    """
        Distribution Management

        A module to record all Outgoing stock from an Inventory:
        - Distributions, Stock Transfers
    """

    names = ["inv_send",
             "inv_send_item",
            ]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        s3 = current.response.s3
        settings = current.deployment_settings

        person_id = self.pr_person_id
        #location_id = self.gis_location_id
        org_site_represent = self.org_site_represent
        # @ToDo: make Sent Items an Item Entity instance
        #item_id = self.supply_item_entity_id
        #supply_item_id = self.supply_item_id
        inv_item_id = self.inv_item_id
        item_pack_id = self.supply_item_pack_id
        item_pack_virtualfields = self.supply_item_pack_virtualfields
        req_item_id = self.req_item_id

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        s3_date_format = settings.get_L10n_date_format()
        s3_date_represent = lambda dt: S3DateTime.date_represent(dt, utc=True)

        # =====================================================================
        # Send (Outgoing / Dispatch / etc)
        #
        tablename = "inv_send"
        table = self.define_table(tablename,
                                  Field("date", "date",
                                        label = T("Date Sent"),
                                        writable = False,
                                        requires = IS_NULL_OR(IS_DATE(format = s3_date_format)),
                                        represent = s3_date_represent,
                                        widget = S3DateWidget()
                                        ),
                                  person_id(name = "sender_id",
                                            label = T("Sent By"),
                                            default = auth.s3_logged_in_person(),
                                            comment = self.pr_person_comment(child="sender_id")),
                                  self.super_link("site_id", "org_site",
                                             label = T("From Facility"),
                                             default = auth.user.site_id if auth.is_logged_in() else None,
                                             readable = True,
                                             writable = True,
                                             # Comment these to use a Dropdown & not an Autocomplete
                                             #widget = S3SiteAutocompleteWidget(),
                                             #comment = DIV(_class="tooltip",
                                             #              _title="%s|%s" % (T("From Warehouse"),
                                             #                                T("Enter some characters to bring up a list of possible matches"))),
                                            represent=org_site_represent),
                                  Field("delivery_date", "date",
                                        label = T("Est. Delivery Date"),
                                        requires = IS_NULL_OR(IS_DATE(format = s3_date_format)),
                                        represent = s3_date_represent,
                                        widget = S3DateWidget()
                                        ),
                                  Field("to_site_id",
                                        self.org_site,
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
                                            label = T("To Person"),
                                            comment = self.pr_person_comment(child="recipient_id")),
                                  s3.comments(),
                                  *s3.meta_fields())

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

        # Reusable Field
        send_id = S3ReusableField( "send_id", db.inv_send, sortby="date",
                                   requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                   "inv_send.id",
                                                                   self.inv_send_represent,
                                                                   orderby="inv_send_id.date",
                                                                   sort=True)),
                                   represent = self.inv_send_represent,
                                   label = T("Send Shipment"),
                                   ondelete = "CASCADE")

        # Component
        self.add_component("inv_send_item",
                           inv_send="send_id")

        # Generate Consignment Note
        self.set_method(tablename,
                        method="form",
                        action=self.inv_send_form )

        # =====================================================================
        # Send (Outgoing / Dispatch / etc) Items
        #
        log_sent_item_status = { 0: NONE,
                                 1: T("Insufficient Quantity") }

        tablename = "inv_send_item"
        table = self.define_table(tablename,
                                  send_id(),
                                  inv_item_id(),
                                  item_pack_id(),
                                  Field("quantity", "double",
                                        label = T("Quantity"),
                                        notnull = True),
                                  s3.comments(),
                                  Field("status",
                                        "integer",
                                        requires = IS_NULL_OR(IS_IN_SET(log_sent_item_status)),
                                        represent = lambda opt: log_sent_item_status[opt] if opt else log_sent_item_status[0],
                                        writable = False),
                                  req_item_id(readable = False,
                                              writable = False),
                                  *s3.meta_fields())

        # pack_quantity virtual field
        table.virtualfields.append(item_pack_virtualfields(tablename=tablename))

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

        # Update owned_by_role to the send's owned_by_role
        self.configure(tablename,
                       onaccept = self.inv_send_item_onaccept)

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                )

    # ---------------------------------------------------------------------
    def inv_send_represent(id):
        """
        """

        if id:

            db = current.db
            s3db = current.s3db

            table = s3db.inv_send
            send_row = db(table.id == id).select(table.date,
                                                 table.to_site_id,
                                                 limitby=(0, 1)).first()
            return SPAN(table.to_site_id.represent(send_row.to_site_id),
                        " - ",
                        table.date.represent(send_row.date)
                        )
        else:
            return current.messages.NONE

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_send_form (r, **attr):
        """
            Generate a PDF of a Consignment Note
        """

        s3db = current.s3db

        table = s3db.inv_recv
        table.date.readable = True

        exporter = S3PDF()
        return exporter(r,
                        componentname = "send_item",
                        formname = T("Consignment Note"),
                        filename = "CN",
                        **attr
                       )

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_send_item_onaccept(form):
        """
        """

        s3db = current.s3db

        table = s3db.inv_send_item
        try:
            # Clear insufficient quantity status
            table[form.vars.id] = dict(status = 0)
        except:
            pass


# =============================================================================
def inv_tabs(r):
    """
        Add an expandable set of Tabs for a Site's Inventory Tasks

        @ToDo: Make these Expand/Contract without a server-side call
    """

    T = current.T
    s3db = current.s3db
    auth = current.auth
    session = current.session
    settings = current.deployment_settings

    if settings.has_module("inv") and \
        auth.s3_has_permission("read", "inv_inv_item"):
        collapse_tabs = settings.get_inv_collapse_tabs()
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
            if settings.get_inv_shipment_name() == "order":
                recv_tab = T("Orders")
            else:
                recv_tab = T("Receive")
            inv_tabs = [(T("Warehouse Stock"), "inv_item"),
                        (T("Incoming"), "incoming/"),
                        (recv_tab, "recv"),
                        (T("Send"), "send", dict(select="sent")),
                        ]
            if settings.has_module("proc"):
                inv_tabs.append((T("Planned Procurements"), "plan"))
            if show_collapse:
                inv_tabs.append(("- %s" % T("Warehouse"),
                                 None, dict(show_inv="False")))
        else:
            inv_tabs = [("+ %s" % T("Warehouse"), "inv_item",
                        dict(show_inv="True"))]
        return inv_tabs
    else:
        return []

# =============================================================================
def inv_recv_rheader(r):
    """ Resource Header for Receiving """

    if r.representation == "html" and r.name == "recv":
        record = r.record
        if record:

            T = current.T
            s3 = current.response.s3
            auth = current.auth

            tabs = [(T("Edit Details"), None),
                    (T("Items"), "recv_item"),
                    ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table

            rheader = DIV( TABLE(
                               TR( TH( "%s: " % table.eta.label),
                                   table.eta.represent(record.eta),
                                   TH("%s: " % table.status.label),
                                   table.status.represent(record.status),
                                  ),
                               TR( TH( "%s: " % table.date.label),
                                   table.date.represent(record.date),
                                  ),
                               TR( TH( "%s: " % table.site_id.label),
                                   table.site_id.represent(record.site_id),
                                  ),
                               TR( TH( "%s: " % table.from_site_id.label),
                                   table.from_site_id.represent(record.from_site_id),
                                   #TH( "%s: " % table.organisation_id.label),
                                   #table.organisation_id.represent(record.organisation_id),
                                  ),
                               TR( TH( "%s: " % table.sender_id.label),
                                   s3_fullname(record.sender_id),
                                   TH( "%s: " % table.recipient_id.label),
                                   s3_fullname(record.recipient_id),
                                  ),
                               TR( TH( "%s: " % table.comments.label),
                                   TD(record.comments or "", _colspan=2),
                                  ),
                                 ),
                            rheader_tabs
                            )

            rfooter = TAG[""]()

            if record.status == SHIP_STATUS_IN_PROCESS:
                if auth.s3_has_permission("update",
                                                  "inv_recv",
                                                  record_id=record.id):
                    recv_btn = A( T("Receive Shipment"),
                                  _href = URL(c = "inv",
                                              f = "recv_process",
                                              args = [record.id]
                                              ),
                                  _id = "recv_process",
                                  _class = "action-btn"
                                  )

                    recv_btn_confirm = SCRIPT("S3ConfirmClick('#recv_process', '%s')"
                                              % T("Do you want to receive this shipment?") )
                    rfooter.append(recv_btn)
                    rfooter.append(recv_btn_confirm)
            else:
                grn_btn = A( T("Goods Received Note"),
                              _href = URL(f = "recv",
                                          args = [record.id, "list.pdf"]
                                          ),
                              _class = "action-btn"
                              )
                rfooter.append(grn_btn)
                dc_btn = A( T("Donation Certificate"),
                              _href = URL(f = "recv",
                                          args = [record.id, "list.pdf"]
                                          ),
                              _class = "action-btn"
                              )
                rfooter.append(dc_btn)

                if record.status != SHIP_STATUS_CANCEL:
                    if current.auth.s3_has_permission("delete",
                                                      "inv_recv",
                                                      record_id=record.id):
                        cancel_btn = A( T("Cancel Shipment"),
                                        _href = URL(c = "inv",
                                                    f = "recv_cancel",
                                                    args = [record.id]
                                                    ),
                                        _id = "recv_cancel",
                                        _class = "action-btn"
                                        )

                        cancel_btn_confirm = SCRIPT("S3ConfirmClick('#recv_cancel', '%s')"
                                                     % T("Do you want to cancel this received shipment? The items will be removed from the Warehouse. This action CANNOT be undone!") )
                        rfooter.append(cancel_btn)
                        rfooter.append(cancel_btn_confirm)

            s3.rfooter = rfooter
            return rheader
    return None

# =============================================================================
def inv_send_rheader(r):
    """ Resource Header for Send """

    if r.representation == "html" and r.name == "send":
        record = r.record
        if record:

            s3db = current.s3db
            auth = current.auth
            s3 = current.response.s3

            tabs = [(T("Edit Details"), None),
                    (T("Items"), "send_item"),
                ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table

            rheader = DIV( TABLE(
                               TR( TH("%s: " % table.date.label),
                                   table.date.represent(record.date),
                                   TH("%s: " % table.delivery_date.label),
                                   table.delivery_date.represent(record.delivery_date),
                                  ),
                               TR( TH("%s: " % table.site_id.label),
                                   table.site_id.represent(record.site_id),
                                   TH("%s: " % table.to_site_id.label),
                                   table.to_site_id.represent(record.to_site_id),
                                  ),
                               TR( TH("%s: " % table.status.label),
                                   table.status.represent(record.status),
                                   TH("%s: " % table.comments.label),
                                   TD(record.comments or "", _colspan=3)
                                  )
                                 ),
                            rheader_tabs
                            )

            rfooter = TAG[""]()

            if record.status == SHIP_STATUS_IN_PROCESS:
                if auth.s3_has_permission("update",
                                          "inv_send",
                                          record_id=record.id):
                    send_btn = A( T("Send Shipment"),
                                  _href = URL(c = "inv",
                                              f = "send_process",
                                              args = [record.id]
                                              ),
                                  _id = "send_process",
                                  _class = "action-btn"
                                  )

                    send_btn_confirm = SCRIPT("S3ConfirmClick('#send_process', '%s')"
                                              % T("Do you want to send this shipment?") )
                    rfooter.append(send_btn)
                    rfooter.append(send_btn_confirm)
            else:
                cn_btn = A( T("Waybill"),
                              _href = URL(f = "send",
                                          args = [record.id, "list.pdf"]
                                          ),
                              _class = "action-btn"
                              )
                rfooter.append(cn_btn)

                if record.status != SHIP_STATUS_CANCEL:
                    if record.status == SHIP_STATUS_SENT:
                        vars = current.request.vars
                        if "site_id" in vars and \
                            auth.s3_has_permission("update",
                                                   "org_site",
                                                   record_id=vars.site_id):
                            receive_btn = A( T("Process Received Shipment"),
                                            _href = URL(c = "inv",
                                                        f = "recv_sent",
                                                        args = [record.id],
                                                        vars = vars
                                                        ),
                                            _id = "send_receive",
                                            _class = "action-btn",
                                            _title = T("Receive this shipment")
                                            )

                            #receive_btn_confirm = SCRIPT("S3ConfirmClick('#send_receive', '%s')"
                            #                             % T("Receive this shipment?") )
                            rfooter.append(receive_btn)
                            #rheader.append(receive_btn_confirm)
                        if auth.s3_has_permission("update",
                                                  "inv_send",
                                                  record_id=record.id):
                            if "received" in vars:
                                s3db.inv_send[record.id] = \
                                    dict(status = SHIP_STATUS_RECEIVED)
                            else:
                                receive_btn = A( T("Confirm Shipment Received"),
                                                _href = URL(f = "send",
                                                            args = [record.id],
                                                            vars = dict(received = True),
                                                            ),
                                                _id = "send_receive",
                                                _class = "action-btn",
                                                _title = T("Only use this button to confirm that the shipment has been received by the destination, if the destination will not enter this information into the system directly")
                                                )

                                receive_btn_confirm = SCRIPT("S3ConfirmClick('#send_receive', '%s')"
                                                             % T("This shipment will be confirmed as received.") )
                                rfooter.append(receive_btn)
                                rfooter.append(receive_btn_confirm)
                        if auth.s3_has_permission("delete",
                                                  "inv_send",
                                                  record_id=record.id):
                            cancel_btn = A( T("Cancel Shipment"),
                                            _href = URL(c = "inv",
                                                        f = "send_cancel",
                                                        args = [record.id]
                                                        ),
                                            _id = "send_cancel",
                                            _class = "action-btn"
                                            )

                            cancel_btn_confirm = SCRIPT("S3ConfirmClick('#send_cancel', '%s')"
                                                         % T("Do you want to cancel this sent shipment? The items will be returned to the Warehouse. This action CANNOT be undone!") )
                            rfooter.append(cancel_btn)
                            rfooter.append(cancel_btn_confirm)

            s3.rfooter = rfooter
            return rheader
    return None

# END =========================================================================
