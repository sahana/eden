# -*- coding: utf-8 -*-

"""
    Education
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return settings.customise_home(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the Schools Summary View
    s3_redirect_default(URL(f="school", args="summary"))

# -----------------------------------------------------------------------------
def school():
    """
        RESTful CRUD controller
    """

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def school_type():
    """
        RESTful CRUD controller
    """

    return s3_rest_controller()

# END =========================================================================
