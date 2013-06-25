# -*- coding: utf-8 -*-

"""
    Project Tracking & Management
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

mode_task = settings.get_project_mode_task()

# =============================================================================
def index():
    """ Module's Home Page """

    if mode_task:
        # Bypass home page & go direct to browsing Tasks for a Project
        redirect(URL(f="project", vars={"tasks":1}))
    elif settings.get_project_mode_drr():
        # Bypass home page & go direct to searching for Projects
        redirect(URL(f="project", args="search"))
    else:
        # Bypass home page & go direct to list of Projects
        # - no good search options available
        redirect(URL(f="project"))

    #module_name = settings.modules[module].name_nice
    #response.title = module_name
    #return dict(module_name=module_name)

# =============================================================================
def create():
    """ Redirect to project/create """
    redirect(URL(f="project", args="create"))

# -----------------------------------------------------------------------------
def project():
    """ RESTful CRUD controller """

    if "tasks" in request.get_vars:
        # Return simplified controller to pick a Project for which to list the Open Tasks
        table = s3db.project_project
        s3.crud_strings["project_project"].title_list = T("Open Tasks for Project")
        #s3.crud_strings["project_project"].sub_title_list = T("Select Project")
        s3mgr.LABEL.READ = "Select"
        s3mgr.LABEL.UPDATE = "Select"
        s3db.configure("project_project",
                       deletable=False,
                       listadd=False)
        # Post-process
        def postp(r, output):
            if r.interactive:
                if not r.component:
                    # @ToDo: Fix the filtering in project_task_controller()
                    read_url = URL(f="task", #args="search",
                                   vars={"project":"[id]"})
                    update_url = URL(f="task", #args="search",
                                     vars={"project":"[id]"})
                    s3mgr.crud.action_buttons(r, deletable=False,
                                              read_url=read_url,
                                              update_url=update_url)
            return output
        s3.postp = postp
        return s3_rest_controller()

    htable = s3db.hrm_human_resource
    htable.person_id.comment = DIV(_class="tooltip",
                                   _title="%s|%s" % (T("Person"),
                                                     T("Select the person assigned to this role for this project.")))

    # Pre-process
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)
        
        if r.component and r.component.name == "project_task":
            list_fields = s3db.get_config("project_task",
                                          "list_fields")
            list_fields.insert(3, (T("Activity"), "activity.name"))
        
        if r.interactive:
            if not r.component or r.component_name == "activity":
                # Filter Themes/Activity Types based on Sector
                if r.record:
                    table = s3db.project_sector_project
                    query = (table.project_id == r.id) & \
                            (table.deleted == False)
                    rows = db(query).select(table.sector_id)
                    sector_ids = [row.sector_id for row in rows]
                else:
                    sector_ids = []
                set_theme_requires(sector_ids)

            if not r.component:
                set_theme_requires(sector_ids)

                if r.method in ("create", "update"):
                    # Context from a Profile page?"
                    location_id = request.get_vars.get("(location)", None)
                    if location_id:
                        field = s3db.project_location.location_id
                        field.default = location_id
                        field.readable = field.writable = False
                    organisation_id = request.get_vars.get("(organisation)", None)
                    if organisation_id:
                        field = r.table.organisation_id
                        field.default = organisation_id
                        field.readable = field.writable = False

                if r.id:
                    r.table.human_resource_id.represent = lambda id: \
                        s3db.hrm_human_resource_represent(id, show_link=True)
                elif r.function == "index":
                    r.method = "search"
                    # If just a few Projects, then a List is sufficient
                    #r.method = "list"
                elif request.get_vars.get("project.status_id", None):
                    stable = s3db.project_status
                    status = request.get_vars.get("project.status_id")
                    row = db(stable.name == status).select(stable.id,
                                                           limitby=(0, 1)).first()
                    if row:
                        r.table.status_id.default = row.id
                        r.table.status_id.writable = False
            else:
                if r.component_name == "organisation":
                    if r.method != "update":
                        # @ToDo: Move this to template?
                        if settings.get_template() == "DRRPP":
                            project_organisation_roles = settings.get_project_organisation_roles()
                            roles_subset = {}
                            exclude_roles = [9] # Partner NS should only come via sync from RMS
                            lead_role = 1
                            otable = s3db.project_organisation
                            query = (otable.deleted != True) & \
                                    (otable.role == lead_role) & \
                                    (otable.project_id == r.id)
                            row = db(query).select(otable.id,
                                                   limitby=(0, 1)).first()
                            if row:
                                # We already have a Lead Org, so ensure we don't try to add a 2nd
                                exclude_roles.append(lead_role)
                            for role in project_organisation_roles:
                                if role not in exclude_roles:
                                    roles_subset[role] = project_organisation_roles[role]
                            otable.role.requires = \
                                IS_NULL_OR(IS_IN_SET(roles_subset))
                        else:
                            lead_role = 1
                            otable = s3db.project_organisation
                            query = (otable.deleted != True) & \
                                    (otable.role == lead_role) & \
                                    (otable.project_id == r.id)
                            row = db(query).select(otable.id,
                                                   limitby=(0, 1)).first()
                            if row:
                                # We already have a Lead Org, so ensure we don't try to add a 2nd
                                project_organisation_roles = settings.get_project_organisation_roles()
                                roles_subset = {}
                                for role in project_organisation_roles:
                                    if role != lead_role:
                                        roles_subset[role] = project_organisation_roles[role]
                                otable.role.requires = \
                                    IS_NULL_OR(IS_IN_SET(roles_subset))

                elif r.component_name == "activity":
                    # Filter Activity Type based on Sector
                    set_activity_type_requires("project_activity_activity_type", sector_ids)

                elif r.component_name == "task":
                    table = r.component.table
                    if not auth.s3_has_role("STAFF"):
                        # Hide fields to avoid confusion (both of inputters & recipients)
                        field = table.source
                        field.readable = field.writable = False
                        field = table.pe_id
                        field.readable = field.writable = False
                        field = table.date_due
                        field.readable = field.writable = False
                        field = table.time_estimated
                        field.readable = field.writable = False
                        field = table.time_actual
                        field.readable = field.writable = False
                        field = table.status
                        field.readable = field.writable = False
                    if "open" in request.get_vars:
                        # Show only the Open Tasks for this Project
                        statuses = s3.project_task_active_statuses
                        filter = (table.status.belongs(statuses))
                        r.resource.add_component_filter("task", filter)

                elif r.component_name == "beneficiary":
                    db.project_beneficiary.project_location_id.requires = IS_NULL_OR(
                        IS_ONE_OF(db, "project_location.id",
                                  s3db.project_location_represent,
                                  sort=True,
                                  filterby="project_id",
                                  filter_opts=[r.id])
                                  )

                elif r.component_name == "human_resource":
                    # We can pass the human resource type filter in the URL
                    group = r.vars.get("group", None)

                    table = db.project_human_resource
                    db.hrm_human_resource.person_id.represent = s3db.pr_PersonRepresent(show_link=True)
                    # These values are defined in hrm_type_opts
                    if group:
                        crud_strings = s3.crud_strings
                        if group == "staff":
                            group = 1
                            table.human_resource_id.label = T("Staff")
                            crud_strings["project_human_resource"] = crud_strings["hrm_staff"]
                            crud_strings["project_human_resource"].update(
                                subtitle_create = T("Add Staff Member to Project")
                                )

                        elif group == "volunteer":
                            group = 2
                            table.human_resource_id.label = T("Volunteer")
                            crud_strings["project_human_resource"] = crud_strings["hrm_volunteer"]
                            crud_strings["project_human_resource"].update(
                                subtitle_create = T("Add Volunteer to Project")
                                )

                        # Use the group to filter the component list
                        filter_by_type = (db.hrm_human_resource.type == group)
                        r.resource.add_component_filter("human_resource", filter_by_type)

                        # Use the group to filter the form widget for adding a new record
                        table.human_resource_id.requires = IS_ONE_OF(
                            db,
                            "hrm_human_resource.id",
                            s3db.hrm_human_resource_represent,
                            filterby="type",
                            filter_opts=(group,),
                            orderby="hrm_human_resource.person_id",
                            sort=True
                        )

                elif r.component_name == "document":
                    doc_table = s3db.doc_document
                    doc_table.organisation_id.readable = doc_table.organisation_id.writable = False
                    doc_table.person_id.readable = doc_table.person_id.writable = False
                    doc_table.location_id.readable = doc_table.location_id.writable = False

        elif r.component_name == "human_resource":
            # We need to also filter PDF/XLS/RSS/XML exports
            # Use the group to filter the component list
            group = r.vars.get("group", None)
            if group:
                if group == "staff":
                    group = 1
                elif group == "volunteer":
                    group = 2
                filter_by_type = (db.hrm_human_resource.type == group)
                r.resource.add_component_filter("human_resource", filter_by_type)

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            if not r.component:
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('project_project_start_date','project_project_end_date')''')
                if mode_task:
                    read_url = URL(args=["[id]", "task"])
                    update_url = URL(args=["[id]", "task"])
                    s3mgr.crud.action_buttons(r,
                                              read_url=read_url,
                                              update_url=update_url)
            elif r.component_name == "beneficiary":
                    # Set the minimum end_date to the same as the start_date
                    s3.jquery_ready.append(
'''S3.start_end_date('project_beneficiary_date','project_beneficiary_end_date')''')
            elif r.component_name == "task" and "form" in output and \
                 not r.method in ("search", "report"):
                # Insert fields to control the Activity & Milestone
                output = s3db.project_task_form_inject(r, output, project=False)
        return output
    s3.postp = postp

    rheader = s3db.project_rheader
    output = s3_rest_controller(module, "project", # Need to specify as sometimes we come via index()
                                rheader=rheader,
                                csv_template="project")
    return output

# -----------------------------------------------------------------------------
def set_theme_requires(sector_ids):
    """
        Filters the theme_id based on the sector_id
    """

    ttable = s3db.project_theme
    tstable = s3db.project_theme_sector

    # All themes linked to the project's sectors or to no sectors 
    rows = db().select(ttable.id,
                       tstable.sector_id,
                       left=tstable.on(ttable.id == tstable.theme_id))
    sector_ids = sector_ids or []
    theme_ids = [row.project_theme.id for row in rows 
                 if not row.project_theme_sector.sector_id or 
                    row.project_theme_sector.sector_id in sector_ids]
    table = s3db.project_theme_project
    table.theme_id.requires = IS_NULL_OR(
                                IS_ONE_OF(db, "project_theme.id",
                                          s3base.S3Represent(lookup="project_theme"),
                                          filterby="id",
                                          filter_opts=theme_ids,
                                          sort=True,
                                          )
                                )

# -----------------------------------------------------------------------------
def set_activity_type_requires(tablename, sector_ids):
    """
        Filters the activity_type_id based on the sector_id
    """

    attable = s3db.project_activity_type
    if sector_ids:
        atstable = s3db.project_activity_type_sector

        # All activity_types linked to the projects sectors or to no sectors 
        rows = db().select(attable.id,
                           atstable.sector_id,
                           left=atstable.on(attable.id == atstable.activity_type_id))
        activity_type_ids = [row.project_activity_type.id for row in rows 
                     if not row.project_activity_type_sector.sector_id or 
                        row.project_activity_type_sector.sector_id in sector_ids]
    else:
        activity_type_ids = []
    s3db[tablename].activity_type_id.requires = IS_NULL_OR(
                                    IS_ONE_OF(db, "project_activity_type.id",
                                              s3base.S3Represent(lookup="project_activity_type"),
                                              filterby="id",
                                              filter_opts=activity_type_ids,
                                              sort=True,
                                              )
                                    )

# -----------------------------------------------------------------------------
def project_theme_id_widget():
    """
        Used by the project controller to return dynamically generated 
        theme_id widget based on sector_id
        - deprecated?
    """

    table = s3db.project_theme_project
    sector_ids = [int(id) for id in request.vars.sector_ids.split(",") if id]
    if "value" in request.vars:
        value = [int(id) for id in request.vars.value.split(",") if id]
    else:
        value = []
    
    set_theme_requires(sector_ids)
    widget = table.theme_id.widget(table.theme_id,
                                   value)
    return widget

# =============================================================================
def status():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def theme():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def theme_project():
    """
        RESTful CRUD controller
        - not normally exposed to users via a menu
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def theme_sector():
    """ RESTful CRUD controller for options.s3json lookups """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def theme_sector_widget():
    """ Render a Widget with Theme options filtered by Sector """

    try:
        values = request.get_vars.sector_ids.split(",")
        values = [int(v) for v in values]
    except:
        values = []

    widget = s3base.s3forms.S3SQLInlineComponentCheckbox(
        "theme",
        label = T("Themes"),
        field = "theme_id",
        cols = 4,
        # Filter Theme by Sector
        filter = {"linktable": "project_theme_sector",
                  "lkey": "theme_id",
                  "rkey": "sector_id",
                  "values": values
                  }
        )

    resource = s3db.resource("project_project")
    #(_instance , _nothing, _field) = widget.resolve(resource)
    widget.resolve(resource)
    value = widget.extract(resource, record_id=None)

    output = widget(s3db.project_theme_project.theme_id, value)

    return output

# -----------------------------------------------------------------------------
def hazard():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def framework():
    """ RESTful CRUD controller """

    return s3_rest_controller(dtargs={"dt_text_maximum_len": 160})

# =============================================================================
def organisation():
    """ RESTful CRUD controller """

    if settings.get_project_multiple_organisations():
        # e.g. IFRC
        s3db.configure("project_organisation",
                       insertable=False,
                       editable=False,
                       deletable=False)

        #list_btn = A(T("Funding Report"),
        #             _href=URL(c="project", f="organisation",
        #                      args="report", vars=request.get_vars),
        #             _class="action-btn")

        return s3_rest_controller(#list_btn=list_btn,
                                  )

    else:
        # e.g. DRRPP
        tabs = [(T("Basic Details"), None),
                (T("Projects"), "project"),
                (T("Contacts"), "human_resource"),
                ]
        rheader = lambda r: s3db.org_rheader(r, tabs)
        return s3_rest_controller("org", resourcename,
                                  rheader=rheader)

# =============================================================================
def beneficiary_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def beneficiary():
    """ RESTful CRUD controller """

    tablename = "project_beneficiary"

    s3db.configure("project_beneficiary",
                   insertable=False,
                   editable=False,
                   deletable=False)

    list_btn = A(T("Beneficiary Report"),
                 _href=URL(c="project", f="beneficiary",
                           args="report", vars=request.get_vars),
                 _class="action-btn")

    return s3_rest_controller()

# =============================================================================
def activity_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def activity_type_sector():
    """ RESTful CRUD controller for options.s3json lookups """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def activity():
    """ RESTful CRUD controller """

    table = s3db.project_activity

    if "project_id" in request.get_vars:
        field = table.project_id
        field.default = request.get_vars.project_id
        field.writable = False
        field.comment = None

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component is not None:
                if r.component_name == "document":
                    doc_table = s3db.doc_document
                    doc_table.organisation_id.readable = False
                    doc_table.person_id.readable = False
                    doc_table.location_id.readable = False
                    doc_table.organisation_id.writable = False
                    doc_table.person_id.writable = False
                    doc_table.location_id.writable = False

        return True
    s3.prep = prep

    # Pre-process
    def postp(r, output):
        if r.representation == "plain":
            def represent(record, field):
                if field.represent:
                    return field.represent(record[field])
                else:
                    return record[field]
            # Add VirtualFields to Map Popup
            # Can't inject into SQLFORM, so need to simply replace
            item = TABLE()
            table.id.readable = False
            table.location_id.readable = False
            fields = [table[f] for f in table.fields if table[f].readable]
            record = r.record
            for field in fields:
                item.append(TR(TD(field.label), TD(represent(record, field))))
            hierarchy = gis.get_location_hierarchy()
            item.append(TR(TD(hierarchy["L4"]), TD(record["name"])))
            for field in ["L3", "L2", "L1"]:
                item.append(TR(TD(hierarchy[field]), TD(record[field])))
            output["item"] = item
        return output
    s3.postp = postp

    return s3_rest_controller(rheader=s3db.project_rheader,
                              csv_template="activity")

# -----------------------------------------------------------------------------
def location():
    """ RESTful CRUD controller """

    table = s3db.project_location

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.record:
                table = s3db.project_sector_project
                query = (table.project_id == r.record.project_id) & \
                        (table.deleted == False)
                rows = db(query).select(table.sector_id)
                sector_ids = [row.sector_id for row in rows]
            else:
                sector_ids = []
            set_activity_type_requires("project_activity_type_location", sector_ids)

            if r.component_name == "document":
                table = db.doc_document
                table.organisation_id.readable = table.organisation_id.writable = False
                table.person_id.readable = table.person_id.writable = False
                table.location_id.readable = table.location_id.writable = False

        return True
    s3.prep = prep

    # Pre-process
    def postp(r, output):
        if r.representation == "plain":
            # Replace the Map Popup contents with custom content
            item = TABLE()
            def represent(record, field):
                if field.represent:
                    return field.represent(record[field])
                else:
                    return record[field]

            if settings.get_project_community():
                # The Community is the primary resource
                record = r.record
                table.id.readable = False
                table.location_id.readable = False
                fields = [table[f] for f in table.fields if table[f].readable]
                for field in fields:
                    data = record[field]
                    if data:
                        represent = field.represent
                        if represent:
                            item.append(TR(TD(field.label),
                                           TD(represent(data))))
                        else:
                            item.append(TR(TD(field.label), TD(data)))
                hierarchy = gis.get_location_hierarchy()
                gtable = s3db.gis_location
                location = db(gtable.id == record.location_id).select(gtable.L1,
                                                                      gtable.L2,
                                                                      gtable.L3,
                                                                      gtable.L4,
                                                                      ).first()
                if location:
                    for field in ["L4", "L3", "L2", "L1"]:
                        if field in hierarchy and location[field]:
                            item.append(TR(TD(hierarchy[field]),
                                           TD(location[field])))
                output["item"] = item
            else:
                # The Project is the primary resource
                project_id = r.record.project_id
                ptable = s3db.project_project
                query = (ptable.id == project_id)
                project = db(query).select(limitby=(0, 1)).first()
                ptable.id.readable = False
                fields = [ptable[f] for f in ptable.fields if ptable[f].readable]
                for field in fields:
                    data = project[field]
                    if data:
                        represent = field.represent
                        if represent:
                            item.append(TR(TD(field.label),
                                           TD(represent(data))))
                        else:
                            item.append(TR(TD(field.label), TD(data)))
                title = s3.crud_strings["project_project"].title_display
                # Assume authorised to see details
                popup_url = URL(f="project", args=[project_id])
                details_btn = A(T("Show Details"), _href=popup_url,
                                _id="details-btn", _target="_blank")
                output = dict(item = item,
                              title = title,
                              details_btn = details_btn,
                              )
        return output
    s3.postp = postp

    if "map" in request.args:
        # S3Map has migrated
        hide_filter = False
    else:
        # Not yet ready otherwise
        hide_filter = True

    return s3_rest_controller(interactive_report=True,
                              rheader=s3db.project_rheader,
                              hide_filter=hide_filter,
                              csv_template="location",
                              )

# -----------------------------------------------------------------------------
def demographic():
    """ RESTful CRUD controller """

    return s3_rest_controller("stats", "demographic")

# -----------------------------------------------------------------------------
def demographic_data():
    """ RESTful CRUD controller """

    return s3db.stats_demographic_data_controller()

# -----------------------------------------------------------------------------
def location_contact():
    """ RESTful CRUD controller for Community Contacts """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def report():
    """
        RESTful CRUD controller

        @ToDo: Why is this needed? To have no rheader?
    """

    return s3_rest_controller(module, "activity")

# -----------------------------------------------------------------------------
def partners():
    """
        RESTful CRUD controller for Organisations filtered by Type
    """

    # @ToDo: This could need to be a deployment setting
    request.get_vars["organisation.organisation_type_id$name"] = \
        "Academic,Bilateral,Government,Intergovernmental,NGO,UN agency"

    return s3db.org_organisation_controller()

# =============================================================================
def task():
    """ RESTful CRUD controller """

    return s3db.project_task_controller()

# =============================================================================
def task_project():
    """ RESTful CRUD controller for options.s3json lookups """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        return True
    s3.prep = prep

    return s3_rest_controller()

# =============================================================================
def task_activity():
    """ RESTful CRUD controller for options.s3json lookups """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        return True
    s3.prep = prep

    return s3_rest_controller()

# =============================================================================
def task_milestone():
    """ RESTful CRUD controller for options.s3json lookups """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        return True
    s3.prep = prep

    return s3_rest_controller()

# =============================================================================
def milestone():
    """ RESTful CRUD controller """

    if "project_id" in request.get_vars:
        field = s3db.project_milestone.project_id
        field.default = request.get_vars.project_id
        field.writable = False
        field.comment = None

    return s3_rest_controller()

# =============================================================================
def time():
    """ RESTful CRUD controller """

    # Load model to get normal CRUD strings
    table = s3db.project_time
    vars = request.get_vars
    if "mine" in vars:
        # Display this user's Logged Hours in reverse-order
        s3.crud_strings["project_time"].title_list = T("My Logged Hours")
        person_id = auth.s3_logged_in_person()
        if person_id:
            # @ToDo: Use URL filter instead, but the Search page will have 
            # to populate it's widgets based on the URL filter  
            s3.filter = (table.person_id == person_id)
            # Log time with just this user's open tasks visible
            ttable = db.project_task
            query = (ttable.pe_id == auth.user.pe_id) & \
                    (ttable.deleted == False) & \
                    (ttable.status.belongs(s3db.project_task_active_statuses))
            dbset = db(query)
            table.task_id.requires = IS_ONE_OF(dbset, "project_task.id",
                                               s3db.project_task_represent_w_project
                                               )
        list_fields = ["id",
                       "date",
                       "hours",
                       (T("Project"), "task_id$task_project.project_id"),
                       (T("Activity"), "task_id$task_activity.activity_id"),
                       "task_id",
                       "comments",
                       ]
        if settings.get_project_milestones():
            # Use the field in this format to get the custom represent
            list_fields.insert(5, (T("Milestone"), "task_id$task_milestone.milestone_id"))

        s3db.configure("project_time",
                       orderby="project_time.date desc",
                       list_fields=list_fields)

    elif "week" in vars:
        # Filter to the specified number of weeks
        weeks = int(vars.get("week", 1))
        now = request.utcnow
        week = datetime.timedelta(days=7)
        delta = week * weeks
        s3.filter = (table.date > (now - delta))

    elif "month" in vars:
        # Filter to the specified number of months
        months = int(vars.get("month", 1))
        now = request.utcnow
        month = datetime.timedelta(weeks=4)
        delta = month * months
        s3.filter = (table.date > (now - delta))

    return s3_rest_controller()

# =============================================================================
# Comments
# =============================================================================
def comment_parse(comment, comments, task_id=None):
    """
        Parse a Comment

        @param: comment - a gluon.sql.Row: the current comment
        @param: comments - a gluon.sql.Rows: full list of comments
        @param: task_id - a reference ID: optional task commented on
    """

    author = B(T("Anonymous"))
    if comment.created_by:
        utable = s3db.auth_user
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        query = (utable.id == comment.created_by)
        left = [ltable.on(ltable.user_id == utable.id),
                ptable.on(ptable.pe_id == ltable.pe_id)]
        row = db(query).select(utable.email,
                               ptable.first_name,
                               ptable.middle_name,
                               ptable.last_name,
                               left=left, limitby=(0, 1)).first()
        if row:
            person = row.pr_person
            user = row[utable._tablename]
            username = s3_fullname(person)
            email = user.email.strip().lower()
            import hashlib
            hash = hashlib.md5(email).hexdigest()
            url = "http://www.gravatar.com/%s" % hash
            author = B(A(username, _href=url, _target="top"))
    if not task_id and comment.task_id:
        table = s3db.project_task
        task = "re: %s" % table[comment.task_id].name
        header = DIV(author, " ", task)
        task_id = comment.task_id
    else:
        header = author
    thread = LI(DIV(s3base.s3_avatar_represent(comment.created_by),
                    DIV(DIV(header,
                            _class="comment-header"),
                        DIV(XML(comment.body)),
                        _class="comment-text"),
                        DIV(DIV(comment.created_on,
                                _class="comment-date"),
                            DIV(A(T("Reply"),
                                  _class="action-btn"),
                                _onclick="comment_reply(%i);" % comment.id,
                                _class="comment-reply"),
                            _class="fright"),
                    _id="comment-%i" % comment.id,
                    _task_id=task_id,
                    _class="comment-box"))

    # Add the children of this thread
    children = UL(_class="children")
    id = comment.id
    count = 0
    for comment in comments:
        if comment.parent == id:
            count = 1
            child = comment_parse(comment, comments, task_id=task_id)
            children.append(child)
    if count == 1:
        thread.append(children)

    return thread

# -----------------------------------------------------------------------------
def comments():
    """ Function accessed by AJAX from rfooter to handle Comments """

    try:
        task_id = request.args[0]
    except:
        raise HTTP(400)

    table = s3db.project_comment
    field = table.task_id
    field.default = task_id
    field.writable = field.readable = False

    # Form to add a new Comment
    # @ToDo: Rewrite using SQLFORM or S3SQLCustomForm
    from s3.s3msg import CrudS3
    crud = CrudS3()
    crud.messages.submit_button = T("Save")
    form = crud.create(table, formname="project_comment/%s" % task_id)

    # List of existing Comments
    comments = db(field == task_id).select(table.id,
                                           table.parent,
                                           table.body,
                                           table.created_by,
                                           table.created_on)

    output = UL(_id="comments")
    for comment in comments:
        if not comment.parent:
            # Show top-level threads at top-level
            thread = comment_parse(comment, comments, task_id=task_id)
            output.append(thread)

    script = "".join((
'''$('#comments').collapsible({xoffset:'-5',yoffset:'50',imagehide:img_path+'arrow-down.png',imageshow:img_path+'arrow-right.png',defaulthide:false})
$('#project_comment_parent__row1').hide()
$('#project_comment_parent__row').hide()
$('#project_comment_body').ckeditor(ck_config)
$('#submit_record__row input').click(function(){
 $('#comment-form').hide()
 $('#project_comment_body').ckeditorGet().destroy()
 return true
})'''))

    # No layout in this output!
    #s3.jquery_ready.append(script)

    output = DIV(output,
                 DIV(H4(T("New Post"),
                        _id="comment-title"),
                     form,
                     _id="comment-form",
                     _class="clear"),
                 SCRIPT(script))

    return XML(output)

# =============================================================================
# Campaigns
# =============================================================================
def campaign():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def campaign_keyword():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def campaign_message():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def campaign_response():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def campaign_response_summary():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# END =========================================================================