# -*- coding: utf-8 -*-

"""
    Volunteer Management
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
    s3_redirect_default(URL(f="volunteer", args="summary"))

# =============================================================================
# People
# =============================================================================
def human_resource():
    """
        HR Controller
        - combined
        Used for Summary view, Imports, S3AddPersonWidget and the service record
    """

    # Custom method for Service Record
    s3db.set_method("hrm", "human_resource",
                    method = "form",
                    action = s3db.vol_service_record,
                    )

    return s3db.hrm_human_resource_controller()

# -----------------------------------------------------------------------------
def person():

    return s3db.vol_person_controller()


# -----------------------------------------------------------------------------
def volunteer():

    return s3db.vol_volunteer_controller()

# -----------------------------------------------------------------------------
def hr_search():
    """
        Human Resource REST controller
        - limited to just search_ac for use in Autocompletes
        - allows differential access permissions
    """

    # Filter to just Volunteers
    s3.filter = FS("human_resource.type") == 2

    # Only allow use in the search_ac method
    s3.prep = lambda r: r.method == "search_ac"

    return s3_rest_controller("hrm", "human_resource")

# -----------------------------------------------------------------------------
def person_search():
    """
        Person REST controller
        - limited to just search_ac for use in Autocompletes
        - allows differential access permissions
    """

    # Filter to just Volunteers
    s3.filter = FS("human_resource.type") == 2

    # Only allow use in the search_ac method
    s3.prep = lambda r: r.method == "search_ac"

    return s3_rest_controller("pr", "person")

# =============================================================================
# Teams
# =============================================================================
def group():
    """
        Team controller
        - uses the group table from PR, but filtered to just 'Relief Teams'
    """

    return s3db.hrm_group_controller()

# -----------------------------------------------------------------------------
def group_membership():
    """
        Membership controller
        - uses the group_membership table from PR
    """

    # Change Labels
    s3db.hrm_configure_pr_group_membership()

    table = db.pr_group_membership

    # Amend list_fields
    s3db.configure("pr_group_membership",
                   list_fields=["group_id",
                                "group_id$description",
                                "group_head",
                                "person_id$first_name",
                                "person_id$middle_name",
                                "person_id$last_name",
                                (T("Email"), "person_id$email.value"),
                                (settings.get_ui_label_mobile_phone(), "person_id$phone.value"),
                                ])

    # Only show Relief Teams
    # Do not show system groups
    # Only show Volunteers
    gtable = db.pr_group
    htable = s3db.hrm_human_resource
    s3.filter = (gtable.system == False) & \
                (gtable.group_type == 3) & \
                (htable.type == 2) & \
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
                              csv_template = ("hrm", "group_membership"),
                              )

# =============================================================================
# Jobs
# =============================================================================
def department():
    """ Departments Controller """

    if not auth.s3_has_role("ADMIN"):
        s3.filter = auth.filter_by_root_org(s3db.hrm_department)

    return s3_rest_controller("hrm", resourcename)

# -----------------------------------------------------------------------------
def job_title():
    """ Job Titles Controller """

    def prep(r):
        if r.representation == "xls":
            # Export format should match Import format
            current.messages["NONE"] = ""
            table = s3db.hrm_job_title
            table.organisation_id.represent = \
                s3db.org_OrganisationRepresent(acronym = False,
                                               parent = False,
                                               )
            table.organisation_id.label = None
            table.type.label = None
            table.comments.label = None
            table.comments.represent = lambda v: v or ""
        return True
    s3.prep = prep

    s3.filter = FS("human_resource.type").belongs((2, 3))

    if not auth.s3_has_role("ADMIN"):
        s3.filter &= auth.filter_by_root_org(s3db.hrm_job_title)

    return s3_rest_controller("hrm", resourcename,
                              csv_stylesheet = ("hrm", "job_title.xsl"),
                              csv_template = ("hrm", "job_title"),
                              )

# =============================================================================
# Skills
# =============================================================================
def skill():
    """ Skills Controller """

    return s3_rest_controller("hrm", resourcename,
                              csv_stylesheet = ("hrm", "skill.xsl"),
                              csv_template = ("hrm", "skill"),
                              )

# -----------------------------------------------------------------------------
def skill_type():
    """ Skill Types Controller """

    return s3_rest_controller("hrm", resourcename)

# -----------------------------------------------------------------------------
def competency_rating():
    """ Competency Rating for Skill Types Controller """

    return s3_rest_controller("hrm", resourcename,
                              csv_stylesheet = ("hrm", "competency_rating.xsl"),
                              csv_template = ("hrm", "competency_rating"),
                              )

# -----------------------------------------------------------------------------
def skill_provision():
    """ Skill Provisions Controller """

    return s3_rest_controller("hrm", resourcename)

# -----------------------------------------------------------------------------
def course():
    """ Courses Controller """

    if not auth.s3_has_role("ADMIN"):
        s3.filter = auth.filter_by_root_org(s3db.hrm_course)

    return s3_rest_controller("hrm", resourcename,
                              csv_stylesheet = ("hrm", "course.xsl"),
                              csv_template = ("hrm", "course"),
                              rheader = s3db.hrm_rheader,
                              )

# -----------------------------------------------------------------------------
def course_certificate():
    """ Courses to Certificates Controller """

    return s3_rest_controller("hrm", resourcename)

# -----------------------------------------------------------------------------
def certificate():
    """ Certificates Controller """

    if settings.get_hrm_filter_certificates() and \
       not auth.s3_has_role("ADMIN"):
        s3.filter = auth.filter_by_root_org(s3db.hrm_certificate)

    return s3_rest_controller("hrm", resourcename,
                              csv_stylesheet = ("hrm", "certificate.xsl"),
                              csv_template = ("hrm", "certificate"),
                              rheader = s3db.hrm_rheader,
                              )

# -----------------------------------------------------------------------------
def certificate_skill():
    """ Certificates to Skills Controller """

    return s3_rest_controller("hrm", resourcename)

# -----------------------------------------------------------------------------
def training():
    """ Training Controller - used for Searching for Participants """

    # Filter to just Volunteers
    s3.filter = FS("human_resource.type") == 2

    return s3db.hrm_training_controller()

# -----------------------------------------------------------------------------
def training_event():
    """ Training Events Controller """

    table = s3db.hrm_training
    table.person_id.widget = S3PersonAutocompleteWidget(controller="vol")

    return s3db.hrm_training_event_controller()

# -----------------------------------------------------------------------------
def competency():
    """ RESTful CRUD controller used to allow searching for people by Skill"""

    # Filter to just Volunteers
    s3.filter = FS("person_id$human_resource.type") == 2

    field = s3db.hrm_competency.person_id
    field.widget = S3PersonAutocompleteWidget(ajax_filter = "~.human_resource.type=2")

    return s3db.hrm_competency_controller()

# -----------------------------------------------------------------------------
def credential():
    """ Credentials Controller """

    # Filter to just Volunteers
    s3.filter = FS("person_id$human_resource.type") == 2

    return s3db.hrm_credential_controller()

# -----------------------------------------------------------------------------
def experience():
    """ Experience Controller """

    # Filter to just Volunteers
    s3.filter = FS("person_id$human_resource.type") == 2

    return s3db.hrm_experience_controller()

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
                               orderby = ~rtable.priority,
                               )

    response.headers["Content-Type"] = "application/json"
    return records.json()

# =============================================================================
def staff_org_site_json():
    """
        Used by the Asset - Assign to Person page
    """

    table = s3db.hrm_human_resource
    otable = s3db.org_organisation
    #db.req_commit.date.represent = lambda dt: dt[:10]
    query = (table.person_id == request.args[0]) & \
            (table.organisation_id == otable.id)
    records = db(query).select(table.site_id,
                               otable.id,
                               otable.name,
                               )

    response.headers["Content-Type"] = "application/json"
    return records.json()

# =============================================================================
def activity_type():

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def activity():

    def prep(r):
        if r.component_name == "hours":

            # Limit Activity Types to those for the Activity
            ltable = s3db.vol_activity_activity_type
            query = (ltable.activity_id == r.id) & \
                    (ltable.deleted == False)
            rows = db(query).select(ltable.activity_type_id)
            activity_types = [row.activity_type_id for row in rows]

            field = s3db.vol_activity_hours_activity_type.activity_type_id
            field.requires = \
               IS_EMPTY_OR(IS_ONE_OF(db,
                                     "vol_activity_type.id",
                                     field.represent,
                                     filterby = "id",
                                     filter_opts = activity_types,
                                     ))

            # Limit the Dates to the same as the Activity
            record = r.record
            start_date = record.date
            end_date = record.end_date
            if end_date is None or start_date == end_date:
                field = s3db.vol_activity_hours.date
                field.default = start_date
                field.readable = field.writable = False
            else:
                # @ToDo: Check widget options (currently this branch is never taken)
                s3db.vol_activity_hours.date.requires = IS_UTC_DATE(
                                                            calendar = "Gregorian",
                                                            minimum = start_date,
                                                            maximum = end_date,
                                                            )
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.hrm_rheader,
                              )

# -----------------------------------------------------------------------------
def activity_hours():
    """
        Volunteer Activity Hours controller
        - used for Imports & Reports
    """

    return s3_rest_controller()

# =============================================================================
def facility():
    """
        e.g. Training Venues
    """

    # Open record in this controller after creation
    s3db.configure("org_facility",
                   create_next = URL(c="vol", f="facility",
                                     args = ["[id]", "read"],
                                     ),
                   )

    return s3db.org_facility_controller()

# =============================================================================
def programme():
    """ Volunteer Programmes controller """

    if not auth.s3_has_role("ADMIN"):
        s3.filter = auth.filter_by_root_org(s3db.hrm_programme)

    def prep(r):
        if r.component_name == "person":
            s3db.configure("hrm_programme_hours",
                           list_fields = ["person_id",
                                          "training",
                                          "programme_id",
                                          "date",
                                          "hours",
                                          ])
        return True
    s3.prep = prep

    return s3_rest_controller("hrm", resourcename,
                              csv_stylesheet = ("hrm", "programme.xsl"),
                              csv_template = ("hrm", "programme"),
                              rheader = s3db.hrm_rheader,
                              )

# -----------------------------------------------------------------------------
def programme_hours():
    """
        Volunteer Programme Hours controller
        - used for Imports & Reports
    """

    return s3_rest_controller("hrm", resourcename,
                              csv_stylesheet = ("hrm", "programme_hours.xsl"),
                              csv_template = ("hrm", "programme_hours")
                              )

# =============================================================================
def award():
    """ Volunteer Awards controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def volunteer_award():
    """
        Used for returning options to the S3PopupLink PopUp
    """

    # We use component form instead
    #def prep(r):
    #    if r.method in ("create", "create.popup", "update", "update.popup"):
    #        # Coming from Profile page?
    #        person_id = get_vars.get("~.person_id", None)
    #        if person_id:
    #            field = r.table.person_id
    #            field.default = person_id
    #            field.readable = field.writable = False
    #    return True
    #s3.prep = prep

    return s3_rest_controller()

# =============================================================================
def cluster_type():
    """ Volunteer Cluster Types controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def cluster():
    """ Volunteer Clusters controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def cluster_position():
    """ Volunteer Group Positions controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def volunteer_cluster():
    """ ONLY FOR RETURNING options to the S3PopupLink PopUp """

    return s3_rest_controller()

# =============================================================================
def task():
    """ Tasks controller """

    return s3db.project_task_controller()

# =============================================================================
# Messaging
# =============================================================================
def compose():
    """ Send message to people/teams """

    return s3db.hrm_compose()

# END =========================================================================
