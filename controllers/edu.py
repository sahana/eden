# -*- coding: utf-8 -*-

"""
    Education
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return settings.customise_home(c, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the Schools Summary View
    s3_redirect_default(URL(f="school",
                            args = "summary",
                            ))

# -----------------------------------------------------------------------------
def school():
    """
        RESTful CRUD controller
    """

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                if r.component_name == "inv_item" or \
                   r.component_name == "recv" or \
                   r.component_name == "send":
                    # Filter out items which are already in this inventory
                    from s3db.inv import inv_prep
                    inv_prep(r)

                elif r.component_name == "human_resource":
                    from s3db.org import org_site_staff_config
                    org_site_staff_config(r)

                elif r.component_name == "req":
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        # inc list_create (list_fields over-rides)
                        from s3db.inv import inv_req_create_form_mods
                        inv_req_create_form_mods(r)

        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def school_type():
    """
        RESTful CRUD controller
    """

    return s3_rest_controller()

# END =========================================================================
