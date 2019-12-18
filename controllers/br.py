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

    from gluon import current
    if auth.s3_has_permission("read", "pr_person", c="br", f="person"):
        # Just redirect to list of current cases
        s3_redirect_default(URL(f="person", vars={"closed": "0"}))

    return {"module_name": settings.modules["br"].name_nice}

# =============================================================================
# Case File and Component Tabs
#
def person():
    """ Case File: RESTful CRUD Controller """

    # Set the default case status
    s3db.br_case_default_status()

    # Set contacts-method for tab
    s3db.set_method("pr", "person",
                    method = "contacts",
                    action = s3db.pr_Contacts,
                    )

    # ID Card Export
    id_card_layout = settings.get_br_id_card_layout()
    id_card_export_roles = settings.get_br_id_card_export_roles()
    if id_card_layout and id_card_export_roles and \
       auth.s3_has_roles(id_card_export_roles):
        id_card_export = True
    else:
        id_card_export = False

    def prep(r):

        # Filter to persons who have a case registered
        resource = r.resource
        resource.add_filter(FS("case.id") != None)

        labels = s3db.br_terminology()
        CASES = labels.CASES

        human_resource_id = auth.s3_logged_in_human_resource()
        insertable = True

        record = r.record
        if not record:

            # Enable bigtable strategies for better performance
            settings.base.bigtable = True

            get_vars = r.get_vars
            queries = []

            # Filter for "my cases"
            mine = get_vars.get("mine")
            if mine == "1":
                if human_resource_id:
                    queries.append(FS("case.human_resource_id") == human_resource_id)
                else:
                    queries.append(FS("case.human_resource_id").belongs(set()))
                CURRENT = labels.CURRENT_MINE
                CASES = labels.CASES_MINE
            else:
                query = None
                CURRENT = labels.CURRENT

            # Filter to open/closed cases
            closed = get_vars.get("closed")
            get_status_filter_opts = s3db.br_case_status_filter_opts
            if closed == "1":
                # Only closed cases
                queries.append(FS("case.status_id$is_closed") == True)
                CASES = labels.CLOSED
                insertable = False
                status_filter_opts = lambda: get_status_filter_opts(closed=True)
            elif closed == "0":
                # Only open cases
                queries.append((FS("case.status_id$is_closed") == False) | \
                               (FS("case.status_id$is_closed") == None))
                CASES = CURRENT
                status_filter_opts = lambda: get_status_filter_opts(closed=False)
            else:
                status_filter_opts = get_status_filter_opts

            # Filter to valid/invalid cases
            invalid = get_vars.get("invalid")
            if invalid == "1":
                queries.append(FS("case.invalid") == True)
                CASES = T("Invalid Cases")
                insertable = False
            else:
                queries.append((FS("case.invalid") == False) | \
                               (FS("case.invalid") == None))

            if queries:
                query = reduce(lambda a, b: a & b, queries)
                resource.add_filter(query)

        # Adapt CRUD strings to perspective (& terminology)
        crud_strings = s3db.br_crud_strings("pr_person")
        crud_strings.title_list = CASES
        s3.crud_strings["pr_person"] = crud_strings

        # Configure Anonymizer
        from s3 import S3Anonymize
        s3db.set_method("pr", "person",
                        method = "anonymize",
                        action = S3Anonymize,
                        )

        # Update resource configuration for perspective
        resource.configure(anonymize = s3db.br_person_anonymize(),
                           deletable = False,
                           insertable = insertable,
                           )

        # Configure ID Cards
        if id_card_export:
            if r.representation == "card":
                # Configure ID card layout
                resource.configure(pdf_card_layout = id_card_layout,
                                   #pdf_card_pagesize="A4",
                                   )

            if not r.id and not r.component:
                # Add export-icon for ID cards
                export_formats = list(settings.get_ui_export_formats())
                export_formats.append(("card", "fa fa-id-card", T("Export ID Cards")))
                settings.ui.export_formats = export_formats
                s3.formats["card"] = r.url(method="")

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
            if record and r.method != "read":
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
            if not record:
                from s3 import S3TextFilter, S3DateFilter, S3OptionsFilter
                filter_widgets = [
                    S3TextFilter(name_fields + ["pe_label", "case.comments"],
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
            s3db.set_method("pr", "person",
                            method = "search_ac",
                            action = s3db.pr_PersonSearchAutocomplete(name_fields),
                            )

        elif r.component_name == "case_activity":

            atable = r.component.table

            assistance_inline = settings.get_br_manage_assistance() and \
                                settings.get_br_assistance_inline()
            mtable =  s3db.br_assistance_measure

            # Default status
            if settings.get_br_case_activity_status():
                s3db.br_case_activity_default_status()

            # Default human_resource_id
            if human_resource_id:

                # Activities
                if settings.get_br_case_activity_manager():
                    atable.human_resource_id.default = human_resource_id

                # Inline updates
                if settings.get_br_case_activity_updates():
                    utable = s3db.br_case_activity_update
                    utable.human_resource_id.default = human_resource_id

                # Inline assistance measures
                if assistance_inline:
                    mtable.human_resource_id.default = human_resource_id

            root_org = None
            org_specific_needs = settings.get_br_case_activity_need() and \
                                 settings.get_br_needs_org_specific()
            if org_specific_needs:
                root_org = s3db.br_case_root_org(r.id)
                if not root_org:
                    root_org = auth.root_org()

            # Limit selectable need types to the case root org
            if org_specific_needs and root_org:
                field = atable.need_id
                field.requires = IS_EMPTY_OR(
                                    IS_ONE_OF(db, "br_need.id",
                                              field.represent,
                                              filterby = "organisation_id",
                                              filter_opts = (root_org,),
                                              ))

            # Configure inline assistance measures
            if assistance_inline:
                if record:
                    mtable.person_id.default = record.id
                if settings.get_br_assistance_themes() and root_org:
                    # Limit selectable themes to the case root org
                    field = mtable.theme_ids
                    dbset = s3db.br_org_assistance_themes(root_org)
                    field.requires = IS_EMPTY_OR(IS_ONE_OF(dbset, "br_assistance_theme.id",
                                                           field.represent,
                                                           multiple = True,
                                                           ))
                s3db.br_assistance_default_status()

        elif r.component_name == "assistance_measure":

            mtable = r.component.table
            ltable = s3db.br_assistance_measure_theme

            # Default status
            s3db.br_assistance_default_status()

            # Default human_resource_id
            if human_resource_id and settings.get_br_assistance_manager():
                mtable.human_resource_id.default = human_resource_id

            # Filter case_activity_id selector to current case
            field = mtable.case_activity_id
            if record and field.writable:
                requires = field.requires
                if isinstance(requires, IS_EMPTY_OR):
                    requires = requires.other
                requires.set_filter(filterby = "person_id",
                                    filter_opts = (record.id,))

            # Represent for br_assistance_measure_theme.id
            details_per_theme = settings.get_br_assistance_details_per_theme()
            if details_per_theme:
                ltable.id.represent = s3db.br_AssistanceMeasureThemeRepresent(
                                            paragraph = True,
                                            details = True,
                                            )

            # Filter theme_id selectors to case root org
            root_org = s3db.br_case_root_org(r.id)
            if not root_org:
                root_org = auth.root_org()
            if root_org:
                dbset = s3db.br_org_assistance_themes(root_org)
                field = mtable.theme_ids
                field.requires = IS_EMPTY_OR(IS_ONE_OF(dbset, "br_assistance_theme.id",
                                                       field.represent,
                                                       multiple = True,
                                                       ))
                field = ltable.theme_id
                field.requires = IS_EMPTY_OR(IS_ONE_OF(dbset, "br_assistance_theme.id",
                                                       field.represent,
                                                       ))

            # Allow organizer to set an end_date
            if r.method == "organize" and \
               settings.get_br_assistance_measures_use_time():
                field = mtable.end_date
                field.writable = True

        elif r.component_name == "br_note":

            # Represent the note author by their name (rather than email)
            ntable = r.component.table
            ntable.modified_by.represent = s3base.s3_auth_user_represent_name

        return True
    s3.prep = prep

    def postp(r, output):

        if not r.component and r.record and isinstance(output, dict):

            # Custom CRUD buttons
            if "buttons" not in output:
                buttons = output["buttons"] = {}
            else:
                buttons = output["buttons"]

            # Anonymize-button
            from s3 import S3AnonymizeWidget
            anonymize = S3AnonymizeWidget.widget(r, _class="action-btn anonymize-btn")

            # ID-Card button
            if id_card_export:
                card_button = A(T("ID Card"),
                                data = {"url": URL(c="br", f="person",
                                                   args = ["%s.card" % r.id]
                                                   ),
                                        },
                                _class = "action-btn s3-download-button",
                                _script = "alert('here')",
                                )
            else:
                card_button = ""

            # Render in place of the delete-button
            buttons["delete_btn"] = TAG[""](card_button,
                                            anonymize,
                                            )
        return output
    s3.postp = postp

    output = s3_rest_controller("pr", "person", rheader=s3db.br_rheader)
    return output

# -----------------------------------------------------------------------------
def person_search():
    """
        RESTful controller for autocomplete-searches
    """

    def prep(r):

        if r.method != "search_ac":
            return False

        # Filter for valid+open cases
        query = (FS("case.id") != None) & \
                (FS("case.invalid") == False) & \
                (FS("case.status_id$is_closed") == False)
        r.resource.add_filter(query)

        # Auto-detect name parts from current name format
        NAMES = ("first_name", "middle_name", "last_name")
        keys = s3base.StringTemplateParser.keys(settings.get_pr_name_format())
        name_fields = [fn for fn in keys if fn in NAMES]

        # Autocomplete search-method including pe_label
        search_fields = tuple(name_fields) + ("pe_label",)
        s3db.set_method("pr", "person",
                        method = "search_ac",
                        action = s3db.pr_PersonSearchAutocomplete(search_fields),
                        )
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
                    group_ids = {group_id}
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
        human_resource_id = auth.s3_logged_in_human_resource()

        # Filter for valid+open cases
        query = (FS("person_id$case.id") != None) & \
                (FS("person_id$case.invalid") == False) & \
                (FS("person_id$case.status_id$is_closed") == False)

        resource.add_filter(query)

        if not r.record:

            # Enable bigtable features for better performance
            settings.base.bigtable = True

            get_vars = r.get_vars
            crud_strings = response.s3.crud_strings["br_case_activity"]

            # Filter for "my activities"
            mine = get_vars.get("mine")
            if mine == "1":
                mine = True
                if human_resource_id:
                    query = FS("human_resource_id") == human_resource_id
                else:
                    query = FS("human_resource_id").belongs(set())
                resource.add_filter(query)
                crud_strings.title_list = T("My Activities")
            else:
                mine = False

            # Adapt list title when filtering for priority 0 (Emergency)
            if get_vars.get("~.priority") == "0":
                crud_strings.title_list = T("Emergencies")

            case_activity_status = settings.get_br_case_activity_status()
            case_activity_need = settings.get_br_case_activity_need()

            # Default status
            if case_activity_status:
                s3db.br_case_activity_default_status()

            # Filter widgets
            from s3 import S3DateFilter, \
                           S3OptionsFilter, \
                           S3TextFilter, \
                           s3_get_filter_opts

            text_filter_fields = ["person_id$pe_label",
                                  "person_id$first_name",
                                  "person_id$middle_name",
                                  "person_id$last_name",
                                  ]
            if settings.get_br_case_activity_subject():
                text_filter_fields.append("subject")
            if settings.get_br_case_activity_need_details():
                text_filter_fields.append("need_details")

            filter_widgets = [S3TextFilter(text_filter_fields,
                                           label = T("Search"),
                                           ),
                             ]

            multiple_orgs = s3db.br_case_read_orgs()[0]
            if multiple_orgs:
                filter_widgets.append(S3OptionsFilter("person_id$case.organisation_id"))

            if case_activity_status:
                stable = s3db.br_case_activity_status
                query = (stable.deleted == False)
                rows = db(query).select(stable.id,
                                        stable.name,
                                        stable.is_closed,
                                        cache = s3db.cache,
                                        orderby = stable.workflow_position,
                                        )
                status_filter_options = OrderedDict((row.id, T(row.name)) for row in rows)
                status_filter_defaults = [row.id for row in rows if not row.is_closed]
                filter_widgets.append(S3OptionsFilter("status_id",
                                                      options = status_filter_options,
                                                      default = status_filter_defaults,
                                                      cols = 3,
                                                      hidden = True,
                                                      sort = False,
                                                      ))

            if not mine and settings.get_br_case_activity_manager():
                filter_widgets.append(S3OptionsFilter("human_resource_id",
                                                      hidden = True,
                                                      ))

            filter_widgets.extend([S3DateFilter("date",
                                                hidden = True,
                                                ),
                                   S3OptionsFilter("person_id$person_details.nationality",
                                                   label = T("Client Nationality"),
                                                   hidden = True,
                                                   ),
                                   ])

            if case_activity_need:
                org_specific_needs = settings.get_br_needs_org_specific()
                filter_widgets.append(S3OptionsFilter("need_id",
                                                      hidden = True,
                                                      header = True,
                                                      options = lambda: \
                                                                s3_get_filter_opts(
                                                                  "br_need",
                                                                  org_filter = org_specific_needs,
                                                                  translate = True,
                                                                  ),
                                                      ))

            resource.configure(filter_widgets=filter_widgets)

            # Report options
            if r.method == "report":
                facts = ((T("Number of Activities"), "count(id)"),
                         (labels.NUMBER_OF_CASES, "count(person_id)"),
                         )
                axes = ["person_id$case.organisation_id",
                        "person_id$gender",
                        "person_id$person_details.nationality",
                        "person_id$person_details.marital_status",
                        "priority",
                        ]
                default_rows = "person_id$case.organisation_id"
                default_cols = "person_id$person_details.nationality"

                if settings.get_br_manage_assistance() and \
                   settings.get_br_assistance_themes():
                    axes.insert(1, "assistance_measure_theme.theme_id")
                if case_activity_need:
                    axes.insert(1, "need_id")
                    default_cols = "need_id"
                if case_activity_status:
                    axes.insert(4, "status_id")

                report_options = {
                    "rows": axes,
                    "cols": axes,
                    "fact": facts,
                    "defaults": {"rows": default_rows,
                                 "cols": default_cols,
                                 "fact": "count(id)",
                                 "totals": True,
                                 },
                    }
                resource.configure(report_options=report_options)

        # Set default for human_resource_ids
        if human_resource_id:
            table.human_resource_id.default = human_resource_id

            utable = s3db.br_case_activity_update
            utable.human_resource_id.default = human_resource_id

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
# Assistance
#
def assistance_status():
    """ Assistance Statuses: RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def assistance_theme():
    """ Assistance Themes: RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def assistance_type():
    """ Types of Assistance: RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def assistance_measure():
    """ Assistance Measures: RESTful CRUD controller """

    def prep(r):

        resource = r.resource
        table = resource.table

        # Set default status
        s3db.br_assistance_default_status()

        # Populate human_resource_id with current user, don't link
        human_resource_id = auth.s3_logged_in_human_resource()
        if human_resource_id:
            table.human_resource_id.default = human_resource_id

        # Filter for valid+open cases
        query = (FS("person_id$case.id") != None) & \
                (FS("person_id$case.invalid") == False) & \
                (FS("person_id$case.status_id$is_closed") == False)

        resource.add_filter(query)

        # Filter for "my measures"
        crud_strings = response.s3.crud_strings["br_assistance_measure"]
        mine = get_vars.get("mine")
        if mine == "1":
            mine = True
            if human_resource_id:
                query = FS("human_resource_id") == human_resource_id
            else:
                query = FS("human_resource_id").belongs(set())
            resource.add_filter(query)
            crud_strings.title_list = T("My Measures")
        else:
            mine = False

        # Allow organizer to set an end_date
        method = r.method
        if method == "organize" and \
           settings.get_br_assistance_measures_use_time():
            field = table.end_date
            field.writable = True

        if not r.component:

            record = r.record
            ltable = s3db.br_assistance_measure_theme

            # Show person_id as link to case file, not writable in this perspective
            field = table.person_id
            field.writable = False
            if r.representation != "popup":
                field.represent = s3db.pr_PersonRepresent(show_link=True)

            # Filter case_activity_id selector to current case
            field = table.case_activity_id
            if record and field.writable:
                requires = field.requires
                if isinstance(requires, IS_EMPTY_OR):
                    requires = requires.other
                requires.set_filter(filterby = "person_id",
                                    filter_opts = (record.person_id,))

            # Filter theme_ids selector to case root org
            if record and field.writable:
                root_org = s3db.br_case_root_org(record.person_id)
                if not root_org:
                    root_org = auth.root_org()
                if root_org:
                    dbset = s3db.br_org_assistance_themes(root_org)
                    field = table.theme_ids
                    field.requires = IS_EMPTY_OR(IS_ONE_OF(dbset, "br_assistance_theme.id",
                                                           field.represent,
                                                           multiple = True,
                                                           ))
                    field = ltable.theme_id
                    field.requires = IS_EMPTY_OR(IS_ONE_OF(dbset, "br_assistance_theme.id",
                                                           field.represent,
                                                           ))

            # Adapt list fields to perspective
            list_fields = [(T("ID"), "person_id$pe_label"),
                           "person_id",
                           #"assistance_type_id"|"comments",
                           #"theme_ids"|measure-theme-links,
                           #"human_resource_id",
                           "start_date",
                           #"hours",
                           "status_id",
                           ]

            # Include human_resource_id if not using mine-filter
            if not mine and settings.get_br_assistance_manager():
                list_fields.insert(2, "human_resource_id")

            use_themes = settings.get_br_assistance_themes()
            details_per_theme = settings.get_br_assistance_details_per_theme()

            # Include comments if not per-theme
            if not use_themes or not details_per_theme:
                list_fields.insert(2, "comments")

            # Include themes if using themes
            if use_themes:
                if details_per_theme:
                    ltable.id.represent = s3db.br_AssistanceMeasureThemeRepresent(
                                                    paragraph = True,
                                                    details = True,
                                                    )

                    list_fields.insert(2, (T("Themes"), "assistance_measure_theme.id"))
                else:
                    list_fields.insert(2, "theme_ids")

            # Include type when using types, otherwise show details
            if settings.get_br_assistance_types():
                list_fields.insert(2, "assistance_type_id")

            # Show effort when tracking effort
            if settings.get_br_assistance_track_effort():
                list_fields.insert(-1, "hours")

            resource.configure(list_fields = list_fields,
                               # Measures should only be added or deleted
                               # from case perspective
                               insertable = False,
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

# -----------------------------------------------------------------------------
def case_activity_update_type():
    """ Activity Update Types: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def need():
    """ Needs: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def note_type():
    """ Note Types: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def service_contact_type():
    """ Service Contact Types: RESTful CRUD Controller """

    return s3_rest_controller()

# END =========================================================================
