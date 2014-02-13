# -*- coding: utf-8 -*-

""" Sahana Eden Budget Model

    @copyright: 2009-2013 (c) Sahana Software Foundation
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

__all__ = ["S3BudgetModel",
           "S3BudgetKitModel",
           "S3BudgetBundleModel",
           "budget_rheader",
          ]

from gluon import *
from gluon.dal import Row
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class S3BudgetModel(S3Model):

    names = ["budget_budget",
             "budget_parameter",
             "budget_location",
             "budget_budget_id",
             "budget_location_id",
             "budget_staff",
             "budget_budget_staff",
             "budget_staff_id",
            ]

    def model(self):

        T = current.T
        configure = self.configure
        define_table = self.define_table
        add_components = self.add_components

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        db = current.db

        # ---------------------------------------------------------------------
        # Budgets
        #
        tablename = "budget_budget"
        table = define_table(tablename,
                             Field("name",
                                   length = 128,
                                   notnull = True,
                                   unique = True,
                                   #requires = [IS_NOT_EMPTY(),
                                               #IS_NOT_ONE_OF(db, "%s.name" % tablename),
                                              #],
                                   label = T("Name"),
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
                             s3_comments(),
                             *s3_meta_fields()
                            )

        # CRUD Strings
        ADD_BUDGET = T("Add Budget")
        crud_strings[tablename] = Storage(
            title_create = ADD_BUDGET,
            title_display = T("Budget Details"),
            title_list = T("Budgets"),
            title_update = T("Edit Budget"),
            title_search = T("Search Budgets"),
            subtitle_create = T("Add New Budget"),
            label_list_button = T("List Budgets"),
            label_create_button = ADD_BUDGET,
            label_delete_button = T("Delete Budget"),
            msg_record_created = T("Budget added"),
            msg_record_modified = T("Budget updated"),
            msg_record_deleted = T("Budget deleted"),
            msg_list_empty = T("No Budgets currently registered"),
        )

        # Represent
        budget_budget_represent = S3Represent(lookup=tablename)

        # Reusable Field
        budget_budget_id = S3ReusableField("budget_id", table,
                                requires = IS_ONE_OF(db, "budget_budget.id",
                                                     budget_budget_represent,
                                                    ),
                                represent = budget_budget_represent,
                                label = T("Budget"),
                                comment = S3AddResourceLink(
                                            c = "budget",
                                            f = "budget",
                                            label = T("Add Budget"),
                                            title = T("Budget"),
                                            tooltip = T("You can add a new budget by clicking link 'Add Budget'.")
                                          ),
                                ondelete = "CASCADE",
                           )

        add_components(tablename,
                       # Staff
                       budget_staff={"link": "budget_budget_staff",
                                     "joinby": "budget_id",
                                     "key": "staff_id",
                                     "actuate": "link",
                                    },
                       # Bundles
                       budget_bundle={"link": "budget_budget_bundle",
                                      "joinby": "budget_id",
                                      "key": "bundle_id",
                                      "actuate": "link",
                                     },
                      )

        # Configuration
        configure(tablename,
                  onaccept = self.budget_budget_onaccept)

        # ---------------------------------------------------------------------
        # Parameters (currently unused)
        #
        # @todo: take into account when calculating totals
        #
        tablename = "budget_parameter"
        table = define_table(tablename,
                             Field("shipping", "double",
                                   default = 15.0,
                                   requires = IS_FLOAT_IN_RANGE(0, 100),
                                   notnull = True,
                                   label = T("Shipping cost"),
                                  ),
                             Field("logistics", "double",
                                   default = 0.0,
                                   requires = IS_FLOAT_IN_RANGE(0, 100),
                                   notnull = True,
                                   label = T("Procurement & Logistics cost"),
                                  ),
                             Field("admin", "double",
                                   default = 0.0,
                                   requires = IS_FLOAT_IN_RANGE(0, 100),
                                   notnull = True,
                                   label = T("Administrative support cost"),
                                  ),
                             Field("indirect", "double",
                                   default = 7.0,
                                   requires = IS_FLOAT_IN_RANGE(0, 100),
                                   notnull = True,
                                   label = T("Indirect support cost HQ"),
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
        table = define_table(tablename,
                             Field("code",
                                   length = 3,
                                   notnull = True,
                                   unique = True,
                                   #requires = [IS_NOT_EMPTY(),
                                               #IS_NOT_ONE_OF(db, "%s.code" % tablename),
                                              #],
                                   label = T("Code"),
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
        ADD_LOCATION = T("Add Location")
        crud_strings[tablename] = Storage(
            title_create = ADD_LOCATION,
            title_display = T("Location Details"),
            title_list = T("Locations"),
            title_update = T("Edit Location"),
            title_search = T("Search Locations"),
            subtitle_create = T("Add New Location"),
            label_list_button = T("List Locations"),
            label_create_button = ADD_LOCATION,
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
        budget_location_id = S3ReusableField("location_id", table,
                                requires = IS_ONE_OF(db, "budget_location.id",
                                                     budget_location_represent,
                                                    ),
                                represent = budget_location_represent,
                                label = T("Location"),
                                comment = S3AddResourceLink(
                                            c = "budget",
                                            f = "location",
                                            label = T("Add Location"),
                                            title = T("Location"),
                                            tooltip = T("You can add a new location by clicking link 'Add Location'.")
                                          ),
                                ondelete = "CASCADE",
                             )

        # Configuration
        configure(tablename,
                  update_onaccept = self.budget_location_onaccept)

        # ---------------------------------------------------------------------
        # Staff Types
        #
        tablename = "budget_staff"
        table = define_table(tablename,
                             Field("name",
                                   length = 128,
                                   notnull = True,
                                   unique = True,
                                   #requires = [IS_NOT_EMPTY(),
                                               #IS_NOT_ONE_OF(db, "%s.name" % tablename),
                                              #],
                                   label = T("Name"),
                                  ),
                             Field("grade",
                                   notnull = True,
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Grade"),
                                  ),
                             Field("salary", "integer",
                                   notnull = True,
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Monthly Salary"),
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
        ADD_STAFF_TYPE = T("Add Staff Type")
        crud_strings[tablename] = Storage(
            title_create = ADD_STAFF_TYPE,
            title_display = T("Staff Type Details"),
            title_list = T("Staff Types"),
            title_update = T("Edit Staff Type"),
            title_search = T("Search Staff Types"),
            subtitle_create = T("Add New Staff Type"),
            label_list_button = T("List Staff Types"),
            label_create_button = ADD_STAFF_TYPE,
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
        budget_staff_id = S3ReusableField("staff_id", table,
                                requires = IS_ONE_OF(db, "budget_staff.id",
                                                     budget_staff_represent,
                                                    ),
                                represent = budget_staff_represent,
                                label = T("Staff"),
                                comment = S3AddResourceLink(
                                            c = "budget",
                                            f = "staff",
                                            label = T("Add Staff"),
                                            title = T("Staff"),
                                            tooltip = T("You can add new staff by clicking link 'Add Staff'.")
                                          ),
                                ondelete = "RESTRICT",
                          )

        # Configuration
        configure(tablename,
                  update_onaccept = self.budget_staff_onaccept)

        # ---------------------------------------------------------------------
        # Budget<>Staff Many2Many
        #
        tablename = "budget_budget_staff"
        table = define_table(tablename,
                             budget_budget_id(),
                             self.project_project_id(),
                             budget_location_id(),
                             budget_staff_id(),
                             Field("quantity", "integer",
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Quantity"),
                                   default = 1,
                                   notnull = True,
                                  ),
                             Field("months", "integer",
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Months"),
                                   default = 3,
                                   notnull = True,
                                  ),
                             *s3_meta_fields())

        # Configuration
        configure(tablename,
                  onaccept = self.budget_budget_staff_onaccept,
                  ondelete = self.budget_budget_staff_ondelete)

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(budget_budget_id = budget_budget_id,
                    budget_location_id = budget_location_id,
                    budget_staff_id=budget_staff_id,
                   )

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        budget_budget_id = S3ReusableField("budget_id", "integer",
                                           readable = False,
                                           writable = False)
        budget_location_id = S3ReusableField("location_id", "integer",
                                             readable = False,
                                             writable = False)
        budget_staff_id = S3ReusableField("staff_id", "integer",
                                          readable = False,
                                          writable = False)
                                             
        return dict(budget_budget_id = budget_budget_id,
                    budget_location_id = budget_location_id,
                    budget_staff_id = budget_staff_id,
                   )
                   
    # -------------------------------------------------------------------------
    @staticmethod
    def budget_budget_onaccept(form):
        """
            Calculate totals for the budget
        """

        try:
            budget_id = form.vars.id
        except:
            return
        budget_budget_totals(budget_id)
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
        budget_id = linktable.budget_id
        rows = current.db(linktable.staff_id == record_id).select(budget_id,
                                                          groupby=budget_id)
        for row in rows:
            budget_budget_totals(row.budget_id)
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
        budget_id = linktable.budget_id
        rows = current.db(linktable.location_id == record_id).select(budget_id,
                                                             groupby=budget_id)
        for row in rows:
            budget_budget_totals(row.budget_id)
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
        row = current.db(table.id == record_id).select(table.budget_id,
                                                       limitby=(0, 1)).first()
        if record:
            budget_budget_totals(row.budget_id)
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
            budget_id = deleted_fk.get("budget_id")
            if budget_id:
                budget_budget_totals(budget_id)
        return

# =============================================================================
class S3BudgetKitModel(S3Model):

    names = ["budget_kit",
             "budget_item",
             "budget_kit_item",
             "budget_kit_id",
             "budget_item_id",
            ]
    
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
        table = define_table(tablename,
                             Field("code",
                                   length = 128,
                                   notnull = True,
                                   unique = True,
                                   #requires = [IS_NOT_EMPTY(),
                                               #IS_NOT_ONE_OF(db, "%s.code" % tablename),
                                              #],
                                   label = T("Code"),
                                  ),
                             Field("description",
                                   label = T("Description"),
                                  ),
                             Field("total_unit_cost", "double",
                                   default = 0.0,
                                   writable = False,
                                   label = T("Total Unit Cost"),
                                  ),
                             Field("total_monthly_cost", "double",
                                   default = 0.0,
                                   writable = False,
                                   label = T("Total Monthly Cost"),
                                  ),
                             Field("total_minute_cost", "double",
                                   default = 0.0,
                                   writable = False,
                                   label = T("Total Cost per Minute"),
                                  ),
                             Field("total_megabyte_cost", "double",
                                   default = 0.0,
                                   writable = False,
                                   label = T("Total Cost per Megabyte"),
                                  ),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_KIT = T("Add Kit")
        crud_strings[tablename] = Storage(
            title_create = ADD_KIT,
            title_display = T("Kit Details"),
            title_list = T("Kits"),
            title_update = T("Edit Kit"),
            title_search = T("Search Kits"),
            subtitle_create = T("Add New Kit"),
            label_list_button = T("List Kits"),
            label_create_button = ADD_KIT,
            label_delete_button = T("Delete Kit"),
            msg_record_created = T("Kit added"),
            msg_record_modified = T("Kit updated"),
            msg_record_deleted = T("Kit deleted"),
            msg_list_empty = T("No Kits currently registered"),
        )

        # Represent
        budget_kit_represent = S3Represent(lookup=tablename, fields=["code"])
                             
        # Reusable Field
        budget_kit_id = S3ReusableField("kit_id", table,
                                requires = IS_ONE_OF(db, "budget_kit.id",
                                                     budget_kit_represent,
                                                    ),
                                represent = budget_kit_represent,
                                label = T("Kit"),
                                comment = S3AddResourceLink(
                                            c = "budget",
                                            f = "kit",
                                            label = T("Add kit"),
                                            title = T("Kit"),
                                            tooltip = T("You can add a new kit by clicking link 'Add Kit'.")
                                          ),
                                ondelete = "RESTRICT",
                             )

        # Configuration
        configure(tablename,
                  onaccept = self.budget_kit_onaccept,
                 )

        # Components
        add_components(tablename,
                       # Items
                       budget_item={"link": "budget_kit_item",
                                    "joinby": "kit_id",
                                    "key": "item_id",
                                    "actuate": "link",
                                   },
                      )

        # ---------------------------------------------------------------------
        # Items
        #
        budget_cost_type_opts = {1:T("One-time"),
                                 2:T("Recurring"),
                                }
                                
        budget_category_type_opts = {1:T("Consumable"),
                                     2:T("Satellite"),
                                     3:"HF",
                                     4:"VHF",
                                     5:T("Telephony"),
                                     6:"WLAN",
                                     7:T("Network"),
                                     8:T("Generator"),
                                     9:T("Electrical"),
                                     10:T("Vehicle"),
                                     11:"GPS",
                                     12:T("Tools"),
                                     13:"IT",
                                     14:"ICT",
                                     15:"TC",
                                     16:T("Stationery"),
                                     17:T("Relief"),
                                     18:T("Miscellaneous"),
                                     19:T("Running Cost"),
                                    }
            
        tablename = "budget_item"
        table = define_table(tablename,
                             Field("category_type", "integer",
                                   notnull = True,
                                   requires = IS_IN_SET(budget_category_type_opts, zero=None),
                                   #default = 1,
                                   label = T("Category"),
                                   represent = lambda opt: \
                                               budget_category_type_opts.get(opt, UNKNOWN_OPT)
                                  ),
                             Field("code",
                                   length = 128,
                                   notnull = True,
                                   unique = True,
                                   #requires = [IS_NOT_EMPTY(),
                                               #IS_NOT_ONE_OF(db, "%s.code" % tablename),
                                              #],
                                   label = T("Code"),
                                  ),
                             Field("description",
                                   notnull = True,
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Description"),
                                  ),
                             Field("cost_type", "integer",
                                   notnull = True,
                                   requires = IS_IN_SET(budget_cost_type_opts,
                                                        zero=None),
                                   #default = 1,
                                   label = T("Cost Type"),
                                   represent = lambda opt: \
                                               budget_cost_type_opts.get(opt, UNKNOWN_OPT)
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
        ADD_ITEM = T("Add Item")
        crud_strings[tablename] = Storage(
            title_create = ADD_ITEM,
            title_display = T("Item Details"),
            title_list = T("Items"),
            title_update = T("Edit Item"),
            title_search = T("Search Items"),
            subtitle_create = T("Add New Item"),
            label_list_button = T("List Items"),
            label_create_button = ADD_ITEM,
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
        budget_item_id = S3ReusableField("item_id", table,
                                requires = IS_ONE_OF(db, "budget_item.id",
                                                     budget_item_represent,
                                                    ),
                                represent = budget_item_represent,
                                label = T("Item"),
                                comment = S3AddResourceLink(
                                            c = "budget",
                                            f = "item",
                                            label = T("Add item"),
                                            title = T("Item"),
                                            tooltip = T("You can add a new item by clicking link 'Add Item'.")
                                          ),
                                ondelete = "RESTRICT",
                             )

        # Configuration
        configure(tablename,
                  onaccept = self.budget_item_onaccept,
                  main = "code",
                  extra = "description",
                  orderby = table.category_type,
                 )

        # ---------------------------------------------------------------------
        # Kit<>Item Many2Many
        #
        tablename = "budget_kit_item"
        table = define_table(tablename,
                             budget_kit_id(),
                             budget_item_id(),
                             Field("quantity", "integer",
                                   default = 1,
                                   notnull = True,
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Quantity"),
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

        budget_kit_id = S3ReusableField("kit_id", "integer",
                                        readable = False,
                                        writable = False)
        budget_item_id = S3ReusableField("item_id", "integer",
                                         readable = False,
                                         writable = False)

        return dict(budget_kit_id = budget_kit_id,
                    budget_item_id = budget_item_id,
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

    names = ["budget_bundle",
             "budget_bundle_kit",
             "budget_bundle_item",
             "budget_budget_bundle",
             "budget_bundle_id",
            ]

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
        table = define_table(tablename,
                             Field("name",
                                   length = 128,
                                   notnull = True,
                                   unique = True,
                                   #requires = [IS_NOT_EMPTY(),
                                               #IS_NOT_ONE_OF(db, "%s.name" % tablename),
                                              #],
                                   label = T("Name"),
                                  ),
                             Field("description",
                                   label = T("Description"),
                                  ),
                             Field("total_unit_cost", "double",
                                   default = 0.0,
                                   writable = False,
                                   label = T("One time cost"),
                                  ),
                             Field("total_monthly_cost", "double",
                                   default = 0.0,
                                   writable = False,
                                   label = T("Recurring cost"),
                                  ),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_BUNDLE = T("Add Bundle")
        crud_strings[tablename] = Storage(
            title_create = ADD_BUNDLE,
            title_display = T("Bundle Details"),
            title_list = T("Bundles"),
            title_update = T("Edit Bundle"),
            title_search = T("Search Bundles"),
            subtitle_create = T("Add New Bundle"),
            label_list_button = T("List Bundles"),
            label_create_button = ADD_BUNDLE,
            label_delete_button = T("Delete Bundle"),
            msg_record_created = T("Bundle added"),
            msg_record_modified = T("Bundle updated"),
            msg_record_deleted = T("Bundle deleted"),
            msg_list_empty = T("No Bundles currently registered"),
        )

        # Configuration
        configure(tablename,
                  onaccept = self.budget_bundle_onaccept)

        # Components
        add_components(tablename,
                       # Items
                       budget_item={"link": "budget_bundle_item",
                                    "joinby": "bundle_id",
                                    "key": "item_id",
                                    "actuate": "link",
                                   },
                       # Kits
                       budget_kit={"link": "budget_bundle_kit",
                                   "joinby": "bundle_id",
                                   "key": "kit_id",
                                   "actuate": "link",
                                  },
                      )

        # Represent
        budget_bundle_represent = S3Represent(lookup=tablename,
                                             fields=["name"])

        # Reusable Field
        budget_bundle_id = S3ReusableField("bundle_id", table,
                                requires = IS_ONE_OF(db, "budget_bundle.id",
                                                     budget_bundle_represent,
                                                    ),
                                represent = budget_bundle_represent,
                                label = T("Bundle"),
                                comment = S3AddResourceLink(
                                            c = "budget",
                                            f = "bundle",
                                            label = T("Add Bundle"),
                                            title = T("Bundle"),
                                            tooltip = T("You can add a new bundle by clicking link 'Add Bundle'.")
                                          ),
                                ondelete = "RESTRICT",
                             )

        # ---------------------------------------------------------------------
        # Bundle<>Kit Many2Many
        #
        tablename = "budget_bundle_kit"
        table = define_table(tablename,
                             budget_bundle_id(),
                             self.budget_kit_id(),
                             Field("quantity", "integer",
                                   default = 1,
                                   notnull = True,
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Quantity"),
                                  ),
                             Field("minutes", "integer",
                                   default = 0,
                                   notnull = True,
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Minutes per Month"),
                                  ),
                             Field("megabytes", "integer",
                                   default = 0,
                                   notnull = True,
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Megabytes per Month"),
                                  ),
                             *s3_meta_fields())

        # @todo: CRUD Strings

        # Configuration
        configure(tablename,
                  onaccept = self.budget_bundle_kit_onaccept,
                  ondelete = self.budget_bundle_kit_ondelete)
        
        # ---------------------------------------------------------------------
        # Bundle<>Item Many2Many
        #
        tablename = "budget_bundle_item"
        table = define_table(tablename,
                             budget_bundle_id(),
                             self.budget_item_id(),
                             Field("quantity", "integer",
                                   default = 1,
                                   notnull = True,
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Quantity"),
                                  ),
                             Field("minutes", "integer",
                                   default = 0,
                                   notnull = True,
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Minutes per Month"),
                                  ),
                             Field("megabytes", "integer",
                                   default = 0,
                                   notnull = True,
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Megabytes per Month"),
                                  ),
                             *s3_meta_fields())

        # @todo: CRUD Strings

        # Configuration
        configure(tablename,
                  onaccept = self.budget_bundle_item_onaccept,
                  ondelete = self.budget_bundle_item_ondelete)

        # ---------------------------------------------------------------------
        # Budget<>Bundle Many2Many
        #
        tablename = "budget_budget_bundle"
        table = define_table(tablename,
                             self.budget_budget_id(),
                             self.project_project_id(),
                             self.budget_location_id(),
                             budget_bundle_id(),
                             Field("quantity", "integer",
                                   default = 1,
                                   notnull = True,
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Quantity"),
                                  ),
                             Field("months", "integer",
                                   default = 3,
                                   notnull = True,
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Months"),
                                  ),
                             *s3_meta_fields())

        # @todo: CRUD Strings

        # Configuration
        configure(tablename,
                  onaccept = self.budget_budget_bundle_onaccept,
                  ondelete = self.budget_budget_bundle_ondelete)

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

        budget_bundle_id = S3ReusableField("bundle_id", "integer",
                                           readable = False,
                                           writable = False)

        return dict(budget_bundle_id = budget_bundle_id,
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
        row = current.db(table.id == record_id).select(table.budget_id,
                                                       limitby=(0, 1)).first()
        if row:
            budget_budget_totals(row.budget_id)
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
            budget_id = deleted_fk.get("budget_id")
            if budget_id:
                budget_budget_totals(budget_id)
        return

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
    budget_id = linktable.budget_id
    rows = db(linktable.bundle_id == bundle_id).select(budget_id,
                                                       groupby=budget_id)
    for row in rows:
        budget_budget_totals(row.budget_id)

    # @todo: fix this:
    #audit("update", module, "bundle", record=bundle, representation="html")
    return

# =============================================================================
def budget_budget_totals(budget_id):
    """
        Calculate Totals for a budget

        @param budget_id: the budget_budget record ID
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
    query = (linktable.budget_id == budget_id)
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

    query = (linktable.budget_id == budget_id)
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
    db(table.id == budget_id).update(total_onetime_costs=total_onetime_cost,
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
        
        tabs = [(T("Basic Details"), None),
                (T("Staff"), "staff"),
                (T("Bundles"), "bundle"),
               ]
               
        rheader_fields = [["name"],
                          ["description"],
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
