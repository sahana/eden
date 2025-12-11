"""
    REQ module customisations for DIRECT

    License: MIT
"""

from collections import OrderedDict

from gluon import current

from core import CustomForm, \
                 DateFilter, LocationFilter, OptionsFilter, TextFilter, \
                 get_filter_options

# =============================================================================
def req_need_resource(r, tablename):

    pass

# -----------------------------------------------------------------------------
def req_need_controller(**attr):

    T = current.T
    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def prep(r):
        # Call standard prep
        result = standard_prep(r) if callable(standard_prep) else True

        resource = r.resource
        if not r.component:

            table = resource.table
            field = table.contact_organisation_id
            field.readable = field.writable = True

            # CRUD Form
            crud_form = CustomForm(
                           # --- Contact ---
                           "contact_organisation_id",
                           "contact_name",
                           "contact_phone",

                           # --- Location ---
                           "site_name",
                           "site_type_id",
                           "location_id",

                           # --- Situation ---
                           "refno",
                           "date",
                           "name",
                           "description",

                           # --- Response Management ---
                           "organisation_id",
                           "priority",
                           "status",

                           "comments",
                           )

            subheadings = {"contact_organisation_id": T("Contact"),
                           "site_name": T("Location"),
                           "date": T("Situation"),
                           "organisation_id": T("Response Management"),
                           }

            # List fields
            list_fields = ["date",
                           "priority",
                           "refno",
                           "site_name",
                           "location_id",
                           "name",
                           # "contact_organisation_id",
                           # "contact_name",
                           # "contact_phone",
                           "status",
                           "comments",
                           ]

            from s3db.req import need_priority_opts, req_status_opts

            # Filters
            filter_widgets = [TextFilter(["refno",
                                          "name",
                                          "description",
                                          "contact_name",
                                          "comments",
                                          ],
                                         label = T("Search"),
                                         ),
                               OptionsFilter("site_type_id",
                                             label = T("Site Type"),
                                             options = lambda: get_filter_options("req_need_site_type"),
                                             ),
                               LocationFilter("location_id",
                                              label = T("Location"),
                                              levels = ["L2", "L3"],
                                              ),
                               DateFilter("date",
                                          hide_time = True,
                                          hidden = True,
                                          ),
                               OptionsFilter("priority",
                                             options = OrderedDict(need_priority_opts()),
                                             sort = False,
                                             cols = 4,
                                             hidden = True,
                                             ),
                               OptionsFilter("contact_organisation_id",
                                             hidden = True,
                                             ),
                               OptionsFilter("status",
                                             options = OrderedDict(req_status_opts()),
                                             sort = False,
                                             cols = 3,
                                             hidden = True,
                                             ),
                              ]

            # Reconfigure resource
            resource.configure(crud_form = crud_form,
                               filter_widgets = filter_widgets,
                               subheadings = subheadings,
                               list_fields = list_fields,
                               )

        return result
    s3.prep = prep

    from ..rheaders import req_rheader
    attr["rheader"] = req_rheader

    return attr

# -----------------------------------------------------------------------------
def req_need_service_controller(**attr):

    T = current.T
    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def prep(r):
        # Call standard prep
        result = standard_prep(r) if callable(standard_prep) else True

        resource = r.resource
        if not r.component:

            from s3db.req import need_priority_opts, req_status_opts

            # Filters
            filter_widgets = [TextFilter(["details",
                                          ],
                                         label = T("Search"),
                                         ),
                               OptionsFilter("priority",
                                             options = OrderedDict(need_priority_opts()),
                                             sort = False,
                                             cols = 4,
                                             ),
                               DateFilter("need_id$date",
                                          hide_time = True,
                                          hidden = True,
                                          ),
                               OptionsFilter("need_id$site_type_id",
                                             label = T("Site Type"),
                                             options = lambda: get_filter_options("req_need_site_type"),
                                             hidden = True,
                                             ),
                               LocationFilter("need_id$location_id",
                                              label = T("Location"),
                                              levels = ["L2", "L3"],
                                             hidden = True,
                                              ),
                               OptionsFilter("service_id",
                                             options = lambda: get_filter_options("org_service"),
                                             hidden = True,
                                             ),
                               OptionsFilter("status",
                                             options = OrderedDict(req_status_opts()),
                                             sort = False,
                                             cols = 3,
                                             hidden = True,
                                             ),
                              ]

            # Reconfigure resource
            resource.configure(filter_widgets = filter_widgets,
                               )

        return result
    s3.prep = prep

    from ..rheaders import req_rheader
    attr["rheader"] = req_rheader

    return attr

# END =========================================================================
