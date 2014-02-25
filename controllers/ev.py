# -*- coding: utf-8 -*-

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

    # Just redirect to the list of Cases
    redirect(URL(f="guest"))

# -----------------------------------------------------------------------------
def guest():
    """ REST Controller """

    s3 = current.response.s3
    
    # Pre-processor
    def prep(r):
        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):

        if r.interactive:
            if not r.component:
                update_url = URL(args=["[id]", "medicalData"])

        return output
    s3.postp = postp
    
    return s3_rest_controller(rheader = s3db.ev_guest_rheader,
                              hide_filter=False
                              )

def group():
    """
        Family controller
        - uses the group table from PR
    """

    return s3db.ev_group_controller()

# END =========================================================================
