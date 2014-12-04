# -*- coding: utf-8 -*-

""" Sahana Eden Inventory Model

    @copyright: 2009-2014 (c) Sahana Software Foundation
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

__all__ = ("S3WarehouseModel",
           "S3InventoryModel",
           "S3InventoryTrackingLabels",
           "S3InventoryTrackingModel",
           "S3InventoryAdjustModel",
           "inv_tabs",
           "inv_rheader",
           "inv_rfooter",
           "inv_recv_crud_strings",
           "inv_recv_rheader",
           "inv_send_rheader",
           "inv_ship_status",
           "inv_tracking_status",
           "inv_adj_rheader",
           "depends",
           "inv_InvItemRepresent",
           )

import itertools

from gluon import *
from gluon.sqlhtml import RadioWidget
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3AddResourceLink

SHIP_STATUS_IN_PROCESS = 0
SHIP_STATUS_RECEIVED   = 1
SHIP_STATUS_SENT       = 2
SHIP_STATUS_CANCEL     = 3
SHIP_STATUS_RETURNING  = 4

# Dependency list
depends = ["supply"]

# To pass to global scope
inv_ship_status = {"IN_PROCESS" : SHIP_STATUS_IN_PROCESS,
                   "RECEIVED"   : SHIP_STATUS_RECEIVED,
                   "SENT"       : SHIP_STATUS_SENT,
                   "CANCEL"     : SHIP_STATUS_CANCEL,
                   "RETURNING"  : SHIP_STATUS_RETURNING,
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

inv_tracking_status = {"UNKNOWN"    : TRACK_STATUS_UNKNOWN,
                       "IN_PROCESS" : TRACK_STATUS_PREPARING,
                       "SENT"       : TRACK_STATUS_TRANSIT,
                       "UNLOADING"  : TRACK_STATUS_UNLOADING,
                       "RECEIVED"   : TRACK_STATUS_ARRIVED,
                       "CANCEL"     : TRACK_STATUS_CANCELED,
                       "RETURNING"  : TRACK_STATUS_RETURNING,
                       }

# Compact JSON encoding
SEPARATORS = (",", ":")

# =============================================================================
class S3WarehouseModel(S3Model):

    names = ("inv_warehouse",
             #"inv_warehouse_type",
             )

    def model(self):

        T = current.T
        #db = current.db
        messages = current.messages
        NONE = messages["NONE"]
        #add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Warehouse Types
        #
        # tablename = "inv_warehouse_type"
        # define_table(tablename,
        #              Field("name", length=128,
        #                    notnull=True, unique=True,
        #                    label=T("Name")),
        #              s3_comments(),
        #              *s3_meta_fields())

        # CRUD strings
        #crud_strings[tablename] = Storage(
        #    label_create = T("Add Warehouse Type"),
        #    title_display = T("Warehouse Type Details"),
        #    title_list = T("Warehouse Types"),
        #    title_update = T("Edit Warehouse Type"),
        #    label_list_button = T("List Warehouse Types"),
        #    label_delete_button = T("Delete Warehouse Type"),
        #    msg_record_created = T("Warehouse Type added"),
        #    msg_record_modified = T("Warehouse Type updated"),
        #    msg_record_deleted = T("Warehouse Type deleted"),
        #    msg_list_empty = T("No Warehouse Types currently registered"))

        #represent = S3Represent(lookup=tablename, translate=True)

        #warehouse_type_id = S3ReusableField("warehouse_type_id", "reference %s" % tablename,
        #                        label = T("Warehouse Type"),
        #                        ondelete = "SET NULL",
        #                        represent = represent,
        #                        requires = IS_EMPTY_OR(
        #                                    IS_ONE_OF(db, "inv_warehouse_type.id",
        #                                              represent,
        #                                              sort=True
        #                                              )),
        #                        sortby = "name",
        #                        comment = S3AddResourceLink(c="inv",
        #                                    f="warehouse_type",
        #                                    label=T("Add Warehouse Type"),
        #                                    title=T("Warehouse Type"),
        #                                    tooltip=T("If you don't see the Type in the list, you can add a new one by clicking link 'Add Warehouse Type'.")),
        #                        )

        #configure(tablename,
        #          deduplicate = self.inv_warehouse_type_duplicate,
        #          )

        # Tags as component of Warehouse Types
        #add_components(tablename,
        #               inv_warehouse_type_tag={"name": "tag",
        #                                       "joinby": "warehouse_type_id",
        #                                      }
        #              )

        # ---------------------------------------------------------------------
        # Warehouses
        #
        tablename = "inv_warehouse"
        define_table(tablename,
                     super_link("pe_id", "pr_pentity"),
                     super_link("site_id", "org_site"),
                     super_link("doc_id", "doc_entity"),
                     Field("name", notnull=True,
                           length=64,           # Mayon Compatibility
                           label = T("Name"),
                           ),
                     Field("code", length=10, # Mayon compatibility
                           label = T("Code"),
                           represent = lambda v: v or NONE,
                           # Deployments that don't wants warehouse codes can hide them
                           #readable=False,
                           #writable=False,
                           # @ToDo: Deployment Setting to add validator to make these unique
                           ),
                     self.org_organisation_id(
                        requires = self.org_organisation_requires(updateable=True),
                        ),
                     #warehouse_type_id(),
                     self.gis_location_id(),
                     Field("phone1", label = T("Phone 1"),
                           represent = lambda v: v or NONE,
                           requires = IS_EMPTY_OR(s3_phone_requires)
                           ),
                     Field("phone2", label = T("Phone 2"),
                           represent = lambda v: v or NONE,
                           requires = IS_EMPTY_OR(s3_phone_requires)
                           ),
                     Field("email", label = T("Email"),
                           represent = lambda v: v or NONE,
                           requires = IS_EMPTY_OR(IS_EMAIL())
                           ),
                     Field("fax", label = T("Fax"),
                           represent = lambda v: v or NONE,
                           requires = IS_EMPTY_OR(s3_phone_requires)
                           ),
                     Field("obsolete", "boolean",
                           default = False,
                           label = T("Obsolete"),
                           represent = lambda opt: \
                                       (opt and [T("Obsolete")] or NONE)[0],
                           readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Warehouse"),
            title_display = T("Warehouse Details"),
            title_list = T("Warehouses"),
            title_update = T("Edit Warehouse"),
            title_upload = T("Import Warehouses"),
            title_map = T("Map of Warehouses"),
            label_list_button = T("List Warehouses"),
            label_delete_button = T("Delete Warehouse"),
            msg_record_created = T("Warehouse added"),
            msg_record_modified = T("Warehouse updated"),
            msg_record_deleted = T("Warehouse deleted"),
            msg_list_empty = T("No Warehouses currently registered"))

        # Filter widgets
        filter_widgets = [
                S3TextFilter(["name",
                              "code",
                              "comments",
                              "organisation_id$name",
                              "organisation_id$acronym",
                              "location_id$name",
                              "location_id$L1",
                              "location_id$L2",
                              ],
                             label=T("Name"),
                             _class="filter-search",
                             ),
                S3OptionsFilter("organisation_id",
                                label=T("Organization"),
                                represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3LocationFilter("location_id",
                                 label=T("Location"),
                                 levels=["L0", "L1", "L2"],
                                 widget="multiselect",
                                 cols=3,
                                 #hidden=True,
                                 ),
                ]

        configure(tablename,
                  deduplicate = self.inv_warehouse_duplicate,
                  filter_widgets=filter_widgets,
                  list_fields=["id",
                               "name",
                               "organisation_id",   # Filtered in Component views
                               #"type",
                               #(T("Address"), "location_id$addr_street"),
                               (messages.COUNTRY, "location_id$L0"),
                               "location_id$L1",
                               "location_id$L2",
                               "location_id$L3",
                               #"location_id$L4",
                               "phone1",
                               "email"
                               ],
                  onaccept = self.inv_warehouse_onaccept,
                  realm_components = ("contact_emergency",
                                      "physical_description",
                                      "config",
                                      "image",
                                      "req",
                                      "send",
                                      "human_resource_site",
                                      "note",
                                      "contact",
                                      "role",
                                      "asset",
                                      "commit",
                                      "inv_item",
                                      "document",
                                      "recv",
                                      "address",
                                      ),
                  super_entity = ("pr_pentity", "org_site"),
                  update_realm = True,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

    # -------------------------------------------------------------------------
    #@staticmethod
    #def inv_warehouse_type_duplicate(item):
    #    """ Import item de-duplication """

    #    name = item.data.get("name")
    #    table = item.table
    #    query = (table.name.lower() == name.lower())
    #    duplicate = current.db(query).select(table.id,
    #                                         limitby=(0, 1)).first()
    #    if duplicate:
    #        item.id = duplicate.id
    #        item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_warehouse_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        current.s3db.org_update_affiliations("inv_warehouse", form.vars)

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_warehouse_duplicate(item):
        """
            Import item deduplication, match by name
                (Adding location_id doesn't seem to be a good idea)

            @param item: the S3ImportItem instance
        """

        name = item.data.get("name")
        table = item.table
        query = (table.name.lower() == name.lower())
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
class S3InventoryModel(S3Model):
    """
        Inventory Management

        A module to record inventories of items at a location (site)
    """

    names = ("inv_inv_item",
             "inv_remove",
             "inv_item_id",
             "inv_item_represent",
             "inv_prep",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        organisation_id = self.org_organisation_id

        messages = current.messages
        NONE = messages["NONE"]
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        settings = current.deployment_settings
        WAREHOUSE = settings.get_inv_facility_label()
        track_pack_values = settings.get_inv_track_pack_values()

        inv_source_type = {0: None,
                           1: T("Donated"),
                           2: T("Procured"),
                           }
        # =====================================================================
        # Inventory Item
        #
        # Stock in a warehouse or other site's inventory store.
        #
        # ondelete references have been set to RESTRICT because the inv. items
        # should never be automatically deleted
        inv_item_status_opts = self.inv_item_status_opts

        tablename = "inv_inv_item"
        self.define_table(tablename,
                          # This is a component, so needs to be a super_link
                          # - can't override field name, ondelete or requires
                          self.super_link("site_id", "org_site",
                                          default = auth.user.site_id if auth.is_logged_in() else None,
                                          empty = False,
                                          label = WAREHOUSE,
                                          ondelete = "RESTRICT",
                                          represent = self.org_site_represent,
                                          readable = True,
                                          writable = True,
                                          # Comment these to use a Dropdown & not an Autocomplete
                                          #widget = S3SiteAutocompleteWidget(),
                                          #comment = DIV(_class="tooltip",
                                          #              _title="%s|%s" % (WAREHOUSE,
                                          #                                messages.AUTOCOMPLETE_HELP)),
                                          ),
                          self.supply_item_entity_id,
                          self.supply_item_id(ondelete = "RESTRICT",
                                              required = True,
                                              ),
                          self.supply_item_pack_id(ondelete = "RESTRICT",
                                                   required = True,
                                                   ),
                          Field("quantity", "double", notnull=True,
                                default = 0.0,
                                label = T("Quantity"),
                                represent = lambda v: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2),
                                requires = IS_FLOAT_IN_RANGE(0, None),
                                writable = False,
                                ),
                          Field("bin", "string", length=16,
                                label = T("Bin"),
                                represent = lambda v: v or NONE,
                                ),
                          # @ToDo: Allow items to be marked as 'still on the shelf but allocated to an outgoing shipment'
                          Field("status", "integer",
                                default = 0,
                                label = T("Status"),
                                represent = lambda opt: \
                                    inv_item_status_opts.get(opt, UNKNOWN_OPT),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(inv_item_status_opts)
                                            ),
                                ),
                          s3_date("purchase_date",
                                  label = T("Purchase Date"),
                                  ),
                          s3_date("expiry_date",
                                  label = T("Expiry Date"),
                                  ),
                          Field("pack_value", "double",
                                label = T("Value per Pack"),
                                represent = lambda v: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2),
                                readable = track_pack_values,
                                writable = track_pack_values,
                                ),
                            # @ToDo: Move this into a Currency Widget for the pack_value field
                          s3_currency(readable = track_pack_values,
                                      writable = track_pack_values,
                                      ),
                          Field("item_source_no", "string", length=16,
                                label = self.inv_itn_label,
                                represent = lambda v: v or NONE,
                                ),
                          # Organisation that owns this item
                          organisation_id("owner_org_id",
                                          label = T("Owned By (Organization/Branch)"),
                                          ondelete = "SET NULL",
                                          ),
                          # Original donating Organisation
                          organisation_id("supply_org_id",
                                          label = T("Supplier/Donor"),
                                          ondelete = "SET NULL",
                                          ),
                          Field("source_type", "integer",
                                default = 0,
                                label = T("Type"),
                                represent = lambda opt: \
                                    inv_source_type.get(opt, UNKNOWN_OPT),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(inv_source_type)
                                            ),
                                writable = False,
                                ),
                          Field.Method("total_value",
                                       self.inv_item_total_value),
                          Field.Method("pack_quantity",
                                       self.supply_item_pack_quantity(tablename=tablename)),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        INV_ITEM = T("Warehouse Stock")
        ADD_INV_ITEM = T("Add Stock to Warehouse")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = ADD_INV_ITEM,
            title_display = T("Warehouse Stock Details"),
            title_list = T("Stock in Warehouse"),
            title_update = T("Edit Warehouse Stock"),
            title_report = T("Warehouse Stock Report"),
            title_upload = T("Import Warehouse Stock"),
            label_list_button = T("List Stock in Warehouse"),
            label_delete_button = T("Remove Stock from Warehouse"),
            msg_record_created = T("Stock added to Warehouse"),
            msg_record_modified = T("Warehouse Stock updated"),
            msg_record_deleted = T("Stock removed from Warehouse"),
            msg_list_empty = T("No Stock currently registered in this Warehouse"))

        # Reusable Field
        inv_item_represent = inv_InvItemRepresent()
        inv_item_id = S3ReusableField("inv_item_id", "reference %s" % tablename,
                                      label = INV_ITEM,
                                      ondelete = "CASCADE",
                                      represent = inv_item_represent,
                                      requires = IS_ONE_OF(db, "inv_inv_item.id",
                                                           inv_item_represent,
                                                           orderby="inv_inv_item.id",
                                                           sort=True),
                                      comment = DIV(_class="tooltip",
                                                    _title="%s|%s" % (INV_ITEM,
                                                                      T("Select Stock from this Warehouse"))),
                                      script = '''
$.filterOptionsS3({
 'trigger':'inv_item_id',
 'target':'item_pack_id',
 'lookupResource':'item_pack',
 'lookupPrefix':'supply',
 'lookupURL':S3.Ap.concat('/inv/inv_item_packs/'),
 'msgNoRecords':i18n.no_packs,
 'fncPrep':S3.supply.fncPrepItem,
 'fncRepresent':S3.supply.fncRepresentItem
})''')

        # Filter widgets
        filter_widgets = [
            S3TextFilter(["item_id$name",
                          "item_pack_id$name",
                         ],
                         label=T("Item name"),
                         comment=T("Search for items with this text in the name."),
                        ),
            S3OptionsFilter("site_id",
                            label=T("Facility"),
                            cols = 2,
                            hidden = True,
                           ),
            S3OptionsFilter("status",
                            label=T("Status"),
                            cols = 2,
                            hidden = True,
                           ),
            S3RangeFilter("quantity",
                          label=T("Quantity range"),
                          comment=T("Include only items where quantity is in this range."),
                          ge=10,
                          hidden = True,
                         ),
            S3DateFilter("purchase_date",
                         label=T("Purchase date"),
                         comment=T("Include only items purchased within the specified dates."),
                         hidden = True,
                        ),
            S3DateFilter("other_date",
                         label=T("Expiry date"),
                         comment=T("Include only items that expire within the specified dates."),
                         hidden = True,
                        ),
            S3OptionsFilter("owner_org_id",
                            label=T("Owning organization"),
                            comment=T("Search for items by owning organization."),
                            represent="%(name)s",
                            cols=2,
                            hidden = True,
                           ),
            S3OptionsFilter("supply_org_id",
                            label=T("Donating Organization"),
                            comment=T("Search for items by donating organization."),
                            represent="%(name)s",
                            cols=2,
                            hidden = True,
                           ),
        ]

        # Report options
        if track_pack_values:
            rows = ["item_id", "item_id$item_category_id", "currency"]
            cols = ["site_id", "owner_org_id", "supply_org_id", "currency"]
            fact = ["quantity", (T("Total Value"), "total_value"),]
        else:
            rows = ["item_id", "item_id$item_category_id"]
            cols = ["site_id", "owner_org_id", "supply_org_id"]
            fact = ["quantity"]

        report_options = Storage(rows = rows,
                                 cols = cols,
                                 fact = fact,
                                 methods = ["sum"],
                                 defaults = Storage(rows = "item_id",
                                                    cols = "site_id",
                                                    fact = "sum(quantity)",
                                                    ),
                                 groupby = self.inv_inv_item.site_id,
                                 hide_comments = True,
                                 )

        # List fields
        if track_pack_values:
            list_fields = ["id",
                           "site_id",
                           "item_id",
                           "item_id$code",
                           "item_id$item_category_id",
                           "quantity",
                           "owner_org_id",
                           "pack_value",
                           (T("Total Value"), "total_value"),
                           "currency",
                           "bin",
                           "supply_org_id",
                           "status",
                           ]
        else:
            list_fields = ["id",
                           "site_id",
                           "item_id",
                           "item_id$code",
                           "item_id$item_category_id",
                           "quantity",
                           "bin",
                           "owner_org_id",
                           "supply_org_id",
                           "status",
                           ]

        # Configuration
        direct_stock_edits = settings.get_inv_direct_stock_edits()
        self.configure(tablename,
                       # Lock the record so that it can't be meddled with
                       # - unless explicitly told to allow this
                       create = direct_stock_edits,
                       deletable = direct_stock_edits,
                       editable = direct_stock_edits,
                       listadd = direct_stock_edits,
                       deduplicate = self.inv_item_duplicate,
                       extra_fields = ["quantity",
                                       "pack_value",
                                       "item_pack_id",
                                       ],
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       onvalidation = self.inv_inv_item_onvalidate,
                       report_options = report_options,
                       super_entity = "supply_item_entity",
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(inv_item_id = inv_item_id,
                    inv_item_represent = inv_item_represent,
                    inv_remove = self.inv_remove,
                    inv_prep = self.inv_prep,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_item_total_value(row):
        """ Total value of an inventory item """

        if hasattr(row, "inv_inv_item"):
            row = row.inv_inv_item
        try:
            v = row.quantity * row.pack_value
            return v

        except (AttributeError,TypeError):
            # not available
            return current.messages["NONE"]

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_inv_item_onvalidate(form):
        """
            When a inv_inv_item record is created with a source number,
            then the source number needs to be unique within the
            organisation.
        """

        item_source_no = form.vars.item_source_no
        if not item_source_no:
            return
        if hasattr(form, "record"):
            record = form.record
            if record and \
               record.item_source_no and \
               record.item_source_no == item_source_no:
                # The tracking number hasn't changed so no validation needed
                return

        db = current.db
        s3db = current.s3db

        itable = s3db.inv_inv_item

        # Was: "track_org_id" - but inv_inv_item has no "track_org_id"!
        org_field = "owner_org_id"

        query = (itable[org_field] == form.vars[org_field]) & \
                (itable.item_source_no == item_source_no)

        record = db(query).select(itable[org_field],
                                  limitby=(0, 1)).first()
        if record:
            org = current.response.s3 \
                         .org_organisation_represent(record[org_field])

            form.errors.item_source_no = current.T("The Tracking Number %s "
                                                   "is already used by %s.") % \
                                                   (item_source_no, org)

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
        inv_p_qnty = db(siptable.id == inv_rec.item_pack_id).select(siptable.quantity,
                                                                    limitby=(0, 1)
                                                                    ).first().quantity
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
            if new_qnty:
                db(inv_item_table.id == inv_rec.id).update(quantity = new_qnty)
            else:
                db(inv_item_table.id == inv_rec.id).update(deleted = True)

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
                    item = db(table.id == r.args[2]).select(table.item_id,
                                                            limitby=(0, 1)).first()
                    item_ids.remove(item.item_id)
                table.item_id.requires.set_filter(not_filterby = "id",
                                                  not_filter_opts = item_ids)

            elif r.component.name == "send":
                # Default to the Search tab in the location selector widget1
                current.response.s3.gis.tab = "search"
                #if current.request.get_vars.get("select", "sent") == "incoming":
                #    # Display only incoming shipments which haven't been received yet
                #    filter = (current.s3db.inv_send.status == SHIP_STATUS_SENT)
                #    r.resource.add_component_filter("send", filter)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_item_duplicate(item):
        """
            Update detection for inv_inv_item

            @param item: the S3ImportItem
        """

        table = item.table
        data = item.data

        site_id = data.get("site_id")
        item_id = data.get("item_id")
        pack_id = data.get("item_pack_id")
        owner_org_id = data.get("owner_org_id")
        supply_org_id = data.get("supply_org_id")
        pack_value = data.get("pack_value")
        currency = data.get("currency")
        bin = data.get("bin")

        # Must match all of these exactly
        query = (table.site_id == site_id) & \
                (table.item_id == item_id) & \
                (table.item_pack_id == pack_id) & \
                (table.owner_org_id == owner_org_id) & \
                (table.supply_org_id == supply_org_id) & \
                (table.pack_value == pack_value) & \
                (table.currency == currency) & \
                (table.bin == bin)

        duplicate = current.db(query).select(table.id,
                                             table.quantity,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

            # If the import item has a quantity of 0 (e.g. when imported
            # implicitly through inv_track_item), retain the stock quantity
            if "quantity" in data and data.quantity == 0:
                item.data.quantity = duplicate.quantity

# =============================================================================
class S3InventoryTrackingLabels(S3Model):
    """ Tracking Status Labels """

    names = ("inv_tracking_status_labels",
             "inv_shipment_status_labels",
             "inv_itn_label",
             "inv_item_status_opts",
             )

    def model(self):

        T = current.T
        shipment_status = {SHIP_STATUS_IN_PROCESS: T("In Process"),
                           SHIP_STATUS_RECEIVED: T("Received"),
                           SHIP_STATUS_SENT: T("Sent"),
                           SHIP_STATUS_CANCEL: T("Canceled"),
                           SHIP_STATUS_RETURNING: T("Returning"),
                           }

        tracking_status = {TRACK_STATUS_UNKNOWN: T("Unknown"),
                           TRACK_STATUS_PREPARING: T("In Process"),
                           TRACK_STATUS_TRANSIT: T("In transit"),
                           TRACK_STATUS_UNLOADING: T("Unloading"),
                           TRACK_STATUS_ARRIVED: T("Arrived"),
                           TRACK_STATUS_CANCELED: T("Canceled"),
                           TRACK_STATUS_RETURNING: T("Returning"),
                           }

        #itn_label = T("Item Source Tracking Number")
        # Overwrite the label until we have a better way to do this
        itn_label = T("CTN")

        settings = current.deployment_settings
        return dict(inv_tracking_status_labels = tracking_status,
                    inv_shipment_status_labels = shipment_status,
                    inv_itn_label = itn_label,
                    inv_item_status_opts = settings.get_inv_item_status()
                    )

    # -------------------------------------------------------------------------
    def defaults(self):

        # inv disabled => label dicts can remain the same, however
        return self.model()

# =============================================================================
class S3InventoryTrackingModel(S3Model):
    """
        A module to manage the shipment of inventory items
        - Sent Items
        - Received Items
        - And audit trail of the shipment process
    """

    names = ("inv_send",
             "inv_send_represent",
             "inv_send_ref_represent",
             "inv_send_controller",
             "inv_send_onaccept",
             "inv_send_process",
             "inv_recv",
             "inv_recv_represent",
             "inv_recv_ref_represent",
             "inv_kit",
             "inv_track_item",
             "inv_track_item_onaccept",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        settings = current.deployment_settings

        person_id = self.pr_person_id
        organisation_id = self.org_organisation_id
        item_id = self.supply_item_id
        inv_item_id = self.inv_item_id
        item_pack_id = self.supply_item_pack_id
        req_item_id = self.req_item_id
        req_ref = self.req_req_ref
        tracking_status = self.inv_tracking_status_labels
        shipment_status = self.inv_shipment_status_labels

        org_site_represent = self.org_site_represent

        messages = current.messages
        NONE = messages["NONE"]
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        SITE_LABEL = settings.get_org_site_label()
        show_org = settings.get_inv_send_show_org()
        show_transport = settings.get_inv_send_show_mode_of_transport()
        show_req_ref = settings.get_req_use_req_number()
        type_default = settings.get_inv_send_type_default()
        time_in = settings.get_inv_send_show_time_in()

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method
        super_link = self.super_link

        is_logged_in = auth.is_logged_in
        user = auth.user

        s3_string_represent = lambda str: str if str else NONE

        send_ref = S3ReusableField("send_ref",
                                   label = T(settings.get_inv_send_ref_field_name()),
                                   represent = self.inv_send_ref_represent,
                                   writable = False,
                                   )
        recv_ref = S3ReusableField("recv_ref",
                                   label = T("%(GRN)s Number") % dict(GRN=settings.get_inv_recv_shortname()),
                                   represent = self.inv_recv_ref_represent,
                                   writable = False,
                                   )
        purchase_ref = S3ReusableField("purchase_ref",
                                       label = T("%(PO)s Number") % dict(PO=settings.get_proc_shortname()),
                                       represent = s3_string_represent,
                                       )

        # ---------------------------------------------------------------------
        # Send (Outgoing / Dispatch / etc)
        #
        send_type_opts = settings.get_inv_shipment_types()
        send_type_opts.update(self.inv_item_status_opts)
        send_type_opts.update(settings.get_inv_send_types())

        tablename = "inv_send"
        define_table(tablename,
                     send_ref(),
                     req_ref(readable = show_req_ref,
                             writable = show_req_ref,
                             ),
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("site_id", "org_site",
                                default = user.site_id if is_logged_in() else None,
                                empty = False,
                                instance_types = auth.org_site_types,
                                label = T("From %(site)s") % dict(site=SITE_LABEL),
                                not_filterby = "obsolete",
                                not_filter_opts = (True,),
                                readable = True,
                                writable = True,
                                represent = org_site_represent,
                                updateable = True,
                                #widget = S3SiteAutocompleteWidget(),
                                ),
                     Field("type", "integer",
                           default = type_default,
                           label = T("Shipment Type"),
                           represent = lambda opt: \
                            send_type_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(send_type_opts),
                           readable = not type_default,
                           writable = not type_default,
                           ),
                     # This is a reference, not a super-link, so we can override
                     Field("to_site_id", self.org_site,
                           label = T("To %(site)s") % dict(site=SITE_LABEL),
                           ondelete = "SET NULL",
                           represent =  org_site_represent,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "org_site.site_id",
                                                  lambda id, row: \
                                                  org_site_represent(id, row,
                                                                     show_link=False),
                                                  sort=True,
                                                  not_filterby = "obsolete",
                                                  not_filter_opts = (True,),
                                                 )),
                           ),
                     organisation_id(
                        label = T("To Organization"),
                        readable = show_org,
                        writable = show_org,
                        ),
                     person_id("sender_id",
                               default = auth.s3_logged_in_person(),
                               label = T("Sent By"),
                               ondelete = "SET NULL",
                               comment = self.pr_person_comment(child="sender_id"),
                               ),
                     person_id("recipient_id",
                               label = T("To Person"),
                               ondelete = "SET NULL",
                               represent = self.pr_person_phone_represent,
                               comment = self.pr_person_comment(child="recipient_id"),
                               ),
                     Field("transport_type",
                           label = T("Type of Transport"),
                           readable = show_transport,
                           writable = show_transport,
                           represent = s3_string_represent,
                           ),
                     Field("transported_by",
                           label = T("Transported by"),
                           readable = show_transport,
                           writable = show_transport,
                           represent = s3_string_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Transported by"),
                                                           T("Freight company or organisation providing transport"))),
                           ),
                     Field("transport_ref",
                           label = T("Transport Reference"),
                           readable = show_transport,
                           writable = show_transport,
                           represent = s3_string_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Transport Reference"),
                                                           T("Consignment Number, Tracking Number, etc"))),
                           ),
                     Field("driver_name",
                           label = T("Name of Driver"),
                           represent = s3_string_represent,
                           ),
                     Field("driver_phone",
                           label = T("Driver Phone Number"),
                           represent = lambda v: v or "",
                           requires = IS_EMPTY_OR(s3_phone_requires),
                           ),
                     Field("vehicle_plate_no",
                           label = T("Vehicle Plate Number"),
                           represent = s3_string_represent,
                           ),
                     Field("time_in", "time",
                           label = T("Time In"),
                           represent = s3_string_represent,
                           readable = time_in,
                           writable = time_in,
                           ),
                     Field("time_out", "time",
                           label = T("Time Out"),
                           represent = s3_string_represent,
                           ),
                     s3_datetime(label = T("Date Sent"),
                                 # Not always sent straight away
                                 #default = "now",
                                 represent = "date",
                                 writable = False,
                                 ),
                     s3_datetime("delivery_date",
                                 label = T("Estimated Delivery Date"),
                                 represent = "date",
                                 writable = False,
                                 ),
                     Field("status", "integer",
                           default = SHIP_STATUS_IN_PROCESS,
                           label = T("Status"),
                           represent = lambda opt: \
                            shipment_status.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(shipment_status)
                                      ),
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Filter Widgets
        filter_widgets = [
            S3TextFilter(["sender_id$first_name",
                          "sender_id$middle_name",
                          "sender_id$last_name",
                          "comments",
                          "site_id$name",
                          "send_ref",
                          "recipient_id$first_name",
                          "recipient_id$middle_name",
                          "recipient_id$last_name",
                         ],
                         label = T("Search"),
                         comment = T("Search for an item by text."),
                        ),
            S3OptionsFilter("to_site_id",
                            label = T("To Organization"),
                            comment = T("If none are selected, then all are searched."),
                            cols = 2,
                            hidden = True,
                           ),
            S3TextFilter("type",
                         label = T("Shipment Type"),
                         hidden = True,
                        ),
            S3TextFilter("transport_type",
                         label = T("Type of Transport"),
                         hidden = True,
                        ),
            S3DateFilter("date",
                         label = T("Date Sent"),
                         comment = T("Search for a shipment sent between these dates."),
                         hidden = True,
                        ),
            S3DateFilter("delivery_date",
                         label = T("Estimated Delivery Date"),
                         comment = T("Search for a shipment which has an estimated delivery between these dates."),
                         hidden = True,
                        ),
        ]

        # CRUD strings
        ADD_SEND = T("Send New Shipment")
        crud_strings[tablename] = Storage(
            label_create = ADD_SEND,
            title_display = T("Sent Shipment Details"),
            title_list = T("Sent Shipments"),
            title_update = T("Shipment to Send"),
            label_list_button = T("List Sent Shipments"),
            label_delete_button = T("Delete Sent Shipment"),
            msg_record_created = T("Shipment Created"),
            msg_record_modified = T("Sent Shipment updated"),
            msg_record_deleted = T("Sent Shipment canceled"),
            msg_list_empty = T("No Sent Shipments"))

        # Reusable Field
        send_id = S3ReusableField("send_id", "reference %s" % tablename,
                                  label = T("Send Shipment"),
                                  ondelete = "RESTRICT",
                                  represent = self.inv_send_represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "inv_send.id",
                                                          self.inv_send_represent,
                                                          orderby="inv_send_id.date",
                                                          sort=True)),
                                  sortby = "date",
                                  )

        # Components
        add_components(tablename,
                       inv_track_item = "send_id",
                       )

        # Custom methods
        # Generate Consignment Note
        set_method("inv", "send",
                   method="form",
                   action=self.inv_send_form)

        set_method("inv", "send",
                   method= "timeline",
                   action = self.inv_timeline)

        # Redirect to the Items tabs after creation
        if current.request.controller == "req":
            c = "req"
        else:
            c = "inv"
        send_item_url = URL(c=c, f="send", args=["[id]",
                                                 "track_item"])

        list_fields = ["id",
                       "send_ref",
                       "req_ref",
                       "sender_id",
                       "site_id",
                       "date",
                       "recipient_id",
                       "delivery_date",
                       "to_site_id",
                       "status",
                       "driver_name",
                       "driver_phone",
                       "vehicle_plate_no",
                       "time_out",
                       "comments"
                       ]
        if time_in:
            list_fields.insert(12, "time_in")
        if show_transport:
            list_fields.insert(10, "transport_type")
        configure(tablename,
                  # It shouldn't be possible for the user to delete a send item
                  # unless *maybe* if it is pending and has no items referencing it
                  deletable = False,
                  filter_widgets = filter_widgets,
                  onaccept = self.inv_send_onaccept,
                  onvalidation = self.inv_send_onvalidation,
                  create_next = send_item_url,
                  update_next = send_item_url,
                  list_fields = list_fields,
                  orderby = "inv_send.date desc",
                  sortby = [[5, "desc"], [1, "asc"]],
                  )

        # ---------------------------------------------------------------------
        # Received (In/Receive / Donation / etc)
        #
        ship_doc_status = { SHIP_DOC_PENDING  : T("Pending"),
                            SHIP_DOC_COMPLETE : T("Complete") }

        recv_type_opts = settings.get_inv_shipment_types()
        recv_type_opts.update(settings.get_inv_recv_types())

        radio_widget = lambda field, value: \
                              RadioWidget().widget(field, value, cols = 2)

        tablename = "inv_recv"
        define_table(tablename,
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("site_id", "org_site",
                                label = T("%(site)s (Recipient)") % dict(site=SITE_LABEL),
                                ondelete = "SET NULL",
                                instance_types = auth.org_site_types,
                                updateable = True,
                                not_filterby = "obsolete",
                                not_filter_opts = (True,),
                                default = user.site_id if is_logged_in() else None,
                                readable = True,
                                writable = True,
                                empty = False,
                                represent = org_site_represent,
                                #widget = S3SiteAutocompleteWidget(),
                                ),
                     Field("type", "integer",
                           requires = IS_IN_SET(recv_type_opts),
                           represent = lambda opt: \
                           recv_type_opts.get(opt, UNKNOWN_OPT),
                           label = T("Shipment Type"),
                           default = 0,
                           ),
                     organisation_id(label = T("Organization/Supplier")
                                     ),
                     # This is a reference, not a super-link, so we can override
                     Field("from_site_id", "reference org_site",
                           label = T("From %(site)s") % dict(site=SITE_LABEL),
                           ondelete = "SET NULL",
                           #widget = S3SiteAutocompleteWidget(),
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "org_site.site_id",
                                                  lambda id, row: \
                                                  org_site_represent(id, row,
                                                                     show_link = False),
                                                  sort=True,
                                                  not_filterby = "obsolete",
                                                  not_filter_opts = (True,),
                                                  )),
                           represent = org_site_represent
                           ),
                     s3_date("eta",
                             label = T("Date Expected"),
                             writable = False),
                     s3_datetime(label = T("Date Received"),
                                 represent = "date",
                                 # Can also be set manually (when catching up with backlog of paperwork)
                                 #comment = DIV(_class="tooltip",
                                 #              _title="%s|%s" % (T("Date Received"),
                                 #                                T("Will be filled automatically when the Shipment has been Received"))),
                                 ),
                     send_ref(),
                     recv_ref(),
                     purchase_ref(),
                     req_ref(readable=show_req_ref,
                             writable=show_req_ref
                             ),
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
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(shipment_status)
                                        ),
                           represent = lambda opt: \
                           shipment_status.get(opt, UNKNOWN_OPT),
                           default = SHIP_STATUS_IN_PROCESS,
                           label = T("Status"),
                           writable = False,
                           ),
                     Field("grn_status", "integer",
                           requires = IS_EMPTY_OR(
                                       IS_IN_SET(ship_doc_status)
                                       ),
                           represent = lambda opt: \
                           ship_doc_status.get(opt, UNKNOWN_OPT),
                           default = SHIP_DOC_PENDING,
                           widget = radio_widget,
                           label = T("%(GRN)s Status") % \
                           dict(GRN=settings.get_inv_recv_shortname()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % \
                                               (T("%(GRN)s Status") % dict(GRN=settings.get_inv_recv_shortname()),
                                                T("Has the %(GRN)s (%(GRN_name)s) form been completed?") % \
                                                dict(GRN=settings.get_inv_recv_shortname(),
                                                                                                                            GRN_name=settings.get_inv_recv_form_name()))),
                           ),
                     Field("cert_status", "integer",
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(ship_doc_status)
                                       ),
                           represent = lambda opt: \
                           ship_doc_status.get(opt, UNKNOWN_OPT),
                           default = SHIP_DOC_PENDING,
                           widget = radio_widget,
                           label = T("Certificate Status"),
                           comment = DIV(_class="tooltip",
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

        # Reusable Field
        recv_id = S3ReusableField("recv_id", "reference %s" % tablename,
                                  label = recv_id_label,
                                  ondelete = "RESTRICT",
                                  represent = self.inv_recv_represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "inv_recv.id",
                                                          self.inv_recv_represent,
                                                          orderby="inv_recv.date",
                                                          sort=True)),
                                  sortby = "date",
                                  )

        # Search Method
        if settings.get_inv_shipment_name() == "order":
            recv_search_comment = T("Search for an order by looking for text in any field.")
            recv_search_date_field = "eta"
            recv_search_date_comment = T("Search for an order expected between these dates")
        else:
            recv_search_comment = T("Search for a shipment by looking for text in any field.")
            recv_search_date_field = "date"
            recv_search_date_comment = T("Search for a shipment received between these dates")

        # @todo: make lazy_table
        table = db[tablename]
        filter_widgets = [
            S3TextFilter(["sender_id$first_name",
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
                         ],
                         label = T("Search"),
                         comment = recv_search_comment,
                        ),
            S3DateFilter(recv_search_date_field,
                         label = table[recv_search_date_field].label,
                         comment = recv_search_date_comment,
                         hidden = True,
                        ),
            S3OptionsFilter("site_id",
                            label = SITE_LABEL,
                            cols = 2,
                            hidden = True,
                           ),
            S3OptionsFilter("status",
                            label = T("Status"),
                            cols = 2,
                            hidden = True,
                           ),
            #S3OptionsFilter("grn_status",
                            #label = T("GRN Status"),
                            #cols = 2,
                            #hidden = True,
                           #),
            #S3OptionsFilter("cert_status",
                            #label = T("Certificate Status"),
                            #cols = 2,
                            #hidden = True,
                           #),
        ]

        # Redirect to the Items tabs after creation
        recv_item_url = URL(c="inv", f="recv", args=["[id]",
                                                     "track_item"])

        configure(tablename,
                  # it shouldn't be possible for the user to delete a send item
                  deletable=False,
                  list_fields = ["id",
                                 "recv_ref",
                                 "send_ref",
                                 "purchase_ref",
                                 "recipient_id",
                                 "organisation_id",
                                 "from_site_id",
                                 "site_id",
                                 "date",
                                 "type",
                                 "status",
                                 "req_ref",
                                 "sender_id",
                                 "comments"
                                 ],
                  mark_required = ("from_site_id", "organisation_id"),
                  onvalidation = self.inv_recv_onvalidation,
                  onaccept = self.inv_recv_onaccept,
                  filter_widgets = filter_widgets,
                  create_next = recv_item_url,
                  update_next = recv_item_url,
                  orderby="inv_recv.date desc",
                  sortby=[[6, "desc"], [1, "asc"]])

        # Components
        add_components(tablename,
                       inv_track_item = "recv_id",
                       )

        # Custom methods
        # Print Forms
        set_method("inv", "recv",
                   method = "form",
                   action = self.inv_recv_form)

        set_method("inv", "recv",
                   method = "cert",
                   action = self.inv_recv_donation_cert )

        set_method("inv", "recv",
                   method = "timeline",
                   action = self.inv_timeline)

        # ---------------------------------------------------------------------
        # Kits
        # - actual Kits in stock
        #
        tablename = "inv_kit"
        define_table(tablename,
                     Field("site_id", "reference org_site",
                           label = T("By %(site)s") % dict(site=SITE_LABEL),
                           requires = IS_ONE_OF(db, "org_site.site_id",
                                                lambda id, row: \
                                                org_site_represent(id, row,
                                                                   show_link=False),
                                                instance_types = auth.org_site_types,
                                                updateable = True,
                                                sort=True,
                                                ),
                           default = user.site_id if is_logged_in() else None,
                           readable = True,
                           writable = True,
                           widget = S3SiteAutocompleteWidget(),
                           represent = org_site_represent,
                           comment = S3AddResourceLink(
                                c="inv",
                                f="warehouse",
                                label=T("Create Warehouse"),
                                title=T("Warehouse"),
                                tooltip=T("Type the name of an existing site OR Click 'Create Warehouse' to add a new warehouse.")),
                            ),
                     item_id(label = T("Kit"),
                             requires = IS_ONE_OF(db, "supply_item.id",
                                                  self.supply_item_represent,
                                                  filterby="kit",
                                                  filter_opts=(True,),
                                                  sort=True),
                             widget = S3AutocompleteWidget("supply", "item",
                                                           filter="item.kit=1"),
                             # Needs better workflow as no way to add the Kit Items
                             #comment = S3AddResourceLink(
                             #   c="supply",
                             #   f="item",
                             #   label=T("Create Kit"),
                             #   title=T("Kit"),
                             #   tooltip=T("Type the name of an existing catalog kit OR Click 'Create Kit' to add a kit which is not in the catalog.")),
                             comment = DIV(_class="tooltip",
                                           _title="%s|%s" % (T("Kit"),
                                                             T("Type the name of an existing catalog kit"))),
                                ),
                     Field("quantity", "double",
                           label = T("Quantity"),
                           represent = lambda v, row=None: \
                           IS_FLOAT_AMOUNT.represent(v, precision=2)
                           ),
                     s3_date(comment = DIV(_class="tooltip",
                                           _title="%s|%s" % \
                                           (T("Date Repacked"),
                                            T("Will be filled automatically when the Item has been Repacked")))
                             ),
                     req_ref(writable = True),
                     person_id(name = "repacked_id",
                               label = T("Repacked By"),
                               ondelete = "SET NULL",
                               default = auth.s3_logged_in_person(),
                               #comment = self.pr_person_comment(child="repacked_id")),
                               ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_KIT = T("Create Kit")
        crud_strings[tablename] = Storage(
            label_create = ADD_KIT,
            title_display = T("Kit Details"),
            title_list = T("Kits"),
            title_update = T("Kit"),
            label_list_button = T("List Kits"),
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
        inv_item_status_opts = self.inv_item_status_opts

        tablename = "inv_track_item"
        define_table(tablename,
                     organisation_id(name = "track_org_id",
                                     label = T("Shipping Organization"),
                                     ondelete = "SET NULL",
                                     readable = False,
                                     writable = False
                                     ),
                     inv_item_id(name="send_inv_item_id",
                                 ondelete = "RESTRICT",
                                 # Local Purchases don't have this available
                                 requires = IS_EMPTY_OR(
                                              IS_ONE_OF(db, "inv_inv_item.id",
                                                        self.inv_item_represent,
                                                        orderby="inv_inv_item.id",
                                                        sort=True)),
                                 script = '''
$.filterOptionsS3({
 'trigger':'send_inv_item_id',
 'target':'item_pack_id',
 'lookupResource':'item_pack',
 'lookupPrefix':'supply',
 'lookupURL':S3.Ap.concat('/inv/inv_item_packs/'),
 'msgNoRecords':i18n.no_packs,
 'fncPrep':S3.supply.fncPrepItem,
 'fncRepresent':S3.supply.fncRepresentItem
})'''),
                     item_id(ondelete = "RESTRICT"),
                     item_pack_id(ondelete = "SET NULL"),
                     # Now done as a VirtualField instead (looks better & updates closer to real-time, so less of a race condition)
                     #Field("req_quantity", "double",
                     #      # This isn't the Quantity requested, but rather the quantity still needed
                     #      label = T("Quantity Needed"),
                     #      readable = False,
                     #      writable = False),
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
                     s3_date("expiry_date",
                             label = T("Expiry Date")),
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
                           label = self.inv_itn_label,
                           represent = s3_string_represent),
                     # original donating org
                     organisation_id(name = "supply_org_id",
                                     label = T("Supplier/Donor"),
                                     ondelete = "SET NULL"),
                     # which org owns this item
                     organisation_id(name = "owner_org_id",
                                     label = T("Owned By (Organization/Branch)"),
                                     ondelete = "SET NULL"),
                     Field("inv_item_status", "integer",
                           label = T("Item Status"),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(inv_item_status_opts)
                                        ),
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
                     self.inv_adj_item_id(ondelete = "RESTRICT"), # any adjustment record
                     # send record
                     send_id(),
                     # receive record
                     recv_id(),
                     req_item_id(readable=False,
                                 writable=False),
                     Field.Method("total_value",
                                  self.inv_track_item_total_value),
                     Field.Method("pack_quantity",
                                  self.supply_item_pack_quantity(tablename=tablename)),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        ADD_TRACK_ITEM = T("Add Item to Shipment")
        crud_strings[tablename] = Storage(
            label_create = ADD_TRACK_ITEM,
            title_display = T("Shipment Item Details"),
            title_list = T("Shipment Items"),
            title_update = T("Edit Shipment Item"),
            label_list_button = T("List Shipment Items"),
            label_delete_button = T("Delete Shipment Item"),
            msg_record_created = T("Item Added to Shipment"),
            msg_record_modified = T("Shipment Item updated"),
            msg_record_deleted = T("Shipment Item deleted"),
            msg_list_empty = T("No Shipment Items"))

        # Filter Widgets
        filter_widgets = [
            S3TextFilter(["item_id$name",
                          "send_id$site_id$name",
                          "recv_id$site_id$name",
                         ],
                         label = T("Search"),
                         #comment = recv_search_comment,
                        ),
            S3DateFilter("send_id$date",
                         label = T("Sent date"),
                         hidden = True,
                        ),
            S3DateFilter("recv_id$date",
                         label = T("Received date"),
                         hidden = True,
                        ),
        ]

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
                  filter_widgets = filter_widgets,
                  onaccept = self.inv_track_item_onaccept,
                  onvalidation = self.inv_track_item_onvalidate,
                  extra_fields = ["quantity", "pack_value", "item_pack_id"],
                 )

        #---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(inv_send_controller = self.inv_send_controller,
                    inv_send_onaccept = self.inv_send_onaccept,
                    inv_send_process = self.inv_send_process,
                    inv_track_item_deleting = self.inv_track_item_deleting,
                    inv_track_item_onaccept = self.inv_track_item_onaccept,
                    )

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_track_item_total_value(row):
        """ Total value of a track item """

        if hasattr(row, "inv_track_item"):
            row = row.inv_track_item
        try:
            v = row.quantity * row.pack_value
            return v
        except:
            # not available
            return current.messages["NONE"]

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_track_item_quantity_needed(row):
        """
            Quantity still needed for a track item - used in Inv Send
            when an Item has come from a Request
        """

        if hasattr(row, "inv_track_item"):
            row = row.inv_track_item
        try:
            req_item_id = row.req_item_id
        except:
            # not available
            req_item_id = None

        if not req_item_id:
            return current.messages["NONE"]

        s3db = current.s3db

        ritable = s3db.req_req_item
        siptable = s3db.supply_item_pack

        query = (ritable.id == req_item_id) & \
                (ritable.item_pack_id == siptable.id)

        row = current.db(query).select(ritable.quantity,
                                       ritable.quantity_transit,
                                       ritable.quantity_fulfil,
                                       siptable.quantity).first()

        if row:
            rim = row.req_req_item

            quantity_shipped = max(rim.quantity_transit,
                                   rim.quantity_fulfil)

            quantity_needed = (rim.quantity - quantity_shipped) * \
                               row.supply_item_pack.quantity
        else:
            return current.messages["NONE"]

        return quantity_needed

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_send_represent(id, row=None, show_link=True):
        """
            Represent a Sent Shipment
        """

        if row:
            id = row.id
            table = current.db.inv_send
        elif not id:
            return current.messages["NONE"]
        else:
            db = current.db
            table = db.inv_send
            row = db(table.id == id).select(table.date,
                                            table.send_ref,
                                            table.to_site_id,
                                            limitby=(0, 1)).first()
        try:
            send_ref_string = table.send_ref.represent(row.send_ref,
                                                       show_link=False)
            to_string = table.to_site_id.represent(row.to_site_id,
                                                   show_link=False)
            date_string = table.date.represent(row.date)

            T = current.T
            represent  = "%s (%s: %s %s %s)" % (send_ref_string,
                                                T("To"),
                                                to_string,
                                                T("on"),
                                                date_string)
            if show_link:
                return A(represent,
                         _href = URL(c="inv", f="send", args=[id]))
            else:
                return represent
        except:
            return current.messages.UNKNOWN_OPT

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
            inv_track_item_onaccept = current.s3db.inv_track_item_onaccept
            site_id = vars.site_id
            itable = db.inv_inv_item
            tracktable = db.inv_track_item
            query = (itable.site_id == site_id) & \
                    (itable.status == int(type))
            rows = db(query).select()
            for row in rows:
                if row.quantity != 0:
                    # Insert inv_item to inv_track_item
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
                    inv_track_item_onaccept(Storage(vars=vars))

        stable = db.inv_send
        # If the send_ref is None then set it up
        record = stable[id]
        if not record.send_ref:
            code = current.s3db.supply_get_shipping_code(
                    current.deployment_settings.get_inv_send_shortname(),
                    record.site_id,
                    stable.send_ref,
                  )
            db(stable.id == id).update(send_ref=code)

    # -------------------------------------------------------------------------
    @classmethod
    def inv_send_controller(cls):
        """
           RESTful CRUD controller for inv_send
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        sendtable = s3db.inv_send
        tracktable = s3db.inv_track_item

        request = current.request
        response = current.response
        s3 = response.s3

        # Limit site_id to sites the user has permissions for
        error_msg = T("You do not have permission for any facility to send a shipment.")
        current.auth.permitted_facilities(table=sendtable, error_msg=error_msg)

        # Set Validator for checking against the number of items in the warehouse
        vars = request.vars
        send_inv_item_id = vars.send_inv_item_id
        if send_inv_item_id:
            if not vars.item_pack_id:
                iitable = s3db.inv_inv_item
                vars.item_pack_id = db(iitable.id == send_inv_item_id).select(iitable.item_pack_id,
                                                                              limitby=(0, 1)
                                                                              ).first().item_pack_id
            s3db.inv_track_item.quantity.requires = QUANTITY_INV_ITEM(db,
                                                                      send_inv_item_id,
                                                                      vars.item_pack_id)

        def set_send_attr(status):
            sendtable.send_ref.writable = False
            if status == SHIP_STATUS_IN_PROCESS:
                sendtable.send_ref.readable = False
            else:
                # Make all fields writable False
                for field in sendtable.fields:
                    sendtable[field].writable = False

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
                #tracktable.req_quantity.readable = True
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
            record = db(sendtable.id == r.id).select(sendtable.status,
                                                     sendtable.req_ref,
                                                     limitby=(0, 1)
                                                     ).first()
            if record:
                status = record.status
                if status != SHIP_STATUS_IN_PROCESS:
                    # Now that the shipment has been sent,
                    # lock the record so that it can't be meddled with
                    s3db.configure("inv_send",
                                   create=False,
                                   listadd=False,
                                   editable=False,
                                   deletable=False,
                                   )

            if r.component:
                record = r.record
                values = current.deployment_settings.get_inv_track_pack_values()
                if status in (SHIP_STATUS_RECEIVED, SHIP_STATUS_CANCEL):
                    list_fields = ["id",
                                   "status",
                                   "item_id",
                                   "item_pack_id",
                                   "bin",
                                   "quantity",
                                   "recv_quantity",
                                   "return_quantity",
                                   "owner_org_id",
                                   "supply_org_id",
                                   "inv_item_status",
                                   "comments",
                                   ]
                    if values:
                        list_fields.insert(7, "pack_value")
                        list_fields.insert(7, "currency")
                elif status == SHIP_STATUS_RETURNING:
                    list_fields = ["id",
                                   "status",
                                   "item_id",
                                   "item_pack_id",
                                   "quantity",
                                   "return_quantity",
                                   "bin",
                                   "owner_org_id",
                                   "supply_org_id",
                                   "inv_item_status",
                                   ]
                    if values:
                        list_fields.insert(5, "pack_value")
                        list_fields.insert(5, "currency")
                else:
                    list_fields = ["id",
                                   "status",
                                   "item_id",
                                   "item_pack_id",
                                   "quantity",
                                   "bin",
                                   "owner_org_id",
                                   "supply_org_id",
                                   "inv_item_status",
                                   ]
                    if values:
                        list_fields.insert(6, "pack_value")
                        list_fields.insert(6, "currency")
                    if record.req_ref and r.interactive:
                        s3db.configure("inv_track_item",
                                       extra_fields = ["req_item_id"])
                        tracktable.quantity_needed = \
                            Field.Method("quantity_needed",
                                         cls.inv_track_item_quantity_needed)
                        list_fields.insert(4, (T("Quantity Needed"),
                                               "quantity_needed"))

                s3db.configure("inv_track_item", list_fields=list_fields)

                # Can only create or delete track items for a send record if the status is preparing
                method = r.method
                if method in ("create", "delete"):
                    if status != SHIP_STATUS_IN_PROCESS:
                        return False
                    if method == "delete":
                        return s3.inv_track_item_deleting(r.component_id)
                if record.get("site_id"):
                    # Restrict to items from this facility only
                    tracktable.send_inv_item_id.requires = IS_ONE_OF(db, "inv_inv_item.id",
                                                                     s3db.inv_item_represent,
                                                                     filterby = "site_id",
                                                                     filter_opts = (record.site_id,),
                                                                     not_filterby = "quantity",
                                                                     not_filter_opts = (0,),
                                                                     orderby = "inv_inv_item.id",
                                                                     sort = True,
                                                                     )
                # Hide the values that will be copied from the inv_inv_item record
                if r.component_id:
                    track_record = db(tracktable.id == r.component_id).select(tracktable.req_item_id,
                                                                              tracktable.send_inv_item_id,
                                                                              tracktable.item_pack_id,
                                                                              tracktable.status,
                                                                              tracktable.quantity,
                                                                              limitby=(0, 1)).first()
                    set_track_attr(track_record.status)
                    # If the track record is linked to a request item then
                    # the stock item has already been selected so make it read only
                    if track_record and track_record.get("req_item_id"):
                        tracktable.send_inv_item_id.writable = False
                        tracktable.item_pack_id.writable = False
                        stock_qnty = track_record.quantity
                        tracktable.quantity.comment = T("%(quantity)s in stock") % dict(quantity=stock_qnty)
                        tracktable.quantity.requires = QUANTITY_INV_ITEM(db,
                                                                         track_record.send_inv_item_id,
                                                                         track_record.item_pack_id)
                    # Hide the item id
                    tracktable.item_id.readable = False
                else:
                    set_track_attr(TRACK_STATUS_PREPARING)
                if r.interactive:
                    crud_strings = s3.crud_strings.inv_send
                    if record.status == SHIP_STATUS_IN_PROCESS:
                        crud_strings.title_update = \
                        crud_strings.title_display = T("Process Shipment to Send")
                    elif "site_id" in request.vars and status == SHIP_STATUS_SENT:
                        crud_strings.title_update = \
                        crud_strings.title_display = T("Review Incoming Shipment to Receive")
            else:
                if r.id and request.get_vars.get("received", None):
                    # "received" must not propagate:
                    del request.get_vars["received"]
                    # Set the items to being received
                    # @ToDo: Check Permissions & Avoid DB updates in GETs
                    db(sendtable.id == r.id).update(status = SHIP_STATUS_RECEIVED)
                    db(tracktable.send_id == r.id).update(status = TRACK_STATUS_ARRIVED)
                    req_ref = record.req_ref
                    if req_ref:
                        # Update the Request Status
                        rtable = s3db.req_req
                        req_id = db(rtable.req_ref == req_ref).select(rtable.id,
                                                                      limitby=(0, 1)).first()
                        # Get the full list of items in the request
                        ritable = s3db.req_req_item
                        query = (ritable.req_id == req_id) & \
                                (ritable.deleted == False)
                        ritems = db(query).select(ritable.id,
                                                  ritable.item_pack_id,
                                                  ritable.quantity,
                                                  # Virtual Field
                                                  #ritable.pack_quantity,
                                                  )
                        # Get all Received Shipments in-system for this request
                        query = (sendtable.status == SHIP_STATUS_RECEIVED) & \
                                (sendtable.req_ref == req_ref) & \
                                (tracktable.send_id == r.id) & \
                                (tracktable.deleted == False)
                        sitems = db(query).select(tracktable.item_pack_id,
                                                  tracktable.quantity,
                                                  # Virtual Field
                                                  #tracktable.pack_quantity,
                                                  )
                        fulfil_qty = {}
                        for item in sitems:
                            item_pack_id = item.item_pack_id
                            if item_pack_id in fulfil_qty:
                                fulfil_qty[item_pack_id] += (item.quantity * item.pack_quantity())
                            else:
                                fulfil_qty[item_pack_id] = (item.quantity * item.pack_quantity())
                        complete = False
                        for item in ritems:
                            if item.item_pack_id in fulfil_qty:
                                quantity_fulfil = fulfil_qty[item.item_pack_id]
                                db(ritable.id == item.id).update(quantity_fulfil=quantity_fulfil)
                                req_quantity = item.quantity * item.pack_quantity()
                                if quantity_fulfil >= req_quantity:
                                    complete = True
                                else:
                                    complete = False

                        # Update overall Request Status
                        if complete:
                            # REQ_STATUS_COMPLETE
                            db(rtable.id == req_id).update(fulfil_status=2)
                        else:
                            # REQ_STATUS_PARTIAL
                            db(rtable.id == req_id).update(fulfil_status=1)
                    response.confirmation = T("Shipment received")
                # else set the inv_send attributes
                elif r.id:
                    record = db(sendtable.id == r.id).select(sendtable.status,
                                                             limitby=(0, 1)).first()
                    set_send_attr(record.status)
                else:
                    set_send_attr(SHIP_STATUS_IN_PROCESS)
                    sendtable.send_ref.readable = False
            return True

        args = request.args
        if len(args) > 1 and args[1] == "track_item":
            # Shouldn't fail but...
            # if user enters the send id then it could so wrap in a try...
            try:
                status = db(sendtable.id == args[0]).select(sendtable.status,
                                                            limitby=(0, 1)).status
            except:
                status = None
            if status:
                editable = False
                if status == SHIP_STATUS_RETURNING:
                    editable = True
                # remove CRUD generated buttons in the tabs
                s3db.configure("inv_track_item",
                               create = False,
                               deletable = False,
                               editable = editable,
                               listadd = False,
                               )

        s3.prep = prep
        output = current.rest_controller("inv", "send",
                                         rheader = inv_send_rheader)
        return output

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_send_process():
        """
            Process a Shipment
        """

        request = current.request
        try:
            send_id = request.args[0]
        except:
            redirect(URL(f="send"))

        T = current.T
        auth = current.auth
        db = current.db
        s3db = current.s3db
        stable = db.inv_send

        session = current.session

        if not auth.s3_has_permission("update", stable, record_id=send_id):
            session.error = T("You do not have permission to send this shipment.")

        send_record = db(stable.id == send_id).select(stable.status,
                                                      stable.sender_id,
                                                      stable.send_ref,
                                                      stable.req_ref,
                                                      stable.site_id,
                                                      stable.delivery_date,
                                                      stable.recipient_id,
                                                      stable.to_site_id,
                                                      stable.comments,
                                                      limitby=(0, 1)).first()

        if send_record.status != SHIP_STATUS_IN_PROCESS:
            session.error = T("This shipment has already been sent.")

        tracktable = db.inv_track_item
        siptable = s3db.supply_item_pack
        rrtable = s3db.req_req
        ritable = s3db.req_req_item

        # Get the track items that are part of this shipment
        query = (tracktable.send_id == send_id ) & \
                (tracktable.deleted == False)
        track_items = db(query).select(tracktable.req_item_id,
                                       tracktable.quantity,
                                       tracktable.item_pack_id)
        if not track_items:
            session.error = T("No items have been selected for shipping.")

        if session.error:
            redirect(URL(f = "send",
                         args = [send_id]))

        # Update Send record & lock for editing
        system_roles = auth.get_system_roles()
        ADMIN = system_roles.ADMIN
        db(stable.id == send_id).update(date = request.utcnow,
                                        status = SHIP_STATUS_SENT,
                                        owned_by_user = None,
                                        owned_by_group = ADMIN)

        # If this is linked to a request then update the quantity in transit
        req_ref = send_record.req_ref
        req_rec = db(rrtable.req_ref == req_ref).select(rrtable.id,
                                                        limitby=(0, 1)).first()
        if req_rec:
            req_id = req_rec.id
            for track_item in track_items:
                req_item_id = track_item.req_item_id
                if req_item_id:
                    req_pack_id = db(ritable.id == req_item_id).select(ritable.item_pack_id,
                                                                       limitby=(0, 1)
                                                                       ).first().item_pack_id
                    req_p_qnty = db(siptable.id == req_pack_id).select(siptable.quantity,
                                                                       limitby=(0, 1)
                                                                       ).first().quantity
                    t_qnty = track_item.quantity
                    t_pack_id = track_item.item_pack_id
                    inv_p_qnty = db(siptable.id == t_pack_id).select(siptable.quantity,
                                                                     limitby=(0, 1)
                                                                     ).first().quantity
                    transit_quantity = t_qnty * inv_p_qnty / req_p_qnty
                    db(ritable.id == req_item_id).update(quantity_transit = ritable.quantity_transit + transit_quantity)
            s3db.req_update_status(req_id)

        # Create a Receive record
        rtable = s3db.inv_recv
        recv_id = rtable.insert(sender_id = send_record.sender_id,
                                send_ref = send_record.send_ref,
                                req_ref = req_ref,
                                from_site_id = send_record.site_id,
                                eta = send_record.delivery_date,
                                recipient_id = send_record.recipient_id,
                                site_id = send_record.to_site_id,
                                comments = send_record.comments,
                                status = SHIP_STATUS_SENT,
                                type = 1, # 1:"Another Inventory"
                                )

        # Change the status for all track items in this shipment to In transit
        # and link to the receive record
        db(tracktable.send_id == send_id).update(status = 2,
                                                 recv_id = recv_id)

        session.confirmation = T("Shipment Items sent from Warehouse")
        if req_rec:
            session.confirmation = T("Request Status updated")
        redirect(URL(f = "send",
                     args = [send_id, "track_item"]))

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_send_form(r, **attr):
        """
            Generate a PDF of a Waybill
        """

        db = current.db
        table = db.inv_send
        tracktable = db.inv_track_item
        table.date.readable = True

        record = db(table.id == r.id).select(table.send_ref,
                                             limitby=(0, 1)).first()
        send_ref = record.send_ref
        # hide the inv_item field
        tracktable.send_inv_item_id.readable = False
        tracktable.recv_inv_item_id.readable = False

        T = current.T
        list_fields = [(T("Item Code"), "item_id$code"),
                       "item_id",
                       (T("Weight (kg)"), "item_id$weight"),
                       (T("Volume (m3)"), "item_id$volume"),
                       "bin",
                       "item_source_no",
                       "item_pack_id",
                       "quantity",
                       ]
        settings = current.deployment_settings
        if r.record.req_ref:
            # This Shipment relates to a request
            # - show the req_item comments
            list_fields.append("req_item_id$comments")
        if settings.get_inv_track_pack_values():
            list_fields + ["currency",
                           "pack_value",
                           ]
        from s3.s3export import S3Exporter
        exporter = S3Exporter().pdf
        return exporter(r.resource,
                        request = r,
                        method = "list",
                        pdf_componentname = "track_item",
                        pdf_title = settings.get_inv_send_form_name(),
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
    def inv_recv_represent(id, row=None, show_link=True):
        """
            Represent a Received Shipment
        """

        if row:
            id = row.id
            table = current.db.inv_recv
        elif not id:
            return current.messages["NONE"]
        else:
            db = current.db
            table = db.inv_recv
            row = db(table.id == id).select(table.date,
                                            table.recv_ref,
                                            table.from_site_id,
                                            table.organisation_id,
                                            limitby=(0, 1)).first()

        recv_ref_string = table.send_ref.represent(row.recv_ref,
                                                   show_link=False)
        if row.from_site_id:
            from_string = table.from_site_id.represent(row.from_site_id,
                                                       show_link=False)
        else:
            from_string = table.organisation_id.represent(row.organisation_id,
                                                          show_link=False)
        date_string = table.date.represent(row.date)

        T = current.T
        represent  = "%s (%s: %s %s %s)" % (recv_ref_string,
                                            T("From"),
                                            from_string,
                                            T("on"),
                                            date_string)
        if show_link:
            return A(represent,
                     _href = URL(c="inv", f="recv", args=[id]))
        else:
            return represent

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
            code = current.s3db.supply_get_shipping_code(
                    current.deployment_settings.get_inv_recv_shortname(),
                    record.site_id,
                    rtable.recv_ref,
                )
            db(rtable.id == id).update(recv_ref = code)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_send_onvalidation(form):
        """
            Check that either organisation_id or to_site_id are filled according to the type
        """

        vars = form.vars
        if not vars.to_site_id and not vars.organisation_id:
            error = current.T("Please enter a %(site)s OR an Organization") % \
                              dict(site=current.deployment_settings.get_org_site_label())
            errors = form.errors
            errors.to_site_id = error
            errors.organisation_id = error

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_recv_onvalidation(form):
        """
            Check that either organisation_id or from_site_id are filled according to the type
            @ToDo: lookup the type values from s3cfg.py instead of hardcoding it
        """

        type = form.vars.type and int(form.vars.type)
        if type == 11 and not form.vars.from_site_id:
            # Internal Shipment needs from_site_id
            form.errors.from_site_id = current.T("Please enter a %(site)s") % \
                                            dict(site=current.deployment_settings.get_org_site_label())
        if type >= 32 and not form.vars.organisation_id:
            # Internal Shipment needs from_site_id
            form.errors.organisation_id = current.T("Please enter an Organization/Supplier")

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
        table.site_id.label = T("By %(site)s") % dict(site=current.deployment_settings.get_inv_facility_label())
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
        from s3.s3export import S3Exporter
        exporter = S3Exporter().pdf
        return exporter(r.resource,
                        request = r,
                        method = "list",
                        pdf_title = T(current.deployment_settings.get_inv_recv_form_name()),
                        pdf_filename = recv_ref,
                        list_fields = list_fields,
                        pdf_hide_comments = True,
                        pdf_componentname = "track_item",
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
        field.label = current.T("By %(site)s") % dict(site=current.deployment_settings.get_inv_facility_label())
        field.represent = current.s3db.org_site_represent

        record = table[r.id]
        site_id = record.site_id
        site = field.represent(site_id, False)

        from s3.s3export import S3Exporter
        exporter = S3Exporter().pdf
        return exporter(r.resource,
                        request=r,
                        method="list",
                        pdf_title="Donation Certificate",
                        pdf_filename="DC-%s" % site,
                        pdf_hide_comments=True,
                        pdf_componentname = "track_item",
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
                             _href = URL(c = "inv",
                                         f = "send",
                                         args = [row.id, "form"]
                                        ),
                            )
                else:
                    return value
            else:
                return value
        else:
            return current.messages["NONE"]

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
                         _href = URL(c = "inv",
                                     f = "recv",
                                     args = [recv_row.id, "form"]
                                     ),
                        )
            else:
                return B(value)
        else:
            return current.messages["NONE"]

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
            form.errors.quantity = current.T("You can only make %d kit(s) with the available stock") % \
                                        int(max_kits)

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
        siptable = db.supply_item_pack
        supply_item_add = s3db.supply_item_add
        form_vars = form.vars
        id = form_vars.id
        record = form.record

        if form_vars.send_inv_item_id:
            stock_item = db(inv_item_table.id == form_vars.send_inv_item_id).select(inv_item_table.id,
                                                                                    inv_item_table.quantity,
                                                                                    inv_item_table.item_pack_id,
                                                                                    limitby=(0, 1)).first()
        elif record:
            stock_item = record.send_inv_item_id
        else:
            # will get here for a recv (from external donor / local supplier)
            stock_item = None

        # Modify the original inv. item total only if we have a quantity on the form
        # and a stock item to take it from.
        # There will not be a quantity if it is being received since by then it is read only
        # It will be there on an import and so the value will be deducted correctly
        if form_vars.quantity and stock_item:
            stock_quantity = stock_item.quantity
            stock_pack = db(siptable.id == stock_item.item_pack_id).select(siptable.quantity,
                                                                           limitby=(0, 1)
                                                                           ).first().quantity
            if record:
                if record.send_inv_item_id != None:
                    # Items have already been removed from stock, so first put them back
                    old_track_pack_quantity = db(siptable.id == record.item_pack_id).select(siptable.quantity,
                                                                                            limitby=(0, 1)
                                                                                            ).first().quantity
                    stock_quantity = supply_item_add(stock_quantity,
                                                     stock_pack,
                                                     record.quantity,
                                                     old_track_pack_quantity
                                                     )
            try:
                new_track_pack_quantity = db(siptable.id == form_vars.item_pack_id).select(siptable.quantity,
                                                                                           limitby=(0, 1)
                                                                                           ).first().quantity
            except:
                new_track_pack_quantity = record.item_pack_id.quantity
            newTotal = supply_item_add(stock_quantity,
                                       stock_pack,
                                       - float(form_vars.quantity),
                                       new_track_pack_quantity
                                       )
            db(inv_item_table.id == stock_item).update(quantity = newTotal)
        if form_vars.send_id and form_vars.recv_id:
            send_ref = db(stable.id == form_vars.send_id).select(stable.send_ref,
                                                                 limitby=(0, 1)
                                                                 ).first().send_ref
            db(rtable.id == form_vars.recv_id).update(send_ref = send_ref)

        rrtable = s3db.table("req_req")
        if rrtable:
            use_req = True
            ritable = s3db.req_req_item
        else:
            # Req module deactivated
            use_req = False

        # If this item is linked to a request, then copy the req_ref to the send item
        if use_req and record and record.req_item_id:

            req_id = db(ritable.id == record.req_item_id).select(ritable.req_id,
                                                                 limitby=(0, 1)
                                                                 ).first().req_id
            req_ref = db(rrtable.id == req_id).select(rrtable.req_ref,
                                                      limitby=(0, 1)
                                                      ).first().req_ref
            db(stable.id == form_vars.send_id).update(req_ref = req_ref)
            if form_vars.recv_id:
                db(rtable.id == form_vars.recv_id).update(req_ref = req_ref)

        # If the status is 'unloading':
        # Move all the items into the site, update any request & make any adjustments
        # Finally change the status to 'arrived'
        if record and record.status == TRACK_STATUS_UNLOADING and \
                      record.recv_quantity:
            # Look for the item in the site already
            recv_rec = db(rtable.id == record.recv_id).select(rtable.site_id,
                                                              rtable.type,
                                                              ).first()
            recv_site_id = recv_rec.site_id
            query = (inv_item_table.site_id == recv_site_id) & \
                    (inv_item_table.item_id == record.item_id) & \
                    (inv_item_table.item_pack_id == record.item_pack_id) & \
                    (inv_item_table.currency == record.currency) & \
                    (inv_item_table.status == record.inv_item_status) & \
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
                if form_vars.send_inv_item_id:
                    source_type = db(inv_item_table.id == form_vars.send_inv_item_id).select(inv_item_table.source_type,
                                                                                             limitby=(0, 1)
                                                                                             ).first().source_type
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
            # If this item is linked to a request, then update the quantity fulfil
            if use_req and record.req_item_id:
                req_item = db(ritable.id == record.req_item_id).select(ritable.quantity_fulfil,
                                                                       ritable.item_pack_id,
                                                                       limitby=(0, 1)
                                                                       ).first()
                req_quantity = req_item.quantity_fulfil
                req_pack_quantity = db(siptable.id == req_item.item_pack_id).select(siptable.quantity,
                                                                                    limitby=(0, 1)
                                                                                    ).first().quantity
                track_pack_quantity = db(siptable.id == record.item_pack_id).select(siptable.quantity,
                                                                                    limitby=(0, 1)
                                                                                    ).first().quantity
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
                    adj_id = db(adjitemtable.id == adj_rec.adj_item_id).select(adjitemtable.adj_id,
                                                                               limitby=(0, 1)
                                                                               ).first().adj_id
                # If we don't yet have an adj record then create it
                else:
                    adjtable = s3db.inv_adj
                    irtable = s3db.inv_recv
                    recv_rec = db(irtable.id == record.recv_id).select(irtable.recipient_id,
                                                                       irtable.site_id,
                                                                       irtable.comments,
                                                                       limitby=(0, 1)).first()
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
                                                  old_pack_value = record.pack_value,
                                                  new_pack_value = record.pack_value,
                                                  expiry_date = record.expiry_date,
                                                  bin = record.recv_bin,
                                                  comments = record.comments,
                                                  )
                # Copy the adj_item_id to the tracking record
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

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_timeline(r, **attr):
        """
            Display the Incidents on a Simile Timeline

            http://www.simile-widgets.org/wiki/Reference_Documentation_for_Timeline

            @ToDo: Play button
            http://www.simile-widgets.org/wiki/Timeline_Moving_the_Timeline_via_Javascript
        """

        if r.representation == "html"  and  (r.name == "recv" or \
                                             r.name == "send"):

            T = current.T
            request = current.request
            response = current.response
            s3 = response.s3

            # Add core Simile Code
            s3.scripts.append("/%s/static/scripts/simile/timeline/timeline-api.js" % request.application)

            # Add our controlled script
            if s3.debug:
                s3.scripts.append("/%s/static/scripts/S3/s3.timeline.js" % request.application)
            else:
                s3.scripts.append("/%s/static/scripts/S3/s3.timeline.min.js" % request.application)
            # Add our data
            # @ToDo: Make this the initial data & then collect extra via REST with a stylesheet
            # add in JS using S3.timeline.eventSource.addMany(events) where events is a []

            db = current.db
            rows1 = db(db.inv_send.id > 0).select()     # select rows from inv_send
            rows2 = db(db.inv_recv.id > 0).select()     # select rows form inv_recv

            if r.record:
                # Single record
                rows = [r.record]
            else:
                # Multiple records
                # @ToDo: Load all records & sort to closest in time
                # http://stackoverflow.com/questions/7327689/how-to-generate-a-sequence-of-future-datetimes-in-python-and-determine-nearest-d
                r.resource.load(limit=2000)
                rows = r.resource._rows


            data = {"dateTimeFormat": "iso8601",
                    }

            now = request.utcnow
            tl_start = tl_end = now
            events = []
            if r.name is "send":
                rr = (rows, rows2)
            else:
                rr = (rows1, rows)
            for (row_send, row_recv) in itertools.izip_longest(rr[0], rr[0]):
                # send  Dates
                start = row_send.date  or ""
                if start:
                    if start < tl_start:
                        tl_start = start
                    if start > tl_end:
                        tl_end = start
                    start = start.isoformat()
                # recv date
                end = row_recv.date or ""
                if end:
                    if end > tl_end:
                        tl_end = end
                    end = end.isoformat()

                # append events
                events.append({"start": start,
                               "end": end,
                               #"title": row.name,
                               #"caption": row.comments or "",
                               #"description": row.comments or "",
                               # @ToDo: Colour based on Category (More generically: Resource or Resource Type)
                               # "color" : "blue",
                               })

            data["events"] = events
            data = json.dumps(data, separators=SEPARATORS)

            code = "".join((
'''S3.timeline.data=''', data, '''
S3.timeline.tl_start="''', tl_start.isoformat(), '''"
S3.timeline.tl_end="''', tl_end.isoformat(), '''"
S3.timeline.now="''', now.isoformat(), '''"
'''))

            # Control our code in static/scripts/S3/s3.timeline.js
            s3.js_global.append(code)

            # Create the DIV
            item = DIV(_id="s3timeline", _class="s3-timeline")

            output = dict(item = item)

            # Maintain RHeader for consistency
            if "rheader" in attr:
                rheader = attr["rheader"](r)
                if rheader:
                    output["rheader"] = rheader

            output["title"] = T("Incident Timeline")
            response.view = "timeline.html"
            return output

        else:
            raise HTTP(501, "bad method")
# =============================================================================
def inv_tabs(r):
    """
        Add an expandable set of Tabs for a Site's Inventory Tasks

        @ToDo: Make these Expand/Contract without a server-side call
    """

    settings = current.deployment_settings
    if settings.get_org_site_inv_req_tabs():
        if settings.has_module("inv") and \
           current.auth.s3_has_permission("read", "inv_inv_item", c="inv"):

            T = current.T
            s3 = current.session.s3

            collapse_tabs = settings.get_inv_collapse_tabs()
            tablename = s3_rheader_resource(r)[0]
            if collapse_tabs and not (tablename == "inv_warehouse"):
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
                            (T("Send"), "send"),
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

    return []

# =============================================================================
def inv_rheader(r):
    """ Resource Header for Warehouses and Inventory Items """

    if r.representation != "html" or r.method == "import":
        # RHeaders only used in interactive views
        return None

    # Need to use this format as otherwise req_match?viewing=org_office.x
    # doesn't have an rheader
    tablename, record = s3_rheader_resource(r)
    if not record:
        # List or Create form: rheader makes no sense here
        return None

    T = current.T
    s3db = current.s3db
    table = s3db.table(tablename)

    rheader = None
    if tablename == "inv_warehouse":

        # Tabs
        tabs = [(T("Basic Details"), None),
                #(T("Contact Data"), "contact"),
                ]
        settings = current.deployment_settings
        if settings.has_module("hrm"):
            STAFF = settings.get_hrm_staff_label()
            tabs.append((STAFF, "human_resource"))
            permit = current.auth.s3_has_permission
            if permit("create", "hrm_human_resource_site") and \
               permit("update", tablename, r.id):
                tabs.append((T("Assign %(staff)s") % dict(staff=STAFF), "assign"))
        if settings.has_module("asset"):
            tabs.insert(6,(T("Assets"), "asset"))
        tabs = tabs + s3db.inv_tabs(r)
        if settings.has_module("req"):
            tabs = tabs + s3db.req_tabs(r)
        tabs.append((T("Attachments"), "document"))
        tabs.append((T("User Roles"), "roles"))

        # Fields
        rheader_fields = [["name", "organisation_id", "email"],
                          ["location_id", "phone1"],
                          ]

        rheader = S3ResourceHeader(rheader_fields, tabs)
        rheader_fields, rheader_tabs = rheader(r, table=table, record=record)

        # Inject logo
        logo = s3db.org_organisation_logo(record.organisation_id)
        if logo:
            rheader = DIV(TABLE(TR(TD(logo),TD(rheader_fields))))
        else:
            rheader = DIV(rheader_fields)
        rheader.append(rheader_tabs)

    elif tablename == "inv_inv_item":
        # Tabs
        tabs = [(T("Details"), None),
                (T("Track Shipment"), "track_movement/"),
               ]
        rheader_tabs = DIV(s3_rheader_tabs(r, tabs))

        # Header
        rheader = DIV(
                    TABLE(
                        TR(TH("%s: " % table.item_id.label),
                           table.item_id.represent(record.item_id),
                           TH("%s: " % table.item_pack_id.label),
                           table.item_pack_id.represent(record.item_pack_id),
                           ),
                        TR(TH("%s: " % table.site_id.label),
                           TD(table.site_id.represent(record.site_id),
                              _colspan=3),
                           ),
                        ), rheader_tabs)

    elif tablename == "inv_track_item":
        # Tabs
        tabs = [(T("Details"), None),
                (T("Track Shipment"), "inv_item/"),
                ]
        rheader_tabs = DIV(s3_rheader_tabs(r, tabs))

        # Get site data
        table = s3db.inv_inv_item
        irecord = current.db(table.id == record.send_inv_item_id).select(
                                                        table.site_id,
                                                        limitby=(0, 1)).first()
        # Header
        if irecord:
            rheader = DIV(
                        TABLE(
                            TR(TH("%s: " % table.item_id.label),
                               table.item_id.represent(record.item_id),
                               TH("%s: " % table.item_pack_id.label),
                               table.item_pack_id.represent(record.item_pack_id),
                            ),
                            TR(TH( "%s: " % table.site_id.label),
                               TD(table.site_id.represent(irecord.site_id),
                                  _colspan=3),
                               ),
                            ), rheader_tabs)
        else:
            rheader = DIV(
                        TABLE(
                            TR(TH("%s: " % table.item_id.label),
                               table.item_id.represent(record.item_id),
                               TH("%s: " % table.item_pack_id.label),
                               table.item_pack_id.represent(record.item_pack_id),
                            ),
                            ), rheader_tabs)

    # Build footer
    inv_rfooter(r, record)

    return rheader

# =============================================================================
def inv_rfooter(r, record):
    """ Resource Footer for Warehouses and Inventory Items """

    if "site_id" not in record:
        return

    if (r.component and r.component.name == "inv_item"):
        T = current.T
        rfooter = TAG[""]()
        component_id = r.component_id
        if not current.deployment_settings.get_inv_direct_stock_edits() and \
           current.auth.s3_has_permission("update", "inv_warehouse", r.id):
            if component_id:
                asi_btn = A(T("Adjust Stock Item"),
                            _href = URL(c = "inv",
                                        f = "adj",
                                        args = ["create"],
                                        vars = {"site": record.site_id,
                                                "item": component_id},
                                        ),
                            _class = "action-btn"
                            )
                rfooter.append(asi_btn)
            else:
                as_btn = A(T("Adjust Stock"),
                           _href = URL(c = "inv",
                                       f = "adj",
                                       args = ["create"],
                                       vars = {"site": record.site_id},
                                       ),
                           _class = "action-btn"
                           )
                rfooter.append(as_btn)

        if component_id:
            ts_btn = A(T("Track Shipment"),
                       _href = URL(c = "inv",
                                   f = "track_movement",
                                   vars = {"viewing": "inv_item.%s" % component_id},
                                   ),
                       _class = "action-btn"
                       )
            rfooter.append(ts_btn)

        current.response.s3.rfooter = rfooter

# =============================================================================
def inv_recv_crud_strings():
    """
        CRUD Strings for inv_recv which need to be visible to menus without a
        model load
    """

    T = current.T

    if current.deployment_settings.get_inv_shipment_name() == "order":
        #recv_id_label = T("Order")
        ADD_RECV = T("Add Order")
        current.response.s3.crud_strings["inv_recv"] = Storage(
            label_create = ADD_RECV,
            title_display = T("Order Details"),
            title_list = T("Orders"),
            title_update = T("Edit Order"),
            label_list_button = T("List Orders"),
            label_delete_button = T("Delete Order"),
            msg_record_created = T("Order Created"),
            msg_record_modified = T("Order updated"),
            msg_record_deleted = T("Order canceled"),
            msg_list_empty = T("No Orders registered")
        )
    else:
        #recv_id_label = T("Receive Shipment")
        ADD_RECV = T("Receive New Shipment")
        current.response.s3.crud_strings["inv_recv"] = Storage(
            label_create = ADD_RECV,
            title_display = T("Received Shipment Details"),
            title_list = T("Received/Incoming Shipments"),
            title_update = T("Shipment to Receive"),
            label_list_button = T("List Received/Incoming Shipments"),
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
            db = current.db
            s3db = current.s3db
            T = current.T
            s3 = current.response.s3

            tabs = [(T("Edit Details"), None),
                    (T("Items"), "track_item"),
                    ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table
            stable = s3db.org_site

            send_id = record.id
            status = record.status
            site_id = record.site_id
            if site_id:
                site = db(stable.site_id == site_id).select(stable.organisation_id,
                                                            stable.instance_type,
                                                            limitby=(0, 1)
                                                            ).first()
                org_id = site.organisation_id
                logo = s3db.org_organisation_logo(org_id) or ""
                instance_table = s3db[site.instance_type]
                if "phone1" in instance_table.fields:
                    site = db(instance_table.site_id == site_id).select(instance_table.phone1,
                                                                        instance_table.phone2,
                                                                        limitby=(0, 1)
                                                                        ).first()
                    phone1 = site.phone1
                    phone2 = site.phone2
                else:
                    phone1 = None
                    phone2 = None
            else:
                org_id = None
                logo = ""
                phone1 = None
                phone2 = None
            to_site_id = record.to_site_id
            if to_site_id:
                site = db(stable.site_id == to_site_id).select(stable.location_id,
                                                               limitby=(0, 1)
                                                               ).first()
                address = s3db.gis_LocationRepresent(address_only=True)(site.location_id)
            else:
                address = current.messages["NONE"]
            rData = TABLE(TR(TD(T(current.deployment_settings.get_inv_send_form_name().upper()),
                                _colspan=2, _class="pdf_title"),
                             TD(logo, _colspan=2),
                             ),
                          TR(TH("%s: " % table.status.label),
                             table.status.represent(status),
                             ),
                          TR(TH("%s: " % table.send_ref.label),
                             TD(table.send_ref.represent(record.send_ref)),
                             TH("%s: " % table.req_ref.label),
                             TD(table.req_ref.represent(record.req_ref)),
                             ),
                          TR(TH("%s: " % table.date.label),
                             table.date.represent(record.date),
                             TH("%s: " % table.delivery_date.label),
                             table.delivery_date.represent(record.delivery_date),
                             ),
                          TR(TH("%s: " % table.to_site_id.label),
                             table.to_site_id.represent(record.to_site_id),
                             TH("%s: " % table.site_id.label),
                             table.site_id.represent(record.site_id),
                             ),
                          TR(TH("%s: " % T("Address")),
                             TD(address, _colspan=3),
                             ),
                          TR(TH("%s: " % table.transported_by.label),
                             table.transported_by.represent(record.transported_by),
                             TH("%s: " % table.transport_ref.label),
                             table.transport_ref.represent(record.transport_ref),
                             ),
                          TR(TH("%s: " % table.sender_id.label),
                             table.sender_id.represent(record.sender_id),
                             TH("%s: " % table.recipient_id.label),
                             table.recipient_id.represent(record.recipient_id),
                             ),
                          TR(TH("%s: " % T("Complete? Please call")),
                             phone1 or "",
                             TH("%s: " % T("Problems? Please call")),
                             phone2 or phone1 or "",
                             ),
                          TR(TH("%s: " % table.comments.label),
                             TD(record.comments or "", _colspan=3)
                             )
                          )

            # Find out how many inv_track_items we have for this send record
            tracktable = s3db.inv_track_item
            query = (tracktable.send_id == send_id) & \
                    (tracktable.deleted == False)
            #cnt = db(query).count()
            cnt = db(query).select(tracktable.id, limitby=(0, 1)).first()
            if cnt:
                cnt = 1
            else:
                cnt = 0

            action = DIV()
            #rSubdata = TABLE()
            rfooter = TAG[""]()

            if status == SHIP_STATUS_IN_PROCESS:
                if current.auth.s3_has_permission("update",
                                                  "inv_send",
                                                  record_id=record.id):

                    if cnt > 0:
                        action.append(A(T("Send Shipment"),
                                        _href = URL(f = "send_process",
                                                    args = [record.id]
                                                    ),
                                        _id = "send_process",
                                        _class = "action-btn"
                                        )
                                      )

                        s3.jquery_ready.append('''S3.confirmClick("#send_process","%s")''' \
                                   % T("Do you want to send this shipment?"))
                    #if not r.component and not r.method == "form":
                    #    ritable = s3db.req_req_item
                    #    rcitable = s3db.req_commit_item
                    #    query = (tracktable.send_id == record.id) & \
                    #            (rcitable.req_item_id == tracktable.req_item_id) & \
                    #            (tracktable.req_item_id == ritable.id) & \
                    #            (tracktable.deleted == False)
                    #    records = db(query).select()
                    #    for record in records:
                    #        rSubdata.append(TR(TH("%s: " % ritable.item_id.label),
                    #                           ritable.item_id.represent(record.req_req_item.item_id),
                    #                           TH("%s: " % rcitable.quantity.label),
                    #                           record.req_commit_item.quantity,
                    #                           ))

            elif status == SHIP_STATUS_RETURNING:
                    if cnt > 0:
                        action.append(A(T("Complete Returns"),
                                        _href = URL(c = "inv",
                                                    f = "return_process",
                                                    args = [record.id]
                                                    ),
                                        _id = "return_process",
                                        _class = "action-btn"
                                        )
                                      )
                        s3.jquery_ready.append('''S3.confirmClick("#return_process","%s")''' \
                            % T("Do you want to complete the return process?") )
                    else:
                        msg = T("You need to check all item quantities before you can complete the return process")
                        rfooter.append(SPAN(msg))
            elif status != SHIP_STATUS_CANCEL:
                if status == SHIP_STATUS_SENT:
                    jappend = s3.jquery_ready.append
                    s3_has_permission = current.auth.s3_has_permission
                    if s3_has_permission("update",
                                         "inv_send",
                                         record_id=record.id):
                        action.append(A(T("Manage Returns"),
                                        _href = URL(c = "inv",
                                                    f = "send_returns",
                                                    args = [record.id],
                                                    vars = None,
                                                    ),
                                        _id = "send_return",
                                        _class = "action-btn",
                                        _title = T("Only use this button to accept back into stock some items that were returned from a delivery to beneficiaries who do not record the shipment details directly into the system")
                                        )
                                      )

                        jappend('''S3.confirmClick("#send_return","%s")''' \
                            % T("Confirm that some items were returned from a delivery to beneficiaries and they will be accepted back into stock."))
                        action.append(A(T("Confirm Shipment Received"),
                                        _href = URL(f = "send",
                                                    args = [record.id],
                                                    vars = {"received": 1},
                                                    ),
                                        _id = "send_receive",
                                        _class = "action-btn",
                                        _title = T("Only use this button to confirm that the shipment has been received by a destination which will not record the shipment directly into the system")
                                        )
                                      )

                        jappend('''S3.confirmClick("#send_receive","%s")''' \
                            % T("Confirm that the shipment has been received by a destination which will not record the shipment directly into the system and confirmed as received.") )
                    if s3_has_permission("delete",
                                         "inv_send",
                                         record_id=record.id):
                        action.append(A(T("Cancel Shipment"),
                                        _href = URL(c = "inv",
                                                    f = "send_cancel",
                                                    args = [record.id]
                                                    ),
                                        _id = "send_cancel",
                                        _class = "action-btn"
                                        )
                                      )

                        jappend('''S3.confirmClick("#send_cancel","%s")''' \
                            % T("Do you want to cancel this sent shipment? The items will be returned to the Warehouse. This action CANNOT be undone!") )
            if not r.method == "form":
            #    msg = ""
            #    if cnt == 1:
            #       msg = T("One item is attached to this shipment")
            #    elif cnt > 1:
            #        msg = T("%s items are attached to this shipment") % cnt
            #    rData.append(TR(TH(action, _colspan=2),
            #                    TD(msg)))
                rData.append(TR(TH(action, _colspan=2)))

            s3.rfooter = rfooter
            rheader = DIV(rData,
                          rheader_tabs,
                          #rSubdata
                          )
            return rheader
    return None

# ---------------------------------------------------------------------
def inv_send_pdf_footer(r):
    """
        Footer for the Waybill
    """

    if r.record:
        T = current.T
        footer = DIV(TABLE(TR(TH(T("Commodities Loaded")),
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
                           ))
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
            rData = TABLE(TR(TD(T(current.deployment_settings.get_inv_recv_form_name()),
                                _colspan=2, _class="pdf_title"),
                             TD(logo, _colspan=2),
                             ),
                          TR(TH("%s: " % table.recv_ref.label),
                             TD(table.recv_ref.represent(record.recv_ref))
                             ),
                          TR(TH("%s: " % table.status.label),
                             table.status.represent(record.status),
                             ),
                          TR(TH("%s: " % table.eta.label),
                             table.eta.represent(record.eta),
                             TH("%s: " % table.date.label),
                             table.date.represent(record.date),
                             ),
                          TR(TH("%s: " % table.from_site_id.label),
                             table.from_site_id.represent(record.from_site_id),
                             TH("%s: " % table.site_id.label),
                             table.site_id.represent(record.site_id),
                             ),
                          TR(TH("%s: " % table.sender_id.label),
                             s3_fullname(record.sender_id),
                             TH("%s: " % table.recipient_id.label),
                             s3_fullname(record.recipient_id),
                             ),
                          TR(TH("%s: " % table.send_ref.label),
                             table.send_ref.represent(record.send_ref),
                             TH("%s: " % table.recv_ref.label),
                             table.recv_ref.represent(record.recv_ref),
                             ),
                          TR(TH("%s: " % table.comments.label),
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
                        action.append(A(T("Receive Shipment"),
                                        _href = URL(c = "inv",
                                                    f = "recv_process",
                                                    args = [record.id]
                                                    ),
                                        _id = "recv_process",
                                        _class = "action-btn"
                                        ))
                        recv_btn_confirm = SCRIPT("S3.confirmClick('#recv_process', '%s')"
                                                  % T("Do you want to receive this shipment?") )
                        rfooter.append(recv_btn_confirm)
                    else:
                        msg = T("You need to check all item quantities and allocate to bins before you can receive the shipment")
                        rfooter.append(SPAN(msg))
            # FB: Removed as serves no useful purpose & AusRC complained about it
            #else:
            #    if record.status == SHIP_STATUS_RECEIVED:
            #        if current.auth.s3_has_permission("delete",
            #                                          "inv_recv",
            #                                          record_id=record.id):
            #            action.append(A(T("Cancel Shipment"),
            #                            _href = URL(c = "inv",
            #                                        f = "recv_cancel",
            #                                        args = [record.id]
            #                                        ),
            #                            _id = "recv_cancel",
            #                            _class = "action-btn"
            #                            ))

            #            cancel_btn_confirm = SCRIPT("S3.confirmClick('#recv_cancel', '%s')"
            #                                         % T("Do you want to cancel this received shipment? The items will be removed from the Warehouse. This action CANNOT be undone!") )
            #            rfooter.append(cancel_btn_confirm)
            msg = ""
            if cnt == 1:
                msg = T("This shipment contains one line item")
            elif cnt > 1:
                msg = T("This shipment contains %s items") % cnt
            rData.append(TR(TH(action,
                               _colspan=2),
                            TD(msg)
                            ))

            current.response.s3.rfooter = rfooter
            rheader = DIV(rData,
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
        T = current.T
        footer = DIV(TABLE(TR(TH(T("Delivered By")),
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
                           ))
        return footer
    return None

# =============================================================================
class S3InventoryAdjustModel(S3Model):
    """
        A module to manage the shipment of inventory items
        - Sent Items
        - Received Items
        - And audit trail of the shipment process
    """

    names = ("inv_adj",
             "inv_adj_item",
             "inv_adj_item_id",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        settings = current.deployment_settings
        track_pack_values = settings.get_inv_track_pack_values()

        organisation_id = self.org_organisation_id
        org_site_represent = self.org_site_represent

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

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
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),
                     self.pr_person_id(name = "adjuster_id",
                                       label = T("Actioning officer"),
                                       ondelete = "RESTRICT",
                                       default = auth.s3_logged_in_person(),
                                       comment = self.pr_person_comment(child="adjuster_id")
                                       ),
                     # This is a reference, not a super-link, so we can override
                     Field("site_id", self.org_site,
                           label = current.deployment_settings.get_inv_facility_label(),
                           ondelete = "SET NULL",
                           default = auth.user.site_id if auth.is_logged_in() else None,
                           requires = IS_ONE_OF(db, "org_site.site_id",
                                                lambda id, row: \
                                                org_site_represent(id, row,
                                                                   show_link=False),
                                                instance_types = auth.org_site_types,
                                                updateable = True,
                                                sort = True,
                                                ),
                           represent=org_site_represent),
                     s3_date("adjustment_date",
                             default = "now",
                             writable = False
                             ),
                     Field("status", "integer",
                           requires = IS_EMPTY_OR(IS_IN_SET(adjust_status)),
                           represent = lambda opt: \
                                       adjust_status.get(opt, UNKNOWN_OPT),
                           default = 0,
                           label = T("Status"),
                           writable = False
                           ),
                     Field("category", "integer",
                           requires = IS_EMPTY_OR(IS_IN_SET(adjust_type)),
                           represent = lambda opt: \
                                       adjust_type.get(opt, UNKNOWN_OPT),
                           default = 1,
                           label = T("Type"),
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        self.configure(tablename,
                       super_entity = "doc_entity",
                       onaccept = self.inv_adj_onaccept,
                       create_next = URL(args=["[id]", "adj_item"]),
                      )

        # Components
        self.add_components(tablename,
                            inv_adj_item = "adj_id",
                            )

        # Reusable Field
        adj_id = S3ReusableField("adj_id", "reference %s" % tablename,
                                 label = T("Inventory Adjustment"),
                                 ondelete = "RESTRICT",
                                 represent = self.inv_adj_represent,
                                 requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "inv_adj.id",
                                                          self.inv_adj_represent,
                                                          orderby="inv_adj.adjustment_date",
                                                          sort=True)),
                                 sortby = "date",
                                 )

        adjust_reason = {0 : T("Unknown"),
                         1 : T("None"),
                         2 : T("Lost"),
                         3 : T("Damaged"),
                         4 : T("Expired"),
                         5 : T("Found"),
                         6 : T("Transfer Ownership"),
                         7 : T("Issued without Record"),
                         7 : T("Distributed without Record"),
                         }

        # CRUD strings
        if settings.get_inv_stock_count():
            ADJUST_STOCK = T("New Stock Count")
            crud_strings["inv_adj"] = Storage(
                label_create = ADJUST_STOCK,
                title_display = T("Stock Count Details"),
                title_list = T("Stock Counts"),
                title_update = T("Edit Stock Count"),
                label_list_button = T("List Stock Counts"),
                label_delete_button = T("Delete Stock Count"),
                msg_record_created = T("Stock Count created"),
                msg_record_modified = T("Stock Count modified"),
                msg_record_deleted = T("Stock Count deleted"),
                msg_list_empty = T("No stock counts have been done"))
        else:
            ADJUST_STOCK = T("New Stock Adjustment")
            crud_strings["inv_adj"] = Storage(
                label_create = ADJUST_STOCK,
                title_display = T("Stock Adjustment Details"),
                title_list = T("Stock Adjustments"),
                title_update = T("Edit Adjustment"),
                label_list_button = T("List Stock Adjustments"),
                label_delete_button = T("Delete Stock Adjustment"),
                msg_record_created = T("Adjustment created"),
                msg_record_modified = T("Adjustment modified"),
                msg_record_deleted = T("Adjustment deleted"),
                msg_list_empty = T("No stock adjustments have been done"))

        # ---------------------------------------------------------------------
        # Adjustment Items
        #
        inv_item_status_opts = self.inv_item_status_opts

        tablename = "inv_adj_item"
        define_table(tablename,
                     # Original inventory item
                     self.inv_item_id(ondelete = "RESTRICT",
                                      readable = False,
                                      writable = False),
                     self.supply_item_id(
                        ondelete = "RESTRICT"
                     ),
                     self.supply_item_pack_id(
                        ondelete = "SET NULL"
                     ),
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
                     Field("old_pack_value", "double",
                           readable = track_pack_values,
                           writable = track_pack_values,
                           label = T("Original Value per Pack")),
                     Field("new_pack_value", "double",
                           readable = track_pack_values,
                           writable = track_pack_values,
                           label = T("Revised Value per Pack")),
                     s3_currency(readable = track_pack_values,
                                 writable = track_pack_values),
                     Field("old_status", "integer",
                           label = T("Current Status"),
                           requires = IS_EMPTY_OR(IS_IN_SET(inv_item_status_opts)),
                           represent = lambda opt: \
                                       inv_item_status_opts.get(opt, UNKNOWN_OPT),
                           default = 0,
                           writable = False),
                     Field("new_status", "integer",
                           label = T("Revised Status"),
                           requires = IS_EMPTY_OR(IS_IN_SET(inv_item_status_opts)),
                           represent = lambda opt: \
                                       inv_item_status_opts.get(opt, UNKNOWN_OPT),
                           default = 0,),
                     s3_date("expiry_date",
                             label = T("Expiry Date")),
                     Field("bin", "string", length=16,
                           label = T("Bin"),
                           # @ToDo:
                           #widget = S3InvBinWidget("inv_adj_item")
                           ),
                     # Organisation that owned this item before
                     organisation_id(name = "old_owner_org_id",
                                     label = T("Current Owned By (Organization/Branch)"),
                                     ondelete = "SET NULL",
                                     writable = False),
                     # Organisation that owns this item now
                     organisation_id(name = "new_owner_org_id",
                                     label = T("Transfer Ownership To (Organization/Branch)"),
                                     ondelete = "SET NULL"),
                     adj_id(),
                     s3_comments(),
                     *s3_meta_fields())

        # Reusable Field
        adj_item_id = S3ReusableField("adj_item_id", "reference %s" % tablename,
                                      label = T("Inventory Adjustment Item"),
                                      ondelete = "RESTRICT",
                                      represent = self.inv_adj_item_represent,
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "inv_adj_item.id",
                                                              self.inv_adj_item_represent,
                                                              orderby="inv_adj_item.item_id",
                                                              sort=True)),
                                      sortby = "item_id",
                                      )

        # CRUD strings
        crud_strings["inv_adj_item"] = Storage(
            label_create = T("Add Item to Stock"),
            title_display = T("Item Details"),
            title_list = T("Items in Stock"),
            title_update = T("Adjust Item Quantity"),
            label_list_button = T("List Items in Stock"),
            #label_delete_button = T("Remove Item from Stock"), # This should be forbidden - set qty to zero instead
            msg_record_created = T("Item added to stock"),
            msg_record_modified = T("Item quantity adjusted"),
            #msg_record_deleted = T("Item removed from Stock"), # This should be forbidden - set qty to zero instead
            msg_list_empty = T("No items currently in stock"))

        return dict(inv_adj_item_id = adj_item_id,
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
                                    new_status = inv_item.status,
                                    old_pack_value = inv_item.pack_value,
                                    new_pack_value = inv_item.pack_value,
                                    expiry_date = inv_item.expiry_date,
                                    bin = inv_item.bin,
                                    old_owner_org_id = inv_item.owner_org_id,
                                    new_owner_org_id = inv_item.owner_org_id,
                                    )

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_adj_represent(id, row=None, show_link=True):
        """
            Represent an Inventory Adjustment
        """

        if row:
            table = current.db.inv_adj
        elif not id:
            return current.messages["NONE"]
        else:
            db = current.db
            table = db.inv_adj
            row = db(table.id == id).select(table.adjustment_date,
                                            table.adjuster_id,
                                            limitby=(0, 1)).first()

        try:
            repr = "%s - %s" % (table.adjuster_id.represent(row.adjuster_id),
                                table.adjustment_date.represent(row.adjustment_date)
                                )
        except:
            return current.messages.UNKNOWN_OPT
        else:
            if show_link:
                return SPAN(repr)
            else:
                return repr

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_adj_item_represent(id, row=None, show_link=True):
        """
            Represent an Inventory Adjustment Item
        """

        if row:
            table = current.db.inv_adj_item
        elif not id:
            return current.messages["NONE"]
        else:
            db = current.db
            table = db.inv_adj_item
            row = db(table.id == id).select(table.item_id,
                                            table.old_quantity,
                                            table.new_quantity,
                                            table.item_pack_id,
                                            limitby=(0, 1)).first()
        changed_quantity = 0
        try:
            if row.new_quantity and row.old_quantity:
                changed_quantity = row.new_quantity - row.old_quantity
            repr = "%s:%s %s" % (table.item_id.represent(row.item_id,
                                                         show_link=show_link),
                                 changed_quantity,
                                 table.item_pack_id.represent(row.item_pack_id),
                                 )
        except:
            return current.messages.UNKNOWN_OPT
        else:
            if show_link:
                return SPAN(repr)
            else:
                return repr

# =============================================================================
def inv_adj_rheader(r):
    """ Resource Header for Inventory Adjustments """

    if r.representation == "html" and r.name == "adj":
        record = r.record
        if record:
            T = current.T

            tabs = [(T("Edit Details"), None),
                    (T("Items"), "adj_item"),
                    (T("Photos"), "image"),
                    ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table

            rheader = DIV(TABLE(
                            TR(TH("%s: " % table.adjuster_id.label),
                               table.adjuster_id.represent(record.adjuster_id),
                               TH("%s: " % table.adjustment_date.label),
                               table.adjustment_date.represent(record.adjustment_date),
                               ),
                            TR(TH("%s: " % table.site_id.label),
                               table.site_id.represent(record.site_id),
                               TH("%s: " % table.category.label),
                               table.category.represent(record.category),
                               ),
                           ))

            if record.status == 0: # In process
                if current.auth.s3_has_permission("update", "inv_adj",
                                                  record_id=record.id):
                    # aitable = current.s3db.inv_adj_item
                    # query = (aitable.adj_id == record.id) & \
                            # (aitable.new_quantity == None)
                    # row = current.db(query).select(aitable.id,
                                                   # limitby=(0, 1)).first()
                    # if row == None:
                    close_btn = A( T("Complete Adjustment"),
                                  _href = URL(c = "inv",
                                              f = "adj_close",
                                              args = [record.id]
                                              ),
                                  _id = "adj_close",
                                  _class = "action-btn"
                                  )
                    close_btn_confirm = SCRIPT("S3.confirmClick('#adj_close', '%s')"
                                              % T("Do you want to complete & close this adjustment?") )
                    rheader.append(close_btn)
                    rheader.append(close_btn_confirm)

            rheader.append(rheader_tabs)

                    # else:
                        # msg = T("You need to check all the revised quantities before you can close this adjustment")
                        # rfooter.append(SPAN(msg))

            return rheader
    return None

# =============================================================================
class inv_InvItemRepresent(S3Represent):

    def __init__(self):
        """
            Constructor
        """

        super(inv_InvItemRepresent, self).__init__(lookup = "inv_inv_item")

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=[]):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        s3db = current.s3db

        itable = s3db.inv_inv_item
        stable = s3db.supply_item

        left = stable.on(stable.id == itable.item_id)
        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(itable.id,
                                        stable.name,
                                        stable.um,
                                        itable.item_source_no,
                                        itable.bin,
                                        itable.expiry_date,
                                        itable.owner_org_id,
                                        left=left)

        self.queries += 1

        # Bulk-represent owner_org_ids
        organisation_id = str(itable.owner_org_id)
        organisation_ids = [row[organisation_id] for row in rows]
        if organisation_ids:
            itable.owner_org_id.represent.bulk(organisation_ids)

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        itable = current.s3db.inv_inv_item

        iitem = row.inv_inv_item
        sitem = row.supply_item

        stringify = lambda string: string if string else ""

        ctn = stringify(iitem.item_source_no)
        org = itable.owner_org_id.represent(iitem.owner_org_id)
        bin = stringify(iitem.bin)

        expires = iitem.expiry_date
        if expires:
            expires = "expires: %s" % \
                      S3DateTime.date_represent(expires, utc=True)
        else:
            expires = ""

        NONE = current.messages["NONE"]

        items = []
        append = items.append
        for string in [sitem.name, expires, ctn, org, bin]:
            if string and string != NONE:
                append(string)
                append(" - ")
        return TAG[""](items[:-1])

# END =========================================================================
