# -*- coding: utf-8 -*-

"""
    Assessments
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ RESTful CRUD controller """

    s3_redirect_default(URL(f="building"))


# -----------------------------------------------------------------------------
def ifrc24h():
    """
        Custom function to demo Mobile Assessment collection
    """

    # This function uses it's own Theme
    settings.base.theme = "mobile"

    # No need to capture DoB/Gender of community contact people
    settings.pr.request_dob = False
    settings.pr.request_gender = False
    # Keep UX simple
    settings.pr.lookup_duplicates = False

    return s3_rest_controller("assess", "24h")

# -----------------------------------------------------------------------------
def building_marker_fn(record):
    """
        Function to decide which Marker to use for Building Assessments Map
        @ToDo: Legend
        @ToDo: Move to Templates
    """

    # Use Marker in preferential order
    if record.asbestos == 1:
        marker = "hazmat"
    else:
        marker = "residence"

    # Colour code by priority
    priority = record.priority
    if priority == 1:
        # High
        marker = "%s_red" % marker
    elif priority == 2:
        # Medium
        marker = "%s_yellow" % marker
    elif priority == 3:
        # Low
        marker = "%s_green" % marker

    mtable = db.gis_marker
    try:
        marker = db(mtable.name == marker).select(mtable.image,
                                                  mtable.height,
                                                  mtable.width,
                                                  cache=s3db.cache,
                                                  limitby=(0, 1)
                                                  ).first()
    except:
        marker = db(mtable.name == "residence").select(mtable.image,
                                                       mtable.height,
                                                       mtable.width,
                                                       cache=s3db.cache,
                                                       limitby=(0, 1)
                                                       ).first()
    return marker

# -----------------------------------------------------------------------------
def building():
    """ RESTful CRUD controller """

    # @ToDo: deployment_setting
    ctable = s3db.gis_config
    config = db(ctable.name == "Queens").select(ctable.id,
                                                limitby=(0, 1)).first()
    if config:
        gis.set_config(config.id)

    # Pre-processor
    def prep(r):
        # Location Filter
        #s3db.gis_location_filter(r)

        if r.interactive:
            if r.method == "map":
                # Tell the client to request per-feature markers
                s3db.configure("assess_building", marker_fn=building_marker_fn)

        elif r.representation == "geojson":
            # Load these models now as they'll be needed when we encode
            mtable = s3db.gis_marker
            s3db.configure("assess_building", marker_fn=building_marker_fn)

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.assess_building_rheader)

# -----------------------------------------------------------------------------
def canvass():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def need():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def needs():
    """ RESTful CRUD controller """

    S3SQLInlineComponent = s3base.S3SQLInlineComponent

    crud_fields = ["name",
                   "location_id",
                   ]
    cappend = crud_fields.append

    # Demographics
    field = s3db.assess_needs_demographic_data.parameter_id
    field.writable = False
    field.comment = None

    table = s3db.stats_demographic
    rows = db(table.deleted != True).select(table.parameter_id,
                                            table.name,
                                            )

    label = T("Demographics")
    number = 0
    for row in rows:
        name = "number%s" % number
        number += 1
        cappend(S3SQLInlineComponent("demographic",
                                     name = name,
                                     label = label,
                                     fields = (("", "parameter_id"),
                                               ("", "value"),
                                               ),
                                     filterby = dict(field = "parameter_id",
                                                     options = row.parameter_id
                                                     ),
                                     multiple = False,
                                     ),
                )
        label = ""

    # Needs
    table = s3db.assess_need
    rows = db(table.deleted != True).select(table.id,
                                            table.name,
                                            )

    label = T("Needs")
    #number = 0
    for row in rows:
        name = "number%s" % number
        number += 1
        cappend(S3SQLInlineComponent("need",
                                     name = name,
                                     label = label,
                                     fields = (("", "need_id"),
                                               ("", "value"),
                                               ),
                                     filterby = dict(field = "need_id",
                                                     options = row.id
                                                     ),
                                     multiple = False,
                                     ),
                )
        label = ""

    crud_form = s3base.S3SQLCustomForm(*crud_fields)

    s3db.configure("assess_needs",
                   crud_form = crud_form,
                   )

    return s3_rest_controller()

# END =========================================================================
