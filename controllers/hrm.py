# -*- coding: utf-8 -*-

"""
    Human Resource Management
"""

module = request.controller
resourcename = request.function

if module not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

s3db.hrm_vars(module)

# =============================================================================
def index():
    """ Dashboard """

    mode = session.s3.hrm.mode
    if mode is not None:
        redirect(URL(f="person"))

    tablename = "hrm_human_resource"
    table = s3db.hrm_human_resource

    roles = session.s3.roles or []
    if ADMIN not in roles:
        orgs = session.s3.hrm.orgs or [None]
        org_filter = (table.organisation_id.belongs(orgs))
    else:
        # Admin can see all Orgs
        org_filter = (table.organisation_id > 0)

    s3mgr.configure(tablename,
                    insertable=False,
                    list_fields=["id",
                                 "person_id",
                                 "job_title",
                                 "type",
                                 "site_id"])

    response.s3.filter = org_filter
    # Parse the Request
    r = s3base.S3Request(s3mgr, prefix="hrm", name="human_resource")
    # Pre-process
    # Only set the method to search if it is not an ajax dataTable call
    # This fixes a problem with the dataTable where the the filter had a
    # distinct in the sql which cause a ticket to be raised
    if r.representation != "aadata":
        r.method = "search"
    r.custom_action = s3db.hrm_human_resource_search
    # Execute the request
    output = r()
    if r.representation == "aadata":
        return output
    # Post-process
    response.s3.actions = [dict(label=str(T(messages["UPDATE"])),
                                _class="action-btn",
                                url=URL(f="person",
                                        args=["human_resource"],
                                        vars={"human_resource.id": "[id]"}))]

    if r.interactive:
        output["module_name"] = response.title
        if session.s3.hrm.orgname:
            output["orgname"] = session.s3.hrm.orgname
        response.view = "hrm/index.html"
        query = (table.deleted != True) & \
                (table.status == 1) & org_filter
        # Staff
        ns = db(query & (table.type == 1)).count()
        # Volunteers
        nv = db(query & (table.type == 2)).count()
        output["ns"] = ns
        output["nv"] = nv

        try:
            module_name = deployment_settings.modules[module].name_nice
        except:
            module_name = T("Human Resources Management")
        response.title = module_name

        output["title"] = module_name

    return output

# =============================================================================
# People
# =============================================================================
def human_resource():
    """
        HR Controller
    """

    tablename = "hrm_human_resource"
    table = s3db[tablename]

    # NB Change these & change the list_fields.pop() later
    list_fields = ["id",
                   "person_id",
                   "job_title",
                   "organisation_id",
                   "site_id",
                   "location_id",
                   "type",
                   "status",
                  ]

    # Must specify a group to create HRs
    # Interactive
    group = request.vars.get("group", None)
    if group == None:
        # Imports
        groupCode = request.vars.get("human_resource.type", None)
        if groupCode == "2":
            group = "volunteer"
        elif groupCode == "1":
            group = "staff"
    if group == "volunteer":
        _type = table.type
        _type.default = 2
        response.s3.filter = (_type == 2)
        _type.readable = False
        _type.writable = False
        _location = table.location_id
        _location.writable = True
        _location.readable = True
        _location.label = T("Home Address")
        list_fields.pop(4)
        table.job_title.label = T("Volunteer Role")
        s3.crud_strings[tablename].update(
            title_create = T("Add Volunteer"),
            title_display = T("Volunteer Information"),
            title_list = T("Volunteers"),
            title_search = T("Search Volunteers"),
            subtitle_create = T("Add New Volunteer"),
            subtitle_list = T("Volunteers"),
            label_create_button = T("Add Volunteer"),
            msg_record_created = T("Volunteer added"))
        # Remove Type filter from the Search widget
        human_resource_search = s3mgr.model.get_config(tablename,
                                                       "search_method")
        human_resource_search._S3Search__advanced.pop(1)
        s3mgr.configure(tablename,
                        search_method = human_resource_search)

    elif group == "staff":
        #s3mgr.configure(table._tablename, insertable=False)
        # Default to Staff
        _type = table.type
        _type.default = 1
        response.s3.filter = (_type == 1)
        _type.readable = False
        _type.writable = False
        table.site_id.writable = True
        table.site_id.readable = True
        list_fields.pop(5)
        list_fields.append("end_date")
        s3.crud_strings[tablename].update(
            title_create = T("Add Staff Member"),
            title_list = T("Staff"),
            title_search = T("Search Staff"),
            title_upload = T("Import Staff & Volunteers"),
        )
        if "expiring" in request.get_vars:
            response.s3.filter = response.s3.filter & \
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
                        search_method = human_resource_search)

    s3mgr.configure(tablename,
                    list_fields = list_fields)

    def prep(r):
        if r.interactive:
            # Assume volunteers only between 12-81
            s3db.pr_person.date_of_birth.widget = S3DateWidget(past=972, future=-144)

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
                if group in (1, 2):
                    field = table.type
                    field.readable = False
                    field.writable = False
            elif r.representation == "plain":
                # Don't redirect Map popups
                pass
            elif r.id:
                # Redirect to person controller
                vars = {"human_resource.id": r.id}
                if group:
                    vars.update(group=group)
                redirect(URL(f="person",
                             vars=vars))
        return True
    response.s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component:
                s3_action_buttons(r, deletable=False)
                if "msg" in deployment_settings.modules:
                    # @ToDo: Remove this now that we have it in Events?
                    response.s3.actions.append({
                        "url": URL(f="compose",
                                   vars = {"hrm_id": "[id]"}),
                        "_class": "action-btn",
                        "label": str(T("Send Message"))})
        elif r.representation == "plain":
            # Map Popups
            output = hrm_map_popup(r)
        return output
    response.s3.postp = postp

    output = s3_rest_controller(interactive_report=True)
    return output

# -----------------------------------------------------------------------------
def hrm_map_popup(r):
    """
        Custom output to place inside a Map Popup
        - called from postp of human_resource controller
    """

    output = TABLE()
    # Edit button
    output.append(TR(TD(A(T("Edit"),
                        _target="_blank",
                        _id="edit-btn",
                        _href=URL(args=[r.id, "update"])))))

    # First name, last name
    output.append(TR(TD(B("%s:" % T("Name"))),
                     TD(s3_fullname(r.record.person_id))))

    # Job Title
    if r.record.job_title:
        output.append(TR(TD(B("%s:" % r.table.job_title.label)),
                         TD(r.record.job_title)))

    # Organization (better with just name rather than Represent)
    table = s3db.org_organisation
    query = (table.id == r.record.organisation_id)
    name = db(query).select(table.name,
                            limitby=(0, 1)).first().name
    output.append(TR(TD(B("%s:" % r.table.organisation_id.label)),
                     TD(name)))

    if r.record.location_id:
        table = s3db.gis_location
        query = (table.id == r.record.location_id)
        location = db(query).select(table.path,
                                    table.addr_street,
                                    limitby=(0, 1)).first()
        # City
        # Street address
        if location.addr_street:
            output.append(TR(TD(B("%s:" % table.addr_street.label)),
                             TD(location.addr_street)))
    # Mobile phone number
    ptable = s3db.pr_person
    ctable = s3db.pr_contact
    query = (ptable.id == r.record.person_id) & \
            (ctable.pe_id == ptable.pe_id)
    contacts = db(query).select(ctable.contact_method,
                                ctable.value)
    email = mobile_phone = ""
    for contact in contacts:
        if contact.contact_method == "EMAIL":
            email = contact.value
        elif contact.contact_method == "SMS":
            mobile_phone = contact.value
    if mobile_phone:
        output.append(TR(TD(B("%s:" % msg.CONTACT_OPTS.get("SMS"))),
                         TD(mobile_phone)))
    # Office number
    if r.record.site_id:
        table = s3db.org_office
        query = (table.site_id == r.record.site_id)
        office = db(query).select(table.phone1,
                                  limitby=(0, 1)).first()
        if office and office.phone1:
            output.append(TR(TD(B("%s:" % T("Office Phone"))),
                             TD(office.phone1)))
        else:
            # @ToDo: Support other Facility Types (Hospitals & Shelters)
            pass
    # Email address (as hyperlink)
    if email:
        output.append(TR(TD(B("%s:" % msg.CONTACT_OPTS.get("EMAIL"))),
                         TD(A(email, _href="mailto:%s" % email))))

    return output

# -----------------------------------------------------------------------------
def person():
    """
        Person Controller
        - used for Personal Profile & Imports
        - includes components relevant to HRM

        @ToDo: Volunteers should be redirected to vol/person?
    """

    # Custom Method for Contacts
    s3mgr.model.set_method("pr", resourcename,
                           method="contacts",
                           action=s3db.pr_contacts)

    if deployment_settings.has_module("asset"):
        # Assets as component of people
        s3mgr.model.add_component("asset_asset",
                                  pr_person="assigned_to_id")
        # Edits should always happen via the Asset Log
        # @ToDo: Allow this method too, if we can do so safely
        s3mgr.configure("asset_asset",
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
        if group == "staff":
            table.site_id.writable = True
            table.site_id.readable = True
        else:
            # Volunteer
            table.location_id.writable = True
            table.location_id.readable = True
            table.location_id.label = T("Home Address")
    else:
        table.location_id.readable = True
        table.site_id.readable = True

    if session.s3.hrm.mode is not None:
        s3mgr.configure(tablename,
                        list_fields=["id",
                                     "organisation_id",
                                     "type",
                                     "job_title",
                                     "status",
                                     "location_id",
                                     "site_id"])
    else:
        s3mgr.configure(tablename,
                        list_fields=["id",
                                     "type",
                                     "job_title",
                                     "status",
                                     "location_id",
                                     "site_id"])

    # Configure person table
    # - hide fields
    tablename = "pr_person"
    table = s3db[tablename]
    table.pe_label.readable = False
    table.pe_label.writable = False
    table.missing.readable = False
    table.missing.writable = False
    table.age_group.readable = False
    table.age_group.writable = False
    s3mgr.configure(tablename,
                    deletable=False)

    if group == "staff":
        s3.crud_strings[tablename].update(
            title_upload = T("Import Staff"))
        # No point showing the 'Occupation' field - that's the Job Title in the Staff Record
        table.occupation.readable = False
        table.occupation.writable = False
        # Just have a Home Address
        table = s3db.pr_address
        table.type.default = 1
        table.type.readable = False
        table.type.writable = False
        _crud = s3.crud_strings.pr_address
        _crud.title_create = T("Add Home Address")
        _crud.title_update = T("Edit Home Address")
        s3mgr.model.add_component("pr_address",
                                  pr_pentity=dict(joinby=super_key(s3db.pr_pentity),
                                                  multiple=False))
        # Default type for HR
        table = s3db.hrm_human_resource
        table.type.default = 1
        request.get_vars.update(xsltmode="staff")
    else:
        s3.crud_strings[tablename].update(
            title_upload = T("Import Volunteers"))
        # Default type for HR
        table = db.hrm_human_resource
        table.type.default = 2
        request.get_vars.update(xsltmode="volunteer")

    if session.s3.hrm.mode is not None:
        # Configure for personal mode
        s3db.hrm_human_resource.organisation_id.readable = True
        s3.crud_strings[tablename].update(
            title_display = T("Personal Profile"),
            title_update = T("Personal Profile"))
        # People can view their own HR data, but not edit it
        s3mgr.configure("hrm_human_resource",
                        insertable = False,
                        editable = False,
                        deletable = False)
        s3mgr.configure("hrm_certification",
                        insertable = True,
                        editable = True,
                        deletable = True)
        s3mgr.configure("hrm_credential",
                        insertable = False,
                        editable = False,
                        deletable = False)
        s3mgr.configure("hrm_competency",
                        insertable = True,  # Can add unconfirmed
                        editable = False,
                        deletable = False)
        s3mgr.configure("hrm_training",    # Can add but not provide grade
                        insertable = True,
                        editable = False,
                        deletable = False)
        s3mgr.configure("hrm_experience",
                        insertable = False,
                        editable = False,
                        deletable = False)
        s3mgr.configure("pr_group_membership",
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
    response.s3.importerPrep = lambda: dict(ReplaceOption=T("Remove existing data before import"))

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

        if response.s3.import_replace:
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
                        htable = db.hrm_human_resource
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
                    s3mgr.configure("asset_asset",
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
                redirect(URL(group, args=["search"]))
            if hr_id and r.component_name == "human_resource":
                r.component_id = hr_id
            s3mgr.configure("hrm_human_resource",
                            insertable = False)
            if not r.component_id or r.method in ("create", "update"):
                address_hide(s3db.pr_address)
        return True
    response.s3.prep = prep

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
    response.s3.postp = postp

    # REST Interface
    if session.s3.hrm.orgname and mode is None:
        orgname = session.s3.hrm.orgname
    else:
        orgname = None

    output = s3_rest_controller("pr", resourcename,
                                native=False,
                                rheader=s3db.hrm_rheader,
                                orgname=orgname,
                                template="person",
                                replace_option=T("Remove existing data before import"))
    return output

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
    response.s3.filter = (table.system == False) & \
                         (_group_type == 3)

    # CRUD Strings
    ADD_TEAM = T("Add Team")
    LIST_TEAMS = T("List Teams")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_TEAM,
        title_display = T("Team Details"),
        title_list = LIST_TEAMS,
        title_update = T("Edit Team"),
        title_search = T("Search Teams"),
        subtitle_create = T("Add New Team"),
        subtitle_list = T("Teams"),
        label_list_button = LIST_TEAMS,
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
        subtitle_list = T("Current Team Members"),
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
                    response.s3.actions.append({
                        "url": URL(f="compose",
                                   vars = {"group_id": "[id]"}),
                        "_class": "action-btn",
                        "label": str(T("Send Notification"))})

        return output
    response.s3.postp = postp

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
    response.s3.prep = prep

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
    response.s3.prep = prep

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

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    roles = session.s3.roles or []
    if ADMIN not in roles and \
       EDITOR not in roles:
        ttable = s3db.hrm_training
        hrtable = s3db.hrm_human_resource
        orgtable = s3db.org_organisation
        orgs = session.s3.hrm.orgs
        query = (ttable.person_id == hrtable.person_id) & \
                (hrtable.organisation_id == orgtable.id) & \
                (orgtable.pe_id.belongs(orgs))
        response.s3.filter = query

    output = s3_rest_controller(interactive_report = True)
    return output

# -----------------------------------------------------------------------------
def training_event():
    """ Training Events Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    def prep(r):
        if r.interactive and r.component:
            # Use appropriate CRUD strings
            s3.crud_strings["hrm_training"] = Storage(
                title_create = T("Add Participant"),
                title_display = T("Participant Details"),
                title_list = T("Participants"),
                title_update = T("Edit Participant"),
                title_search = T("Search Participants"),
                title_upload = T("Import Participant Participants"),
                subtitle_create = T("Add Participant"),
                subtitle_list = T("Participants"),
                label_list_button = T("List Participants"),
                label_create_button = T("Add New Participant"),
                label_delete_button = T("Delete Participant"),
                msg_record_created = T("Participant added"),
                msg_record_modified = T("Participant updated"),
                msg_record_deleted = T("Participant deleted"),
                msg_no_match = T("No entries found"),
                msg_list_empty = T("Currently no Participants registered"))

        return True
    response.s3.prep = prep

    output = s3_rest_controller(rheader=s3db.hrm_rheader)
    return output

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

    vars = request.vars

    if "hrm_id" in vars:
        id = vars.hrm_id
        fieldname = "hrm_id"
        table = s3db.pr_person
        htable = s3db.hrm_human_resource
        query = (htable.id == id) & \
                (htable.person_id == table.id)
        title = T("Send a message to this person")
    elif "group_id" in request.vars:
        id = request.vars.group_id
        fieldname = "group_id"
        table = s3db.pr_group
        query = (table.id == id)
        title = T("Send a message to this team")
    else:
        session.error = T("Record not found")
        redirect(URL(f="index"))

    pe = db(query).select(table.pe_id,
                          limitby=(0, 1)).first()
    if not pe:
        session.error = T("Record not found")
        redirect(URL(f="index"))

    pe_id = pe.pe_id

    if "hrm_id" in vars:
        # Get the individual's communications options & preference
        ctable = s3db.pr_contact
        contact = db(ctable.pe_id == pe_id).select(ctable.contact_method,
                                                   orderby="priority",
                                                   limitby=(0, 1)).first()
        if contact:
            s3db.msg_outbox.pr_message_method.default = contact.contact_method
        else:
            session.error = T("No contact method found")
            redirect(URL(f="index"))

    # URL to redirect to after message sent
    url = URL(c=module,
              f="compose",
              vars={fieldname: id})

    # Create the form
    output = msg.compose(recipient = pe_id,
                         url = url)

    output["title"] = title
    response.view = "msg/compose.html"
    return output

# END =========================================================================
