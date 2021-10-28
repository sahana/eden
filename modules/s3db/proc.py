# -*- coding: utf-8 -*-

""" Sahana Eden Procurement Model

        A module to handle Procurement

        Currently handles
            Planned Procurements
            Purchase Orders (PO)

        @ToDo: Extend to
            Purchase Requests (PR)
            Requests for Quotation (RFQ)
            Competitive Bid Analysis (CBA)

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

__all__ = ("ProcurementPlansModel",
           "PurchaseOrdersModel",
           "proc_rheader"
           )

from gluon import *
from gluon.storage import Storage
from ..s3 import *
#from .supply import SupplyItemPackQuantity

# =============================================================================
class ProcurementPlansModel(S3Model):
    """
        Procurement Plans

        @ToDo: Link Table to Projects
    """

    names = ("proc_plan",
             "proc_plan_item"
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        messages = current.messages
        configure = self.configure
        settings = current.deployment_settings

        SITE_LABEL = settings.get_org_site_label()

        # =====================================================================
        # Planned Procurements
        #
        proc_shipping_opts = {0: messages["NONE"],
                              1: T("Air"),
                              2: T("Rail"),
                              3: T("Road"),
                              4: T("Sea")
                              }

        tablename = "proc_plan"
        define_table(tablename,
                     self.super_link("site_id", "org_site",
                                     label = SITE_LABEL,
                                     default = auth.user.site_id if auth.is_logged_in() else None,
                                     readable = True,
                                     writable = True,
                                     empty = False,
                                     # Comment these to use a Dropdown & not an Autocomplete
                                     #widget = S3SiteAutocompleteWidget(),
                                     #comment = DIV(_class="tooltip",
                                     #              _title="%s|%s" % (T("Inventory"),
                                     #                                messages.AUTOCOMPLETE_HELP)),
                                     represent = self.org_site_represent,
                                     ),
                     s3_date("order_date",
                             label = T("Order Date")
                             ),
                     s3_date("eta",
                             label = T("Date Expected"),
                             ),
                     # @ToDo: Do we want more than 1 supplier per Plan?
                     # @ToDo: Filter to orgs of type 'supplier'
                     self.org_organisation_id(label = T("Supplier")),
                     Field("shipping", "integer",
                           requires = IS_EMPTY_OR(IS_IN_SET(proc_shipping_opts)),
                           represent = s3_options_represent(proc_shipping_opts),
                           label = T("Shipping Method"),
                           default = 0,
                           ),
                     # @ToDo: Add estimated shipping costs
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Procurement Plan"),
            title_display = T("Procurement Plan Details"),
            title_list = T("Procurement Plans"),
            title_update = T("Edit Procurement Plan"),
            label_list_button = T("List Procurement Plans"),
            label_delete_button = T("Delete Procurement Plan"),
            msg_record_created = T("Procurement Plan added"),
            msg_record_modified = T("Procurement Plan updated"),
            msg_record_deleted = T("Procurement Plan deleted"),
            msg_list_empty = T("No Procurement Plans currently registered"))

        # ---------------------------------------------------------------------
        # Redirect to the Items tabs after creation
        plan_item_url = URL(f="plan", args=["[id]", "plan_item"])
        configure(tablename,
                  # @ToDo: Move these to controller r.interactive?
                  create_next = plan_item_url,
                  update_next = plan_item_url,
                  )

        proc_plan_represent = self.proc_plan_represent
        plan_id = S3ReusableField("plan_id", "reference %s" % tablename,
                                  sortby = "date",
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "proc_plan.id",
                                                          proc_plan_represent,
                                                          orderby="proc_plan.date",
                                                          sort=True)),
                                  represent = proc_plan_represent,
                                  label = T("Procurement Plan"),
                                  ondelete = "CASCADE",
                                  )

        # Items as a component of Plans
        self.add_components(tablename,
                            proc_plan_item = "plan_id",
                            )

        # =====================================================================
        # Procurement Plan Items
        #
        tablename = "proc_plan_item"
        define_table(tablename,
                     plan_id(),
                     self.supply_item_entity_id(),
                     self.supply_item_id(),
                     self.supply_item_pack_id(),
                     Field("quantity", "double", notnull = True,
                           label = T("Quantity"),
                           ),
                     # @ToDo: Move this into a Currency Widget
                     #        for the pack_value field
                     s3_currency(readable=False,
                                 writable=False
                                 ),
                     Field("pack_value", "double",
                           label = T("Value per Pack"),
                           readable = False,
                           writable = False,
                           ),
                     #Field("pack_quantity",
                     #      "double",
                     #      compute = record_pack_quantity), # defined in supply
                     #Field.Method("pack_quantity",
                     #             SupplyItemPackQuantity(tablename)),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Item to Procurement Plan"),
            title_display = T("Procurement Plan Item Details"),
            title_list = T("Items in Procurement Plan"),
            title_update = T("Edit Procurement Plan Item"),
            label_list_button = T("List Items in Procurement Plan"),
            label_delete_button = T("Remove Item from Procurement Plan"),
            msg_record_created = T("Item added to Procurement Plan"),
            msg_record_modified = T("Procurement Plan Item updated"),
            msg_record_deleted = T("Item removed from Procurement Plan"),
            msg_list_empty = T("No Items currently registered in this Procurement Plan"))

        # ---------------------------------------------------------------------
        # Item Search Method
        #
        filter_widgets = [
            S3TextFilter(["item_id$name",
                          #"item_id$category_id$name",
                          #"plan_id$site_id$name"
                         ],
                         label = T("Search"),
                         comment = T("Search for an item by text."),
                         ),
            S3OptionsFilter("plan_id$organisation_id$name",
                            label = T("Supplier"),
                            comment = T("If none are selected, then all are searched."),
                            cols = 2,
                            hidden = True,
                            ),
            #S3OptionsFilter("plan_id$site_id",
            #                label = T("Facility"),
            #                represent = "%(name)s",
            #                comment = T("If none are selected, then all are searched."),
            #                cols = 2,
            #                hidden = True,
            #                ),
            #S3DateFilter("plan_id$order_date",
            #             label=T("Order Date"),
            #             hidden = True,
            #             ),
            #S3DateFilter("plan_id$eta",
            #             label = T("Date Expected"),
            #             hidden = True,
            #             ),
        ]

        configure(tablename,
                  super_entity = "supply_item_entity",
                  filter_widgets = filter_widgets,
                  #report_groupby = db.proc_plan.site_id,
                  report_hide_comments = True,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def proc_plan_represent(plan_id, row=None):
        """
            Represent a Procurement Plan
        """

        if row:
            table = current.db.proc_plan
        elif not plan_id:
            return current.messages["NONE"]
        else:
            db = current.db
            table = db.proc_plan
            row = db(table.id == plan_id).select(table.site_id,
                                                 table.order_date,
                                                 limitby = (0, 1),
                                                 ).first()
        try:
            return "%s (%s)" % (table.site_id.represent(row.site_id),
                                table.order_date.represent(row.order_date))
        except AttributeError:
            # Plan not found
            return current.messages.UNKNOWN_OPT

# =============================================================================
class PurchaseOrdersModel(S3Model):
    """
        Purchase Orders (PO)

        @ToDo: Link to inv_send
        @ToDo: Link to inv_req
    """

    names = ("proc_order",
             "proc_order_item"
             "proc_order_tag"
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        #messages = current.messages
        configure = self.configure
        settings = current.deployment_settings

        SITE_LABEL = settings.get_org_site_label()
        string_represent = lambda s: s if s else current.messages["NONE"]
        purchase_ref = S3ReusableField("purchase_ref",
                                       label = T("%(PO)s Number") % \
                                               {"PO": settings.get_proc_shortname()},
                                       represent = string_represent,
                                       )

        # =====================================================================
        # Purchase Orders
        #

        tablename = "proc_order"
        define_table(tablename,
                     purchase_ref(),
                     self.super_link("site_id", "org_site",
                                     label = SITE_LABEL,
                                     default = auth.user.site_id if auth.is_logged_in() else None,
                                     readable = True,
                                     writable = True,
                                     #empty = False,
                                     # Comment these to use a Dropdown & not an Autocomplete
                                     #widget = S3SiteAutocompleteWidget(),
                                     #comment = DIV(_class="tooltip",
                                     #              _title="%s|%s" % (T("Inventory"),
                                     #                                messages.AUTOCOMPLETE_HELP)),
                                     represent = self.org_site_represent,
                                     ),
                     s3_date(default = "now"),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Purchase Order"),
            title_display = T("Purchase Order Details"),
            title_list = T("Purchase Orders"),
            title_update = T("Edit Purchase Order"),
            label_list_button = T("List Purchase Orders"),
            label_delete_button = T("Delete Purchase Order"),
            msg_record_created = T("Purchase Order added"),
            msg_record_modified = T("Purchase Order updated"),
            msg_record_deleted = T("Purchase Order deleted"),
            msg_list_empty = T("No Purchase Orders currently registered"))

        # ---------------------------------------------------------------------
        # Redirect to the Items tabs after creation
        order_item_url = URL(f="order", args=["[id]", "order_item"])
        configure(tablename,
                  create_onaccept = self.proc_order_onaccept,
                  # @ToDo: Move these to controller r.interactive?
                  create_next = order_item_url,
                  update_next = order_item_url,
                  )

        proc_order_represent = S3Represent(lookup = tablename,
                                           fields = ["purchase_ref"],
                                           )
        order_id = S3ReusableField("order_id", "reference %s" % tablename,
                                   sortby = "date",
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "proc_order.id",
                                                          proc_order_represent,
                                                          orderby="proc_order.date",
                                                          sort=True)),
                                   represent = proc_order_represent,
                                   label = T("Purchase Order"),
                                   ondelete = "CASCADE",
                                   )

        # Items as a component of Plans
        self.add_components(tablename,
                            proc_order_item = "order_id",
                            proc_order_tag = {"name": "tag",
                                              "joinby": "order_id",
                                              },
                            )

        # =====================================================================
        # Purchase Order Items
        #
        tablename = "proc_order_item"
        define_table(tablename,
                     order_id(),
                     self.supply_item_entity_id(),
                     self.supply_item_id(),
                     self.supply_item_pack_id(),
                     Field("quantity", "double", notnull = True,
                           label = T("Quantity"),
                           ),
                     # @ToDo: Move this into a Currency Widget
                     #        for the pack_value field
                     s3_currency(readable=False,
                                 writable=False
                                ),
                     Field("pack_value", "double",
                           label = T("Value per Pack"),
                           readable = False,
                           writable = False,
                           ),
                     #Field.Method("pack_quantity",
                     #             SupplyItemPackQuantity(tablename)),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Item to Purchase Order"),
            title_display = T("Purchase Order Item Details"),
            title_list = T("Items in Purchase Order"),
            title_update = T("Edit Purchase Order Item"),
            label_list_button = T("List Items in Purchase Order"),
            label_delete_button = T("Remove Item from Purchase Order"),
            msg_record_created = T("Item added to Purchase Order"),
            msg_record_modified = T("Purchase Order Item updated"),
            msg_record_deleted = T("Item removed from Purchase Order"),
            msg_list_empty = T("No Items currently registered in this Purchase Order"))

        # ---------------------------------------------------------------------
        # Item Search Method
        #
        filter_widgets = [
            S3TextFilter(["item_id$name",
                          #"item_id$category_id$name",
                          #"order_id$site_id$name"
                          ],
                         label = T("Search"),
                         comment = T("Search for an item by text."),
                         ),
            S3OptionsFilter("order_id$organisation_id$name",
                            label = T("Supplier"),
                            comment = T("If none are selected, then all are searched."),
                            cols = 2,
                            hidden = True,
                            ),
            #S3OptionsFilter("order_id$site_id",
            #                label = T("Facility"),
            #                represent ="%(name)s",
            #                comment = T("If none are selected, then all are searched."),
            #                cols = 2,
            #                hidden = True,
            #                ),
            #S3DateFilter("order_id$order_date",
            #             label = T("Order Date"),
            #             hidden = True,
            #             ),
        ]

        configure(tablename,
                  super_entity = "supply_item_entity",
                  filter_widgets = filter_widgets,
                  #report_groupby = db.proc_order.site_id,
                  report_hide_comments = True,
                  )

        # ---------------------------------------------------------------------
        # Purchase Order Tags
        # - Key-Value extensions
        # - can be used to provide conversions to external systems
        # - can be a Triple Store for Semantic Web support
        #
        tablename = "proc_order_tag"
        define_table(tablename,
                     order_id(),
                     # key is a reserved word in MySQL
                     Field("tag",
                           label = T("Key"),
                           ),
                     Field("value",
                           label = T("Value"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("order_id",
                                                       "tag",
                                                       ),
                                            ),
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"proc_order_id": order_id,
                }

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        return {"proc_order_id": S3ReusableField.dummy("order_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def proc_order_onaccept(form):
        """
           When a proc_order record is created then create the purchase_ref.
        """

        db = current.db
        table = db.proc_order
        # If the purchase_ref is None then set it up
        record_id = form.vars.id
        record = table[record_id]
        if not record.purchase_ref:
            # PO Number
            code = current.s3db.supply_get_shipping_code(
                    current.deployment_settings.get_proc_shortname(),
                    record.site_id,
                    table.purchase_ref,
                    )
            db(table.id == record_id).update(purchase_ref = code)

# =============================================================================
def proc_rheader(r):
    """ Resource Header for Procurements """

    rheader = None

    if r.representation == "html":
        record = r.record
        if record:
            tablename = r.tablename
            if tablename == "proc_order":
                T = current.T

                tabs = [(T("Edit Details"), None),
                        (T("Items"), "order_item"),
                        ]
                rheader_tabs = s3_rheader_tabs(r, tabs)

                table = r.table

                rheader = DIV(TABLE(TR(TH("%s: " % table.purchase_ref.label),
                                       record.purchase_ref,
                                       ),
                                    TR(TH("%s: " % table.site_id.label),
                                       table.site_id.represent(record.site_id),
                                       ),
                                    TR(TH("%s: " % table.date.label),
                                       table.date.represent(record.date),
                                       ),
                                    ),
                              rheader_tabs
                              )

            elif tablename == "proc_plan":
                T = current.T

                tabs = [(T("Edit Details"), None),
                        (T("Items"), "plan_item"),
                        ]
                rheader_tabs = s3_rheader_tabs(r, tabs)

                table = r.table

                rheader = DIV(TABLE(TR(TH("%s: " % table.site_id.label),
                                       table.site_id.represent(record.site_id),
                                       ),
                                    TR(TH("%s: " % table.order_date.label),
                                       table.order_date.represent(record.order_date),
                                       ),
                                    TR(TH("%s: " % table.eta.label),
                                       table.eta.represent(record.eta),
                                       ),
                                    TR(TH("%s: " % table.shipping.label),
                                       table.shipping.represent(record.shipping),
                                       ),
                                    ),
                              rheader_tabs
                              )
    return rheader

# END =========================================================================
