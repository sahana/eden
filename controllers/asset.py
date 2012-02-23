# -*- coding: utf-8 -*-

"""
    Asset Management Functionality

    http://eden.sahanafoundation.org/wiki/BluePrint/Assets
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module Home Page """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name

    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def create():
    """ Redirect to asset/create """

    redirect(URL(f="asset", args="create"))

# -----------------------------------------------------------------------------
def asset():
    """ RESTful CRUD controller """

    # Defined in Model for use from Multiple Controllers for unified menus
    return asset_controller()

# =============================================================================
def item():
    """ RESTful CRUD controller """

    # Sort Alphabetically for the AJAX-pulled dropdown
    s3mgr.configure("supply_item",
                    orderby=s3db.supply_item.name)

    # Defined in the Model for use from Multiple Controllers for unified menus
    return supply_item_controller()

# END =========================================================================

