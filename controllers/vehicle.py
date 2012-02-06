# -*- coding: utf-8 -*-

"""
    Vehicle Management Functionality

    http://eden.sahanafoundation.org/wiki/BluePrint/Vehicle
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# Vehicle Module depends on Assets
if not deployment_settings.has_module("asset"):
    raise HTTP(404, body="Module disabled: %s" % "asset")

s3_menu(module)

# -----------------------------------------------------------------------------
def index():
    """ Module Home Page """

    module_name = deployment_settings.modules[module].name_nice
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

    s3mgr.configure("vehicle_vehicle",
                    deletable=False)

    # Type is Vehicle
    VEHICLE = s3db.asset_types["VEHICLE"]
    field = table.type
    field.default = VEHICLE
    field.readable = False
    field.writable = False

    # Only show vehicles
    response.s3.filter = (field == VEHICLE)

    # Remove type from list_fields
    list_fields = s3mgr.model.get_config("asset_asset", "list_fields")
    list_fields.remove("type")
    s3mgr.configure(tablename, list_fields=list_fields)

    # Only select from vehicles
    field = table.item_id
    field.label = T("Vehicle Type")
    field.comment = DIV(A(T("Add Vehicle Type"),
                          _class="colorbox",
                          _href=URL(c="supply", f="item", args="create",
                                    vars=dict(format="popup", vehicle="1")),
                          _target="top", _title=T("Add a new vehicle type")),
                        DIV(_class="tooltip",
                            _title="%s|%s" % (T("Vehicle Type"),
                                              T("Only Items whose Category are of type 'Vehicle' will be seen in the dropdown."))))
    field.widget = None # We want a simple dropdown
    ctable = s3db.supply_item_category
    itable = s3db.supply_item
    query = (ctable.is_vehicle == True) & \
            (itable.item_category_id == ctable.id)
    field.requires = IS_ONE_OF(db(query),
                               "supply_item.id",
                               "%(name)s",
                               sort=True,
                            )
    # Label changes
    table.sn.label = T("License Plate")
    s3db.asset_log.room_id.label = T("Parking Area")

    # CRUD strings
    ADD_VEHICLE = T("Add Vehicle")
    LIST_VEHICLE = T("List Vehicles")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_VEHICLE,
        title_display = T("Vehicle Details"),
        title_list = LIST_VEHICLE,
        title_update = T("Edit Vehicle"),
        title_search = T("Search Vehicles"),
        subtitle_create = T("Add New Vehicle"),
        subtitle_list = T("Vehicles"),
        label_list_button = LIST_VEHICLE,
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
                s3base.S3SearchLocationHierarchyWidget(
                    name="vehicle_search_location",
                    comment=T("Search for vehicle by location."),
                    represent ="%(name)s",
                    cols = 3
                ),
                s3base.S3SearchLocationWidget(
                    name="vehicle_search_map",
                    label=T("Map"),
                ),
        ))
    s3mgr.configure(tablename,
                    search_method = vehicle_search)

    # Defined in Model
    return asset_controller()

# END =========================================================================

