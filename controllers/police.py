# -*- coding: utf-8 -*-

"""
    Police
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

    # Just redirect to the Police Stations Summary View
    s3_redirect_default(URL(f = "station",
                            args = "summary",
                            ))

# -----------------------------------------------------------------------------
def station():
    """
        RESTful CRUD controller
    """

    # Pre-processor
    def prep(r):
        # Location Filter
        from s3db.gis import gis_location_filter
        gis_location_filter(r)

        if r.interactive:
            if r.component:
                component_name = r.component_name
                if component_name == "inv_item" or \
                   component_name == "recv" or \
                   component_name == "send":
                    # Filter out items which are already in this inventory
                    from s3db.inv import inv_prep
                    inv_prep(r)

                elif component_name == "human_resource":
                    from s3db.org import org_site_staff_config
                    org_site_staff_config(r)

                elif component_name == "layout" and \
                     r.method != "hierarchy":
                    from s3db.org import org_site_layout_config
                    org_site_layout_config(r.record.site_id)

                elif component_name == "req":
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        # inc list_create (list_fields over-rides)
                        from s3db.inv import inv_req_create_form_mods
                        inv_req_create_form_mods(r)

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = police_rheader,
                              )

# -----------------------------------------------------------------------------
#def police_station_type():
#    """
#        RESTful CRUD controller
#    """

#    return s3_rest_controller()

# -----------------------------------------------------------------------------
def site_location():
    """ RESTful CRUD controller """

    from s3 import FS
    s3.filter = (FS("site_id$instance_type") == "police_station")

    table = s3db.org_site_location
    table.site_id.label = T("Police Station")
    table.site_id.represent = s3db.org_SiteRepresent(show_type=False)
    table.location_id.label = T("Beat")

    return s3_rest_controller("org", "site_location",
                              )

# -----------------------------------------------------------------------------
def police_rheader(r, tabs=[]):
    """ Resource headers for component views """

    rheader = None
    if r.representation == "html":

        if r.name == "station":
            station = r.record
            if station:
                tabs = [
                    (T("Station Details"), None),
                    #(T("Vehicles"), "vehicle"),
                    (T("Staff"), "human_resource"),
                    #(T("Shifts"), "shift"),
                    #(T("Roster"), "shift_staff"),
                    #(T("Vehicle Deployments"), "vehicle_report"),
                    (T("Beats"), "location"),
                ]
                rheader_tabs = s3_rheader_tabs(r, tabs)

                rheader = DIV(rheader_tabs)

    return rheader

# END =========================================================================
