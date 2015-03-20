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

    return s3db.cms_index(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    redirect(URL(f="household", args="summary"))

# -----------------------------------------------------------------------------
def area():
    """ RESTful Controller for Area Model """

    return s3_rest_controller(rheader = s3db.po_rheader)

# -----------------------------------------------------------------------------
def household():
    """ RESTful Controller for Household Model """

    def prep(r):
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

# END =========================================================================
