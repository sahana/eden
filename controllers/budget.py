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

# NB Requires 'project' module too
if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# =============================================================================
def index():
    """ Module's Home Page """

    module_name = settings.modules[c].get("name_nice")
    response.title = module_name
    return {"module_name": module_name, 
            }

# =============================================================================
def budget():
    """ RESTful CRUD controller """

    def prep(r):
        if r.method == "timeplot" and \
           r.get_vars.get("component") == "allocation":
            # Disregard unterminated allocations (those without start date)
            query = (FS("allocation.start_date") != None)
            r.resource.add_component_filter("allocation", query)
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.budget_rheader)

# =============================================================================
def allocation():
    """
        REST controller for budget_allocation

        @status: experimental, not for production use
    """

    return s3_rest_controller()

# =============================================================================
def location():
    """
        REST controller for budget_location
    """

    # @todo: link to gis_location

    return s3_rest_controller(main = "code")

# =============================================================================
def item():
    """ REST controller for items """

    # @todo: link to supply items

    #s3.formats.pdf = URL(f="item_export_pdf")

    return s3_rest_controller()

# =============================================================================
def kit():
    """ REST controller for kits """

    #s3.formats.pdf = URL(f="kit_export_pdf")
    #s3.formats.xls = URL(f="kit_export_xls")

    if len(request.args) == 2:
        s3db.configure("budget_kit",
                       update_next=URL(f="kit_item", args=request.args[1]))

    return s3_rest_controller(main = "code",
                              rheader = s3db.budget_rheader,
                              )

# =============================================================================
def bundle():
    """ REST controller for bundles """

    if len(request.args) == 2:
        s3db.configure("budget_bundle",
            update_next=URL(f="bundle_kit_item", args=request.args[1]))

    return s3_rest_controller(rheader = s3db.budget_rheader)

# =============================================================================
def staff():
    """
        REST controller for budget_staff
    """

    # @todo: link to hrm_job_title (?)

    return s3_rest_controller()

# =============================================================================
def budget_staff():
    """
        REST controller to retrieve budget_budget_staff field options
    """

    s3.prep = lambda r: r.representation == "s3json"
    return s3_rest_controller()

# =============================================================================
def budget_bundle():
    """
        REST controller to retrieve budget_budget_bundle field options
    """

    s3.prep = lambda r: r.representation == "s3json"
    return s3_rest_controller()

# =============================================================================
def bundle_kit():
    """
        REST controller to retrieve budget_bundle_kit field options
    """

    s3.prep = lambda r: r.representation == "s3json"
    return s3_rest_controller()

# =============================================================================
def bundle_item():
    """
        REST controller to retrieve budget_bundle_item field options
    """

    s3.prep = lambda r: r.representation == "s3json"
    return s3_rest_controller()

# =============================================================================
def kit_item():
    """
        REST controller to retrieve budget_kit_item field options
    """

    s3.prep = lambda r: r.representation == "s3json"
    return s3_rest_controller()

# =============================================================================
def project():
    """ REST controller for projects """

    tabs = [(T("Basic Details"), None),
            (T("Staff"), "staff"),
            (T("Tasks"), "task"),
           #(T("Donors"), "organisation"),
           #(T("Facilities"), "site"),
           ]
    rheader = lambda r: s3db.project_rheader(r, tabs=tabs)

    output = s3_rest_controller("project", "project",
                                rheader = rheader,
                                )

    return output

# =============================================================================
def parameter():
    """
        REST controller for budget parameters
        - should always be 1 & only 1 record
    """

    s3db.configure("budget_parameter",
                   deletable = False,
                   )

    table = s3db.budget_parameter
    record = db().select(table.id,
                         limitby = (0, 1)
                         ).first()
    if not record:
        record_id = table.insert()
    else:
        record_id = record.id

    def postp(r, output):
        if isinstance(output, dict) and "buttons" in output:
            output["buttons"].pop("list_btn", None)
        return output
    s3.postp = postp

    from s3 import s3_request
    r = s3_request(args = [str(record_id)])
    return r()

# =============================================================================
def kit_export_xls():
    """
        Export a list of Kits in Excel XLS format
        Sheet 1 is a list of Kits
        Then there is a separate sheet per kit, listing it's component items
    """

    try:
        import xlwt
    except ImportError:
        session.error = "xlwt module not available within the running Python - this needs installing for XLS output!"
        redirect(URL(c="kit"))

    from io import BytesIO
    output = BytesIO()

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
        sheetname = kit.code.replace("/", "_")
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

# =============================================================================
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
        session.error = "Python needs the ReportLab module installed for PDF export"
        redirect(URL(c="kit"))
    try:
        from geraldo import Report, ReportBand, SubReport, Label, ObjectValue, SystemField, landscape, BAND_WIDTH
        from geraldo.generators import PDFGenerator
    except ImportError:
        session.error = "Python needs the Geraldo module installed for PDF export"
        redirect(URL(c="kit"))

    table = db.budget_kit
    objects_list = db(table.id > 0).select()
    if not objects_list:
        session.warning = T("No data in this table - cannot create PDF!")
        redirect(URL(r=request))

    from io import BytesIO
    output = BytesIO()

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

# =============================================================================
def kit_export_csv():
    """
        Export kits in CSV format
        Concatenates: kits, items & kit_item
    """
    output = ""

    for resourcename in ["kit", "item", "kit_item"]:
        _table = "budget_" + resourcename
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

# =============================================================================
def budget_import_csv(file, table=None):
    """ Import CSV file into Database """

    if table:
        table.import_from_csv_file(file)
    else:
        # This is the preferred method as it updates reference fields
        db.import_from_csv_file(file)
        db.commit()

# =============================================================================
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

# =============================================================================
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
        session.error = "Python needs the ReportLab module installed for PDF export"
        redirect(URL(c="item"))
    try:
        from geraldo import Report, ReportBand, ReportGroup, Label, ObjectValue, SystemField, landscape, BAND_WIDTH
        from geraldo.generators import PDFGenerator
    except ImportError:
        session.error = "Python needs the Geraldo module installed for PDF export"
        redirect(URL(c="item"))

    table = db.budget_item
    objects_list = db(table.id > 0).select(orderby=table.category_type)
    if not objects_list:
        session.warning = T("No data in this table - cannot create PDF!")
        redirect(URL(f="item"))

    from io import BytesIO
    output = BytesIO()

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

# END =========================================================================

