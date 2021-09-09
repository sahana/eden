# -*- coding: utf-8 -*-

"""
    Disease Case Tracking and Contact Tracing
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
def index():
    "Module's Home Page"

    module_name = settings.modules[c].get("name_nice")
    response.title = module_name
    return {"module_name": module_name,
            }

# -----------------------------------------------------------------------------
def disease():
    """ Disease Information Controller """

    return s3_rest_controller(rheader = s3db.disease_rheader)

# -----------------------------------------------------------------------------
def case():
    """ Case Tracking Controller """

    def prep(r):

        if settings.get_disease_case_id():
            ptable = s3db.pr_person
            ptable.pe_label.label = T("ID")

        if r.record:
            # Do not allow changing the person ID
            person_id = r.table.person_id
            person_id.writable = False
            person_id.comment = None
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

        component_name = r.component_name
        if component_name in ("contact", "exposure"):
            field = r.component.table.tracing_id
            field.readable = field.writable = False

        if component_name == "contact":
            # Adapt CRUD strings to perspective
            s3.crud_strings["disease_exposure"] = Storage(
                label_create = T("Add Close Contact"),
                title_display = T("Close Contact Details"),
                title_list = T("Close Contacts"),
                title_update = T("Edit Contact"),
                label_list_button = T("List Close Contacts"),
                label_delete_button = T("Delete Contact"),
                msg_record_created = T("Contact added"),
                msg_record_modified = T("Contact updated"),
                msg_record_deleted = T("Contact deleted"),
                msg_list_empty = T("No Close Contacts currently registered"))


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
def person():
    """ Delegated person-controller for case tab """

    def prep(r):

        resource = r.resource
        table = resource.table

        table.pe_label.label = T("ID")

        get_vars = r.get_vars
        if "viewing" in get_vars:

            try:
                vtablename, record_id = get_vars["viewing"].split(".")
            except ValueError:
                return False

            if vtablename == "disease_case":

                # Get the person_id from the case
                ctable = s3db[vtablename]
                query = (ctable.id == record_id)
                row = db(query).select(ctable.person_id,
                                       limitby = (0, 1),
                                       ).first()
                if not row:
                    r.error(404, current.ERROR.BAD_RECORD)

                # Update the request
                request = s3base.S3Request("pr", "person",
                                           args = [str(row.person_id)],
                                           vars = {},
                                           )
                r.resource = resource = request.resource
                r.record = request.record
                r.id = request.id

                # Name fields in name-format order
                NAMES = ("first_name", "middle_name", "last_name")
                keys = s3base.StringTemplateParser.keys(settings.get_pr_name_format())
                name_fields = [fn for fn in keys if fn in NAMES]

                # Fields in form
                from s3 import S3SQLInlineComponent
                crud_fields = name_fields + \
                              ["gender",
                               "date_of_birth",
                               S3SQLInlineComponent(
                                    "contact",
                                    fields = [("", "value")],
                                    filterby = {"field": "contact_method",
                                                "options": "SMS",
                                                },
                                    label = settings.get_ui_label_mobile_phone(),
                                    multiple = False,
                                    name = "phone",
                                    ),
                               S3SQLInlineComponent(
                                    "contact",
                                    fields = [("", "value")],
                                    filterby = {"field": "contact_method",
                                                "options": "EMAIL",
                                                },
                                    label = T("Email"),
                                    multiple = False,
                                    name = "email",
                                    ),
                               ]

                resource.configure(crud_form = s3base.S3SQLCustomForm(*crud_fields),
                                   deletable = False,
                                   )
            return True
        else:
            return False
    s3.prep = prep

    def postp(r, output):

        # Remove list- and summary-buttons
        if r.record and isinstance(output, dict):
            buttons = output.get("buttons")
            if buttons:
                buttons.pop("list_btn", None)
                buttons.pop("summary_btn", None)
        return output
    s3.postp = postp

    return s3_rest_controller("pr", "person",
                              rheader = s3db.disease_rheader,
                              )

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
def testing_report():
    """ Testing Site Daily Summary Report: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def testing_device():
    """ Testing Device Registry: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def case_diagnostics():
    """ Diagnostic Tests: RESTful CRUD Controller """

    return s3_rest_controller()

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
