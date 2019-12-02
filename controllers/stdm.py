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

            from s3 import S3AddPersonWidget, S3SQLCustomForm

            table = s3db.pr_group_membership
            f = table.person_id
            f.widget = S3AddPersonWidget(controller="stdm")

            if auth.s3_has_role("INFORMAL_SETTLMENT"):
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
            else:
                list_fields = ["person_id",
                               ]

                crud_form = S3SQLCustomForm("person_id",
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
def profile():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def tenure():
    """ RESTful CRUD controller """

    def prep(r):

        has_role = auth.s3_has_role
        if has_role("ADMIN"):
            # Unfiltered
            pass

        else:
            ptable = s3db.stdm_profile
            if has_role("INFORMAL_SETTLEMENT"):
                profile = db(ptable.name == "Informal Settlement").select(ptable.id,
                                                                          limitby=(0, 1)
                                                                          ).first()
                try:
                    filter_opts = (profile.id,)
                except:
                    filter_opts = ()
            elif has_role("RURAL_AGRICULTURE"):
                profile = db(ptable.name == "Rural Agriculture").select(ptable.id,
                                                                        limitby=(0, 1)
                                                                        ).first()
                try:
                    filter_opts = (profile.id,)
                except:
                    filter_opts = ()
            elif has_role("LOCAL_GOVERNMENT"):
                profile = db(ptable.name == "Local Government").select(ptable.id,
                                                                       limitby=(0, 1)
                                                                       ).first()
                try:
                    filter_opts = (profile.id,)
                except:
                    filter_opts = ()
            else:
                # Shouldn't ever get here
                filter_opts = ()

            f = s3db.stdm_tenure_relationship.tenure_type_id
            v = f.requires.other
            v.set_filter(filterby = "profile_id",
                         filter_opts = filter_opts)
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def tenure_type():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def parcel():
    """ RESTful CRUD controller """

    def postp(r, output):
        if r.interactive and r.component_name == "tenure":
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons
            s3.actions += [{"label": s3_str(T("Certificate")),
                            "_class": "action-btn",
                            "url": URL(f = "tenure",
                                       args = ["[id]", "certificate"],
                                       ),
                            },
                           ]

        return output
    s3.postp = postp

    return s3_rest_controller(rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def parcel_type():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def landuse():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def dispute():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def job_title():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def surveyor():
    """ RESTful CRUD controller """

    return s3_rest_controller(rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def planner():
    """ RESTful CRUD controller """

    return s3_rest_controller(rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def gov_survey():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def ownership_type():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def recognition_status():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def structure():
    """ RESTful CRUD controller """

    def postp(r, output):
        if r.interactive and r.component_name == "tenure":
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons
            s3.actions += [{"label": s3_str(T("Certificate")),
                            "_class": "action-btn",
                            "url": URL(f = "tenure",
                                       args = ["[id]", "certificate"],
                                       ),
                            },
                           ]

        return output
    s3.postp = postp

    return s3_rest_controller(rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def garden():
    """ RESTful CRUD controller """

    def postp(r, output):
        if r.interactive and r.component_name == "tenure":
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons
            s3.actions += [{"label": s3_str(T("Certificate")),
                            "_class": "action-btn",
                            "url": URL(f = "tenure",
                                       args = ["[id]", "certificate"],
                                       ),
                            },
                           ]

        return output
    s3.postp = postp

    return s3_rest_controller(rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def socioeconomic_impact():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def input_service():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def farmer():
    """ RESTful CRUD controller """

    return s3_rest_controller(rheader = s3db.stdm_rheader,
                              )

# -----------------------------------------------------------------------------
def rural_survey():
    """ RESTful CRUD controller """

    return s3_rest_controller(#rheader = s3db.stdm_rheader,
                              )

# END =========================================================================
