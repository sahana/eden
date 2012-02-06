# -*- coding: utf-8 -*-

"""
    Impact - Controller
"""

module = request.controller
resourcename = request.function

if module not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

# =============================================================================
def type():

    """ RESTful CRUD controller """

    return s3_rest_controller()

# =============================================================================
def impact():

    """ RESTful CRUD controller """

    return s3_rest_controller()

# END =========================================================================

