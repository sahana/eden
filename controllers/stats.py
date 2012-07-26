# -*- coding: utf-8 -*-

"""
    Sahana Eden Stats Controller
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def parameter():
    """ REST Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def data():
    """ REST Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def aggregate():
    """ REST Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def demographic():
    """ REST Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def demographic_data():
    """ REST Controller """

    return s3_rest_controller()

# END =========================================================================