# -*- coding: utf-8 -*-

"""
    Default Controllers
"""

module = "default"

# -----------------------------------------------------------------------------
def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    # If webservices don't use sessions, avoid cluttering up the storage
    #session.forget()
    return service()

# -----------------------------------------------------------------------------
def download():
    """ Download a file """

    # Load the Model
    tablename = request.args[0].split(".", 1)[0]
    table = s3db[tablename]

    return response.download(request, db)

# =============================================================================
def register_validation(form):
    """ Validate the fields in registration form """

    vars = form.vars
    # Mobile Phone
    if "mobile" in vars and vars.mobile:
        import re
        regex = re.compile(single_phone_number_pattern)
        if not regex.match(vars.mobile):
            form.errors.mobile = T("Invalid phone number")
    elif settings.get_auth_registration_mobile_phone_mandatory():
        form.errors.mobile = T("Phone number is required")

    org = settings.get_auth_registration_organisation_id_default()
    if org:
        # Add to default organisation
        vars.organisation_id = org

    return

# -----------------------------------------------------------------------------
auth.settings.register_onvalidation = register_validation

# =============================================================================
def index():
    """ Main Home Page """

    page = request.args(0)
    if page:
        # Go to a custom page
        # Arg 1 = function in /private/templates/<template>/controllers.py
        # other Args & Vars passed through
        controller = "applications.%s.private.templates.%s.controllers" % \
                            (appname, settings.get_template())
        try:
            exec("import %s as custom" % controller)
        except ImportError, e:
            # No Custom Page available, continue with the default
            page = "private/templates/%s/controllers.py" % \
                        settings.get_template()
            s3base.s3_debug("File not loadable: %s, %s" % (page, e.message))
        else:
            if page in custom.__dict__:
                exec ("output = custom.%s()()" % page)
                return output
            else:
                raise(HTTP(404, "Function not found: %s()" % page))
    elif settings.get_template() != "default":
        # Try a Custom Homepage
        controller = "applications.%s.private.templates.%s.controllers" % \
                            (appname, settings.get_template())
        try:
            exec("import %s as custom" % controller)
        except ImportError, e:
            # No Custom Page available, continue with the default
            # @ToDo: cache this result in session
            s3base.s3_debug("Custom homepage cannot be loaded: %s" % e.message)
        else:
            if "index" in custom.__dict__:
                output = custom.index()()
                return output

    # Default Homepage
    title = settings.get_system_name()
    response.title = title

    item = ""
    if settings.has_module("cms"):
        table = s3db.cms_post
        item = db(table.module == module).select(table.body,
                                                 limitby=(0, 1)).first()
        if item:
            item = DIV(XML(item.body))
        else:
            item = ""

    if settings.has_module("cr"):
        table = s3db.cr_shelter
        SHELTERS = s3.crud_strings["cr_shelter"].title_list
    else:
        SHELTERS = ""

    # Menu Boxes
    menu_btns = [#div, label, app, function
                ["facility", T("Facilities"), "org", "facility"],
                ["facility", T("Hospitals"), "hms", "hospital"],
                ["facility", T("Offices"), "org", "office"],
                ["facility", SHELTERS, "cr", "shelter"],
                ["facility", T("Warehouses"), "inv", "warehouse"],
                ["sit", T("Staff"), "hrm", "staff"],
                ["sit", T("Volunteers"), "vol", "volunteer"],
                ["sit", T("Incidents"), "irs", "ireport"],
                ["sit", T("Assessments"), "survey", "series"],
                ["sit", T("Assets"), "asset", "asset"],
                ["sit", T("Inventory Items"), "inv", "inv_item"],
                #["dec", T("Gap Map"), "project", "gap_map"],
                #["dec", T("Gap Report"), "project", "gap_report"],
                ["dec", T("Requests"), "req", "req"],
                ["res", T("Projects"), "project", "project"],
                ["res", T("Commitments"), "req", "commit"],
                ["res", T("Sent Shipments"), "inv", "send"],
                ["res", T("Received Shipments"), "inv", "recv"]
                ]

    # Change to (Mitigation)/Preparedness/Response/Recovery?
    menu_divs = {"facility": DIV( H3(T("Facilities")),
                                 _id = "facility_box", _class = "menu_box"),
                 "sit": DIV( H3(T("Situation")),
                              _id = "menu_div_sit", _class = "menu_div"),
                 "dec": DIV( H3(T("Decision")),
                              _id = "menu_div_dec", _class = "menu_div"),
                 "res": DIV( H3(T("Response")),
                              _id = "menu_div_res", _class = "menu_div"),
                }

    for div, label, app, function in menu_btns:
        if settings.has_module(app):
            # @ToDo: Also check permissions (e.g. for anonymous users)
            menu_divs[div].append(A(DIV(label,
                                        _class = "menu-btn-r"),
                                    _class = "menu-btn-l",
                                    _href = URL(app,function)
                                    )
                                 )

    div_arrow = DIV(IMG(_src = "/%s/static/img/arrow_blue_right.png" % \
                                 appname),
                    _class = "div_arrow")
    sit_dec_res_box = DIV(menu_divs["sit"],
                          div_arrow,
                          menu_divs["dec"],
                          div_arrow,
                          menu_divs["res"],
                          _id = "sit_dec_res_box",
                          _class = "menu_box fleft swidth"
                     #div_additional,
                    )
    facility_box  = menu_divs["facility"]
    facility_box.append(A(IMG(_src = "/%s/static/img/map_icon_128.png" % \
                                       appname),
                          _href = URL(c="gis", f="index"),
                          _title = T("Map")
                          )
                        )

    datatable_ajax_source = ""

    # Check logged in AND permissions
    roles = session.s3.roles
    if AUTHENTICATED in roles and \
       auth.s3_has_permission("read", db.org_organisation):
        org_items = organisation()
        datatable_ajax_source = "/%s/default/organisation.aaData" % \
                                appname
        s3.actions = None
        response.view = "default/index.html"
        auth.permission.controller = "org"
        auth.permission.function = "site"
        permitted_facilities = auth.permitted_facilities(redirect_on_error=False)
        manage_facility_box = ""
        if permitted_facilities:
            facility_list = s3base.s3_represent_facilities(db, permitted_facilities,
                                                           link=False)
            facility_list = sorted(facility_list, key=lambda fac: fac[1])
            facility_opts = [OPTION(opt[1], _value = opt[0])
                             for opt in facility_list]
            if facility_list:
                manage_facility_box = DIV(H3(T("Manage Your Facilities")),
                                          SELECT(_id = "manage_facility_select",
                                                 _style = "max-width:400px;",
                                                 *facility_opts
                                                 ),
                                          A(T("Go"),
                                            _href = URL(c="default", f="site",
                                                        args=[facility_list[0][0]]),
                                            #_disabled = "disabled",
                                            _id = "manage_facility_btn",
                                            _class = "action-btn"
                                            ),
                                          _id = "manage_facility_box",
                                          _class = "menu_box fleft"
                                          )
                s3.jquery_ready.append(
'''$('#manage_facility_select').change(function(){
 $('#manage_facility_btn').attr('href',S3.Ap.concat('/default/site/',$('#manage_facility_select').val()))
})''')
            else:
                manage_facility_box = DIV()

        org_box = DIV(H3(T("Organizations")),
                      A(T("Add Organization"),
                        _href = URL(c="org", f="organisation",
                                    args=["create"]),
                        _id = "add-btn",
                        _class = "action-btn",
                        _style = "margin-right: 10px;"),
                      org_items,
                      _id = "org_box",
                      _class = "menu_box fleft"
                      )
    else:
        manage_facility_box = ""
        org_box = ""

    # Login/Registration forms
    self_registration = settings.get_security_self_registration()
    registered = False
    login_form = None
    login_div = None
    register_form = None
    register_div = None
    if AUTHENTICATED not in roles:
        # This user isn't yet logged-in
        if request.cookies.has_key("registered"):
            # This browser has logged-in before
            registered = True

        if self_registration:
            # Provide a Registration box on front page
            register_form = auth.register()
            register_div = DIV(H3(T("Register")),
                               P(XML(T("If you would like to help, then please %(sign_up_now)s") % \
                                        dict(sign_up_now=B(T("sign-up now"))))))

             # Add client-side validation
            s3base.s3_register_validation()

            if request.env.request_method == "POST":
                post_script = \
'''$('#register_form').removeClass('hide')
$('#login_form').addClass('hide')'''
            else:
                post_script = ""
            register_script = \
'''$('#register-btn').attr('href','#register')
$('#login-btn').attr('href','#login')
%s
$('#register-btn').click(function(){
 $('#register_form').removeClass('hide')
 $('#login_form').addClass('hide')
})
$('#login-btn').click(function(){
 $('#register_form').addClass('hide')
 $('#login_form').removeClass('hide')
})''' % post_script
            s3.jquery_ready.append(register_script)

        # Provide a login box on front page
        request.args = ["login"]
        auth.messages.submit_button = T("Login")
        login_form = auth()
        login_div = DIV(H3(T("Login")),
                        P(XML(T("Registered users can %(login)s to access the system" % \
                                dict(login=B(T("login")))))))

    if settings.frontpage.rss:
        s3.external_stylesheets.append( "http://www.google.com/uds/solutions/dynamicfeed/gfdynamicfeedcontrol.css" )
        s3.scripts.append( "http://www.google.com/jsapi?key=notsupplied-wizard" )
        s3.scripts.append( "http://www.google.com/uds/solutions/dynamicfeed/gfdynamicfeedcontrol.js" )
        counter = 0
        feeds = ""
        for feed in settings.frontpage.rss:
            counter += 1
            feeds = "".join((feeds,
                             "{title:'%s',\n" % feed["title"],
                             "url:'%s'}" % feed["url"]))
            # Don't add a trailing comma for old IEs
            if counter != len(settings.frontpage.rss):
                feeds += ",\n"
        # feedCycleTime: milliseconds before feed is reloaded (5 minutes)
        feed_control = "".join(('''
function LoadDynamicFeedControl(){
 var feeds=[
  ''', feeds, '''
 ]
 var options={
  feedCycleTime:300000,
  numResults:5,
  stacked:true,
  horizontal:false,
  title:"''', str(T("News")), '''"
 }
 new GFdynamicFeedControl(feeds,'feed-control',options)
}
google.load('feeds','1')
google.setOnLoadCallback(LoadDynamicFeedControl)'''))
        s3.js_global.append(feed_control)

    return dict(title = title,
                item = item,
                sit_dec_res_box = sit_dec_res_box,
                facility_box = facility_box,
                manage_facility_box = manage_facility_box,
                org_box = org_box,
                r = None, # Required for dataTable to work
                datatable_ajax_source = datatable_ajax_source,
                self_registration=self_registration,
                registered=registered,
                login_form=login_form,
                login_div=login_div,
                register_form=register_form,
                register_div=register_div
                )

# -----------------------------------------------------------------------------
def organisation():
    """
        Function to handle pagination for the org list on the homepage
    """

    from s3.s3utils import S3DataTable

    resource = s3db.resource("org_organisation")
    totalrows = resource.count()
    table = resource.table

    list_fields = ["id", "name"]
    limit = int(request.get_vars["iDisplayLength"]) if request.extension == "aaData" else 1
    rfields = resource.resolve_selectors(list_fields)[0]
    (orderby, filter) = S3DataTable.getControlData(rfields, request.vars)
    resource.add_filter(filter)
    filteredrows = resource.count()
    if isinstance(orderby, bool):
        orderby = table.name
    rows = resource.select(list_fields,
                           orderby=orderby,
                           start=0,
                           limit=limit,
                           )
    data = resource.extract(rows,
                            list_fields,
                            represent=True,
                            )
    dt = S3DataTable(rfields, data)
    dt.defaultActionButtons(resource)
    s3.no_formats = True
    if request.extension == "html":
        items = dt.html(totalrows,
                        filteredrows,
                        "org_list_1",
                        dt_displayLength=10,
                        dt_ajax_url=URL(c="default",
                                        f="organisation",
                                        extension="aaData",
                                        vars={"id": "org_list_1"},
                                        ),
                       )
    elif request.extension.lower() == "aadata":
        limit = resource.count()
        if "sEcho" in request.vars:
            echo = int(request.vars.sEcho)
        else:
            echo = None
        items = dt.json(totalrows,
                        filteredrows,
                        "supply_list_1",
                        echo)
    else:
        raise HTTP(501, s3mgr.ERROR.BAD_FORMAT)
    return items

# -----------------------------------------------------------------------------
def site():
    """
        @todo: Avoid redirect
    """
    s3db.table("org_site")
    if len(request.args):
        site_id = request.args[0]
        site_r = db.org_site[site_id]
        tablename = site_r.instance_type
        table = s3db.table(tablename)
        if table:
            query = (table.site_id == site_id)
            id = db(query).select(db[tablename].id,
                                  limitby = (0, 1)).first().id
            cf = tablename.split("_", 1)
            redirect(URL(c = cf[0],
                         f = cf[1],
                         args = [id]))
    raise HTTP(404)

# -----------------------------------------------------------------------------
def message():
    #if "verify_email_sent" in request.args:
    title = T("Account Registered - Please Check Your Email")
    message = T( "%(system_name)s has sent an email to %(email)s to verify your email address.\nPlease check your email to verify this address. If you do not receive this email please check you junk email or spam filters." )\
                 % {"system_name": settings.get_system_name(),
                    "email": request.vars.email}
    image = "email_icon.png"
    return dict(title = title,
                message = message,
                image_src = "/%s/static/img/%s" % (appname, image)
                )

# -----------------------------------------------------------------------------
def rapid():
    """ Set/remove rapid data entry flag """

    val = request.vars.get("val", True)
    if val == "0":
        val = False
    else:
        val = True
    session.s3.rapid_data_entry = val

    response.view = "xml.html"
    return dict(item=str(session.s3.rapid_data_entry))

# -----------------------------------------------------------------------------
def user():
    """ Auth functions based on arg. See gluon/tools.py """

    arg = request.args(0)
    auth.settings.on_failed_authorization = URL(f="error")

    auth.configure_user_fields()

    _table_user = auth.settings.table_user

    auth.settings.profile_onaccept = auth.s3_user_profile_onaccept

    self_registration = settings.get_security_self_registration()
    login_form = register_form = None

    if request.args:
        arg = request.args(0)
    else:
        arg = None

    if arg == "login":
        # @ToDo: move this code to /modules/s3/s3aaa.py:def login?
        auth.messages.submit_button = T("Login")
        form = auth()
        #form = auth.login()
        login_form = form
        if s3.crud.submit_style:
            form[0][-1][1][0]["_class"] = s3.crud.submit_style
    elif arg == "register":
        # @ToDo: move this code to /modules/s3/s3aaa.py:def register?
        if not self_registration:
            session.error = T("Registration not permitted")
            redirect(URL(f="index"))

        form = auth.register()
        register_form = form
        # Add client-side validation
        s3base.s3_register_validation()
    elif arg == "change_password":
        form = auth()
    elif arg == "profile":
        # @ToDo: move this code to /modules/s3/s3aaa.py:def profile?

        # If we have an opt_in and some post_vars then update the opt_in value
        if settings.get_auth_opt_in_to_email() and request.post_vars:
            opt_list = settings.get_auth_opt_in_team_list()
            removed = []
            selected = []
            for opt_in in opt_list:
                if opt_in in request.post_vars:
                    selected.append(opt_in)
                else:
                    removed.append(opt_in)
            ptable = s3db.pr_person
            putable = s3db.pr_person_user
            query = (putable.user_id == request.post_vars.id) & \
                    (putable.pe_id == ptable.pe_id)
            person_id = db(query).select(ptable.id, limitby=(0, 1)).first().id
            db(ptable.id == person_id).update(opt_in = selected)

            g_table = s3db["pr_group"]
            gm_table = s3db["pr_group_membership"]
            # Remove them from any team they are a member of in the removed list
            for team in removed:
                query = (g_table.name == team) & \
                        (gm_table.group_id == g_table.id) & \
                        (gm_table.person_id == person_id)
                gm_rec = db(query).select(g_table.id, limitby=(0, 1)).first()
                if gm_rec:
                    db(gm_table.id == gm_rec.id).delete()
            # Add them to the team (if they are not already a team member)
            for team in selected:
                query = (g_table.name == team) & \
                        (gm_table.group_id == g_table.id) & \
                        (gm_table.person_id == person_id)
                gm_rec = db(query).select(g_table.id, limitby=(0, 1)).first()
                if not gm_rec:
                    query = (g_table.name == team)
                    team_rec = db(query).select(g_table.id, limitby=(0, 1)).first()
                    # if the team doesn't exist then add it
                    if team_rec == None:
                        team_id = g_table.insert(name = team, group_type = 5)
                    else:
                        team_id = team_rec.id
                    gm_table.insert(group_id = team_id,
                                    person_id = person_id)
        if settings.get_auth_openid():
            form = DIV(form, openid_login_form.list_user_openids())
        else:
            form = auth.profile()
        # add an opt in clause to receive emails depending on the deployment settings
        if settings.get_auth_opt_in_to_email():
            ptable = s3db.pr_person
            ltable = s3db.pr_person_user
            opt_list = settings.get_auth_opt_in_team_list()
            query = (ltable.user_id == form.record.id) & \
                    (ltable.pe_id == ptable.pe_id)
            db_opt_in_list = db(query).select(ptable.opt_in, limitby=(0, 1)).first().opt_in
            for opt_in in opt_list:
                field_id = "%s_opt_in_%s" % (_table_user, opt_list)
                if opt_in in db_opt_in_list:
                    checked = "selected"
                else:
                    checked = None
                form[0].insert(-1,
                               TR(TD(LABEL("Receive %s updates:" % opt_in,
                                           _for="opt_in",
                                           _id=field_id + SQLFORM.ID_LABEL_SUFFIX),
                                     _class="w2p_fl"),
                                     INPUT(_name=opt_in, _id=field_id, _type="checkbox", _checked=checked),
                               _id=field_id + SQLFORM.ID_ROW_SUFFIX))
    else:
        # Retrieve Password / Logout
        form = auth()

    # Use Custom Ext views
    # Best to not use an Ext form for login: can't save username/password in browser & can't hit 'Enter' to submit!
    #if request.args(0) == "login":
    #    response.title = T("Login")
    #    response.view = "auth/login.html"

    return dict(form=form,
                login_form=login_form,
                register_form=register_form,
                self_registration=self_registration)

# -----------------------------------------------------------------------------
def facebook():
    """ Login using Facebook """

    if not auth.settings.facebook:
        redirect(URL(f="user", args=request.args, vars=request.vars))

    from s3oauth import FaceBookAccount
    auth.settings.login_form = FaceBookAccount()
    form = auth()

    return dict(form=form)

# -----------------------------------------------------------------------------
def google():
    """ Login using Google """

    if not auth.settings.google:
        redirect(URL(f="user", args=request.args, vars=request.vars))

    from s3oauth import GooglePlusAccount
    auth.settings.login_form = GooglePlusAccount()
    form = auth()

    return dict(form=form)

# -----------------------------------------------------------------------------
def source():
    """ RESTful CRUD controller """
    return s3_rest_controller("s3", "source")

# -----------------------------------------------------------------------------
# About Sahana
def apath(path=""):
    """ Application path """

    from gluon.fileutils import up
    opath = up(request.folder)
    #TODO: This path manipulation is very OS specific.
    while path[:3] == "../": opath, path=up(opath), path[3:]
    return os.path.join(opath,path).replace("\\", "/")

def about():
    """
        The About page provides details on the software dependencies and
        versions available to this instance of Sahana Eden.

        @ToDo: Avoid relying on Command Line tools which may not be in path
               - pull back info from Python modules instead?
    """

    import sys
    import subprocess
    import string

    python_version = sys.version
    web2py_version = open(apath("../VERSION"), "r").read()[8:]
    sahana_version = open(os.path.join(request.folder, "VERSION"), "r").read()
    # Database
    sqlite_version = None
    mysql_version = None
    mysqldb_version = None
    pgsql_version = None
    psycopg_version = None
    if db_string[0].find("sqlite") != -1:
        try:
            import sqlite3
            #sqlite_version = (subprocess.Popen(["sqlite3", "-version"], stdout=subprocess.PIPE).communicate()[0]).rstrip()
            sqlite_version = sqlite3.version
        except:
            sqlite_version = T("Unknown")
    elif db_string[0].find("mysql") != -1:
        try:
            mysql_version = (subprocess.Popen(["mysql", "--version"], stdout=subprocess.PIPE).communicate()[0]).rstrip()[10:]
        except:
            mysql_version = T("Unknown")
        try:
            import MySQLdb
            mysqldb_version = MySQLdb.__revision__
        except:
            mysqldb_version = T("Not installed or incorrectly configured.")
    else:
        # Postgres
        try:
            pgsql_reply = (subprocess.Popen(["psql", "--version"], stdout=subprocess.PIPE).communicate()[0])
            pgsql_version = string.split(pgsql_reply)[2]
        except:
            pgsql_version = T("Unknown")
        try:
            import psycopg2
            psycopg_version = psycopg2.__version__
        except:
            psycopg_version = T("Not installed or incorrectly configured.")
    # Libraries
    try:
        import reportlab
        reportlab_version = reportlab.Version
    except:
        reportlab_version = T("Not installed or incorrectly configured.")
    try:
        import xlwt
        xlwt_version = xlwt.__VERSION__
    except:
        xlwt_version = T("Not installed or incorrectly configured.")
    return dict(
                python_version=python_version,
                sahana_version=sahana_version,
                web2py_version=web2py_version,
                sqlite_version=sqlite_version,
                mysql_version=mysql_version,
                mysqldb_version=mysqldb_version,
                pgsql_version=pgsql_version,
                psycopg_version=psycopg_version,
                reportlab_version=reportlab_version,
                xlwt_version=xlwt_version
                )

# -----------------------------------------------------------------------------
def help():
    """ Custom View """
    response.title = T("Help")
    return dict()

# -----------------------------------------------------------------------------
def privacy():
    """ Custom View """
    response.title = T("Privacy")
    return dict()

# -----------------------------------------------------------------------------
def contact():
    """
        Give the user options to contact the site admins.
        Either:
            An internal Support Requests database
        or:
            Custom View
    """

    if auth.is_logged_in() and settings.has_module("support"):
        # Provide an internal Support Requests ticketing system.
        prefix = "support"
        resourcename = "req"
        tablename = "%s_%s" % (prefix, resourcename)
        table = s3db[tablename]

        # Pre-processor
        def prep(r):
            if r.interactive:
                # Only Admins should be able to update ticket status
                status = table.status
                actions = table.actions
                if not auth.s3_has_role(ADMIN):
                    status.writable = False
                    actions.writable = False
                if r.method != "update":
                    status.readable = False
                    status.writable = False
                    actions.readable = False
                    actions.writable = False
            return True
        s3.prep = prep

        output = s3_rest_controller(prefix, resourcename)
        return output
    else:
        # Default: Simple Custom View
        response.title = T("Contact us")
        return dict()


# END =========================================================================
