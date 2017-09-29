# -*- coding: utf-8 -*-

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module Homepage """

    return s3db.cms_index(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the list of Fire stations
    s3_redirect_default(URL(f="station"))

# -----------------------------------------------------------------------------
def zone():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def zone_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def station():
    """ Fire Station """

    # CSV column headers, so no T()
    csv_extra_fields = [
        dict(label="Country",
             field=s3db.gis_country_id()),
        dict(label="Organisation",
             field=s3db.org_organisation_id())
    ]

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                if r.component.name == "human_resource":
                    s3db.org_site_staff_config(r)
                elif r.component.name == "inv_item":
                    # remove CRUD generated buttons in the tabs
                    s3db.configure("inv_inv_item",
                                   create = False,
                                   deletable = False,
                                   editable = False,
                                   listadd = False,
                                   )
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = fire_rheader,
                              csv_extra_fields = csv_extra_fields,
                              )

# -----------------------------------------------------------------------------
def station_vehicle():
    """ Vehicles of Fire Stations """

    s3.prep = lambda r: r.method == "import"

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
                    #(T("Vehicle Deployments"), "vehicle_report"),
                ]
                rheader_tabs = s3_rheader_tabs(r, tabs)

                rheader = DIV(rheader_tabs)

    return rheader

# END =========================================================================
