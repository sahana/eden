# -*- coding: utf-8 -*-

"""
    Data Collection:
    - a front-end UI to manage Assessments which uses the Dynamic Tables back-end
"""

module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def template():
    """ RESTful CRUD controller """

    def prep(r):

        if r.record and r.component_name == "question":

            # All Questions should be in the same Dynamic Table
            ftable = db.s3_field
            f = ftable.table_id
            f.default = r.record.table_id
            f.readable = f.writable = False

            # Hide fields which complicate things
            for fn in ("require_unique",
                       "options",
                       "default_value",
                       "component_key",
                       "component_alias",
                       "component_tab",
                       "settings",
                       ):
                ftable[fn].readable = ftable[fn].writable = False

            # Hide the fieldname
            from uuid import uuid1
            f = ftable.name
            f.default = lambda: "f%s" % str(uuid1()).replace("-", "_")
            f.readable = f.writable = False

            # CRUD Strings
            s3.crud_strings["s3_field"] = Storage(
                label_create = T("Create Question"),
                title_display = T("Question Details"),
                title_list = T("Questions"),
                title_update = T("Edit Question"),
                label_list_button = T("List Questions"),
                label_delete_button = T("Delete Question"),
                msg_record_created = T("Question created"),
                msg_record_modified = T("Question updated"),
                msg_record_deleted = T("Question deleted"),
                msg_list_empty = T("No Questions currently defined"),
            )

            # Simplify the choices of Question Type
            type_opts = {"boolean": T("Yes/No"),
                         #"Yes, No, Don't Know"
                         "string": T("Text"),
                         "integer": T("Number"),
                         #"float": T("Fractional Number"),
                         #"integer": T("Options"),
                         }
            f = ftable.field_type
            f.requires = IS_IN_SET(type_opts)
            f.represent = lambda opt: type_opts.get(opt, messages.UNKNOWN_OPT)

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.dc_rheader)

# -----------------------------------------------------------------------------
def target():
    """ RESTful CRUD controller """

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component_name == "response":
                # Default component values from master record
                record = r.record
                table = s3db.dc_response
                table.location_id.default = record.location_id
                f = table.template_id
                f.default = record.template_id
                f.writable = False

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.dc_rheader)

# -----------------------------------------------------------------------------
def respnse(): # Cannot call this 'response' or it will clobber the global
    """ RESTful CRUD controller """

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component_name == "answer":
                # CRUD Strings
                s3.crud_strings[r.component.tablename] = Storage(
                    label_create = T("Create Responses"),
                    title_display = T("Response Details"),
                    title_list = T("Responses"),
                    title_update = T("Edit Response"),
                    label_list_button = T("List Responses"),
                    label_delete_button = T("Clear Response"),
                    msg_record_created = T("Response created"),
                    msg_record_modified = T("Response updated"),
                    msg_record_deleted = T("Response deleted"),
                    msg_list_empty = T("No Responses currently defined"),
                )
                
        return True
    s3.prep = prep

    return s3_rest_controller("dc", "response",
                              rheader = s3db.dc_rheader,
                              )

# END =========================================================================
