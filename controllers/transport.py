# -*- coding: utf-8 -*-

"""
    Transport
"""

module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    "Module's Home Page"

    return s3db.cms_index(module)

# -----------------------------------------------------------------------------
def airport():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                if r.component.name == "human_resource":
                    s3db.org_site_staff_config(r)
                elif r.component.name == "inv_item":
                    # remove CRUD generated buttons in the tabs
                    s3db.configure("inv_inv_item",
                                   create = False,
                                   deletable = False,
                                   editable = False,
                                   listadd = False,
                                   )
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
        return True
    s3.prep = prep

    return s3_rest_controller(rheader=transport_rheader)

# -----------------------------------------------------------------------------
def heliport():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                if r.component.name == "human_resource":
                    s3db.org_site_staff_config(r)
                elif r.component.name == "inv_item":
                    # remove CRUD generated buttons in the tabs
                    s3db.configure("inv_inv_item",
                                   create = False,
                                   deletable = False,
                                   editable = False,
                                   listadd = False,
                                   )
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
        return True
    s3.prep = prep

    return s3_rest_controller(rheader=transport_rheader)

# -----------------------------------------------------------------------------
def seaport():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                if r.component.name == "human_resource":
                    s3db.org_site_staff_config(r)
                elif r.component.name == "inv_item":
                    # remove CRUD generated buttons in the tabs
                    s3db.configure("inv_inv_item",
                                   create = False,
                                   deletable = False,
                                   editable = False,
                                   listadd = False,
                                   )
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
        return True
    s3.prep = prep

    return s3_rest_controller(rheader=transport_rheader)

# -----------------------------------------------------------------------------
def vehicle():
    """
        RESTful CRUD controller
        Filtered version of the asset_asset resource
    """
    # Vehicle depends upon Asset module
    module = "asset"
    if not settings.has_module(module):
        raise HTTP(404, body="Module disabled: %s" % module)

    tablename = "asset_asset"
    table = s3db[tablename]

    s3db.configure("transport_vehicle",
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
    if "type" in list_fields:
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
        label_create = ADD_VEHICLE,
        title_display = T("Vehicle Details"),
        title_list = T("Vehicles"),
        title_update = T("Edit Vehicle"),
        title_map = T("Map of Vehicles"),
        label_list_button = T("List Vehicles"),
        label_delete_button = T("Delete Vehicle"),
        msg_record_created = T("Vehicle added"),
        msg_record_modified = T("Vehicle updated"),
        msg_record_deleted = T("Vehicle deleted"),
        msg_list_empty = T("No Vehicles currently registered"))

    # Use this controller for options.json rather than looking for one called 'asset'
    field = s3.org_organisation_id
    fcomment = field.attr["comment"]
    comment_vars = fcomment.get("vars")
    comment_vars["parent"] = "vehicle"

    # @ToDo: Tweak the search comment
    
    # Defined in Model
    return s3db.asset_controller()

# =============================================================================
def item():
    """ RESTful CRUD controller """
    
    # Vehicle depends upon Asset module
    module = "asset"
    if not settings.has_module(module):
        raise HTTP(404, body="Module disabled: %s" % module)

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
        label_create = ADD_ITEM,
        title_display = T("Vehicle Type Details"),
        title_list = T("Vehicle Types"),
        title_update = T("Edit Vehicle Type"),
        label_list_button = T("List Vehicle Types"),
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

    # Vehicle depends upon Asset module
    module = "asset"
    if not settings.has_module(module):
        raise HTTP(404, body="Module disabled: %s" % module)

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

# -----------------------------------------------------------------------------
def transport_rheader(r, tabs=[]):

    # Need to use this format as otherwise /inv/incoming?viewing=org_office.x
    # doesn't have an rheader
    tablename, record = s3base.s3_rheader_resource(r)
    r.record = record
    r.table = s3db[tablename]

    tabs = [(T("Details"), None)]
    try:
        tabs = tabs + s3db.req_tabs(r)
    except:
        pass
    try:
        tabs = tabs + s3db.inv_tabs(r)
    except:
        pass
    rheader_fields = [["name"], ["location_id"]]
    rheader = S3ResourceHeader(rheader_fields, tabs)(r)
    return rheader

# END =========================================================================
