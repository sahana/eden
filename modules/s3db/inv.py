# -*- coding: utf-8 -*-

""" Sahana Eden Inventory Model

    @copyright: 2009-2021 (c) Sahana Software Foundation
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

__all__ = ("WarehouseModel",
           "InventoryModel",
           "InventoryAdjustModel",
           "InventoryCommitModel",
           "InventoryCommitItemModel",
           "InventoryKittingModel",
           "InventoryMinimumModel",
           "InventoryOrderItemModel",
           "InventoryPalletModel",
           "InventoryPalletShipmentModel",
           "InventoryRequisitionModel",
           "InventoryRequisitionApproverModel",
           "InventoryRequisitionItemModel",
           "InventoryRequisitionProjectModel",
           "InventoryRequisitionRecurringModel",
           "InventoryRequisitionShipmentModel",
           "InventoryRequisitionTagModel",
           "InventoryStockCardModel",
           "InventoryTrackingModel",
           "inv_adj_rheader",
           #"inv_gift_certificate",
           "inv_item_total_weight",
           "inv_item_total_volume",
           #"inv_pick_list",
           "inv_prep",
           "inv_recv_attr",
           "inv_recv_controller",
           "inv_recv_crud_strings",
           "inv_recv_rheader",
           #"inv_recv_process",
           "inv_remove",
           "inv_req_add_from_template",
           "inv_req_approvers",
           "inv_req_create_form_mods",
           "inv_req_inline_form",
           #"inv_req_is_approver",
           "inv_req_match",
           "inv_req_rheader",
           "inv_req_tabs",
           "inv_req_update_status", # exported for recv_cancel controller (until rewritten as Method)
           "inv_rfooter",
           "inv_rheader",
           "inv_send_commit",
           "inv_send_controller",
           "inv_send_onaccept",
           #"inv_send_process",
           #"inv_send_received",
           "inv_send_rheader",
           "inv_ship_status",
           #"inv_stock_card_update",
           "inv_stock_movements",
           "inv_tabs",
           "inv_track_item_deleting",
           #"inv_track_item_onaccept",
           "inv_tracking_status",
           "inv_warehouse_free_capacity",
           "inv_InvItemRepresent",
           #"inv_RecvRepresent",
           #"inv_ReqCheckMethod",
           "inv_ReqItemRepresent",
           "inv_ReqRefRepresent",
           #"inv_SendRepresent",
           #"inv_TrackItemRepresent",
           )

import datetime
import json

from gluon import *
from gluon.sqlhtml import RadioWidget, StringWidget
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3PopupLink
from .supply import SupplyItemPackQuantity

# Compact JSON encoding
SEPARATORS = (",", ":")

# Dependency list for translate-module
depends = ["supply"]

# =============================================================================
def req_priority_opts():
    T = current.T
    return {3: T("High"),
            2: T("Medium"),
            1: T("Low")
            }

def req_priority():
    priority_opts = req_priority_opts()
    return S3ReusableField("priority", "integer",
                           default = 2,
                           label = current.T("Priority"),
                           #@ToDo: Colour code the priority text - red, orange, green
                           #represent = req_priority_represent,
                           represent = S3Represent(options = priority_opts),
                           requires = IS_EMPTY_OR(
                                           IS_IN_SET(priority_opts)
                                           ),
                           )

# =============================================================================
REQ_STATUS_NONE     = 0
REQ_STATUS_PARTIAL  = 1
REQ_STATUS_COMPLETE = 2
REQ_STATUS_CANCEL   = 3

def req_status_opts():
    T = current.T
    return {REQ_STATUS_NONE:     SPAN(T("None"),
                                      _class = "req_status_none",
                                      ),
            REQ_STATUS_PARTIAL:  SPAN(T("Partial"),
                                      _class = "req_status_partial",
                                      ),
            REQ_STATUS_COMPLETE: SPAN(T("Complete"),
                                      _class = "req_status_complete",
                                      ),
            }

def req_status():
    status_opts = req_status_opts()
    return S3ReusableField("req_status", "integer",
                           label = current.T("Request Status"),
                           represent = S3Represent(options = status_opts),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(status_opts,
                                                  zero = None,
                                                  )
                                        ),
                           )

# =============================================================================
SHIP_STATUS_IN_PROCESS = 0
SHIP_STATUS_RECEIVED   = 1
SHIP_STATUS_SENT       = 2
SHIP_STATUS_CANCEL     = 3
SHIP_STATUS_RETURNING  = 4

# Dict to lookup a status by name
inv_ship_status = {"IN_PROCESS" : SHIP_STATUS_IN_PROCESS,
                   "SENT"       : SHIP_STATUS_SENT,
                   "RECEIVED"   : SHIP_STATUS_RECEIVED,
                   "CANCEL"     : SHIP_STATUS_CANCEL,
                   "RETURNING"  : SHIP_STATUS_RETURNING,
                   }

def inv_shipment_status_labels():
    T = current.T
    return OrderedDict({SHIP_STATUS_IN_PROCESS: T("In Process"),
                        SHIP_STATUS_SENT: T("Sent"),
                        SHIP_STATUS_RECEIVED: T("Received"),
                        SHIP_STATUS_CANCEL: T("Canceled"),
                        SHIP_STATUS_RETURNING: T("Returning"),
                        })

SHIP_DOC_PENDING  = 0
SHIP_DOC_COMPLETE = 1

# =============================================================================
TRACK_STATUS_UNKNOWN    = 0
TRACK_STATUS_PREPARING  = 1
TRACK_STATUS_TRANSIT    = 2
TRACK_STATUS_UNLOADING  = 3
TRACK_STATUS_ARRIVED    = 4
TRACK_STATUS_CANCELED   = 5
TRACK_STATUS_RETURNING  = 6

# Dict to lookup a status by name
inv_tracking_status = {"UNKNOWN"    : TRACK_STATUS_UNKNOWN,
                       "IN_PROCESS" : TRACK_STATUS_PREPARING,
                       "SENT"       : TRACK_STATUS_TRANSIT,
                       "UNLOADING"  : TRACK_STATUS_UNLOADING,
                       "RECEIVED"   : TRACK_STATUS_ARRIVED,
                       "CANCEL"     : TRACK_STATUS_CANCELED,
                       "RETURNING"  : TRACK_STATUS_RETURNING,
                       }

# =============================================================================
def inv_itn_label():
    # Overwrite the label until we have a better way to do this
    #return current.T("Item Source Tracking Number")
    return current.T("CTN")

# =============================================================================
class WarehouseModel(S3Model):

    names = ("inv_warehouse",
             "inv_warehouse_type",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        messages = current.messages
        NONE = messages["NONE"]
        OBSOLETE = messages.OBSOLETE

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        settings = current.deployment_settings
        super_link = self.super_link

        organisation_id = self.org_organisation_id

        ADMIN = current.session.s3.system_roles.ADMIN
        is_admin = auth.s3_has_role(ADMIN)

        root_org = auth.root_org()
        if is_admin:
            filter_opts = ()
        elif root_org:
            filter_opts = (root_org, None)
        else:
            filter_opts = (None,)

        # ---------------------------------------------------------------------
        # Warehouse Types
        #
        org_dependent_wh_types = settings.get_inv_org_dependent_warehouse_types()

        tablename = "inv_warehouse_type"
        define_table(tablename,
                     Field("name", length=128, notnull=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     organisation_id(default = root_org if org_dependent_wh_types else None,
                                     readable = is_admin if org_dependent_wh_types else False,
                                     writable = is_admin if org_dependent_wh_types else False,
                                     ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_WAREHOUSE_TYPE = T("Create Warehouse Type")
        crud_strings[tablename] = Storage(
           label_create = ADD_WAREHOUSE_TYPE,
           title_display = T("Warehouse Type Details"),
           title_list = T("Warehouse Types"),
           title_update = T("Edit Warehouse Type"),
           label_list_button = T("List Warehouse Types"),
           label_delete_button = T("Delete Warehouse Type"),
           msg_record_created = T("Warehouse Type added"),
           msg_record_modified = T("Warehouse Type updated"),
           msg_record_deleted = T("Warehouse Type deleted"),
           msg_list_empty = T("No Warehouse Types currently registered"))

        represent = S3Represent(lookup = tablename,
                                translate = True,
                                )

        warehouse_type_id = S3ReusableField("warehouse_type_id", "reference %s" % tablename,
                                            label = T("Warehouse Type"),
                                            ondelete = "SET NULL",
                                            represent = represent,
                                            requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "inv_warehouse_type.id",
                                                                  represent,
                                                                  filterby = "organisation_id",
                                                                  filter_opts = filter_opts,
                                                                  sort = True
                                                                  )),
                                            sortby = "name",
                                            comment = S3PopupLink(c = "inv",
                                                                  f = "warehouse_type",
                                                                  label = ADD_WAREHOUSE_TYPE,
                                                                  title = T("Warehouse Type"),
                                                                  tooltip = T("If you don't see the Type in the list, you can add a new one by clicking link 'Create Warehouse Type'."),
                                                                  ),
                                            )

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("name",),
                                            secondary = ("organisation_id",),
                                            ),
                  )

        # Tags as component of Warehouse Types
        #self.add_components(tablename,
        #                    inv_warehouse_type_tag={"name": "tag",
        #                                            "joinby": "warehouse_type_id",
        #                                            }
        #                    )

        # ---------------------------------------------------------------------
        # Warehouses
        #
        if settings.get_inv_warehouse_code_unique():
            code_requires = IS_EMPTY_OR([IS_LENGTH(10),
                                         IS_NOT_IN_DB(db, "inv_warehouse.code"),
                                         ])
        else:
            code_requires = IS_LENGTH(10)

        free_capacity_calculated = settings.get_inv_warehouse_free_capacity_calculated()

        tablename = "inv_warehouse"
        define_table(tablename,
                     super_link("pe_id", "pr_pentity"),
                     super_link("site_id", "org_site"),
                     super_link("doc_id", "doc_entity"),
                     Field("name", notnull=True,
                           length=64,           # Mayon Compatibility
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     Field("code", length=10, # Mayon compatibility
                           label = T("Code"),
                           represent = lambda v: v or NONE,
                           requires = code_requires,
                           ),
                     organisation_id(requires = self.org_organisation_requires(updateable = True),
                                     ),
                     warehouse_type_id(),
                     self.gis_location_id(),
                     Field("capacity", "double",
                           label = T("Capacity (m3)"),
                           represent = lambda v: v or NONE,
                           requires = IS_EMPTY_OR(
                                        IS_FLOAT_IN_RANGE(0, None)
                                        ),
                           ),
                     Field("free_capacity", "double",
                           label = T("Free Capacity (m3)"),
                           represent = lambda v: v or NONE,
                           requires = IS_EMPTY_OR(
                                        IS_FLOAT_IN_RANGE(0, None)
                                        ),
                           writable = not free_capacity_calculated,
                           ),
                     Field("contact",
                           label = T("Contact"),
                           represent = lambda v: v or NONE,
                           ),
                     Field("phone1",
                           label = T("Phone"),
                           represent = lambda v: v or NONE,
                           requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI())
                           ),
                     Field("phone2",
                           label = T("Phone 2"),
                           represent = lambda v: v or NONE,
                           requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI())
                           ),
                     Field("email",
                           label = T("Email"),
                           represent = lambda v: v or NONE,
                           requires = IS_EMPTY_OR(IS_EMAIL())
                           ),
                     #Field("fax", label = T("Fax"),
                     #      represent = lambda v: v or NONE,
                     #      requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI())
                     #      ),
                     Field("obsolete", "boolean",
                           default = False,
                           label = T("Obsolete"),
                           represent = lambda opt: OBSOLETE if opt else NONE,
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

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        list_fields = ["name",
                       "organisation_id",   # Filtered in Component views
                       "warehouse_type_id",
                       ]

        text_fields = ["name",
                       "code",
                       "comments",
                       "organisation_id$name",
                       "organisation_id$acronym",
                       ]

        #report_fields = ["name",
        #                 "organisation_id",
        #                 ]

        for level in levels:
            lfield = "location_id$%s" % level
            list_fields.append(lfield)
            #report_fields.append(lfield)
            text_fields.append(lfield)

        list_fields += [#(T("Address"), "location_id$addr_street"),
                        "phone1",
                        "email",
                        ]

        # Filter widgets
        filter_widgets = [
            S3TextFilter(text_fields,
                         label = T("Search"),
                         #_class = "filter-search",
                         ),
            S3OptionsFilter("organisation_id",
                            #label = T("Organization"),
                            # Doesn't support l10n
                            #represent = "%(name)s",
                            #hidden = True,
                            ),
            S3LocationFilter("location_id",
                             #label = T("Location"),
                             levels = levels,
                             #hidden = True,
                             ),
            ]

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("name",),
                                            secondary = ("organisation_id",),
                                            ),
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  onaccept = self.inv_warehouse_onaccept,
                  realm_components = ("contact_emergency",
                                      "physical_description",
                                      "config",
                                      "image",
                                      "req",
                                      "send",
                                      "human_resource_site",
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
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_warehouse_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        current.s3db.org_update_affiliations("inv_warehouse", form.vars)

# =============================================================================
class InventoryModel(S3Model):
    """
        Inventory Management

        Record inventories of items at sites:
            Warehouses, Offices, Shelters, Hospitals, etc
    """

    names = ("inv_inv_item",
             "inv_item_id",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        organisation_id = self.org_organisation_id

        #messages = current.messages
        NONE = current.messages["NONE"]

        settings = current.deployment_settings
        bin_site_layout = settings.get_inv_bin_site_layout()
        direct_stock_edits = settings.get_inv_direct_stock_edits()
        track_pack_values = settings.get_inv_track_pack_values()
        WAREHOUSE = T(settings.get_inv_facility_label())

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
        inv_item_status_opts = settings.get_inv_item_status()

        tablename = "inv_inv_item"
        self.define_table(tablename,
                          # This is a component, so needs to be a super_link
                          # - can't override field name, ondelete or requires
                          self.super_link("site_id", "org_site",
                                          default = auth.user.site_id if auth.is_logged_in() else None,
                                          empty = False,
                                          instance_types = auth.org_site_types,
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
                          self.supply_item_entity_id(),
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
                                requires = IS_FLOAT_AMOUNT(minimum=0.0),
                                writable = direct_stock_edits,
                                ),
                          Field("bin", length=16,
                                label = T("Bin"),
                                represent = lambda v: v or NONE,
                                requires = IS_LENGTH(16),
                                readable = not bin_site_layout,
                                writable = not bin_site_layout,
                                ),
                          self.org_site_layout_id(label = T("Bin"),
                                                  readable = bin_site_layout,
                                                  writable = bin_site_layout,
                                                  ),
                          # e.g.: Allow items to be marked as 'still on the shelf but allocated to an outgoing shipment'
                          Field("status", "integer",
                                default = 0, # Only Items with this Status can be allocated to Outgoing Shipments
                                label = T("Status"),
                                represent = S3Represent(options = inv_item_status_opts),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(inv_item_status_opts)
                                            ),
                                ),
                          s3_date("purchase_date",
                                  label = T("Purchase Date"),
                                  ),
                          s3_date("expiry_date",
                                  label = T("Expiry Date"),
                                  represent = inv_expiry_date_represent,
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
                          Field("item_source_no", length=16,
                                label = inv_itn_label(),
                                represent = lambda v: v or NONE,
                                requires = [IS_LENGTH(16),
                                            IS_NOT_EMPTY_STR(),
                                            ]
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
                                represent = S3Represent(options = inv_source_type),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(inv_source_type)
                                            ),
                                writable = False,
                                ),
                          Field.Method("total_value",
                                       self.inv_item_total_value
                                       ),
                          Field.Method("pack_quantity",
                                       SupplyItemPackQuantity(tablename)
                                       ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        INV_ITEM = T("Warehouse Stock")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Stock to Warehouse"),
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
                                                           orderby = "inv_inv_item.id",
                                                           sort = True,
                                                           ),
                                      comment = DIV(_class = "tooltip",
                                                    _title = "%s|%s" % (INV_ITEM,
                                                                        T("Select Stock from this Warehouse"),
                                                                        ),
                                                    ),
                                      script = '''
$.filterOptionsS3({
 'trigger':'inv_item_id',
 'target':'item_pack_id',
 'lookupResource':'item_pack',
 'lookupPrefix':'supply',
 'lookupURL':S3.Ap.concat('/inv/inv_item_packs.json/'),
 'msgNoRecords':i18n.no_packs,
 'fncPrep':S3.supply.fncPrepItem,
 'fncRepresent':S3.supply.fncRepresentItem
})''')

        # Filter widgets
        filter_widgets = [
            S3TextFilter(["item_id$name",
                          "item_id$code",
                          "item_id$brand",
                          "item_id$model",
                          "item_id$comments",
                          "item_pack_id$name",
                          ],
                          label = T("Search"),
                          #comment = T("Search for items with this text in the name."),
                          ),
            S3OptionsFilter("site_id",
                            #label = T("Facility"),
                            cols = 2,
                            hidden = True,
                            ),
            S3OptionsFilter("status",
                            #label = T("Status"),
                            cols = 2,
                            hidden = True,
                            ),
            S3RangeFilter("quantity",
                          label = T("Quantity Range"),
                          comment = T("Include only items where quantity is in this range."),
                          ge = 10,
                          hidden = True,
                          ),
            S3DateFilter("purchase_date",
                         #label = T("Purchase Date"),
                         comment = T("Include only items purchased within the specified dates."),
                         hidden = True,
                         ),
            S3DateFilter("expiry_date",
                         #label = T("Expiry Date"),
                         comment = T("Include only items that expire within the specified dates."),
                         hidden = True,
                         ),
            S3OptionsFilter("owner_org_id",
                            label = T("Owning Organization"),
                            comment = T("Search for items by owning organization."),
                            represent = "%(name)s",
                            #cols = 2,
                            hidden = True,
                            ),
            S3OptionsFilter("supply_org_id",
                            label = T("Donating Organization"),
                            comment = T("Search for items by donating organization."),
                            represent = "%(name)s",
                            #cols = 2,
                            hidden = True,
                            ),
            ]

        # Report options
        if track_pack_values:
            rows = ["item_id", "item_id$item_category_id"]
            cols = ["site_id", "owner_org_id", "supply_org_id"]
            fact = ["quantity", (T("Total Value"), "total_value")]
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
        if bin_site_layout:
            bin_field = "layout_id"
        else:
            bin_field = "bin"

        if track_pack_values:
            list_fields = ["site_id",
                           "item_id",
                           "item_id$code",
                           "item_id$item_category_id",
                           "quantity",
                           "expiry_date",
                           "owner_org_id",
                           "pack_value",
                           (T("Total Value"), "total_value"),
                           "currency",
                           bin_field,
                           "supply_org_id",
                           "status",
                           ]
        else:
            list_fields = ["site_id",
                           "item_id",
                           "item_id$code",
                           "item_id$item_category_id",
                           "quantity",
                           bin_field,
                           "owner_org_id",
                           "supply_org_id",
                           "status",
                           ]

        # Configuration
        self.configure(tablename,
                       # Lock the record so that it can't be meddled with
                       # - unless explicitly told to allow this
                       deletable = direct_stock_edits,
                       editable = direct_stock_edits,
                       insertable = direct_stock_edits,
                       context = {"location": "site_id$location_id",
                                  },
                       deduplicate = self.inv_item_duplicate,
                       extra_fields = ["quantity",
                                       "pack_value",
                                       "item_pack_id",
                                       ],
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       onaccept = self.inv_item_onaccept,
                       report_options = report_options,
                       super_entity = "supply_item_entity",
                       grouped = {
                        "default": {
                            "title": T("Warehouse Stock Report"),
                            "fields": [(T("Warehouse"), "site_id$name"),
                                       "item_id$item_category_id",
                                       bin_field,
                                       "item_id$name",
                                       "quantity",
                                       "pack_value",
                                       "total_value",
                                       ],
                            "groupby": ["site_id",
                                        ],
                            "orderby": ["site_id$name",
                                        "item_id$name",
                                        ],
                            "aggregate": [("sum", "quantity"),
                                          ("sum", "total_value"),
                                          ],
                         },
                        },
                       )

        self.add_components(tablename,
                            inv_adj_item = "inv_item_id",
                            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"inv_item_id": inv_item_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_item_total_value(row):
        """ Total value of an inventory item """

        if hasattr(row, "inv_inv_item"):
            row = row.inv_inv_item

        try:
            value = row.quantity * row.pack_value
        except (AttributeError, TypeError):
            # not available
            return current.messages["NONE"]
        else:
            return round(value, 2)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_item_onaccept(form):
        """
            Called when Stock is created/updated by:
            - direct_stock_edits
            - imports

            Create/Update a Stock Card
            Update the Free Capacity of the Warehouse
        """

        inv_item_id = form.vars.id

        settings = current.deployment_settings

        stock_cards = settings.get_inv_stock_cards()
        if stock_cards:
            comments = "Import" if current.response.s3.bulk else "Direct Stock Edit"
            inv_stock_card_update([inv_item_id], comments = comments)

        free_capacity_calculated = settings.get_inv_warehouse_free_capacity_calculated()
        if free_capacity_calculated:
            site_id = form.vars.get("site_id")
            if not site_id:
                table = current.s3db.inv_inv_item
                record = current.db(table.id == inv_item_id).select(table.site_id,
                                                                    limitby = (0, 1),
                                                                    ).first()
                site_id = record.site_id

            inv_warehouse_free_capacity(site_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_item_duplicate(item):
        """
            Update detection for inv_inv_item

            @param item: the S3ImportItem
        """

        table = item.table
        data = item.data
        data_get = data.get

        site_id = data_get("site_id")
        item_id = data_get("item_id")
        pack_id = data_get("item_pack_id")
        owner_org_id = data_get("owner_org_id")
        supply_org_id = data_get("supply_org_id")
        pack_value = data_get("pack_value")
        currency = data_get("currency")
        item_bin = data_get("bin")
        item_layout_id = data_get("layout_id")

        # Must match all of these exactly
        query = (table.site_id == site_id) & \
                (table.item_id == item_id) & \
                (table.item_pack_id == pack_id) & \
                (table.owner_org_id == owner_org_id) & \
                (table.supply_org_id == supply_org_id) & \
                (table.pack_value == pack_value) & \
                (table.currency == currency) & \
                (table.bin == item_bin) & \
                (table.layout_id == item_layout_id)

        duplicate = current.db(query).select(table.id,
                                             table.quantity,
                                             limitby = (0, 1),
                                             ).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

            # If the import item has a quantity of 0 (e.g. when imported
            # implicitly through inv_track_item), retain the stock quantity
            if "quantity" in data and data.quantity == 0:
                item.data.quantity = duplicate.quantity

# =============================================================================
class InventoryAdjustModel(S3Model):
    """
        A module to manage Stock Adjustments
        - Inventory Counts
        - Adjustments to Shipments
    """

    names = ("inv_adj",
             "inv_adj_id",
             "inv_adj_item",
             "inv_adj_item_id",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        settings = current.deployment_settings
        bin_site_layout = settings.get_inv_bin_site_layout()
        track_pack_values = settings.get_inv_track_pack_values()

        organisation_id = self.org_organisation_id
        org_site_represent = self.org_site_represent

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

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
                     super_link("doc_id", "doc_entity"),
                     self.pr_person_id(name = "adjuster_id",
                                       label = T("Actioning officer"),
                                       ondelete = "RESTRICT",
                                       default = auth.s3_logged_in_person(),
                                       comment = self.pr_person_comment(child="adjuster_id")
                                       ),
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("site_id", "org_site",
                                default = auth.user.site_id if auth.is_logged_in() else None,
                                empty = False,
                                instance_types = auth.org_site_types,
                                label = T(current.deployment_settings.get_inv_facility_label()),
                                not_filterby = "obsolete",
                                not_filter_opts = (True,),
                                readable = True,
                                writable = True,
                                represent = org_site_represent,
                                updateable = True,
                                #widget = S3SiteAutocompleteWidget(),
                                ),
                     s3_date("adjustment_date",
                             default = "now",
                             writable = False
                             ),
                     Field("status", "integer",
                           requires = IS_EMPTY_OR(IS_IN_SET(adjust_status)),
                           represent = S3Represent(options = adjust_status),
                           default = 0,
                           label = T("Status"),
                           writable = False
                           ),
                     Field("category", "integer",
                           requires = IS_EMPTY_OR(IS_IN_SET(adjust_type)),
                           represent = S3Represent(options = adjust_type),
                           default = 1,
                           label = T("Type"),
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        self.configure(tablename,
                       super_entity = "doc_entity",
                       create_onaccept = self.inv_adj_create_onaccept,
                       create_next = URL(args = ["[id]", "adj_item"]),
                       )

        # Components
        self.add_components(tablename,
                            inv_adj_item = "adj_id",
                            )

        self.set_method("inv", "adj",
                        method = "close",
                        action = self.adj_close,
                        )

        # Reusable Field
        inv_adj_represent = inv_AdjRepresent()
        adj_id = S3ReusableField("adj_id", "reference %s" % tablename,
                                 label = T("Inventory Adjustment"),
                                 ondelete = "RESTRICT",
                                 represent = inv_adj_represent,
                                 requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "inv_adj.id",
                                                          inv_adj_represent,
                                                          orderby = "inv_adj.adjustment_date",
                                                          sort = True,
                                                          )),
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
                         8 : T("Distributed without Record"),
                         }

        # CRUD strings
        if settings.get_inv_stock_count():
            crud_strings["inv_adj"] = Storage(
                label_create = T("New Stock Count"),
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
            crud_strings["inv_adj"] = Storage(
                label_create = T("New Stock Adjustment"),
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
        inv_item_status_opts = settings.get_inv_item_status()

        tablename = "inv_adj_item"
        define_table(tablename,
                     # Original inventory item
                     self.inv_item_id(ondelete = "RESTRICT",
                                      readable = False,
                                      writable = False,
                                      ),
                     self.supply_item_id(
                        ondelete = "RESTRICT"
                     ),
                     self.supply_item_pack_id(
                        ondelete = "SET NULL"
                     ),
                     Field("old_quantity", "double", notnull=True,
                           default = 0,
                           label = T("Original Quantity"),
                           represent = lambda v: \
                                       IS_FLOAT_AMOUNT.represent(v, precision=2),
                           writable = False,
                           ),
                     Field("new_quantity", "double",
                           label = T("Revised Quantity"),
                           represent = self.qnty_adj_repr,
                           requires = IS_FLOAT_AMOUNT(minimum=0.0),
                           ),
                     Field("reason", "integer",
                           default = 1,
                           label = T("Reason"),
                           represent = S3Represent(options = adjust_reason),
                           requires = IS_IN_SET(adjust_reason),
                           writable = False,
                           ),
                     Field("old_pack_value", "double",
                           label = T("Original Value per Pack"),
                           readable = track_pack_values,
                           writable = track_pack_values,
                           ),
                     Field("new_pack_value", "double",
                           label = T("Revised Value per Pack"),
                           readable = track_pack_values,
                           writable = track_pack_values,
                           ),
                     s3_currency(readable = track_pack_values,
                                 writable = track_pack_values),
                     Field("old_status", "integer",
                           default = 0,
                           label = T("Current Status"),
                           represent = S3Represent(options = inv_item_status_opts),
                           requires = IS_EMPTY_OR(IS_IN_SET(inv_item_status_opts)),
                           writable = False,
                           ),
                     Field("new_status", "integer",
                           default = 0,
                           label = T("Revised Status"),
                           represent = S3Represent(options = inv_item_status_opts),
                           requires = IS_EMPTY_OR(IS_IN_SET(inv_item_status_opts)),
                           ),
                     s3_date("expiry_date",
                             label = T("Expiry Date"),
                             ),
                     Field("bin", length=16,
                           label = T("Bin"),
                           requires = IS_LENGTH(16),
                           # @ToDo:
                           #widget = S3InvBinWidget("inv_adj_item")
                           readable = not bin_site_layout,
                           writable = not bin_site_layout,
                           ),
                     self.org_site_layout_id(label = T("Bin"),
                                             readable = bin_site_layout,
                                             writable = bin_site_layout,
                                             ),
                     # Organisation that owned this item before
                     organisation_id("old_owner_org_id",
                                     label = T("Current Owned By (Organization/Branch)"),
                                     ondelete = "SET NULL",
                                     writable = False,
                                     comment = None,
                                     ),
                     # Organisation that owns this item now
                     organisation_id("new_owner_org_id",
                                     label = T("Transfer Ownership To (Organization/Branch)"),
                                     ondelete = "SET NULL",
                                     ),
                     adj_id(),
                     s3_comments(),
                     *s3_meta_fields())

        # Reusable Field
        inv_adj_item_represent = inv_AdjItemRepresent()
        adj_item_id = S3ReusableField("adj_item_id", "reference %s" % tablename,
                                      label = T("Inventory Adjustment Item"),
                                      ondelete = "RESTRICT",
                                      represent = inv_adj_item_represent,
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "inv_adj_item.id",
                                                              inv_adj_item_represent,
                                                              orderby = "inv_adj_item.item_id",
                                                              sort = True,
                                                              )
                                                    ),
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
            msg_record_created = T("Item added to stock adjustment"),
            msg_record_modified = T("Item quantity adjusted"),
            #msg_record_deleted = T("Item removed from Stock"), # This should be forbidden - set qty to zero instead
            msg_list_empty = T("No items currently in stock"))

        return {"inv_adj_id": adj_id,
                "inv_adj_item_id": adj_item_id,
                }

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        dummy = S3ReusableField.dummy

        return {"inv_adj_id": dummy("adj_id"),
                "inv_adj_item_id": dummy("adj_item_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def qnty_adj_repr(value):
        """
            Make unadjusted quantities show up in bold
        """

        if value is None:
            # We want the word "None" here, not just a dash
            return B(current.T("None"))
        else:
            return IS_FLOAT_AMOUNT.represent(value, precision=2)

    # -----------------------------------------------------------------------------
    @staticmethod
    def adj_close(r, **attr):
        """ 
            Close an Adjustment
        """

        adj_id = r.id
        if not adj_id:
            r.error(405, current.ERROR.BAD_METHOD)

        auth = current.auth

        # Check Permissions
        if not auth.s3_has_permission("update", "inv_adj",
                                      record_id = adj_id):
            r.unauthorised()

        db = current.db
        s3db = current.s3db

        # Check current Status
        atable = s3db.inv_adj
        adj_record = db(atable.id == adj_id).select(atable.status,
                                                    atable.site_id,
                                                    limitby = (0, 1),
                                                    ).first()
        if adj_record.status != 0:
            r.error(409, current.T("This adjustment has already been closed."))

        aitable = s3db.inv_adj_item
        inv_item_table = s3db.inv_inv_item
        get_realm_entity = auth.get_realm_entity
        site_id = adj_record.site_id

        settings = current.deployment_settings
        stock_cards = settings.get_inv_stock_cards()
        if stock_cards:
            inv_item_ids = []
            iiappend = inv_item_ids.append

        # Go through all the adj_items
        query = (aitable.adj_id == adj_id) & \
                (aitable.deleted == False)
        adj_items = db(query).select(aitable.id,
                                     aitable.inv_item_id,
                                     aitable.item_id,
                                     aitable.item_pack_id,
                                     aitable.currency,
                                     aitable.bin,
                                     aitable.layout_id,
                                     aitable.old_pack_value,
                                     aitable.expiry_date,
                                     aitable.new_quantity,
                                     aitable.old_owner_org_id,
                                     aitable.new_owner_org_id,
                                     aitable.new_status,
                                     )
        for adj_item in adj_items:
            if adj_item.inv_item_id is None:
                # Create a new stock item
                inv_item = {"site_id": site_id,
                            "item_id": adj_item.item_id,
                            "item_pack_id": adj_item.item_pack_id,
                            "currency": adj_item.currency,
                            "bin": adj_item.bin,
                            "layout_id": adj_item.layout_id,
                            "pack_value": adj_item.old_pack_value,
                            "expiry_date": adj_item.expiry_date,
                            "quantity": adj_item.new_quantity,
                            "owner_org_id": adj_item.old_owner_org_id,
                            }
                inv_item_id = inv_item_table.insert(**inv_item)

                # Apply the realm entity
                inv_item["id"] = inv_item_id
                realm_entity = get_realm_entity(inv_item_table, inv_item)
                db(inv_item_table.id == inv_item_id).update(realm_entity = realm_entity)

                # Add the inventory item id to the adjustment record
                db(aitable.id == adj_item.id).update(inv_item_id = inv_item_id)

            elif adj_item.new_quantity is not None:
                # Update the existing stock item
                inv_item_id = adj_item.inv_item_id
                db(inv_item_table.id == inv_item_id).update(item_pack_id = adj_item.item_pack_id,
                                                            bin = adj_item.bin,
                                                            layout_id = adj_item.layout_id,
                                                            pack_value = adj_item.old_pack_value,
                                                            expiry_date = adj_item.expiry_date,
                                                            quantity = adj_item.new_quantity,
                                                            owner_org_id = adj_item.new_owner_org_id,
                                                            status = adj_item.new_status,
                                                            )
            if stock_cards:
                iiappend(inv_item_id)

        # Change the status of the adj record to Complete
        db(atable.id == adj_id).update(status = 1)

        # Go to the Inventory of the Site which has adjusted these items
        (prefix, resourcename, instance_id) = s3db.get_instance(s3db.org_site,
                                                                site_id)
        if resourcename == "warehouse" and \
           settings.get_inv_warehouse_free_capacity_calculated():
            # Update the Free Capacity for this Warehouse
            inv_warehouse_free_capacity(site_id)

        if stock_cards:
            inv_stock_card_update(inv_item_ids, comments = "Adjustment")

        # Call on_inv_adj_close hook if-configured
        #tablename = "inv_adj"
        #on_inv_adj_close = s3db.get_config(tablename, "on_inv_adj_close")
        #if on_inv_adj_close:
        #    adj_record.id = adj_id
        #    on_inv_adj_close(adj_record)

        redirect(URL(c = prefix,
                     f = resourcename,
                     args = [instance_id,
                             "inv_item",
                             ],
                     ))

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_adj_create_onaccept(form):
        """
           When an adjustment record is created and it is of type inventory
           then an adj_item record for each inv_inv_item in the site will be
           created. If needed, extra adj_item records can be created later.
        """

        record_id = form.vars.id
        db = current.db
        inv_item_table = db.inv_inv_item
        adjitemtable = db.inv_adj_item
        adjtable = db.inv_adj
        adj_rec = adjtable[record_id]
        if adj_rec.category == 1:
            site_id = form.vars.site_id
            # Only get inv. item with a positive quantity
            query = (inv_item_table.site_id == site_id) & \
                    (inv_item_table.quantity > 0) & \
                    (inv_item_table.deleted == False)
            rows = db(query).select(inv_item_table.id,
                                    inv_item_table.item_id,
                                    inv_item_table.item_pack_id,
                                    inv_item_table.quantity,
                                    inv_item_table.currency,
                                    inv_item_table.status,
                                    inv_item_table.pack_value,
                                    inv_item_table.expiry_date,
                                    inv_item_table.bin,
                                    inv_item_table.layout_id,
                                    inv_item_table.owner_org_id,
                                    )
            for inv_item in rows:
                # add an adjustment item record
                adjitemtable.insert(reason = 0,
                                    adj_id = record_id,
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
                                    layout_id = inv_item.layout_id,
                                    old_owner_org_id = inv_item.owner_org_id,
                                    new_owner_org_id = inv_item.owner_org_id,
                                    )

# =============================================================================
class InventoryCommitModel(S3Model):
    """
        Model for Commits (Pledges) to Inventory Requisitions
    """

    names = ("inv_commit",
             "inv_commit_id",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        add_components = self.add_components

        settings = current.deployment_settings

        commit_value = settings.get_inv_commit_value()
        unsolicited_commit = settings.get_inv_commit_without_request()

        # Site/Committer defaults
        committer_is_author = settings.get_inv_committer_is_author()
        if committer_is_author:
            site_default = auth.user.site_id if auth.is_logged_in() else None
            committer_default = auth.s3_logged_in_person()
        else:
            site_default = None
            committer_default = None

        # Dropdown or Autocomplete for Committing Site?
        if settings.get_org_site_autocomplete():
            site_widget = S3SiteAutocompleteWidget()
            site_comment = DIV(_class = "tooltip",
                               _title = "%s|%s" % (T("From Facility"),
                                                   current.messages.AUTOCOMPLETE_HELP,
                                                   ),
                               )
        else:
            site_widget = None
            site_comment = None

        # ---------------------------------------------------------------------
        # Commitments (Pledges)
        #
        tablename = "inv_commit"
        self.define_table(tablename,
                          self.super_link("site_id", "org_site",
                                          comment = site_comment,
                                          default = site_default,
                                          label = T("From Facility"),
                                          # Non-Item Requests make False in the prep
                                          readable = True,
                                          writable = True,
                                          represent = self.org_site_represent,
                                          updateable = True,
                                          widget = site_widget,
                                          ),
                          # Used for reporting on where Donations originated
                          self.gis_location_id(readable = False,
                                               writable = False
                                               ),
                          # Non-Item Requests make True in the prep
                          self.org_organisation_id(readable = False,
                                                   writable = False
                                                   ),
                          self.inv_req_id(empty = not unsolicited_commit,
                                          ),
                          s3_datetime(default = "now",
                                      represent = "date",
                                      ),
                          s3_datetime("date_available",
                                      label = T("Date Available"),
                                      represent = "date",
                                      ),
                          self.pr_person_id("committer_id",
                                            default = committer_default,
                                            label = T("Committed By"),
                                            comment = self.pr_person_comment(child="committer_id"),
                                            ),
                          # @ToDo: Calculate this from line items in Item Commits
                          Field("value", "double",
                                label = T("Estimated Value"),
                                readable = commit_value,
                                writable = commit_value,
                                ),
                          # @ToDo: Move this into a Currency Widget for the value field
                          s3_currency(readable = commit_value,
                                      writable = commit_value,
                                      ),
                          Field("cancel", "boolean",
                                default = False,
                                label = T("Cancel"),
                                readable = False,
                                writable = False,
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        filter_widgets = [
            S3TextFilter(["committer_id$first_name",
                          "committer_id$middle_name",
                          "committer_id$last_name",
                          "site_id$name",
                          "comments",
                          "req_id$name",
                          "organisation_id$name"
                          ],
                         label = T("Search"),
                         comment = T("Search for a commitment by Committer name, Request ID, Site or Organization."),
                         ),
            S3LocationFilter("location_id",
                             hidden = True,
                             ),
            S3DateFilter("date",
                         # Better to default (easier to customise/consistency)
                         #label = T("Date"),
                         hide_time = True,
                         comment = T("Search for commitments made between these dates."),
                         hidden = True,
                         ),
            S3DateFilter("date_available",
                         # Better to default (easier to customise/consistency)
                         #label = T("Date Available"),
                         hide_time = True,
                         comment = T("Search for commitments available between these dates."),
                         hidden = True,
                         ),
            ]

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Make Commitment"),
            title_display = T("Commitment Details"),
            title_list = T("Commitments"),
            title_update = T("Edit Commitment"),
            label_list_button = T("List Commitments"),
            label_delete_button = T("Delete Commitment"),
            msg_record_created = T("Commitment Added"),
            msg_record_modified = T("Commitment Updated"),
            msg_record_deleted = T("Commitment Canceled"),
            msg_list_empty = T("No Commitments"))

        # Reusable Field
        commit_represent = inv_CommitRepresent()
        commit_id = S3ReusableField("commit_id", "reference %s" % tablename,
                                    label = T("Commitment"),
                                    ondelete = "CASCADE",
                                    represent = commit_represent,
                                    requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "inv_commit.id",
                                                              commit_represent,
                                                              orderby = "inv_commit.date",
                                                              sort = True,
                                                              )),
                                    sortby = "date",
                                    )

        list_fields = ["site_id",
                       "req_id",
                       "committer_id",
                       (T("Committed Items"), "commit_item.req_item_id$item_id"),
                       "date",
                       "date_available",
                       "comments",
                       ]

        self.configure(tablename,
                       context = {"location": "location_id",
                                  "organisation": "organisation_id",
                                  "request": "req_id",
                                  # We want 'For Sites XX' not 'From Site XX'
                                  #"site": "site_id",
                                  "site": "req_id$site_id",
                                  },
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       # Commitments should only be made to a specific request
                       listadd = unsolicited_commit,
                       onaccept = self.commit_onaccept,
                       ondelete = self.commit_ondelete,
                       )

        # Components
        add_components(tablename,
                       # Committed Items
                       inv_commit_item = "commit_id",
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"inv_commit_id": commit_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def commit_onaccept(form):
        """
            On-accept actions for commits:
                - set location_id
                - update status of request & components
        """

        db = current.db
        s3db = current.s3db

        form_vars = form.vars
        try:
            commit_id = form_vars.id
        except AttributeError:
            return
        if not commit_id:
            return

        ctable = s3db.inv_commit
        cdata = {}

        site_id = form_vars.get("site_id")
        if site_id:
            # Set location_id to location of site
            stable = s3db.org_site
            site = db(stable.site_id == site_id).select(stable.location_id,
                                                        limitby = (0, 1),
                                                        ).first()
            if site and site.location_id:
                cdata["location_id"] = site.location_id

        # Update the commit
        if cdata:
            db(ctable.id == commit_id).update(**cdata)

        # Find the request
        rtable = s3db.inv_req
        query = (ctable.id == commit_id) & \
                (rtable.id == ctable.req_id)
        req = db(query).select(rtable.id,
                               rtable.req_status,
                               rtable.commit_status,
                               limitby = (0, 1),
                               ).first()
        if not req:
            return

        # Update committed quantities and request status
        req_update_commit_quantities_and_status(req)

    # -------------------------------------------------------------------------
    @staticmethod
    def commit_ondelete(row):
        """
            Update Status of Request & components
        """

        db = current.db
        s3db = current.s3db
        commit_id = row.id

        # Find the request
        ctable = s3db.inv_commit
        fks = db(ctable.id == commit_id).select(ctable.deleted_fk,
                                                limitby = (0, 1),
                                                ).first().deleted_fk
        req_id = json.loads(fks)["req_id"]
        rtable = s3db.inv_req
        req = db(rtable.id == req_id).select(rtable.id,
                                             rtable.commit_status,
                                             limitby = (0, 1),
                                             ).first()
        if not req:
            return

        # Update committed quantities and request status
        req_update_commit_quantities_and_status(req)

# =============================================================================
class InventoryCommitItemModel(S3Model):
    """
        Model for Committed (Pledged) Items for Inventory Requisitions

        @ToDo: Move to inv_commit_item
    """

    names = ("inv_commit_item",
             )

    def model(self):

        T = current.T

        # -----------------------------------------------------------------
        # Commitment Items
        # @ToDo: Update the req_item_id in the commit_item if the req_id of the commit is changed
        #
        tablename = "inv_commit_item"
        self.define_table(tablename,
                          self.inv_commit_id(),
                          #item_id,
                          #supply_item_id(),
                          self.inv_req_item_id(),
                          self.supply_item_pack_id(),
                          Field("quantity", "double", notnull=True,
                                label = T("Quantity"),
                                ),
                          Field.Method("pack_quantity",
                                       SupplyItemPackQuantity(tablename)
                                       ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Item to Commitment"),
            title_display = T("Commitment Item Details"),
            title_list = T("Commitment Items"),
            title_update = T("Edit Commitment Item"),
            label_list_button = T("List Commitment Items"),
            label_delete_button = T("Delete Commitment Item"),
            msg_record_created = T("Commitment Item added"),
            msg_record_modified = T("Commitment Item updated"),
            msg_record_deleted = T("Commitment Item deleted"),
            msg_list_empty = T("No Commitment Items currently registered"))

        self.configure(tablename,
                       extra_fields = ["item_pack_id"],
                       onaccept = self.commit_item_onaccept,
                       ondelete = self.commit_item_ondelete,
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {# Used by commit_req() controller (TODO make module-global then?)
                "inv_commit_item_onaccept": self.commit_item_onaccept,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def commit_item_onaccept(form):
        """
            On-accept actions for committed items
                - update the commit quantities and -status of the request
        """

        db = current.db

        try:
            item_id = form.vars.id
        except AttributeError:
            return

        # Get the req
        rtable = db.inv_req
        ctable = db.inv_commit
        itable = db.inv_commit_item
        query = (itable.id == item_id) & \
                (ctable.id == itable.commit_id) & \
                (rtable.id == ctable.req_id)
        req = db(query).select(rtable.id,
                               rtable.req_status,
                               rtable.commit_status,
                               limitby = (0, 1),
                               ).first()
        if not req:
            return

        req_update_commit_quantities_and_status(req)

    # -------------------------------------------------------------------------
    @staticmethod
    def commit_item_ondelete(row):
        """
            On-delete actions for committed items
                - update the commit quantities and -status of the request
        """

        db = current.db
        s3db = current.s3db

        # Get the commit_id
        table = s3db.inv_commit_item
        row = db(table.id == row.id).select(table.deleted_fk,
                                            limitby = (0, 1),
                                            ).first()
        try:
            deleted_fk = json.loads(row.deleted_fk)
        except:
            return

        commit_id = deleted_fk.get("commit_id")
        if commit_id:
            ctable = s3db.inv_commit
            rtable = s3db.inv_req
            query = (ctable.id == commit_id) & \
                    (rtable.id == ctable.req_id)
            req = db(query).select(rtable.id,
                                   rtable.req_status,
                                   rtable.commit_status,
                                   limitby = (0, 1),
                                   ).first()
            if req:
                req_update_commit_quantities_and_status(req)

# =============================================================================
class InventoryKittingModel(S3Model):
    """
        A module to manage the Kitting of Inventory Items
    """

    names = ("inv_kitting",
             "inv_kitting_item",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        configure = self.configure
        define_table = self.define_table

        item_id = self.supply_item_id
        item_pack_id = self.supply_item_pack_id

        is_float_represent = IS_FLOAT_AMOUNT.represent
        float_represent = lambda v: is_float_represent(v, precision=2)
        string_represent = lambda v: v if v else NONE

        settings = current.deployment_settings
        bin_site_layout = settings.get_inv_bin_site_layout()
        SITE_LABEL = settings.get_org_site_label()

        # ---------------------------------------------------------------------
        # Kittings
        # - process for creating Kits from component items
        #
        tablename = "inv_kitting"
        define_table(tablename,
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     self.super_link("site_id", "org_site",
                                     default = auth.user.site_id if auth.is_logged_in() else None,
                                     empty = False,
                                     label = T("By %(site)s") % {"site": SITE_LABEL},
                                     instance_types = auth.org_site_types,
                                     not_filterby = "obsolete",
                                     not_filter_opts = (True,),
                                     readable = True,
                                     writable = True,
                                     represent = self.org_site_represent,
                                     updateable = True,
                                     #widget = S3SiteAutocompleteWidget(),
                                     ),
                     item_id(label = T("Kit"),
                             requires = IS_ONE_OF(db, "supply_item.id",
                                                  self.supply_item_represent,
                                                  filterby = "kit",
                                                  filter_opts = (True,),
                                                  sort = True
                                                  ),
                             widget = S3AutocompleteWidget("supply", "item",
                                                           filter = "item.kit=1",
                                                           ),
                             # Needs better workflow as no way to add the Kit Items
                             #comment = S3PopupLink(c = "supply",
                             #                      f = "item",
                             #                      label = T("Create Kit"),
                             #                      title = T("Kit"),
                             #                      tooltip = T("Type the name of an existing catalog kit OR Click 'Create Kit' to add a kit which is not in the catalog."),
                             #                      ),
                             comment = DIV(_class = "tooltip",
                                           _title = "%s|%s" % (T("Kit"),
                                                               T("Type the name of an existing catalog kit"),
                                                               ),
                                           ),
                             ),
                     item_pack_id(),
                     Field("quantity", "double",
                           label = T("Quantity"),
                           represent = float_represent,
                           requires = IS_FLOAT_AMOUNT(minimum = 1.0),
                           ),
                     s3_date(comment = DIV(_class = "tooltip",
                                           _title = "%s|%s" % (T("Date Repacked"),
                                                               T("Will be filled automatically when the Item has been Repacked"),
                                                               ),
                                           ),
                            ),
                     self.inv_req_ref(writable = True),
                     self.pr_person_id("repacked_id",
                                       default = auth.s3_logged_in_person(),
                                       label = T("Repacked By"),
                                       ondelete = "SET NULL",
                                       #comment = self.pr_person_comment(child = "repacked_id")),
                                       ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Kitting"),
            title_display = T("Kitting Details"),
            title_list = T("Kittings"),
            title_update = T("Kitting"),
            label_list_button = T("List Kittings"),
            label_delete_button = T("Delete Kitting"),
            msg_record_created = T("Kitting completed"),
            msg_record_modified = T("Kitting updated"),
            msg_record_deleted = T("Kitting canceled"),
            msg_list_empty = T("No Kittings"))

        # Components
        self.add_components(tablename,
                            inv_kitting_item = {"name": "item",
                                                "joinby": "kitting_id",
                                                },
                            )

        # Resource configuration
        configure(tablename,
                  create_next = URL(c="inv", f="kitting",
                                    args = ["[id]", "item"],
                                    ),
                  create_onaccept = self.inv_kitting_onaccept,
                  list_fields = ["site_id",
                                 "req_ref",
                                 "quantity",
                                 "date",
                                 "repacked_id",
                                 ],
                  onvalidation = self.inv_kitting_onvalidate,
                  )

        # ---------------------------------------------------------------------
        # Kitting Items
        # - Component items of Kits which can be used to build a pick-list
        #
        tablename = "inv_kitting_item"
        define_table(tablename,
                     Field("site_id", "reference org_site",
                           readable = False,
                           writable = False,
                           ),
                     Field("kitting_id", "reference inv_kitting",
                           readable = False,
                           writable = False,
                           ),
                     item_id(writable = False),
                     item_pack_id(writable = False),
                     Field("quantity", "double",
                           label = T("Quantity"),
                           represent = float_represent,
                           writable = False,
                           ),
                     Field("bin", length=16,
                           label = T("Bin"),
                           represent = string_represent,
                           requires = IS_LENGTH(16),
                           readable = not bin_site_layout,
                           #writable = not bin_site_layout,
                           writable = False,
                           ),
                     self.org_site_layout_id(label = T("Bin"),
                                             readable = bin_site_layout,
                                             #writable = bin_site_layout,
                                             writable = False,
                                             ),
                     Field("item_source_no", length=16,
                           label = inv_itn_label(),
                           represent = string_represent,
                           requires = [IS_LENGTH(16),
                                       IS_NOT_EMPTY_STR(),
                                       ]
                           ),
                     self.inv_item_id(ondelete = "RESTRICT",
                                      readable = False,
                                      writable = False,
                                      ),
                     #s3_comments(),
                     *s3_meta_fields())

        # Resource configuration
        configure(tablename,
                  deletable = False,
                  editable = False,
                  insertable = False,
                  )

        #----------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_kitting_onvalidate(form):
        """
            Check that we have sufficient inv_item in stock to build the kits
        """

        form_vars = form.vars
        item_id = form_vars.item_id
        item_pack_id = form_vars.item_pack_id
        quantity = form_vars.quantity
        site_id = form_vars.site_id

        db = current.db
        s3db = current.s3db
        ktable = s3db.supply_kit_item
        ptable = db.supply_item_pack
        iitable = s3db.inv_inv_item

        # Get contents of this kit
        query = (ktable.parent_item_id == item_id)
        rows = db(query).select(ktable.item_id,
                                ktable.quantity,
                                ktable.item_pack_id,
                                )

        # How many kits are we building?
        p_id_field = ptable.id
        p_qty_field = ptable.quantity
        pack_qty = db(p_id_field == item_pack_id).select(p_qty_field,
                                                         limitby = (0, 1),
                                                         ).first().quantity
        quantity = quantity * pack_qty

        max_kits = None

        ii_pack_field = iitable.item_pack_id
        ii_qty_field = iitable.quantity
        ii_expiry_field = iitable.expiry_date

        # Base Query: The Facility at which we're building these kits
        # Filter out Stock which is in Bad condition or Expired
        squery = (iitable.site_id == site_id) & \
                 (iitable.deleted == False) & \
                 ((ii_expiry_field >= current.request.now) | ((ii_expiry_field == None))) & \
                 (iitable.status == 0)

        # Loop through each supply_item in the kit
        for record in rows:
            # How much of this supply_item is required per kit?
            pack_qty = db(p_id_field == record.item_pack_id).select(p_qty_field,
                                                                    limitby = (0, 1),
                                                                    ).first().quantity
            one_kit = record.quantity * pack_qty

            # How much of this supply_item do we have in stock?
            stock_amount = 0
            query = squery & (iitable.item_id == record.item_id)
            wh_items = db(query).select(#iitable.id,
                                        ii_qty_field,
                                        ii_pack_field,
                                        )
            for wh_item in wh_items:
                pack_qty = db(p_id_field == wh_item.item_pack_id).select(p_qty_field,
                                                                         limitby = (0, 1),
                                                                         ).first().quantity
                amount = wh_item.quantity * pack_qty
                stock_amount += amount

            # How many Kits can we create based on this item?
            kits = stock_amount / one_kit
            if max_kits is None:
                # 1st run so this item starts the list
                max_kits = kits
            else:
                # Reduce the total possible if less than for previous items
                if kits < max_kits:
                    max_kits = kits

        # @ToDo: Save the results for the onaccept?

        if max_kits is None:
            form.errors.item_id = current.T("This kit hasn't got any Kit Items defined")
        elif max_kits < quantity:
            form.errors.quantity = current.T("You can only make %d kit(s) with the available stock") % \
                                        int(max_kits)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_kitting_onaccept(form):
        """
            Adjust the Inventory stocks
                reduce the components & increase the kits
            - picks items which have an earlier expiry_date where they have them,
              earlier purchase_data otherwise
            Provide a pick list to ensure that the right stock items are used
            to build the kits: inv_kitting_item
        """

        form_vars = form.vars
        kitting_id = form_vars.id
        item_id = form_vars.item_id
        item_pack_id = form_vars.item_pack_id
        quantity = form_vars.quantity
        site_id = form_vars.site_id

        db = current.db
        s3db = current.s3db
        ktable = s3db.supply_kit_item
        ptable = db.supply_item_pack
        iitable = s3db.inv_inv_item
        insert = s3db.inv_kitting_item.insert

        bin_site_layout = current.deployment_settings.get_inv_bin_site_layout()

        # Get contents of this kit
        query = (ktable.parent_item_id == item_id)
        rows = db(query).select(ktable.item_id,
                                ktable.quantity,
                                ktable.item_pack_id,
                                )

        # How many kits are we building?
        p_id_field = ptable.id
        p_qty_field = ptable.quantity
        pack_qty = db(p_id_field == item_pack_id).select(p_qty_field,
                                                         limitby = (0, 1),
                                                         ).first().quantity
        quantity = quantity * pack_qty

        ii_id_field = iitable.id
        if bin_site_layout:
            ii_bin_field = iitable.layout_id
        else:
            ii_bin_field = iitable.bin
        ii_pack_field = iitable.item_pack_id
        ii_qty_field = iitable.quantity
        ii_expiry_field = iitable.expiry_date
        ii_purchase_field = iitable.purchase_date
        ii_src_field = iitable.item_source_no

        # Match Stock based on oldest expiry date or purchase date
        orderby = ii_expiry_field | ii_purchase_field

        # We set expiry date of the kit to the oldest expiry date of the components
        expiry_date = None

        # Base Query: The Facility at which we're building these kits
        # Filter out Stock which is in Bad condition or Expired
        squery = (iitable.site_id == site_id) & \
                 (iitable.deleted == False) & \
                 ((ii_expiry_field >= current.request.now) | ((ii_expiry_field == None))) & \
                 (iitable.status == 0)

        # Loop through each supply_item in the kit
        for record in rows:
            # How much of this supply_item is required per kit?
            pack_qty = db(p_id_field == record.item_pack_id).select(p_qty_field,
                                                                    limitby = (0, 1),
                                                                    ).first().quantity
            one_kit = record.quantity * pack_qty

            # How much is required for all Kits?
            required = one_kit * quantity

            # List of what we have available in stock
            ritem_id = record.item_id
            query = squery & (iitable.item_id == ritem_id)

            wh_items = db(query).select(ii_id_field,
                                        ii_qty_field,
                                        ii_expiry_field,
                                        ii_purchase_field, # Included just for orderby on Postgres
                                        ii_pack_field,
                                        ii_bin_field,
                                        ii_src_field,
                                        orderby = orderby,
                                        )
            for wh_item in wh_items:
                # Get the pack_qty
                pack_qty = db(p_id_field == wh_item.item_pack_id).select(p_qty_field,
                                                                         limitby = (0, 1),
                                                                         ).first().quantity
                # How many of this item can we use for these kits?
                amount = wh_item.quantity * pack_qty
                # How many of this item will we use for the kits?
                if amount > required:
                    # Use only what is required
                    amount = required
                #else:
                #    # We use all

                if wh_item.expiry_date:
                    if expiry_date is None:
                        # No expiry date set so this item starts the list
                        expiry_date = wh_item.expiry_date
                    else:
                        # Shorten the expiry date if less than for previous items
                        if wh_item.expiry_date < expiry_date:
                            expiry_date = wh_item.expiry_date

                # @ToDo: Record which components are to be used for the kits
                # Store results in a table?

                # Remove from stock
                inv_remove(wh_item, amount)

                # Add to Pick List
                new_record = {"site_id": site_id,
                              "kitting_id": kitting_id,
                              "item_id": ritem_id,
                              "item_pack_id": wh_item.item_pack_id,
                              "item_source_no": wh_item.item_source_no,
                              "quantity": amount,
                              "inv_item_id": wh_item.id,
                              }
                if bin_site_layout:
                    new_record["layout_id"] = wh_item.layout_id
                else:
                    new_record["bin"] = wh_item.bin
                insert(**new_record)

                # Update how much is still required
                required -= amount

                if not required:
                    # No more required: move on to the next component
                    break

        # Add Kits to Stock
        # @ToDo: Keep track of Donor? Owner?
        # @ToDo: Update Pack Value
        new_id = iitable.insert(site_id = site_id,
                                item_id = item_id,
                                item_pack_id = item_pack_id,
                                quantity = quantity,
                                expiry_date = expiry_date,
                                )
        s3db.update_super(iitable, {"id": new_id})

# =============================================================================
class InventoryMinimumModel(S3Model):
    """
        Manage Minimum Stock levels for Sites

        Used by: RMS
    """

    names = ("inv_minimum",
             )

    def model(self):

        T = current.T
        auth = current.auth

        WAREHOUSE = T(current.deployment_settings.get_inv_facility_label())

        # ---------------------------------------------------------------------
        # Minimum Stock Levels
        #

        tablename = "inv_minimum"
        self.define_table(tablename,
                          # This is a component, so needs to be a super_link
                          # - can't override field name, ondelete or requires
                          self.super_link("site_id", "org_site",
                                          default = auth.user.site_id if auth.is_logged_in() else None,
                                          empty = False,
                                          label = WAREHOUSE,
                                          instance_types = auth.org_site_types,
                                          not_filterby = "obsolete",
                                          not_filter_opts = (True,),
                                          ondelete = "CASCADE",
                                          represent = self.org_site_represent,
                                          readable = True,
                                          writable = True,
                                          updateable = True,
                                          # Comment these to use a Dropdown & not an Autocomplete
                                          #widget = S3SiteAutocompleteWidget(),
                                          #comment = DIV(_class = "tooltip",
                                          #              _title = "%s|%s" % (WAREHOUSE,
                                          #                                  messages.AUTOCOMPLETE_HELP)),
                                          ),
                          self.supply_item_id(ondelete = "RESTRICT",
                                              required = True,
                                              ),
                          Field("quantity", "double", notnull=True,
                                default = 0.0,
                                label = T("Quantity"),
                                represent = lambda v: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2),
                                requires = IS_FLOAT_AMOUNT(minimum=0.0),
                                ),
                          s3_comments(),
                          *s3_meta_fields()
                          )

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
           label_create = T("Add Minimum Stock Level"),
           title_display = T("Minimum Stock Level Details"),
           title_list = T("Minimum Stock Levels"),
           title_update = T("Edit Minimum Stock Level"),
           label_list_button = T("List Minimum Stock Levels"),
           label_delete_button = T("Delete Minimum Stock Level"),
           msg_record_created = T("Minimum Stock Level added"),
           msg_record_modified = T("Minimum Stock Level updated"),
           msg_record_deleted = T("Minimum Stock Level deleted"),
           msg_list_empty = T("No Minimum Stock Levels currently registered"),
           )

        return {}

# =============================================================================
class InventoryOrderItemModel(S3Model):
    """
        Simple Item Ordering for fulfilment of Inventory Requisitions
        - for when Procurement model isn't being used
    """

    names = ("inv_order_item",
             )

    def model(self):

        T = current.T
        NONE = current.messages["NONE"]

        # -----------------------------------------------------------------
        # Request Item Ordering
        #
        tablename = "inv_order_item"
        self.define_table(tablename,
                          self.inv_req_item_id(empty = False,
                                               readable = False, # Hidden
                                               writable = False,
                                               ),
                          self.inv_req_id(empty = False,
                                          writable = False, # Auto-populated
                                          ),
                          self.supply_item_id(empty = False,
                                              writable = False, # Auto-populated
                                              ),
                          self.supply_item_pack_id(writable = False, # Auto-populated
                                                   ),
                          Field("quantity", "double", notnull=True,
                                default = 0.0,
                                label = T("Quantity"),
                                represent = lambda v: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2),
                                #requires = IS_FLOAT_AMOUNT(minimum=0.0),
                                writable = False, # Auto-populated
                                ),
                          Field("purchase_ref",
                                label = T("%(PO)s Number") % \
                                    {"PO": current.deployment_settings.get_proc_shortname()},
                                represent = lambda v: v if v else NONE,
                                ),
                          self.inv_recv_id(label = T("Received Shipment"),
                                           ),
                          *s3_meta_fields())

        self.configure(tablename,
                       insertable = False,
                       )

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            #label_create = T("Create Purchase Item"),
            title_display = T("Purchase Item Details"),
            title_list = T("Purchase Items"),
            title_update = T("Edit Purchase Item"),
            label_list_button = T("List Purchase Items"),
            label_delete_button = T("Delete Purchase Item"),
            #msg_record_created = T("Purchase Item Added"),
            msg_record_modified = T("Purchase Item Updated"),
            msg_record_deleted = T("Purchase Item Deleted"),
            msg_list_empty = T("No Purchase Items"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class InventoryPalletModel(S3Model):
    """
        Pallets model
        https://en.wikipedia.org/wiki/Pallet
    """

    names = ("inv_pallet",
             "inv_pallet_id",
             )

    def model(self):

        T = current.T
        db = current.db

        is_float_represent = IS_FLOAT_AMOUNT.represent
        float_represent = lambda v: is_float_represent(v, precision=3)

        # -----------------------------------------------------------------
        # Pallets
        #
        tablename = "inv_pallet"
        self.define_table(tablename,
                          Field("name", length=64, notnull=True,
                                label = T("Name"),
                                requires = [IS_NOT_EMPTY(),
                                            IS_LENGTH(64),
                                            ]
                                ),
                          Field("width", "double",
                                default = 0.0,
                                label = T("Width"),
                                represent = float_represent,
                                comment = "m",
                                ),
                          Field("length", "double",
                                default = 0.0,
                                label = T("Length"),
                                represent = float_represent,
                                comment = "m",
                                ),
                          Field("depth", "double",
                                default = 0.0,
                                label = T("Depth"),
                                represent = float_represent,
                                comment = "m",
                                ),
                          Field("weight", "double",
                                default = 0.0,
                                label = T("Weight"),
                                represent = float_represent,
                                comment = "kg",
                                ),
                          Field("load_capacity", "double",
                                default = 0.0,
                                label = T("Load Capacity"),
                                represent = float_represent,
                                comment = "kg",
                                ),
                          Field("max_height", "double",
                                default = 0.0,
                                label = T("Maximum Height (m)"),
                                represent = float_represent,
                                comment = T("Not including the Palette"),
                                ),
                          Field("max_volume", "double",
                                default = 0.0,
                                label = T("Maximum Volume"),
                                represent = float_represent,
                                comment = "m3",
                                writable = False,
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Pallet"),
            title_display = T("Pallet Details"),
            title_list = T("Pallets"),
            title_update = T("Edit Pallet"),
            label_list_button = T("List Pallets"),
            label_delete_button = T("Delete Pallet"),
            msg_record_created = T("Pallet Added"),
            msg_record_modified = T("Pallet Updated"),
            msg_record_deleted = T("Pallet Deleted"),
            msg_list_empty = T("No Pallets defined"),
            )

        self.configure(tablename,
                       onaccept = self.inv_pallet_onaccept,
                       )

        # Reusable Field
        represent = S3Represent(lookup = tablename)
        pallet_id = S3ReusableField("pallet_id", "reference %s" % tablename,
                                    label = T("Pallet Type"),
                                    ondelete = "RESTRICT",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "inv_pallet.id",
                                                          represent,
                                                          orderby = "inv_pallet.name",
                                                          sort = True,
                                                          )
                                                ),
                                    sortby = "name",
                                    )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"inv_pallet_id": pallet_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_pallet_onaccept(form):
        """
            Calculate the Max Volume
        """

        form_vars = form.vars
        form_vars_get = form_vars.get

        max_volume = form_vars_get("width") * form_vars_get("length") * form_vars_get("max_height")

        current.db(current.s3db.inv_pallet.id == form_vars.id).update(max_volume = max_volume)

# =============================================================================
class InventoryPalletShipmentModel(S3Model):
    """
        Pallets <> Shipments model
    """

    names = ("inv_send_pallet",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        define_table = self.define_table

        #is_float_represent = IS_FLOAT_AMOUNT.represent
        #float_represent = lambda v: is_float_represent(v, precision=3)

        # -----------------------------------------------------------------
        # Shipment Pallets
        # i.e. Pallets <> Outbound Shipments
        #
        tablename = "inv_send_pallet"
        define_table(tablename,
                     Field("number", "integer",
                           label = T("Number"),
                           ),
                     self.inv_send_id(empty = False,
                                      ondelete = "CASCADE",
                                      ),
                     self.inv_pallet_id(empty = False,
                                        ondelete = "SET NULL",
                                        ),
                     Field("weight", "double",
                           default = 0.0,
                           #label = T("Weight"),
                           #represent = float_represent,
                           #comment = "kg",
                           readable = False,
                           writable = False,
                           ),
                     Field("volume", "double",
                           default = 0.0,
                           #label = T("Volume"),
                           #represent = float_represent,
                           #comment = "m3",
                           readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     Field.Method("weight_max",
                                  self.send_pallet_weight,
                                  ),
                     Field.Method("volume_max",
                                  self.send_pallet_volume,
                                  ),
                     *s3_meta_fields())

        crud_form = S3SQLCustomForm("send_id",
                                    "number",
                                    "pallet_id",
                                    S3SQLInlineComponent("send_pallet_item",
                                                         label = T("Items"),
                                                         fields = [("", "track_item_id")],
                                                         ),
                                    "comments",
                                    )

        list_fields = ["number",
                       "pallet_id",
                       (T("Items"), "send_pallet_item.track_item_id$item_id$code"),
                       (T("Weight (kg)"), "weight_max"),
                       (T("Volume (m3)"), "volume_max"),
                       "comments",
                       ]

        configure(tablename,
                  crud_form = crud_form,
                  extra_fields = ["weight",
                                  "volume",
                                  "pallet_id$load_capacity",
                                  "pallet_id$max_volume",
                                  ],
                  list_fields = list_fields,
                  onvalidation = self.send_pallet_onvalidation,
                  )

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Pallet"),
            title_display = T("Pallet Details"),
            title_list = T("Pallets"),
            title_update = T("Edit Pallet"),
            label_list_button = T("List Pallets"),
            label_delete_button = T("Delete Pallet"),
            msg_record_created = T("Pallet Added"),
            msg_record_modified = T("Pallet Updated"),
            msg_record_deleted = T("Pallet Deleted"),
            msg_list_empty = T("No Pallets defined"),
            )

        self.add_components(tablename,
                            inv_send_pallet_item = "send_pallet_id",
                            )

        # -----------------------------------------------------------------
        # Shipment Pallets <> Shipment Items
        #
        track_item_represent = inv_TrackItemRepresent()

        tablename = "inv_send_pallet_item"
        define_table(tablename,
                     Field("send_pallet_id", "reference inv_send_pallet",
                           ondelete = "CASCADE",
                           requires = IS_ONE_OF(db, "inv_send_pallet.id",
                                                "%(number)s",
                                                orderby = "inv_send_pallet.number",
                                                sort = True,
                                                ),
                           ),
                     Field("track_item_id", "reference inv_track_item",
                           label = T("Item"),
                           ondelete = "CASCADE",
                           represent = track_item_represent,
                           requires = IS_ONE_OF(db, "inv_track_item.id",
                                                track_item_represent,
                                                ),
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = self.send_pallet_item_onaccept,
                  ondelete = self.send_pallet_item_ondelete,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def send_pallet_onvalidation(form):
        """
            Number must be Unique per Shipment
        """

        # @ToDo
        pass

    # -------------------------------------------------------------------------
    @staticmethod
    def send_pallet_item_onaccept(form):
        """
            Update the Weight & Volume of the Shipment's Pallet
        """

        inv_send_pallet_update(form.vars.get("send_pallet_id"))

    # -------------------------------------------------------------------------
    @staticmethod
    def send_pallet_item_ondelete(row):
        """
            Update the Weight & Volume of the Shipment's Pallet
        """

        inv_send_pallet_update(row.send_pallet_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def send_pallet_volume(row):
        """
            Display the Volume of the Shipment's Pallet
            - with capacity
            - in red if over capacity
        """

        try:
            inv_send_pallet = getattr(row, "inv_send_pallet")
        except AttributeError:
            inv_send_pallet = row

        try:
            volume = inv_send_pallet.volume
        except AttributeError:
            # Need to reload the inv_send_pallet
            # Avoid this by adding to extra_fields
            table = current.s3db.inv_send_pallet
            query = (table.id == inv_send_pallet.id)
            inv_send_pallet = current.db(query).select(table.id,
                                                       table.volume,
                                                       limitby = (0, 1),
                                                       ).first()
            volume = inv_send_pallet.volume if inv_send_pallet else None

        if volume is None:
            return current.messages["NONE"]

        volume = round(volume, 3)

        try:
            inv_pallet = getattr(row, "inv_pallet")
            max_volume = inv_pallet.max_volume
        except KeyError:
            # Need to load the inv_pallet
            # Avoid this by adding to extra_fields
            s3db = current.s3db
            ttable = s3db.inv_send_pallet
            ptable = s3db.inv_pallet
            query = (table.id == inv_send_pallet.id) & \
                    (table.pallet_id == ptable.id)
            inv_pallet = current.db(query).select(ptable.max_volume,
                                                  limitby = (0, 1),
                                                  ).first()
            max_volume = inv_pallet.max_volume

        if not max_volume:
            return volume

        max_volume = round(max_volume, 3)
        
        if volume > max_volume:
            return SPAN(SPAN(volume,
                             _class = "expired",
                             ),
                        " / %s" % max_volume,
                        )
        else:
            return "%s / %s" % (volume,
                                max_volume,
                                )

    # -------------------------------------------------------------------------
    @staticmethod
    def send_pallet_weight(row):
        """
            Display the Weight of the Shipment's Pallet
            - with capacity
            - in red if over capacity
        """

        try:
            inv_send_pallet = getattr(row, "inv_send_pallet")
        except AttributeError:
            inv_send_pallet = row

        try:
            weight = inv_send_pallet.weight
        except AttributeError:
            # Need to reload the inv_send_pallet
            # Avoid this by adding to extra_fields
            table = current.s3db.inv_send_pallet
            query = (table.id == inv_send_pallet.id)
            inv_send_pallet = current.db(query).select(table.id,
                                                       table.weight,
                                                       limitby = (0, 1),
                                                       ).first()
            weight = inv_send_pallet.weight if inv_send_pallet else None

        if weight is None:
            return current.messages["NONE"]

        weight = round(weight, 3)

        try:
            inv_pallet = getattr(row, "inv_pallet")
            load_capacity = inv_pallet.load_capacity
        except KeyError:
            # Need to load the inv_pallet
            # Avoid this by adding to extra_fields
            s3db = current.s3db
            ttable = s3db.inv_send_pallet
            ptable = s3db.inv_pallet
            query = (table.id == inv_send_pallet.id) & \
                    (table.pallet_id == ptable.id)
            inv_pallet = current.db(query).select(ptable.load_capacity,
                                                  limitby = (0, 1),
                                                  ).first()
            load_capacity = inv_pallet.load_capacity

        if not load_capacity:
            return weight

        load_capacity = round(load_capacity, 3)
        
        if weight > load_capacity:
            return SPAN(SPAN(weight,
                             _class = "expired",
                             ),
                        " / %s" % load_capacity,
                        )
        else:
            return "%s / %s" % (weight,
                                load_capacity,
                                )

# =============================================================================
class InventoryRequisitionModel(S3Model):
    """
        Model for Requisitions for Inventory Items
        - i.e. Consumable Goods, which are not to be managed as Assets

        Can be used for both raising Requisitions & fulfilling them
        - stands separate from the Req module

        In the future, this may be used for fulfilling Inventory Requisitions raised via req_requisition
    """

    names = ("inv_req",
             "inv_req_id",
             "inv_req_ref",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        s3 = current.response.s3
        settings = current.deployment_settings

        messages = current.messages
        NONE = messages["NONE"]
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        AUTOCOMPLETE_HELP = messages.AUTOCOMPLETE_HELP

        add_components = self.add_components
        crud_strings = s3.crud_strings
        set_method = self.set_method
        super_link = self.super_link

        person_id = self.pr_person_id
        req_status_field = req_status()

        # ---------------------------------------------------------------------
        # Model Options
        #
        ask_security = settings.get_inv_req_ask_security()
        ask_transport = settings.get_inv_req_ask_transport()
        date_writable = settings.get_inv_req_date_writable()
        multiple_req_items = settings.get_inv_multiple_req_items()
        recurring = settings.get_inv_req_recurring()
        req_status_writable = settings.get_inv_req_status_writable()
        requester_label = settings.get_inv_requester_label()
        transit_status =  settings.get_inv_req_show_quantity_transit()
        use_commit = settings.get_inv_use_commit()
        use_req_number = settings.get_inv_use_req_number()
        use_workflow = settings.get_inv_req_workflow()

        # Defaults for Requesting Site and Requester
        requester_is_author = settings.get_inv_requester_is_author()
        if requester_is_author and auth.s3_logged_in() and auth.user:
            site_default = auth.user.site_id
            requester_default = auth.s3_logged_in_person()
        else:
            site_default = None
            requester_default = None

        # Dropdown or Autocomplete for Requesting Site?
        if settings.get_org_site_autocomplete():
            site_widget = S3SiteAutocompleteWidget()
            site_comment = S3PopupLink(c = "org",
                                       f = "facility",
                                       vars = {"child": "site_id"},
                                       title = T("Create Facility"),
                                       tooltip = AUTOCOMPLETE_HELP,
                                       )
        else:
            site_widget = None
            site_comment = S3PopupLink(c = "org",
                                       f = "facility",
                                       vars = {"child": "site_id"},
                                       title = T("Create Facility"),
                                       )

        # Workflow options
        workflow_opts = {1: T("Draft"),
                         2: T("Submitted for Approval"),
                         3: T("Approved"),
                         4: T("Completed"),
                         5: T("Cancelled"),
                         }
        if use_workflow:
            workflow_default = 1 # Draft
            workflow_status_requires = IS_IN_SET(workflow_opts)
        else:
            # Don't make assumptions
            workflow_default = None
            workflow_status_requires = IS_EMPTY_OR(IS_IN_SET(workflow_opts))

        # ---------------------------------------------------------------------
        # Request Reference
        #
        req_ref = S3ReusableField("req_ref", "string",
                                  label = T("%(REQ)s Number") %
                                          {"REQ": settings.get_inv_req_shortname()},
                                  writable = False,
                                  )

        # ---------------------------------------------------------------------
        # Requests
        #
        tablename = "inv_req"
        self.define_table(tablename,
                          # Instance
                          super_link("doc_id", "doc_entity"),
                          req_ref(# Adds no value when not using show_link
                                  #represent = inv_ReqRefRepresent(),
                                  readable = use_req_number,
                                  writable = use_req_number,
                                  widget = lambda f, v: \
                                    StringWidget.widget(f, v, _placeholder = T("Leave blank to have this autogenerated"))
                                  ),
                          s3_datetime(default = "now",
                                      label = T("Date Requested"),
                                      past = 8760, # Hours, so 1 year
                                      future = 0,
                                      readable = date_writable,
                                      writable = date_writable,
                                      #represent = "date",
                                      #widget = "date",
                                      ),
                          req_priority()(),
                          # This is a component, so needs to be a super_link
                          # - can't override field name, ondelete or requires
                          super_link("site_id", "org_site",
                                     comment = site_comment,
                                     default = site_default,
                                     empty = False,
                                     filterby = "obsolete",
                                     filter_opts = (False,),
                                     instance_types = auth.org_site_types,
                                     label = T("Requested For Facility"),
                                     readable = True,
                                     represent = self.org_site_represent,
                                     updateable = True,
                                     widget = site_widget,
                                     writable = True,
                                     ),
                          # Donations: What will the Items be used for?; People: Task Details
                          s3_comments("purpose",
                                      comment = "",
                                      label = T("Purpose"),
                                      # Only-needed for summary mode (unused)
                                      #represent = self.req_purpose_represent,
                                      represent = lambda s: s if s else NONE,
                                      ),
                          Field("is_template", "boolean",
                                default = False,
                                label = T("Recurring Request?"),
                                represent = s3_yes_no_represent,
                                readable = recurring,
                                writable = recurring,
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Recurring Request?"),
                                                                T("If this is a request template to be added repeatedly then the schedule can be set on the next page."))),
                                ),
                          s3_datetime("date_required",
                                      label = T("Date Needed By"),
                                      past = 1, # Allow time for people to fill out form
                                      future = 8760, # Hours, so 1 year
                                      #represent = "date",
                                      #widget = "date",
                                      ),
                          # Not needed for consumable goods, i.e. Inventory Requisitions:
                          #s3_datetime("date_required_until",
                          #            label = T("Date Required Until"),
                          #            past = 0,
                          #            future = 8760, # Hours, so 1 year
                          #            readable = False,
                          #            writable = False
                          #            ),
                          person_id("requester_id",
                                    default = requester_default,
                                    empty = settings.get_inv_requester_optional(),
                                    label = requester_label,
                                    represent = self.pr_PersonRepresentContact(link_contacts = True),
                                    #writable = False,
                                    comment = S3PopupLink(c = "pr",
                                                          f = "person",
                                                          vars = {"child": "requester_id",
                                                                  "parent": "req",
                                                                  },
                                                          title = crud_strings["pr_person"].label_create,
                                                          tooltip = AUTOCOMPLETE_HELP,
                                                          ),
                                    ),
                          person_id("assigned_to_id", # This field should be in inv_commit, but that complicates the UI
                                    label = T("Assigned To"),
                                    readable = False,
                                    writable = False,
                                    ),
                          person_id("approved_by_id",
                                    label = T("Approved By"),
                                    readable = False,
                                    writable = False,
                                    ),
                          person_id("request_for_id",
                                    #default = auth.s3_logged_in_person(),
                                    label = T("Requested For"),
                                    readable = False,
                                    writable = False,
                                    ),
                          Field("transport_req", "boolean",
                                label = T("Transportation Required"),
                                represent = s3_yes_no_represent,
                                readable = ask_transport,
                                writable = ask_transport,
                                ),
                          Field("security_req", "boolean",
                                label = T("Security Required"),
                                represent = s3_yes_no_represent,
                                readable = ask_security,
                                writable = ask_security,
                                ),
                          s3_datetime("date_recv",
                                      label = T("Date Received"), # Could be T("Date Delivered") - make deployment_setting or just use Template
                                      past = 8760, # Hours, so 1 year
                                      future = 0,
                                      readable = False,
                                      writable = False,
                                      ),
                          person_id("recv_by_id",
                                    # @ToDo: Set this in Update forms? Dedicated 'Receive' button?
                                    # (Definitely not in Create forms)
                                    #default = auth.s3_logged_in_person(),
                                    label = T("Received By"),
                                    ),
                          # Workflow Status
                          Field("workflow_status", "integer",
                                label = T("Status"),
                                default = workflow_default,
                                requires = workflow_status_requires,
                                represent = S3Represent(options = workflow_opts),
                                readable = use_workflow,
                                writable = False,
                                ),
                          # Simple Status
                          # - currently just enabled in customise_req_fields() workflow
                          req_status_field(readable = False,
                                           writable = False,
                                           ),
                          # Detailed Status
                          req_status_field("commit_status",
                                           label = T("Commit Status"),
                                           represent = self.inv_commit_status_represent,
                                           readable = use_commit,
                                           writable = req_status_writable and use_commit,
                                           ),
                          req_status_field("transit_status",
                                           label = T("Transit Status"),
                                           readable = transit_status,
                                           writable = req_status_writable and transit_status,
                                           ),
                          req_status_field("fulfil_status",
                                           label = T("Fulfil. Status"),
                                           writable = req_status_writable,
                                           ),
                          #req_status_field("filing_status",
                          #                 label = T("Filing Status"),
                          #                 comment = DIV(_class="tooltip",
                          #                               _title="%s|%s" % (T("Filing Status"),
                          #                                                 T("Have all the signed documents for this shipment been filed?"))),
                          #                 readable = settings.get_inv_req_document_filing(),
                          #                 writable = False,
                          #                 ),
                          Field("closed", "boolean",
                                default = False,
                                label = T("Closed"),
                                readable = not use_workflow,
                                writable = not use_workflow,
                                comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (T("Closed"),
                                                                  T("No more items may be added to this request"),
                                                                  )),
                                ),
                          Field("cancel", "boolean",
                                default = False,
                                label = T("Cancel"),
                                ),
                          Field.Method("details", inv_req_details),
                          Field.Method("drivers", inv_req_drivers),
                          s3_comments(comment = ""),
                          *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Raise Requisition"),
            title_display = T("Requisition Details"),
            title_list = T("Requisitions"),
            title_map = T("Map of Requisitions"),
            title_report = T("Requisitions Report"),
            title_update = T("Edit Requisition"),
            label_list_button = T("List Requisitions"),
            label_delete_button = T("Delete Requisition"),
            msg_record_created = T("Requisition Added"),
            msg_record_modified = T("Requisition Updated"),
            msg_record_deleted = T("Requisition Canceled"),
            msg_list_empty = T("No Requisitions"),
            )

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        filter_widgets = [
            #S3TextFilter(["committer_id$first_name",
            #              "committer_id$middle_name",
            #              "committer_id$last_name",
            #              "site_id$name",
            #              "comments",
            #              "req_id$name",
            #              "organisation_id$name"
            #              ],
            #             label = T("Search"),
            #             comment = T("Search for a Requisition by Committer name, Requisition ID, Site or Organization."),
            #             ),
            S3OptionsFilter("fulfil_status",
                            # Better to default (easier to customise/consistency)
                            #label = T("Fulfill Status"),
                            cols = 3,
                            ),
            S3LocationFilter("site_id$location_id",
                             levels = levels,
                             hidden = True,
                             ),
            S3OptionsFilter("site_id",
                            # Better to default (easier to customise/consistency)
                            #label = T("Requested For Facility"),
                            hidden = True,
                            ),
            S3OptionsFilter("created_by",
                            label = T("Logged By"),
                            hidden = True,
                            ),
            S3DateFilter("date",
                         # Better to default (easier to customise/consistency)
                         #label = T("Date Requested"),
                         hide_time = True,
                         input_labels = {"ge": "From", "le": "To"},
                         comment = T("Search for requests made between these dates."),
                         hidden = True,
                         ),
            S3DateFilter("date_required",
                         # Better to default (easier to customise/consistency)
                         #label = T("Date Needed By"),
                         hide_time = True,
                         input_labels = {"ge": "From", "le": "To"},
                         comment = T("Search for requests required between these dates."),
                         hidden = True,
                         ),
            ]

        position = 1
        if transit_status:
            position += 1
            filter_widgets.insert(0,
                                  S3OptionsFilter("transit_status",
                                                  # Better to default (easier to customise/consistency)
                                                  #label = T("Transit Status"),
                                                  options = req_status_opts,
                                                  cols = 3,
                                                  ))
        filter_widgets.insert(position + 2,
                              S3OptionsFilter("req_item.item_id$item_category_id",
                                              label = T("Item Category"),
                                              hidden = True,
                                              ))
        if use_commit:
            filter_widgets.insert(position,
                                  S3OptionsFilter("commit_status",
                                                  # Better to default (easier to customise/consistency)
                                                  #label = T("Commit Status"),
                                                  options = req_status_opts,
                                                  cols = 3,
                                                  hidden = True,
                                                  ))

        report_fields = ["priority",
                         "site_id$organisation_id",
                         ]
        rappend = report_fields.append
        for level in levels:
            rappend("site_id$location_id$%s" % level)
        rappend("site_id")
        # @ToDo: id gets stripped in _select_field
        fact_fields = report_fields + [(T("Requisitions"), "id")]

        # Reusable Field
        req_represent = inv_ReqRepresent(show_link = True)
        req_id = S3ReusableField("req_id", "reference %s" % tablename,
                                         label = T("Requisition"),
                                         ondelete = "CASCADE",
                                         represent = req_represent,
                                         requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "inv_req.id",
                                                                  req_represent,
                                                                  orderby = "inv_req.date",
                                                                  sort = True,
                                                                  )
                                                        ),
                                         sortby = "date",
                                         )

        list_fields = ["date",
                       "date_required",
                       "site_id",
                       "requester_id",
                       ]

        if use_req_number:
            list_fields.insert(1, "req_ref")
        list_fields.extend(("priority",
                           (T("Details"), "details"),
                           T("Drivers"), "drivers")
                           )
        if use_commit:
            list_fields.append("commit_status")
        if transit_status:
            list_fields.append("transit_status")
        list_fields.append("fulfil_status")
        if use_commit:
            list_fields.append((T("Committed By"), "commit.site_id"))

        self.configure(tablename,
                       context = {"location": "site_id$location_id",
                                  "organisation": "site_id$organisation_id",
                                  "site": "site_id",
                                  },
                       deduplicate = S3Duplicate(primary = ("req_ref",)),
                       extra_fields = ("req_ref",),
                       filter_widgets = filter_widgets,
                       onaccept = self.inv_req_onaccept,
                       ondelete = self.inv_req_ondelete,
                       list_fields = list_fields,
                       orderby = "inv_req.date desc",
                       report_options = Storage(
                            rows = report_fields,
                            cols = report_fields,
                            fact = fact_fields,
                            methods = ["count", "list", "sum"],
                            defaults = Storage(
                                rows = "site_id$location_id$%s" % levels[0], # Highest-level of hierarchy
                                cols = "priority",
                                fact = "count(id)",
                                totals = True,
                                )
                            ),
                       super_entity = "doc_entity",
                       # Leave this to templates
                       # - reduce load on templates which don't need this
                       #update_realm = True,
                       realm_components = ("req_item",
                                           ),
                       )

        # Custom Methods
        set_method("inv", "req",
                   method = "check",
                   action = inv_ReqCheckMethod(),
                   )

        set_method("inv", "req",
                   method = "commit_all",
                   action = self.inv_commit_all,
                   )

        set_method("inv", "req",
                   method = "copy_all",
                   action = self.inv_req_copy_all,
                   )

        set_method("inv", "req",
                   method = "submit",
                   action = self.inv_req_submit,
                   )

        set_method("inv", "req",
                   method = "approve_req", # Don't clash with core approve method
                   action = self.inv_req_approve,
                   )

        # Lookup to limit sites to those requested_from the selected Requests' Items
        set_method("inv", "req",
                   method = "send_sites",
                   action = inv_req_send_sites,
                   )

        # Lookup to limit sites in an inv_recv when a Request is selected
        set_method("inv", "req",
                   method = "recv_sites",
                   action = inv_req_recv_sites,
                   )

        # Print Forms
        set_method("inv", "req",
                   method = "form",
                   action = self.inv_req_form,
                   )

        # Components
        add_components(tablename,
                       # Tags
                       inv_req_tag = {"alias": "tag",
                                      "joinby": "req_id",
                                      },
                       # Requested Items
                       inv_req_item = {"joinby": "req_id",
                                       "multiple": multiple_req_items,
                                       },
                       # Commitment
                       inv_commit = "req_id",
                       # Item Categories
                       supply_item_category = {"link": "inv_req_item_category",
                                               "joinby": "req_id",
                                               "key": "item_category_id",
                                               },
                       # Approvers
                       inv_req_approver_req = {"name": "approver",
                                               "joinby": "req_id",
                                               },

                       # Shipments
                       #inv_send_req = "req_id",
                       #inv_send = {"link": "inv_send_req",
                       #            "joinby": "req_id",
                       #            "key": "send_id",
                       #            "actuate": "hide",
                       #            },

                       # Projects
                       inv_req_project = {"joinby": "req_id",
                                          "multiple": False,
                                          },
                       project_project = {"link": "inv_req_project",
                                          "joinby": "req_id",
                                          "key": "project_id",
                                          "actuate": "hide",
                                          "multiple": False,
                                          },
                       **{# Scheduler Jobs (for recurring requests)
                          S3Task.TASK_TABLENAME: {"name": "job",
                                                  "joinby": "req_id",
                                                  "link": "inv_req_job",
                                                  "key": "scheduler_task_id",
                                                  "actuate": "replace",
                                                  },
                         }
                      )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"inv_req_id": req_id,
                "inv_req_ref": req_ref,
                }

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        #dummy = S3ReusableField.dummy

        return {"inv_req_id": S3ReusableField.dummy("req_id"), # For unused/disabled EventRequestModel
                #"inv_req_ref": dummy("req_ref", "string"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_commit_all(r, **attr):
        """
            Custom Method to commit to a Request
                - creates a commit with commit_items for each req_item or
                  commit_skills for each req_skill
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        table = s3db.inv_commit

        record = r.record
        req_id = record.id

        # Check if there is an existing Commitment
        query = (table.req_id == req_id) & \
                (table.deleted == False)
        exists = db(query).select(table.id,
                                  limitby = (0, 1),
                                  ).first()
        if exists:
            # Browse existing commitments
            redirect(URL(f = "req",
                         args = [r.id, "commit"],
                         ))

        # Create the commitment
        cid = table.insert(req_id = req_id,
                           )

        # Items
        ritable = s3db.inv_req_item
        items = db(ritable.req_id == req_id).select(ritable.id,
                                                    ritable.item_pack_id,
                                                    ritable.quantity,
                                                    ritable.comments,
                                                    )
        if items:
            citable = s3db.inv_commit_item
            insert = citable.insert
            for item in items:
                commit_item_id = item.id
                quantity = item.quantity
                insert(commit_id = cid,
                       req_item_id = commit_item_id,
                       item_pack_id = item.item_pack_id,
                       quantity = quantity,
                       comments = item.comments,
                       )
                # Mark Item in the Request as Committed
                db(ritable.id == commit_item_id).update(quantity_commit = quantity)
        # Mark Request as Committed
        db(s3db.inv_req.id == req_id).update(commit_status = REQ_STATUS_COMPLETE)
        msg = T("You have committed to all items in this Request. Please check that all details are correct and update as-required.")

        if "send" in r.args:
            redirect(URL(f = "send_commit",
                         args = [cid],
                         ))

        elif "assign" in r.args:
            redirect(URL(f = "commit",
                         args = [cid, "assign"],
                         ))

        else:
            current.session.confirmation = msg
            redirect(URL(c="inv", f="commit",
                         args = [cid],
                         ))

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_commit_status_represent(commit_status):
        """
            Represet the Commitment Status of the Request
        """

        if commit_status == REQ_STATUS_COMPLETE:
            # Include the Site Name of the Committer if we can
            # @ToDo: figure out how!
            return SPAN(current.T("Complete"),
                        _class = "req_status_complete",
                        )
        else:
            return req_status_opts().get(commit_status,
                                         current.messages.UNKNOWN_OPT)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_req_copy_all(r, **attr):
        """
            Copy an existing Request (custom REST method)
                - creates a req with req_item records
        """

        db = current.db
        s3db = current.s3db
        table = s3db.inv_req
        settings = current.deployment_settings
        now = current.request.now

        record = r.record
        req_id = record.id
        # Make a copy of the request record
        #if settings.get_inv_generate_req_number():
        # But we have no option but to generate for a non-interactive addition
        if settings.get_inv_use_req_number():
            from .supply import supply_get_shipping_code as get_shipping_code
            code = get_shipping_code(settings.get_inv_req_shortname(),
                                     record.site_id,
                                     table.req_ref,
                                     )
        else:
            code = None
        if record.date_required and record.date_required < now:
            date_required = now + datetime.timedelta(days = 14) # @ToDo: This figure should be configurable
        else:
            date_required = record.date_required
        new_req_id = table.insert(req_ref = code,
                                  date = now,
                                  date_required = date_required,
                                  priority = record.priority,
                                  site_id = record.site_id,
                                  purpose = record.purpose,
                                  requester_id = record.requester_id,
                                  transport_req = record.transport_req,
                                  security_req = record.security_req,
                                  comments = record.comments,
                                  )
        # Make a copy of each child record
        # Items
        ritable = s3db.inv_req_item
        items = db(ritable.req_id == req_id).select(ritable.id,
                                                    ritable.item_entity_id,
                                                    ritable.item_id,
                                                    ritable.item_pack_id,
                                                    ritable.quantity,
                                                    ritable.pack_value,
                                                    ritable.currency,
                                                    ritable.site_id,
                                                    ritable.comments,
                                                    )
        if items:
            insert = ritable.insert
            for item in items:
                insert(req_id = new_req_id,
                       item_entity_id = item.item_entity_id,
                       item_id = item.item_id,
                       item_pack_id = item.item_pack_id,
                       quantity = item.quantity,
                       pack_value = item.pack_value,
                       currency = item.currency,
                       site_id = item.site_id,
                       comments = item.comments,
                       )

        redirect(URL(f = "req",
                     args = [new_req_id, "update"],
                     ))

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_req_form(r, **attr):
        """
            Generate a PDF of a Request Form (custom REST method)
        """

        record = r.record

        pdf_componentname = "req_item"
        list_fields = ["item_id",
                       "item_pack_id",
                       "quantity",
                       "quantity_commit",
                       "quantity_transit",
                       "quantity_fulfil",
                       ]

        if current.deployment_settings.get_inv_use_req_number():
            filename = record.req_ref
        else:
            filename = None

        from s3.s3export import S3Exporter
        exporter = S3Exporter().pdf
        return exporter(r.resource,
                        request = r,
                        method = "list",
                        pdf_title = current.deployment_settings.get_inv_form_name(),
                        pdf_filename = filename,
                        list_fields = list_fields,
                        pdf_hide_comments = True,
                        pdf_componentname = pdf_componentname,
                        pdf_header_padding = 12,
                        #pdf_footer = inv_recv_pdf_footer,
                        pdf_table_autogrow = "B",
                        pdf_orientation = "Landscape",
                        **attr
                        )

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_req_submit(r, **attr):
        """
            Submit a Request for Approval (custom REST method)
        """

        record = r.record
        req_id = r.id

        # Check we are the right place in the workflow
        if record.workflow_status != 1:
            current.session.error = current.T("Can only Submit Draft Requests")
            redirect(URL(args = req_id))

        s3db = current.s3db
        rtable = s3db.inv_req

        # Check we have permission to update the Request
        if not current.auth.s3_has_permission("update", rtable, record_id=req_id):
            r.unauthorised()

        db = current.db

        # Lookup Approver(s)
        site_id = record.site_id
        stable = s3db.org_site
        site_entity = db(stable.site_id == site_id).select(stable.instance_type,
                                                           limitby = (0, 1),
                                                           ).first()
        itable = s3db.table(site_entity.instance_type)
        site = db(itable.site_id == site_id).select(itable.name, # Needed later for Message construction
                                                    itable.pe_id,
                                                    limitby = (0, 1),
                                                    ).first()
        pe_id = site.pe_id
        ancestors = s3db.pr_get_ancestors(pe_id)
        pe_ids = ancestors + [pe_id]
        atable = s3db.inv_req_approver
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        utable = db.auth_user
        query = (atable.pe_id.belongs(pe_ids)) & \
                (atable.person_id == ptable.id) & \
                (ptable.pe_id == ltable.pe_id) & \
                (ltable.user_id == utable.id)
        approvers = db(query).select(ltable.pe_id,
                                     ltable.user_id, # For custom hooks (e.g. RMS)
                                     utable.language,
                                     )
        if not approvers:
            current.session.error = current.T("No Request Approver defined")
            redirect(URL(args = req_id))

        T = current.T
        on_req_submit = s3db.get_config("inv_req", "on_req_submit")
        if on_req_submit:
            # Custom Notification processing (e.g. RMS)
            on_req_submit(req_id, record, site, approvers)
        else:
            # Send Localised Mail(s)
            languages = {}
            for row in approvers:
                language = row["auth_user.language"]
                if language not in languages:
                    languages[language] = []
                languages[language].append(row["pr_person_user.pe_id"])
            session_s3 = current.session.s3
            ui_language = session_s3.language
            url = "%s%s" % (current.deployment_settings.get_base_public_url(),
                            URL(c="inv", f="req",
                                args = req_id,
                                ))
            req_ref = record.req_ref
            requester = s3_fullname(record.requester_id)
            date_required = record.date_required
            date_represent = S3DateTime.date_represent # We want Dates not datetime which table.date_required uses
            site_name = site.name
            send_email = current.msg.send_by_pe_id
            subject_T = T("Request submitted for Approval")
            message_T = T("A new Request, %(reference)s, has been submitted for Approval by %(person)s for delivery to %(site)s by %(date_required)s. Please review at: %(url)s")
            for language in languages:
                T.force(language)
                session_s3.language = language # for date_represent
                subject = "%s: %s" % (s3_str(subject_T), req_ref)
                message = s3_str(message_T) % {"date_required": date_represent(date_required),
                                               "reference": req_ref,
                                               "person": requester,
                                               "site": site_name,
                                               "url": url,
                                               }
                users = languages[language]
                for pe_id in users:
                    send_email(pe_id,
                               subject = subject,
                               message = message,
                               )
            # Restore language for UI
            session_s3.language = ui_language
            T.force(ui_language)

        # Update the Status
        db(rtable.id == req_id).update(workflow_status = 2) # Submitted

        current.session.confirmation = T("Request submitted for Approval")
        redirect(URL(args = req_id))

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_req_approve(r, **attr):
        """
            Approve a Request (custom REST method)
        """

        record = r.record

        # Check we are the right place in the workflow
        if record.workflow_status != 2:
            current.session.error = current.T("Can only Approve Submitted Requests")
            redirect(URL(args = r.id))

        s3db = current.s3db
        rtable = s3db.inv_req

        req_id = r.id

        approvers = inv_req_approvers(record.site_id)
        person_id = current.auth.s3_logged_in_person()

        # Check we have permission to approve the Request
        if person_id not in approvers:
            r.unauthorised()

        db = current.db

        # Check if this person has already approved the Request
        artable = s3db.inv_req_approver_req
        approved = db(artable.req_id == req_id).select(artable.person_id)
        approved = [row.person_id for row in approved]
        if person_id in approved:
            current.session.warning = current.T("You have already Approved this Request")
            redirect(URL(args = req_id))

        ritable = s3db.inv_req_item
        query = (ritable.req_id == req_id) & \
                (ritable.deleted == False)
        request_items = db(query).select(ritable.id,
                                         ritable.site_id,
                                         )
        site_ids = [row.site_id for row in request_items]

        approver = approvers[person_id]

        if approver["matcher"]:
            # This person is responsible for Matching Items to Warehouses
            if None in site_ids:
                # Check for Purchases
                unmatched_items = [row.id for row in request_items if row.site_id == None]
                oitable = s3db.inv_order_item
                orders = db(oitable.req_item_id.belongs(unmatched_items)).select(oitable.id)
                if len(unmatched_items) != len(orders):
                    current.session.warning = current.T("You need to Match Items in this Request")
                    redirect(URL(args = [req_id, "req_item"]))

        # Add record to show that we have approved request
        artable.insert(req_id = req_id,
                       person_id = person_id,
                       title = approver["title"],
                       )
        # Call any Template-specific Hook
        # e.g. RMS
        on_req_approve = s3db.get_config("inv_req", "on_req_approve")
        if on_req_approve:
            on_req_approve(req_id)

        # Have all Approvers approved the Request?
        if len(approvers) == len(approved) + 1:
            # Update the Status
            db(rtable.id == req_id).update(workflow_status = 3, # Approved
                                           )
            # Call any Template-specific Hook
            # e.g. RMS
            on_req_approved = s3db.get_config("inv_req", "on_req_approved")
            if on_req_approved:
                on_req_approved(req_id, record, set(site_ids))

        current.session.confirmation = current.T("Request Approved")
        redirect(URL(args = req_id))

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_req_onaccept(form):
        """
            On-accept actions for requests
                - auto-generate a request number (req_ref) if required and
                  not specified in form
                - translate simple request status into differentiated
                  committed/fulfilled statuses
                - add requester as human resource of the requesting site if
                  configured to do so automatically
                - configure post-create/update redirection
        """

        db = current.db
        s3db = current.s3db
        settings = current.deployment_settings

        tablename = "inv_req"
        table = s3db.inv_req

        req_id = form.vars.id
        record = db(table.id == req_id).select(table.id,
                                               table.site_id,
                                               table.requester_id,
                                               table.is_template,
                                               table.req_ref,
                                               table.req_status,
                                               table.commit_status,
                                               table.fulfil_status,
                                               table.cancel,
                                               limitby = (0, 1),
                                               ).first()
        if record.is_template:
            is_template = True
            f = "req_template"
        else:
            is_template = False
            f = "req"

            update = {}

            if settings.get_inv_generate_req_number() and not record.req_ref:
                # Auto-generate req_ref
                from .supply import supply_get_shipping_code as get_shipping_code
                code = get_shipping_code(settings.get_inv_shortname(),
                                         record.site_id,
                                         table.req_ref,
                                         )
                update["req_ref"] = code

            req_status = record.req_status
            if req_status is not None:
                status_requires = table.req_status.requires
                if status_requires.has_attr("other"):
                    status_requires = status_requires.other
                opts = [opt[0] for opt in status_requires.options()]
                if str(REQ_STATUS_CANCEL) in opts:
                    # Cancel flag implied by simple status
                    update["cancel"] = False
                elif record.cancel:
                    # Using explicit cancel flag
                    update["workflow_status"] = 5

                # Translate Simple Status
                if req_status == REQ_STATUS_PARTIAL:
                    if record.commit_status != REQ_STATUS_COMPLETE:
                        update["commit_status"] = REQ_STATUS_PARTIAL
                    if record.fulfil_status == REQ_STATUS_COMPLETE:
                        update["fulfil_status"] = REQ_STATUS_PARTIAL

                elif req_status == REQ_STATUS_COMPLETE:
                    update["fulfil_status"] = REQ_STATUS_COMPLETE

                elif req_status == REQ_STATUS_CANCEL:
                    update["cancel"] = True
                    update["workflow_status"] = 5

                elif req_status == REQ_STATUS_NONE:
                    update["commit_status"] = REQ_STATUS_NONE
                    update["fulfil_status"] = REQ_STATUS_NONE

            elif record.cancel:
                # Using 3-tiered status (commit/transit/fulfill), and explicit cancel flag
                update["workflow_status"] = 5

            if update:
                record.update_record(**update)

        if settings.get_inv_requester_to_site():
            requester_id = record.requester_id
            if requester_id:
                site_id = record.site_id
                # If the requester has no HR record, then create one
                hrtable = s3db.hrm_human_resource
                query = (hrtable.person_id == requester_id)
                exists = db(query).select(hrtable.id,
                                          hrtable.organisation_id,
                                          hrtable.site_id,
                                          hrtable.site_contact,
                                          limitby = (0, 1),
                                          ).first()
                if exists:
                    if site_id and not exists.site_id:
                        # Check that the Request site belongs to this Org
                        stable = s3db.org_site
                        site = db(stable.site_id == site_id).select(stable.organisation_id,
                                                                    limitby = (0, 1),
                                                                    ).first()
                        # @ToDo: Think about branches
                        if site and site.organisation_id == exists.organisation_id:
                            # Set the HR record as being for this site
                            exists.update(site_id = site_id)
                            s3db.hrm_human_resource_onaccept(exists)
                elif site_id:
                    # Lookup the Org for the site
                    stable = s3db.org_site
                    site = db(stable.site_id == site_id).select(stable.organisation_id,
                                                                limitby = (0, 1),
                                                                ).first()
                    # Is there already a site_contact for this site?
                    ltable = s3db.hrm_human_resource_site
                    query = (ltable.site_id == site_id) & \
                            (ltable.site_contact == True)
                    already = db(query).select(ltable.id,
                                               limitby = (0, 1),
                                               ).first()
                    if already:
                        site_contact = False
                    else:
                        site_contact = True
                    hr_id = hrtable.insert(person_id = requester_id,
                                           organisation_id = site.organisation_id,
                                           site_id = site_id,
                                           site_contact = site_contact,
                                           )
                    s3db.hrm_human_resource_onaccept(Storage(id = hr_id))

        # Configure the next page to go to
        inline_forms = settings.get_inv_req_inline_forms()
        if inline_forms and is_template:
            s3db.configure(tablename,
                           create_next = URL(c="inv", f=f,
                                             args = ["[id]", "job"],
                                             ),
                           update_next = URL(c="inv", f=f,
                                             args=["[id]", "job"],
                                             ))

        elif not inline_forms:
            s3db.configure(tablename,
                           create_next = URL(c="inv", f=f,
                                             args = ["[id]", "req_item"],
                                             ),
                           update_next = URL(c="inv", f=f,
                                             args=["[id]", "req_item"],
                                             ))

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_req_ondelete(row):
        """
            Remove any scheduled tasks when deleting a recurring request
            template

            @param row: the deleted inv_req Row
        """

        db = current.db
        table = db.scheduler_task
        query = (table.function_name == "inv_req_add_from_template") & \
                (table.args == "[%s]" % row.id)
        db(query).delete()

# =============================================================================
class InventoryRequisitionApproverModel(S3Model):
    """
        Model for Approvers for Inventory Requisitions raised via inv_req
    """

    names = ("inv_req_approver",
             "inv_req_approver_req",
             )

    def model(self):

        T = current.T

        define_table = self.define_table

        person_id = self.pr_person_id

        # -----------------------------------------------------------------
        # Request Approvers
        #
        instance_types = ["org_organisation"] + list(current.auth.org_site_types.keys())
        pr_pentity_represent = self.pr_PersonEntityRepresent(show_type = False)

        tablename = "inv_req_approver"
        define_table(tablename,
                     # Could be a Site or Organisation
                     # - may have to add rules in the template's customise_req_approver_resource to filter the options appropriately
                     # - permission sets (inc realms) should only be applied to the instances, not the super-entity
                     self.super_link("pe_id", "pr_pentity",
                                     label = T("Organization/Site"),
                                     empty = False,
                                     filterby = "instance_type", # Not using instance_types as not a Super-Entity
                                     filter_opts = instance_types,
                                     represent = pr_pentity_represent,
                                     readable = True,
                                     writable = True,
                                     # @ToDo: Widget
                                     #widget = S3PentityWidget(),
                                     ),
                     Field("title", # 'position' is a Reserved word in SQL
                           label = T("Position"),
                           ),
                     person_id(),
                     Field("matcher", "boolean",
                           default = False,
                           label = T("Matcher"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Matcher"),
                                                             T("Is this person the one to match requested items to specific warehouses &/or purchase them."),
                                                             ))
                           ),
                     s3_comments(),
                     *s3_meta_fields(),
                     )

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Approver"),
            title_display = T("Approver Details"),
            title_list = T("Request Approvers"),
            title_update = T("Edit Approver"),
            label_list_button = T("List Approvers"),
            label_delete_button = T("Delete Approver"),
            msg_record_created = T("Approver added"),
            msg_record_modified = T("Approver updated"),
            msg_record_deleted = T("Approver deleted"),
            msg_list_empty = T("No Approvers currently registered"))

        # -----------------------------------------------------------------
        # Link Approvers <> Requests
        #
        tablename = "inv_req_approver_req"
        define_table(tablename,
                     self.inv_req_id(),
                     Field("title", # 'position' is a Reserved word in SQL
                           label = T("Position"),
                           ),
                     person_id(),
                     #s3_comments(),
                     *s3_meta_fields(),
                     )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class InventoryRequisitionItemModel(S3Model):
    """
        Model for Inventory Requisition Items
    """

    names = ("inv_req_item",
             "inv_req_item_id",
             "inv_req_item_represent",
             "inv_req_item_category",
             )

    def model(self):

        T = current.T
        db = current.db

        settings = current.deployment_settings
        quantities_writable = settings.get_inv_req_item_quantities_writable()
        use_commit = settings.get_inv_use_commit()
        show_qty_transit = settings.get_inv_req_show_quantity_transit()
        track_pack_values = settings.get_inv_req_pack_values()

        define_table = self.define_table
        req_id = self.inv_req_id

        # -----------------------------------------------------------------
        # Request Items
        #
        tablename = "inv_req_item"
        define_table(tablename,
                     req_id(empty = False),
                     self.supply_item_entity_id(),
                     self.supply_item_id(),
                     self.supply_item_pack_id(),
                     Field("quantity", "double", notnull=True,
                           label = T("Quantity"),
                           represent = lambda v: \
                                IS_FLOAT_AMOUNT.represent(v, precision = 2),
                           requires = IS_FLOAT_AMOUNT(minimum = 1.0),
                           ),
                     Field("pack_value", "double",
                           label = T("Estimated Value per Pack"),
                           readable = track_pack_values,
                           writable = track_pack_values,
                           ),
                     # @ToDo: Move this into a Currency Widget for the pack_value field
                     s3_currency(readable = track_pack_values,
                                 writable = track_pack_values,
                                 ),
                     # Requested from:
                     self.org_site_id(),
                     Field("quantity_commit", "double",
                           default = 0,
                           label = T("Quantity Committed"),
                           represent = self.req_qnty_commit_represent,
                           requires = IS_FLOAT_AMOUNT(minimum = 0.0),
                           readable = use_commit,
                           writable = use_commit and quantities_writable,
                           ),
                     Field("quantity_transit", "double",
                           default = 0,
                           # FB: I think this is Qty Shipped not remaining in transit
                           # @ToDo: Distinguish between:
                           #        items lost in transit (shipped but not recvd and unlikely to ever be, so still required)
                           #        items still in transit (shipped but not yet recvd but still expected, so no longer need sending)
                           #label = T("Quantity Shipped"),
                           label = T("Quantity in Transit"),
                           represent = self.req_qnty_transit_represent,
                           requires = IS_FLOAT_AMOUNT(minimum = 0.0),
                           readable = show_qty_transit,
                           writable = show_qty_transit and quantities_writable,
                           ),
                     Field("quantity_fulfil", "double",
                           label = T("Quantity Fulfilled"),
                           represent = self.req_qnty_fulfil_represent,
                           default = 0,
                           requires = IS_FLOAT_AMOUNT(minimum = 0.0),
                           writable = quantities_writable,
                           ),
                     Field.Method("pack_quantity",
                                  SupplyItemPackQuantity(tablename)
                                  ),
                     s3_comments(),
                     *s3_meta_fields(),
                     on_define = lambda table: \
                        [table.site_id.set_attributes(label = T("Requested From")),
                         ]
                     )

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Item to Request"),
            title_display = T("Request Item Details"),
            title_list = T("Items in Request"),
            title_update = T("Edit Item in Request"),
            label_list_button = T("List Items in Request"),
            label_delete_button = T("Delete Item from Request"),
            msg_record_created = T("Item(s) added to Request"),
            msg_record_modified = T("Item(s) updated on Request"),
            msg_record_deleted = T("Item(s) deleted from Request"),
            msg_list_empty = T("No Items currently requested"))

        # Reusable Field
        req_item_represent = inv_ReqItemRepresent()
        req_item_id = S3ReusableField("req_item_id", "reference %s" % tablename,
                                      label = T("Request Item"),
                                      ondelete = "CASCADE",
                                      represent = req_item_represent,
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "inv_req_item.id",
                                                              req_item_represent,
                                                              orderby = "inv_req_item.id",
                                                              sort = True,
                                                              )),
                                      comment = DIV(_class = "tooltip",
                                                    _title = "%s|%s" % (T("Request Item"),
                                                                        T("Select Items from the Requisition")),
                                                                        ),
                                      script = '''
$.filterOptionsS3({
 'trigger':'req_item_id',
 'target':'item_pack_id',
 'lookupResource':'item_pack',
 'lookupPrefix':'supply',
 'lookupURL':S3.Ap.concat('/inv/req_item_packs.json/'),
 'msgNoRecords':i18n.no_packs,
 'fncPrep':S3.supply.fncPrepItem,
 'fncRepresent':S3.supply.fncRepresentItem
})''')

        if settings.get_inv_req_prompt_match():
            # Shows the inventory items which match a requested item
            # @ToDo: Make this page a component of req_item
            create_next = URL(c="inv", f="req_item_inv_item",
                              args = ["[id]"],
                              )
        else:
            create_next = None

        list_fields = ["item_id",
                       "item_pack_id",
                       ]
        lappend = list_fields.append
        if settings.get_inv_req_prompt_match():
            lappend("site_id")
        lappend("quantity")
        if use_commit:
            lappend("quantity_commit")
        if show_qty_transit:
            lappend("quantity_transit")
        lappend("quantity_fulfil")
        lappend("comments")

        filter_widgets = [
            S3OptionsFilter("req_id$fulfil_status",
                            label = T("Status"),
                            options = req_status_opts,
                            cols = 3,
                            ),
            S3OptionsFilter("req_id$priority",
                            # Better to default (easier to customise/consistency)
                            #label = T("Priority"),
                            options = req_priority_opts,
                            cols = 3,
                            ),
            S3LocationFilter("req_id$site_id$location_id",
                             ),
            ]

        self.configure(tablename,
                       create_next = create_next,
                       deduplicate = self.req_item_duplicate,
                       deletable = settings.get_inv_multiple_req_items(),
                       extra_fields = ["item_pack_id"],
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       onaccept = self.req_item_onaccept,
                       ondelete = self.req_item_ondelete,
                       # @ToDo: default realm to that of the req_id
                       #realm_entity = self.req_item_realm_entity,
                       super_entity = "supply_item_entity",
                       )

        self.add_components(tablename,
                            inv_order_item = "req_item_id",
                            )

        # ---------------------------------------------------------------------
        # Req <> Item Category link table
        #
        # - used to provide a search filter
        # - populated onaccept/ondelete of req_item
        #
        tablename = "inv_req_item_category"
        define_table(tablename,
                     req_id(empty = False),
                     self.supply_item_category_id(),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"inv_req_item_id": req_item_id,
                "inv_req_item_represent": req_item_represent,
                }

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        return {"inv_req_item_id": S3ReusableField.dummy("req_item_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def req_item_onaccept(form):
        """
            On-accept actions for requested items:
                - update committed/in-transit/fulfilled status of the request
                  when an item is added or quantity changed
                - add item category links for the request when adding an item
                  of a new item category
        """

        db = current.db

        form_vars = form.vars

        req_id = form_vars.get("req_id")
        if not req_id:
            # Reload the record to get the req_id
            record_id = form_vars.get("id")
            table = current.s3db.inv_req_item
            record = db(table.id == record_id).select(table.req_id,
                                                      limitby = (0, 1),
                                                      ).first()
            if record:
                req_id = record.req_id

        if not req_id:
            # Item has no inv_req context => nothing we can (or need to) do
            return

        # Update Request Status
        inv_req_update_status(req_id)

        # Update req_item_category link table
        item_id = form_vars.get("item_id")
        citable = db.supply_catalog_item
        cats = db(citable.item_id == item_id).select(citable.item_category_id)
        rictable = db.inv_req_item_category
        for cat in cats:
            item_category_id = cat.item_category_id
            query = (rictable.deleted == False) & \
                    (rictable.req_id == req_id) & \
                    (rictable.item_category_id == item_category_id)
            exists = db(query).select(rictable.id,
                                      limitby = (0, 1),
                                      )
            if not exists:
                rictable.insert(req_id = req_id,
                                item_category_id = item_category_id,
                                )

    # -------------------------------------------------------------------------
    @staticmethod
    def req_item_ondelete(row):
        """
            On-delete actions for requested items:
                - delete item category links from the requisition when the last
                  item of a category is removed from the requisition

            FIXME shouldn't this also update the committed/in-transit/fulfilled
                  status of the requisition?
        """

        db = current.db
        sitable = db.supply_item
        ritable = db.inv_req_item
        item = db(ritable.id == row.id).select(ritable.deleted_fk,
                                               limitby = (0, 1),
                                               ).first()
        fks = json.loads(item.deleted_fk)
        req_id = fks["req_id"]
        item_id = fks["item_id"]
        citable = db.supply_catalog_item
        cats = db(citable.item_id == item_id).select(citable.item_category_id)
        for cat in cats:
            item_category_id = cat.item_category_id
            # Check if we have other req_items in the same category
            query = (ritable.deleted == False) & \
                    (ritable.req_id == req_id) & \
                    (ritable.item_id == sitable.id) & \
                    (sitable.item_category_id == item_category_id)
            others = db(query).select(ritable.id,
                                      limitby = (0, 1),
                                      ).first()
            if not others:
                # Delete req_item_category link table
                rictable = db.inv_req_item_category
                query = (rictable.req_id == req_id) & \
                        (rictable.item_category_id == item_category_id)
                db(query).delete()

    # ---------------------------------------------------------------------
    @classmethod
    def req_qnty_commit_represent(cls, quantity, show_link=True):

        return cls.req_item_quantity_represent(quantity, "commit", show_link)

    # ---------------------------------------------------------------------
    @classmethod
    def req_qnty_transit_represent(cls, quantity, show_link=True):

        return cls.req_item_quantity_represent(quantity, "transit", show_link)

    # ---------------------------------------------------------------------
    @classmethod
    def req_qnty_fulfil_represent(cls, quantity, show_link=True):

        return cls.req_item_quantity_represent(quantity, "fulfil", show_link)

    # ---------------------------------------------------------------------
    @staticmethod
    def req_item_quantity_represent(quantity, qtype, show_link=True):
        """
            Allow Drill-down on inv_req_item to see what:
                inv_commits contibute to the quantity_commit
                inv_sends contibute to the quantity_transit
                inv_recvs contibute to the quantity_fulfil
            Uses s3.req_item.js

            @ToDo: Build this for req_status_represent
        """

        if quantity and show_link and \
           not current.deployment_settings.get_inv_req_item_quantities_writable():
            return TAG[""](quantity,
                           A(DIV(_class = "quantity %s ajax_more collapsed" % qtype
                                 ),
                             _href = "#",
                             )
                           )
        else:
            return quantity

    # -------------------------------------------------------------------------
    @staticmethod
    def req_item_duplicate(item):
        """
            This callback will be called when importing records. It will look
            to see if the record being imported is a duplicate.

            @param item: An S3ImportItem object which includes all the details
                         of the record being imported

            If the record is a duplicate then it will set the item method to update

            Rules for finding a duplicate:
                - If the Request Number matches
                - The item is the same
        """

        db = current.db

        itable = item.table

        req_id = None
        item_id = None
        for ref in item.references:
            if ref.entry.tablename == "inv_req":
                if ref.entry.id != None:
                    req_id = ref.entry.id
                else:
                    uuid = ref.entry.item_id
                    jobitem = item.job.items[uuid]
                    req_id = jobitem.id
            elif ref.entry.tablename == "supply_item":
                if ref.entry.id != None:
                    item_id = ref.entry.id
                else:
                    uuid = ref.entry.item_id
                    jobitem = item.job.items[uuid]
                    item_id = jobitem.id

        if req_id is not None and item_id is not None:
            query = (itable.req_id == req_id) & \
                    (itable.item_id == item_id)
        else:
            return

        duplicate = db(query).select(itable.id,
                                     limitby = (0, 1),
                                     ).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
class InventoryRequisitionProjectModel(S3Model):
    """
        Link Inventory Requisitions to Projects
    """

    names = ("inv_req_project",
             )

    def model(self):

        # -----------------------------------------------------------------
        # Link Requests to Projects
        #
        tablename = "inv_req_project"
        self.define_table(tablename,
                          self.inv_req_id(empty = False),
                          self.project_project_id(empty = False),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("req_id",
                                                            "project_id",
                                                            ),
                                                 ),
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class InventoryRequisitionRecurringModel(S3Model):
    """
        Adjuvant model to support Scheduler-generated Inventory Requisitions
    """

    names = ("inv_req_job",
             )

    def model(self):

        T = current.T
        s3 = current.response.s3

        # -----------------------------------------------------------------
        # Jobs for Scheduling Recurring Requests
        #
        tablename = "inv_req_job"
        self.define_table(tablename,
                          self.inv_req_id(empty = False),
                          s3.scheduler_task_id(),
                          *s3_meta_fields())

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            label_create = T("Create Job"),
            title_display = T("Request Job"),
            title_list = T("Request Schedule"),
            title_update = T("Edit Job"),
            label_list_button = T("List Jobs"),
            msg_record_created = T("Job added"),
            msg_record_modified = T("Job updated"),
            msg_record_deleted = T("Job deleted"),
            msg_list_empty = T("No jobs configured yet"),
            msg_no_match = T("No jobs configured"))

        # Custom Methods
        self.set_method("inv", "req",
                        component_name = "job",
                        method = "reset",
                        action = inv_req_job_reset,
                        )

        self.set_method("inv", "req",
                        component_name = "job",
                        method = "run",
                        action = inv_req_job_run,
                        )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class InventoryRequisitionShipmentModel(S3Model):
    """
        Link Shipments <> Requisitions

        By default, this link is neither a proper RDBMS link, nor M2M,
        but rather a single freetext field containing the req_ref

        Used by: RMS
    """

    names = ("inv_send_req",
             "inv_recv_req",
             )

    def model(self):

        define_table = self.define_table
        req_id = self.inv_req_id

        # ---------------------------------------------------------------------
        # Outgoing Shipments <> Requests
        #
        tablename = "inv_send_req"
        define_table(tablename,
                     self.inv_send_id(empty = False,
                                      ondelete = "CASCADE",
                                      ),
                     req_id(empty = False,
                            # Default anyway
                            #ondelete = "CASCADE",
                            ),
                     *s3_meta_fields()
                     )

        # ---------------------------------------------------------------------
        # Incoming Shipments <> Requests
        #
        tablename = "inv_recv_req"
        define_table(tablename,
                     self.inv_recv_id(empty = False,
                                      ondelete = "CASCADE",
                                      ),
                     req_id(empty = False,
                            # Default anyway
                            #ondelete = "CASCADE",
                            ),
                     *s3_meta_fields()
                     )

        return {}

# =============================================================================
class InventoryRequisitionTagModel(S3Model):
    """
        Inventory Requisition Tags
    """

    names = ("inv_req_tag",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Inventory Requisition Tags
        # - Key-Value extensions
        # - can be used to provide conversions to external systems, such as:
        #   * HXL
        # - can be a Triple Store for Semantic Web support
        #
        tablename = "inv_req_tag"
        self.define_table(tablename,
                          self.inv_req_id(),
                          # key is a reserved word in MySQL
                          Field("tag",
                                label = T("Key"),
                                ),
                          Field("value",
                                label = T("Value"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("req_id",
                                                            "tag",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class InventoryStockCardModel(S3Model):
    """
        Stock Cards

        Used by: RMS
    """

    names = ("inv_stock_card",
             "inv_stock_log",
             )

    def model(self):

        T = current.T

        configure = self.configure
        define_table = self.define_table
        settings = current.deployment_settings

        bin_site_layout = settings.get_inv_bin_site_layout()

        NONE = current.messages["NONE"]
        WAREHOUSE = T(settings.get_inv_facility_label())

        is_float_represent = IS_FLOAT_AMOUNT.represent
        float_represent = lambda v: is_float_represent(v, precision=2)

        # ---------------------------------------------------------------------
        # Outgoing Shipments <> Requests
        #
        tablename = "inv_stock_card"
        define_table(tablename,
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     self.super_link("site_id", "org_site",
                                     #default = auth.user.site_id if auth.is_logged_in() else None,
                                     empty = False,
                                     label = WAREHOUSE,
                                     ondelete = "RESTRICT",
                                     represent = self.org_site_represent,
                                     readable = True,
                                     #writable = True,
                                     # Comment these to use a Dropdown & not an Autocomplete
                                     #widget = S3SiteAutocompleteWidget(),
                                     #comment = DIV(_class = "tooltip",
                                     #              _title = "%s|%s" % (WAREHOUSE,
                                     #                                  messages.AUTOCOMPLETE_HELP)),
                                     ),
                     Field("stock_card_ref",
                           label = T("Stock Card No."),
                           ),
                     self.supply_item_id(ondelete = "RESTRICT",
                                         required = True,
                                         ),
                     self.supply_item_pack_id(ondelete = "RESTRICT",
                                              required = True,
                                              ),
                     Field("item_source_no", length=16,
                           label = inv_itn_label(),
                           represent = lambda v: v or NONE,
                           requires = [IS_LENGTH(16),
                                       IS_NOT_EMPTY_STR(),
                                       ]
                           ),
                     s3_date("expiry_date",
                             label = T("Expiry Date"),
                             represent = inv_expiry_date_represent,
                             ),
                     *s3_meta_fields()
                     )

        configure(tablename,
                  create_onaccept = self.inv_stock_card_onaccept,
                  # Never created/edited manually
                  deletable = False,
                  editable = False,
                  insertable = False,
                  )

        self.add_components(tablename,
                            inv_stock_log = "card_id",
                            )

        current.response.s3.crud_strings[tablename] = Storage(title_display = T("Stock Card"),
                                                              )

        # ---------------------------------------------------------------------
        # Log of Updates to Stock Cards
        #
        tablename = "inv_stock_log"
        define_table(tablename,
                     Field("card_id", "reference inv_stock_card",
                           ),
                     s3_datetime(represent = "date"),
                     self.inv_send_id(label = T("Sent Shipment"),
                                      represent = inv_SendRepresent(show_link = True),
                                      ),
                     self.inv_recv_id(label = T("Received Shipment"),
                                      represent = inv_RecvRepresent(show_link = True),
                                      ),
                     self.inv_adj_id(label = T("Adjustment")),
                     Field("bin", length=16,
                           label = T("Bin"),
                           represent = lambda v: v or NONE,
                           requires = IS_LENGTH(16),
                           readable = not bin_site_layout,
                           writable = not bin_site_layout,
                           ),
                     self.org_site_layout_id(label = T("Bin"),
                                             readable = bin_site_layout,
                                             writable = bin_site_layout
                                             ),
                     Field("quantity_in", "double", notnull=True,
                           default = 0.0,
                           label = T("Quantity In"),
                           represent = float_represent,
                           requires = IS_FLOAT_AMOUNT(minimum = 0.0),
                           ),
                     Field("quantity_out", "double", notnull=True,
                           default = 0.0,
                           label = T("Quantity Out"),
                           represent = float_represent,
                           requires = IS_FLOAT_AMOUNT(minimum = 0.0),
                           ),
                     Field("balance", "double", notnull=True,
                           default = 0.0,
                           label = T("Balance"),
                           represent = float_represent,
                           requires = IS_FLOAT_AMOUNT(minimum = 0.0),
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        if bin_site_layout:
            bin_field = "layout_id"
        else:
            bin_field = "bin"

        configure(tablename,
                  # Never created/edited manually
                  deletable = False,
                  editable = False,
                  insertable = False,
                  list_fields = ["date",
                                 "send_id",
                                 "send_id$to_site_id",
                                 "recv_id",
                                 "recv_id$from_site_id",
                                 "adj_id",
                                 bin_field,
                                 "quantity_in",
                                 "quantity_out",
                                 "balance",
                                 "comments",
                                 ],
                  )

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_stock_card_onaccept(form):
        """
            Generate the Stock Card No.
        """

        db = current.db
        form_vars = form.vars
        ctable = db.inv_stock_card

        from .supply import supply_get_shipping_code as get_shipping_code
        code = get_shipping_code("STC",
                                 form_vars.get("site_id"),
                                 ctable.stock_card_ref,
                                 )
        db(ctable.id == form_vars.id).update(stock_card_ref = code)

# =============================================================================
class InventoryTrackingModel(S3Model):
    """
        A module to manage the shipment of inventory items
        - Sent Items
        - Received Items
        - And audit trail of the shipment process
    """

    names = ("inv_send",
             "inv_send_id",
             "inv_recv",
             "inv_recv_id",
             "inv_track_item",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        settings = current.deployment_settings

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method
        super_link = self.super_link

        person_id = self.pr_person_id
        organisation_id = self.org_organisation_id
        item_id = self.supply_item_id
        inv_item_id = self.inv_item_id
        item_pack_id = self.supply_item_pack_id
        req_item_id = self.inv_req_item_id
        req_ref = self.inv_req_ref

        site_types = auth.org_site_types

        shipment_status = inv_shipment_status_labels()
        tracking_status = {TRACK_STATUS_UNKNOWN: T("Unknown"),
                           TRACK_STATUS_PREPARING: T("In Process"),
                           TRACK_STATUS_TRANSIT: T("In transit"),
                           TRACK_STATUS_UNLOADING: T("Unloading"),
                           TRACK_STATUS_ARRIVED: T("Arrived"),
                           TRACK_STATUS_CANCELED: T("Canceled"),
                           TRACK_STATUS_RETURNING: T("Returning"),
                           }

        NONE = current.messages["NONE"]
        SITE_LABEL = settings.get_org_site_label()

        bin_site_layout = settings.get_inv_bin_site_layout()
        document_filing = settings.get_inv_document_filing()
        recv_shortname = settings.get_inv_recv_shortname()
        show_org = settings.get_inv_send_show_org()
        send_req_ref = settings.get_inv_send_req_ref()
        type_default = settings.get_inv_send_type_default()

        is_logged_in = auth.is_logged_in
        user = auth.user

        org_site_represent = self.org_site_represent
        string_represent = lambda v: v if v else NONE

        send_ref = S3ReusableField("send_ref",
                                   label = T(settings.get_inv_send_ref_field_name()),
                                   represent = self.inv_send_ref_represent,
                                   writable = False,
                                   )
        recv_ref = S3ReusableField("recv_ref",
                                   label = T("%(GRN)s Number") % {"GRN": recv_shortname},
                                   represent = self.inv_recv_ref_represent,
                                   writable = False,
                                   )

        ship_doc_status = {SHIP_DOC_PENDING  : T("Pending"),
                           SHIP_DOC_COMPLETE : T("Complete"),
                           }
        radio_widget = lambda field, value: \
                              RadioWidget().widget(field, value, cols = 2)

        # ---------------------------------------------------------------------
        # Send (Outgoing / Dispatch / etc)
        #
        send_type_opts = settings.get_inv_shipment_types()
        # @ToDo: When is this actually wanted?
        #send_type_opts.update(self.inv_item_status_opts)
        send_type_opts.update(settings.get_inv_send_types())

        tablename = "inv_send"
        define_table(tablename,
                     # Instance
                     super_link("doc_id", "doc_entity"),
                     send_ref(),
                     # Useful for when the Request comes from a site not using the same system
                     # - doesn't support multiple Requests for a Shipment
                     # - doesn't try to update Request status
                     req_ref(#represent = inv_ReqRefRepresent(show_link = True),
                             represent = string_represent,
                             readable = send_req_ref,
                             writable = send_req_ref,
                             ),
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("site_id", "org_site",
                                default = user.site_id if is_logged_in() else None,
                                empty = False,
                                instance_types = site_types,
                                label = T("From %(site)s") % {"site": SITE_LABEL},
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
                           represent = S3Represent(options = send_type_opts),
                           requires = IS_IN_SET(send_type_opts),
                           readable = not type_default,
                           writable = not type_default,
                           ),
                     # This is a reference, not a super_link, so we can override
                     Field("to_site_id", self.org_site,
                           label = T("To %(site)s") % {"site": SITE_LABEL},
                           ondelete = "SET NULL",
                           represent = org_site_represent,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "org_site.site_id",
                                                  org_site_represent,
                                                  instance_types = site_types,
                                                  sort = True,
                                                  not_filterby = "obsolete",
                                                  not_filter_opts = (True,),
                                                  )),
                           ),
                     organisation_id(label = T("To Organization"),
                                     readable = show_org,
                                     writable = show_org,
                                     ),
                     person_id("sender_id",
                               default = auth.s3_logged_in_person(),
                               label = T("Sent By"),
                               ondelete = "SET NULL",
                               comment = self.pr_person_comment(child = "sender_id"),
                               ),
                     person_id("recipient_id",
                               label = T("To Person"),
                               ondelete = "SET NULL",
                               represent = self.pr_PersonRepresentContact(),
                               comment = self.pr_person_comment(child = "recipient_id"),
                               ),
                     Field("transport_type",
                           label = T("Type of Transport"),
                           represent = string_represent,
                           ),
                     Field("transported_by",
                           label = T("Transported by"),
                           represent = string_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Transported by"),
                                                             T("Freight company or organisation providing transport"),
                                                             ),
                                         ),
                           ),
                     Field("transport_ref",
                           label = T("Transport Reference"),
                           represent = string_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Transport Reference"),
                                                             T("Consignment Number, Tracking Number, etc"),
                                                             ),
                                         ),
                           ),
                     Field("driver_name",
                           label = T("Name of Driver"),
                           represent = string_represent,
                           ),
                     Field("driver_phone",
                           label = T("Driver Phone Number"),
                           represent = lambda v: v or "",
                           requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                           ),
                     Field("vehicle_plate_no",
                           label = T("Vehicle Plate Number"),
                           represent = string_represent,
                           ),
                     Field("time_in", "time",
                           label = T("Time In"),
                           represent = string_represent,
                           # Enable in Template if-required
                           readable = False,
                           writable = False,
                           ),
                     Field("time_out", "time",
                           label = T("Time Out"),
                           represent = string_represent,
                           # Enable in Template if-required
                           readable = False,
                           writable = False,
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
                           represent = S3Represent(options = shipment_status),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(shipment_status)
                                      ),
                           writable = False,
                           ),
                     Field("filing_status", "integer",
                           default = SHIP_DOC_PENDING,
                           label = T("Filing Status"),
                           represent = S3Represent(options = ship_doc_status),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(ship_doc_status)
                                       ),
                           widget = radio_widget,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s|%s" % (T("Filing Status"),
                                                                T("Have all the signed documents for this shipment been filed?"),
                                                                "* %s|* %s" % (T("Requisition"), T("Waybill")),
                                                                )),
                           readable = document_filing,
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
        crud_strings[tablename] = Storage(
            label_create = T("Send New Shipment"),
            title_display = T("Sent Shipment Details"),
            title_list = T("Sent Shipments"),
            title_update = T("Shipment to Send"),
            label_list_button = T("List Sent Shipments"),
            label_delete_button = T("Delete Sent Shipment"),
            msg_record_created = T("Shipment Created"),
            msg_record_modified = T("Sent Shipment updated"),
            msg_record_deleted = T("Sent Shipment canceled"),
            msg_list_empty = T("No Sent Shipments"),
            )

        # Reusable Field
        send_represent = inv_SendRepresent(show_link = True,
                                           show_site = True,
                                           show_date = True,
                                           )
        send_id = S3ReusableField("send_id", "reference %s" % tablename,
                                  label = T("Send Shipment"),
                                  ondelete = "RESTRICT",
                                  represent = send_represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "inv_send.id",
                                                          send_represent,
                                                          orderby = "inv_send.date",
                                                          sort = True,
                                                          )),
                                  sortby = "date",
                                  )

        # Components
        add_components(tablename,

                       inv_track_item = "send_id",

                       inv_send_pallet = "send_id",

                       # Requisitions
                       inv_send_req = "send_id",
                       inv_req = {"link": "inv_send_req",
                                  "joinby": "send_id",
                                  "key": "req_id",
                                  "actuate": "hide",
                                  },
                       )

        # Custom methods
        # Generate PDF of Waybill
        set_method("inv", "send",
                   method = "form",
                   action = self.inv_send_form,
                   )

        # Generate Gift Certificate
        set_method("inv", "send",
                   method = "gift_certificate",
                   action = inv_gift_certificate,
                   )

        # Generate Picking List
        set_method("inv", "send",
                   method = "pick_list",
                   action = inv_pick_list,
                   )

        # Process Shipment
        set_method("inv", "send",
                   method = "process",
                   action = inv_send_process,
                   )

        # Confirm Shipment Received
        set_method("inv", "send",
                   method = "received",
                   action = inv_send_received,
                   )

        # Display Timeline
        set_method("inv", "send",
                   method = "timeline",
                   action = self.inv_timeline,
                   )

        # Redirect to the Items tabs after creation
        send_item_url = URL(c="inv", f="send",
                            args = ["[id]",
                                    "track_item",
                                    ],
                            )

        list_fields = ["send_ref",
                       "req_ref",
                       "sender_id",
                       "site_id",
                       "date",
                       "recipient_id",
                       "delivery_date",
                       "to_site_id",
                       "status",
                       "transport_type",
                       "driver_name",
                       "driver_phone",
                       "vehicle_plate_no",
                       "time_out",
                       "comments",
                       ]

        configure(tablename,
                  create_next = send_item_url,
                  update_next = send_item_url,
                  # It shouldn't be possible for the user to delete a shipment
                  # unless *maybe* if it is pending and has no items referencing it
                  deletable = False,
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  onaccept = inv_send_onaccept,
                  onvalidation = self.inv_send_onvalidation,
                  orderby = "inv_send.date desc",
                  sortby = [[5, "desc"], [1, "asc"]],
                  super_entity = ("doc_entity",),
                  )

        # ---------------------------------------------------------------------
        # Received (In/Receive / Donation / etc)
        #
        recv_req_ref = settings.get_inv_recv_req_ref()
        recv_type_opts = settings.get_inv_shipment_types()
        recv_type_opts.update(settings.get_inv_recv_types())

        tablename = "inv_recv"
        define_table(tablename,
                     # Instance
                     super_link("doc_id", "doc_entity"),
                     recv_ref(),
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("site_id", "org_site",
                                default = user.site_id if is_logged_in() else None,
                                empty = False,
                                label = T("%(site)s (Recipient)") % {"site": SITE_LABEL},
                                ondelete = "SET NULL",
                                instance_types = site_types,
                                not_filterby = "obsolete",
                                not_filter_opts = (True,),
                                readable = True,
                                writable = True,
                                represent = org_site_represent,
                                updateable = True,
                                #widget = S3SiteAutocompleteWidget(),
                                ),
                     Field("type", "integer",
                           default = 0,
                           label = T("Shipment Type"),
                           represent = S3Represent(options = recv_type_opts),
                           requires = IS_IN_SET(recv_type_opts),
                           ),
                     organisation_id(label = T("Organization/Supplier"), # From Organization/Supplier
                                     ),
                     # This is a reference, not a super_link, so we can override
                     Field("from_site_id", "reference org_site",
                           label = T("From %(site)s") % {"site": SITE_LABEL},
                           ondelete = "SET NULL",
                           #widget = S3SiteAutocompleteWidget(),
                           represent = org_site_represent,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "org_site.site_id",
                                                  org_site_represent,
                                                  instance_types = site_types,
                                                  not_filterby = "obsolete",
                                                  not_filter_opts = (True,),
                                                  sort = True,
                                                  )),
                           ),
                     s3_date("eta",
                             label = T("Date Expected"),
                             writable = False,
                             ),
                     s3_datetime(label = T("Date Received"),
                                 represent = "date",
                                 # Can also be set manually (when catching up with backlog of paperwork)
                                 #comment = DIV(_class = "tooltip",
                                 #              _title = "%s|%s" % (T("Date Received"),
                                 #                                  T("Will be filled automatically when the Shipment has been Received"))),
                                 ),
                     send_ref(),
                     Field("purchase_ref",
                           label = T("%(PO)s Number") % {"PO": settings.get_proc_shortname()},
                           represent = string_represent,
                           ),
                     req_ref(readable = recv_req_ref,
                             writable = recv_req_ref
                             ),
                     person_id(name = "sender_id",
                               label = T("Sent By Person"),
                               ondelete = "SET NULL",
                               comment = self.pr_person_comment(child = "sender_id"),
                               ),
                     person_id(name = "recipient_id",
                               label = T("Received By"),
                               ondelete = "SET NULL",
                               default = auth.s3_logged_in_person(),
                               comment = self.pr_person_comment(child = "recipient_id")),
                     Field("transport_type",
                           label = T("Type of Transport"),
                           # Enable in template as-required
                           readable = False,
                           writable = False,
                           represent = string_represent,
                           ),
                     Field("status", "integer",
                           default = SHIP_STATUS_IN_PROCESS,
                           label = T("Status"),
                           represent = S3Represent(options = shipment_status),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(shipment_status)
                                        ),
                           writable = False,
                           ),
                     Field("grn_status", "integer",
                           default = SHIP_DOC_PENDING,
                           label = T("%(GRN)s Status") % {"GRN": recv_shortname},
                           represent = S3Represent(options = ship_doc_status),
                           requires = IS_EMPTY_OR(
                                       IS_IN_SET(ship_doc_status)
                                       ),
                           widget = radio_widget,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("%(GRN)s Status") % {"GRN": recv_shortname},
                                                             T("Has the %(GRN)s (%(GRN_name)s) form been completed?") % \
                                                                {"GRN": recv_shortname,
                                                                 "GRN_name": settings.get_inv_recv_form_name()
                                                                 },
                                                             ),
                                         ),
                           ),
                     Field("cert_status", "integer",
                           default = SHIP_DOC_PENDING,
                           label = T("Certificate Status"),
                           represent = S3Represent(options = ship_doc_status),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(ship_doc_status)
                                       ),
                           widget = radio_widget,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Certificate Status"),
                                                             T("Has the Certificate for receipt of the shipment been given to the sender?"),
                                                             ),
                                         ),
                           ),
                     Field("filing_status", "integer",
                           default = SHIP_DOC_PENDING,
                           label = T("Filing Status"),
                           represent = S3Represent(options = ship_doc_status),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(ship_doc_status)
                                       ),
                           widget = radio_widget,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s|%s" % (T("Filing Status"),
                                                                T("Have all the signed documents for this shipment been filed?"),
                                                                "* %s|* %s|* %s" % (T("Requisition"), T("Waybill"), T("GRN")),
                                                                ),
                                         ),
                           readable = document_filing,
                           writable = False,
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
        recv_represent = inv_RecvRepresent(show_link = True,
                                           show_from = True,
                                           show_date = True,
                                           )
        recv_id = S3ReusableField("recv_id", "reference %s" % tablename,
                                  label = recv_id_label,
                                  ondelete = "RESTRICT",
                                  represent = recv_represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "inv_recv.id",
                                                          recv_represent,
                                                          orderby = "inv_recv.date",
                                                          sort = True,
                                                          )),
                                  sortby = "date",
                                  )

        # Filter Widgets
        if settings.get_inv_shipment_name() == "order":
            recv_search_comment = T("Search for an order by looking for text in any field.")
            recv_search_date_field = "eta"
            recv_search_date_comment = T("Search for an order expected between these dates")
        else:
            recv_search_comment = T("Search for a shipment by looking for text in any field.")
            recv_search_date_field = "date"
            recv_search_date_comment = T("Search for a shipment received between these dates")

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
                         comment = recv_search_date_comment,
                         hidden = True,
                         ),
            S3OptionsFilter("status",
                            label = T("Status"),
                            cols = 3,
                            #options = shipment_status,
                            # Needs to be visible for default_filter to work
                            #hidden = True,
                            ),
            S3OptionsFilter("site_id",
                            label = SITE_LABEL,
                            cols = 2,
                            hidden = True,
                            ),
            #S3OptionsFilter("grn_status",
            #                label = T("GRN Status"),
            #                options = ship_doc_status,
            #                cols = 2,
            #                hidden = True,
            #                ),
            #S3OptionsFilter("cert_status",
            #                label = T("Certificate Status"),
            #                options = ship_doc_status,
            #                cols = 2,
            #                hidden = True,
            #                ),
        ]

        # Redirect to the Items tabs after creation
        recv_item_url = URL(c="inv", f="recv",
                            args = ["[id]",
                                    "track_item",
                                    ],
                            )

        configure(tablename,
                  create_next = recv_item_url,
                  update_next = recv_item_url,
                  # It shouldn't be possible for the user to delete a shipment
                  # unless *maybe* if it is pending and has no items referencing it
                  deletable = False,
                  filter_widgets = filter_widgets,
                  list_fields = ["recv_ref",
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
                  onaccept = self.inv_recv_onaccept,
                  onvalidation = self.inv_recv_onvalidation,
                  orderby = "inv_recv.date desc",
                  sortby = [[6, "desc"], [1, "asc"]],
                  super_entity = ("doc_entity",),
                  )

        # Components
        add_components(tablename,

                       inv_track_item = "recv_id",

                       # Requisitions
                       inv_recv_req = "recv_id",
                       inv_req = {"link": "inv_recv_req",
                                  "joinby": "recv_id",
                                  "key": "req_id",
                                  "actuate": "hide",
                                  },
                       )

        # Custom methods
        # Print Forms
        set_method("inv", "recv",
                   method = "form",
                   action = self.inv_recv_form,
                   )

        set_method("inv", "recv",
                   method = "cert",
                   action = self.inv_recv_donation_cert,
                   )

        # Process Shipment
        set_method("inv", "recv",
                   method = "process",
                   action = inv_recv_process,
                   )

        # Timeline
        set_method("inv", "recv",
                   method = "timeline",
                   action = self.inv_timeline,
                   )

        # ---------------------------------------------------------------------
        # Tracking Items
        #
        inv_item_represent = inv_InvItemRepresent()
        inv_item_status_opts = settings.get_inv_item_status()

        tablename = "inv_track_item"
        define_table(tablename,
                     organisation_id("track_org_id",
                                     label = T("Shipping Organization"),
                                     ondelete = "SET NULL",
                                     readable = False,
                                     writable = False
                                     ),
                     # Local Purchases don't have this available
                     inv_item_id("send_inv_item_id",
                                 ondelete = "RESTRICT",
                                 represent = inv_item_represent,
                                 requires = IS_EMPTY_OR(
                                              IS_ONE_OF(db, "inv_inv_item.id",
                                                        inv_item_represent,
                                                        orderby = "inv_inv_item.id",
                                                        sort = True,
                                                        )),
                                 script = '''
$.filterOptionsS3({
 'trigger':'send_inv_item_id',
 'target':'item_pack_id',
 'lookupResource':'item_pack',
 'lookupPrefix':'supply',
 'lookupURL':S3.Ap.concat('/inv/inv_item_packs.json/'),
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
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("recv_quantity", "double",
                           label = T("Quantity Received"),
                           represent = self.qnty_recv_repr,
                           readable = False,
                           writable = False,
                           ),
                     Field("return_quantity", "double",
                           label = T("Quantity Returned"),
                           represent = self.qnty_recv_repr,
                           readable = False,
                           writable = False,
                           ),
                     Field("pack_value", "double",
                           label = T("Value per Pack"),
                           ),
                     s3_currency(),
                     s3_date("expiry_date",
                             label = T("Expiry Date"),
                             represent = inv_expiry_date_represent,
                             ),
                     # The bin at origin
                     Field("bin", length=16,
                           label = T("Bin"),
                           represent = string_represent,
                           requires = IS_LENGTH(16),
                           readable = not bin_site_layout,
                           writable = not bin_site_layout,
                           ),
                     self.org_site_layout_id(label = T("Bin"),
                                             readable = bin_site_layout,
                                             writable = bin_site_layout,
                                             ),
                     inv_item_id("recv_inv_item_id",
                                 label = T("Receiving Inventory"),
                                 ondelete = "RESTRICT",
                                 #represent = inv_item_represent,
                                 required = False,
                                 readable = False,
                                 writable = False,
                                 ),
                     # The bin at destination
                     Field("recv_bin", length=16,
                           label = T("Add to Bin"),
                           represent = string_represent,
                           requires = IS_LENGTH(16),
                           readable = False,
                           writable = False,
                           # Nice idea but not working properly
                           #widget = S3InvBinWidget("inv_track_item"),
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Bin"),
                                                             T("The Bin in which the Item is being stored (optional)."),
                                                             ),
                                         ),
                           ),
                     self.org_site_layout_id("recv_bin_id",
                                             label = T("Add to Bin"),
                                             readable = False,
                                             writable = False,
                                             ),
                     Field("item_source_no", length=16,
                           label = inv_itn_label(),
                           represent = string_represent,
                           requires = [IS_LENGTH(16),
                                       IS_NOT_EMPTY_STR(),
                                       ]
                           ),
                     # Organisation which originally supplied/donated item(s)
                     organisation_id("supply_org_id",
                                     label = T("Supplier/Donor"),
                                     ondelete = "SET NULL",
                                     ),
                     # Organisation that owns item(s)
                     organisation_id("owner_org_id",
                                     label = T("Owned By (Organization/Branch)"),
                                     ondelete = "SET NULL",
                                     ),
                     Field("inv_item_status", "integer",
                           default = 0,
                           label = T("Item Status"),
                           represent = S3Represent(options = inv_item_status_opts),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(inv_item_status_opts)
                                        ),
                           ),
                     Field("status", "integer",
                           default = TRACK_STATUS_PREPARING, # 1
                           label = T("Item Tracking Status"),
                           represent = S3Represent(options = tracking_status),
                           required = True,
                           requires = IS_IN_SET(tracking_status),
                           writable = False,
                           ),
                     self.inv_adj_item_id(ondelete = "RESTRICT"), # any adjustment record
                     # send record
                     send_id(),
                     # receive record
                     recv_id(),
                     req_item_id(readable = False,
                                 writable = False,
                                 ),
                     Field.Method("total_value",
                                  self.inv_track_item_total_value,
                                  ),
                     Field.Method("pack_quantity",
                                  SupplyItemPackQuantity(tablename),
                                  ),
                     Field.Method("total_volume",
                                  self.inv_track_item_total_volume,
                                  ),
                     Field.Method("total_weight",
                                  self.inv_track_item_total_weight,
                                  ),
                     Field.Method("total_recv_volume",
                                  lambda row: \
                                    self.inv_track_item_total_volume(row, received=True),
                                  ),
                     Field.Method("total_recv_weight",
                                  lambda row: \
                                    self.inv_track_item_total_weight(row, received=True),
                                  ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Item to Shipment"),
            title_display = T("Shipment Item Details"),
            title_list = T("Shipment Items"),
            title_update = T("Edit Shipment Item"),
            label_list_button = T("List Shipment Items"),
            label_delete_button = T("Delete Shipment Item"),
            msg_record_created = T("Item Added to Shipment"),
            msg_record_modified = T("Shipment Item updated"),
            msg_record_deleted = T("Shipment Item deleted"),
            msg_list_empty = T("No Shipment Items"),
            )

        # Filter Widgets
        filter_widgets = [
            S3TextFilter(["item_source_no",
                          "item_id$name",
                          "send_id$site_id$name",
                          "recv_id$site_id$name",
                          "recv_id$purchase_ref",
                          "recv_id$recv_ref",
                          "recv_id$req_ref",
                          "recv_id$send_ref",
                          "send_id$req_ref",
                          "send_id$send_ref",
                          "supply_org_id",
                          "owner_org_id",
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

        if bin_site_layout:
            bin_field = "layout_id"
            recv_bin_field = "recv_bin_id"
        else:
            bin_field = "bin"
            recv_bin_field = "recv_bin"

        list_fields = ["status",
                       "item_source_no",
                       "item_id",
                       "item_pack_id",
                       "send_id",
                       "recv_id",
                       "quantity",
                       (T("Total Weight (kg)"), "total_weight"),
                       (T("Total Volume (m3)"), "total_volume"),
                       "currency",
                       "pack_value",
                       bin_field,
                       "return_quantity",
                       "recv_quantity",
                       recv_bin_field,
                       "owner_org_id",
                       "supply_org_id",
                       ]

        # Resource configuration
        configure(tablename,
                  extra_fields = ["quantity",
                                  "recv_quantity",
                                  "pack_value",
                                  "item_id$volume",
                                  "item_id$weight",
                                  "item_pack_id$quantity",
                                  ],
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  onaccept = inv_track_item_onaccept,
                  onvalidation = self.inv_track_item_onvalidate,
                  )

        #----------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"inv_recv_id": recv_id,
                "inv_send_id": send_id,
                }

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        dummy = S3ReusableField.dummy

        return {"inv_recv_id": dummy("recv_id"),
                "inv_send_id": dummy("send_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_track_item_total_value(row):
        """ Total value of a track item """

        try:
            inv_track_item = getattr(row, "inv_track_item")
        except AttributeError:
            inv_track_item = row

        try:
            quantity = inv_track_item.quantity
            pack_value = inv_track_item.pack_value
        except AttributeError:
            # Need to reload the track item
            # Avoid this by adding to extra_fields
            ttable = current.s3db.inv_track_item
            query = (ttable.id == inv_track_item.id)
            inv_track_item = current.db(query).select(ttable.quantity,
                                                      ttable.pack_value,
                                                      limitby = (0, 1),
                                                      ).first()
            quantity = inv_track_item.quantity
            pack_value = inv_track_item.pack_value

        if quantity and pack_value:
            return round(quantity * pack_value, 2)
        else:
            # Item lacks quantity, or value per pack, or both
            return current.messages["NONE"]

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_track_item_total_volume(row, received=False):
        """ Total volume of a track item """

        try:
            inv_track_item = getattr(row, "inv_track_item")
        except AttributeError:
            inv_track_item = row

        try:
            supply_item = getattr(row, "supply_item")
            volume = supply_item.volume
        except AttributeError:
            # Need to load the supply item
            # Avoid this by adding to extra_fields
            ttable = current.s3db.inv_track_item
            stable = current.s3db.supply_item
            query = (ttable.id == inv_track_item.id) & \
                    (ttable.item_id == stable.id)
            supply_item = current.db(query).select(stable.volume,
                                                   limitby = (0, 1),
                                                   ).first()
            volume = supply_item.volume if supply_item else None

        if volume is None:
            return current.messages["NONE"]

        if received:
            qfield = "recv_quantity"
        else:
            qfield = "quantity"

        try:
            quantity = inv_track_item[qfield]
        except KeyError:
            # Need to reload the track item
            # Avoid this by adding to extra_fields
            ttable = current.s3db.inv_inv_item
            query = (ttable.id == inv_track_item.id)
            inv_track_item = current.db(query).select(ttable[qfield],
                                                      limitby = (0, 1),
                                                      ).first()
            quantity = inv_track_item[qfield]

        try:
            supply_item_pack = getattr(row, "supply_item_pack")
            pack_quantity = supply_item_pack.quantity
        except AttributeError:
            # Need to load the supply item pack
            # Avoid this by adding to extra_fields
            ttable = current.s3db.inv_track_item
            ptable = current.s3db.supply_item_pack
            query = (ttable.id == inv_track_item.id) & \
                    (ttable.item_pack_id == ptable.id)
            supply_item_pack = current.db(query).select(ptable.quantity,
                                                        limitby = (0, 1),
                                                        ).first()
            pack_quantity = supply_item_pack.quantity

        return round(quantity * pack_quantity * volume, 3)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_track_item_total_weight(row, received=False):
        """ Total weight of a track item """

        try:
            inv_track_item = getattr(row, "inv_track_item")
        except AttributeError:
            inv_track_item = row

        try:
            supply_item = getattr(row, "supply_item")
            weight = supply_item.weight
        except AttributeError:
            # Need to load the supply item
            # Avoid this by adding to extra_fields
            ttable = current.s3db.inv_track_item
            stable = current.s3db.supply_item
            query = (ttable.id == inv_track_item.id) & \
                    (ttable.item_id == stable.id)
            supply_item = current.db(query).select(stable.weight,
                                                   limitby = (0, 1),
                                                   ).first()
            weight = supply_item.weight if supply_item else None

        if weight is None:
            return current.messages["NONE"]

        if received:
            qfield = "recv_quantity"
        else:
            qfield = "quantity"

        try:
            quantity = inv_track_item[qfield]
        except KeyError:
            # Need to reload the track item
            # Avoid this by adding to extra_fields
            ttable = current.s3db.inv_inv_item
            query = (ttable.id == inv_track_item.id)
            inv_track_item = current.db(query).select(ttable[qfield],
                                                      limitby = (0, 1),
                                                      ).first()
            quantity = inv_track_item[qfield]

        try:
            supply_item_pack = getattr(row, "supply_item_pack")
            pack_quantity = supply_item_pack.quantity
        except AttributeError:
            # Need to load the supply item pack
            # Avoid this by adding to extra_fields
            ttable = current.s3db.inv_track_item
            ptable = current.s3db.supply_item_pack
            query = (ttable.id == inv_track_item.id) & \
                    (ttable.item_pack_id == ptable.id)
            supply_item_pack = current.db(query).select(ptable.quantity,
                                                        limitby = (0, 1),
                                                        ).first()
            pack_quantity = supply_item_pack.quantity

        return round(quantity * pack_quantity * weight, 2)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_send_form(r, **attr):
        """
            Generate a PDF of a Waybill
        """

        T = current.T
        db = current.db
        settings = current.deployment_settings

        table = db.inv_send
        tracktable = db.inv_track_item

        table.date.readable = True
        # Hide the inv_item field
        tracktable.send_inv_item_id.readable = False
        tracktable.recv_inv_item_id.readable = False

        record = db(table.id == r.id).select(table.send_ref,
                                             limitby = (0, 1),
                                             ).first()
        send_ref = record.send_ref

        if settings.get_inv_bin_site_layout():
            bin_field = "bin"
        else:
            bin_field = "layout_id"

        list_fields = [(T("Item Code"), "item_id$code"),
                       "item_id",
                       (T("Weight (kg)"), "item_id$weight"),
                       (T("Volume (m3)"), "item_id$volume"),
                       bin_field,
                       "item_source_no",
                       "item_pack_id",
                       "quantity",
                       ]

        if r.record.req_ref:
            # This Shipment relates to a requisition
            # - show the req_item comments
            list_fields.append("req_item_id$comments")
        if settings.get_inv_track_pack_values():
            list_fields.extend(("currency",
                                "pack_value",
                                ))

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
                        pdf_orientation = "Landscape",
                        pdf_table_autogrow = "B",
                        **attr
                        )

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_recv_onaccept(form):
        """
           When a inv recv record is created then create the recv_ref.
        """

        record_id = form.vars.id

        db = current.db
        rtable = db.inv_recv

        # If the recv_ref is None then set it up
        record = db(rtable.id == record_id).select(rtable.id,
                                                   rtable.recv_ref,
                                                   rtable.site_id,
                                                   limitby = (0, 1),
                                                   ).first()
        if not record.recv_ref:
            # AR Number
            from .supply import supply_get_shipping_code as get_shipping_code
            code = get_shipping_code(current.deployment_settings.get_inv_recv_shortname(),
                                     record.site_id,
                                     rtable.recv_ref,
                                     )
            record.update_record(recv_ref = code)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_send_onvalidation(form):
        """
            Check that either organisation_id or to_site_id are filled according to the type
        """

        form_vars = form.vars
        if not form_vars.to_site_id and not form_vars.organisation_id:
            error = current.T("Please enter a %(site)s OR an Organization") % \
                              {"site": current.deployment_settings.get_org_site_label()}
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

        form_vars_get = form.vars.get
        shipment_type = form_vars_get("type")
        if shipment_type is None:
            return
        shipment_type = int(shipment_type)
        if shipment_type == 11 and not form_vars_get("from_site_id"):
            # Internal Shipment needs from_site_id
            form.errors.from_site_id = current.T("Please enter a %(site)s") % \
                                            {"site": current.deployment_settings.get_org_site_label()}
        elif shipment_type >= 32 and not form_vars_get("organisation_id"):
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
        settings = current.deployment_settings

        table = db.inv_recv
        track_table = db.inv_track_item

        table.date.readable = True
        table.site_id.readable = True
        track_table.recv_quantity.readable = True

        table.site_id.label = T("By %(site)s") % {"site": T(settings.get_inv_facility_label())}
        table.site_id.represent = current.s3db.org_site_represent

        record = db(table.id == r.id).select(table.recv_ref,
                                             limitby = (0, 1),
                                             ).first()
        recv_ref = record.recv_ref

        if settings.get_inv_bin_site_layout():
            bin_field = "bin"
        else:
            bin_field = "layout_id"

        list_fields = ["item_id",
                       (T("Weight (kg)"), "item_id$weight"),
                       (T("Volume (m3)"), "item_id$volume"),
                       "item_source_no",
                       "item_pack_id",
                       "quantity",
                       "recv_quantity",
                       "currency",
                       "pack_value",
                       bin_field,
                       ]

        from s3.s3export import S3Exporter
        exporter = S3Exporter().pdf
        return exporter(r.resource,
                        request = r,
                        method = "list",
                        pdf_title = T(settings.get_inv_recv_form_name()),
                        pdf_filename = recv_ref,
                        list_fields = list_fields,
                        pdf_hide_comments = True,
                        pdf_componentname = "track_item",
                        pdf_header_padding = 12,
                        pdf_footer = inv_recv_pdf_footer,
                        pdf_table_autogrow = "B",
                        pdf_orientation = "Landscape",
                        **attr
                        )

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_recv_donation_cert (r, **attr):
        """
            Generate a PDF of a Donation certificate
        """

        T = current.T
        db = current.db

        table = db.inv_recv

        table.date.readable = True
        table.type.readable = False
        field = table.site_id
        field.readable = True

        field.label = T("By %(site)s") % \
            {"site": T(current.deployment_settings.get_inv_facility_label())}
        field.represent = current.s3db.org_site_represent

        record = db(table.id == r.id).select(table.site_id,
                                             limitby = (0, 1),
                                             ).first()
        site_id = record.site_id
        site = field.represent(site_id, False)

        from s3.s3export import S3Exporter
        exporter = S3Exporter().pdf
        return exporter(r.resource,
                        request = r,
                        method = "list",
                        pdf_title = "Donation Certificate",
                        pdf_filename = "DC-%s" % site,
                        pdf_hide_comments = True,
                        pdf_componentname = "track_item",
                        **attr
                        )

    # -------------------------------------------------------------------------
    @staticmethod
    def qnty_recv_repr(value):

        if value is None:
            reprstr = B(current.T("None"))
        else:
            reprstr = value if value else B(value)
        return reprstr

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_send_ref_represent(value, show_link=True):
        """
            Represent for the Way Bill,
            if show_link is True then it will generate a link to the pdf
        """
        if value:
            if show_link:
                db = current.db
                table = db.inv_send
                row = db(table.send_ref == value).select(table.id,
                                                         limitby = (0, 1),
                                                         ).first()
                if row:
                    return A(value,
                             _href = URL(c = "inv",
                                         f = "send",
                                         args = [row.id, "form"],
                                         extension = "",
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
                                                              limitby = (0, 1),
                                                              ).first()
                return A(value,
                         _href = URL(c = "inv",
                                     f = "recv",
                                     args = [recv_row.id, "form"],
                                     extension = "",
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

            If the inv. item is being received then there might be a selected bin
            ensure that the correct bin is selected and save those details.
        """

        form_vars = form.vars
        send_inv_item_id = form_vars.send_inv_item_id

        if send_inv_item_id:
            # Copy the data from the sent inv_item
            db = current.db
            itable = db.inv_inv_item
            query = (itable.id == send_inv_item_id)
            record = db(query).select(itable.item_id,
                                      itable.item_source_no,
                                      itable.expiry_date,
                                      itable.bin,
                                      itable.layout_id,
                                      itable.owner_org_id,
                                      itable.supply_org_id,
                                      itable.pack_value,
                                      itable.currency,
                                      itable.status,
                                      limitby = (0, 1),
                                      ).first()
            form_vars.item_id = record.item_id
            form_vars.item_source_no = record.item_source_no
            form_vars.expiry_date = record.expiry_date
            form_vars.bin = record.bin
            form_vars.layout_id = record.layout_id
            form_vars.owner_org_id = record.owner_org_id
            form_vars.supply_org_id = record.supply_org_id
            form_vars.pack_value = record.pack_value
            form_vars.currency = record.currency
            form_vars.inv_item_status = record.status

            # Save the organisation from where this tracking originates
            stable = current.s3db.org_site
            query = query & (itable.site_id == stable.id)
            record = db(query).select(stable.organisation_id,
                                      limitby = (0, 1),
                                      ).first()
            form_vars.track_org_id = record.organisation_id

        if not form_vars.recv_quantity and "quantity" in form_vars:
            # If we have no send_id and no recv_quantity then
            # copy the quantity sent directly into the received field
            # This is for when there is no related send record
            # The Quantity received ALWAYS defaults to the quantity sent
            # (Please do not change this unless there is a specific user requirement)
            #db.inv_track_item.recv_quantity.default = form_vars.quantity
            form_vars.recv_quantity = form_vars.quantity

        recv_bin = form_vars.recv_bin
        if recv_bin:
            # If there is a receiving bin then select the right one
            if isinstance(recv_bin, list):
                if recv_bin[1] != "":
                    recv_bin = recv_bin[1]
                else:
                    recv_bin = recv_bin[0]

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_timeline(r, **attr):
        """
            Display the Incidents on a Simile Timeline

            http://www.simile-widgets.org/wiki/Reference_Documentation_for_Timeline

            @ToDo: Play button
            http://www.simile-widgets.org/wiki/Timeline_Moving_the_Timeline_via_Javascript
        """

        resource_name = r.name

        if r.representation != "html" or resource_name not in ("recv", "send"):
            r.error(405, current.ERROR.BAD_METHOD)

        T = current.T
        db = current.db

        response = current.response
        s3 = response.s3

        s3_include_simile()

        # Add our data
        # @ToDo: Make this the initial data & then collect extra via REST with a stylesheet
        # add in JS using S3.timeline.eventSource.addMany(events) where events is a []

        if r.record:
            # Single record
            rows = [r.record]
        else:
            # Multiple records
            # @ToDo: Load all records & sort to closest in time
            # http://stackoverflow.com/questions/7327689/how-to-generate-a-sequence-of-future-datetimes-in-python-and-determine-nearest-d
            fields = ["id",
                      "date",
                      "send_ref",
                      "comments",
                      ]
            if resource_name == "recv":
                fields.append("recv_ref")
            rows = r.resource.select(fields,
                                     limit = 2000,
                                     virtual = False,
                                     as_rows = True,
                                     )

        # We need to link these records to the other end, which can only be done by send_ref
        send_refs = [row.send_ref for row in rows if row.send_ref is not None]

        data = {"dateTimeFormat": "iso8601",
                }

        now = r.utcnow
        tl_start = tl_end = now
        events = []
        eappend = events.append
        if resource_name == "send":
            table = db.inv_recv
            query = (table.deleted == False) & \
                    current.auth.s3_accessible_query("read", table) & \
                    (table.send_ref.belongs(send_refs)) & \
                    (table.date != None)
            recv_rows = db(query).select(table.date,
                                         table.send_ref,
                                         #table.comments,
                                         )

            for row in rows:
                send_date = row.date
                if send_date is None:
                    # Can't put on Timeline
                    continue
                send_ref = row.send_ref
                if send_ref is not None:
                    recv_row = recv_rows.find(lambda rrow: rrow.send_ref == send_ref).first()
                    if recv_row is None:
                        recv_date = send_date
                    else:
                        recv_date = recv_row.date
                else:
                    recv_date = send_date

                if send_date < tl_start:
                    tl_start = send_date
                if recv_date > tl_end:
                    tl_end = recv_date
                send_date = send_date.isoformat()
                recv_date = recv_date.isoformat()

                # @ToDo: Build better Caption rather than just using raw Comments
                caption = description = row.comments or ""
                link = URL(args = [row.id])

                # Append to events
                eappend({"start": send_date,
                         "end": recv_date,
                         "title": send_ref,
                         "caption": caption,
                         "description": description or "",
                         "link": link,
                         # @ToDo: Colour based on Category (More generically: Resource or Resource Type)
                         # "color" : "blue",
                         })
        else:
            table = db.inv_send
            query = (table.deleted == False) & \
                    current.auth.s3_accessible_query("read", table) & \
                    (table.send_ref.belongs(send_refs)) & \
                    (table.date != None)
            send_rows = db(query).select(table.date,
                                         table.send_ref,
                                         #table.comments,
                                         )

            for row in rows:
                recv_date = row.date
                if recv_date is None:
                    # Can't put on Timeline
                    continue
                send_ref = row.send_ref
                if send_ref is not None:
                    send_row = send_rows.find(lambda srow: srow.send_ref == send_ref).first()
                    if send_row is None:
                        send_date = recv_date
                    else:
                        send_date = send_row.date
                else:
                    send_date = recv_date
                    send_ref = row.recv_ref

                if send_date < tl_start:
                    tl_start = send_date
                if recv_date > tl_end:
                    tl_end = recv_date
                send_date = send_date.isoformat()
                recv_date = recv_date.isoformat()

                # @ToDo: Build better Caption rather than just using raw Comments
                caption = description = row.comments or ""
                link = URL(args = [row.id])

                # Append to events
                eappend({"start": send_date,
                         "end": recv_date,
                         "title": send_ref,
                         "caption": caption,
                         "description": description or "",
                         "link": link,
                         # @ToDo: Colour based on Category (More generically: Resource or Resource Type)
                         # "color" : "blue",
                         })

        if len(events) == 0:
            response.warning = T("No suitable data found")

        data["events"] = events
        data = json.dumps(data, separators=SEPARATORS)

        code = "".join((
'''S3.timeline.data=''', data, '''
S3.timeline.tl_start="''', tl_start.isoformat(), '''"
S3.timeline.tl_end="''', tl_end.isoformat(), '''"
S3.timeline.now="''', now.isoformat(), '''"
'''))

        # Configure our code in static/scripts/S3/s3.timeline.js
        s3.js_global.append(code)

        # Create the DIV
        item = DIV(_id = "s3timeline",
                   _class = "s3-timeline",
                   )

        output = {"item": item}

        # Maintain RHeader for consistency
        if "rheader" in attr:
            rheader = attr["rheader"](r)
            if rheader:
                output["rheader"] = rheader

        output["title"] = T("Shipments Timeline")
        response.view = "timeline.html"
        return output



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
                                                  record_id = record.id):
                    # aitable = current.s3db.inv_adj_item
                    # query = (aitable.adj_id == record.id) & \
                    #         (aitable.new_quantity == None)
                    # row = current.db(query).select(aitable.id,
                    #                                limitby = (0, 1),
                    #                                ).first()
                    # if row == None:
                    close_btn = A(T("Complete Adjustment"),
                                  _href = URL(c = "inv",
                                              f = "adj",
                                              args = [record.id,
                                                      "close",
                                                      ]
                                              ),
                                  _id = "adj_close",
                                  _class = "action-btn"
                                  )
                    close_btn_confirm = SCRIPT("S3.confirmClick('#adj_close', '%s')"
                                              % T("Do you want to complete & close this adjustment?"))
                    rheader.append(close_btn)
                    rheader.append(close_btn_confirm)

            rheader.append(rheader_tabs)

                    # else:
                        # msg = T("You need to check all the revised quantities before you can close this adjustment")
                        # rfooter.append(SPAN(msg))

            return rheader
    return None

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
                                                  record_id = record.id):
                    # aitable = current.s3db.inv_adj_item
                    # query = (aitable.adj_id == record.id) & \
                    #         (aitable.new_quantity == None)
                    # row = current.db(query).select(aitable.id,
                    #                                limitby = (0, 1),
                    #                                ).first()
                    # if row == None:
                    close_btn = A(T("Complete Adjustment"),
                                  _href = URL(c = "inv",
                                              f = "adj",
                                              args = [record.id,
                                                      "close",
                                                      ]
                                              ),
                                  _id = "adj_close",
                                  _class = "action-btn"
                                  )
                    close_btn_confirm = SCRIPT("S3.confirmClick('#adj_close', '%s')"
                                              % T("Do you want to complete & close this adjustment?"))
                    rheader.append(close_btn)
                    rheader.append(close_btn_confirm)

            rheader.append(rheader_tabs)

                    # else:
                        # msg = T("You need to check all the revised quantities before you can close this adjustment")
                        # rfooter.append(SPAN(msg))

            return rheader
    return None

# =============================================================================
def inv_gift_certificate(r, **attr):
    """
        Generate a Gift Certificate for an Outbound Shipment.
        This is part of Humanitarian Logistics when sending goods across borders
        so as not to incur import duties.

        Gift Certificate should be readable to the Country of Destination
        - we default to English, with an option for a 2nd language to be added.

        This is exported in XLS format to allow modification before use.
    """

    from s3.codecs.xls import S3XLS

    try:
        import xlwt
    except ImportError:
        r.error(503, S3XLS.ERROR.XLWT_ERROR)

    # Extract the Data
    send_id = r.id
    record = r.record
    send_ref = record.send_ref
    to_site_id = record.to_site_id

    db = current.db
    s3db = current.s3db

    # Items
    table = s3db.inv_track_item
    itable = s3db.supply_item
    #ptable = s3db.supply_item_pack

    query = (table.send_id == send_id) & \
            (table.item_id == itable.id)# & \
            #(table.item_pack_id == ptable.id)
    items = db(query).select(table.quantity,
                             table.pack_value,
                             table.currency,
                             #itable.code,
                             itable.name,
                             #ptable.name,
                             )

    # Destination
    stable = s3db.org_site
    gtable = s3db.gis_location
    query = (stable.site_id == to_site_id) & \
            (stable.location_id == gtable.id)
    location = db(query).select(gtable.L0,
                                limitby = (0, 1),
                                ).first()
    country = location.L0
    fr = "fr" in current.deployment_settings.get_L10n_languages_by_country(country)

    # Organisation
    otable = s3db.org_organisation

    query = (stable.site_id == record.site_id) & \
            (stable.organisation_id == otable.id)

    fields = [otable.id,
              otable.root_organisation,
              otable.name,
              otable.logo,
              ]

    if fr:
        ontable = s3db.org_organisation_name
        fields.append(ontable.name_l10n)
        left = ontable.on((ontable.organisation_id == otable.id) & \
                          (ontable.language == "fr"))
    else:
        left = None

    org = db(query).select(*fields,
                           left = left,
                           limitby = (0, 1)
                           ).first()
    if fr:
        org_name = org["org_organisation_name.name_l10n"]
        org = org["org_organisation"]
        if not org_name:
            org_name = org.name
    else:
        org_name = org.name

    if org.id == org.root_organisation:
        branch = None
    else:
        branch = org.name
        # Lookup Root Org
        fields = [otable.name,
                  otable.logo,
                  ]
        if fr:
            fields.append(ontable.name_l10n)
        org = db(otable.id == org.root_organisation).select(*fields,
                                                            left = left,
                                                            limitby = (0, 1)
                                                            ).first()
        if fr:
            org_name = org["org_organisation_name.name_l10n"]
            org = org["org_organisation"]
            if not org_name:
                org_name = org.name
        else:
            org_name = org.name

    # Represent the Data
    from .org import org_SiteRepresent
    destination = org_SiteRepresent(show_type = False)(to_site_id)

    T = current.T

    if fr:
        VALUE = "VALUE / VALEUR"
    else:
        VALUE = "VALUE"

    labels = ["Description",
              "Quantity",
              #"Unit",
              "Unit VALUE",
              VALUE,
              ]

    # Create the workbook
    book = xlwt.Workbook(encoding = "utf-8")

    # Add sheet
    title = "Gift Certificate"
    sheet = book.add_sheet(title)
    sheet.set_print_scaling(65)

    # Set column Widths
    sheet.col(0).width = 2750  # 2.10 cm
    sheet.col(1).width = 10180 # 7.78 cm
    sheet.col(2).width = 5940  # 4.54 cm
    sheet.col(3).width = 2785  # 2.13 cm
    sheet.col(4).width = 4110  # 3.14 cm
    sheet.col(5).width = 4985  # 3.81 cm
    sheet.col(6).width = 3400  # 2.60 cm
    #COL_WIDTH_MULTIPLIER = S3XLS.COL_WIDTH_MULTIPLIER
    #col_index = 3
    #column_widths = [None, # Empty Column
    #                 None, # Merged Column
    #                 None, # Merged Column
    #                 ]
    #for label in labels[1:]:
    #    if col_index in (5, 6):
    #        width = max(int(len(label) * COL_WIDTH_MULTIPLIER * 1.1), 2000)
    #    else:
    #        width = max(len(label) * COL_WIDTH_MULTIPLIER, 2000)
    #    width = min(width, 65535) # USHRT_MAX
    #    column_widths.append(width)
    #    sheet.col(col_index).width = width
    #    col_index += 1

    # Define styles
    POINT_12 = 240 # 240 Twips = 12 point
    ROW_HEIGHT = 320 # Realised through trial & error

    style = xlwt.XFStyle()
    style.font.height = POINT_12

    THICK = style.borders.THICK
    THIN = style.borders.THIN
    HORZ_CENTER = style.alignment.HORZ_CENTER
    HORZ_RIGHT = style.alignment.HORZ_RIGHT
    VERT_CENTER = style.alignment.VERT_CENTER

    if fr:
        italic_style = xlwt.XFStyle()
        italic_style.font.italic = True
        italic_style.font.height = POINT_12

        italic_wrap_style = xlwt.XFStyle()
        italic_wrap_style.font.italic = True
        italic_wrap_style.font.height = POINT_12
        italic_wrap_style.alignment.wrap = 1

    bold_style = xlwt.XFStyle()
    bold_style.font.bold = True
    bold_style.font.height = POINT_12

    bold_italic_style = xlwt.XFStyle()
    bold_italic_style.font.italic = True
    bold_italic_style.font.bold = True
    bold_italic_style.font.height = POINT_12

    bold_italic_right_style = xlwt.XFStyle()
    bold_italic_right_style.font.italic = True
    bold_italic_right_style.font.bold = True
    bold_italic_right_style.font.height = POINT_12
    bold_italic_right_style.alignment.horz = HORZ_RIGHT

    center_style = xlwt.XFStyle()
    center_style.font.height = POINT_12
    center_style.alignment.horz = HORZ_CENTER

    right_style = xlwt.XFStyle()
    right_style.font.height = POINT_12
    right_style.alignment.horz = HORZ_RIGHT
    right_style.borders.top = THIN
    right_style.borders.left = THIN
    right_style.borders.right = THIN
    right_style.borders.bottom = THIN

    wrap_style = xlwt.XFStyle()
    wrap_style.font.height = POINT_12
    wrap_style.alignment.wrap = 1

    header_style = xlwt.XFStyle()
    header_style.font.bold = True
    header_style.font.height = POINT_12
    header_style.alignment.horz = HORZ_CENTER
    header_style.alignment.vert = VERT_CENTER
    header_style.borders.top = THIN
    header_style.borders.left = THIN
    header_style.borders.right = THIN
    header_style.borders.bottom = THIN
    header_style.pattern.pattern = xlwt.Style.pattern_map["fine_dots"]
    header_style.pattern.pattern_fore_colour = xlwt.Style.colour_map["gray25"]

    dest_style = xlwt.XFStyle()
    dest_style.font.bold = True
    dest_style.font.height = POINT_12
    dest_style.alignment.horz = HORZ_CENTER
    dest_style.alignment.vert = VERT_CENTER

    left_header_style = xlwt.XFStyle()
    left_header_style.font.bold = True
    left_header_style.font.height = POINT_12

    box_style = xlwt.XFStyle()
    box_style.font.bold = True
    box_style.font.height = 360 # 360 Twips = 18 point
    box_style.alignment.horz = HORZ_CENTER
    box_style.alignment.vert = VERT_CENTER
    box_style.borders.top = THICK
    box_style.borders.left = THICK
    box_style.borders.right = THICK
    box_style.borders.bottom = THICK

    large_italic_font = xlwt.Font()
    large_italic_font.bold = True
    large_italic_font.height = 360 # 360 Twips = 18 point
    large_italic_font.italic = True

    # 1st row => Org Name and Logo
    current_row = sheet.row(0)
    # current_row.set_style() not giving the correct height
    current_row.height = ROW_HEIGHT
    sheet.write_merge(0, 0, 0, 1, org_name, left_header_style)
    logo = org.logo
    if logo:
        # We need to convert to 24-bit BMP
        try:
            from PIL import Image
        except:
            current.log.error("PIL not installed: Cannot insert logo")
        else:
            IMG_WIDTH = 230
            filename, extension = os.path.splitext(logo)
            logo_path = os.path.join(r.folder, "uploads", logo)
            if extension == ".png":
                # Remove Transparency
                png = Image.open(logo_path).convert("RGBA")
                size = png.size
                background = Image.new("RGBA", size, (255,255,255))
                img = Image.alpha_composite(background, png)
            else:
                img = Image.open(logo_path)
                size = img.size
            width = size[0]
            height = int(IMG_WIDTH/width * size[1])
            img = img.convert("RGB").resize((IMG_WIDTH, height))
            from io import BytesIO
            bmpfile = BytesIO()
            img.save(bmpfile, "BMP")
            bmpfile.seek(0)
            bmpdata = bmpfile.read()
            sheet.insert_bitmap_data(bmpdata, 0, 5)

    if branch: 
        # 2nd row => Branch
        current_row = sheet.row(1)
        current_row.height = ROW_HEIGHT
        current_row.write(0, "Branch: %s" % branch, style)

    # 3rd row => Department
    current_row = sheet.row(2)
    current_row.height = ROW_HEIGHT
    current_row.write(0, "Logistics Department", style)

    if fr:
        # 4th row => Department (Translated)
        current_row = sheet.row(3)
        current_row.height = ROW_HEIGHT
        current_row.write(0, "Service Logistique", italic_style)

    # 7th row => Gift Certificate
    row_index = 6
    current_row = sheet.row(row_index)
    current_row.height = int(2.8 * 360 * 1.2) # 2 rows * twips * bold
    label = "GIFT CERTIFICATE"
    if fr:
        sheet.merge(row_index, row_index, 0, 6, box_style)
        rich_text = ((label, box_style.font),
                     ("\nCERTIFICAT DE DON", large_italic_font),
                     )
        sheet.write_rich_text(row_index, 0, rich_text, box_style)
    else:
        sheet.write_merge(row_index, row_index, 0, 6, label, box_style)
    

    # 9th row => Reference
    current_row = sheet.row(8)
    current_row.height = ROW_HEIGHT
    current_row.write(0, "Ref:", bold_italic_right_style)
    current_row.write(1, send_ref, style)

    # 11th row => Statement
    current_row = sheet.row(10)
    current_row.height = int(2.8 * POINT_12) # 2 rows * twips
    msg = "We, %s, non-profit organisation, hereby certify that the following goods here under declared aren't destined for a commercial act but represent a donation to:" % org_name
    sheet.write_merge(10, 10, 0, 6, msg, wrap_style)

    if fr:
        # 13th row => Statement (Translated)
        current_row = sheet.row(12)
        current_row.height = int(2.8 * POINT_12) # 2 rows * twips
        msg = "Nous, %s, association reconnue d'utilité publique, certifions que les marchandises ci-dessous décrites ne sont pas destinées à un acte commercial mais représentent un don à:" % org_name
        sheet.write_merge(12, 12, 0, 6, msg, italic_wrap_style)

    # 15th row => Beneficiary
    row_index = 14
    current_row = sheet.row(row_index)
    current_row.height = ROW_HEIGHT
    if fr:
        rich_text = (("Beneficiary / ", bold_style.font),
                     ("bénéficiaire:", bold_italic_style.font),
                     )
        sheet.write_rich_text(row_index, 0, rich_text, bold_style)
    else:
        current_row.write(0, "Beneficiary:", bold_style)
    label = "%s,\n%s" % (destination, country)
    sheet.write_merge(row_index, 18, 2, 5, label, dest_style)

    # 20th row => Goods
    row_index = 19
    current_row = sheet.row(row_index)
    current_row.height = ROW_HEIGHT
    if fr:
        rich_text = (("Goods / ", bold_style.font),
                     ("Biens:", bold_italic_style.font),
                     )
        sheet.write_rich_text(row_index, 0, rich_text, bold_style)
    else:
        current_row.write(0, "Goods:", bold_style)

    # 21st row => Column Headers
    row_index = 20
    current_row = sheet.row(row_index)
    current_row.height = ROW_HEIGHT
    sheet.write_merge(row_index, row_index, 0, 2, labels[0], header_style)
    col_index = 3
    for label in labels[1:]:
        current_row.write(col_index, label, header_style)
        col_index += 1

    # Data rows
    one_currency = True
    grand_total = 0
    row_index = 21
    for row in items:
        current_row = sheet.row(row_index)
        current_row.height = ROW_HEIGHT
        track_row = row["inv_track_item"]
        item_row = row["supply_item"]
        #pack_row = row["supply_item_pack"]
        quantity = track_row.quantity
        item_value = track_row.pack_value
        if item_value:
            currency = track_row.currency
            if one_currency is True:
                one_currency = currency
            elif one_currency:
                if one_currency != currency:
                    one_currency = False
            total_value = quantity * item_value
            grand_total += total_value
            total_value = "%s %s" % ("{:.2f}".format(round(total_value, 2)),
                                     currency,
                                     )
            item_value = "%s %s" % ("{:.2f}".format(item_value),
                                     currency,
                                     )
        else:
            item_value = ""
            total_value = ""
        sheet.write_merge(row_index, row_index, 0, 2, item_row.name, right_style)
        col_index = 3
        values = [str(int(quantity)),
                  #pack_row.name,
                  item_value,
                  total_value,
                  ]
        for value in values:
            current_row.write(col_index, value, right_style)
            #if col_index in (5, 6):
            #    # Values
            #    width = round(len(value) * COL_WIDTH_MULTIPLIER)
            #    if width > column_widths[col_index]:
            #        column_widths[col_index] = width
            #        sheet.col(col_index).width = width
            col_index += 1
        row_index += 1

    # Totals
    current_row = sheet.row(row_index)
    current_row.height = ROW_HEIGHT
    sheet.write_merge(row_index, row_index, 0, 2, "Total", header_style)
    current_row.write(3, "", header_style) # Cell Pattern
    current_row.write(4, "", header_style) # Cell Pattern
    if one_currency:
        grand_total = "%s %s" % ("{:.2f}".format(round(grand_total, 2)),
                                 currency,
                                 )
        current_row.write(5, grand_total, header_style)
    else:
        current_row.write(5, "", header_style)

    # Without Commercial Value
    row_index += 2
    current_row = sheet.row(row_index)
    current_row.height = ROW_HEIGHT
    label = "WITHOUT COMMERCIAL VALUE - VALUE FOR CUSTOMS PURPOSES ONLY"
    current_row.write(0, label, style)

    row_index += 2
    if fr:
        # Without Commercial Value (Translated)
        current_row = sheet.row(row_index)
        current_row.height = ROW_HEIGHT
        label = "SANS VALEUR COMMERCIALE - A USAGE EXCLUSIVEMENT DOUANIER"
        current_row.write(0, label, italic_style)

    # Humanitarian Aid
    row_index += 2
    current_row = sheet.row(row_index)
    current_row.height = int(2.8 * POINT_12 * 1.2) # 2 rows * twips * bold
    label = "HUMANITARIAN AID - NOT FOR SALE - RELIEF GOODS"
    if fr:
        sheet.merge(row_index, row_index, 1, 5, box_style)
        rich_text = ((label, box_style.font),
                     ("\nAIDE HUMANITAIRE - NE PEUT ETRE VENDU -", large_italic_font),
                     )
        sheet.write_rich_text(row_index, 1, rich_text, box_style)
    else:
        sheet.write_merge(row_index, row_index, 1, 5, label, box_style)

    # Transported under GMA
    row_index += 2
    current_row = sheet.row(row_index)
    current_row.height = ROW_HEIGHT
    if fr:
        label = "Marchandise transportée sous régime GMA"
    else:
        label = "Goods transported under GMA regime"
    sheet.write_merge(row_index, row_index, 1, 5, label, center_style)

    # Place/Date
    row_index += 1
    current_row = sheet.row(row_index)
    current_row.height = ROW_HEIGHT
    label = "Place, date:"
    current_row.write(1, label, style)
    if fr:
        rich_text = (("Logistics Department / ", center_style.font),
                     ("Service Logistique", italic_style.font),
                     )
        sheet.write_rich_text(row_index, 5, rich_text, center_style)
    else:
        current_row.write(5, "Logistics Department", center_style)

    # Org
    row_index += 1
    current_row = sheet.row(row_index)
    current_row.height = ROW_HEIGHT
    current_row.write(5, org_name, center_style)

    # Received By
    row_index += 1
    current_row = sheet.row(row_index)
    current_row.height = ROW_HEIGHT
    if fr:
        rich_text = (("Received by / ", style.font),
                     ("reçu par:", italic_style.font),
                     )
        sheet.write_rich_text(row_index, 0, rich_text, style)
    else:
        current_row.write(0, "Received by:", italic_style)

    # Export to File
    output = BytesIO()
    try:
        book.save(output)
    except:
        import sys
        error = sys.exc_info()[1]
        current.log.error(error)
    output.seek(0)

    # Response headers
    title = "Gift Certificate for %(waybill)s" % {"waybill": send_ref}
    filename = "%s.xls" % title
    response = current.response
    from gluon.contenttype import contenttype
    response.headers["Content-Type"] = contenttype(".xls")
    disposition = "attachment; filename=\"%s\"" % filename
    response.headers["Content-disposition"] = disposition

    return output.read()

# =============================================================================
def inv_item_total_volume(row):
    """
        Compute the total volume of an inventory item (Field.Method)

        @param row: the Row
    """

    try:
        inv_item = getattr(row, "inv_inv_item")
    except AttributeError:
        inv_item = row

    try:
        supply_item = getattr(row, "supply_item")
        volume = supply_item.volume
    except AttributeError:
        # Need to load the supply item
        # Avoid this by adding to extra_fields
        itable = current.s3db.inv_inv_item
        stable = current.s3db.supply_item
        query = (itable.id == inv_item.id) & \
                (itable.item_id == stable.id)
        supply_item = current.db(query).select(stable.volume,
                                               limitby = (0, 1),
                                               ).first()
        volume = supply_item.volume if supply_item else None

    if volume is None:
        return current.messages["NONE"]

    try:
        quantity = inv_item.quantity
    except AttributeError:
        # Need to reload the inv item
        # Avoid this by adding to extra_fields
        itable = current.s3db.inv_inv_item
        query = (itable.id == inv_item.id)
        inv_item = current.db(query).select(itable.quantity,
                                            limitby = (0, 1),
                                            ).first()
        quantity = inv_item.quantity

    try:
        supply_item_pack = getattr(row, "supply_item_pack")
        pack_quantity = supply_item_pack.quantity
    except AttributeError:
        # Need to load the supply item pack
        # Avoid this by adding to extra_fields
        itable = current.s3db.inv_inv_item
        ptable = current.s3db.supply_item_pack
        query = (itable.id == inv_item.id) & \
                (itable.item_pack_id == ptable.id)
        supply_item_pack = current.db(query).select(ptable.quantity,
                                                    limitby = (0, 1),
                                                    ).first()
        pack_quantity = supply_item_pack.quantity

    return round(quantity * pack_quantity * volume, 2)

# -----------------------------------------------------------------------------
def inv_item_total_weight(row):
    """
        Compute the total weight of an inventory item (Field.Method)

        @param row: the Row
    """

    try:
        inv_item = getattr(row, "inv_inv_item")
    except AttributeError:
        inv_item = row

    try:
        supply_item = getattr(row, "supply_item")
        weight = supply_item.weight
    except AttributeError:
        # Need to load the supply item
        # Avoid this by adding to extra_fields
        itable = current.s3db.inv_inv_item
        stable = current.s3db.supply_item
        query = (itable.id == inv_item.id) & \
                (itable.item_id == stable.id)
        supply_item = current.db(query).select(stable.weight,
                                               limitby = (0, 1),
                                               ).first()
        weight = supply_item.weight if supply_item else None

    if weight is None:
        return current.messages["NONE"]

    try:
        quantity = inv_item.quantity
    except AttributeError:
        # Need to reload the inv item
        # Avoid this by adding to extra_fields
        itable = current.s3db.inv_inv_item
        query = (itable.id == inv_item.id)
        inv_item = current.db(query).select(itable.quantity,
                                            limitby = (0, 1),
                                            ).first()
        quantity = inv_item.quantity

    try:
        supply_item_pack = getattr(row, "supply_item_pack")
        pack_quantity = supply_item_pack.quantity
    except AttributeError:
        # Need to load the supply item pack
        # Avoid this by adding to extra_fields
        itable = current.s3db.inv_inv_item
        ptable = current.s3db.supply_item_pack
        query = (itable.id == inv_item.id) & \
                (itable.item_pack_id == ptable.id)
        supply_item_pack = current.db(query).select(ptable.quantity,
                                                    limitby = (0, 1),
                                                    ).first()
        pack_quantity = supply_item_pack.quantity

    return round(quantity * pack_quantity * weight, 3)

# =============================================================================
def inv_pick_list(r, **attr):
    """
        Generate a Picking List for a Sent Shipment

        In order to order this list for optimal picking, we assume that the Bins are
        strctured as Aisle/Site/Shelf with the Aisle being the gap between Racks as per Figure 2 in:
        http://www.appriseconsulting.co.uk/warehouse-layout-and-pick-sequence/
        We assume that Racks are numbered to match Figure 2, so we can do a simple sort on the Bin

        Currently this is exported in XLS format

        @ToDo: Provide an on-screen version
        @ToDo: Optimise Picking Route (as per Figure 3 in the above link)
    """

    send_id = r.id
    record = r.record

    if record.status != SHIP_STATUS_IN_PROCESS:
        r.error(405, T("Picking List can only be generated for Shipments being prepared"),
                next = URL(c = "inv",
                           f = "send",
                           args = [send_id],
                           ),
                )

    from s3.codecs.xls import S3XLS

    try:
        import xlwt
    except ImportError:
        r.error(503, S3XLS.ERROR.XLWT_ERROR)

    # Extract the Data
    send_ref = record.send_ref

    s3db = current.s3db
    settings = current.deployment_settings

    table = s3db.inv_track_item
    itable = s3db.supply_item
    ptable = s3db.supply_item_pack

    bin_site_layout = settings.get_inv_bin_site_layout()
    if bin_site_layout:
        bin_field = "layout_id"
        bin_represent = table.layout_id.represent
    else:
        bin_field = "bin"

    fields = [table[bin_field],
              table.quantity,
              itable.code,
              itable.name,
              itable.volume,
              itable.weight,
              ptable.name,
              ptable.quantity,
              ]

    query = (table.send_id == send_id) & \
            (table.item_id == itable.id) & \
            (table.item_pack_id == ptable.id)
    items = current.db(query).select(*fields)

    if bin_site_layout:
        # Bulk Represent the Bins
        # - values stored in class instance
        bins = bin_represent.bulk([row["inv_track_item.layout_id"] for row in items])
        # Sort the Data
        def sort_function(row):
            return bin_represent(row["inv_track_item.layout_id"])
        items = items.sort(sort_function)

    # Represent the Data
    from .org import org_SiteRepresent
    destination = org_SiteRepresent(show_type = False)(record.to_site_id)

    T = current.T

    labels = [s3_str(T("Location")),
              s3_str(T("Code")),
              s3_str(T("Item Name")),
              s3_str(T("UoM")),
              s3_str(T("Qty to Pick")),
              s3_str(T("Picked Qty")),
              s3_str(T("Unit")),
              s3_str(T("Total")),
              s3_str(T("Unit")),
              s3_str(T("Total")),
              ]

    # Create the workbook
    book = xlwt.Workbook(encoding = "utf-8")

    # Add sheet
    title = s3_str(T("Picking List"))
    sheet = book.add_sheet(title)
    sheet.set_portrait(0) # Landscape
    sheet.set_print_scaling(90)

    # Set column Widths
    COL_WIDTH_MULTIPLIER = S3XLS.COL_WIDTH_MULTIPLIER
    col_index = 0
    column_widths = []
    for label in labels:
        width = max(len(label) * COL_WIDTH_MULTIPLIER, 2000)
        width = min(width, 65535) # USHRT_MAX
        column_widths.append(width)
        sheet.col(col_index).width = width
        col_index += 1

    # Define styles
    left_style = xlwt.XFStyle()

    THIN = left_style.borders.THIN
    HORZ_CENTER = left_style.alignment.HORZ_CENTER
    HORZ_RIGHT = left_style.alignment.HORZ_RIGHT

    left_style.borders.top = THIN
    left_style.borders.left = THIN
    left_style.borders.right = THIN
    left_style.borders.bottom = THIN

    right_style = xlwt.XFStyle()
    right_style.alignment.horz = HORZ_RIGHT
    right_style.borders.top = THIN
    right_style.borders.left = THIN
    right_style.borders.right = THIN
    right_style.borders.bottom = THIN

    center_style = xlwt.XFStyle()
    center_style.alignment.horz = HORZ_CENTER
    center_style.borders.top = THIN
    center_style.borders.left = THIN
    center_style.borders.right = THIN
    center_style.borders.bottom = THIN

    large_header_style = xlwt.XFStyle()
    large_header_style.font.bold = True
    large_header_style.font.height = 400

    header_style = xlwt.XFStyle()
    header_style.font.bold = True
    header_style.alignment.horz = HORZ_CENTER
    header_style.borders.top = THIN
    header_style.borders.left = THIN
    header_style.borders.right = THIN
    header_style.borders.bottom = THIN
    header_style.pattern.pattern = xlwt.Style.pattern_map["fine_dots"]
    header_style.pattern.pattern_fore_colour = xlwt.Style.colour_map["gray25"]

    # 1st row => Report Title & Waybill
    current_row = sheet.row(0)
    current_row.height = 500
    #current_row.write(0, title, large_header_style)
    sheet.write_merge(0, 0, 0, 1, title, large_header_style)
    current_row.write(2, send_ref, large_header_style)

    # 2nd row => Destination
    current_row = sheet.row(1)
    current_row.height = 500
    #current_row.write(0, "%s:" % s3_str(T("Destination")), large_header_style)
    sheet.write_merge(1, 1, 0, 1, "%s:" % s3_str(T("Destination")), large_header_style)
    current_row.write(2, destination, large_header_style)
    sheet.write_merge(1, 1, 6, 7, s3_str(T("Weight (kg)")), header_style)
    sheet.write_merge(1, 1, 8, 9, s3_str(T("Volume (m3)")), header_style)

    # 3rd row => Column Headers
    current_row = sheet.row(2)
    col_index = 0
    for label in labels:
        current_row.write(col_index, label, header_style)
        col_index += 1

    # Data rows
    translate = settings.get_L10n_translate_supply_item()
    row_index = 3
    for row in items:
        current_row = sheet.row(row_index)
        #style = even_style if row_index % 2 == 0 else odd_style
        track_row = row["inv_track_item"]
        item_row = row["supply_item"]
        pack_row = row["supply_item_pack"]
        bin = track_row[bin_field]
        if bin_site_layout:
            bin = bin_represent(bin)
        elif not bin:
            bin = ""
        item_name = item_row.name or ""
        if translate and item_name:
            item_name = s3_str(T(item_name))
        pack_name = pack_row.name
        if translate:
            pack_name = s3_str(T(pack_name))
        quantity = track_row.quantity
        item_weight = item_row.weight
        if item_weight:
            total_weight = "{:.2f}".format(round(quantity * pack_row.quantity * item_weight, 2))
        else:
            total_weight = ""
        item_volume = item_row.volume
        if item_volume:
            total_volume = "{:.2f}".format(round(quantity * pack_row.quantity * item_volume, 2))
        else:
            total_volume = ""
        values = [bin,
                  item_row.code or "",
                  item_name,
                  pack_name,
                  str(int(quantity)),
                  "", # Included for styling
                  "{:.2f}".format(item_weight),
                  total_weight,
                  "{:.2f}".format(item_volume),
                  total_volume,
                  ]
        col_index = 0
        for value in values:
            if col_index in (0, 1, 2, 3):
                style = left_style
            elif col_index == 4:
                # Qty to Pick
                style = center_style
            else:
                style = right_style
            current_row.write(col_index, value, style)
            if col_index == 1:
                # Code
                width = round(len(value) * COL_WIDTH_MULTIPLIER * 1.1)
                if width > column_widths[col_index]:
                    column_widths[col_index] = width
                    sheet.col(col_index).width = width
            elif col_index == 2:
                # Item Name
                width = round(len(value) * COL_WIDTH_MULTIPLIER * 0.9)
                if width > column_widths[col_index]:
                    column_widths[col_index] = width
                    sheet.col(col_index).width = width
            col_index += 1
        row_index += 1

    # Export to File
    output = BytesIO()
    try:
        book.save(output)
    except:
        import sys
        error = sys.exc_info()[1]
        current.log.error(error)
    output.seek(0)

    # Response headers
    title = s3_str(T("Picking List for %(waybill)s")) % {"waybill": send_ref}
    filename = "%s.xls" % title
    response = current.response
    from gluon.contenttype import contenttype
    response.headers["Content-Type"] = contenttype(".xls")
    disposition = "attachment; filename=\"%s\"" % filename
    response.headers["Content-disposition"] = disposition

    return output.read()

# =============================================================================
def inv_prep(r):
    """
        Used in site REST controllers
        - Filter out items which are already in this inventory
        - Limit to Bins from this site
    """

    settings = current.deployment_settings
    if not settings.get_inv_direct_stock_edits():
        # Can't create/edit stock so no point configuring this workflow
        return

    if r.component:
        if r.component_name == "inv_item":
            db = current.db
            table = db.inv_inv_item
            # Filter out items which are already in this inventory
            site_id = r.record.site_id
            query = (table.site_id == site_id) & \
                    (table.deleted == False)
            inv_item_rows = db(query).select(table.item_id)
            item_ids = [row.item_id for row in inv_item_rows]

            # Ensure that the current item CAN be selected
            if r.method == "update":
                item = db(table.id == r.args[2]).select(table.item_id,
                                                        limitby = (0, 1),
                                                        ).first()
                item_ids.remove(item.item_id)
            table.item_id.requires.set_filter(not_filterby = "id",
                                              not_filter_opts = item_ids,
                                              )

            if settings.get_inv_bin_site_layout():
                # Limit to Bins from this site
                f = table.layout_id
                f.requires.other.set_filter(filterby = "site_id",
                                            filter_opts = [site_id],
                                            )
                f.widget.filter = (current.s3db.org_site_layout.site_id == site_id)

        #elif r.component_name == "send":
        #    # Default to the Search tab in the location selector widget1
        #    current.response.s3.gis.tab = "search"
        #    #if current.request.get_vars.get("select", "sent") == "incoming":
        #    #    # Display only incoming shipments which haven't been received yet
        #    #    filter = (current.s3db.inv_send.status == SHIP_STATUS_SENT)
        #    #    r.resource.add_component_filter("send", filter)

# =============================================================================
def inv_recv_attr(status):
    """
        Set field attributes for inv_recv table
    """

    s3db = current.s3db
    settings = current.deployment_settings

    table = s3db.inv_recv

    table.sender_id.readable = table.sender_id.writable = False
    table.grn_status.readable = table.grn_status.writable = False
    table.cert_status.readable = table.cert_status.writable = False
    table.eta.readable = False
    table.req_ref.writable = True
    if status == inv_ship_status["IN_PROCESS"]:
        if settings.get_inv_recv_ref_writable():
            f = table.recv_ref
            f.writable = True
            f.widget = lambda f, v: \
                StringWidget.widget(f, v, _placeholder = current.T("Leave blank to have this autogenerated"))
        else:
            table.recv_ref.readable = False
        table.send_ref.writable = True
        table.sender_id.readable = False
    else:
        # Make all fields writable False
        for field in table.fields:
            table[field].writable = False
        if settings.get_inv_recv_req():
            s3db.inv_recv_req.req_id.writable = False

        if status == inv_ship_status["SENT"]:
            table.date.writable = True
            table.recipient_id.readable = table.recipient_id.writable = True
            table.comments.writable = True

# =============================================================================
def inv_recv_controller():
    """
        RESTful CRUD controller for Inbound Shipments
    """

    T = current.T
    db = current.db
    s3db = current.s3db
    s3 = current.response.s3
    settings = current.deployment_settings

    recvtable = s3db.inv_recv

    # Limit site_id to sites the user has permissions for
    if settings.get_inv_shipment_name() == "order":
        error_msg = T("You do not have permission for any facility to add an order.")
    else:
        error_msg = T("You do not have permission for any facility to receive a shipment.")
    current.auth.permitted_facilities(table = recvtable,
                                      error_msg = error_msg)

    def prep(r):

        record = r.record
        if record:
            status = record.status

        if r.component:
            if r.component_name == "document":
                # Simplify a little
                table = s3db.doc_document
                table.file.required = True
                table.url.readable = table.url.writable = False
                table.date.readable = table.date.writable = False

            elif r.component_name == "track_item":

                # Security-wise, we are already covered by configure()
                # Performance-wise, we should optimise for UI-acessible flows
                #if r.method == "create" or r.method == "delete":
                #    # Can only create or delete track items for a recv record
                #    # if the status is preparing:
                #    if status != SHIP_STATUS_IN_PROCESS:
                #        return False

                tracktable = s3db.inv_track_item

                bin_site_layout = settings.get_inv_bin_site_layout()
                track_pack_values = settings.get_inv_track_pack_values()

                def set_track_attr(track_status):
                    # By default Make all fields writable False
                    for field in tracktable.fields:
                        tracktable[field].writable = False
                    # Hide some fields
                    tracktable.send_id.readable = False
                    tracktable.recv_id.readable = False
                    if bin_site_layout:
                        tracktable.layout_id.readable = False
                    else:
                        tracktable.bin.readable = False
                    tracktable.adj_item_id.readable = False
                    tracktable.recv_quantity.readable = True

                    if track_status == TRACK_STATUS_PREPARING:
                        # External Shipment
                        # Show some fields
                        tracktable.item_source_no.writable = True
                        tracktable.item_id.writable = True
                        tracktable.item_pack_id.writable = True
                        tracktable.quantity.writable = True
                        tracktable.recv_quantity.writable = True
                        tracktable.recv_quantity.comment = T("Can leave this blank if all Items received OK")
                        if track_pack_values:
                            tracktable.currency.writable = True
                            tracktable.pack_value.writable = True
                        tracktable.expiry_date.writable = True
                        tracktable.owner_org_id.writable = True
                        tracktable.supply_org_id.writable = True
                        tracktable.inv_item_status.writable = True
                        tracktable.comments.writable = True
                        # Hide some fields
                        tracktable.send_inv_item_id.readable = False
                        # Change some labels - NO - use consistent labels
                        #tracktable.quantity.label = T("Quantity Delivered")
                        if bin_site_layout:
                            tracktable.recv_bin_id.readable = True
                            tracktable.recv_bin_id.writable = True
                            tracktable.recv_bin_id.label = T("Bin")
                            # Limit to Bins from this site
                            site_id = record.site_id
                            f = tracktable.recv_bin_id
                            f.requires.other.set_filter(filterby = "site_id",
                                                        filter_opts = [site_id],
                                                        )
                            f.widget.filter = (s3db.org_site_layout.site_id == site_id)
                        else:
                            tracktable.recv_bin.readable = True
                            tracktable.recv_bin.writable = True
                            tracktable.recv_bin.label = T("Bin")

                    elif track_status == TRACK_STATUS_TRANSIT:
                        # Internal Shipment auto-generated from inv_send_process
                        # Hide the values that will be copied from the inv_inv_item record
                        tracktable.send_inv_item_id.readable = False
                        tracktable.send_inv_item_id.writable = False
                        tracktable.item_source_no.readable = True
                        tracktable.item_source_no.writable = False
                        # Display the values that can only be entered on create
                        tracktable.recv_quantity.writable = True
                        if bin_site_layout:
                            tracktable.recv_bin_id.readable = True
                            tracktable.recv_bin_id.writable = True
                            # Limit to Bins from this site
                            site_id = record.site_id
                            f = tracktable.recv_bin_id
                            f.requires.other.set_filter(filterby = "site_id",
                                                        filter_opts = [site_id],
                                                        )
                            f.widget.filter = (s3db.org_site_layout.site_id == site_id)
                        else:
                            tracktable.recv_bin.readable = True
                            tracktable.recv_bin.writable = True
                        tracktable.comments.writable = True
                        # This is a received purchase so change the label to reflect this - NO - use consistent labels
                        #tracktable.quantity.label =  T("Quantity Delivered")

                    elif track_status == TRACK_STATUS_ARRIVED:
                        # Received Shipment
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
                        if bin_site_layout:
                            tracktable.recv_bin_id.readable = True
                            #tracktable.recv_bin_id.writable = True
                            # Limit to Bins from this site
                            #site_id = record.site_id
                            #f = tracktable.recv_bin_id
                            #f.requires.other.set_filter(filterby = "site_id",
                            #                            filter_opts = [site_id],
                            #                            )
                            #f.widget.filter = (s3db.org_site_layout.site_id == site_id)
                        else:
                            tracktable.recv_bin.readable = True
                            #tracktable.recv_bin.writable = True

                # Configure which fields in track_item are readable/writable
                # depending on track_item.status:
                if r.component_id:
                    track_record = db(tracktable.id == r.component_id).select(tracktable.status,
                                                                              limitby = (0, 1),
                                                                              ).first()
                    set_track_attr(track_record.status)
                else:
                    set_track_attr(TRACK_STATUS_PREPARING)
                    tracktable.status.readable = False

                if bin_site_layout:
                    recv_bin_field = "recv_bin_id"
                else:
                    recv_bin_field = "recv_bin"
                list_fields = [#"status",
                               "item_id",
                               "item_pack_id",
                               "quantity",
                               "recv_quantity",
                               recv_bin_field,
                               "owner_org_id",
                               "supply_org_id",
                               ]
                if track_pack_values:
                    list_fields.insert(4, "pack_value")
                    list_fields.insert(4, "currency")

                if status == SHIP_STATUS_SENT:
                    # Lock the record so it can't be fiddled with
                    # - other than being able to edit Quantity Received & Bin
                    deletable = False
                    editable = True
                    insertable = False
                elif status:
                    # Lock the record so it can't be fiddled with
                    deletable = False
                    editable = False
                    insertable = False
                else:
                    # status == SHIP_STATUS_IN_PROCESS
                    deletable = True
                    editable = True
                    insertable = True
                    # Adjust CRUD strings
                    s3.crud_strings.inv_recv.title_update = \
                    s3.crud_strings.inv_recv.title_display = T("Process Received Shipment")
                    if settings.get_inv_recv_req():
                        rrtable = s3db.inv_recv_req
                        reqs = db(rrtable.recv_id == r.id).select(rrtable.req_id)
                        if reqs:
                            # Allow populating req_item_id
                            f = tracktable.req_item_id
                            f.writable = True
                            f.comment = None
                            f.label = T("Request")
                            # Items use dropdown, not Autocomplete
                            f = tracktable.item_id
                            f.comment = None # Cannot create new Items here
                            f.widget = None
                            # We replace filterOptionsS3
                            tracktable.item_pack_id.comment = None
                            if s3.debug:
                                s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv_item.js" % r.application)
                            else:
                                s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv_item.min.js" % r.application)
                            # Filter to Items in the Request(s) which have not yet been received
                            rtable = s3db.inv_req
                            ritable = s3db.inv_req_item
                            iptable = s3db.supply_item_pack
                            req_ids = [row.req_id for row in reqs]
                            if len(req_ids) == 1:
                                query = (rtable.id == req_ids[0])
                            else:
                                query = (rtable.id.belongs(req_ids))
                            query &= (ritable.req_id == rtable.id) & \
                                     (ritable.quantity_fulfil < ritable.quantity) & \
                                     (ritable.item_pack_id == iptable.id)
                            items = db(query).select(rtable.req_ref,
                                                     ritable.id,
                                                     ritable.item_id,
                                                     ritable.quantity,
                                                     iptable.quantity,
                                                     )
                            item_ids = [row["inv_req_item.item_id"] for row in items]
                            f.requires.set_filter(filterby = "id",
                                                  filter_opts = item_ids,
                                                  )
                            item_data = {}
                            for row in items:
                                req_pack_quantity = row["supply_item_pack.quantity"]
                                req_ref = row["inv_req.req_ref"]
                                req_row = row["inv_req_item"]
                                item_id = req_row.item_id
                                if item_id in item_data:
                                    item_data[item_id]["req_items"].append({"req_item_id": req_row.id,
                                                                            "req_quantity": req_row.quantity * req_pack_quantity,
                                                                            "req_ref": req_ref,
                                                                            })
                                else:
                                    item_data[item_id] = {"req_items": [{"req_item_id": req_row.id,
                                                                         "req_quantity": req_row.quantity * req_pack_quantity,
                                                                         "req_ref": req_ref,
                                                                         }],
                                                          }
                            # Remove req_ref when there are no duplicates to distinguish
                            for item_id in item_data:
                                req_items = item_data[item_id]["req_items"]
                                if len(req_items) == 1:
                                    req_items[0].pop("req_ref")

                            # Add Packs to replace the filterOptionsS3 lookup
                            rows = db(iptable.item_id.belongs(item_ids)).select(iptable.id,
                                                                                iptable.item_id,
                                                                                iptable.name,
                                                                                iptable.quantity,
                                                                                )
                            for row in rows:
                                item_id = row.item_id
                                this_data = item_data[item_id]
                                packs = this_data.get("packs")
                                if not packs:
                                    this_data["packs"] = [{"id": row.id,
                                                           "name": row.name,
                                                           "quantity": row.quantity,
                                                           },
                                                          ]
                                else:
                                    this_data["packs"].append({"id": row.id,
                                                               "name": row.name,
                                                               "quantity": row.quantity,
                                                               })
                            # Pass data to inv_recv_item.js
                            # to Apply req_item_id & quantity when item_id selected
                            s3.js_global.append('''S3.supply.item_data=%s''' % json.dumps(item_data, separators=SEPARATORS))

                s3db.configure("inv_track_item",
                               deletable = deletable,
                               editable = editable,
                               insertable = insertable,
                               list_fields = list_fields,
                               )

                # Default the Supplier/Donor to the Org sending the shipment
                tracktable.supply_org_id.default = record.organisation_id
        else:
            # No Component
            # Configure which fields in inv_recv are readable/writable
            # depending on status
            if record:
                if status not in (SHIP_STATUS_IN_PROCESS, SHIP_STATUS_SENT):
                    # Now that the shipment has been sent
                    # lock the record so that it can't be meddled with
                    if settings.get_inv_document_filing():
                        dtable = s3db.doc_document
                        filed = db(dtable.doc_id == record.doc_id).select(dtable.id,
                                                                          limitby = (0, 1),
                                                                          )
                        if filed:
                            # Still allow access to filing_status
                            inv_recv_attr(status)
                            recvtable.filing_status.writable = True
                            s3db.configure("inv_recv",
                                           deletable = False,
                                           )
                        else:
                            s3db.configure("inv_recv",
                                           deletable = False,
                                           editable = False,
                                           )
                    else:
                        s3db.configure("inv_recv",
                                       deletable = False,
                                       editable = False,
                                       )
                else:
                    inv_recv_attr(status)
            else:
                inv_recv_attr(SHIP_STATUS_IN_PROCESS)
                recvtable.recv_ref.readable = False
                if r.method and r.method != "read":
                    # Don't want to see in Create forms
                    recvtable.status.readable = False

            if r.method == "create" or \
               (r.method == "update" and record.status == SHIP_STATUS_IN_PROCESS):
                if s3.debug:
                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv.js" % r.application)
                else:
                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv.min.js" % r.application)
                # Only allow External Shipment Types (Internal Shipments have the recv auto-created)
                # - no, need to be able to support Internal Shipments from sites not using the system
                #recvtable.type.requires = IS_IN_SET(settings.get_inv_recv_types())
                if settings.get_inv_recv_req():
                    # Filter Requests to those which are:
                    # - For Our Sites
                    # - Approved (or Open)
                    sites = recvtable.site_id.requires.options(zero = False)
                    site_ids = [site[0] for site in sites]
                    rtable = s3db.inv_req
                    ritable = s3db.inv_req_item
                    if len(site_ids) > 1:
                        query = (rtable.site_id.belongs(site_ids))
                        if s3.debug:
                            s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv_multisite.js" % r.application)
                        else:
                            s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv_multisite.min.js" % r.application)
                    else:
                       query = (rtable.site_id == site_ids[0])
                    if settings.get_inv_req_workflow():
                        query &= (rtable.workflow_status == 3)
                    else:
                        query &= (rtable.fulfil_status.belongs((REQ_STATUS_NONE, REQ_STATUS_PARTIAL)))
                    f = s3db.inv_recv_req.req_id 
                    f.requires = IS_ONE_OF(db(query), "inv_req.id",
                                           f.represent,
                                           sort = True,
                                           )

        return True
    s3.prep = prep
       
    return current.rest_controller("inv", "recv",
                                   rheader = inv_recv_rheader,
                                   )

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
            msg_list_empty = T("No Orders registered"),
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
            msg_list_empty = T("No Received Shipments"),
            )

# =============================================================================
def inv_recv_rheader(r):
    """ Resource Header for Receiving """

    if r.representation == "html" and r.name == "recv":
        record = r.record
        if record:

            T = current.T
            s3db = current.s3db
            settings = current.deployment_settings

            tabs = [(T("Edit Details"), None),
                    (T("Items"), "track_item"),
                    ]
            if settings.get_inv_document_filing():
                tabs.append((T("Documents"), "document"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table
            tracktable = s3db.inv_track_item

            recv_id = record.id
            site_id = record.site_id
            stable = s3db.org_site
            site = current.db(stable.site_id == site_id).select(stable.organisation_id,
                                                                limitby = (0, 1),
                                                                ).first()
            try:
                org_id = site.organisation_id
            except AttributeError:
                org_id = None
            logo = s3db.org_organisation_logo(org_id)
            shipment_details = TABLE(
                          TR(TD(T(settings.get_inv_recv_form_name()),
                                _colspan = 2,
                                _class = "pdf_title",
                                ),
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
                             # Duplicate! req_ref?
                             #TH("%s: " % table.recv_ref.label),
                             #table.recv_ref.represent(record.recv_ref),
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
                if current.auth.s3_has_permission("update", "inv_recv",
                                                  record_id = record.id):
                    if cnt > 0:
                        action.append(A(T("Receive Shipment"),
                                        _href = URL(c = "inv",
                                                    f = "recv",
                                                    args = [record.id,
                                                            "process",
                                                            ]
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
            #        if current.auth.s3_has_permission("update", "inv_recv",
            #                                          record_id = record.id):
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
            shipment_details.append(TR(TH(action, _colspan=2), TD(msg)))

            current.response.s3.rfooter = rfooter
            rheader = DIV(shipment_details,
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
def inv_recv_process(r, **attr):
    """
        Receive a Shipment

        @ToDo: Avoid Writes in GETs
    """

    T = current.T

    recv_id = r.id

    if not recv_id:
        r.error(405, T("Can only receive a single shipment."),
                next = URL(c = "inv",
                           f = "recv",
                           ),
                )

    auth = current.auth
    s3db = current.s3db
    rtable = s3db.inv_recv

    if not auth.s3_has_permission("update", rtable,
                                  record_id = recv_id):
        r.unauthorised()

    db = current.db

    recv_record = db(rtable.id == recv_id).select(rtable.date,
                                                  rtable.recipient_id,
                                                  rtable.status,
                                                  rtable.site_id,
                                                  rtable.recv_ref,
                                                  limitby = (0, 1),
                                                  ).first()

    # Check status
    status = recv_record.status
    if status == inv_ship_status["RECEIVED"]:
        r.error(405, T("This shipment has already been received."),
                next = URL(c = "inv",
                           f = "recv",
                           args = [recv_id],
                           ),
                )

    elif status == inv_ship_status["CANCEL"]:
        r.error(405, T("This shipment has already been received & subsequently canceled."),
                next = URL(c = "inv",
                           f = "recv",
                           args = [recv_id],
                           ),
                )

    settings = current.deployment_settings
    stock_cards = settings.get_inv_stock_cards()

    # Update Receive record & lock for editing
    #ADMIN = auth.get_system_roles().ADMIN
    data = {"status": inv_ship_status["RECEIVED"],
            #"owned_by_user": None,
            #"owned_by_group": ADMIN,
            }

    if not recv_record.recv_ref:
        # No recv_ref yet? => add one now
        from .supply import supply_get_shipping_code as get_shipping_code
        code = get_shipping_code(settings.get_inv_recv_shortname(),
                                 recv_record.site_id,
                                 rtable.recv_ref,
                                 )
        data["recv_ref"] = code

    if not recv_record.date:
        # Date not set? => set to now
        data["date"] = r.utcnow

    if not recv_record.recipient_id:
        # The inv_recv record might be created when the shipment is sent and so it
        # might not have the recipient identified. If it is null then set it to
        # the person who is logged in (the default)
        data["recipient_id"] = auth.s3_logged_in_person()

    db(rtable.id == recv_id).update(**data)

    # Lookup the send_id from a track item of this recv
    tracktable = s3db.inv_track_item
    track_item = db(tracktable.recv_id == recv_id).select(tracktable.send_id,
                                                          limitby = (0, 1),
                                                          ).first()
    if track_item:
        send_id = track_item.send_id
        # Update the Send record & lock for editing
        stable = db.inv_send
        db(stable.id == send_id).update(status = inv_ship_status["RECEIVED"],
                                        #owned_by_user = None,
                                        #owned_by_group = ADMIN,
                                        )

    # Change the status for all track items in this shipment to UNLOADING
    # - onaccept will then move the values into the site, update any request
    #   record, create any adjustment if needed and finally change the item
    #   status to ARRIVED
    db(tracktable.recv_id == recv_id).update(status = 3) # UNLOADING

    # Call onaccept for each track item (see above why)
    track_rows = db(tracktable.recv_id == recv_id).select(tracktable.id,
                                                          #tracktable.send_id,
                                                          tracktable.recv_id,
                                                          tracktable.req_item_id,
                                                          tracktable.send_inv_item_id,
                                                          tracktable.item_id,
                                                          tracktable.item_pack_id,
                                                          tracktable.quantity,
                                                          tracktable.recv_quantity,
                                                          tracktable.recv_bin,
                                                          tracktable.recv_bin_id,
                                                          tracktable.currency,
                                                          tracktable.pack_value,
                                                          tracktable.expiry_date,
                                                          tracktable.item_source_no,
                                                          tracktable.owner_org_id,
                                                          tracktable.supply_org_id,
                                                          tracktable.status,
                                                          tracktable.inv_item_status,
                                                          )

    # Defaults to inv_track_item_onaccept, but allow templates to override
    onaccept = s3db.get_config("inv_track_item", "onaccept")
    for track_item in track_rows:
        onaccept(Storage(vars = Storage(id = track_item.id),
                         record = Storage(track_item),
                         ))

    if settings.get_inv_warehouse_free_capacity_calculated():
        # Update the Warehouse Free capacity
        inv_warehouse_free_capacity(recv_record.site_id)

    if stock_cards:
        # Reload all track_items to read the recv_inv_item_ids
        rows = db(tracktable.recv_id == recv_id).select(tracktable.recv_inv_item_id,
                                                        )
        inv_item_ids = [row.recv_inv_item_id for row in rows]
        inv_stock_card_update(inv_item_ids,
                              recv_id = recv_id,
                              comments = "Shipment Received",
                              )

    # Call on_inv_recv_process hook if-configured
    tablename = "inv_recv"
    on_inv_recv_process = s3db.get_config(tablename, "on_inv_recv_process")
    if on_inv_recv_process:
        recv_record.id = recv_id
        on_inv_recv_process(recv_record)

    # Done => confirmation message, open the record
    current.session.confirmation = T("Shipment Items Received")
    redirect(URL(c="inv", f="recv",
                 args = [recv_id],
                 ))

# =============================================================================
def inv_req_job_reset(r, **attr):
    """
        Reset a job status from FAILED to QUEUED (custom REST method),
        for "Reset" action button
    """

    if r.interactive:
        if r.component and r.component.alias == "job":
            job_id = r.component_id
            if job_id:
                S3Task.reset(job_id)
                current.session.confirmation = current.T("Job reactivated")

    redirect(r.url(method="", component_id=0))

# =============================================================================
def inv_req_job_run(r, **attr):
    """
        Run a job now (custom REST method),
        for "Run Now" action button
    """

    if r.interactive:
        if r.id:
            current.s3task.run_async("inv_req_add_from_template",
                                     [r.id], # args
                                     {"user_id":current.auth.user.id} # vars
                                     )
            current.session.confirmation = current.T("Request added")

    redirect(r.url(method="", component_id=0))

# =============================================================================
def inv_req_add_from_template(req_id):
    """
        Add an Inventory Requisition from a Template
        - scheduled function to create recurring requests

        @param req_id: record ID of the request template
    """

    db = current.db
    s3db = current.s3db
    table = s3db.inv_req
    fieldnames = ["priority",
                  "site_id",
                  "purpose",
                  "requester_id",
                  "comments",
                  ]
    fields = [table[field] for field in fieldnames]

    # Load Template
    template = db(table.id == req_id).select(*fields,
                                             limitby = (0, 1)
                                             ).first()
    data = {"is_template": False}
    try:
        for field in fieldnames:
            data[field] = template[field]
    except:
        raise RuntimeError("Template not found: %s" % req_id)

    settings = current.deployment_settings
    #if settings.get_inv_generate_req_number():
    # But we have no option but to generate for a non-interactive addition
    if settings.get_inv_use_req_number():
        from .supply import supply_get_shipping_code as get_shipping_code
        code = get_shipping_code(settings.get_inv_req_shortname(),
                                 template.site_id,
                                 table.req_ref,
                                 )
        data["req_ref"] = code

    new_req_id = table.insert(**data)

    # Copy across req_items
    table = s3db.inv_req_item
    fieldnames = ["site_id",
                  "item_id",
                  "item_pack_id",
                  "quantity",
                  "pack_value",
                  "currency",
                  "comments",
                  ]
    fields = [table[field] for field in fieldnames]
    items = db(table.req_id == req_id).select(*fields)
    for item in items:
        data = {"req_id": new_req_id}
        for field in fieldnames:
            data[field] = item[field]
        table.insert(**data)

    return new_req_id

# -------------------------------------------------------------------------
def inv_req_tabs(r, match=True):
    """
        Add a set of rheader tabs for a site's Inventory Requisition management

        @param r: the S3Request (for permission checking)
        @param match: request matching is applicable for this type of site

        @return: list of rheader tab definitions
    """

    tabs = []

    settings = current.deployment_settings
    if settings.get_org_site_inv_req_tabs():

        has_permission = current.auth.s3_has_permission
        if has_permission("read", "inv_req"):

            T = current.T

            # Requests tab
            tabs = [(T("Requests"), "req")]

            # Match-tab if configured, applicable for the use-case and user
            # is permitted to match requests
            if match and settings.get_inv_req_match_tab() \
                     and has_permission("read", "inv_req",
                                        c = r.controller,
                                        f = "req_match",
                                        ):
                tabs.append((T("Match Requests"), "req_match/"))

            # Commit-tab if using commits
            if settings.get_inv_use_commit():
                tabs.append((T("Commit"), "commit"))

    return tabs

# -----------------------------------------------------------------------------
def inv_req_update_status(req_id):
    """
        Update the request committed/in-transit/fulfilled statuses from the
        quantities of items requested vs. committed/in-transit/fulfilled

        Status:
            NONE            quantity=0 for all items
            PARTIAL         quantity>0 but less than requested quantity for
                            at least one item
            COMPLETE        quantity>=requested quantity for all items
    """

    db = current.db
    s3db = current.s3db

    is_none = {"commit": True,
               "transit": True,
               "fulfil": True,
               }

    is_complete = {"commit": True,
                   "transit": True,
                   "fulfil": True,
                   }

    # Read the Items in the Request
    table = s3db.inv_req_item
    query = (table.req_id == req_id) & \
            (table.deleted == False )
    req_items = db(query).select(table.quantity,
                                 table.quantity_commit,
                                 table.quantity_transit,
                                 table.quantity_fulfil,
                                 )

    for req_item in req_items:
        quantity = req_item.quantity
        for status_type in ["commit", "transit", "fulfil"]:
            if req_item["quantity_%s" % status_type] < quantity:
                is_complete[status_type] = False
            if req_item["quantity_%s" % status_type]:
                is_none[status_type] = False

    status_update = {}
    for status_type in ["commit", "transit", "fulfil"]:
        if is_complete[status_type]:
            status_update["%s_status" % status_type] = REQ_STATUS_COMPLETE
        elif is_none[status_type]:
            status_update["%s_status" % status_type] = REQ_STATUS_NONE
        else:
            status_update["%s_status" % status_type] = REQ_STATUS_PARTIAL

    if current.deployment_settings.get_inv_req_workflow() and \
       status_update["fulfil_status"] == REQ_STATUS_COMPLETE:
        status_update["workflow_status"] = 4 # Completed

    db(s3db.inv_req.id == req_id).update(**status_update)

# =============================================================================
def inv_req_details(row):
    """
        Field method for Inventory Requisitions, representing all requested items
        as string (for use in data tables/lists)
    """

    if hasattr(row, "inv_req"):
        row = row.inv_req

    try:
        record_id = row.id
    except AttributeError:
        return None

    s3db = current.s3db
    itable = s3db.supply_item
    ltable = s3db.inv_req_item
    query = (ltable.deleted != True) & \
            (ltable.req_id == record_id) & \
            (ltable.item_id == itable.id)
    items = current.db(query).select(itable.name,
                                     ltable.quantity,
                                     )
    if items:
        items = ["%s %s" % (int(item.inv_req_item.quantity),
                            item.supply_item.name)
                 for item in items]
        return ",".join(items)

    return current.messages["NONE"]

# =============================================================================
def inv_req_drivers(row):
    """
        Field method for Inventory Requisitions, representing all assigned drivers
        as string (for use in data tables/lists)
    """

    if hasattr(row, "inv_req"):
        row = row.inv_req

    try:
        req_ref = row.req_ref
    except AttributeError:
        return None

    s3db = current.s3db
    stable = s3db.inv_send
    query = (stable.deleted != True) & \
            (stable.req_ref == req_ref)
    drivers = current.db(query).select(stable.driver_name,
                                       stable.driver_phone,
                                       stable.vehicle_plate_no,
                                       )
    if drivers:
        drivers = ["%s %s %s" % (driver.driver_name or "",
                                 driver.driver_phone or "",
                                 driver.vehicle_plate_no or "") \
                   for driver in drivers]
        return ",".join(drivers)

    return current.messages["NONE"]

# =============================================================================
def inv_req_is_approver(site_id):
    """
        Check if User has permission to Approve an Inventory Requisition
    """

    auth = current.auth

    # Will cause issues
    #if auth.s3_has_role("ADMIN"):
    #    return True

    db = current.db
    s3db = current.s3db
    atable = s3db.inv_req_approver
    query = (atable.person_id == auth.s3_logged_in_person()) & \
            (atable.deleted == False)
    entities = db(query).select(atable.pe_id)
    if not entities:
        # Not an Approver for any
        return False

    pe_ids = [row.pe_id for row in entities]

    stable = s3db.org_site
    site_entity = db(stable.site_id == site_id).select(stable.instance_type,
                                                       limitby = (0, 1),
                                                       ).first()
    itable = s3db.table(site_entity.instance_type)
    site = db(itable.site_id == site_id).select(itable.pe_id,
                                                limitby = (0, 1),
                                                ).first()

    pe_id = site.pe_id
    if pe_id in pe_ids:
        # Directly permitted
        return True

    # Check for child entities
    entity_types = ["org_organisation"] + list(auth.org_site_types.keys())
    child_pe_ids = s3db.pr_get_descendants(pe_ids, entity_types=entity_types)
    if pe_id in child_pe_ids:
        # Permitted via child entity
        return True

    return False

# =============================================================================
def inv_req_approvers(site_id):
    """
        Return people permitted to Approve an Inventory Requisition
    """

    db = current.db
    s3db = current.s3db

    stable = s3db.org_site
    site_entity = db(stable.site_id == site_id).select(stable.instance_type,
                                                       limitby = (0, 1),
                                                       ).first()
    itable = s3db.table(site_entity.instance_type)
    site = db(itable.site_id == site_id).select(itable.pe_id,
                                                limitby = (0, 1),
                                                ).first()

    pe_id = site.pe_id
    entities = s3db.pr_get_ancestors(pe_id)
    entities.append(pe_id)

    atable = s3db.inv_req_approver
    query = (atable.pe_id.belongs(entities)) & \
            (atable.deleted == False)
    approvers = db(query).select(atable.person_id,
                                 atable.title,
                                 atable.matcher,
                                 )

    return {row.person_id: {"title": row.title,
                            "matcher": row.matcher,
                            } for row in approvers}

# =============================================================================
def inv_req_create_form_mods(r):
    """
        Function to be called from REST prep functions
         - main module & components (sites & events)
    """

    T = current.T
    db = current.db
    s3 = current.response.s3
    settings = current.deployment_settings

    table = db.inv_req

    if not settings.get_inv_req_inline_forms():
        # Amend the Save button
        s3.crud.submit_button = T("Save and add Items")

    # Hide fields which don't make sense in a Create form
    table.req_ref.readable = False
    table.commit_status.readable = table.commit_status.writable = False
    table.transit_status.readable = table.transit_status.writable = False
    table.fulfil_status.readable = table.fulfil_status.writable = False
    table.workflow_status.readable = table.workflow_status.writable = False
    table.cancel.readable = table.cancel.writable = False
    table.closed.readable = table.closed.writable = False
    table.date_recv.readable = table.date_recv.writable = False
    table.recv_by_id.readable = table.recv_by_id.writable = False

    if settings.get_inv_requester_from_site():
        # Filter the list of Contacts to those for the site
        table.requester_id.widget = None
        table.requester_id.comment = S3PopupLink(c = "pr",
                                                 f = "person",
                                                 vars = {"child": "requester_id",
                                                         "parent": "req",
                                                         },
                                                 title = s3.crud_strings["pr_person"].label_create,
                                                 )
        s3.jquery_ready.append('''
$.filterOptionsS3({
'trigger':'site_id',
'target':'requester_id',
'lookupResource':'staff',
'lookupURL':S3.Ap.concat('/hrm/staff_for_site/'),
'msgNoRecords':'%s',
'optional':true,
})''' % T("No contacts yet defined for this site"))
        #table.site_id.comment = A(T("Set as default Site"),
        #                          _id = "inv_req_site_id_link",
        #                          _target = "_blank",
        #                          _href = URL(c="default",
        #                                      f="user",
        #                                      args = ["profile"],
        #                                      ),
        #                          )

    s3.scripts.append("/%s/static/scripts/S3/s3.req_create.js" % r.application)

# =============================================================================
def inv_req_inline_form(method):
    """
        Function to be called from REST prep functions
         - to add req_item components as inline forms

        @param method: the URL request method
    """

    T = current.T
    s3db = current.s3db
    table = s3db.inv_req
    s3 = current.response.s3
    # Was used by NYC template
    #postprocess = s3.inv_req_postprocess

    # Custom Form
    settings = current.deployment_settings
    fields = [#req_ref
              "site_id",
              #is_template
              "requester_id",
              "date",
              "priority",
              "date_required",
              S3SQLInlineComponent(
                "req_item",
                label = T("Items"),
                fields = ["item_id",
                          "item_pack_id",
                          "quantity",
                          "comments"
                          ]
              ),
              #purpose
              "comments",
              ]

    if method in ("create", "update"):
        # Dropdown not Autocomplete
        itable = s3db.inv_req_item
        itable.item_id.widget = None

        # Options-filter item=>pack
        jquery_ready = s3.jquery_ready
        jquery_ready.append('''
$.filterOptionsS3({
'trigger':{'alias':'req_item','name':'item_id'},
'target':{'alias':'req_item','name':'item_pack_id'},
'scope':'row',
'lookupPrefix':'supply',
'lookupResource':'item_pack',
'msgNoRecords':i18n.no_packs,
'fncPrep':S3.supply.fncPrepItem,
'fncRepresent':S3.supply.fncRepresentItem
})''')
        if settings.get_inv_requester_from_site():
            # Filter the list of Contacts to those for the site
            jquery_ready.append('''
$.filterOptionsS3({
'trigger':'site_id',
'target':'requester_id',
'lookupResource':'staff',
'lookupURL':S3.Ap.concat('/hrm/staff_for_site/'),
'msgNoRecords':'%s',
'optional':true,
})''' % T("No contacts yet defined for this site"))

            # Popup link to allow adding a contact (...for the site)
            table.requester_id.widget = None
            table.requester_id.comment = S3PopupLink(c = "pr",
                                                     f = "person",
                                                     vars = {"child": "requester_id",
                                                             "parent": "req",
                                                             },
                                                     title = s3.crud_strings["pr_person"].label_create,
                                                     )

            # Link to user profile to allow setting this site
            # as their current default site, so that they appear
            # in the dropdown themselves
            table.site_id.comment = A(T("Set as default Site"),
                                      _id = "inv_req_site_id_link",
                                      _target = "_blank",
                                      _href = URL(c = "default",
                                                  f = "user",
                                                  args = ["profile"],
                                                  ),
                                      )

    if method in ("update", "read"):
        # Append status details
        status_fields = []
        if settings.get_inv_req_status_writable():
            if settings.get_inv_use_commit():
                status_fields.append("commit_status")
            if settings.get_inv_req_show_quantity_transit():
                status_fields.append("transit_status")
            status_fields.append("fulfil_status")
        status_fields.append("date_recv")

        fields.extend(status_fields)

        # Show request number?
        if settings.get_inv_use_req_number():
            if settings.get_inv_generate_req_number():
                table.req_ref.writable = False
            fields.insert(0, "req_ref")
    else:
        # Is-template flag can only be set during create
        fields.insert(1, "is_template")

    if settings.get_inv_req_ask_purpose():
        fields.insert(-1, "purpose")

    #if postprocess:
    #    crud_form = S3SQLCustomForm(*fields, postprocess=postprocess)
    #else:
    crud_form = S3SQLCustomForm(*fields)
    s3db.configure("inv_req",
                   crud_form = crud_form,
                   )

    # Reset to standard submit button
    s3.crud.submit_button = T("Save")

# =============================================================================
def inv_req_match(rheader = None):
    """
        Generic controller to display all Inventory Requisitions a site could potentially
        fulfill as a tab of that site instance
            - add as inv_req_match controller to the module, then
            - configure as rheader-tab "inv_req_match/" for the site resource

        @param rheader: module-specific rheader

        NB make sure rheader uses s3_rheader_resource to handle "viewing"
        NB can override rheader in customise_inv_req_controller by
           updating attr dict
    """

    T = current.T
    s3db = current.s3db
    s3 = current.response.s3
    request = current.request
    settings = current.deployment_settings

    output = {}

    viewing = request.get_vars.get("viewing", None)
    if not viewing:
        return output
    if "." in viewing:
        tablename, record_id = viewing.split(".", 1)
    else:
        return output

    # Ensure any custom settings are applied
    customise = settings.get("customise_%s_resource" % tablename)
    if customise:
        try:
            customise(request, tablename)
        except:
            current.log.error("customise_%s_resource is using attributes of r which aren't in request" % tablename)

    table = s3db[tablename]
    row = current.db(table.id == record_id).select(table.site_id,
                                                   limitby = (0, 1),
                                                   ).first()
    if row:
        site_id = row.site_id
    else:
        return output

    actions = [{"label": s3_str(T("Check")),
                "url": URL(c="inv", f="req",
                           args = ["[id]", "check"],
                           vars = {"site_id": site_id,
                                   }
                           ),
                "_class": "action-btn",
                }
               ]

    if current.auth.s3_has_permission("update", tablename, record_id):
        # @ToDo: restrict to those which we've not already committed/sent?
        if settings.get_inv_use_commit():
            actions.append({"label": s3_str(T("Commit")),
                            "url": URL(c="inv", f="commit_req",
                                       args = ["[id]"],
                                       vars = {"site_id": site_id,
                                               }
                                       ),
                            "_class": "action-btn",
                            })
        # Better to force people to go through the Check process
        #actions.append({"label": s3_str(T("Send")),
        #                "url": URL(c="inv", f="send_req",
        #                           args = ["[id]"],
        #                           vars = {"site_id": site_id,
        #                                   }
        #                           ),
        #                "_class": "action-btn dispatch",
        #                })

    s3.actions = actions

    if rheader is None:
        if tablename == "org_office":
            from .org import org_rheader
            rheader = org_rheader
        elif tablename == "org_facility":
            from .org import org_facility_rheader
            rheader = org_facility_rheader
        elif tablename == "inv_warehouse":
            rheader = inv_rheader
        elif tablename == "cr_shelter":
            from .cr import cr_shelter_rheader
            rheader = cr_shelter_rheader
        elif tablename == "hms_hospital":
            from .hms import hms_hospital_rheader
            rheader = hms_hospital_rheader

    s3.filter = (s3db.inv_req.site_id != site_id)
    s3db.configure("inv_req",
                   insertable = False,
                   )

    # Pre-process
    def prep(r):
        # Plugin OrgRoleManager when appropriate
        S3OrgRoleManager.set_method(r, entity=tablename, record_id=record_id)

        if settings.get_inv_req_workflow():
            # Only show Approved Requests
            r.resource.add_filter(FS("workflow_status") == 3)

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.representation == "html":
            output["title"] = s3.crud_strings[tablename].title_display
        return output
    s3.postp = postp

    return current.rest_controller("inv", "req",
                                   rheader = rheader,
                                   )

# =============================================================================
def inv_req_recv_sites(r, **attr):
    """
        Lookup to limit
            - from sites to those requested_from the selected Requests' remaining Items
            - to sites to those from the selected Requests
        Accessed from inv_recv.js
        Access via the .json representation to avoid work rendering menus, etc
    """

    
    req_id = r.get_vars.get("req_id")
    if not req_id:
        return
    req_id = req_id.split(",")

    s3db = current.s3db

    # From Sites
    available_from_sites = s3db.inv_recv.from_site_id.requires.options(zero = False)
    ritable = s3db.inv_req_item
    if len(req_id) == 1:
        query = (ritable.req_id == req_id[0])
    else:
        query = (ritable.req_id.belongs(req_id))
    query &= (ritable.quantity_transit < ritable.quantity)
    request_items = current.db(query).select(ritable.site_id)
    requested_from_sites = set([int(row.site_id) for row in request_items if row.site_id])
    from_sites = []
    for site in available_from_sites:
        if site[0] and int(site[0]) in requested_from_sites:
            from_sites.append(site)

    # To Sites
    available_to_sites = s3db.inv_recv.site_id.requires.options(zero = False)
    rtable = s3db.inv_req
    if len(req_id) == 1:
        query = (rtable.id == req_id[0])
        limitby = (0, 1)
    else:
        query = (rtable.id.belongs(req_id))
        limitby = (0, len(req_id))
    requests = current.db(query).select(rtable.site_id,
                                        limitby = limitby,
                                        )
    requested_to_sites = set([int(row.site_id) for row in requests])
    to_sites = []
    for site in available_to_sites:
        if int(site[0]) in requested_to_sites:
            to_sites.append(site)

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps((from_sites, to_sites), separators=SEPARATORS)

# =============================================================================
def inv_req_rheader(r, check_page=False):
    """
        Resource Header for Inventory Requisitions
    """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None

    record = r.record
    if not record:
        # RHeaders only used in single-record views
        return None

    if r.name == "req":
        T = current.T
        db = current.db
        s3db = current.s3db
        s3 = current.response.s3
        settings = current.deployment_settings

        is_template = record.is_template
        use_commit = settings.get_inv_use_commit()
        use_workflow = settings.get_inv_req_workflow()

        site_id = record.site_id
        workflow_status = record.workflow_status

        tabs = [(T("Edit Details"), None)]
        if settings.get_inv_multiple_req_items():
            req_item_tab_label = T("Items")
        else:
            req_item_tab_label = T("Item")
        tabs.append((req_item_tab_label, "req_item"))
        #if settings.get_inv_req_document_filing():
        tabs.append((T("Documents"), "document"))
        if is_template:
            tabs.append((T("Schedule"), "job"))
        else:
            # Hide these if no Items on one of these requests yet
            auth = current.auth
            req_id = record.id
            user = auth.user
            user_site_id = user.site_id if user else None
            ritable = s3db.inv_req_item
            possibly_complete = db(ritable.req_id == req_id).select(ritable.id,
                                                                    limitby = (0, 1),
                                                                    )
            if possibly_complete:
                if use_commit:
                    tabs.append((T("Commitments"), "commit"))
                if user_site_id:
                    tabs.append((T("Check"), "check"))
                if use_workflow:
                    if workflow_status == 1: # Draft
                        if current.auth.s3_has_permission("update", "inv_req", record_id=req_id):
                            submit_btn = A(T("Submit for Approval"),
                                           _href = URL(c = "inv",
                                                       f = "req",
                                                       args = [req_id, "submit"]
                                                       ),
                                           _id = "req-submit",
                                           _class = "action-btn",
                                           )
                            s3.jquery_ready.append('''S3.confirmClick('#req-submit','%s')''' \
                                    % T("Are you sure you want to submit this request?"))
                            s3.rfooter = TAG[""](submit_btn)
                    elif workflow_status == 2: # Submitted
                        if inv_req_is_approver(site_id):
                            # Have they already approved?
                            atable = s3db.inv_req_approver_req
                            query = (atable.req_id == req_id) & \
                                    (atable.person_id == auth.s3_logged_in_person())
                            approved = db(query).select(atable.id,
                                                        limitby = (0, 1),
                                                        )
                            if not approved:
                                approve_btn = A(T("Approve"),
                                               _href = URL(c = "inv",
                                                           f = "req",
                                                           args = [req_id, "approve_req"]
                                                           ),
                                               _id = "req-approve",
                                               _class = "action-btn",
                                               )
                                s3.jquery_ready.append('''S3.confirmClick('#req-approve','%s')''' \
                                        % T("Are you sure you want to approve this request?"))
                                s3.rfooter = TAG[""](approve_btn)
                    elif workflow_status == 3: # Approved
                        # @ToDo: Check for permission on sites requested_from
                        if current.auth.s3_has_permission("create", "inv_send"):
                            fulfil_btn = A(T("Fulfil Request"),
                                           _href = URL(c = "inv",
                                                       f = "send",
                                                       args = ["create"],
                                                       vars = {"req_id": req_id},
                                                       ),
                                           _id = "req-fulfil",
                                           _class = "action-btn",
                                           )
                            s3.jquery_ready.append('''S3.confirmClick('#req-fulfil','%s')''' \
                                    % T("Are you sure you want to fulfil this request?"))
                            s3.rfooter = TAG[""](fulfil_btn)

        if not check_page:
            rheader_tabs = s3_rheader_tabs(r, tabs)
        else:
            rheader_tabs = DIV()

        if r.component and \
           r.component_name == "commit" and \
           r.component_id:
            prepare_btn = A(T("Prepare Shipment"),
                            _href = URL(f = "send_commit",
                                        args = [r.component_id]
                                        ),
                            _id = "send-commit",
                            _class = "action-btn",
                            )
            s3.rfooter = TAG[""](prepare_btn)

        if site_id:
            stable = s3db.org_site
        if use_workflow and workflow_status in (1, 2, 5): # Draft/Submitted/Cancelled
            transit_status = ("",)
        elif settings.get_inv_req_show_quantity_transit() and not is_template:
            transit_status = req_status_opts().get(record.transit_status,
                                                   "")
            # @ToDo: Create the 'incoming' function if we need this!
            #if site_id and \
            #   record.transit_status in [REQ_STATUS_PARTIAL, REQ_STATUS_COMPLETE] and \
            #   record.fulfil_status in [None, REQ_STATUS_NONE, REQ_STATUS_PARTIAL]:
            #   site_record = db(stable.site_id == site_id).select(stable.uuid,
            #                                                      stable.instance_type,
            #                                                      limitby = (0, 1),
            #                                                      ).first()
            #   instance_type = site_record.instance_type
            #   table = s3db[instance_type]
            #   query = (table.uuid == site_record.uuid)
            #   instance_id = db(query).select(table.id,
            #                                  limitby = (0, 1),
            #                                  ).first().id
            #   transit_status = SPAN(transit_status,
            #                         A(T("Incoming Shipments"),
            #                           _href = URL(c = instance_type.split("_")[0],
            #                                       f = "incoming",
            #                                       vars = {"viewing" : "%s.%s" % (instance_type, instance_id)}
            #                                       )
            #                           )
            #                      )
            transit_status = (TH("%s: " % T("Transit Status")),
                              transit_status)
        else:
            transit_status = ("",)

        table = r.table

        if settings.get_inv_use_req_number() and not is_template:
            headerTR = TR(TH("%s: " % table.req_ref.label),
                          TD(table.req_ref.represent(record.req_ref, show_link=True))
                          )
        else:
            headerTR = TR(TD(settings.get_inv_req_form_name(),
                             _colspan = 2,
                             _class = "pdf_title",
                             ),
                          )
        if site_id:
            org_id = db(stable.site_id == site_id).select(stable.organisation_id,
                                                          limitby = (0, 1),
                                                          ).first().organisation_id
            logo = s3db.org_organisation_logo(org_id)
            if logo:
                headerTR.append(TD(logo,
                                   _colspan = 2,
                                   ))

        if is_template:
            row1 = ""
            row3 = ""
        else:
            if use_workflow and workflow_status in (1, 2, 5): # Draft/Submitted/Cancelled
                row1_status = (TH("%s: " % table.workflow_status.label),
                               table.workflow_status.represent(workflow_status),
                               )
                fulfil_status = ("",)
            else:
                if use_commit:
                    row1_status = (TH("%s: " % table.commit_status.label),
                                   table.commit_status.represent(record.commit_status),
                                   )
                else:
                    row1_status = ("",)
                fulfil_status = (TH("%s: " % table.fulfil_status.label),
                                 table.fulfil_status.represent(record.fulfil_status),
                                 )
            row1 = TR(TH("%s: " % table.date.label),
                      table.date.represent(record.date),
                      *row1_status
                      )
            row3 = TR(TH("%s: " % table.date_required.label),
                      table.date_required.represent(record.date_required),
                      *fulfil_status
                      )

        rheader = DIV(TABLE(headerTR,
                            row1,
                            TR(TH("%s: " % table.site_id.label),
                               table.site_id.represent(site_id),
                               *transit_status
                               ),
                            row3,
                            TR(TH("%s: " % table.requester_id.label),
                               table.requester_id.represent(record.requester_id),
                               ),
                            TR(TH("%s: " % table.purpose.label),
                               record.purpose or current.messages["NONE"],
                               ),
                            TR(TH("%s: " % table.comments.label),
                               TD(record.comments or "",
                                  _colspan = 3,
                                  ),
                               ),
                            ),
                      rheader_tabs,
                      )

    else:
        # Not defined, probably using wrong rheader
        rheader = None

    return rheader

# =============================================================================
def inv_req_send_sites(r, **attr):
    """
        Lookup to limit
            - from sites to those requested_from the selected Requests' remaining Items
            - to sites to those from the selected Requests
        Accessed from inv_send.js
        Access via the .json representation to avoid work rendering menus, etc
    """

    
    req_id = r.get_vars.get("req_id")
    if not req_id:
        return
    req_id = req_id.split(",")

    s3db = current.s3db

    # From Sites
    available_from_sites = s3db.inv_send.site_id.requires.options(zero = False)
    ritable = s3db.inv_req_item
    if len(req_id) == 1:
        query = (ritable.req_id == req_id[0])
    else:
        query = (ritable.req_id.belongs(req_id))
    query &= (ritable.quantity_transit < ritable.quantity)
    request_items = current.db(query).select(ritable.site_id)
    requested_from_sites = set([int(row.site_id) for row in request_items if row.site_id])
    from_sites = []
    for site in available_from_sites:
        if int(site[0]) in requested_from_sites:
            from_sites.append(site)

    # To Sites
    available_to_sites = s3db.inv_send.to_site_id.requires.options(zero = False)
    rtable = s3db.inv_req
    if len(req_id) == 1:
        query = (rtable.id == req_id[0])
        limitby = (0, 1)
    else:
        query = (rtable.id.belongs(req_id))
        limitby = (0, len(req_id))
    requests = current.db(query).select(rtable.site_id,
                                        limitby = limitby,
                                        )
    requested_to_sites = set([int(row.site_id) for row in requests])
    to_sites = []
    for site in available_to_sites:
        if site[0] and int(site[0]) in requested_to_sites:
            to_sites.append(site)

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps((from_sites, to_sites), separators=SEPARATORS)

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
        permit = current.auth.s3_has_permission
        settings = current.deployment_settings
        if settings.has_module("hrm"):
            STAFF = settings.get_hrm_staff_label()
            tabs.append((STAFF, "human_resource"))
            if permit("create", "hrm_human_resource_site") and \
               permit("update", tablename,
                      record_id = r.id):
                tabs.append((T("Assign %(staff)s") % {"staff": STAFF}, "assign"))
        if settings.has_module("asset") and permit("read", "asset_asset"):
            tabs.insert(6, (T("Assets"), "asset"))
        tabs.extend(inv_tabs(r))
        tabs.extend(inv_req_tabs(r))
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
            rheader = DIV(TABLE(TR(TD(logo),
                                   TD(rheader_fields)
                                   )))
        else:
            rheader = DIV(rheader_fields)
        rheader.append(rheader_tabs)

    elif tablename == "inv_inv_item":
        # Tabs
        tabs = [(T("Details"), None),
                ]
        if current.deployment_settings.get_inv_stock_cards():
            tabs += [(T("Adjust"), "adj/", {"item": record.id,
                                            "site": record.site_id,
                                            }),
                     (T("Stock Card"), "stock_card/"),
                     ]
        else:
            tabs += [(T("Adjustments"), "adj_item"),
                     (T("Track Shipment"), "track_movement/"),
                     ]
                
        rheader_tabs = DIV(s3_rheader_tabs(r, tabs))

        # Header
        rheader = DIV(TABLE(TR(TH("%s: " % table.item_id.label),
                               table.item_id.represent(record.item_id),
                               TH("%s: " % table.item_pack_id.label),
                               table.item_pack_id.represent(record.item_pack_id),
                               ),
                            TR(TH("%s: " % table.site_id.label),
                               TD(table.site_id.represent(record.site_id),
                                  _colspan = 3,
                                  ),
                               ),
                            ),
                      rheader_tabs,
                      )

    elif tablename == "inv_kitting":
        # Tabs
        tabs = [(T("Details"), None),
                (T("Pick List"), "item"),
               ]
        rheader_tabs = DIV(s3_rheader_tabs(r, tabs))

        # Header
        rheader = DIV(TABLE(TR(TH("%s: " % table.req_ref.label),
                               TD(table.req_ref.represent(record.req_ref),
                                  _colspan = 3,
                                  ),
                               ),
                            TR(TH("%s: " % table.item_id.label),
                               table.item_id.represent(record.item_id),
                               TH("%s: " % table.item_pack_id.label),
                               table.item_pack_id.represent(record.item_pack_id),
                               TH("%s: " % table.quantity.label),
                               table.quantity.represent(record.quantity),
                               ),
                            TR(TH("%s: " % table.site_id.label),
                               TD(table.site_id.represent(record.site_id),
                                  _colspan = 3,
                                  ),
                               ),
                            TR(TH("%s: " % table.repacked_id.label),
                               TD(table.repacked_id.represent(record.repacked_id),
                                  _colspan = 3,
                                  ),
                               ),
                            TR(TH("%s: " % table.date.label),
                               TD(table.date.represent(record.date),
                                  _colspan = 3,
                                  ),
                               ),
                            ),
                      rheader_tabs,
                      )

    elif tablename == "inv_track_item":
        # Tabs
        tabs = [(T("Details"), None),
                (T("Track Shipment"), "inv_item/"),
                ]
        rheader_tabs = DIV(s3_rheader_tabs(r, tabs))

        # Get site data
        table = s3db.inv_inv_item
        irecord = current.db(table.id == record.send_inv_item_id).select(table.site_id,
                                                                         limitby = (0, 1),
                                                                         ).first()
        # Header
        if irecord:
            rheader = DIV(TABLE(TR(TH("%s: " % table.item_id.label),
                                   table.item_id.represent(record.item_id),
                                   TH("%s: " % table.item_pack_id.label),
                                   table.item_pack_id.represent(record.item_pack_id),
                                   ),
                                TR(TH( "%s: " % table.site_id.label),
                                   TD(table.site_id.represent(irecord.site_id),
                                      _colspan = 3,
                                      ),
                                   ),
                                ),
                          rheader_tabs,
                          )
        else:
            rheader = DIV(TABLE(TR(TH("%s: " % table.item_id.label),
                                   table.item_id.represent(record.item_id),
                                   TH("%s: " % table.item_pack_id.label),
                                   table.item_pack_id.represent(record.item_pack_id),
                                   ),
                                ),
                          rheader_tabs,
                          )

    elif tablename == "inv_stock_card":
        # Tabs not used...we only ever see Log tab
        #tabs = [(T("Details"), None),
        #        (T("Log"), "stock_log"),
        #        ]
        #rheader_tabs = DIV(s3_rheader_tabs(r, tabs))

        db = current.db
        item_id = record.item_id
        site_id = record.site_id
        NONE = current.messages["NONE"]

        # Lookup Item Details
        itable = s3db.supply_item
        item = db(itable.id == item_id).select(itable.name,
                                               itable.code,
                                               limitby = (0, 1),
                                               ).first()

        # Lookup Stock Minimum
        mtable = s3db.inv_minimum
        query = (mtable.item_id == item_id) & \
                (mtable.site_id == site_id)
        minimum = db(query).select(mtable.quantity,
                                   limitby = (0, 1),
                                   ).first()
        if minimum:
            stock_minimum = minimum.quantity
        else:
            stock_minimum = NONE

        # Header
        rheader = DIV(TABLE(TR(TH("%s: " % table.site_id.label),
                               TD(table.site_id.represent(site_id)),
                               TD(),
                               TD(),
                               TH("%s: " % table.stock_card_ref.label),
                               record.stock_card_ref,
                               ),
                            TR(TH("%s: " % T("Item Description")),
                               item.name,
                               TH("%s: " % T("Item Code")),
                               item.code,
                               TH("%s: " % table.item_pack_id.label),
                               table.item_pack_id.represent(record.item_pack_id),
                               ),
                            TR(TH("%s: " % table.item_source_no.label),
                               record.item_source_no or NONE,
                               TH("%s: " % table.expiry_date.label),
                               record.expiry_date or NONE,
                               TH("%s: " % T("Stock Minimum")),
                               stock_minimum,
                               ),
                            ),
                      #rheader_tabs,
                      )

    # Build footer
    inv_rfooter(r, record)

    return rheader

# =============================================================================
def inv_rfooter(r, record):
    """ Resource Footer for Warehouses and Inventory Items """

    if "site_id" not in record:
        return

    if (r.component and r.component_name == "inv_item"):
        T = current.T
        rfooter = TAG[""]()
        component_id = r.component_id
        if not current.deployment_settings.get_inv_direct_stock_edits() and \
           current.auth.s3_has_permission("update", "inv_warehouse",
                                          record_id = r.id):
            if component_id:
                asi_btn = A(T("Adjust Stock Item"),
                            _href = URL(c = "inv",
                                        f = "adj",
                                        args = ["create"],
                                        vars = {"site": record.site_id,
                                                "item": component_id,
                                                },
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
                                   vars = {"viewing": "inv_inv_item.%s" % component_id},
                                   ),
                       _class = "action-btn"
                       )
            rfooter.append(ts_btn)

        current.response.s3.rfooter = rfooter

# =============================================================================
def inv_remove(inv_rec,
               required_total,
               required_pack_value = 1,
               current_track_total = 0,
               update = True,
               ):
    """
        Check that the required_total can be removed from the inv_record
        if there is insufficient stock then set up the total to being
        what is in stock otherwise set it to be the required total.
        If the update flag is true then remove it from stock.

        The current total is what has already been removed for this
        transaction.
    """

    db = current.db
    inv_item_table = db.inv_inv_item
    siptable = db.supply_item_pack
    inv_p_qnty = db(siptable.id == inv_rec.item_pack_id).select(siptable.quantity,
                                                                limitby = (0, 1),
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

# =============================================================================
def inv_send_controller():
    """
       RESTful CRUD controller for inv_send
    """

    T = current.T
    db = current.db
    s3db = current.s3db

    sendtable = s3db.inv_send

    # Limit site_id to sites the user has permissions for
    error_msg = T("You do not have permission for any facility to send a shipment.")
    current.auth.permitted_facilities(table = sendtable,
                                      error_msg = error_msg)

    response = current.response
    s3 = response.s3

    def prep(r):
        settings = current.deployment_settings
        send_req = settings.get_inv_send_req()

        record = r.record
        if record:
            status = record.status
        elif r.method == "create":
            req_id = r.get_vars.get("req_id")
            if req_id:
                if send_req:
                    s3db.inv_send_req.req_id.default = req_id
                else:
                    rtable = s3db.inv_req
                    req = db(rtable.id == req_id).select(rtable.req_ref,
                                                         limitby = (0, 1),
                                                         ).first()
                    sendtable.req_ref.default = req.req_ref

        if r.component:
            cname = r.component_name
            if cname == "document":
                # Simplify a little
                table = s3db.doc_document
                table.file.required = True
                table.url.readable = table.url.writable = False
                table.date.readable = table.date.writable = False

            elif cname == "send_pallet":
                send_id = r.id
                # Number the Pallet automatically
                sptable = s3db.inv_send_pallet
                query = (sptable.send_id == send_id)
                field = sptable.number
                max_field = field.max()
                current_number = db(query).select(max_field,
                                                  orderby = max_field,
                                                  limitby = (0, 1)
                                                  ).first()[max_field]
                if current_number:
                    next_number = current_number + 1
                else:
                    next_number = 1
                field.default = next_number
                # Filter out Items which are already palletised
                spitable = s3db.inv_send_pallet_item
                query &= (sptable.id == spitable.send_pallet_id)
                rows = db(query).select(spitable.track_item_id)
                track_item_ids = [row.track_item_id for row in rows]
                spitable.track_item_id.requires.set_filter(not_filterby = "id",
                                                           not_filter_opts = track_item_ids,
                                                           )

            elif cname == "track_item":

                # Security-wise, we are already covered by configure()
                # Performance-wise, we should optimise for UI-acessible flows
                #method = r.method
                #if method in ("create", "delete"):
                #    # Can only create or delete track items for a send record
                #    # if the status is preparing
                #    if status != SHIP_STATUS_IN_PROCESS:
                #        return False
                if r.method == "delete":
                    return inv_track_item_deleting(r.component_id)

                tracktable = s3db.inv_track_item
                iitable = s3db.inv_inv_item

                # Set Validator for checking against the number of items in the warehouse
                req_vars = r.vars
                send_inv_item_id = req_vars.send_inv_item_id
                if send_inv_item_id:
                    if not req_vars.item_pack_id:
                        req_vars.item_pack_id = db(iitable.id == send_inv_item_id).select(iitable.item_pack_id,
                                                                                          limitby = (0, 1),
                                                                                          ).first().item_pack_id
                    tracktable.quantity.requires = IS_AVAILABLE_QUANTITY(send_inv_item_id,
                                                                         req_vars.item_pack_id,
                                                                         )

                bin_site_layout = settings.get_inv_bin_site_layout()
                track_pack_values = settings.get_inv_track_pack_values()

                def set_track_attr(status):
                    # By default Make all fields writable False
                    for field in tracktable.fields:
                        tracktable[field].writable = False
                    # Hide some fields
                    tracktable.send_id.readable = False
                    tracktable.recv_id.readable = False
                    tracktable.bin.readable = False
                    tracktable.layout_id.readable = False
                    tracktable.item_id.readable = False
                    tracktable.recv_quantity.readable = False
                    tracktable.return_quantity.readable = False
                    tracktable.expiry_date.readable = False
                    tracktable.owner_org_id.readable = False
                    tracktable.supply_org_id.readable = False
                    tracktable.adj_item_id.readable = False
                    if status == TRACK_STATUS_PREPARING:
                        # Show some fields
                        tracktable.send_inv_item_id.writable = True
                        tracktable.item_pack_id.writable = True
                        tracktable.quantity.writable = True
                        #tracktable.req_quantity.readable = True
                        tracktable.comments.writable = True
                        # Hide some fields
                        tracktable.currency.readable = False
                        tracktable.pack_value.readable = False
                        tracktable.item_source_no.readable = False
                        tracktable.inv_item_status.readable = False
                    elif status == TRACK_STATUS_ARRIVED:
                        # Shipment arrived display some extra fields at the destination
                        tracktable.item_source_no.readable = True
                        tracktable.recv_quantity.readable = True
                        tracktable.return_quantity.readable = True
                        if bin_site_layout:
                            tracktable.recv_bin_id.readable = True
                        else:
                            tracktable.recv_bin.readable = True
                        if track_pack_values:
                            tracktable.currency.readable = True
                            tracktable.pack_value.readable = True
                    elif status == TRACK_STATUS_RETURNING:
                        tracktable.return_quantity.readable = True
                        tracktable.return_quantity.writable = True
                        tracktable.currency.readable = False
                        tracktable.pack_value.readable = False

                if bin_site_layout:
                    bin_field = "layout_id"
                else:
                    bin_field = "bin"

                if status in (SHIP_STATUS_RECEIVED, SHIP_STATUS_CANCEL):
                    deletable = editable = insertable = False
                    list_fields = [#"status",
                                   "item_id",
                                   "item_pack_id",
                                   bin_field,
                                   "quantity",
                                   "recv_quantity",
                                   "return_quantity",
                                   "owner_org_id",
                                   "supply_org_id",
                                   "inv_item_status",
                                   "comments",
                                   ]
                    if track_pack_values:
                        list_fields.insert(6, "pack_value")
                        list_fields.insert(6, "currency")

                elif status == SHIP_STATUS_RETURNING:
                    deletable = insertable = False
                    editable = True
                    list_fields = [#"status",
                                   "item_id",
                                   "item_pack_id",
                                   "quantity",
                                   "return_quantity",
                                   bin_field,
                                   "owner_org_id",
                                   "supply_org_id",
                                   "inv_item_status",
                                   ]
                    if track_pack_values:
                        list_fields.insert(3, "pack_value")
                        list_fields.insert(3, "currency")

                else:
                    if status == SHIP_STATUS_IN_PROCESS:
                        deletable = editable = insertable = True
                    else:
                        deletable = editable = insertable = False

                    list_fields = [#"status",
                                   "item_id",
                                   "item_pack_id",
                                   "quantity",
                                   bin_field,
                                   "owner_org_id",
                                   "supply_org_id",
                                   "inv_item_status",
                                   ]
                    if track_pack_values:
                        list_fields.insert(4, "pack_value")
                        list_fields.insert(4, "currency")
                    if r.interactive:
                        if send_req:
                            s3db.configure("inv_track_item",
                                           extra_fields = ["req_item_id"],
                                           )
                            tracktable.quantity_needed = \
                                Field.Method("quantity_needed",
                                             inv_track_item_quantity_needed
                                             )
                            list_fields.insert(2, (T("Quantity Needed"),
                                                   "quantity_needed"))

                s3db.configure("inv_track_item",
                               # Lock the record so it can't be fiddled with
                               deletable = deletable,
                               editable = editable,
                               insertable = insertable,
                               list_fields = list_fields,
                               )

                # Hide the values that will be copied from the inv_inv_item record
                if r.component_id:
                    track_record = db(tracktable.id == r.component_id).select(tracktable.req_item_id,
                                                                              tracktable.send_inv_item_id,
                                                                              tracktable.item_pack_id,
                                                                              tracktable.status,
                                                                              tracktable.quantity,
                                                                              limitby = (0, 1),
                                                                              ).first()
                    set_track_attr(track_record.status)
                    # If the track record is linked to a request item then
                    # the stock item has already been selected so make it read only
                    if track_record and track_record.get("req_item_id"):
                        tracktable.send_inv_item_id.writable = False
                        tracktable.item_pack_id.writable = False
                        stock_qnty = track_record.quantity
                        tracktable.quantity.comment = T("%(quantity)s in stock") % {"quantity": stock_qnty}
                        tracktable.quantity.requires = IS_AVAILABLE_QUANTITY(track_record.send_inv_item_id,
                                                                             track_record.item_pack_id,
                                                                             )
                    # Hide the item id
                    tracktable.item_id.readable = False
                else:
                    set_track_attr(TRACK_STATUS_PREPARING)

                if status == SHIP_STATUS_IN_PROCESS:
                    # We replace filterOptionsS3
                    f = tracktable.send_inv_item_id
                    f.comment = None
                    if s3.debug:
                        s3.scripts.append("/%s/static/scripts/S3/s3.inv_send_item.js" % r.application)
                    else:
                        s3.scripts.append("/%s/static/scripts/S3/s3.inv_send_item.min.js" % r.application)
                    # Filter out Items which have Quantity 0, are Expired or in Bad condition
                    site_id = record.site_id
                    ii_query = (iitable.quantity > 0) & \
                               ((iitable.expiry_date >= r.now) | ((iitable.expiry_date == None))) & \
                               (iitable.status == 0)
                    # Restrict to items from this facility only
                    query = ii_query & (iitable.site_id == site_id)
                    f.requires = f.requires.other
                    f.requires.dbset = db(query)

                    if settings.get_inv_send_req():
                        srtable = s3db.inv_send_req
                        reqs = db(srtable.send_id == r.id).select(srtable.req_id)
                        if reqs:
                            # Allow populating req_item_id
                            f = tracktable.req_item_id
                            f.writable = True
                            f.comment = None
                            f.label = T("Request")
                            # Limit send_inv_item_id to
                            # - Items in the Request
                            # - Items Requested from this site
                            # - Items not yet Shipped
                            req_ids = [row.req_id for row in reqs]
                            iptable = s3db.supply_item_pack
                            rtable = s3db.inv_req
                            ritable = s3db.inv_req_item
                            riptable = s3db.get_aliased(iptable, "req_item_pack")
                            if len(req_ids) == 1:
                                query = (rtable.id == req_ids[0])
                            else:
                                query = (rtable.id.belongs(req_ids))
                            query &= (ritable.req_id == rtable.id) & \
                                     (ritable.site_id == site_id) & \
                                     (ritable.quantity_transit < ritable.quantity) & \
                                     (ritable.item_pack_id == riptable.id) & \
                                     (ritable.item_id == iitable.item_id) & \
                                     (iitable.site_id == site_id) & \
                                     (iitable.item_pack_id == iptable.id)
                            items = db(query).select(iitable.id,
                                                     iitable.quantity,
                                                     iptable.quantity,
                                                     rtable.req_ref,
                                                     ritable.id,
                                                     ritable.quantity,
                                                     riptable.quantity,
                                                     )
                            inv_data = {}
                            inv_item_ids = []
                            iiappend = inv_item_ids.append
                            for row in items:
                                inv_pack_quantity = row["supply_item_pack.quantity"]
                                req_pack_quantity = row["req_item_pack.quantity"]
                                req_ref = row["inv_req.req_ref"]
                                inv_row = row["inv_inv_item"]
                                req_row = row["inv_req_item"]
                                inv_item_id = inv_row.id
                                iiappend(inv_item_id)
                                if inv_item_id in inv_data:
                                    inv_data[inv_item_id]["req_items"].append({"inv_quantity": inv_row.quantity * inv_pack_quantity,
                                                                               "req_item_id": req_row.id,
                                                                               "req_quantity": req_row.quantity * req_pack_quantity,
                                                                               "req_ref": req_ref,
                                                                               })
                                else:
                                    inv_data[inv_item_id] = {"req_items": [{"inv_quantity": inv_row.quantity * inv_pack_quantity,
                                                                            "req_item_id": req_row.id,
                                                                            "req_quantity": req_row.quantity * req_pack_quantity,
                                                                            "req_ref": req_ref,
                                                                            }],
                                                             }
                            # Remove req_ref when there are no duplicates to distinguish
                            for inv_item_id in inv_data:
                                req_items = inv_data[inv_item_id]["req_items"]
                                if len(req_items) == 1:
                                    req_items[0].pop("req_ref")

                            # Set the dropdown options
                            query = (iitable.id.belongs(inv_item_ids))
                            tracktable.send_inv_item_id.requires.dbset = db(query & ii_query)

                            # Add Packs to replace the filterOptionsS3 lookup
                            query &= (iitable.item_id == iptable.item_id)
                            rows = db(query).select(iitable.id,
                                                    iptable.id,
                                                    iptable.name,
                                                    iptable.quantity,
                                                    )
                            for row in rows:
                                inv_item_id = row["inv_inv_item.id"]
                                pack = row.supply_item_pack
                                this_data = inv_data[inv_item_id]
                                packs = this_data.get("packs")
                                if not packs:
                                    this_data["packs"] = [{"id": pack.id,
                                                           "name": pack.name,
                                                           "quantity": pack.quantity,
                                                           },
                                                          ]
                                else:
                                    this_data["packs"].append({"id": pack.id,
                                                               "name": pack.name,
                                                               "quantity": pack.quantity,
                                                               })

                            # Pass data to s3.inv_send_item.js
                            # to Apply req_item_id & quantity when item_id selected
                            s3.js_global.append('''S3.supply.inv_items=%s''' % json.dumps(inv_data, separators=SEPARATORS))

                if r.interactive:
                    crud_strings = s3.crud_strings.inv_send
                    if status == SHIP_STATUS_IN_PROCESS:
                        crud_strings.title_update = \
                        crud_strings.title_display = T("Process Shipment to Send")
                    elif "site_id" in req_vars and status == SHIP_STATUS_SENT:
                        crud_strings.title_update = \
                        crud_strings.title_display = T("Review Incoming Shipment to Receive")
        else:
            # No Component
            # Set the inv_send attributes
            def set_send_attr(status):
                if status == SHIP_STATUS_IN_PROCESS:
                    if settings.get_inv_send_ref_writable():
                        f = sendtable.send_ref
                        f.writable = True
                        f.widget = lambda f, v: \
                            StringWidget.widget(f, v, _placeholder = T("Leave blank to have this autogenerated"))
                              
                    else:
                        sendtable.send_ref.readable = False
                else:
                    # Make all fields writable False
                    for field in sendtable.fields:
                        sendtable[field].writable = False
                    if settings.get_inv_send_req():
                        s3db.inv_send_req.req_id.writable = False

            if record:
                if status != SHIP_STATUS_IN_PROCESS:
                    # Now that the shipment has been sent,
                    # lock the record so that it can't be meddled with
                    if settings.get_inv_document_filing():
                        dtable = s3db.doc_document
                        filed = db(dtable.doc_id == record.doc_id).select(dtable.id,
                                                                          limitby = (0, 1),
                                                                          )
                        if filed:
                            # Still allow access to filing_status
                            set_send_attr(status)
                            sendtable.filing_status.writable = True
                            s3db.configure("inv_send",
                                           deletable = False,
                                           )
                        else:
                            s3db.configure("inv_send",
                                           deletable = False,
                                           editable = False,
                                           )
                    else:
                        s3db.configure("inv_send",
                                       deletable = False,
                                       editable = False,
                                       )
                    
                else:
                    set_send_attr(status)
            else:
                set_send_attr(SHIP_STATUS_IN_PROCESS)
                sendtable.send_ref.readable = False

            if settings.get_inv_recv_req() and \
               (r.method == "create" or \
                (r.method == "update" and record.status == SHIP_STATUS_IN_PROCESS)):
                # Filter Requests to those which are:
                # - Approved (or Open)
                # - Have Items Requested From our sites which are not yet in-Transit/Fulfilled
                sites = sendtable.site_id.requires.options(zero = False)
                site_ids = [site[0] for site in sites]
                rtable = s3db.inv_req
                ritable = s3db.inv_req_item
                if len(site_ids) > 1:
                    site_query = (ritable.site_id.belongs(site_ids))
                    if s3.debug:
                        s3.scripts.append("/%s/static/scripts/S3/s3.inv_send.js" % r.application)
                    else:
                        s3.scripts.append("/%s/static/scripts/S3/s3.inv_send.min.js" % r.application)
                else:
                    site_query = (ritable.site_id == site_ids[0])
                query = (rtable.id == ritable.req_id) & \
                        site_query & \
                        (ritable.quantity_transit < ritable.quantity)
                if settings.get_inv_req_workflow():
                    query = (rtable.workflow_status == 3) & query
                else:
                    query = (rtable.fulfil_status.belongs((REQ_STATUS_NONE, REQ_STATUS_PARTIAL))) & query
                f = s3db.inv_send_req.req_id
                f.requires = IS_ONE_OF(db(query), "inv_req.id",
                                       f.represent,
                                       sort = True,
                                       )

        return True

    s3.prep = prep

    return current.rest_controller("inv", "send",
                                   rheader = inv_send_rheader,
                                   )

# =============================================================================
def inv_send_onaccept(form):
    """
       When a inv send record is created
       - create the send_ref if not provided
       - add all inv items with the status of the shipment type
    """

    db = current.db

    form_vars = form.vars
    record_id = form_vars.id

    shipment_type = form_vars.type
    if shipment_type:
        shipment_type = int(shipment_type)
        if shipment_type:
            # Add all inv_items with status matching the send shipment type
            # eg. Items for Dump, Sale, Reject, Surplus
            site_id = form_vars.site_id
            itable = db.inv_inv_item
            tracktable = db.inv_track_item
            query = (itable.site_id == site_id) & \
                    (itable.status == shipment_type)
            rows = db(query).select()
            for row in rows:
                if row.quantity != 0:
                    # Insert inv_item to inv_track_item
                    inv_track_id = tracktable.insert(send_id = record_id,
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
                    form_vars = Storage(id = inv_track_id,
                                        quantity = row.quantity,
                                        item_pack_id = row.item_pack_id,
                                        send_inv_item_id = row.id,
                                        )
                    # Call inv_track_item_onaccept to remove inv_item from stock
                    inv_track_item_onaccept(Storage(vars = form_vars))

    # If the send_ref is None then set it up
    stable = db.inv_send
    record = db(stable.id == record_id).select(stable.id,
                                               stable.send_ref,
                                               stable.site_id,
                                               limitby = (0, 1),
                                               ).first()
    if not record.send_ref:
        from .supply import supply_get_shipping_code as get_shipping_code
        code = get_shipping_code(current.deployment_settings.get_inv_send_shortname(),
                                 record.site_id,
                                 stable.send_ref,
                                 )
        record.update_record(send_ref = code)

# =============================================================================
def inv_send_pallet_update(send_pallet_id):
    """
        Updfate a Shipment Pallet's Total Weight & Volume
    """

    db = current.db
    s3db = current.s3db

    table = s3db.inv_send_pallet_item
    itable = s3db.supply_item
    ptable = s3db.supply_item_pack
    ttable = s3db.inv_track_item
    query = (table.send_pallet_id == send_pallet_id) & \
            (table.track_item_id == ttable.id) & \
            (ttable.item_id == itable.id) & \
            (ttable.item_pack_id == ptable.id)
    items = db(query).select(itable.weight,
                             itable.volume,
                             ttable.quantity,
                             ptable.quantity,
                             )
    total_volume = 0
    total_weight = 0
    for row in items:
        quantity = row["inv_track_item.quantity"] * row["supply_item_pack.quantity"]
        row = row.supply_item
        volume = row.volume
        if volume:
            total_volume += (volume * quantity)
        weight = row.weight
        if weight:
            total_weight += (weight * quantity)

    db(s3db.inv_send_pallet.id == send_pallet_id).update(volume = total_volume,
                                                         weight = total_weight,
                                                         )

# =============================================================================
def inv_send_process(r, **attr):
    """
        Process a Shipment

        @ToDo: Avoid Writes in GETs
    """

    T = current.T

    send_id = r.id

    if not send_id:
        r.error(405, T("Can only process a single shipment."),
                next = URL(f = "send",
                           ),
                )

    auth = current.auth
    s3db = current.s3db
    stable = s3db.inv_send

    if not auth.s3_has_permission("update", stable,
                                  record_id = send_id):
        r.unauthorised()

    db = current.db

    send_record = db(stable.id == send_id).select(stable.status,
                                                  stable.sender_id,
                                                  stable.send_ref,
                                                  stable.req_ref,
                                                  stable.site_id,
                                                  stable.delivery_date,
                                                  stable.recipient_id,
                                                  stable.to_site_id,
                                                  stable.transport_type,
                                                  stable.comments,
                                                  limitby = (0, 1),
                                                  ).first()

    if send_record.status != SHIP_STATUS_IN_PROCESS:
        r.error(409, T("This shipment has already been sent."),
                next = URL(f = "send",
                           args = [send_id],
                           ),
                )

    settings = current.deployment_settings
    stock_cards = settings.get_inv_stock_cards()

    # Get the track items that are part of this shipment
    tracktable = db.inv_track_item
    track_fields = [tracktable.req_item_id,
                    tracktable.quantity,
                    tracktable.item_pack_id,
                    ]
    if stock_cards:
        track_fields.append(tracktable.send_inv_item_id)
    track_items = db(tracktable.send_id == send_id).select(*track_fields)
    if not track_items:
        r.error(409, T("No items have been selected for shipping."),
                next = URL(f = "send",
                           args = [send_id],
                           ),
                )

    # Update Send record & lock for editing
    #system_roles = auth.get_system_roles()
    #ADMIN = system_roles.ADMIN
    db(stable.id == send_id).update(date = r.utcnow,
                                    status = SHIP_STATUS_SENT,
                                    #owned_by_user = None,
                                    #owned_by_group = ADMIN,
                                    )

    # If this is linked to a Request then update the quantity in transit
    if settings.get_inv_send_req():
        srtable = s3db.inv_send_req
        reqs = db(srtable.send_id == send_id).select(srtable.req_id)
        if reqs:
            ritable = s3db.inv_req_item
            siptable = s3db.supply_item_pack
            query = (ritable.id.belongs([row.req_item_id for row in track_items])) & \
                    (ritable.item_pack_id == siptable.id)
            req_packs = db(query).select(ritable.id,
                                         siptable.quantity,
                                         )
            req_packs = {row["inv_req_item.id"]: row["supply_item_pack.quantity"] for row in req_packs}
            query = (siptable.id.belongs([row.item_pack_id for row in track_items]))
            track_packs = db(query).select(siptable.id,
                                           siptable.quantity,
                                           )
            track_packs = {row.id: row.quantity for row in track_packs}
            for track_item in track_items:
                req_item_id = track_item.req_item_id
                if req_item_id:
                    req_p_qnty = req_packs.get(req_item_id)
                    t_qnty = track_item.quantity
                    inv_p_qnty = track_packs.get(track_item.item_pack_id)
                    transit_quantity = t_qnty * inv_p_qnty / req_p_qnty
                    db(ritable.id == req_item_id).update(quantity_transit = ritable.quantity_transit + transit_quantity)

            for row in reqs:
                inv_req_update_status(row.req_id)

    # Create a Receive record
    rtable = s3db.inv_recv
    recv = {"sender_id": send_record.sender_id,
            "send_ref": send_record.send_ref,
            "req_ref": send_record.req_ref,
            "from_site_id": send_record.site_id,
            "eta": send_record.delivery_date,
            "recipient_id": send_record.recipient_id,
            "site_id": send_record.to_site_id,
            "transport_type": send_record.transport_type,
            "comments": send_record.comments,
            "status": SHIP_STATUS_SENT,
            "type": 1, # "Another Inventory"
            }
    recv_id = rtable.insert(**recv)
    recv["id"] = recv_id
    auth.set_realm_entity(rtable, recv_id)

    # Change the status for all track items in this shipment to 'In Transit'
    # and link to the receive record
    db(tracktable.send_id == send_id).update(status = TRACK_STATUS_TRANSIT, # 2
                                             recv_id = recv_id,
                                             )

    if settings.get_inv_warehouse_free_capacity_calculated():
        # Update the Warehouse Free capacity
        inv_warehouse_free_capacity(send_record.site_id)

    if stock_cards:
        inv_item_ids = [row.send_inv_item_id for row in track_items]
        inv_stock_card_update(inv_item_ids,
                              send_id = send_id,
                              comments = "Shipment Sent",
                              )

    # Call on_inv_send_process hook if-configured
    tablename = "inv_send"
    on_inv_send_process = s3db.get_config(tablename, "on_inv_send_process")
    if on_inv_send_process:
        send_record.id = send_id
        on_inv_send_process(send_record)

    current.session.confirmation = T("Shipment Items sent from Warehouse")
    redirect(URL(f = "send",
                 args = [send_id, "track_item"]
                 ))

# =============================================================================
def inv_send_received(r, **attr):
    """
        Confirm a Shipment has been Received

        @ToDo: Avoid Writes in GETs
    """

    T = current.T

    send_id = r.id

    if not send_id:
        r.error(405, T("Can only confirm a single shipment."),
                next = URL(f = "send",
                           ),
                )

    auth = current.auth
    s3db = current.s3db
    stable = s3db.inv_send

    if not auth.s3_has_permission("update", stable,
                                  record_id = send_id):
        r.unauthorised()

    db = current.db

    tracktable = s3db.inv_track_item

    db(stable.id == send_id).update(status = SHIP_STATUS_RECEIVED)
    db(tracktable.send_id == send_id).update(status = TRACK_STATUS_ARRIVED)

    if current.deployment_settings.get_inv_send_req():
        rtable = s3db.inv_req
        srtable = s3db.inv_send_req
        reqs = db(srtable.send_id == send_id).select(srtable.req_id)
        if reqs:
            req_ids = [row.req_id for row in reqs]
            # Get the full list of items in the request(s)
            ritable = s3db.inv_req_item
            for req_id in req_ids:
                query = (ritable.req_id == req_id)
                ritems = db(query).select(ritable.id,
                                          ritable.item_pack_id,
                                          ritable.quantity,
                                          # Virtual Field
                                          #ritable.pack_quantity,
                                          )
                # Get all Received Shipments in-system for this request
                query = (stable.status == SHIP_STATUS_RECEIVED) & \
                        (tracktable.send_id == send_id) & \
                        (stable.id == srtable.send_id) & \
                        (srtable.req_id == req_id)
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
                        db(ritable.id == item.id).update(quantity_fulfil = quantity_fulfil)
                        req_quantity = item.quantity * item.pack_quantity()
                        complete = quantity_fulfil >= req_quantity

                # Update overall Request Status
                if complete:
                    # REQ_STATUS_COMPLETE
                    db(rtable.id == req_id).update(fulfil_status = 2)
                else:
                    # REQ_STATUS_PARTIAL
                    db(rtable.id == req_id).update(fulfil_status = 1)

    current.session.confirmation = T("Shipment received")
    redirect(URL(c = "inv",
                 f = "send",
                 args = [send_id],
                 ))

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
            settings = current.deployment_settings

            tabs = [(T("Edit Details"), None),
                    (T("Items"), "track_item"),
                    ]
            if settings.get_inv_send_pallets():
                tabs.append((T("Pallets"), "send_pallet"))
            if settings.get_inv_document_filing():
                tabs.append((T("Documents"), "document"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table
            stable = s3db.org_site

            send_id = record.id
            status = record.status
            site_id = record.site_id
            if site_id:
                site = db(stable.site_id == site_id).select(stable.organisation_id,
                                                            stable.instance_type,
                                                            limitby = (0, 1),
                                                            ).first()
                org_id = site.organisation_id
                logo = s3db.org_organisation_logo(org_id) or ""
                instance_table = s3db[site.instance_type]
                if "phone1" in instance_table.fields:
                    site = db(instance_table.site_id == site_id).select(instance_table.phone1,
                                                                        instance_table.phone2,
                                                                        limitby = (0, 1),
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
                                                               limitby = (0, 1),
                                                               ).first()
                address = s3db.gis_LocationRepresent(address_only = True)(site.location_id)
            else:
                address = current.messages["NONE"]
            if settings.get_inv_send_req():
                req_ref_label = TH("%s: " % table.req_ref.label)
                ltable = s3db.inv_send_req
                rtable = s3db.inv_req
                query = (ltable.send_id == send_id) & \
                        (ltable.req_id == rtable.id)
                rows = db(query).select(rtable.id,
                                        rtable.req_ref,
                                        )
                if len(rows) == 1:
                    row = rows.first()
                    req_ref_value = TD(inv_ReqRefRepresent(show_link = True)(row.req_ref, row))
                else:
                    # Cache values in class
                    refs = [row.req_ref for row in rows]
                    represent = inv_ReqRefRepresent(show_link = True)
                    represent.bulk(refs, rows, show_link = True)
                    refs_repr = [s3_str(represent(ref)) for ref in refs]
                    refs_repr = ", ".join(refs_repr)
                    req_ref_value = TD(XML(refs_repr))
            elif settings.get_inv_send_req_ref():
                req_ref_label = TH("%s: " % table.req_ref.label)
                #req_ref_value = TD(inv_ReqRefRepresent(show_link = True)(record.req_ref))
                req_ref_value = TD(record.req_ref)
            else:
                req_ref_label = ""
                req_ref_value = ""
            shipment_details = TABLE(TR(TD(T(settings.get_inv_send_form_name().upper()),
                                           _colspan = 2,
                                           _class = "pdf_title",
                                           ),
                                        TD(logo,
                                           _colspan = 2,
                                           ),
                                        ),
                                     TR(TH("%s: " % table.status.label),
                                        table.status.represent(status),
                                        ),
                                     TR(TH("%s: " % table.send_ref.label),
                                        TD(table.send_ref.represent(record.send_ref)),
                                        req_ref_label,
                                        req_ref_value,
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
            cnt = db(query).select(tracktable.id,
                                   limitby = (0, 1),
                                   ).first()
            if cnt:
                cnt = 1
            else:
                cnt = 0

            actions = DIV()
            #rSubdata = TABLE()
            rfooter = TAG[""]()

            if not r.method == "form":
                if status == SHIP_STATUS_IN_PROCESS:
                    if current.auth.s3_has_permission("update", "inv_send",
                                                      record_id = record.id):

                        if cnt > 0:
                            actions.append(A(ICON("print"),
                                             " ",
                                             T("Picking List"),
                                             _href = URL(args = [record.id, "pick_list.xls"]
                                                         ),
                                             _class = "action-btn",
                                             )
                                           )

                            actions.append(A(T("Send Shipment"),
                                             _href = URL(args = [record.id, "process"]
                                                         ),
                                             _id = "send_process",
                                             _class = "action-btn",
                                             )
                                           )

                            s3.jquery_ready.append('''S3.confirmClick("#send_process","%s")''' \
                                                    % T("Do you want to send this shipment?"))
                        #if not r.component:
                        #    ritable = s3db.inv_req_item
                        #    rcitable = s3db.inv_commit_item
                        #    query = (tracktable.send_id == record.id) & \
                        #            (rcitable.req_item_id == tracktable.req_item_id) & \
                        #            (tracktable.req_item_id == ritable.id) & \
                        #            (tracktable.deleted == False)
                        #    records = db(query).select()
                        #    for record in records:
                        #        rSubdata.append(TR(TH("%s: " % ritable.item_id.label),
                        #                           ritable.item_id.represent(record.inv_req_item.item_id),
                        #                           TH("%s: " % rcitable.quantity.label),
                        #                           record.inv_commit_item.quantity,
                        #                           ))

                elif status == SHIP_STATUS_RETURNING:
                    if cnt > 0:
                        actions.append(A(T("Complete Returns"),
                                         _href = URL(c = "inv",
                                                     f = "return_process",
                                                     args = [record.id]
                                                     ),
                                         _id = "return_process",
                                         _class = "action-btn"
                                         )
                                       )
                        s3.jquery_ready.append('''S3.confirmClick("#return_process","%s")''' \
                                        % T("Do you want to complete the return process?"))
                    else:
                        msg = T("You need to check all item quantities before you can complete the return process.")
                        rfooter.append(SPAN(msg))
                elif status != SHIP_STATUS_CANCEL:
                    if status == SHIP_STATUS_SENT:
                        jappend = s3.jquery_ready.append
                        s3_has_permission = current.auth.s3_has_permission
                        if s3_has_permission("update", "inv_send",
                                             record_id = record.id):
                            actions.append(A(T("Manage Returns"),
                                             _href = URL(c = "inv",
                                                         f = "send_returns",
                                                         args = [record.id],
                                                         vars = None,
                                                         ),
                                             _id = "send-return",
                                             _class = "action-btn",
                                             _title = T("Only use this button to accept back into stock some items that were returned from a delivery.")
                                             )
                                           )
                            jappend('''S3.confirmClick("#send-return","%s")''' % \
                                T("Confirm that some items were returned from a delivery and they will be accepted back into stock."))

                            actions.append(A(T("Confirm Shipment Received"),
                                             _href = URL(f = "send",
                                                         args = [record.id,
                                                                 "received",
                                                                 ],
                                                         ),
                                             _id = "send-receive",
                                             _class = "action-btn",
                                             _title = T("Only use this button to confirm that the shipment has been received by a destination which will not record the shipment directly into the system.")
                                             )
                                           )
                            jappend('''S3.confirmClick("#send-receive","%s")''' % \
                                T("Confirm that the shipment has been received by a destination which will not record the shipment directly into the system."))

                        if s3_has_permission("update", "inv_send",
                                             record_id = record.id):
                            actions.append(A(T("Cancel Shipment"),
                                             _href = URL(c = "inv",
                                                         f = "send_cancel",
                                                         args = [record.id]
                                                         ),
                                             _id = "send-cancel",
                                             _class = "action-btn"
                                             )
                                           )

                            jappend('''S3.confirmClick("#send-cancel","%s")''' \
                                % T("Do you want to cancel this sent shipment? The items will be returned to the Warehouse. This action CANNOT be undone!"))

                if settings.get_inv_send_gift_certificate():
                    actions.append(A(ICON("print"),
                                     " ",
                                     T("Gift Certificate"),
                                     _href = URL(c = "inv",
                                                 f = "send",
                                                 args = [record.id,
                                                         "gift_certificate",
                                                         ]
                                                 ),
                                     _class = "action-btn"
                                     )
                                   )

            #    msg = ""
            #    if cnt == 1:
            #       msg = T("One item is attached to this shipment")
            #    elif cnt > 1:
            #        msg = T("%s items are attached to this shipment") % cnt
            #    shipment_details.append(TR(TH(actions, _colspan=2), TD(msg)))
                shipment_details.append(TR(TH(actions,
                                              _colspan = 2,
                                              )))

            s3.rfooter = rfooter
            rheader = DIV(shipment_details,
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
def inv_stock_movements(resource, selectors, orderby):
    """
        Extraction method for stock movements report

        @param resource: the S3Resource (inv_inv_item)
        @param selectors: the field selectors
        @param orderby: orderby expression

        @note: transactions can be filtered by earliest/latest date
               using an S3DateFilter with selector="_transaction.date"

        @todo: does not take manual stock adjustments into account
        @todo: does not represent sites or Waybill/GRN as
               links (breaks PDF export, but otherwise it's useful)
    """

    # Extract the stock item data
    if current.deployment_settings.get_inv_bin_site_layout():
        bin_field = "layout_id"
    else:
        bin_field = "bin"
    selectors = ["id",
                 "site_id",
                 "site_id$name",
                 "item_id$item_category_id",
                 bin_field,
                 "item_id$name",
                 "quantity",
                 ]

    data = resource.select(selectors,
                           limit = None,
                           orderby = orderby,
                           raw_data = True,
                           represent = True,
                           )

    # Get all stock item IDs
    inv_item_ids = [row["_row"]["inv_inv_item.id"] for row in data.rows]

    # Earliest and latest date of the report (read from filter)
    convert = S3TypeConverter.convert
    request = current.request

    get_vars_get = request.get_vars.get
    dtstr = get_vars_get("_transaction.date__ge")
    earliest = convert(datetime.datetime, dtstr) if dtstr else None
    dtstr = get_vars_get("_transaction.date__le")
    latest = convert(datetime.datetime, dtstr) if dtstr else request.utcnow

    def item_dict():
        """ Stock movement data per inventory item """

        return {# Quantity in/out between earliest and latest date
                "quantity_in": 0,
                "quantity_out": 0,
                # Quantity in/out after latest date
                "quantity_in_after": 0,
                "quantity_out_after": 0,
                # Origin/destination sites
                "sites": [],
                # GRN/Waybill numbers
                "documents": [],
                }

    # Dict to collect stock movement data
    movements = {}

    # Set of site IDs for bulk representation
    all_sites = set()

    s3db = current.s3db

    # Incoming shipments
    query = (FS("recv_inv_item_id").belongs(inv_item_ids))
    if earliest:
        query &= (FS("recv_id$date") >= earliest)
    incoming = s3db.resource("inv_track_item", filter=query)
    transactions = incoming.select(["recv_id$date",
                                    "recv_id$from_site_id",
                                    "recv_id$recv_ref",
                                    "recv_inv_item_id",
                                    "recv_quantity",
                                    ],
                                    limit = None,
                                    raw_data = True,
                                    represent = True,
                                    )
    for transaction in transactions.rows:
        raw = transaction["_row"]
        inv_item_id = raw["inv_track_item.recv_inv_item_id"]
        # Get the movement data dict for this item
        if inv_item_id in movements:
            item_data = movements[inv_item_id]
        else:
            movements[inv_item_id] = item_data = item_dict()
        # Incoming quantities
        quantity_in = raw["inv_track_item.recv_quantity"]
        if quantity_in:
            if raw["inv_recv.date"] > latest:
                item_data["quantity_in_after"] += quantity_in
                continue
            else:
                item_data["quantity_in"] += quantity_in
        # Origin sites
        sites = item_data["sites"]
        from_site = raw["inv_recv.from_site_id"]
        if from_site and from_site not in sites:
            all_sites.add(from_site)
            sites.append(from_site)
        # GRN numbers
        if raw["inv_recv.recv_ref"]:
            documents = item_data["documents"]
            documents.append(raw["inv_recv.recv_ref"])

    # Outgoing shipments
    query = (FS("send_inv_item_id").belongs(inv_item_ids))
    if earliest:
        query &= (FS("send_id$date") >= earliest)
    outgoing = s3db.resource("inv_track_item", filter=query)
    transactions = outgoing.select(["send_id$date",
                                    "send_id$to_site_id",
                                    "send_id$send_ref",
                                    "send_inv_item_id",
                                    "quantity",
                                    ],
                                    limit = None,
                                    raw_data = True,
                                    represent = True,
                                    )
    for transaction in transactions.rows:
        raw = transaction["_row"]
        inv_item_id = raw["inv_track_item.send_inv_item_id"]
        # Get the movement data dict for this item
        if inv_item_id in movements:
            item_data = movements[inv_item_id]
        else:
            movements[inv_item_id] = item_data = item_dict()
        # Outgoing quantities
        quantity_in = raw["inv_track_item.quantity"]
        if quantity_in:
            send_date = raw["inv_send.date"]
            if send_date and send_date > latest:
                item_data["quantity_out_after"] += quantity_in
                continue
            else:
                item_data["quantity_out"] += quantity_in
        # Destination sites
        sites = item_data["sites"]
        to_site = raw["inv_send.to_site_id"]
        if to_site and to_site not in sites:
            all_sites.add(to_site)
            sites.append(to_site)
        # Waybill numbers
        if raw["inv_send.send_ref"]:
            documents = item_data["documents"]
            documents.append(raw["inv_send.send_ref"])

    # Bulk-represent sites (stores the representations in represent)
    represent = s3db.inv_inv_item.site_id.represent
    represent.bulk(list(all_sites))

    # Extend the original rows in the data dict
    for row in data.rows:
        raw = row["_row"]

        inv_item_id = raw["inv_inv_item.id"]
        if inv_item_id in movements:
            item_data = movements[inv_item_id]
        else:
            item_data = item_dict()

        # Compute original and final quantity
        total_in = item_data["quantity_in"]
        total_out = item_data["quantity_out"]

        current_quantity = raw["inv_inv_item.quantity"]
        final_quantity = current_quantity - \
                         item_data["quantity_in_after"] + \
                         item_data["quantity_out_after"]
        original_quantity = final_quantity - total_in + total_out

        # Write into raw data (for aggregation)
        raw["inv_inv_item.quantity"] = final_quantity
        raw["inv_inv_item.quantity_in"] = total_in
        raw["inv_inv_item.quantity_out"] = total_out
        raw["inv_inv_item.original_quantity"] = original_quantity

        # Copy into represented data (for rendering)
        row["inv_inv_item.quantity"] = final_quantity
        row["inv_inv_item.quantity_in"] = total_in
        row["inv_inv_item.quantity_out"] = total_out
        row["inv_inv_item.original_quantity"] = original_quantity

        # Add sites
        row["inv_inv_item.sites"] = represent.multiple(item_data["sites"],
                                                        show_link = False,
                                                        )
        # Add GRN/Waybill numbers
        row["inv_inv_item.documents"] = ", ".join(item_data["documents"])

    # Return to S3GroupedItemsReport
    return data.rows

# =============================================================================
def inv_tabs(r):
    """
        Add an expandable set of Tabs for a Site's Inventory Tasks

        @ToDo: Make these Expand/Contract without a server-side call
    """

    settings = current.deployment_settings
    if settings.get_org_site_inv_req_tabs() and \
       current.auth.s3_has_permission("read", "inv_inv_item"):

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
            recv_label = settings.get_inv_recv_tab_label()
            send_label = settings.get_inv_send_tab_label()
            tabs = [(T("Stock"), "inv_item"),
                    #(T("Incoming"), "incoming/"),
                    (T(recv_label), "recv"),
                    (T(send_label), "send"),
                    ]
            if settings.get_inv_bin_site_layout():
                tabs.append((T("Bins"), "layout", {}, "hierarchy"))
            if settings.has_module("proc"):
                tabs.append((T("Planned Procurements"), "plan"))
            if settings.get_inv_minimums():
                tabs.append((T("Stock Minimums"), "minimum"))
            if show_collapse:
                tabs.append(("- %s" % T("Warehouse"), None, {"show_inv": "False"}))
        else:
            tabs = [("+ %s" % T("Warehouse"), "inv_item", {"show_inv": "True"}),
                    ]
        return tabs

    return []

# =============================================================================
def inv_track_item_quantity_needed(row):
    """
        Quantity still needed for a track item - used in Inv Send
        when an Item has come from a Request
    """

    if hasattr(row, "inv_track_item"):
        row = row.inv_track_item
    try:
        req_item_id = row.req_item_id
    except AttributeError:
        # not available
        req_item_id = None

    if not req_item_id:
        return current.messages["NONE"]

    s3db = current.s3db

    ritable = s3db.inv_req_item
    siptable = s3db.supply_item_pack

    query = (ritable.id == req_item_id) & \
            (ritable.item_pack_id == siptable.id)

    row = current.db(query).select(ritable.quantity,
                                   ritable.quantity_transit,
                                   ritable.quantity_fulfil,
                                   siptable.quantity
                                   ).first()

    if row:
        rim = row.inv_req_item

        quantity_shipped = max(rim.quantity_transit,
                               rim.quantity_fulfil)

        quantity_needed = (rim.quantity - quantity_shipped) * \
                           row.supply_item_pack.quantity
    else:
        return current.messages["NONE"]

    return quantity_needed

# =============================================================================
def inv_send_commit():
    """
        Controller function to create a Shipment containing all
        Items in a Commitment (interactive)

        @ToDo: Rewrite as Method
        @ToDo: Avoid Writes in GETs
    """

    # Get the commit record
    try:
        commit_id = current.request.args[0]
    except KeyError:
        redirect(URL(c="inv", f="commit"))

    db = current.db
    s3db = current.s3db

    req_table = db.inv_req
    rim_table = db.inv_req_item
    com_table = db.inv_commit
    cim_table = db.inv_commit_item

    send_table = s3db.inv_send
    tracktable = s3db.inv_track_item

    query = (com_table.id == commit_id) & \
            (com_table.req_id == req_table.id) & \
            (com_table.deleted == False)
    record = db(query).select(com_table.committer_id,
                              com_table.site_id,
                              com_table.organisation_id,
                              req_table.id,
                              req_table.requester_id,
                              req_table.site_id,
                              #req_table.req_ref, # Only used for External Requests
                              limitby = (0, 1),
                              ).first()

    # @ToDo: Identify if we have stock items which match the commit items
    # If we have a single match per item then proceed automatically (as-now) & then decrement the stock quantity
    # If we have no match then warn the user & ask if they should proceed anyway
    # If we have mulitple matches then provide a UI to allow the user to select which stock items to use

    # Create an inv_send and link to the commit
    form_vars = Storage(sender_id = record.inv_commit.committer_id,
                        site_id = record.inv_commit.site_id,
                        recipient_id = record.inv_req.requester_id,
                        to_site_id = record.inv_req.site_id,
                        #req_ref = record.inv_req.req_ref,
                        status = 0,
                        )
    send_id = send_table.insert(**form_vars)
    form_vars.id = send_id
    s3db.inv_send_req.insert(send_id = send_id,
                             req_id = record.inv_req.id,
                             )

    # Get all of the committed items
    query = (cim_table.commit_id == commit_id) & \
            (cim_table.req_item_id == rim_table.id) & \
            (cim_table.deleted == False)
    records = db(query).select(rim_table.id,
                               rim_table.item_id,
                               rim_table.item_pack_id,
                               rim_table.currency,
                               rim_table.quantity,
                               rim_table.quantity_transit,
                               rim_table.quantity_fulfil,
                               cim_table.quantity,
                               )
    # Create inv_track_items for each commit item
    insert = tracktable.insert
    for row in records:
        rim = row.inv_req_item
        # Now done as a VirtualField instead (looks better & updates closer to real-time, so less of a race condition)
        #quantity_shipped = max(rim.quantity_transit, rim.quantity_fulfil)
        #quantity_needed = rim.quantity - quantity_shipped
        insert(req_item_id = rim.id,
               track_org_id = record.inv_commit.organisation_id,
               send_id = send_id,
               status = 1,
               item_id = rim.item_id,
               item_pack_id = rim.item_pack_id,
               currency = rim.currency,
               #req_quantity = quantity_needed,
               quantity = row.inv_commit_item.quantity,
               recv_quantity = row.inv_commit_item.quantity,
               )

    # Create the Waybill
    form = Storage()
    form.vars = form_vars
    inv_send_onaccept(form)

    # Redirect to inv_send for the send id just created
    redirect(URL(c = "inv",
                 f = "send",
                 #args = [send_id, "track_item"]
                 args = [send_id]
                 ))

# =============================================================================
def inv_update_commit_quantities_and_status(req):
    """
        Update commit quantities and status of an Inventory Requisition

        @param req: the inv_req record (Row)
    """

    db = current.db
    s3db = current.s3db
    ctable = s3db.inv_commit

    req_id = req.id

    pack_quantities = s3db.supply_item_pack_quantities

    # Get all commits for this request
    citable = s3db.inv_commit_item
    query = (ctable.req_id == req_id) & \
            (citable.commit_id == ctable.id) & \
            (citable.deleted == False)
    citems = db(query).select(citable.item_pack_id,
                              citable.quantity,
                              )
    pqty = pack_quantities(item.item_pack_id for item in citems)

    # Determine committed quantities per pack type
    commit_qty = {}
    for item in citems:

        item_pack_id = item.item_pack_id
        committed_quantity = (item.quantity * pqty.get(item_pack_id, 1))

        if item_pack_id in commit_qty:
            commit_qty[item_pack_id] += committed_quantity
        else:
            commit_qty[item_pack_id] = committed_quantity

    ritable = s3db.inv_req_item
    query = (ritable.req_id == req_id) & \
            (ritable.deleted == False)
    if not any(qty for qty in commit_qty.values()):
        # Nothing has been committed for this request so far
        commit_status = REQ_STATUS_NONE
        db(query).update(quantity_commit = 0)
    else:
        # Get all requested items for this request
        ritems = db(query).select(ritable.id,
                                  ritable.item_pack_id,
                                  ritable.quantity,
                                  ritable.quantity_commit,
                                  )

        pack_ids = (item.item_pack_id for item in ritems
                                      if item.item_pack_id not in pqty)
        pqty.update(pack_quantities(pack_ids))

        # Assume complete unless we find a gap
        commit_status = REQ_STATUS_COMPLETE

        # Update committed quantity for each requested item (if changed),
        # and check if there is still a commit-gap
        for item in ritems:

            committed_quantity = commit_qty.get(item.item_pack_id) or 0
            requested_quantity = item.quantity * pqty.get(item_pack_id, 1)

            if committed_quantity != item.quantity_commit:
                # Update it
                item.update_record(quantity_commit=committed_quantity)

            if committed_quantity < requested_quantity:
                # Gap!
                commit_status = REQ_STATUS_PARTIAL

    # Update commit-status of the request (if changed)
    if commit_status != req.commit_status:
        req.update_record(commit_status = commit_status)

# =============================================================================
def inv_stock_card_update(inv_item_ids,
                          send_id = None,
                          recv_id = None,
                          comments = None,
                          ):
    """
        Create/Update the Stock Card
    """

    db = current.db
    s3db = current.s3db

    iitable = s3db.inv_inv_item

    len_ids = len(inv_item_ids)
    if len_ids == 1:
        query = (iitable.id == inv_item_ids[0])
        limitby = (0, 1)
    else:
        query = (iitable.id.belongs(inv_item_ids))
        limitby = (0, len_ids)

    records = db(query).select(iitable.id,
                               iitable.site_id,
                               iitable.item_id,
                               iitable.item_source_no,
                               iitable.expiry_date,
                               iitable.item_pack_id,
                               iitable.quantity,
                               iitable.bin,
                               iitable.layout_id,
                               limitby = limitby,
                               )

    siptable = s3db.supply_item_pack
    sctable = s3db.inv_stock_card
    sltable = s3db.inv_stock_log

    for record in records:
        site_id = record.site_id
        item_id = record.item_id
        item_source_no = record.item_source_no
        expiry_date = record.expiry_date

        # Lookup Item Packs
        card_pack_id = None
        packs = db(siptable.item_id == item_id).select(siptable.id,
                                                       siptable.quantity,
                                                       )
        for row in packs:
            if row.quantity == 1:
                card_pack_id = row.id
                break
        packs = {row.id: row.quantity for row in packs}

        quantity = record.quantity * packs[record.item_pack_id]

        # Read all matching inv_items
        query = (iitable.site_id == site_id) & \
                (iitable.item_id == item_id) & \
                (iitable.item_source_no == item_source_no) & \
                (iitable.expiry_date == expiry_date) & \
                (iitable.id != record.id)
        matches = db(query).select(iitable.quantity,
                                   iitable.item_pack_id,
                                   )
        for row in matches:
            quantity += (row.quantity * packs[row.item_pack_id])

        # Search for existing Stock Card
        query = (sctable.site_id == site_id) & \
                (sctable.item_id == item_id) & \
                (sctable.item_source_no == item_source_no) & \
                (sctable.expiry_date == expiry_date)

        exists = db(query).select(sctable.id,
                                  limitby = (0, 1),
                                  ).first()
        if exists:
            card_id = exists.id

            # Lookup Latest Log Entry
            log = db(sltable.card_id == card_id).select(sltable.date,
                                                        sltable.balance,
                                                        orderby = ~sltable.date,
                                                        limitby = (0, 1),
                                                        ).first()
            if not log:
                quantity_in = quantity
                quantity_out = 0
            else:
                old_balance = log.balance
                if quantity > old_balance:
                    quantity_in = quantity - old_balance
                    quantity_out = 0
                elif quantity < old_balance:
                    quantity_in = 0
                    quantity_out = old_balance - quantity
                else:
                    # quantity == balance some other change
                    quantity_in = 0
                    quantity_out = 0
        else:
            card_id = sctable.insert(site_id = site_id,
                                     item_id = item_id,
                                     item_pack_id = card_pack_id,
                                     item_source_no = item_source_no,
                                     expiry_date = expiry_date,
                                     )
            onaccept = s3db.get_config("inv_stock_card", "create_onaccept")
            if onaccept:
                onaccept(Storage(vars = Storage(id = card_id,
                                                site_id = site_id,
                                                )
                                 ))
            quantity_in = quantity
            quantity_out = 0

        balance = quantity

        # Add Log Entry
        sltable.insert(card_id = card_id,
                       date = current.request.utcnow,
                       send_id = send_id,
                       recv_id = recv_id,
                       bin = record.bin,
                       layout_id = record.layout_id,
                       quantity_in = quantity_in,
                       quantity_out = quantity_out,
                       balance = balance,
                       comments = comments,
                       )

# =============================================================================
def inv_track_item_deleting(record_id):
    """
       A track item can only be deleted if the status is Preparing
       When a track item record is deleted and it is linked to an inv_item
       then the inv_item quantity will be adjusted.
    """

    db = current.db
    s3db = current.s3db
    tracktable = db.inv_track_item
    record = db(tracktable.id == record_id).select(tracktable.status,
                                                   tracktable.req_item_id,
                                                   tracktable.item_pack_id,
                                                   tracktable.quantity,
                                                   tracktable.send_inv_item_id,
                                                   limitby = (0, 1),
                                                   ).first()
    if record.status != 1:
        # Not 'Preparing': Do not allow
        return False

    if record.req_item_id:
        # This is linked to a Request:
        # - remove these items from the quantity in transit
        req_id = record.req_item_id
        ritable = s3db.inv_req_item
        req_item = db(ritable.id == req_id).select(ritable.id,
                                                   ritable.quantity_transit,
                                                   ritable.item_pack_id,
                                                   limitby = (0, 1),
                                                   ).first()
        req_quantity = req_item.quantity_transit
        siptable = db.supply_item_pack
        req_pack_quantity = db(siptable.id == req_item.item_pack_id).select(siptable.quantity,
                                                                            limitby = (0, 1),
                                                                            ).first().quantity
        track_pack_quantity = db(siptable.id == record.item_pack_id).select(siptable.quantity,
                                                                            limitby = (0, 1),
                                                                            ).first().quantity
        from .supply import supply_item_add
        quantity_transit = supply_item_add(req_quantity,
                                           req_pack_quantity,
                                           - record.quantity,
                                           track_pack_quantity
                                           )
        req_item.update_record(quantity_transit = quantity_transit)
        inv_req_update_status(req_id)

    if record.send_inv_item_id:
        # This is linked to a Warehouse Inventory item:
        # - remove the total from this record and place it back in the warehouse
        track_total = record.quantity
        inv_item_table = db.inv_inv_item
        db(inv_item_table.id == record.send_inv_item_id).update(quantity = inv_item_table.quantity + track_total)
        db(tracktable.id == record_id).update(quantity = 0,
                                              comments = "%sQuantity was: %s" % \
                                                            (tracktable.comments,
                                                             track_total,
                                                             ),
                                              )
    return True

# =============================================================================
def inv_track_item_onaccept(form):
    """
       When a track item record is created
       - if it is linked to an inv_item then that quantity will be updated
       - if it is linked to a req_item then that status will be updated
    """

    from .supply import supply_item_add

    db = current.db
    s3db = current.s3db

    tracktable = db.inv_track_item
    inv_item_table = db.inv_inv_item
    stable = db.inv_send
    rtable = db.inv_recv
    siptable = db.supply_item_pack

    form_vars = form.vars       # Used by Interactive forms & inv_send_onaccept
    form_vars_get = form.vars.get
    record_id = form_vars.id    # This is all that inv_recv_process has in form_vars
    record = form.record        # This is where inv_recv_process puts data, as well as record updates (empty for inv_send_onaccept)

    send_inv_item_id = form_vars_get("send_inv_item_id")
    if send_inv_item_id:
        stock_item = db(inv_item_table.id == send_inv_item_id).select(inv_item_table.id,
                                                                      inv_item_table.quantity,
                                                                      inv_item_table.item_pack_id,
                                                                      inv_item_table.source_type,
                                                                      limitby = (0, 1),
                                                                      ).first()
    elif record:
        stock_item = db(inv_item_table.id == record.send_inv_item_id).select(inv_item_table.id,
                                                                             inv_item_table.quantity,
                                                                             inv_item_table.item_pack_id,
                                                                             inv_item_table.source_type,
                                                                             limitby = (0, 1),
                                                                             ).first()
    else:
        # will get here for a recv from external donor / local supplier
        stock_item = None

    # Modify the original inv_item total only if we have a quantity on the form
    # and a stock item to take it from.
    # There will not be a quantity if it is being received since by then it is read only
    # It will be there on an import and so the value will be deducted correctly
    if form_vars.quantity and stock_item:
        stock_quantity = stock_item.quantity
        stock_pack = db(siptable.id == stock_item.item_pack_id).select(siptable.quantity,
                                                                       limitby = (0, 1),
                                                                       ).first().quantity
        if record:
            if record.send_inv_item_id != None:
                # Items have already been removed from stock, so first put them back
                old_track_pack_quantity = db(siptable.id == record.item_pack_id).select(siptable.quantity,
                                                                                        limitby = (0, 1),
                                                                                        ).first().quantity
                stock_quantity = supply_item_add(stock_quantity,
                                                 stock_pack,
                                                 record.quantity,
                                                 old_track_pack_quantity
                                                 )
        new_track_pack_quantity = db(siptable.id == form_vars.item_pack_id).select(siptable.quantity,
                                                                                   limitby = (0, 1),
                                                                                   ).first().quantity
        new_total = supply_item_add(stock_quantity,
                                    stock_pack,
                                    - float(form_vars.quantity),
                                    new_track_pack_quantity
                                    )
        db(inv_item_table.id == stock_item.id).update(quantity = new_total)

    send_id = form_vars_get("send_id")
    recv_id = form_vars_get("recv_id")
    if send_id and recv_id:
        send_ref = db(stable.id == send_id).select(stable.send_ref,
                                                   limitby = (0, 1),
                                                   ).first().send_ref
        db(rtable.id == recv_id).update(send_ref = send_ref)

    if record:
        settings = current.deployment_settings

        # Check if this item is linked to a Request
        req_item_id = record.req_item_id
        if req_item_id:
            rrtable = s3db.inv_req
            ritable = s3db.inv_req_item
            req_id = db(ritable.id == req_item_id).select(ritable.req_id,
                                                          limitby = (0, 1),
                                                          ).first().req_id

        # If the status is 'unloading':
        # Move all the items into the site, update any request & make any adjustments
        # Finally change the status to 'arrived'
        if record.status == TRACK_STATUS_UNLOADING and \
           record.recv_quantity:

            recv_id = record.recv_id
            # Look for the item in the site already
            recv_rec = db(rtable.id == recv_id).select(rtable.site_id,
                                                       rtable.type,
                                                       limitby = (0, 1),
                                                       ).first()
            recv_site_id = recv_rec.site_id
            if settings.get_inv_bin_site_layout():
                bin_query = (inv_item_table.layout_id == record.recv_bin_id)
            else:
                bin_query = (inv_item_table.bin == record.recv_bin)
            query = (inv_item_table.site_id == recv_site_id) & \
                    (inv_item_table.item_id == record.item_id) & \
                    (inv_item_table.item_pack_id == record.item_pack_id) & \
                    (inv_item_table.currency == record.currency) & \
                    (inv_item_table.status == record.inv_item_status) & \
                    (inv_item_table.pack_value == record.pack_value) & \
                    (inv_item_table.expiry_date == record.expiry_date) & \
                    bin_query & \
                    (inv_item_table.owner_org_id == record.owner_org_id) & \
                    (inv_item_table.item_source_no == record.item_source_no) & \
                    (inv_item_table.status == record.inv_item_status) & \
                    (inv_item_table.supply_org_id == record.supply_org_id)
            inv_item_row = db(query).select(inv_item_table.id,
                                            limitby = (0, 1),
                                            ).first()
            if inv_item_row:
                # Update the existing item
                inv_item_id = inv_item_row.id
                db(inv_item_table.id == inv_item_id).update(quantity = inv_item_table.quantity + record.recv_quantity)
            else:
                # Add a new item
                source_type = 0
                if send_inv_item_id:
                    source_type = stock_item.source_type
                else:
                    if recv_rec.type == 2:
                        source_type = 1 # Donation
                    else:
                        source_type = 2 # Procured
                inv_item = {"site_id": recv_site_id,
                            "item_id": record.item_id,
                            "item_pack_id": record.item_pack_id,
                            "currency": record.currency,
                            "pack_value": record.pack_value,
                            "expiry_date": record.expiry_date,
                            "bin": record.recv_bin,
                            "layout_id": record.recv_bin_id,
                            "owner_org_id": record.owner_org_id,
                            "supply_org_id": record.supply_org_id,
                            "quantity": record.recv_quantity,
                            "item_source_no": record.item_source_no,
                            "source_type": source_type,
                            "status": record.inv_item_status,
                            }
                inv_item_id = inv_item_table.insert(**inv_item)
                inv_item["id"] = inv_item_id
                realm_entity = current.auth.get_realm_entity(inv_item_table, inv_item)
                db(inv_item_table.id == inv_item_id).update(realm_entity = realm_entity)

            # If this item is linked to a Request, then update the quantity fulfil
            if req_item_id:
                req_item = db(ritable.id == req_item_id).select(ritable.id,
                                                                ritable.quantity_fulfil,
                                                                ritable.item_pack_id,
                                                                limitby = (0, 1),
                                                                ).first()
                req_quantity = req_item.quantity_fulfil
                req_pack_quantity = db(siptable.id == req_item.item_pack_id).select(siptable.quantity,
                                                                                    limitby = (0, 1),
                                                                                    ).first().quantity
                track_pack_quantity = db(siptable.id == record.item_pack_id).select(siptable.quantity,
                                                                                    limitby = (0, 1),
                                                                                    ).first().quantity
                quantity_fulfil = supply_item_add(req_quantity,
                                                  req_pack_quantity,
                                                  record.recv_quantity,
                                                  track_pack_quantity
                                                  )
                req_item.update_record(quantity_fulfil = quantity_fulfil)
                inv_req_update_status(req_id)

            data = {"recv_inv_item_id": inv_item_id,
                    "status": TRACK_STATUS_ARRIVED,
                    }

            # If the receive quantity doesn't equal the sent quantity
            # then an adjustment needs to be set up
            if record.quantity != record.recv_quantity:
                # Do we have an adjustment record?
                # (which might have be created for another item in this shipment)
                query = (tracktable.recv_id == recv_id) & \
                        (tracktable.adj_item_id != None)
                adj_rec = db(query).select(tracktable.adj_item_id,
                                           limitby = (0, 1),
                                           ).first()
                adjitemtable = s3db.inv_adj_item
                if adj_rec:
                    adj_id = db(adjitemtable.id == adj_rec.adj_item_id).select(adjitemtable.adj_id,
                                                                               limitby = (0, 1),
                                                                               ).first().adj_id
                # If we don't yet have an adj record then create it
                else:
                    adjtable = s3db.inv_adj
                    irtable = s3db.inv_recv
                    recv_rec = db(irtable.id == recv_id).select(irtable.recipient_id,
                                                                irtable.site_id,
                                                                irtable.comments,
                                                                limitby = (0, 1),
                                                                ).first()
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
                                                  layout_id = record.recv_bin_id,
                                                  comments = record.comments,
                                                  )
                # Copy the adj_item_id to the tracking record
                data["adj_item_id"] = adj_item_id

            db(tracktable.id == record_id).update(**data)

# =============================================================================
def inv_warehouse_free_capacity(site_id):
    """
        Update the Warehouse Free Capacity
    """

    db = current.db
    s3db = current.s3db
    table = s3db.inv_warehouse

    warehouse = db(table.site_id == site_id).select(table.id,      # For update_record
                                                    table.site_id, # For on_free_capacity_update hook
                                                    table.capacity,
                                                    table.name,    # For on_free_capacity_update hook
                                                    limitby = (0, 1),
                                                    ).first()
    if not warehouse or not warehouse.capacity:
        # Not a Warehouse, or Capacity not defined
        return

    table = s3db.inv_inv_item
    itable = s3db.supply_item
    ptable = s3db.supply_item_pack
    query = (table.site_id == site_id) & \
            (table.deleted == False) & \
            (table.quantity != 0) & \
            (table.item_id == itable.id) & \
            (itable.volume != None) & \
            (table.item_pack_id == ptable.id)

    items = db(query).select(table.quantity,
                             itable.volume,
                             ptable.quantity,
                             )
    used_capacity = 0
    for row in items:
        volume = row["inv_inv_item.quantity"] * row["supply_item.volume"] * row["supply_item_pack.quantity"]
        used_capacity += volume

    free_capacity = round(warehouse.capacity - used_capacity, 1)

    warehouse.update_record(free_capacity = free_capacity)

    # Hook to be configured in templates
    # e.g. Generate Alert if e.g. free_capacity < 10% of capacity

    # Customise the resource, to be sure that any hook is actually configured
    tablename = "inv_warehouse"
    customise = current.deployment_settings.customise_resource(tablename)
    if customise:
        r = S3Request("inv", "warehouse", args=[], vars={})
        customise(r, tablename)
    on_free_capacity_update = s3db.get_config(tablename, "on_free_capacity_update")
    if on_free_capacity_update:
        on_free_capacity_update(warehouse)

    # In case it's useful to CLI scripts
    return free_capacity

# =============================================================================
class inv_ReqCheckMethod(S3Method):
    """
        Check to see if you can match an Inventory Requisition
        - from the Inventory Items in your Site
    """

    def apply_method(self, r, **attr):
        """
            Apply method.

            @param r: the S3Request
            @param attr: controller options for this request
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        response = current.response
        s3 = response.s3

        output = {"title": T("Check Request"),
                  "rheader": req_rheader(r, check_page=True),
                  "subtitle": T("Requested Items"),
                  }

        # Read req_items
        table = s3db.inv_req_item
        query = (table.req_id == r.id ) & \
                (table.deleted == False )
        req_items = db(query).select(table.id,
                                     table.item_id,
                                     table.quantity,
                                     table.item_pack_id,
                                     table.quantity_commit,
                                     table.quantity_transit,
                                     table.quantity_fulfil,
                                     )

        if len(req_items):
            site_id = r.get_vars.get("site_id") or current.auth.user.site_id

            if site_id:
                site_name = s3db.org_site_represent(site_id, show_link=False)
                qty_in_label = s3_str(T("Quantity in %s")) % site_name
            else:
                qty_in_label = T("Quantity Available")

            # Build the Output Representation
            row = TR(TH(table.item_id.label),
                     TH(table.quantity.label),
                     TH(table.item_pack_id.label),
                     #TH(table.quantity_transit.label),
                     #TH(table.quantity_fulfil.label),
                     TH(T("Quantity Oustanding")),
                     TH(qty_in_label),
                     TH(T("Match?"))
                     )
            #use_commit = current.deployment_settings.get_inv_use_commit()
            #if use_commit:
            #    row.insert(3, TH(table.quantity_commit.label))
            items = TABLE(THEAD(row),
                          _id = "list",
                          _class = "dataTable display",
                          )
            if site_id:
                stable = s3db.org_site
                ltable = s3db.gis_location
                query = (stable.id == site_id) & \
                        (stable.location_id == ltable.id)
                location_r = db(query).select(ltable.lat,
                                              ltable.lon,
                                              limitby = (0, 1),
                                              ).first()
                query = (stable.id == r.record.site_id ) & \
                        (stable.location_id == ltable.id)
                req_location_r = db(query).select(ltable.lat,
                                                  ltable.lon,
                                                  limitby = (0, 1),
                                                  ).first()

                try:
                    distance = current.gis.greatCircleDistance(location_r.lat,
                                                               location_r.lon,
                                                               req_location_r.lat,
                                                               req_location_r.lon)
                    output["rheader"][0].append(TR(TH(s3_str(T("Distance from %s:")) % site_name,
                                                      ),
                                                   TD(T("%.1f km") % distance)
                                                   ))
                except:
                    pass

                if len(req_items):
                    # Get inv_items from this site which haven't expired and are in good condition
                    iitable = s3db.inv_inv_item
                    query = (iitable.site_id == site_id) & \
                            (iitable.deleted == False) & \
                            ((iitable.expiry_date >= r.now) | ((iitable.expiry_date == None))) & \
                            (iitable.status == 0)
                    inv_items_dict = {}
                    inv_items = db(query).select(iitable.item_id,
                                                 iitable.quantity,
                                                 iitable.item_pack_id,
                                                 # VF
                                                 #iitable.pack_quantity,
                                                 )
                    for item in inv_items:
                        item_id = item.item_id
                        if item_id in inv_items_dict:
                            inv_items_dict[item_id] += item.quantity * item.pack_quantity()
                        else:
                            inv_items_dict[item_id] = item.quantity * item.pack_quantity()

                    supply_item_represent = table.item_id.represent
                    item_pack_represent = table.item_pack_id.represent
                    no_match = True
                    for req_item in req_items:
                        req_quantity = req_item.quantity
                        # Do we have any outstanding quantity?
                        quantity_outstanding = req_quantity - max(req_item.quantity_fulfil, req_item.quantity_transit)
                        if quantity_outstanding:
                            # Convert Packs inv item quantity to req item quantity
                            item_id = req_item.item_id
                            if item_id in inv_items_dict:
                                inv_quantity = inv_items_dict[item_id] / req_item.pack_quantity()
                            else:
                                inv_quantity = 0

                            if inv_quantity != 0:
                                no_match = False
                                if inv_quantity < req_quantity:
                                    status = SPAN(T("Partial"),
                                                  _class = "req_status_partial",
                                                  )
                                else:
                                    status = SPAN(T("YES"),
                                                  _class = "req_status_complete",
                                                  )
                            else:
                                status = SPAN(T("NO"),
                                              _class = "req_status_none",
                                              )
                        else:
                            inv_quantity = T("N/A")
                            status = SPAN(T("N/A"),
                                          _class = "req_status_none",
                                          )

                        items.append(TR(#A(req_item.id),
                                        supply_item_represent(req_item.item_id),
                                        req_quantity,
                                        item_pack_represent(req_item.item_pack_id),
                                        # This requires an action btn to get the req_id
                                        #req_item.quantity_commit, # if use_commit
                                        #req_item.quantity_transit,
                                        #req_item.quantity_fulfil,
                                        #req_item_quantity_represent(req_item.quantity_commit, "commit"), # if use_commit
                                        #req_item_quantity_represent(req_item.quantity_fulfil, "fulfil"),
                                        #req_item_quantity_represent(req_item.quantity_transit, "transit"),
                                        quantity_outstanding,
                                        inv_quantity,
                                        status,
                                        )
                                     )

                    #s3.actions = [req_item_inv_item_btn]
                    if no_match:
                        response.warning = s3_str(T("%(site_name)s has no items exactly matching this request. Use Alternative Items if wishing to use other items to fulfill this request!") %
                                                  {"site_name": site_name})
                    else:
                        commit_btn = A(s3_str(T("Send from %s")) % site_name,
                                       _href = URL(c = "inv",
                                                   f = "send_req",
                                                   args = [r.id],
                                                   vars = {"site_id": site_id}
                                                   ),
                                       _class = "action-btn"
                                       )
                        s3.rfooter = TAG[""](commit_btn)

            else:
                response.error = T("User has no Site to check against!")

            output["items"] = items
            s3.no_sspag = True # pag won't work
            s3.no_formats = True

        else:
            output["items"] = s3.crud_strings.inv_req_item.msg_list_empty

        response.view = "list.html"

        return output

# =============================================================================
def inv_expiry_date_represent(date):
    """
        Show Expired Dates in Red
    """

    dtstr = S3DateTime.date_represent(date, utc=True)

    if date and datetime.datetime(date.year, date.month, date.day) < current.request.now:
        return SPAN(dtstr, _class="expired")
    else:
        return dtstr

# =============================================================================
class inv_AdjRepresent(S3Represent):
    """
        Represent an Inventory Adjustment
    """

    def __init__(self,
                 show_link = True,
                 field_sep = " - ",
                 **attr
                 ):

        super(inv_AdjRepresent, self).__init__(lookup = "inv_adj",
                                               fields = ["adjuster_id",
                                                         "adjustment_date",
                                                         ],
                                               show_link = show_link,
                                               field_sep = field_sep,
                                               **attr
                                               )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: never used for custom fns (retained for API compatibility)
        """

        fields = self.fields
        fields.append(key)

        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(*fields)
        self.queries += 1

        table = current.db.inv_adj

        # Bulk-represent adjuster_ids
        adjuster_ids = [row.adjuster_id for row in rows]
        if adjuster_ids:
            # Results cached in the represent class
            table.adjuster_id.represent.bulk(adjuster_ids)

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent the referenced row.
            (in foreign key representations)

            @param row: the row

            @return: the representation of the Row, or None if there
                     is an error in the Row
        """

        table = current.s3db.inv_adj

        v = self.field_sep.join((table.adjuster_id.represent(row.adjuster_id),
                                 table.adjustment_date.represent(row.adjustment_date),
                                 ))
        return v

# =============================================================================
class inv_AdjItemRepresent(S3Represent):
    """
        Represent an Inventory Adjustment Item
    """

    def __init__(self,
                 show_link = False,
                 **attr
                 ):

        super(inv_AdjItemRepresent, self).__init__(lookup = "inv_adj_item",
                                                   fields = ["item_id",
                                                             "old_quantity",
                                                             "new_quantity",
                                                             "item_pack_id",
                                                             ],
                                                   show_link = show_link,
                                                   **attr
                                                   )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: never used for custom fns (retained for API compatibility)
        """

        fields = self.fields
        fields.append(key)

        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(*fields)
        self.queries += 1

        table = current.db.inv_adj_item

        # Bulk-represent item_ids
        item_ids = [row.item_id for row in rows]
        if item_ids:
            # Results cached in the represent class
            table.item_id.represent.bulk(item_ids)

        # Bulk-represent item_pack_ids
        item_pack_ids = [row.item_pack_id for row in rows]
        if item_pack_ids:
            # Results cached in the represent class
            table.item_pack_id.represent.bulk(item_pack_ids)

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent the referenced row.
            (in foreign key representations)

            @param row: the row

            @return: the representation of the Row, or None if there
                     is an error in the Row
        """

        table = current.s3db.inv_adj_item

        if row.new_quantity and row.old_quantity:
            changed_quantity = row.new_quantity - row.old_quantity
        else:
            changed_quantity = 0

        v = "%s:%s %s" % (table.item_id.represent(row.item_id),
                          changed_quantity,
                          table.item_pack_id.represent(row.item_pack_id),
                          )
        return v

# =============================================================================
class inv_CommitRepresent(S3Represent):
    """
        Represent a Commit
    """

    def __init__(self):
        """
            Constructor
        """

        super(inv_CommitRepresent, self).__init__(lookup = "inv_commit",
                                                  )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom look-up of rows

            @param key: the key field
            @param values: the values to look up
            @param fields: unused (retained for API compatibility)
        """

        table = self.table

        count = len(values)
        if count == 1:
            query = (table.id == values[0])
        else:
            query = (table.id.belongs(values))

        rows = current.db(query).select(table.id,
                                        table.date,
                                        table.site_id,
                                        limitby = (0, count),
                                        )
        self.queries += 1

        # Collect site_ids
        site_ids = set()
        for row in rows:
            site_ids.add(row.site_id)

        # Bulk-represent site_ids
        if site_ids:
            represent = table.site_id.represent
            if represent and hasattr(represent, "bulk"):
                represent.bulk(list(site_ids))

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        table = self.table

        # Represent the committer (site)
        committer = table.site_id.represent(row.site_id)

        # Represent the commit date
        if row.date:
            daterepr = table.date.represent(row.date)
        else:
            daterepr = T("undated")

        # Combine committer/date as available
        if committer:
            if isinstance(committer, DIV):
                reprstr = TAG[""](committer, " - ", daterepr)
            else:
                reprstr = "%s - %s" % (committer, daterepr)
        else:
            reprstr = daterepr

        return reprstr

# =============================================================================
class inv_InvItemRepresent(S3Represent):
    """
        Represent an Inventory Item
    """

    def __init__(self):

        self.bin_site_layout = current.deployment_settings.get_inv_bin_site_layout()

        super(inv_InvItemRepresent, self).__init__(lookup = "inv_inv_item")

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: never used for custom fns (retained for API compatibility)
        """

        s3db = current.s3db

        itable = s3db.inv_inv_item
        stable = s3db.supply_item

        bin_site_layout = self.bin_site_layout
        if bin_site_layout:
            bin_field = itable.layout_id
        else:
            bin_field = itable.bin

        left = stable.on(stable.id == itable.item_id)
        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(itable.id,
                                        stable.name,
                                        stable.um,
                                        itable.item_source_no,
                                        bin_field,
                                        itable.expiry_date,
                                        itable.owner_org_id,
                                        left = left
                                        )

        self.queries += 1

        # Bulk-represent owner_org_ids
        organisation_id = str(itable.owner_org_id)
        organisation_ids = [row[organisation_id] for row in rows]
        if organisation_ids:
            # Results cached in the represent class
            itable.owner_org_id.represent.bulk(organisation_ids)

        if bin_site_layout:
            # Bulk-represent layout_ids
            layout_id = str(itable.layout_id)
            layout_ids = [row[layout_id] for row in rows]
            if layout_ids:
                # Results cached in the represent class
                itable.layout_id.represent.bulk(layout_ids)

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
        if self.bin_site_layout:
            item_bin = itable.layout_id.represent(iitem.layout_id)
        else:
            item_bin = stringify(iitem.bin)

        expires = iitem.expiry_date
        if expires:
            expires = "expires: %s" % \
                      S3DateTime.date_represent(expires, utc=True)
        else:
            expires = ""

        NONE = current.messages["NONE"]

        items = []
        append = items.append
        for string in [sitem.name, expires, ctn, org, item_bin]:
            if string and string != NONE:
                append(string)
                append(" - ")
        return TAG[""](items[:-1])

# =============================================================================
class inv_RecvRepresent(S3Represent):
    """
        Represent a Received Shipment
    """

    def __init__(self,
                 show_link = False,
                 show_from = False,
                 show_date = False,
                 ):

        fields = ["recv_ref",
                  ]
        if show_from:
            fields += ["from_site_id",
                       "organisation_id",
                       ]
        if show_date:
            fields.append("date")

        self.show_from = show_from
        self.show_date = show_date

        super(inv_RecvRepresent, self).__init__(lookup = "inv_recv",
                                                fields = fields,
                                                show_link = show_link,
                                                )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: never used for custom fns (retained for API compatibility)
        """

        fields = self.fields
        fields.append(key)

        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(*fields)
        self.queries += 1

        if self.show_from:
            table = current.db.inv_recv

            # Bulk-represent site_ids
            site_ids = [row.from_site_id for row in rows]
            if site_ids:
                # Results cached in the represent class
                table.from_site_id.represent.bulk(site_ids, show_link = False)

            # Bulk-represent organisation_ids
            organisation_ids = [row.organisation_id for row in rows]
            if organisation_ids:
                # Results cached in the represent class
                table.organisation_id.represent.bulk(organisation_ids, show_link = False)

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        v = row.recv_ref

        show_from = self.show_from
        show_date = self.show_date

        if show_from or show_date:
            v = "%s (" % v 
            T = current.T
            table = current.s3db.inv_recv
            if show_from:
                from_site_id = row.from_site_id
                if from_site_id:
                    from_string = table.from_site_id.represent(from_site_id,
                                                               show_link = False,
                                                               )
                else:
                    from_string = table.organisation_id.represent(row.organisation_id,
                                                                  show_link = False,
                                                                  )
                v = "%s%s: %s" % (v, T("From"), from_string)
            if show_date:
                date_string = table.date.represent(row.date)
                v = "%s %s %s" % (v, T("on"), date_string)

            v = "%s)" % v 

        return v

# =============================================================================
class inv_ReqRepresent(S3Represent):
    """
        Represent an Inventory Requisition
    """

    def __init__(self,
                 show_link = False,
                 ):

        super(inv_ReqRepresent, self).__init__(lookup = "inv_req",
                                               fields = ["date",
                                                         "req_ref",
                                                         "site_id",
                                                         ],
                                               show_link = show_link,
                                               )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: never used for custom fns (retained for API compatibility)
        """

        fields = self.fields
        fields.append(key)

        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(*fields)
        self.queries += 1

        table = current.db.inv_req

        # Bulk-represent site_ids for rows with no req_ref
        site_ids = [row.site_id for row in rows if not row.req_ref]
        if site_ids:
            # Results cached in the represent class
            table.site_id.represent.bulk(site_ids, show_link = False)

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        if row.req_ref:
            v = row.req_ref
        else:
            table = current.s3db.inv_req

            site_string = table.site_id.represent(row.site_id,
                                                  show_link = False,
                                                  )
            date_string = table.date.represent(row.date)

            v = "%s - %s" % (site_string,
                             date_string)

        return v

# =============================================================================
class inv_ReqItemRepresent(S3Represent):

    def __init__(self):
        """
            Constructor
        """

        super(inv_ReqItemRepresent, self).__init__(lookup = "inv_req_item",
                                                   )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom look-up of rows

            @param key: the key field
            @param values: the values to look up
            @param fields: unused (retained for API compatibility)
        """

        ritable = self.table
        sitable = current.s3db.supply_item

        count = len(values)
        if count == 1:
            query = (ritable.id == values[0])
        else:
            query = (ritable.id.belongs(values))

        left = sitable.on(ritable.item_id == sitable.id)
        rows = current.db(query).select(ritable.id,
                                        sitable.name,
                                        left = left,
                                        limitby = (0, count),
                                        )
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        if not hasattr(row, "supply_item"):
            return str(row.id)

        return row.supply_item.name

# =============================================================================
class inv_ReqRefRepresent(S3Represent):
    """
        Represent an Inventory Requisition Reference
    """

    def __init__(self,
                 show_link = False,
                 pdf = False,
                 ):

        self.pdf = pdf

        super(inv_ReqRefRepresent, self).__init__(lookup = "inv_req",
                                                  key = "req_ref",
                                                  fields = ["id",
                                                            ],
                                                  show_link = show_link,
                                                  )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Lookup all rows referenced by values.
            (in foreign key representations)

            @param key: the key Field
            @param values: the values
            @param fields: the fields to retrieve
        """

        fields = ["id",
                  "req_ref",
                  ]

        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(*fields)
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link.

                - Typically, k is a foreign key value, and v the
                  representation of the referenced record, and the link
                  shall open a read view of the referenced record.

                - In the base class, the linkto-parameter expects a URL (as
                  string) with "[id]" as placeholder for the key.

            @param k: the key
            @param v: the representation of the key
            @param row: the row with this key (unused in the base class)
        """

        if self.linkto:
            k = s3_str(row.id)
            _href = self.linkto.replace("[id]", k) \
                               .replace("%5Bid%5D", k)
            
            if self.pdf:
                _href = "%s/%s" % (_href,
                                   "form",
                                   )
            return A(v, _href=_href)
        else:
            return v

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        return row.req_ref or current.messages["NONE"]

# =============================================================================
class inv_SendRepresent(S3Represent):
    """
        Represent a Sent Shipment
    """

    def __init__(self,
                 show_link = False,
                 show_site = False,
                 show_date = False,
                 ):

        fields = ["send_ref",
                  ]
        if show_site:
            fields.append("to_site_id")
        if show_date:
            fields.append("date")

        self.show_site = show_site
        self.show_date = show_date

        super(inv_SendRepresent, self).__init__(lookup = "inv_send",
                                                fields = fields,
                                                show_link = show_link,
                                                )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: never used for custom fns (retained for API compatibility)
        """

        fields = self.fields
        fields.append(key)

        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(*fields)
        self.queries += 1

        table = current.db.inv_send

        if self.show_site:
            # Bulk-represent site_ids
            site_ids = [row.to_site_id for row in rows]
            if site_ids:
                # Results cached in the represent class
                table.to_site_id.represent.bulk(site_ids, show_link = False)

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """


        v = row.send_ref

        show_site = self.show_site
        show_date = self.show_date
        if show_site or show_date:
            v = "%s (" % v 
            T = current.T
            table = current.s3db.inv_send
            if show_site:
                to_string = table.to_site_id.represent(row.to_site_id,
                                                       show_link = False,
                                                       )
                v = "%s%s: %s" % (v, T("To"), to_string)
            if show_date:
                date_string = table.date.represent(row.date)
                v = "%s %s %s" % (v, T("on"), date_string)

            v = "%s)" % v 

        return v

# =============================================================================
class inv_TrackItemRepresent(S3Represent):

    def __init__(self):
        """
            Constructor
        """

        super(inv_TrackItemRepresent, self).__init__(lookup = "inv_track_item",
                                                     fields = ["send_inv_item_id"],
                                                     )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom look-up of rows

            @param key: the key field
            @param values: the values to look up
            @param fields: unused (retained for API compatibility)
        """

        fields = self.fields
        fields.append(key)

        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(*fields)
        self.queries += 1

        # Bulk-represent inv_item_ids
        inv_item_ids = [row.send_inv_item_id for row in rows]
        if inv_item_ids:
            # Results cached in the represent class
            current.db.inv_track_item.send_inv_item_id.represent.bulk(inv_item_ids,
                                                                      show_link = False,
                                                                      )

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        send_inv_item_id = row.send_inv_item_id
        if not send_inv_item_id:
            return str(row.id)

        return current.db.inv_track_item.send_inv_item_id.represent(send_inv_item_id,
                                                                    show_link = False,
                                                                    )

# END =========================================================================
