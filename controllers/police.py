# -*- coding: utf-8 -*-

"""
    Police
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return settings.customise_home(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the Police Stations Summary View
    s3_redirect_default(URL(f="station", args="summary"))

# -----------------------------------------------------------------------------
def station():
    """
        RESTful CRUD controller
    """

    output = s3_rest_controller(rheader = police_rheader,
                                )
    return output

# -----------------------------------------------------------------------------
#def police_station_type():
#    """
#        RESTful CRUD controller
#    """

#    return s3_rest_controller()

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
