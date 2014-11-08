# -*- coding: utf-8 -*-

"""
    Disease Case Tracking and Contact Tracing
"""

module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    "Module's Home Page"

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def disease():
    """ Disease Information Controller """

    return s3_rest_controller(rheader = s3db.disease_rheader)

# -----------------------------------------------------------------------------
def case():
    """ Case Tracking Controller """

    def prep(r):
        if r.method == "update":
            r.table.person_id.writable = False
        else:
            dtable = s3db.disease_disease
            diseases = db(dtable.deleted == False).select(dtable.id,
                                                          limitby=(0, 2)
                                                          )
            if len(diseases) == 1:
                # Default to only disease
                field = r.table.disease_id
                field.default = diseases.first().id
                field.writable = False

        if r.component_name == "contact" or \
           r.component_name == "exposure":
            field = r.component.table.tracing_id
            field.readable = field.writable = False
            
        if r.interactive:
            field = r.table.person_id
            field.requires = IS_ADD_PERSON_WIDGET2()
            field.widget = S3AddPersonWidget2(controller="pr")

        return True
    s3.prep = prep

    def postp(r, output):
        if isinstance(output, dict) and "buttons" in output:
            buttons = output["buttons"]
            if "list_btn" in buttons and "summary_btn" in buttons:
                buttons["list_btn"] = buttons["summary_btn"]
        return output
    s3.postp = postp

    return s3_rest_controller(rheader = s3db.disease_rheader)

# -----------------------------------------------------------------------------
def tracing():
    """ Contact Tracing Controller """

    def prep(r):

        if r.id and r.component_name == "exposure":

            ctable = r.component.table
            case_id = ctable.case_id
            case_id.default = r.id
            case_id.readable = case_id.writable = False

            crud_strings = s3.crud_strings[r.component.tablename]
            crud_strings["label_create"] = T("Add Contact Person")
            crud_strings["label_delete_button"] = T("Delete Contact Person")

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.disease_rheader)

# -----------------------------------------------------------------------------
def statistic():
    """ RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def stats_data():
    """ RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def stats_aggregate():
    """ RESTful CRUD Controller """

    return s3_rest_controller()

# END =========================================================================
