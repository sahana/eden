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
        # Function to call for all Site Instance Types
        from s3db.org import org_site_prep
        org_site_prep(r)

        if r.interactive:
            if r.component:
                component_name = r.component_name
                if component_name in ("asset", "vehicle"):
                    atable = s3db.asset_asset
                    # Stay within Site tab
                    s3db.configure("asset_asset",
                                   create_next = None,
                                   )
                    if component_name == "asset":
                        # Default/Hide the Organisation field
                        org_field = atable.organisation_id
                        org_field.default = r.record.organisation_id
                        org_field.readable = org_field.writable = False
                        # Filter out Vehicles
                        r.resource.add_component_filter(component_name, (FS("type") != 1))
                    else:
                        atable.organisation_id.required = False # Otherwise needs to be in crud_form & isn't defaulted
                        # Default new to Vehicle
                        atable.type.default = 1
                        # Only select from vehicles
                        ctable = s3db.supply_item_category
                        vehicle_categories = db(ctable.is_vehicle == True).select(ctable.id)
                        atable.item_id.requires.set_filter(filterby = "item_category_id",
                                                           filter_opts = [row.id for row in vehicle_categories],
                                                           )
                        # Include Vehicle Details in the form
                        from s3 import S3SQLCustomForm, S3SQLInlineComponent
                        
                        def vehicle_postprocess(form):
                            # Set the organisation_id
                            db(atable.id == form.vars.id).update(organisation_id = r.record.organisation_id)

                        crud_form = S3SQLCustomForm("number",
                                                    (T("Vehicle Type"), "item_id"),
                                                    (T("License Plate"), "sn"),
                                                    "purchase_date",
                                                    "purchase_price",
                                                    "purchase_currency",
                                                    "cond",
                                                    S3SQLInlineComponent("vehicle",
                                                                         label = "",
                                                                         multiple = False,
                                                                         fields = [#"vehicle_type_id",
                                                                                   "mileage",
                                                                                   "service_mileage",
                                                                                   "service_date",
                                                                                   "insurance_date",
                                                                                   ],
                                                                         ),
                                                    postprocess = vehicle_postprocess,
                                                    )
                        s3db.configure("asset_asset",
                                       crud_form = crud_form,
                                       )
                        s3.crud_strings["asset_asset"] = Storage(label_create = T("Add Vehicle Details"),
                                                                 title_display = T("Vehicle Details"),
                                                                 title_list = T("Vehicles"),
                                                                 title_update = T("Edit Vehicle Details"),
                                                                 label_list_button = T("List Vehicle Details"),
                                                                 label_delete_button = T("Delete Vehicle Details"),
                                                                 msg_record_created = T("Vehicle Details added"),
                                                                 msg_record_modified = T("Vehicle Details updated"),
                                                                 msg_record_deleted = T("Vehicle Details deleted"),
                                                                 msg_list_empty = T("No Vehicle Details currently defined"),
                                                                 )
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
                        (T("Staff"), "human_resource"),
                        (T("Shifts"), "shift"),
                        # @ToDo:
                        #(T("Roster"), "shift_staff"),
                        (T("Vehicles"), "vehicle"),
                        (T("Vehicle Deployments"), "vehicle_report"),
                        (T("Assets"), "asset"),
                        ]
                rheader_tabs = s3_rheader_tabs(r, tabs)

                rheader = DIV(rheader_tabs)

    return rheader

# END =========================================================================
