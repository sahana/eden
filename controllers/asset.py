# -*- coding: utf-8 -*-

"""
    Asset

    @author: Michael Howden (michael@sahanafoundation.org)
    @author: Fran Boon (fran@sahanafoundation.org)
    @date-created: 2011-03-18

    Asset Management Functionality

    http://eden.sahanafoundation.org/wiki/BluePrint/Assets
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

s3_menu(module)

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

    # Load the models
    s3mgr.load("asset_asset")
    if deployment_settings.has_module("vehicle"):
        s3mgr.load("vehicle_vehicle")

    # Defined in Model
    return s3.asset.controller()

# =============================================================================
def item():
    """ RESTful CRUD controller """

    # Load the models
    s3mgr.load("supply_item")

    # Sort Alphabetically for the AJAX-pulled dropdown
    s3mgr.configure("supply_item",
                    orderby=db.supply_item.name)

    # Defined in the Model for use from Multiple Controllers for unified menus
    return response.s3.supply_item_controller()

# END =========================================================================

