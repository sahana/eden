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

    def prep(r):
        if r.method == "clear":
            if not s3_has_role(ADMIN):
                auth.permission.fail()
            s3db.stats_rebuild_aggregates()
            redirect(URL(c="stats",
                         f="aggregate",
                         args="",
                         ))
        return True
    s3.prep = prep

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def demographic():
    """ REST Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def demographic_data():
    """ REST Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def group():
    """ REST Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def group_type():
    """ REST Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def source():
    """ REST Controller """

    return s3_rest_controller()

# END =========================================================================
