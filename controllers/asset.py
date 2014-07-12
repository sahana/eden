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
    """ Module's Home Page """

    return s3db.cms_index(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the list of Assets
    redirect(URL(f="asset"))

# -----------------------------------------------------------------------------
def create():
    """ Redirect to asset/create """

    redirect(URL(f="asset", args="create"))

# -----------------------------------------------------------------------------
def asset():
    """ RESTful CRUD controller """

    # Use the item() controller in this module to set options correctly
    s3db.asset_asset.item_id.comment = S3AddResourceLink(f="item",
        label=T("Create Item"),
        title=T("Item"),
        tooltip=T("Type the name of an existing catalog item OR Click 'Create Item' to add an item which is not in the catalog."))

    # Defined in Model for use from Multiple Controllers for unified menus
    return s3db.asset_controller()

# -----------------------------------------------------------------------------
def brand():
    """ RESTful CRUD controller """

    return s3_rest_controller("supply", "brand")

# -----------------------------------------------------------------------------
def catalog():
    """ RESTful CRUD controller """

    return s3_rest_controller("supply", "catalog",
                              rheader = s3db.supply_catalog_rheader,
                              )

# -----------------------------------------------------------------------------
def item():
    """ RESTful CRUD controller """

    if "catalog_item" not in request.args:
        # Filter to just Assets
        table = s3db.supply_item
        ctable = s3db.supply_item_category
        s3.filter = (table.item_category_id == ctable.id) & \
                    (ctable.can_be_asset == True)

        # Limit the Categories to just those which can be Assets
        # - make category mandatory so that filter works
        field = s3db.supply_item.item_category_id
        field.requires = IS_ONE_OF(db,
                                   "supply_item_category.id",
                                   s3db.supply_item_category_represent,
                                   sort=True,
                                   filterby = "can_be_asset",
                                   filter_opts = (True,)
                                   )
                    
        field.comment = S3AddResourceLink(f="item_category",
                                          label=T("Create Item Category"),
                                          title=T("Item Category"),
                                          tooltip=T("Only Categories of type 'Asset' will be seen in the dropdown."))

    # Defined in the Model for use from Multiple Controllers for unified menus
    return s3db.supply_item_controller()

# -----------------------------------------------------------------------------
def catalog_item():
    """
        RESTful CRUD controller
        - used for Imports
    """

    return s3_rest_controller("supply", "catalog_item",
                              csv_template = ("supply", "catalog_item"),
                              csv_stylesheet = ("supply", "catalog_item.xsl"),
                              )

# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
def supplier():
    """ RESTful CRUD controller """

    get_vars["organisation_type.name"] = "Supplier"

    # Load model
    table = s3db.org_organisation

    # Modify CRUD Strings
    s3.crud_strings.org_organisation = Storage(
        label_create = T("Create Supplier"),
        title_display = T("Supplier Details"),
        title_list = T("Suppliers"),
        title_update = T("Edit Supplier"),
        title_upload = T("Import Suppliers"),
        label_list_button = T("List Suppliers"),
        label_delete_button = T("Delete Supplier"),
        msg_record_created = T("Supplier added"),
        msg_record_modified = T("Supplier updated"),
        msg_record_deleted = T("Supplier deleted"),
        msg_list_empty = T("No Suppliers currently registered")
        )

    # Modify filter_widgets
    filter_widgets = s3db.get_config("org_organisation", "filter_widgets")
    # Remove type (always 'Supplier')
    filter_widgets.pop(1)
    # Remove sector (not relevant)
    filter_widgets.pop(1)

    return s3db.org_organisation_controller()

# END =========================================================================
