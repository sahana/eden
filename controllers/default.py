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
def register_onaccept(form):
    """ Tasks to be performed after a new user registers """

    # Add newly-registered users to Person Registry, add 'Authenticated' role
    # If Organisation is provided, then: add HRM record & add to 'Org_X_Access' role
    person_id = auth.s3_register(form)

    if form.vars.organisation_id and not settings.get_hrm_show_staff():
        # Convert HRM record to a volunteer
        htable = s3db.hrm_human_resource
        query = (htable.person_id == person_id)
        db(query).update(type=2)

    # Add to required roles:
    roles = settings.get_auth_registration_roles()
    if roles or settings.has_module("delphi"):
        utable = auth.settings.table_user
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        query = (ptable.id == person_id) & \
                (ptable.pe_id == ltable.pe_id) & \
                (ltable.user_id == utable.id)
        user = db(query).select(utable.id,
                                ltable.user_id,
                                limitby=(0, 1)).first()

    if roles:
        gtable = auth.settings.table_group
        mtable = auth.settings.table_membership
        query = (gtable.uuid.belongs(roles))
        rows = db(query).select(gtable.id)
        for role in rows:
            mtable.insert(user_id=user[ltable._tablename].user_id,
                          group_id=role.id)

    if settings.has_module("delphi"):
        # Add user as a participant of the default problem group
        table = s3db.delphi_group
        query = (table.uuid == "DEFAULT")
        group = db(query).select(table.id,
                                 limitby=(0, 1)).first()
        if group:
            table = s3db.delphi_membership
            table.insert(group_id=group.id,
                         user_id=user[utable._tablename].id,
                         status=3)

# -----------------------------------------------------------------------------
auth.settings.register_onvalidation = register_validation
auth.settings.register_onaccept = register_onaccept

_table_user = auth.settings.table_user
_table_user.first_name.label = T("First Name")
_table_user.first_name.comment = SPAN("*", _class="req")
_table_user.last_name.label = T("Last Name")
if settings.get_L10n_mandatory_lastname():
    _table_user.last_name.comment = SPAN("*", _class="req")
_table_user.email.label = T("E-mail")
_table_user.email.comment = SPAN("*", _class="req")
_table_user.password.comment = SPAN("*", _class="req")
_table_user.language.label = T("Language")
_table_user.language.comment = DIV(_class="tooltip",
                                   _title="%s|%s" % (T("Language"),
                                                     T("The language you wish the site to be displayed in.")))
_table_user.language.represent = lambda opt: s3_languages.get(opt, UNKNOWN_OPT)

# Organisation widget for use in Registration Screen
# NB User Profile is only editable by Admin - using User Management
organisation_represent = s3db.org_organisation_represent
org_widget = IS_ONE_OF(db, "org_organisation.id",
                       organisation_represent,
                       orderby="org_organisation.name",
                       sort=True)
if settings.get_auth_registration_organisation_mandatory():
    _table_user.organisation_id.requires = org_widget
else:
    _table_user.organisation_id.requires = IS_NULL_OR(org_widget)

# For the User Profile:
_table_user.utc_offset.comment = DIV(_class="tooltip",
                                     _title="%s|%s" % (auth.messages.label_utc_offset,
                                                       auth.messages.help_utc_offset))
_table_user.organisation_id.represent = organisation_represent
_table_user.organisation_id.comment = DIV(_class="tooltip",
                                          _title="%s|%s|%s" % (T("Organization"),
                                                               T("The default Organization for whom you are acting."),
                                                               T("This setting can only be controlled by the Administrator.")))

org_site_represent = s3db.org_site_represent
_table_user.site_id.represent = org_site_represent
_table_user.site_id.comment = DIV(_class="tooltip",
                                  _title="%s|%s|%s" % (T("Facility"),
                                                       T("The default Facility for which you are acting."),
                                                       T("This setting can only be controlled by the Administrator.")))

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
            pass
        except ImportError:
            # No Custom Page available, continue with the default
            page = "private/templates/%s/controllers.py" % \
                        settings.get_template()
            s3base.s3_debug("File not loadable: %s" % page)
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
            pass
        except ImportError:
            # No Custom Page available, continue with the default
            # @ToDo: cache this result - at least in session, ideally in class startup
            pass
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
                ["facility", SHELTERS, "cr", "shelter"],
                ["facility", T("Warehouses"), "inv", "warehouse"],
                ["facility", T("Hospitals"), "hms", "hospital"],
                ["facility", T("Offices"), "org", "office"],
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
                ["res", T("Activities"), "project", "activity"],
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
    if AUTHENTICATED in session.s3.roles and \
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
                                    _class = "menu_box fleft")
                s3.jquery_ready.append( """
$('#manage_facility_select').change(function() {
    $('#manage_facility_btn').attr('href', S3.Ap.concat('/default/site/',  $('#manage_facility_select').val()));
})""" )
            else:
                manage_facility_box = DIV()

        org_box = DIV( H3(T("Organizations")),
                       A(T("Add Organization"),
                          _href = URL(c="org", f="organisation",
                                      args=["create"]),
                          _id = "add-btn",
                          _class = "action-btn",
                          _style = "margin-right: 10px;"),
                        org_items["items"],
                        _id = "org_box",
                        _class = "menu_box fleft"
                        )
    else:
        manage_facility_box = ""
        org_box = ""

    # @ToDo: Replace this with an easily-customisable section on the homepage
    #settings = db(db.s3_setting.id == 1).select(limitby=(0, 1)).first()
    #if settings:
    #    admin_name = settings.admin_name
    #    admin_email = settings.admin_email
    #    admin_tel = settings.admin_tel
    #else:
    #    # db empty and prepopulate is false
    #    admin_name = T("Sahana Administrator").xml(),
    #    admin_email = "support@Not Set",
    #    admin_tel = T("Not Set").xml(),

    # Login/Registration forms
    self_registration = settings.get_security_self_registration()
    registered = False
    login_form = None
    login_div = None
    register_form = None
    register_div = None
    if AUTHENTICATED not in session.s3.roles:
        # This user isn't yet logged-in
        if request.cookies.has_key("registered"):
            # This browser has logged-in before
            registered = True

        if self_registration:
            # Provide a Registration box on front page
            request.args = ["register"]
            if settings.get_terms_of_service():
                auth.messages.submit_button = T("I accept. Create my account.")
            else:
                auth.messages.submit_button = T("Register")
            register_form = auth()
            register_div = DIV(H3(T("Register")),
                               P(XML(T("If you would like to help, then please %(sign_up_now)s") % \
                                        dict(sign_up_now=B(T("sign-up now"))))))

             # Add client-side validation
            s3base.s3_register_validation()

            if s3.debug:
                s3.scripts.append("/%s/static/scripts/jquery.validate.js" % appname)
            else:
                s3.scripts.append("/%s/static/scripts/jquery.validate.min.js" % appname)
            if request.env.request_method == "POST":
                post_script = """// Unhide register form
    $('#register_form').removeClass('hide');
    // Hide login form
    $('#login_form').addClass('hide');"""
            else:
                post_script = ""
            register_script = """
    // Change register/login links to avoid page reload, make back button work.
    $('#register-btn').attr('href', '#register');
    $('#login-btn').attr('href', '#login');
    %s
    // Redirect Register Button to unhide
    $('#register-btn').click(function() {
        // Unhide register form
        $('#register_form').removeClass('hide');
        // Hide login form
        $('#login_form').addClass('hide');
    });

    // Redirect Login Button to unhide
    $('#login-btn').click(function() {
        // Hide register form
        $('#register_form').addClass('hide');
        // Unhide login form
        $('#login_form').removeClass('hide');
    });""" % post_script
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
                             "{title: '%s',\n" % feed["title"],
                             "url: '%s'}" % feed["url"]))
            # Don't add a trailing comma for old IEs
            if counter != len(settings.frontpage.rss):
                feeds += ",\n"
        feed_control = "".join(("""
function LoadDynamicFeedControl() {
  var feeds = [
    """, feeds, """
  ];
  var options = {
    // milliseconds before feed is reloaded (5 minutes)
    feedCycleTime : 300000,
    numResults : 5,
    stacked : true,
    horizontal : false,
    title : '""", str(T("News")), """'
  };
  new GFdynamicFeedControl(feeds, 'feed-control', options);
}
// Load the feeds API and set the onload callback.
google.load('feeds', '1');
google.setOnLoadCallback(LoadDynamicFeedControl);"""))
        s3.js_global.append( feed_control )

    return dict(title = title,
                item = item,

                sit_dec_res_box = sit_dec_res_box,
                facility_box = facility_box,
                manage_facility_box = manage_facility_box,
                org_box = org_box,

                r = None, # Required for dataTable to work
                datatable_ajax_source = datatable_ajax_source,
                #admin_name=admin_name,
                #admin_email=admin_email,
                #admin_tel=admin_tel,
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

    table = db.org_organisation
    table.id.label = T("Organization")
    table.id.represent = organisation_represent

    s3.dataTable_sPaginationType = "two_button"
    s3.dataTable_sDom = "rtip" #"frtip" - filter broken
    s3.dataTable_iDisplayLength = 25

    s3mgr.configure("org_organisation",
                    listadd = False,
                    addbtn = True,
                    super_entity = db.pr_pentity,
                    linkto = "/%s/org/organisation/%s" % (appname,
                                                          "%s"),
                    list_fields = ["id",])

    return s3_rest_controller("org", "organisation")
# -----------------------------------------------------------------------------
def site():
    """
        @todo: Avoid redirect
    """
    s3mgr.load("org_site")
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
def user_profile_onaccept(form):
    """ Update the UI locale from user profile """

    if form.vars.language:
        session.s3.language = form.vars.language
    return

# -----------------------------------------------------------------------------
def user():
    """ Auth functions based on arg. See gluon/tools.py """

    auth.settings.on_failed_authorization = URL(f="error")

    _table_user = auth.settings.table_user
    if request.args and request.args(0) == "profile":
        #_table_user.organisation.writable = False
        _table_user.utc_offset.readable = True
        _table_user.utc_offset.writable = True

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

    auth.settings.profile_onaccept = user_profile_onaccept

    self_registration = settings.get_security_self_registration()

    login_form = register_form = None
    if request.args and request.args(0) == "login":
        auth.messages.submit_button = T("Login")
        form = auth()
        login_form = form
        if s3.crud.submit_style:
            form[0][-1][1][0]["_class"] = s3.crud.submit_style
    elif request.args and request.args(0) == "register":
        if not self_registration:
            session.error = T("Registration not permitted")
            redirect(URL(f="index"))
        if settings.get_terms_of_service():
            auth.messages.submit_button = T("I accept. Create my account.")
        else:
            auth.messages.submit_button = T("Register")
        # Default the profile language to the one currently active
        _table_user.language.default = T.accepted_language
        form = auth()
        register_form = form
        # Add client-side validation
        s3base.s3_register_validation()
    elif request.args and request.args(0) == "change_password":
        form = auth()
    elif request.args and request.args(0) == "profile":
        if settings.get_auth_openid():
            form = DIV(form, openid_login_form.list_user_openids())
        else:
            form = auth()
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
        # Retrieve Password
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

    auth.settings.login_form = s3base.FaceBookAccount()
    form = auth()

    return dict(form=form)

# -----------------------------------------------------------------------------
def google():
    """ Login using Google """

    if not auth.settings.google:
        redirect(URL(f="user", args=request.args, vars=request.vars))

    auth.settings.login_form = s3base.GooglePlusAccount()
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
