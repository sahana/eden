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
def building():
    """ RESTful CRUD controller """

    # @ToDo: deployment_setting
    ctable = s3db.gis_config
    config = db(ctable.name == "Queens").select(ctable.id,
                                                limitby=(0, 1)).first()
    if config:
        gis.set_config(config.id)

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def canvass():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# END =========================================================================
