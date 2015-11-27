# -*- coding: utf-8 -*-

module = request.controller
resourcename = request.function

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

    # Just redirect to the person list
    s3_redirect_default(URL(f="person"))

# -----------------------------------------------------------------------------
def person():
    """ Persons: RESTful CRUD Controller """

    # Set the default case status
    default_status = s3db.dvr_case_default_status()

    def prep(r):

        # Filter to persons who have a case registered
        resource = r.resource
        resource.add_filter(FS("dvr_case.id") != None)

        if r.component and r.id:
            ctable = r.component.table
            if "case_id" in ctable.fields and \
               str(ctable.case_id.type)[:18] == "reference dvr_case":

                # Find the Case ID
                dvr_case = s3db.dvr_case
                query = (dvr_case.person_id == r.id) & \
                        (dvr_case.deleted != True)
                cases = db(query).select(dvr_case.id, limitby=(0, 2))

                case_id = ctable.case_id
                if cases:
                    # Set default
                    case_id.default = cases.first().id
                if len(cases) == 1:
                    # Only one case => hide case selector
                    case_id.readable = case_id.writable = False
                else:
                    # Configure case selector
                    case_id.requires = IS_ONE_OF(db(query), "dvr_case.id",
                                                 case_id.represent,
                                                 )

        if r.interactive:

            # Adapt CRUD strings to context
            s3.crud_strings["pr_person"] = Storage(
                label_create = T("Create Case"),
                title_display = T("Case Details"),
                title_list = T("Cases"),
                title_update = T("Edit Case Details"),
                label_list_button = T("List Cases"),
                label_delete_button = T("Delete Case"),
                msg_record_created = T("Case added"),
                msg_record_modified = T("Case details updated"),
                msg_record_deleted = T("Case deleted"),
                msg_list_empty = T("No Cases currently registered")
                )

            if not r.component:
                # Module-specific CRUD form
                # NB: this assumes single case per person, must use
                #     case perspective (dvr/case) for multiple cases
                #     per person!
                from s3 import S3SQLCustomForm, S3SQLInlineComponent
                crud_form = S3SQLCustomForm(
                                "dvr_case.reference",
                                "dvr_case.organisation_id",
                                "dvr_case.date",
                                "dvr_case.status_id",
                                "first_name",
                                "middle_name",
                                "last_name",
                                "date_of_birth",
                                "gender",
                                S3SQLInlineComponent(
                                        "contact",
                                        fields = [("", "value"),
                                                  ],
                                        filterby = {"field": "contact_method",
                                                    "options": "EMAIL",
                                                    },
                                        label = T("Email"),
                                        multiple = False,
                                        name = "email",
                                        ),
                                S3SQLInlineComponent(
                                        "contact",
                                        fields = [("", "value"),
                                                  ],
                                        filterby = {"field": "contact_method",
                                                    "options": "SMS",
                                                    },
                                        label = T("Mobile Phone"),
                                        multiple = False,
                                        name = "phone",
                                        ),
                                "person_details.nationality",
                                S3SQLInlineComponent(
                                        "address",
                                        label = T("Current Address"),
                                        fields = [("", "location_id"),
                                                  ],
                                        filterby = {"field": "type",
                                                    "options": "1",
                                                    },
                                        link = False,
                                        multiple = False,
                                        ),
                                "dvr_case.comments",
                                )

                # Module-specific filter widgets
                from s3 import get_s3_filter_opts, S3TextFilter, S3OptionsFilter
                filter_widgets = [
                    S3TextFilter(["pe_label",
                                  "first_name",
                                  "middle_name",
                                  "last_name",
                                  #"email.value",
                                  #"phone.value",
                                  "dvr_case.reference",
                                  ],
                                  label = T("Search"),
                                  comment = T("You can search by name, ID or case number"),
                                  ),
                    S3OptionsFilter("dvr_case.status_id",
                                    cols = 3,
                                    default = default_status,
                                    #label = T("Case Status"),
                                    options = s3db.dvr_case_status_filter_opts,
                                    sort = False,
                                    ),
                    S3OptionsFilter("person_details.nationality",
                                    ),
                    ]

                resource.configure(crud_form = crud_form,
                                   filter_widgets = filter_widgets,
                                   )

        # Module-specific list fields (must be outside of r.interactive)
        list_fields = ["dvr_case.reference",
                       "first_name",
                       "middle_name",
                       "last_name",
                       "date_of_birth",
                       "gender",
                       "dvr_case.date",
                       "dvr_case.status_id",
                       ]
        resource.configure(list_fields = list_fields,
                           )

        return True
    s3.prep = prep

    return s3_rest_controller("pr", "person", rheader = s3db.dvr_rheader)

# -----------------------------------------------------------------------------
def group_membership():
    """
        RESTful CRUD controller for person<=>group links, normally called
        only from component tab in person perspective (e.g. family members)
    """

    def prep(r):

        table = r.table
        resource = r.resource

        get_vars = r.get_vars
        if "viewing" in get_vars:

            try:
                vtablename, record_id = get_vars["viewing"].split(".")
            except ValueError:
                return False

            if vtablename == "pr_person":
                # Get all group_ids with this person_id
                gtable = s3db.pr_group
                join = gtable.on(gtable.id == table.group_id)
                query = (table.person_id == record_id) & \
                        (gtable.group_type == 7) & \
                        (table.deleted != True)
                rows = db(query).select(table.group_id,
                                        join=join,
                                        )
                group_ids = set(row.group_id for row in rows)
                # Hide the link for this person (to prevent changes/deletion)
                if group_ids:
                    # Single group ID?
                    group_id = tuple(group_ids)[0] if len(group_ids) == 1 else None
                else:
                    group_id = gtable.insert(name = record_id,
                                             group_type = 7,
                                             )
                    table.insert(group_id = group_id,
                                 person_id = record_id,
                                 )
                    group_ids = set((group_id,))
                resource.add_filter(FS("person_id") != record_id)
            else:
                group_ids = set()


            # Show only links for relevant cases
            # NB Filter also prevents showing all links if case_ids is empty
            if not r.id:
                if len(group_ids) == 1:
                    r.resource.add_filter(FS("group_id") == group_id)
                else:
                    r.resource.add_filter(FS("group_id").belongs(group_ids))

            list_fields = ["person_id",
                           "person_id$gender",
                           "person_id$date_of_birth",
                           ]

            if len(group_ids) == 1:
                field = table.group_id
                field.default = group_id
                # If we have only one relevant case, then hide the group ID
                # in create-forms:
                if not r.id:
                    field.readable = field.writable = False
            else:
                # Show the case ID in list fields if there is more than one
                # relevant case
                list_fields.insert(0, "group_id")
            r.resource.configure(list_fields = list_fields)

        # Do not allow update of person_id
        if r.id:
            field = table.person_id
            field.writable = False
            field.comment = None

        return True
    s3.prep = prep

    # Disable unwanted fields in person widget (can override in template)
    settings.pr.request_email = False
    settings.pr.request_home_phone = False
    settings.hrm.email_required = False

    return s3_rest_controller("pr", "group_membership",
                              rheader = s3db.dvr_rheader,
                              )

# -----------------------------------------------------------------------------
def case_activity():
    """ Case Activities: RESTful CRUD Controller """

    def prep(r):

        resource = r.resource
        list_fields = ["case_id$reference",
                       "person_id$first_name",
                       "person_id$last_name",
                       "need_id",
                       "need_details",
                       "emergency",
                       "referral_details",
                       "followup",
                       "followup_date",
                       "completed",
                       ]
        resource.configure(list_fields = list_fields,
                           insertable = False,
                           deletable = False,
                           )
        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def case_status():
    """ Case Statuses: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def case_type():
    """ Case Types: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def case_appointment_type():
    """ Appointment Type: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def case():
    """ Cases: RESTful CRUD Controller """

    s3db.dvr_case_default_status()

    return s3_rest_controller(rheader = s3db.dvr_rheader)

# -----------------------------------------------------------------------------
def need():
    """ Needs: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def housing():
    """ Housing: RESTful CRUD Controller for option lookups """

    s3.prep = lambda r: r.method == "options" and \
                        r.representation == "s3json"

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def housing_type():
    """ Housing Types: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def beneficiary_data():
    """ Beneficiary Data: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def beneficiary_type():
    """ Beneficiary Types: RESTful CRUD Controller """

    return s3_rest_controller()

# END =========================================================================
