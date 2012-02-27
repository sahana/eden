# -*- coding: utf-8 -*-

module = request.controller
resourcename = request.function

if module not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module Homepage """

    # @todo: have a link to the fire station the current user works at

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name

    # Note that this requires setting the Porto Incident Types in modules/eden.irs.py
    incidents = DIV(A(DIV(T("Fire"),
                          _style="background-color:red;",
                          _class="question-container fleft"),
                      _href=URL(c="irs", f="ireport", args=["create"],
                                vars={"type":"fire"})),
                    A(DIV(T("Rescue"),
                          _style="background-color:green;",
                          _class="question-container fleft"),
                      _href=URL(c="irs", f="ireport", args=["create"],
                                vars={"type":"rescue"})),
                    A(DIV(T("Hazmat"),
                          _style="background-color:yellow;",
                          _class="question-container fleft"),
                      _href=URL(c="irs", f="ireport", args=["create"],
                                vars={"type":"hazmat"})))

    return dict(module_name=module_name,
                incidents=incidents)

# -----------------------------------------------------------------------------
def station():
    """ Fire Station """

    location_id = s3db.gis_location_id

    csv_extra_fields = [
        dict(label="Country",
             field=location_id("country_id",
                               label=T("Country"),
                               requires = IS_NULL_OR(
                                          IS_ONE_OF(db,
                                                    "gis_location.id",
                                                    "%(name)s",
                                                    filterby = "level",
                                                    filter_opts = ["L0"],
                                                    sort=True)),
                               widget = None)),
        dict(label="Organisation",
             field=s3db.org_organisation_id())
    ]

    return s3_rest_controller(rheader = fire_rheader,
                              csv_extra_fields = csv_extra_fields)

# -----------------------------------------------------------------------------
def station_vehicle():
    """ Vehicles of Fire Stations """

    response.s3.prep = lambda r: r.method == "import"

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def water_source():
    """ Water Sources """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def hazard_point():
    """ Hazard Points """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def person():
    """ Person Controller for Ajax Requests """

    return s3_rest_controller("pr", "person")

# -----------------------------------------------------------------------------
def ireport_vehicle():
    """ REST controller """

    return s3_rest_controller("irs", "ireport_vehicle")

# -----------------------------------------------------------------------------
def fire_rheader(r, tabs=[]):
    """ Resource headers for component views """

    rheader = None
    if r.representation == "html":

        if r.name == "station":
            station = r.record
            if station:

                tabs = [
                    (T("Station Details"), None),
                    (T("Vehicles"), "vehicle"),
                    (T("Staff"), "human_resource"),
                    #(T("Shifts"), "shift"),
                    (T("Roster"), "shift_staff"),
                    (T("Vehicle Deployments"), "vehicle_report"),
                ]
                rheader_tabs = s3_rheader_tabs(r, tabs)

                rheader = DIV(rheader_tabs)

    return rheader

# END =========================================================================
