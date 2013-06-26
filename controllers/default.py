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

    try:
        filename = request.args[0]
    except:
        session.error("Need to specify the file to download!")
        redirect(URL(f="index"))

    # Load the Model
    tablename = filename.split(".", 1)[0]
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

# =============================================================================
def index():
    """ Main Home Page """

    auth.settings.register_onvalidation = register_validation
    auth.configure_user_fields()

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
            if "." in page:
                # Remove extension
                page = page.split(".", 1)[0]
            if page in custom.__dict__:
                exec ("output = custom.%s()()" % page)
                return output
            elif page != "login":
                raise(HTTP(404, "Function not found: %s()" % page))
            else:
                output = custom.index()()
                return output
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
    has_module = settings.has_module
    if has_module("cms"):
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        query = (ltable.module == module) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = db(query).select(table.body,
                                limitby=(0, 1)).first()
        if item:
            item = DIV(XML(item.body))
        else:
            item = ""

    if has_module("cr"):
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
                 ["res", T("Received Shipments"), "inv", "recv"],
                ]

    # Change to (Mitigation)/Preparedness/Response/Recovery?
    menu_divs = {"facility": DIV(H3(T("Facilities")),
                                 _id = "facility_box",
                                 _class = "menu_box",
                                 ),
                 "sit": DIV(H3(T("Situation")),
                            _id = "menu_div_sit",
                            _class = "menu_div",
                            ),
                 "dec": DIV(H3(T("Decision")),
                            _id = "menu_div_dec",
                            _class = "menu_div",
                            ),
                 "res": DIV(H3(T("Response")),
                            _id = "menu_div_res",
                            _class = "menu_div",
                            ),
                 }

    for div, label, app, function in menu_btns:
        if has_module(app):
            # @ToDo: Also check permissions (e.g. for anonymous users)
            menu_divs[div].append(A(DIV(label,
                                        _class = "menu-btn-r"),
                                    _class = "menu-btn-l",
                                    _href = URL(app, function)
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

    # Check logged in AND permissions
    roles = session.s3.roles
    table = s3db.org_organisation
    has_permission = auth.s3_has_permission
    if AUTHENTICATED in roles and \
       has_permission("read", table):
        org_items = organisation()
        datatable_ajax_source = "/%s/default/organisation.aadata" % \
                                appname
        s3.actions = None
        response.view = "default/index.html"
        permission = auth.permission
        permission.controller = "org"
        permission.function = "site"
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

        if has_permission("create", table):
            create = A(T("Add Organization"),
                       _href = URL(c="org", f="organisation",
                                   args=["create"]),
                       _id = "add-btn",
                       _class = "action-btn",
                       _style = "margin-right: 10px;")
        else:
            create = ""
        org_box = DIV(H3(T("Organizations")),
                      create,
                      org_items,
                      _id = "org_box",
                      _class = "menu_box fleft"
                      )
    else:
        datatable_ajax_source = ""
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
                        P(XML(T("Registered users can %(login)s to access the system") % \
                              dict(login=B(T("login"))))))

    if settings.frontpage.rss:
        s3.external_stylesheets.append("http://www.google.com/uds/solutions/dynamicfeed/gfdynamicfeedcontrol.css")
        s3.scripts.append("http://www.google.com/jsapi?key=notsupplied-wizard")
        s3.scripts.append("http://www.google.com/uds/solutions/dynamicfeed/gfdynamicfeedcontrol.js")
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

    request = current.request
    get_vars = request.get_vars

    resource = current.s3db.resource("org_organisation")
    totalrows = resource.count()
    if "iDisplayLength" in get_vars:
        display_length = int(request.get_vars["iDisplayLength"])
    else:
        display_length = 10
    limit = 4 * display_length

    list_fields = ["id", "name"]
    filter, orderby, left = resource.datatable_filter(list_fields,
                                                        get_vars)
    resource.add_filter(filter)

    data = resource.fast_select(list_fields,
                                start=0,
                                limit=limit,
                                orderby=orderby,
                                left=left,
                                count=True,
                                represent=True)
    filteredrows = data["numrows"]
    rfields = data["rfields"]
    data = data["rows"]

    dt = S3DataTable(rfields, data)
    dt.defaultActionButtons(resource)
    current.response.s3.no_formats = True

    if request.extension == "html":
        items = dt.html(totalrows,
                        totalrows,
                        "org_dt",
                        dt_displayLength=display_length,
                        dt_ajax_url=URL(c="default",
                                        f="organisation",
                                        extension="aadata",
                                        vars={"id": "org_dt"},
                                        ),
                        dt_pagination="true",
                        )
    elif request.extension.lower() == "aadata":
        if "sEcho" in request.vars:
            echo = int(request.vars.sEcho)
        else:
            echo = None
        items = dt.json(totalrows,
                        filteredrows,
                        "org_dt",
                        echo)
    else:
        from gluon.http import HTTP
        raise HTTP(501, resource.ERROR.BAD_FORMAT)
    return items

# -----------------------------------------------------------------------------
def site():
    """
        @ToDo: Avoid redirect
    """

    try:
        site_id = request.args[0]
    except:
        raise HTTP(404)

    table = s3db.org_site
    record = db(table.site_id == site_id).select(table.instance_type,
                                                 limitby=(0, 1)).first()
    tablename = record.instance_type
    table = s3db.table(tablename)
    if table:
        query = (table.site_id == site_id)
        id = db(query).select(table.id,
                              limitby = (0, 1)).first().id
        cf = tablename.split("_", 1)
        redirect(URL(c = cf[0],
                     f = cf[1],
                     args = [id]))

# -----------------------------------------------------------------------------
def message():
    """ Show a confirmation screen """

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
    auth.settings.register_onvalidation = register_validation

    _table_user = auth.settings.table_user

    auth.settings.profile_onaccept = auth.s3_user_profile_onaccept

    self_registration = settings.get_security_self_registration()
    login_form = register_form = None

    if request.args:
        arg = request.args(0)
    else:
        arg = None

    # Check for template-specific customisations
    customize = settings.ui.get("customize_auth_user", None)
    if customize:
        customize(arg=arg)

    # Needs more work to integrate our form extensions
    #auth.settings.formstyle = s3_formstyle
    if arg == "login":
        title = response.title = T("Login")
        # @ToDo: move this code to /modules/s3/s3aaa.py:def login()?
        auth.messages.submit_button = T("Login")
        form = auth()
        #form = auth.login()
        login_form = form
    elif arg == "register":
        title = response.title = T("Register")
        # @ToDo: move this code to /modules/s3/s3aaa.py:def register()?
        if not self_registration:
            session.error = T("Registration not permitted")
            redirect(URL(f="index"))

        form = auth.register()
        register_form = form
        # Add client-side validation
        s3base.s3_register_validation()
    elif arg == "change_password":
        title = response.title = T("Change Password")
        form = auth()
        # Add client-side validation
        if s3.debug:
            s3.scripts.append("/%s/static/scripts/jquery.pstrength.2.1.0.js" % appname)
        else:
            s3.scripts.append("/%s/static/scripts/jquery.pstrength.2.1.0.min.js" % appname)
        s3.jquery_ready.append("$('.password:eq(1)').pstrength()")
    elif arg == "retrieve_password":
        title = response.title = T("Retrieve Password")
        form = auth()
    elif arg == "profile":
        title = response.title = T("User Profile")
        form = auth.profile()
    else:
        # logout
        title = ""
        form = auth()

    if form:
        if s3.crud.submit_style:
            form[0][-1][1][0]["_class"] = s3.crud.submit_style
        elif s3_formstyle == "bootstrap":
            form[0][-1][1][0]["_class"] = "btn btn-primary"

    # Use Custom Ext views
    # Best to not use an Ext form for login: can't save username/password in browser & can't hit 'Enter' to submit!
    #if request.args(0) == "login":
    #    response.title = T("Login")
    #    response.view = "auth/login.html"

    if settings.get_template() != "default":
        # Try a Custom View
        view = os.path.join(request.folder, "private", "templates",
                            settings.get_template(), "views", "user.html")
        if os.path.exists(view):
            try:
                # Pass view as file not str to work in compiled mode
                response.view = open(view, "rb")
            except IOError:
                from gluon.http import HTTP
                raise HTTP("404", "Unable to open Custom View: %s" % view)

    return dict(title=title,
                form=form,
                login_form=login_form,
                register_form=register_form,
                self_registration=self_registration)

# -----------------------------------------------------------------------------
def person():
    """
        Profile to show:
         - User Details
         - Person Details
         - Staff/Volunteer Record
         - Map Config
    """

    # Set to current user
    user_person_id  = str(s3_logged_in_person())
    if not request.args or request.args[0] != user_person_id:
        request.args = [str(user_person_id)]

    set_method = s3db.set_method

    # Custom Method for User
    def auth_profile_method(r, **attr):
        # Custom View
        response.view = "update.html"
        current.menu.breadcrumbs = None

        # RHeader for consistency
        rheader = attr.get("rheader", None)
        if callable(rheader):
            rheader = rheader(r)

        table = auth.settings.table_user
        tablename = table._tablename

        next = URL(c = "default",
                   f = "person",
                   args = [str(user_person_id), "user"])
        onaccept = lambda form: auth.s3_approve_user(form.vars),
        form = auth.profile(next = next,
                            onaccept = onaccept)

        return dict(title = T("User Profile"),
                    rheader = rheader,
                    form = form,
                    )

    set_method("pr", "person",
               method="user",
               action=auth_profile_method)

    # Custom Method for Contacts
    set_method("pr", "person",
               method="contacts",
               action=s3db.pr_contacts)

    #if settings.has_module("asset"):
    #    # Assets as component of people
    #    s3db.add_component("asset_asset",
    #                       pr_person="assigned_to_id")

    # Configure person table for personal mode
    tablename = "pr_person"
    table = s3db[tablename]

    s3.crud_strings[tablename].update(
        title_display = T("Personal Profile"),
        title_update = T("Personal Profile"))

    # Organisation-dependent Fields
    set_org_dependent_field = settings.set_org_dependent_field
    set_org_dependent_field("pr_person_details", "father_name")
    set_org_dependent_field("pr_person_details", "mother_name")
    set_org_dependent_field("pr_person_details", "affiliations")
    set_org_dependent_field("pr_person_details", "company")

    # CRUD pre-process
    def prep(r):
        if r.interactive and r.method != "import":
            if r.component:
                if r.component_name == "physical_description":
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

                elif r.component_name == "saved_search":
                    if r.method == "load":
                        if r.component_id:
                            table = db.pr_saved_search
                            record = db(table.id == r.component_id).select(table.url,
                                                                           limitby=(0, 1)
                                                                           ).first()
                            if record:
                                redirect(record.url)
                            else:
                                raise HTTP(404)

                elif r.component_name == "config":
                    _config = s3db.gis_config
                    s3db.gis_config_form_setup()
                    # Name will be generated from person's name.
                    #_config.name.readable = _config.name.writable = False
                    # Hide Location
                    #_config.region_location_id.readable = _config.region_location_id.writable = False

                    # OpenStreetMap config
                    s3db.add_component("auth_user_options",
                                       gis_config=dict(joinby="pe_id",
                                                       pkey="pe_id",
                                                       multiple=False)
                                       )
                    fields = ["default_location_id",
                              "zoom",
                              "lat",
                              "lon",
                              "projection_id",
                              "symbology_id",
                              "wmsbrowser_url",
                              "wmsbrowser_name",
                              "user_options.osm_oauth_consumer_key",
                              "user_options.osm_oauth_consumer_secret",
                              ]
                    crud_form = s3base.S3SQLCustomForm(*fields)
                    s3db.configure("gis_config", crud_form=crud_form)
            else:
                table = r.table
                table.pe_label.readable = False
                table.pe_label.writable = False
                table.missing.readable = False
                table.missing.writable = False
                table.age_group.readable = False
                table.age_group.writable = False
                # Assume volunteers only between 12-81
                table.date_of_birth.widget = S3DateWidget(past=972, future=-144)
            return True
        else:
            # Disable non-interactive & import
            return False
    s3.prep = prep

    # CRUD post-process
    def postp(r, output):
        if r.interactive and r.component:
            if r.component_name == "human_resource":
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('hrm_human_resource_start_date','hrm_human_resource_end_date')''')
            if r.component_name == "experience":
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('hrm_experience_start_date','hrm_experience_end_date')''')
            elif r.component_name == "saved_search" and r.method in (None, "search"):
                s3_action_buttons(r)
                s3.actions.append(
                    dict(url=URL(args=r.args + ["[id]", "load"]),
                         label=str(T("Load")),
                         _class="action-btn")
                )
            elif r.component_name == "asset":
                # Provide a link to assign a new Asset
                # @ToDo: Proper Widget to do this inline
                output["add_btn"] = A(T("Assign Asset"),
                                      _href=URL(c="asset", f="asset"),
                                      _id="add-btn",
                                      _class="action-btn")
        return output
    s3.postp = postp

    if settings.get_hrm_staff_experience() == "experience":
        experience_tab = (T("Experience"), "experience")
    else:
        experience_tab = None

    if settings.get_hrm_use_certificates():
        certificates_tab = (T("Certificates"), "certificate")
    else:
        certificates_tab = None

    if settings.get_hrm_use_credentials():
        credentials_tab = (T("Credentials"), "credential")
    else:
        credentials_tab = None

    if settings.get_hrm_use_description():
        description_tab = (T("Description"), "physical_description")
    else:
        description_tab = None

    if settings.get_hrm_use_education():
        education_tab = (T("Education"), "education")
    else:
        education_tab = None

    if settings.get_hrm_use_id():
        id_tab = (T("ID"), "identity")
    else:
        id_tab = None

    if settings.get_hrm_use_skills():
        skills_tab = (T("Skills"), "competency")
    else:
        skills_tab = None

    teams = settings.get_hrm_teams()
    if teams:
        teams_tab = (T(teams), "group_membership")
    else:
        teams_tab = None

    if settings.get_hrm_use_trainings():
        trainings_tab = (T("Trainings"), "training")
    else:
        trainings_tab = None

    if settings.get_search_save_widget():
        searches_tab = (T("Saved Searches"), "saved_search")
    else:
        searches_tab = None

    tabs = [(T("Person Details"), None),
            (T("User Account"), "user"),
            (T("Staff/Volunteer Record"), "human_resource"),
            id_tab,
            description_tab,
            (T("Address"), "address"),
            (T("Contacts"), "contacts"),
            education_tab,
            trainings_tab,
            certificates_tab,
            skills_tab,
            credentials_tab,
            experience_tab,
            teams_tab,
            #(T("Assets"), "asset"),
            (T("Map Options"), "config"),
            searches_tab,
            ]
    
    output = s3_rest_controller("pr", "person",
                                rheader = lambda r: \
                                    s3db.pr_rheader(r, tabs=tabs))
    return output

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
# About Sahana
def apath(path=""):
    """ Application path """

    from gluon.fileutils import up
    opath = up(request.folder)
    # @ToDo: This path manipulation is very OS specific.
    while path[:3] == "../": opath, path=up(opath), path[3:]
    return os.path.join(opath,path).replace("\\", "/")

def about():
    """
        The About page provides details on the software dependencies and
        versions available to this instance of Sahana Eden.
    """

    response.title = T("About")
    if settings.get_template() != "default":
        # Try a Custom View
        view = os.path.join(request.folder, "private", "templates",
                            settings.get_template(), "views", "about.html")
        if os.path.exists(view):
            try:
                # Pass view as file not str to work in compiled mode
                response.view = open(view, "rb")
            except IOError:
                from gluon.http import HTTP
                raise HTTP("404", "Unable to open Custom View: %s" % view)

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
            sqlite_version = sqlite3.version
        except:
            sqlite_version = T("Unknown")
    elif db_string[0].find("mysql") != -1:
        try:
            import MySQLdb
            mysqldb_version = MySQLdb.__revision__
        except:
            mysqldb_version = T("Not installed or incorrectly configured.")
            mysql_version = T("Unknown")
        else:
            #mysql_version = (subprocess.Popen(["mysql", "--version"], stdout=subprocess.PIPE).communicate()[0]).rstrip()[10:]
            con = MySQLdb.connect(host=settings.database.get("host", "localhost"),
                                  port=settings.database.get("port", None) or 3306,
                                  db=settings.database.get("database", "sahana"),
                                  user=settings.database.get("username", "sahana"),
                                  passwd=settings.database.get("password", "password")
                                  )
            cur = con.cursor()
            cur.execute("SELECT VERSION()")
            mysql_version = cur.fetchone()
    else:
        # Postgres
        try:
            import psycopg2
            psycopg_version = psycopg2.__version__
        except:
            psycopg_version = T("Not installed or incorrectly configured.")
            pgsql_version = T("Unknown")
        else:
            #pgsql_reply = (subprocess.Popen(["psql", "--version"], stdout=subprocess.PIPE).communicate()[0])
            #pgsql_version = string.split(pgsql_reply)[2]
            con = psycopg2.connect(host=settings.database.get("host", "localhost"),
                                   port=settings.database.get("port", None) or 5432,
                                   database=settings.database.get("database", "sahana"),
                                   user=settings.database.get("username", "sahana"),
                                   password=settings.database.get("password", "password")
                                   )
            cur = con.cursor()
            cur.execute("SELECT version()")
            pgsql_version = cur.fetchone()

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

    if settings.get_template() != "default":
        # Try a Custom View
        view = os.path.join(request.folder, "private", "templates",
                            settings.get_template(), "views", "help.html")
        if os.path.exists(view):
            try:
                # Pass view as file not str to work in compiled mode
                response.view = open(view, "rb")
            except IOError:
                from gluon.http import HTTP
                raise HTTP("404", "Unable to open Custom View: %s" % view)

    response.title = T("Help")
    return dict()

# -----------------------------------------------------------------------------
def privacy():
    """ Custom View """

    if settings.get_template() != "default":
        # Try a Custom View
        view = os.path.join(request.folder, "private", "templates",
                            settings.get_template(), "views", "privacy.html")
        if os.path.exists(view):
            try:
                # Pass view as file not str to work in compiled mode
                response.view = open(view, "rb")
            except IOError:
                from gluon.http import HTTP
                raise HTTP("404", "Unable to open Custom View: %s" % view)

    response.title = T("Privacy")
    return dict()

# -----------------------------------------------------------------------------
def tos():
    """ Custom View """

    if settings.get_template() != "default":
        # Try a Custom View
        view = os.path.join(request.folder, "private", "templates",
                            settings.get_template(), "views", "tos.html")
        if os.path.exists(view):
            try:
                # Pass view as file not str to work in compiled mode
                response.view = open(view, "rb")
            except IOError:
                from gluon.http import HTTP
                raise HTTP("404", "Unable to open Custom View: %s" % view)

    response.title = T("Terms of Service")
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
        template = settings.get_template()
        if template != "default":
            # Try a Custom Page
            controller = "applications.%s.private.templates.%s.controllers" % \
                                (appname, template)
            try:
                exec("import %s as custom" % controller) in globals(), locals()
            except ImportError, e:
                # No Custom Page available, try a custom view
                pass
            else:
                if "contact" in custom.__dict__:
                    output = custom.contact()()
                    return output

            view = os.path.join(request.folder, "private", "templates",
                                template, "views", "contact.html")
            if os.path.exists(view):
                try:
                    # Pass view as file not str to work in compiled mode
                    response.view = open(view, "rb")
                except IOError:
                    from gluon.http import HTTP
                    raise HTTP("404", "Unable to open Custom View: %s" % view)

                response.title = T("Contact us")
    return dict()

# END =========================================================================
