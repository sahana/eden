# -*- coding: utf-8 -*-

"""
    Water module
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    from s3db.cms import cms_index
    return cms_index(c)

# -----------------------------------------------------------------------------
def debris_basin():
    """ Debris Basins, RESTful controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def gauge():
    """ Flood Gauges, RESTful controller """

    # Pre-processor
    def prep(r):
        if r.interactive:
            pass
        elif r.representation == "plain":
            # Map Popups
            r.table.image_url.readable = False
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive:
            pass
        elif r.representation == "plain":
            # Map Popups
            # use the Image URL
            # @ToDo: The default photo not the 1st
            image_url = r.record.image_url
            if image_url:
                output["item"].append(IMG(_src = image_url,
                                          # @ToDo: capture the size on upload & have controller resize where-required on-download
                                          _width = 400,
                                          _height = 310,
                                          ))
        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def river():
    """ Rivers, RESTful controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def reservoir():
    """ Reservoirs, RESTful controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def zone():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def zone_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# END =========================================================================
