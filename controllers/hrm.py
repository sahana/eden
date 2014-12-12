# -*- coding: utf-8 -*-

"""
    Human Resource Management
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

s3db.hrm_vars()

# =============================================================================
def index():
    """ Module Home Page """

    mode = session.s3.hrm.mode
    if mode is not None:
        # Go to Personal Profile
        redirect(URL(f="person"))
    else:
        # Bypass home page & go direct to searchable list of Staff
        redirect(URL(f="staff", args="search"))

# =============================================================================
# People
# =============================================================================
def human_resource():
    """
        HR Controller
        - combined Staff/Volunteers
        Used for Summary view, Imports and S3AddPersonWidget2
    """

    return s3db.hrm_human_resource_controller()

# -----------------------------------------------------------------------------
def staff():
    """
        Staff Controller
    """

    tablename = "hrm_human_resource"
    table = s3db[tablename]

    get_vars = request.get_vars
    _type = table.type
    _type.default = 1
    s3.filter = (_type == 1)
    s3.crud_strings[tablename] = s3.crud_strings["hrm_staff"]
    if "expiring" in get_vars:
        s3.filter = s3.filter & \
            (table.end_date < (request.utcnow + datetime.timedelta(weeks=4)))
        s3.crud_strings[tablename].title_list = T("Staff with Contracts Expiring in the next Month")
        s3db.configure(tablename,
                       # Sort by Expiry
                       sortby = table.end_date,
                       # Remove the Add button
                       insertable=False
                       )
        list_fields = ["id",
                       (T("Contract End Date"), "end_date"),
                       "person_id",
                       "job_title_id",
                       "organisation_id",
                       "department_id",
                       "site_id",
                       #"site_contact",
                       ]
    else:
        list_fields = ["id",
                       "person_id",
                       "job_title_id",
                       "organisation_id",
                       "department_id",
                       "site_id",
                       #"site_contact",
                       (T("Email"), "email.value"),
                       (settings.get_ui_label_mobile_phone(), "phone.value"),
                       ]
        if settings.get_hrm_use_trainings():
            list_fields.append("person_id$training.course_id")
        if settings.get_hrm_use_certificates():
            list_fields.append("person_id$certification.certificate_id")
        list_fields.append((T("Contract End Date"), "end_date"))
        list_fields.append("status")
    # Remove Type filter from the Search widget
    human_resource_search = s3db.get_config(tablename,
                                            "search_method")
    human_resource_search.advanced.pop(1)
    s3db.configure(tablename,
                   list_fields = list_fields,
                   search_method = human_resource_search)

    def prep(r):
        if r.interactive:
            if not r.component and \
               not r.id and \
               r.method in [None, "create"]:
                # Don't redirect
                table = r.table
                site_id = get_vars.get("site_id", None)
                if site_id:
                    table.site_id.default = site_id
                    table.site_id.writable = False
                # Assume staff only between 16-81
                s3db.pr_person.date_of_birth.widget = S3DateWidget(past=972, future=-192)

                table.site_id.comment = DIV(DIV(_class="tooltip",
                                                _title="%s|%s" % (settings.get_org_site_label(),
                                                                  T("The facility where this position is based."),
                                                                  #T("Enter some characters to bring up a list of possible matches")
                                                                  )))
                table.status.writable = table.status.readable = False

            elif r.method == "delete":
                # Don't redirect
                pass
            elif r.id:
                # Redirect to person controller
                vars = {
                    "human_resource.id": r.id,
                    "group": "staff"
                }
                redirect(URL(f="person",
                             vars=vars))
            elif r.method == "import":
                # Redirect to person controller
                redirect(URL(f="person",
                             args="import",
                             vars={"group": "staff"}))
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component:
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('hrm_human_resource_start_date','hrm_human_resource_end_date')''')

                s3_action_buttons(r, deletable=settings.get_hrm_deletable())
                if "msg" in settings.modules and \
                   auth.permission.has_permission("update", c="hrm", f="compose"):
                    # @ToDo: Remove this now that we have it in Events?
                    s3.actions.append({
                            "url": URL(f="compose",
                                       vars = {"human_resource.id": "[id]"}),
                            "_class": "action-btn send",
                            "label": str(T("Send Message"))
                        })
                #s3.scripts.append("/%s/static/scripts/jquery.doubleScroll.js" % appname)
                #s3.jquery_ready.append('''$('.dataTable_table').doubleScroll()''')
                #s3.jquery_ready.append('''$('.dataTables_wrapper').doubleScroll()''')
        elif r.representation == "plain" and \
             r.method !="search":
            # Map Popups
            output = s3db.hrm_map_popup(r)
        return output
    s3.postp = postp

    output = s3_rest_controller("hrm", "human_resource")
    return output

# -----------------------------------------------------------------------------
def person():
    """
        Person Controller
        - used for access to component Tabs, Personal Profile & Imports
        - includes components relevant to HRM
    """

    return s3db.hrm_person_controller()

# -----------------------------------------------------------------------------
def profile():
    """
        Profile Controller
        - includes components relevant to HRM
    """

    request.args = [str(s3_logged_in_person())]

    # Custom Method for Contacts
    s3db.set_method("pr", resourcename,
                    method="contacts",
                    action=s3db.pr_contacts)

    if settings.has_module("asset"):
        # Assets as component of people
        s3db.add_component("asset_asset",
                           pr_person="assigned_to_id")

    group = request.get_vars.get("group", "staff")

    # Configure human resource table
    tablename = "hrm_human_resource"
    table = s3db[tablename]
    table.type.default = 1

    # Configure person table
    tablename = "pr_person"
    table = s3db[tablename]
    s3db.configure(tablename,
                   deletable=False)

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
                table.date_of_birth.widget = S3DateWidget(past=972, future=-144)
                return True
        else:
            # Disable non-interactive & import
            return False
    s3.prep = prep

    # CRUD post-process
    def postp(r, output):
        if r.interactive and r.component:
            if r.component_name == "human_resource":
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('hrm_human_resource_start_date','hrm_human_resource_end_date')''')
            if r.component_name == "experience":
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('hrm_experience_start_date','hrm_experience_end_date')''')

        return output
    s3.postp = postp

    output = s3_rest_controller("pr", "person",
                                rheader=s3db.hrm_rheader,
                                )
    return output

# -----------------------------------------------------------------------------
def person_search():
    """
        Person REST controller
        - limited to just search_ac for use in Autocompletes
        - allows differential access permissions
    """

    # Filter
    group = request.get_vars.get("group", None)
    if group == "staff":
        s3.filter = (s3db.hrm_human_resource.type == 1)
    elif group == "volunteer":
        s3.filter = (s3db.hrm_human_resource.type == 2)

    s3.prep = lambda r: r.method == "search_ac"
    return s3_rest_controller("hrm", "human_resource")

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

    output = s3_rest_controller("pr", "group_membership",
                                csv_template="group_membership",
                                csv_stylesheet=("hrm", "group_membership.xsl"),
                                )
    return output 

# =============================================================================
# Jobs
# =============================================================================
def department():
    """ Departments Controller """

    mode = session.s3.hrm.mode
    def prep(r):
        if mode is not None:
            r.error(403, message=auth.permission.INSUFFICIENT_PRIVILEGES)
        return True
    s3.prep = prep

    if not auth.s3_has_role(ADMIN):
        s3.filter = auth.filter_by_root_org(s3db.hrm_department)

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def job_title():
    """ Job Titles Controller """

    mode = session.s3.hrm.mode
    def prep(r):
        if mode is not None:
            r.error(403, message=auth.permission.INSUFFICIENT_PRIVILEGES)
        return True
    s3.prep = prep

    table = s3db.hrm_job_title
    s3.filter = (table.type.belongs([1, 3]))

    if not auth.s3_has_role(ADMIN):
        s3.filter &= auth.filter_by_root_org(table)

    output = s3_rest_controller()
    return output

# =============================================================================
# Skills
# =============================================================================
def skill():
    """ Skills Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def skill_type():
    """ Skill Types Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def competency_rating():
    """ Competency Rating for Skill Types Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def skill_provision():
    """ Skill Provisions Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def course():
    """ Courses Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    if not auth.s3_has_role(ADMIN):
        s3.filter = auth.filter_by_root_org(s3db.hrm_course)

    output = s3_rest_controller(rheader=s3db.hrm_rheader)
    return output

# -----------------------------------------------------------------------------
def course_certificate():
    """ Courses to Certificates Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def certificate():
    """ Certificates Controller """

    mode = session.s3.hrm.mode
    def prep(r):
        if mode is not None:
            r.error(403, message=auth.permission.INSUFFICIENT_PRIVILEGES)
        return True
    s3.prep = prep

    if settings.get_hrm_filter_certificates() and \
       not auth.s3_has_role(ADMIN):
        s3.filter = auth.filter_by_root_org(s3db.hrm_certificate)

    output = s3_rest_controller(rheader=s3db.hrm_rheader)
    return output

# -----------------------------------------------------------------------------
def certificate_skill():
    """ Certificates to Skills Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def training():
    """ Training Controller - used for Searching for Participants """

    table = s3db.hrm_human_resource
    s3.filter = ((table.type == 1) & \
                 (s3db.hrm_training.person_id == table.person_id))
    return s3db.hrm_training_controller()

# -----------------------------------------------------------------------------
def training_event():
    """ Training Events Controller """

    return s3db.hrm_training_event_controller()

# -----------------------------------------------------------------------------
def experience():
    """ Experience Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def competency():
    """ RESTful CRUD controller used to allow searching for people by Skill"""

    table = s3db.hrm_human_resource
    s3.filter = ((table.type == 1) & \
                 (s3db.hrm_competency.person_id == table.person_id))
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
        rows = db(query).select(table.id,
                                ptable.first_name,
                                ptable.middle_name,
                                ptable.last_name,
                                orderby=ptable.first_name)
        result = []
        append = result.append
        for row in rows:
            id = row.hrm_human_resource.id
            append({"id"   : id,
                    "name" : s3_fullname(row.pr_person)
                    })
        result = json.dumps(result)

    response.headers["Content-Type"] = "application/json"
    return result

# =============================================================================
# Messaging
# =============================================================================
def compose():
    """ Send message to people/teams """

    return s3db.hrm_compose()

# END =========================================================================
