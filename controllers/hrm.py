# -*- coding: utf-8 -*-

"""
    Human Resource Management
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# =============================================================================
def index():
    """ Customisable module homepage """

    return settings.customise_home(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Fallback for module homepage when not customised and
        no CMS content found (ADMINs will see CMS edit unless
        disabled globally via settings.cms.hide_index)
    """

    # Bypass home page & go direct to searchable list of Staff
    s3_redirect_default(URL(f="staff", args="summary"))

# =============================================================================
# People
# =============================================================================
def human_resource():
    """
        HR Controller
        - combined Staff/Volunteers
        Used for Summary view, Imports and S3AddPersonWidget
    """

    return s3db.hrm_human_resource_controller()

# -----------------------------------------------------------------------------
def staff():
    """ Staff Controller """

    # Staff only
    s3.filter = FS("type") == 1

    def prep(r):

        table = r.table
        tablename = r.tablename
        get_vars = r.get_vars

        # Use CRUD strings for staff
        crud_strings = s3.crud_strings
        crud_strings[tablename] = crud_strings["hrm_staff"]

        resource = r.resource
        if "expiring" in get_vars:
            # Filter for staff with contracts expiring in the next 4 weeks
            query = FS("end_date") < \
                        (request.utcnow + datetime.timedelta(weeks=4))
            resource.add_filter(query)
            # Adapt CRUD strings
            crud_strings[tablename].title_list = \
                T("Staff with Contracts Expiring in the next Month")
            # Reconfigure
            resource.configure(# Sort by Expiry
                               sortby = table.end_date,
                               # Remove the Add button
                               insertable=False
                              )
            # Adapt list_fields
            list_fields = [(T("Contract End Date"), "end_date"),
                           "person_id",
                           "job_title_id",
                           "organisation_id",
                           "site_id",
                           #"site_contact",
                           ]
            if settings.get_hrm_staff_departments():
                list_fields.insert(4, "department_id")
            resource.configure(list_fields = list_fields)
        elif r.representation == "xls":
            s3db.hrm_xls_list_fields(r, vol=False)
        else:
            # Adapt list_fields
            list_fields = ["person_id",
                           "job_title_id",
                           "organisation_id",
                           "site_id",
                           #"site_contact",
                           (T("Email"), "email.value"),
                           (settings.get_ui_label_mobile_phone(), "phone.value"),
                           ]
            if settings.get_hrm_staff_departments():
                list_fields.insert(3, "department_id")
            if settings.get_hrm_use_trainings():
                list_fields.append("person_id$training.course_id")
            if settings.get_hrm_use_certificates():
                list_fields.append("person_id$certification.certificate_id")
            list_fields.append((T("Contract End Date"), "end_date"))
            list_fields.append("status")
            resource.configure(list_fields = list_fields)

        if r.interactive:
            if r.id:
                if r.method not in ("profile", "delete"):
                    # Redirect to person controller
                    vars = {"human_resource.id": r.id,
                            "group": "staff"
                            }
                    args = [r.method]
                    if r.representation == "iframe":
                        vars["format"] = "iframe"
                        #args = [r.method]
                    redirect(URL(f="person", vars=vars, args=args))
            else:
                if r.method == "import":
                    # Redirect to person controller
                    redirect(URL(f="person",
                                 args="import",
                                 vars={"group": "staff"}))
                elif not r.component and r.method != "delete":
                    # Configure site_id
                    field = table.site_id
                    site_id = get_vars.get("site_id", None)
                    if site_id:
                        field.default = site_id
                        field.writable = False
                    field.comment = DIV(DIV(_class="tooltip",
                                            _title="%s|%s" % (
                                                    settings.get_org_site_label(),
                                                    T("The facility where this position is based."),
                                                    #messages.AUTOCOMPLETE_HELP,
                                            )))
                    #field.comment = S3PopupLink(c="org", f="facility",
                    #                            vars = dict(child="site_id",
                    #                                        parent="req"),
                    #                            title=T("Add New Site"),
                    #                            )

                    # Hide status field
                    table.status.writable = table.status.readable = False

                    # Assume staff only between 16-81
                    dob = s3db.pr_person.date_of_birth
                    dob.widget = S3CalendarWidget(past_months = 972,
                                                  future_months = -192,
                                                  )

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component:
                s3_action_buttons(r,
                                  deletable = settings.get_hrm_deletable())
                if "msg" in settings.modules and \
                   settings.get_hrm_compose_button() and \
                   auth.permission.has_permission("update", c="hrm", f="compose"):
                    # @ToDo: Remove this now that we have it in Events?
                    s3.actions.append(
                        {"url": URL(f="compose",
                                    vars = {"human_resource.id": "[id]"}),
                         "_class": "action-btn send",
                         "label": str(T("Send Message"))
                        })
                #s3.scripts.append("/%s/static/scripts/jquery.doubleScroll.js" % appname)
                #s3.jquery_ready.append('''$('.dataTable_table').doubleScroll()''')
                #s3.jquery_ready.append('''$('.dataTables_wrapper').doubleScroll()''')
        elif r.representation == "plain":
            # Map Popups
            output = s3db.hrm_map_popup(r)
        return output
    s3.postp = postp

    return s3_rest_controller("hrm", "human_resource")

# -----------------------------------------------------------------------------
def person():
    """
        Person Controller
        - used for access to component Tabs, Personal Profile & Imports
        - includes components relevant to HRM
    """

    return s3db.hrm_person_controller()

# -----------------------------------------------------------------------------
def trainee():
    """
        HR Controller
        - used by RMSAmericas to be able to filter to 'External Trainees'
    """

    return s3db.hrm_human_resource_controller()

# -----------------------------------------------------------------------------
def trainee_person():
    """
        Person Controller
        - used by RMSAmericas to be able to configure for 'External Trainees'
    """

    return s3db.hrm_person_controller()

# -----------------------------------------------------------------------------
def profile():
    """
        Profile Controller
        - includes components relevant to HRM
    """

    request.args = [str(auth.s3_logged_in_person())]

    # Custom Method for Contacts
    s3db.set_method("pr", resourcename,
                    method = "contacts",
                    action = s3db.pr_Contacts)

    if settings.has_module("asset"):
        # Assets as component of people
        s3db.add_components("pr_person",
                            asset_asset = "assigned_to_id",
                            )

    group = get_vars.get("group", "staff")

    # Configure human resource table
    tablename = "hrm_human_resource"
    table = s3db[tablename]
    table.type.default = 1

    # Configure person table
    tablename = "pr_person"
    table = s3db[tablename]
    s3db.configure(tablename,
                   deletable = False,
                   )

    # Configure for personal mode
    s3.crud_strings[tablename].update(
        title_display = T("Personal Profile"),
        title_update = T("Personal Profile"))

    # CRUD pre-process
    def prep(r):
        if r.interactive and r.method != "import":
            if r.component:
                if r.component_name == "physical_description":
                    # Hide all but those details that we want
                    # Lock all the fields
                    table = r.component.table
                    for field in table.fields:
                        table[field].writable = table[field].readable = False
                    # Now enable those that we want
                    table.ethnicity.writable = table.ethnicity.readable = True
                    table.blood_type.writable = table.blood_type.readable = True
                    table.medical_conditions.writable = table.medical_conditions.readable = True
                    table.other_details.writable = table.other_details.readable = True
            else:
                table = r.table
                table.pe_label.readable = table.pe_label.writable = False
                table.missing.readable = table.missing.writable = False
                table.age_group.readable = table.age_group.writable = False
                # Assume volunteers only between 12-81
                dob = table.date_of_birth
                dob.widget = S3CalendarWidget(past_months = 972,
                                              future_months = -144,
                                              )
                return True
        else:
            # Disable non-interactive & import
            return False
    s3.prep = prep

    return s3_rest_controller("pr", "person",
                              rheader = s3db.hrm_rheader,
                              )

# -----------------------------------------------------------------------------
def hr_search():
    """
        Human Resource REST controller
        - limited to just search_ac for use in Autocompletes
        - allows differential access permissions
    """

    # Filter
    group = get_vars.get("group", None)
    if group == "staff":
        s3.filter = FS("human_resource.type") == 1
    elif group == "volunteer":
        s3.filter = FS("human_resource.type") == 2

    s3.prep = lambda r: r.method == "search_ac"

    return s3_rest_controller("hrm", "human_resource")

# -----------------------------------------------------------------------------
def person_search():
    """
        Person REST controller
        - limited to just search_ac for use in Autocompletes
        - allows differential access permissions
    """

    # Filter
    group = get_vars.get("group", None)
    if group == "staff":
        s3.filter = FS("human_resource.type") == 1
    elif group == "volunteer":
        s3.filter = FS("human_resource.type") == 2

    s3.prep = lambda r: r.method == "search_ac"

    return s3_rest_controller("pr", "person")

# =============================================================================
# Teams
# =============================================================================
def group():
    """
        Team controller
        - uses the group table from PR
    """

    return s3db.hrm_group_controller()

# -----------------------------------------------------------------------------
def group_membership():
    """
        Membership controller
        - uses the group_membership table from PR
    """

    # Change Labels & list_fields
    s3db.hrm_configure_pr_group_membership()

    # Only show Relief Teams
    # Do not show system groups
    # Only show Staff
    table = db.pr_group_membership
    gtable = db.pr_group
    htable = s3db.hrm_human_resource
    s3.filter = (gtable.system == False) & \
                (gtable.group_type == 3) & \
                (htable.type == 1) & \
                (htable.person_id == table.person_id)

    def prep(r):
        if r.method in ("create", "create.popup", "update", "update.popup"):
            # Coming from Profile page?
            person_id = get_vars.get("~.person_id", None)
            if person_id:
                field = table.person_id
                field.default = person_id
                field.readable = field.writable = False
        return True
    s3.prep = prep

    return s3_rest_controller("pr", "group_membership",
                              csv_stylesheet = ("hrm", "group_membership.xsl"),
                              csv_template = "group_membership",
                              )

# =============================================================================
# Jobs
# =============================================================================
def department():
    """ Departments Controller """

    if not auth.s3_has_role("ADMIN"):
        s3.filter = auth.filter_by_root_org(s3db.hrm_department)

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def job_title():
    """ Job Titles Controller """

    def prep(r):
        if r.representation == "xls":
            # Export format should match Import format
            current.messages["NONE"] = ""
            table = s3db.hrm_job_title
            table.organisation_id.represent = \
                s3db.org_OrganisationRepresent(acronym=False,
                                               parent=False)
            table.organisation_id.label = None
            table.type.label = None
            table.comments.label = None
            table.comments.represent = lambda v: v or ""
        elif r.get_vars.get("caller") in ("event_human_resource_job_title_id", "event_scenario_human_resource_job_title_id"):
            # Default / Hide type
            f = s3db.hrm_job_title.type
            f.default = 4 # Deployment
            f.readable = f.writable = False
        return True
    s3.prep = prep

    s3.filter = FS("type").belongs((1, 3))

    if not auth.s3_has_role("ADMIN"):
        s3.filter &= auth.filter_by_root_org(s3db.hrm_job_title)

    return s3_rest_controller()

# =============================================================================
# Skills
# =============================================================================
def skill():
    """ Skills Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def skill_type():
    """ Skill Types Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def competency_rating():
    """ Competency Rating for Skill Types Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def skill_provision():
    """ Skill Provisions Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def course():
    """ Courses Controller """

    def prep(r):
        if r.component_name == "training":
            s3.crud_strings["hrm_training"].label_create = T("Add Trainee")
        return True
    s3.prep = prep

    if not auth.s3_has_role("ADMIN") and not s3.filter:
        s3.filter = auth.filter_by_root_org(s3db.hrm_course)

    return s3_rest_controller(rheader = s3db.hrm_rheader,
                              )

# -----------------------------------------------------------------------------
def course_certificate():
    """ Courses to Certificates Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def certificate():
    """ Certificates Controller """

    if settings.get_hrm_filter_certificates() and \
       not auth.s3_has_role("ADMIN"):
        s3.filter = auth.filter_by_root_org(s3db.hrm_certificate)

    return s3_rest_controller(rheader = s3db.hrm_rheader,
                              )

# -----------------------------------------------------------------------------
def certification():
    """ Certifications Controller """

    # Load Model
    table = s3db.hrm_certification

    # Over-ride list_fields
    s3db.configure("hrm_certification",
                   list_fields = ["person_id",
                                  "certificate_id",
                                  "number",
                                  "date",
                                  #"comments",
                                  ],
                   )

    if settings.get_hrm_filter_certificates() and \
       not auth.s3_has_role("ADMIN"):
        s3.filter = auth.filter_by_root_org(s3db.hrm_certificate)

    return s3_rest_controller(rheader = s3db.hrm_rheader,
                              )

# -----------------------------------------------------------------------------
def certificate_skill():
    """ Certificates to Skills Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def event_type():
    """ Event Types Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def facility():
    """
        Filtered version of the facility() REST controller
    """

    get_vars["facility_type.name"] = "Training Center"

    # Load model (including normal CRUD strings)
    table = s3db.org_facility

    # Modify CRUD Strings
    s3.crud_strings.org_facility = Storage(
        label_create = T("Create Training Center"),
        title_display = T("Training Center Details"),
        title_list = T("Training Centers"),
        title_update = T("Edit Training Center"),
        title_upload = T("Import Training Centers"),
        label_list_button = T("List Training Centers"),
        label_delete_button = T("Delete Training Center"),
        msg_record_created = T("Training Center added"),
        msg_record_modified = T("Training Center updated"),
        msg_record_deleted = T("Training Center deleted"),
        msg_list_empty = T("No Training Centers currently registered")
        )


    # Open record in this controller after creation
    s3db.configure("org_facility",
                   create_next = URL(c="hrm", f="facility",
                                     args = ["[id]", "read"]),
                   )

    return s3db.org_facility_controller()

# -----------------------------------------------------------------------------
def training_center():
    """
        Filtered version of the organisation() REST controller
    """

    get_vars["organisation_type.name"] = "Training Center"

    # Load model (including normal CRUD strings)
    table = s3db.org_organisation

    # Modify CRUD Strings
    s3.crud_strings.org_organisation = Storage(
        label_create = T("Create Training Center"),
        title_display = T("Training Center Details"),
        title_list = T("Training Centers"),
        title_update = T("Edit Training Center"),
        title_upload = T("Import Training Centers"),
        label_list_button = T("List Training Centers"),
        label_delete_button = T("Delete Training Center"),
        msg_record_created = T("Training Center added"),
        msg_record_modified = T("Training Center updated"),
        msg_record_deleted = T("Training Center deleted"),
        msg_list_empty = T("No Training Centers currently registered")
        )

    def create_onaccept(form):
        # Set this new Org to be a Branch of the User's Root Org
        root_org = auth.root_org()
        if root_org:
            id_ = s3db.org_organisation_branch.insert(organisation_id = root_org,
                                                      branch_id = form.vars.id,
                                                      )
            onaccept = s3db.get_config("org_organisation_branch", "onaccept")
            onaccept(Storage(vars = Storage(id = id_)))

        # Call normal onaccept
        onaccept = s3db.get_config("org_organisation", "onaccept")
        onaccept(form)

    s3db.configure("org_organisation",
                   # Open record in this controller after creation
                   create_next = URL(c="hrm", f="training_center",
                                     args = ["[id]", "read"]),
                   create_onaccept = create_onaccept,
                   )

    return s3db.org_organisation_controller()

# -----------------------------------------------------------------------------
def training():
    """ Training Controller - used for Importing/Searching for Participants """

    s3.filter = FS("person_id$human_resource.type") == 1
    return s3db.hrm_training_controller()

# -----------------------------------------------------------------------------
def training_event():
    """ Training Events Controller """

    return s3db.hrm_training_event_controller()

# -----------------------------------------------------------------------------
def credential():
    """ Credentials Controller """

    s3.filter = FS("person_id$human_resource.type") == 1
    return s3db.hrm_credential_controller()

# -----------------------------------------------------------------------------
def experience():
    """ Experience Controller """

    s3.filter = FS("person_id$human_resource.type") == 1
    return s3db.hrm_experience_controller()

# -----------------------------------------------------------------------------
def competency():
    """
        RESTful CRUD controller
        - used to allow searching for people by Skill
        - used for options.s3json lookups
    """

    s3.filter = FS("person_id$human_resource.type") == 1

    field = s3db.hrm_competency.person_id
    field.widget = S3PersonAutocompleteWidget(ajax_filter = "~.human_resource.type=1")

    return s3db.hrm_competency_controller()

# =============================================================================
def skill_competencies():
    """
        Called by S3OptionsFilter to provide the competency options for a
            particular Skill Type
    """

    table = s3db.hrm_skill
    ttable = s3db.hrm_skill_type
    rtable = s3db.hrm_competency_rating
    query = (table.id == request.args[0]) & \
            (table.skill_type_id == ttable.id) & \
            (rtable.skill_type_id == table.skill_type_id)
    records = db(query).select(rtable.id,
                               rtable.name,
                               orderby=~rtable.priority)

    response.headers["Content-Type"] = "application/json"
    return records.json()

# =============================================================================
def staff_org_site_json():
    """
        Used by the Asset - Assign to Person page
    """

    table = s3db.hrm_human_resource
    otable = s3db.org_organisation
    query = (table.person_id == request.args[0]) & \
            (table.organisation_id == otable.id)
    records = db(query).select(table.site_id,
                               otable.id,
                               otable.name)

    response.headers["Content-Type"] = "application/json"
    return records.json()

# =============================================================================
def staff_for_site():
    """
        Used by the Req/Req/Create page
        - note that this returns Person IDs
    """

    try:
        site_id = request.args[0]
    except:
        result = current.xml.json_message(False, 400, "No Site provided!")
    else:
        table = s3db.hrm_human_resource
        ptable = db.pr_person
        query = (table.site_id == site_id) & \
                (table.deleted == False) & \
                (table.status == 1) & \
                ((table.end_date == None) | \
                 (table.end_date > request.utcnow)) & \
                (ptable.id == table.person_id)
        rows = db(query).select(ptable.id,
                                ptable.first_name,
                                ptable.middle_name,
                                ptable.last_name,
                                orderby=ptable.first_name)
        result = []
        append = result.append
        for row in rows:
            append({"id"   : row.id,
                    "name" : s3_fullname(row)
                    })
        result = json.dumps(result)

    response.headers["Content-Type"] = "application/json"
    return result

# =============================================================================
# Programmes
# =============================================================================
def programme():
    """ Programmes Controller """

    return s3_rest_controller()

def programme_hours():
    """ Programme Hours Controller """

    return s3_rest_controller()

# =============================================================================
def strategy():
    """ Strategies Controller """

    return s3_rest_controller("project")

# =============================================================================
# Salaries
# =============================================================================
def staff_level():
    """ Staff Levels Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def salary_grade():
    """ Salary Grade Controller """

    return s3_rest_controller()

# =============================================================================
# Insurance Information
# =============================================================================
def insurance():
    """ Insurance Information Controller """

    return s3_rest_controller()

# =============================================================================
# Awards
# =============================================================================
def award_type():
    """ Award Type Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def award():
    """ Awards Controller """

    return s3_rest_controller()

# =============================================================================
# Disciplinary Record
# =============================================================================
def disciplinary_type():
    """ Disciplinary Type Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def disciplinary_action():
    """ Disciplinary Action Controller """

    return s3_rest_controller()

# =============================================================================
# Shifts
# =============================================================================
def shift():
    """ Shifts Controller """

    return s3_rest_controller()

def shift_template():
    """ Shift Templates Controller """

    return s3_rest_controller()

# =============================================================================
# Messaging
# =============================================================================
def compose():
    """ Send message to people/teams """

    return s3db.hrm_compose()

# END =========================================================================
