# -*- coding: utf-8 -*-

"""
    Supply

    Generic Supply functionality such as catalogs and items that are used across multiple applications
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# =============================================================================
def index():
    """
        Application Home page
    """

    module_name = settings.modules[c].get("name_nice")
    response.title = module_name
    return {"module_name": module_name,
            }

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
def distribution_rheader(r):
    if r.representation == "html":
        distribution = r.record
        if distribution:
            T = current.T
            tabs = [(T("Edit Details"), None),
                    (T("Beneficiaries"), "person"),
                    ]
            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table

            rheader = DIV(TABLE(TR(TH("%s: " % table.parameter_id.label),
                                   table.parameter_id.represent(distribution.parameter_id),
                                   ),
                                TR(TH("%s: " % table.date.label),
                                   table.date.represent(distribution.date),
                                   ),
                                #TR(TH("%s: " % table.location_id.label),
                                #   table.location_id.represent(distribution.location_id),
                                #   ),
                                #TR(TH("%s: " % table.organisation_id.label),
                                #   table.organisation_id.represent(distribution.organisation_id),
                                #   ),
                                ),
                          rheader_tabs
                          )
            return rheader
    return None

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

    return s3_rest_controller(rheader = distribution_rheader)

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
    from s3db.supply import supply_item_controller
    return supply_item_controller()

# -----------------------------------------------------------------------------
def item_category():
    """ RESTful CRUD controller """

    def prep(r):
        table = s3db.supply_item_category
        if r.get_vars.get("assets") == "1":
            # Category must be one that supports Assets
            f = table.can_be_asset
            # Default anyway
            #f.default = True
            f.readable = f.writable = False

        if r.id:
            # Should not be able to set the Parent to this record
            # @ToDo: Also prevent setting to any of the categories of which this is an ancestor
            from s3db.supply import supply_ItemCategoryRepresent
            the_set = db(table.id != r.id)
            table.parent_item_category_id.requires = IS_EMPTY_OR(
                IS_ONE_OF(the_set, "supply_item_category.id",
                          supply_ItemCategoryRepresent(use_code = False),
                          sort = True,
                          )
                )

        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def item_entity():
    """ RESTful CRUD controller """

    # Defined in the Model for use from Multiple Controllers for unified menus
    from s3db.supply import supply_item_entity_controller
    return supply_item_entity_controller()

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

# -----------------------------------------------------------------------------
def person_item():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def person_item_status():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# END =========================================================================
