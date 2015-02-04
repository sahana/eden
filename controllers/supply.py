# -*- coding: utf-8 -*-

"""
    Supply

    Generic Supply functionality such as catalogs and items that are used across multiple applications
"""

module = request.controller
resourcename = request.function

if not settings.has_module("supply"):
    raise HTTP(404, body="Module disabled: %s" % module)

# =============================================================================
def index():
    """
        Application Home page
    """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def brand():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def catalog():
    """ RESTful CRUD controller """

    return s3_rest_controller(rheader=s3db.supply_catalog_rheader)

# -----------------------------------------------------------------------------
def catalog_item():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def distribution():
    """ RESTful CRUD controller """

    #def prep(r):
    #    if r.method in ("create", "create.popup", "update", "update.popup"):
    #        # Coming from Profile page?
    #        location_id = r.get_vars.get("~.(location)", None)
    #        if location_id:
    #            field = r.table.location_id
    #            field.default = location_id
    #            field.readable = field.writable = False
    #    if r.record:
    #        field = r.table.location_id
    #        field.comment = None
    #        field.writable = False
    #    return True
    #s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def distribution_report():
    """
        RESTful CRUD controller for Supply Distributions
        - limited to just seeing aggregated data for differential permissions
    """

    def prep(r):
        r.method = "report"
        return True
    s3.prep = prep

    return s3_rest_controller("supply", "distribution")

# -----------------------------------------------------------------------------
def distribution_item():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def item():
    """ RESTful CRUD controller """

    # Defined in the Model for use from Multiple Controllers for unified menus
    return s3db.supply_item_controller()

# -----------------------------------------------------------------------------
def item_category():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def item_entity():
    """ RESTful CRUD controller """

    # Defined in the Model for use from Multiple Controllers for unified menus
    return s3db.supply_item_entity_controller()

# -----------------------------------------------------------------------------
def item_pack():
    """ RESTful CRUD controller """

    s3db.configure("supply_item_pack",
                   listadd = False,
                   )

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def kit_item():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# END =========================================================================
