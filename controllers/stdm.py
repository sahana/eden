# -*- coding: utf-8 -*-

"""
    Social Tenure Domain Model
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return s3db.cms_index(module)

# -----------------------------------------------------------------------------
def location():
    """ RESTful CRUD controller """

    location_hierarchy = gis.get_location_hierarchy()
    from s3 import S3TextFilter, S3OptionsFilter#, S3LocationFilter
    search_fields = ["name",
                     "comments",
                     "tag.value",
                     ]
    if settings.get_L10n_translate_gis_location():
        search_fields.append("name.name_l10n")
    if settings.get_L10n_name_alt_gis_location():
        search_fields.append("name_alt.name_alt")

    filter_level_widgets = []
    for level, level_label in location_hierarchy.items():
        search_fields.append(level)
        hidden = False if level == "L0" else True
        filter_level_widgets.append(S3OptionsFilter(level,
                                                    label = level_label,
                                                    #cols = 5,
                                                    hidden = hidden,
                                                    ))

    filter_widgets = [
        S3TextFilter(search_fields,
                     label = T("Search"),
                     comment = T("To search for a location, enter the name. You may use % as wildcard. Press 'Search' without input to list all locations."),
                     #_class = "filter-search",
                     ),
        S3OptionsFilter("level",
                        label = T("Level"),
                        options = location_hierarchy,
                        #hidden = True,
                        ),
        # @ToDo: Hierarchical filter working on id
        #S3LocationFilter("id",
        #                label = T("Location"),
        #                levels = ("L0", "L1", "L2", "L3",),
        #                #hidden = True,
        #                ),
        ]
    filter_widgets.extend(filter_level_widgets)

    s3db.configure("gis_location",
                   filter_widgets = filter_widgets,
                   # Don't include Bulky Location Selector in List Views
                   listadd = False,
                   )

    return s3_rest_controller("gis", resourcename,
                              rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def person():
    """ RESTful CRUD controller """

    s3db.set_method("pr", resourcename,
                    method = "contacts",
                    action = s3db.pr_Contacts)

    return s3_rest_controller("pr", resourcename,
                              rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def group():
    """ RESTful CRUD controller """

    return s3_rest_controller("pr", resourcename,
                              rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def tenure():
    """
        RESTful CRUD controller
        - not yet sure what this will be used for...probably reporting, maybe mapping
    """

    return s3_rest_controller(rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def tenure_role():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def tenure_type():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# END =========================================================================
