# -*- coding: utf-8 -*-

"""
    Impact - Controller
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
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

