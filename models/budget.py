# -*- coding: utf-8 -*-

"""
    Budgetting module

    NB Depends on Project Tracking module

    @ToDo: Rewrite to use Inventory for Items
    @ToDo: Rewrite to use HRM for Staff
    @ToDo: Rewrite to remove the dependency on Geraldo
           - Items easy
           - Kits harder

    @author: Fran Boon
"""

# Requires 'project' module
if deployment_settings.has_module("budget") and \
   deployment_settings.has_module("project"):

    def budget_tables():
        """ Load the Budget tables as-needed """

        # Load the models we depend on
        project_id = s3db.project_project_id

        module = "budget"

        # Parameters
        # Only record 1 is used
        resourcename = "parameter"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("shipping", "double", default=15.00, notnull=True),
                                Field("logistics", "double", default=0.00, notnull=True),
                                Field("admin", "double", default=0.00, notnull=True),
                                Field("indirect", "double", default=7.00, notnull=True),

                                *(s3_timestamp() + s3_uid()))

        table.shipping.requires = IS_FLOAT_IN_RANGE(0, 100)
        table.logistics.requires = IS_FLOAT_IN_RANGE(0, 100)
        table.admin.requires = IS_FLOAT_IN_RANGE(0, 100)
        table.indirect.requires = IS_FLOAT_IN_RANGE(0, 100)

        # Items
        budget_cost_type_opts = {
            1:T("One-time"),
            2:T("Recurring")
            }
        cost_type = S3ReusableField("cost_type", "integer",
                                    notnull=True,
                                    requires = IS_IN_SET(budget_cost_type_opts,
                                                        zero=None),
                                    # default = 1,
                                    label = T("Cost Type"),
                                    represent = lambda opt: \
                                        budget_cost_type_opts.get(opt, UNKNOWN_OPT))

        budget_category_type_opts = {
            1:T("Consumable"),
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
            19:T("Running Cost")
            }
        category_type = S3ReusableField("category_type", "integer", notnull=True,
                                        requires = IS_IN_SET(budget_category_type_opts, zero=None),
                                        # default = 1,
                                        label = T("Category"),
                                        represent = lambda opt: budget_category_type_opts.get(opt, UNKNOWN_OPT))
        resourcename = "item"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                category_type(),
                                Field("code", length=128, notnull=True, unique=True),
                                Field("description", notnull=True),
                                cost_type(),
                                Field("unit_cost", "double", default=0.00),
                                Field("monthly_cost", "double", default=0.00),
                                Field("minute_cost", "double", default=0.00),
                                Field("megabyte_cost", "double", default=0.00),
                                s3_comments(),

                                *(s3_timestamp() + s3_uid() + s3_deletion_status()))

        table.code.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.code" % table)]
        table.description.requires = IS_NOT_EMPTY()

        def item_cascade(form):
            """
            When an Item is updated, then also need to update all Kits, Bundles & Budgets which contain this item
            Called as an onaccept from the RESTlike controller
            """
            # Check if we're an update form
            if form.vars.id:
                item = form.vars.id
                # Update Kits containing this Item
                table = db.budget_kit_item
                query = table.item_id==item
                rows = db(query).select()
                for row in rows:
                    kit = row.kit_id
                    kit_totals(kit)
                    # Update Bundles containing this Kit
                    table = db.budget_bundle_kit
                    query = (table.kit_id == kit)
                    rows = db(query).select()
                    for row in rows:
                        bundle = row.bundle_id
                        bundle_totals(bundle)
                        # Update Budgets containing this Bundle (tbc)
                # Update Bundles containing this Item
                table = db.budget_bundle_item
                query = (table.item_id == item)
                rows = db(query).select()
                for row in rows:
                    bundle = row.bundle_id
                    bundle_totals(bundle)
                    # Update Budgets containing this Bundle (tbc)
            return

        s3mgr.configure(tablename,
                        onaccept=item_cascade)

        # Kits
        resourcename = "kit"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("code", length=128, notnull=True, unique=True),
                                Field("description"),
                                Field("total_unit_cost", "double", writable=False),
                                Field("total_monthly_cost", "double", writable=False),
                                Field("total_minute_cost", "double", writable=False),
                                Field("total_megabyte_cost", "double", writable=False),
                                s3_comments(),

                                *(s3_timestamp() + s3_uid() + s3_deletion_status()))

        table.code.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.code" % table)]

        def kit_totals(kit):
            "Calculate Totals for a Kit"
            table = db.budget_kit_item
            query = table.kit_id == kit
            items = db(query).select()
            total_unit_cost = 0
            total_monthly_cost = 0
            total_minute_cost = 0
            total_megabyte_cost = 0
            for item in items:
                query = (table.kit_id == kit) & (table.item_id == item.item_id)
                quantity = db(query).select(table.quantity, limitby=(0, 1)).first().quantity
                row = db(db.budget_item.id == item.item_id).select(db.budget_item.unit_cost, db.budget_item.monthly_cost, db.budget_item.minute_cost, db.budget_item.megabyte_cost, limitby=(0, 1)).first()
                total_unit_cost += row.unit_cost * quantity
                total_monthly_cost += row.monthly_cost * quantity
                total_minute_cost += row.minute_cost * quantity
                total_megabyte_cost += row.megabyte_cost * quantity
            db(db.budget_kit.id == kit).update(total_unit_cost=total_unit_cost, total_monthly_cost=total_monthly_cost, total_minute_cost=total_minute_cost, total_megabyte_cost=total_megabyte_cost)
            s3_audit("update", module, "kit", record=kit, representation="html")


        def kit_total(form):
            "Calculate Totals for the Kit specified by Form"
            if "kit_id" in form.vars:
                # called by kit_item()
                kit = form.vars.kit_id
            else:
                # called by kit()
                kit = form.vars.id
            kit_totals(kit)

        s3mgr.configure(tablename,
                        onaccept=kit_total)

        # Kit<>Item Many2Many
        resourcename = "kit_item"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("kit_id", db.budget_kit),
                                Field("item_id", db.budget_item, ondelete="RESTRICT"),
                                Field("quantity", "integer", default=1, notnull=True),

                                *(s3_timestamp() + s3_uid() + s3_deletion_status()))

        table.kit_id.requires = IS_ONE_OF(db, "budget_kit.id", "%(code)s")
        table.item_id.requires = IS_ONE_OF(db, "budget_item.id", "%(description)s")
        table.quantity.requires = IS_NOT_EMPTY()

        # Bundles
        resourcename = "bundle"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("name", length=128, notnull=True, unique=True),
                                Field("description"),
                                Field("total_unit_cost", "double", writable=False),
                                Field("total_monthly_cost", "double", writable=False),
                                s3_comments(),

                                *(s3_timestamp() + s3_uid() + s3_deletion_status()))

        table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % table)]

        def bundle_totals(bundle):
            "Calculate Totals for a Bundle"
            total_unit_cost = 0
            total_monthly_cost = 0

            table = db.budget_bundle_kit
            query = (table.bundle_id == bundle)
            kits = db(query).select()
            for kit in kits:
                query = (table.bundle_id == bundle) & (table.kit_id == kit.kit_id)
                row = db(query).select(table.quantity, table.minutes, table.megabytes, limitby=(0, 1)).first()
                quantity = row.quantity
                row2 = db(db.budget_kit.id == kit.kit_id).select(db.budget_kit.total_unit_cost, db.budget_kit.total_monthly_cost, db.budget_kit.total_minute_cost, db.budget_kit.total_megabyte_cost, limitby=(0, 1)).first()
                total_unit_cost += row2.total_unit_cost * quantity
                total_monthly_cost += row2.total_monthly_cost * quantity
                total_monthly_cost += row2.total_minute_cost * quantity * row.minutes
                total_monthly_cost += row2.total_megabyte_cost * quantity * row.megabytes

            table = db.budget_bundle_item
            query = (table.bundle_id == bundle)
            items = db(query).select()
            for item in items:
                query = (table.bundle_id == bundle) & (table.item_id == item.item_id)
                row = db(query).select(table.quantity, table.minutes, table.megabytes, limitby=(0, 1)).first()
                quantity = row.quantity
                row2 = db(db.budget_item.id == item.item_id).select(db.budget_item.unit_cost, db.budget_item.monthly_cost, db.budget_item.minute_cost, db.budget_item.megabyte_cost, limitby=(0, 1)).first()
                total_unit_cost += row2.unit_cost * quantity
                total_monthly_cost += row2.monthly_cost * quantity
                total_monthly_cost += row2.minute_cost * quantity * row.minutes
                total_monthly_cost += row2.megabyte_cost * quantity * row.megabytes

            db(db.budget_bundle.id == bundle).update(total_unit_cost=total_unit_cost, total_monthly_cost=total_monthly_cost)
            s3_audit("update", module, "bundle", record=bundle, representation="html")


        def bundle_total(form):
            "Calculate Totals for the Bundle specified by Form"
            if "bundle_id" in form.vars:
                # called by bundle_kit_item()
                bundle = form.vars.bundle_id
            else:
                # called by bundle()
                bundle = form.vars.id
            bundle_totals(bundle)

        s3mgr.configure(tablename,
                        onaccept=bundle_total)

        # Bundle<>Kit Many2Many
        resourcename = "bundle_kit"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("bundle_id", db.budget_bundle),
                                Field("kit_id", db.budget_kit, ondelete="RESTRICT"),
                                Field("quantity", "integer", default=1, notnull=True),
                                Field("minutes", "integer", default=0, notnull=True),
                                Field("megabytes", "integer", default=0, notnull=True),

                                *(s3_timestamp() + s3_deletion_status()))

        table.bundle_id.requires = IS_ONE_OF(db, "budget_bundle.id", "%(description)s")
        table.kit_id.requires = IS_ONE_OF(db, "budget_kit.id", "%(code)s")
        table.quantity.requires = IS_NOT_EMPTY()
        table.minutes.requires = IS_NOT_EMPTY()
        table.megabytes.requires = IS_NOT_EMPTY()

        # Bundle<>Item Many2Many
        resourcename = "bundle_item"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("bundle_id", db.budget_bundle),
                                Field("item_id", db.budget_item, ondelete="RESTRICT"),
                                Field("quantity", "integer", default=1, notnull=True),
                                Field("minutes", "integer", default=0, notnull=True),
                                Field("megabytes", "integer", default=0, notnull=True),

                                *(s3_timestamp() + s3_deletion_status()))

        table.bundle_id.requires = IS_ONE_OF(db, "budget_bundle.id", "%(description)s")
        table.item_id.requires = IS_ONE_OF(db, "budget_item.id", "%(description)s")
        table.quantity.requires = IS_NOT_EMPTY()
        table.minutes.requires = IS_NOT_EMPTY()
        table.megabytes.requires = IS_NOT_EMPTY()

        # Staff Types
        resourcename = "staff"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("name", length=128, notnull=True, unique=True),
                                Field("grade", notnull=True),
                                Field("salary", "integer", notnull=True),
                                currency_type(),
                                Field("travel", "integer", default=0),
                                # Shouldn't be grade-dependent, but purely location-dependent
                                #Field("subsistence", "double", default=0.00),
                                # Location-dependent
                                #Field("hazard_pay", "double", default=0.00),
                                s3_comments(),

                                *(s3_timestamp() + s3_uid() + s3_deletion_status()))

        table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % table)]
        table.grade.requires = IS_NOT_EMPTY()
        table.salary.requires = IS_NOT_EMPTY()

        # Locations
        resourcename = "location"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("code", length=3, notnull=True, unique=True),
                                Field("description"),
                                Field("subsistence", "double", default=0.00),
                                Field("hazard_pay", "double", default=0.00),
                                s3_comments(),

                                *(s3_timestamp() + s3_uid() + s3_deletion_status()))

        table.code.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.code" % table)]

        # Budgets
        resourcename = "budget"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("name", length=128, notnull=True, unique=True),
                                Field("description"),
                                Field("total_onetime_costs", "double", writable=False),
                                Field("total_recurring_costs", "double", writable=False),
                                s3_comments(),

                                *(s3_timestamp() + s3_uid() + s3_deletion_status()))

        table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % table)]

        # Budget<>Bundle Many2Many
        resourcename = "budget_bundle"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("budget_id", db.budget_budget),
                                project_id(),
                                Field("location_id", db.budget_location),
                                Field("bundle_id", db.budget_bundle, ondelete="RESTRICT"),
                                Field("quantity", "integer", default=1, notnull=True),
                                Field("months", "integer", default=3, notnull=True),

                                *(s3_timestamp() + s3_deletion_status()))

        table.budget_id.requires = IS_ONE_OF(db, "budget_budget.id", "%(name)s")
        table.location_id.requires = IS_ONE_OF(db, "budget_location.id", "%(code)s")
        table.bundle_id.requires = IS_ONE_OF(db, "budget_bundle.id", "%(name)s")
        table.quantity.requires = IS_NOT_EMPTY()
        table.months.requires = IS_NOT_EMPTY()

        # Budget<>Staff Many2Many
        resourcename = "budget_staff"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("budget_id", db.budget_budget),
                                project_id(),
                                Field("location_id", db.budget_location),
                                Field("staff_id", db.budget_staff, ondelete="RESTRICT"),
                                Field("quantity", "integer", default=1, notnull=True),
                                Field("months", "integer", default=3, notnull=True),

                                *(s3_timestamp() + s3_deletion_status()))

        table.budget_id.requires = IS_ONE_OF(db, "budget_budget.id", "%(name)s")
        table.location_id.requires = IS_ONE_OF(db, "budget_location.id", "%(code)s")
        table.staff_id.requires = IS_ONE_OF(db, "budget_staff.id", "%(name)s")
        table.quantity.requires = IS_NOT_EMPTY()
        table.months.requires = IS_NOT_EMPTY()

    # Provide a handle to this load function
    s3mgr.loader(budget_tables,
                 "budget_budget")

# END =========================================================================
