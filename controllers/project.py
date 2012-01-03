# -*- coding: utf-8 -*-

"""
    Project Tracking & Management
"""

module = request.controller
resourcename = request.function

if module not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

s3_menu(module)

# =============================================================================
def index():
    """ Module's Home Page """

    # Bypass home page & go direct to searching for Projects
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
    db.hrm_human_resource.person_id.comment = DIV(_class="tooltip",
                                                  _title="%s|%s" % (T("Person"),
                                                                    T("Select the person assigned to this role for this project.")))

    if deployment_settings.get_project_community_activity():
        activity_label = T("Communities")
    else:
        activity_label = T("Activities")

    tabs = [(T("Basic Details"), None),
            (T("Organizations"), "organisation"),
            (activity_label, "activity"),
            (T("Tasks"), "task"),
            (T("Documents"), "document"),
           ]

    doc_table = s3db.table("doc_document", None)
    if doc_table is not None:
        doc_table.organisation_id.readable = False
        doc_table.person_id.readable = False
        doc_table.location_id.readable = False
        doc_table.organisation_id.writable = False
        doc_table.person_id.writable = False
        doc_table.location_id.writable = False

    def prep(r):
        s3mgr.load("project_beneficiary")
        btable = db.project_beneficiary
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
                        ltable = db.gis_location
                        query = (ltable.id.belongs(countries))
                        countries = db(query).select(ltable.code)
                        deployment_settings.gis.countries = [c.code for c in countries]
            elif not r.id and r.function == "index":
                r.method = "search"

        return True
    response.s3.prep = prep

    rheader = lambda r: response.s3.project_rheader(r, tabs)
    return s3_rest_controller(module, resourcename,
                              rheader=rheader,
                              interactive_report=True,
                              csv_template="project")

# =============================================================================
def theme():
    """ RESTful CRUD controller """

    return s3_rest_controller(module, resourcename)

# -----------------------------------------------------------------------------
def hazard():
    """ RESTful CRUD controller """

    return s3_rest_controller(module, resourcename)

# =============================================================================
def organisation():
    """ RESTful CRUD controller """

    s3mgr.configure("project_organisation",
                    insertable=False,
                    editable=False,
                    deletable=False)

    list_btn = A(T("Funding Report"),
                 _href=URL(c="project", f="organisation",
                           args="analyze", vars=request.get_vars),
                 _class="action-btn")

    return s3_rest_controller(module, resourcename,
                              list_btn=list_btn,
                              interactive_report=True,
                              csv_template="organisation")

# =============================================================================
def beneficiary_type():
    """ RESTful CRUD controller """

    return s3_rest_controller(module, resourcename)

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
                           args="analyze", vars=request.get_vars),
                 _class="action-btn")

    return s3_rest_controller(module, resourcename,
                              interactive_report=True)

# =============================================================================
def activity_type():
    """ RESTful CRUD controller """

    return s3_rest_controller(module, resourcename)

# -----------------------------------------------------------------------------
def activity():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3mgr.load(tablename)
    table = db[tablename]

    tabs = [(T("Details"), None),
            (T("Beneficiaries"), "beneficiary"),
            (T("Tasks"), "task"),
            (T("Documents"), "document"),
           ]


    doc_table = s3db.table("doc_document", None)
    if doc_table is not None:
        doc_table.organisation_id.readable = False
        doc_table.person_id.readable = False
        doc_table.location_id.readable = False
        doc_table.organisation_id.writable = False
        doc_table.person_id.writable = False
        doc_table.location_id.writable = False

    rheader = lambda r: response.s3.project_rheader(r, tabs)
    return s3_rest_controller(module, resourcename,
                              interactive_report=True,
                              rheader=rheader,
                              csv_template="activity")

# -----------------------------------------------------------------------------
def report():
    """
        RESTful CRUD controller

        @ToDo: Why is this needed? To have no rheader?
    """

    resourcename = "activity"

    return s3_rest_controller(module, resourcename)

# =============================================================================
def task():
    """ RESTful CRUD controller """

    s3mgr.load("project_task")
    # Discussion can also be done at the Solution component level
    s3mgr.model.set_method(module, resourcename,
                           method="discuss",
                           action=discuss)

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component:
                if r.component_name == "req":
                    if deployment_settings.has_module("hrm"):
                        r.component.table.type.default = 3
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        response.s3.req_create_form_mods()
                elif r.component_name == "human_resource":
                    r.component.table.type.default = 2

        return True
    response.s3.prep = prep

    return s3_rest_controller(module, resourcename,
                              rheader=response.s3.project_rheader)

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

    return s3_rest_controller("pr", "person")

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

    if comment.created_by:
        utable = db.auth_user
        query = (utable.id == comment.created_by)
        user = db(query).select(utable.email,
                                utable.person_uuid,
                                limitby=(0, 1)).first()
        ptable = db.pr_person
        query = (ptable.uuid == user.person_uuid)
        person = db(query).select(ptable.first_name,
                                  ptable.middle_name,
                                  ptable.last_name,
                                  limitby=(0, 1)).first()
        username = s3_fullname(person)
        email = user.email.strip().lower()
        hash = md5.new(email).hexdigest()
        url = "http://www.gravatar.com/%s" % hash
        author = B(A(username, _href=url, _target="top"))
    else:
        author = B(T("Anonymous"))
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

    s3mgr.load("project_comment")
    table = db.project_comment
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

    _user_table = db.auth_user
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
                    #(T("Documents"), "document"),
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

    return s3_rest_controller(module, resourcename,
                              rheader = site_rheader)

# =============================================================================
def need():
    """ RESTful CRUD controller """

    return s3_rest_controller(module, resourcename)

# -----------------------------------------------------------------------------
def need_type():
    """ RESTful CRUD controller """

    return s3_rest_controller(module, resourcename)

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

    atable = db.project_activity
    ntable = db.project_need
    ltable = db.gis_location
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
