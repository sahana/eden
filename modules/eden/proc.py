# -*- coding: utf-8 -*-

""" Sahana Eden Procurement Model

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

__all__ = ["S3SupplierModel",
           "S3ProcurementModel",
           "proc_plan_rheader"]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3ProcurementModel(S3Model):
    """
        Procurement

        A module to handle Procurement

        Currently handles
            Suppliers
            Planned Procurements

        @ToDo: Extend to
            Purchase Requests (PR)
            Requests for Quotation (RFQ)
            Competitive Bid Analysis (CBA)
            Purchase Orders (PO)
    """

    names = ["proc_plan",
             "proc_plan_item"
            ]
    
    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        currency_type = s3.currency_type
        item_id = self.supply_item_entity_id
        supply_item_id = self.supply_item_id
        item_pack_id = self.supply_item_pack_id
        item_pack_virtualfields = self.supply_item_pack_virtualfields

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        s3_date_format = settings.get_L10n_date_format()
        s3_date_represent = lambda dt: S3DateTime.date_represent(dt, utc=True)

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
        table = self.define_table(tablename,
                                  self.super_link("site_id", "org_site",
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
                                                  represent=self.org_site_represent),
                                  # @ToDo: Link the Plan to a Project or Activity (if that module is enabled)
                                  #project_id(),
                                  Field("order_date", "date",
                                        label = T("Order Date"),
                                        requires = IS_NULL_OR(IS_DATE(format = s3_date_format)),
                                        represent = s3_date_represent,
                                        widget = S3DateWidget()
                                        ),
                                  Field("eta", "date",
                                        label = T("Date Expected"),
                                        requires = IS_NULL_OR(IS_DATE(format = s3_date_format)),
                                        represent = s3_date_represent,
                                        widget = S3DateWidget()
                                        ),
                                  # @ToDo: Do we want more than 1 supplier per Plan?
                                  supplier_id(),
                                  Field("shipping", "integer",
                                        requires = IS_NULL_OR(IS_IN_SET(proc_shipping_opts)),
                                        represent = lambda opt: proc_shipping_opts.get(opt,
                                                                                       UNKNOWN_OPT),
                                        label = T("Shipping Method"),
                                        default = 0,
                                        ),
                                  # @ToDo: Add estimated shipping costs
                                  s3.comments(),
                                  *s3.meta_fields())

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
        self.configure(tablename,
                       # @ToDo: Move these to controller r.interactive?
                       create_next = plan_item_url,
                       update_next = plan_item_url)

        plan_id = S3ReusableField("plan_id", db.proc_plan, sortby="date",
                                  requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                  "proc_plan.id",
                                                                  self.proc_plan_represent,
                                                                  orderby="proc_plan.date",
                                                                  sort=True)),
                                  represent = self.proc_plan_represent,
                                  label = T("Procurement Plan"),
                                  ondelete = "CASCADE")

        # Items as a component of Plans
        self.add_component("proc_plan_item",
                           proc_plan="plan_id")

        # =====================================================================
        # Procurement Plan Items
        #
        tablename = "proc_plan_item"
        table = self.define_table(tablename,
                                  plan_id(),
                                  item_id,
                                  supply_item_id(),
                                  item_pack_id(),
                                  Field("quantity",
                                        "double",
                                        notnull = True,
                                        label = T("Quantity"),
                                        ),
                                  # @ToDo: Move this into a Currency Widget for the pack_value field
                                  currency_type("currency",
                                                readable=False,
                                                writable=False
                                            ),
                                  Field("pack_value",
                                        "double",
                                        readable=False,
                                        writable=False,
                                        label = T("Value per Pack")),
                                  #Field("pack_quantity",
                                  #      "double",
                                  #      compute = record_pack_quantity), # defined in supply
                                  s3.comments(),
                                  *s3.meta_fields())

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
        plan_item_search = S3Search(
            # Advanced Search only
            advanced=(S3SearchSimpleWidget(
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
                      #S3SearchOptionsWidget(
                      #  name="proc_plan_search_site",
                      #  label=T("Facility"),
                      #  field=["site_id"],
                      #  represent ="%(name)s",
                      #  comment=T("If none are selected, then all are searched."),
                      #  cols = 2
                      #),
                      #S3SearchMinMaxWidget(
                      #  name="proc_plan_search_order_date",
                      #  method="range",
                      #  label=T("Order Date"),
                      #  field=["order_date"]
                      #),
                      #S3SearchMinMaxWidget(
                      #  name="proc_plan_search_eta",
                      #  method="range",
                      #  label=T("Date Expected"),
                      #  field=["eta"]
                      #)
            ))

        # ---------------------------------------------------------------------
        self.configure(tablename,
                       super_entity = "supply_item_entity",
                       search_method = plan_item_search,
                       #report_groupby = db.proc_plan.site_id,
                       report_hide_comments = True)

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                proc_plan_rheader = proc_plan_rheader,
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def proc_plan_represent(id):
        """
        """

        db = current.db
        s3db = current.s3db

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        if not id:
            return NONE
        table = s3db.proc_plan
        query = (table.id == id)
        record = db(query).select(table.site_id,
                                  table.order_date,
                                  limitby=(0, 1)).first()
        if record:
            return "%s (%s)" % (table.site_id.represent(record.site_id),
                                table.order_date.represent(record.order_date))
        else:
            return UNKNOWN_OPT


# =============================================================================
class S3SupplierModel(S3Model):
    """
        Suppliers

        @ToDo: Are these really different enough from Orgs to be worth separating?
               e.g. Donor Orgs vs Purchases
    """

    names = ["proc_supplier",
             "proc_supplier_id",
            ]
    
    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        location_id = self.gis_location_id

        # =====================================================================
        # Suppliers
        #
        tablename = "proc_supplier"
        table = self.define_table(tablename,
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
                                  s3.comments(),
                                  *(s3.address_fields() + s3.meta_fields()))

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

        # Reusable Field
        supplier_id = S3ReusableField("supplier_id", db.proc_supplier, sortby="name",
                                      requires = IS_NULL_OR(IS_ONE_OF(db, "proc_supplier.id",
                                                                      "%(name)s",
                                                                      sort=True)),
                                      represent = self.proc_supplier_represent,
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

        # Plans as a component of Supplier
        self.add_component("proc_plan",
                           proc_supplier="supplier_id")

        # Assets as a component of Supplier
        self.add_component("asset_asset",
                           proc_supplier="supplier_id")

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                proc_supplier_id = supplier_id
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def proc_supplier_represent(id):
        """
        """

        db = current.db
        s3db = current.s3db

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        if not id:
            return NONE
        table = s3db.proc_supplier
        query = (table.id == id)
        record = db(query).select(table.name,
                                  limitby=(0, 1)).first()
        if record:
            return record.name
        else:
            return UNKNOWN_OPT


# =============================================================================
def proc_plan_rheader(r):
    """ Resource Header for Planned Procurements """

    if r.representation == "html":
        plan = r.record
        if plan:

            T = current.T

            tabs = [
                    (T("Edit Details"), None),
                    (T("Items"), "plan_item"),
                   ]
            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table

            rheader = DIV(TABLE(TR( TH("%s: " % table.site_id.label),
                                    table.site_id.represent(plan.site_id),
                                  ),
                                TR( TH("%s: " % table.order_date.label),
                                    table.order_date.represent(plan.order_date),
                                  ),
                                TR( TH("%s: " % table.eta.label),
                                    table.eta.represent(plan.eta),
                                  ),
                                TR( TH("%s: " % table.shipping.label),
                                    table.shipping.represent(plan.shipping),
                                  ),
                               ),
                          rheader_tabs
                         )
            return rheader
    return None

# END =========================================================================
