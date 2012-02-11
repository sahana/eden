# -*- coding: utf-8 -*-

"""
    Project Tracking & Management
"""

module = request.controller
resourcename = request.function

if module not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

s3_menu(module)

drr = deployment_settings.get_project_drr()

# =============================================================================
def index():
    """ Module's Home Page """

    # Bypass home page & go direct to searching for Projects
    redirect(URL(f="project", vars={"tasks":1}))
    #return project()

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# =============================================================================
def create():
    """ Redirect to project/create """
    redirect(URL(f="project", args="create"))

# -----------------------------------------------------------------------------
def project():
    """ RESTful CRUD controller """

    resourcename = "project"

    if "tasks" in request.get_vars:
        # Return simplified controller to pick a Project for which to list the Open Tasks
        s3mgr.load("project_project")
        s3.crud_strings["project_project"].title_list = T("Open Tasks for Project")
        s3.crud_strings["project_project"].subtitle_list = T("Select Project")
        s3mgr.LABEL.READ = "Select"
        s3mgr.LABEL.UPDATE = "Select"
        s3mgr.configure("project_project",
                        deletable=False,
                        listadd=False)
        # Post-process
        def postp(r, output):
            if r.interactive:
                if not r.component:
                    read_url = URL(f="task", args="search",
                                   vars={"project":"[id]"})
                    update_url = URL(f="task", args="search",
                                     vars={"project":"[id]"})
                    s3mgr.crud.action_buttons(r, deletable=False,
                                              read_url=read_url,
                                              update_url=update_url)
            return output
        response.s3.postp = postp
        return s3_rest_controller()

    table = s3db.hrm_human_resource
    table.person_id.comment = DIV(_class="tooltip",
                                  _title="%s|%s" % (T("Person"),
                                                    T("Select the person assigned to this role for this project.")))

    doc_table = s3db.table("doc_document", None)
    if doc_table is not None:
        doc_table.organisation_id.readable = False
        doc_table.person_id.readable = False
        doc_table.location_id.readable = False
        doc_table.organisation_id.writable = False
        doc_table.person_id.writable = False
        doc_table.location_id.writable = False

    def prep(r):
        btable = s3db.project_beneficiary
        btable.activity_id.requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                    "project_activity.id",
                                                    "%(name)s",
                                                    filterby="project_id",
                                                    filter_opts=[r.id],
                                                    sort=True))
        if r.interactive:
            if r.component is not None:
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
                elif r.component_name == "activity":
                    # Default the Location Selector list of countries to those found in the project
                    countries = r.record.countries_id
                    if countries:
                        ltable = s3db.gis_location
                        query = (ltable.id.belongs(countries))
                        countries = db(query).select(ltable.code)
                        deployment_settings.gis.countries = [c.code for c in countries]
                elif r.component_name == "task":
                    r.component.table.milestone_id.requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                "project_milestone.id",
                                                                "%(name)s",
                                                                filterby="project_id",
                                                                filter_opts=(r.id,),
                                                                ))
                    if "open" in request.get_vars:
                        # Show only the Open Tasks for this Project
                        statuses = response.s3.project_task_active_statuses
                        filter = (r.component.table.status.belongs(statuses))
                        r.resource.add_component_filter("task", filter)

            elif not r.id and r.function == "index":
                r.method = "search"
                # If just a few Projects, then a List is sufficient
                #r.method = "list"

        return True
    response.s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            if not r.component and not deployment_settings.get_project_drr():
                read_url = URL(args=["[id]", "task"])
                update_url = URL(args=["[id]", "task"])
                s3mgr.crud.action_buttons(r,
                                          read_url=read_url,
                                          update_url=update_url)
        return output
    response.s3.postp = postp

    rheader = eden.project.project_rheader
    return s3_rest_controller(module, resourcename,
                              rheader=rheader,
                              interactive_report=True,
                              csv_template="project")

# =============================================================================
def theme():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def hazard():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# =============================================================================
def organisation():
    """ RESTful CRUD controller """

    if drr:
        s3mgr.configure("project_organisation",
                        insertable=False,
                        editable=False,
                        deletable=False)

        list_btn = A(T("Funding Report"),
                     _href=URL(c="project", f="organisation",
                               args="report", vars=request.get_vars),
                     _class="action-btn")

        return s3_rest_controller(list_btn=list_btn,
                                  interactive_report=True,
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

    s3mgr.configure("project_beneficiary",
                    insertable=False,
                    editable=False,
                    deletable=False)

    list_btn = A(T("Beneficiary Report"),
                 _href=URL(c="project", f="beneficiary",
                           args="report", vars=request.get_vars),
                 _class="action-btn")

    return s3_rest_controller(interactive_report=True)

# =============================================================================
def activity_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def activity():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    tabs = [(T("Details"), None),
            (T("Contact Persons"), "contact")]
    if drr:
        tabs.append((T("Beneficiaries"), "beneficiary"))
        tabs.append((T("Documents"), "document"))
    else:
        tabs.append((T("Tasks"), "task"))
        #tabs.append((T("Attachments"), "document"))

    doc_table = s3db.table("doc_document", None)
    if doc_table is not None:
        doc_table.organisation_id.readable = False
        doc_table.person_id.readable = False
        doc_table.location_id.readable = False
        doc_table.organisation_id.writable = False
        doc_table.person_id.writable = False
        doc_table.location_id.writable = False

    rheader = lambda r: response.s3.project_rheader(r, tabs)
    return s3_rest_controller(interactive_report=True,
                              rheader=rheader,
                              csv_template="activity")

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

    tablename = "project_task"
    table = s3db[tablename]
    # Custom Method to add Comments
    s3mgr.model.set_method(module, resourcename,
                           method="discuss",
                           action=discuss)

    statuses = response.s3.project_task_active_statuses
    if "mine" in request.get_vars:
        # Show the Open Tasks for this User
        s3.crud_strings[tablename].title_list = T("My Open Tasks")
        s3.crud_strings[tablename].msg_list_empty = T("No Tasks Assigned")
        s3mgr.configure(tablename,
                        copyable=False,
                        listadd=False)
        try:
            # Add Virtual Fields
            table.virtualfields.append(eden.project.S3ProjectTaskVirtualfields())
            list_fields = s3mgr.model.get_config(tablename,
                                                 "list_fields")
            list_fields.insert(4, (T("Project"), "project"))
            # Hide the Assignee column (always us)
            list_fields.remove("pe_id")
            # Hide the Status column
            list_fields.remove("status")
            s3mgr.configure(tablename,
                            list_fields=list_fields)
        except:
            pass
        if auth.user:
            pe_id = auth.user.pe_id
            response.s3.filter = (table.pe_id == pe_id) & \
                                 (table.status.belongs(statuses))
    elif "project" in request.get_vars:
        # Show Open Tasks for this Project
        project = request.get_vars.project
        ptable = s3db.project_project
        try:
            name = db(ptable.id == project).select(ptable.name,
                                                   limitby=(0, 1)).first().name
        except:
            session.error = T("Project not Found")
            redirect(URL(args=None, vars=None))
        s3.crud_strings[tablename].title_list = T("Open Tasks for %(project)s") % dict(project=name)
        s3.crud_strings[tablename].title_search = T("Search Open Tasks for %(project)s") % dict(project=name)
        s3.crud_strings[tablename].msg_list_empty = T("No Open Tasks for %(project)s") % dict(project=name)
        # Add Virtual Fields
        table.virtualfields.append(eden.project.S3ProjectTaskVirtualfields())
        list_fields = s3mgr.model.get_config(tablename,
                                             "list_fields")
        list_fields.insert(2, (T("Activity"), "activity"))
        # task_search = s3base.S3Search(
                # advanced = (s3base.S3SearchSimpleWidget(
                    # name = "task_search_text_advanced",
                    # label = T("Search"),
                    # comment = T("Search for a Task by description."),
                    # field = [ "name",
                              # "description",
                            # ]
                    # ),
                    # s3base.S3SearchOptionsWidget(
                        # name = "task_search_activity",
                        # label = T("Activity"),
                        # field = ["activity"],
                        # cols = 2
                    # ),
                    # s3base.S3SearchOptionsWidget(
                        # name = "task_search_assignee",
                        # label = T("Assigned To"),
                        # field = ["pe_id"],
                        # cols = 2
                    # ),
                    # s3base.S3SearchMinMaxWidget(
                        # name="task_search_date_due",
                        # method="range",
                        # label=T("Date Due"),
                        # field=["date_due"]
                    # )
                # )
            # )
        s3mgr.configure(tablename,
                        # Block Add until we get the injectable component lookups
                        insertable=False,
                        deletable=False,
                        copyable=False,
                        #search_method=task_search,
                        list_fields=list_fields)
        ltable = s3db.project_task_project
        response.s3.filter = (ltable.project_id == project) & \
                             (ltable.task_id == table.id) & \
                             (table.status.belongs(statuses))
    else:
        s3.crud_strings[tablename].title_list = T("All Tasks")
        s3.crud_strings[tablename].title_search = T("All Tasks")
        # Add Virtual Fields
        table.virtualfields.append(eden.project.S3ProjectTaskVirtualfields())
        list_fields = s3mgr.model.get_config(tablename,
                                             "list_fields")
        list_fields.insert(2, (T("Project"), "project"))
        list_fields.insert(3, (T("Activity"), "activity"))
        # task_search = s3base.S3Search(
                # advanced = (s3base.S3SearchSimpleWidget(
                    # name = "task_search_text_advanced",
                    # label = T("Search"),
                    # comment = T("Search for a Task by description."),
                    # field = [ "name",
                              # "description",
                            # ]
                    # ),
                    # s3base.S3SearchOptionsWidget(
                        # name = "task_search_project",
                        # label = T("Project"),
                        # field = ["project"],
                        # cols = 2
                    # ),
                    # s3base.S3SearchOptionsWidget(
                        # name = "task_search_activity",
                        # label = T("Activity"),
                        # field = ["activity"],
                        # cols = 2
                    # ),
                    # s3base.S3SearchOptionsWidget(
                        # name = "task_search_assignee",
                        # label = T("Assigned To"),
                        # field = ["pe_id"],
                        # cols = 2
                    # ),
                    # s3base.S3SearchMinMaxWidget(
                        # name="task_search_date_due",
                        # method="range",
                        # label=T("Date Due"),
                        # field=["date_due"]
                    # )
                # )
            # )
        s3mgr.configure(tablename,
                        # Block Add until we get the injectable component lookups
                        insertable=False,
                        report_filter=[
                            s3base.S3SearchOptionsWidget(field=["project"],
                                                         name="project",
                                                         label=T("Project"))
                        ],
                        #search_method=search,
                        list_fields=list_fields)
        if "open" in request.get_vars:
            # Show Only Open Tasks
            s3.crud_strings[tablename].title_list = T("All Open Tasks")
            response.s3.filter = (table.status.belongs(statuses))

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component:
                if r.component_name == "req":
                    if deployment_settings.has_module("hrm"):
                        r.component.table.type.default = 3
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        s3db.req_create_form_mods()
                elif r.component_name == "human_resource":
                    r.component.table.type.default = 2

        return True
    response.s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            if r.method != "import":
                update_url = URL(args=["[id]"], vars=request.get_vars)
                s3mgr.crud.action_buttons(r,
                                          update_url=update_url)
        return output
    response.s3.postp = postp

    return s3_rest_controller(rheader=response.s3.project_rheader)

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
        s3mgr.load("project_time")
        s3.crud_strings["project_time"].title_list = T("My Logged Hours")
        s3mgr.configure("project_time",
                        listadd=False)
        person_id = auth.logged_in_person()
        if person_id:
            response.s3.filter = (table.person_id == person_id)
        try:
            list_fields = s3mgr.model.get_config(tablename,
                                                 "list_fields")
            list_fields.remove("person_id")
            s3mgr.configure(tablename,
                            list_fields=list_fields)
        except:
            pass

    elif "week" in request.get_vars:
        now = request.utcnow
        week = datetime.timedelta(days=7)
        response.s3.filter = (table.date > (now - week))

    return s3_rest_controller()

# =============================================================================
def person():
    """ Person controller for AddPersonWidget """

    def prep(r):
        if r.representation != "s3json":
            # Do not serve other representations here
            return False
        else:
            s3mgr.show_ids = True
        return True
    response.s3.prep = prep

    return s3_rest_controller("pr", resourcename)

# =============================================================================
# Comments
# =============================================================================
def discuss(r, **attr):
    """ Custom Method to manage the discussion of a Task """

    #if r.component:
    #    resourcename = "activity"
    #    id = r.component_id
    #else:
    resourcename = "task"
    id = r.id

    # Add the RHeader to maintain consistency with the other pages
    rheader = response.s3.project_rheader(r)

    ckeditor = URL(c="static", f="ckeditor", args="ckeditor.js")
    response.s3.scripts.append(ckeditor)
    adapter = URL(c="static", f="ckeditor", args=["adapters",
                                                  "jquery.js"])
    response.s3.scripts.append(adapter)

    # Toolbar options: http://docs.cksource.com/CKEditor_3.x/Developers_Guide/Toolbar
    js = "".join(("""
S3.i18n.reply = '""", str(T("Reply")), """';
var img_path = S3.Ap.concat('/static/img/jCollapsible/');
var ck_config = {toolbar:[['Bold','Italic','-','NumberedList','BulletedList','-','Link','Unlink','-','Smiley','-','Source','Maximize']],toolbarCanCollapse:false,removePlugins:'elementspath'};
function comment_reply(id) {
    $('#project_comment_task_id__row').hide();
    $('#project_comment_task_id__row1').hide();
    $('#comment-title').html(S3.i18n.reply);
    var editor = $('#project_comment_body').ckeditorGet();
    editor.destroy();
    $('#project_comment_body').ckeditor(ck_config);
    $('#comment-form').insertAfter($('#comment-' + id));
    $('#project_comment_parent').val(id);
    var task_id = $('#comment-' + id).attr('task_id');
    if (undefined == solution_id) {
    } else {
        $('#project_comment_task_id').val(task_id);
    }
}"""))

    response.s3.js_global.append(js)

    response.view = "project/discuss.html"
    return dict(rheader=rheader,
                resourcename=resourcename,
                id=id)

# -----------------------------------------------------------------------------
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
            hash = md5.new(email).hexdigest()
            url = "http://www.gravatar.com/%s" % hash
            author = B(A(username, _href=url, _target="top"))
    if not task_id and comment.task_id:
        s3mgr.load("project_task")
        task = "re: %s" % db.project_task[comment.task_id].name
        header = DIV(author, " ", task)
        task_id = comment.task_id
    else:
        header = author
    thread = LI(DIV(s3_avatar_represent(comment.created_by),
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
    """ Function accessed by AJAX from discuss() to handle Comments """

    resourcename = request.args(0)
    if not resourcename:
        raise HTTP(400)

    try:
        id = request.args[1]
    except:
        raise HTTP(400)

    #if resourcename == "problem":
    #    problem_id = id
    #    solution_id = None
    if resourcename == "task":
        task_id = id
    else:
        raise HTTP(400)

    table = s3db.project_comment
    if task_id:
        table.task_id.default = task_id
        table.task_id.writable = table.task_id.readable = False
    else:
        table.task_id.label = T("Related to Task (optional)")
        table.task_id.requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                       "project_task.id",
                                                       "%(name)s",
                                                       filterby="project_id",
                                                       filter_opts=[project_id]
                                                      ))

    # Form to add a new Comment
    form = crud.create(table)

    # List of existing Comments
    if task_id:
        comments = db(table.task_id == task_id).select(table.id,
                                                       table.parent,
                                                       table.body,
                                                       table.created_by,
                                                       table.created_on)
    else:
        comments = db(table.project_id == project_id).select(table.id,
                                                             table.parent,
                                                             table.solution_id,
                                                             table.body,
                                                             table.created_by,
                                                             table.created_on)

    output = UL(_id="comments")
    for comment in comments:
        if not comment.parent:
            # Show top-level threads at top-level
            thread = comment_parse(comment, comments, task_id=task_id)
            output.append(thread)

    # Also see the outer discuss()
    script = "".join(("""
$('#comments').collapsible({xoffset:'-5',yoffset:'50',imagehide:img_path+'arrow-down.png',imageshow:img_path+'arrow-right.png',defaulthide:false});
$('#project_comment_parent__row1').hide();
$('#project_comment_parent__row').hide();
$('#project_comment_body').ckeditor(ck_config);
$('#submit_record__row input').click(function(){$('#comment-form').hide();$('#project_comment_body').ckeditorGet().destroy();return true;});
"""))

    # No layout in this output!
    #response.s3.jquery_ready.append(script)

    output = DIV(output,
                 DIV(H4(T("New Post"),
                        _id="comment-title"),
                     form,
                     _id="comment-form",
                     _class="clear"),
                 SCRIPT(script))

    return XML(output)


# =============================================================================
# Deprecated
# =============================================================================
def site_rheader(r):
    """ Project Site page headers """

    if r.representation == "html":

        tablename, record = s3_rheader_resource(r)
        if tablename == "project_site" and record:
            site = record
            tabs = [(T("Details"), None),
                    #(T("Activities"), "activity"),
                    (T("Beneficiaries"), "beneficiary"),
                    #(T("Attachments"), "document"),
                    #(T("Photos"), "image"),
                    #(T("Shipments To"), "rms_req"),
                   ]

            rheader = DIV( TABLE( TR( TH("%s: " % T("Name") ),
                                      site.name
                                      ),
                                  TR( TH("%s: " % T("Project") ),
                                      s3.project_represent(site.project_id)
                                      )
                                 ),
                           s3_rheader_tabs(r, tabs)
                           )
            return rheader
    return None

# -----------------------------------------------------------------------------
def site():
    """ RESTful CRUD controller """

    return s3_rest_controller(rheader = site_rheader)

# =============================================================================
def need():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def need_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# =============================================================================
def gap_report():
    """
        Provide a Report on Gaps between Activities & Needs Assessments
        @deprecated
    """

    # Get all assess_summary
    assess_need_rows = db((db.project_need.id > 0) &\
                          (db.project_need.assess_id == db.assess_assess.id) &\
                          (db.assess_assess.location_id > 0) &\
                          (db.assess_assess.deleted != True)
                          ).select(db.assess_assess.id,
                                   db.assess_assess.location_id,
                                   db.assess_assess.datetime,
                                   db.project_need.need_type_id,
                                   db.project_need.value
                                   )

    patable = db.project_activity
    query = (patable.id > 0) & \
            (patable.location_id > 0) & \
            (patable.deleted != True)
    activity_rows = db(query).select(patable.id,
                                     patable.location_id,
                                     patable.need_type_id,
                                     patable.organisation_id,
                                     patable.total_bnf,
                                     patable.start_date,
                                     patable.end_date
                                    )

    def map_assess_to_gap(row):
        return Storage( assess_id = row.assess_assess.id,
                        location_id = row.assess_assess.location_id,
                        datetime = row.assess_assess.datetime,
                        need_type_id = row.project_need.need_type_id,
                        value = row.project_need.value,
                        activity_id = None,
                        organisation_id = None,
                        start_date = NONE,
                        end_date = NONE,
                        total_bnf = NONE,
                        )

    gap_rows = map(map_assess_to_gap, assess_need_rows)

    for activity_row in activity_rows:
        add_new_gap_row = True
        # Check if there is an Assessment of this location & subsector_id
        for gap_row in gap_rows:
            if activity_row.location_id == gap_row.location_id and \
               activity_row.need_type_id == gap_row.need_type_id:

                add_new_gap_row = False

                gap_row.activity_id = activity_row.id,
                gap_row.organisation_id = activity_row.organisation_id
                gap_row.start_date = activity_row.start_date
                gap_row.end_date = activity_row.end_date
                gap_row.total_bnf = activity_row.total_bnf
                break

        if add_new_gap_row:
            gap_rows.append(Storage(location_id = activity_row.location_id,
                                    need_type_id = activity_row.need_type_id,
                                    activity_id = activity_row.id,
                                    organisation_id = activity_row.organisation_id,
                                    start_date = activity_row.start_date,
                                    end_date = activity_row.end_date,
                                    total_bnf = activity_row.total_bnf,
                                    )
                            )

    headings = ("Location",
                "Needs",
                "Assessment",
                "Date",
                "Activity",
                "Start Date",
                "End Date",
                "Total Beneficiaries",
                "Organization",
                "Gap (% Needs Met)",
                )
    gap_table = TABLE(THEAD(TR(*[TH(header) for header in headings])),
                      _id = "list",
                      _class = "dataTable display"
                      )

    for gap_row in gap_rows:
        if gap_row.assess_id:
            assess_action_btn = A(T("Open"),
                                  _href = URL(c="assess", f="assess",
                                              args = (gap_row.assess_id, "need")
                                              ),
                                  _target = "blank",
                                  _id = "show-add-btn",
                                  _class="action-btn"
                                  )
        else:
            assess_action_btn = NONE

        if gap_row.activity_id:
            activity_action_btn =A(T("Open"),
                                   _href = URL(c="project", f="activity",
                                               args = (gap_row.activity_id)
                                               ),
                                   _target = "blank",
                                   _id = "show-add-btn",
                                   _class="action-btn"
                                   ),
        else:
            activity_action_btn = A(T("Add"),
                                   _href = URL(c="project", f="activity",
                                               args = ("create"),
                                               vars = {"location_id":gap_row.location_id,
                                                       "need_type_id":gap_row.need_type_id,
                                                       }
                                               ),
                                   _id = "show-add-btn",
                                   _class="action-btn"
                                   ),

        need_str = response.s3.need_type_represent(gap_row.need_type_id)
        if gap_row.value:
            need_str = "%d %s" % (gap_row.value, need_str)

        #Calculate the Gap
        if not gap_row.value:
            gap_str = NONE
        elif gap_row.total_bnf and gap_row.total_bnf != NONE:
            gap_str = "%d%%" % min((gap_row.total_bnf / gap_row.value) * 100, 100)
        else:
            gap_str = "0%"

        organisation_represent = s3db.org_organisation_represent

        gap_table.append(TR( gis_location_represent(gap_row.location_id),
                             need_str,
                             assess_action_btn,
                             gap_row.datetime or NONE,
                             activity_action_btn,
                             gap_row.start_date or NONE,
                             gap_row.end_date or NONE,
                             gap_row.total_bnf or NONE,
                             organisation_represent(gap_row.organisation_id),
                             gap_str
                            )
                        )

    return dict(title = T("Gap Analysis Report"),
                subtitle = T("Assessments Needs vs. Activities"),
                gap_table = gap_table,
                # Stop dataTables crashing
                r = None
                )

# -----------------------------------------------------------------------------
def gap_map():
    """
       Provide a Map Report on Gaps between Activities & Needs Assessments

       For every Need Type, there is a Layer showing the Assessments (Inactive)
       & the Activities (Inactive, Blue)

       @ToDo: popup_url
       @ToDo: Colour code the Assessments based on quantity of need

       @deprecated
    """

    # NB Currently the colour-coding isn't used (all needs are red)
    assess_summary_colour_code = {0:"#008000", # green
                                  1:"#FFFF00", # yellow
                                  2:"#FFA500", # orange
                                  3:"#FF0000", # red
                                  }

    atable = s3db.project_activity
    ntable = s3db.project_need
    ltable = s3db.gis_location
    astable = db.assess_assess
    feature_queries = []

    need_type_rows = db(db.project_need_type.id > 0).select()
    need_type_represent = response.s3.need_type_represent

    for need_type in need_type_rows:

        need_type_id = need_type.id
        need_type = need_type_represent(need_type_id)

        # Add Activities layer
        query = (atable.id > 0) & \
                (atable.need_type_id == need_type_id) & \
                (atable.location_id > 0) & \
                (atable.deleted != True) & \
                (atable.location_id == ltable.id)
        activity_rows = db(query).select(atable.id,
                                         atable.location_id,
                                         #atable.need_type_id,
                                         ltable.uuid,
                                         ltable.id,
                                         ltable.name,
                                         ltable.code,
                                         ltable.lat,
                                         ltable.lon)
        if len(activity_rows):
            for i in range( 0 , len( activity_rows) ):
                # Insert how we want this to appear on the map
                activity_rows[i].gis_location.shape = "circle"
                activity_rows[i].gis_location.size = 6
                activity_rows[i].gis_location.colour = "#0000FF" # blue
            feature_queries.append({ "name": "%s: Activities" % need_type,
                                     "query": activity_rows,
                                     "active": False })

        # Add Assessments layer
        query = (ntable.id > 0) & \
                (ntable.need_type_id == need_type_id) & \
                (ntable.assess_id == astable.id) & \
                (astable.location_id > 0) & \
                (astable.deleted != True) & \
                (astable.location_id == ltable.id)
        assess_need_rows = db(query).select(astable.id,
                                            astable.location_id,
                                            astable.datetime,
                                            #ntable.need_type_id,
                                            #ntable.value,
                                            ltable.uuid,
                                            ltable.id,
                                            ltable.name,
                                            ltable.code,
                                            ltable.lat,
                                            ltable.lon)

        if len(assess_need_rows):
            for i in range( 0 , len( assess_need_rows) ):
                # Insert how we want this to appear on the map
                assess_need_rows[i].gis_location.shape = "circle"
                assess_need_rows[i].gis_location.size = 4
                #assess_need_rows[i].gis_location.colour = assess_summary_colour_code[assess_need_rows[i].assess_summary.value]
                assess_need_rows[i].gis_location.colour = assess_summary_colour_code[3] # red

            feature_queries.append({ "name": "%s: Assessments" % need_type,
                                     "query": assess_need_rows,
                                     "active": False })

    map = gis.show_map(feature_queries = feature_queries)

    return dict(map = map,
                title = T("Gap Analysis Map"),
                subtitle = T("Assessments and Activities") )

# END =========================================================================
