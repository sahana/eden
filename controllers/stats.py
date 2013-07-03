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
def source():
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

# -----------------------------------------------------------------------------
def demographic_aggregate():
    """ REST Controller """

    def clear_aggregates(r, **attr):
        if not s3_has_role(ADMIN):
            auth.permission.fail()
        s3db.stats_demographic_rebuild_all_aggregates()
        redirect(URL(c="stats",
                     f="demographic_aggregate",
                     args="",
                     ))
        
    s3db.set_method("stats", "demographic_aggregate",
                    method="clear",
                    action=clear_aggregates)

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def resident_type():
    """ REST Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def resident():
    """ REST Controller """

    return s3_rest_controller()
    
# -----------------------------------------------------------------------------
def trained_type():
    """ REST Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def trained():
    """ REST Controller """

    return s3_rest_controller()

 # END =========================================================================
