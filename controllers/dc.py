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
                       "component_multiple",
                       "component_tab",
                       "settings",
                       ):
                ftable[fn].readable = ftable[fn].writable = False

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
                table.template_id.default = record.template_id
                
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.dc_rheader)

# -----------------------------------------------------------------------------
def respnse(): # Cannot call this 'response' or it will clobber the global
    """ RESTful CRUD controller """

    return s3_rest_controller("dc", "response",
                              rheader = s3db.dc_rheader,
                              )

# END =========================================================================
