# -*- coding: utf-8 -*-

"""
    Supply

    Generic Supply functionality such as catalogs and items that are used across multiple applications
"""

module = request.controller
resourcename = request.function

if not (deployment_settings.has_module("inv") or deployment_settings.has_module("asset")):
    raise HTTP(404, body="Module disabled: %s" % module)

# =============================================================================
def index():
    """
        Application Home page
    """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def catalog():
    """ RESTful CRUD controller """

    return s3_rest_controller(rheader=catalog_rheader)

# -----------------------------------------------------------------------------
def catalog_rheader(r):

    """ Resource Header for Catalogs """

    if r.representation == "html":
        catalog = r.record
        if catalog:
            tabs = [
                    (T("Edit Details"), None),
                    (T("Categories"), "item_category"),
                    (T("Items"), "catalog_item"),
                   ]
            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table

            rheader = DIV(TABLE(TR( TH("%s: " % table.name.label),
                                    catalog.name,
                                  ),
                                TR( TH("%s: " % table.organisation_id.label),
                                    table.organisation_id.represent(catalog.organisation_id),
                                  ),
                               ),
                          rheader_tabs
                         )
            return rheader
    return None


# =============================================================================
def item_category():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def item_pack():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)

    s3mgr.configure(tablename,
                    listadd=False)

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def brand():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# =============================================================================
def item():
    """ RESTful CRUD controller """

    # Sort Alphabetically for the AJAX-pulled dropdown
    s3mgr.configure("supply_item",
                    orderby=s3db.supply_item.name)

    # Defined in the Model for use from Multiple Controllers for unified menus
    return supply_item_controller()

# =============================================================================
def catalog_item():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# =============================================================================
def item_entity():
    """ RESTful CRUD controller """

    # Defined in the Model for use from Multiple Controllers for unified menus
    return item_entity_controller()

# END =========================================================================
