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

    def prep(r):
        if r.component_name == "group_membership":

            from s3 import IS_ADD_PERSON_WIDGET2, S3AddPersonWidget2, S3SQLCustomForm

            table = s3db.pr_group_membership
            f = table.person_id
            f.requires = IS_ADD_PERSON_WIDGET2()
            f.widget = S3AddPersonWidget2(controller="stdm")

            # @ToDo: This should only be for the Informal Settlement profile
            f = table.role_id
            f.readable = f.writable = True
            f.label = T("Household Relation")
            f.comment = S3PopupLink(c = "stdm",
                                    f = "group_member_role",
                                    label = T("Create Household Relation"),
                                    vars = {"child": "role_id"},
                                    )

            list_fields = ["person_id",
                           "role_id",
                           ]

            crud_form = S3SQLCustomForm("person_id",
                                        "role_id",
                                        )

            s3db.configure("pr_group_membership",
                           crud_form = crud_form,
                           list_fields = list_fields,
                           )
        return True
    s3.prep = prep

    return s3_rest_controller("pr", resourcename,
                              rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def group_member_role():
    """ RESTful CRUD controller """

    f = s3db.pr_group_member_role.group_type
    f.readable = f.writable = False

    s3.crud_strings["pr_group_member_role"] = Storage(
        label_create = T("Create Household Relation"),
        title_display = T("Household Relation Details"),
        title_list = T("Household Relations"),
        title_update = T("Edit Household Relations"),
        label_list_button = T("List Household Relations"),
        label_delete_button = T("Delete Household Relation"),
        msg_record_created = T("Household Relation added"),
        msg_record_modified = T("Household Relation updated"),
        msg_record_deleted = T("Household Relation deleted"),
        msg_list_empty = T("No Household Relations currently defined"),
    )

    return s3_rest_controller("pr", resourcename,
                              #rheader = s3db.stdm_rheader,
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
