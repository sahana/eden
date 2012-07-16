# -*- coding: utf-8 -*-

"""
    Budgetting module

    NB Depends on Project Tracking module

    @ToDo: Rewrite to use Inventory for Items
    @ToDo: Rewrite to use HRM for Staff
    @ToDo: Rewrite to remove the dependency on Geraldo
           - Items easy
           - Kits harder
"""

module = request.controller
resourcename = request.function

# NB Requires 'project' module too
if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
# Define the Model
# @ToDo: Move to modules/eden/budget.py
# - here it isn't visible to s3db.load_all_models() or Sync
# -----------------------------------------------------------------------------
# Load the models we depend on
project_id = s3db.project_project_id

s3_deletion_status = s3base.s3_deletion_status
s3_timestamp = s3base.s3_timestamp
s3_uid = s3base.s3_uid

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

s3db.configure(tablename,
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

s3db.configure(tablename,
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

s3db.configure(tablename,
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
                        s3base.s3_currency(),
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

# Options used in multiple functions
# @ToDo: integrate into db.define_table()
table = db.budget_item
table.code.label = T("Code")
table.description.label = T("Description")
table.unit_cost.label = T("Unit Cost")
table.monthly_cost.label = T("Monthly Cost")
table.minute_cost.label = T("Cost per Minute")
table.megabyte_cost.label = T("Cost per Megabyte")
table.comments.label = T("Comments")

table = db.budget_kit
table.code.label = T("Code")
table.description.label = T("Description")
table.total_unit_cost.label = T("Total Unit Cost")
table.total_monthly_cost.label = T("Total Monthly Cost")
table.total_minute_cost.label = T("Total Cost per Minute")
table.total_megabyte_cost.label = T("Total Cost per Megabyte")
table.comments.label = T("Comments")

table = db.budget_kit_item
table.kit_id.label = T("Kit")
table.kit_id.represent = lambda kit_id: \
    db(db.budget_kit.id == kit_id).select(db.budget_kit.code,
                                          limitby=(0, 1)).first().code
table.item_id.label = T("Item")
table.item_id.represent = lambda item_id: \
    db(db.budget_item.id == item_id).select(db.budget_item.description,
                                            limitby=(0, 1)).first().description
table.quantity.label = T("Quantity")

table = db.budget_bundle
table.name.label = T("Name")
table.description.label = T("Description")
table.total_unit_cost.label = T("One time cost")
table.total_monthly_cost.label = T("Recurring cost")
table.comments.label = T("Comments")

table = db.budget_bundle_kit
table.bundle_id.label = T("Bundle")
table.bundle_id.represent = lambda bundle_id: \
    db(db.budget_bundle.id == bundle_id).select(db.budget_bundle.description,
                                                limitby=(0, 1)).first().description
table.kit_id.label = T("Kit")
table.kit_id.represent = lambda kit_id: \
    db(db.budget_kit.id == kit_id).select(db.budget_kit.code,
                                          limitby=(0, 1)).first().code
table.quantity.label = T("Quantity")
table.minutes.label = T("Minutes per Month")
table.megabytes.label = T("Megabytes per Month")

table = db.budget_bundle_item
table.bundle_id.label = T("Bundle")
table.bundle_id.represent = lambda bundle_id: \
    db(db.budget_bundle.id == bundle_id).select(db.budget_bundle.description,
                                                limitby=(0, 1)).first().description
table.item_id.label = T("Item")
table.item_id.represent = lambda item_id: \
    db(db.budget_item.id == item_id).select(db.budget_item.description,
                                            limitby=(0, 1)).first().description
table.quantity.label = T("Quantity")
table.minutes.label = T("Minutes per Month")
table.megabytes.label = T("Megabytes per Month")

table = db.budget_staff
table.name.label = T("Name")
table.grade.label = T("Grade")
table.salary.label = T("Monthly Salary")
table.travel.label = T("Travel Cost")
table.comments.label = T("Comments")

table = db.budget_location
table.code.label = T("Code")
table.description.label = T("Description")
table.subsistence.label = T("Subsistence Cost")
# UN terminology
#table.subsistence.label = "DSA"
table.hazard_pay.label = T("Hazard Pay")
table.comments.label = T("Comments")

#table = db.budget_project
#table.code.label = T("Code")
#table.title.label = T("Title")
#table.comments.label = T("Comments")

table = db.budget_budget
table.name.label = T("Name")
table.description.label = T("Description")
table.total_onetime_costs.label = T("Total One-time Costs")
table.total_recurring_costs.label = T("Total Recurring Costs")
table.comments.label = T("Comments")

table = db.budget_budget_bundle
table.budget_id.label = T("Budget")
table.budget_id.represent = lambda budget_id: \
    db(db.budget_budget.id == budget_id).select(db.budget_budget.name,
                                                limitby=(0, 1)).first().name
#table.project_id.label = T("Project")
#table.project_id.represent = lambda project_id: db(db.budget_project.id == project_id).select(db.budget_project.code, limitby=(0, 1)).first().code
table.location_id.label = T("Location")
table.location_id.represent = lambda location_id: \
    db(db.budget_location.id == location_id).select(db.budget_location.code,
                                                    limitby=(0, 1)).first().code
table.bundle_id.label = T("Bundle")
table.bundle_id.represent = lambda bundle_id: \
    db(db.budget_bundle.id == bundle_id).select(db.budget_bundle.name,
                                                limitby=(0, 1)).first().name
table.quantity.label = T("Quantity")
table.months.label = T("Months")

table = db.budget_budget_staff
table.budget_id.label = T("Budget")
table.budget_id.represent = lambda budget_id: \
    db(db.budget_budget.id == budget_id).select(db.budget_budget.name,
                                                limitby=(0, 1)).first().name
#table.project_id.label = T("Project")
#table.project_id.represent = lambda project_id: db(db.budget_project.id == project_id).select(db.budget_project.code, limitby=(0, 1)).first().code
table.location_id.label = T("Location")
table.location_id.represent = lambda location_id: \
    db(db.budget_location.id == location_id).select(db.budget_location.code,
                                                    limitby=(0, 1)).first().code
table.staff_id.label = T("Staff")
table.staff_id.represent = lambda bundle_id: \
    db(db.budget_staff.id == staff_id).select(db.budget_staff.description,
                                              limitby=(0, 1)).first().description
table.quantity.label = T("Quantity")
table.months.label = T("Months")

# -----------------------------------------------------------------------------
# Controllers
# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

def parameters():
    """ Select which page to go to depending on login status """
    table = db.budget_parameter
    authorised = s3_has_permission("update", table)
    if authorised:
        redirect (URL(f="parameter", args=[1, "update"]))
    else:
        redirect (URL(f="parameter", args=[1, "read"]))

def parameter():
    """ RESTful CRUD controller """
    tablename = "budget_parameter"
    table = db[tablename]

    # Model Options
    table.shipping.label = "Shipping cost"
    table.logistics.label = "Procurement & Logistics cost"
    table.admin.label = "Administrative support cost"
    table.indirect.label = "Indirect support cost HQ"

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_update = T("Edit Parameters"),
        title_display = T("Parameters"))

    s3db.configure(tablename, deletable=False)
    return s3_rest_controller()

def item():
    """ RESTful CRUD controller """
    tablename = "budget_item"
    table = db[tablename]

    # Model options used in multiple controllers so defined at the top of the file

    # CRUD Strings
    ADD_ITEM = T("Add Item")
    s3.crud_strings[tablename] = Storage(
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
        msg_list_empty = T("No Items currently registered"))

    response.s3.formats.pdf = URL(f="item_export_pdf")

    s3db.configure(tablename,
                    main="code",
                    extra="description",
                    orderby=db.budget_item.category_type)

    return s3_rest_controller()

def item_export_pdf():
    """
        Export a list of Items in Adobe PDF format
        Uses Geraldo Grouping Report
        @ToDo: Use S3PDF Method
    """
    try:
        from reportlab.lib.units import cm
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    except ImportError:
        session.error = REPORTLAB_ERROR
        redirect(URL(c="item"))
    try:
        from geraldo import Report, ReportBand, ReportGroup, Label, ObjectValue, SystemField, landscape, BAND_WIDTH
        from geraldo.generators import PDFGenerator
    except ImportError:
        session.error = GERALDO_ERROR
        redirect(URL(c="item"))

    table = db.budget_item
    objects_list = db(table.id > 0).select(orderby=table.category_type)
    if not objects_list:
        session.warning = T("No data in this table - cannot create PDF!")
        redirect(URL(f="item"))

    import cStringIO
    output = cStringIO.StringIO()

    class MyReport(Report):
        def __init__(self, queryset=None, T=None):
            " Initialise parent class & make any necessary modifications "
            Report.__init__(self, queryset)
            self.T = T
        def _T(self, rawstring):
            return self.T(rawstring)
        # can't use T() here!
        #title = _T("Items")
        title = "Items"
        page_size = landscape(A4)
        class band_page_header(ReportBand):
            height = 1.3*cm
            elements = [
                SystemField(expression="%(report_title)s", top=0.1*cm,
                    left=0, width=BAND_WIDTH, style={"fontName": "Helvetica-Bold",
                    "fontSize": 14, "alignment": TA_CENTER}
                    ),
                Label(text="Code", top=0.8*cm, left=0.2*cm),
                Label(text="Description", top=0.8*cm, left=3*cm),
                Label(text="Unit Cost", top=0.8*cm, left=13*cm),
                Label(text="per Month", top=0.8*cm, left=15*cm),
                Label(text="per Minute", top=0.8*cm, left=17*cm),
                Label(text="per Megabyte", top=0.8*cm, left=19*cm),
                Label(text="Comments", top=0.8*cm, left=21*cm),
            ]
            borders = {"bottom": True}
        class band_page_footer(ReportBand):
            height = 0.5*cm
            elements = [
                Label(text="%s" % request.utcnow.date(), top=0.1*cm, left=0),
                SystemField(expression="Page # %(page_number)d of %(page_count)d", top=0.1*cm,
                    width=BAND_WIDTH, style={"alignment": TA_RIGHT}),
            ]
            borders = {"top": True}
        class band_detail(ReportBand):
            height = 0.5*cm
            auto_expand_height = True
            elements = (
                    ObjectValue(attribute_name="code", left=0.2*cm, width=2.8*cm),
                    ObjectValue(attribute_name="description", left=3*cm, width=10*cm),
                    ObjectValue(attribute_name="unit_cost", left=13*cm, width=2*cm),
                    ObjectValue(attribute_name="monthly_cost", left=15*cm, width=2*cm),
                    ObjectValue(attribute_name="minute_cost", left=17*cm, width=2*cm),
                    ObjectValue(attribute_name="megabyte_cost", left=19*cm, width=2*cm),
                    ObjectValue(attribute_name="comments", left=21*cm, width=6*cm),
                    )
        groups = [
        ReportGroup(attribute_name="category_type",
            band_header=ReportBand(
                height=0.7*cm,
                elements=[
                    ObjectValue(attribute_name="category_type", left=0, top=0.1*cm,
                        get_value=lambda instance: instance.category_type and budget_category_type_opts[instance.category_type],
                        style={"fontName": "Helvetica-Bold", "fontSize": 12})
                ],
                borders={"bottom": True},
            ),
        ),
    ]

    #report = MyReport(queryset=objects_list)
    report = MyReport(queryset=objects_list, T=T)
    report.generate_by(PDFGenerator, filename=output)

    output.seek(0)
    import gluon.contenttype
    response.headers["Content-Type"] = gluon.contenttype.contenttype(".pdf")
    filename = "%s_items.pdf" % (request.env.server_name)
    response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
    return output.read()

def kit():
    """ RESTful CRUD controller """
    tablename = "budget_kit"
    table = db[tablename]

    # Model options used in multiple controllers so defined at the top of the file

    # CRUD Strings
    ADD_KIT = T("Add Kit")
    s3.crud_strings[tablename] = Storage(
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
        msg_list_empty = T("No Kits currently registered"))

    response.s3.formats.pdf = URL(f="kit_export_pdf")
    response.s3.formats.xls = URL(f="kit_export_xls")
    if len(request.args) == 2:
        s3db.configure(tablename,
            update_next=URL(f="kit_item", args=request.args[1]))

    return s3_rest_controller(main="code")

def kit_item():
    """ Many to Many CRUD Controller """
    format = request.vars.get("format", None)
    if format:
        if format == "xls":
            redirect(URL(f="kit_export_xls"))
        elif format == "pdf":
            redirect(URL(f="kit_export_pdf"))
        elif format == "csv":
            if request.args[0]:
                if str.lower(request.args[0]) == "create":
                    return kit_import_csv()
                else:
                    session.error = BADMETHOD
                    redirect(URL(r=request))
            else:
                # List
                redirect(URL(f="kit_export_csv"))
        else:
            session.error = BADFORMAT
            redirect(URL(r=request))

    try:
        kit = int(request.args[0])
    except TypeError, ValueError:
        session.error = T("Need to specify a Kit!")
        redirect(URL(f="kit"))

    table = db.budget_kit_item
    authorised = s3_has_permission("update", table)

    _kit = db.budget_kit[kit]
    title = _kit.code
    kit_description = _kit.description
    kit_total_cost = _kit.total_unit_cost
    kit_monthly_cost = _kit.total_monthly_cost
    query = (table.kit_id == kit)
    # Start building the Return with the common items
    output = dict(title=title, description=kit_description, total_cost=kit_total_cost, monthly_cost=kit_monthly_cost)
    # Audit
    s3_audit("list", module, "kit_item", record=kit, representation="html")
    item_list = []
    sqlrows = db(query).select()
    even = True
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: s3_audit("create", module, "kit_item",
                                                              form=form,
                                                              representation="html")
        # Display a List_Create page with editable Quantities
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.item_id
            _item = db.budget_item[id]
            description = _item.description
            id_link = A(id, _href=URL(f="item", args=[id, "read"]))
            quantity_box = INPUT(_value=row.quantity, _size=4, _name="qty" + str(id))
            unit_cost = _item.unit_cost
            monthly_cost = _item.monthly_cost
            minute_cost = _item.minute_cost
            megabyte_cost = _item.megabyte_cost
            total_units = unit_cost * row.quantity
            total_monthly = monthly_cost * row.quantity
            checkbox = INPUT(_type="checkbox", _value="on", _name=id, _class="remove_item")
            item_list.append(TR(TD(id_link), TD(description, _align="left"), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(minute_cost), TD(megabyte_cost), TD(total_units), TD(total_monthly), TD(checkbox, _align="center"), _class=theclass, _align="right"))

        table_header = THEAD(TR(TH("ID"), TH(table.item_id.label), TH(table.quantity.label), TH(db.budget_item.unit_cost.label), TH(db.budget_item.monthly_cost.label), TH(db.budget_item.minute_cost.label), TH(db.budget_item.megabyte_cost.label), TH(T("Total Units")), TH(T("Total Monthly")), TH(T("Remove"))))
        table_footer = TFOOT(TR(TD(B(T("Totals for Kit:")), _colspan=7), TD(B(kit_total_cost)), TD(B(kit_monthly_cost)), TD(INPUT(_id="submit_button", _type="submit", _value=T("Update")))), _align="right")
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name="custom", _method="post", _enctype="multipart/form-data", _action=URL(f="kit_update_items", args=[kit])))
        subtitle = T("Contents")

        crud.messages.submit_button = T("Add")
        # Check for duplicates before Item is added to DB
        crud.settings.create_onvalidation = kit_dupes
        # Calculate Totals for the Kit after Item is added to DB
        crud.settings.create_onaccept = kit_total
        crud.messages.record_created = T("Kit Updated")
        form = crud.create(table, next=URL(args=[kit]))
        addtitle = T("Add New Item to Kit")
        response.view = "%s/kit_item_list_create.html" % module
        output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form=form, kit=kit))
    else:
        # Display a simple List page
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.item_id
            _item = db.budget_item[id]
            description = _item.description
            id_link = A(id, _href=URL(f="item", args=[id, "read"]))
            quantity_box = row.quantity
            unit_cost = _item.unit_cost
            monthly_cost = _item.monthly_cost
            minute_cost = _item.minute_cost
            megabyte_cost = _item.megabyte_cost
            total_units = unit_cost * row.quantity
            total_monthly = monthly_cost * row.quantity
            item_list.append(TR(TD(id_link), TD(description, _align="left"), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(minute_cost), TD(megabyte_cost), TD(total_units), TD(total_monthly), _class=theclass, _align="right"))

        table_header = THEAD(TR(TH("ID"), TH(table.item_id.label), TH(table.quantity.label), TH(db.budget_item.unit_cost.label), TH(db.budget_item.monthly_cost.label), TH(db.budget_item.minute_cost.label), TH(db.budget_item.megabyte_cost.label), TH(T("Total Units")), TH(T("Total Monthly"))))
        table_footer = TFOOT(TR(TD(B(T("Totals for Kit:")), _colspan=7), TD(B(kit_total_cost)), TD(B(kit_monthly_cost)), _align="right"))
        items = DIV(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"))
        add_btn = A(T("Edit Contents"), _href=URL(c="default", f="user", args="login"), _class="action-btn")
        response.view = "%s/kit_item_list.html" % module
        output.update(dict(items=items, add_btn=add_btn))
    return output

def kit_dupes(form):
    """ Checks for duplicate Item before adding to DB """
    kit = form.vars.kit_id
    item = form.vars.item_id
    table = db.budget_kit_item
    query = (table.kit_id == kit) & (table.item_id == item)
    items = db(query).select()
    if items:
        session.error = T("Item already in Kit!")
        redirect(URL(args=kit))
    else:
        return

def kit_update_items():
    """ Update a Kit's items (Quantity & Delete) """

    try:
        kit = int(request.args[0])
    except TypeError, ValueError:
        session.error = T("Need to specify a Kit!")
        redirect(URL(f="kit"))

    table = db.budget_kit_item
    authorised = s3_has_permission("update", table)
    if authorised:
        for var in request.vars:
            if "qty" in var:
                item = var[3:]
                quantity = request.vars[var]
                query = (table.kit_id == kit) & (table.item_id == item)
                db(query).update(quantity=quantity)
            else:
                # Delete
                item = var
                query = (table.kit_id == kit) & (table.item_id == item)
                db(query).delete()
        # Update the Total values
        kit_totals(kit)
        # Audit
        s3_audit("update", module, "kit_item", record=kit, representation="html")
        session.flash = T("Kit updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(f="kit_item", args=[kit]))

def kit_export_xls():
    """
        Export a list of Kits in Excel XLS format
        Sheet 1 is a list of Kits
        Then there is a separate sheet per kit, listing it's component items
    """
    try:
        import xlwt
    except ImportError:
        session.error = XLWT_ERROR
        redirect(URL(c="kit"))

    import cStringIO
    output = cStringIO.StringIO()

    book = xlwt.Workbook()
    # List of Kits
    sheet1 = book.add_sheet("Kits")
    # Header row for Kits sheet
    row0 = sheet1.row(0)
    cell = 0
    table = db.budget_kit
    kits = db(table.id > 0).select()
    fields = [table[f] for f in table.fields if table[f].readable]
    for field in fields:
        row0.write(cell, field.label, xlwt.easyxf("font: bold True;"))
        cell += 1

    # For Header row on Items sheets
    table = db.budget_item
    fields_items = [table[f] for f in table.fields if table[f].readable]

    row = 1
    for kit in kits:
        # The Kit details on Sheet 1
        rowx = sheet1.row(row)
        row += 1
        cell1 = 0
        for field in fields:
            tab, col = str(field).split(".")
            rowx.write(cell1, kit[col])
            cell1 += 1
        # Sheet per Kit detailing constituent Items
        # Replace characters which are illegal in sheetnames
        sheetname = kit.code.replace("/","_")
        sheet = book.add_sheet(sheetname)
        # Header row for Items sheet
        row0 = sheet.row(0)
        cell = 0
        for field_item in fields_items:
            row0.write(cell, field_item.label, xlwt.easyxf("font: bold True;"))
            cell += 1
        # List Items in each Kit
        table = db.budget_kit_item
        contents = db(table.kit_id == kit.id).select()
        rowy = 1
        for content in contents:
            table = db.budget_item
            item = db(table.id == content.item_id).select().first()
            rowx = sheet.row(rowy)
            rowy += 1
            cell = 0
            for field_item in fields_items:
                tab, col = str(field_item).split(".")
                # Do lookups for option fields
                if col == "cost_type":
                    opt = item[col]
                    value = str(budget_cost_type_opts[opt])
                elif col == "category_type":
                    opt = item[col]
                    value = str(budget_category_type_opts[opt])
                else:
                    value = item[col]
                rowx.write(cell, value)
                cell += 1

    book.save(output)

    output.seek(0)
    import gluon.contenttype
    response.headers["Content-Type"] = gluon.contenttype.contenttype(".xls")
    filename = "%s_kits.xls" % (request.env.server_name)
    response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
    return output.read()

def kit_export_pdf():
    """
        Export a list of Kits in Adobe PDF format
        Uses Geraldo SubReport
        @ToDo: Use S3PDF Method
    """
    try:
        from reportlab.lib.units import cm
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    except ImportError:
        session.error = REPORTLAB_ERROR
        redirect(URL(c="kit"))
    try:
        from geraldo import Report, ReportBand, SubReport, Label, ObjectValue, SystemField, landscape, BAND_WIDTH
        from geraldo.generators import PDFGenerator
    except ImportError:
        session.error = GERALDO_ERROR
        redirect(URL(c="kit"))

    table = db.budget_kit
    objects_list = db(table.id > 0).select()
    if not objects_list:
        session.warning = T("No data in this table - cannot create PDF!")
        redirect(URL(r=request))

    import cStringIO
    output = cStringIO.StringIO()

    #class MySubReport(SubReport):
    #    def __init__(self, db=None, **kwargs):
    #        " Initialise parent class & make any necessary modifications "
    #        self.db = db
    #        SubReport.__init__(self, **kwargs)

    class MyReport(Report):
        def __init__(self, queryset=None, db=None):
            " Initialise parent class & make any necessary modifications "
            Report.__init__(self, queryset)
            self.db = db
        # can't use T() here!
        title = "Kits"
        page_size = landscape(A4)
        class band_page_header(ReportBand):
            height = 1.3*cm
            elements = [
                SystemField(expression="%(report_title)s", top=0.1*cm,
                    left=0, width=BAND_WIDTH, style={"fontName": "Helvetica-Bold",
                    "fontSize": 14, "alignment": TA_CENTER}
                    ),
                Label(text="Code", top=0.8*cm, left=0.2*cm),
                Label(text="Description", top=0.8*cm, left=2*cm),
                Label(text="Cost", top=0.8*cm, left=10*cm),
                Label(text="Monthly", top=0.8*cm, left=12*cm),
                Label(text="per Minute", top=0.8*cm, left=14*cm),
                Label(text="per Megabyte", top=0.8*cm, left=16*cm),
                Label(text="Comments", top=0.8*cm, left=18*cm),
            ]
            borders = {"bottom": True}
        class band_page_footer(ReportBand):
            height = 0.5*cm
            elements = [
                Label(text="%s" % request.utcnow.date(), top=0.1*cm, left=0),
                SystemField(expression="Page # %(page_number)d of %(page_count)d", top=0.1*cm,
                    width=BAND_WIDTH, style={"alignment": TA_RIGHT}),
            ]
            borders = {"top": True}
        class band_detail(ReportBand):
            height = 0.5*cm
            auto_expand_height = True
            elements = (
                    ObjectValue(attribute_name="code", left=0.2*cm, width=1.8*cm),
                    ObjectValue(attribute_name="description", left=2*cm, width=8*cm),
                    ObjectValue(attribute_name="total_unit_cost", left=10*cm, width=2*cm),
                    ObjectValue(attribute_name="total_monthly_cost", left=12*cm, width=2*cm),
                    ObjectValue(attribute_name="total_minute_cost", left=14*cm, width=2*cm),
                    ObjectValue(attribute_name="total_megabyte_cost", left=16*cm, width=2*cm),
                    ObjectValue(attribute_name="comments", left=18*cm, width=6*cm),
                    )
        subreports = [
            SubReport(
                #queryset_string = "db((db.budget_kit_item.kit_id == %(object)s.id) & (db.budget_item.id == db.budget_kit_item.item_id)).select(db.budget_item.code, db.budget_item.description, db.budget_item.unit_cost)",
                #queryset_string = "db(db.budget_kit_item.kit_id == %(object)s.id).select()",
                band_header = ReportBand(
                        height=0.5*cm,
                        elements=[
                            Label(text="Item ID", top=0, left=0.2*cm, style={"fontName": "Helvetica-Bold"}),
                            Label(text="Quantity", top=0, left=2*cm, style={"fontName": "Helvetica-Bold"}),
                            #Label(text="Unit Cost", top=0, left=4*cm, style={"fontName": "Helvetica-Bold"}),
                            ],
                        borders={"top": True, "left": True, "right": True},
                        ),
                detail_band = ReportBand(
                        height=0.5*cm,
                        elements=[
                            ObjectValue(attribute_name="item_id", top=0, left=0.2*cm),
                            ObjectValue(attribute_name="quantity", top=0, left=2*cm),
                            #ObjectValue(attribute_name="unit_cost", top=0, left=4*cm),
                            ]
                        ),
                ),
            ]


    #report = MyReport(queryset=objects_list)
    report = MyReport(queryset=objects_list, db=db)
    report.generate_by(PDFGenerator, filename=output)

    output.seek(0)
    import gluon.contenttype
    response.headers["Content-Type"] = gluon.contenttype.contenttype(".pdf")
    filename = "%s_kits.pdf" % (request.env.server_name)
    response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
    return output.read()

def kit_export_csv():
    """
        Export kits in CSV format
        Concatenates: kits, items & kit_item
    """
    output = ""

    for resourcename in ["kit", "item", "kit_item"]:
        _table = module + "_" + resourcename
        table = db[_table]
        # Filter Search list to just those records which user can read
        query = auth.s3_accessible_query("read", table)
        # Filter Search List to remove entries which have been deleted
        if "deleted" in table:
            query = ((table.deleted == False) | (table.deleted == None)) & query # includes None for backward compatability
        output += "TABLE " + _table + "\n"
        output += str(db(query).select())
        output += "\n\n"

    import gluon.contenttype
    response.headers["Content-Type"] = gluon.contenttype.contenttype(".csv")
    filename = "%s_kits.csv" % (request.env.server_name)
    response.headers["Content-disposition"] = "attachment; filename=%s" % filename
    return output

def budget_import_csv(file, table=None):
    """ Import CSV file into Database """

    if table:
        table.import_from_csv_file(file)
    else:
        # This is the preferred method as it updates reference fields
        db.import_from_csv_file(file)
        db.commit()

def kit_import_csv():
    """
        Import kits in CSV format
        Assumes concatenated: kits, items & kit_item
    """
    # Read in POST
    file = request.vars.filename.file
    try:
        # Assumes that it is a concatenation of tables
        budget_import_csv(file)
        session.flash = T("Data uploaded")
    except:
        session.error = T("Unable to parse CSV file!")
    redirect(URL(f="kit"))

def bundle():
    """ RESTful CRUD controller """
    tablename = "budget_bundle"
    table = db[tablename]

    # Model options used in multiple controllers so defined at the top of the file

    # CRUD Strings
    ADD_BUNDLE = T("Add Bundle")
    s3.crud_strings[tablename] = Storage(
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
        msg_list_empty = T("No Bundles currently registered"))

    if len(request.args) == 2:
        s3db.configure(tablename,
            update_next=URL(f="bundle_kit_item", args=request.args[1]))

    return s3_rest_controller()

def bundle_kit_item():
    """ Many to Many CRUD Controller """

    try:
        bundle = int(request.args[0])
    except TypeError, ValueError:
        session.error = T("Need to specify a bundle!")
        redirect(URL(f="bundle"))

    tables = [db.budget_bundle_kit, db.budget_bundle_item]
    authorised = s3_has_permission("update", tables[0]) and s3_has_permission("update", tables[1])

    _bundle = db.budget_bundle[bundle]
    title = _bundle.name
    bundle_description = _bundle.description
    bundle_total_cost = _bundle.total_unit_cost
    bundle_monthly_cost = _bundle.total_monthly_cost
    # Start building the Return with the common items
    output = dict(title=title, description=bundle_description, total_cost=bundle_total_cost, monthly_cost=bundle_monthly_cost)
    # Audit
    s3_audit("list", module, "bundle_kit_item", record=bundle, representation="html")
    item_list = []
    even = True
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: s3_audit(module, "bundle_kit_item",
                                                              form=form,
                                                              representation="html")
        # Display a List_Create page with editable Quantities, Minutes & Megabytes

        # Kits
        query = (tables[0].bundle_id == bundle)
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.kit_id
            _kit = db.budget_kit[id]
            description = _kit.description
            id_link = A(id, _href=URL(f="kit", args=[id, "read"]))
            quantity_box = INPUT(_value=row.quantity, _size=4, _name="kit_qty_" + str(id))
            minute_cost = _kit.total_minute_cost
            if minute_cost:
                minutes_box = INPUT(_value=row.minutes, _size=4, _name="kit_mins_" + str(id))
            else:
                minutes_box = INPUT(_value=0, _size=4, _name="kit_mins_" + str(id), _disabled="disabled")
            megabyte_cost = _kit.total_megabyte_cost
            if megabyte_cost:
                megabytes_box = INPUT(_value=row.megabytes, _size=4, _name="kit_mbytes_" + str(id))
            else:
                megabytes_box = INPUT(_value=0, _size=4, _name="kit_mbytes_" + str(id), _disabled="disabled")
            unit_cost = _kit.total_unit_cost
            monthly_cost = _kit.total_monthly_cost
            minute_cost = _kit.total_minute_cost
            megabyte_cost = _kit.total_megabyte_cost
            total_units = unit_cost * row.quantity
            total_monthly = monthly_cost * row.quantity
            checkbox = INPUT(_type="checkbox", _value="on", _name="kit_" + str(id), _class="remove_item")
            item_list.append(TR(TD(id_link), TD(description, _align="left"), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(minutes_box), TD(minute_cost), TD(megabytes_box), TD(megabyte_cost), TD(total_units), TD(total_monthly), TD(checkbox, _align="center"), _class=theclass, _align="right"))

        # Items
        query = tables[1].bundle_id == bundle
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.item_id
            _item = db.budget_item[id]
            description = _item.description
            id_link = A(id, _href=URL(f="item", args=[id, "read"]))
            quantity_box = INPUT(_value=row.quantity, _size=4, _name="item_qty_" + str(id))
            minute_cost = _item.minute_cost
            if minute_cost:
                minutes_box = INPUT(_value=row.minutes, _size=4, _name="item_mins_" + str(id))
            else:
                minutes_box = INPUT(_value=0, _size=4, _name="item_mins_" + str(id), _disabled="disabled")
            megabyte_cost = _item.megabyte_cost
            if megabyte_cost:
                megabytes_box = INPUT(_value=row.megabytes, _size=4, _name="item_mbytes_" + str(id))
            else:
                megabytes_box = INPUT(_value=0, _size=4, _name="item_mbytes_" + str(id), _disabled="disabled")
            unit_cost = _item.unit_cost
            monthly_cost = _item.monthly_cost
            minute_cost = _item.minute_cost
            megabyte_cost = _item.megabyte_cost
            total_units = unit_cost * row.quantity
            total_monthly = monthly_cost * row.quantity
            checkbox = INPUT(_type="checkbox", _value="on", _name="item_" + str(id), _class="remove_item")
            item_list.append(TR(TD(id_link), TD(description, _align="left"), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(minutes_box), TD(minute_cost), TD(megabytes_box), TD(megabyte_cost), TD(total_units), TD(total_monthly), TD(checkbox, _align="center"), _class=theclass, _align="right"))

        table_header = THEAD(TR(TH("ID"), TH(T("Description")), TH(tables[0].quantity.label), TH(db.budget_item.unit_cost.label), TH(db.budget_item.monthly_cost.label), TH(tables[0].minutes.label), TH(db.budget_item.minute_cost.label), TH(tables[0].megabytes.label), TH(db.budget_item.megabyte_cost.label), TH(T("Total Units")), TH(T("Total Monthly")), TH(T("Remove"))))
        table_footer = TFOOT(TR(TD(B(T("Totals for Bundle:")), _colspan=9), TD(B(bundle_total_cost)), TD(B(bundle_monthly_cost)), TD(INPUT(_id="submit_button", _type="submit", _value=T("Update")))), _align="right")
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name="custom", _method="post", _enctype="multipart/form-data", _action=URL(f="bundle_update_items", args=[bundle])))
        subtitle = T("Contents")

        crud.messages.submit_button = T("Add")
        # Check for duplicates before Item is added to DB
        crud.settings.create_onvalidation = bundle_dupes
        # Calculate Totals for the Bundle after Item is added to DB
        crud.settings.create_onaccept = bundle_total
        crud.messages.record_created = T("Bundle Updated")
        form1 = crud.create(tables[0], next=URL(args=[bundle]))
        form1[0][0].append(TR(TD(T("Type") + ":"), TD(LABEL(T("Kit"), INPUT(_type="radio", _name="kit_item1", _value="Kit", value="Kit")), LABEL(T("Item"), INPUT(_type="radio", _name="kit_item1", _value="Item", value="Kit")))))
        form2 = crud.create(tables[1], next=URL(args=[bundle]))
        form2[0][0].append(TR(TD(T("Type") + ":"), TD(LABEL(T("Kit"), INPUT(_type="radio", _name="kit_item2", _value="Kit", value="Item")), LABEL(T("Item"), INPUT(_type="radio", _name="kit_item2", _value="Item", value="Item")))))
        addtitle = T("Add to Bundle")
        response.view = "%s/bundle_kit_item_list_create.html" % module
        output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form1=form1, form2=form2, bundle=bundle))
    else:
        # Display a simple List page
        # Kits
        query = tables[0].bundle_id == bundle
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.kit_id
            _kit = db.budget_kit[id]
            description = _kit.description
            id_link = A(id, _href=URL(f="kit", args=[id, "read"]))
            quantity_box = INPUT(_value=row.quantity, _size=4, _name="kit_qty_" + str(id))
            minute_cost = _kit.total_minute_cost
            if minute_cost:
                minutes_box = INPUT(_value=row.minutes, _size=4, _name="kit_mins_" + str(id))
            else:
                minutes_box = INPUT(_value=0, _size=4, _name="kit_mins_" + str(id), _disabled="disabled")
            megabyte_cost = _kit.total_megabyte_cost
            if megabyte_cost:
                megabytes_box = INPUT(_value=row.megabytes, _size=4, _name="kit_mbytes_" + str(id))
            else:
                megabytes_box = INPUT(_value=0, _size=4, _name="kit_mbytes_" + str(id), _disabled="disabled")
            unit_cost = _kit.total_unit_cost
            monthly_cost = _kit.total_monthly_cost
            minute_cost = _kit.total_minute_cost
            megabyte_cost = _kit.total_megabyte_cost
            total_units = unit_cost * row.quantity
            total_monthly = monthly_cost * row.quantity
            checkbox = INPUT(_type="checkbox", _value="on", _name="kit_" + str(id), _class="remove_item")
            item_list.append(TR(TD(id_link), TD(description, _align="left"), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(minutes_box), TD(minute_cost), TD(megabytes_box), TD(megabyte_cost), TD(total_units), TD(total_monthly), _class=theclass, _align="right"))

        # Items
        query = tables[1].bundle_id == bundle
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.item_id
            _item = db.budget_item[id]
            description = _item.description
            id_link = A(id, _href=URL(f="item", args=[id, "read"]))
            quantity_box = row.quantity
            minute_cost = _item.minute_cost
            minutes_box = row.minutes
            megabyte_cost = _item.megabyte_cost
            megabytes_box = row.megabytes
            unit_cost = _item.unit_cost
            monthly_cost = _item.monthly_cost
            minute_cost = _item.minute_cost
            megabyte_cost = _item.megabyte_cost
            total_units = unit_cost * row.quantity
            total_monthly = monthly_cost * row.quantity
            item_list.append(TR(TD(id_link), TD(description, _align="left"), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(minutes_box), TD(minute_cost), TD(megabytes_box), TD(megabyte_cost), TD(total_units), TD(total_monthly), _class=theclass, _align="right"))

        table_header = THEAD(TR(TH("ID"), TH(T("Description")), TH(tables[0].quantity.label), TH(db.budget_item.unit_cost.label), TH(db.budget_item.monthly_cost.label), TH(tables[0].minutes.label), TH(db.budget_item.minute_cost.label), TH(tables[0].megabytes.label), TH(db.budget_item.megabyte_cost.label), TH(T("Total Units")), TH(T("Total Monthly"))))
        table_footer = TFOOT(TR(TD(B(T("Totals for Bundle:")), _colspan=9), TD(B(bundle_total_cost)), TD(B(bundle_monthly_cost))), _align="right")
        items = DIV(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"))

        add_btn = A(T("Edit Contents"), _href=URL(c="default", f="user", args="login"), _class="action-btn")
        response.view = "%s/bundle_kit_item_list.html" % module
        output.update(dict(items=items, add_btn=add_btn))
    return output

def bundle_dupes(form):
    """ Checks for duplicate Kit/Item before adding to DB """
    bundle = form.vars.bundle_id
    if "kit_id" in form.vars:
        kit = form.vars.kit_id
        table = db.budget_bundle_kit
        query = (table.bundle_id == bundle) & (table.kit_id==kit)
    elif "item_id" in form.vars:
        item = form.vars.item_id
        table = db.budget_bundle_item
        query = (table.bundle_id == bundle) & (table.item_id==item)
    else:
        # Something went wrong!
        return
    items = db(query).select()
    if items:
        session.error = T("Item already in Bundle!")
        redirect(URL(args=bundle))
    else:
        return

def bundle_update_items():
    """ Update a Bundle's items (Quantity, Minutes, Megabytes & Delete) """

    try:
        bundle = int(request.args[0])
    except TypeError, ValueError:
        session.error = T("Need to specify a bundle!")
        redirect(URL(f="bundle"))

    tables = [db.budget_bundle_kit, db.budget_bundle_item]
    authorised = s3_has_permission("update", tables[0]) and s3_has_permission("update", tables[1])
    if authorised:
        for var in request.vars:
            if "kit" in var:
                if "qty" in var:
                    kit = var[8:]
                    quantity = request.vars[var]
                    query = (tables[0].bundle_id == bundle) & (tables[0].kit_id == kit)
                    db(query).update(quantity=quantity)
                elif "mins" in var:
                    kit = var[9:]
                    minutes = request.vars[var]
                    query = (tables[0].bundle_id == bundle) & (tables[0].kit_id == kit)
                    db(query).update(minutes=minutes)
                elif "mbytes" in var:
                    kit = var[11:]
                    megabytes = request.vars[var]
                    query = (tables[0].bundle_id == bundle) & (tables[0].kit_id == kit)
                    db(query).update(megabytes=megabytes)
                else:
                    # Delete
                    kit = var[4:]
                    query = (tables[0].bundle_id == bundle) & (tables[0].kit_id == kit)
                    db(query).delete()
            if "item" in var:
                if "qty" in var:
                    item = var[9:]
                    quantity = request.vars[var]
                    query = (tables[1].bundle_id == bundle) & (tables[1].item_id == item)
                    db(query).update(quantity=quantity)
                elif "mins" in var:
                    item = var[10:]
                    minutes = request.vars[var]
                    query = (tables[1].bundle_id == bundle) & (tables[1].item_id == item)
                    db(query).update(minutes=minutes)
                elif "mbytes" in var:
                    item = var[12:]
                    megabytes = request.vars[var]
                    query = (tables[1].bundle_id == bundle) & (tables[1].item_id == item)
                    db(query).update(megabytes=megabytes)
                else:
                    # Delete
                    item = var[5:]
                    query = (tables[1].bundle_id == bundle) & (tables[1].item_id == item)
                    db(query).delete()
        # Update the Total values
        bundle_totals(bundle)
        # Audit
        s3_audit("update", module, "bundle_kit_item", record=bundle, representation="html")
        session.flash = T("Bundle updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(f="bundle_kit_item", args=[bundle]))

# This should be deprecated & replaced with a link to hrm_human_resource
def staff():
    """ RESTful CRUD controller """
    tablename = "budget_staff"
    #table = db[tablename]

    # Model options used in multiple controllers so defined at the top of the file

    # CRUD Strings
    ADD_STAFF_TYPE = T("Add Staff Type")
    s3.crud_strings[tablename] = Storage(
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
        msg_list_empty = T("No Staff Types currently registered"))

    return s3_rest_controller()

# This should be deprecated & replaced with a link to gis_location
def location():
    """ RESTful CRUD controller """
    tablename = "budget_location"
    #table = db[tablename]

    # Model options used in multiple controllers so defined at the top of the file

    # CRUD Strings
    ADD_LOCATION = T("Add Location")
    s3.crud_strings[tablename] = Storage(
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
        msg_list_empty = T("No Locations currently registered"))

    return s3_rest_controller(main="code")

def project():
    """ RESTful CRUD controller """

    #tablename = "project_%s" % (resourcename)
    #table = db[tablename]

    tabs = [(T("Basic Details"), None),
            (T("Staff"), "staff"),
            (T("Tasks"), "task"),
           #(T("Donors"), "organisation"),
           #(T("Facilities"), "site"),   # Ticket 195
           ]
    rheader = lambda r: response.s3.project_rheader(r, tabs=tabs)

    output = s3_rest_controller("project", resourcename,
                                rheader=rheader)

    return output


def budget():
    """ RESTful CRUD controller """
    tablename = "budget_budget"
    #table = db[tablename]

    # Model options used in multiple controllers so defined at the top of the file

    # CRUD Strings
    ADD_BUDGET = T("Add Budget")
    s3.crud_strings[tablename] = Storage(
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
        msg_list_empty = T("No Budgets currently registered"))

    return s3_rest_controller()

def budget_staff_bundle():
    """ Many to Many CRUD Controller """

    try:
        budget = int(request.args[0])
    except TypeError, ValueError:
        session.error = T("Need to specify a Budget!")
        redirect(URL(f="budget"))

    tables = [db.budget_budget_staff, db.budget_budget_bundle]
    authorised = s3_has_permission("update", tables[0]) and s3_has_permission("update", tables[1])

    _budget = db.budget_budget[budget]
    title = _budget.name
    budget_description = _budget.description
    budget_onetime_cost = _budget.total_onetime_costs
    budget_recurring_cost = _budget.total_recurring_costs
    # Start building the Return with the common items
    output = dict(title=title, description=budget_description, onetime_cost=budget_onetime_cost, recurring_cost=budget_recurring_cost)
    # Audit
    s3_audit("list", module, "budget_staff_bundle", record=budget, representation="html")
    item_list = []
    even = True
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: s3_audit("create", module, "budget_staff_bundle",
                                                              form=form,
                                                              representation="html")
        # Display a List_Create page with editable Quantities & Months

        # Staff
        query = tables[0].budget_id == budget
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.staff_id
            _staff = db.budget_staff[id]
            name = _staff.name
            id_link = A(name, _href=URL(f="staff", args=[id, "read"]))
            location = db.budget_location[row.location_id].code
            location_link = A(location, _href=URL(f="location", args=[row.location_id, "read"]))
            project = db.project_project[row.project_id].code
            project_link = A(project, _href=URL(c="org", f="project", args=[row.project_id, "read"]))
            description = _staff.comments
            quantity_box = INPUT(_value=row.quantity, _size=4, _name="staff_qty_" + str(id))
            months_box = INPUT(_value=row.months, _size=4, _name="staff_months_" + str(id))
            salary = _staff.salary
            travel = _staff.travel
            onetime = travel * row.quantity
            recurring = salary * row.quantity
            checkbox = INPUT(_type="checkbox", _value="on", _name="staff_" + str(id), _class="remove_item")
            item_list.append(TR(TD(location_link), TD(project_link), TD(id_link), TD(description, _align="left"), TD(quantity_box), TD(travel), TD(salary), TD(months_box), TD(onetime), TD(recurring), TD(checkbox, _align="center"), _class=theclass, _align="right"))

        # Bundles
        query = tables[1].budget_id==budget
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.bundle_id
            _bundle = db.budget_bundle[id]
            name = _bundle.name
            id_link = A(name, _href=URL(f="bundle", args=[id, "read"]))
            location = db.budget_location[row.location_id].code
            location_link = A(location, _href=URL(f="location", args=[row.location_id, "read"]))
            project = db.project_project[row.project_id].code
            project_link = A(project, _href=URL(c="org", f="project", args=[row.project_id, "read"]))
            description = _bundle.description
            quantity_box = INPUT(_value=row.quantity, _size=4, _name="bundle_qty_" + str(id))
            months_box = INPUT(_value=row.months, _size=4, _name="bundle_months_" + str(id))
            unit_cost = _bundle.total_unit_cost
            monthly_cost = _bundle.total_monthly_cost
            onetime = unit_cost * row.quantity
            recurring = monthly_cost * row.months
            checkbox = INPUT(_type="checkbox", _value="on", _name="bundle_" + str(id), _class="remove_item")
            item_list.append(TR(TD(location_link), TD(project_link), TD(id_link), TD(description, _align="left"), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(months_box), TD(onetime), TD(recurring), TD(checkbox, _align="center"), _class=theclass, _align="right"))

        table_header = THEAD(TR(TH("Location"), TH("Project"), TH("Item"), TH(T("Description")), TH(tables[0].quantity.label), TH(T("One-time costs")), TH(T("Recurring costs")), TH(tables[0].months.label), TH(db.budget_budget.total_onetime_costs.label), TH(db.budget_budget.total_recurring_costs.label), TH(T("Remove"))))
        table_footer = TFOOT(TR(TD(B(T("Totals for Budget:")), _colspan=8), TD(B(budget_onetime_cost)), TD(B(budget_recurring_cost)), TD(INPUT(_id="submit_button", _type="submit", _value=T("Update")))), _align="right")
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name="custom", _method="post", _enctype="multipart/form-data", _action=URL(f="budget_update_items", args=[budget])))
        subtitle = T("Contents")

        crud.messages.submit_button = T("Add")
        # Check for duplicates before Item is added to DB
        crud.settings.create_onvalidation = budget_dupes
        # Calculate Totals for the budget after Item is added to DB
        crud.settings.create_onaccept = budget_total
        crud.messages.record_created = T("Budget Updated")
        form1 = crud.create(tables[0], next=URL(args=[budget]))
        form1[0][0].append(TR(TD(T("Type") + ":"), TD(LABEL(T("Staff"), INPUT(_type="radio", _name="staff_bundle1", _value="Staff", value="Staff")), LABEL(T("Bundle"), INPUT(_type="radio", _name="staff_bundle1", _value="Bundle", value="Staff")))))
        form2 = crud.create(tables[1], next=URL(args=[budget]))
        form2[0][0].append(TR(TD(T("Type") + ":"), TD(LABEL(T("Staff"), INPUT(_type="radio", _name="staff_bundle2", _value="Staff", value="Bundle")), LABEL(T("Bundle"), INPUT(_type="radio", _name="staff_bundle2", _value="Bundle", value="Bundle")))))
        addtitle = T("Add to budget")
        response.view = "%s/budget_staff_bundle_list_create.html" % module
        output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form1=form1, form2=form2, budget=budget))
    else:
        # Display a simple List page
        # Staff
        query = tables[0].budget_id==budget
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.staff_id
            _staff = db.budget_staff[id]
            name = _staff.name
            id_link = A(name, _href=URL(f="staff", args=[id, "read"]))
            location = db.budget_location[row.location_id].code
            location_link = A(location, _href=URL(f="location", args=[row.location_id, "read"]))
            project = db.project_project[row.project_id].code
            project_link = A(project, _href=URL(c="org", f="project", args=[row.project_id, "read"]))
            description = _staff.comments
            quantity_box = INPUT(_value=row.quantity, _size=4, _name="staff_qty_" + str(id))
            months_box = INPUT(_value=row.months, _size=4, _name="staff_mins_" + str(id))
            salary = _staff.salary
            travel = _staff.travel
            onetime = travel * row.quantity
            recurring = salary * row.quantity
            checkbox = INPUT(_type="checkbox", _value="on", _name="staff_" + str(id), _class="remove_item")
            item_list.append(TR(TD(location_link), TD(project_link), TD(id_link), TD(description, _align="left"), TD(quantity_box), TD(travel), TD(salary), TD(months_box), TD(onetime), TD(recurring), _class=theclass, _align="right"))

        # Bundles
        query = tables[1].budget_id==budget
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.bundle_id
            _bundle = db.budget_bundle[id]
            name = _bundle.name
            id_link = A(name, _href=URL(f="bundle", args=[id, "read"]))
            location = db.budget_location[row.location_id].code
            location_link = A(location, _href=URL(f="location", args=[row.location_id, "read"]))
            project = db.project_project[row.project_id].code
            project_link = A(project, _href=URL(c="org", f="project", args=[row.project_id, "read"]))
            description = _bundle.description
            quantity_box = row.quantity
            months_box = row.months
            unit_cost = _bundle.total_unit_cost
            monthly_cost = _bundle.total_monthly_cost
            onetime = unit_cost * row.quantity
            recurring = monthly_cost * row.months
            item_list.append(TR(TD(location_link), TD(project_link), TD(id_link), TD(description, _align="left"), TD(quantity_box), TD(unit_cost), TD(monthly_cost), TD(months_box), TD(onetime), TD(recurring), _class=theclass, _align="right"))

        table_header = THEAD(TR(TH("Location"),
                                TH("Project"),
                                TH("Item"),
                                TH(T("Description")),
                                TH(tables[0].quantity.label),
                                TH(T("One-time costs")),
                                TH(T("Recurring costs")),
                                TH(tables[0].months.label),
                                TH(db.budget_budget.total_onetime_costs.label),
                                TH(db.budget_budget.total_recurring_costs.label)))
        table_footer = TFOOT(TR(TD(B(T("Totals for Budget:")), _colspan=8),
                                TD(B(budget_onetime_cost)),
                                TD(B(budget_recurring_cost))), _align="right")
        items = DIV(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"))

        add_btn = A(T("Edit Contents"), _href=URL(c="default", f="user", args="login"), _class="action-btn")
        response.view = "%s/budget_staff_bundle_list.html" % module
        output.update(dict(items=items, add_btn=add_btn))
    return output

def budget_dupes(form):
    """ Checks for duplicate staff/bundle before adding to DB """
    budget = form.vars.budget_id
    if "staff_id" in form.vars:
        staff = form.vars.staff_id
        table = db.budget_budget_staff
        query = (table.budget_id == budget) & (table.staff_id == staff)
    elif "bundle_id" in form.vars:
        bundle = form.vars.bundle_id
        table = db.budget_budget_bundle
        query = (table.budget_id == budget) & (table.bundle_id == bundle)
    else:
        # Something went wrong!
        return
    items = db(query).select()
    if items:
        session.error = T("Item already in budget!")
        redirect(URL(args=budget))
    else:
        return

def budget_total(form):
    """ Calculate Totals for the budget specified by Form """
    if "budget_id" in form.vars:
        # called by budget_staff_bundle()
        budget = form.vars.budget_id
    else:
        # called by budget()
        budget = form.vars.id
    budget_totals(budget)

def budget_totals(budget):
    """ Calculate Totals for a budget """
    total_onetime_cost = 0
    total_recurring_cost = 0

    table = db.budget_budget_staff
    query = (table.budget_id == budget)
    staffs = db(query).select()
    for staff in staffs:
        query = (table.budget_id == budget) & (table.staff_id == staff.staff_id)
        row = db(query).select(table.quantity, table.months, limitby=(0, 1)).first()
        quantity = row.quantity
        months = row.months
        row2 = db(db.budget_staff.id == staff.staff_id).select(db.budget_staff.travel, db.budget_staff.salary, limitby=(0, 1)).first()
        row3 = db(db.budget_location.id == staff.location_id).select(db.budget_location.subsistence, db.budget_location.hazard_pay, limitby=(0, 1)).first()
        total_onetime_cost += row2.travel * quantity
        total_recurring_cost += row2.salary * quantity * months
        total_recurring_cost += row3.subsistence * quantity * months
        total_recurring_cost += row3.hazard_pay * quantity * months

    table = db.budget_budget_bundle
    query = (table.budget_id == budget)
    bundles = db(query).select()
    for bundle in bundles:
        query = (table.budget_id == budget) & (table.bundle_id == bundle.bundle_id)
        row = db(query).select(table.quantity, table.months, limitby=(0, 1)).first()
        quantity = row.quantity
        months = row.months
        row2 = db(db.budget_bundle.id == bundle.bundle_id).select(db.budget_bundle.total_unit_cost, db.budget_bundle.total_monthly_cost, limitby=(0, 1)).first()
        total_onetime_cost += row2.total_unit_cost * quantity
        total_recurring_cost += row2.total_monthly_cost * quantity * months

    db(db.budget_budget.id == budget).update(total_onetime_costs=total_onetime_cost, total_recurring_costs=total_recurring_cost)
    s3_audit("update", module, "budget", record=budget, representation="html")


def budget_update_items():
    """ Update a Budget's items (Quantity, Months & Delete) """

    try:
        budget = int(request.args[0])
    except TypeError, ValueError:
        session.error = T("Need to specify a Budget!")
        redirect(URL(f="budget"))

    tables = [db.budget_budget_staff, db.budget_budget_bundle]
    authorised = s3_has_permission("update", tables[0]) and s3_has_permission("update", tables[1])
    if authorised:
        for var in request.vars:
            if "staff" in var:
                if "qty" in var:
                    staff = var[10:]
                    quantity = request.vars[var]
                    query = (tables[0].budget_id == budget) & (tables[0].staff_id == staff)
                    db(query).update(quantity=quantity)
                elif "months" in var:
                    staff = var[13:]
                    months = request.vars[var]
                    query = (tables[0].budget_id == budget) & (tables[0].staff_id == staff)
                    db(query).update(months=months)
                else:
                    # Delete
                    staff = var[6:]
                    query = (tables[0].budget_id == budget) & (tables[0].staff_id == staff)
                    db(query).delete()
            if "bundle" in var:
                if "qty" in var:
                    bundle = var[11:]
                    quantity = request.vars[var]
                    query = (tables[1].budget_id == budget) & (tables[1].bundle_id == bundle)
                    db(query).update(quantity=quantity)
                elif "months" in var:
                    bundle = var[14:]
                    months = request.vars[var]
                    query = (tables[1].budget_id == budget) & (tables[1].bundle_id == bundle)
                    db(query).update(months=months)
                else:
                    # Delete
                    bundle = var[7:]
                    query = (tables[1].budget_id == budget) & (tables[1].bundle_id == bundle)
                    db(query).delete()
        # Update the Total values
        budget_totals(budget)
        # Audit
        s3_audit("update", module, "staff_bundle", record=budget, representation="html")
        session.flash = T("Budget updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(f="budget_staff_bundle", args=[budget]))

# END =========================================================================

