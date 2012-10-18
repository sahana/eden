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
def inline():
    """ Test controller for inline link tables """

    from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent

    crud_form = S3SQLCustomForm(
                    "name",
                    # Project Organisations
                    S3SQLInlineComponent(
                        "organisation",
                        label=T("Participating Organisations"),
                        fields=["organisation_id",
                                "role",
                                "amount"
                                ],
                    ),
                )

    s3db.configure("project_project", crud_form=crud_form)

    return s3_rest_controller("project", "project")


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

    table = s3db.hrm_human_resource
    table.person_id.comment = DIV(_class="tooltip",
                                  _title="%s|%s" % (T("Person"),
                                                    T("Select the person assigned to this role for this project.")))

    doc_table = s3db.table("doc_document", None)
    if doc_table is not None:
        doc_table.organisation_id.readable = doc_table.organisation_id.writable = False
        doc_table.person_id.readable = doc_table.person_id.writable = False
        doc_table.location_id.readable = doc_table.location_id.writable = False

    # Pre-process
    def prep(r):
        table = s3db.project_project 
        
        # Location Filter
        s3db.gis_location_filter(r)
        
        # Filter Themes based on Sector
        if r.record:
            sector_ids = r.record.multi_sector_id
        else:
            sector_ids = []
        set_project_multi_theme_id_requires(sector_ids)

        if r.interactive:
            if not r.component:
                if r.id:
                    r.table.human_resource_id.represent = lambda id: \
                        s3db.hrm_human_resource_represent(id, show_link=True)
                elif r.function == "index":
                    r.method = "search"
                    # If just a few Projects, then a List is sufficient
                    #r.method = "list"
            else:
                if r.component_name == "organisation":
                    if r.method != "update":
                        host_role = 1
                        otable = s3db.project_organisation
                        query = (otable.deleted != True) & \
                                (otable.role == host_role) & \
                                (otable.project_id == r.id)
                        row = db(query).select(otable.id,
                                               limitby=(0, 1)).first()
                        if row:
                            project_organisation_roles = \
                                dict(s3.project_organisation_roles)
                            del project_organisation_roles[host_role]
                            otable.role.requires = \
                                IS_NULL_OR(IS_IN_SET(project_organisation_roles))
                elif r.component_name in ("activity", "location"):
                    # Default the Location Selector list of countries to those found in the project
                    countries = r.record.countries_id
                    if countries:
                        ttable = s3db.gis_location_tag
                        query = (ttable.location_id.belongs(countries)) & \
                                (ttable.tag == "ISO2")
                        countries = db(query).select(ttable.value)
                        settings.gis.countries = [c.value for c in countries]
                        
                    # Filter Activity Type based on Sector
                    set_project_multi_activity_type_id_requires(sector_ids)
                    #@ToDo: Do this for project_activity too.
                elif r.component_name == "task":
                    r.component.table.milestone_id.requires = IS_NULL_OR(
                                                                IS_ONE_OF(db,
                                                                          "project_milestone.id",
                                                                          s3db.project_milestone_represent,
                                                                          filterby="project_id",
                                                                          filter_opts=(r.id,),
                                                                          ))
                    if "open" in request.get_vars:
                        # Show only the Open Tasks for this Project
                        statuses = s3.project_task_active_statuses
                        filter = (r.component.table.status.belongs(statuses))
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
                    s3db.hrm_human_resource.person_id.represent = lambda id: \
                        s3db.pr_person_represent(id, show_link=True)
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
        return output
    s3.postp = postp

    rheader = s3db.project_rheader
    return s3_rest_controller(module,
                              "project", # Need to specify as sometimes we come via index()
                              rheader=rheader,
                              csv_template="project")
# -----------------------------------------------------------------------------
def set_project_multi_theme_id_requires(sector_ids):
    """
        Filters the multi_theme_id based on the sector_id
    """

    table = s3db.project_project
    ttable = s3db.project_theme
    tstable = s3db.project_theme_sector

    # All themes linked to the projects sectors or to no sectors 
    rows = db().select(ttable.id,
                       tstable.sector_id,
                       left=tstable.on(ttable.id == tstable.theme_id))
    sector_ids = sector_ids or []
    theme_ids = [row.project_theme.id for row in rows 
                 if not row.project_theme_sector.sector_id or 
                    row.project_theme_sector.sector_id in sector_ids]
    table.multi_theme_id.requires = IS_NULL_OR(
                                        IS_ONE_OF(db, 
                                                  "project_theme.id",
                                                  s3db.project_theme_represent,
                                                  filterby="id",
                                                  filter_opts=theme_ids,
                                                  sort=True,
                                                  multiple=True
                                                  )
                                               )

# -----------------------------------------------------------------------------
def set_project_multi_activity_type_id_requires(sector_ids):
    """
        Filters the multi_activity_type_id based on the sector_id
    """

    if sector_ids:
        # @ToDo: merge with set_project_multi_theme_id_requires?
        attable = s3db.project_activity_type
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
    s3db.project_location.multi_activity_type_id.requires = IS_NULL_OR(
                                        IS_ONE_OF(db, 
                                                  "project_activity_type.id",
                                                  s3db.project_activity_type_represent,
                                                  filterby="id",
                                                  filter_opts=activity_type_ids,
                                                  sort=True,
                                                  multiple=True
                                                  )
                                               )

# -----------------------------------------------------------------------------
def project_multi_theme_id_widget():
    """
        Used by the project controller to return dynamically generated 
        multi_theme_id widget based on sector_id
    """
    ptable = s3db.project_project
    sector_ids = [int(id) for id in request.vars.sector_ids.split(",") if id]
    value = [int(id) for id in request.vars.value.split(",") if id]
    
    set_project_multi_theme_id_requires(sector_ids)
    widget = ptable.multi_theme_id.widget(ptable.multi_theme_id,
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
def hazard():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def framework():
    """ RESTful CRUD controller """

    return s3_rest_controller(rheader=s3db.project_rheader)

# =============================================================================
def organisation():
    """ RESTful CRUD controller """

    if settings.get_project_multiple_organisations():
        s3db.configure("project_organisation",
                       insertable=False,
                       editable=False,
                       deletable=False)

        list_btn = A(T("Funding Report"),
                     _href=URL(c="project", f="organisation",
                               args="report", vars=request.get_vars),
                     _class="action-btn")

        return s3_rest_controller(list_btn=list_btn,
                                  csv_template="organisation")
    else:
        tabs = [
                (T("Basic Details"), None),
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
def activity():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

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
    """
        RESTful CRUD controller to display project location information
    """

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.record and r.record.project_id:
                table = s3db.project_project
                sector_ids = db(table.id == r.record.project_id).select(table.multi_sector_id,
                                                                        limitby=(0, 1)
                                                                        ).first().multi_sector_id
            else:
                sector_ids = []
            set_project_multi_activity_type_id_requires(sector_ids)
                    
            if r.component:
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
                for field in ["L4", "L3", "L2", "L1"]:
                    if field in hierarchy and record[field]:
                        item.append(TR(TD(hierarchy[field]),
                                       TD(record[field])))
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
                output = dict(
                        item = item,
                        title = title,
                        details_btn = details_btn,
                    )

        return output
    s3.postp = postp

    return s3_rest_controller(interactive_report=True,
                              rheader=s3db.project_rheader,
                              csv_template="location")

# -----------------------------------------------------------------------------
def demographic_data():
    """ RESTful CRUD controller """

    return s3db.stats_demographic_data_controller()

# -----------------------------------------------------------------------------
def location_contact():
    """ Show a list of all community contacts """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def report():
    """
        RESTful CRUD controller

        @ToDo: Why is this needed? To have no rheader?
    """

    return s3_rest_controller(module, "activity")

# =============================================================================
def task():
    """ RESTful CRUD controller """

    return s3db.project_task_controller()

# =============================================================================
def task_project():
    """ RESTful CRUD controller """

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
    """ RESTful CRUD controller """

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

    return s3_rest_controller()

# =============================================================================
def time():
    """ RESTful CRUD controller """

    tablename = "project_time"
    table = s3db[tablename]
    if "mine" in request.get_vars:
        # Show the Logged Time for this User
        s3.crud_strings["project_time"].title_list = T("My Logged Hours")
        s3db.configure("project_time",
                       orderby=~table.date,
                       listadd=False)
        person_id = auth.s3_logged_in_person()
        if person_id:
            # @ToDo: Use URL filter instead, but the Search page will have 
            # to populate it's widgets based on the URL filter  
            s3.filter = (table.person_id == person_id)
        list_fields = ["id",
                       "date",
                       "hours",
                       (T("Project"), "project"),
                       (T("Activity"), "activity"),
                       "task_id",
                       "comments",
                       ]
        s3db.configure(tablename,
                       list_fields=list_fields)

    elif "week" in request.get_vars:
        now = request.utcnow
        week = datetime.timedelta(days=7)
        s3.filter = (table.date > (now - week))

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

# -----------------------------------------------------------------------------
def partners():
    # ToDo: This could need to be a deployment setting
    current.request.get_vars["organisation.organisation_type_id$name"] = "Bilateral,Government,Intergovernmental,NGO,UN agency"
    return s3db.org_organisation_controller()

# END =========================================================================