# -*- coding: utf-8 -*-

"""
    Impact - Controller

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-10-12
"""

prefix = request.controller
resourcename = request.function

if prefix not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % prefix)

# =============================================================================
def type():

    """ RESTful CRUD controller """

    return s3_rest_controller(prefix, resourcename)

# =============================================================================
def impact():

    """ RESTful CRUD controller """

    return s3_rest_controller(prefix, resourcename)

# END =========================================================================

