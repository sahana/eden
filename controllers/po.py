# -*- coding: utf-8 -*-

"""
    Population Outreach Module - Controllers
"""

module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return {}
    # @todo: swallows error messages
    #return s3db.cms_index(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    redirect(URL(f="household", args="summary"))

# -----------------------------------------------------------------------------
def area():
    """ RESTful Controller for Area Model """

    def prep(r):
        if r.component_name == "organisation":
            # Filter to just referral agencies
            otable = s3db.org_organisation
            rtable = s3db.po_referral_organisation
            atable = s3db.po_organisation_area
            query = (rtable.id != None) & (atable.area_id != r.id)
            left = [rtable.on((rtable.organisation_id == otable.id) & \
                              (rtable.deleted != True)),
                    atable.on((atable.organisation_id == otable.id) & \
                              (atable.deleted != True)),
                    ]
            atable.organisation_id.requires = IS_ONE_OF(
                                    db(query),
                                    "org_organisation.id",
                                    atable.organisation_id.represent,
                                    left=left,
                                    error_message=T("Agency is required")
                                    )
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.po_rheader)

# -----------------------------------------------------------------------------
def household():
    """ RESTful Controller for Household Model """

    def prep(r):

        record = r.record

        if r.component_name == "person":
            # Configure CRUD form and list fields
            crud_form = s3base.S3SQLCustomForm("first_name",
                                               "middle_name",
                                               "last_name",
                                               "gender",
                                               #"age_group", # @todo
                                               )
            list_fields = ["first_name",
                           "middle_name",
                           "last_name",
                           "gender",
                           #"age_group", @todo
                           ]
            s3db.configure("pr_person",
                           crud_form = crud_form,
                           list_fields = list_fields,
                           )
            # Tweak CRUD strings
            crud_strings = s3.crud_strings["pr_person"]
            crud_strings["label_create"] = T("Add Household Member")

        # Filter organisations to just referrals and by area
        # @todo: suppress area filter per deployment setting
        elif record and r.component_name == "organisation_household":

            table = r.component.table
            otable = s3db.org_organisation
            rtable = s3db.po_referral_organisation
            atable = s3db.po_organisation_area

            query = (rtable.id != None) & \
                    ((atable.area_id == record.area_id) |
                     (atable.area_id == None))
            left = [rtable.on((rtable.organisation_id == otable.id) & \
                              (rtable.deleted != True)),
                    atable.on((atable.organisation_id == otable.id) & \
                              (atable.deleted != True)),
                    ]

            table.organisation_id.requires = IS_ONE_OF(
                                    db(query),
                                    "org_organisation.id",
                                    atable.organisation_id.represent,
                                    left=left,
                                    error_message=T("Agency is required")
                                    )

        return True
    s3.prep = prep

    def postp(r, output):
        # Replace normal list button by summary button
        if isinstance(output, dict) and "buttons" in output:
            buttons = output["buttons"]
            if "summary_btn" in buttons:
                buttons["list_btn"] = buttons["summary_btn"]
        return output
    s3.postp = postp

    return s3_rest_controller(rheader = s3db.po_rheader)

# -----------------------------------------------------------------------------
def organisation():
    """ RESTful Controller for Organisation (Referral Agencies) """

    def prep(r):

        # @todo: limit organisation types?
        # @todo: hide unwanted form fields?

        # Filter for just referral agencies
        query = FS("organisation_id:po_referral_organisation.id") != None
        r.resource.add_filter(query)

        # Create referral_organisation record onaccept
        onaccept = s3db.get_config("org_organisation", "onaccept")
        s3db.configure("org_organisation",
                       onaccept = (onaccept, s3db.po_organisation_onaccept))

        # Filter households to areas served (if any areas defined)
        # @todo: suppress this filter per deployment setting
        if r.record and r.component_name == "organisation_household":

            atable = s3db.po_organisation_area
            query = (atable.organisation_id == r.id) & \
                    (atable.deleted != True)
            rows = db(query).select(atable.area_id)
            if rows:
                area_ids = [row.area_id for row in rows]
                area_ids.append(None)
                table = r.component.table
                table.household_id.requires.set_filter(filterby="area_id",
                                                       filter_opts=area_ids,
                                                       )

        if r.interactive:
            # Adapt CRUD Strings
            s3.crud_strings["org_organisation"].update(
                {"label_create": T("Create Agency"),
                 "title_list": T("Referral Agencies"),
                 "title_display": T("Agency Details"),
                 "title_update": T("Edit Agency Details"),
                 "label_delete_button": T("Delete Agency"),
                 }
            )
            if r.component_name == "area":
                s3.crud_strings["po_organisation_area"].update(
                    {"label_create": T("Add Area"),
                     }
                )

        return True
    s3.prep = prep

    return s3_rest_controller("org", "organisation",
                              rheader = s3db.po_rheader)

# -----------------------------------------------------------------------------
def organisation_area():
    """ @todo: docstring """

    s3.prep = lambda r: r.representation == "s3json" and r.method == "options"
    return s3_rest_controller()

# END =========================================================================
