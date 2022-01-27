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
           "InventoryPackageModel",
           "InventoryPackageShipmentModel",
           "InventoryRequisitionModel",
           "InventoryRequisitionApproverModel",
           "InventoryRequisitionItemModel",
           "InventoryRequisitionItemInventoryModel",
           "InventoryRequisitionItemCategoryModel",
           "InventoryRequisitionProjectModel",
           "InventoryRequisitionRecurringModel",
           "InventoryRequisitionShipmentModel",
           "InventoryRequisitionTagModel",
           "InventoryStockCardModel",
           "InventoryTrackingModel",
           "inv_adj_close",
           "inv_adj_rheader",
           "inv_commit_send",
           #"inv_gift_certificate",
           #"inv_item_label",
           "inv_item_total_weight",
           "inv_item_total_volume",
           #"inv_package_labels",
           #"inv_packing_list",
           #"inv_pick_list",
           "inv_recv_attr",
           #"inv_recv_cancel",
           "inv_recv_controller",
           "inv_recv_crud_strings",
           "inv_recv_form",
           "inv_recv_rheader",
           #"inv_recv_process",
           #"inv_remove",
           "inv_req_add_from_template", # Exported for Tasks
           #"inv_req_approve",
           #"inv_req_approvers",
           #"inv_req_approvers_to_notify",
           #"inv_req_copy_all",
           #"inv_req_commit_all",
           "inv_req_controller",
           "inv_req_create_form_mods",
           #"inv_req_from",
           #"inv_req_inline_form",
           #"inv_req_is_approver",
           "inv_req_item_inv_item",
           "inv_req_item_order",
           #"inv_req_item_postprocess",
           #"inv_req_marker_fn",
           "inv_req_match",
           #"inv_req_pick_list",
           "inv_req_rheader",
           #"inv_req_send",
           "inv_req_tabs",
           #"inv_req_update_status",
           "inv_rfooter",
           "inv_rheader",
           #"inv_send_add_items_of_shipment_type",
           "inv_send_controller",
           #"inv_send_cancel",
           #"inv_send_form",
           #"inv_send_item_postprocess",
           #"inv_send_onaccept",
           "inv_send_postprocess",
           #"inv_send_process",
           #"inv_send_received",
           #"inv_send_return",
           #"inv_send_return_complete",
           #"inv_send_rheader",
           #"inv_ship_status",
           #"inv_stock_card_update",
           "inv_stock_movements",
           "inv_tabs",
           #"inv_timeline",
           "inv_track_item_deleting",
           "inv_tracking_status",
           "inv_warehouse_controller",
           "inv_warehouse_free_capacity",
           "inv_InvItemRepresent",
           #"inv_PackageRepresent",
           #"inv_RecvRepresent",
           #"inv_RecvWizard",
           #"inv_ReqCheckMethod",
           "inv_ReqItemRepresent",
           "inv_ReqRefRepresent",
           #"inv_SendRepresent",
           #"inv_SendWizard",
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
                           represent = s3_options_represent(priority_opts),
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
                           represent = s3_options_represent(status_opts),
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
TRACK_STATUS_UNLOADING  = 3 # Not used any more (was a temporary status used for processing by inv_track_item_onaccept, but that is now all done in inv_recv_process)
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
def inv_itn_field(**attr):
    label = current.deployment_settings.get_inv_itn_label()
    if label:
        return S3ReusableField("item_source_no", length=16,
                               label = label,
                               represent = lambda v: v or NONE,
                               requires = [IS_LENGTH(16),
                                           # Prevent storing "" (always store None in this case)
                                           # - makes for easier matching
                                           IS_NOT_EMPTY_STR(),
                                           ],
                               **attr)
    else:
        return S3ReusableField("item_source_no", length=16,
                               readable = False,
                               writable = False,
                               **attr)

# =============================================================================
class WarehouseModel(S3Model):

    names = ("inv_warehouse",
             "inv_warehouse_type",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        OBSOLETE = current.messages.OBSOLETE

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
           msg_list_empty = T("No Warehouse Types currently registered"),
           )

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
            msg_list_empty = T("No Warehouses currently registered"),
            )

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
        return None

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
             "inv_inv_item_bin",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        define_table = self.define_table

        organisation_id = self.org_organisation_id

        settings = current.deployment_settings
        direct_stock_edits = settings.get_inv_direct_stock_edits()
        inv_item_status_opts = settings.get_inv_item_status()
        track_pack_values = settings.get_inv_track_pack_values()
        WAREHOUSE = T(settings.get_inv_facility_label())

        if settings.get_org_branches():
            owner_org_id_label = T("Owned By (Organization/Branch)")
        else:
            owner_org_id_label = T("Owned By Organization")

        inv_source_type = {0: None,
                           1: T("Donated"),
                           2: T("Procured"),
                           }

        is_float_represent = IS_FLOAT_AMOUNT.represent
        float_represent = lambda v: is_float_represent(v, precision=2)

        # =====================================================================
        # Inventory Item
        #
        # Stock in a warehouse, or other site,'s inventory store.
        #
        # ondelete references have been set to RESTRICT because the inv. items
        # should never be automatically deleted
        #
        tablename = "inv_inv_item"
        define_table(tablename,
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     self.super_link("site_id", "org_site",
                                     default = auth.user.site_id if auth.is_logged_in() else None,
                                     empty = False,
                                     instance_types = auth.org_site_types,
                                     label = WAREHOUSE,
                                     ondelete = "RESTRICT",
                                     represent = self.org_site_represent,
                                     updateable = True,
                                     readable = True,
                                     writable = True,
                                     # Comment these to use a Dropdown & not an Autocomplete
                                     #widget = S3SiteAutocompleteWidget(),
                                     #comment = DIV(_class = "tooltip",
                                     #              _title = "%s|%s" % (WAREHOUSE,
                                     #                                  messages.AUTOCOMPLETE_HELP
                                     #                                  ).
                                     #              ),
                                     ),
                     self.supply_item_entity_id(),
                     self.supply_item_id(ondelete = "RESTRICT",
                                         required = True,
                                         ),
                     self.supply_item_pack_id(ondelete = "RESTRICT",
                                              required = True,
                                              script = None, # We use s3.inv_item.js rather than filterOptionsS3
                                              ),
                     Field("quantity", "double", notnull=True,
                           default = 0.0,
                           label = T("Quantity"),
                           represent = float_represent,
                           requires = IS_FLOAT_AMOUNT(minimum = 0.0),
                           writable = direct_stock_edits,
                           ),
                     # e.g.: Allow items to be marked as 'still on the shelf but allocated to an outgoing shipment'
                     Field("status", "integer",
                           default = 0, # Good. Only Items with this Status can be allocated to Outgoing Shipments
                           label = T("Status"),
                           represent = s3_options_represent(inv_item_status_opts),
                           requires = IS_IN_SET(inv_item_status_opts,
                                                zero = None),
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
                           represent = float_represent,
                           readable = track_pack_values,
                           writable = track_pack_values,
                           ),
                     # @ToDo: Move this into a Currency Widget for the pack_value field
                     s3_currency(readable = track_pack_values,
                                 writable = track_pack_values,
                                 ),
                     inv_itn_field()(),
                     # Organisation that owns this item
                     organisation_id("owner_org_id",
                                     label = owner_org_id_label,
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
                           represent = s3_options_represent(inv_source_type),
                           requires = IS_EMPTY_OR(
                                       IS_IN_SET(inv_source_type)
                                       ),
                           writable = False,
                           ),
                     Field.Method("total_value",
                                  self.inv_item_total_value,
                                  ),
                     Field.Method("pack_quantity",
                                  SupplyItemPackQuantity(tablename),
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
            msg_list_empty = T("No Stock currently registered in this Warehouse"),
            )

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

        report_options = {"rows": rows,
                          "cols": cols,
                          "fact": fact,
                          "methods": ["sum"],
                          "defaults": {"rows": "item_id",
                                       "cols": "site_id",
                                       "fact": "sum(quantity)",
                                       },
                          # These options don't do anything:
                          #"groupby": self.inv_inv_item.site_id,
                          #"hide_comments": True,
                          }

        # List fields
        list_fields = ["site_id",
                       "item_id",
                       "item_id$code",
                       "item_id$item_category_id",
                       "quantity",
                       "bin.layout_id",
                       "expiry_date",
                       "owner_org_id",
                       "supply_org_id",
                       "status",
                       ]

        if track_pack_values:
            list_fields.insert(7, "currency")
            list_fields.insert(7, (T("Total Value"), "total_value"))
            list_fields.insert(7, "pack_value")

        crud_form = S3SQLCustomForm("site_id",
                                    "item_id",
                                    "item_pack_id",
                                    "quantity",
                                    S3SQLInlineComponent("bin",
                                                         label = T("Bins"),
                                                         fields = ["layout_id",
                                                                   "quantity",
                                                                   ],
                                                         ),
                                    "status",
                                    "purchase_date",
                                    "expiry_date",
                                    "pack_value",
                                    "currency",
                                    "item_source_no",
                                    "owner_org_id",
                                    "supply_org_id",
                                    "source_type",
                                    "comments",
                                    postprocess = self.inv_item_postprocess,
                                    )

        # Configuration
        self.configure(tablename,
                       # Lock the record so that it can't be meddled with
                       # - unless explicitly told to allow this
                       deletable = direct_stock_edits,
                       editable = direct_stock_edits,
                       insertable = direct_stock_edits,
                       context = {"location": "site_id$location_id",
                                  },
                       crud_form = crud_form,
                       deduplicate = self.inv_item_duplicate,
                       extra_fields = ["quantity",
                                       "pack_value",
                                       "item_pack_id",
                                       ],
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       onaccept = self.inv_item_onaccept,
                       ondelete = self.inv_item_ondelete,
                       ondelete_cascade = self.inv_item_ondelete_cascade,
                       onimport = self.inv_item_onimport,
                       report_options = report_options,
                       super_entity = "supply_item_entity",
                       grouped = {"default": {"title": T("Warehouse Stock Report"),
                                              "fields": [(T("Warehouse"), "site_id$name"),
                                                         "item_id$item_category_id",
                                                         "layout_id",
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
                            inv_inv_item_bin = {"name": "bin",
                                                "joinby": "inv_item_id",
                                                },
                            )

        # ---------------------------------------------------------------------
        # Inventory Items <> Bins
        #

        tablename = "inv_inv_item_bin"
        define_table(tablename,
                     inv_item_id(),
                     self.org_site_layout_id(label = T("Bin"),
                                             empty = False,
                                             # This has the URL adjusted for the right site_id in the controller & s3.inv_item.js
                                             comment = S3PopupLink(c = "org",
                                                                   f = "site",
                                                                   args = ["[id]", "layout", "create"],
                                                                   vars = {"child": "layout_id",
                                                                           # @ToDo: Restrict to site_id to reduce risk of race condition
                                                                           #"optionsVar": "site_id",
                                                                           #"optionsValue": "[id]",
                                                                           },
                                                                   label = T("Create Bin"),
                                                                   title = T("Bin"),
                                                                   tooltip = T("If you don't see the Bin listed, you can add a new one by clicking link 'Create Bin'."),
                                                                   _id = "inv_inv_item_bin_layout_id-create-btn",
                                                                   ),
                                             ),
                     Field("quantity", "double", notnull=True,
                           default = 0,
                           label = T("Quantity"),
                           represent = float_represent,
                           ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"inv_item_id": inv_item_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_item_duplicate(item):
        """
            Update detection for inv_inv_item

            Args:
                item: the S3ImportItem
        """

        table = item.table
        data = item.data
        data_get = data.get

        # Must match all of these exactly
        query = (table.site_id == data_get("site_id")) & \
                (table.item_id == data_get("item_id")) & \
                (table.owner_org_id == data_get("owner_org_id")) & \
                (table.supply_org_id == data_get("supply_org_id")) & \
                (table.pack_value == data_get("pack_value")) & \
                (table.currency == data_get("currency"))
        if current.deployment_settings.get_inv_itn_label():
            query &= (table.item_source_no == data_get("item_source_no"))

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

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_item_onaccept(form):
        """
            Called when Stock is created/updated by:
            - direct_stock_edits
            - imports

            Update the Free Capacity of the Warehouse
        """

        if current.response.s3.bulk:
            # Done in inv_item_onimport to reduce load
            return

        # Update the Free Capacity of the Warehouse
        if current.deployment_settings.get_inv_warehouse_free_capacity_calculated():
            site_id = form.vars.get("site_id")
            if not site_id:
                table = current.s3db.inv_inv_item
                record = current.db(table.id == form.vars.id).select(table.site_id,
                                                                     limitby = (0, 1),
                                                                     ).first()
                site_id = record.site_id

            inv_warehouse_free_capacity(site_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_item_ondelete(row):
        """
            Called when Stock is deleted by:
            - direct_stock_edits

            Update the Free Capacity of the Warehouse
        """

        # Update the Free Capacity of the Warehouse
        if current.deployment_settings.get_inv_warehouse_free_capacity_calculated():
            site_id = row.get("site_id")
            if not site_id:
                table = current.s3db.inv_inv_item
                record = current.db(table.id == row.id).select(table.site_id,
                                                               limitby = (0, 1),
                                                               ).first()
                site_id = record.site_id

            inv_warehouse_free_capacity(site_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_item_ondelete_cascade(row):
        """
            Called when Stock is deleted by:
            - direct_stock_edits

            Update the Stock Cards
            - needs to be done in ondelete_cascade not ondelete
        """

        # Update the Stock Cards
        if current.deployment_settings.get_inv_stock_cards():
            inv_stock_card_update([row.id],
                                  comments = "Direct Stock Edit",
                                  delete = True,
                                  )

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_item_onimport(import_info):
        """
            Called when Stock is created/updated by:
            - imports

            Create/Update the Stock Cards
            Update the Free Capacity of the Warehouses
        """

        if not import_info["records"]:
            # Nothing imported
            return

        created = import_info.get("created", [])
        updated = import_info.get("updated", [])
        inv_item_ids = created + updated

        settings = current.deployment_settings

        # Update the Free Capacity of the Warehouses
        if settings.get_inv_warehouse_free_capacity_calculated():
            table = current.s3db.inv_inv_item
            rows = current.db(table.id.belongs(inv_item_ids)).select(table.site_id)
            site_ids = set([row.site_id for row in rows])
            for site_id in site_ids:
                inv_warehouse_free_capacity(site_id)

        # Create/Update the Stock Cards
        if settings.get_inv_stock_cards():
            inv_stock_card_update(inv_item_ids,
                                  comments = "Import",
                                  )

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_item_postprocess(form):
        """
            Called when Stock is created/updated by:
            - direct_stock_edits

            Create/Update the Stock Card
        """

        if current.deployment_settings.get_inv_stock_cards():
            inv_stock_card_update([form.vars.id],
                                  comments = "Direct Stock Edit",
                                  )

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
            return NONE
        else:
            return round(value, 2)

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
             "inv_adj_item_bin",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        settings = current.deployment_settings
        track_pack_values = settings.get_inv_track_pack_values()

        organisation_id = self.org_organisation_id
        org_site_represent = self.org_site_represent

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        is_float_represent = IS_FLOAT_AMOUNT.represent
        float_represent = lambda v: is_float_represent(v, precision=2)

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
                                       comment = self.pr_person_comment(child = "adjuster_id")
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
                           default = 0,
                           label = T("Status"),
                           represent = s3_options_represent(adjust_status),
                           requires = IS_IN_SET(adjust_status,
                                                zero = None),
                           writable = False
                           ),
                     Field("category", "integer",
                           default = 1,
                           label = T("Type"),
                           represent = s3_options_represent(adjust_type),
                           requires = IS_IN_SET(adjust_type,
                                                zero = None),
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  super_entity = "doc_entity",
                  create_onaccept = self.inv_adj_create_onaccept,
                  create_next = URL(args = ["[id]", "adj_item"]),
                  )

        # Components
        add_components(tablename,
                       inv_adj_item = "adj_id",
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
                         1 : T("Lost"),
                         2 : T("Found"),
                         3 : T("Damaged"),
                         4 : T("Expired"),
                         5 : T("Transfer Ownership"),
                         6 : T("Update Bin"),
                         11 : T("Issued without Record"),
                         12 : T("Distributed without Record"),
                         }

        if track_pack_values:
            adjust_reason[7] = T("Update Value")

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
                msg_list_empty = T("No stock counts have been done"),
                )
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
                msg_list_empty = T("No stock adjustments have been done"),
                )

        # ---------------------------------------------------------------------
        # Adjustment Items
        #
        inv_item_status_opts = settings.get_inv_item_status()

        if settings.get_org_branches():
            old_owner_org_id_label = T("Currently Owned by (Organization/Branch)")
            new_owner_org_id_label = T("Transfer Ownership to Organization/Branch")
        else:
            old_owner_org_id_label = T("Currently Owned by Organization")
            new_owner_org_id_label = T("Transfer Ownership to Organization")

        itn_label = settings.get_inv_itn_label()
        if itn_label:
            # Display Inv Item as the CTN
            inv_item_readable = True
            inv_item_represent = S3Represent(lookup = "inv_inv_item",
                                             fields = ("item_source_no",),
                                             )
        else:
            inv_item_readable = False
            inv_item_represent = None

        tablename = "inv_adj_item"
        define_table(tablename,
                     adj_id(),
                     # Original inventory item
                     self.inv_item_id(ondelete = "RESTRICT",
                                      label = itn_label,
                                      represent = inv_item_represent,
                                      readable = inv_item_readable,
                                      writable = False,
                                      comment = None,
                                      ),
                     self.supply_item_id(ondelete = "RESTRICT"),
                     self.supply_item_pack_id(ondelete = "SET NULL"),
                     Field("reason", "integer",
                           default = 0, # Unknown
                           label = T("Reason"),
                           represent = s3_options_represent(adjust_reason),
                           requires = IS_IN_SET(adjust_reason,
                                                zero = None),
                           writable = False,
                           ),
                     Field("old_quantity", "double", notnull=True,
                           default = 0,
                           label = T("Original Quantity"),
                           represent = float_represent,
                           writable = False,
                           ),
                     Field("new_quantity", "double",
                           label = T("Revised Quantity"),
                           represent = self.qnty_adj_repr,
                           requires = IS_FLOAT_AMOUNT(minimum = 0.0),
                           ),
                     Field("old_status", "integer",
                           default = 0, # Good
                           label = T("Current Status"),
                           represent = s3_options_represent(inv_item_status_opts),
                           requires = IS_IN_SET(inv_item_status_opts,
                                                zero = None),
                           writable = False,
                           ),
                     Field("new_status", "integer",
                           default = 0, # Good
                           label = T("Revised Status"),
                           represent = s3_options_represent(inv_item_status_opts),
                           requires = IS_IN_SET(inv_item_status_opts,
                                                zero = None),
                           ),
                     # Organisation that owned this item before
                     organisation_id("old_owner_org_id",
                                     label = old_owner_org_id_label,
                                     ondelete = "SET NULL",
                                     writable = False,
                                     comment = None,
                                     ),
                     # Organisation that owns this item now
                     organisation_id("new_owner_org_id",
                                     label = new_owner_org_id_label,
                                     ondelete = "SET NULL",
                                     ),
                     s3_date("expiry_date",
                             label = T("Expiry Date"),
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
                                 writable = track_pack_values,
                                 ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_form = S3SQLCustomForm("item_id",
                                    "inv_item_id",
                                    "item_pack_id",
                                    "reason",
                                    "old_quantity",
                                    "new_quantity",
                                    S3SQLInlineComponent("bin",
                                                         label = T("Bins"),
                                                         fields = ["layout_id",
                                                                   "quantity",
                                                                   ],
                                                         ),
                                    "old_status",
                                    "new_status",
                                    "old_owner_org_id",
                                    "new_owner_org_id",
                                    "expiry_date",
                                    "old_pack_value",
                                    "new_pack_value",
                                    "currency",
                                    "comments",
                                    )

        configure(tablename,
                  crud_form = crud_form,
                  deletable = False,
                  )

        # Components
        add_components(tablename,
                       inv_adj_item_bin = {"name": "bin",
                                           "joinby": "adj_item_id",
                                           },
                       )

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
            #title_list = T("Items in Stock"),
            title_update = T("Adjust Stock Item"),
            label_list_button = T("List Items"),
            #label_delete_button = T("Remove Item from Stock"), # This is forbidden - set qty to zero instead
            msg_record_created = T("Item added to stock adjustment"),
            msg_record_modified = T("Item adjustment saved as Draft until Adjustment Completed"),
            #msg_record_deleted = T("Item removed from Stock"), # This is forbidden - set qty to zero instead
            msg_list_empty = T("No items currently in stock"),
            )

        # ---------------------------------------------------------------------
        # Inventory Adjustment Items <> Bins
        #
        #  Can't just use Inventory Item Bins as we need to be able to make
        #  draft changes which aren't committed until the adjustment is closed.
        #
        tablename = "inv_adj_item_bin"
        define_table(tablename,
                     adj_item_id(empty = False,
                                 ondelete = "CASCADE",
                                 ),
                     self.org_site_layout_id(label = T("Bin"),
                                             empty = False,
                                             # This has the URL adjusted for the right site_id in the controller & s3.inv_item.js
                                             comment = S3PopupLink(c = "org",
                                                                   f = "site",
                                                                   args = ["[id]", "layout", "create"],
                                                                   vars = {"child": "layout_id",
                                                                           # @ToDo: Restrict to site_id to reduce risk of race condition
                                                                           #"optionsVar": "site_id",
                                                                           #"optionsValue": "[id]",
                                                                           },
                                                                   label = T("Create Bin"),
                                                                   title = T("Bin"),
                                                                   tooltip = T("If you don't see the Bin listed, you can add a new one by clicking link 'Create Bin'."),
                                                                   _id = "inv_adj_item_bin_layout_id-create-btn",
                                                                   ),
                                             ),
                     Field("quantity", "double", notnull=True,
                           default = 0,
                           label = T("Quantity"),
                           represent = float_represent,
                           ),
                     *s3_meta_fields())

        return {"inv_adj_id": adj_id,
                "inv_adj_item_id": adj_item_id,
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

    # ---------------------------------------------------------------------
    @staticmethod
    def inv_adj_create_onaccept(form):
        """
           When an adjustment record is created and it is of type inventory
           then an adj_item record for each inv_inv_item in the site will be
           created. If needed, extra adj_item records can be created later.
        """

        db = current.db

        adj_id = form.vars.id

        adj_table = db.inv_adj
        record = db(adj_table.id == adj_id).select(adj_table.category,
                                                   limitby = (0, 1),
                                                   ).first()
        if record.category != 1:
            # Not a (Full) Inventory Adjustment
            return

        s3db = current.s3db

        site_id = form.vars.site_id

        adj_bin_table = s3db.inv_adj_item_bin
        adj_item_table = s3db.inv_adj_item
        inv_bin_table = s3db.inv_inv_item_bin
        inv_item_table = s3db.inv_inv_item

        # Get all inv items for this site with a positive quantity
        query = (inv_item_table.site_id == site_id) & \
                (inv_item_table.quantity > 0) & \
                (inv_item_table.deleted == False)
        left = inv_bin_table.on(inv_bin_table.inv_item_id == inv_item_table.id)
        rows = db(query).select(inv_item_table.id,
                                inv_item_table.item_id,
                                inv_item_table.item_pack_id,
                                inv_item_table.quantity,
                                inv_item_table.currency,
                                inv_item_table.status,
                                inv_item_table.pack_value,
                                inv_item_table.expiry_date,
                                inv_item_table.owner_org_id,
                                inv_bin_table.layout_id,
                                inv_bin_table.quantity,
                                left = left,
                                )

        # Group by inv_item_id
        inv_items = {}
        for row in rows:
            inv_item_id = row["inv_inv_item.id"]
            if inv_item_id in inv_items:
                inv_items[inv_item_id].append(row)
            else:
                inv_items[inv_item_id] = [row]

        for inv_item_id in inv_items:
            bins = inv_items[inv_item_id]
            # Add an adjustment item record
            inv_item = bins[0].inv_inv_item
            adj_item_id = adj_item_table.insert(reason = 0,
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
                                                old_owner_org_id = inv_item.owner_org_id,
                                                new_owner_org_id = inv_item.owner_org_id,
                                                )

            for row in bins:
                bin_record = row.inv_inv_item_bin
                layout_id = bin_record.layout_id
                if layout_id:
                    adj_bin_table.insert(adj_item_id = adj_item_id,
                                         layout_id = layout_id,
                                         quantity = bin_record.quantity,
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
            msg_list_empty = T("No Commitments"),
            )

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

        if hasattr(row, "req_id"):
            req_id = row.req_id
        else:
            # Read from deleted_fk
            template_id = row.id

            # Load record
            table = db.inv_commit
            record = db(table.id == record_id).select(table.deleted_fk,
                                                      limitby = (0, 1),
                                                      ).first()

            deleted_fk = json.loads(record.deleted_fk)
            req_id = deleted_fk.get("req_id")

        if req_id:
            rtable = current.s3db.inv_req
            req = db(rtable.id == req_id).select(rtable.id,
                                                 rtable.commit_status,
                                                 limitby = (0, 1),
                                                 ).first()
            if req:
                # Update committed quantities and request status
                req_update_commit_quantities_and_status(req)

# =============================================================================
class InventoryCommitItemModel(S3Model):
    """
        Model for Committed (Pledged) Items for Inventory Requisitions
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
            msg_list_empty = T("No Commitment Items currently registered"),
            )

        self.configure(tablename,
                       extra_fields = ["item_pack_id"],
                       onaccept = self.commit_item_onaccept,
                       ondelete = self.commit_item_ondelete,
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return None

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

        if hasattr(row, "commit_id"):
            commit_id = row.commit_id
        else:
            # Read it from deleted_fk
            record_id = row.id

            # Load full record
            table = db.inv_commit_item
            record = db(table.id == record_id).select(table.deleted_fk,
                                                      limitby = (0, 1),
                                                      ).first()

            deleted_fk = json.loads(record.deleted_fk)
            commit_id = deleted_fk.get("commit_id")

        if commit_id:
            s3db = current.s3db
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

        @ToDo: Do the Kitting on 'process' & allow editing of bins before this
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
                             # Not likely to be so many kits in the Catalog to need this:
                             #widget = S3AutocompleteWidget("supply", "item",
                             #                              filter = "item.kit=1",
                             #                              ),
                             widget = None,
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
                     #self.inv_req_ref(writable = True),
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
            msg_list_empty = T("No Kittings"),
            )

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
                                 #"req_ref",
                                 "quantity",
                                 "date",
                                 "repacked_id",
                                 ],
                  onvalidation = self.inv_kitting_onvalidation,
                  )

        # ---------------------------------------------------------------------
        # Kitting Items
        # - Component items of Kits which can be used to build a pick-list
        #
        tablename = "inv_kitting_item"
        define_table(tablename,
                     # Component
                     Field("kitting_id", "reference inv_kitting",
                           readable = False,
                           writable = False,
                           ),
                     # Why duplicate this here?
                     #Field("site_id", "reference org_site",
                     #      readable = False,
                     #      writable = False,
                     #      ),
                     self.inv_item_id(ondelete = "RESTRICT",
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
                     self.org_site_layout_id(label = T("Bin"),
                                             writable = False,
                                             ),
                     inv_itn_field()(),
                     #s3_comments(),
                     *s3_meta_fields())

        # This is a read-only Pick List
        configure(tablename,
                  deletable = False,
                  editable = False,
                  insertable = False,
                  )

        #----------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_kitting_onvalidation(form):
        """
            Check that we have sufficient inv_item in stock to build the kits
        """

        form_vars = form.vars

        item_id = form_vars.item_id
        quantity = form_vars.quantity
        site_id = form_vars.site_id

        db = current.db
        s3db = current.s3db

        # Get contents of this kit
        ktable = s3db.supply_kit_item
        kit_items = db(ktable.parent_item_id == item_id).select(ktable.item_id,
                                                                ktable.quantity,
                                                                ktable.item_pack_id,
                                                                )
        item_ids = [row.item_id for row in kit_items]

        # Lookup the Stock of these component items
        iitable = s3db.inv_inv_item
        ii_expiry_field = iitable.expiry_date

        # Filter out Stock which is in Bad condition or Expired
        query = (iitable.site_id == site_id) & \
                (iitable.item_id.belongs(item_ids)) & \
                (iitable.quantity > 0) & \
                ((ii_expiry_field >= current.request.utcnow) | ((ii_expiry_field == None))) & \
                (iitable.status == 0)

        wh_items = db(query).select(iitable.item_id,
                                    iitable.quantity,
                                    iitable.item_pack_id,
                                    )

        # Lookup Packs
        item_pack_id = int(form_vars.item_pack_id)
        item_pack_ids = [row.item_pack_id for row in kit_items] + [row.item_pack_id for row in wh_items]
        item_pack_ids.append(item_pack_id)

        ptable = db.supply_item_pack
        packs = db(ptable.id.belongs(set(item_pack_ids))).select(ptable.id,
                                                                 ptable.quantity,
                                                                 )
        packs = {p.id: p.quantity for p in packs}
        
        # How many kits are we building?
        quantity = quantity * packs[item_pack_id]

        max_kits = None

        # Loop through each supply_item in the kit
        for kit_item in kit_items:
            # How much of this supply_item is required per kit?
            one_kit = kit_item.quantity * packs[kit_item.item_pack_id]

            # How much of this supply_item do we have in stock?
            stock_amount = 0
            rows = wh_items.find(lambda row: row.item_id == kit_item.item_id)
            for wh_item in rows:
                amount = wh_item.quantity * packs[wh_item.item_pack_id]
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
            - optimise to minimise the number of Bins remaining for an Item
            Provide a pick list to ensure that the right stock items are used
            to build the kits: inv_kitting_item
        """

        form_vars = form.vars

        kitting_id = form_vars.id
        item_id = form_vars.item_id
        site_id = form_vars.site_id

        db = current.db
        s3db = current.s3db

        # Get contents of this kit
        ktable = s3db.supply_kit_item
        kit_items = db(ktable.parent_item_id == item_id).select(ktable.item_id,
                                                                ktable.quantity,
                                                                ktable.item_pack_id,
                                                                )
        item_ids = [row.item_id for row in kit_items]

        # Lookup the Stock of these component items
        iitable = s3db.inv_inv_item
        ii_id_field = iitable.id
        ii_expiry_field = iitable.expiry_date
        ii_purchase_field = iitable.purchase_date

        # Match Stock based on oldest expiry date or purchase date
        orderby = ii_expiry_field | ii_purchase_field

        # We set expiry date of the kit to the oldest expiry date of the components
        expiry_date = None

        # Include Bins
        ibtable = s3db.inv_inv_item_bin
        ib_id_field = ibtable.id
        left = ibtable.on(ibtable.inv_item_id == ii_id_field)

        # Filter out Stock which is in Bad condition or Expired
        query = (iitable.site_id == site_id) & \
                (iitable.item_id.belongs(item_ids)) & \
                (iitable.quantity > 0) & \
                ((ii_expiry_field >= current.request.utcnow) | ((ii_expiry_field == None))) & \
                (iitable.status == 0)

        wh_items = db(query).select(ii_id_field,
                                    iitable.quantity,
                                    iitable.item_id,
                                    iitable.item_pack_id,
                                    iitable.item_source_no,
                                    ii_expiry_field,
                                    ii_purchase_field, # Included just for orderby on Postgres
                                    ib_id_field,
                                    ibtable.layout_id,
                                    ibtable.quantity,
                                    left = left,
                                    orderby = orderby,
                                    )

        # Lookup Packs
        item_pack_id = int(form_vars.item_pack_id)
        pack_ids = [row.item_pack_id for row in kit_items] + [row["inv_inv_item.item_pack_id"] for row in wh_items]
        pack_ids.append(item_pack_id)

        ptable = db.supply_item_pack
        packs = db(ptable.id.belongs(set(pack_ids))).select(ptable.id,
                                                            ptable.quantity,
                                                            )
        packs = {p.id: p.quantity for p in packs}

        # How many kits are we building?
        quantity = form_vars.quantity * packs[item_pack_id]

        # Loop through each supply_item in the kit
        from operator import itemgetter
        insert = s3db.inv_kitting_item.insert
        inv_item_ids = []
        append = inv_item_ids.append
        for kit_item in kit_items:
            # How much of this supply_item is required per kit?
            one_kit = kit_item.quantity * packs[kit_item.item_pack_id]

            # How much is required for all Kits?
            required = one_kit * quantity

            # What stock do we have for this item?
            ritem_id = kit_item.item_id
            rows = wh_items.find(lambda row: row["inv_inv_item.item_id"] == ritem_id)

            # Group by inv_item_id
            inv_items = {}
            for row in rows:
                inv_item_id = row["inv_inv_item.id"]
                if inv_item_id in inv_items:
                    inv_items[inv_item_id].append(row)
                else:
                    inv_items[inv_item_id] = [row]

            for inv_item_id in inv_items:
                append(inv_item_id)
                binned_quantity = 0
                bins = inv_items[inv_item_id]
                inv_item = bins[0].inv_inv_item

                if inv_item.expiry_date:
                    if expiry_date is None:
                        # No expiry date set so this item starts the list
                        expiry_date = inv_item.expiry_date
                    else:
                        # Shorten the expiry date if less than for previous items
                        if inv_item.expiry_date < expiry_date:
                            expiry_date = inv_item.expiry_date

                # How many of this item can we use for these kits?
                inv_quantity = inv_item.quantity
                pack_quantity = packs[inv_item.item_pack_id]
                inv_amount = inv_quantity * pack_quantity
                # How many of this item will we use for the kits?
                if inv_amount > required:
                    # Use only what is required
                    inv_amount = required
                    inv_quantity -= (inv_amount / pack_quantity)
                else:
                    # We use all
                    inv_quantity = 0

                if len(bins) > 1:
                    # Multiple Bins
                    binned_quantity = 0
                    inv_bins = [row.inv_inv_item_bin for row in bins]
                    # Optimise to minimise the number of Bins remaining for an Item
                    inv_bins.sort(key = itemgetter("quantity"))
                    for inv_bin in inv_bins:
                        bin_quantity = inv_bin.quantity
                        binned_quantity += bin_quantity
                        bin_amount = bin_quantity * pack_quantity
                        # How many from this bin will we use for the kits?
                        if bin_amount > required:
                            # Use only what is required
                            bin_amount = required
                            bin_quantity -= (bin_amount / pack_quantity)
                        else:
                            # We use all
                            bin_quantity = 0

                        # Update the Bin
                        db(ib_id_field == inv_bin.id).update(quantity = bin_quantity)

                        # Add to Pick List
                        insert(kitting_id = kitting_id,
                               item_id = ritem_id,
                               item_pack_id = inv_item.item_pack_id,
                               item_source_no = inv_item.item_source_no,
                               quantity = bin_amount,
                               inv_item_id = inv_item_id,
                               layout_id = inv_bin.layout_id,
                               )

                        # Update how much is still required
                        required -= bin_amount

                        if not required:
                            # No more required: skip remaining bins
                            break

                    if required and (binned_quantity < inv_quantity):
                        # We still have some unbinned to take from
                        unbinned_quantity = inv_quantity - binned_quantity
                        unbinned_amount = unbinned_quantity * pack_quantity
                        # How many of this will we use for the kits?
                        if unbinned_amount > required:
                            # Use only what is required
                            unbinned_amount = required
                        #else:
                        #    # We use all

                        # Add to Pick List
                        insert(kitting_id = kitting_id,
                               item_id = ritem_id,
                               item_pack_id = inv_item.item_pack_id,
                               item_source_no = inv_item.item_source_no,
                               quantity = unbinned_amount,
                               inv_item_id = inv_item_id,
                               #layout_id = None,
                               )

                        # Update how much is still required
                        required -= unbinned_amount
                    
                else:
                    inv_bin = bins[0].inv_inv_item_bin
                    layout_id = inv_bin.layout_id
                    if layout_id:
                        # Single Bin
                        # Update the Bin
                        db(ib_id_field == inv_bin.id).update(quantity = inv_quantity)
                    #else:
                    #    # Unbinned

                    # Add to Pick List
                    insert(kitting_id = kitting_id,
                           item_id = ritem_id,
                           item_pack_id = inv_item.item_pack_id,
                           item_source_no = inv_item.item_source_no,
                           quantity = inv_amount,
                           inv_item_id = inv_item_id,
                           layout_id = layout_id,
                           )

                    # Update how much is still required
                    required -= inv_amount

                # Update Inv Quantity
                db(ii_id_field == inv_item_id).update(quantity = inv_quantity)

                if not required:
                    # No more required: move on to the next kit_item
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
        # supply_item_entity
        s3db.update_super(iitable, {"id": new_id})

        if current.deployment_settings.get_inv_stock_cards():
            append(new_id)
            inv_stock_card_update(inv_item_ids,
                                  comments = "Kitting",
                                  )

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

        return None

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
        return None

# =============================================================================
class InventoryPackageModel(S3Model):
    """
        Packages (Boxes & Pallets)
        https://en.wikipedia.org/wiki/Pallet
    """

    names = ("inv_package",
             "inv_package_id",
             )

    def model(self):

        T = current.T
        db = current.db

        is_float_represent = IS_FLOAT_AMOUNT.represent
        float_represent = lambda v: is_float_represent(v, precision=3)

        package_type_opts = {"BOX": T("Box"), 
                             "PALLET": T("Pallet"), 
                             }

        # -----------------------------------------------------------------
        # Packages
        #
        tablename = "inv_package"
        self.define_table(tablename,
                          Field("type", length=8,
                                default = "PALLET",
                                label = T("Type"),
                                represent = s3_options_represent(package_type_opts),
                                requires = IS_IN_SET(package_type_opts,
                                                     zero = None,
                                                     ),
                                ),
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
                                comment = T("Including the Package"),
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
            label_create = T("Create Package"),
            title_display = T("Package Details"),
            title_list = T("Packages"),
            title_update = T("Edit Package"),
            label_list_button = T("List Packages"),
            label_delete_button = T("Delete Package"),
            msg_record_created = T("Package Added"),
            msg_record_modified = T("Package Updated"),
            msg_record_deleted = T("Package Deleted"),
            msg_list_empty = T("No Packages defined"),
            )

        self.configure(tablename,
                       onaccept = self.inv_package_onaccept,
                       )

        # Reusable Field
        represent = inv_PackageRepresent()
        package_id = S3ReusableField("package_id", "reference %s" % tablename,
                                     label = T("Package Type"),
                                     ondelete = "RESTRICT",
                                     represent = represent,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "inv_package.id",
                                                              represent,
                                                              orderby = "inv_package.name",
                                                              sort = True,
                                                              )
                                                    ),
                                     sortby = "name",
                                     )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"inv_package_id": package_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_package_onaccept(form):
        """
            Set the Max Height for Boxes
            Calculate the Max Volume
        """

        form_vars = form.vars
        form_vars_get = form_vars.get

        package_type = form_vars_get("type")
        if package_type == "BOX":
            # max_height == depth
            max_height = form_vars_get("depth")
            updates = {"max_height": max_height}
        else:
            # max_height needs to be specified manually
            max_height = form_vars_get("max_height")
            if max_height:
                # Includes pallet height, so remove this for max volume of load
                depth = form_vars_get("depth")
                if depth:
                    max_height -= depth
            updates = {}

        if max_height:
            width = form_vars_get("width")
            length = form_vars_get("length")
            max_volume = width * length * max_height
            updates["max_volume"] = max_volume

        if updates:
            current.db(current.s3db.inv_package.id == form_vars.id).update(**updates)

# =============================================================================
class InventoryPackageShipmentModel(S3Model):
    """
        Packages <> Shipments model
    """

    names = ("inv_send_package",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        define_table = self.define_table

        is_float_represent = IS_FLOAT_AMOUNT.represent
        float_represent = lambda v: is_float_represent(v, precision=3)

        # -----------------------------------------------------------------
        # Shipment Packages
        # i.e. Packages <> Outbound Shipments
        #
        tablename = "inv_send_package"
        define_table(tablename,
                     Field("number", "integer",
                           label = T("Number"),
                           ),
                     self.inv_send_id(empty = False,
                                      ondelete = "CASCADE",
                                      ),
                     self.inv_package_id(empty = False,
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
                     Field.Method("items",
                                  self.send_package_items,
                                  ),
                     Field.Method("weight_max",
                                  self.send_package_weight,
                                  ),
                     Field.Method("volume_max",
                                  self.send_package_volume,
                                  ),
                     *s3_meta_fields())

        crud_form = S3SQLCustomForm("send_id",
                                    "number",
                                    "package_id",
                                    S3SQLInlineComponent("send_package_item",
                                                         label = "",
                                                         fields = [(T("Item"), "track_item_id"),
                                                                   (T("Quantity"), "quantity"),
                                                                   ],
                                                         ),
                                    "comments",
                                    )

        list_fields = ["number",
                       "package_id",
                       #(T("Items"), "send_package_item.track_item_id$item_id$code"),
                       (T("Items"), "items"),
                       #"weight",
                       (T("Weight (kg)"), "weight_max"),
                       #"volume",
                       (T("Volume (m3)"), "volume_max"),
                       "comments",
                       ]

        configure(tablename,
                  crud_form = crud_form,
                  extra_fields = ["weight",
                                  "volume",
                                  "package_id$load_capacity",
                                  "package_id$max_volume",
                                  # Crashes:
                                  #"send_package_item.track_item_id$item_id$name",
                                  ],
                  list_fields = list_fields,
                  onvalidation = self.send_package_onvalidation,
                  )

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Package"),
            title_display = T("Package Details"),
            title_list = T("Packages"),
            title_update = T("Edit Package"),
            label_list_button = T("List Packages"),
            label_delete_button = T("Delete Package"),
            msg_record_created = T("Package Added"),
            msg_record_modified = T("Package Updated"),
            msg_record_deleted = T("Package Deleted"),
            msg_list_empty = T("No Packages defined"),
            )

        self.add_components(tablename,
                            inv_send_package_item = "send_package_id",
                            )

        # -----------------------------------------------------------------
        # Shipment Packages <> Shipment Items
        #
        track_item_represent = inv_TrackItemRepresent()

        tablename = "inv_send_package_item"
        define_table(tablename,
                     Field("send_package_id", "reference inv_send_package",
                           ondelete = "CASCADE",
                           requires = IS_ONE_OF(db, "inv_send_package.id",
                                                "%(number)s",
                                                orderby = "inv_send_package.number",
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
                     Field("quantity", "double",
                           default = 1.0,
                           label = T("Quantity"),
                           represent = float_represent,
                           requires = IS_FLOAT_IN_RANGE(1),
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = self.send_package_item_onaccept,
                  ondelete = self.send_package_item_ondelete,
                  onvalidation = self.send_package_item_onvalidation,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def send_package_onvalidation(form):
        """
            Number must be Unique per Shipment
        """

        send_id = current.request.args(0)
        if not send_id:
            # Must be running from a script
            return

        db = current.db
        table = db.inv_send_package
        query = (table.send_id == send_id) 
        send_package_id = form.record_id
        if send_package_id:
            query &= (table.id != send_package_id)
        rows = db(query).select(table.number)
        numbers = [row.number for row in rows]
        if form.vars.get("number") in numbers:
            form.errors.number = current.T("There is already a Package with this Number in this Shipment.")

    # -------------------------------------------------------------------------
    @staticmethod
    def send_package_item_onaccept(form):
        """
            Update the Weight & Volume of the Shipment's Package
        """

        inv_send_package_update(form.vars.get("send_package_id"))

    # -------------------------------------------------------------------------
    @staticmethod
    def send_package_item_ondelete(row):
        """
            Update the Weight & Volume of the Shipment's Package
        """

        inv_send_package_update(row.send_package_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def send_package_item_onvalidation(form):
        """
            Validate the Quantity Packaged doesn't exceed the Quantity Shipped
        """

        db = current.db

        form_vars = form.vars
        new_quantity = float(form_vars.quantity)

        spitable = db.inv_send_package_item

        record_id = form.record_id
        if record_id:
            # Check if new quantity exceeds quantity already packed in this package
            record = db(spitable.id == record_id).select(spitable.quantity,
                                                         limitby = (0, 1),
                                                         ).first()
            old_quantity = record.quantity
            if old_quantity >= new_quantity:
                # Quantity reduced or unchanged, no need to re-validate
                return
        else:
            old_quantity = 0

        # Get the track_item quantity
        track_item_id = form_vars.track_item_id
        ttable = db.inv_track_item
        ptable = db.supply_item_pack
        query = (ttable.id == track_item_id) & \
                (ttable.item_pack_id == ptable.id)
        track_item = db(query).select(ttable.quantity,
                                      ptable.name,
                                      limitby = (0, 1),
                                      ).first()
        send_quantity = track_item["inv_track_item.quantity"]

        packed_items = db(spitable.track_item_id == track_item_id).select(spitable.quantity)
        packed_quantity = sum([row.quantity for row in packed_items])

        left_quantity = send_quantity - packed_quantity + old_quantity

        if new_quantity > left_quantity:
            form.errors.quantity = current.T("Only %(quantity)s %(pack)s left to package.") % \
                                        {"quantity": left_quantity,
                                         "pack": track_item["supply_item_pack.name"],
                                         }

    # -------------------------------------------------------------------------
    @staticmethod
    def send_package_items(row):
        """
            Display the Items on the Shipment's Package
        """

        try:
            inv_send_package = getattr(row, "inv_send_package")
        except AttributeError:
            inv_send_package = row

        s3db = current.s3db
        table = s3db.inv_send_package_item
        ttable = s3db.inv_track_item
        itable = s3db.supply_item
        query = (table.send_package_id == inv_send_package.id) & \
                (table.track_item_id == ttable.id) & \
                (ttable.item_id == itable.id)
        rows = current.db(query).select(itable.name)

        len_items = len(rows)
        if len_items == 0:
            return NONE
        elif len_items == 1:
            return rows.first().name
        else:
            len_item = 48 / len_items
            items = [row.name[:] for row in rows]
            return ", ".join(items)

    # -------------------------------------------------------------------------
    @staticmethod
    def send_package_volume(row):
        """
            Display the Volume of the Shipment's Package
            - with capacity
            - in red if over capacity
        """

        try:
            inv_send_package = getattr(row, "inv_send_package")
        except AttributeError:
            inv_send_package = row

        try:
            volume = inv_send_package.volume
        except AttributeError:
            # Need to reload the inv_send_package
            # Avoid this by adding to extra_fields
            table = current.s3db.inv_send_package
            query = (table.id == inv_send_package.id)
            inv_send_package = current.db(query).select(table.id,
                                                        table.volume,
                                                        limitby = (0, 1),
                                                        ).first()
            volume = inv_send_package.volume if inv_send_package else None

        if volume is None:
            return NONE

        volume = round(volume, 3)

        try:
            inv_package = getattr(row, "inv_package")
            max_volume = inv_package.max_volume
        except KeyError:
            # Need to load the inv_package
            # Avoid this by adding to extra_fields
            s3db = current.s3db
            table = s3db.inv_send_package
            ptable = s3db.inv_package
            query = (table.id == inv_send_package.id) & \
                    (table.package_id == ptable.id)
            inv_package = current.db(query).select(ptable.max_volume,
                                                   limitby = (0, 1),
                                                   ).first()
            max_volume = inv_package.max_volume

        if not max_volume:
            return volume

        max_volume = round(max_volume, 3)
        
        if volume > max_volume:
            return SPAN(SPAN(volume,
                             _class = "expired",
                             ),
                        " / %s" % max_volume,
                        )
        elif volume > (0.8 * max_volume):
            return SPAN(SPAN(volume,
                             _class = "expiring",
                             ),
                        " / %s" % max_volume,
                        )
        else:
            return "%s / %s" % (volume,
                                max_volume,
                                )

    # -------------------------------------------------------------------------
    @staticmethod
    def send_package_weight(row):
        """
            Display the Weight of the Shipment's Package
            - with capacity
            - in red if over capacity
        """

        try:
            inv_send_package = getattr(row, "inv_send_package")
        except AttributeError:
            inv_send_package = row

        try:
            weight = inv_send_package.weight
        except AttributeError:
            # Need to reload the inv_send_package
            # Avoid this by adding to extra_fields
            table = current.s3db.inv_send_package
            query = (table.id == inv_send_package.id)
            inv_send_package = current.db(query).select(table.id,
                                                        table.weight,
                                                        limitby = (0, 1),
                                                        ).first()
            weight = inv_send_package.weight if inv_send_package else None

        if weight is None:
            return NONE

        weight = round(weight, 3)

        try:
            inv_package = getattr(row, "inv_package")
            load_capacity = inv_package.load_capacity
        except KeyError:
            # Need to load the inv_package
            # Avoid this by adding to extra_fields
            s3db = current.s3db
            ttable = s3db.inv_send_package
            ptable = s3db.inv_package
            query = (table.id == inv_send_package.id) & \
                    (table.package_id == ptable.id)
            inv_package = current.db(query).select(ptable.load_capacity,
                                                   limitby = (0, 1),
                                                   ).first()
            load_capacity = inv_package.load_capacity

        if not load_capacity:
            return weight

        load_capacity = round(load_capacity, 3)
        
        if weight > load_capacity:
            return SPAN(SPAN(weight,
                             _class = "expired",
                             ),
                        " / %s" % load_capacity,
                        )
        elif weight > (0.8 * load_capacity):
            return SPAN(SPAN(weight,
                             _class = "expiring",
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

        TODO
            crud_form & list_fields for settings.inv.req_project
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
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        AUTOCOMPLETE_HELP = messages.AUTOCOMPLETE_HELP

        add_components = self.add_components
        crud_strings = s3.crud_strings
        super_link = self.super_link

        person_id = self.pr_person_id
        req_status_field = req_status()

        # ---------------------------------------------------------------------
        # Model Options
        #
        ask_security = settings.get_inv_req_ask_security()
        ask_transport = settings.get_inv_req_ask_transport()
        date_writable = settings.get_inv_req_date_writable()
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
                                     updateable = settings.get_inv_requester_site_updateable(),
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
                                represent = s3_options_represent(workflow_opts),
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
        if settings.get_inv_req_filter_by_item_category():
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
                       report_options = {"rows": report_fields,
                                         "cols": report_fields,
                                         "fact": fact_fields,
                                         "methods": ["count", "list", "sum"],
                                         "defaults": {"rows": "site_id$location_id$%s" % levels[0], # Highest-level of hierarchy
                                                      "cols": "priority",
                                                      "fact": "count(id)",
                                                      },
                                         },
                       super_entity = "doc_entity",
                       # Leave this to templates
                       # - reduce load on templates which don't need this
                       #update_realm = True,
                       realm_components = ("req_item",
                                           ),
                       )

        # Components
        add_components(tablename,
                       # Tags
                       inv_req_tag = {"alias": "tag",
                                      "joinby": "req_id",
                                      },
                       # Requested Items
                       inv_req_item = {"joinby": "req_id",
                                       "multiple": settings.get_inv_req_multiple_items(),
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
                if hasattr(status_requires, "other"):
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

            Args:
                row: the deleted inv_req Row
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
            msg_list_empty = T("No Approvers currently registered"),
            )

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
        return None

# =============================================================================
class InventoryRequisitionItemModel(S3Model):
    """
        Model for Inventory Requisition Items
    """

    names = ("inv_req_item",
             "inv_req_item_id",
             "inv_req_item_represent",
             )

    def model(self):

        T = current.T
        db = current.db

        settings = current.deployment_settings
        quantities_writable = settings.get_inv_req_item_quantities_writable()
        prompt_match = settings.get_inv_req_prompt_match()
        use_commit = settings.get_inv_use_commit()
        show_qty_transit = settings.get_inv_req_show_quantity_transit()
        track_pack_values = settings.get_inv_req_pack_values()

        float_represent = IS_FLOAT_AMOUNT.represent

        # -----------------------------------------------------------------
        # Request Items
        #
        tablename = "inv_req_item"
        self.define_table(tablename,
                          self.inv_req_id(empty = False),
                          self.supply_item_entity_id(),
                          self.supply_item_id(),
                          self.supply_item_pack_id(),
                          Field("quantity", "double", notnull=True,
                                label = T("Quantity"),
                                represent = lambda v: \
                                    float_represent(v, precision = 2),
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
                          Field("quantity_reserved", "double",
                                default = 0,
                                label = T("Quantity Reserved"),
                                represent = float_represent,
                                requires = IS_FLOAT_AMOUNT(minimum = 0.0),
                                # Gets enabled in the controller when settings.get_inv_req_reserve_items() and the Item has been Requested From
                                readable = False,
                                writable = False,
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
            msg_list_empty = T("No Items currently requested"),
            )

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

        if prompt_match:
            # Shows the inventory items which match a requested item
            create_next = URL(c="inv", f="req_item",
                              args = ["[id]", "inv_item"],
                              )
        else:
            create_next = None

        list_fields = ["item_id",
                       "item_pack_id",
                       ]
        lappend = list_fields.append
        if prompt_match:
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

        if settings.get_inv_req_filter_by_item_category():
            ondelete = self.req_item_ondelete
        else:
            ondelete = None

        if settings.get_inv_req_reserve_items():
            ondelete_cascade = self.req_item_ondelete_cascade
        else:
            ondelete_cascade = None

        self.configure(tablename,
                       create_next = create_next,
                       deduplicate = self.req_item_duplicate,
                       deletable = settings.get_inv_req_multiple_items(),
                       extra_fields = ["item_pack_id"],
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       onaccept = self.req_item_onaccept,
                       ondelete = ondelete,
                       ondelete_cascade = ondelete_cascade,
                       # @ToDo: default realm to that of the req_id
                       #realm_entity = self.req_item_realm_entity,
                       super_entity = "supply_item_entity",
                       )

        self.add_components(tablename,
                            inv_order_item = "req_item_id",
                            inv_req_item_inv = "req_item_id",
                            )

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
                - if the site requested from changes, then delete any reservations
                    (putting items back into stock)
                - add item category links for the request when adding an item
                  of a new item category

            Note:
                Calling update_realm_entity of the parent Req based on changed
                site_id is left to templates to do in custom onaccept (e.g. see RMS)
        """

        db = current.db
        s3db = current.s3db

        form_vars_get = form.vars.get

        req_id = form_vars_get("req_id")
        if req_id:
            record_id = None
        else:
            # Reload the record to get the req_id
            record_id = form_vars_get("id")
            table = s3db.inv_req_item
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

        settings = current.deployment_settings

        if settings.get_inv_req_reserve_items():
            record = form.record
            if record:
                site_id = record.site_id
                if site_id:
                    new_site_id = form_vars_get("site_id")
                    if not new_site_id:
                        if not record_id:
                            record_id = form_vars_get("id")
                            table = s3db.inv_req_item
                        record = db(table.id == record_id).select(table.site_id,
                                                                  limitby = (0, 1),
                                                                  ).first()
                        new_site_id = record.site_id
                    if new_site_id != site_id:
                        # Remove any old reservations
                        if not record_id:
                            record_id = form_vars_get("id")
                            table = s3db.inv_req_item
                        db(table.id == record_id).update(quantity_reserved = 0)
                        rbtable = s3db.inv_req_item_inv
                        reservations = db(rbtable.req_item_id == record_id).select(rbtable.id,
                                                                                   rbtable.inv_item_id,
                                                                                   rbtable.layout_id,
                                                                                   rbtable.quantity,
                                                                                   )
                        if reservations:
                            iitable = s3db.inv_inv_item
                            ibtable = s3db.inv_inv_item_bin
                            for row in reservations:
                                # Restore Inventory
                                quantity = row.quantity
                                inv_item_id = row.inv_item_id
                                db(iitable.id == inv_item_id).update(quantity = iitable.quantity + quantity)
                                layout_id = row.layout_id
                                if layout_id:
                                    query = (ibtable.inv_item_id == inv_item_id) & \
                                            (ibtable.layout_id == layout_id)
                                    db(query).update(qquantity = ibtable.quantity + quantity)
                            db(rbtable.id.belongs([row.id for row in reservations])).delete()

        if settings.get_inv_req_filter_by_item_category():
            # Update inv_req_item_category link table
            item_id = form_vars_get("item_id")
            if item_id: # Field not present when coming from inv_req_from
                citable = db.supply_catalog_item
                cats = db(citable.item_id == item_id).select(citable.item_category_id)
                rictable = s3db.inv_req_item_category
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

            TODO:
                If a template allows deleting of REQ Items which relate to
                Committed/In-Transit or Fulfilled Requests then the REQ Status
                should be updated accordingly
        """

        db = current.db
        s3db = current.db
        #settings = current.deployment_settings

        record_id = row.id

        #if settings.get_inv_req_filter_by_item_category():
        table = db.inv_req_item

        if hasattr(row, "req_id") and hasattr(row, "item_id"):
            req_id = row.req_id
            item_id = row.item_id
        else:
            # Read from deleted_fk
            # Load record
            record = db(table.id == record_id).select(table.deleted_fk,
                                                      limitby = (0, 1),
                                                      ).first()
    
            deleted_fk = json.loads(record.deleted_fk)
            req_id = deleted_fk.get("req_id")
        item_id = deleted_fk.get("item_id")
    
        if req_id and item_id:
            citable = s3db.supply_catalog_item
            cats = db(citable.item_id == item_id).select(citable.item_category_id)
            for cat in cats:
                item_category_id = cat.item_category_id
                # Check if we have other req_items in the same category
                query = (table.req_id == req_id) & \
                        (table.item_id == sitable.id) & \
                        (sitable.item_category_id == item_category_id)
                others = db(query).select(table.id,
                                          limitby = (0, 1),
                                          ).first()
                if not others:
                    # Delete req_item_category link table
                    rictable = s3db.inv_req_item_category
                    query = (rictable.req_id == req_id) & \
                            (rictable.item_category_id == item_category_id)
                    resource = s3db.resource("inv_req_item_category",
                                             filter = query,
                                             )
                    resource.delete(cascade = True)

    # -------------------------------------------------------------------------
    @staticmethod
    def req_item_ondelete_cascade(row):
        """
            On-delete Cascade actions for requested items:
                - delete any reservations (putting items back into stock)
        """

        db = current.db
        s3db = current.db
        #settings = current.deployment_settings

        record_id = row.id

        #if settings.get_inv_req_reserve_items():
        # Remove any old reservations
        rbtable = s3db.inv_req_item_inv
        reservations = db(rbtable.req_item_id == record_id).select(rbtable.id,
                                                                   rbtable.inv_item_id,
                                                                   rbtable.layout_id,
                                                                   rbtable.quantity,
                                                                   )
        if reservations:
            iitable = s3db.inv_inv_item
            ibtable = s3db.inv_inv_item_bin
            for row in reservations:
                # Restore Inventory
                quantity = row.quantity
                inv_item_id = row.inv_item_id
                db(iitable.id == inv_item_id).update(quantity = iitable.quantity + quantity)
                layout_id = row.layout_id
                if layout_id:
                    query = (ibtable.inv_item_id == inv_item_id) & \
                            (ibtable.layout_id == layout_id)
                    db(query).update(quantity = ibtable.quantity + quantity)
            db(rbtable.id.belongs([row.id for row in reservations])).delete()

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

            Args:
                item: An S3ImportItem object which includes all the details
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
class InventoryRequisitionItemInventoryModel(S3Model):
    """
        Make Inventory Reservations for Request Items
        - used when settings.get_inv_req_reserve_items() == True
    """

    names = ("inv_req_item_inv",
             )

    def model(self):

        T = current.T
        db = current.db

        inv_item_represent = inv_InvItemRepresent(show_bin = False)

        # -----------------------------------------------------------------
        # Request Items <> Inventory for Reserved Items
        #
        tablename = "inv_req_item_inv"
        self.define_table(tablename,
                          self.inv_req_item_id(empty = False),
                          self.inv_item_id(empty = False,
                                           represent = inv_item_represent,
                                           requires = IS_ONE_OF(db, "inv_inv_item.id",
                                                                inv_item_represent,
                                                                orderby = "inv_inv_item.id",
                                                                sort = True,
                                                                ),
                                           ),
                          self.org_site_layout_id(label = T("Bin"),
                                                  ),
                          Field("quantity", "double",
                                default = 0,
                                label = T("Quantity"),
                                represent = IS_FLOAT_AMOUNT.represent,
                                requires = IS_FLOAT_AMOUNT(minimum = 0.0),
                                ),
                          *s3_meta_fields())

        return None

# =============================================================================
class InventoryRequisitionItemCategoryModel(S3Model):
    """
        Link Inventory Requisitions to Item Categories to be able to Filter Requisitions
        - used when settings.get_inv_req_filter_by_item_category() == True
    """

    names = ("inv_req_item_category",
             )

    def model(self):

        # ---------------------------------------------------------------------
        # Req <> Item Category link table
        #
        # - used to provide a search filter
        # - populated onaccept/ondelete of req_item
        #
        tablename = "inv_req_item_category"
        self.define_table(tablename,
                          self.inv_req_id(empty = False),
                          self.supply_item_category_id(),
                          *s3_meta_fields())

        return None

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
        return None

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
            msg_no_match = T("No jobs configured"),
            )

        # Custom Methods
        set_method = self.set_method
        set_method("inv", "req",
                   component_name = "job",
                   method = "reset",
                   action = inv_req_job_reset,
                   )

        set_method("inv", "req",
                   component_name = "job",
                   method = "run",
                   action = inv_req_job_run,
                   )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return None

# =============================================================================
class InventoryRequisitionShipmentModel(S3Model):
    """
        Link Shipments <> Requisitions

        By default, this link is neither a proper RDBMS link, nor M2M,
        but rather a single freetext field containing the req_ref

        Used by:
            RMS
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

        return None

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
        return None

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
                     inv_itn_field()(),
                     self.org_organisation_id("supply_org_id",
                                              label = T("Supplier/Donor"),
                                              ondelete = "SET NULL",
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
                            inv_stock_log = {"name": "log",
                                             "joinby": "card_id",
                                             },
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
                     self.org_site_layout_id(label = T("Bin"),
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

        configure(tablename,
                  # Never created/edited manually
                  deletable = False,
                  editable = False,
                  insertable = False,
                  datatable_includes_id = False,
                  list_fields = ["date",
                                 "send_id",
                                 "send_id$to_site_id",
                                 "recv_id",
                                 "recv_id$from_site_id",
                                 "adj_id",
                                 "layout_id",
                                 "quantity_in",
                                 "quantity_out",
                                 "balance",
                                 "comments",
                                 ],
                  )

        return None

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
        - An audit trail of the shipment process
    """

    names = ("inv_send",
             "inv_send_id",
             "inv_recv",
             "inv_recv_id",
             "inv_track_item",
             "inv_send_item_bin",
             "inv_recv_item_bin",
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
        super_link = self.super_link

        inv_item_id = self.inv_item_id
        organisation_id = self.org_organisation_id
        person_id = self.pr_person_id
        req_ref = self.inv_req_ref

        is_logged_in = auth.is_logged_in
        user = auth.user

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

        SITE_LABEL = settings.get_org_site_label()

        document_filing = settings.get_inv_document_filing()
        recv_shortname = settings.get_inv_recv_shortname()
        show_org = settings.get_inv_send_show_org()
        send_req_ref = settings.get_inv_send_req_ref()
        track_pack_values = settings.get_inv_track_pack_values()
        type_default = settings.get_inv_send_type_default()

        is_float_represent = IS_FLOAT_AMOUNT.represent
        float_represent = lambda v: is_float_represent(v, precision=2)
        string_represent = lambda v: v if v else NONE
        org_site_represent = self.org_site_represent

        send_ref = S3ReusableField("send_ref",
                                   label = T(settings.get_inv_send_ref_field_name()),
                                   represent = self.inv_send_ref_represent,
                                   writable = False,
                                   )

        ship_doc_status = {SHIP_DOC_PENDING  : T("Pending"),
                           SHIP_DOC_COMPLETE : T("Complete"),
                           }
        radio_widget = lambda field, value: \
                              RadioWidget().widget(field, value, cols = 2)

        transport_opts = {"Air": T("Air"),
                          "Sea": T("Sea"),
                          "Road": T("Road"),
                          "Rail": T("Rail"),
                          "Hand": T("Hand"),
                          }

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
                           represent = s3_options_represent(send_type_opts),
                           requires = IS_IN_SET(send_type_opts,
                                                zero = None),
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
                           represent = s3_options_represent(transport_opts),
                           requires = IS_EMPTY_OR(IS_IN_SET(transport_opts)),
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
                           # Label adjusted based on transport_type in controller
                           label = T("Transport Reference"),
                           represent = string_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Transport Reference"),
                                                             T("Air WayBill, Bill of Lading, Consignment Number, Tracking Number, etc"),
                                                             ),
                                         ),
                           ),
                     Field("vehicle",
                           label = T("Vehicle"),
                           represent = string_represent,
                           ),
                     Field("registration_no",
                           label = T("Registration Number"),
                           represent = string_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Registration Number"),
                                                             T("Flight Number, Vheicle Plate Number, Vessel Registration, etc"),
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
                                 ),
                     s3_datetime("date_received",
                                 label = T("Date Received"),
                                 represent = "date",
                                 ),
                     Field("status", "integer",
                           default = SHIP_STATUS_IN_PROCESS,
                           label = T("Status"),
                           represent = s3_options_represent(shipment_status),
                           requires = IS_IN_SET(shipment_status),
                           writable = False,
                           ),
                     Field("filing_status", "integer",
                           default = SHIP_DOC_PENDING,
                           label = T("Filing Status"),
                           represent = s3_options_represent(ship_doc_status),
                           requires = IS_IN_SET(ship_doc_status),
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
                     Field.Method("month",
                                  self.inv_send_month,
                                  ),
                     Field.Method("total_value",
                                  self.inv_send_total_value,
                                  ),
                     Field.Method("total_volume",
                                  self.inv_send_total_volume,
                                  ),
                     Field.Method("transit_time",
                                  self.inv_send_transit_time,
                                  ),
                     *s3_meta_fields())

        # Filter Widgets
        none_selected_comment = T("If none are selected, then all are searched.")

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
            S3OptionsFilter("status",
                            label = T("Status"),
                            comment = none_selected_comment,
                            cols = 3,
                            #options = shipment_status,
                            # Needs to be visible for default_filter to work
                            #hidden = True,
                            ),
            S3OptionsFilter("site_id",
                            label = T("From %(site)s") % {"site": SITE_LABEL},
                            comment = none_selected_comment,
                            cols = 3,
                            hidden = True,
                            ),
            S3OptionsFilter("to_site_id",
                            label = T("To %(site)s") % {"site": SITE_LABEL},
                            comment = none_selected_comment,
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
            title_report = T("Sent Shipments Report"),
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
                       inv_send_package = "send_id",
                       # Requisitions
                       inv_send_req = "send_id",
                       inv_req = {"link": "inv_send_req",
                                  "joinby": "send_id",
                                  "key": "req_id",
                                  "actuate": "hide",
                                  },
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
                       "registration_no",
                       "time_out",
                       "comments",
                       ]

        WB = settings.get_inv_send_form_name()

        configure(tablename,
                  addbtn = True,
                  listadd = False,
                  create_next = send_item_url,
                  update_next = send_item_url,
                  # It shouldn't be possible for the user to delete a shipment
                  # unless *maybe* if it is pending and has no items referencing it
                  deletable = False,
                  extra_fields = ["date",
                                  "date_received",
                                  ],
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  onaccept = inv_send_onaccept,
                  onvalidation = self.inv_send_onvalidation,
                  orderby = "inv_send.date desc",
                  report_options = {"rows": ["track_item.item_id",
                                             "site_id",
                                             "to_site_id",
                                             (T("Month"), "month"),
                                             "transport_type",
                                             (T("Volume (kg)"), "total_volume"),
                                             (T("Value"), "total_value"),
                                             (WB, "send_ref"),
                                             ],
                                    "cols": ["track_item.item_id",
                                             "site_id",
                                             "to_site_id",
                                             (T("Month"), "month"),
                                             "transport_type",
                                             (T("Volume (kg)"), "total_volume"),
                                             (T("Value"), "total_value"),
                                             (WB, "send_ref"),
                                             ],
                                    "fact": [(T("Average Transit Time (h)"), "avg(transit_time)"),
                                             (T("Item Quantity"), "sum(track_item.quantity)"),
                                             (T("List of Shipments"), "list(send_ref)"),
                                             (T("Number of Shipments"), "count(id)"),
                                             (T("Total Value of Shipments"), "sum(total_value)"),
                                             (T("Total Volume of Shipments (kg)"), "sum(total_volume)"),
                                             ],
                                    "defaults": {"rows": "month",
                                                 "cols": "site_id",
                                                 "fact": "count(id)",
                                                 "chart": "barchart:rows",
                                                 "table": "collapse",
                                                 },
                                    },
                  sortby = [[5, "desc"], [1, "asc"]],
                  super_entity = ("doc_entity",),
                  wizard = inv_SendWizard(),
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
                     Field("recv_ref",
                           label = T("%(GRN)s Number") % {"GRN": recv_shortname},
                           represent = self.inv_recv_ref_represent,
                           writable = False,
                           ),
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
                           represent = s3_options_represent(recv_type_opts),
                           requires = IS_IN_SET(recv_type_opts,
                                                zero = None),
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
                               comment = self.pr_person_comment(child = "recipient_id"),
                               ),
                     Field("transport_type",
                           label = T("Type of Transport"),
                           represent = s3_options_represent(transport_opts),
                           requires = IS_EMPTY_OR(IS_IN_SET(transport_opts)),
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
                           # Label adjusted based on transport_type in controller
                           label = T("Transport Reference"),
                           represent = string_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Transport Reference"),
                                                             T("Air WayBill, Bill of Lading, Consignment Number, Tracking Number, etc"),
                                                             ),
                                         ),
                           ),
                     Field("registration_no",
                           label = T("Registration Number"),
                           represent = string_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Registration Number"),
                                                             T("Flight Number, Vheicle Plate Number, Vessel Registration, etc"),
                                                             ),
                                         ),
                           ),
                     Field("status", "integer",
                           default = SHIP_STATUS_IN_PROCESS,
                           label = T("Status"),
                           represent = s3_options_represent(shipment_status),
                           requires = IS_IN_SET(shipment_status,
                                                zero = None),
                           writable = False,
                           ),
                     Field("grn_status", "integer",
                           default = SHIP_DOC_PENDING,
                           label = T("%(GRN)s Status") % {"GRN": recv_shortname},
                           represent = s3_options_represent(ship_doc_status),
                           requires = IS_IN_SET(ship_doc_status,
                                                zero = None),
                           widget = radio_widget,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("%(GRN)s Status") % {"GRN": recv_shortname},
                                                             T("Has the %(GRN)s (%(GRN_name)s) form been completed?") % \
                                                                {"GRN": recv_shortname,
                                                                 "GRN_name": settings.get_inv_recv_form_name(),
                                                                 },
                                                             ),
                                         ),
                           ),
                     Field("cert_status", "integer",
                           default = SHIP_DOC_PENDING,
                           label = T("Certificate Status"),
                           represent = s3_options_represent(ship_doc_status),
                           requires = IS_IN_SET(ship_doc_status,
                                                zero = None),
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
                           represent = s3_options_represent(ship_doc_status),
                           requires = IS_IN_SET(ship_doc_status,
                                                zero = None),
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
            S3OptionsFilter("status",
                            label = T("Status"),
                            comment = none_selected_comment,
                            cols = 3,
                            #options = shipment_status,
                            # Needs to be visible for default_filter to work
                            #hidden = True,
                            ),
            S3OptionsFilter("site_id",
                            label = T("To %(site)s") % {"site": SITE_LABEL},
                            comment = none_selected_comment,
                            cols = 3,
                            hidden = True,
                            ),
            S3OptionsFilter("from_site_id",
                            label = T("From %(site)s") % {"site": SITE_LABEL},
                            comment = none_selected_comment,
                            hidden = True,
                            ),
            S3DateFilter(recv_search_date_field,
                         comment = recv_search_date_comment,
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
                  addbtn = True,
                  listadd = False,
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
                  wizard = inv_RecvWizard(),
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

        # ---------------------------------------------------------------------
        # Track Items
        #
        # - Items in both Sent & Received Shipments
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
# We use s3.inv_send_item.js instead
#                                 script = '''
#$.filterOptionsS3({
# 'trigger':'send_inv_item_id',
# 'target':'item_pack_id',
# 'lookupResource':'item_pack',
# 'lookupPrefix':'supply',
# 'lookupURL':S3.Ap.concat('/inv/inv_item_packs.json/'),
# 'msgNoRecords':i18n.no_packs,
# 'fncPrep':S3.supply.fncPrepItem,
# 'fncRepresent':S3.supply.fncRepresentItem
#})''',
                                 ),
                     self.supply_item_id(ondelete = "RESTRICT"),
                     self.supply_item_pack_id(# We replace filterOptionsS3
                                              script = None,
                                              ),
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
                           readable = track_pack_values,
                           writable = track_pack_values,
                           ),
                     s3_currency(readable = track_pack_values,
                                 writable = track_pack_values,
                                 ),
                     s3_date("expiry_date",
                             label = T("Expiry Date"),
                             represent = inv_expiry_date_represent,
                             ),
                     inv_item_id("recv_inv_item_id",
                                 label = T("Receiving Inventory"),
                                 ondelete = "RESTRICT",
                                 #represent = inv_item_represent,
                                 required = False,
                                 readable = False,
                                 writable = False,
                                 ),
                     inv_itn_field()(),
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
                           represent = s3_options_represent(inv_item_status_opts),
                           requires = IS_IN_SET(inv_item_status_opts,
                                                zero = None),
                           ),
                     Field("status", "integer",
                           default = TRACK_STATUS_PREPARING, # 1
                           label = T("Item Tracking Status"),
                           represent = s3_options_represent(tracking_status),
                           required = True,
                           requires = IS_IN_SET(tracking_status),
                           writable = False,
                           ),
                     self.inv_adj_item_id(ondelete = "RESTRICT"), # any adjustment record
                     # send record
                     send_id(),
                     # receive record
                     recv_id(),
                     self.inv_req_item_id(readable = False,
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
                  # Configured in the Controller to adapt to requirements
                  #list_fields = list_fields,
                  # Now done in crud_form.postprocess
                  #onaccept = inv_track_item_onaccept,
                  onvalidation = self.inv_track_item_onvalidation,
                  )

        # Components
        add_components(tablename,
                       inv_send_item_bin = {"name": "send_bin",
                                            "joinby": "track_item_id",
                                            },
                       inv_recv_item_bin = {"name": "recv_bin",
                                            "joinby": "track_item_id",
                                            },
                       )

        track_item_id = S3ReusableField("track_item_id", "reference inv_track_item",
                                        ondelete = "CASCADE",
                                        )

        # ---------------------------------------------------------------------
        # Send Items <> Bins
        #
        #  Can't just use Inventory Item Bins as we need to be able to make
        #  draft changes which aren't committed until the shipment is sent.
        #
        layout_id = self.org_site_layout_id

        tablename = "inv_send_item_bin"
        define_table(tablename,
                     track_item_id(),
                     layout_id(label = T("Bin"),
                               empty = False,
                               # This has the URL adjusted for the right site_id
                               comment = S3PopupLink(c = "org",
                                                     f = "site",
                                                     args = ["[id]", "layout", "create"],
                                                     vars = {"child": "layout_id",
                                                             # @ToDo: Restrict to site_id to reduce risk of race condition
                                                             #"optionsVar": "site_id",
                                                             #"optionsValue": "[id]",
                                                             },
                                                     label = T("Create Bin"),
                                                     title = T("Bin"),
                                                     tooltip = T("If you don't see the Bin listed, you can add a new one by clicking link 'Create Bin'."),
                                                     _id = "inv_send_item_bin_layout_id-create-btn",
                                                     ),
                                 ),
                     Field("quantity", "double", notnull=True,
                           default = 0,
                           label = T("Quantity"),
                           represent = float_represent,
                           ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Recv Items <> Bins
        #
        tablename = "inv_recv_item_bin"
        define_table(tablename,
                     track_item_id(),
                     layout_id(label = T("Bin"),
                               empty = False,
                               # This has the URL adjusted for the right site_id in the controller
                               comment = S3PopupLink(c = "org",
                                                     f = "site",
                                                     args = ["[id]", "layout", "create"],
                                                     vars = {"child": "layout_id",
                                                             # @ToDo: Restrict to site_id to reduce risk of race condition
                                                             #"optionsVar": "site_id",
                                                             #"optionsValue": "[id]",
                                                             },
                                                     label = T("Create Bin"),
                                                     title = T("Bin"),
                                                     tooltip = T("If you don't see the Bin listed, you can add a new one by clicking link 'Create Bin'."),
                                                     _id = "inv_recv_item_bin_layout_id-create-btn",
                                                     ),
                                 ),
                     Field("quantity", "double", notnull=True,
                           default = 0,
                           label = T("Quantity"),
                           represent = float_represent,
                           ),
                     *s3_meta_fields())

        #----------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"inv_recv_id": recv_id,
                "inv_send_id": send_id,
                }

    # Only used internally
    # -------------------------------------------------------------------------
    #def defaults(self):
    #    """
    #        Safe defaults for model-global names in case module is disabled
    #    """

    #    dummy = S3ReusableField.dummy

    #    return {"inv_recv_id": dummy("recv_id"),
    #            "inv_send_id": dummy("send_id"),
    #            }

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_send_month(row):
        """
            Abbreviated string format for date, allows grouping per month,
            instead of the individual datetime, used for inv_send report.

            Requires "date" to be in the extra_fields

            Args:
                row: the Row
        """

        try:
            inv_send = getattr(row, "inv_send")
        except AttributeError:
            inv_send = row

        try:
            thisdate = inv_send.date
        except AttributeError:
            return NONE
        if not thisdate:
            return NONE

        return thisdate.date().strftime("%y-%m")

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_send_total_value(row):
        """
            Total value of a sent shipment

            Note:
                This only makes sense if all items use the same currency for their values!
        """

        try:
            inv_send = getattr(row, "inv_send")
        except AttributeError:
            inv_send = row

        ttable = current.s3db.inv_track_item
        rows = current.db(ttable.send_id == inv_send.id).select(ttable.quantity,
                                                                ttable.pack_value,
                                                                )
        total_value = 0
        for row in rows:
            pack_value = row.pack_value
            quantity = row.quantity
            if quantity and pack_value:
                total_value += (quantity * pack_value)

        return round(total_value, 2)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_send_total_volume(row):
        """
            Total volume of a sent shipment
        """

        try:
            inv_send = getattr(row, "inv_send")
        except AttributeError:
            inv_send = row

        s3db = current.s3db
        ttable = s3db.inv_track_item
        ptable = s3db.supply_item_pack
        itable = s3db.supply_item
        query = (ttable.send_id == inv_send.id) & \
                (ttable.item_pack_id == ptable.id) & \
                (ttable.item_id == itable.id)
        rows = current.db(query).select(ttable.quantity,
                                        ptable.quantity,
                                        itable.volume,
                                        )
        total_volume = 0
        for row in rows:
            quantity = row["inv_track_item.quantity"]
            volume = row["supply_item.volume"]
            if quantity and volume:
                pack_quantity = row["supply_item_pack.quantity"]
                total_volume += (quantity * pack_quantity * volume)

        return round(total_volume, 3)

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_send_transit_time(row):
        """
            Time in transit of a sent shipment (in Hours)
        """

        try:
            inv_send = getattr(row, "inv_send")
        except AttributeError:
            inv_send = row

        try:
            date = inv_send.date
            date_received = inv_send.date_received
        except AttributeError:
            # Need to reload the send
            # Avoid this by adding to extra_fields
            stable = current.s3db.inv_send
            inv_send = current.db(stable.id == inv_send.id).select(stable.date,
                                                                   stable.date_received,
                                                                   limitby = (0, 1),
                                                                   ).first()
            date = inv_send.date
            date_received = inv_send.date_received

        if date and date_received:
            delta = date_received - date
            return round(delta.hours, 1)
        else:
            # Item lacks date, or date_received, or both
            return NONE

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
            inv_track_item = current.db(ttable.id == inv_track_item.id).select(ttable.quantity,
                                                                               ttable.pack_value,
                                                                               limitby = (0, 1),
                                                                               ).first()
            quantity = inv_track_item.quantity
            pack_value = inv_track_item.pack_value

        if quantity and pack_value:
            return round(quantity * pack_value, 2)
        else:
            # Item lacks quantity, or value per pack, or both
            return NONE

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
            return NONE

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
            return NONE

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
            return NONE

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
            return NONE

    # -------------------------------------------------------------------------
    @staticmethod
    def inv_track_item_onvalidation(form):
        """
            When a track item record is being created with a tracking number
            then the tracking number needs to be unique within the organisation.

            If the inv. item is coming out of a warehouse then the inv. item details
            need to be copied across (org, expiry etc)
        """

        form_vars = form.vars
        send_inv_item_id = form_vars.send_inv_item_id

        if send_inv_item_id:
            db = current.db
            iitable = db.inv_inv_item
            query = (iitable.id == send_inv_item_id)

            # Validate that the Quantity to be added is available in Stock
            valid_quantity = False

            iptable = db.supply_item_pack
            new_pack_id = form_vars.item_pack_id
            new_pack_quantity = db(iptable.id == new_pack_id).select(iptable.quantity,
                                                                     limitby = (0, 1),
                                                                     ).first().quantity
            new_quantity = float(form_vars.quantity) * new_pack_quantity

            record_id = form.record_id
            if record_id:
                # Check if new quantity exceeds quantity already tracked
                ttable = db.inv_track_item
                record = db(ttable.id == record_id).select(ttable.quantity,
                                                           ttable.item_pack_id,
                                                           limitby = (0, 1),
                                                           ).first()
                old_quantity = record.quantity
                old_pack_id = record.item_pack_id
                if old_pack_id != new_pack_id:
                    # Convert to units
                    old_pack_quantity = db(iptable.id == old_pack_id).select(iptable.quantity,
                                                                             limitby = (0, 1),
                                                                             ).first().quantity
                    old_quantity = old_quantity * old_pack_quantity
                else:
                    old_quantity = old_quantity * new_pack_quantity
                if old_quantity >= new_quantity:
                    # Quantity reduced or unchanged, no need to re-validate
                    valid_quantity = True
            else:
                old_quantity = 0

            if not valid_quantity:
                # Get the inventory item quantity & pack
                inv_item = db(query & (iitable.item_pack_id == iptable.id)).select(iitable.quantity,
                                                                                   iptable.quantity,
                                                                                   iptable.name,
                                                                                   limitby = (0, 1),
                                                                                   ).first()
                inv_item_pack = inv_item.supply_item_pack
                inv_pack_quantity = inv_item_pack.quantity
                inv_quantity = (inv_item["inv_inv_item.quantity"] * inv_pack_quantity) + old_quantity

                if new_quantity > inv_quantity:
                    form.errors.quantity = current.T("Only %(quantity)s %(pack)s in the Warehouse Stock.") % \
                                                {"quantity": inv_quantity,
                                                 "pack": inv_item_pack.name,
                                                 }
                    # Nothing else to validate
                    return

            # Copy the data from the sent inv_item
            inv_item = db(query).select(iitable.item_id,
                                        iitable.item_source_no,
                                        iitable.expiry_date,
                                        iitable.owner_org_id,
                                        iitable.supply_org_id,
                                        iitable.pack_value,
                                        iitable.currency,
                                        iitable.status,
                                        limitby = (0, 1),
                                        ).first()
            form_vars.item_id = inv_item.item_id
            form_vars.item_source_no = inv_item.item_source_no
            form_vars.expiry_date = inv_item.expiry_date
            form_vars.owner_org_id = inv_item.owner_org_id
            form_vars.supply_org_id = inv_item.supply_org_id
            form_vars.pack_value = inv_item.pack_value
            form_vars.currency = inv_item.currency
            form_vars.inv_item_status = inv_item.status

            # Save the organisation from where this tracking originates
            stable = current.s3db.org_site
            site = db(query & (iitable.site_id == stable.id)).select(stable.organisation_id,
                                                                     limitby = (0, 1),
                                                                     ).first()
            form_vars.track_org_id = site.organisation_id

        if not form_vars.recv_quantity and "quantity" in form_vars:
            # If we have no send_id and no recv_quantity then
            # copy the quantity sent directly into the received field
            # This is for when there is no related send record
            # The Quantity received ALWAYS defaults to the quantity sent
            # (Please do not change this unless there is a specific user requirement)
            #db.inv_track_item.recv_quantity.default = form_vars.quantity
            form_vars.recv_quantity = form_vars.quantity

# =============================================================================
def inv_adj_close(r, **attr):
    """ 
        Close an Adjustment
        - called via POST from inv_send_rheader
        - called via JSON method to reduce request overheads
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    adj_id = r.id

    if not adj_id:
        r.error(405, "Can only close a single adjustment")

    auth = current.auth
    s3db = current.s3db
    atable = s3db.inv_adj

    if not auth.s3_has_permission("update", atable,
                                  record_id = adj_id,
                                  ):
        r.unauthorised()

    T = current.T

    record = r.record

    if record.status != 0:
        error = T("This adjustment has already been closed.")
        current.session.error = error
        r.error(409, error,
                tree = '"%s"' % URL(args = [adj_id]),
                )

    db = current.db

    site_id = record.site_id

    adj_bin_table = s3db.inv_adj_item_bin
    adj_item_table = s3db.inv_adj_item
    inv_bin_table = s3db.inv_inv_item_bin
    inv_item_table = s3db.inv_inv_item

    # Go through all the adj_items
    left = adj_bin_table.on(adj_bin_table.adj_item_id == adj_item_table.id)
    rows = db(adj_item_table.adj_id == adj_id).select(adj_item_table.id,
                                                      adj_item_table.inv_item_id,
                                                      adj_item_table.item_id,
                                                      adj_item_table.item_pack_id,
                                                      adj_item_table.currency,
                                                      adj_item_table.old_pack_value,
                                                      adj_item_table.expiry_date,
                                                      adj_item_table.new_quantity,
                                                      adj_item_table.old_owner_org_id,
                                                      adj_item_table.new_owner_org_id,
                                                      adj_item_table.new_status,
                                                      adj_bin_table.layout_id,
                                                      adj_bin_table.quantity,
                                                      left = left,
                                                      )

    # Group by adj_item_id & collect inv_item_ids for bulk lookup of bins
    adj_items = {}
    inv_item_ids = []
    iiappend = inv_item_ids.append
    for row in rows:
        adj_item = row.inv_adj_item
        inv_item_id = adj_item.inv_item_id
        if inv_item_id:
            iiappend(inv_item_id)
        adj_item_id = adj_item.id
        if adj_item_id in adj_items:
            adj_items[adj_item_id].append(row)
        else:
            adj_items[adj_item_id] = [row]

    inv_item_ids = set(inv_item_ids)

    # Bulk Lookup all existing Inv Bins
    rows = db(inv_bin_table.inv_item_id.belongs(inv_item_ids)).select(inv_bin_table.id,
                                                                      inv_bin_table.inv_item_id,
                                                                      inv_bin_table.layout_id,
                                                                      )
    # Group by inv_item_id
    inv_bins = {}
    for row in rows:
        inv_item_id = row.inv_item_id
        if inv_item_id in inv_bins:
            inv_bins[inv_item_id].append(row)
        else:
            inv_bins[inv_item_id] = [row]

    get_realm_entity = auth.get_realm_entity

    for adj_item_id in adj_items:
        bins = adj_items[adj_item_id]
        adj_item = bins[0].inv_adj_item
        if adj_item.inv_item_id is None:
            # Create a new stock item
            inv_item = {"site_id": site_id,
                        "item_id": adj_item.item_id,
                        "item_pack_id": adj_item.item_pack_id,
                        "currency": adj_item.currency,
                        "pack_value": adj_item.old_pack_value,
                        "expiry_date": adj_item.expiry_date,
                        "quantity": adj_item.new_quantity,
                        "owner_org_id": adj_item.old_owner_org_id,
                        }
            inv_item_id = inv_item_table.insert(**inv_item)

            # Add the Bins
            for row in bins:
                row = row.inv_adj_item_bin
                layout_id = row.layout_id
                if layout_id:
                    inv_bin_table.insert(inv_item_id = inv_item_id,
                                         layout_id = layout_id,
                                         quantity = row.quantity,
                                         )

            # Apply the realm entity
            inv_item["id"] = inv_item_id
            realm_entity = get_realm_entity(inv_item_table, inv_item)
            db(inv_item_table.id == inv_item_id).update(realm_entity = realm_entity)

            # Add the inventory item id to the adjustment record
            db(adj_item_table.id == adj_item.id).update(inv_item_id = inv_item_id)

        elif adj_item.new_quantity is not None:
            # Update the existing stock item
            inv_item_id = adj_item.inv_item_id
            db(inv_item_table.id == inv_item_id).update(item_pack_id = adj_item.item_pack_id,
                                                        pack_value = adj_item.old_pack_value,
                                                        expiry_date = adj_item.expiry_date,
                                                        quantity = adj_item.new_quantity,
                                                        owner_org_id = adj_item.new_owner_org_id,
                                                        status = adj_item.new_status,
                                                        )
            # Update the Bins
            old_bins = inv_bins[inv_item_id]
            new_layout_ids = [row["inv_adj_item_bin.layout_id"] for row in bins]

            bins_to_delete = {}
            bins_to_update = {}
            for row in old_bins:
                layout_id = row.layout_id
                if layout_id in new_layout_ids:
                    bins_to_update[layout_id] = row.id
                else:
                    bins_to_delete[layout_id] = row.id

            for row in bins:
                bin_record = row.inv_adj_item_bin
                layout_id = bin_record.layout_id
                if not layout_id:
                    continue
                if layout_id in bins_to_update:
                    # Update link
                    db(inv_bin_table.id == bins_to_update[layout_id]).update(quantity = bin_record.quantity)
                else:
                    # Create new link
                    inv_bin_table.insert(inv_item_id = inv_item_id,
                                         layout_id = layout_id,
                                         quantity = bin_record.quantity,
                                         )

            for layout_id in bins_to_delete:
                # Remove link
                db(inv_bin_table.id == bins_to_delete[layout_id]).delete()

    # Change the status of the adj record to Complete
    db(atable.id == adj_id).update(status = 1)

    settings = current.deployment_settings

    # Go to the Inventory of the Site which has adjusted these items
    (prefix, resourcename, instance_id) = s3db.get_instance(s3db.org_site,
                                                            site_id)
    if resourcename == "warehouse" and \
       settings.get_inv_warehouse_free_capacity_calculated():
        # Update the Free Capacity for this Warehouse
        inv_warehouse_free_capacity(site_id)

    if settings.get_inv_stock_cards():
        inv_stock_card_update(list(inv_item_ids),
                              comments = "Adjustment",
                              )

    # Call on_inv_adj_close hook if-configured
    #tablename = "inv_adj"
    #on_inv_adj_close = s3db.get_config(tablename, "on_inv_adj_close")
    #if on_inv_adj_close:
    #    adj_record.id = adj_id
    #    on_inv_adj_close(adj_record)

    message = T("Adjustment Closed")
    current.session.confirmation = message

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": URL(c = prefix,
                                   f = resourcename,
                                   args = [instance_id, "inv_item"],
                                   ),
                       }, separators=SEPARATORS)

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
                                                  record_id = record.id,
                                                  ):
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
                                  _id = "adj-close",
                                  _class = "action-btn",
                                  )
                    # Handle Confirmation
                    # Switch to POST
                    s3 = current.response.s3
                    if s3.debug:
                        s3.scripts.append("/%s/static/scripts/S3/s3.inv_adj_rheader.js" % r.application)
                    else:
                        s3.scripts.append("/%s/static/scripts/S3/s3.inv_adj_rheader.min.js" % r.application)
                    s3.js_global.append('''i18n.adj_close_confirm="%s"''' % \
                            T("Do you want to complete & close this adjustment?"))
                    rheader.append(close_btn)

            rheader.append(rheader_tabs)

                    # else:
                        # msg = T("You need to check all the revised quantities before you can close this adjustment")
                        # rfooter.append(SPAN(msg))

            return rheader
    return None

# =============================================================================
def inv_commit_all(r, **attr):
    """
        Custom Method to commit to a Request
            - creates a commit with commit_items for each req_item
        - called via POST from inv_send_rheader
        - called via JSON method to reduce request overheads
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    T = current.T

    req_id = r.id

    if not req_id:
        r.error(405, "Can only commit to a single request")

    auth = current.auth
    s3db = current.s3db
    table = s3db.inv_commit

    if not auth.s3_has_permission("create", table):
        r.unauthorised()

    db = current.db

    record = r.record

    # Check if there is an existing Commitment
    exists = db(table.req_id == req_id).select(table.id,
                                               limitby = (0, 1),
                                               ).first()
    if exists:
        # Browse existing commitments
        error = T("Some items have already been committed")
        current.session.error = error
        r.error(409, error,
                tree = '"%s"' % URL(args = [req_id, "commit"]),
                )

    # Create the commitment
    cid = table.insert(req_id = req_id)

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

    if "send" in r.args:
        message = ""
        url = URL(f = "commit",
                  args = [cid, "send"],
                  )

    elif "assign" in r.args:
        message = ""
        url = URL(f = "commit",
                  args = [cid, "assign"],
                  )
    else:
        message = T("You have committed to all items in this Request. Please check that all details are correct and update as-required.")
        current.session.confirmation = message
        url = URL(c = "inv",
                  f = "commit",
                  args = [cid],
                  )

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": url,
                       }, separators=SEPARATORS)

# =============================================================================
def inv_commit_send(r, **attr):
    """
        Create a Shipment containing all Items in a Commitment
        - called via POST from inv_send_rheader
        - called via JSON method to reduce request overheads

        @ToDo: inv_commit_all
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    T = current.T

    commit_id = r.id

    if not commit_id:
        r.error(405, "Can only create a shipment from a single commit.",
                tree = URL(),
                )

    s3db = current.s3db

    stable = s3db.inv_send

    if not current.auth.s3_has_permission("create", stable):
        r.unauthorised()

    record = r.record
    req_id = record.req_id

    db = current.db

    req_table = db.inv_req
    rim_table = db.inv_req_item
    com_table = db.inv_commit
    cim_table = db.inv_commit_item


    req_record = db(req_table.id == req_id).select(req_table.requester_id,
                                                   req_table.site_id,
                                                   #req_table.req_ref, # Only used for External Requests
                                                   limitby = (0, 1),
                                                   ).first()

    # @ToDo: Identify if we have stock items which match the commit items
    # If we have a single match per item then proceed automatically (as-now) & then decrement the stock quantity
    # If we have no match then warn the user & ask if they should proceed anyway
    # If we have mulitple matches then provide a UI to allow the user to select which stock items to use

    # Create an inv_send and link to the commit
    form_vars = Storage(sender_id = record.committer_id,
                        site_id = record.site_id,
                        recipient_id = req_record.requester_id,
                        to_site_id = req_record.site_id,
                        #req_ref = req_record.req_ref,
                        status = 0,
                        )
    send_id = stable.insert(**form_vars)
    form_vars.id = send_id
    inv_send_onaccept(Storage(vars = form_vars))

    s3db.inv_send_req.insert(send_id = send_id,
                             req_id = req_id,
                             )

    # Get all of the committed items
    query = (cim_table.commit_id == commit_id) & \
            (cim_table.req_item_id == rim_table.id)
    rows = db(query).select(rim_table.id,
                            rim_table.item_id,
                            rim_table.item_pack_id,
                            rim_table.currency,
                            rim_table.quantity,
                            rim_table.quantity_transit,
                            rim_table.quantity_fulfil,
                            cim_table.quantity,
                            )
    # Create inv_track_items for each commit item
    track_org_id = record.organisation_id
    insert = s3db.inv_track_item.insert
    for row in rows:
        rim = row.inv_req_item
        # Now done as a VirtualField instead (looks better & updates closer to real-time, so less of a race condition)
        #quantity_shipped = max(rim.quantity_transit, rim.quantity_fulfil)
        #quantity_needed = rim.quantity - quantity_shipped
        insert(req_item_id = rim.id,
               track_org_id = organisation_id,
               send_id = send_id,
               status = 1,
               item_id = rim.item_id,
               item_pack_id = rim.item_pack_id,
               currency = rim.currency,
               #req_quantity = quantity_needed,
               quantity = row.inv_commit_item.quantity,
               recv_quantity = row.inv_commit_item.quantity,
               )

    message = T("Shipment created")
    current.session.confirmation = message

    # Redirect to inv_send for the send id just created
    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": URL(c = "inv",
                                   f = "send",
                                   args = [send_id],
                                   ),
                       }, separators=SEPARATORS)

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
    site_id = record.site_id
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
    location = db(query).select(gtable.id,
                                gtable.L0,
                                limitby = (0, 1),
                                ).first()
    country = location.L0
    fr = "fr" in current.deployment_settings.get_L10n_languages_by_country(country)

    # Organisations
    otable = s3db.org_organisation
    query = (stable.site_id.belongs((to_site_id, site_id))) & \
            (stable.organisation_id == otable.id)
    fields = [stable.site_id,
              otable.id,
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
    orgs = db(query).select(*fields,
                            left = left,
                            limitby = (0, 2)
                            )
    for row in orgs:
        if row["org_site.site_id"] == site_id:
            # Sender Org
            if fr:
                org_name = row["org_organisation_name.name_l10n"]
                org = row["org_organisation"]
                if not org_name:
                    org_name = org.name
            else:
                org = row["org_organisation"]
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
        else:
            # Recipient Org
            if fr:
                dest_org_name = row["org_organisation_name.name_l10n"]
                dest_org = row["org_organisation"]
                if not dest_org_name:
                    dest_org_name = dest_org.name
            else:
                dest_org = row["org_organisation"]
                dest_org_name = dest_org.name
            if dest_org.id != dest_org.root_organisation:
                # Lookup Root Org
                fields = [otable.name,
                          ]
                if fr:
                    fields.append(ontable.name_l10n)
                dest_org = db(otable.id == dest_org.root_organisation).select(*fields,
                                                                              left = left,
                                                                              limitby = (0, 1)
                                                                              ).first()
                if fr:
                    dest_org_name = dest_org["org_organisation_name.name_l10n"]
                    dest_org = dest_org["org_organisation"]
                    if not dest_org_name:
                        dest_org_name = dest_org.name
                else:
                    dest_org_name = dest_org.name

    # Represent the Data
    from .org import org_SiteRepresent
    destination = org_SiteRepresent(show_type = False)(to_site_id)

    from .gis import gis_LocationRepresent
    address = gis_LocationRepresent(show_level = False)(location.id)

    recipient_id = record.recipient_id
    if recipient_id:
        from .pr import pr_PersonRepresent
        recipient = pr_PersonRepresent(truncate = False)(recipient_id)
    else:
        recipient = None

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

    # Define styles
    POINT_12 = 240 # Twips = Points * 20
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
    if destination in address:
        label = "%s\n%s" % (dest_org_name.upper(), address)
    else:
        label = "%s\n%s\n%s" % (dest_org_name.upper(), destination, address)
    if recipient:
        label = "%s\n%s" % (label, recipient)
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
    currency = ""
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
        current_row.write(0, "Received by:", style)

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
def inv_item_label(r, **attr):
    """
        Generate a Label for a Shipment Item
        - can be used to label items as they are stored in the warehouse
        - can be used to label items as they are added to outbound packages

        This is exported in XLS format to be user-editable
        - we don't have the width x length x height (we don't currently store these for packs)
    """

    from s3.codecs.xls import S3XLS

    try:
        import xlwt
    except ImportError:
        r.error(503, S3XLS.ERROR.XLWT_ERROR)

    # Extract the Data
    db = current.db
    s3db = current.s3db

    # Item Details
    ttable = s3db.inv_track_item
    itable = s3db.supply_item
    ptable = s3db.supply_item_pack
    query = (ttable.id == r.component_id) & \
            (ttable.item_id == itable.id) & \
            (ttable.item_pack_id == ptable.id)
    item = db(query).select(ttable.expiry_date,
                            ttable.supply_org_id,
                            itable.code,
                            itable.name,
                            itable.weight,
                            ptable.name,
                            ptable.quantity,
                            limitby = (0, 1),
                            ).first()

    pack = item["supply_item_pack"]
    track_item = item["inv_track_item"]
    supply_item = item["supply_item"]
    item_code = supply_item.code or ""
    item_name = supply_item.name[:24]
    pack_quantity = pack.quantity

    weight = supply_item.weight
    if weight:
        weight = weight * pack_quantity
    else:
        weight = ""

    # Length & Width are unknown as we don't track pack sizes
    length = ""
    width = ""
    height = ""

    # Organisation
    otable = s3db.org_organisation
    stable = s3db.org_site
    query = (stable.site_id == r.record.site_id) & \
            (stable.organisation_id == otable.id)
    org = db(query).select(otable.id,
                           otable.root_organisation,
                           otable.logo,
                           limitby = (0, 1)
                           ).first()

    if org.id != org.root_organisation:
        # Lookup Root Org
        org = db(otable.id == org.root_organisation).select(otable.logo,
                                                            limitby = (0, 1)
                                                            ).first()

    # Represent the Data
    T = current.T

    from .org import org_OrganisationRepresent
    org_represent = org_OrganisationRepresent(acronym = False,
                                              parent = False,
                                              )

    # Create the workbook
    book = xlwt.Workbook(encoding = "utf-8")

    # Define styles
    POINT_36 = 720 # Twips = Points * 20
    ROW_HEIGHT = 890 # Realised through trial & error

    style = xlwt.XFStyle()
    style.font.height = POINT_36

    HORZ_CENTER = style.alignment.HORZ_CENTER
    VERT_CENTER = style.alignment.VERT_CENTER

    bold_style = xlwt.XFStyle()
    bold_style.font.bold = True
    bold_style.font.height = POINT_36
    bold_style.borders.top = style.borders.THICK

    center_style = xlwt.XFStyle()
    center_style.alignment.horz = style.alignment.HORZ_CENTER
    center_style.font.height = POINT_36

    right_style = xlwt.XFStyle()
    right_style.alignment.horz = style.alignment.HORZ_RIGHT
    right_style.font.height = POINT_36

    big_box_style = xlwt.XFStyle()
    big_box_style.font.bold = True
    big_box_style.font.height = 1120 # 1120 Twips = 56 point
    big_box_style.alignment.horz = HORZ_CENTER
    big_box_style.alignment.vert = VERT_CENTER

    box_style = xlwt.XFStyle()
    box_style.font.height = 960 # 960 Twips = 48 point
    box_style.alignment.horz = HORZ_CENTER
    box_style.alignment.vert = VERT_CENTER

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
            img_width = size[0]
            img_height = int(IMG_WIDTH/img_width * size[1])
            img = img.convert("RGB").resize((IMG_WIDTH, img_height))
            from io import BytesIO
            bmpfile = BytesIO()
            img.save(bmpfile, "BMP")
            bmpfile.seek(0)
            bmpdata = bmpfile.read()

    # Add sheet
    sheet = book.add_sheet(item_code or item_name)
    sheet.fit_num_pages = 1

    # Set column Widths
    sheet.col(0).width = 4172   # 3.19 cm A
    sheet.col(1).width = 1505   # 1.15 cm B
    sheet.col(2).width = 4069   # 3.11 cm C
    sheet.col(3).width = 1752   # 1.34 cm D
    sheet.col(4).width = 4069   # 3.11 cm E
    sheet.col(5).width = 1505   # 1.15 cm F
    sheet.col(6).width = 3256   # 2.49 cm G
    sheet.col(7).width = 2341   # 1.79 cm H
    sheet.col(8).width = 2642   # 2.05 cm I
    sheet.col(9).width = 4682   # 3.58 cm J
    sheet.col(10).width = 2341  # 1.79 cm K
    sheet.col(11).width = 5414  # 4.14 cm L
    sheet.col(12).width = 2341  # 1.79 cm M
    sheet.col(13).width = 2341  # 1.79 cm N

    if logo:
        # 1st row: Logo
        sheet.insert_bitmap_data(bmpdata, 0, 11)

    # 7th row: Height
    current_row = sheet.row(6)
    current_row.height = ROW_HEIGHT

    # 8th row: Item Name
    row_index = 7
    sheet.write_merge(row_index, row_index + 5, 0, 13, item_name, big_box_style)

    # 14th row: Height
    current_row = sheet.row(13)
    current_row.height = ROW_HEIGHT

    # 16th row: Divider
    current_row = sheet.row(15)
    for col_index in range(14):
        current_row.write(col_index, "", bold_style)

    # 18th row: Item Name
    row_index = 16
    sheet.write_merge(row_index, row_index + 5, 0, 13, item_code, box_style)

    # 25th row: Height
    current_row = sheet.row(24)
    current_row.height = ROW_HEIGHT

    # 26th row: UoM
    current_row = sheet.row(25)
    current_row.height = ROW_HEIGHT
    current_row.write(4, "measure of unit :", right_style)
    if pack_quantity == 1:
        label = pack.name
    else:
        # Lookup the Unit Pack
        query = (ptable.item_id == supply_item.id) & \
                (ptable.quantity == 1)
        unit_pack = db(query).select(ptable.name,
                                     limitby = (0, 1),
                                     ).first()
        label = "%s %s / %s" % (pack_quantity,
                                unit_pack.name,
                                pack.name,
                                )
    current_row.write(6, label, style)

    # 27th row: Height
    current_row = sheet.row(26)
    current_row.height = ROW_HEIGHT

    # 28th row: Expiry Date
    current_row = sheet.row(27)
    current_row.height = ROW_HEIGHT
    current_row.write(4, "expiry date :", right_style)
    expiry_date = track_item.expiry_date
    if expiry_date:
        label = str(expiry_date)
    else:
        label = "N/A"
    current_row.write(6, label, style)

    # 29th row: Height
    current_row = sheet.row(28)
    current_row.height = ROW_HEIGHT

    # 30th row: Donor
    current_row = sheet.row(29)
    current_row.height = ROW_HEIGHT
    current_row.write(4, "donor :", right_style)
    donor = track_item.supply_org_id
    if donor:
        label = org_represent(donor)
    else:
        label = "N/A"
    current_row.write(6, label, style)

    # 31st row: Height
    current_row = sheet.row(30)
    current_row.height = ROW_HEIGHT

    # 32nd row: Height
    current_row = sheet.row(31)
    current_row.height = ROW_HEIGHT

    # 37th row: Size Labels
    current_row = sheet.row(36)
    current_row.height = ROW_HEIGHT
    current_row.write(0, "Dimensions :", bold_style)
    for col_index in range(1, 8):
        # Divider
        current_row.write(col_index, "", bold_style)
    current_row.write(8, "Weight", bold_style)
    for col_index in range(9, 11):
        # Divider
        current_row.write(col_index, "", bold_style)
    current_row.write(11, "Volume", bold_style)
    for col_index in range(12, 14):
        # Divider
        current_row.write(col_index, "", bold_style)

    # 38th row: Sizes
    current_row = sheet.row(37)
    current_row.height = ROW_HEIGHT
    current_row.write(0, width, center_style)
    current_row.write(1, "x", style)
    current_row.write(2, length, center_style)
    current_row.write(3, "x", style)
    current_row.write(4, height, center_style)
    current_row.write(5, "m", style)
    current_row.write(7, weight, style)
    current_row.write(9, "Kgs", style)
    formula = xlwt.Formula("ROUND(A38*C38*E38, 2)")
    current_row.write(11, formula, center_style)
    current_row.write(12, "m3", style)

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
    title = s3_str(T("Label for %(item)s")) % {"item": item_code or item_code or item_name}
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

        Args:
            row: the Row
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
        return NONE

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

        Args:
            row: the Row
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
        return NONE

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
def inv_packing_list(r, **attr):
    """
        Generate a Packing List for an Outbound Shipment

        This is exported in XLS format
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
    site_id = record.site_id
    to_site_id = record.to_site_id
    sites = [site_id, to_site_id]

    db = current.db
    s3db = current.s3db

    # Items
    ptable = s3db.inv_package
    sptable = s3db.inv_send_package
    spitable = s3db.inv_send_package_item
    ttable = s3db.inv_track_item
    itable = s3db.supply_item
    query = (sptable.send_id == send_id) & \
            (sptable.package_id == ptable.id) & \
            (spitable.send_package_id == sptable.id) & \
            (spitable.track_item_id == ttable.id) & \
            (ttable.item_id == itable.id)
    items = db(query).select(ptable.type,
                             sptable.number,
                             itable.name,
                             spitable.quantity,
                             sptable.weight,
                             sptable.volume,
                             orderby = sptable.number,
                             )

    # Countries of both Source & Destination
    stable = s3db.org_site
    gtable = s3db.gis_location
    query = (stable.site_id.belongs(sites)) & \
            (stable.location_id == gtable.id)
    locations = db(query).select(gtable.L0,
                                 limitby = (0, 2),
                                 )
    fr = False
    settings = current.deployment_settings
    for row in locations:
        if "fr" in settings.get_L10n_languages_by_country(row.L0):
            fr = True
            break

    # Organisations
    otable = s3db.org_organisation
    query = (stable.site_id.belongs(sites)) & \
            (stable.organisation_id == otable.id)
    fields = [stable.location_id,
              stable.site_id,
              otable.id,
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

    orgs = db(query).select(*fields,
                           left = left,
                           limitby = (0, 2)
                           )
    for row in orgs:
        site = row.org_site
        if site.site_id == site_id:
            # Sender Org
            if fr:
                org_name = row["org_organisation_name.name_l10n"]
                org = row["org_organisation"]
                if not org_name:
                    org_name = org.name
            else:
                org = row["org_organisation"]
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
        else:
            # Recipient Org
            location_id = site.location_id
            if fr:
                dest_org_name = row["org_organisation_name.name_l10n"]
                dest_org = row["org_organisation"]
                if not dest_org_name:
                    dest_org_name = dest_org.name
            else:
                dest_org = row["org_organisation"]
                dest_org_name = dest_org.name
            if dest_org.id != dest_org.root_organisation:
                # Lookup Root Org
                fields = [otable.name,
                          ]
                if fr:
                    fields.append(ontable.name_l10n)
                dest_org = db(otable.id == dest_org.root_organisation).select(*fields,
                                                                              left = left,
                                                                              limitby = (0, 1)
                                                                              ).first()
                if fr:
                    dest_org_name = dest_org["org_organisation_name.name_l10n"]
                    dest_org = dest_org["org_organisation"]
                    if not dest_org_name:
                        dest_org_name = dest_org.name
                else:
                    dest_org_name = dest_org.name

    # Represent the Data
    from .org import org_SiteRepresent
    site_represent = org_SiteRepresent(show_type = False)
    site_represent.bulk(sites) # Bulk lookup, with results cached in class instance
    source = site_represent(site_id)
    destination = site_represent(to_site_id)

    from .gis import gis_LocationRepresent
    address = gis_LocationRepresent(show_level = False)(location_id)

    recipient_id = record.recipient_id
    if recipient_id:
        from .pr import pr_PersonRepresent
        recipient = pr_PersonRepresent(truncate = False)(recipient_id)
    else:
        recipient = None

    package_type_represent = ptable.type.represent

    T = current.T

    labels = ["N° Box",
              "Description",
              "Quantity",
              "Weight\nKg",
              "Volume\nm3",
              ]

    # Create the workbook
    book = xlwt.Workbook(encoding = "utf-8")

    # Add sheet
    title = "Packing List"
    sheet = book.add_sheet(title)
    sheet.set_print_scaling(69)

    # Set column Widths
    sheet.col(0).width = 3300  # 2.52 cm
    sheet.col(1).width = 13595 # 10.39 cm
    sheet.col(2).width = 4291  # 3.28 cm
    sheet.col(3).width = 4432  # 3.39 cm
    sheet.col(4).width = 4031  # 3.08 cm

    # Define styles
    POINT_12 = 240 # Twips = Points * 20
    POINT_10 = 200 # Twips = Points * 20
    POINT_9 = 180 # Twips = Points * 20
    ROW_HEIGHT = 320 # Realised through trial & error
    ROWS_2_HEIGHT = int(2.2 * 320)

    style = xlwt.XFStyle()
    style.font.height = POINT_12

    HORZ_CENTER = style.alignment.HORZ_CENTER
    HORZ_RIGHT = style.alignment.HORZ_RIGHT
    VERT_CENTER = style.alignment.VERT_CENTER
    THICK = style.borders.THICK
    THIN = style.borders.THIN

    style.borders.top = THIN
    style.borders.left = THIN
    style.borders.right = THIN
    style.borders.bottom = THIN

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

    bold_italic_center_style = xlwt.XFStyle()
    bold_italic_center_style.font.italic = True
    bold_italic_center_style.font.bold = True
    bold_italic_center_style.font.height = POINT_12
    bold_italic_center_style.alignment.horz = HORZ_CENTER

    center_style = xlwt.XFStyle()
    center_style.font.height = POINT_12
    center_style.alignment.horz = HORZ_CENTER
    center_style.borders.top = THIN
    center_style.borders.left = THIN
    center_style.borders.right = THIN
    center_style.borders.bottom = THIN

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

    # 1st row => Org Logo
    current_row = sheet.row(0)
    # current_row.set_style() not giving the correct height
    current_row.height = ROW_HEIGHT
    #sheet.write_merge(0, 0, 0, 1, org_name, left_header_style)
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
            sheet.insert_bitmap_data(bmpdata, 0, 3)

    # 7th row => Packing List
    row_index = 6
    current_row = sheet.row(row_index)
    current_row.height = int(2.8 * 240 * 1.2) # 2 rows
    label = "PACKING LIST"
    if fr:
        sheet.merge(row_index, row_index, 0, 4, box_style)
        rich_text = ((label, box_style.font),
                     ("\nListe de colisage", large_italic_font),
                     )
        sheet.write_rich_text(row_index, 0, rich_text, box_style)
    else:
        sheet.write_merge(row_index, row_index, 0, 4, label, box_style)

    # 9th row => Reference
    row_index = 8
    current_row = sheet.row(row_index)
    current_row.height = ROW_HEIGHT
    label = "Ref: %s" % send_ref
    sheet.write_merge(row_index, row_index, 0, 4, label, bold_italic_center_style)

    # 11th row => Source
    row_index = 10
    current_row = sheet.row(row_index)
    if fr:
        current_row.height = ROWS_2_HEIGHT
        rich_text = (("Location /", header_style.font),
                     ("\nLieu:", bold_italic_style.font),
                     )
        sheet.write_rich_text(row_index, 0, rich_text, header_style)
    else:
        current_row.height = ROW_HEIGHT
        label = "Location:"
        current_row.write(0, label, header_style)
    current_row.write(1, source, header_style)
    current_row.write(3, "Date:", header_style)
    current_row.write(4, str(r.now.date()), header_style)

    # 14th row => Destination
    row_index = 13
    current_row = sheet.row(row_index)
    current_row.height = ROW_HEIGHT
    if fr:
        rich_text = (("CONSIGNEE / ", bold_style.font),
                     ("DESTINATAIRE:", bold_italic_style.font),
                     )
        sheet.write_rich_text(row_index, 1, rich_text, bold_style)
        rich_text = (("Address / ", right_style.font),
                     ("Adresse:", italic_style.font),
                     )
        sheet.write_rich_text(row_index + 2, 1, rich_text, right_style)
    else:
        current_row.write(1, "CONSIGNEE:", bold_style)
        sheet.row(row_index + 2).write(1, "Address:", right_style)
    sheet.row(row_index + 4).write(1, "Contact:", right_style)
    if destination in address:
        label = "%s\n\n%s" % (dest_org_name.upper(), address)
    else:
        label = "%s\n\n%s\n%s" % (dest_org_name.upper(), destination, address)
    if recipient:
        label = "%s\n\n%s" % (label, recipient)
    sheet.write_merge(row_index, 16, 2, 4, label, dest_style)

    # 24nd row => Column Headers
    row_index = 23
    current_row = sheet.row(row_index)
    current_row.height = ROWS_2_HEIGHT
    col_index = 0
    for label in labels:
        if fr and col_index in (0, 3):
            if col_index == 0:
                rich_text = (("N° Box /", header_style.font),
                             ("\nColis", bold_italic_style.font),
                             )
            else:
                rich_text = (("Weight / ", header_style.font),
                             ("Poids", bold_italic_style.font),
                             ("\nKg", header_style.font),
                             )
            sheet.write_rich_text(row_index, col_index, rich_text, header_style)
        else:
            current_row.write(col_index, label, header_style)
        col_index += 1

    # Data rows
    total_weight = 0
    total_volume = 0
    row_index = 24
    for row in items:
        current_row = sheet.row(row_index)
        current_row.height = ROW_HEIGHT
        package_type = row["inv_package.type"]
        item_name = row["supply_item.name"]
        quantity = row["inv_send_package_item.quantity"]
        row = row["inv_send_package"]
        weight = row.weight
        if weight:
            total_weight += weight
            weight = str(round(weight, 0))
        else:
            weight = ""
        volume = row.volume
        if volume:
            total_volume += volume
            volume = "{:.3f}".format(round(volume, 3))
        else:
            volume = ""
        col_index = 0
        values = ["%s %s" % (package_type_represent(package_type),
                             row.number,
                             ),
                  item_name,
                  quantity,
                  weight,
                  volume,
                  ]
        for value in values:
            if col_index in (0, 1):
                current_row.write(col_index, value, style)
            else:
                current_row.write(col_index, value, center_style)
            col_index += 1
        row_index += 1

    # Totals
    current_row = sheet.row(row_index)
    current_row.height = ROW_HEIGHT
    current_row.write(0, "Total", header_style)
    current_row.write(1, "", header_style) # Cell Pattern
    current_row.write(2, "", header_style) # Cell Pattern
    total_weight = str(round(total_weight, 0))
    total_volume = "{:.2f}".format(round(total_volume, 2))
    current_row.write(3, total_weight, header_style)
    current_row.write(4, total_volume, header_style)

    # Footer
    row_index += 2
    current_row = sheet.row(row_index)
    if fr:
        current_row.height = ROWS_2_HEIGHT
        rich_text = (("Function /", style.font),
                     ("\nFonction", italic_style.font),
                     )
        sheet.write_rich_text(row_index, 0, rich_text, style)
        rich_text = (("Name / ", style.font),
                     ("Nom:", italic_style.font),
                     )
        sheet.write_rich_text(row_index, 1, rich_text, style)
        sheet.write_merge(row_index, row_index, 2, 3, "Signature", style)
        rich_text = (("Stamp /", style.font),
                     ("\ntampon", italic_style.font),
                     )
        sheet.write_rich_text(row_index, 4, rich_text, style)
    else:
        current_row.height = ROW_HEIGHT
        current_row.write(0, "Function:", style)
        current_row.write(1, "Name:", style)
        sheet.write_merge(row_index, row_index, 2, 3, "Signature", style)
        current_row.write(4, "Stamp", style)
    # Empty space for Signature, etc
    row_index += 1
    current_row = sheet.row(row_index)
    current_row.height = ROWS_2_HEIGHT
    current_row.write(0, "", style)
    current_row.write(1, "", style)
    sheet.write_merge(row_index, row_index, 2, 3, "", style)
    current_row.write(4, "", style)

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
    title = s3_str(T("Packing List for %(waybill)s")) % {"waybill": send_ref}
    filename = "%s.xls" % title
    response = current.response
    from gluon.contenttype import contenttype
    response.headers["Content-Type"] = contenttype(".xls")
    disposition = "attachment; filename=\"%s\"" % filename
    response.headers["Content-disposition"] = disposition

    return output.read()

# =============================================================================
def inv_package_labels(r, **attr):
    """
        Generate Labels for an Outbound Shipment's Packages
        - separate sheet per Package

        This is exported in XLS format to be user-editable
        - we can only estimate height for Palettes
    """

    from s3.codecs.xls import S3XLS

    try:
        import xlwt
    except ImportError:
        r.error(503, S3XLS.ERROR.XLWT_ERROR)

    # Extract the Data
    record = r.record

    db = current.db
    s3db = current.s3db

    # Packages
    ptable = s3db.inv_package
    sptable = s3db.inv_send_package
    query = (sptable.send_id == r.id) & \
            (sptable.package_id == ptable.id)
    packages = db(query).select(sptable.id,
                                sptable.number,
                                sptable.weight,
                                sptable.volume,
                                ptable.type,
                                ptable.weight,
                                ptable.width,
                                ptable.length,
                                ptable.depth,
                                )

    total_packages = len(packages)

    # Organisation
    otable = s3db.org_organisation
    stable = s3db.org_site
    query = (stable.site_id == record.site_id) & \
            (stable.organisation_id == otable.id)
    org = db(query).select(otable.id,
                           otable.root_organisation,
                           otable.logo,
                           limitby = (0, 1)
                           ).first()

    if org.id != org.root_organisation:
        # Lookup Root Org
        org = db(otable.id == org.root_organisation).select(otable.logo,
                                                            limitby = (0, 1)
                                                            ).first()

    # Represent the Data
    T = current.T

    site_represent = S3Represent(lookup = "org_site")
    source = site_represent(record.site_id)
    destination = site_represent(record.to_site_id)

    # Create the workbook
    book = xlwt.Workbook(encoding = "utf-8")

    # Define styles
    POINT_36 = 720 # Twips = Points * 20
    ROW_HEIGHT = 890 # Realised through trial & error

    style = xlwt.XFStyle()
    style.font.height = POINT_36

    HORZ_CENTER = style.alignment.HORZ_CENTER
    VERT_CENTER = style.alignment.VERT_CENTER

    bold_style = xlwt.XFStyle()
    bold_style.font.bold = True
    bold_style.font.height = POINT_36
    bold_style.borders.top = style.borders.THICK

    center_style = xlwt.XFStyle()
    center_style.alignment.horz = style.alignment.HORZ_CENTER
    center_style.font.height = POINT_36

    right_style = xlwt.XFStyle()
    right_style.alignment.horz = style.alignment.HORZ_RIGHT
    right_style.font.height = POINT_36

    big_box_style = xlwt.XFStyle()
    big_box_style.font.bold = True
    big_box_style.font.height = 1120 # 1120 Twips = 56 point
    big_box_style.alignment.horz = HORZ_CENTER
    big_box_style.alignment.vert = VERT_CENTER

    box_style = xlwt.XFStyle()
    box_style.font.height = 960 # 960 Twips = 48 point
    box_style.alignment.horz = HORZ_CENTER
    box_style.alignment.vert = VERT_CENTER

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

    for row in packages:
        package = row.inv_package
        send_package = row.inv_send_package
        package_type = package.type
        package_number = send_package.number

        # Add sheet
        sheet = book.add_sheet(str(package_number))
        sheet.fit_num_pages = 1

        # Weight is Load + Package Weight
        package_weight = str(int(send_package.weight + package.weight))
        # Length & Width are those of the Package
        length = package.length
        width = package.width
        if package_type == "BOX":
            height = package.depth
        elif length and width:
            # Pallet
            # Height is Load Height + Package Depth
            height = (send_package.volume / (length * width)) + package.depth
        else:
            # We cannot calculate it
            height = ""

        send_package_id = send_package.id

        # Set column Widths
        sheet.col(0).width = 4172   # 3.19 cm A
        sheet.col(1).width = 1505   # 1.15 cm B
        sheet.col(2).width = 4069   # 3.11 cm C
        sheet.col(3).width = 1752   # 1.34 cm D
        sheet.col(4).width = 4069   # 3.11 cm E
        sheet.col(5).width = 1505   # 1.15 cm F
        sheet.col(6).width = 3256   # 2.49 cm G
        sheet.col(7).width = 2341   # 1.79 cm H
        sheet.col(8).width = 2642   # 2.05 cm I
        sheet.col(9).width = 4682   # 3.58 cm J
        sheet.col(10).width = 2341  # 1.79 cm K
        sheet.col(11).width = 5414  # 4.14 cm L
        sheet.col(12).width = 2341  # 1.79 cm M
        sheet.col(13).width = 2341  # 1.79 cm N

        if logo:
            # 1st row: Logo
            sheet.insert_bitmap_data(bmpdata, 0, 11)

        # 7th row: Height
        current_row = sheet.row(6)
        current_row.height = ROW_HEIGHT

        # 8th row: Package Number
        row_index = 7
        
        if package_type == "BOX":
            package_name = T("Box %(number)s / %(total)s") % {"number": package_number,
                                                              "total": total_packages,
                                                              }
        else:
            # Pallet
            package_name = T("Pallet %(number)s / %(total)s") % {"number": package_number,
                                                                 "total": total_packages,
                                                                 }
        sheet.write_merge(row_index, row_index + 5, 0, 13, s3_str(package_name), big_box_style)

        # 14th row: Height
        current_row = sheet.row(13)
        current_row.height = ROW_HEIGHT

        # 16th row: Divider
        current_row = sheet.row(15)
        for col_index in range(14):
            current_row.write(col_index, "", bold_style)

        # 18th row: From
        row_index = 16
        sheet.write_merge(row_index, row_index + 5, 0, 13, "%s: %s" % (T("From"),
                                                                       source,
                                                                       ), box_style)

        # 25th row: To
        row_index = 24
        sheet.write_merge(row_index, row_index + 5, 0, 13, "%s: %s" % (T("To"),
                                                                       destination,
                                                                       ), box_style)

        # 32rd row: Size Labels
        current_row = sheet.row(31)
        current_row.height = ROW_HEIGHT
        current_row.write(0, "Dimensions :", bold_style)
        for col_index in range(1, 8):
            # Divider
            current_row.write(col_index, "", bold_style)
        current_row.write(8, "Weight", bold_style)
        for col_index in range(9, 11):
            # Divider
            current_row.write(col_index, "", bold_style)
        current_row.write(11, "Volume", bold_style)
        for col_index in range(12, 14):
            # Divider
            current_row.write(col_index, "", bold_style)

        # 33rd row: Sizes
        current_row = sheet.row(32)
        current_row.height = ROW_HEIGHT
        current_row.write(0, width, center_style)
        current_row.write(1, "x", style)
        current_row.write(2, length, center_style)
        current_row.write(3, "x", style)
        current_row.write(4, height, center_style)
        current_row.write(5, "m", style)
        current_row.write(7, package_weight, style)
        current_row.write(9, "Kgs", style)
        formula = xlwt.Formula("ROUND(A33*C33*E33, 2)")
        current_row.write(11, formula, center_style)
        current_row.write(12, "m3", style)

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
    title = s3_str(T("Labels for %(waybill)s")) % {"waybill": record.send_ref}
    filename = "%s.xls" % title
    response = current.response
    from gluon.contenttype import contenttype
    response.headers["Content-Type"] = contenttype(".xls")
    disposition = "attachment; filename=\"%s\"" % filename
    response.headers["Content-disposition"] = disposition

    return output.read()

# =============================================================================
def inv_pick_list(r, **attr):
    """
        Generate a Picking List for an Outbound Shipment

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
                next = '"%s"' % URL(c = "inv",
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

    table = s3db.inv_track_item
    itable = s3db.supply_item
    ptable = s3db.supply_item_pack
    sbtable = s3db.inv_send_item_bin

    query = (table.send_id == send_id) & \
            (table.item_id == itable.id) & \
            (table.item_pack_id == ptable.id)
    left = sbtable.on(sbtable.track_item_id == table.id)
    items = current.db(query).select(table.quantity,
                                     itable.code,
                                     itable.name,
                                     itable.volume,
                                     itable.weight,
                                     ptable.name,
                                     ptable.quantity,
                                     sbtable.layout_id,
                                     sbtable.quantity,
                                     left = left,
                                     )

    # Bulk Represent the Bins
    # - values stored in class instance
    bin_represent = sbtable.layout_id.represent
    bins = bin_represent.bulk([row["inv_send_item_bin.layout_id"] for row in items])
    # Sort the Data
    def sort_function(row):
        return bin_represent(row["inv_send_item_bin.layout_id"])
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
    style = xlwt.XFStyle()

    THIN = style.borders.THIN
    HORZ_CENTER = style.alignment.HORZ_CENTER
    HORZ_RIGHT = style.alignment.HORZ_RIGHT

    style.borders.top = THIN
    style.borders.left = THIN
    style.borders.right = THIN
    style.borders.bottom = THIN

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
    translate = current.deployment_settings.get_L10n_translate_supply_item()
    row_index = 3
    for row in items:
        current_row = sheet.row(row_index)
        item_row = row["supply_item"]
        pack_row = row["supply_item_pack"]
        bin_row = row["inv_send_item_bin"]
        layout_id = bin_row.layout_id
        if layout_id:
            bin = bin_represent(layout_id)
            quantity = bin_row.quantity
        else:
            bin = ""
            # @ToDo: Handle the case where some of the Inventory is binned & some not!
            #        - need to loop through 1st separately to find this out...or can we get it from the sort?
            quantity = row["inv_track_item.quantity"]
        item_name = item_row.name or ""
        if translate and item_name:
            item_name = s3_str(T(item_name))
        pack_name = pack_row.name
        if translate:
            pack_name = s3_str(T(pack_name))
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
                current_row.write(col_index, value, style)
            elif col_index == 4:
                # Qty to Pick
                current_row.write(col_index, value, center_style)
            else:
                current_row.write(col_index, value, right_style)
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

    # Footer
    current_row = sheet.row(row_index)
    current_row.height = 400
    sheet.write_merge(row_index, row_index, 0, 4, "%s:" % s3_str(T("Picked By")), right_style)
    sheet.write_merge(row_index, row_index, 5, 9, "", style) # Styling
    row_index += 1
    current_row = sheet.row(row_index)
    current_row.height = 400
    sheet.write_merge(row_index, row_index, 0, 4, "%s:" % s3_str(T("Signature")), right_style)
    sheet.write_merge(row_index, row_index, 5, 9, "", style) # Styling

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
    if status == SHIP_STATUS_IN_PROCESS:
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

        if status == SHIP_STATUS_SENT:
            table.date.writable = True
            table.recipient_id.readable = table.recipient_id.writable = True
            table.comments.writable = True

# =============================================================================
def inv_recv_cancel(r, **attr):
    """
        Cancel a Received Shipment

        - not currently visible in UI as
            "serves no useful purpose & AusRC complained about it"

        @todo what to do if the quantity cancelled doesn't exist?
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    recv_id = r.id
    if not recv_id:
        r.error(405, "Can only cancel a single shipment.")

    T = current.T
    s3db = current.s3db
    rtable = s3db.inv_send

    if not current.auth.s3_has_permission("delete", rtable,
                                          record_id = recv_id,
                                          ):
        r.unauthorised()

    record = r.record

    if record.status != SHIP_STATUS_RECEIVED:
        r.error(409, T("This shipment has not been received - it has NOT been canceled because it can still be edited."),
                tree = '"%s"' % URL(args = [send_id]),
                )

    db = current.db

    stable = s3db.inv_send
    tracktable = s3db.inv_track_item
    inv_item_table = s3db.inv_inv_item
    ritable = s3db.inv_req_item
    siptable = s3db.supply_item_pack

    # Go through each item in the shipment remove them from the site store
    # and put them back in the track item record
    recv_items = db(tracktable.recv_id == recv_id).select(tracktable.recv_inv_item_id,
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
        db(tracktable.recv_id == recv_id).update(status = TRACK_STATUS_TRANSIT) # 2
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
    db(rtable.id == recv_id).update(date = r.utcnow,
                                    status = SHIP_STATUS_CANCEL,
                                    )
    if send_id != None:
        # The sent record is now set back to SENT so the source warehouse can
        # now cancel this record to get the stock back into their warehouse.
        # IMPORTANT reports need to locate this record otherwise it can be
        # a mechanism to circumvent the auditing of stock
        db(stable.id == send_id).update(status = SHIP_STATUS_SENT)

    if current.deployment_settings.get_inv_warehouse_free_capacity_calculated():
        # Update the Warehouse Free capacity
        inv_warehouse_free_capacity(record.site_id)

    message = T("Received Shipment canceled and items removed from Warehouse")
    current.session.confirmation = message

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": URL(args = [recv_id]),
                       }, separators=SEPARATORS)

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

    # Custom methods
    set_method = s3db.set_method
    # Printable GRN Form in PDF format
    # - note that it is easy to over-ride this method to produce custom versions
    set_method("inv", "recv",
               method = "form",
               action = inv_recv_form,
               )

    # Cancel Received Shipment
    #set_method("inv", "recv",
    #           method = "cancel",
    #           action = inv_recv_cancel,
    #           )

    # Donation Certificate
    set_method("inv", "recv",
               method = "cert",
               action = inv_recv_donation_cert,
               )

    # Generate Item Labels
    set_method("inv", "recv",
               component_name = "track_item",
               method = "label",
               action = inv_item_label,
               )

    # Process Shipment
    set_method("inv", "recv",
               method = "process",
               action = inv_recv_process,
               )

    # Timeline
    set_method("inv", "recv",
               method = "timeline",
               action = inv_timeline,
               )

    def prep(r):

        record = r.record
        if record:
            status = record.status

        export_formats = settings.ui.export_formats
        if "pdf" in export_formats:
            # Use 'form' instead of standard PDF exporter
            export_formats = list(export_formats)
            export_formats.remove("pdf")
            settings.ui.export_formats = export_formats

        if r.component:
            component_name = r.component_name
            if component_name == "document":
                s3.crud_strings["doc_document"].label_create = T("File Signed Document")

                # Simplify a little
                table = s3db.doc_document
                table.file.required = True
                #table.url.readable = table.url.writable = False
                #table.date.readable = table.date.writable = False

                GRN = settings.get_inv_recv_form_name()
                field = table.name
                field.label = T("Type")
                document_type_opts = {"REQ": settings.get_inv_req_form_name(),
                                      "GRN": GRN,
                                      "WB": settings.get_inv_send_form_name(),
                                      }
                field.default = "GRN"
                field.requires = IS_IN_SET(document_type_opts)
                field.represent = s3_options_represent(document_type_opts)

                # Add button to print the GRN
                # - needed for Wizard, but generalised for consistency
                button = DIV(P(T("Print and Upload the signed %(grn)s:") % {"grn": GRN}),
                             A(ICON("print"),
                               " ",
                               settings.get_inv_recv_shortname(),
                               _href = URL(args = [record.id,
                                                   "form",
                                                   ]
                                         ),
                               _class = "action-btn",
                               ),
                            )

                crud_form = S3SQLCustomForm(S3SQLInlineWidget(button),
                                            "name",
                                            "file",
                                            "comments",
                                            )

                s3db.configure("doc_document",
                               crud_form = crud_form,
                               )

            elif component_name == "track_item":

                method = r.method
                if method == "wizard":
                    page = r.get_vars.get("page")
                else:
                    page = None
                # Security-wise, we are already covered by configure()
                # Performance-wise, we should optimise for UI-acessible flows
                #if method == "create" or method == "delete":
                #    # Can only create or delete track items for a recv record
                #    # if the status is preparing:
                #    if status != SHIP_STATUS_IN_PROCESS:
                #        return False

                tracktable = s3db.inv_track_item

                track_pack_values = settings.get_inv_track_pack_values()

                def set_track_attr(track_status):
                    # By default Make all fields writable False
                    for field in tracktable.fields:
                        tracktable[field].writable = False
                    # Hide some fields
                    tracktable.send_id.readable = False
                    tracktable.recv_id.readable = False
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
                        if page == "items":
                            # Standard form, but without Bins
                            crud_form = S3SQLCustomForm("item_id",
                                                        "item_pack_id",
                                                        "quantity",
                                                        "recv_quantity",
                                                        "return_quantity",
                                                        "pack_value",
                                                        "currency",
                                                        "expiry_date",
                                                        "item_source_no",
                                                        "supply_org_id",
                                                        "owner_org_id",
                                                        "inv_item_status",
                                                        "status",
                                                        # readable/writable = False by default
                                                        # writable set to True later if linked to requests
                                                        "req_item_id",
                                                        "comments",
                                                        )
                        elif page == "bins":
                            # Just Bins
                            # - currently has more fields, to support JS
                            crud_form = S3SQLCustomForm("item_id",
                                                        "item_pack_id",
                                                        "quantity",
                                                        "recv_quantity",
                                                        S3SQLInlineComponent("recv_bin",
                                                                             label = T("Add to Bins"),
                                                                             fields = ["layout_id",
                                                                                       "quantity",
                                                                                       ],
                                                                             ),
                                                        # readable/writable = False by default
                                                        # writable set to True later if linked to requests
                                                        "req_item_id",
                                                        )
                        else:
                            crud_form = S3SQLCustomForm("item_id",
                                                        "item_pack_id",
                                                        "quantity",
                                                        "recv_quantity",
                                                        S3SQLInlineComponent("recv_bin",
                                                                             label = T("Add to Bins"),
                                                                             fields = ["layout_id",
                                                                                       "quantity",
                                                                                       ],
                                                                             ),
                                                        "return_quantity",
                                                        "pack_value",
                                                        "currency",
                                                        "expiry_date",
                                                        "item_source_no",
                                                        "supply_org_id",
                                                        "owner_org_id",
                                                        "inv_item_status",
                                                        "status",
                                                        # readable/writable = False by default
                                                        # writable set to True later if linked to requests
                                                        "req_item_id",
                                                        "comments",
                                                        )

                    elif track_status == TRACK_STATUS_TRANSIT:
                        # Internal Shipment auto-generated from inv_send_process
                        # Hide the values that will be copied from the inv_inv_item record
                        tracktable.send_inv_item_id.readable = False
                        # Display the values that can only be entered on create
                        tracktable.recv_quantity.writable = True
                        tracktable.comments.writable = True
                        # This is a received purchase so change the label to reflect this - NO - use consistent labels
                        #tracktable.quantity.label =  T("Quantity Delivered")
                        crud_form = S3SQLCustomForm("item_id",
                                                    "item_pack_id",
                                                    "quantity",
                                                    "recv_quantity",
                                                    S3SQLInlineComponent("recv_bin",
                                                                         label = T("Add to Bins"),
                                                                         fields = ["layout_id",
                                                                                   "quantity",
                                                                                   ],
                                                                         ),
                                                    "pack_value",
                                                    "currency",
                                                    "expiry_date",
                                                    "item_source_no",
                                                    "supply_org_id",
                                                    "owner_org_id",
                                                    "inv_item_status",
                                                    "status",
                                                    "comments",
                                                    )

                    elif track_status == TRACK_STATUS_ARRIVED:
                        # Received Shipment
                        crud_form = S3SQLCustomForm("send_inv_item_id",
                                                    "item_id",
                                                    "item_pack_id",
                                                    "quantity",
                                                    "recv_quantity",
                                                    "pack_value",
                                                    "currency",
                                                    "expiry_date",
                                                    S3SQLInlineComponent("recv_bin",
                                                                         label = T("Add to Bins"),
                                                                         fields = ["layout_id",
                                                                                   "quantity",
                                                                                   ],
                                                                         readonly = True,
                                                                         ),
                                                    "item_source_no",
                                                    "supply_org_id",
                                                    "owner_org_id",
                                                    "inv_item_status",
                                                    "status",
                                                    "comments",
                                                    )
                    else:
                        crud_form = S3SQLCustomForm("send_inv_item_id",
                                                    "item_id",
                                                    "item_pack_id",
                                                    "quantity",
                                                    "recv_quantity",
                                                    "pack_value",
                                                    "currency",
                                                    "expiry_date",
                                                    S3SQLInlineComponent("send_bin",
                                                                         label = T("Bins"),
                                                                         fields = ["layout_id",
                                                                                   "quantity",
                                                                                   ],
                                                                         ),
                                                    S3SQLInlineComponent("recv_bin",
                                                                         label = T("Add to Bins"),
                                                                         fields = ["layout_id",
                                                                                   "quantity",
                                                                                   ],
                                                                         ),
                                                    "item_source_no",
                                                    "supply_org_id",
                                                    "owner_org_id",
                                                    "inv_item_status",
                                                    "status",
                                                    "comments",
                                                    )
                    return crud_form

                track_item_id = r.component_id
                if track_item_id:
                    track_record = db(tracktable.id == track_item_id).select(tracktable.item_id,
                                                                             tracktable.quantity,
                                                                             tracktable.status,
                                                                             limitby = (0, 1),
                                                                             ).first()
                    crud_form = set_track_attr(track_record.status)
                    update_item_id = track_record.item_id
                    if r.http == "GET" and \
                       track_record.status == TRACK_STATUS_PREPARING:
                        # Provide initial options for Pack in Update forms
                        # Don't include in the POSTs as we want to be able to select alternate Items, and hance packs
                        f = tracktable.item_pack_id
                        f.requires = IS_ONE_OF(db, "supply_item_pack.id",
                                               f.represent,
                                               sort = True,
                                               filterby = "item_id",
                                               filter_opts = (update_item_id,),
                                               )
                else:
                    crud_form = set_track_attr(TRACK_STATUS_PREPARING)
                    tracktable.status.readable = False

                if page == "bins":
                    list_fields = ["item_id",
                                   "recv_quantity",
                                   "recv_bin.layout_id",
                                   ]
                else:
                    list_fields = [#"status",
                                   "item_id",
                                   "item_pack_id",
                                   "quantity",
                                   "recv_quantity",
                                   "recv_bin.layout_id",
                                   "owner_org_id",
                                   "supply_org_id",
                                   ]
                    if track_pack_values:
                        list_fields.insert(4, "pack_value")
                        list_fields.insert(4, "currency")
                    if page == "items":
                        # Bins are handled on a separate step
                        list_fields.remove("recv_bin.layout_id")

                if status:
                    # Lock the record so it can't be fiddled with
                    deletable = False
                    insertable = False
                    if status == SHIP_STATUS_SENT:
                        # Lock the record so it can't be fiddled with
                        # - other than being able to edit Quantity Received & Bin
                        editable = True
                        if r.interactive:
                            s3.crud_strings.inv_recv.title_update = \
                            s3.crud_strings.inv_recv.title_display = T("Process Received Shipment")
                            if track_item_id and method in (None, "update", "wizard"):
                                # Limit to Bins from this site
                                from .org import org_site_layout_config
                                irbtable = s3db.inv_recv_item_bin
                                org_site_layout_config(record.site_id, irbtable.layout_id)
                                # Manage bin allocations
                                if s3.debug:
                                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv_sent_item.js" % r.application)
                                else:
                                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv_sent_item.min.js" % r.application)
                                js_global_append = s3.js_global.append
                                js_global_append('''S3.supply.sendQuantity=%s''' % track_record.quantity)
                                bins = db(irbtable.track_item_id == track_item_id).select(irbtable.quantity)
                                if len(bins) > 1:
                                    js_global_append('''S3.supply.binnedQuantity=%s''' % sum([row.quantity for row in bins]))
                                
                    else:
                        editable = False
                else:
                    # status == SHIP_STATUS_IN_PROCESS
                    deletable = True
                    editable = True
                    if page == "bins":
                        insertable = False
                    else:
                        insertable = True
                    if r.interactive:
                        s3.crud_strings.inv_recv.title_update = \
                        s3.crud_strings.inv_recv.title_display = T("Process Received Shipment")
                        if method in (None, "update", "wizard"):
                            # Limit to Bins from this site
                            from .org import org_site_layout_config
                            irbtable = s3db.inv_recv_item_bin
                            org_site_layout_config(record.site_id, irbtable.layout_id)

                            # Default the Supplier/Donor to the Org sending the shipment
                            tracktable.supply_org_id.default = record.organisation_id

                            # Replace filterOptionsS3
                            # Update req_item_id & quantity when item_id selected
                            if s3.debug:
                                s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv_item.js" % r.application)
                            else:
                                s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv_item.min.js" % r.application)
                            js_global_append = s3.js_global.append
                            packs = {}
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
                                        req_row = row["inv_req_item"]
                                        item_id = req_row.item_id
                                        if item_id in item_data:
                                            item_data[item_id].append({"i": req_row.id,
                                                                       "q": req_row.quantity * row["supply_item_pack.quantity"],
                                                                       "r": row["inv_req.req_ref"],
                                                                       })
                                        else:
                                            item_data[item_id] = [{"i": req_row.id,
                                                                   "q": req_row.quantity * row["supply_item_pack.quantity"],
                                                                   "r": row["inv_req.req_ref"],
                                                                   }]
                                    # Remove req_ref when there are no duplicates to distinguish
                                    for item_id in item_data:
                                        req_items = item_data[item_id]
                                        if len(req_items) == 1:
                                            req_items[0].pop("r")

                                    js_global_append('''S3.supply.req_data=%s''' % json.dumps(item_data, separators=SEPARATORS))

                                    # Add Packs for all Req Items to avoid AJAX lookups
                                    rows = db(iptable.item_id.belongs(item_ids)).select(iptable.id,
                                                                                        iptable.item_id,
                                                                                        iptable.name,
                                                                                        iptable.quantity,
                                                                                        )
                                    for row in rows:
                                        item_id = row.item_id
                                        if item_id in packs:
                                            packs[item_id].append({"i": row.id,
                                                                   "n": row.name,
                                                                   "q": row.quantity,
                                                                   })
                                        else:
                                            packs[item_id] = [{"i": row.id,
                                                               "n": row.name,
                                                               "q": row.quantity,
                                                               }]

                            if track_item_id:
                                # Update form
                                # add binnedQuantity if there are multiple Bins to manage
                                # @ToDo: Do we also need to do this if 1 Bin + unbinned?
                                bins = db(irbtable.track_item_id == track_item_id).select(irbtable.quantity)
                                if len(bins) > 1:
                                    js_global_append('''S3.supply.binnedQuantity=%s''' % sum([row.quantity for row in bins]))

                                if update_item_id not in packs:
                                    # Also send the current pack details to avoid an AJAX call
                                    iptable = s3db.supply_item_pack
                                    rows = db(iptable.item_id == update_item_id).select(iptable.id,
                                                                                        iptable.name,
                                                                                        iptable.quantity,
                                                                                        )

                                    # Simplify format
                                    packs[update_item_id] = [{"i": row.id,
                                                              "n": row.name,
                                                              "q": row.quantity,
                                                              } for row in rows]
                            if len(packs):
                                js_global_append('''S3.supply.packs=%s''' % json.dumps(packs, separators=SEPARATORS))

                s3db.configure("inv_track_item",
                               crud_form = crud_form,
                               deletable = deletable,
                               editable = editable,
                               insertable = insertable,
                               list_fields = list_fields,
                               )
        else:
            # No Component
            # Configure which fields in inv_recv are readable/writable
            # depending on status
            method = r.method
            recvtable = s3db.inv_recv
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
                if method and method != "read":
                    # Don't want to see in Create forms
                    recvtable.status.readable = False

            if method in ("create", "wizard") or \
               (method == "update" and record.status == SHIP_STATUS_IN_PROCESS):
                if s3.debug:
                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv.js" % r.application)
                else:
                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv.min.js" % r.application)
                if recvtable.transport_type.writable:
                    s3.js_global.append(
'''i18n.AWB='%s'
i18n.BL='%s'
i18n.CMR='%s'
i18n.ref='%s'
i18n.flight='%s'
i18n.vessel='%s'
i18n.vehicle='%s'
i18n.reg='%s'
''' % (T("AWB No"),
       T("B/L No"),
       T("Waybill/CMR No"),
       T("Transport Reference"),
       T("Flight"),
       T("Vessel"),
       T("Vehicle Plate Number"),
       T("Registration Number"),
       ))
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
            elif record:
                transport_type = record.transport_type
                if transport_type == "Air":
                    recvtable.transport_ref.label = T("AWB No")
                    recvtable.registration_no.label = T("Flight")
                elif transport_type == "Sea":
                    recvtable.transport_ref.label = T("B/L No")
                    recvtable.registration_no.label = T("Vessel")
                elif transport_type == "Road":
                    recvtable.transport_ref.label = T("Waybill/CMR No")
                    recvtable.registration_no.label = T("Vehicle Plate Number")
                elif transport_type == "Hand":
                    recvtable.transport_ref.readable = False
                    recvtable.registration_no.readable = False

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if r.component_name == "track_item" and \
               not r.component_id:
                # Add Action Button to Print Item Label
                if s3.actions == None:
                    # Normal Action Buttons
                    s3_action_buttons(r)
                # Custom Action Buttons
                s3.actions += [{"icon": ICON.css_class("print"),
                                "label": s3_str(T("Label")),
                                "url": URL(args = [r.id,
                                                   "track_item",
                                                   "[id]",
                                                   "label",
                                                   ],
                                           ),
                                "_class": "action-btn",
                                },
                               ]

            elif r.method == None and \
                 settings.get_inv_wizards() and \
                isinstance(output, dict):
                try:
                    # Launch Wizard, not Create form
                    output["buttons"]["add_btn"]["_href"] = URL(args = "wizard")
                except KeyError:
                    pass

        return output
    s3.postp = postp

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

# =============================================================================
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

    list_fields = ["item_id",
                   (T("Weight (kg)"), "item_id$weight"),
                   (T("Volume (m3)"), "item_id$volume"),
                   "item_source_no",
                   "item_pack_id",
                   "quantity",
                   "recv_quantity",
                   "currency",
                   "pack_value",
                   ]

    from s3.s3export import S3Exporter
    exporter = S3Exporter().pdf
    return exporter(r.resource,
                    request = r,
                    method = "list",
                    pdf_title = T(settings.get_inv_recv_form_name()),
                    pdf_filename = r.record.recv_ref,
                    list_fields = list_fields,
                    pdf_hide_comments = True,
                    pdf_componentname = "track_item",
                    pdf_header_padding = 12,
                    pdf_footer = inv_recv_pdf_footer,
                    pdf_table_autogrow = "B",
                    pdf_orientation = "Landscape",
                    **attr
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
                organisation_id = site.organisation_id
            except AttributeError:
                organisation_id = None
            from .org import org_organisation_logo
            logo = org_organisation_logo(organisation_id)
            shipment_details = TABLE(TR(TD(T(settings.get_inv_recv_form_name()),
                                           _class = "pdf_title",
                                           _colspan = 2,
                                           ),
                                        TD(logo,
                                           _colspan = 2,
                                           ),
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
            actions = DIV()
            # Find out how many inv_track_items we have for this recv record
            query = (tracktable.recv_id == recv_id) & \
                    (tracktable.deleted == False)
            cnt = current.db(query).count()

            s3 = current.response.s3
            if record.status == SHIP_STATUS_SENT or \
               record.status == SHIP_STATUS_IN_PROCESS:
                if current.auth.s3_has_permission("update", "inv_recv",
                                                  record_id = record.id,
                                                  ):
                    if settings.get_inv_wizards():
                        actions.append(A(ICON("wizard"),
                                         " ",
                                         T("Wizard"),
                                         _href = URL(args = [record.id,
                                                             "wizard",
                                                             ]
                                                     ),
                                         _class = "action-btn",
                                         )
                                       )

                    if cnt > 0:
                        actions.append(A(T("Receive Shipment"),
                                         _href = URL(args = [record.id,
                                                             "process",
                                                             ],
                                                     ),
                                         _id = "recv-process",
                                         _class = "action-btn",
                                         ))
                        s3.js_global.append('''i18n.recv_process_confirm="%s"''' % T("Do you want to receive this shipment?"))
                        if s3.debug:
                            s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv_rheader.js" % r.application)
                        else:
                            s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv_rheader.min.js" % r.application)
                    else:
                        msg = T("You need to check all item quantities and allocate to bins before you can receive the shipment")
                        rfooter.append(SPAN(msg))
            # FB: Removed as serves no useful purpose & AusRC complained about it
            #else:
            #    if record.status == SHIP_STATUS_RECEIVED:
            #        if current.auth.s3_has_permission("update", "inv_recv",
            #                                          record_id = record.id,
            #                                          ):
            #            actions.append(A(T("Cancel Shipment"),
            #                             _href = URL(args = [record.id,
            #                                                 "cancel",
            #                                                 ],
            #                                         ),
            #                             _id = "recv-cancel",
            #                             _class = "action-btn",
            #                             ))
            #            s3.js_global.append('''i18n.recv_cancel_confirm="%s"''' % T("Do you want to cancel this received shipment? The items will be removed from the Warehouse. This action CANNOT be undone!"))
            #            if s3.debug:
            #                s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv_rheader.js" % r.application)
            #            else:
            #                s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv_rheader.min.js" % r.application)
            msg = ""
            if cnt == 1:
                msg = T("This shipment contains one line item")
            elif cnt > 1:
                msg = T("This shipment contains %s items") % cnt
            shipment_details.append(TR(TH(actions,
                                          _colspan = 2,
                                          ),
                                       TD(msg),
                                       ))

            s3.rfooter = rfooter
            rheader = DIV(shipment_details,
                          rheader_tabs,
                          )
            return rheader
    return None

# ---------------------------------------------------------------------
def inv_recv_pdf_footer(r):
    """
        Default Footer for PDF of GRN
        - called by inv_recv_form
        - has come from Red Cross
    """

    T = current.T
    return DIV(TABLE(TR(TH(T("Delivered By")),
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

# =============================================================================
def inv_recv_process(r, **attr):
    """
        Receive a Shipment
        - called via POST from inv_recv_rheader
        - called via JSON method to reduce request overheads
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    recv_id = r.id
    if not recv_id:
        r.error(405, "Can only receive a single shipment.")

    auth = current.auth
    s3db = current.s3db
    rtable = s3db.inv_recv

    if not auth.s3_has_permission("update", rtable,
                                  record_id = recv_id,
                                  ):
        r.unauthorised()

    T = current.T

    record = r.record

    # Check status
    status = record.status
    if status == SHIP_STATUS_RECEIVED:
        r.error(405, T("This shipment has already been received."),
                tree = '"%s"' % URL(args = [recv_id]),
                )

    elif status == SHIP_STATUS_CANCEL:
        r.error(405, T("This shipment has already been received & subsequently canceled."),
                tree = '"%s"' % URL(args = [recv_id]),
                )

    db = current.db

    site_id = record.site_id

    settings = current.deployment_settings
    stock_cards = settings.get_inv_stock_cards()

    # Update Receive record
    data = {"status": SHIP_STATUS_RECEIVED, # Will lock for editing
            }

    if not record.recv_ref:
        # No recv_ref yet? => add one now
        from .supply import supply_get_shipping_code as get_shipping_code
        code = get_shipping_code(settings.get_inv_recv_shortname(),
                                 site_id,
                                 rtable.recv_ref,
                                 )
        data["recv_ref"] = code

    if not record.date:
        # Date not set? => set to now
        data["date"] = r.utcnow

    if not record.recipient_id:
        # The inv_recv record might be created when the shipment is sent and so it
        # might not have the recipient identified. If it is null then set it to
        # the person who is logged in (the default)
        data["recipient_id"] = auth.s3_logged_in_person()

    db(rtable.id == recv_id).update(**data)

    # Lookup the send_id from a track item of this recv
    table = s3db.inv_track_item
    track_item = db(table.recv_id == recv_id).select(table.send_id,
                                                     limitby = (0, 1),
                                                     ).first()
    if track_item:
        send_id = track_item.send_id
        if send_id:
            # Update the Send record
            db(db.inv_send.id == send_id).update(status = SHIP_STATUS_RECEIVED,
                                                 date_recvd = r.utcnow,
                                                 )

    rbtable = s3db.inv_recv_item_bin
    iitable = s3db.inv_inv_item
    ibtable = s3db.inv_inv_item_bin
    ptable = s3db.supply_item_pack

    # Get all track items for this shipment with a positive recv_quantity
    query = (table.recv_id == recv_id) & \
            (table.recv_quantity > 0)
    left = rbtable.on(rbtable.track_item_id == table.id)
    rows = db(query).select(table.id,
                            table.req_item_id,
                            table.send_inv_item_id,
                            table.item_id,
                            table.item_pack_id,
                            table.quantity,
                            table.recv_quantity,
                            table.currency,
                            table.pack_value,
                            table.expiry_date,
                            table.item_source_no,
                            table.owner_org_id,
                            table.supply_org_id,
                            table.status,
                            table.inv_item_status,
                            table.comments,
                            rbtable.layout_id,
                            rbtable.quantity,
                            left = left
                            )

    # Group by track_item_id
    track_items = {}
    item_pack_ids = []
    inv_item_ids = []
    req_item_ids = []
    for row in rows:
        track_item = row.inv_track_item
        track_item_id = track_item.id
        if track_item_id in track_items:
            track_items[track_item_id].append(row)
        else:
            track_items[track_item_id] = [row]
            item_pack_ids.append(track_item.item_pack_id)
            send_inv_item_id = track_item.send_inv_item_id
            if send_inv_item_id:
                inv_item_ids.append(send_inv_item_id)
            req_item_id = track_item.req_item_id
            if req_item_id:
                req_item_ids.append(req_item_id)

    if req_item_ids:
        # Lookup req_items which are for this Site
        # - do not update status for Requests for other Sites
        # - (i.e. assume that we are just an intermediate transit stop for such items)
        # - @ToDo: We could update the Transit Status for these, in case that hasn't yet been done
        rrtable = s3db.inv_req
        ritable = s3db.inv_req_item
        query = (ritable.id.belongs(req_item_ids)) & \
                (ritable.req_id == rrtable.id) & \
                (rrtable.site_id == site_id)
        req_items = db(query).select(ritable.id,
                                     ritable.item_pack_id,
                                     ritable.quantity_fulfil,
                                     ritable.req_id,
                                     )
        item_pack_ids += [row.item_pack_id for row in req_items]
        req_ids = [row.req_id for row in req_items]
        req_items = {row.id: row for row in req_items}

    # Lookup Packs
    packs = db(ptable.id.belongs(set(item_pack_ids))).select(ptable.id,
                                                             ptable.quantity,
                                                             )
    packs = {p.id: p.quantity for p in packs}

    if inv_item_ids:
        # Lookup sending inventory source_types
        stock_items = db(iitable.id.belongs(set(inv_item_ids))).select(iitable.id,
                                                                       iitable.source_type,
                                                                       )
        stock_items = {s.id: s.source_type for s in stock_items}

    # Move all the items into the Stock, update any Requisitions & make any Adjustments
    adj_id = None
    get_realm_entity = current.auth.get_realm_entity
    use_itn = settings.get_inv_itn_label()
    DONATION = record.type == 2
    for track_item_id in track_items:
        bins = track_items[track_item_id]
        track_item = bins[0].inv_track_item
        send_inv_item_id = track_item.send_inv_item_id
        send_quantity = track_item.quantity
        recv_quantity = track_item.recv_quantity
        item_id = track_item.item_id
        item_pack_id = track_item.item_pack_id
        pack_value = track_item.pack_value
        currency = track_item.currency
        inv_item_status = track_item.inv_item_status
        expiry_date = track_item.expiry_date
        owner_org_id = track_item.owner_org_id
        supply_org_id = track_item.supply_org_id

        # Look for the item in the site already
        query = (iitable.site_id == site_id) & \
                (iitable.item_id == item_id) & \
                (iitable.status == inv_item_status) & \
                (iitable.pack_value == pack_value) & \
                (iitable.currency == currency) & \
                (iitable.expiry_date == expiry_date) & \
                (iitable.owner_org_id == owner_org_id) & \
                (iitable.supply_org_id == supply_org_id)
        if use_itn:
            item_source_no = track_item.item_source_no
            query &= (iitable.item_source_no == track_item)
        else:
            item_source_no = None
        left = ibtable.on(ibtable.inv_item_id == iitable.id)
        inv_items = db(query).select(iitable.id,
                                     iitable.item_pack_id,
                                     iitable.quantity,
                                     ibtable.id,
                                     ibtable.layout_id,
                                     ibtable.quantity,
                                     left = left,
                                     )
        if inv_items:
            # Update the existing inv_item
            inv_item = inv_items[0].inv_inv_item
            inv_item_id = inv_item.id
            inv_pack_id = inv_item.item_pack_id
            if inv_pack_id == item_pack_id:
                pack_quantity = None
                quantity = inv_item.quantity + recv_quantity
            else:
                # Adjust Quantities
                pack_quantity = packs[item_pack_id]
                inv_pack_quantity = packs[inv_pack_id]
                quantity = inv_item.quantity + (recv_quantity * pack_quantity / inv_pack_quantity)
            inv_item.update_record(quantity = quantity)
            # Group by Bin
            inv_bins = {}
            for row in inv_items:
                bin_record = row.inv_inv_item_bin
                layout_id = bin_record.layout_id
                if layout_id:
                    inv_bins[layout_id] = bin_record
            for row in bins:
                bin_record = row.inv_recv_item_bin
                layout_id = bin_record.layout_id
                if layout_id:
                    inv_bin = inv_bins.get(layout_id)
                    if inv_bin:
                        if pack_quantity:
                            bin_quantity = inv_bin.quantity + (bin_record.quantity * pack_quantity / inv_pack_quantity)
                        else:
                            bin_quantity = inv_bin.quantity + bin_record.quantity
                        db(ibtable.id == inv_bin.id).update(bin_quantity = bin_quantity)
                    else:
                        ibtable.insert(track_item_id = track_item_id,
                                       layout_id = bin_record.layout_id,
                                       quantity = bin_record.quantity,
                                       )
        else:
            # Add a new item
            if send_inv_item_id:
                source_type = stock_items[send_inv_item_id]
            elif DONATION:
                source_type = 1 # Donation
            else:
                source_type = 2 # Procured
            inv_item = {"site_id": site_id,
                        "item_id": item_id,
                        "item_pack_id": item_pack_id,
                        "currency": currency,
                        "pack_value": pack_value,
                        "expiry_date": expiry_date,
                        "owner_org_id": owner_org_id,
                        "supply_org_id": supply_org_id,
                        "quantity": recv_quantity,
                        "item_source_no": item_source_no,
                        "source_type": source_type,
                        "status": inv_item_status,
                        }
            inv_item_id = iitable.insert(**inv_item)
            inv_item["id"] = inv_item_id
            realm_entity = get_realm_entity(iitable, inv_item)
            db(iitable.id == inv_item_id).update(realm_entity = realm_entity)
            for row in bins:
                bin_record = row.inv_recv_item_bin
                layout_id = bin_record.layout_id
                if layout_id:
                    ibtable.insert(inv_item_id = inv_item_id,
                                   layout_id = bin_record.layout_id,
                                   quantity = bin_record.quantity,
                                   )

        # If this item is linked to a Requisition, then update the quantity fulfil
        req_item_id = track_item.req_item_id
        if req_item_id:
            req_item = req_items.get(req_item_id)
            if req_item:
                # For this Site: Update status
                req_pack_id = req_item.item_pack_id
                if req_pack_id == item_pack_id:
                    quantity_fulfil = req_item.quantity_fulfil + recv_quantity
                else:
                    # Adjust Quantities
                    quantity_fulfil = req_item.quantity_fulfil + (recv_quantity * packs[item_pack_id] / packs[req_pack_id])
                req_item.update_record(quantity_fulfil = quantity_fulfil)

        # Update the track_item
        data = {"recv_inv_item_id": inv_item_id,
                "status": TRACK_STATUS_ARRIVED,
                }

        # If the receive quantity doesn't equal the sent quantity
        # then an adjustment needs to be set up
        if send_quantity != recv_quantity:
            if not adj_id:
                adj_item_table = s3db.inv_adj_item
                # Create an Adjustment for the 1st item in the Shipment, which needs adjusting
                adj_id = s3db.inv_adj.insert(adjuster_id = record.recipient_id,
                                             site_id = site_id,
                                             adjustment_date = r.utcnow.date(),
                                             category = 0,
                                             status = 1,
                                             comments = record.comments, # Shipment Comments
                                             )
            # Create the adj_item record
            adj_item_id = adj_item_table.insert(reason = 0,
                                                adj_id = adj_id,
                                                inv_item_id = send_inv_item_id,
                                                item_id = item_id,
                                                item_pack_id = item_pack_id,
                                                old_quantity = send_quantity,
                                                new_quantity = recv_quantity,
                                                currency = currency,
                                                old_pack_value = pack_value,
                                                new_pack_value = pack_value,
                                                expiry_date = expiry_date,
                                                comments = track_item.comments,
                                                )

            # Copy the adj_item_id to the track_item
            data["adj_item_id"] = adj_item_id

        db(table.id == track_item_id).update(**data)

    if req_item_ids:
        # Update Requisition Statuses
        req_ids = set(req_ids)
        for req_id in req_ids:
            inv_req_update_status(req_item.req_id)

    if settings.get_inv_warehouse_free_capacity_calculated():
        # Update the Warehouse Free capacity
        inv_warehouse_free_capacity(site_id)

    if stock_cards:
        # Reload all track_items to read the recv_inv_item_ids
        rows = db(table.recv_id == recv_id).select(table.recv_inv_item_id)
        inv_item_ids = [row.recv_inv_item_id for row in rows]
        inv_stock_card_update(inv_item_ids,
                              recv_id = recv_id,
                              comments = "Shipment Received",
                              )

    # Call on_inv_recv_process hook if-configured
    tablename = "inv_recv"
    on_inv_recv_process = s3db.get_config(tablename, "on_inv_recv_process")
    if on_inv_recv_process:
        on_inv_recv_process(record)

    # Done => confirmation message, open the record
    message = T("Shipment Items Received")
    current.session.confirmation = message

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": URL(args = [recv_id]),
                       }, separators=SEPARATORS)

# =============================================================================
def inv_req_add_from_template(req_id):
    """
        Add an Inventory Requisition from a Template
        - scheduled function to create recurring requests

        Args:
            req_id: record ID of the request template
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

# =============================================================================
def inv_req_approve(r, **attr):
    """
        Approve a Request
        - called via POST from inv_req_rfooter
        - called via JSON method to reduce request overheads
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    req_id = r.id
    if not req_id:
        r.error(405, "Can only process a single shipment.")

    auth = current.auth
    s3db = current.s3db
    rtable = s3db.inv_req

    if not auth.s3_has_permission("update", rtable,
                                  record_id = req_id,
                                  ):
        r.unauthorised()

    T = current.T
    record = r.record

    # Check we are the right place in the workflow
    if record.workflow_status != 2:
        error = T("Can only Approve Submitted Requests")
        current.session.error = error
        r.error(409, error,
                tree = '"%s"' % URL(args = [req_id]),
                )

    approvers_lookup = current.deployment_settings.get_inv_req_approvers()
    if not approvers_lookup:
        approvers_lookup = inv_req_approvers
    approvers = approvers_lookup(record)
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
        error = T("You have already Approved this Request")
        current.session.warning = error
        r.error(409, error,
                tree = '"%s"' % URL(args = [req_id]),
                )

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
                error = T("You need to Match Items in this Request")
                current.session.warning = error
                r.error(409, error,
                        tree = '"%s"' % URL(args = [req_id, "req_item"]),
                        )

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

    message = T("Request Approved")
    current.session.confirmation = message

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": URL(args = [req_id]),
                       }, separators=SEPARATORS)

# =============================================================================
def inv_req_approvers(record):
    """
        Return people permitted to Approve an Inventory Requisition

        Defaults to looking up entries in the inv_req_approver table for the
        REQ's site_id.
    """

    db = current.db
    s3db = current.s3db

    site_id = record.site_id

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
def inv_req_approvers_to_notify(record):
    """
        Return a list of Approvers to Notify for an Inventory Requisition

        Defaults to looking up entries in the inv_req_approver table for the
        REQ's site_id.
    """

    from .pr import pr_get_ancestors

    db = current.db
    s3db = current.s3db

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
    ancestors = pr_get_ancestors(pe_id)
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
                                 #ltable.user_id, # For on_req_submit hook (e.g. RMS)
                                 utable.language,
                                 )
    return approvers, site

# =============================================================================
def inv_req_copy_all(r, **attr):
    """
        Copy an existing Request
            - creates a req with req_item records

        TODO:
            Convert to POST
    """

    db = current.db
    s3db = current.s3db
    table = s3db.inv_req
    settings = current.deployment_settings
    now = current.request.utcnow

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

# =============================================================================
def inv_req_commit_all(r, **attr):
    """
        Function to commit items for a Request
        - i.e. copy data from a req into a commitment
        arg: req_id
        vars: site_id

        TODO:
            Rewrite as Method
            POST
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

# =============================================================================
def inv_req_controller(template = False):
    """
        REST Controller for Inventory Requisitions
    """

    T = current.T
    db = current.db
    s3db = current.s3db
    auth = current.auth
    response = current.response
    s3 = response.s3
    settings = current.deployment_settings

    if not template:
        # Custom Methods
        set_method = s3db.set_method
        set_method("inv", "req",
                   method = "check",
                   action = inv_ReqCheckMethod(),
                   )

        set_method("inv", "req",
                   method = "commit_all",
                   action = inv_commit_all,
                   )

        set_method("inv", "req",
                   method = "copy_all",
                   action = inv_req_copy_all,
                   )

        set_method("inv", "req",
                   component_name = "req_item",
                   method = "from",
                   action = inv_req_from,
                   )

        # Print Picking List (for settings.inv_req_reserve_items)
        set_method("inv", "req",
                   method = "pick_list",
                   action = inv_req_pick_list,
                   )

        # Submit Request for Approval
        set_method("inv", "req",
                   method = "submit",
                   action = inv_req_submit,
                   )

        # Approve Request
        set_method("inv", "req",
                   method = "approve_req", # Don't clash with core approve method
                   action = inv_req_approve,
                   )

        # Prepare Shipment from Request
        set_method("inv", "req",
                   method = "send",
                   action = inv_req_send,
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

        # Print PDF of Request Form
        set_method("inv", "req",
                   method = "form",
                   action = inv_req_form,
                   )

    def prep(r):
        table = r.table
        record = r.record

        if r.interactive:
            get_vars = r.get_vars
            if "req.site_id" in get_vars:
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
                    if r.method != "from":
                        ctable = r.component.table
                        ctable.site_id.writable = ctable.site_id.readable = False

                        if not settings.get_inv_req_item_quantities_writable():
                            ctable.quantity_commit.readable = \
                            ctable.quantity_commit.writable = False
                            ctable.quantity_transit.readable = \
                            ctable.quantity_transit.writable = False
                            ctable.quantity_fulfil.readable = \
                            ctable.quantity_fulfil.writable = False

                        use_workflow = settings.get_inv_req_workflow()
                        if use_workflow and \
                           record.workflow_status in (3, 4, 5): # Approved, Completed, Cancelled
                            # Lock all fields
                            s3db.configure("inv_req_item",
                                           deletable = False,
                                           editable = False,
                                           insertable = False,
                                           )

                        if settings.get_inv_req_reserve_items():
                            req_item_id = r.component_id
                            if not req_item_id:
                                if use_workflow:
                                    if record.workflow_status in (2, 3): # Submitted for Approval, Approved
                                        assignable = True
                                    else:
                                        assignable = False
                                else:
                                    assignable = True
                                if assignable:
                                    # Add to List Fields
                                    list_fields = r.component.get_config("list_fields")
                                    list_fields.insert(-3, "quantity_reserved")
                            else:
                                req_item = db(ctable.id == req_item_id).select(ctable.site_id,
                                                                               ctable.quantity,
                                                                               ctable.item_id,
                                                                               ctable.item_pack_id,
                                                                               limitby = (0, 1),
                                                                               ).first()
                                site_id = req_item.site_id
                                if not site_id:
                                    # Replace the NONE with a button
                                    ctable.site_id.represent = lambda v: A(T("Request from Facility"),
                                                                           _href = URL(f = "req_item",
                                                                                       args = [req_item_id,
                                                                                               "inv_item",
                                                                                               ],
                                                                                       ),
                                                                           _class = "action-btn",
                                                                           )
                                else:
                                    # Item has been allocated to come from a Site
                                    # Don't allow basic fields to be edited
                                    ctable.item_id.writable = False
                                    ctable.item_id.comment = None
                                    ctable.item_pack_id.writable = False
                                    ctable.item_pack_id.comment = None
                                    ctable.quantity.writable = False

                                    # Limit to Bins from this site with Inventory
                                    iitable = s3db.inv_inv_item
                                    ibtable = s3db.inv_inv_item_bin
                                    query = (iitable.site_id == site_id) & \
                                            (iitable.item_id == req_item.item_id) & \
                                            (iitable.quantity > 0) & \
                                            ((iitable.expiry_date >= r.utcnow) | ((iitable.expiry_date == None))) & \
                                            (iitable.status == 0)
                                    left = ibtable.on(ibtable.inv_item_id == iitable.id)
                                    inv_rows = db(query).select(iitable.id,
                                                                iitable.quantity,
                                                                iitable.item_pack_id,
                                                                ibtable.layout_id,
                                                                ibtable.quantity,
                                                                left = left,
                                                                )
                                    if inv_rows:
                                        # Allow Items to be Reserved
                                        ctable.quantity_reserved.readable = \
                                        ctable.quantity_reserved.writable = True

                                        layout_ids = []
                                        req_pack_id = req_item.item_pack_id
                                        pack_ids = [req_pack_id]
                                        # Sort by inv_item_id
                                        inv_items = {}
                                        for row in inv_rows:
                                            inv_item = row.inv_inv_item
                                            inv_item_id = inv_item.id
                                            if inv_item_id not in inv_items:
                                                pack_id = inv_item.item_pack_id
                                                if pack_id not in pack_ids:
                                                    pack_ids.append(pack_id)
                                                inv_items[inv_item_id] = {"q": inv_item.quantity,
                                                                          "p": pack_id,
                                                                          "b": {},
                                                                          }
                                            item_bin = row.inv_inv_item_bin
                                            layout_id = item_bin.layout_id
                                            if layout_id:
                                                inv_items[inv_item_id]["b"][layout_id] = item_bin.quantity

                                        stock_quantity = 0

                                        # Lookup Packs
                                        ptable = s3db.supply_item_pack
                                        len_pack_ids = len(pack_ids)
                                        if len_pack_ids == 1:
                                            query = (ptable.id == pack_ids[0])
                                            fields = [ptable.name]
                                        else:
                                            query = (ptable.id.belongs(pack_ids))
                                            fields = [ptable.id,
                                                      ptable.name,
                                                      ptable.quantity,
                                                      ]
                                        packs = db(query).select(*fields,
                                                                 limitby = (0, len_pack_ids),
                                                                 )
                                        if len_pack_ids == 1:
                                            # No need to adjust Inventory Quantity to match Req Quantity
                                            pack_name = packs.first().name
                                            for inv_item_id in inv_items:
                                                inv_item = inv_items[inv_item_id]
                                                stock_quantity += inv_item["q"]
                                        else:
                                            # Adjust Inventory Quantity to match Req Quantity
                                            packs = {p.id: {n: p.name,
                                                            q: p.quantity,
                                                            } for p in packs}
                                            req_pack = packs[req_pack_id]
                                            pack_name = req_pack["n"]
                                            req_pack_quantity = req_pack["q"]
                                            for inv_item_id in inv_items:
                                                inv_item = inv_items[inv_item_id]
                                                inv_pack_id = inv_item["p"]
                                                if inv_pack_id == req_pack_id:
                                                    stock_quantity += inv_item["q"]
                                                else:
                                                    inv_pack_quantity = packs[inv_pack_id]["q"]
                                                    inv_quantity = inv_item["q"]
                                                    inv_quantity = inv_quantity * inv_pack_quantity / req_pack_quantity
                                                    inv_item["q"] = inv_quantity
                                                    stock_quantity += inv_quantity
                                                    inv_bins = inv_item["b"]
                                                    for layout_id in inv_bins:
                                                        bin_quantity = inv_bins[layout_id]
                                                        bin_quantity = bin_quantity * inv_pack_quantity / req_pack_quantity
                                                        inv_bins[layout_id] = bin_quantity
                                                del inv_item["p"]

                                        rbtable = s3db.inv_req_item_inv
                                        req_bins = db(rbtable.req_item_id == req_item_id).select(rbtable.inv_item_id,
                                                                                                 rbtable.layout_id,
                                                                                                 rbtable.quantity,
                                                                                                 )
                                        binned_quantity = sum([row.quantity for row in req_bins])

                                        inv_fields = ["inv_item_id",
                                                      "quantity",
                                                      ]

                                        layout_ids = set([row["inv_inv_item_bin.layout_id"] for row in inv_rows] + [row.layout_id for row in req_bins])
                                        layout_ids_len = len(layout_ids)
                                        if layout_ids_len:
                                            # Add/Filter Bin field
                                            inv_fields.insert(1, "layout_id")

                                            field = rbtable.layout_id
                                            requires = field.requires
                                            if hasattr(requires, "other"):
                                                requires.other.set_filter(filterby = "id",
                                                                          filter_opts = layout_ids,
                                                                          )
                                            else:
                                                requires.set_filter(filterby = "id",
                                                                    filter_opts = layout_ids,
                                                                    )
                                            if layout_ids_len == 1:
                                                field.widget.filter = (s3db.org_site_layout.id == list(layout_ids)[0])
                                            else:
                                                field.widget.filter = (s3db.org_site_layout.id.belongs(layout_ids))

                                        rbtable.inv_item_id.requires.set_filter(filterby = "id",
                                                                                filter_opts = inv_items,
                                                                                )

                                        crud_form = S3SQLCustomForm("item_id",
                                                                    "item_pack_id",
                                                                    "quantity",
                                                                    "quantity_reserved",
                                                                    "site_id",
                                                                    S3SQLInlineComponent("req_item_inv",
                                                                                         label = T("Assign from Inventory"),
                                                                                         fields = inv_fields,
                                                                                         ),
                                                                    "comments",
                                                                    # Remove Reserved Items from Stock
                                                                    postprocess = inv_req_item_postprocess,
                                                                    )
                                        s3db.configure("inv_req_item",
                                                       crud_form = crud_form,
                                                       )

                                        # @ToDo:
                                        # Add to list_fields

                                        # Pass data to s3.inv_req_item.js
                                        # - show stock quantity
                                        # - manage bins
                                        req_data = {"q": stock_quantity,
                                                    "r": req_item.quantity,
                                                    "p": pack_name,
                                                    "s": site_id,
                                                    "i": inv_items,
                                                    }
                                        if binned_quantity:
                                            req_data["b"] = binned_quantity
                                        s3.js_global.append('''S3.supply.reqData=%s''' % json.dumps(req_data, separators=SEPARATORS))
                                    else:
                                        response.error = T("The Site Requested From has no Inventory available of this Item")

                elif r.component.alias == "job":
                    current.s3task.configure_tasktable_crud(
                        function = "inv_req_add_from_template",
                        args = [r.id],
                        vars = {"user_id": 0 if auth.user is None else auth.user.id},
                        period = 86400, # seconds, so 1 day
                        )
                    db.scheduler_task.timeout.writable = False
            else:
                if r.id:
                    table.is_template.readable = table.is_template.writable = False

                if not table.requester_id.writable:
                    table.requester_id.comment = None

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
                    inv_req_create_form_mods(r)

                    if settings.get_inv_req_inline_forms():
                        # Use inline form
                        inv_req_inline_form(method)

                    # Get the default Facility for this user
                    # Use site_id in User Profile
                    if auth.is_logged_in() and not table.site_id.default:
                        table.site_id.default = auth.user.site_id

                elif method in ("update", "read"):
                    if settings.get_inv_req_inline_forms():
                        # Use inline form
                        inv_req_inline_form(method)

                    if settings.get_inv_req_workflow():
                        workflow_status = record.workflow_status if record else None
                        if workflow_status in (1, 2, 5): # Draft, Submitted, Cancelled
                            # Hide individual statuses
                            table = db.inv_req
                            table.commit_status.readable = table.commit_status.writable = False
                            table.transit_status.readable = table.transit_status.writable = False
                            table.fulfil_status.readable = table.fulfil_status.writable = False
                        else:
                            # Block Delete
                            s3db.configure("inv_req",
                                           deletable = False,
                                           )
                        if workflow_status in (3, 4, 5): # Approved, Completed, Cancelled
                            # Lock all fields
                            s3db.configure("inv_req",
                                           editable = False,
                                           )

                elif method == "map":
                    # Tell the client to request per-feature markers
                    s3db.configure("inv_req",
                                   marker_fn = inv_req_marker_fn,
                                   )

        elif r.representation == "plain":
            # Map Popups
            pass

        elif r.representation == "geojson":
            table.req_ref.represent = inv_ReqRefRepresent()
            # Load these models now as they'll be needed when we encode
            mtable = s3db.gis_marker
            s3db.configure("inv_req",
                           marker_fn = inv_req_marker_fn,
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

                # @ToDo: We shouldn't need to use permitted_facilities here
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
                            redirect(r.url(component = "",
                                           method = "",
                                           ))
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
                    crud_form = S3SQLCustomForm("site_id",
                                                "date",
                                                "date_available",
                                                "committer_id",
                                                S3SQLInlineComponent("commit_item",
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
                    s3_action_buttons(r,
                                      deletable = s3db.get_config(r.component.tablename, "deletable"),
                                      )
                    if r.component_name == "req_item" and \
                       settings.get_inv_req_prompt_match():
                        # Allow Items to be re-matched later (e.g. for Intermediate Hops), or just a change of plan
                        #table = r.component.table
                        #query = (table.site_id == None) & \
                        #        (table.deleted == False)
                        #rows = db(query).select(table.id)
                        #restrict = [str(row.id) for row in rows]
                        s3.actions.append({"label": s3_str(T("Request from Facility")),
                                           "url": URL(c = "inv",
                                                      f = "req_item",
                                                      args = ["[id]", "inv_item"],
                                                      ),
                                           "_class": "action-btn",
                                           #"restrict": restrict,
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
                                               _id = "commit-all",
                                               )
                                # Assumes that s3.inv_rheader.js included by inv_req_rheader
                                s3.js_global.append('''i18n.commit-all="%s"''' \
                                                % T("Do you want to commit to this request?"))
                            # Items
                            s3.actions.append({"label": s3_str(T("Prepare Shipment")),
                                               "url": URL(c = "inv",
                                                          f = "commit",
                                                          args = ["[id]", "send"],
                                                          ),
                                               "_class": "action-btn send-btn",
                                               })
                            # Convert to POST
                            if s3.debug:
                                s3.scripts.append("/%s/static/scripts/S3/s3.inv_commit.js" % r.application)
                            else:
                                s3.scripts.append("/%s/static/scripts/S3/s3.inv_commit.min.js" % r.application)

                    elif r.component.alias == "job":
                        record_id = r.id
                        # @ToDo: Switch Action buttons which change data to POST
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
                    if r.http == "POST" and r.method == "create":
                        # Create form
                        # @ToDo: DRY
                        if not settings.get_inv_req_inline_forms():
                            form_vars = output["form"].vars
                            # Stock: Open Tab for Items
                            r.next = URL(args = [form_vars.id, "req_item"])
                    else:
                        s3_action_buttons(r, deletable=False)
                        # @ToDo: Switch Action buttons which change data to POST
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
                                                   #           f = "req",
                                                   #           args = ["[id]", "send"],
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

    return current.rest_controller("inv", "req",
                                   rheader = inv_req_rheader,
                                   )

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

    return NONE

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
                                       stable.registration_no,
                                       )
    if drivers:
        drivers = ["%s %s %s" % (driver.driver_name or "",
                                 driver.driver_phone or "",
                                 driver.registration_no or "") \
                   for driver in drivers]
        return ",".join(drivers)

    return NONE

# =============================================================================
def inv_req_form(r, **attr):
    """
        Generate a PDF of a Request Form
    """

    pdf_componentname = "req_item"
    list_fields = ["item_id",
                   "item_pack_id",
                   "quantity",
                   "quantity_commit",
                   "quantity_transit",
                   "quantity_fulfil",
                   ]

    if current.deployment_settings.get_inv_use_req_number():
        filename = r.record.req_ref
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
                    #pdf_footer = inv_req_pdf_footer,
                    pdf_table_autogrow = "B",
                    pdf_orientation = "Landscape",
                    **attr
                    )

# =============================================================================
def inv_req_submit(r, **attr):
    """
        Submit a Request for Approval
        - called via POST from inv_req_rfooter
        - called via JSON method to reduce request overheads
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    req_id = r.id
    if not req_id:
        r.error(405, "Can only submit a single request")

    auth = current.auth
    s3db = current.s3db
    rtable = s3db.inv_req

    if not auth.s3_has_permission("update", rtable,
                                  record_id = req_id,
                                  ):
        r.unauthorised()

    T = current.T
    record = r.record

    # Check we are the right place in the workflow
    if record.workflow_status != 1:
        error = T("Can only Submit Draft Requests")
        current.session.error = error
        r.error(409, error,
                tree = '"%s"' % URL(args = [req_id]),
                )

    db = current.db

    # Lookup Approver(s)
    approvers_to_notify = current.deployment_settings.get_inv_req_approvers_to_notify()
    if not approvers_to_notify:
        approvers_to_notify = inv_req_approvers_to_notify
    approvers, site = approvers_to_notify(record)
    if not approvers:
        error = T("No Request Approver defined")
        current.session.error = error
        r.error(409, error,
                tree = '"%s"' % URL(args = [req_id]),
                )

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

    message = T("Request submitted for Approval")
    current.session.confirmation = message

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": URL(args = [req_id]),
                       }, separators=SEPARATORS)

# =============================================================================
def inv_req_from(r, **attr):
    """
        Request From Inventory
        - called via POST from inv_req_item_inv_item
        - called via JSON method to reduce request overheads
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    inv_item_id = r.get_vars.get("inv_item_id").split(".json")[0]
    if not inv_item_id:
        r.error(405, "Inventory Item missing!")

    req_item_id = r.component_id
    if not req_item_id:
        r.error(405, "Can only request a single item at once from Inventory")

    if not current.auth.s3_has_permission("update", "inv_req_item",
                                          record_id = req_item_id,
                                          ):
        r.unauthorised()

    req_id = r.id

    db = current.db
    s3db = current.s3db

    # Set the req_item.site_id (Requested From)
    iitable = s3db.inv_inv_item
    inv_item = db(iitable.id == inv_item_id).select(iitable.site_id,
                                                    iitable.item_id,
                                                    limitby = (0, 1),
                                                    ).first()
    site_id = inv_item.site_id
    db(s3db.inv_req_item.id == req_item_id).update(site_id = site_id)
    onaccepts = s3db.get_config("inv_req_item", "onaccept")
    if onaccepts:
        form = Storage(vars = Storage(id = req_item_id,
                                      req_id = req_id,
                                      site_id = site_id, # For custom onaccepts (e.g. to set realm_entity)
                                      ),
                       record = Storage(site_id = r.record.site_id),
                       )
        if not isinstance(onaccepts, (list, tuple)):
            onaccepts = [onaccepts]
        [onaccept(form) for onaccept in onaccepts]

    from .org import org_SiteRepresent
    from .supply import supply_ItemRepresent

    message = current.T("%(item)s requested from %(site)s") % \
        {"item": supply_ItemRepresent()(inv_item.item_id),
         "site": org_SiteRepresent()(site_id)
         }
    current.session.confirmation = message

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": URL(args = [req_id, "req_item"]),
                       }, separators=SEPARATORS)

# =============================================================================
def inv_req_inline_form(method):
    """
        Function to be called from REST prep functions
         - to add req_item components as inline forms

        Args:
            method: the URL request method
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
              S3SQLInlineComponent("req_item",
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
def inv_req_is_approver(record):
    """
        Check if User has permission to Approve an Inventory Requisition

        Defaults to looking up entries in the inv_req_approver table for the
        REQ's site_id.
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

    site_id = record.site_id
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
    from .pr import pr_get_descendants
    entity_types = ["org_organisation"] + list(auth.org_site_types.keys())
    child_pe_ids = pr_get_descendants(pe_ids, entity_types=entity_types)
    if pe_id in child_pe_ids:
        # Permitted via child entity
        return True

    return False

# =============================================================================
def inv_req_job_reset(r, **attr):
    """
        Reset a job status from FAILED to QUEUED
        for "Reset" action button

        @ToDo: POST
    """

    if r.interactive:
        if r.component and r.component.alias == "job":
            job_id = r.component_id
            if job_id:
                S3Task.reset(job_id)
                current.session.confirmation = current.T("Job reactivated")

    redirect(r.url(method = "",
                   component_id = 0,
                   ))

# =============================================================================
def inv_req_job_run(r, **attr):
    """
        Run a job now
        for "Run Now" action button

        @ToDo: POST
    """

    if r.interactive:
        if r.id:
            current.s3task.run_async("inv_req_add_from_template",
                                     [r.id], # args
                                     {"user_id":current.auth.user.id} # vars
                                     )
            current.session.confirmation = current.T("Request added")

    redirect(r.url(method = "",
                   component_id = 0,
                   ))

# =============================================================================
def inv_req_item_inv_item(r, **attr):
    """
        Shows the inventory items which match a requested item
    """

    T = current.T
    db = current.db
    s3db = current.s3db
    response = current.response
    s3 = response.s3

    req_item_id  = r.id

    record = r.record
    req_id = record.req_id

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

    item_id = record.item_id

    output["req_item"] = TABLE(TR(TH( "%s: " % T("Requested By") ),
                                  rtable.site_id.represent(site_id),
                                  TH( "%s: " % T("Item")),
                                  s3db.inv_req_item.item_id.represent(item_id),
                                  ),
                               TR(TH( "%s: " % T("Requester") ),
                                  rtable.requester_id.represent(req.requester_id),
                                  TH( "%s: " % T("Quantity")),
                                  record.quantity,
                                  ),
                               TR(TH( "%s: " % T("Date Requested") ),
                                  rtable.date.represent(req.date),
                                  TH( T("Quantity Committed")),
                                  record.quantity_commit,
                                  ),
                               TR(TH( "%s: " % T("Date Required") ),
                                  rtable.date_required.represent(req.date_required),
                                  TH( "%s: " % T("Quantity in Transit")),
                                  record.quantity_transit,
                                  ),
                               TR(TH( "%s: " % T("Priority") ),
                                  rtable.priority.represent(req.priority),
                                  TH( "%s: " % T("Quantity Fulfilled")),
                                  record.quantity_fulfil,
                                  )
                               )

    s3.no_sspag = True # pagination won't work with 2 datatables on one page @todo: test

    iitable = s3db.inv_inv_item
    # Get list of matching inventory items
    s3.filter = (iitable.item_id == item_id) & \
                (iitable.site_id != site_id) & \
                (iitable.quantity > 0) & \
                ((iitable.expiry_date >= r.utcnow) | ((iitable.expiry_date == None))) & \
                (iitable.status == 0)
    # Tweak CRUD String for this context
    s3.crud_strings["inv_inv_item"].msg_list_empty = T("No Inventories currently have this item in stock")

    current.request.args = []
    s3.postp = None
    inv_items = current.rest_controller("inv", "inv_item")
    output["items"] = inv_items["items"]

    settings = current.deployment_settings
    if settings.get_supply_use_alt_name():
        # Get list of alternative inventory items
        atable = s3db.supply_item_alt
        alt_item_rows = db(atable.item_id == item_id).select(atable.alt_item_id)
        alt_item_ids = [alt_item_row.alt_item_id for alt_item_row in alt_item_rows]

        if alt_item_ids:
            s3.filter = (iitable.item_id.belongs(alt_item_ids))
            inv_items_alt = current.rest_controller("inv", "inv_item")
            output["items_alt"] = inv_items_alt["items"]
        else:
            output["items_alt"] = T("No Inventories currently have suitable alternative items in stock")
    else:
        output["items_alt"] = None

    if settings.get_inv_req_order_item():
        output["order_btn"] = A(T("Order Item"),
                                _href = URL(args = [req_item_id,
                                                    "order",
                                                    ]
                                            ),
                                _id = "req-order",
                                _class = "action-btn",
                                )
    else:
        output["order_btn"] = None

    s3.action_methods = ("inv_item",)
    s3.actions = [{"label": s3_str(T("Request From")),
                   "url": URL(f = "req",
                              args = [req_id,
                                      "req_item",
                                      req_item_id,
                                      "from",
                                      ],
                              vars = {"inv_item_id": "[id]"},
                              ),
                   "_class": "action-btn req-from",
                   },
                  ]

    # Convert to POST
    if s3.debug:
        s3.scripts.append("/%s/static/scripts/S3/s3.inv_req_item_inv_item.js" % r.application)
    else:
        s3.scripts.append("/%s/static/scripts/S3/s3.inv_req_item_inv_item.min.js" % r.application)

    response.view = "inv/req_item_inv_item.html"
    return output
    
# =============================================================================
def inv_req_item_order(r, **attr):
    """
        Create an inv_order_item from a inv_req_item
        - called via POST from inv_req_item_inv_item
        - called via JSON method to reduce request overheads
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    record = r.record
    req_id = record.req_id

    current.s3db.inv_order_item.insert(req_item_id = record.id,
                                       req_id = req_id,
                                       item_id = record.item_id,
                                       item_pack_id = record.item_pack_id,
                                       quantity = record.quantity,
                                       )

    message = current.T("Item added to your list of Purchases")
    current.session.confirmation = message

    # Redirect back to the Request's Items tab
    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": URL(c = "inv",
                                   f = "req",
                                   args = [req_id, "req_item"],
                                   ),
                       }, separators=SEPARATORS)

# =============================================================================
def inv_req_item_postprocess(form):
    """
        Called when using settings.inv.req_reserve_items
        - remove reserved items from stock

        If the stock to take from hasn't been selected then we auto-allocate.
        We optimise to use the stock which expires soonest

        If the bin to take from hasn't been selected then we auto-allocate.
        We optimise to minimise the number of Bins remaining for an Item
        (An alternative would be to optimise this Pick)

        Stock cards, Request Status and Warehouse Free Capacity not updated until
        Shipment actually Sent (inv_send_process)
    """

    record = form.record
    req_item_id = form.vars.id

    db = current.db
    s3db = current.s3db

    table = s3db.inv_req_item
    rbtable = s3db.inv_req_item_inv
    iitable = s3db.inv_inv_item
    ibtable = s3db.inv_inv_item_bin
    iptable = s3db.supply_item_pack

    # Read the Request Item, including Stock Reservations
    query = (table.id == req_item_id) & \
            (table.item_pack_id == iptable.id)
    left = rbtable.on(rbtable.req_item_id == table.id)
    rows = db(query).select(table.site_id,
                            table.item_id,
                            table.quantity_reserved,
                            iptable.quantity,
                            rbtable.id,
                            rbtable.inv_item_id,
                            rbtable.layout_id,
                            rbtable.quantity,
                            left = left,
                            )

    # Sort by Inv Item ID
    row = rows.first()
    req_item_row = row["inv_req_item"]
    quantity_reserved = req_item_row.quantity_reserved
    pack_row = row["supply_item_pack"]
    req_pack_quantity = pack_row.quantity
    inv_reservations = {}
    reserved_quantity = 0
    binned_quantity = 0
    for row in rows:
        inv_row = row["inv_req_item_inv"]
        inv_quantity = inv_row.quantity
        if inv_quantity:
            inv_item_id = inv_row.inv_item_id
            if inv_item_id not in inv_reservations:
                inv_reservations[inv_item_id] = {"bins": {},
                                                 "quantity": 0,
                                                 "binned_quantity": 0,
                                                 }
            inv_reservations[inv_item_id]["quantity"] += inv_quantity
            reserved_quantity += inv_quantity
            layout_id = inv_row.layout_id
            if layout_id:
                binned_quantity += inv_quantity
                inv_reservations[inv_item_id]["binned_quantity"] += inv_quantity
            inv_reservations[inv_item_id]["bins"][layout_id] = {"id": inv_row.id,
                                                                "layout_id": layout_id,
                                                                "quantity": inv_quantity,
                                                                }

    # Read the Inv Items, including Bins
    if reserved_quantity == quantity_reserved:
        # Reservation has been completely allocated to stock items
        if len(inv_reservations) == 1:
            query = (iitable.id == list(inv_reservations)[0])
        else:
            query = (iitable.id.belongs(inv_reservations))
    else:
        # We need to auto-allocate some of the stock
        query = (iitable.site_id == req_item_row.site_id) & \
                (iitable.item_id == req_item_row.item_id) & \
                (iitable.quantity > 0) & \
                ((iitable.expiry_date >= current.request.utcnow) | ((iitable.expiry_date == None))) & \
                (iitable.status == 0)

    query &= (iitable.item_pack_id == iptable.id)
    left = ibtable.on(ibtable.inv_item_id == iitable.id)
    rows = db(query).select(iitable.id,
                            iitable.quantity,
                            iitable.expiry_date,
                            iptable.quantity,
                            ibtable.id,
                            ibtable.layout_id,
                            ibtable.quantity,
                            left = left,
                            )

    # Sort by Inv Item ID
    inv_items_dict = {}
    for row in rows:
        inv_row = row["inv_inv_item"]
        inv_item_id = inv_row.id
        if inv_item_id not in inv_items_dict:
            inv_items_dict[inv_item_id] = {"id": inv_item_id,
                                           "expiry_date": inv_row.expiry_date,
                                           "quantity": inv_row.quantity,
                                           "pack_quantity": row["supply_item_pack.quantity"],
                                           "bins": [],
                                           }
        bin_row = row["inv_inv_item_bin"]
        bin_quantity = bin_row.quantity
        if bin_quantity:
            inv_items_dict[inv_item_id]["bins"].append({"id": bin_row.id,
                                                        "layout_id": bin_row.layout_id,
                                                        "quantity": bin_quantity,
                                                        })

    # Convert to list to sort by Expiry Date
    inv_items = []
    iiappend = inv_items.append
    for inv_item_id in inv_items_dict:
        iiappend(inv_items_dict[inv_item_id])

    #if record: # will always be an update form
    # Read the old Reservations Data
    old_inv = {}
    old_inv_data = record.sub_defaultreq_item_inv
    if old_inv_data:
        old_inv_data = json.loads(old_inv_data) or {}
        old_inv_data = old_inv_data.get("data", [])
        for row in old_inv_data:
            inv_quantity = row["quantity"]["value"]
            if inv_quantity:
                inv_quantity = float(inv_quantity)
                inv_item_id = row["inv_item_id"]["value"]
                if inv_item_id not in old_inv:
                    old_inv[inv_item_id] = {"bins": {},
                                            "quantity": 0,
                                            }
                old_inv[inv_item_id]["quantity"] += inv_quantity
                layout_id = row["layout_id"]["value"]
                if layout_id:
                    old_inv[inv_item_id]["bins"][layout_id] = inv_quantity

    from operator import itemgetter
    if quantity_reserved > reserved_quantity:
        # Auto-allocate Stock
        # - optimise to use stock with higher Expiry Date first
        inv_items.sort(key = itemgetter("expiry_date"),
                       reverse = True,
                       )
        to_allocate = (quantity_reserved - reserved_quantity) * req_pack_quantity
        while (to_allocate > 0):
            for inv_item in inv_items:
                inv_item_id = inv_item["id"]
                inv_pack_quantity = inv_item["pack_quantity"]
                inv_quantity = inv_item["quantity"] * inv_pack_quantity
                #if record# Always an Update form                
                # Add previously allocated inventory
                old_inv_row = old_inv.get(inv_item_id)
                if old_inv_row:
                    old_quantity = old_inv_row["quantity"]
                    if old_quantity:
                        inv_quantity += (old_quantity * inv_pack_quantity)
                if inv_item_id in inv_reservations:
                    req_inv = inv_reservations[inv_item_id]
                    reservation_quantity = req_inv["quantity"] * req_pack_quantity
                    if inv_quantity > reservation_quantity:
                        # Allocate more of this stock
                        if inv_quantity >= (to_allocate + reservation_quantity):
                            # Allocate all from this stock
                            new_quantity = (to_allocate + reservation_quantity) / req_pack_quantity
                            req_inv["quantity"] = new_quantity
                            to_allocate = 0
                            break
                        else:
                            # Allocate what we can from this stock
                            new_quantity = inv_quantity / req_pack_quantity
                            req_inv["quantity"] = new_quantity
                            to_allocate -= (inv_quantity - reservation_quantity)
                else:
                    if inv_quantity >= to_allocate:
                        # Allocate all from this stock
                        new_quantity = to_allocate / req_pack_quantity
                        inv_reservations[inv_item_id] = {"bins": {},
                                                         "quantity": new_quantity,
                                                         "binned_quantity": 0,
                                                         }
                        to_allocate = 0
                        break
                    else:
                        # Allocate what we can from this stock
                        new_quantity = inv_quantity / req_pack_quantity
                        inv_reservations[inv_item_id] = {"bins": {},
                                                         "quantity": new_quantity,
                                                         "binned_quantity": 0,
                                                         }
                        to_allocate -= inv_quantity

    if quantity_reserved > binned_quantity:
        # Auto-allocate Bins
        # - optimise to use bins with lower quantity first
        to_allocate = (quantity_reserved - binned_quantity) * req_pack_quantity
        while (to_allocate > 0):
            for inv_item_id in inv_reservations:
                req_inv = inv_reservations[inv_item_id]
                reservation_quantity = req_inv["quantity"]
                binned_quantity = req_inv["binned_quantity"]
                unbinned_quantity = reservation_quantity - binned_quantity
                if not unbinned_quantity:
                    # This Item is fully allocated from bins
                    continue
                #if record# Always an Update form                
                # Add previously allocated inventory
                old_inv_row = old_inv.get(inv_item_id)
                if old_inv_row:
                    old_quantity = old_inv_row["quantity"]
                    if old_quantity:
                        old_bins = old_inv_row["bins"]
                    else:
                        old_bins = {}
                else:
                    old_bins = {}
                req_bins = req_inv["bins"]
                inv_item = inv_items_dict[inv_item_id]
                inv_pack_quantity = inv_item["pack_quantity"]
                inv_bins = inv_item["bins"]
                inv_bins.sort(key = itemgetter("quantity"))
                while (unbinned_quantity > 0):
                    for inv_bin in inv_bins:
                        layout_id = inv_bin["layout_id"]
                        inv_quantity = inv_bin["quantity"] * inv_pack_quantity
                        old_quantity = old_bins.get(layout_id)
                        if old_quantity:
                            inv_quantity += (old_quantity * inv_pack_quantity)
                        if layout_id in req_bins:
                            req_bin = req_bins[layout_id]
                            reservation_quantity = req_bin["quantity"] * req_pack_quantity
                            if inv_quantity > reservation_quantity:
                                # Allocate more from this bin
                                if inv_quantity >= (unbinned_quantity + reservation_quantity):
                                    # Allocate all from this bin
                                    new_quantity = (unbinned_quantity + reservation_quantity) / req_pack_quantity
                                    req_bin["quantity"] = new_quantity
                                    db(rbtable.id == req_bin["id"]).update(quantity = new_quantity)
                                    to_allocate -= unbinned_quantity
                                    unbinned_quantity = 0
                                    break
                                else:
                                    # Allocate what we can from this bin
                                    new_quantity = inv_quantity / req_pack_quantity
                                    req_bin["quantity"] = new_quantity
                                    db(rbtable.id == req_bin["id"]).update(quantity = new_quantity)
                                    to_allocate -= (inv_quantity - reservation_quantity)
                                    unbinned_quantity -= (inv_quantity - reservation_quantity)
                        else:
                            if inv_quantity >= unbinned_quantity:
                                # Allocate all from this bin
                                new_quantity = unbinned_quantity / req_pack_quantity
                                bin_id = rbtable.insert(req_item_id = req_item_id,
                                                        inv_item_id = inv_item_id,
                                                        layout_id = layout_id,
                                                        quantity = new_quantity,
                                                        )
                                req_bins[layout_id] = {"id": bin_id,
                                                       "quantity": new_quantity,
                                                       }
                                to_allocate -= unbinned_quantity
                                unbinned_quantity = 0
                                break
                            else:
                                # Allocate what we can from this bin
                                new_quantity = inv_quantity / req_pack_quantity
                                bin_id = rbtable.insert(req_item_id = req_item_id,
                                                        inv_item_id = inv_item_id,
                                                        layout_id = layout_id,
                                                        quantity = new_quantity,
                                                        )
                                req_bins[layout_id] = {"id": bin_id,
                                                       "quantity": new_quantity,
                                                       }
                                to_allocate -= inv_quantity
                                unbinned_quantity -= inv_quantity
                    req_inv["bins"] = req_bins
                    if unbinned_quantity > 0:
                        # Allocate from unbinned Stock
                        if None in req_bins:
                            # Allocate more from unbinned
                            req_bin = req_bins[None]
                            reservation_quantity = req_bin["quantity"] * req_pack_quantity
                            new_quantity = (unbinned_quantity + reservation_quantity) / req_pack_quantity
                            req_bin["quantity"] = new_quantity
                            db(rbtable.id == req_bin["id"]).update(quantity = new_quantity)
                        else:
                            # Allocate some from unbinned
                            new_quantity = unbinned_quantity / req_pack_quantity
                            bin_id = rbtable.insert(req_item_id = req_item_id,
                                                    inv_item_id = inv_item_id,
                                                    layout_id = None,
                                                    quantity = new_quantity,
                                                    )
                            req_bins[None] = {"id": bin_id,
                                              "quantity": new_quantity,
                                              }
                        to_allocate -= unbinned_quantity

    # Update Stock levels
    # @ToDo: Complete
    for inv_item_id in inv_reservations:
        inv_item = inv_items_dict[inv_item_id]
        inv_pack_quantity = inv_item["pack_quantity"]
        inv_total_quantity = inv_item["quantity"]
        req_inv = inv_reservations[inv_item_id]
        reservation_quantity = req_inv["quantity"]
        new_inv_quantity = ((inv_total_quantity * inv_pack_quantity)  + (record.quantity_reserved * req_pack_quantity) - (reservation_quantity * req_pack_quantity)) / inv_pack_quantity
        db(iitable.id == inv_item_id).update(quantity = new_inv_quantity)

        # Update Bins
        req_bins = req_inv["bins"]
        inv_bins = inv_item["bins"]
        old_inv_row = old_inv.get(inv_item_id)
        if old_inv_row:
            old_bins = old_inv_row.get("bins")
        else:
            old_bins = {}
        for inv_bin in inv_bins:
            layout_id = inv_bin["layout_id"]
            old_bin = old_bins.get(layout_id)
            req_bin = req_bins.get(layout_id)
            if req_bin and not old_bin:
                new_bin_quantity = ((inv_bin["quantity"] * inv_pack_quantity) - (req_bin["quantity"] * req_pack_quantity)) / inv_pack_quantity
                db(ibtable.id == inv_bin["id"]).update(quantity = new_bin_quantity)
            elif old_bin and not req_bin:
                new_bin_quantity = ((inv_bin["quantity"] * inv_pack_quantity) + (old_bin * req_pack_quantity)) / inv_pack_quantity
                db(ibtable.id == inv_bin["id"]).update(quantity = new_bin_quantity)
            elif req_bin and old_bin:
                new_bin_quantity = ((inv_bin["quantity"] * inv_pack_quantity) + (old_bin * req_pack_quantity) - (req_bin["quantity"] * req_pack_quantity)) / inv_pack_quantity
                db(ibtable.id == inv_bin["id"]).update(quantity = new_bin_quantity)

# =============================================================================
def inv_req_marker_fn(record):
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

    db = current.db
    mtable = db.gis_marker
    marker = db(mtable.name == marker).select(mtable.image,
                                              mtable.height,
                                              mtable.width,
                                              cache = current.s3db.cache,
                                              limitby = (0, 1),
                                              ).first()
    return marker

# =============================================================================
def inv_req_match(rheader = None):
    """
        Generic controller to display all Inventory Requisitions a site could potentially
        fulfill as a tab of that site instance
            - add as inv_req_match controller to the module, then
            - configure as rheader-tab "inv_req_match/" for the site resource

        Args:
            rheader: module-specific rheader

        Note:
            Make sure rheader uses s3_rheader_resource to handle "viewing"
            Can override rheader in customise_inv_req_controller by
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
                            "url": URL(c="inv", f="req",
                                       args = ["[id]", "commit_all"],
                                       vars = {"site_id": site_id,
                                               }
                                       ),
                            "_class": "action-btn",
                            })
        # Better to force people to go through the Check process
        #actions.append({"label": s3_str(T("Send")),
        #                "url": URL(c="inv", f="req",
        #                           args = ["[id]", "send"],
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
        elif tablename == "med_hospital":
            from .med import med_hospital_rheader
            rheader = med_hospital_rheader

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
def inv_req_pick_list(r, **attr):
    """
        Generate a Picking List for an Inventory Requisition
        - for settings.inv_req_reserve_items

        In order to order this list for optimal picking, we assume that the Bins are
        strctured as Aisle/Site/Shelf with the Aisle being the gap between Racks as per Figure 2 in:
        http://www.appriseconsulting.co.uk/warehouse-layout-and-pick-sequence/
        We assume that Racks are numbered to match Figure 2, so we can do a simple sort on the Bin

        Currently this is exported in XLS format

        TODO:
            Provide an on-screen version
            Optimise Picking Route (as per Figure 3 in the above link)
    """

    req_id = r.id
    record = r.record

    from s3.codecs.xls import S3XLS

    try:
        import xlwt
    except ImportError:
        r.error(503, S3XLS.ERROR.XLWT_ERROR)

    # Extract the Data
    req_ref = record.req_ref
    site_id = record.site_id

    s3db = current.s3db

    table = s3db.inv_req_item
    itable = s3db.supply_item
    ptable = s3db.supply_item_pack
    rbtable = s3db.inv_req_item_inv

    query = (table.req_id == req_id) & \
            (table.item_id == itable.id) & \
            (table.item_pack_id == ptable.id)
    left = rbtable.on(rbtable.req_item_id == table.id)
    items = current.db(query).select(table.site_id,
                                     itable.code,
                                     itable.name,
                                     itable.volume,
                                     itable.weight,
                                     ptable.name,
                                     ptable.quantity,
                                     #rbtable.inv_item_id,
                                     rbtable.layout_id,
                                     rbtable.quantity,
                                     left = left,
                                     )

    # Bulk Represent the Bins
    # - values stored in class instance
    bin_represent = rbtable.layout_id.represent
    bins = bin_represent.bulk([row["inv_req_item_inv.layout_id"] for row in items])

    # Bulk Represent the Sites
    # - values stored in class instance
    site_represent = S3Represent(lookup = "org_site")
    sites = site_represent.bulk([row["inv_req_item.site_id"] for row in items] + [record.site_id])
    destination = site_represent(site_id)

    # Sort the data by Fulfilling Warehouse
    items_by_site = {}
    for row in items:
        site = site_represent(row["inv_req_item.site_id"])
        if site in items_by_site:
            items_by_site[site].append(row)
        else:
            items_by_site[site] = [row]

    translate = current.deployment_settings.get_L10n_translate_supply_item()

    T = current.T

    title = s3_str(T("Picking List"))

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

    # Set column Widths
    COL_WIDTH_MULTIPLIER = S3XLS.COL_WIDTH_MULTIPLIER
    col_index = 0
    label_widths = []
    for label in labels:
        width = max(len(label) * COL_WIDTH_MULTIPLIER, 2000)
        width = min(width, 65535) # USHRT_MAX
        label_widths.append(width)
        col_index += 1

    # Define styles
    style = xlwt.XFStyle()

    THIN = style.borders.THIN
    HORZ_CENTER = style.alignment.HORZ_CENTER
    HORZ_RIGHT = style.alignment.HORZ_RIGHT

    style.borders.top = THIN
    style.borders.left = THIN
    style.borders.right = THIN
    style.borders.bottom = THIN

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

    for site in items_by_site:
        # Add sheet
        sheet = book.add_sheet(site)
        sheet.set_portrait(0) # Landscape
        sheet.set_print_scaling(90)

        column_widths = list(label_widths)

        # 1st row => Report Title & Requisition Number
        current_row = sheet.row(0)
        current_row.height = 500
        #current_row.write(0, title, large_header_style)
        sheet.write_merge(0, 0, 0, 1, title, large_header_style)
        current_row.write(2, req_ref, large_header_style)

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
            # Set column Width
            sheet.col(col_index).width = column_widths[col_index]
            current_row.write(col_index, label, header_style)
            col_index += 1

        # Data rows
        items = items_by_site[site]

        # Sort each Fulfilling Warehouse by Bin
        def sort_function(row):
            return bin_represent(row["inv_req_item_inv.layout_id"])
        items.sort(key = sort_function)

        row_index = 3
        for row in items:
            current_row = sheet.row(row_index)
            item_row = row["supply_item"]
            pack_row = row["supply_item_pack"]
            bin_row = row["inv_req_item_inv"]
            layout_id = bin_row.layout_id
            if layout_id:
                bin = bin_represent(layout_id)
            else:
                bin = ""
            quantity = bin_row.quantity
            item_name = item_row.name or ""
            if translate and item_name:
                item_name = s3_str(T(item_name))
            pack_name = pack_row.name
            if translate:
                pack_name = s3_str(T(pack_name))
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
                    current_row.write(col_index, value, style)
                elif col_index == 4:
                    # Qty to Pick
                    current_row.write(col_index, value, center_style)
                else:
                    current_row.write(col_index, value, right_style)
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

        # Footer
        current_row = sheet.row(row_index)
        current_row.height = 400
        sheet.write_merge(row_index, row_index, 0, 4, "%s:" % s3_str(T("Picked By")), right_style)
        sheet.write_merge(row_index, row_index, 5, 9, "", style) # Styling
        row_index += 1
        current_row = sheet.row(row_index)
        current_row.height = 400
        sheet.write_merge(row_index, row_index, 0, 4, "%s:" % s3_str(T("Signature")), right_style)
        sheet.write_merge(row_index, row_index, 5, 9, "", style) # Styling

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
    title = s3_str(T("Picking List for %(request)s")) % {"request": req_ref}
    filename = "%s.xls" % title
    response = current.response
    from gluon.contenttype import contenttype
    response.headers["Content-Type"] = contenttype(".xls")
    disposition = "attachment; filename=\"%s\"" % filename
    response.headers["Content-disposition"] = disposition

    return output.read()

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
    for from_site in available_from_sites:
        site = from_site[0]
        if site:
            site = int(site)
            if site in requested_from_sites:
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
    for to_site in available_to_sites:
        site = int(to_site[0])
        if site in requested_to_sites:
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
        if settings.get_inv_req_multiple_items():
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
                if user_site_id and user_site_id != site_id:
                    tabs.append((T("Check"), "check"))
                if use_workflow:
                    if workflow_status == 1: # Draft
                        if auth.s3_has_permission("update", "inv_req",
                                                  record_id = req_id,
                                                  ):
                            submit_btn = A(T("Submit for Approval"),
                                           _href = URL(args = [req_id,
                                                               "submit",
                                                               ]
                                                       ),
                                           _id = "req-submit",
                                           _class = "action-btn",
                                           )
                            # Handle Confirmation
                            # Convert to POST
                            if s3.debug:
                                s3.scripts.append("/%s/static/scripts/S3/s3.inv_req_rheader.js" % r.application)
                            else:
                                s3.scripts.append("/%s/static/scripts/S3/s3.inv_req_rheader.min.js" % r.application)
                            s3.js_global.append('''i18n.req_submit_confirm="%s"''' \
                                    % T("Are you sure you want to submit this request?"))
                            s3.rfooter = TAG[""](submit_btn)

                    elif workflow_status == 2: # Submitted
                        is_approver = settings.get_inv_req_is_approver()
                        if not is_approver:
                            is_approver = inv_req_is_approver
                        if is_approver(record):
                            # Have they already approved?
                            atable = s3db.inv_req_approver_req
                            query = (atable.req_id == req_id) & \
                                    (atable.person_id == auth.s3_logged_in_person())
                            approved = db(query).select(atable.id,
                                                        limitby = (0, 1),
                                                        )
                            if not approved:
                                approve_btn = A(T("Approve"),
                                               _href = URL(args = [req_id,
                                                                   "approve_req",
                                                                   ]
                                                           ),
                                               _id = "req-approve",
                                               _class = "action-btn",
                                               )
                                # Handle Confirmation
                                # Convert to POST
                                if s3.debug:
                                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_req_rheader.js" % r.application)
                                else:
                                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_req_rheader.min.js" % r.application)
                                s3.js_global.append('''i18n.req_approve_confirm="%s"''' \
                                        % T("Are you sure you want to approve this request?"))
                                s3.rfooter = TAG[""](approve_btn)

                    elif workflow_status == 3: # Approved
                        # @ToDo: Check for permission on sites requested_from
                        if auth.s3_has_permission("create", "inv_send"):
                            if settings.get_inv_wizards():
                                method = "wizard"
                            else:
                                method = "create"
                            fulfil_btn = A(T("Prepare Shipment"),
                                           _href = URL(c = "inv",
                                                       f = "send",
                                                       args = [method],
                                                       vars = {"req_id": req_id},
                                                       ),
                                           _id = "req-fulfil",
                                           _class = "action-btn",
                                           )
                            # Not converted to POST as directs to a create form
                            s3.rfooter = TAG[""](fulfil_btn)

                        if settings.get_inv_req_reserve_items():
                            pl_btn = A(ICON("print"),
                                       " ",
                                       T("Picking List"),
                                       _href = URL(args = [req_id,
                                                           "pick_list.xls",
                                                           ],
                                                   ),
                                       _class = "action-btn",
                                       )
                            if s3.rfooter:
                                s3.rfooter.append(pl_btn)
                            else:
                                s3.rfooter = TAG[""](pl_btn)

        if not check_page:
            rheader_tabs = s3_rheader_tabs(r, tabs)
        else:
            rheader_tabs = DIV()

        if r.component and \
           r.component_name == "commit" and \
           r.component_id:
            prepare_btn = A(T("Prepare Shipment"),
                            _href = URL(f = "commit",
                                        args = [r.component_id, "send"]
                                        ),
                            _id = "commit-send",
                            _class = "action-btn",
                            )
            # Convert to POST
            if s3.debug:
                s3.scripts.append("/%s/static/scripts/S3/s3.inv_req_rheader.js" % r.application)
            else:
                s3.scripts.append("/%s/static/scripts/S3/s3.inv_req_rheader.min.js" % r.application)
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
            represent = table.req_ref.represent
            if not represent:
                represent = inv_ReqRefRepresent(show_link = True)
            headerTR = TR(TH("%s: " % table.req_ref.label),
                          TD(represent(record.req_ref,
                                       show_link = True,
                                       ))
                          )
        else:
            headerTR = TR(TD(settings.get_inv_req_form_name(),
                             _colspan = 2,
                             _class = "pdf_title",
                             ),
                          )
        if site_id:
            site = db(stable.site_id == site_id).select(stable.organisation_id,
                                                        limitby = (0, 1),
                                                        ).first()
            from .org import org_organisation_logo
            logo = org_organisation_logo(site.organisation_id)
            if logo:
                headerTR.append(TD(logo,
                                   _colspan = 2,
                                   ))

        if is_template:
            row0 = ""
            row1 = ""
            row3 = ""
        else:
            if settings.get_inv_req_project():
                ltable = s3db.inv_req_project
                f = ltable.project_id
                link = db(ltable.req_id == req_id).select(f,
                                                          limitby = (0, 1),
                                                          ).first()
                if link:
                    row0 = TR(TH("%s: " % f.label),
                              f.represent(link.project_id),
                              )
                else:
                    row0 = ""
            else:
                row0 = ""

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
                            row0,
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
                               record.purpose or NONE,
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
def inv_req_send(r, **attr):
    """
        Function to send items for a Request.
        - i.e. copy data from a req into a send
        vars: site_id <- The Site to Ship from

        Currently not exposed to UI
        - deemed better to force users through Check process

        - called via POST from inv_req_rfooter
        - called via JSON method to reduce request overheads

        @ToDo: Update for inv_inv_item_bin and inv_send_item_bin
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    req_id = r.id
    if not req_id:
        r.error(405, "Can only create a shipment for a single request")

    auth = current.auth
    s3db = current.s3db
    stable = s3db.inv_send

    has_permission = auth.s3_has_permission
    if not has_permission("create", stable):
        r.unauthorised()

    # The Site to Ship from
    site_id = r.get_vars.get("site_id")
    if not site_id:
        error = "Site not provided!"
        current.session.error = error
        r.error(405, error,
                tree = '"%s"' % URL(args = [req_id]),
                )

    db = current.db

    # User must have permissions over facility which is sending
    (prefix, resourcename, instance_id) = s3db.get_instance(db.org_site, site_id)
    if not has_permission("update",
                          "%s_%s" % (prefix,
                                     resourcename,
                                     ),
                          record_id = instance_id,
                          ):
        r.unauthorised()

    T = current.T

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
        error = T("This request has no items outstanding!")
        current.session.warning = error
        r.error(409, error,
                tree = '"%s"' % URL(args = [req_id, "req_item"]),
                )

    record = r.record

    # Create a new send record
    from .supply import supply_get_shipping_code as get_shipping_code
    code = get_shipping_code(current.deployment_settings.get_inv_send_shortname(),
                             site_id,
                             sendtable.send_ref
                             )
    send_id = sendtable.insert(send_ref = code,
                               #req_ref = record.req_ref,
                               sender_id = auth.s3_logged_in_person(),
                               site_id = site_id,
                               date = r.utcnow,
                               recipient_id = record.requester_id,
                               to_site_id = record.site_id,
                               status = SHIP_STATUS_IN_PROCESS,
                               )
    s3db.inv_send_req.insert(send_id = send_id,
                             req_id = req_id,
                             )

    # Loop through each request item and find matches in the site inventory
    # - don't match items which are expired or in bad condition
    # @ToDo: Update for inv_inv_item_bin and inv_send_item_bin
    # @ToDo: This doesn't actually remove items from Inventory?
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
                iitable.owner_org_id,
                iitable.supply_org_id,
                sip_quantity_field,
                iitable.item_source_no,
                ]
    bquery = (ii_quantity_field > 0) & \
             (iitable.site_id == site_id) & \
             (iitable.item_pack_id == sip_id_field) & \
             ((iitable.expiry_date >= r.utcnow) | ((iitable.expiry_date == None))) & \
             (iitable.status == 0)
    orderby = ii_expiry_field | ii_purchase_field

    no_match = True

    for ritem in req_items:
        rim = ritem.inv_req_item
        rim_id = rim.id
        query = bquery & \
                (ii_item_id_field == rim.item_id)
        inv_items = db(query).select(orderby = orderby,
                                     *iifields)

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
                # @ToDo: inv_remove doesn't handle Bins
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
                   status = TRACK_STATUS_PREPARING,
                   pack_value = iitem.pack_value,
                   currency = iitem.currency,
                   #layout_id = iitem.layout_id,
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
                   status = TRACK_STATUS_PREPARING,
                   pack_value = iitem.pack_value,
                   currency = iitem.currency,
                   #layout_id = iitem.layout_id,
                   expiry_date = iitem.expiry_date,
                   owner_org_id = iitem.owner_org_id,
                   supply_org_id = iitem.supply_org_id,
                   item_source_no = iitem.item_source_no,
                   #comments = comment,
                   )

    if no_match:
        # Can't use %(site_name)s as gluon/languages.py def translate has a str() which can give a Unicode error
        #site_name = s3db.org_site_represent(site_id, show_link=False)
        current.session.warning = \
            T("This site has no items exactly matching this request. There may still be other items in stock which can fulfill this request!")

    # Redirect to view the list of items in the Send
    message = T("Shipment created")
    current.session.confirmation = message

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": URL(args = [send_id, "track_item"]),
                       }, separators=SEPARATORS)

# =============================================================================
def inv_req_send_sites(r, **attr):
    """
        Lookup to limit
            - from sites to those requested_from the selected Requests' remaining Items
            - to sites to those from the selected Requests
        Accessed from inv_send.js
        Access via the .json representation to avoid work rendering menus, etc
    """

    req_id = r.get_vars.get("req_id") # Not using r.id as can be multiple
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
    for from_site in available_from_sites:
        site = int(from_site[0])
        if site in requested_from_sites:
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
    for to_site in available_to_sites:
        site = to_site[0]
        if site:
            site = int(site)
            if site in requested_to_sites:
                to_sites.append(site)

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps((from_sites, to_sites), separators=SEPARATORS)

# =============================================================================
def inv_req_tabs(r, match=True):
    """
        Add a set of rheader tabs for a site's Inventory Requisition management

        Args:
            r: the S3Request (for permission checking)
            match: request matching is applicable for this type of site

        Returns:
            list of rheader tab definitions
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
        from .org import org_organisation_logo
        logo = org_organisation_logo(record.organisation_id)
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
                     (T("Track Shipment"), "track_item/"),
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
        rheader = DIV(TABLE(#TR(TH("%s: " % table.req_ref.label),
                            #   TD(table.req_ref.represent(record.req_ref),
                            #      _colspan = 3,
                            #      ),
                            #   ),
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
        #        (T("Log"), "log"),
        #        ]
        #rheader_tabs = DIV(s3_rheader_tabs(r, tabs))

        db = current.db
        item_id = record.item_id
        site_id = record.site_id

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
                            TR(TH("%s: " % table.supply_org_id.label),
                               table.supply_org_id.represent(record.supply_org_id),
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
                                   f = "track_item",
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
def inv_send_add_items_of_shipment_type(send_id, site_id, shipment_type):
    """
        Add all inv_items with status matching the send shipment type
        eg. Items for Dump, Sale, Reject, Surplus
    """

    table = db.inv_track_item
    sbtable = db.inv_send_item_bin
    iitable = db.inv_inv_item
    ibtable = db.inv_inv_item_bin
    query = (iitable.site_id == site_id) & \
            (iitable.status == shipment_type) & \
            (iitable.quantity > 0)
    left = ibtable.on(ubtable.inv_item_id == iitable.id)
    rows = db(query).select(iitable.id,
                            iitable.item_id,
                            iitable.item_pack_id,
                            iitable.quantity,
                            iitable.pack_value,
                            iitable.currency,
                            iitable.expiry_date,
                            iitable.item_source_no,
                            iitable.owner_org_id,
                            iitable.supply_org_id,
                            ibtable.id,
                            ibtable.layout_id,
                            ibtable.quantity,
                            left = left,
                            )

    inv_items = {}
    inv_bin_ids = []
    iappend = inv_bin_ids.append
    for row in rows:
        bin_row = row["inv_inv_item_bin"]
        bin_quantity = bin_row.quantity
        if bin_quantity:
            iappend(bin_row.id)
            inv_bin = {"layout_id": bin_row.layout_id,
                       "quantity": bin_quantity,
                       }
        inv_row = row["inv_inv_item"]
        inv_item_id = inv_row.id
        if inv_item_id not in inv_items:
            if bin_quantity:
                inv_bins = [inv_bin]
            else:
                inv_bins = []
            inv_items[inv_item_id] = {"track_record": {"send_inv_item_id": inv_item_id,
                                                       "inv_item_status": shipment_type,
                                                       "item_id": inv_row.item_id,
                                                       "item_pack_id": inv_row.item_pack_id,
                                                       "quantity": inv_row.quantity,
                                                       "pack_value": inv_row.pack_value,
                                                       "currency": inv_row.currency,
                                                       "expiry_date": inv_row.expiry_date,
                                                       "item_source_no": inv_row.item_source_no,
                                                       "owner_org_id": inv_row.owner_org_id,
                                                       "supply_org_id": inv_row.supply_org_id,
                                                       },
                                      "inv_bins": inv_bins,
                                      }
        elif bin_quantity:
            inv_items["inv_bins"].append(inv_bin)

    for inv_item_id in inv_items:
        inv_item = inv_items[inv_item_id]

        # Create the Track Item record
        track_record = inv_item["track_record"]
        track_item_id = table.insert(**track_record)

        # Create the Send Bins
        inv_bins = inv_item["inv_bins"]
        for inv_bin in inv_bins:
            sbtable.insert(track_item_id = track_item_id,
                           layout_id = inv_bin["layout_id"],
                           quantity = inv_bin["quantity"],
                           )

    # Remove the Stock from Inventory
    db(iitable.id.belongs(inv_items.keys())).update(quantity = 0)
    db(ibtable.id.belongs(inv_bin_ids)).update(quantity = 0)

# =============================================================================
def inv_send_controller():
    """
       RESTful CRUD controller for inv_send
    """

    T = current.T
    db = current.db
    s3db = current.s3db
    settings = current.deployment_settings

    sendtable = s3db.inv_send

    response = current.response
    s3 = response.s3

    # Custom methods
    set_method = s3db.set_method
    # Cancel Shipment
    set_method("inv", "send",
               method = "cancel",
               action = inv_send_cancel,
               )

    # Generate PDF of Waybill
    set_method("inv", "send",
               method = "form",
               action = inv_send_form,
               )

    # Generate Gift Certificate
    set_method("inv", "send",
               method = "gift_certificate",
               action = inv_gift_certificate,
               )

    # Generate Item Labels
    set_method("inv", "send",
               component_name = "track_item",
               method = "label",
               action = inv_item_label,
               )

    # Generate Package Labels
    set_method("inv", "send",
               method = "labels",
               action = inv_package_labels,
               )

    # Generate Picking List
    set_method("inv", "send",
               method = "pick_list",
               action = inv_pick_list,
               )

    # Generate Packing List
    set_method("inv", "send",
               method = "packing_list",
               action = inv_packing_list,
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

    # Manage Returns
    set_method("inv", "send",
               method = "return",
               action = inv_send_return,
               )

    # Complete Returns
    set_method("inv", "send",
               method = "return_complete",
               action = inv_send_return_complete,
               )

    # Display Timeline
    set_method("inv", "send",
               method = "timeline",
               action = inv_timeline,
               )

    def prep(r):
        send_req = settings.get_inv_send_req()

        export_formats = settings.ui.export_formats
        if "pdf" in export_formats:
            # Use 'form' instead of standard PDF exporter
            export_formats = list(export_formats)
            export_formats.remove("pdf")
            settings.ui.export_formats = export_formats

        method = r.method
        record = r.record
        if record:
            status = record.status
        elif method in ("create", "wizard"):
            req_id = r.get_vars.get("req_id")
            if req_id:
                rtable = s3db.inv_req
                fields = [rtable.site_id]
                if send_req:
                    s3db.inv_send_req.req_id.default = req_id
                else:
                    fields.append(rtable.req_ref)

                req = db(rtable.id == req_id).select(limitby = (0, 1),
                                                     *fields).first()
                sendtable.to_site_id.default = req.site_id
                if not send_req:
                    sendtable.req_ref.default = req.req_ref

        if r.component:
            cname = r.component_name
            if cname == "document":
                s3.crud_strings["doc_document"].label_create = T("File Signed Document")

                # Simplify a little
                table = s3db.doc_document
                table.file.required = True
                #table.url.readable = table.url.writable = False
                #table.date.readable = table.date.writable = False

                WAYBILL = settings.get_inv_send_form_name()
                field = table.name
                field.label = T("Type")
                document_type_opts = {"PL": T("Picking List"),
                                      "REQ": settings.get_inv_req_form_name(),
                                      "WB": WAYBILL,
                                      }
                field.default = "WB"
                field.requires = IS_IN_SET(document_type_opts)
                field.represent = s3_options_represent(document_type_opts)

                # Add button to print the WB
                # - needed for Wizard, but generalised for consistency
                button = DIV(P(T("Print and Upload the signed %(waybill)s:") % {"waybill": WAYBILL}),
                             A(ICON("print"),
                               " ",
                               settings.get_inv_send_shortname(),
                               _href = URL(args = [record.id,
                                                   "form",
                                                   ]
                                         ),
                               _class = "action-btn",
                               ),
                            )

                crud_form = S3SQLCustomForm(S3SQLInlineWidget(button),
                                            "name",
                                            "file",
                                            "comments",
                                            )

                s3db.configure("doc_document",
                               crud_form = crud_form,
                               )

            elif cname == "send_package":

                # Uncommon workflow, so no need to optimise for this:
                #if method == "read":
                #    return True

                if status != SHIP_STATUS_IN_PROCESS:
                    # Locked
                    s3db.configure("inv_send_package",
                                   deletable = False,
                                   insertable = False,
                                   updateable = False,
                                   )
                    return True

                send_id = r.id

                # Number the Package automatically
                sptable = s3db.inv_send_package
                query = (sptable.send_id == send_id)
                field = sptable.number
                max_field = field.max()
                current_number = db(query).select(max_field,
                                                  limitby = (0, 1),
                                                  orderby = max_field,
                                                  ).first()[max_field]
                if current_number:
                    next_number = current_number + 1
                else:
                    next_number = 1
                field.default = next_number

                send_package_id = r.component_id
                if send_package_id:
                    send_package_id = int(send_package_id)

                # Read all Items in the Shipment
                ttable = s3db.inv_track_item
                rows = db(ttable.send_id == send_id).select(ttable.id,
                                                            ttable.quantity,
                                                            )
                track_items = {row.id: row.quantity for row in rows}

                # Filter out Items which are already fully packaged
                # - other than those in this Package (update forms)
                send_package = []
                spitable = s3db.inv_send_package_item
                query &= (sptable.id == spitable.send_package_id)
                rows = db(query).select(spitable.send_package_id,
                                        spitable.track_item_id,
                                        spitable.quantity,
                                        )
                for row in rows:
                    track_item_id = row.track_item_id
                    if row.send_package_id == send_package_id:
                        send_package.append(track_item_id)
                    track_items[track_item_id] -= row.quantity
                track_item_ids = [track_item_id for track_item_id in track_items if ((track_item_id in send_package) or (track_items[track_item_id] > 0))]
                spitable.track_item_id.requires.set_filter(filterby = "id",
                                                           filter_opts = track_item_ids,
                                                           )
                # Default Quantity
                if send_package_id:
                    # Update form
                    track_items = {k: v for k, v in track_items.items() if (k in send_package) or (v > 0)}
                else:
                    # Create form
                    track_items = {k: v for k, v in track_items.items() if v > 0}
                if track_items:
                    s3.js_global.append('''S3.supply.track_items=%s''' % json.dumps(track_items, separators=SEPARATORS))
                    if s3.debug:
                        s3.scripts.append("/%s/static/scripts/S3/s3.inv_send_package_item.js" % r.application)
                    else:
                        s3.scripts.append("/%s/static/scripts/S3/s3.inv_send_package_item.min.js" % r.application)
                    
            elif cname == "track_item":

                # Security-wise, we are already covered by configure()
                # Performance-wise, we should optimise for UI-acessible flows
                #if method in ("create", "delete"):
                #    # Can only create or delete track items for a send record
                #    # if the status is preparing
                #    if status != SHIP_STATUS_IN_PROCESS:
                #        return False
                if method == "delete":
                    return inv_track_item_deleting(r.component_id)

                tracktable = s3db.inv_track_item
                iitable = s3db.inv_inv_item

                track_pack_values = settings.get_inv_track_pack_values()

                def set_track_attr(status):
                    # By default Make all fields writable False
                    for field in tracktable.fields:
                        tracktable[field].writable = False
                    # Hide some fields
                    tracktable.send_id.readable = False
                    tracktable.recv_id.readable = False
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
                        crud_form = S3SQLCustomForm("send_inv_item_id",
                                                    "item_pack_id",
                                                    "quantity",
                                                    S3SQLInlineComponent("send_bin",
                                                                         label = T("Bins"),
                                                                         fields = ["layout_id",
                                                                                   "quantity",
                                                                                   ],
                                                                         ),
                                                    "expiry_date",
                                                    "item_source_no",
                                                    "supply_org_id",
                                                    "owner_org_id",
                                                    "inv_item_status",
                                                    "status",
                                                    "adj_item_id",
                                                    # readable/writable = False by default
                                                    # writable set to True later if linked to requests
                                                    "req_item_id",
                                                    "comments",
                                                    # Remove Items from stock when allocated to a Shipment
                                                    postprocess = inv_send_item_postprocess,
                                                    )
                    elif status == TRACK_STATUS_ARRIVED:
                        # Shipment arrived display some extra fields at the destination
                        tracktable.item_source_no.readable = True
                        tracktable.recv_quantity.readable = True
                        tracktable.return_quantity.readable = True
                        crud_form = S3SQLCustomForm("send_inv_item_id",
                                                    "item_pack_id",
                                                    "quantity",
                                                    "recv_quantity",
                                                    "return_quantity",
                                                    "pack_value",
                                                    "currency",
                                                    "expiry_date",
                                                    S3SQLInlineComponent("recv_bin",
                                                                         label = T("Bins"),
                                                                         fields = ["layout_id",
                                                                                   "quantity",
                                                                                   ],
                                                                         readonly = True,
                                                                         ),
                                                    "item_source_no",
                                                    "supply_org_id",
                                                    "owner_org_id",
                                                    "inv_item_status",
                                                    "status",
                                                    "adj_item_id",
                                                    "comments",
                                                    )
                    elif status == TRACK_STATUS_RETURNING:
                        tracktable.return_quantity.readable = True
                        tracktable.return_quantity.writable = True
                        tracktable.currency.readable = False
                        tracktable.pack_value.readable = False
                        crud_form = S3SQLCustomForm("send_inv_item_id",
                                                    "item_pack_id",
                                                    "quantity",
                                                    "return_quantity",
                                                    "expiry_date",
                                                    # @ToDo: Bin?
                                                    "item_source_no",
                                                    "supply_org_id",
                                                    "owner_org_id",
                                                    "inv_item_status",
                                                    "status",
                                                    "adj_item_id",
                                                    "comments",
                                                    )
                    else:
                        # Read-only form
                        crud_form = S3SQLCustomForm("send_inv_item_id",
                                                    "item_pack_id",
                                                    "quantity",
                                                    "pack_value",
                                                    "currency",
                                                    "expiry_date",
                                                    "item_source_no",
                                                    "inv_item_status",
                                                    "status",
                                                    "comments",
                                                    )

                    return crud_form

                if status in (SHIP_STATUS_RECEIVED, SHIP_STATUS_CANCEL):
                    deletable = editable = insertable = False
                    list_fields = [#"status",
                                   "item_id",
                                   "item_pack_id",
                                   "send_bin.layout_id",
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
                                   "send_bin.layout_id",
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
                                   "send_bin.layout_id",
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
                            list_fields.insert(2, (T("Quantity Needed"), "quantity_needed"))

                track_item_id = r.component_id
                if track_item_id:
                    track_record = db(tracktable.id == track_item_id).select(tracktable.item_id,
                                                                             tracktable.item_pack_id,
                                                                             tracktable.send_inv_item_id, # Ensure we include the current inv_item
                                                                             tracktable.status,
                                                                             limitby = (0, 1),
                                                                             ).first()
                    crud_form = set_track_attr(track_record.status)
                    if r.http == "GET" and \
                       track_record.status == TRACK_STATUS_PREPARING:
                        # Provide initial options for Pack in Update forms
                        # Don't include in the POSTs as we want to be able to select alternate Items, and hence Packs
                        f = tracktable.item_pack_id
                        f.requires = IS_ONE_OF(db, "supply_item_pack.id",
                                               f.represent,
                                               sort = True,
                                               filterby = "item_id",
                                               filter_opts = (track_record.item_id,),
                                               )
                else:
                    crud_form = set_track_attr(TRACK_STATUS_PREPARING)

                s3db.configure("inv_track_item",
                               crud_form = crud_form,
                               # Lock the record so it can't be fiddled with
                               deletable = deletable,
                               editable = editable,
                               insertable = insertable,
                               list_fields = list_fields,
                               )

                if status == SHIP_STATUS_IN_PROCESS and \
                   r.interactive:
                    crud_strings = s3.crud_strings.inv_send
                    crud_strings.title_update = \
                    crud_strings.title_display = T("Process Shipment to Send")

                    if method in (None, "update", "wizard"):
                        # Limit to Bins from this site
                        from .org import org_site_layout_config
                        isbtable = s3db.inv_send_item_bin
                        org_site_layout_config(r.record.site_id, isbtable.layout_id)

                        # We replace filterOptionsS3
                        if s3.debug:
                            s3.scripts.append("/%s/static/scripts/S3/s3.inv_send_item.js" % r.application)
                        else:
                            s3.scripts.append("/%s/static/scripts/S3/s3.inv_send_item.min.js" % r.application)
                        # Filter out Items which have Quantity 0, are Expired or in Bad condition
                        site_id = record.site_id
                        ii_query = (iitable.quantity > 0) & \
                                   ((iitable.expiry_date >= r.now) | ((iitable.expiry_date == None))) & \
                                   (iitable.status == 0)
                        # Filter out Items which are already in this shipment
                        send_id = r.id
                        track_items = db(tracktable.send_id == send_id).select(tracktable.send_inv_item_id)
                        inv_item_ids = [row.send_inv_item_id for row in track_items]
                        ii_query &= ~(iitable.id.belongs(inv_item_ids))
                        if track_item_id:
                            # Ensure we include the current inv_item
                            ii_query |= (iitable.id == track_record.send_inv_item_id)

                        ibtable = s3db.inv_inv_item_bin
                        iptable = s3db.supply_item_pack
                        inv_data = {}
                        inv_item_ids = []
                        iiappend = inv_item_ids.append

                        reqs = None
                        if settings.get_inv_send_req():
                            srtable = s3db.inv_send_req
                            reqs = db(srtable.send_id == send_id).select(srtable.req_id)
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
                                rtable = s3db.inv_req
                                ritable = s3db.inv_req_item
                                #riptable = s3db.get_aliased(iptable, "req_item_pack")
                                if len(req_ids) == 1:
                                    query = (rtable.id == req_ids[0])
                                else:
                                    query = (rtable.id.belongs(req_ids))
                                # Note: In order to allow request items to go via transit hops, we only check quantity_fulfil
                                # ToDo: Add req_item_site table to track each hop
                                query &= (ritable.req_id == rtable.id) & \
                                         (ritable.site_id == site_id) & \
                                         (ritable.quantity_fulfil < ritable.quantity) & \
                                         (ritable.item_pack_id == iptable.id) & \
                                         (ritable.item_id == iitable.item_id) & \
                                         (iitable.site_id == site_id)
                                items = db(query).select(iitable.id,
                                                         iitable.quantity, # inv_pack_quantity done later, when adding packs
                                                         rtable.req_ref,
                                                         ritable.id,
                                                         ritable.quantity,
                                                         iptable.quantity,
                                                         )
                                for row in items:
                                    req_pack_quantity = row["supply_item_pack.quantity"]
                                    req_ref = row["inv_req.req_ref"]
                                    inv_row = row["inv_inv_item"]
                                    req_row = row["inv_req_item"]
                                    inv_item_id = inv_row.id
                                    iiappend(inv_item_id)
                                    if inv_item_id in inv_data:
                                        inv_data[inv_item_id]["r"].append({"i": req_row.id,
                                                                           "q": req_row.quantity * req_pack_quantity,
                                                                           "r": req_ref,
                                                                           })
                                    else:
                                        inv_data[inv_item_id] = {"q": inv_row.quantity,
                                                                 "r": [{"i": req_row.id,
                                                                        "q": req_row.quantity * req_pack_quantity,
                                                                        "r": req_ref,
                                                                        },
                                                                       ],
                                                                 }
                                # Remove req_ref when there are no duplicates to distinguish
                                for inv_item_id in inv_data:
                                    req_items = inv_data[inv_item_id]["r"]
                                    if len(req_items) == 1:
                                        req_items[0].pop("r")

                                inv_item_ids = set(inv_item_ids)
                                query = (iitable.id.belongs(inv_item_ids))

                                # Add Bins
                                bin_query = query & (ibtable.inv_item_id == iitable.id)
                                rows = db(bin_query).select(iitable.id,
                                                            ibtable.layout_id,
                                                            ibtable.quantity,
                                                            )
                                for row in rows:
                                    bin_row = row.inv_inv_item_bin
                                    layout_id = bin_row.layout_id
                                    if not layout_id:
                                        continue
                                    inv_item_id = row["inv_inv_item.id"]
                                    this_data = inv_data[inv_item_id]
                                    bins = this_data.get("b")
                                    if not bins:
                                        this_data["b"] = {layout_id: bin_row.quantity,
                                                          }
                                    else:
                                        this_data["b"][layout_id] = bin_row.quantity

                                dbset = db(query & ii_query)
                                if dbset.select(iitable.id,
                                                limitby = (0, 1),
                                                ):
                                    # Set the dropdown options
                                    f = tracktable.send_inv_item_id
                                    f.requires = f.requires.other
                                    f.requires.dbset = dbset
                                else:
                                    # No more items can be added
                                    s3db.configure("inv_track_item",
                                                   insertable = False,
                                                   )

                        if not reqs:
                            # Restrict to valid items from this site only
                            f = tracktable.send_inv_item_id
                            f.requires = f.requires.other
                            query = ii_query & (iitable.site_id == site_id)
                            f.requires.dbset = db(query)

                            # Read Item Details
                            # @ToDo: This may have scalability issues if a site has a very large number of items
                            #        => Switch back to reading data per item via AJAX in this case
                            left = ibtable.on(ibtable.inv_item_id == iitable.id)
                            items = db(query).select(iitable.id,
                                                     iitable.quantity,
                                                     ibtable.layout_id,
                                                     ibtable.quantity,
                                                     left = left,
                                                     )
                            for row in items:
                                inv_row = row["inv_inv_item"]
                                bin_row = row["inv_inv_item_bin"]
                                inv_item_id = inv_row.id
                                iiappend(inv_item_id)
                                if inv_item_id in inv_data:
                                    layout_id = bin_row.layout_id
                                    if layout_id:
                                        inv_data[inv_item_id]["b"][layout_id] = bin_row.quantity
                                else:
                                    layout_id = bin_row.layout_id
                                    if layout_id:
                                        b = {layout_id: bin_row.quantity,
                                             }
                                    else:
                                        b = {}
                                    inv_data[inv_item_id] = {"q": inv_row.quantity,
                                                             "b": b,
                                                             }

                            inv_item_ids = set(inv_item_ids)
                            query = (iitable.id.belongs(inv_item_ids))

                        # Add Packs to replace the filterOptionsS3 lookup
                        pack_query = query & (iitable.item_id == iptable.item_id)
                        rows = db(pack_query).select(iitable.id,
                                                     iitable.item_pack_id,
                                                     iptable.id,
                                                     iptable.name,
                                                     iptable.quantity,
                                                     )
                        for row in rows:
                            inv_row = row["inv_inv_item"]
                            inv_item_id = inv_row.id
                            inv_pack_id = inv_row.item_pack_id
                            this_data = inv_data[inv_item_id]
                            packs = this_data.get("p")
                            pack_row = row.supply_item_pack
                            pack_id = pack_row.id
                            pack = {"i": pack_id,
                                    "n": pack_row.name,
                                    "q": pack_row.quantity,
                                    }
                            if pack_id == inv_pack_id:
                                # Default for inv_item & hence it's Bins
                                pack["d"] = 1
                            if not packs:
                                this_data["p"] = [pack]
                            else:
                                this_data["p"].append(pack)

                        binned_quantity = ""
                        if track_item_id:
                            # Update form
                            # add binnedQuantity if there are multiple Bins to manage
                            # @ToDo: Do we also need to do this if 1 Bin + unbinned?
                            bins = db(isbtable.track_item_id == track_item_id).select(isbtable.quantity)
                            if len(bins) > 1:
                                binned_quantity = '''
S3.supply.binnedQuantity=%s
S3.supply.itemPackID=%s''' % (sum([row.quantity for row in bins]),
                              track_record.item_pack_id,
                              )

                        # Pass data to s3.inv_send_item.js
                        # When send_inv_item_id is selected
                        # - populate item_pack_id
                        # - show stock quantity
                        # - set/filter Bins
                        # - set req_item_id (if coming from a Request)
                        s3.js_global.append('''S3.supply.inv_items=%s
S3.supply.site_id=%s%s''' % (json.dumps(inv_data, separators=SEPARATORS),
                             site_id,
                             binned_quantity,
                             ))

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

            if (method in ("create", "wizard") or \
               (method == "update" and record.status == SHIP_STATUS_IN_PROCESS)):
                if s3.debug:
                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_send.js" % r.application)
                else:
                    s3.scripts.append("/%s/static/scripts/S3/s3.inv_send.min.js" % r.application)
                if sendtable.transport_type.writable:
                    s3.js_global.append(
'''i18n.AWB='%s'
i18n.BL='%s'
i18n.CMR='%s'
i18n.ref='%s'
i18n.flight='%s'
i18n.vessel='%s'
i18n.vehicle='%s'
i18n.reg='%s'
''' % (T("AWB No"),
       T("B/L No"),
       T("Waybill/CMR No"),
       T("Transport Reference"),
       T("Flight"),
       T("Vessel"),
       T("Vehicle Plate Number"),
       T("Registration Number"),
       ))
                if settings.get_inv_send_req():
                    # Filter Requests to those which are:
                    # - Approved (or Open)
                    # - Have Items Requested From our sites which are not yet in-Transit/Fulfilled
                    sites = sendtable.site_id.requires.options(zero = False)
                    site_ids = [site[0] for site in sites]
                    rtable = s3db.inv_req
                    ritable = s3db.inv_req_item
                    if len(site_ids) > 1:
                        site_query = (ritable.site_id.belongs(site_ids))
                    else:
                        site_query = (ritable.site_id == site_ids[0])
                    # Note: In order to allow request items to go via transit hops, we only check quantity_fulfil
                    # ToDo: Add req_item_site table to track each hop
                    query = (rtable.id == ritable.req_id) & \
                            site_query & \
                            (ritable.quantity_fulfil < ritable.quantity)
                    if settings.get_inv_req_workflow():
                        query = (rtable.workflow_status == 3) & query
                    else:
                        query = (rtable.fulfil_status.belongs((REQ_STATUS_NONE, REQ_STATUS_PARTIAL))) & query
                    f = s3db.inv_send_req.req_id
                    f.requires = IS_ONE_OF(db(query), "inv_req.id",
                                           f.represent,
                                           sort = True,
                                           )
                    if settings.get_inv_req_reserve_items():
                        crud_fields = [f for f in sendtable.fields if sendtable[f].readable]
                        crud_form = S3SQLCustomForm(*crud_fields,
                                                    postprocess = inv_send_postprocess,
                                                    )
            elif record:
                transport_type = record.transport_type
                if transport_type == "Air":
                    sendtable.transport_ref.label = T("AWB No")
                    sendtable.registration_no.label = T("Flight")
                elif transport_type == "Sea":
                    sendtable.transport_ref.label = T("B/L No")
                    sendtable.registration_no.label = T("Vessel")
                elif transport_type == "Road":
                    sendtable.transport_ref.label = T("Waybill/CMR No")
                    sendtable.registration_no.label = T("Vehicle Plate Number")
                elif transport_type == "Hand":
                    sendtable.transport_ref.readable = False
                    sendtable.vehicle.readable = False
                    sendtable.registration_no.readable = False

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if r.component_name == "track_item" and \
               not r.component_id:
                # Add Action Button to Print Item Label
                if s3.actions == None:
                    # Normal Action Buttons
                    s3_action_buttons(r)
                # Custom Action Buttons
                s3.actions += [{"icon": ICON.css_class("print"),
                                "label": s3_str(T("Label")),
                                "url": URL(args = [r.id,
                                                   "track_item",
                                                   "[id]",
                                                   "label",
                                                   ],
                                           ),
                                "_class": "action-btn",
                                },
                               ]

            elif r.method == None and \
                 settings.get_inv_wizards() and \
                isinstance(output, dict):
                try:
                    # Launch Wizard, not Create form
                    output["buttons"]["add_btn"]["_href"] = URL(args = "wizard")
                except KeyError:
                    pass

        return output
    s3.postp = postp

    return current.rest_controller("inv", "send",
                                   rheader = inv_send_rheader,
                                   )

# =============================================================================
def inv_send_cancel(r, **attr):
    """
        This will cancel a shipment that has been sent

        @ToDo: Redirect to a screen to do Bin allocations?

        @todo need to roll back commitments
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    T = current.T

    send_id = r.id
    if not send_id:
        r.error(405, "Can only cancel a single shipment")

    s3db = current.s3db

    stable = s3db.inv_send

    if not current.auth.s3_has_permission("delete", stable,
                                          record_id = send_id,
                                          ):
        r.unauthorised()

    record = r.record

    if record.status != SHIP_STATUS_SENT:
        r.error(409, T("This shipment has not been sent - it has NOT been canceled because it can still be edited."),
                tree = '"%s"' % URL(args = [send_id]),
                )

    db = current.db

    rtable = s3db.inv_recv
    tracktable = s3db.inv_track_item

    # Change the send and recv status to cancelled
    db(stable.id == send_id).update(status = SHIP_STATUS_CANCEL)
    recv_row = db(tracktable.send_id == send_id).select(tracktable.recv_id,
                                                        limitby = (0, 1),
                                                        ).first()
    if recv_row:
        db(rtable.id == recv_row.recv_id).update(date = r.utcnow,
                                                 status = SHIP_STATUS_CANCEL,
                                                 )

    # Change the track items status to canceled and then delete them
    # If they are linked to a request then the in transit total will also be reduced
    # Records can only be deleted if the status is In Process (or preparing)
    # so change the status before we delete
    # @ToDo: Rewrite to do this in Bulk
    db(tracktable.send_id == send_id).update(status = TRACK_STATUS_PREPARING)
    track_rows = db(tracktable.send_id == send_id).select(tracktable.id)
    for track_item in track_rows:
        inv_track_item_deleting(track_item.id)

    # Now change the status to cancelled
    db(tracktable.send_id == send_id).update(status = TRACK_STATUS_CANCELED)

    if current.deployment_settings.get_inv_warehouse_free_capacity_calculated():
        # Update the Warehouse Free capacity
        inv_warehouse_free_capacity(record.site_id)

    message = T("Sent Shipment canceled and items returned to Warehouse")
    current.session.confirmation = message

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": URL(args = [send_id]),
                       }, separators=SEPARATORS)

# =============================================================================
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

    list_fields = [(T("Item Code"), "item_id$code"),
                   "item_id",
                   (T("Weight (kg)"), "item_id$weight"),
                   (T("Volume (m3)"), "item_id$volume"),
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
                    pdf_filename = r.record.send_ref,
                    list_fields = list_fields,
                    pdf_hide_comments = True,
                    pdf_header_padding = 12,
                    pdf_footer = inv_send_pdf_footer,
                    pdf_orientation = "Landscape",
                    pdf_table_autogrow = "B",
                    **attr
                    )

# =============================================================================
def inv_send_item_postprocess(form):
    """
        When a Stock Item is added to a Shipment then we need to remove it from
        the Inventory.
        We do this whilst preparing the Shipment to prevent them being allocated
        multiple times.

        If the bin to take from hasn't been selected then we auto-allocate.
        We optimise to minimise the number of Bins remaining for an Item
        (An alternative would be to optimise this Pick)

        Stock cards, Request Status and Warehouse Free Capacity not updated until
        Shipment actually Sent (inv_send_process)
    """

    record = form.record
    track_item_id = form.vars.id

    db = current.db
    s3db = current.s3db

    table = s3db.inv_track_item
    sbtable = s3db.inv_send_item_bin
    iitable = s3db.inv_inv_item
    ibtable = s3db.inv_inv_item_bin
    iptable = s3db.supply_item_pack

    # Read the Send Item, including Bins
    query = (table.id == track_item_id) & \
            (table.item_pack_id == iptable.id)
    left = sbtable.on(sbtable.track_item_id == table.id)
    rows = db(query).select(table.quantity,
                            table.send_inv_item_id,
                            iptable.id,
                            iptable.quantity,
                            sbtable.id,
                            sbtable.layout_id,
                            sbtable.quantity,
                            left = left,
                            )

    row = rows.first()
    track_row = row["inv_track_item"]
    inv_item_id = track_row.send_inv_item_id
    send_quantity = track_row.quantity
    pack_row = row["supply_item_pack"]
    send_item_pack_id = pack_row.id
    send_pack_quantity = pack_row.quantity
    send_bins = {}
    binned_quantity = 0
    for row in rows:
        bin_row = row["inv_send_item_bin"]
        bin_quantity = bin_row.quantity
        if bin_quantity:
            binned_quantity += bin_quantity
            send_bins[bin_row.layout_id] = {"id": bin_row.id,
                                            "quantity": bin_quantity,
                                            }

    # Read the Inv Item, including Bins
    query = (iitable.id == inv_item_id) & \
            (iitable.item_pack_id == iptable.id)
    left = ibtable.on(ibtable.inv_item_id == iitable.id)
    rows = db(query).select(iitable.quantity,
                            iptable.quantity,
                            ibtable.id,
                            ibtable.layout_id,
                            ibtable.quantity,
                            left = left,
                            )

    row = rows.first()
    inv_total_quantity = row["inv_inv_item.quantity"]
    inv_pack_quantity = row["supply_item_pack.quantity"]
    inv_bins = []
    for row in rows:
        bin_row = row["inv_inv_item_bin"]
        bin_quantity = bin_row.quantity
        if bin_quantity:
            inv_bins.append({"id": bin_row.id,
                             "layout_id": bin_row.layout_id,
                             "quantity": bin_quantity,
                             })

    if record:
        # Update form: Read the old Bin Data
        old_bin_data = record.sub_defaultsend_bin
        old_bin_data = json.loads(old_bin_data) or {}
        old_bin_data = old_bin_data.get("data", [])
        old_bins = {}
        for row in old_bin_data:
            bin_quantity = row["quantity"]["value"]
            if bin_quantity:
                old_bins[row["layout_id"]["value"]] = float(bin_quantity)

    if send_quantity > binned_quantity:
        # Auto-allocate
        from operator import itemgetter
        inv_bins.sort(key = itemgetter("quantity"))
        to_allocate = (send_quantity - binned_quantity) * send_pack_quantity
        while (to_allocate > 0):
            for inv_bin in inv_bins:
                layout_id = inv_bin["layout_id"]
                inv_quantity = inv_bin["quantity"] * inv_pack_quantity
                if record:
                    # Update form
                    # - add previously allocated inventory
                    old_quantity = old_bins.get(layout_id)
                    if old_quantity:
                        inv_quantity += (old_quantity * inv_pack_quantity)
                if layout_id in send_bins:
                    send_bin = send_bins[layout_id]
                    send_bin_quantity = send_bin["quantity"] * send_pack_quantity
                    if inv_quantity > send_bin_quantity:
                        # Allocate more from this bin
                        if inv_quantity >= (to_allocate + send_bin_quantity):
                            # Allocate all from this bin
                            new_quantity = (to_allocate + send_bin_quantity) / send_pack_quantity
                            send_bin["quantity"] = new_quantity
                            db(sbtable.id == send_bin["id"]).update(quantity = new_quantity)
                            to_allocate = 0
                            break
                        else:
                            # Allocate what we can from this bin
                            new_quantity = inv_quantity / send_pack_quantity
                            send_bin["quantity"] = new_quantity
                            db(sbtable.id == send_bin["id"]).update(quantity = new_quantity)
                            to_allocate -= (inv_quantity - send_bin_quantity)
                else:
                    if inv_quantity >= to_allocate:
                        # Allocate all from this bin
                        new_quantity = to_allocate / send_pack_quantity
                        bin_id = sbtable.insert(track_item_id = track_item_id,
                                                layout_id = layout_id,
                                                quantity = new_quantity,
                                                )
                        send_bins[layout_id] = {"id": bin_id,
                                                "quantity": new_quantity,
                                                }
                        to_allocate = 0
                        break
                    else:
                        # Allocate what we can from this bin
                        new_quantity = inv_quantity / send_pack_quantity
                        bin_id = sbtable.insert(track_item_id = track_item_id,
                                                layout_id = layout_id,
                                                quantity = new_quantity,
                                                )
                        send_bins[layout_id] = {"id": bin_id,
                                                "quantity": new_quantity,
                                                }
                        to_allocate -= inv_quantity
            # Allocate from unbinned Stock
            break

    # Update Stock levels
    if record:
        # Update form
        item_pack_id = record.item_pack_id
        if item_pack_id == send_item_pack_id:
            old_pack_quantity = send_pack_quantity
        else:
            old_pack = db(iptable.id == item_pack_id).select(iptable.quantity,
                                                             limitby = (0, 1),
                                                             ).first()
            old_pack_quantity = old_pack.quantity
        new_inv_quantity = ((inv_total_quantity * inv_pack_quantity)  + (record.quantity * old_pack_quantity) - (send_quantity * send_pack_quantity)) / inv_pack_quantity
    else:
        new_inv_quantity = ((inv_total_quantity * inv_pack_quantity) - (send_quantity * send_pack_quantity)) / inv_pack_quantity
    db(iitable.id == inv_item_id).update(quantity = new_inv_quantity)

    # Update Bins
    for inv_bin in inv_bins:
        layout_id = inv_bin["layout_id"]
        if record:
            old_bin = old_bins.get(layout_id)
            send_bin = send_bins.get(layout_id)
            if send_bin and not old_bin:
                new_bin_quantity = ((inv_bin["quantity"] * inv_pack_quantity) - (send_bin["quantity"] * send_pack_quantity)) / inv_pack_quantity
                db(ibtable.id == inv_bin["id"]).update(quantity = new_bin_quantity)
            elif old_bin and not send_bin:
                new_bin_quantity = ((inv_bin["quantity"] * inv_pack_quantity) + (old_bin * old_pack_quantity)) / inv_pack_quantity
                db(ibtable.id == inv_bin["id"]).update(quantity = new_bin_quantity)
            elif send_bin and old_bin:
                new_bin_quantity = ((inv_bin["quantity"] * inv_pack_quantity) + (old_bin * old_pack_quantity) - (send_bin["quantity"] * send_pack_quantity)) / inv_pack_quantity
                db(ibtable.id == inv_bin["id"]).update(quantity = new_bin_quantity)
        else:
            send_bin = send_bins.get(layout_id)
            if send_bin:
                new_bin_quantity = ((inv_bin["quantity"] * inv_pack_quantity) - (send_bin["quantity"] * send_pack_quantity)) / inv_pack_quantity
                db(ibtable.id == inv_bin["id"]).update(quantity = new_bin_quantity)

# =============================================================================
def inv_send_onaccept(form):
    """
       When a inv send record is created
       - create the send_ref if not provided
       - add all inv items with the status of the shipment type
    """

    db = current.db
    settings = current.deployment_settings

    form_vars = form.vars
    send_id = form_vars.id

    # If the send_ref is None then set it up
    stable = db.inv_send
    record = db(stable.id == send_id).select(stable.id,
                                             stable.send_ref,
                                             stable.site_id,
                                             limitby = (0, 1),
                                             ).first()
    if not record.send_ref:
        from .supply import supply_get_shipping_code as get_shipping_code
        code = get_shipping_code(settings.get_inv_send_shortname(),
                                 record.site_id,
                                 stable.send_ref,
                                 )
        record.update_record(send_ref = code)

    # Add all Items matching Shipment Type
    if settings.get_inv_send_add_items_of_shipment_type():
        shipment_type = form_vars.type
        if shipment_type:
            inv_send_add_items_of_shipment_type(send_id, form_vars.site_id, int(shipment_type))

# =============================================================================
def inv_send_postprocess(form):
    """
       When a inv send record is created
       - add all reserved items for linked Inventory Requisitions
    """

    if form.record:
        # @ToDo: Allow Update forms? (Be careful if keeping track in the req as we could delete the send...)
        return

    # Only called when inv_req_reserve_items is active
    #if not current.deployment_settings.get_inv_req_reserve_items():
    #    return

    form_vars = form.vars
    send_id = form_vars.id

    s3db = current.s3db

    ltable = s3db.inv_send_req
    ritable = s3db.inv_req_item
    rbtable = s3db.inv_req_item_inv
    iitable = s3db.inv_inv_item

    query = (ltable.send_id == send_id) & \
            (ltable.req_id == ritable.req_id) & \
            (ritable.site_id == form_vars.site_id) & \
            (ritable.id == rbtable.req_item_id) & \
            (rbtable.inv_item_id == iitable.id)
    items = current.db(query).select(ritable.id,
                                     ritable.item_id,
                                     ritable.item_pack_id,
                                     rbtable.inv_item_id,
                                     rbtable.layout_id,
                                     rbtable.quantity,
                                     iitable.pack_value,
                                     iitable.currency,
                                     iitable.expiry_date,
                                     iitable.item_source_no,
                                     iitable.supply_org_id,
                                     iitable.owner_org_id,
                                     )
    if items:
        # Sort by inv_item_id
        inv_items = {}
        for row in items:
            req_inv_row = row.inv_req_item_inv
            inv_item_id = req_inv_row.inv_item_id
            if inv_item_id not in inv_items:
                req_row = row.inv_req_item
                inv_row = row.inv_inv_item
                inv_items[inv_item_id] = {"req_item_id": req_row.id,
                                          "item_id": req_row.item_id,
                                          "item_pack_id": req_row.item_pack_id,
                                          "pack_value": inv_row.pack_value,
                                          "currency": inv_row.currency,
                                          "expiry_date": inv_row.expiry_date,
                                          "item_source_no": inv_row.item_source_no,
                                          "supply_org_id": inv_row.supply_org_id,
                                          "owner_org_id": inv_row.owner_org_id,
                                          "bins": [],
                                          "quantity": 0,
                                          }
            bin_quantity = req_inv_row.quantity
            if bin_quantity:
                inv_items[inv_item_id]["quantity"] += bin_quantity
                layout_id = req_inv_row.layout_id
                if layout_id:
                    inv_items[inv_item_id]["bins"].append({"layout_id": layout_id,
                                                           "quantity": bin_quantity,
                                                           })

        ttable = s3db.inv_track_item
        sbtable = s3db.inv_send_item_bin
        for inv_item_id in inv_items:
            item = inv_items[inv_item_id]
            track_item_id = ttable.insert(send_id = send_id,
                                          item_id = item["item_id"],
                                          item_pack_id = item["item_pack_id"],
                                          quantity = item["quantity"],
                                          pack_value = item["pack_value"],
                                          currency = item["currency"],
                                          expiry_date = item["expiry_date"],
                                          item_source_no = item["item_source_no"],
                                          supply_org_id = item["supply_org_id"],
                                          owner_org_id = item["owner_org_id"],
                                          req_item_id = item["req_item_id"],
                                          send_inv_item_id = inv_item_id,
                                          status = TRACK_STATUS_TRANSIT, # Record locked (can't edit, no duplication of stock removal)
                                          )
            for req_bin in item["bins"]:
                sbtable.insert(track_item_id = track_item_id,
                               layout_id = req_bin["layout_id"],
                               quantity = req_bin["quantity"],
                               )

# =============================================================================
def inv_send_package_update(send_package_id):
    """
        Update a Shipment Package's Total Weight & Volume
    """

    db = current.db
    s3db = current.s3db

    table = s3db.inv_send_package_item
    itable = s3db.supply_item
    ptable = s3db.supply_item_pack
    ttable = s3db.inv_track_item
    query = (table.send_package_id == send_package_id) & \
            (table.track_item_id == ttable.id) & \
            (ttable.item_id == itable.id) & \
            (ttable.item_pack_id == ptable.id)
    items = db(query).select(table.quantity,
                             itable.weight,
                             itable.volume,
                             ptable.quantity,
                             )
    total_volume = 0
    total_weight = 0
    for row in items:
        quantity = row["inv_send_package_item.quantity"] * row["supply_item_pack.quantity"]
        row = row.supply_item
        volume = row.volume
        if volume:
            total_volume += (volume * quantity)
        weight = row.weight
        if weight:
            total_weight += (weight * quantity)

    db(s3db.inv_send_package.id == send_package_id).update(volume = total_volume,
                                                           weight = total_weight,
                                                           )

# =============================================================================
def inv_send_process(r, **attr):
    """
        Process a Shipment
        - called via POST from inv_send_rheader
        - called via JSON method to reduce request overheads
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    T = current.T

    send_id = r.id

    if not send_id:
        r.error(405, "Can only process a single shipment")

    auth = current.auth
    s3db = current.s3db
    stable = s3db.inv_send

    if not auth.s3_has_permission("update", stable,
                                  record_id = send_id,
                                  ):
        r.unauthorised()

    record = r.record

    if record.status != SHIP_STATUS_IN_PROCESS:
        error = T("No items have been selected for shipping.")
        current.session.error = error
        r.error(409, error,
                tree = '"%s"' % URL(args = [send_id]),
                )

    db = current.db

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
        error = T("No items have been selected for shipping.")
        current.session.error = error
        r.error(409, error,
                tree = '"%s"' % URL(args = [send_id]),
                )

    # Update Send record & lock for editing
    db(stable.id == send_id).update(date = r.utcnow,
                                    status = SHIP_STATUS_SENT,
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
    recv = {"sender_id": record.sender_id,
            "send_ref": record.send_ref,
            "req_ref": record.req_ref,
            "from_site_id": record.site_id,
            "eta": record.delivery_date,
            "recipient_id": record.recipient_id,
            "site_id": record.to_site_id,
            "transport_type": record.transport_type,
            "transported_by": record.transported_by,
            "transport_ref": record.transport_ref,
            "registration_no": record.registration_no,
            "comments": record.comments,
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
        inv_warehouse_free_capacity(record.site_id)

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
        on_inv_send_process(record)

    message = T("Shipment Items sent from Warehouse")
    current.session.confirmation = message

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": URL(args = [send_id, "track_item"]),
                       }, separators=SEPARATORS)

# =============================================================================
def inv_send_received(r, **attr):
    """
        Confirm a Shipment has been Received
        - called via POST from inv_send_rheader
        - called via JSON method to reduce request overheads
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    T = current.T

    send_id = r.id

    if not send_id:
        r.error(405, "Can only confirm a single shipment.")

    auth = current.auth
    s3db = current.s3db
    stable = s3db.inv_send

    if not auth.s3_has_permission("update", stable,
                                  record_id = send_id,
                                  ):
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

    message = T("Shipment received")
    current.session.confirmation = message

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": URL(args = [send_id, "track_item"]),
                       }, separators=SEPARATORS)

# =============================================================================
def inv_send_return_complete(r, **attr):
    """
        Return some stock from a shipment back into the warehouse
        - called via POST from inv_send_rheader
        - called via JSON method to reduce request overheads

        @ToDo: Bin Allocations
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    T = current.T

    send_id = r.id

    if not send_id:
        r.error(405, "Can only return a single shipment")

    s3db = current.s3db

    stable = s3db.inv_send

    if not current.auth.s3_has_permission("update", stable,
                                          record_id = send_id,
                                          ):
        r.unauthorised()

    record = r.record

    if record.status != SHIP_STATUS_RETURNING:
        r.error(409, T("This shipment has not been returned."),
                tree = '"%s"' % URL(args = [send_id]),
                )

    db = current.db

    invtable = s3db.inv_inv_item
    tracktable = s3db.inv_track_item

    # Move the goods back into the warehouse and change the status to received
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
        # Update the receive quantity in the tracking record
        db(tracktable.id == track_item.id).update(recv_quantity = track_item.quantity - return_qnty)
        if return_qnty:
            db(invtable.id == send_inv_id).update(quantity = invtable.quantity + return_qnty)

    db(stable.id == send_id).update(status = SHIP_STATUS_RECEIVED)
    recv_row = db(tracktable.send_id == send_id).select(tracktable.recv_id,
                                                        limitby = (0, 1),
                                                        ).first()
    if recv_row:
        db(s3db.inv_recv.id == recv_row.recv_id).update(date = r.utcnow,
                                                        status = SHIP_STATUS_RECEIVED,
                                                        )

    # Change the status for all track items in this shipment to Received
    db(tracktable.send_id == send_id).update(status = TRACK_STATUS_ARRIVED)

    if current.deployment_settings.get_inv_warehouse_free_capacity_calculated():
        # Update the Warehouse Free capacity
        inv_warehouse_free_capacity(record.site_id)

    redirect(URL(args = [send_id]))

    message = T("Return completed. Stock is back in the Warehouse and can be assigned to Bins")
    current.session.confirmation = message

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": URL(args = [send_id]),
                       }, separators=SEPARATORS)

# =============================================================================
def inv_send_return(r, **attr):
    """
        This will return a shipment that has been sent
        - called via POST from inv_send_rheader
        - called via JSON method to reduce request overheads

        @todo need to roll back commitments
    """

    if r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD,
                next = URL(),
                )

    T = current.T

    send_id = r.id

    if not send_id:
        r.error(405, "Can only return a single shipment",
                next = URL(),
                )

    s3db = current.s3db

    stable = s3db.inv_send

    if not current.auth.s3_has_permission("update", stable,
                                          record_id = send_id,
                                          ):
        r.unauthorised()

    if r.record.status == SHIP_STATUS_IN_PROCESS:
        r.error(409, T("This shipment has not been sent - it cannot be returned because it can still be edited."),
                tree = '"%s"' % URL(args = [send_id]),
                )

    db = current.db

    rtable = s3db.inv_recv
    tracktable = s3db.inv_track_item

    # Change the status to Returning
    db(stable.id == send_id).update(status = SHIP_STATUS_RETURNING)
    recv_row = db(tracktable.send_id == send_id).select(tracktable.recv_id,
                                                        limitby = (0, 1),
                                                        ).first()
    if recv_row:
        db(rtable.id == recv_row.recv_id).update(date = r.utcnow,
                                                 status = SHIP_STATUS_RETURNING,
                                                 )

    # Set all track items to status of returning
    db(tracktable.send_id == send_id).update(status = TRACK_STATUS_RETURNING)

    message = T("Sent Shipment has returned, indicate how many items will be returned to Warehouse.")
    current.session.confirmation = message

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps({"message": s3_str(message),
                       "tree": URL(args = [send_id, "track_item"]),
                       }, separators=SEPARATORS)

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
            if settings.get_inv_send_packaging():
                tabs.append((T("Packaging"), "send_package"))
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
                from .org import org_organisation_logo
                logo = org_organisation_logo(site.organisation_id)
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
                address = NONE
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

            rfooter = TAG[""]()

            if status != SHIP_STATUS_CANCEL and \
               r.method != "form":
                if current.auth.s3_has_permission("update", "inv_send",
                                                  record_id = record.id,
                                                  ):

                    if status == SHIP_STATUS_IN_PROCESS and \
                       settings.get_inv_wizards():
                        actions = DIV(A(ICON("wizard"),
                                             " ",
                                             T("Wizard"),
                                            _href = URL(args = [record.id,
                                                                "wizard",
                                                                ]
                                                        ),
                                            _class = "action-btn",
                                            )
                                      )
                    else:
                        actions = None
                        
                    packaging = None
                    # Don't show buttons unless Items have been added
                    tracktable = s3db.inv_track_item
                    query = (tracktable.send_id == send_id)
                    item = db(query).select(tracktable.id,
                                            limitby = (0, 1),
                                            ).first()
                    if item:
                        if not actions:
                            actions = DIV()
                        jappend = s3.js_global.append
                        if s3.debug:
                            s3.scripts.append("/%s/static/scripts/S3/s3.inv_send_rheader.js" % r.application)
                        else:
                            s3.scripts.append("/%s/static/scripts/S3/s3.inv_send_rheader.min.js" % r.application)

                        if status == SHIP_STATUS_IN_PROCESS:
                            actions.append(A(ICON("print"),
                                             " ",
                                             T("Picking List"),
                                             _href = URL(args = [record.id,
                                                                 "pick_list.xls",
                                                                 ]
                                                         ),
                                             _class = "action-btn",
                                             )
                                           )

                            if settings.get_inv_send_packaging():
                                actions.append(A(ICON("print"),
                                                 " ",
                                                 T("Labels"),
                                                 _href = URL(args = [record.id,
                                                                     "labels.xls",
                                                                     ]
                                                             ),
                                                 _class = "action-btn",
                                                 )
                                               )

                            actions.append(A(T("Send Shipment"),
                                             _href = URL(args = [record.id,
                                                                 "process",
                                                                 ]
                                                         ),
                                             _id = "send-process",
                                             _class = "action-btn",
                                             )
                                           )

                            jappend('''i18n.send_process_confirm="%s"''' % \
                                T("Do you want to send this shipment?"))

                        elif status == SHIP_STATUS_RETURNING:
                            actions.append(A(T("Complete Returns"),
                                             _href = URL(c = "inv",
                                                         f = "send",
                                                         args = [record.id,
                                                                 "return_complete",
                                                                 ]
                                                         ),
                                             _id = "return-process",
                                             _class = "action-btn"
                                             )
                                           )
                            jappend('''i18n.return_process_confirm="%s"''' % \
                                T("Do you want to complete the return process?"))

                        elif status == SHIP_STATUS_SENT:
                            actions.append(A(T("Manage Returns"),
                                             _href = URL(c = "inv",
                                                         f = "send",
                                                         args = [record.id,
                                                                 "return",
                                                                 ],
                                                         vars = None,
                                                         ),
                                             _id = "send-return",
                                             _class = "action-btn",
                                             _title = T("Only use this button to accept back into stock some items that were returned from a delivery.")
                                             )
                                           )
                            jappend('''i18n.send_return_confirm="%s"''' % \
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
                            jappend('''i18n.send_receive_confirm="%s"''' % \
                                T("Confirm that the shipment has been received by a destination which will not record the shipment directly into the system."))

                        if status != SHIP_STATUS_RECEIVED:

                            if settings.get_inv_send_packaging():
                                if status == SHIP_STATUS_IN_PROCESS:
                                    # Insert in front of 'Send Shipment'
                                    index = -1
                                else:
                                    # Append at end
                                    index = len(actions)
                                actions.insert(index, A(ICON("print"),
                                                        " ",
                                                        T("Packing List"),
                                                        _href = URL(args = [record.id,
                                                                            "packing_list.xls",
                                                                            ]
                                                                    ),
                                                        _class = "action-btn",
                                                        )
                                               )
                            
                            if settings.get_inv_send_gift_certificate():
                                if status == SHIP_STATUS_IN_PROCESS:
                                    # Insert in front of 'Send Shipment'
                                    index = -1
                                else:
                                    # Append at end
                                    index = len(actions)
                                actions.insert(index, A(ICON("print"),
                                                        " ",
                                                        T("Gift Certificate"),
                                                        _href = URL(c = "inv",
                                                                    f = "send",
                                                                    args = [record.id,
                                                                            "gift_certificate.xls",
                                                                            ]
                                                                    ),
                                                        _class = "action-btn"
                                                        )
                                               )

                            if status != SHIP_STATUS_IN_PROCESS:
                                actions.append(A(T("Cancel Shipment"),
                                                 _href = URL(c = "inv",
                                                             f = "send",
                                                             args = [record.id,
                                                                     "cancel",
                                                                     ]
                                                             ),
                                                 _id = "send-cancel",
                                                 _class = "delete-btn"
                                                 )
                                               )

                                jappend('''i18n.send_cancel_confirm="%s"''' % \
                                    T("Do you want to cancel this sent shipment? The items will be returned to the Warehouse. This action CANNOT be undone!"))

                    if actions:
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
        Default Footer for the Waybill
        - called by inv_send_form
        - has come from Red Cross
    """

    T = current.T
    return DIV(TABLE(TR(TH(T("Commodities Loaded")),
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

# =============================================================================
def inv_stock_movements(resource, selectors, orderby):
    """
        Extraction method for stock movements report

        Args:
            resource: the S3Resource (inv_inv_item)
            selectors: the field selectors
            orderby: orderby expression

        Note:
            Transactions can be filtered by earliest/latest date
            using an S3DateFilter with selector="_transaction.date"

        TODO:
            Does not take manual stock adjustments into account
            Does not represent sites or Waybill/GRN as
               links (breaks PDF export, but otherwise it's useful)
    """

    # Extract the stock item data
    selectors = ["id",
                 "site_id",
                 "site_id$name",
                 "item_id$item_category_id",
                 "send_bin.layout_id",
                 #"recv_bin.layout_id",
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
                    (T("Bins"), "layout", {}, "hierarchy"),
                    ]
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
def inv_timeline(r, **attr):
    """
        Display the Shipments on a Simile Timeline

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
        return NONE

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
        return NONE

    return quantity_needed

# =============================================================================
def inv_update_commit_quantities_and_status(req):
    """
        Update commit quantities and status of an Inventory Requisition

        Args:
            req: the inv_req record (Row)
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
                item.update_record(quantity_commit = committed_quantity)

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
                          delete = False,
                          ):
    """
        Create/Update the Stock Card
    """

    db = current.db
    s3db = current.s3db

    iitable = s3db.inv_inv_item
    ibtable = s3db.inv_inv_item_bin

    # read the data for these inv_item_ids
    len_ids = len(inv_item_ids)
    if len_ids == 1:
        query = (iitable.id == inv_item_ids[0])
        #limitby = (0, 1)
    else:
        query = (iitable.id.belongs(inv_item_ids))
        #limitby = (0, len_ids)

    left = ibtable.on(ibtable.inv_item_id == iitable.id)

    rows = db(query).select(iitable.id,
                            iitable.site_id,
                            iitable.item_id,
                            iitable.item_source_no,
                            iitable.supply_org_id,
                            iitable.expiry_date,
                            iitable.item_pack_id,
                            iitable.quantity,
                            ibtable.layout_id,
                            ibtable.quantity,
                            left = left,
                            # Can't limitby as we don't know how many we split to for the left
                            #limitby = limitby,
                            )

    # Lookup Packs
    siptable = s3db.supply_item_pack
    item_ids = [row["inv_inv_item.item_id"] for row in rows]
    packs = db(siptable.item_id.belongs(item_ids)).select(siptable.id,
                                                          siptable.item_id,
                                                          siptable.quantity,
                                                          )
    packs_by_id = {}
    packs_by_item = {}
    for row in packs:
        pack_id = row.id
        quantity = row.quantity
        packs_by_id[pack_id] = quantity
        if quantity == 1:
            # The Pack used by the Card
            packs_by_item[row.item_id] = pack_id

    # Group by inv_item_id
    inv_items = {}
    for row in rows:
        inv_item_id = row["inv_inv_item.id"]
        if inv_item_id in inv_items:
            inv_items[inv_item_id].append(row)
        else:
            inv_items[inv_item_id] = [row]

    sctable = s3db.inv_stock_card
    sltable = s3db.inv_stock_log

    for inv_item_id in inv_items:
        bins = inv_items[inv_item_id]
        inv_item = bins[0].inv_inv_item
        site_id = inv_item.site_id
        item_id = inv_item.item_id
        item_source_no = inv_item.item_source_no
        supply_org_id = inv_item.supply_org_id
        expiry_date = inv_item.expiry_date

        # Search for existing Stock Card
        query = (sctable.site_id == site_id) & \
                (sctable.item_id == item_id) & \
                (sctable.item_source_no == item_source_no) & \
                (sctable.supply_org_id == supply_org_id) & \
                (sctable.expiry_date == expiry_date)

        exists = db(query).select(sctable.id,
                                  limitby = (0, 1),
                                  ).first()
        if exists:
            card_id = exists.id
        else:
            # Create Stock Card
            card_id = sctable.insert(site_id = site_id,
                                     item_id = item_id,
                                     item_pack_id = packs_by_item[item_id],
                                     item_source_no = item_source_no,
                                     supply_org_id = supply_org_id,
                                     expiry_date = expiry_date,
                                     )
            onaccept = s3db.get_config("inv_stock_card", "create_onaccept")
            if onaccept:
                # Generate the Stock Card No.
                onaccept(Storage(vars = Storage(id = card_id,
                                                site_id = site_id,
                                                )
                                 ))
            quantity_out = 0

        pack_quantity = packs_by_id[inv_item.item_pack_id]
        inv_quantity = inv_item.quantity
        binned_quantity = sum([row["inv_inv_item_bin.quantity"] for row in bins if row["inv_inv_item_bin.quantity"] is not None])

        if inv_quantity > binned_quantity:
            # We have some unbinned
            if binned_quantity > 0:
                # We have some binned too, so the unbinned won't show as a separate row
                bins.append(Storage(inv_inv_item_bin = Storage(layout_id = None)))

        # Read all matching inv_items
        query = (iitable.site_id == site_id) & \
                (iitable.item_id == item_id) & \
                (iitable.item_source_no == item_source_no) & \
                (iitable.expiry_date == expiry_date) & \
                (iitable.id != inv_item.id)

        for row in bins:
            bin_record = row.inv_inv_item_bin
            layout_id = bin_record.layout_id
            if layout_id:
                if delete:
                    delete_quantity = bin_record.quantity * pack_quantity
                    quantity = 0
                else:
                    quantity = bin_record.quantity * pack_quantity

                # Need to match with all others in this bin
                match_query = query & (ibtable.inv_item_id == iitable.id) & \
                                      (ibtable.layout_id == layout_id)
                matches = db(match_query).select(iitable.item_pack_id,
                                                 ibtable.quantity,
                                                 )
                for match in matches:
                    quantity += (match["inv_inv_item_bin.quantity"] * packs_by_id[match["inv_inv_item.item_pack_id"]])

            else:
                # Unbinned
                if delete:
                    delete_quantity = (inv_quantity - binned_quantity) * pack_quantity
                    quantity = 0
                else:
                    quantity = (inv_quantity - binned_quantity) * pack_quantity

                # Need to match with all other unbinned
                matches = db(query).select(iitable.id,
                                           iitable.quantity,
                                           iitable.item_pack_id,
                                           ibtable.quantity,
                                           left = left,
                                           )
                # Group by inv_item_id
                match_inv_items = {}
                for match in matches:
                    inv_item_id = match["inv_inv_item.id"]
                    if inv_item_id in match_inv_items:
                        match_inv_items[inv_item_id].append(match)
                    else:
                        match_inv_items[inv_item_id] = [match]

                for inv_item_id in match_inv_items:
                    match_bins = match_inv_items[inv_item_id]
                    match_inv_item = match_bins[0].inv_inv_item
                    match_pack_quantity = packs_by_id[match_inv_item.item_pack_id]
                    match_quantity = match_inv_item.quantity
                    match_binned_quantity = sum([match["inv_inv_item_bin.quantity"] for match in match_bins if match["inv_inv_item_bin.quantity"] is not None])
                    quantity += ((match_quantity - match_binned_quantity) * match_pack_quantity)

            if exists:
                # Lookup Latest Log Entry for this Bin (or Unbinned)
                log_query = (sltable.card_id == card_id) & \
                            (sltable.layout_id == layout_id)
                log = db(log_query).select(sltable.date,
                                           sltable.balance,
                                           orderby = ~sltable.date,
                                           limitby = (0, 1),
                                           ).first()
                if delete:
                    quantity_in = 0
                    quantity_out = delete_quantity
                elif not log:
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
                quantity_in = quantity
                if delete:
                    quantity_out = delete_quantity

            if quantity_in == quantity_out:
                # An untouched bin
                continue

            balance = quantity

            # Add Log Entry
            sltable.insert(card_id = card_id,
                           date = current.request.utcnow,
                           send_id = send_id,
                           recv_id = recv_id,
                           layout_id = layout_id,
                           quantity_in = quantity_in,
                           quantity_out = quantity_out,
                           balance = balance,
                           comments = comments,
                           )

# =============================================================================
def inv_track_item_deleting(track_item_id):
    """
       A track item can only be deleted if the status is Preparing
       When a track item record is deleted and it is linked to an inv_item
       then the inv_item quantity will be adjusted.
    """

    db = current.db

    table = db.inv_track_item
    record = db(table.id == track_item_id).select(table.send_inv_item_id,
                                                  table.status,
                                                  limitby = (0, 1),
                                                  ).first()
    if record.status != TRACK_STATUS_PREPARING: # 1
        # Do not allow
        return False

    inv_item_id = record.send_inv_item_id
    if not inv_item_id:
        return True

    # This is linked to a Warehouse Inventory item:
    # - place the stock back in the warehouse

    s3db = current.s3db

    sbtable = s3db.inv_send_item_bin
    iitable = s3db.inv_inv_item
    ibtable = s3db.inv_inv_item_bin
    iptable = s3db.supply_item_pack

    # Read the Send Item, including Bins
    query = (table.id == track_item_id) & \
            (table.item_pack_id == iptable.id)
    left = sbtable.on(sbtable.track_item_id == table.id)
    rows = db(query).select(table.quantity,
                            iptable.quantity,
                            sbtable.layout_id,
                            sbtable.quantity,
                            left = left,
                            )

    row = rows.first()
    send_quantity = row["inv_track_item.quantity"]
    send_pack_quantity = row["supply_item_pack.quantity"]
    send_bins = {}
    for row in rows:
        bin_row = row["inv_send_item_bin"]
        bin_quantity = bin_row.quantity
        if bin_quantity:
            send_bins[bin_row.layout_id] = bin_quantity

    # Read the Inv Item, including Bins
    query = (iitable.id == inv_item_id) & \
            (iitable.item_pack_id == iptable.id)
    left = ibtable.on((ibtable.inv_item_id == iitable.id) & \
                      (ibtable.layout_id.belongs(send_bins.keys())))
    rows = db(query).select(iitable.quantity,
                            iptable.quantity,
                            ibtable.id,
                            ibtable.layout_id,
                            ibtable.quantity,
                            left = left,
                            )

    row = rows.first()
    inv_total_quantity = row["inv_inv_item.quantity"]
    inv_pack_quantity = row["supply_item_pack.quantity"]
    inv_bins = []
    for row in rows:
        bin_row = row["inv_inv_item_bin"]
        layout_id = bin_row.layout_id 
        if layout_id:
            inv_bins.append({"id": bin_row.id,
                             "layout_id": layout_id,
                             "quantity": bin_row.quantity or 0,
                             })

    # Update Stock level
    new_inv_quantity = ((inv_total_quantity * inv_pack_quantity) + (send_quantity * send_pack_quantity)) / inv_pack_quantity
    db(iitable.id == inv_item_id).update(quantity = new_inv_quantity)

    # Update Bins
    for inv_bin in inv_bins:
        layout_id = inv_bin["layout_id"]
        send_bin_quantity = send_bins[layout_id]
        new_bin_quantity = ((inv_bin["quantity"] * inv_pack_quantity) + (send_bin_quantity * send_pack_quantity)) / inv_pack_quantity
        db(ibtable.id == inv_bin["id"]).update(quantity = new_bin_quantity)

    return True

# =============================================================================
def inv_warehouse_controller():
    """
        RESTful CRUD controller

        Defined in the model for forwards from org/site controller
    """

    s3 = current.response.s3
    request = current.request
    get_vars = request.get_vars

    request_args = request.args
    if "viewing" in get_vars:
        viewing = get_vars.viewing
        tn, record_id = viewing.split(".", 1)
        if tn == "inv_warehouse":
            request_args.insert(0, record_id)

    # CRUD pre-process
    def prep(r):
        # Function to call for all Site Instance Types
        from .org import org_site_prep
        org_site_prep(r)

        # "show_obsolete" var option can be added (btn?) later to disable this filter
        # @ToDo: Better to do this using a default_filter BUT we then need to have the filter visible, which isn't great UX for a little-used filter...
        if r.method in [None, "list"] and \
            not r.vars.get("show_obsolete", False):
            r.resource.add_filter(current.db.inv_warehouse.obsolete != True)

        # Add this to Template if-desired
        #if r.representation == "xls":
        #    list_fields = r.resource.get_config("list_fields")
        #    list_fields += ["location_id$lat",
        #                    "location_id$lon",
        #                    "location_id$inherited",
        #                    ]

        return True
    s3.prep = prep

    # CRUD post-process
    def postp(r, output):
        if r.interactive and not r.component and r.method != "import":
            if current.auth.s3_has_permission("read", "inv_inv_item"):
                # Change Action buttons to open Stock Tab by default
                read_url = URL(f = "warehouse",
                               args = ["[id]", "inv_item"],
                               )
                update_url = URL(f = "warehouse",
                                 args = ["[id]", "inv_item"],
                                 )
                s3_action_buttons(r,
                                  read_url = read_url,
                                  update_url = update_url,
                                  )
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
        return output
    s3.postp = postp

    if "extra_data" in get_vars:
        resourcename = "inv_item"
    else:
        resourcename = "warehouse"
    csv_stylesheet = "%s.xsl" % resourcename

    if len(request_args) > 1 and request_args[1] in ("req", "send", "recv"):
        # Sends/Receives should break out of Component Tabs
        # to allow access to action buttons in inv_recv rheader
        native = True
    else:
        native = False

    return current.rest_controller(#hide_filter = {"inv_item": False,
                                   #               "_default": True,
                                   #               },
                                   # Extra fields for CSV uploads:
                                   #csv_extra_fields = [{"label": "Organisation",
                                   #                     "field": s3db.org_organisation_id(comment = None)
                                   #                     },
                                   #                    ]
                                   csv_stylesheet = csv_stylesheet,
                                   csv_template = resourcename,
                                   native = native,
                                   rheader = inv_rheader,
                                   )

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
        r = s3_request("inv", "warehouse", args=[], vars={})
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

            Args:
                r: the S3Request
                attr: controller options for this request
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        response = current.response
        s3 = response.s3

        output = {"title": T("Check Request"),
                  "rheader": inv_req_rheader(r, check_page=True),
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
                                                   f = "req",
                                                   args = [r.id, "send"],
                                                   vars = {"site_id": site_id},
                                                   ),
                                       _class = "action-btn",
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

    if date and datetime.datetime(date.year, date.month, date.day) < current.request.utcnow:
        return SPAN(dtstr,
                    _class = "expired",
                    )
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

            Args:
                key: the key Field
                values: the values
                fields: never used for custom fns (retained for API compatibility)
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

            Args:
                row: the row

            Returns:
                The representation of the Row, or None if there
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

            Args:
                key: the key Field
                values: the values
                fields: never used for custom fns (retained for API compatibility)
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

            Args:
                row: the row

            Returns:
                The representation of the Row, or None if there
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

            Args:
                key: the key field
                values: the values to look up
                fields: unused (retained for API compatibility)
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

            Args:
                row: the Row
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

    def __init__(self,
                 show_bin = True,
                 ):

        self.show_bin = show_bin

        super(inv_InvItemRepresent, self).__init__(lookup = "inv_inv_item")

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            Args:
                key: the key Field
                values: the values
                fields: never used for custom fns (retained for API compatibility)
        """

        show_bin = self.show_bin

        s3db = current.s3db

        itable = s3db.inv_inv_item
        stable = s3db.supply_item

        fields = [itable.id,
                  itable.expiry_date,
                  itable.item_source_no,
                  itable.owner_org_id,
                  stable.name,
                  #stable.um,
                  ]

        left = [stable.on(stable.id == itable.item_id),
                ]

        if show_bin:
            ibtable = s3db.inv_inv_item_bin
            fields.append(ibtable.layout_id)
            left.append(ibtable.on(ibtable.inv_item_id == itable.id))

        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(*fields,
                                        left = left
                                        )

        self.queries += 1

        # Bulk-represent owner_org_ids
        organisation_id = str(itable.owner_org_id)
        organisation_ids = [row[organisation_id] for row in rows]
        if organisation_ids:
            # Results cached in the represent class
            itable.owner_org_id.represent.bulk(organisation_ids)

        if show_bin:
            # Bulk-represent Bins
            layout_id = str(ibtable.layout_id)
            layout_ids = [row[layout_id] for row in rows]
            if layout_ids:
                # Results cached in the represent class
                ibtable.layout_id.represent.bulk(layout_ids)

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            Args:
                row: the Row
        """

        s3db = current.s3db

        iitem = row.inv_inv_item

        stringify = lambda string: string if string else ""

        ctn = stringify(iitem.item_source_no)
        org = s3db.inv_inv_item.owner_org_id.represent(iitem.owner_org_id)

        if self.show_bin:
            item_bin = s3db.inv_inv_item_bin.layout_id.represent(row.inv_inv_item_bin.layout_id)
        else:
            item_bin = None

        expires = iitem.expiry_date
        if expires:
            expires = "expires: %s" % \
                      S3DateTime.date_represent(expires, utc=True)
        else:
            expires = ""

        items = []
        append = items.append
        for string in [row.supply_item.name, expires, ctn, org, item_bin]:
            if string and string != NONE:
                append(string)
                append(" - ")
        return TAG[""](items[:-1])

# =============================================================================
class inv_PackageRepresent(S3Represent):
    """
        Represent a Package
    """

    def __init__(self,
                 show_link = False,
                 ):

        fields = ["type",
                  "name",
                  ]

        super(inv_PackageRepresent, self).__init__(lookup = "inv_package",
                                                   fields = fields,
                                                   show_link = show_link,
                                                   )

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            Args:
                row: the Row
        """

        v = "%s %s" % (current.db.inv_package.type.represent(row.type),
                       row.name,
                       )

        return v

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

            Args:
                key: the key Field
                values: the values
                fields: never used for custom fns (retained for API compatibility)
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

            Args:
                row: the Row
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
class inv_RecvWizard(S3CrudWizard):
    """
        Wizard for Receiving a New Shipment
    """

    def __init__(self):

        T = current.T

        super(inv_RecvWizard, self).__init__()

        self.pages = [{"page": "recv",
                       "label": T("Incoming Shipment"),
                       },
                      {"page": "items",
                       "label": T("Add Items"),
                       "component": "track_item",
                       "required": True,
                       },
                      {"page": "bins",
                       "label": T("Allocate to Bins"),
                       "component": "track_item",
                       },
                      {"page": "document",
                       "label": "%s %s" % (T("Upload"),
                                           current.deployment_settings.get_inv_recv_shortname(),
                                           ),
                       "component": "document",
                       },
                      {"page": "process",
                       "label": T("Process"),
                       },
                      ]

    # -------------------------------------------------------------------------
    def __call__(self, r, **attr):
    
        if r.record and r.record.status not in (SHIP_STATUS_SENT,
                                                SHIP_STATUS_IN_PROCESS,
                                                ):
            # Cannot use the Wizard
            redirect(r.url(method = "",
                           component = "",
                           vars = {},
                           ))

        get_vars = r.get_vars
        current_page = get_vars.get("page")
        if current_page == "process":
            # Return a button to Process the Incoming Shipment
            T = current.T
            # Script already added as rheader being run, even though not displayed in page
            #current.response.s3.scripts.append("/%s/static/scripts/S3/s3.inv_recv_rheader.js" % r.application)
            next_btn = A(T("Finish"),
                         _href = URL(c = "inv",
                                     f = "recv",
                                     args = [r.id,
                                             "process",
                                             ],
                                     ),
                         _id = "recv-process",
                         _class = "crud-submit-button button small next",
                         )
            return {"form": DIV(P(T("Clicking Finish will add all the Items from the Shipment to the Inventory.")),
                                P(T("This step cannot be reversed.")),
                                ),
                    "controls": self._controls(r, next_btn=next_btn),
                    "header": self._header(r),
                    }

        elif current_page == "bins":
            # Check to see if we can streamline as we only have 1 item
            # @ToDo: Make this a default if insertable = False?
            record_id = r.id
            s3db = current.s3db
            ttable = s3db.inv_track_item
            items = current.db(ttable.recv_id == record_id).select(ttable.id,
                                                                   limitby = (0, 2),
                                                                   )
            if len(items) == 1:
                if not r.component_id:
                    # Open this record rather than list view
                    redirect(r.url(component_id = items.first().id))
                else:
                    current.response.s3.crud.submit_button = "Next"
                    if r.http == "POST":
                        next_vars = dict(get_vars)
                        next_vars["page"] = "document"
                        self.method.next = r.url(id = record_id,
                                                 component = "document",
                                                 component_id = 0,
                                                 method = "wizard",
                                                 vars = next_vars,
                                                 )

        return super(inv_RecvWizard, self).__call__(r, **attr)

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

            Args:
                key: the key Field
                values: the values
                fields: never used for custom fns (retained for API compatibility)
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

            Args:
                row: the Row
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

            Args:
                key: the key field
                values: the values to look up
                fields: unused (retained for API compatibility)
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

            Args:
                row: the Row
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
    def _lookup(self, values, rows=None):
        """
            Lazy lookup values.

            Args:
                values: list of values to lookup
                rows: rows referenced by values (if values are foreign keys)
                      optional

            Modified from super to NOT int values (otherwise req_refs like '00001' fail!)
        """

        theset = self.theset

        keys = {}
        items = {}
        lookup = {}

        # Check whether values are already in theset
        table = self.table
        for _v in values:
            v = _v
            keys[v] = _v
            if v is None:
                items[_v] = self.none
            elif v in theset:
                items[_v] = theset[v]
            else:
                lookup[v] = True

        if table is None or not lookup:
            return items

        if table and self.hierarchy:
            # Does the lookup table have a hierarchy?
            from .s3hierarchy import S3Hierarchy
            h = S3Hierarchy(table._tablename)
            if h.config:
                def lookup_parent(node_id):
                    parent = h.parent(node_id)
                    if parent and \
                       parent not in theset and \
                       parent not in lookup:
                        lookup[parent] = False
                        lookup_parent(parent)
                    return
                for node_id in list(lookup.keys()):
                    lookup_parent(node_id)
            else:
                h = None
        else:
            h = None

        # Get the primary key
        pkey = self.key
        ogetattr = object.__getattribute__
        try:
            key = ogetattr(table, pkey)
        except AttributeError:
            return items

        # Use the given rows to lookup the values
        pop = lookup.pop
        represent_row = self.represent_row
        represent_path = self._represent_path
        if rows and not self.custom_lookup:
            rows_ = dict((row[key], row) for row in rows)
            self.rows.update(rows_)
            for row in rows:
                k = row[key]
                if k not in theset:
                    if h:
                        theset[k] = represent_path(k,
                                                   row,
                                                   rows = rows_,
                                                   hierarchy = h,
                                                   )
                    else:
                        theset[k] = represent_row(row)
                if pop(k, None):
                    items[keys.get(k, k)] = theset[k]

        # Retrieve additional rows as needed
        if lookup:
            if not self.custom_lookup:
                try:
                    # Need for speed: assume all fields are in table
                    fields = [ogetattr(table, f) for f in self.fields]
                except AttributeError:
                    # Ok - they are not: provide debug output and filter fields
                    current.log.error(sys.exc_info()[1])
                    fields = [ogetattr(table, f)
                              for f in self.fields if hasattr(table, f)]
            else:
                fields = []
            rows = self.lookup_rows(key, list(lookup.keys()), fields=fields)
            rows = {row[key]: row for row in rows}
            self.rows.update(rows)
            if h:
                for k, row in rows.items():
                    if lookup.pop(k, None):
                        items[keys.get(k, k)] = represent_path(k,
                                                               row,
                                                               rows = rows,
                                                               hierarchy = h,
                                                               )
            else:
                for k, row in rows.items():
                    lookup.pop(k, None)
                    items[keys.get(k, k)] = theset[k] = represent_row(row)

        # Anything left gets set to default
        if lookup:
            for k in lookup:
                items[keys.get(k, k)] = self.default

        return items

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Lookup all rows referenced by values.
            (in foreign key representations)

            Args:
                key: the key Field
                values: the values
                fields: the fields to retrieve
        """

        fields = ("id",
                  "req_ref",
                  )

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

            Args:
                k: the key
                v: the representation of the key
                row: the row with this key (unused in the base class)
        """

        if self.linkto:
            k = str(row.id)
            _href = self.linkto.replace("[id]", k) \
                               .replace("%5Bid%5D", k)
            
            if self.pdf:
                _href = "%s/%s" % (_href,
                                   "form",
                                   )
            return A(v,
                     _href = _href,
                     )
        else:
            return v

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            Args:
                row: the Row
        """

        return row.req_ref or NONE

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

            Args:
                key: the key Field
                values: the values
                fields: never used for custom fns (retained for API compatibility)
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

            Args:
                row: the Row
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
class inv_SendWizard(S3CrudWizard):
    """
        Wizard for Sending a New Shipment
    """

    def __init__(self):

        T = current.T

        super(inv_SendWizard, self).__init__()

        self.pages = [{"page": "send",
                       "label": T("Outgoing Shipment"),
                       },
                      {"page": "items",
                       "label": T("Add Items"),
                       "component": "track_item",
                       "required": True,
                       },
                      {"page": "packaging",
                       "label": T("Packaging"),
                       "component": "send_package",
                       },
                      {"page": "document",
                       "label": "%s %s" % (T("Upload"),
                                           current.deployment_settings.get_inv_send_shortname(),
                                           ),
                       "component": "document",
                       },
                      {"page": "process",
                       "label": T("Process"),
                       },
                      ]

    # -------------------------------------------------------------------------
    def __call__(self, r, **attr):
    
        if r.record and r.record.status != SHIP_STATUS_IN_PROCESS:
            # Cannot use the Wizard
            redirect(r.url(method = "",
                           component = "",
                           vars = {},
                           ))

        current_page = r.get_vars.get("page")
        if current_page == "process":
            # Return a button to Process the Outgoing Shipment
            T = current.T
            # Script already added as rheader being run, even though not displayed in page
            #current.response.s3.scripts.append("/%s/static/scripts/S3/s3.inv_send_rheader.js" % r.application)
            next_btn = A(T("Finish"),
                         _href = URL(c = "inv",
                                     f = "send",
                                     args = [r.id,
                                             "process",
                                             ],
                                     ),
                         _id = "send-process",
                         _class = "crud-submit-button button small next",
                         )
            return {"form": DIV(P(T("Clicking Finish will lock the Sent Shipment, create an Inbound Shipment for the recipient Site, update Stock Cards and update Request Status(es).")),
                                P(T("This step cannot be reversed.")),
                                ),
                    "controls": self._controls(r, next_btn=next_btn),
                    "header": self._header(r),
                    }

        elif current_page == "items":
            # Add a button to print the Picking List
            current.response.s3.wizard_buttons = DIV(A(ICON("print"),
                                                       " ",
                                                       current.T("Picking List"),
                                                       _href = URL(args = [r.id,
                                                                           "pick_list.xls",
                                                                           ]
                                                                   ),
                                                       _class = "action-btn",
                                                       ),
                                                     _class = "wizard-btns",
                                                     )

        elif current_page == "packaging":
            # Add buttons to print the Labels, Packing List and Gift Certificate
            T = current.T
            current.response.s3.wizard_buttons = DIV(A(ICON("print"),
                                                       " ",
                                                       T("Labels"),
                                                       _href = URL(args = [r.id,
                                                                           "labels.xls",
                                                                           ]
                                                                   ),
                                                       _class = "action-btn",
                                                       ),
                                                     A(ICON("print"),
                                                       " ",
                                                       T("Packing List"),
                                                       _href = URL(args = [r.id,
                                                                           "packing_list.xls",
                                                                           ]
                                                                   ),
                                                       _class = "action-btn",
                                                       ),
                                                     A(ICON("print"),
                                                       " ",
                                                       T("Gift Certificate"),
                                                       _href = URL(args = [r.id,
                                                                           "gift_certificate.xls",
                                                                           ]
                                                                   ),
                                                       _class = "action-btn",
                                                       ),
                                                     _class = "wizard-btns",
                                                     )

        return super(inv_SendWizard, self).__call__(r, **attr)

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

            Args:
                key: the key field
                values: the values to look up
                fields: unused (retained for API compatibility)
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

            Args:
                row: the Row
        """

        send_inv_item_id = row.send_inv_item_id
        if not send_inv_item_id:
            return NONE

        return current.db.inv_track_item.send_inv_item_id.represent(send_inv_item_id,
                                                                    show_link = False,
                                                                    )

# END =========================================================================
