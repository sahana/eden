# -*- coding: utf-8 -*-

"""
    Social Tenure Domain Model
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return s3db.cms_index(module)

# -----------------------------------------------------------------------------
def person():
    """ RESTful CRUD controller """

    s3db.set_method("pr", resourcename,
                    method = "contacts",
                    action = s3db.pr_Contacts)

    return s3_rest_controller("pr", resourcename,
                              rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def group():
    """ RESTful CRUD controller """

    return s3_rest_controller("pr", resourcename,
                              rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def tenure():
    """
        RESTful CRUD controller
        - not yet sure what this will be used for...probably reporting, maybe mapping
    """

    return s3_rest_controller(rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def tenure_role():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def tenure_type():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# END =========================================================================
