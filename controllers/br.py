# -*- coding: utf-8 -*-

"""
    Beneficiary Registry and Case Management Controllers
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return settings.customise_home(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """ Default Module Homepage """

    # Just redirect to the person list
    s3_redirect_default(URL(f="person"))

# =============================================================================
# Beneficiaries
#
def person():
    """ Case File: RESTful CRUD Controller """

    # Set the default case status
    default_status = s3db.br_case_default_status()

    # Set contacts-method for tab
    s3db.set_method("pr", "person",
                    method = "contacts",
                    action = s3db.pr_Contacts,
                    )

    def prep(r):

        # Filter to persons who have a case registered
        resource = r.resource
        resource.add_filter(FS("case.id") != None)

        labels = s3db.br_terminology()
        CASES = labels.CASES

        insertable = True

        if not r.record:

            get_vars = r.get_vars

            # Filter to open/closed cases
            closed = get_vars.get("closed")
            if closed == "1":
                # Only closed cases
                query = FS("case.status_id$is_closed") == True
                CASES = labels.CLOSED
                insertable = False
            elif closed == "0":
                # Only open cases
                query = (FS("case.status_id$is_closed") == False) | \
                        (FS("case.status_id$is_closed") == None)
                CASES = labels.CURRENT
            else:
                query = None

            # TODO mine URL option

            # Filter to valid/invalid cases
            invalid = get_vars.get("invalid")
            if invalid == "1":
                q = FS("case.invalid") == True
                query = query & q if query is not None else q
                CASES = T("Invalid Cases")
                insertable = False
            else:
                q = (FS("case.invalid") == False) | \
                    (FS("case.invalid") == None)
                query = query & q if query is not None else q

            resource.add_filter(query)

        # Adapt CRUD strings to perspective (& terminology)
        crud_strings = s3db.br_crud_strings("pr_person")
        crud_strings.title_list = CASES
        s3.crud_strings["pr_person"] = crud_strings

        # Should not be able to delete records in this view
        resource.configure(deletable = False,
                           insertable = insertable,
                           )

        if not r.component:

            # Adapt fields to module context
            table = resource.table
            ctable = s3db.br_case

            # Configure pe_label
            field = table.pe_label
            field.label = T("ID")
            field.comment = None

            # Make gender mandatory, remove "unknown"
            field = table.gender
            field.default = None
            options = dict(s3db.pr_gender_opts)
            del options[1] # Remove "unknown"
            field.requires = IS_PERSON_GENDER(options, sort=True)

            # Configure case.organisation_id
            field = ctable.organisation_id
            field.comment = None
            if not field.default:
                multiple_orgs = s3db.br_case_read_orgs()[0]
                default_org, selectable = s3db.br_case_default_org()
                if default_org and settings.get_br_case_hide_default_org():
                    field.writable = selectable
                    field.readable = selectable or multiple_orgs
                field.default = default_org
            requires = field.requires
            if isinstance(requires, IS_EMPTY_OR):
                field.requires = requires.other

            # Expose the "invalid"-flag? (update forms only)
            if r.record and r.method != "read":
                field = ctable.invalid
                field.readable = field.writable = True

            # Custom CRUD form
            crud_fields = ["case.date",
                           "case.organisation_id",
                           "case.status_id",
                           "pe_label",
                           # +name fields
                           "gender",
                           "person_details.nationality",
                           "date_of_birth",
                           "person_details.marital_status",
                           s3base.S3SQLInlineComponent(
                                "contact",
                                fields = [("", "value")],
                                filterby = {"field": "contact_method",
                                           "options": "SMS",
                                           },
                                label = T("Mobile Phone"),
                                multiple = False,
                                name = "phone",
                                ),
                           "person_details.literacy",
                           "case.comments",
                           "case.invalid",
                           ]

            # Custom list fields
            list_fields = ["pe_label",
                           # +name fields
                           "gender",
                           "date_of_birth",
                           "person_details.nationality",
                           "case.date",
                           "case.status_id",
                           ]

            # Insert name fields in name-format order
            NAMES = ("first_name", "middle_name", "last_name")
            keys = s3base.StringTemplateParser.keys(settings.get_pr_name_format())
            name_fields = [fn for fn in keys if fn in NAMES]
            crud_fields[3:3] = name_fields
            list_fields[1:1] = name_fields

            # Autocomplete search-method
            if r.function == "person_search":
                # Autocomplete-Widget (e.g. response actions)
                search_fields = tuple(name_fields) + ("pe_label",)
            else:
                # Add-Person-Widget (family members)
                search_fields = tuple(name_fields)
            s3db.set_method("pr", "person",
                            method = "search_ac",
                            action = s3db.pr_PersonSearchAutocomplete(search_fields),
                            )

            resource.configure(crud_form = s3base.S3SQLCustomForm(*crud_fields),
                               list_fields = list_fields,
                               )


        return True
    s3.prep = prep

    return s3_rest_controller("pr", "person", rheader=s3db.br_rheader)

# -----------------------------------------------------------------------------
def person_search():
    """
        RESTful controller for autocomplete-searches
    """

    def prep(r):

        if r.method != "search_ac":
            return False

        # Filter to persons who have a case registered
        resource = r.resource
        resource.add_filter(FS("br_case.id") != None)
        return True

    s3.prep = prep

    return s3_rest_controller("pr", "person")

# -----------------------------------------------------------------------------
def group_membership():
    """
        RESTful CRUD controller for person<=>group links, normally called
        only from component tab in person perspective (e.g. family members)
    """

    def prep(r):

        resource = r.resource
        table = resource.table

        get_vars = r.get_vars
        if "viewing" in get_vars:

            try:
                vtablename, record_id = get_vars["viewing"].split(".")
            except ValueError:
                return False

            if vtablename == "pr_person":

                # Set contacts-method to retain the tab
                s3db.set_method("pr", "person",
                                method = "contacts",
                                action = s3db.pr_Contacts,
                                )

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
                elif r.http == "POST":
                    name = s3_fullname(record_id)
                    group_id = gtable.insert(name = name,
                                             group_type = 7,
                                             )
                    s3db.update_super(gtable, {"id": group_id})
                    table.insert(group_id = group_id,
                                 person_id = record_id,
                                 group_head = True,
                                 )
                    group_ids = set((group_id,))
                resource.add_filter(FS("person_id") != record_id)
            else:
                group_ids = set()

            # Add-Person widget to use BR controller and expose pe_label
            from s3 import S3AddPersonWidget
            field = table.person_id
            field.represent = s3db.pr_PersonRepresent(show_link=True)
            field.widget = S3AddPersonWidget(controller = "br",
                                             pe_label = True,
                                             )

            # Expose Family Member Roles
            ROLE = T("Role")
            field = table.role_id
            field.readable = field.writable = True
            field.label = ROLE
            field.comment = None
            field.requires = IS_EMPTY_OR(
                                IS_ONE_OF(db, "pr_group_member_role.id",
                                          field.represent,
                                          filterby = "group_type",
                                          filter_opts = (7,),
                                          ))

            # Adjust label for group_head
            field = table.group_head
            field.label = T("Head of Family")

            # Show only links for relevant cases
            # NB Filter also prevents showing all links if case_ids is empty
            if not r.id:
                if len(group_ids) == 1:
                    resource.add_filter(FS("group_id") == group_id)
                else:
                    resource.add_filter(FS("group_id").belongs(group_ids))

            # Adjust list-fields for this perspective
            s3db.pr_person.pe_label.label = T("ID")
            list_fields = ["person_id$pe_label",
                           "person_id",
                           "person_id$gender",
                           "person_id$date_of_birth",
                           "group_head",
                           (ROLE, "role_id"),
                           (T("Case Status"), "person_id$dvr_case.status_id"),
                           ]

            if len(group_ids) == 0:
                # No case group exists, will be auto-generated on POST,
                # hide the field in the form:
                field = table.group_id
                field.readable = field.writable = False
            elif len(group_ids) == 1:
                field = table.group_id
                field.default = group_id
                # If we have only one relevant case, then hide the group ID:
                field.readable = field.writable = False
            elif len(group_ids) > 1:
                # Show the case ID in list fields if there is more than one
                # relevant case
                list_fields.insert(0, "group_id")
            resource.configure(filter_widgets = None,
                               list_fields = list_fields,
                               )

            # Adjust CRUD strings for this perspective
            s3.crud_strings["pr_group_membership"] = Storage(
                label_create = T("Add Family Member"),
                title_display = T("Family Member Details"),
                title_list = T("Family Members"),
                title_update = T("Edit Family Member"),
                label_list_button = T("List Family Members"),
                label_delete_button = T("Remove Family Member"),
                msg_record_created = T("Family Member added"),
                msg_record_modified = T("Family Member updated"),
                msg_record_deleted = T("Family Member removed"),
                msg_list_empty = T("No Family Members currently registered")
                )

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
                              rheader = s3db.br_rheader,
                              )

# =============================================================================
# Look-up Tables
#
def case_status():
    """ Case Statuses: RESTful CRUD Controller """

    def prep(r):

        table = r.resource.table
        field = table.name
        field.requires = IS_NOT_EMPTY()

        return True
    s3.prep = prep

    return s3_rest_controller()

# END =========================================================================
