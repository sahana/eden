# -*- coding: utf-8 -*-

"""
    Security module: controllers
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return s3db.cms_index(c)

# -----------------------------------------------------------------------------
def level():
    """ Security Level Assessments: RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def zone():
    """ Security Zones: RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def zone_type():
    """ Security Zone Types: RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def person():
    """
        Module-specific pr_person controller, to allow differential
        authorisation and configuration
    """

    return s3_rest_controller("pr")

# -----------------------------------------------------------------------------
def person_search():
    """
        RESTful controller for autocomplete-searches
    """

    s3.prep = lambda r: r.method == "search_ac"
    return s3_rest_controller("pr", "person")

# -----------------------------------------------------------------------------
def staff():
    """ Security Staff Assignments: RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def staff_type():
    """ Security Staff Types (roles): RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def essential():
    """ Filtered Staff controller """

    table = s3db.hrm_human_resource
    s3.filter = (table.essential == True)

    return s3_rest_controller("hrm", "human_resource")

# -----------------------------------------------------------------------------
def seized_item_type():
    """ Seized item types: RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def seized_item_depository():
    """ Seized item depositories: RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def seized_item():
    """ Seized items: RESTful CRUD controller """

    return s3_rest_controller()

# END =========================================================================
