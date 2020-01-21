# -*- coding: utf-8 -*-

"""
    Finance
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
def expense():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def payment_service():
    """ Payment Services: RESTful CRUD controller """

    return s3_rest_controller(rheader = s3db.fin_rheader)

# END =========================================================================
