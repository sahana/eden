# -*- coding: utf-8 -*-

"""
    Volunteer Management
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
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
        redirect(URL(f="volunteer", args="search"))

# =============================================================================
# People
# =============================================================================
def human_resource():
    """
        HR Controller
        - combined (unused, except for Imports)
    """

    table = s3db.hrm_human_resource
    _type = table.type
    s3.filter = (_type == 2)

    # Custom method for Service Record
    s3db.set_method("hrm", "human_resource",
                    method="form",
                    action=s3db.hrm_service_record
                   )

    def prep(r):
        if r.method == "form":
            return True
        if r.interactive:
            if r.method == "create" and not r.component:
                redirect(URL(f="volunteer",
                             args=args,
                             vars=vars))
            elif r.method == "delete":
                # Don't redirect
                pass
            elif r.id:
                # Redirect to person controller
                vars = {
                        "human_resource.id" : r.id,
                        "group" : "volunteer"
                        }
                redirect(URL(f="person",
                             vars=vars))
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component:
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

    output = s3_rest_controller("hrm", "human_resource")
    return output

# -----------------------------------------------------------------------------
def volunteer():
    """
        Volunteer Controller
    """

    tablename = "hrm_human_resource"
    table = s3db[tablename]

    _type = table.type
    s3.filter = (_type == 2)
    _location = table.location_id
    _location.label = T("Home Address")
    list_fields = ["id",
                   "person_id",
                   "job_title_id",
                   "organisation_id",
                   (settings.get_ui_label_mobile_phone(), "phone"),
                   "location_id",
                   (T("Trainings"), "course"),
                   (T("Certificates"), "certificate"),
                   (T("Email"), "email"),
                  ]
    get_config = s3db.get_config
    report_options = get_config(tablename,
                                "report_options")
    # Remove inappropriate filters from the Search widget
    human_resource_search = get_config(tablename,
                                       "search_method")
    # Remove Facility
    human_resource_search.advanced.pop(8)
    if settings.get_hrm_vol_experience() == "programme":
        enable_active_field = settings.set_org_dependent_field("vol_volunteer", "active",
                                                               enable_field = False)
        # Add Programme Virtual Fields
        table.virtualfields.append(s3db.hrm_programme_virtual_fields())
        # Add VF to List Fields
        if enable_active_field:
            list_fields.insert(4, (T("Active?"), "active"))
        list_fields.insert(6, (T("Programme"), "programme"))
        # Add VF to Report Options
        report_fields = report_options.rows
        report_fields.append((T("Programme"), "programme"))
        if enable_active_field:
            report_fields.append((T("Active?"), "active"))
        report_options.rows = report_fields
        report_options.cols = report_fields
        report_options.facts = report_fields
        # Add VF to the Search Filters
        # Remove deprecated Active/Obsolete
        human_resource_search.advanced.pop(1)
        table.status.readable = False
        table.status.writable = False
        if enable_active_field:
            widget = s3base.S3SearchOptionsWidget(
                                name="human_resource_search_active",
                                label=T("Active?"),
                                field="active",
                                cols = 2,
                                options = {
                                        T("Yes"): T("Yes"),
                                        T("No"): T("No")
                                    }
                              ),
            search_widget = ("human_resource_search_active", widget[0])
            human_resource_search.advanced.insert(1, search_widget)

        def hrm_programme_opts():
            """
                Provide the options for the HRM programme search filter
            """
            ptable = s3db.hrm_programme
            root_org = auth.root_org()
            if root_org:
                query = (ptable.deleted == False) & \
                        ((ptable.organisation_id == root_org) | \
                         (ptable.organisation_id == None))
            else:
                query = (ptable.deleted == False) & \
                        (ptable.organisation_id == None)
            opts = db(query).select(ptable.id,
                                    ptable.name)
            _dict = {}
            for opt in opts:
                _dict[opt.id] = opt.name
            return _dict

        widget = s3base.S3SearchOptionsWidget(
                            name="human_resource_search_programme",
                            label=T("Programme"),
                            field="programme",
                            cols = 2,
                            options = hrm_programme_opts
                          ),
        search_widget = ("human_resource_search_programme", widget[0])
        human_resource_search.advanced.insert(3, search_widget)
    else:
        list_fields.append("status")
    s3.crud_strings[tablename] = s3.crud_strings["hrm_volunteer"]
    s3db.configure(tablename,
                    list_fields = list_fields,
                    report_options = report_options,
                    search_method = human_resource_search)

    def prep(r):
        if r.interactive:
            table = r.table
            table.person_id.widget = S3AddPersonWidget(controller="vol")
            if not r.component and \
               not r.id and \
               r.method in [None, "create"]:
                # Don't redirect
                # Assume staff only between 12-81
                s3db.pr_person.date_of_birth.widget = S3DateWidget(past=972, future=-144)

                _type.default = 2
                _location.writable = True
                _location.readable = True
                table.site_id.writable = False
                table.site_id.readable = False
                table.code.writable = False
                table.code.readable = False
                table.department_id.writable = False
                table.department_id.readable = False
                table.essential.writable = False
                table.essential.readable = False
                table.site_contact.writable = False
                table.site_contact.readable = False
                table.status.writable = False
                table.status.readable = False

                person_details_table = s3db.pr_person_details
                person_details_table.occupation.label = T("Normal Job")

                # Organisation Dependent Fields
                set_org_dependent_field = settings.set_org_dependent_field
                set_org_dependent_field("pr_person_details", "father_name")
                set_org_dependent_field("pr_person_details", "mother_name")
                set_org_dependent_field("pr_person_details", "affiliations")
                set_org_dependent_field("pr_person_details", "company")
                set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_type_id")
                set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_id")
                set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_position_id")

            elif r.method == "delete":
                # Don't redirect
                pass
            elif r.id:
                # Redirect to person controller
                redirect(URL(f="person",
                             vars={"human_resource.id": r.id,
                                   "group": "volunteer"
                                   }))
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component:
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('hrm_human_resource_start_date','hrm_human_resource_end_date')''')

                s3_action_buttons(r, deletable=settings.get_hrm_deletable())
                if "msg" in settings.modules:
                    # @ToDo: Remove this now that we have it in Events?
                    s3.actions.append({
                            "url": URL(f="compose",
                                       vars = {"hrm_id": "[id]"}),
                            "_class": "action-btn",
                            "label": str(T("Send Message"))
                        })
                if settings.get_hrm_vol_experience() == "programme" and \
                   r.method not in ["search", "report", "import"] and \
                   "form" in output:
                    # Insert field to set the Programme
                    sep = ": "
                    table = s3db.hrm_programme_hours
                    field = table.programme_id
                    default = field.default
                    widget = field.widget or SQLFORM.widgets.options.widget(field, default)
                    field_id = "%s_%s" % (table._tablename, field.name)
                    label = field.label
                    label = LABEL(label, label and sep, _for=field_id,
                                  _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                    row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                    programme = s3.crud.formstyle(row_id, label, widget, field.comment)
                    try:
                        output["form"][0].insert(4, programme[1])
                    except:
                        # A non-standard formstyle with just a single row
                        pass
                    try:
                        output["form"][0].insert(4, programme[0])
                    except:
                        pass
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

    group = request.get_vars.get("group", "volunteer")
    hr_id = request.get_vars.get("human_resource.id", None)
    if not str(hr_id).isdigit():
        hr_id = None

    # Configure human resource table
    table = s3db.hrm_human_resource
    table.type.default = 2
    request.get_vars.update(xsltmode="volunteer")
    if hr_id:
        hr = table[hr_id]
        if hr:
            group = hr.type == 2 and "volunteer" or "staff"
            # Also inform the back-end of this finding
            request.get_vars["group"] = group

    # Configure person table
    tablename = "pr_person"
    table = s3db[tablename]
    if settings.get_hrm_vol_experience() == "programme":
        table.virtualfields.append(s3db.hrm_programme_person_virtual_fields())
    configure(tablename,
              deletable=False)

    mode = session.s3.hrm.mode
    if mode is not None:
        # Configure for personal mode
        s3db.hrm_human_resource.organisation_id.readable = True
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
                title_display = T("Volunteer Details"),
                title_update = T("Volunteer Details"),
                title_upload = T("Import Volunteers"),
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
                        resource = s3base.S3Resource("hrm_human_resource", filter=query)
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
                # Assume volunteers only between 12-81
                table.date_of_birth.widget = S3DateWidget(past=972, future=-144)
                table.pe_label.readable = False
                table.pe_label.writable = False
                table.missing.readable = False
                table.missing.writable = False
                table.age_group.readable = False
                table.age_group.writable = False

                person_details_table = s3db.pr_person_details
                person_details_table.occupation.label = T("Normal Job")

                # Organisation Dependent Fields
                set_org_dependent_field = settings.set_org_dependent_field
                set_org_dependent_field("pr_person_details", "father_name")
                set_org_dependent_field("pr_person_details", "mother_name")
                set_org_dependent_field("pr_person_details", "affiliations")
                set_org_dependent_field("pr_person_details", "company")

            else:
                if r.component_name == "human_resource":
                    table = r.component.table
                    table.code.writable = False
                    table.code.readable = False
                    table.department_id.writable = False
                    table.department_id.readable = False
                    table.essential.writable = False
                    table.essential.readable = False
                    #table.location_id.readable = True
                    #table.location_id.writable = True
                    table.site_id.writable = False
                    table.site_id.readable = False
                    table.site_contact.writable = False
                    table.site_contact.readable = False
                    org = session.s3.hrm.org
                    if org is not None:
                        field = table.organisation_id
                        field.default = org
                        field.readable = False
                        field.writable = False

                    # Organisation Dependent Fields
                    set_org_dependent_field = settings.set_org_dependent_field
                    set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_type_id")
                    set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_id")
                    set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_position_id")

                elif r.component_name == "hours":
                    filter = (r.component.table.hours != None)
                    r.resource.add_component_filter("hours", filter)
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
                    redirect(URL(r=r, f="volunteer"))
            if resource.count() == 1:
                resource.load()
                r.record = resource.records().first()
                if r.record:
                    r.id = r.record.id
            if not r.record:
                session.error = T("Record not found")
                redirect(URL(f="volunteer",
                             args=["search"]))
            if hr_id and r.component_name == "human_resource":
                r.component_id = hr_id
            configure("hrm_human_resource",
                      insertable = False)
        return True
    s3.prep = prep

    # CRUD post-process
    def postp(r, output):
        if r.interactive and r.component:
            if r.component_name == "human_resource":
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('hrm_human_resource_start_date','hrm_human_resource_end_date')''')
                if settings.get_hrm_vol_experience() == "programme" and \
                   r.method not in ["search", "report", "import"] and \
                   "form" in output:
                    # Insert field to set the Programme
                    sep = ": "
                    table = s3db.hrm_programme_hours
                    field = table.programme_id
                    if r.id:
                        query = (table.person_id == r.id)
                        default = db(query).select(table.programme_id,
                                                   orderby=table.date).last()
                        if default:
                            default = default.programme_id
                    else:
                        default = field.default
                    widget = field.widget or SQLFORM.widgets.options.widget(field, default)
                    field_id = "%s_%s" % (table._tablename, field.name)
                    label = field.label
                    label = LABEL(label, label and sep, _for=field_id,
                                  _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                    row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                    programme = s3.crud.formstyle(row_id, label, widget, field.comment)
                    try:
                        output["form"][0].insert(2, programme[1])
                    except:
                        # A non-standard formstyle with just a single row
                        pass
                    try:
                        output["form"][0].insert(2, programme[0])
                    except:
                        pass

            elif r.component_name == "experience":
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
                                csv_stylesheet=("hrm", "person.xsl"),
                                csv_extra_fields=[
                                    dict(label="Type",
                                         field=s3db.hrm_human_resource.type)
                                                  ]
                                )
    return output

# -----------------------------------------------------------------------------
def person_search():
    """
        Person REST controller
        - limited to just search.json for use in Autocompletes
        - allows differential access permissions
    """

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

    configure = s3db.configure
    configure(tablename, main="name", extra="description",
              # Redirect to member list when a new group has been created
              create_next = URL(f="group",
                                args=["[id]", "group_membership"]))
    configure("pr_group_membership",
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
                if "msg" in settings.modules:
                    s3.actions.append({
                        "url": URL(f = "compose",
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

    output = s3_rest_controller("hrm", resourcename)
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

    output = s3_rest_controller("hrm", resourcename)
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

    output = s3_rest_controller("hrm", resourcename)
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

    output = s3_rest_controller("hrm", resourcename)
    return output

# -----------------------------------------------------------------------------
def skill_type():
    """ Skill Types Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    output = s3_rest_controller("hrm", resourcename)
    return output

# -----------------------------------------------------------------------------
def competency_rating():
    """ Competency Rating for Skill Types Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    output = s3_rest_controller("hrm", resourcename)
    return output

# -----------------------------------------------------------------------------
def skill_provision():
    """ Skill Provisions Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    output = s3_rest_controller("hrm", resourcename)
    return output

# -----------------------------------------------------------------------------
def course():
    """ Courses Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

        s3.filter = auth.filter_by_root_org(s3db.hrm_course)

    output = s3_rest_controller("hrm", resourcename,
                                rheader=s3db.hrm_rheader)
    return output

# -----------------------------------------------------------------------------
def course_certificate():
    """ Courses to Certificates Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    output = s3_rest_controller("hrm", resourcename)
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

    output = s3_rest_controller("hrm", resourcename,
                                rheader=s3db.hrm_rheader)
    return output

# -----------------------------------------------------------------------------
def certificate_skill():
    """ Certificates to Skills Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    output = s3_rest_controller("hrm", resourcename)
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
def programme():
    """ Volunteer Programmes controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    s3.filter = auth.filter_by_root_org(s3db.hrm_programme)

    output = s3_rest_controller("hrm", resourcename,
                                rheader=s3db.hrm_rheader)
    return output

# -----------------------------------------------------------------------------
def programme_hours():
    """
        Volunteer Programme Hours controller
        - just meant for Imports
    """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    output = s3_rest_controller("hrm", resourcename)
    return output
# =============================================================================
def cluster_type():
    """ Volunteer Clusters controller """

    return s3_rest_controller()

# =============================================================================
def volunteer_cluster():
    """ ONLY FOR RETURNING options to the S3AddResourceLink PopUp """

    return s3_rest_controller()

# =============================================================================
def cluster():
    """ Volunteer Clusters controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def cluster_position():
    """ Volunteer Group Positions controller """

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
