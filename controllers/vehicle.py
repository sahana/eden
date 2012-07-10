# -*- coding: utf-8 -*-

"""
    Vehicle Management Functionality

    http://eden.sahanafoundation.org/wiki/BluePrint/Vehicle
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# Vehicle Module depends on Assets
if not settings.has_module("asset"):
    raise HTTP(404, body="Module disabled: %s" % "asset")

# -----------------------------------------------------------------------------
def index():
    """ Module Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name

    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def create():
    """ Redirect to vehicle/create """
    redirect(URL(f="vehicle", args="create"))

# -----------------------------------------------------------------------------
def vehicle():
    """
        RESTful CRUD controller
        Filtered version of the asset_asset resource
    """

    tablename = "asset_asset"
    table = s3db[tablename]

    s3db.configure("vehicle_vehicle",
                    deletable=False)

    # Type is Vehicle
    VEHICLE = s3db.asset_types["VEHICLE"]
    field = table.type
    field.default = VEHICLE
    field.readable = False
    field.writable = False

    # Only show vehicles
    s3.filter = (field == VEHICLE)

    # Remove type from list_fields
    list_fields = s3db.get_config("asset_asset", "list_fields")
    list_fields.remove("type")
    s3db.configure(tablename, list_fields=list_fields)

    field = table.item_id
    field.label = T("Vehicle Type")
    field.comment = S3AddResourceLink(f="item",
                                      # Use this controller for options.json rather than looking for one called 'asset'
                                      vars=dict(parent="vehicle"),
                                      label=T("Add Vehicle Type"),
                                      info=T("Add a new vehicle type"),
                                      title=T("Vehicle Type"),
                                      tooltip=T("Only Items whose Category are of type 'Vehicle' will be seen in the dropdown."))

    # Only select from vehicles
    field.widget = None # We want a simple dropdown
    ctable = s3db.supply_item_category
    itable = s3db.supply_item
    query = (ctable.is_vehicle == True) & \
            (itable.item_category_id == ctable.id)
    field.requires = IS_ONE_OF(db(query),
                               "supply_item.id",
                               "%(name)s",
                               sort=True)
    # Label changes
    table.sn.label = T("License Plate")
    s3db.asset_log.room_id.label = T("Parking Area")

    # CRUD strings
    ADD_VEHICLE = T("Add Vehicle")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_VEHICLE,
        title_display = T("Vehicle Details"),
        title_list = T("Vehicles"),
        title_update = T("Edit Vehicle"),
        title_search = T("Search Vehicles"),
        title_map = T("Map of Vehicles"),
        subtitle_create = T("Add New Vehicle"),
        label_list_button = T("List Vehicles"),
        label_create_button = ADD_VEHICLE,
        label_delete_button = T("Delete Vehicle"),
        msg_record_created = T("Vehicle added"),
        msg_record_modified = T("Vehicle updated"),
        msg_record_deleted = T("Vehicle deleted"),
        msg_list_empty = T("No Vehicles currently registered"))

    # Tweak the search method labels
    vehicle_search = s3base.S3Search(
        # Advanced Search only
        advanced=(s3base.S3SearchSimpleWidget(
                    name="vehicle_search_text",
                    label=T("Search"),
                    comment=T("Search for a vehicle by text."),
                    field=[
                            "number",
                            "item_id$name",
                            #"item_id$category_id$name",
                            "comments"
                        ]
                  ),
                s3base.S3SearchOptionsWidget(
                    name="vehicle_search_location",
                    field="L1",
                    location_level="L1",
                    cols = 3
                ),
                s3base.S3SearchLocationWidget(
                    name="vehicle_search_map",
                    label=T("Map"),
                ),
        ))
    s3db.configure(tablename,
                    search_method = vehicle_search)

    # Defined in Model
    return s3db.asset_controller()

# =============================================================================
def item():
    """ RESTful CRUD controller """

    # Filter to just Vehicles
    table = s3db.supply_item
    ctable = s3db.supply_item_category
    s3.filter = (table.item_category_id == ctable.id) & \
                (ctable.is_vehicle == True)

    # Limit the Categories to just those with vehicles in
    # - make category mandatory so that filter works
    field = s3db.supply_item.item_category_id
    field.requires = IS_ONE_OF(db,
                               "supply_item_category.id",
                               s3db.supply_item_category_represent,
                               sort=True,
                               filterby = "is_vehicle",
                               filter_opts = [True]
                               )

    field.label = T("Vehicle Categories")
    field.comment = S3AddResourceLink(f="item_category",
                                      label=T("Add Vehicle Category"),
                                      info=T("Add a new vehicle category"),
                                      title=T("Vehicle Category"),
                                      tooltip=T("Only Categories of type 'Vehicle' will be seen in the dropdown."))

    # CRUD strings
    ADD_ITEM = T("Add New Vehicle Type")
    s3.crud_strings["supply_item"] = Storage(
        title_create = ADD_ITEM,
        title_display = T("Vehicle Type Details"),
        title_list = T("Vehicle Types"),
        title_update = T("Edit Vehicle Type"),
        title_search = T("Search Vehicle Types"),
        subtitle_create = T("Add New Vehicle Type"),
        label_list_button = T("List Vehicle Types"),
        label_create_button = ADD_ITEM,
        label_delete_button = T("Delete Vehicle Type"),
        msg_record_created = T("Vehicle Type added"),
        msg_record_modified = T("Vehicle Type updated"),
        msg_record_deleted = T("Vehicle Type deleted"),
        msg_list_empty = T("No Vehicle Types currently registered"),
        msg_match = T("Matching Vehicle Types"),
        msg_no_match = T("No Matching Vehicle Types")
        )

    # Defined in the Model for use from Multiple Controllers for unified menus
    return s3db.supply_item_controller()

# =============================================================================
def item_category():
    """ RESTful CRUD controller """

    table = s3db.supply_item_category

    # Filter to just Vehicles
    s3.filter = (table.is_vehicle == True)

    # Default to Vehicles
    field = table.can_be_asset
    field.readable = field.writable = False
    field.default = True
    field = table.is_vehicle
    field.readable = field.writable = False
    field.default = True

    return s3_rest_controller("supply", "item_category")

# END =========================================================================
