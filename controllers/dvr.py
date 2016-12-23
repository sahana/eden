# -*- coding: utf-8 -*-

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

        beneficiary = settings.get_dvr_label() # If we add more options in future then == "Beneficiary"
        if beneficiary:
            CASES = T("Beneficiaries")
            CURRENT = T("Current Beneficiaries")
            CLOSED = T("Former Beneficiaries")
        else:
            CASES = T("Cases")
            CURRENT = T("Current Cases")
            CLOSED = T("Closed Cases")

        # Filters to split case list
        if not r.record:
            get_vars = r.get_vars

            # Filter to active/archived cases
            archived = get_vars.get("archived")
            if archived == "1":
                archived = True
                CASES = T("Archived Cases")
                query = FS("dvr_case.archived") == True
            else:
                archived = False
                query = (FS("dvr_case.archived") == False) | \
                        (FS("dvr_case.archived") == None)

            # Filter to open/closed cases
            # (also filtering status filter opts)
            closed = get_vars.get("closed")
            get_status_opts = s3db.dvr_case_status_filter_opts
            if closed == "1":
                CASES = CLOSED
                query &= FS("dvr_case.status_id$is_closed") == True
                status_opts = lambda: get_status_opts(closed=True)
            elif closed == "0":
                CASES = CURRENT
                query &= (FS("dvr_case.status_id$is_closed") == False) | \
                         (FS("dvr_case.status_id$is_closed") == None)
                status_opts = lambda: get_status_opts(closed=False)
            else:
                status_opts = get_status_opts

            resource.add_filter(query)
        else:
            archived = False
            status_opts = s3db.dvr_case_status_filter_opts

        # Should not be able to delete records in this view
        resource.configure(deletable = False)

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
            if beneficiary:
                s3.crud_strings["pr_person"] = Storage(
                    label_create = T("Create Beneficiary"),
                    title_display = T("Beneficiary Details"),
                    title_list = CASES,
                    title_update = T("Edit Beneficiary Details"),
                    label_list_button = T("List Beneficiaries"),
                    label_delete_button = T("Delete Beneficiary"),
                    msg_record_created = T("Beneficiary added"),
                    msg_record_modified = T("Beneficiary details updated"),
                    msg_record_deleted = T("Beneficiary deleted"),
                    msg_list_empty = T("No Beneficiaries currently registered")
                    )
            else:
                s3.crud_strings["pr_person"] = Storage(
                    label_create = T("Create Case"),
                    title_display = T("Case Details"),
                    title_list = CASES,
                    title_update = T("Edit Case Details"),
                    label_list_button = T("List Cases"),
                    label_delete_button = T("Delete Case"),
                    msg_record_created = T("Case added"),
                    msg_record_modified = T("Case details updated"),
                    msg_record_deleted = T("Case deleted"),
                    msg_list_empty = T("No Cases currently registered")
                    )

            if not r.component:

                # Expose the "archived"-flag? (update forms only)
                if r.record and r.method != "read":
                    ctable = s3db.dvr_case
                    field = ctable.archived
                    field.readable = field.writable = True

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
                                "dvr_case.archived",
                                )

                # Module-specific filter widgets
                from s3 import s3_get_filter_opts, S3TextFilter, S3OptionsFilter
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
                                    options = status_opts,
                                    sort = False,
                                    ),
                    S3OptionsFilter("person_details.nationality",
                                    ),
                    ]

                # Add filter for case flags
                if settings.get_dvr_case_flags():
                    filter_widgets.append(
                        S3OptionsFilter("case_flag_case.flag_id",
                                        label = T("Flags"),
                                        options = s3_get_filter_opts("dvr_case_flag",
                                                                     translate = True,
                                                                     ),
                                        cols = 3,
                                        hidden = True,
                                        ))

                # Add filter for transferability if relevant for deployment
                if settings.get_dvr_manage_transferability():
                    filter_widgets.append(
                        S3OptionsFilter("dvr_case.transferable",
                                        options = {True: T("Yes"),
                                                   False: T("No"),
                                                   },
                                        cols = 2,
                                        hidden = True,
                                        ))

                resource.configure(crud_form = crud_form,
                                   filter_widgets = filter_widgets,
                                   )
            elif r.component_name == "allowance" and \
                 r.method in (None, "update"):

                records = r.component.select(["status"], as_rows=True)
                if len(records) == 1:
                    record = records[0]
                    table = r.component.table
                    readonly = []
                    if record.status == 2:
                        # Can't change payment details if already paid
                        readonly = ["person_id",
                                    "entitlement_period",
                                    "date",
                                    "paid_on",
                                    "amount",
                                    "currency",
                                    ]
                    for fn in readonly:
                        if fn in table.fields:
                            field = table[fn]
                            field.writable = False
                            field.comment = None
            elif r.component_name == "evaluation":
                S3SQLInlineComponent = s3base.S3SQLInlineComponent

                crud_fields = [#"person_id",
                               #"case_id",
                               #"date",
                               ]
                cappend = crud_fields.append

                table = s3db.dvr_evaluation_question
                rows = db(table.deleted != True).select(table.id,
                                                        table.section,
                                                        #table.header,
                                                        table.number,
                                                        table.name,
                                                        orderby = table.number,
                                                        )

                #subheadings = {}

                section = None
                for row in rows:
                    name = "number%s" % row.number
                    if row.section != section:
                        label = section = row.section
                        #subheadings[T(section)] = "sub_%sdata" % name
                    else:
                        label = ""
                    cappend(S3SQLInlineComponent("data",
                                                 name = name,
                                                 label = label,
                                                 fields = (("", "question_id"),
                                                           ("", "answer"),
                                                           ),
                                                 filterby = dict(field = "question_id",
                                                                 options = row.id
                                                                 ),
                                                 multiple = False,
                                                 ),
                            )

                cappend("comments")
                crud_form = s3base.S3SQLCustomForm(*crud_fields)

                s3db.configure("dvr_evaluation",
                               crud_form = crud_form,
                               #subheadings = subheadings,
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
def activity_age_group():
    """ Activity Age Groups: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def activity_group_type():
    """ Activity Group Types: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def activity():
    """ Activities: RESTful CRUD Controller """

    return s3_rest_controller(rheader = s3db.dvr_rheader,
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
def due_followups():
    """ RESTful Controller for Due Follow-ups """

    def prep(r):
        resource = r.resource
        s3.crud_strings["dvr_case_activity"]["title_list"] = T("Activities to follow up")
        if not r.record:
            query = (FS("followup") == True) & \
                    (FS("followup_date") <= datetime.datetime.utcnow().date()) & \
                    (FS("completed") != True) & \
                    ((FS("person_id$dvr_case.archived") == None) | \
                    (FS("person_id$dvr_case.archived") == False))

            resource.add_filter(query)

        list_fields = ["case_id$reference",
                       "person_id$first_name",
                       "person_id$last_name",
                       "need_id",
                       "need_details",
                       "emergency",
                       "referral_details",
                       "followup_date",
                       "completed",
                       ]

        resource.configure(list_fields = list_fields,
                           insertable = False,
                           deletable = False,
                           )
        return True
    s3.prep = prep

    return s3_rest_controller("dvr", "case_activity")

# -----------------------------------------------------------------------------
def case_flag():
    """ Case Flags: RESTful CRUD Controller """

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
def allowance():
    """ Allowances: RESTful CRUD Controller """

    deduplicate = s3db.get_config("pr_person", "deduplicate")

    def person_deduplicate(item):
        """
            Wrapper for person deduplicator to identify person
            records, but preventing actual imports of persons
        """

        # Run standard person deduplication
        if deduplicate:
            deduplicate(item)

        # Person not found?
        if item.method != item.METHOD.UPDATE:

            # Provide some meaningful details of the failing
            # person record to facilitate correction of the source:
            from s3 import s3_unicode
            person_details = []
            append = person_details.append
            data = item.data
            for f in ("pe_label", "last_name", "first_name", "date_of_birth"):
                value = data.get(f)
                if value:
                    append(s3_unicode(value))
            error = "Person not found: %s" % ", ".join(person_details)
            item.error = error
            item.element.set(current.xml.ATTRIBUTE["error"], error)

            # Reject any new person records
            item.accepted = False

        # Skip - we don't want to update person records here
        item.skip = True
        item.method = None

    s3db.configure("pr_person", deduplicate=person_deduplicate)

    def prep(r):

        if r.method == "import":
            # Allow deduplication of persons by pe_label: existing
            # pe_labels would be caught by IS_NOT_ONE_OF before
            # reaching the deduplicator, so remove the validator here:
            ptable = s3db.pr_person
            ptable.pe_label.requires = None

        record = r.record
        if record:
            table = r.table
            if record.status == 2:
                # Can't change payment details if already paid
                readonly = ["person_id",
                            "entitlement_period",
                            "date",
                            "paid_on",
                            "amount",
                            "currency",
                            ]
                for fn in readonly:
                    if fn in table.fields:
                        field = table[fn]
                        field.writable = False
                        field.comment = None
        return True
    s3.prep = prep

    table = s3db.dvr_allowance

    return s3_rest_controller(csv_extra_fields=[{"label": "Date",
                                                 "field": table.date,
                                                 },
                                                ],
                              )

# -----------------------------------------------------------------------------
def case_appointment():
    """ Appointments: RESTful CRUD Controller """

    def prep(r):

        if r.method == "import":
            # Allow deduplication of persons by pe_label: existing
            # pe_labels would be caught by IS_NOT_ONE_OF before
            # reaching the deduplicator, so remove the validator here:
            ptable = s3db.pr_person
            ptable.pe_label.requires = None
        return True
    s3.prep = prep

    table = s3db.dvr_case_appointment

    return s3_rest_controller(csv_extra_fields=[{"label": "Appointment Type",
                                                 "field": table.type_id,
                                                 },
                                                {"label": "Appointment Date",
                                                 "field": table.date,
                                                 },
                                                {"label": "Appointment Status",
                                                 "field": table.status,
                                                 },
                                                ],
                              )

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

    if settings.get_dvr_needs_hierarchical():

        tablename = "dvr_need"

        from s3 import S3Represent
        represent = S3Represent(lookup = tablename,
                                hierarchy = True,
                                translate = True,
                                )

        table = s3db[tablename]
        field = table.parent
        field.represent = represent
        field.requires = IS_EMPTY_OR(IS_ONE_OF(db, "%s.id" % tablename,
                                               represent,
                                               orderby="%s.name" % tablename,
                                               ))

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def note():
    """ Notes: RESTful CRUD Controller """

    # Coming from a Profile page?"
    person_id = get_vars.get("~.person_id")
    if person_id:
        field = s3db.dvr_note.person_id
        field.default = person_id
        field.readable = field.writable = False

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def housing():
    """ Housing: RESTful CRUD Controller for option lookups """

    s3.prep = lambda r: r.method == "options" and \
                        r.representation == "s3json"

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def beneficiary_data():
    """ Beneficiary Data: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def housing_type():
    """ Housing Types: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def income_source():
    """ Income Sources: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def beneficiary_type():
    """ Beneficiary Types: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def case_event_type():
    """ Case Event Types: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def case_event():
    """ Case Event Types: RESTful CRUD Controller """

    def prep(r):
        if not r.component:
            list_fields = ["date",
                           (T("ID"), "person_id$pe_label"),
                           "person_id",
                           "type_id",
                           (T("Registered by"), "created_by"),
                           "comments",
                           ]
            r.resource.configure(list_fields = list_fields,
                                 )
        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def activity_funding_reason():
    """ Activity Funding Reasons: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def activity_funding():
    """ Activity Funding Proposals: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def site_activity():
    """ Site Activity Reports: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def evaluation_question():
    """ RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def evaluation():
    """
        RESTful CRUD Controller
        - unused
    """

    S3SQLInlineComponent = s3base.S3SQLInlineComponent

    crud_fields = ["person_id",
                   "case_id",
                   #"date",
                   ]
    cappend = crud_fields.append

    table = s3db.dvr_evaluation_question
    rows = db(table.deleted != True).select(table.id,
                                            table.section,
                                            #table.header,
                                            table.number,
                                            table.name,
                                            orderby = table.number,
                                            )

    #subheadings = {}

    section = None
    for row in rows:
        name = "number%s" % row.number
        if row.section != section:
            label = section = row.section
            #subheadings[T(section)] = "sub_%sdata" % name
        else:
            label = ""
        cappend(S3SQLInlineComponent("data",
                                     name = name,
                                     label = label,
                                     fields = (("", "question_id"),
                                               ("", "answer"),
                                               ),
                                     filterby = dict(field = "question_id",
                                                     options = row.id
                                                     ),
                                     multiple = False,
                                     ),
                )

    cappend("comments")
    crud_form = s3base.S3SQLCustomForm(*crud_fields)

    s3db.configure("dvr_evaluation",
                   crud_form = crud_form,
                   #subheadings = subheadings,
                   )

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def evaluation_data():
    """ RESTful CRUD Controller """

    return s3_rest_controller()

# END =========================================================================
