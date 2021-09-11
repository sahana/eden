# -*- coding: utf-8 -*-

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
def index():
    """ Module Homepage """

    module_name = settings.modules[c].get("name_nice")
    response.title = module_name

    htable = s3db.hrm_human_resource
    stable = s3db.fire_station

    person_id = auth.s3_logged_in_person()

    query = (htable.person_id == person_id) & \
            (htable.site_id == stable.site_id)

    row = db(query).select(stable.id,
                           stable.name,
                           limitby = (0, 1),
                           ).first()
    if row:
        station_id = row.id
        station_name = row.name
    else:
        station_id = None
        station_name = None

    incidents = DIV(A(DIV(T("Fire"),
                          _style = "background-color:red;",
                          _class = "question-container fleft",
                          ),
                      _href = URL(c="event", f="incident_report",
                                  args = ["create"],
                                  vars = {"incident_type": "Fire"},
                                  ),
                      ),
                    A(DIV(T("Rescue"),
                          _style = "background-color:green;",
                          _class = "question-container fleft"),
                      _href = URL(c="event", f="incident_report",
                                  args = ["create"],
                                  # Needs 'Rescue' adding to event_incident_type table
                                  vars = {"incident_type": "Rescue"},
                                  ),
                      ),
                    A(DIV(T("Hazmat"),
                          _style = "background-color:yellow;",
                          _class = "question-container fleft",
                          ),
                      _href = URL(c="event", f="incident_report",
                                  args = ["create"],
                                  vars = {"incident_type": "Hazardous Material"},
                                  ),
                      ))

    return {"incidents": incidents,
            "station_id": station_id,
            "station_name": station_name,
            "module_name": module_name,
            }

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

    
    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                component_name = r.component_name
                if component_name == "inv_item":
                    # Filter out items which are already in this inventory
                    from s3db.inv import inv_prep
                    inv_prep(r)
                    # Remove the Site Name from the list_fields
                    list_fields = s3db.get_config("inv_inv_item", "list_fields")
                    try:
                        list_fields.remove("site_id")
                        s3db.configure("inv_inv_item",
                                       list_fields = list_fields,
                                       )
                    except:
                        pass

                elif component_name == "recv":
                    # Filter out items which are already in this inventory
                    from s3db.inv import inv_prep
                    inv_prep(r)

                    # Configure which fields in inv_recv are readable/writable
                    # depending on status
                    recvtable = s3db.inv_recv
                    if r.component_id:
                        record = db(recvtable.id == r.component_id).select(recvtable.status,
                                                                           limitby = (0, 1)
                                                                           ).first()
                        set_recv_attr(record.status)
                    else:
                        from s3db.inv import inv_ship_status
                        set_recv_attr(inv_ship_status["IN_PROCESS"])
                        recvtable.recv_ref.readable = False
                        if r.method and r.method != "read":
                            # Don't want to see in Create forms
                            recvtable.status.readable = False

                elif component_name == "send":
                    # Filter out items which are already in this inventory
                    from s3db.inv import inv_prep
                    inv_prep(r)

                elif component_name == "human_resource":
                    from s3db.org import org_site_staff_config
                    org_site_staff_config(r)

                elif component_name == "req":
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        # inc list_create (list_fields over-rides)
                        from s3db.req import req_create_form_mods
                        req_create_form_mods()

                elif component_name == "asset":
                    # Default/Hide the Organisation & Site fields
                    record = r.record
                    atable = s3db.asset_asset
                    field = atable.organisation_id
                    field.default = record.organisation_id
                    field.readable = field.writable = False
                    field = atable.site_id
                    field.default = record.site_id
                    field.readable = field.writable = False
                    # Stay within Site tab
                    s3db.configure("asset_asset",
                                   create_next = None,
                                   )
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = fire_rheader,
                              # CSV column headers, so no T()
                              csv_extra_fields = [{"label": "Country",
                                                   "field": s3db.gis_country_id(),
                                                   },
                                                  {"label": "Organisation",
                                                   "field": s3db.org_organisation_id(),
                                                   },
                                                  ],
                              )

# -----------------------------------------------------------------------------
def person():
    """ Person Controller for Ajax Requests """

    return s3_rest_controller("pr", "person")

# -----------------------------------------------------------------------------
def fire_rheader(r, tabs=[]):
    """ Resource headers for component views """

    rheader = None
    if r.representation == "html":

        if r.name == "station":
            station = r.record
            if station:

                tabs = [(T("Station Details"), None),
                        (T("Vehicles"), "asset"),
                        # @ToDo:
                        #(T("Vehicles"), "vehicle"),
                        (T("Staff"), "human_resource"),
                        (T("Shifts"), "shift"),
                        # @ToDo:
                        #(T("Roster"), "shift_staff"),
                        (T("Vehicle Deployments"), "vehicle_report"),
                        ]
                rheader_tabs = s3_rheader_tabs(r, tabs)

                rheader = DIV(rheader_tabs)

    return rheader

# END =========================================================================
