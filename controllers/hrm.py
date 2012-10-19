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
        - combined (unused, except for Imports)
    """

    tablename = "hrm_human_resource"
    table = s3db[tablename]

    # Default to Staff
    _type = table.type
    s3.filter = (_type == 1)

    def prep(r):
        if r.method == "form":
            return True
        if r.interactive:
            if r.method == "create" and not r.component:
                redirect(URL(f="volunteer",
                             args=request.args,
                             vars=request.vars))
            elif r.method == "delete":
                # Don't redirect
                pass
            elif r.id:
                # Redirect to person controller
                vars = {
                        "human_resource.id" : r.id,
                        "group" : "staff"
                        }
                redirect(URL(f="person",
                             vars=vars))
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
                                   vars = {"hrm_id": "[id]"}),
                        "_class": "action-btn",
                        "label": str(T("Send Message"))})
        elif r.representation == "plain" and \
             r.method !="search":
            # Map Popups
            output = s3db.hrm_map_popup(r)
        return output
    s3.postp = postp

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def staff():
    """
        Staff Controller
    """

    tablename = "hrm_human_resource"
    table = s3db[tablename]

    _type = table.type
    _type.default = 1
    s3.filter = (_type == 1)
    table.site_id.writable = True
    table.site_id.readable = True
    list_fields = ["id",
                   "person_id",
                   "job_title_id",
                   "organisation_id",
                   "department_id",
                   "site_id",
                   #"site_contact",
                   (T("Email"), "email"),
                   (settings.get_ui_label_mobile_phone(), "phone"),
                   (T("Trainings"), "course"),
                   (T("Certificates"), "certificate"),
                   (T("Contract End Date"), "end_date"),
                   "status",
                   ]
    s3.crud_strings[tablename] = s3.crud_strings["hrm_staff"]
    if "expiring" in request.get_vars:
        s3.filter = s3.filter & \
            (table.end_date < (request.utcnow + datetime.timedelta(weeks=4)))
        s3.crud_strings[tablename].title_list = T("Staff with Contracts Expiring in the next Month")
        # Remove the big Add button
        s3db.configure(tablename,
                        insertable=False)
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
                # Assume staff only between 16-81
                s3db.pr_person.date_of_birth.widget = S3DateWidget(past=972, future=-192)

                table = r.table
                table.site_id.comment = DIV(DIV(_class="tooltip",
                                                _title="%s|%s|%s" % (settings.get_org_site_label(),
                                                                     T("The facility where this position is based."),
                                                                     T("Enter some characters to bring up a list of possible matches."))))
                table.status.writable = False
                table.status.readable = False

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
                                       vars = {"hrm_id": "[id]"}),
                            "_class": "action-btn",
                            "label": str(T("Send Message"))
                        })
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
        - used for Personal Profile & Imports
        - includes components relevant to HRM
    """

    configure = s3db.configure
    set_method = s3db.set_method

    # Custom Method for Contacts
    set_method("pr", resourcename,
               method="contacts",
               action=s3db.pr_contacts)

    # Plug-in role matrix for Admins/OrgAdmins
    realms = auth.user is not None and auth.user.realms or []
    if ADMIN in realms or ORG_ADMIN in realms:
        set_method("pr", resourcename, method="roles",
                   action=s3base.S3PersonRoleManager())

    if settings.has_module("asset"):
        # Assets as component of people
        s3db.add_component("asset_asset",
                            pr_person="assigned_to_id")
        # Edits should always happen via the Asset Log
        # @ToDo: Allow this method too, if we can do so safely
        configure("asset_asset",
                  insertable = False,
                  editable = False,
                  deletable = False)

    group = request.get_vars.get("group", "staff")
    hr_id = request.get_vars.get("human_resource.id", None)
    if not str(hr_id).isdigit():
        hr_id = None

    # Configure human resource table
    tablename = "hrm_human_resource"
    table = s3db[tablename]
    table.type.default = 1
    request.get_vars.update(xsltmode="staff")
    if hr_id:
        hr = table[hr_id]
        if hr:
            group = hr.type == 2 and "volunteer" or "staff"
            # Also inform the back-end of this finding
            request.get_vars["group"] = group

    # Configure person table
    tablename = "pr_person"
    table = s3db[tablename]
    if (group == "staff" and settings.get_hrm_staff_experience() == "programme") or \
       (group == "volunteer" and settings.get_hrm_vol_experience() == "programme"):
        table.virtualfields.append(s3db.hrm_programme_person_virtual_fields())
    configure(tablename,
              deletable=False)

    mode = session.s3.hrm.mode
    if mode is not None:
        # Configure for personal mode
        s3.crud_strings[tablename].update(
            title_display = T("Personal Profile"),
            title_update = T("Personal Profile"))
        # People can view their own HR data, but not edit it
        configure("hrm_human_resource",
                  insertable = False,
                  editable = False,
                  deletable = False)
        configure("hrm_certification",
                  insertable = True,
                  editable = True,
                  deletable = True)
        configure("hrm_credential",
                  insertable = False,
                  editable = False,
                  deletable = False)
        configure("hrm_competency",
                  insertable = True,  # Can add unconfirmed
                  editable = False,
                  deletable = False)
        configure("hrm_training",    # Can add but not provide grade
                  insertable = True,
                  editable = False,
                  deletable = False)
        configure("hrm_experience",
                  insertable = False,
                  editable = False,
                  deletable = False)
        configure("pr_group_membership",
                  insertable = False,
                  editable = False,
                  deletable = False)
    else:
        # Configure for HR manager mode
        s3.crud_strings[tablename].update(
                title_upload = T("Import Staff"),
                title_display = T("Staff Member Details"),
                title_update = T("Staff Member Details")
            )
    # Upload for configuration (add replace option)
    s3.importerPrep = lambda: dict(ReplaceOption=T("Remove existing data before import"))

    # Import pre-process
    def import_prep(data, group=group):
        """
            Deletes all HR records (of the given group) of the organisation
            before processing a new data import, used for the import_prep
            hook in s3mgr
        """
        resource, tree = data
        xml = current.xml
        tag = xml.TAG
        att = xml.ATTRIBUTE
        if s3.import_replace:
            if tree is not None:
                if group == "staff":
                    group = 1
                elif group == "volunteer":
                    group = 2
                else:
                    return # don't delete if no group specified

                root = tree.getroot()
                expr = "/%s/%s[@%s='org_organisation']/%s[@%s='name']" % \
                       (tag.root, tag.resource, att.name, tag.data, att.field)
                orgs = root.xpath(expr)
                for org in orgs:
                    org_name = org.get("value", None) or org.text
                    if org_name:
                        try:
                            org_name = json.loads(xml.xml_decode(org_name))
                        except:
                            pass
                    if org_name:
                        htable = s3db.hrm_human_resource
                        otable = s3db.org_organisation
                        query = (otable.name == org_name) & \
                                (htable.organisation_id == otable.id) & \
                                (htable.type == group)
                        resource = s3db.resource("hrm_human_resource", filter=query)
                        ondelete = s3db.get_config("hrm_human_resource", "ondelete")
                        resource.delete(ondelete=ondelete, format="xml", cascade=True)

    s3mgr.import_prep = import_prep

    # CRUD pre-process
    def prep(r):
        if r.representation == "s3json":
            s3mgr.show_ids = True
        elif r.interactive and r.method != "import":
            if not r.component:
                table = r.table
                table.pe_label.readable = False
                table.pe_label.writable = False
                table.missing.readable = False
                table.missing.writable = False
                table.age_group.readable = False
                table.age_group.writable = False
                # Assume volunteers only between 5-120
                table.date_of_birth.widget = S3DateWidget(past=1440, future=-60)

                person_details_table = s3db.pr_person_details
                # No point showing the 'Occupation' field - that's the Job Title in the Staff Record
                person_details_table.occupation.readable = False
                person_details_table.occupation.writable = False

                # Organisation Dependent Fields
                set_org_dependent_field = settings.set_org_dependent_field
                set_org_dependent_field("pr_person_details", "father_name")
                set_org_dependent_field("pr_person_details", "mother_name")
                set_org_dependent_field("pr_person_details", "affiliations")
                set_org_dependent_field("pr_person_details", "company")
            else:
                if r.component_name == "human_resource":
                    table = r.component.table
                    table.site_id.writable = True
                    table.site_id.readable = True
                    org = session.s3.hrm.org
                    if org is not None:
                        table.organisation_id.default = org
                        table.organisation_id.comment = None
                        table.organisation_id.readable = False
                        table.organisation_id.writable = False
                        table.site_id.requires = IS_EMPTY_OR(
                            IS_ONE_OF(db,
                                      "org_site.%s" % s3db.super_key(db.org_site),
                                      s3db.org_site_represent,
                                      filterby="organisation_id",
                                      filter_opts=[session.s3.hrm.org]))
                elif r.component_name == "physical_description":
                    # Hide all but those details that we want
                    # Lock all the fields
                    table = r.component.table
                    for field in table.fields:
                        table[field].writable = False
                        table[field].readable = False
                    # Now enable those that we want
                    table.ethnicity.writable = True
                    table.ethnicity.readable = True
                    table.blood_type.writable = True
                    table.blood_type.readable = True
                    table.medical_conditions.writable = True
                    table.medical_conditions.readable = True
                    table.other_details.writable = True
                    table.other_details.readable = True
                elif r.component_name == "asset":
                    # Edits should always happen via the Asset Log
                    # @ToDo: Allow this method too, if we can do so safely
                    configure("asset_asset",
                              insertable = False,
                              editable = False,
                              deletable = False)

            resource = r.resource
            if mode is not None:
                r.resource.build_query(id=s3_logged_in_person())
            else:
                if not r.id and not hr_id:
                    # pre-action redirect => must retain prior errors
                    if response.error:
                        session.error = response.error
                    redirect(URL(r=r, f="staff"))
            if resource.count() == 1:
                resource.load()
                r.record = resource.records().first()
                if r.record:
                    r.id = r.record.id
            if not r.record:
                session.error = T("Record not found")
                redirect(URL(f="staff",
                             args=["search"]))
            if hr_id and r.component_name == "human_resource":
                r.component_id = hr_id
            configure("hrm_human_resource",
                      insertable = False)
            #if not r.component_id or r.method in ("create", "update"):
            #    s3base.s3_address_hide(s3db.pr_address)
        return True
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
            elif r.component_name == "asset":
                # Provide a link to assign a new Asset
                # @ToDo: Proper Widget to do this inline
                output["add_btn"] = A(T("Assign Asset"),
                                      _href=URL(c="asset", f="asset"),
                                      _id="add-btn",
                                      _class="action-btn")
        return output
    s3.postp = postp

    # REST Interface
    if session.s3.hrm.orgname and mode is None:
        orgname = session.s3.hrm.orgname
    else:
        orgname = None

    output = s3_rest_controller("pr", resourcename,
                                native=False,
                                rheader=s3db.hrm_rheader,
                                orgname=orgname,
                                replace_option=T("Remove existing data before import"),
                                csv_extra_fields=[
                                    dict(label="Type",
                                         field=s3db.hrm_human_resource.type)
                                                  ],
                                )
    return output

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
    if (group == "staff" and settings.get_hrm_staff_experience() == "programme") or \
       (group == "volunteer" and settings.get_hrm_vol_experience() == "programme"):
        table.virtualfields.append(s3db.hrm_programme_person_virtual_fields())
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
                        table[field].writable = False
                        table[field].readable = False
                    # Now enable those that we want
                    table.ethnicity.writable = True
                    table.ethnicity.readable = True
                    table.blood_type.writable = True
                    table.blood_type.readable = True
                    table.medical_conditions.writable = True
                    table.medical_conditions.readable = True
                    table.other_details.writable = True
                    table.other_details.readable = True
            else:
                table = r.table
                # No point showing the 'Occupation' field - that's the Job Title in the Staff Record
                table.occupation.readable = False
                table.occupation.writable = False
                table.pe_label.readable = False
                table.pe_label.writable = False
                table.missing.readable = False
                table.missing.writable = False
                table.age_group.readable = False
                table.age_group.writable = False
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
                                native=False,
                                rheader=s3db.hrm_rheader,
                                )
    return output

# -----------------------------------------------------------------------------
def person_search():
    """
        Person REST controller
        - limited to just search.json for use in Autocompletes
        - allows differential access permissions
    """

    group = request.get_vars.get("group", None)
    if group == "staff":
        s3.filter = (s3db.hrm_human_resource.type == 1)
    elif group == "volunteer":
        s3.filter = (s3db.hrm_human_resource.type == 2)

    s3db.configure("hrm_human_resource",
                    # S3HRSearch
                    search_method = s3db.hrm_autocomplete_search,
                   )
    s3.prep = lambda r: r.representation == "json" and \
                        r.method == "search"
    return s3_rest_controller("hrm", "human_resource")

# =============================================================================
# Teams
# =============================================================================
def group():
    """
        Team controller
        - uses the group table from PR
    """

    tablename = "pr_group"
    table = s3db[tablename]

    _group_type = table.group_type
    _group_type.label = T("Team Type")
    table.description.label = T("Team Description")
    table.name.label = T("Team Name")
    mtable = s3db.pr_group_membership
    mtable.group_id.label = T("Team ID")
    mtable.group_head.label = T("Team Leader")

    # Set Defaults
    _group_type.default = 3  # 'Relief Team'
    _group_type.readable = _group_type.writable = False

    # Only show Relief Teams
    # Do not show system groups
    s3.filter = (table.system == False) & \
                (_group_type == 3)

    # CRUD Strings
    ADD_TEAM = T("Add Team")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_TEAM,
        title_display = T("Team Details"),
        title_list = T("Teams"),
        title_update = T("Edit Team"),
        title_search = T("Search Teams"),
        subtitle_create = T("Add New Team"),
        label_list_button = T("List Teams"),
        label_create_button = T("Add New Team"),
        label_search_button = T("Search Teams"),
        msg_record_created = T("Team added"),
        msg_record_modified = T("Team updated"),
        msg_record_deleted = T("Team deleted"),
        msg_list_empty = T("No Teams currently registered"))

    s3.crud_strings["pr_group_membership"] = Storage(
        title_create = T("Add Member"),
        title_display = T("Membership Details"),
        title_list = T("Team Members"),
        title_update = T("Edit Membership"),
        title_search = T("Search Member"),
        subtitle_create = T("Add New Member"),
        label_list_button = T("List Members"),
        label_create_button = T("Add Team Member"),
        label_delete_button = T("Delete Membership"),
        msg_record_created = T("Team Member added"),
        msg_record_modified = T("Membership updated"),
        msg_record_deleted = T("Membership deleted"),
        msg_list_empty = T("No Members currently registered"))

    s3db.configure(tablename, main="name", extra="description",
                    # Redirect to member list when a new group has been created
                    create_next = URL(f="group",
                                      args=["[id]", "group_membership"]))
    s3db.configure("pr_group_membership",
                    list_fields=["id",
                                 "person_id",
                                 "group_head",
                                 "description"])

    # Post-process
    def postp(r, output):

        if r.interactive:
            if not r.component:
                update_url = URL(args=["[id]", "group_membership"])
                s3_action_buttons(r, deletable=False, update_url=update_url)
                if "msg" in settings.modules and \
                   auth.permission.has_permission("update", c="hrm", f="compose"):
                    s3.actions.append({
                        "url": URL(f="compose",
                                   vars = {"group_id": "[id]"}),
                        "_class": "action-btn",
                        "label": str(T("Send Notification"))})

        return output
    s3.postp = postp

    tabs = [
            (T("Team Details"), None),
            # Team should be contacted either via the Leader or
            # simply by sending a message to the group as a whole.
            #(T("Contact Data"), "contact"),
            (T("Members"), "group_membership")
            ]

    output = s3_rest_controller("pr", resourcename,
                                rheader=lambda r: s3db.pr_rheader(r, tabs=tabs))

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

    s3.filter = auth.filter_by_root_org(s3db.hrm_department)

    output = s3_rest_controller()
    return output

def job_role():
    """ Job Roles Controller """

    mode = session.s3.hrm.mode
    def prep(r):
        if mode is not None:
            r.error(403, message=auth.permission.INSUFFICIENT_PRIVILEGES)
        return True
    s3.prep = prep
    
    s3.filter = auth.filter_by_root_org(s3db.hrm_job_role)

    output = s3_rest_controller()
    return output

def job_title():
    """ Job Titles Controller """

    mode = session.s3.hrm.mode
    def prep(r):
        if mode is not None:
            r.error(403, message=auth.permission.INSUFFICIENT_PRIVILEGES)
        return True
    s3.prep = prep

    s3.filter = auth.filter_by_root_org(s3db.hrm_job_title)

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

    s3.filter = auth.filter_by_root_org(s3db.hrm_job_title)

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

    return s3db.hrm_training_controller()

# -----------------------------------------------------------------------------
def training_event():
    """ Training Events Controller """

    return s3db.hrm_training_event_controller()

# =============================================================================
def skill_competencies():
    """
        Called by S3FilterFieldChange to provide the competency options for a
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
    #db.req_commit.date.represent = lambda dt: dt[:10]
    query = (table.person_id == request.args[0]) & \
            (table.organisation_id == otable.id)
    records = db(query).select(table.site_id,
                               otable.id,
                               otable.name)

    response.headers["Content-Type"] = "application/json"
    return records.json()

# =============================================================================
# Messaging
# =============================================================================
def compose():
    """ Send message to people/teams """

    return s3db.hrm_compose()

# END =========================================================================
