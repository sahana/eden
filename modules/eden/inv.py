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
           "S3TrackingModel",
           "S3AdjustModel",
           "inv_tabs",
           "inv_warehouse_rheader",
           "inv_recv_crud_strings",
           "inv_recv_rheader",
           "inv_send_rheader",
           "inv_ship_status",
           "inv_tracking_status",
           "inv_adj_rheader",
           ]

from gluon import *
from gluon.sqlhtml import RadioWidget
from gluon.storage import Storage
from ..s3 import *
#from eden.layouts import S3AddResourceLink

SHIP_STATUS_IN_PROCESS = 0
SHIP_STATUS_RECEIVED   = 1
SHIP_STATUS_SENT       = 2
SHIP_STATUS_CANCEL     = 3
SHIP_STATUS_RETURNING  = 4

# To pass to global scope
inv_ship_status = {
                    "IN_PROCESS" : SHIP_STATUS_IN_PROCESS,
                    "RECEIVED"   : SHIP_STATUS_RECEIVED,
                    "SENT"       : SHIP_STATUS_SENT,
                    "CANCEL"     : SHIP_STATUS_CANCEL,
                    "RETURNING"  : SHIP_STATUS_RETURNING,
                }

T = current.T
shipment_status = { SHIP_STATUS_IN_PROCESS: T("In Process"),
                    SHIP_STATUS_RECEIVED:   T("Received"),
                    SHIP_STATUS_SENT:       T("Sent"),
                    SHIP_STATUS_CANCEL:     T("Canceled"),
                    SHIP_STATUS_RETURNING:  T("Returning"),
                  }

SHIP_DOC_PENDING  = 0
SHIP_DOC_COMPLETE = 1

TRACK_STATUS_UNKNOWN    = 0
TRACK_STATUS_PREPARING  = 1
TRACK_STATUS_TRANSIT    = 2
TRACK_STATUS_UNLOADING  = 3
TRACK_STATUS_ARRIVED    = 4
TRACK_STATUS_CANCELED   = 5
TRACK_STATUS_RETURNING  = 6

inv_tracking_status = {
                        "UNKNOWN"    : TRACK_STATUS_UNKNOWN,
                        "IN_PROCESS" : TRACK_STATUS_PREPARING,
                        "SENT"       : TRACK_STATUS_TRANSIT,
                        "UNLOADING"  : TRACK_STATUS_UNLOADING,
                        "RECEIVED"   : TRACK_STATUS_ARRIVED,
                        "CANCEL"     : TRACK_STATUS_CANCELED,
                        "RETURNING"  : TRACK_STATUS_RETURNING,
                      }

tracking_status = {TRACK_STATUS_UNKNOWN   : T("Unknown"),
                   TRACK_STATUS_PREPARING : T("In Process"),
                   TRACK_STATUS_TRANSIT   : T("In transit"),
                   TRACK_STATUS_UNLOADING : T("Unloading"),
                   TRACK_STATUS_ARRIVED   : T("Arrived"),
                   TRACK_STATUS_CANCELED  : T("Canceled"),
                   TRACK_STATUS_RETURNING : T("Returning"),
                   }

#itn_label = T("Item Source Tracking Number")
# Overwrite the label until we have a better way to do this
itn_label = T("CTN")

settings = current.deployment_settings
inv_item_status_opts = settings.get_inv_item_status()
send_type_opts = settings.get_inv_shipment_types()
send_type_opts.update(inv_item_status_opts)
send_type_opts.update(settings.get_inv_send_types())
recv_type_opts = settings.get_inv_shipment_types()
recv_type_opts.update(settings.get_inv_recv_types())
# =============================================================================
class S3InventoryModel(S3Model):
    """
        Inventory Management

        A module to record inventories of items at a location (site)
    """

    names = ["inv_inv_item",
             "inv_remove",
             "inv_item_id",
             "inv_item_represent",
             "inv_prep",
            ]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        org_id = self.org_organisation_id

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        s3_date_format = current.deployment_settings.get_L10n_date_format()
        s3_date_represent = lambda dt: S3DateTime.date_represent(dt, utc=True)

        inv_source_type = { 0: None,
                            1: T("Donated"),
                            2: T("Procured"),
                          }
        # =====================================================================
        # Inventory Item
        #
        # ondelete references have been set to RESTRICT because the inv. items
        # should never be automatically deleted

        tablename = "inv_inv_item"
        table = self.define_table(tablename,
                                  # This is a component, so needs to be a super_link
                                  # - can't override field name, ondelete or requires
                                  self.super_link("site_id", "org_site",
                                                   label = T("Warehouse"),
                                                   default = auth.user.site_id if auth.is_logged_in() else None,
                                                   readable = True,
                                                   writable = True,
                                                   empty = False,
                                                   ondelete = "RESTRICT",
                                                   # Comment these to use a Dropdown & not an Autocomplete
                                                   #widget = S3SiteAutocompleteWidget(),
                                                   #comment = DIV(_class="tooltip",
                                                   #              _title="%s|%s" % (T("Warehouse"),
                                                   #                                T("Enter some characters to bring up a list of possible matches"))),
                                                   represent=self.org_site_represent),
                                  self.supply_item_entity_id,
                                  self.supply_item_id(ondelete = "RESTRICT"),
                                  self.supply_item_pack_id(ondelete = "RESTRICT"),
                                  Field("quantity", "double", notnull=True,
                                        label = T("Quantity"),
                                        represent=lambda v, row=None: \
                                            IS_FLOAT_AMOUNT.represent(v, precision=2),
                                        requires = IS_FLOAT_IN_RANGE(0, None),
                                        writable = False),
                                  Field("bin", "string", length=16,
                                        label = T("Bin"),
                                        represent = lambda bin: bin or NONE
                                        ),
                                  # @ToDo: Allow items to be marked as 'still on the shelf but allocated to an outgoing shipment'
                                  Field("status", "integer",
                                        label = T("Status"),
                                        requires = IS_NULL_OR(IS_IN_SET(inv_item_status_opts)),
                                        represent = lambda opt: \
                                            inv_item_status_opts.get(opt, UNKNOWN_OPT),
                                        default = 0,),
                                  Field("expiry_date", "date",
                                        label = T("Expiry Date"),
                                        requires = IS_NULL_OR(IS_DATE(format=s3_date_format)),
                                        represent = s3_date_represent,
                                        widget = S3DateWidget()
                                        ),
                                  Field("pack_value", "double",
                                        label = T("Value per Pack"),
                                        represent=lambda v, row=None: \
                                            IS_FLOAT_AMOUNT.represent(v, precision=2)),
                                  # @ToDo: Move this into a Currency Widget for the pack_value field
                                  s3_currency(),
                                  #Field("pack_quantity",
                                  #      "double",
                                  #      compute = record_pack_quantity), # defined in 06_supply
                                  Field("item_source_no", "string", length=16,
                                        label = itn_label,
                                        ),
                                  org_id(name = "owner_org_id",
                                         label = T("Organization/Department"),
                                         ondelete = "SET NULL"), # which org owns this item
                                  org_id(name = "supply_org_id",
                                         label = T("Supplier/Donor"),
                                         ondelete = "SET NULL"), # original donating org
                                  Field("source_type", "integer",
                                        label = T("Type"),
                                        requires = IS_NULL_OR(IS_IN_SET(inv_source_type)),
                                        represent = lambda opt: \
                                            inv_source_type.get(opt, UNKNOWN_OPT),
                                        default = 0,
                                        writable = False,
                                        ),
                                  s3_comments(),
                                  *s3_meta_fields())

        table.virtualfields.append(self.supply_item_pack_virtualfields(tablename=tablename))
        table.virtualfields.append(InvItemVirtualFields())

        # CRUD strings
        INV_ITEM = T("Warehouse Stock")
        ADD_INV_ITEM = T("Add Stock to Warehouse")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_INV_ITEM,
            title_display = T("Warehouse Stock Details"),
            title_list = T("Stock in Warehouse"),
            title_update = T("Edit Warehouse Stock"),
            title_search = T("Search Warehouse Stock"),
            title_report = T("Warehouse Stock Report"),
            title_upload = T("Import Warehouse Stock"),
            subtitle_create = ADD_INV_ITEM,
            label_list_button = T("List Stock in Warehouse"),
            label_create_button = ADD_INV_ITEM,
            label_delete_button = T("Remove Stock from Warehouse"),
            msg_record_created = T("Stock added to Warehouse"),
            msg_record_modified = T("Warehouse Stock updated"),
            msg_record_deleted = T("Stock removed from Warehouse"),
            msg_list_empty = T("No Stock currently registered in this Warehouse"))

        # Reusable Field
        inv_item_id = S3ReusableField("inv_item_id", table,
                                      requires = IS_ONE_OF(db, "inv_inv_item.id",
                                                           self.inv_item_represent,
                                                           orderby="inv_inv_item.id",
                                                           sort=True),
                                      represent = self.inv_item_represent,
                                      label = INV_ITEM,
                                      comment = DIV( _class="tooltip",
                                                     _title="%s|%s" % (INV_ITEM,
                                                                       T("Select Stock from this Warehouse"))),
                                      ondelete = "CASCADE",
                                      script = SCRIPT('''
$(document).ready(function(){
 S3FilterFieldChange({
  'FilterField':'inv_item_id',
  'Field':'item_pack_id',
  'FieldResource':'item_pack',
  'FieldPrefix':'supply',
  'url':S3.Ap.concat('/inv/inv_item_packs/'),
  'msgNoRecords':S3.i18n.no_packs,
  'fncPrep':fncPrepItem,
  'fncRepresent':fncRepresentItem
 })
})'''),
                                )

        report_options = Storage(
            search=[
                S3SearchSimpleWidget(
                    name="inv_item_search_text",
                    label=T("Search"),
                    comment=T("Search for an item by text."),
                    field=[
                        "item_id$name",
                        #"item_id$category_id$name",
                        #"site_id$name"
                    ]
                ),
                S3SearchOptionsWidget(
                    name="inv_item_search_site",
                    label=T("Facility"),
                    field="site_id",
                    represent="%(name)s",
                    comment=T("If none are selected, then all are searched."),
                    cols = 2
                ),
                S3SearchOptionsWidget(
                    name="inv_item_search_status",
                    label=T("Status"),
                    field="status",
                    represent="%(name)s",
                    comment=T("If none are selected, then all are searched."),
                    cols = 2
                ),
                S3SearchOptionsWidget(
                    name="owner_org_seach",
                    label=T("Owning Organisation"),
                    field="owner_org_id",
                    represent="%(name)s",
                    comment=T("If none are selected, then all are searched."),
                    cols = 2
                ),
                S3SearchOptionsWidget(
                    name="supply_org_seach",
                    label=T("Donating Organisation"),
                    field="supply_org_id",
                    represent="%(name)s",
                    comment=T("If none are selected, then all are searched."),
                    cols = 2
                ),
                # NotImplemented yet
                # S3SearchOptionsWidget(
                    # name="inv_item_search_category",
                    # label=T("Category"),
                    # field="item_category",
                    ##represent="%(name)s",
                    # comment=T("If none are selected, then all are searched."),
                    # cols = 2
                # ),
                S3SearchMinMaxWidget(
                    name="inv_item_search_expiry_date",
                    method="range",
                    label=T("Expiry Date"),
                    field="expiry_date"
                )
            ],
            #rows=["item_id", "currency"],
            rows=["item_id", (T("Category"), "item_category"),],
            #cols=["site_id", "currency"],
            cols=["site_id", "owner_org_id", "supply_org_id"],
            facts=["quantity", (T("Total Value"), "total_value"),],
            methods=["sum"],
            groupby=self.inv_inv_item.site_id,
            hide_comments=True,
        )

        # Item Search Method (Advanced Search only)
        inv_item_search = S3Search(advanced=report_options.get("search"))

        self.configure(tablename,
                        # Lock the record so that it can't be meddled with
                        create=False,
                        listadd=False,
                        editable=False,
                        deletable=False,
                        super_entity = "supply_item_entity",
                        list_fields = ["id",
                                       "site_id",
                                       "item_id",
                                       (T("Item Code"), "item_code"),
                                       (T("Category"), "item_category"),
                                       "quantity",
                                       "pack_value",
                                       (T("Total Value"), "total_value"),
                                       "currency",
                                       "bin",
                                       "owner_org_id",
                                       "supply_org_id",
                                       "status",
                                       ],
                        onvalidation = self.inv_inv_item_onvalidate,
                        search_method = inv_item_search,
                        report_options = report_options,
                        deduplicate = self.inv_item_duplicate,
                        )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                    inv_item_id = inv_item_id,
                    inv_item_represent = self.inv_item_represent,
                    inv_remove = self.inv_remove,
                    inv_prep = self.inv_prep,
                )
    # -------------------------------------------------------------------------
    @staticmethod
    def inv_inv_item_onvalidate(form):
        """
            When a inv item record is being created with a source number
            then the source number needs to be unique within the organisation.
        """

        # If there is a tracking number check that it is unique within the org
        item_source_no = form.vars.item_source_no
        if item_source_no:
            if form.record.item_source_no and form.record.item_source_no == item_source_no:
                # The tracking number hasn't changed so no validation needed
                pass
            else:
                db = current.db
                s3db = current.s3db
                itable = db.inv_inv_item
                stable = s3db.org_site
                query = (itable.track_org_id == form.vars.track_org_id) & \
                        (itable.item_source_no == item_source_no)
                record = db(query).select(record.track_org_id,
                                          limitby=(0, 1)).first()
                if record:
                    org_repr = current.response.s3.org_organisation_represent
                    form.errors.item_source_no = T("The Tracking Number %s is already used by %s.") % \
                        (item_source_no,
                         org_repr(record.track_org_id))

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_remove(inv_rec,
                   required_total,
                   required_pack_value = 1,
                   current_track_total = 0,
                   update = True,
                  ):
        """
            Check that the required_total can be removed from the inv_record
            if their is insufficient stock then set up the total to being
            what is in stock otherwise set it to be the required total.
            If the update flag is true then remove it from stock.

            The current total is what has already been removed for this
            transaction.
        """

        db = current.db
        inv_item_table = db.inv_inv_item
        siptable = db.supply_item_pack
        inv_p_qnty = siptable[inv_rec.item_pack_id].quantity
        inv_qnty = inv_rec.quantity * inv_p_qnty
        cur_qnty = current_track_total * inv_p_qnty
        req_qnty = required_total * required_pack_value

        # It already matches so no change required
        if cur_qnty == req_qnty:
            return required_total

        if inv_qnty + cur_qnty > req_qnty:
            send_item_quantity = req_qnty
            new_qnty = (inv_qnty + cur_qnty - req_qnty) / inv_p_qnty
        else:
            send_item_quantity = inv_qnty + cur_qnty
            new_qnty = 0
        send_item_quantity = send_item_quantity / inv_p_qnty

        if update:
            # Update the levels in stock
            db(inv_item_table.id == inv_rec.id).update(quantity = new_qnty)

        return send_item_quantity

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_prep(r):
        """
            Used in site REST controllers to Filter out items which are
            already in this inventory
        """

        if r.component:
            if r.component.name == "inv_item":
                db = current.db
                table = db.inv_inv_item
                # Filter out items which are already in this inventory
                query = (table.site_id == r.record.site_id) & \
                        (table.deleted == False)
                inv_item_rows = db(query).select(table.item_id)
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
                    filter = (current.s3db.inv_send.status == SHIP_STATUS_SENT)
                    #r.resource.add_component_filter("send", filter)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_item_represent(id, show_link=True):
        """
        """

        db = current.db
        itable = db.inv_inv_item
        stable = db.supply_item
        query = (itable.id == id) & \
                (itable.item_id == stable.id)
        record = db(query).select(stable.name,
                                  stable.um,
                                  itable.item_source_no,
                                  itable.bin,
                                  itable.expiry_date,
                                  itable.owner_org_id,
                                  limitby = (0, 1)).first()
        if record:
            s3_string_represent = lambda str: str if str else ""
            s3_date_represent = lambda dt: \
                S3DateTime.date_represent(dt, utc=True)
            ctn = s3_string_represent(record.inv_inv_item.item_source_no)
            org = current.s3db.org_organisation_represent(record.inv_inv_item.owner_org_id)
            if record.inv_inv_item.expiry_date:
                exp_date = "expires:%s" % \
                    s3_date_represent(record.inv_inv_item.expiry_date)
            else:
                exp_date = ""
            bin = s3_string_represent(record.inv_inv_item.bin)
            NONE = current.messages.NONE
            rep_strings = [str for str in [record.supply_item.name,
                                           exp_date,
                                           ctn,
                                           org,
                                           bin
                                           ] if str and str != NONE]
            return " - ".join(rep_strings)
        else:
            return None

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_item_duplicate(job):
        """
          Rules for finding a duplicate:
           - Look for a record with the same site,
                                             bin,
                                             supply item and,
                                             pack item

            If a item is added as part of an inv_track_item import then the
            quantity will be set to zero. This will overwrite any existing
            total, if we have a duplicate. If the total was None then
            validation would fail (it's a not null field). So if a duplicate
            is found then the quantity needs to be removed.
        """

        if job.tablename == "inv_inv_item":
            table = job.table
            data = job.data
            site_id = "site_id" in data and data.site_id
            item_id = "item_id" in data and data.item_id
            pack_id = "item_pack_id" in data and data.item_pack_id
            owner_org_id = "owner_org_id" in data and data.owner_org_id
            supply_org_id = "supply_org_id" in data and data.supply_org_id
            pack_value = "pack_value" in data and data.pack_value
            currency = "currency" in data and data.currency
            bin = "bin" in data and data.bin
            query = (table.site_id == site_id) & \
                    (table.item_id == item_id) & \
                    (table.item_pack_id == pack_id) & \
                    (table.owner_org_id == owner_org_id) & \
                    (table.supply_org_id == supply_org_id) & \
                    (table.pack_value == pack_value) & \
                    (table.currency == currency) & \
                    (table.bin == bin)
            id = duplicator(job, query)
            if id:
                if "quantity" in data and data.quantity == 0:
                    job.data.quantity = table[id].quantity

# =============================================================================
class S3TrackingModel(S3Model):
    """
        A module to manage the shipment of inventory items
        - Sent Items
        - Received Items
        - And audit trail of the shipment process
    """

    names = ["inv_send",
             "inv_send_represent",
             "inv_send_ref_represent",
             "inv_recv",
             "inv_recv_represent",
             "inv_recv_ref_represent",
             "inv_kit",
             "inv_track_item",
             "inv_track_item_onaccept",
             "inv_get_shipping_code",
             ]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        settings = current.deployment_settings

        person_id = self.pr_person_id
        org_id = self.org_organisation_id
        item_id = self.supply_item_id
        inv_item_id = self.inv_item_id
        item_pack_id = self.supply_item_pack_id
        req_item_id = self.req_item_id
        req_ref = self.req_req_ref
        adj_item_id = self.inv_adj_item_id

        org_site_represent = self.org_site_represent

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method

        s3_date_format = settings.get_L10n_date_format()
        s3_date_represent = lambda dt: S3DateTime.date_represent(dt, utc=True)
        s3_string_represent = lambda str: str if str else NONE

        send_ref = S3ReusableField("send_ref",
                                   label = T(settings.get_inv_send_ref_field_name()),
                                   writable = False,
                                   represent = self.inv_send_ref_represent,
                                   )
        recv_ref = S3ReusableField("recv_ref",
                                   label = T("%(GRN)s Number") % dict(GRN=settings.get_inv_recv_shortname()),
                                   writable = False,
                                   represent = self.inv_recv_ref_represent,
                                   )
        purchase_ref = S3ReusableField("purchase_ref",
                                       label = T("%(PO)s Number") % dict(PO=settings.get_proc_shortname()),
                                       represent = s3_string_represent,
                                       )

        # ---------------------------------------------------------------------
        # Send (Outgoing / Dispatch / etc)
        #
        tablename = "inv_send"
        table = define_table(tablename,
                             send_ref(),
                             req_ref(),
                             person_id(name = "sender_id",
                                       label = T("Sent By"),
                                       default = auth.s3_logged_in_person(),
                                       ondelete = "SET NULL",
                                       comment = self.pr_person_comment(child="sender_id")),
                             # This is a component, so needs to be a super_link
                             # - can't override field name, ondelete or requires
                             self.super_link("site_id", "org_site",
                                              label = T("From Facility"),
                                              default = auth.user.site_id if auth.is_logged_in() else None,
                                              readable = True,
                                              writable = True,
                                              represent = org_site_represent,
                                              #widget = S3SiteAutocompleteWidget(),
                                              ),
                             Field("date", "date",
                                   label = T("Date Sent"),
                                   writable = False,
                                   requires = IS_NULL_OR(IS_DATE(format=s3_date_format)),
                                   represent = s3_date_represent,
                                   widget = S3DateWidget()
                                   ),
                             person_id(name = "recipient_id",
                                       label = T("To Person"),
                                       ondelete = "SET NULL",
                                       comment = self.pr_person_comment(child="recipient_id")),
                             Field("delivery_date", "date",
                                   label = T("Est. Delivery Date"),
                                   requires = IS_NULL_OR(IS_DATE(format=s3_date_format)),
                                   represent = s3_date_represent,
                                   widget = S3DateWidget()
                                   ),
                             # This is a reference, not a super-link, so we can override
                             Field("to_site_id", self.org_site,
                                   label = T("To Facility"),
                                   requires = IS_ONE_OF(db, "org_site.site_id",
                                                        lambda id: \
                                                            org_site_represent(id, show_link = False),
                                                        sort=True,
                                                        ),
                                   ondelete = "SET NULL",
                                   represent =  org_site_represent
                                  ),
                             Field("status", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(shipment_status)),
                                   represent = lambda opt: shipment_status.get(opt, UNKNOWN_OPT),
                                   default = SHIP_STATUS_IN_PROCESS,
                                   label = T("Status"),
                                   writable = False,
                                   ),
                             Field("type", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(send_type_opts)),
                                   represent = lambda opt: send_type_opts.get(opt, UNKNOWN_OPT),
                                   label = T("Shipment Type"),
                                   default = 0,
                                   ),
                             Field("transport_type",
                                   label = T("Type of Transport"),
                                   represent = s3_string_represent,
                                   ),
                             Field("vehicle_plate_no",
                                   label = T("Vehicle Plate Number"),
                                   represent = s3_string_represent,
                                   ),
                             Field("driver_name",
                                   label = T("Name of Driver"),
                                   represent = s3_string_represent,
                                   ),
                             Field("time_in", "time",
                                   label = T("Time In"),
                                   represent = s3_string_represent,
                                   ),
                             Field("time_out", "time",
                                   label = T("Time Out"),
                                   represent = s3_string_represent,
                                   ),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        ADD_SEND = T("Send New Shipment")
        crud_strings[tablename] = Storage(
            title_create = ADD_SEND,
            title_display = T("Sent Shipment Details"),
            title_list = T("Sent Shipments"),
            title_update = T("Shipment to Send"),
            title_search = T("Search Sent Shipments"),
            subtitle_create = ADD_SEND,
            label_list_button = T("List Sent Shipments"),
            label_create_button = ADD_SEND,
            label_delete_button = T("Delete Sent Shipment"),
            msg_record_created = T("Shipment Created"),
            msg_record_modified = T("Sent Shipment updated"),
            msg_record_deleted = T("Sent Shipment canceled"),
            msg_list_empty = T("No Sent Shipments"))

        if not settings.get_req_use_req_number():
            table.req_ref.readable = False
            table.req_ref.writable = False

        # Reusable Field
        send_id = S3ReusableField("send_id", table, sortby="date",
                                  requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "inv_send.id",
                                                          self.inv_send_represent,
                                                          orderby="inv_send_id.date",
                                                          sort=True)),
                                  represent = self.inv_send_represent,
                                  label = T("Send Shipment"),
                                  ondelete = "RESTRICT")

        # Components
        add_component("inv_track_item",
                      inv_send="send_id")

        # Generate Consignment Note
        set_method("inv", "send",
                   method="form",
                   action=self.inv_send_form )

        # Redirect to the Items tabs after creation
        send_item_url = URL(f="send", args=["[id]",
                                            "track_item"])

        configure(tablename,
                  # it shouldn't be possible for the user to delete a send item
                  # unless *maybe* if it is pending and has no items referencing it
                  deletable=False,
                  list_fields = ["id",
                                 "send_ref",
                                 "req_ref",
                                 "sender_id",
                                 "site_id",
                                 "date",
                                 "recepient_id",
                                 "delivery_date",
                                 "to_site_id",
                                 "status",
                                 "transport_type",
                                 "vehicle_plate_no",
                                 "driver_name",
                                 "time_in",
                                 "time_out",
                                 "comments"
                                ],
                  onaccept = self.inv_send_onaccept,
                  create_next = send_item_url,
                  update_next = send_item_url,
                  orderby=~table.date,
                  sortby=[[5, "desc"], [1, "asc"]],
                  )

        # ---------------------------------------------------------------------
        # Received (In/Receive / Donation / etc)
        #
        ship_doc_status = { SHIP_DOC_PENDING  : T("Pending"),
                            SHIP_DOC_COMPLETE : T("Complete") }

        radio_widget = lambda field, value: \
                                RadioWidget().widget(field, value, cols = 2)

        tablename = "inv_recv"
        table = define_table(tablename,
                             Field("site_id", "reference org_site", notnull = True,
                                   label=T("By Facility"),
                                   ondelete = "SET NULL",
                                   default = auth.user.site_id if auth.is_logged_in() else None,
                                   readable = True,
                                   writable = True,
                                   #widget = S3SiteAutocompleteWidget(),
                                   requires = IS_ONE_OF(db, "org_site.site_id",
                                                        lambda id: \
                                                            org_site_represent(id, show_link = False),
                                                        sort=True,
                                                        ),
                                   represent=org_site_represent
                                   ),
                             Field("type", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(recv_type_opts)),
                                   represent = lambda opt: \
                                    recv_type_opts.get(opt, UNKNOWN_OPT),
                                   label = T("Type"),
                                   default = 0,
                                   ),
                             Field("eta", "date",
                                   label = T("Date Expected"),
                                   writable = False,
                                   requires = IS_NULL_OR(IS_DATE(format=s3_date_format)),
                                   represent = s3_date_represent,
                                   widget = S3DateWidget()
                                   ),
                             Field("date", "date",
                                   label = T("Date Received"),
                                   requires = IS_NULL_OR(IS_DATE(format=s3_date_format)),
                                   represent = s3_date_represent,
                                   widget = S3DateWidget(),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Date Received"),
                                                                   T("Will be filled automatically when the Shipment has been Received"))
                                                 )
                                   ),
                             Field("from_site_id", "reference org_site",
                                   label = T("From Facility"),
                                   ondelete = "SET NULL",
                                   #widget = S3SiteAutocompleteWidget(),
                                   requires = IS_ONE_OF(db, "org_site.site_id",
                                                        lambda id: \
                                                            org_site_represent(id, show_link = False),
                                                        sort=True,
                                                        ),
                                   represent = org_site_represent
                                   ),
                             send_ref(),
                             recv_ref(),
                             purchase_ref(),
                             req_ref(),
                             person_id(name = "sender_id",
                                       label = T("Sent By Person"),
                                       ondelete = "SET NULL",
                                       comment = self.pr_person_comment(child="sender_id"),
                                       ),
                             person_id(name = "recipient_id",
                                       label = T("Received By"),
                                       ondelete = "SET NULL",
                                       default = auth.s3_logged_in_person(),
                                       comment = self.pr_person_comment(child="recipient_id")),
                             Field("status", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(shipment_status)),
                                   represent = lambda opt: \
                                    shipment_status.get(opt, UNKNOWN_OPT),
                                   default = SHIP_STATUS_IN_PROCESS,
                                   label = T("Status"),
                                   writable = False,
                                   ),
                             Field("grn_status", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(ship_doc_status)),
                                   represent = lambda opt: \
                                    ship_doc_status.get(opt, UNKNOWN_OPT),
                                   default = SHIP_DOC_PENDING,
                                   widget = radio_widget,
                                   label = T("%(GRN)s Status") % \
                                    dict(GRN=settings.get_inv_recv_shortname()),
                                   comment = DIV( _class="tooltip",
                                                  _title="%s|%s" % \
                                        (T("%(GRN)s Status") % dict(GRN=settings.get_inv_recv_shortname()),
                                         T("Has the %(GRN)s (%(GRN_name)s) form been completed?") % \
                                            dict(GRN=settings.get_inv_recv_shortname(),
                                                                                                                                    GRN_name=settings.get_inv_recv_form_name()))),
                                   ),
                             Field("cert_status", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(ship_doc_status)),
                                   represent = lambda opt: \
                                    ship_doc_status.get(opt, UNKNOWN_OPT),
                                   default = SHIP_DOC_PENDING,
                                   widget = radio_widget,
                                   label = T("Certificate Status"),
                                   comment = DIV( _class="tooltip",
                                                  _title="%s|%s" % (T("Certificate Status"),
                                                                    T("Has the Certificate for receipt of the shipment been given to the sender?"))),
                                   ),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD Strings
        inv_recv_crud_strings()
        if settings.get_inv_shipment_name() == "order":
            recv_id_label = T("Order")
        else:
            recv_id_label = T("Receive Shipment")

        if not settings.get_req_use_req_number():
            table.req_ref.readable = False
            table.req_ref.writable = False

        # Reusable Field
        recv_id = S3ReusableField("recv_id", table, sortby="date",
                                  requires = IS_NULL_OR(
                                                IS_ONE_OF(db,
                                                          "inv_recv.id",
                                                          self.inv_recv_represent,
                                                          orderby="inv_recv.date",
                                                          sort=True)),
                                  represent = self.inv_recv_represent,
                                  label = recv_id_label,
                                  ondelete = "RESTRICT")

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
                        field=[
                                "sender_id$first_name",
                                "sender_id$middle_name",
                                "sender_id$last_name",
                                "comments",
                                "from_site_id$name",
                                "recipient_id$first_name",
                                "recipient_id$middle_name",
                                "recipient_id$last_name",
                                "site_id$name",
                                "recv_ref",
                                "send_ref",
                                "purchase_ref",
                              ]
                      )),
            advanced=(S3SearchSimpleWidget(
                        name="recv_search_text_advanced",
                        label=T("Search"),
                        comment=recv_search_comment,
                        field=[ "from_person",
                                "comments",
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
                        field=recv_search_date_field
                      ),
                      S3SearchOptionsWidget(
                        name="recv_search_site",
                        label=T("Facility"),
                        field="site_id",
                        represent ="%(name)s",
                        cols = 2
                      ),
                      S3SearchOptionsWidget(
                        name="recv_search_status",
                        label=T("Status"),
                        field="status",
                        cols = 2
                      ),
                      #S3SearchOptionsWidget(
                      #  name="recv_search_grn",
                      #  label=T("GRN Status"),
                      #  field="grn_status",
                      #  cols = 2
                      #),
                      #S3SearchOptionsWidget(
                      #  name="recv_search_cert",
                      #  label=T("Certificate Status"),
                      #  field="grn_status",
                      #  cols = 2
                      #),
            ))

        # Redirect to the Items tabs after creation
        recv_item_url = URL(f="recv", args=["[id]",
                                            "track_item"])

        configure(tablename,
                  # it shouldn't be possible for the user to delete a send item
                  deletable=False,
                  list_fields = ["id",
                                 "recv_ref",
                                 "send_ref",
                                 "purchase_ref",
                                 "recipient_id",
                                 "site_id",
                                 "date",
                                 "type",
                                 "status",
                                 "req_ref",
                                 "sender_id",
                                 "comments"
                                 ],
                  onaccept = self.inv_recv_onaccept,
                  search_method = recv_search,
                  create_next = recv_item_url,
                  update_next = recv_item_url,
                  orderby=~table.date,
                  sortby=[[6, "desc"], [1, "asc"]])

        # Components
        add_component("inv_track_item",
                      inv_recv="recv_id")

        # Print Forms
        set_method("inv", "recv",
                   method="form",
                   action=self.inv_recv_form)

        set_method("inv", "recv",
                   method="cert",
                   action=self.inv_recv_donation_cert )

        # ---------------------------------------------------------------------
        # Kits
        # - actual Kits in stock
        #
        tablename = "inv_kit"
        table = define_table(tablename,
                             Field("site_id", "reference org_site",
                                    label = T("By Facility"),
                                    default = auth.user.site_id if auth.is_logged_in() else None,
                                    readable = True,
                                    writable = True,
                                    widget = S3SiteAutocompleteWidget(),
                                    represent = org_site_represent),
                             item_id(label = T("Kit"),
                                     requires = IS_ONE_OF(db, "supply_item.id",
                                                          self.supply_item_represent,
                                                          filterby="kit",
                                                          filter_opts=(True,),
                                                          sort=True),
                                     widget = S3AutocompleteWidget("supply", "item",
                                                                   filter="item.kit=1"),
                                     # Needs better workflow as no way to add the Kit Items
                                     comment = None,
                                     #comment = S3AddResourceLink(
                                     #   c="supply",
                                     #   f="item",
                                     #   label=T("Add New Kit"),
                                     #   title=T("Kit"),
                                     #   tooltip=T("Type the name of an existing catalog kit OR Click 'Add New Kit' to add a kit which is not in the catalog.")),
                                     ),
                             Field("quantity", "double",
                                   label = T("Quantity"),
                                   represent = lambda v, row=None: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2)
                                   ),
                             Field("date", "date",
                                   label = T("Date"),
                                   requires = IS_NULL_OR(IS_DATE(format=s3_date_format)),
                                   represent = s3_date_represent,
                                   widget = S3DateWidget(),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % \
                                        (T("Date Repacked"),
                                         T("Will be filled automatically when the Item has been Repacked"))
                                                 )
                                   ),
                             req_ref(writable = True),
                             person_id(name = "repacked_id",
                                       label = T("Repacked By"),
                                       ondelete = "SET NULL",
                                       default = auth.s3_logged_in_person(),
                                       #comment = self.pr_person_comment(child="repacked_id")),
                                      ),
                             s3_comments(),
                             *s3_meta_fields()
                            )

        # CRUD strings
        ADD_KIT = T("Add New Kit")
        crud_strings[tablename] = Storage(
            title_create = ADD_KIT,
            title_display = T("Kit Details"),
            title_list = T("Kits"),
            title_update = T("Kit"),
            title_search = T("Search Kits"),
            subtitle_create = ADD_KIT,
            label_list_button = T("List Kits"),
            label_create_button = ADD_KIT,
            label_delete_button = T("Delete Kit"),
            msg_record_created = T("Kit Created"),
            msg_record_modified = T("Kit updated"),
            msg_record_deleted = T("Kit canceled"),
            msg_list_empty = T("No Kits"))

        # Resource configuration
        configure(tablename,
                  list_fields = ["site_id",
                                 "req_ref",
                                 "quantity",
                                 "date",
                                 "repacked_id"],
                  onvalidation = self.inv_kit_onvalidate,
                  onaccept = self.inv_kit_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Tracking Items
        #

        tablename = "inv_track_item"
        table = define_table(tablename,
                             org_id(name = "track_org_id",
                                    label = T("Shipping Organization"),
                                    ondelete = "SET NULL",
                                    readable = False,
                                    writable = False),
                             inv_item_id(name="send_inv_item_id",
                                         ondelete = "RESTRICT",
                                         script = SCRIPT('''
$(document).ready(function(){
 S3FilterFieldChange({
  'FilterField':'send_inv_item_id',
  'Field':'item_pack_id',
  'FieldResource':'item_pack',
  'FieldPrefix':'supply',
  'url':S3.Ap.concat('/inv/inv_item_packs/'),
  'msgNoRecords':S3.i18n.no_packs,
  'fncPrep':fncPrepItem,
  'fncRepresent':fncRepresentItem
 })
})''')),
                            item_id(ondelete = "RESTRICT"),
                            item_pack_id(ondelete = "SET NULL"),
                            Field("quantity", "double", notnull=True,
                                   label = T("Quantity Sent"),
                                   requires = IS_NOT_EMPTY()),
                             Field("recv_quantity", "double",
                                   label = T("Quantity Received"),
                                   represent = self.qnty_recv_repr,
                                   readable = False,
                                   writable = False),
                             Field("return_quantity", "double",
                                   label = T("Quantity Returned"),
                                   represent = self.qnty_recv_repr,
                                   readable = False,
                                   writable = False),
                             Field("pack_value", "double",
                                   label = T("Value per Pack")),
                             s3_currency(),
                             Field("expiry_date", "date",
                                   label = T("Expiry Date"),
                                   requires = IS_NULL_OR(IS_DATE(format=s3_date_format)),
                                   represent = s3_date_represent,
                                   widget = S3DateWidget()
                                   ),
                             # The bin at origin
                             Field("bin", length=16,
                                   label = T("Bin"),
                                   represent = s3_string_represent),
                             inv_item_id(name="recv_inv_item_id",
                                         label = T("Receiving Inventory"),
                                         required = False,
                                         readable = False,
                                         writable = False,
                                         ondelete = "RESTRICT"),
                             # The bin at destination
                             Field("recv_bin", length=16,
                                   label = T("Add to Bin"),
                                   readable = False,
                                   writable = False,
                                   represent = s3_string_represent,
                                   widget = S3InvBinWidget("inv_track_item"),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % \
                                        (T("Bin"),
                                         T("The Bin in which the Item is being stored (optional)."))),
                                   ),
                             Field("item_source_no", "string", length=16,
                                   label = itn_label,
                                   represent = s3_string_represent),
                             # original donating org
                             org_id(name = "supply_org_id",
                                    label = T("Supplier/Donor"),
                                    ondelete = "SET NULL"),
                             # which org owns this item
                             org_id(name = "owner_org_id",
                                    label = T("Organization/Department"),
                                    ondelete = "SET NULL"),
                             Field("inv_item_status", "integer",
                                   label = T("Item Status"),
                                   requires = IS_NULL_OR(IS_IN_SET(inv_item_status_opts)),
                                   represent = lambda opt: \
                                        inv_item_status_opts.get(opt, UNKNOWN_OPT),
                                   default = 0,),
                             Field("status", "integer",
                                   label = T("Item Tracking Status"),
                                   required = True,
                                   requires = IS_IN_SET(tracking_status),
                                   default = 1,
                                   represent = lambda opt: tracking_status[opt],
                                   writable = False),
                             adj_item_id(ondelete = "RESTRICT"), # any adjustment record
                             # send record
                             send_id(),
                             # receive record
                             recv_id(),
                             req_item_id(readable=False,
                                         writable=False),
                             s3_comments(),
                             *s3_meta_fields()
                             )

        # pack_quantity virtual field
        table.virtualfields.append(self.supply_item_pack_virtualfields(tablename=tablename))
        table.virtualfields.append(InvTrackItemVirtualFields())

        # CRUD strings
        ADD_TRACK_ITEM = T("Add Item to Shipment")
        crud_strings[tablename] = Storage(
            title_create = ADD_TRACK_ITEM,
            title_display = T("Shipment Item Details"),
            title_list = T("Shipment Items"),
            title_update = T("Edit Shipment Item"),
            title_search = T("Search Shipment Items"),
            subtitle_create = T("Add New Shipment Item"),
            label_list_button = T("List Shipment Items"),
            label_create_button = ADD_TRACK_ITEM,
            label_delete_button = T("Delete Shipment Item"),
            msg_record_created = T("Item Added to Shipment"),
            msg_record_modified = T("Shipment Item updated"),
            msg_record_deleted = T("Shipment Item deleted"),
            msg_list_empty = T("No Shipment Items"))

        track_search = S3Search(
            simple=(S3SearchSimpleWidget(
                        name="track_search_text_simple",
                        label=T("Search"),
                        #comment=recv_search_comment,
                        field=["item_id$name",
                               "send_id$site_id$name",
                               "recv_id$site_id$name",
                              ]
                      )),
            advanced=(S3SearchSimpleWidget(
                        name="track_search_text_advanced",
                        label=T("Search"),
                        #comment=recv_search_comment,
                        field=["item_id$name",
                               "send_id$site_id$name",
                               "recv_id$site_id$name",
                              ]
                      ),
                      S3SearchMinMaxWidget(
                        name="send_search_date",
                        method="range",
                        label=T("Sent date"),
                        field="send_id$date"
                      ),
                      S3SearchMinMaxWidget(
                        name="recv_search_date",
                        method="range",
                        label=T("Received date"),
                        field="recv_id$date"
                      ),
            ))

        # Resource configuration
        configure(tablename,
                  list_fields = ["id",
                                 "status",
                                 "item_id",
                                 (T("Weight (kg)"), "item_id$weight"),
                                 (T("Volume (m3)"), "item_id$volume"),
                                 "item_pack_id",
                                 "send_id",
                                 "recv_id",
                                 "quantity",
                                 "currency",
                                 "pack_value",
                                 "bin",
                                 "return_quantity",
                                 "recv_quantity",
                                 "recv_bin",
                                 "owner_org_id",
                                 "supply_org_id",
                                ],
                  search_method = track_search,
                  onaccept = self.inv_track_item_onaccept,
                  onvalidation = self.inv_track_item_onvalidate,
                  )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(inv_track_item_deleting = self.inv_track_item_deleting,
                       inv_get_shipping_code = self.inv_get_shipping_code,
                       inv_track_item_onaccept = self.inv_track_item_onaccept,
                      )

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_send_represent(id, show_link=True):
        """
        """

        if id:
            db = current.db
            table = db.inv_send
            row = db(table.id == id).select(table.date,
                                            table.site_id,
                                            limitby=(0, 1)).first()
            if show_link:
                return SPAN(table.site_id.represent(row.site_id),
                            " - ",
                            table.date.represent(row.date)
                            )
            else:
                return "%s - %s" % (table.site_id.represent(row.site_id,
                                                            show_link = False),
                                    table.date.represent(row.date),
                                    )
        else:
            return current.messages.NONE

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_send_onaccept(form):
        """
           When a inv send record is created then create the send_ref.
        """

        db = current.db

        vars = form.vars
        id = vars.id

        type = vars.type
        if type:
            # Add all inv_items with status matching the send shipment type
            # eg. Items for Dump, Sale, Reject, Surplus
            site_id = vars.site_id
            itable = db.inv_inv_item
            tracktable = db.inv_track_item
            query = (itable.site_id == site_id) & \
                    (itable.status == int(type))
            rows = db(query).select()

            for row in rows:
                if row.quantity != 0:
                    #Insert inv_item to inv_track_item
                    inv_track_id = tracktable.insert(send_id = id,
                                                     send_inv_item_id = row.id,
                                                     item_id = row.item_id,
                                                     quantity = row.quantity,
                                                     currency = row.currency,
                                                     pack_value = row.pack_value,
                                                     expiry_date = row.expiry_date,
                                                     owner_org_id = row.owner_org_id,
                                                     supply_org_id = row.supply_org_id,
                                                     item_source_no = row.item_source_no,
                                                     item_pack_id = row.item_pack_id,
                                                     inv_item_status = row.status,
                                                     #status = TRACK_STATUS_PREPARING,
                                                     )
                    # Construct form.vars for inv_track_item_onaccept
                    vars = Storage()
                    vars.id = inv_track_id
                    vars.quantity = row.quantity
                    vars.item_pack_id = row.item_pack_id
                    vars.send_inv_item_id = row.id
                    # Call inv_track_item_onaccept to remove inv_item from stock
                    current.s3db.inv_track_item_onaccept(Storage(vars=vars))

        stable = db.inv_send
        # If the send_ref is None then set it up
        record = stable[id]
        if not record.send_ref:
            code = S3TrackingModel.inv_get_shipping_code(
                    current.deployment_settings.get_inv_send_shortname(),
                    record.site_id,
                    stable.send_ref,
                  )
            db(stable.id == id).update(send_ref=code)

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_send_form (r, **attr):
        """
            Generate a PDF of a Waybill
        """

        db = current.db
        table = db.inv_send
        tracktable = db.inv_track_item
        table.date.readable = True

        record = table[r.id]
        send_ref = record.send_ref
        # hide the inv_item field
        tracktable.send_inv_item_id.readable = False
        tracktable.recv_inv_item_id.readable = False

        list_fields = [(T("Item Code"), "item_code"),
                       "item_id",
                       (T("Weight (kg)"), "item_id$weight"),
                       (T("Volume (m3)"), "item_id$volume"),
                       "item_source_no",
                       "item_pack_id",
                       "quantity",
                       "currency",
                       "pack_value",
                       "bin",
                       ]
        exporter = r.resource.exporter.pdf
        return exporter(r,
                        method = "list",
                        pdf_componentname = "inv_track_item",
                        pdf_title = current.deployment_settings.get_inv_send_form_name(),
                        pdf_filename = send_ref,
                        list_fields = list_fields,
                        pdf_hide_comments = True,
                        pdf_header_padding = 12,
                        pdf_footer = inv_send_pdf_footer,
                        pdf_paper_alignment = "Landscape",
                        pdf_table_autogrow = "B",
                        **attr
                       )

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_recv_represent(id, show_link=True):
        """
            @ToDo: 'From Organisation' is great for Donations
            (& Procurement if we make Suppliers Organisations), but isn't useful
            for shipments between facilities within a single Org where
            'From Facility' could be more appropriate
        """

        if id:
            db = current.db
            table = db.inv_recv
            row = db(table.id == id).select(table.date,
                                            table.site_id,
                                            limitby=(0, 1)).first()
            if show_link:
                return SPAN(table.site_id.represent(row.site_id),
                            " - ",
                            table.date.represent(row.date)
                            )
            else:
                return "%s - %s" % (table.site_id.represent(row.site_id,
                                                            show_link = False),
                                    table.date.represent(row.date),
                                    )
        else:
            return current.messages.NONE

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_recv_onaccept(form):
        """
           When a inv recv record is created then create the recv_ref.
        """
        db = current.db
        rtable = db.inv_recv
        # If the recv_ref is None then set it up
        id = form.vars.id
        record = rtable[id]
        if not record.recv_ref:
            # AR Number
            code = S3TrackingModel.inv_get_shipping_code(
                    current.deployment_settings.get_inv_recv_shortname(),
                    record.site_id,
                    rtable.recv_ref,
                )
            db(rtable.id == id).update(recv_ref = code)

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_recv_form (r, **attr):
        """
            Generate a PDF of a GRN (Goods Received Note)
        """

        T = current.T
        db = current.db

        table = db.inv_recv
        track_table = db.inv_track_item
        table.date.readable = True
        table.site_id.readable = True
        track_table.recv_quantity.readable = True
        table.site_id.label = T("By Warehouse")
        table.site_id.represent = current.s3db.org_site_represent

        record = table[r.id]
        recv_ref = record.recv_ref
        list_fields = ["item_id",
                       (T("Weight (kg)"), "item_id$weight"),
                       (T("Volume (m3)"), "item_id$volume"),
                       "item_source_no",
                       "item_pack_id",
                       "quantity",
                       "recv_quantity",
                       "currency",
                       "pack_value",
                       "bin"
                       ]
        exporter = r.resource.exporter.pdf
        return exporter(r,
                        method = "list",
                        pdf_title = T(current.deployment_settings.get_inv_recv_form_name()),
                        pdf_filename = recv_ref,
                        list_fields = list_fields,
                        pdf_hide_comments = True,
                        pdf_componentname = "inv_track_item",
                        pdf_header_padding = 12,
                        pdf_footer = inv_recv_pdf_footer,
                        pdf_table_autogrow = "B",
                        pdf_paper_alignment = "Landscape",
                        **attr
                       )

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_recv_donation_cert (r, **attr):
        """
            Generate a PDF of a Donation certificate
        """

        db = current.db
        table = db.inv_recv
        table.date.readable = True
        table.type.readable = False
        field = table.site_id
        field.readable = True
        field.label = current.T("By Warehouse")
        field.represent = current.s3db.org_site_represent

        record = table[r.id]
        site_id = record.site_id
        site = field.represent(site_id, False)

        exporter = r.resource.exporter.pdf
        return exporter(r,
                        method="list",
                        pdf_title="Donation Certificate",
                        pdf_filename="DC-%s" % site,
                        pdf_hide_comments=True,
                        pdf_componentname = "inv_track_item",
                        **attr
                       )

    # -------------------------------------------------------------------------
    @staticmethod
    def qnty_recv_repr(value):
        if value:
            return value
        else:
            return B(value)

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_send_ref_represent(value, show_link=True):
        """
            Represent for the Tall Out number,
            if show_link is True then it will generate a link to the pdf
        """
        if value:
            if show_link:
                db = current.db
                table = db.inv_send
                row = db(table.send_ref == value).select(table.id,
                                                         limitby=(0, 1)).first()
                if row:
                    return A(value,
                             _href = URL(f = "send",
                                         args = [row.id, "form"]
                                        ),
                            )
                else:
                    return B(value)
            else:
                return B(value)
        else:
            return current.messages.NONE

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_recv_ref_represent(value, show_link=True):
        """
            Represent for the Goods Received Note
            if show_link is True then it will generate a link to the pdf
        """

        if value:
            if show_link:
                db = current.db
                table = db.inv_recv
                recv_row = db(table.recv_ref == value).select(table.id,
                                                              limitby=(0, 1)).first()
                return A(value,
                         _href = URL(f = "recv",
                                     args = [recv_row.id, "form"]
                                    ),
                        )
            else:
                return B(value)
        else:
            return current.messages.NONE

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_track_item_onvalidate(form):
        """
            When a track item record is being created with a tracking number
            then the tracking number needs to be unique within the organisation.

            If the inv. item is coming out of a warehouse then the inv. item details
            need to be copied across (org, expiry etc)

            If the inv. item is being received then their might be a selected bin
            ensure that the correct bin is selected and save those details.
        """

        vars = form.vars
        send_inv_item_id = vars.send_inv_item_id

        if send_inv_item_id:
            # Copy the data from the sent inv_item
            db = current.db
            itable = db.inv_inv_item
            query = (itable.id == send_inv_item_id)
            record = db(query).select(limitby=(0, 1)).first()
            vars.item_id = record.item_id
            vars.item_source_no = record.item_source_no
            vars.expiry_date = record.expiry_date
            vars.bin = record.bin
            vars.owner_org_id = record.owner_org_id
            vars.supply_org_id = record.supply_org_id
            vars.pack_value = record.pack_value
            vars.currency = record.currency
            vars.inv_item_status = record.status

            # Save the organisation from where this tracking originates
            stable = current.s3db.org_site
            query = query & (itable.site_id == stable.id)
            record = db(query).select(stable.organisation_id,
                                      limitby=(0, 1)).first()
            vars.track_org_id = record.organisation_id

        if not vars.recv_quantity:
            # If we have no send_id and no recv_quantity then
            # copy the quantity sent directly into the received field
            # This is for when there is no related send record
            # The Quantity received ALWAYS defaults to the quantity sent
            # (Please do not change this unless there is a specific user requirement)
            #db.inv_track_item.recv_quantity.default = form.vars.quantity
            vars.recv_quantity = vars.quantity

        recv_bin = vars.recv_bin
        if recv_bin:
            # If there is a receiving bin then select the right one
            if isinstance(recv_bin, list):
                if recv_bin[1] != "":
                    recv_bin = recv_bin[1]
                else:
                    recv_bin = recv_bin[0]

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_kit_onvalidate(form):
        """
            Check that we have sufficient inv_item in stock to build the kits
        """

        vars = form.vars

        db = current.db
        s3db = current.s3db
        ktable = s3db.supply_kit_item
        ptable = db.supply_item_pack
        invtable = db.inv_inv_item

        # The Facility at which we're building these kits
        squery = (invtable.site_id == vars.site_id)

        # Get contents of this kit
        query = (ktable.parent_item_id == vars.item_id)
        rows = db(query).select(ktable.item_id,
                                ktable.quantity,
                                ktable.item_pack_id)

        quantity = vars.quantity
        max_kits = 0
        # @ToDo: Save the results for the onaccept
        #items = {}

        # Loop through each supply_item in the kit
        for record in rows:
            # How much of this supply_item is required per kit?
            one_kit = record.quantity * ptable[record.item_pack_id].quantity

            # How much of this supply_item do we have in stock?
            stock_amount = 0
            query = squery & (invtable.item_id == record.item_id)
            wh_items = db(query).select(invtable.quantity,
                                        invtable.item_pack_id)
            for wh_item in wh_items:
                amount = wh_item.quantity * ptable[wh_item.item_pack_id].quantity
                stock_amount += amount

            # How many Kits can we create?
            kits = stock_amount / one_kit
            if kits > max_kits:
                max_kits = kits

            # @ToDo: Save the results for the onaccept

        if max_kits < quantity:
            form.errors.quantity = T("You can only make %d kit(s) with the available stock" % int(max_kits))

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_kit_onaccept(form):
        """
            Reduce the Inventory stocks by the amounts used to make the kits
            - pick items which have an earlier expiry_date where they have them
            - provide a pick list to ensure that the right stock items are used
              to build the kits: inv_kit_item
        """

        # @ToDo

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_get_shipping_code(type, site_id, field):

        if site_id:
            ostable = current.s3db.org_site
            scode = ostable[site_id].code
            code = "%s-%s-" % (type, scode)
        else:
            code = "%s-###-" % (type)
        number = 0
        if field:
            query = (field.like("%s%%" % code))
            ref_row = current.db(query).select(field,
                                               limitby=(0, 1),
                                               orderby=~field).first()
            if ref_row:
                ref = ref_row(field)
                number = int(ref[-6:])
        return "%s%06d" % (code, number+1)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_track_item_onaccept(form):
        """
           When a track item record is created and it is linked to an inv_item
           then the inv_item quantity will be reduced.
        """

        db = current.db
        s3db = current.s3db
        tracktable = db.inv_track_item
        inv_item_table = db.inv_inv_item
        stable = db.inv_send
        rtable = db.inv_recv
        ritable = s3db.req_req_item
        rrtable = s3db.req_req
        siptable = db.supply_item_pack
        supply_item_add = s3db.supply_item_add
        oldTotal = 0
        id = form.vars.id
        record = form.record

        if form.vars.send_inv_item_id:
            stock_item = inv_item_table[form.vars.send_inv_item_id]
        elif record:
            stock_item = record.send_inv_item_id
        else:
            # will get here for a recv (from external donor / local supplier)
            stock_item = None

        # only modify the original inv. item total if we have a quantity on the form
        # and a stock item to take it from.
        # There will not be a quantity if it is being received since by then it is read only
        # It will be there on an import and so the value will be deducted correctly
        if form.vars.quantity and stock_item:
            stock_quantity = stock_item.quantity
            stock_pack = siptable[stock_item.item_pack_id].quantity
            if record:
                if record.send_inv_item_id != None:
                    # Items have already been removed from stock, so first put them back
                    old_track_pack_quantity = siptable[record.item_pack_id].quantity
                    stock_quantity = supply_item_add(stock_quantity,
                                                     stock_pack,
                                                     record.quantity,
                                                     old_track_pack_quantity
                                                    )
            try:
                new_track_pack_quantity = siptable[form.vars.item_pack_id].quantity
            except:
                new_track_pack_quantity = record.item_pack_id.quantity
            newTotal = supply_item_add(stock_quantity,
                                       stock_pack,
                                       - float(form.vars.quantity),
                                       new_track_pack_quantity
                                      )
            db(inv_item_table.id == stock_item).update(quantity = newTotal)
        if form.vars.send_id and form.vars.recv_id:
            db(rtable.id == form.vars.recv_id).update(send_ref = stable[form.vars.send_id].send_ref)
        # if this is linked to a request then copy the req_ref to the send item
        if record and record.req_item_id:
            req_id = ritable[record.req_item_id].req_id
            req_ref = rrtable[req_id].req_ref
            db(stable.id == form.vars.send_id).update(req_ref = req_ref)
            if form.vars.recv_id:
                db(rtable.id == form.vars.recv_id).update(req_ref = req_ref)

        # if the status is 3 unloading
        # Move all the items into the site, update any request & make any adjustments
        # Finally change the status to 4 arrived
        if record and record.status == TRACK_STATUS_UNLOADING and record.recv_quantity:
            # Look for the item in the site already
            recv_rec = rtable[record.recv_id]
            recv_site_id = recv_rec.site_id
            query = (inv_item_table.site_id == recv_site_id) & \
                    (inv_item_table.item_id == record.item_id) & \
                    (inv_item_table.item_pack_id == record.item_pack_id) & \
                    (inv_item_table.currency == record.currency) & \
                    (inv_item_table.status == record.status) & \
                    (inv_item_table.pack_value == record.pack_value) & \
                    (inv_item_table.expiry_date == record.expiry_date) & \
                    (inv_item_table.bin == record.recv_bin) & \
                    (inv_item_table.owner_org_id == record.owner_org_id) & \
                    (inv_item_table.item_source_no == record.item_source_no) & \
                    (inv_item_table.status == record.inv_item_status) & \
                    (inv_item_table.supply_org_id == record.supply_org_id)
            inv_item_row = db(query).select(inv_item_table.id,
                                            limitby=(0, 1)).first()
            if inv_item_row:
                # Update the existing item
                inv_item_id = inv_item_row.id
                db(inv_item_table.id == inv_item_id).update(quantity = inv_item_table.quantity + record.recv_quantity)
            else:
                # Add a new item
                source_type = 0
                if form.vars.send_inv_item_id:
                    source_type = inv_item_table[form.vars.send_inv_item_id].source_type
                else:
                    if recv_rec.type == 2:
                        source_type = 1 # Donation
                    else:
                        source_type = 2 # Procured
                inv_item_id = inv_item_table.insert(site_id = recv_site_id,
                                             item_id = record.item_id,
                                             item_pack_id = record.item_pack_id,
                                             currency = record.currency,
                                             pack_value = record.pack_value,
                                             expiry_date = record.expiry_date,
                                             bin = record.recv_bin,
                                             owner_org_id = record.owner_org_id,
                                             supply_org_id = record.supply_org_id,
                                             quantity = record.recv_quantity,
                                             item_source_no = record.item_source_no,
                                             source_type = source_type,
                                             status = record.inv_item_status,
                                            )
            # if this is linked to a request then update the quantity fulfil
            if record.req_item_id:
                req_item = ritable[record.req_item_id]
                req_quantity = req_item.quantity_fulfil
                req_pack_quantity = siptable[req_item.item_pack_id].quantity
                track_pack_quantity = siptable[record.item_pack_id].quantity
                quantity_fulfil = supply_item_add(req_quantity,
                                                  req_pack_quantity,
                                                  record.recv_quantity,
                                                  track_pack_quantity
                                                 )
                db(ritable.id == record.req_item_id).update(quantity_fulfil = quantity_fulfil)
                s3db.req_update_status(req_id)

            db(tracktable.id == id).update(recv_inv_item_id = inv_item_id,
                                           status = TRACK_STATUS_ARRIVED)
            # If the receive quantity doesn't equal the sent quantity
            # then an adjustment needs to be set up
            if record.quantity != record.recv_quantity:
                # Do we have an adjustment record?
                # (which might have be created for another item in this shipment)
                query = (tracktable.recv_id == record.recv_id) & \
                        (tracktable.adj_item_id != None)
                adj_rec = db(query).select(tracktable.adj_item_id,
                                          limitby = (0, 1)).first()
                adjitemtable = s3db.inv_adj_item
                if adj_rec:
                    adj_id = adjitemtable[adj_rec.adj_item_id].adj_id
                # If we don't yet have an adj record then create it
                else:
                    adjtable = s3db.inv_adj
                    recv_rec = s3db.inv_recv[record.recv_id]
                    adj_id = adjtable.insert(adjuster_id = recv_rec.recipient_id,
                                             site_id = recv_rec.site_id,
                                             adjustment_date = current.request.now.date(),
                                             category = 0,
                                             status = 1,
                                             comments = recv_rec.comments,
                                            )
                # Now create the adj item record
                adj_item_id = adjitemtable.insert(reason = 0,
                                                  adj_id = adj_id,
                                                  inv_item_id = record.send_inv_item_id, # original source inv_item
                                                  item_id = record.item_id, # the supply item
                                                  item_pack_id = record.item_pack_id,
                                                  old_quantity = record.quantity,
                                                  new_quantity = record.recv_quantity,
                                                  currency = record.currency,
                                                  pack_value = record.pack_value,
                                                  expiry_date = record.expiry_date,
                                                  bin = record.recv_bin,
                                                  comments = record.comments,
                                                  )
                # copy the adj_item_id to the tracking record
                db(tracktable.id == id).update(adj_item_id = adj_item_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_track_item_deleting(id):
        """
           A track item can only be deleted if the status is Preparing
           When a track item record is deleted and it is linked to an inv_item
           then the inv_item quantity will be reduced.
        """

        db = current.db
        s3db = current.s3db
        tracktable = db.inv_track_item
        inv_item_table = db.inv_inv_item
        ritable = s3db.req_req_item
        siptable = db.supply_item_pack
        record = tracktable[id]
        if record.status != 1:
            return False
        # if this is linked to a request
        # then remove these items from the quantity in transit
        if record.req_item_id:
            req_id = record.req_item_id
            req_item = ritable[req_id]
            req_quantity = req_item.quantity_transit
            req_pack_quantity = siptable[req_item.item_pack_id].quantity
            track_pack_quantity = siptable[record.item_pack_id].quantity
            quantity_transit = s3db.supply_item_add(req_quantity,
                                                   req_pack_quantity,
                                                   - record.quantity,
                                                   track_pack_quantity
                                                  )
            db(ritable.id == req_id).update(quantity_transit = quantity_transit)
            s3db.req_update_status(req_id)

        # Check that we have a link to a warehouse
        if record.send_inv_item_id:
            trackTotal = record.quantity
            # Remove the total from this record and place it back in the warehouse
            db(inv_item_table.id == record.send_inv_item_id).update(quantity = inv_item_table.quantity + trackTotal)
            db(tracktable.id == id).update(quantity = 0,
                                           comments = "%sQuantity was: %s" % (inv_item_table.comments, trackTotal))
        return True


# =============================================================================
def inv_tabs(r):
    """
        Add an expandable set of Tabs for a Site's Inventory Tasks

        @ToDo: Make these Expand/Contract without a server-side call
    """

    T = current.T
    s3 = current.session.s3
    settings = current.deployment_settings

    if settings.has_module("inv") and \
        current.auth.s3_has_permission("read", "inv_inv_item"):
        collapse_tabs = settings.get_inv_collapse_tabs()
        tablename, record = s3_rheader_resource(r)
        if collapse_tabs and not \
            (tablename == "org_office" and record.type == 5): # 5 = Warehouse
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
                if not s3.show_inv:
                    s3.show_inv = Storage()
                s3.show_inv["%s_%s" %  (r.name, r.id)] = show_inv
            elif s3.show_inv:
                show_inv = s3.show_inv.get("%s_%s" %  (r.name, r.id))
            else:
                show_inv = False
        else:
            show_inv = True
            show_collapse = False

        if show_inv:
            if settings.get_inv_shipment_name() == "order":
                recv_tab = T("Orders")
            else:
                recv_tab = T("Receive")
            inv_tabs = [(T("Stock"), "inv_item"),
                        #(T("Incoming"), "incoming/"),
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
def inv_warehouse_rheader(r):
    """ Resource Header for warehouse inv. item """

    if r.representation != "html" or r.method == "import":
        # RHeaders only used in interactive views
        return None

    s3db = current.s3db
    tablename, record = s3_rheader_resource(r)
    rheader = None
    if tablename == "org_organisation" or tablename == "org_office":
        rheader = s3db.org_rheader(r)
    if tablename == "inv_inv_item" and record != None:
        tabs = [(T("Details"), None),
                (T("Track Shipment"), "track_movement/"),
               ]
        rheader_tabs = DIV (s3_rheader_tabs(r, tabs))
        table = s3db[tablename]
        rheader = DIV( TABLE(
                           TR( TH("%s: " % table.item_id.label),
                               table.item_id.represent(record.item_id),
                               TH( "%s: " % table.item_pack_id.label),
                               table.item_pack_id.represent(record.item_pack_id),
                              ),
                           TR( TH( "%s: " % table.site_id.label),
                               TD(table.site_id.represent(record.site_id), _colspan=3),
                              ),
                             ),
                        rheader_tabs
                        )
    if tablename == "inv_track_item" and record != None:
        table = s3db["inv_inv_item"]
        irecord = table[record.item_id]
        tabs = [(T("Details"), None),
                (T("Track Shipment"), "inv_item/"),
               ]
        rheader_tabs = DIV (s3_rheader_tabs(r, tabs))
        rheader = DIV( TABLE(
                           TR( TH("%s: " % table.item_id.label),
                               table.item_id.represent(irecord.item_id),
                               TH( "%s: " % table.item_pack_id.label),
                               table.item_pack_id.represent(irecord.item_pack_id),
                              ),
                           TR( TH( "%s: " % table.site_id.label),
                               TD(table.site_id.represent(irecord.site_id), _colspan=3),
                              ),
                             ),
                        rheader_tabs
                        )

    rfooter = TAG[""]()
    if record and "site_id" in record:
        if (r.component and r.component.name == "inv_item"):
            as_btn = A( T("Adjust Stock"),
                          _href = URL(c = "inv",
                                      f = "adj",
                                      args = ["create"],
                                      vars = {"site":record.site_id},
                                      ),
                          _class = "action-btn"
                          )
            rfooter.append(as_btn)
            ts_btn = A( T("Track Shipment"),
                          _href = URL(c = "inv",
                                      f = "track_movement",
                                      vars = {"viewing":"inv_item.%s" % r.component_id},
                                      ),
                          _class = "action-btn"
                          )
            rfooter.append(ts_btn)
    # else:
        # ns_btn = A( T("Receive New Stock"),
                      # _href = URL(c = "inv",
                                  # f = "recv",
                                  # args = ["create"]
                                  # ),
                      # _class = "action-btn"
                      # )
        # rfooter.append(ns_btn)

    current.response.s3.rfooter = rfooter
    return rheader

# =============================================================================
def inv_recv_crud_strings():
    """
        CRUD Strings for inv_recv which ened to be visible to menus without a
        model load
    """

    if current.deployment_settings.get_inv_shipment_name() == "order":
        recv_id_label = T("Order")
        ADD_RECV = T("Add Order")
        current.response.s3.crud_strings["inv_recv"] = Storage(
            title_create = ADD_RECV,
            title_display = T("Order Details"),
            title_list = T("Orders"),
            title_update = T("Edit Order"),
            title_search = T("Search Orders"),
            subtitle_create = ADD_RECV,
            label_list_button = T("List Orders"),
            label_create_button = ADD_RECV,
            label_delete_button = T("Delete Order"),
            msg_record_created = T("Order Created"),
            msg_record_modified = T("Order updated"),
            msg_record_deleted = T("Order canceled"),
            msg_list_empty = T("No Orders registered")
        )
    else:
        recv_id_label = T("Receive Shipment")
        ADD_RECV = T("Receive New Shipment")
        current.response.s3.crud_strings["inv_recv"] = Storage(
            title_create = ADD_RECV,
            title_display = T("Received Shipment Details"),
            title_list = T("Received/Incoming Shipments"),
            title_update = T("Edit Received Shipment"),
            title_search = T("Search Received/Incoming Shipments"),
            subtitle_create = ADD_RECV,
            label_list_button = T("List Received/Incoming Shipments"),
            label_create_button = ADD_RECV,
            label_delete_button = T("Delete Received Shipment"),
            msg_record_created = T("Shipment Created"),
            msg_record_modified = T("Received Shipment updated"),
            msg_record_deleted = T("Received Shipment canceled"),
            msg_list_empty = T("No Received Shipments")
        )
    return

# =============================================================================
def inv_send_rheader(r):
    """ Resource Header for Send """

    if r.representation == "html" and r.name == "send":
        record = r.record
        if record:

            auth = current.auth
            s3db = current.s3db

            tabs = [(T("Edit Details"), None),
                    (T("Items"), "track_item"),
                ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table
            tracktable = s3db.inv_track_item

            send_id = record.id
            site_id = record.site_id
            if site_id:
                org_id = s3db.org_site[site_id].organisation_id
            else:
                org_id = None
            logo = s3db.org_organisation_logo(org_id)
            rData = TABLE(
                           TR(TD(T(settings.get_inv_send_form_name().upper()),
                                 _colspan=2, _class="pdf_title"),
                              TD(logo, _colspan=2),
                              ),
                           TR(TH("%s: " % table.send_ref.label),
                              TD(table.send_ref.represent(record.send_ref))
                              ),
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
                             ),
                           TR(
                               TH("%s: " % table.comments.label),
                               TD(record.comments or "", _colspan=3)
                              )
                         )
            rSubdata = TABLE ()
            rfooter = TAG[""]()

            # Find out how many inv_track_items we have for this send record
            query = (tracktable.send_id == send_id) & \
                    (tracktable.deleted == False)
            cnt = current.db(query).count()

            action = DIV()
            if record.status == SHIP_STATUS_IN_PROCESS:
                if auth.s3_has_permission("update",
                                          "inv_send",
                                          record_id=record.id):

                    if cnt > 0:
                        action.append( A( T("Send Shipment"),
                                      _href = URL(c = "inv",
                                                  f = "send_process",
                                                  args = [record.id]
                                                  ),
                                      _id = "send_process",
                                      _class = "action-btn"
                                      )
                                    )

                        send_btn_confirm = SCRIPT("S3ConfirmClick('#send_process', '%s')"
                                                  % T("Do you want to send this shipment?") )
                        rfooter.append(send_btn_confirm)
                    ritable = current.s3db.req_req_item
                    rcitable = current.s3db.req_commit_item
                    query = (tracktable.send_id == record.id) & \
                            (rcitable.req_item_id == tracktable.req_item_id) & \
                            (tracktable.req_item_id == ritable.id) & \
                            (tracktable.deleted == False)
                    records = current.db(query).select()
                    for record in records:
                        rSubdata.append(TR( TH("%s: " % ritable.item_id.label),
                                   ritable.item_id.represent(record.req_req_item.item_id),
                                   TH("%s: " % rcitable.quantity.label),
                                   record.req_commit_item.quantity,
                                  ))
            elif record.status == SHIP_STATUS_RETURNING:
                    if cnt > 0:
                        action.append( A( T("Complete Returns"),
                                      _href = URL(c = "inv",
                                                  f = "return_process",
                                                  args = [record.id]
                                                  ),
                                      _id = "return_process",
                                      _class = "action-btn"
                                      )
                                    )
                        return_btn_confirm = SCRIPT("S3ConfirmClick('#return_process', '%s')"
                                                  % T("Do you want to complete the return process?") )
                        rfooter.append(return_btn_confirm)
                    else:
                        msg = T("You need to check all item quantities before you can complete the return process")
                        rfooter.append(SPAN(msg))
            elif record.status != SHIP_STATUS_CANCEL:
                if record.status == SHIP_STATUS_SENT:
                    vars = current.request.vars
                    if auth.s3_has_permission("update",
                                              "inv_send",
                                              record_id=record.id):
                        action.append( A( T("Manage Returns"),
                                        _href = URL(f = "send_returns",
                                                    args = [record.id],
                                                    vars = None,
                                                    ),
                                        _id = "send_return",
                                        _class = "action-btn",
                                        _title = T("Only use this button to accept back into stock some items that were returned from a delivery to beneficiaries who do not record the shipment details directly into the system")
                                        )
                                     )

                        return_btn_confirm = SCRIPT("S3ConfirmClick('#send_receive', '%s')"
                                                     % T("Confirm that the shipment has been received by a destination which will not record the shipment directly into the system and confirmed as received.") )
                        rfooter.append(return_btn_confirm)
                        action.append( A( T("Confirm Shipment Received"),
                                        _href = URL(f = "send",
                                                    args = [record.id],
                                                    vars = dict(received = True),
                                                    ),
                                        _id = "send_receive",
                                        _class = "action-btn",
                                        _title = T("Only use this button to confirm that the shipment has been received by a destination which will not record the shipment directly into the system")
                                        )
                                     )

                        receive_btn_confirm = SCRIPT("S3ConfirmClick('#send_receive', '%s')"
                                                     % T("Confirm that the shipment has been received by a destination which will not record the shipment directly into the system and confirmed as received.") )
                        rfooter.append(receive_btn_confirm)
                    if auth.s3_has_permission("delete",
                                              "inv_send",
                                              record_id=record.id):
                        action.append( A( T("Cancel Shipment"),
                                        _href = URL(c = "inv",
                                                    f = "send_cancel",
                                                    args = [record.id]
                                                    ),
                                        _id = "send_cancel",
                                        _class = "action-btn"
                                        )
                                     )

                        cancel_btn_confirm = SCRIPT("S3ConfirmClick('#send_cancel', '%s')"
                                                     % T("Do you want to cancel this sent shipment? The items will be returned to the Warehouse. This action CANNOT be undone!") )
                        rfooter.append(cancel_btn_confirm)
            msg = ""
            if cnt == 1:
                msg = T("One item is attached to this shipment")
            elif cnt > 1:
                msg = T("%s items are attached to this shipment") % cnt
            rData.append(
                         TR( TH(action, _colspan=2),
                             TD(msg)
                           )
                        )

            current.response.s3.rfooter = rfooter
            rheader = DIV (rData,
                           rheader_tabs,
                           rSubdata
                          )
            return rheader
    return None

# ---------------------------------------------------------------------
def inv_send_pdf_footer(r):
    """
    """

    record = r.record
    if record:
        footer = DIV (TABLE (TR(TH(T("Commodities Loaded")),
                                TH(T("Date")),
                                TH(T("Function")),
                                TH(T("Name")),
                                TH(T("Signature")),
                                TH(T("Location (Site)")),
                                TH(T("Condition")),
                                ),
                             TR(TD(T("Loaded By")),
                                TD(),
                                TD(),
                                TD(),
                                TD(),
                                TD(),
                                TD(),
                                ),
                             TR(TD(T("Transported By")),
                                TD(),
                                TD(),
                                TD(),
                                TD(),
                                TD(),
                                TD(),
                                ),
                             TR(TH(T("Reception")),
                                TH(T("Date")),
                                TH(T("Function")),
                                TH(T("Name")),
                                TH(T("Signature")),
                                TH(T("Location (Site)")),
                                TH(T("Condition")),
                                ),
                             TR(TD(T("Received By")),
                                TD(),
                                TD(),
                                TD(),
                                TD(),
                                TD(),
                                TD(),
                                ),
                            )
                     )
        return footer
    return None

# =============================================================================
def inv_recv_rheader(r):
    """ Resource Header for Receiving """

    if r.representation == "html" and r.name == "recv":
        record = r.record
        if record:

            T = current.T
            s3db = current.s3db

            tabs = [(T("Edit Details"), None),
                    (T("Items"), "track_item"),
                    ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table
            tracktable = s3db.inv_track_item

            recv_id = record.id
            site_id = record.site_id
            org_id = s3db.org_site[site_id].organisation_id
            logo = s3db.org_organisation_logo(org_id)
            rData = TABLE(
                           TR(TD(T(current.deployment_settings.get_inv_recv_form_name()),
                                 _colspan=2, _class="pdf_title"),
                              TD(logo, _colspan=2),
                              ),
                           TR(TH("%s: " % table.recv_ref.label),
                              TD(table.recv_ref.represent(record.recv_ref))
                              ),
                           TR( TH("%s: " % table.status.label),
                               table.status.represent(record.status),
                              ),
                           TR( TH( "%s: " % table.eta.label),
                               table.eta.represent(record.eta),
                               TH( "%s: " % table.date.label),
                               table.date.represent(record.date),
                              ),
                           TR( TH( "%s: " % table.from_site_id.label),
                               table.from_site_id.represent(record.from_site_id),
                               TH( "%s: " % table.site_id.label),
                               table.site_id.represent(record.site_id),
                              ),
                           TR( TH( "%s: " % table.sender_id.label),
                               s3_fullname(record.sender_id),
                               TH( "%s: " % table.recipient_id.label),
                               s3_fullname(record.recipient_id),
                              ),
                           TR( TH( "%s: " % table.send_ref.label),
                               table.send_ref.represent(record.send_ref),
                               TH( "%s: " % table.recv_ref.label),
                               table.recv_ref.represent(record.recv_ref),
                              ),
                           TR( TH( "%s: " % table.comments.label),
                               TD(record.comments or "", _colspan=3),
                              ),
                            )

            rfooter = TAG[""]()
            action = DIV()
            # Find out how many inv_track_items we have for this recv record
            query = (tracktable.recv_id == recv_id) & \
                    (tracktable.deleted == False)
            cnt = current.db(query).count()

            if record.status == SHIP_STATUS_SENT or \
               record.status == SHIP_STATUS_IN_PROCESS:
                if current.auth.s3_has_permission("update",
                                                  "inv_recv",
                                                  record_id=record.id):
                    if cnt > 0:
                        action.append( A( T("Receive Shipment"),
                                              _href = URL(c = "inv",
                                                          f = "recv_process",
                                                          args = [record.id]
                                                          ),
                                              _id = "recv_process",
                                              _class = "action-btn"
                                        )
                                      )
                        recv_btn_confirm = SCRIPT("S3ConfirmClick('#recv_process', '%s')"
                                                  % T("Do you want to receive this shipment?") )
                        rfooter.append(recv_btn_confirm)
                    else:
                        msg = T("You need to check all item quantities and allocate to bins before you can receive the shipment")
                        rfooter.append(SPAN(msg))
            else:
                if record.status == SHIP_STATUS_RECEIVED:
                    if current.auth.s3_has_permission("delete",
                                                      "inv_recv",
                                                      record_id=record.id):
                        action.append( A( T("Cancel Shipment"),
                                        _href = URL(c = "inv",
                                                    f = "recv_cancel",
                                                    args = [record.id]
                                                    ),
                                        _id = "recv_cancel",
                                        _class = "action-btn"
                                        )
                                     )

                        cancel_btn_confirm = SCRIPT("S3ConfirmClick('#recv_cancel', '%s')"
                                                     % T("Do you want to cancel this received shipment? The items will be removed from the Warehouse. This action CANNOT be undone!") )
                        rfooter.append(cancel_btn_confirm)
            msg = ""
            if cnt == 1:
                msg = T("This shipment contains one item")
            elif cnt > 1:
                msg = T("This shipment contains %s items") % cnt
            rData.append(
                         TR( TH(action, _colspan=2),
                             TD(msg)
                           )
                        )

            current.response.s3.rfooter = rfooter
            rheader = DIV (rData,
                           rheader_tabs,
                          )
            return rheader
    return None

# ---------------------------------------------------------------------
def inv_recv_pdf_footer(r):
    """
    """

    record = r.record
    if record:
        footer = DIV (TABLE (TR(TH(T("Delivered By")),
                                TH(T("Date")),
                                TH(T("Function")),
                                TH(T("Name")),
                                TH(T("Signature")),
                                ),
                             TR(TD(),
                                TD(),
                                TD(),
                                TD(),
                                TD(),
                                ),
                            TR(TH(T("Received By")),
                                TH(T("Date")),
                                TH(T("Function")),
                                TH(T("Name")),
                                TH(T("Signature / Stamp")),
                                ),
                             TR(TD(),
                                TD(),
                                TD(),
                                TD(),
                                TD(),
                                ),
                            )
                     )
        return footer
    return None

# =============================================================================
class S3AdjustModel(S3Model):
    """
        A module to manage the shipment of inventory items
        - Sent Items
        - Received Items
        - And audit trail of the shipment process
    """

    names = ["inv_adj",
             "inv_adj_item",
             "inv_adj_item_id",
             ]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        person_id = self.pr_person_id
        org_id = self.org_organisation_id
        org_site_represent = self.org_site_represent
        item_id = self.supply_item_id
        inv_item_id = self.inv_item_id
        item_pack_id = self.supply_item_pack_id

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        s3_date_format = current.deployment_settings.get_L10n_date_format()
        s3_date_represent = lambda dt: S3DateTime.date_represent(dt, utc=True)

        # ---------------------------------------------------------------------
        # Adjustments
        #
        adjust_type = {0 : T("Shipment"),
                       1 : T("Inventory"),
                      }
        adjust_status = {0 : T("In Process"),
                         1 : T("Complete"),
                        }

        tablename = "inv_adj"
        table = define_table(tablename,
                             person_id(name = "adjuster_id",
                                       label = T("Actioning officer"),
                                       ondelete = "RESTRICT",
                                       default = auth.s3_logged_in_person(),
                                       comment = self.pr_person_comment(child="adjuster_id")),
                             # This is a reference, not a super-link, so we can override
                             Field("site_id", self.org_site,
                                   label = T("Warehouse"),
                                   ondelete = "SET NULL",
                                   default = auth.user.site_id if auth.is_logged_in() else None,
                                   requires = IS_ONE_OF(db, "org_site.site_id",
                                                        lambda id: \
                                                            org_site_represent(id, show_link = False),
                                                        sort=True,
                                                        ),
                                   represent=org_site_represent),
                             Field("adjustment_date", "date",
                                   label = T("Date of adjustment"),
                                   default = current.request.utcnow,
                                   writable = False,
                                   represent = s3_date_represent,
                                   widget = S3DateWidget()
                                   ),
                             Field("status", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(adjust_status)),
                                   represent = lambda opt: \
                                    adjust_status.get(opt, UNKNOWN_OPT),
                                   default = 0,
                                   label = T("Status of adjustment"),
                                   writable = False,
                                   ),
                             Field("category", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(adjust_type)),
                                   represent = lambda opt: \
                                    adjust_type.get(opt, UNKNOWN_OPT),
                                   default = 1,
                                   label = T("Type of adjustment"),
                                   writable = False,
                                   ),
                             s3_comments(),
                             *s3_meta_fields())

        self.configure("inv_adj",
                        onaccept = self.inv_adj_onaccept,
                        create_next = URL(args=["[id]", "adj_item"]),
                        )

        # Reusable Field
        adj_id = S3ReusableField("adj_id", table,
                                 sortby="date",
                                 requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "inv_adj.id",
                                                          self.inv_adj_represent,
                                                          orderby="inv_adj.adjustment_date",
                                                          sort=True)),
                                 represent = self.inv_adj_represent,
                                 label = T("Inventory Adjustment"),
                                 ondelete = "RESTRICT")

        adjust_reason = {0 : T("Unknown"),
                         1 : T("None"),
                         2 : T("Lost"),
                         3 : T("Damaged"),
                         4 : T("Expired"),
                         5 : T("Found"),
                         6 : T("Transfer Ownership"),
                        }

        # CRUD strings
        ADJUST_STOCK = T("New Stock Adjustment")
        crud_strings["inv_adj"] = Storage(
            title_create = ADJUST_STOCK,
            title_display = T("Stock Adjustment Details"),
            title_list = T("Stock Adjustments"),
            title_update = T("Edit Adjustment"),
            title_search = T("Search Stock Adjustments"),
            subtitle_create = T("New Stock Adjustment"),
            label_list_button = T("List Stock Adjustments"),
            label_create_button = ADJUST_STOCK,
            label_delete_button = T("Delete Stock Adjustment"),
            msg_record_created = T("Adjustment created"),
            msg_record_modified = T("Adjustment modified"),
            msg_record_deleted = T("Adjustment deleted"),
            msg_list_empty = T("No stock adjustments have been done"))

        # ---------------------------------------------------------------------
        # Adjustment Items
        #
        tablename = "inv_adj_item"
        table = define_table(tablename,
                             inv_item_id(ondelete = "RESTRICT",
                                         readable = False,
                                         writable = False),  # original inventory
                             item_id(ondelete = "RESTRICT"),
                             item_pack_id(ondelete = "SET NULL"),
                             Field("old_quantity", "double", notnull=True,
                                   label = T("Original Quantity"),
                                   default = 0,
                                   writable = False),
                             Field("new_quantity", "double",
                                   label = T("Revised Quantity"),
                                   represent = self.qnty_adj_repr,
                                   requires = IS_NOT_EMPTY(),
                                   ),
                             Field("reason", "integer",
                                   label = T("Reason"),
                                   requires = IS_IN_SET(adjust_reason),
                                   default = 1,
                                   represent = lambda opt: \
                                    adjust_reason.get(opt, UNKNOWN_OPT),
                                   writable = False),
                             Field("pack_value", "double",
                                   label = T("Value per Pack")),
                             s3_currency(),
                             Field("old_status", "integer",
                                   label = T("Current Status"),
                                   requires = IS_NULL_OR(IS_IN_SET(inv_item_status_opts)),
                                   represent = lambda opt: \
                                    inv_item_status_opts.get(opt, UNKNOWN_OPT),
                                   default = 0,
                                   writable = False),
                             Field("new_status", "integer",
                                   label = T("Revised Status"),
                                   requires = IS_NULL_OR(IS_IN_SET(inv_item_status_opts)),
                                   represent = lambda opt: \
                                    inv_item_status_opts.get(opt, UNKNOWN_OPT),
                                   default = 0,),
                             Field("expiry_date", "date",
                                   label = T("Expiry Date"),
                                   requires = IS_NULL_OR(IS_DATE(format=s3_date_format)),
                                   represent = s3_date_represent,
                                   widget = S3DateWidget()
                                   ),
                             Field("bin", "string", length=16,
                                   label = T("Bin"),
                                   # @ToDo:
                                   #widget = S3InvBinWidget("inv_adj_item")
                                   ),
                             org_id(name = "old_owner_org_id",
                                    label = T("Current owning Organization"),
                                    ondelete = "SET NULL",
                                    writable = False), # which org owned this item
                             org_id(name = "new_owner_org_id",
                                    label = T("Transfer ownership to Organization"),
                                    ondelete = "SET NULL"), # which org owns this item
                             adj_id(),
                             s3_comments(),
                             *s3_meta_fields()
                             )
        # Reusable Field
        adj_item_id = S3ReusableField("adj_item_id", table,
                                      sortby="item_id",
                                      requires = IS_NULL_OR(
                                                    IS_ONE_OF(db,
                                                              "inv_adj_item.id",
                                                              self.inv_adj_item_represent,
                                                              orderby="inv_adj_item.item_id",
                                                              sort=True)),
                                      represent = self.inv_adj_item_represent,
                                      label = T("Inventory Adjustment Item"),
                                      ondelete = "RESTRICT")

        # CRUD strings
        ADJUST_STOCK = T("Add New Stock Items")
        crud_strings["inv_adj_item"] = Storage(
            title_create = ADJUST_STOCK,
            title_display = T("Item Details"),
            title_list = T("Items in Stock"),
            title_update = T("Adjust Item Quantity"),
            title_search = T("Search Stock Items"),
            subtitle_create = T("Add New Item to Stock"),
            label_list_button = T("List Items in Stock"),
            label_create_button = ADJUST_STOCK,
            #label_delete_button = T("Remove Item from Stock"), # This should be forbidden - set qty to zero instead
            msg_record_created = T("Item added to stock"),
            msg_record_modified = T("Item quantity adjusted"),
            #msg_record_deleted = T("Item removed from Stock"), # This should be forbidden - set qty to zero instead
            msg_list_empty = T("No items currently in stock"))

        # Component
        self.add_component("inv_adj_item",
                            inv_adj="adj_id")

        return Storage(
                    inv_adj_item_id = adj_item_id,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def qnty_adj_repr(value):
        """
            Make unadjusted quantities show up in bold
        """

        if value is None:
            return B(value)
        else:
            return value

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_adj_onaccept(form):
        """
           When an adjustment record is created and it is of type inventory
           then an adj_item record for each inv_inv_item in the site will be
           created. If needed, extra adj_item records can be created later.
        """

        id = form.vars.id
        db = current.db
        inv_item_table = db.inv_inv_item
        adjitemtable = db.inv_adj_item
        adjtable = db.inv_adj
        adj_rec = adjtable[id]
        if adj_rec.category == 1:
            site_id = form.vars.site_id
            # Only get inv. item with a positive quantity
            query = (inv_item_table.site_id == site_id) & \
                    (inv_item_table.quantity > 0) & \
                    (inv_item_table.deleted == False)
            row = db(query).select()
            for inv_item in row:
                # add an adjustment item record
                adjitemtable.insert(reason = 0,
                                    adj_id = id,
                                    inv_item_id = inv_item.id, # original source inv_item
                                    item_id = inv_item.item_id, # the supply item
                                    item_pack_id = inv_item.item_pack_id,
                                    old_quantity = inv_item.quantity,
                                    currency = inv_item.currency,
                                    old_status = inv_item.status,
                                    pack_value = inv_item.pack_value,
                                    expiry_date = inv_item.expiry_date,
                                    bin = inv_item.bin,
                                    old_owner_org_id = inv_item.owner_org_id,
                                   )

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_adj_represent(id, show_link=True):
        """
        """

        if id:
            db = current.db
            table = db.inv_adj
            row = db(table.id == id).select(table.adjustment_date,
                                            table.adjuster_id,
                                            limitby=(0, 1)).first()
            repr = "%s - %s" % (table.adjuster_id.represent(row.adjuster_id),
                                table.adjustment_date.represent(row.adjustment_date)
                                )
            if show_link:
                return SPAN(repr)
            else:
                return repr
        else:
            return current.messages.NONE

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_adj_item_represent(id, show_link=True):
        """
        """

        if id:
            db = current.db
            table = db.inv_adj_item
            row = db(table.id == id).select(table.item_id,
                                            table.old_quantity,
                                            table.new_quantity,
                                            table.item_pack_id,
                                            limitby=(0, 1)).first()
            repr = "%s:%s %s" % (table.item_id.represent(row.item_id,
                                                         show_link = show_link),
                                 (row.new_quantity - row.old_quantity),
                                 table.item_pack_id.represent(row.item_pack_id),
                                 )
            if show_link:
                return SPAN(repr)
            else:
                return repr
        else:
            return current.messages.NONE

# =============================================================================
def inv_adj_rheader(r):
    """ Resource Header for Inventory Adjustments """

    if r.representation == "html" and r.name == "adj":
        record = r.record
        if record:

            tabs = [(T("Edit Details"), None),
                    (T("Items"), "adj_item"),
                ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table
            rheader = DIV( TABLE(
                               TR( TH("%s: " % table.adjuster_id.label),
                                   table.adjuster_id.represent(record.adjuster_id),
                                   TH("%s: " % table.adjustment_date.label),
                                   table.adjustment_date.represent(record.adjustment_date),
                                  ),
                               TR( TH("%s: " % table.site_id.label),
                                   table.site_id.represent(record.site_id),
                                   TH("%s: " % table.category.label),
                                   table.category.represent(record.category),
                                  ),
                                 ),
                            rheader_tabs
                            )

            rfooter = TAG[""]()
            if record.status == 0: # In process
                if current.auth.s3_has_permission("update",
                                                  "inv_adj",
                                                  record_id=record.id):
                    # aitable = current.s3db.inv_adj_item
                    # query = (aitable.adj_id == record.id) & \
                            # (aitable.new_quantity == None)
                    # row = current.db(query).select(aitable.id,
                                                   # limitby=(0, 1)).first()
                    # if row == None:
                    close_btn = A( T("Close Adjustment"),
                                  _href = URL(c = "inv",
                                              f = "adj_close",
                                              args = [record.id]
                                              ),
                                  _id = "adj_close",
                                  _class = "action-btn"
                                  )
                    close_btn_confirm = SCRIPT("S3ConfirmClick('#adj_close', '%s')"
                                              % T("Do you want to close this adjustment?") )
                    rfooter.append(close_btn)
                    rfooter.append(close_btn_confirm)
                    # else:
                        # msg = T("You need to check all the revised quantities before you can close this adjustment")
                        # rfooter.append(SPAN(msg))
            current.response.s3.rfooter = rfooter
            return rheader
    return None

# =============================================================================
# Generic function called by the duplicator methods to determine if the
# record already exists on the database.
def duplicator(job, query):
    """
      This callback will be called when importing records it will look
      to see if the record being imported is a duplicate.

      @param job: An S3ImportJob object which includes all the details
                  of the record being imported

      If the record is a duplicate then it will set the job method to update
    """

    table = job.table
    _duplicate = current.db(query).select(table.id,
                                          limitby=(0, 1)).first()
    if _duplicate:
        job.id = _duplicate.id
        job.data.id = _duplicate.id
        job.method = job.METHOD.UPDATE
        return _duplicate.id
    return False

# =============================================================================
class InvItemVirtualFields:
    """ Virtual fields as dimension classes for reports """

    extra_fields = ["quantity",
                    "pack_value",
                    ]

    def total_value(self):
        """ Year/Month of the start date of the training event """
        try:
            v = self.inv_inv_item.quantity * self.inv_inv_item.pack_value
            # Need real numbers to use for Report calculations
            #return IS_FLOAT_AMOUNT.represent(v, precision=2)
            return v
        except:
            # not available
            return current.messages.NONE

    def item_code(self):
        try:
            return self.inv_inv_item.item_id.code
        except:
            # not available
            return current.messages.NONE

    def item_category(self):
        try:
            return self.inv_inv_item.item_id.item_category_id.name
        except:
            # not available
            return current.messages.NONE

# =============================================================================
class InvTrackItemVirtualFields:
    """ Virtual fields as dimension classes for reports """

    extra_fields = ["quantity",
                    "pack_value",
                    ]

    def total_value(self):
        try:
            v = self.inv_track_item.quantity * self.inv_track_item.pack_value
            # Need real numbers to use for Report calculations
            #return IS_FLOAT_AMOUNT.represent(v, precision=2)
            return v
        except:
            # not available
            return current.messages.NONE

# END =========================================================================
