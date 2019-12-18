# -*- coding: utf-8 -*-

"""
    Sahana Eden Stats Controller
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return s3db.cms_index(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the Demographic Data
    s3_redirect_default(URL(f="demographic_data", args="summary"))

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
        if not auth.s3_has_role("ADMIN"):
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
def people_type():
    """ REST Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def people():
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

# -----------------------------------------------------------------------------
def impact_type():
    """ REST Controller for impact types """

    return s3_rest_controller()

# END =========================================================================
