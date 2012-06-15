# -*- coding: utf-8 -*-

"""
    Human Resource Management
"""
module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

s3db.hrm_vars()

# =============================================================================
def index():
    """ Dashboard """

    mode = session.s3.hrm.mode
    if mode is not None:
        # Go to Personal Profile
        redirect(URL(f="person"))
    else:
        # Bypass home page & go direct to searchable list of Volunteers
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
    _type.default = 1
    s3.filter = (_type == 1)
    _type.readable = False
    _type.writable = False
    table.site_id.writable = True
    table.site_id.readable = True
    list_fields = ["id",
                   "person_id",
                   "job_role_id",
                   "organisation_id",
                   "site_id",
                   #"site_contact",
                   (T("Email"), "email"),
                   (deployment_settings.get_ui_label_mobile_phone(), "phone"),
                   (T("Trainings"), "course"),
                   (T("Certificates"), "certificate"),
                   (T("Contract End Date"), "end_date"),
                   "status",
                  ]
    s3mgr.configure(tablename,
                    list_fields = list_fields)
    if "expiring" in request.get_vars:
        s3.filter = s3.filter & \
            (table.end_date < (request.utcnow + datetime.timedelta(weeks=4)))
        s3.crud_strings[tablename].title_list = T("Staff with Contracts Expiring in the next Month")
        # Remove the big Add button
        s3mgr.configure(tablename,
                        insertable=False)

    def prep(r):
        if r.method == "form":
            return True
        if r.interactive:
            # Assume staff only between 16-81
            s3db.pr_person.date_of_birth.widget = S3DateWidget(past=972, future=-192)

            table = r.table
            table.site_id.comment = DIV(DIV(_class="tooltip",
                                            _title="%s|%s|%s" % (T("Facility"),
                                                                 T("The site where this position is based."),
                                                                 T("Enter some characters to bring up a list of possible matches."))))
            if r.method != "read":
                # Don't want to see in Create forms
                # inc list_create (list_fields over-rides)
                field = table.status
                field.writable = False
                field.readable = False

            if r.method == "create" and r.component is None:
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
                s3_action_buttons(r, deletable=deployment_settings.get_hrm_deletable())
                if "msg" in deployment_settings.modules:
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
                   "job_role_id",
                   "organisation_id",
                   "site_id",
                   #"site_contact",
                   (T("Email"), "email"),
                   (deployment_settings.get_ui_label_mobile_phone(), "phone"),
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
        s3mgr.configure(tablename,
                        insertable=False)
    # Remove Type filter from the Search widget
    human_resource_search = s3mgr.model.get_config(tablename,
                                                   "search_method")
    human_resource_search._S3Search__advanced.pop(1)
    s3mgr.configure(tablename,
                    list_fields = list_fields,
                    search_method = human_resource_search)

    def prep(r):
        if r.interactive:
            # Assume staff only between 16-81
            s3db.pr_person.date_of_birth.widget = S3DateWidget(past=972, future=-192)

            table = r.table
            table.site_id.comment = DIV(DIV(_class="tooltip",
                                            _title="%s|%s|%s" % (T("Facility"),
                                                                 T("The site where this position is based."),
                                                                 T("Enter some characters to bring up a list of possible matches."))))
            if r.method != "read":
                # Don't want to see in Create forms
                # inc list_create (list_fields over-rides)
                field = table.status
                field.writable = False
                field.readable = False

            if r.method == "create" and r.component is None:
                # Don't redirect
                pass
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
                s3_action_buttons(r, deletable=deployment_settings.get_hrm_deletable())
                if "msg" in deployment_settings.modules:
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

    configure = s3mgr.configure
    set_method = s3mgr.model.set_method
    super_key = s3mgr.model.super_key

    # Custom Method for Contacts
    set_method("pr", resourcename,
               method="contacts",
               action=s3db.pr_contacts)
    # Custom Method for Identity
    set_method("pr", resourcename,
               method="identity")
    # Custom Method for Education
    set_method("pr", resourcename,
               method="education")
    # Custom Method for Description
    set_method("pr", resourcename,
               method="physical_description")
    # Hide all but those details that we want
    # Lock all the fields
    pr_desc_table = s3db.pr_physical_description
    for field in pr_desc_table.fields:
        pr_desc_table[field].writable = False
        pr_desc_table[field].readable = False
    # Now enable those that we want
    pr_desc_table.ethnicity.writable = True
    pr_desc_table.ethnicity.readable = True
    pr_desc_table.blood_type.writable = True
    pr_desc_table.blood_type.readable = True
    pr_desc_table.medical_conditions.writable = True
    pr_desc_table.medical_conditions.readable = True
    pr_desc_table.other_details.writable = True
    pr_desc_table.other_details.readable = True

    # Plug-in role matrix for Admins/OrgAdmins
    realms = auth.user is not None and auth.user.realms or []
    if ADMIN in realms or ORG_ADMIN in realms:
        set_method("pr", resourcename, method="roles",
                   action=s3base.S3PersonRoleManager())

    if deployment_settings.has_module("asset"):
        # Assets as component of people
        s3mgr.model.add_component("asset_asset",
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

    mode = session.s3.hrm.mode

    # Configure human resource table
    tablename = "hrm_human_resource"
    table = s3db[tablename]
    if hr_id and str(hr_id).isdigit():
        hr = table[hr_id]
        if hr:
            group = hr.type == 2 and "volunteer" or "staff"
            # Also inform the back-end of this finding
            request.get_vars["group"] = group

    org = session.s3.hrm.org
    if org is not None:
        table.organisation_id.default = org
        table.organisation_id.comment = None
        table.organisation_id.readable = False
        table.organisation_id.writable = False
        table.site_id.requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                    "org_site.%s" % super_key(db.org_site),
                                    s3db.org_site_represent,
                                    filterby="organisation_id",
                                    filter_opts=[session.s3.hrm.org]))
    if hr_id:
        table.site_id.writable = True
        table.site_id.readable = True
    else:
        table.location_id.readable = True
        table.site_id.readable = True

    if session.s3.hrm.mode is not None:
        list_fields=["id",
                     "organisation_id",
                     "type",
                     "job_role_id",
                     "location_id",
                     "site_id",
                     "status"
                     ]
    else:
        list_fields=["id",
                     "type",
                     "job_role_id",
                     "location_id",
                     "site_id",
                     "status"
                     ]

    configure(tablename,
              list_fields=list_fields)

    # Configure person table
    # - hide fields
    tablename = "pr_person"
    table = s3db[tablename]
    if deployment_settings.get_hrm_experience() == "programme":
        table.virtualfields.append(s3db.hrm_programme_person_virtual_fields())
    table.pe_label.readable = False
    table.pe_label.writable = False
    table.missing.readable = False
    table.missing.writable = False
    table.age_group.readable = False
    table.age_group.writable = False
    configure(tablename,
              deletable=False)

    s3.crud_strings[tablename].update(
        title_upload = T("Import Staff"))
    # No point showing the 'Occupation' field - that's the Job Title in the Staff Record
    table.occupation.readable = False
    table.occupation.writable = False
    # Just have a Home Address
    table = s3db.pr_address
    #table.type.default = 1
    #table.type.readable = False
    #table.type.writable = False
    _crud = s3.crud_strings.pr_address
    _crud.title_create = T("Add Home Address")
    _crud.title_update = T("Edit Home Address")
    #s3mgr.model.add_component("pr_address",
    #                          pr_pentity=dict(joinby=super_key(s3db.pr_pentity),
    #                                          multiple=False))
    # Default type for HR
    table = s3db.hrm_human_resource
    table.type.default = 1
    request.get_vars.update(xsltmode="staff")

    if session.s3.hrm.mode is not None:
        # Configure for personal mode
        s3db.hrm_human_resource.organisation_id.readable = True
        s3.crud_strings[tablename].update(
            title_display = T("Personal Profile"),
            title_update = T("Personal Profile"))
        # People can view their own HR data, but not edit it
        configure("hrm_human_resource",
                  insertable = False,
                  editable = False,
                  deletable = False
                  )
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
            title_upload = T("Import Staff & Volunteers"))
        if group == "staff":
            s3.crud_strings[tablename].update(
                title_display = T("Staff Member Details"),
                title_update = T("Staff Member Details"))
        elif group == "volunteer":
            s3.crud_strings[tablename].update(
                title_display = T("Volunteer Details"),
                title_update = T("Volunteer Details"))

    # Upload for configuration (add replace option)
    s3.importerPrep = lambda: dict(ReplaceOption=T("Remove existing data before import"))

    # Import pre-process
    def import_prep(data, group=group):
        """
            Deletes all HR records (of the given group) of the organisation
            before processing a new data import, used for the import_prep
            hook in s3mgr
        """
        request = current.request

        resource, tree = data
        xml = s3mgr.xml
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
                            org_name = json.loads(s3mgr.xml.xml_decode(org_name))
                        except:
                            pass
                    if org_name:
                        htable = s3db.hrm_human_resource
                        otable = s3db.org_organisation
                        query = (otable.name == org_name) & \
                                (htable.organisation_id == otable.id) & \
                                (htable.type == group)
                        resource = s3mgr.define_resource("hrm", "human_resource", filter=query)
                        ondelete = s3mgr.model.get_config("hrm_human_resource", "ondelete")
                        resource.delete(ondelete=ondelete, format="xml", cascade=True)

    s3mgr.import_prep = import_prep

    # CRUD pre-process
    def prep(r):
        if r.representation == "s3json":
            s3mgr.show_ids = True
        elif r.interactive and r.method != "import":
            if r.component:
                if r.component_name == "asset":
                    # Edits should always happen via the Asset Log
                    # @ToDo: Allow this method too, if we can do so safely
                    configure("asset_asset",
                              insertable = False,
                              editable = False,
                              deletable = False)
            else:
                # Assume volunteers only between 12-81
                r.table.date_of_birth.widget = S3DateWidget(past=972, future=-144)

            resource = r.resource
            if mode is not None:
                r.resource.build_query(id=s3_logged_in_person())
            else:
                if not r.id and not hr_id:
                    # pre-action redirect => must retain prior errors
                    if response.error:
                        session.error = response.error
                    redirect(URL(r=r, f="human_resource"))
            if resource.count() == 1:
                resource.load()
                r.record = resource.records().first()
                if r.record:
                    r.id = r.record.id
            if not r.record:
                session.error = T("Record not found")
                redirect(URL(f="human_resource",
                             args=["search"], vars={"group":group}))
            if hr_id and r.component_name == "human_resource":
                r.component_id = hr_id
            configure("hrm_human_resource",
                      insertable = False)
            if not r.component_id or r.method in ("create", "update"):
                address_hide(s3db.pr_address)
        return True
    s3.prep = prep

    # CRUD post-process
    def postp(r, output):
        if r.interactive and r.component and r.component_name == "asset":
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
                                replace_option=T("Remove existing data before import"))
    return output

# -----------------------------------------------------------------------------
def person_search():
    """
        Person REST controller
        - limited to just search.json for use in Autocompletes
        - allows differential access permissions
    """
    s3mgr.configure("hrm_human_resource",
                    search_method = s3db.hrm_autocomplete_search,
                   )
    s3.prep = lambda r: r.representation == "json" and \
                        r.method == "search"
    return s3_rest_controller(module, "human_resource")

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

    s3mgr.configure(tablename, main="name", extra="description",
                    # Redirect to member list when a new group has been created
                    create_next = URL(f="group",
                                      args=["[id]", "group_membership"]))
    s3mgr.configure("pr_group_membership",
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
                if "msg" in deployment_settings.modules:
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
def job_role():
    """ Job Roles Controller """

    mode = session.s3.hrm.mode
    def prep(r):
        if mode is not None:
            r.error(403, message=auth.permission.INSUFFICIENT_PRIVILEGES)
        return True
    s3.prep = prep

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
    """ Training Controller """

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
