# -*- coding: utf-8 -*-

"""
    Asset Management Functionality

    http://eden.sahanafoundation.org/wiki/BluePrint/Assets
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name

    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def create():
    """ Redirect to asset/create """

    redirect(URL(f="asset", args="create"))

# -----------------------------------------------------------------------------
def asset():
    """ RESTful CRUD controller """

    # Use the item() controller in this module to set options correctly
    s3db.asset_asset.item_id.comment = S3AddResourceLink(f="item",
        label=T("Add New Item"),
        title=T("Item"),
        tooltip=T("Type the name of an existing catalog item OR Click 'Add New Item' to add an item which is not in the catalog."))

    # Defined in Model for use from Multiple Controllers for unified menus
    return s3db.asset_controller()

# =============================================================================
def supplier():
    """
        REST controller
    """

    request.get_vars["organisation.organisation_type_id$name"] = "Supplier"
    return s3db.org_organisation_controller()

# =============================================================================
def item():
    """ RESTful CRUD controller """

    # Filter to just Assets
    table = s3db.supply_item
    ctable = s3db.supply_item_category
    s3.filter = (table.item_category_id == ctable.id) & \
                (ctable.can_be_asset == True)

    # Limit the Categories to just those with vehicles in
    # - make category mandatory so that filter works
    field = s3db.supply_item.item_category_id
    field.requires = IS_ONE_OF(db,
                               "supply_item_category.id",
                               s3db.supply_item_category_represent,
                               sort=True,
                               filterby = "can_be_asset",
                               filter_opts = [True]
                               )
                
    field.comment = S3AddResourceLink(f="item_category",
                                      label=T("Add Item Category"),
                                      title=T("Item Category"),
                                      tooltip=T("Only Categories of type 'Vehicle' will be seen in the dropdown."))

    # Defined in the Model for use from Multiple Controllers for unified menus
    return s3db.supply_item_controller()

# =============================================================================
def item_category():
    """ RESTful CRUD controller """

    table = s3db.supply_item_category

    # Filter to just Assets
    s3.filter = (table.can_be_asset == True)

    # Default to Assets
    field = table.can_be_asset
    field.readable = field.writable = False
    field.default = True
    
    return s3_rest_controller("supply", "item_category")

# END =========================================================================
