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
# Case File and Component Tabs
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

        human_resource_id = auth.s3_logged_in_human_resource()
        insertable = True

        if not r.record:

            get_vars = r.get_vars

            # Filter to open/closed cases
            closed = get_vars.get("closed")
            get_status_filter_opts = s3db.br_case_status_filter_opts
            if closed == "1":
                # Only closed cases
                query = FS("case.status_id$is_closed") == True
                CASES = labels.CLOSED
                insertable = False
                status_filter_opts = lambda: get_status_filter_opts(closed=True)
            elif closed == "0":
                # Only open cases
                query = (FS("case.status_id$is_closed") == False) | \
                        (FS("case.status_id$is_closed") == None)
                CASES = labels.CURRENT
                status_filter_opts = lambda: get_status_filter_opts(closed=False)
            else:
                query = None
                status_filter_opts = get_status_filter_opts

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

            # Module-specific field and form configuration
            from s3 import S3SQLInlineComponent

            # Adapt fields to module context
            table = resource.table
            ctable = s3db.br_case
            multiple_orgs = s3db.br_case_read_orgs()[0]

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
                default_org, selectable = s3db.br_case_default_org()
                if default_org and settings.get_br_case_hide_default_org():
                    field.writable = selectable
                    field.readable = selectable or multiple_orgs
                field.default = default_org
            requires = field.requires
            if isinstance(requires, IS_EMPTY_OR):
                field.requires = requires.other

            # Configure case.human_resource_id
            field = ctable.human_resource_id
            if settings.get_br_case_manager():
                if human_resource_id:
                    field.default = human_resource_id
                field.readable = field.writable = True
            else:
                field.readable = field.writable = False

            # Size of family
            if settings.get_br_household_size() in (False, "auto"):
                field = ctable.household_size
                field.readable = field.writable = False

            # Address (optional)
            if settings.get_br_case_address():
                address = S3SQLInlineComponent(
                                "address",
                                label = T("Current Address"),
                                fields = [("", "location_id")],
                                filterby = {"field": "type",
                                            "options": "1",
                                            },
                                link = False,
                                multiple = False,
                                )
            else:
                address = None

            # Language details (optional)
            if settings.get_br_case_language_details():
                language_details = S3SQLInlineComponent(
                                        "case_language",
                                        fields = ["language",
                                                  "quality",
                                                  "comments",
                                                  ],
                                        label = T("Language / Communication Mode"),
                                        )
            else:
                language_details = None

            # Expose the "invalid"-flag? (update forms only)
            if r.record and r.method != "read":
                field = ctable.invalid
                field.readable = field.writable = True

            # Custom CRUD form
            crud_fields = ["case.date",
                           "case.organisation_id",
                           "case.human_resource_id",
                           "case.status_id",
                           "pe_label",
                           # +name fields
                           "person_details.nationality",
                           "date_of_birth",
                           "gender",
                           "person_details.marital_status",
                           "case.household_size",
                           address,
                           S3SQLInlineComponent(
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
                           language_details,
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

            # Add organisation if user can see cases from multiple orgs
            if multiple_orgs:
                list_fields.insert(-2, "case.organisation_id")

            # Insert name fields in name-format order
            NAMES = ("first_name", "middle_name", "last_name")
            keys = s3base.StringTemplateParser.keys(settings.get_pr_name_format())
            name_fields = [fn for fn in keys if fn in NAMES]
            crud_fields[5:5] = name_fields
            list_fields[1:1] = name_fields

            resource.configure(crud_form = s3base.S3SQLCustomForm(*crud_fields),
                               list_fields = list_fields,
                               )

            # Filter Widgets
            if not r.record:
                from s3 import S3TextFilter, S3DateFilter, S3OptionsFilter
                filter_widgets = [
                    S3TextFilter(["pe_label",
                                  "first_name",
                                  "middle_name",
                                  "last_name",
                                  "case.comments",
                                  ],
                                  label = T("Search"),
                                  comment = T("You can search by name, ID or comments"),
                                  ),
                    S3DateFilter("date_of_birth",
                                 hidden = True,
                                 ),
                    S3OptionsFilter("case.status_id",
                                   cols = 3,
                                   options = status_filter_opts,
                                   sort = False,
                                   hidden = True,
                                   ),
                    S3OptionsFilter("person_details.nationality",
                                    hidden = True,
                                    ),
                    S3DateFilter("case.date",
                                 hidden = True,
                                 ),
                    ]

                # Org-filter if user can see cases from multiple orgs/branches
                if multiple_orgs:
                    filter_widgets.insert(1,
                                          S3OptionsFilter("case.organisation_id"),
                                          )

                resource.configure(filter_widgets = filter_widgets)

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

        elif r.component_name == "case_activity":

            # Configure case_activity.human_resource_id
            atable = r.component.table
            if settings.get_br_case_activity_manager() and human_resource_id:
                field = atable.human_resource_id
                field.default = human_resource_id

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
        Case File Family-Tab: RESTful CRUD controller
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
            field.comment = DIV(_class="tooltip",
                                _title="%s|%s" % (T("Role"),
                                                  T("The role of the person within the family"),
                                                  ))
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
                           (T("Case Status"), "person_id$case.status_id"),
                           "comments",
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

# -----------------------------------------------------------------------------
def document():
    """
        Case File Documents-Tab: RESTful CRUD controller
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
        else:
            return False

        ctable = s3db.br_case
        auth = current.auth
        has_permission = auth.s3_has_permission
        accessible_query = auth.s3_accessible_query

        if vtablename == "pr_person":

            # Check permission to read the case
            if not has_permission("read", "pr_person", record_id):
                r.unauthorised()

            # Set contacts-method to retain the tab
            s3db.set_method("pr", "person",
                            method = "contacts",
                            action = s3db.pr_Contacts,
                            )

            include_activity_docs = settings.get_br_case_include_activity_docs()
            include_group_docs = settings.get_br_case_include_group_docs()
            query = accessible_query("read", ctable) & \
                    (ctable.person_id == record_id) & \
                    (ctable.deleted == False)

        else:
            # Unsupported
            return False

        # Get the case doc_id
        case = db(query).select(ctable.doc_id,
                                limitby = (0, 1),
                                orderby = ~ctable.modified_on,
                                ).first()
        if not case:
            # No case found
            r.error(404, "Case not found")
        elif not case.doc_id:
            # Case has no doc_id (invalid)
            r.error(404, "Invalid Case")

        case_doc_id = case.doc_id
        doc_ids = [case_doc_id]

        # Include case groups
        if include_group_docs:

            # Look up relevant case groups
            mtable = s3db.pr_group_membership
            gtable = s3db.pr_group
            join = gtable.on((gtable.id == mtable.group_id) & \
                             (gtable.group_type == 7))
            query = accessible_query("read", mtable) & \
                    (mtable.person_id == record_id) & \
                    (mtable.deleted == False)
            rows = db(query).select(gtable.doc_id,
                                    join = join,
                                    orderby = ~mtable.created_on,
                                    )

            # Append the doc_ids
            for row in rows:
                if row.doc_id:
                    doc_ids.append(row.doc_id)

        # Include case activities
        if include_activity_docs:

           # Look up relevant case activities
           atable = s3db.br_case_activity
           query = accessible_query("read", atable) & \
                   (atable.person_id == record_id) & \
                   (atable.deleted == False)
           rows = db(query).select(atable.doc_id,
                                   orderby = ~atable.created_on,
                                   )

           # Append the doc_ids
           for row in rows:
               if row.doc_id:
                   doc_ids.append(row.doc_id)

        # Hide URL field
        field = table.url
        field.readable = field.writable = False

        # Custom label for date-field
        field = table.date
        field.label = T("Uploaded on")
        field.default = r.utcnow.date()
        field.writable = False

        # Hide name-field in this context
        field = table.name
        field.readable = field.writable = False

        # List fields
        list_fields = ["id", "file", "date", "comments"]

        # Default order: newest document first
        orderby = ["doc_document.date desc"]

        if include_activity_docs or include_group_docs:

            # Make doc_id readable and visible in table
            field = table.doc_id
            field.represent = s3db.br_DocEntityRepresent()
            field.label = T("Attachment of")
            field.readable = True
            list_fields.insert(1, (T("Attachment of"), "doc_id"))
            orderby.insert(0, "doc_document.doc_id")

        s3db.configure("doc_document",
                       list_fields = list_fields,
                       orderby = orderby,
                       )

        # Apply filter and defaults
        field = table.doc_id
        field.default = case_doc_id
        if len(doc_ids) == 1:
            # Single doc_id => set default, hide field
            field.readable = field.writable = False
            r.resource.add_filter(FS("doc_id") == case_doc_id)
        else:
            # Multiple doc_ids => default to case, make selectable
            field.readable = field.writable = True
            field.requires = IS_ONE_OF(db, "doc_entity.doc_id",
                                       field.represent,
                                       filterby = "doc_id",
                                       filter_opts = doc_ids,
                                       orderby = "instance_type",
                                       sort = False,
                                       )
            r.resource.add_filter(FS("doc_id").belongs(doc_ids))

        return True
    s3.prep = prep

    return s3_rest_controller("doc", "document",
                              rheader = s3db.br_rheader,
                              )

# =============================================================================
# Case Activities
#
def case_activity():
    """ Case Activities: RESTful CRUD controller """

    def prep(r):

        resource = r.resource
        table = resource.table

        labels = s3db.br_terminology()

        # Filter for valid+open cases
        query = (FS("person_id$case.id") != None) & \
                (FS("person_id$case.invalid") == False) & \
                (FS("person_id$case.status_id$is_closed") == False)

        # TODO mine-filter

        resource.add_filter(query)

        # Represent person_id as link to case file
        field = table.person_id
        field.label = labels.CASE
        field.represent = s3db.pr_PersonRepresent(show_link=True)

        # Add case data to list fields
        list_fields = resource.get_config("list_fields")
        list_fields[1:1] = [(T("ID"), "person_id$pe_label"),
                            "person_id",
                            ]

        # Create/delete must happen on case file tab, not here
        resource.configure(insertable = False,
                           deletable = False,
                           )

        return True
    s3.prep = prep

    return s3_rest_controller()

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

# -----------------------------------------------------------------------------
def case_activity_status():
    """ Activity Statuses: RESTful CRUD Controller """

    return s3_rest_controller()

# END =========================================================================
