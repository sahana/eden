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
    
    return s3_rest_controller(rheader = s3db.disease_rheader)

# END =========================================================================
