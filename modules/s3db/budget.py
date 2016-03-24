# -*- coding: utf-8 -*-

""" Sahana Eden Budget Model

    @copyright: 2009-2016 (c) Sahana Software Foundation
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
from reportlab.lib.validators import Percentage

__all__ = ("S3BudgetModel",
           "S3BudgetKitModel",
           "S3BudgetBundleModel",
           "S3BudgetAllocationModel",
           "S3BudgetMonitoringModel",
           "budget_rheader",
           "budget_CostItemRepresent",
           )

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3dal import Row
from s3layouts import S3PopupLink

# =============================================================================
class S3BudgetModel(S3Model):

    names = ("budget_entity",
             "budget_budget",
             "budget_parameter",
             "budget_location",
             #"budget_budget_id",
             "budget_location_id",
             "budget_staff",
             "budget_staff_id",
             "budget_budget_staff",
             )

    def model(self):

        T = current.T
        db = current.db
        configure = self.configure
        define_table = self.define_table
        super_link = self.super_link
        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        # ---------------------------------------------------------------------
        # Budget Entity (super-entity for resources that can have a budget)
        entity_types = Storage(#event_incident = T("Incident"),
                               #org_organisation = T("Organization"),
                               #org_site = T("Facility"),
                               #pr_group = T("Team"),
                               project_project = T("Project"),
                               )

        tablename = "budget_entity"
        self.super_entity(tablename, "budget_entity_id", entity_types)

        self.add_components(tablename,
                            # Budget Details
                            budget_budget = "budget_entity_id",
                            # Allocations
                            budget_allocation = "budget_entity_id",
                            # Monitoring
                            budget_monitoring = "budget_entity_id",
                            # Staff
                            budget_staff = {"link": "budget_budget_staff",
                                            "joinby": "budget_entity_id",
                                            "key": "staff_id",
                                            "actuate": "link",
                                            },
                            # Bundles
                            budget_bundle = {"link": "budget_budget_bundle",
                                             "joinby": "budget_entity_id",
                                             "key": "bundle_id",
                                             "actuate": "link",
                                             },
                            )

        # ---------------------------------------------------------------------
        # Budgets
        #
        status_opts = {1: T("Draft"),
                       2: T("Approved"),
                       3: T("Rejected"),
                       }

        # Currently only Monthly is supported
        monitoring_opts = {1: messages["NONE"],
                           #2: T("Annually"),
                           3: T("Monthly"),
                           #3: T("Weekly"),
                           #3: T("Daily"),
                           }

        tablename = "budget_budget"
        define_table(tablename,
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("budget_entity_id", "budget_entity"),
                     Field("name", length=128, notnull=True, unique=True,
                           label = T("Name"),
                           #requires = [IS_NOT_EMPTY(),
                           #            IS_NOT_ONE_OF(db, "%s.name" % tablename),
                           #            ],
                           ),
                     Field("description",
                           label = T("Description"),
                           ),
                     Field("total_onetime_costs", "double",
                           default = 0.0,
                           label = T("Total One-time Costs"),
                           writable = False,
                           ),
                     Field("total_recurring_costs", "double",
                           default = 0.0,
                           label = T("Total Recurring Costs"),
                           writable = False,
                           ),
                     Field("total_budget", "double",
                           default = 0.0,
                           label = T("Total Budget"),
                           ),
                     s3_currency(required = True),
                     Field("monitoring_frequency", "integer",
                           default = 1,
                           label = T("Monitoring Frequency"),
                           represent = lambda opt: \
                            monitoring_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(monitoring_opts),
                           ),
                     Field("status", "integer",
                           default = 1,
                           represent = lambda opt: \
                            status_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(status_opts),
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        #ADD_BUDGET = T("Create Budget")
        crud_strings[tablename] = Storage(
            #label_create = ADD_BUDGET,
            label_create = T("Create Budget"),
            title_display = T("Budget Details"),
            title_list = T("Budgets"),
            title_update = T("Edit Budget"),
            label_list_button = T("List Budgets"),
            label_delete_button = T("Delete Budget"),
            msg_record_created = T("Budget added"),
            msg_record_modified = T("Budget updated"),
            msg_record_deleted = T("Budget deleted"),
            msg_list_empty = T("No Budgets currently registered"),
        )

        # Represent
        #budget_budget_represent = S3Represent(lookup=tablename, show_link=True)

        # Reusable Field
        #budget_budget_id = S3ReusableField("budget_id", "reference %s" % tablename,
        #    label = T("Budget"),
        #    ondelete = "CASCADE",
        #    represent = budget_budget_represent,
        #    requires = IS_ONE_OF(db, "budget_budget.id",
        #                         budget_budget_represent,
        #                         ),
        #    comment = S3PopupLink(
        #        c = "budget",
        #        f = "budget",
        #        label = ADD_BUDGET,
        #        title = T("Budget"),
        #        tooltip = T("You can create a new budget by clicking link '%s'.") % ADD_BUDGET
        #        ),
        #    )

        # Configuration
        configure(tablename,
                  onaccept = self.budget_budget_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Parameters (currently unused)
        #
        # @todo: take into account when calculating totals
        #
        tablename = "budget_parameter"
        define_table(tablename,
                     Field("shipping", "double", notnull=True,
                           default = 15.0,
                           label = T("Shipping cost"),
                           requires = IS_FLOAT_IN_RANGE(0, 100),
                           ),
                     Field("logistics", "double", notnull=True,
                           default = 0.0,
                           label = T("Procurement & Logistics cost"),
                           requires = IS_FLOAT_IN_RANGE(0, 100),
                           ),
                     Field("admin", "double", notnull=True,
                           default = 0.0,
                           label = T("Administrative support cost"),
                           requires = IS_FLOAT_IN_RANGE(0, 100),
                           ),
                     Field("indirect", "double", notnull=True,
                           default = 7.0,
                           label = T("Indirect support cost HQ"),
                           requires = IS_FLOAT_IN_RANGE(0, 100),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_update = T("Edit Parameters"),
            title_display = T("Parameters")
        )

        # ---------------------------------------------------------------------
        # Locations
        #
        tablename = "budget_location"
        define_table(tablename,
                     Field("code", length=3, notnull=True, unique=True,
                           label = T("Code"),
                           #requires = [IS_NOT_EMPTY(),
                           #            IS_NOT_ONE_OF(db, "%s.code" % tablename),
                           #            ],
                           ),
                     Field("description",
                           label = T("Description"),
                           ),
                     Field("subsistence", "double",
                           default = 0.0,
                           label = T("Subsistence Cost"),
                           # UN terminology:
                           #label = "DSA",
                           ),
                     Field("hazard_pay", "double",
                           default = 0.0,
                           label = T("Hazard Pay"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_LOCATION = T("Create Location")
        crud_strings[tablename] = Storage(
            label_create = ADD_LOCATION,
            title_display = T("Location Details"),
            title_list = T("Locations"),
            title_update = T("Edit Location"),
            label_list_button = T("List Locations"),
            label_delete_button = T("Delete Location"),
            msg_record_created = T("Location added"),
            msg_record_modified = T("Location updated"),
            msg_record_deleted = T("Location deleted"),
            msg_list_empty = T("No Locations currently registered"),
        )

        # Represent
        budget_location_represent = S3Represent(lookup=tablename,
                                                fields=["code"])

        # Reusable Field
        budget_location_id = S3ReusableField("location_id", "reference %s" % tablename,
            label = T("Location"),
            ondelete = "CASCADE",
            represent = budget_location_represent,
            requires = IS_ONE_OF(db, "budget_location.id",
                                 budget_location_represent,
                                 ),
            comment = S3PopupLink(
                c = "budget",
                f = "location",
                label = ADD_LOCATION,
                title = T("Location"),
                tooltip = T("You can create a new location by clicking link '%s'.") % ADD_LOCATION
                ),
            )

        # Configuration
        configure(tablename,
                  update_onaccept = self.budget_location_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Staff Types
        #
        tablename = "budget_staff"
        define_table(tablename,
                     Field("name", length=128, notnull=True, unique=True,
                           label = T("Name"),
                           #requires = [IS_NOT_EMPTY(),
                           #            IS_NOT_ONE_OF(db, "%s.name" % tablename),
                           #            ],
                           ),
                     Field("grade", notnull=True,
                           label = T("Grade"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("salary", "integer", notnull=True,
                           label = T("Monthly Salary"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_currency(),
                     Field("travel", "integer",
                           default = 0,
                           label = T("Travel Cost"),
                           ),
                     # Shouldn't be grade-dependent, but purely
                     # location-dependent
                     #Field("subsistence", "double",
                     #      default=0.00,
                     #     ),
                     # Location-dependent
                     #Field("hazard_pay", "double",
                     #      default=0.00,
                     #     ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_STAFF_TYPE = T("Create Staff Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_STAFF_TYPE,
            title_display = T("Staff Type Details"),
            title_list = T("Staff Types"),
            title_update = T("Edit Staff Type"),
            label_list_button = T("List Staff Types"),
            label_delete_button = T("Delete Staff Type"),
            msg_record_created = T("Staff Type added"),
            msg_record_modified = T("Staff Type updated"),
            msg_record_deleted = T("Staff Type deleted"),
            msg_list_empty = T("No Staff Types currently registered"),
        )

        # Represent
        budget_staff_represent = S3Represent(lookup=tablename,
                                             fields=["name"])

        # Reusable Field
        budget_staff_id = S3ReusableField("staff_id", "reference %s" % tablename,
            label = T("Staff"),
            ondelete = "RESTRICT",
            represent = budget_staff_represent,
            requires = IS_ONE_OF(db, "budget_staff.id",
                                 budget_staff_represent,
                                 ),
            comment = S3PopupLink(
                c = "budget",
                f = "staff",
                label = ADD_STAFF_TYPE,
                title = T("Staff"),
                tooltip = T("You can create new staff by clicking link '%s'.") % ADD_STAFF_TYPE
                ),
            )

        # Configuration
        configure(tablename,
                  update_onaccept = self.budget_staff_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Budget<>Staff Many2Many
        #
        tablename = "budget_budget_staff"
        define_table(tablename,
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("budget_entity_id", "budget_entity"),
                     budget_location_id(),
                     budget_staff_id(),
                     Field("quantity", "integer", notnull=True,
                           default = 1,
                           label = T("Quantity"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("months", "integer", notnull=True,
                           default = 3,
                           label = T("Months"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     *s3_meta_fields())

        # Configuration
        configure(tablename,
                  onaccept = self.budget_budget_staff_onaccept,
                  ondelete = self.budget_budget_staff_ondelete,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(#budget_budget_id = budget_budget_id,
                    budget_location_id = budget_location_id,
                    budget_staff_id=budget_staff_id,
                    )

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(budget_budget_id = lambda **attr: dummy("budget_id"),
                    budget_location_id = lambda **attr: dummy("location_id"),
                    budget_staff_id = lambda **attr: dummy("staff_id"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_budget_onaccept(form):
        """
            Calculate totals for the budget
        """

        try:
           budget_entity_id = form.vars.budget_entity_id
        except:
           return
        budget_budget_totals(budget_entity_id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_staff_onaccept(form):
        """
            Staff type has been updated => update totals of all budgets with
            this staff type
        """

        try:
            record_id = form.vars.id
        except:
            return
        linktable = current.s3db.budget_budget_staff
        budget_entity_id = linktable.budget_entity_id
        query = (linktable.staff_id == record_id)
        rows = current.db(query).select(budget_entity_id,
                                        groupby=budget_entity_id)
        for row in rows:
            budget_budget_totals(row.budget_entity_id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_location_onaccept(form):
        """
            Location has been updated => update totals of all budgets with
            staff at this location
        """

        try:
            record_id = form.vars.id
        except:
            return
        linktable = current.s3db.budget_budget_staff
        budget_entity_id = linktable.budget_entity_id
        query = (linktable.location_id == record_id)
        rows = current.db(query).select(budget_entity_id,
                                        groupby=budget_entity_id)
        for row in rows:
            budget_budget_totals(row.budget_entity_id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_budget_staff_onaccept(form):
        """
            Budget staff has been updated => update totals of the budget
        """

        try:
            record_id = form.vars.id
        except:
            return
        table = current.s3db.budget_budget_staff
        row = current.db(table.id == record_id).select(table.budget_entity_id,
                                                       limitby=(0, 1)).first()
        if row:
            budget_budget_totals(row.budget_entity_id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_budget_staff_ondelete(row):
        """
            Budget staff has been deleted => update totals of the budget
        """

        db = current.db
        linktable = current.s3db.budget_budget_staff
        try:
            record_id = row.id
        except:
            return
        link = db(linktable.id == record_id).select(linktable.deleted_fk,
                                                    limitby=(0, 1)).first()
        if link:
            deleted_fk = json.loads(link.deleted_fk)
            budget_entity_id = deleted_fk.get("budget_entity_id")
            if budget_entity_id:
                budget_budget_totals(budget_entity_id)
        return

# =============================================================================
class S3BudgetKitModel(S3Model):

    names = ("budget_kit",
             "budget_item",
             "budget_kit_item",
             "budget_kit_id",
             "budget_item_id",
             )

    def model(self):

        T = current.T
        configure = self.configure
        define_table = self.define_table
        add_components = self.add_components

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        db = current.db

        # ---------------------------------------------------------------------
        # Kits
        #
        tablename = "budget_kit"
        define_table(tablename,
                     Field("code", length=128, notnull=True, unique=True,
                           label = T("Code"),
                           #requires = [IS_NOT_EMPTY(),
                           #            IS_NOT_ONE_OF(db, "%s.code" % tablename),
                           #            ],
                           ),
                     Field("description",
                           label = T("Description"),
                           ),
                     Field("total_unit_cost", "double",
                           default = 0.0,
                           label = T("Total Unit Cost"),
                           writable = False,
                           ),
                     Field("total_monthly_cost", "double",
                           default = 0.0,
                           label = T("Total Monthly Cost"),
                           writable = False,
                           ),
                     Field("total_minute_cost", "double",
                           default = 0.0,
                           label = T("Total Cost per Minute"),
                           writable = False,
                           ),
                     Field("total_megabyte_cost", "double",
                           default = 0.0,
                           label = T("Total Cost per Megabyte"),
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_KIT = T("Create Kit")
        crud_strings[tablename] = Storage(
            label_create = ADD_KIT,
            title_display = T("Kit Details"),
            title_list = T("Kits"),
            title_update = T("Edit Kit"),
            label_list_button = T("List Kits"),
            label_delete_button = T("Delete Kit"),
            msg_record_created = T("Kit added"),
            msg_record_modified = T("Kit updated"),
            msg_record_deleted = T("Kit deleted"),
            msg_list_empty = T("No Kits currently registered"),
        )

        # Represent
        budget_kit_represent = S3Represent(lookup=tablename, fields=["code"])

        # Reusable Field
        budget_kit_id = S3ReusableField("kit_id", "reference %s" % tablename,
            ondelete = "RESTRICT",
            label = T("Kit"),
            represent = budget_kit_represent,
            requires = IS_ONE_OF(db, "budget_kit.id",
                                 budget_kit_represent,
                                 ),
            comment = S3PopupLink(
                c = "budget",
                f = "kit",
                label = ADD_KIT,
                title = T("Kit"),
                tooltip = T("You can create a new kit by clicking link '%s'.") % ADD_KIT
                ),
            )

        # Configuration
        configure(tablename,
                  onaccept = self.budget_kit_onaccept,
                  )

        # Components
        add_components(tablename,
                       # Items
                       budget_item = {"link": "budget_kit_item",
                                      "joinby": "kit_id",
                                      "key": "item_id",
                                      "actuate": "link",
                                      },
                       )

        # ---------------------------------------------------------------------
        # Items
        #
        budget_cost_type_opts = {1: T("One-time"),
                                 2: T("Recurring"),
                                }

        budget_category_type_opts = {1: T("Consumable"),
                                     2: T("Satellite"),
                                     3: "HF",
                                     4: "VHF",
                                     5: T("Telephony"),
                                     6: "WLAN",
                                     7: T("Network"),
                                     8: T("Generator"),
                                     9: T("Electrical"),
                                     10: T("Vehicle"),
                                     11: "GPS",
                                     12: T("Tools"),
                                     13: "IT",
                                     14: "ICT",
                                     15: "TC",
                                     16: T("Stationery"),
                                     17: T("Relief"),
                                     18: T("Miscellaneous"),
                                     19: T("Running Cost"),
                                     }

        tablename = "budget_item"
        define_table(tablename,
                     Field("category_type", "integer", notnull=True,
                           #default = 1,
                           label = T("Category"),
                           represent = lambda opt: \
                                       budget_category_type_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(budget_category_type_opts, zero=None),
                           ),
                     Field("code", length=128, notnull=True, unique=True,
                           label = T("Code"),
                           #requires = [IS_NOT_EMPTY(),
                           #            IS_NOT_ONE_OF(db, "%s.code" % tablename),
                           #            ],
                           ),
                     Field("description", notnull=True,
                           label = T("Description"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("cost_type", "integer", notnull=True,
                           #default = 1,
                           label = T("Cost Type"),
                           represent = lambda opt: \
                                       budget_cost_type_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(budget_cost_type_opts,
                                                zero=None),
                           ),
                     Field("unit_cost", "double",
                           default = 0.00,
                           label = T("Unit Cost"),
                           ),
                     Field("monthly_cost", "double",
                           default = 0.00,
                           label = T("Monthly Cost"),
                           ),
                     Field("minute_cost", "double",
                           default = 0.00,
                           label = T("Cost per Minute"),
                           ),
                     Field("megabyte_cost", "double",
                           default = 0.00,
                           label = T("Cost per Megabyte"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_ITEM = T("Create Item")
        crud_strings[tablename] = Storage(
            label_create = ADD_ITEM,
            title_display = T("Item Details"),
            title_list = T("Items"),
            title_update = T("Edit Item"),
            label_list_button = T("List Items"),
            label_delete_button = T("Delete Item"),
            label_search_button = T("Search Items"),
            msg_record_created = T("Item added"),
            msg_record_modified = T("Item updated"),
            msg_record_deleted = T("Item deleted"),
            msg_list_empty = T("No Items currently registered"),
        )

        # Represent
        budget_item_represent = S3Represent(lookup=tablename,
                                            fields=["description"])

        # Reusable Field
        budget_item_id = S3ReusableField("item_id", "reference %s" % tablename,
            label = T("Item"),
            ondelete = "RESTRICT",
            represent = budget_item_represent,
            requires = IS_ONE_OF(db, "budget_item.id",
                                 budget_item_represent,
                                 ),
            comment = S3PopupLink(
                c = "budget",
                f = "item",
                label = ADD_ITEM,
                title = T("Item"),
                tooltip = T("You can create a new item by clicking link '%s'.") % ADD_ITEM
                ),
            )

        # Configuration
        configure(tablename,
                  main = "code",
                  extra = "description",
                  onaccept = self.budget_item_onaccept,
                  orderby = "budget_item.category_type",
                  )

        # ---------------------------------------------------------------------
        # Kit<>Item Many2Many
        #
        tablename = "budget_kit_item"
        define_table(tablename,
                     budget_kit_id(),
                     budget_item_id(),
                     Field("quantity", "integer", notnull=True,
                           default = 1,
                           label = T("Quantity"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = self.budget_kit_item_onaccept,
                  ondelete = self.budget_kit_item_ondelete,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(budget_kit_id = budget_kit_id,
                    budget_item_id = budget_item_id,
                    )

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(budget_kit_id = lambda **attr: dummy("kit_id"),
                    budget_item_id = lambda **attr: dummy("item_id"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_kit_onaccept(form):
        """
            Calculate totals for the kit
        """
        try:
            kit_id = form.vars.id
        except:
            return
        budget_kit_totals(kit_id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_item_onaccept(form):
        """
            Calculate totals for all kits and bundles with this item
        """
        db = current.db
        s3db = current.s3db

        try:
            item_id = form.vars.id
        except:
            return

        # Update totals of all kits with this item
        linktable = s3db.budget_kit_item
        kit_id = linktable.kit_id
        rows = db(linktable.item_id == item_id).select(kit_id,
                                                       groupby=kit_id)
        kit_ids = set()
        for row in rows:
            kit_id = row.kit_id
            budget_kit_totals(kit_id)
            kit_ids.add(kit_id)

        # Find all bundles which have just been updated by budget_kit_totals
        if kit_ids:
            linktable = s3db.budget_bundle_kit
            bundle_id = linktable.bundle_id
            rows = db(linktable.kit_id.belongs(kit_ids)).select(bundle_id,
                                                                groupby=bundle_id)
            already_updated = [row.bundle_id for row in rows]
        else:
            already_updated = None

        # Update totals of all remaining bundles with this item
        linktable = s3db.budget_bundle_item
        bundle_id = linktable.bundle_id
        query = (linktable.item_id == item_id)
        if already_updated:
            query &= ~(linktable.bundle_id.belongs(already_updated))
        rows = db(query).select(bundle_id, groupby=bundle_id)
        for row in rows:
            budget_bundle_totals(kit_id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_kit_item_onaccept(form):
        """
            Kit item has been updated => update totals of the kit
        """

        try:
            record_id = form.vars.id
        except:
            return
        table = current.s3db.budget_kit_item
        row = current.db(table.id == record_id).select(table.kit_id,
                                                       limitby=(0, 1)).first()
        if row:
            budget_kit_totals(row.kit_id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_kit_item_ondelete(row):
        """
            Kit item has been deleted => update totals of the kit
        """

        db = current.db
        linktable = current.s3db.budget_kit_item
        try:
            record_id = row.id
        except:
            return
        link = db(linktable.id == record_id).select(linktable.deleted_fk,
                                                    limitby=(0, 1)).first()
        if link:
            deleted_fk = json.loads(link.deleted_fk)
            kit_id = deleted_fk.get("kit_id")
            if kit_id:
                budget_kit_totals(kit_id)
        return

# =============================================================================
class S3BudgetBundleModel(S3Model):
    """ Model for Budget Bundles """

    names = ("budget_bundle",
             "budget_bundle_kit",
             "budget_bundle_item",
             "budget_budget_bundle",
             "budget_bundle_id",
             )

    def model(self):

        T = current.T
        configure = self.configure
        define_table = self.define_table
        add_components = self.add_components

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        db = current.db

        # ---------------------------------------------------------------------
        # Bundles
        #
        tablename = "budget_bundle"
        define_table(tablename,
                     Field("name", length=128, notnull=True, unique=True,
                           label = T("Name"),
                           #requires = [IS_NOT_EMPTY(),
                           #            IS_NOT_ONE_OF(db, "%s.name" % tablename),
                           #            ],
                           ),
                     Field("description",
                           label = T("Description"),
                           ),
                     Field("total_unit_cost", "double",
                           default = 0.0,
                           label = T("One time cost"),
                           writable = False,
                           ),
                     Field("total_monthly_cost", "double",
                           default = 0.0,
                           label = T("Recurring cost"),
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_BUNDLE = T("Create Bundle")
        crud_strings[tablename] = Storage(
            label_create = ADD_BUNDLE,
            title_display = T("Bundle Details"),
            title_list = T("Bundles"),
            title_update = T("Edit Bundle"),
            label_list_button = T("List Bundles"),
            label_delete_button = T("Delete Bundle"),
            msg_record_created = T("Bundle added"),
            msg_record_modified = T("Bundle updated"),
            msg_record_deleted = T("Bundle deleted"),
            msg_list_empty = T("No Bundles currently registered"),
        )

        # Configuration
        configure(tablename,
                  onaccept = self.budget_bundle_onaccept,
                  )

        # Components
        add_components(tablename,
                       # Items
                       budget_item = {"link": "budget_bundle_item",
                                      "joinby": "bundle_id",
                                      "key": "item_id",
                                      "actuate": "link",
                                      },
                       # Kits
                       budget_kit = {"link": "budget_bundle_kit",
                                     "joinby": "bundle_id",
                                     "key": "kit_id",
                                     "actuate": "link",
                                     },
                       )

        # Represent
        budget_bundle_represent = S3Represent(lookup=tablename,
                                             fields=["name"])

        # Reusable Field
        budget_bundle_id = S3ReusableField("bundle_id", "reference %s" % tablename,
            label = T("Bundle"),
            ondelete = "RESTRICT",
            represent = budget_bundle_represent,
            requires = IS_ONE_OF(db, "budget_bundle.id",
                                 budget_bundle_represent,
                                 ),
            comment = S3PopupLink(
                c = "budget",
                f = "bundle",
                label = ADD_BUNDLE,
                title = T("Bundle"),
                tooltip = T("You can create a new bundle by clicking link '%s'.") % ADD_BUNDLE
                ),
            )

        # ---------------------------------------------------------------------
        # Bundle<>Kit Many2Many
        #
        tablename = "budget_bundle_kit"
        define_table(tablename,
                     budget_bundle_id(),
                     self.budget_kit_id(),
                     Field("quantity", "integer", notnull=True,
                           default = 1,
                           label = T("Quantity"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("minutes", "integer", notnull=True,
                           default = 0,
                           label = T("Minutes per Month"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("megabytes", "integer", notnull=True,
                           default = 0,
                           label = T("Megabytes per Month"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Kit"),
            title_display = T("Kit Details"),
            title_list = T("Kits"),
            title_update = T("Edit Kit"),
            label_list_button = T("List Kits"),
            label_delete_button = T("Remove Kit"),
            msg_record_created = T("Kit added"),
            msg_record_modified = T("Kit updated"),
            msg_record_deleted = T("Kit removed"),
            msg_list_empty = T("No Kits currently registered in this bundle"),
        )

        # Configuration
        configure(tablename,
                  onaccept = self.budget_bundle_kit_onaccept,
                  ondelete = self.budget_bundle_kit_ondelete,
                  )

        # ---------------------------------------------------------------------
        # Bundle<>Item Many2Many
        #
        tablename = "budget_bundle_item"
        define_table(tablename,
                     budget_bundle_id(),
                     self.budget_item_id(),
                     Field("quantity", "integer", notnull=True,
                           default = 1,
                           requires = IS_NOT_EMPTY(),
                           label = T("Quantity"),
                           ),
                     Field("minutes", "integer", notnull=True,
                           default = 0,
                           requires = IS_NOT_EMPTY(),
                           label = T("Minutes per Month"),
                           ),
                     Field("megabytes", "integer", notnull=True,
                           default = 0,
                           requires = IS_NOT_EMPTY(),
                           label = T("Megabytes per Month"),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Item"),
            title_display = T("Item Details"),
            title_list = T("Items"),
            title_update = T("Edit Item"),
            label_list_button = T("List Items"),
            label_delete_button = T("Remove Item"),
            msg_record_created = T("Item added"),
            msg_record_modified = T("Item updated"),
            msg_record_deleted = T("Item removed"),
            msg_list_empty = T("No Items currently registered in this bundle"),
        )

        # Configuration
        configure(tablename,
                  onaccept = self.budget_bundle_item_onaccept,
                  ondelete = self.budget_bundle_item_ondelete,
                  )

        # ---------------------------------------------------------------------
        # Budget<>Bundle Many2Many
        #
        tablename = "budget_budget_bundle"
        define_table(tablename,
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     self.super_link("budget_entity_id", "budget_entity"),
                     self.budget_location_id(),
                     budget_bundle_id(),
                     Field("quantity", "integer", notnull=True,
                           default = 1,
                           label = T("Quantity"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("months", "integer", notnull=True,
                           default = 3,
                           label = T("Months"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Bundle"),
            title_display = T("Bundle Details"),
            title_list = T("Budget Bundles"),
            title_update = T("Edit Bundle"),
            label_list_button = T("List Bundles"),
            label_delete_button = T("Remove Bundle"),
            msg_record_created = T("Bundle added"),
            msg_record_modified = T("Bundle updated"),
            msg_record_deleted = T("Bundle removed"),
            msg_list_empty = T("No Bundles currently registered in this Budget"),
        )

        # Configuration
        configure(tablename,
                  onaccept = self.budget_budget_bundle_onaccept,
                  ondelete = self.budget_budget_bundle_ondelete,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(budget_bundle_id = budget_bundle_id,
                    )

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(budget_bundle_id = lambda **attr: dummy("bundle_id"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_bundle_onaccept(form):
        """
            Calculate totals for the bundle
        """
        try:
            bundle_id = form.vars.id
        except:
            return
        budget_bundle_totals(bundle_id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_bundle_item_onaccept(form):
        """
            Bundle item has been updated => update totals of the bundle
        """

        try:
            record_id = form.vars.id
        except:
            return
        table = current.s3db.budget_bundle_item
        row = current.db(table.id == record_id).select(table.bundle_id,
                                                       limitby=(0, 1)).first()
        if row:
            budget_bundle_totals(row.bundle_id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_bundle_item_ondelete(row):
        """
            Bundle item has been deleted => update totals of the bundle
        """

        db = current.db
        linktable = current.s3db.budget_bundle_item
        try:
            record_id = row.id
        except:
            return
        link = db(linktable.id == record_id).select(linktable.deleted_fk,
                                                    limitby=(0, 1)).first()
        if link:
            deleted_fk = json.loads(link.deleted_fk)
            bundle_id = deleted_fk.get("bundle_id")
            if bundle_id:
                budget_bundle_totals(bundle_id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_bundle_kit_onaccept(form):
        """
            Bundle kit has been updated => update totals of the bundle
        """

        try:
            record_id = form.vars.id
        except:
            return
        table = current.s3db.budget_bundle_kit
        row = current.db(table.id == record_id).select(table.bundle_id,
                                                       limitby=(0, 1)).first()
        if row:
            budget_bundle_totals(row.bundle_id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_bundle_kit_ondelete(row):
        """
            Bundle kit has been deleted => update totals of the bundle
        """

        db = current.db
        linktable = current.s3db.budget_bundle_kit
        try:
            record_id = row.id
        except:
            return
        link = db(linktable.id == record_id).select(linktable.deleted_fk,
                                                    limitby=(0, 1)).first()
        if link:
            deleted_fk = json.loads(link.deleted_fk)
            bundle_id = deleted_fk.get("bundle_id")
            if bundle_id:
                budget_bundle_totals(bundle_id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_budget_bundle_onaccept(form):
        """
            Budget bundle has been updated => update totals of the budget
        """

        try:
            record_id = form.vars.id
        except:
            return
        table = current.s3db.budget_budget_bundle
        row = current.db(table.id == record_id).select(table.budget_entity_id,
                                                       limitby=(0, 1)).first()
        if row:
            budget_budget_totals(row.budget_entity_id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_budget_bundle_ondelete(row):
        """
            Budget bundle has been deleted => update totals of the budget
        """

        db = current.db
        linktable = current.s3db.budget_budget_bundle
        try:
            record_id = row.id
        except:
            return
        link = db(linktable.id == record_id).select(linktable.deleted_fk,
                                                    limitby=(0, 1)).first()
        if link:
            deleted_fk = json.loads(link.deleted_fk)
            budget_entity_id = deleted_fk.get("budget_entity_id")
            if budget_entity_id:
                budget_budget_totals(budget_entity_id)
        return

# =============================================================================
class S3BudgetAllocationModel(S3Model):
    """
        Model for Budget Allocation
   """

    names = ("budget_allocation",
             "budget_cost_item",
             )

    def model(self):

        T = current.T
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Budget allocatable (super-entity for resource assignments that
        # can be linked to a budget)
        entity_types = Storage(event_asset = T("Event Asset"),
                               event_human_resource = T("Event Human Resource"),
                               event_site = T("Event Facility"),
                               #project_asset = T("Project Asset"),
                               project_human_resource_project = T("Project Human Resource"),
                               #project_site = T("Project Facility"),
                               )

        tablename = "budget_cost_item"
        self.super_entity(tablename, "cost_item_id", entity_types)

        self.add_components(tablename,
                            budget_allocation = "cost_item_id",
                            )

        # @todo: implement S3Represent for cost_item_id

        # ---------------------------------------------------------------------
        # Budget allocation (links a resource assignment to a budget)
        #
        tablename = "budget_allocation"
        self.define_table(tablename,
                          # This is a component, so needs to be a super_link
                          # - can't override field name, ondelete or requires
                          super_link("budget_entity_id", "budget_entity"),
                          # Component not instance
                          super_link("cost_item_id", "budget_cost_item",
                                     readable = True,
                                     writable = True,
                                     represent = self.budget_CostItemRepresent(),
                                     ),
                          # @ToDo: s3_datetime
                          s3_date("start_date",
                                  label = T("Start Date")
                                  ),
                          s3_date("end_date",
                                  label = T("End Date"),
                                  start_field = "budget_allocation_start_date",
                                  default_interval = 12,
                                  ),
                          Field("unit_cost", "double",
                                default = 0.00,
                                label = T("One-Time Cost"),
                                ),
                          # @ToDo: make the Time Unit configurable
                          Field("daily_cost", "double",
                                default = 0.00,
                                label = T("Daily Cost"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = self.budget_allocation_duplicate,
                       timeplot_options = {
                            "defaults": {
                                "baseline": "budget_entity_id$total_budget",
                                "fact": "cumulate(unit_cost,daily_cost,days)",
                                "slots": "",
                                "start": "",
                                "end": "+1month",
                            },
                       },
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_allocation_duplicate(item):
        """
            Import item de-duplication

            @todo: additionally have an onaccept sanitizing overlapping
                   allocations? (may be too simple, though)
        """

        data = item.data
        budget_entity_id = data.get("budget_entity_id")
        cost_item_id = data.get("cost_item_id")

        if budget_entity_id and cost_item_id:
            table = item.table

            start_date = data.get("start_date")
            end_date = data.get("end_date")

            # Regard same budget_entity_id and cost_item_id, and with
            # start_date = None or same start_date as match
            query = (table.budget_entity_id == budget_entity_id) & \
                    (table.cost_item_id == cost_item_id) & \
                    ((table.start_date == None) | \
                     (table.start_date == start_date))
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

# =============================================================================
class S3BudgetMonitoringModel(S3Model):
    """
        Budget Monitoring Model

        Allow Monitoring spend on a Budget

        @ToDo: Allow this to be broken down by Activity Type (VNRC) or Theme
    """

    names = ("budget_monitoring",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Monitoring of a Budget
        #
        tablename = "budget_monitoring"
        self.define_table(tablename,
                          # This is a component, so needs to be a super_link
                          # - can't override field name, ondelete or requires
                          self.super_link("budget_entity_id", "budget_entity"),
                          # Populated Automatically
                          # Used for Timeplot &, in future, to ease changing the monitoring frequency
                          s3_date("start_date",
                                  readable = False,
                                  writable = False,
                                  ),
                          s3_date("end_date",
                                  empty = False,
                                  label = T("Date"),
                                  ),
                          Field("planned", "double", notnull=True,
                                default = 0.00,
                                label = T("Planned Spend"),
                                represent = lambda v: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2),
                                requires = IS_FLOAT_AMOUNT(),
                                ),
                          Field("value", "double", notnull=True,
                                default = 0.00,
                                #label = T("Amount Spent"),
                                label = T("Actual Spend"),
                                represent = lambda v: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2),
                                requires = IS_FLOAT_AMOUNT(),
                                ),
                          s3_currency(required = True,
                                      # Normally set at Budget level
                                      writable = False,
                                      ),
                          Field.Method("percentage", self.budget_monitoring_percentage),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD Strings
        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Add Monitoring Data"),
        #    title_display = T("Monitoring Data Details"),
        #    title_list = T("Monitoring Data"),
        #    title_update = T("Edit Monitoring Data"),
        #    label_list_button = T("List Monitoring Data"),
        #    label_delete_button = T("Remove Monitoring Data"),
        #    msg_record_created = T("Monitoring Data added"),
        #    msg_record_modified = T("Monitoring Data updated"),
        #    msg_record_deleted = T("Monitoring Data removed"),
        #    msg_list_empty = T("No Monitoring Data currently registered in this Budget"),
        #)

        self.configure(tablename,
                       list_fields = ["end_date",
                                      "planned",
                                      "value",
                                      (T("Percentage"), "percentage"),
                                      "comments",
                                      ],
                       onaccept = self.budget_monitoring_onaccept,
                       onvalidation = self.budget_monitoring_onvalidation,
                       )

        # Pass names back to global scope (s3.*)
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_monitoring_onaccept(form):
        """
            Handle Updates of entries to reset the hidden start_date
        """

        db = current.db
        table = current.s3db.budget_monitoring

        # Read the Budget Monitoring record
        record_id = form.vars.id
        record = db(table.id == record_id).select(table.budget_entity_id,
                                                  table.start_date,
                                                  table.end_date,
                                                  limitby=(0, 1)
                                                  ).first()
        if not record:
            s3_debug("Cannot find Budget Monitoring record (no record for this ID), so can't update start_date")
            return
        budget_entity_id = record.budget_entity_id
        start_date = record.start_date
        end_date = record.end_date

        # Locate the immediately preceding record
        query = (table.budget_entity_id == budget_entity_id)  & \
                (table.deleted == False) & \
                (table.end_date < end_date)
        record = db(query).select(table.end_date,
                                  limitby=(0, 1),
                                  orderby=~(table.end_date),
                                  ).first()
        if record and record.end_date != start_date:
            # Update this record's start_date
            db(table.id == record_id).update(start_date = record.end_date)

        # Locate the immediately succeeding record
        query = (table.budget_entity_id == budget_entity_id)  & \
                (table.deleted == False) & \
                (table.end_date > end_date)
        record = db(query).select(table.id,
                                  table.start_date,
                                  limitby=(0, 1),
                                  orderby=table.end_date,
                                  ).first()
        if record and record.start_date != end_date:
            # Update that record's start_date
            record.update_record(start_date = end_date)

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_monitoring_onvalidation(form):
        """
            Don't allow total Planned to exceed Total Budget
        """

        db = current.db
        s3db = current.s3db
        mtable = s3db.budget_monitoring

        # Find the Budget
        record_id = form.record_id
        record = db(mtable.id == record_id).select(mtable.budget_entity_id,
                                                   limitby=(0, 1)
                                                   ).first()
        if not record:
            s3_debug("Cannot find Budget Monitoring record (no record for this ID), so can't check whether Total Budget is exceeded")
            return
        budget_entity_id = record.budget_entity_id

        # Read the Total Budget
        btable = s3db.budget_budget
        query = (btable.budget_entity_id == budget_entity_id)
        budget = db(query).select(btable.total_budget,
                                  limitby=(0, 1)
                                  ).first()
        if not budget:
            s3_debug("Cannot find Budget record (no record for this super_key), so can't check whether Total Budget is exceeded")
            return

        # Read the total Planned
        query = (mtable.budget_entity_id == budget_entity_id) & \
                (mtable.deleted == False) & \
                (mtable.id != record_id)
        records = db(query).select(mtable.planned)
        planned = 0
        for r in records:
            planned += r.planned
        # Add what we're trying to add
        planned += form.vars.planned

        # Check if we're over
        if planned > budget.total_budget:
            form.errors.planned = current.T("Total Budget of %s would be exceeded") % \
                budget.total_budget

    # -------------------------------------------------------------------------
    @staticmethod
    def budget_monitoring_percentage(row):
        """
            Virtual Field to show the percentage used of the Budget
        """

        if hasattr(row, "budget_monitoring"):
            row = row.budget_monitoring
        if hasattr(row, "planned"):
            planned = row.planned
            if planned == 0.0:
                # Can't divide by Zero
                return current.messages["NONE"]
        else:
            planned = None
        if hasattr(row, "value"):
            actual = row.value
        else:
            actual = None

        if planned is not None and actual is not None:
            percentage = actual / planned * 100
            return "%s %%" % "{0:.2f}".format(percentage)

        if hasattr(row, "id"):
            # Reload the record
            #s3_debug("Reloading budget_monitoring record")
            table = current.s3db.budget_monitoring
            r = current.db(table.id == row.id).select(table.planned,
                                                      table.value,
                                                      limitby=(0, 1)
                                                      ).first()
            if r:
                planned = r.planned
                if planned == 0.0:
                    # Can't divide by Zero
                    return current.messages["NONE"]
                percentage = r.value / planned * 100
                return "%s %%" % percentage

        return current.messages["NONE"]

# =============================================================================
class budget_CostItemRepresent(S3Represent):
    """ Representation of Cost Items """

    # -------------------------------------------------------------------------
    def __init__(self, show_link=False):
        """
            Constructor
        """

        super(budget_CostItemRepresent, self).__init__(lookup="budget_cost_item",
                                                       key="cost_item_id",
                                                       show_link=show_link,
                                                       )

        s3db = current.s3db
        self.represent = {
            "asset_id": s3db.asset_AssetRepresent(show_link=False),
            "site_id": s3db.org_SiteRepresent(show_link=False),
            "human_resource_id": s3db.hrm_HumanResourceRepresent(show_link=False),
        }

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=[]):
        """
            Custom rows lookup function

            @param key: the key field
            @param values: the values to look up
            @param fields: unused (retained for API compatibility)
        """

        db = current.db
        s3db = current.s3db

        instance_fields = {
            "event_asset": ["incident_id", "asset_id"],
            "event_site": ["incident_id", "site_id"],
            "event_human_resource": ["incident_id", "human_resource_id"],
        }

        # Get all super-entity rows
        etable = s3db.budget_cost_item
        rows = db(key.belongs(values)).select(key,
                                              etable.instance_type)
        self.queries += 1

        # Sort the super-entity rows by instance type
        keyname = key.name
        types = {}
        for row in rows:
            instance_type = row.instance_type
            cost_item_id = row[keyname]
            if instance_type not in types:
                types[instance_type] = {cost_item_id: row}
            else:
                types[instance_type][cost_item_id] = row

        # Get all instance records (per instance type)
        results = []
        append = results.append
        for instance_type in types:

            # Determine instance table
            table = s3db.table(instance_type)
            if not table:
                continue

            # Determine instance fields
            fields = []
            bulk_repr = {}
            if instance_type in instance_fields:
                for fname in instance_fields[instance_type]:
                    field = table[fname]
                    # Supports bulk representation?
                    if fname in self.represent:
                        represent = self.represent[fname]
                    else:
                        represent = field.represent
                    if represent and hasattr(represent, "bulk"):
                        bulk_repr[fname] = {"method": represent, "values": []}
                    fields.append(field)
            else:
                continue
            fields.insert(0, table[keyname])

            # Extract instance rows
            query = (table[keyname].belongs(types[instance_type].keys()))
            rows = db(query).select(*fields)
            self.queries += 1

            # Construct result rows
            sdata = types[instance_type]
            for row in rows:
                for fname, frepr in bulk_repr.items():
                    frepr["values"].append(row[fname])
                # Construct a new Row which contains both, the super-entity
                # record and the instance record:
                append(Row(budget_cost_item = sdata[row[keyname]],
                           **{instance_type: row}))

            # Bulk representation of instance fields:
            # The results are stored in S3Represent instance, and there they
            # will be re-used for single-value representation in represent_row
            for fname, frepr in bulk_repr.items():
                frepr["method"].bulk(frepr["values"])

        return results

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        s3db = current.s3db

        cost_item = row.budget_cost_item
        instance_type = cost_item.instance_type

        # Type-specific representation
        item = object.__getattribute__(row, instance_type)
        if instance_type == "event_asset":
            table = s3db.event_asset
            repr_str = "%s - %s" % \
                       (table.incident_id.represent(item.incident_id),
                        self.represent["asset_id"](item.asset_id),
                        )
        elif instance_type == "event_site":
            table = s3db.event_site
            repr_str = "%s - %s" % \
                       (table.incident_id.represent(item.incident_id),
                        self.represent["site_id"](item.site_id),
                        )
        elif instance_type == "event_human_resource":
            table = s3db.event_human_resource
            repr_str = "%s - %s" % \
                        (table.incident_id.represent(item.incident_id),
                         self.represent["human_resource_id"](item.human_resource_id),
                         )
        else:
            # Unknown instance type
            etable = s3db.budget_cost_item
            instance_type_nice = etable.instance_type.represent(instance_type)
            repr_str = "%s #%s" % (instance_type_nice,
                                   cost_item.cost_item_id,
                                   )
        return repr_str

# =============================================================================
def budget_kit_totals(kit_id):
    """
        Calculate Totals for a Kit
    """

    db = current.db
    s3db = current.s3db

    # Lookup all item quantities in this kit
    ltable = s3db.budget_kit_item
    query = (ltable.kit_id == kit_id) & \
            (ltable.deleted == False)
    items = db(query).select(ltable.item_id, ltable.quantity)
    item_ids = set(item.item_id for item in items)

    # Lookup the individual costs of each item
    itable = s3db.budget_item
    query = (itable.id.belongs(item_ids))
    costs = db(query).select(itable.id,
                             itable.unit_cost,
                             itable.monthly_cost,
                             itable.minute_cost,
                             itable.megabyte_cost).as_dict()

    # Calculate the totals per cost category
    total_unit_cost = 0
    total_monthly_cost = 0
    total_minute_cost = 0
    total_megabyte_cost = 0

    for item in items:

        quantity = item.quantity
        item_costs = costs[item.item_id]

        total_unit_cost += item_costs["unit_cost"] * quantity
        total_monthly_cost += item_costs["monthly_cost"] * quantity
        total_minute_cost += item_costs["minute_cost"] * quantity
        total_megabyte_cost += item_costs["megabyte_cost"] * quantity

    # Update the kit
    ktable = s3db.budget_kit
    db(ktable.id == kit_id).update(total_unit_cost=total_unit_cost,
                                   total_monthly_cost=total_monthly_cost,
                                   total_minute_cost=total_minute_cost,
                                   total_megabyte_cost=total_megabyte_cost)

    # Update totals in all bundles with this kit
    linktable = s3db.budget_bundle_kit
    bundle_id = linktable.bundle_id
    rows = db(linktable.kit_id == kit_id).select(bundle_id,
                                                 groupby=bundle_id)
    for row in rows:
        budget_bundle_totals(row.bundle_id)

    # @todo: fix this
    #audit("update", module, "kit", record=kit, representation="html")
    return

# =============================================================================
def budget_bundle_totals(bundle_id):
    """
        Calculate Totals for a Bundle
    """

    s3db = current.s3db
    db = current.db

    total_unit_cost = 0
    total_monthly_cost = 0

    # Calculate costs of kits
    ktable = s3db.budget_kit
    linktable = s3db.budget_bundle_kit
    left = [ktable.on(linktable.kit_id == ktable.id)]
    query = (linktable.bundle_id == bundle_id)
    rows = db(query).select(linktable.quantity,
                            linktable.minutes,
                            linktable.megabytes,
                            ktable.total_unit_cost,
                            ktable.total_monthly_cost,
                            ktable.total_minute_cost,
                            ktable.total_megabyte_cost,
                            left=left)
    for row in rows:
        kit = row[ktable]
        link = row[linktable]
        quantity = link.quantity

        # One-time costs
        total_unit_cost += kit.total_unit_cost * quantity

        # Monthly costs
        monthly_cost = kit.total_monthly_cost + \
                       kit.total_minute_cost * link.minutes + \
                       kit.total_megabyte_cost * link.megabytes
        total_monthly_cost += monthly_cost * quantity

    # Calculate costs of items
    itable = s3db.budget_item
    linktable = s3db.budget_bundle_item
    left = [itable.on(linktable.item_id == itable.id)]
    query = (linktable.bundle_id == bundle_id)
    rows = db(query).select(linktable.quantity,
                            linktable.minutes,
                            linktable.megabytes,
                            itable.unit_cost,
                            itable.monthly_cost,
                            itable.minute_cost,
                            itable.megabyte_cost,
                            left=left)
    for row in rows:
        item = row[itable]
        link = row[linktable]
        quantity = link.quantity

        # One-time costs
        total_unit_cost += item.unit_cost * quantity

        # Monthly costs
        monthly_cost = item.monthly_cost + \
                       item.minute_cost * link.minutes + \
                       item.megabyte_cost * link.megabytes
        total_monthly_cost += monthly_cost * quantity

    # Update the bundle
    btable = s3db.budget_bundle
    db(btable.id == bundle_id).update(total_unit_cost=total_unit_cost,
                                      total_monthly_cost=total_monthly_cost)

    # Update totals of all budgets with this bundle
    linktable = s3db.budget_budget_bundle
    budget_entity_id = linktable.budget_entity_id
    rows = db(linktable.bundle_id == bundle_id).select(budget_entity_id,
                                                       groupby=budget_entity_id)
    for row in rows:
        budget_budget_totals(row.budget_entity_id)

    # @todo: fix this:
    #audit("update", module, "bundle", record=bundle, representation="html")
    return

# =============================================================================
def budget_budget_totals(budget_entity_id):
    """
        Calculate Totals for a budget

        @param budget_entity_id: the budget_entity record ID
    """

    db = current.db
    s3db = current.s3db

    total_onetime_cost = 0
    total_recurring_cost = 0

    # Calculate staff costs
    stable = s3db.budget_staff
    ltable = s3db.budget_location

    linktable = s3db.budget_budget_staff

    left = [stable.on(linktable.staff_id == stable.id),
            ltable.on(linktable.location_id == ltable.id),
            ]
    query = (linktable.budget_entity_id == budget_entity_id)
    rows = db(query).select(linktable.quantity,
                            linktable.months,
                            stable.salary,
                            stable.travel,
                            ltable.subsistence,
                            ltable.hazard_pay,
                            left=left)

    for row in rows:
        quantity = row[linktable.quantity]

        # Travel costs are one time
        total_onetime_cost += row[stable.travel] * quantity

        # Recurring costs are monthly
        recurring_costs = row[stable.salary] + \
                          row[ltable.subsistence] + \
                          row[ltable.hazard_pay]
        total_recurring_cost += recurring_costs * \
                                quantity * \
                                row[linktable.months]

    # Calculate bundle costs
    btable = s3db.budget_bundle

    linktable = s3db.budget_budget_bundle

    left = [btable.on(linktable.bundle_id == btable.id)]

    query = (linktable.budget_entity_id == budget_entity_id)
    rows = db(query).select(linktable.quantity,
                            linktable.months,
                            btable.total_unit_cost,
                            btable.total_monthly_cost,
                            left=left)

    for row in rows:
        quantity = row[linktable.quantity]

        total_onetime_cost += row[btable.total_unit_cost] * \
                              quantity
        total_recurring_cost += row[btable.total_monthly_cost] * \
                                quantity * \
                                row[linktable.months]

    table = s3db.budget_budget
    db(table.id == budget_entity_id).update(total_onetime_costs=total_onetime_cost,
                                     total_recurring_costs=total_recurring_cost)

    # @todo: fix this
    #audit("update", module, "budget", record=budget, representation="html")

# =============================================================================
def budget_rheader(r):

    T = current.T
    if r.representation != "html":
        return None

    resourcename = r.name

    if resourcename == "budget":

        tpvars = dict(r.get_vars)
        tpvars["component"] = "allocation"

        tabs = [(T("Basic Details"), None),
                (T("Staff"), "staff"),
                (T("Bundles"), "bundle"),
                (T("Allocation"), "allocation"),
                (T("Report"), "timeplot", tpvars),
                ]

        rheader_fields = [["name"],
                          ["description"],
                          ["total_budget"],
                          ["total_onetime_costs"],
                          ["total_recurring_costs"],
                          ]
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename == "bundle":

        tabs = [(T("Basic Details"), None),
                (T("Kits"), "kit"),
                (T("Items"), "item"),
                ]

        rheader_fields = [["name"],
                          ["description"],
                          ["total_unit_cost"],
                          ["total_monthly_cost"],
                          ]
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename == "kit":

        tabs = [(T("Basic Details"), None),
                (T("Items"), "item"),
                ]

        rheader_fields = [["code"],
                          ["description"],
                          ["total_unit_cost"],
                          ["total_monthly_cost"],
                          ]
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    return rheader

# END =========================================================================
