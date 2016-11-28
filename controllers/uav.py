# -*- coding: utf-8 -*-

"""
    UAV Management - Controllers
"""

module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    # Redirect to dataset page
    s3_redirect_default(URL(f="dataset"))

# -----------------------------------------------------------------------------
def manufacturer():
    """ Drone Manufacturer - RESTful controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def model():
    """ Drone Model - RESTful controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def dataset():
    """ Dataset from drone flight - RESTful controller """

    return s3_rest_controller()

# END =========================================================================
