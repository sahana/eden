# -*- coding: utf-8 -*-

"""
    Security module
"""

module = request.controller
#resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return s3db.cms_index(module)

# -----------------------------------------------------------------------------
def level():
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def zone():
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def zone_type():
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def staff():
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def staff_type():
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def essential():
    """
        Filtered Staff controller
    """

    table = s3db.hrm_human_resource
    s3.filter = (table.essential == True)

    return s3_rest_controller("hrm", "human_resource")

# END =========================================================================
