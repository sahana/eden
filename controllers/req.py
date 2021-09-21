# -*- coding: utf-8 -*-

"""
    Request Management
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
def index():
    """ Customisable module homepage """

    return settings.customise_home(c, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the list of Needs
    s3_redirect_default(URL(f = "need"))

# =============================================================================
def create():
    """ Redirect to need/create """

    redirect(URL(f = "need",
                 args = "create",
                 ))

# -----------------------------------------------------------------------------
def need():
    """
        RESTful CRUD Controller for Needs
    """

    def prep(r):
        if r.component_name == "impact":
            s3db.stats_impact.location_id.default = r.record.location_id
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.req_rheader)

# END =========================================================================
