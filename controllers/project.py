# -*- coding: utf-8 -*-

"""
    Project Tracking & Management
"""

module = request.controller
resourcename = request.function

if module not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

drr = deployment_settings.get_project_drr()

# =============================================================================
def index():
    """ Module's Home Page """

    # Bypass home page & go direct to searching for Projects
    if deployment_settings.get_project_drr():
        return project()
    else:
        redirect(URL(f="project", vars={"tasks":1}))

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

    if "tasks" in request.get_vars:
        # Return simplified controller to pick a Project for which to list the Open Tasks
        table = s3db.project_project
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

    # Pre-process
    def prep(r):
        btable = s3db.project_beneficiary
        btable.community_id.requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                    "project_community.id",
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
                elif r.component_name in ("activity", "community"):
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
                elif r.component_name == "human_resource":
                    from eden.hrm import hrm_human_resource_represent

                    # We can pass the human resource type filter in the URL
                    group = r.vars.get('group', None)

                    # These values are defined in hrm_type_opts
                    if group:
                        if group == "staff":
                            group = 1
                        elif group == "volunteer":
                            group = 2

                        # Use the group to filter the component list
                        filter_by_type = (db.hrm_human_resource.type == group)
                        r.resource.add_component_filter("human_resource", filter_by_type)

                        # Use the group to filter the form widget for adding a new record
                        r.component.table.human_resource_id.requires = IS_ONE_OF(
                            db,
                            "hrm_human_resource.id",
                            hrm_human_resource_represent,
                            filterby="type",
                            filter_opts=(group,),
                            orderby="hrm_human_resource.person_id",
                            sort=True
                        )

            elif not r.id and r.function == "index":
                r.method = "search"
                # If just a few Projects, then a List is sufficient
                #r.method = "list"

        return True
    response.s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            if not r.component:
                # Do extra client-side validation
                # This part needs to be able to support multiple L10n_date_format
                #var datePattern = /^(19|20)\d\d([-\/.])(0[1-9]|1[012])\2(0[1-9]|[12][0-9]|3[01])$/;
                #if ( (start_date && !(datePattern.test(start_date))) | (end_date && !(datePattern.test(end_date))) ) {
                #    error_msg = '%s';
                #    jQuery('#project_project_start_date__row > td').last().text(error_msg);
                #    jQuery('#project_project_start_date__row > td').last().addClass('red');
                #    return false;
                #}
                validate = True
                date_format = deployment_settings.get_L10n_date_format()
                if date_format == T("%Y-%m-%d"):
                    # Default
                    start_date_string = "start_date[0], start_date[1], start_date[2]"
                    end_date_string = "end_date[0], end_date[1], end_date[2]"
                elif date_format == T("%m-%d-%Y"):
                    # US Style
                    start_date_string = "start_date[2], start_date[0], start_date[1]"
                    end_date_string = "end_date[2], end_date[0], end_date[1]"
                elif date_format == T("%d-%b-%Y"):
                    # Unsortable 'Pretty' style
                    start_date_string = "start_date[0] + ' ' + start_date[1] + ' ' + start_date[2]"
                    end_date_string = "end_date[0] + ' ' + end_date[1] + ' ' + end_date[2]"
                else:
                    # Unknown format - don't add extra validation
                    validate = False
                script = """$('.form-container > form').submit(function () {
    var start_date = this.start_date.value;
    var end_date = this.end_date.value;
    start_date = start_date.split('-');
    start_date = new Date(%s);
    end_date = end_date.split('-');
    end_date = new Date(%s);
    if (start_date > end_date) {
        var error_msg = '%s';
        jQuery('#project_project_end_date__row > td').last().text(error_msg);
        jQuery('#project_project_end_date__row > td').last().addClass('red');
        return false;
    } else {
        return true;
    }
});""" % (start_date_string,
          end_date_string,
          T("End date should be after start date"))
                if validate:
                    response.s3.jquery_ready.append(script)

                if not deployment_settings.get_project_drr():
                    read_url = URL(args=["[id]", "task"])
                    update_url = URL(args=["[id]", "task"])
                    s3mgr.crud.action_buttons(r,
                                              read_url=read_url,
                                              update_url=update_url)
        return output
    response.s3.postp = postp

    rheader = s3db.project_rheader
    return s3_rest_controller(module,
                              "project", # Need to specify as sometimes we come via index()
                              rheader=rheader,
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
    response.s3.prep = prep

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
    response.s3.postp = postp

    tabs = [(T("Details"), None),
            (T("Contact Persons"), "contact")]
    if drr:
        #tabs.append((T("Beneficiaries"), "beneficiary"))
        tabs.append((T("Documents"), "document"))
    else:
        tabs.append((T("Tasks"), "task"))
        #tabs.append((T("Attachments"), "document"))

    rheader = lambda r: s3db.project_rheader(r, tabs)
    return s3_rest_controller(rheader=rheader,
                              csv_template="activity")


def community():
    """
    RESTful CRUD controller to display project community information
    """
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
    response.s3.prep = prep

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
    response.s3.postp = postp

    tabs = [(T("Details"), None),
            (T("Contact Persons"), "contact"),
            (T("Beneficiaries"), "beneficiary"),
            ]

    rheader = lambda r: s3db.project_rheader(r, tabs)
    return s3_rest_controller(interactive_report=True,
                              rheader=rheader,
                              csv_template="community")

# -----------------------------------------------------------------------------
def community_contact():
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

    tablename = "project_task"
    table = s3db[tablename]
    # Custom Method to add Comments
    s3mgr.model.set_method(module, resourcename,
                           method="discuss",
                           action=discuss)

    statuses = response.s3.project_task_active_statuses
    crud_strings = s3.crud_strings[tablename]
    if "mine" in request.get_vars:
        # Show the Open Tasks for this User
        crud_strings.title_list = T("My Open Tasks")
        crud_strings.msg_list_empty = T("No Tasks Assigned")
        s3mgr.configure(tablename,
                        copyable=False,
                        listadd=False)
        try:
            # Add Virtual Fields
            list_fields = s3mgr.model.get_config(tablename,
                                                 "list_fields")
            list_fields.insert(4, (T("Project"), "project"))
            # Hide the Assignee column (always us)
            list_fields.remove("pe_id")
            # Hide the Status column (always 'assigned' or 'reopened')
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
        crud_strings.title_list = T("Open Tasks for %(project)s") % dict(project=name)
        crud_strings.title_search = T("Search Open Tasks for %(project)s") % dict(project=name)
        crud_strings.msg_list_empty = T("No Open Tasks for %(project)s") % dict(project=name)
        # Add Virtual Fields
        list_fields = s3mgr.model.get_config(tablename,
                                             "list_fields")
        list_fields.insert(2, (T("Activity"), "activity"))
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
        crud_strings.title_list = T("All Tasks")
        crud_strings.title_search = T("All Tasks")
        list_fields = s3mgr.model.get_config(tablename,
                                             "list_fields")
        list_fields.insert(2, (T("Project"), "project"))
        list_fields.insert(3, (T("Activity"), "activity"))
        s3mgr.configure(tablename,
                        report_options=Storage(
                            search=[
                                s3base.S3SearchOptionsWidget(
                                    field="project",
                                    name="project",
                                    label=T("Project")
                                )
                            ]
                        ),
                        list_fields=list_fields)
        if "open" in request.get_vars:
            # Show Only Open Tasks
            crud_strings.title_list = T("All Open Tasks")
            response.s3.filter = (table.status.belongs(statuses))

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.record:
                # Put the Comments in the RFooter
                ckeditor()
                response.s3.rfooter = LOAD("project", "comments.load", args=["task", r.id], ajax=True)
            if r.component:
                if r.component_name == "req":
                    if deployment_settings.has_module("hrm"):
                        r.component.table.type.default = 3
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        s3db.req_create_form_mods()
                elif r.component_name == "human_resource":
                    r.component.table.type.default = 2
            else:
                if not auth.s3_has_role("STAFF"):
                    # Hide fields to avoid confusion (both of inputters & recipients)
                    table = r.table
                    field = table.source
                    field.readable = field.writable = False
                    field = table.pe_id
                    field.readable = field.writable = False
                    field = table.date_due
                    field.readable = field.writable = False
                    field = table.milestone_id
                    field.readable = field.writable = False
                    field = table.time_estimated
                    field.readable = field.writable = False
                    field = table.time_actual
                    field.readable = field.writable = False
                    field = table.status
                    field.readable = field.writable = False
        return True
    response.s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            if r.method != "import":
                update_url = URL(args=["[id]"], vars=request.get_vars)
                s3mgr.crud.action_buttons(r,
                                          update_url=update_url)
                if not r.component and \
                   r.method != "search" and \
                   "form" in output:
                    # Insert fields to control the Project & Activity
                    sep = ": "
                    if auth.s3_has_role("STAFF"):
                        # Activity not easy for non-Staff to know about, so don't add
                        table = s3db.project_task_activity
                        field = table.activity_id
                        if r.record:
                            query = (table.task_id == r.record.id)
                            default = db(query).select(table.activity_id,
                                                       limitby=(0, 1)).first()
                            if default:
                                default = default.activity_id
                        else:
                            default = field.default
                        widget = field.widget or SQLFORM.widgets.options.widget(field, default)
                        field_id = '%s_%s' % (table._tablename, field.name)
                        label = field.label
                        label = LABEL(label, label and sep, _for=field_id,
                                      _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                        row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                        activity = s3.crud.formstyle(row_id, label, widget, field.comment)
                        try:
                            output["form"][0].insert(0, activity[1])
                        except:
                            # A non-standard formstyle with just a single row
                            pass
                        try:
                            output["form"][0].insert(0, activity[0])
                        except:
                            pass
                        s3.scripts.append("%s/s3.project.js" % s3_script_dir)
                    if "project" in request.get_vars:
                        widget = INPUT(value=request.get_vars.project, _name="project_id")
                        project = s3.crud.formstyle("project_task_project__row", "", widget, "")
                    else:
                        table = s3db.project_task_project
                        field = table.project_id
                        if r.record:
                            query = (table.task_id == r.record.id)
                            default = db(query).select(table.project_id,
                                                       limitby=(0, 1)).first()
                            if default:
                                default = default.project_id
                        else:
                            default = field.default
                        widget = field.widget or SQLFORM.widgets.options.widget(field, default)
                        field_id = '%s_%s' % (table._tablename, field.name)
                        label = field.label
                        label = LABEL(label, label and sep, _for=field_id,
                                      _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                        comment = field.comment if auth.s3_has_role("STAFF") else ""
                        row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                        project = s3.crud.formstyle(row_id, label, widget, comment)
                    try:
                        output["form"][0].insert(0, project[1])
                    except:
                        # A non-standard formstyle with just a single row
                        pass
                    try:
                        output["form"][0].insert(0, project[0])
                    except:
                        pass

        return output
    response.s3.postp = postp

    return s3_rest_controller(rheader=s3db.project_rheader)

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
    response.s3.prep = prep

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
    response.s3.prep = prep

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
        s3mgr.load("project_time")
        s3.crud_strings["project_time"].title_list = T("My Logged Hours")
        s3mgr.configure("project_time",
                        listadd=False)
        person_id = auth.s3_logged_in_person()
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
# Comments
# =============================================================================
def ckeditor():
    """ Load the Project Comments JS """

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
    $('#project_comment_task_id').val(task_id);
}"""))

    response.s3.js_global.append(js)

def discuss(r, **attr):
    """ Custom Method to manage the discussion of a Task """

    #if r.component:
    #    resourcename = "activity"
    #    id = r.component_id
    #else:
    resourcename = "task"
    id = r.id

    # Add the RHeader to maintain consistency with the other pages
    rheader = s3db.project_rheader(r)

    # Load the Project Comments JS
    ckeditor()

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
            import md5
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
                                                       "%(name)s"
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
        comments = ""

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

# END =========================================================================
