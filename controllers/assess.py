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

    redirect(URL(f="building"))

# -----------------------------------------------------------------------------
def building_marker_fn(record):
    """
        Function to decide which Marker to use for Building Assessments Map
        @ToDo: Legend
        @ToDo: Move to Templates
        @ToDo: Use Symbology
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

    output = s3_rest_controller(rheader=s3db.assess_building_rheader)
    return output

# -----------------------------------------------------------------------------
def canvass():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# END =========================================================================
