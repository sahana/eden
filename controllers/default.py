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
    if "_" in tablename:
        table = s3db.table(tablename)

    return response.download(request, db)

# =============================================================================
def register_validation(form):
    """ Validate the fields in registration form """

    form_vars = form.vars

    # Mobile Phone
    mobile = form_vars.get("mobile")
    if mobile:
        import re
        regex = re.compile(single_phone_number_pattern)
        if not regex.match(mobile):
            form.errors.mobile = T("Invalid phone number")
    elif settings.get_auth_registration_mobile_phone_mandatory():
        form.errors.mobile = T("Phone number is required")

    # Home Phone
    home = form_vars.get("home")
    if home:
        import re
        regex = re.compile(single_phone_number_pattern)
        if not regex.match(home):
            form.errors.home = T("Invalid phone number")

    org = settings.get_auth_registration_organisation_id_default()
    if org:
        # Add to default organisation
        form_vars.organisation_id = org

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
        except ImportError:
            # No Custom Page available, continue with the default
            page = "private/templates/%s/controllers.py" % \
                        settings.get_template()
            current.log.warning("File not loadable",
                                "%s, %s" % (page, sys.exc_info()[1]))
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
        except ImportError:
            # No Custom Page available, continue with the default
            # @ToDo: cache this result in session
            current.log.warning("Custom homepage cannot be loaded",
                                sys.exc_info()[1])
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
                ((ltable.resource == None) | (ltable.resource == "index")) & \
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
        datatable_ajax_source = "/%s/default/organisation.aadata" % appname
        s3.actions = None
        response.view = "default/index.html"
        permission = auth.permission
        permission.controller = "org"
        permission.function = "site"
        permitted_facilities = auth.permitted_facilities(redirect_on_error=False)
        if permitted_facilities:
            facilities = s3db.org_SiteRepresent().bulk(permitted_facilities,
                                                       include_blank=False)
            facility_list = [(fac, facilities[fac]) for fac in facilities]
            facility_list = sorted(facility_list, key=lambda fac: fac[1])
            facility_opts = [OPTION(fac[1], _value=fac[0])
                             for fac in facility_list]
            manage_facility_box = DIV(H3(T("Manage Your Facilities")),
                                      SELECT(_id = "manage_facility_select",
                                             _style = "max-width:360px",
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
 $('#manage_facility_btn').attr('href',S3.Ap.concat('/default/site/',$('#manage_facility_select').val()))})
$('#manage_facility_btn').click(function(){
if ( ($('#manage_facility_btn').attr('href').toString())===S3.Ap.concat('/default/site/None') )
{$("#manage_facility_box").append("<div class='alert alert-error'>%s</div>")
return false}})''' % (T("Please Select a Facility")))
        else:
            manage_facility_box = ""

        if has_permission("create", table):
            create = A(T("Create Organization"),
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
        auth.messages.submit_button = T("Login")
        login_form = auth.login(inline=True)
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

    output = dict(title = title,
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

    if get_vars.tour:
        output = s3db.tour_builder(output)

    return output
# -----------------------------------------------------------------------------
def organisation():
    """
        Function to handle pagination for the org list on the homepage
    """

    representation = request.extension

    resource = s3db.resource("org_organisation")
    totalrows = resource.count()
    display_start = int(get_vars.displayStart) if get_vars.displayStart else 0
    display_length = int(get_vars.pageLength) if get_vars.pageLength else 10
    limit = 4 * display_length

    list_fields = ["id", "name"]
    default_orderby = orderby = "org_organisation.name asc"
    if representation == "aadata":
        query, orderby, left = resource.datatable_filter(list_fields, get_vars)
        if orderby is None:
            orderby = default_orderby
        if query:
            resource.add_filter(query)
    
    data = resource.select(list_fields,
                           start=display_start,
                           limit=limit,
                           orderby=orderby,
                           count=True,
                           represent=True)
    filteredrows = data["numrows"]
    rfields = data["rfields"]
    data = data["rows"]

    dt = S3DataTable(rfields, data)
    dt.defaultActionButtons(resource)
    s3.no_formats = True

    if representation == "html":
        items = dt.html(totalrows,
                        totalrows,
                        "org_dt",
                        dt_ajax_url=URL(c="default",
                                        f="organisation",
                                        extension="aadata",
                                        vars={"id": "org_dt"},
                                        ),
                        dt_pageLength=display_length,
                        dt_pagination="true",
                        )
    elif representation == "aadata":
        draw = request.get_vars.get("draw")
        if draw:
            draw = int(draw)
        items = dt.json(totalrows,
                        filteredrows,
                        "org_dt",
                        draw)
    else:
        from gluon.http import HTTP
        raise HTTP(501, ERROR.BAD_FORMAT)
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

    val = get_vars.get("val", True)
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

    auth_settings = auth.settings
    utable = auth_settings.table_user

    arg = request.args(0)
    if arg == "verify_email":
        # Ensure we use the user's language
        key = request.args[-1]
        query = (utable.registration_key == key)
        user = db(query).select(utable.language,
                                limitby=(0, 1)).first()
        if not user:
            redirect(auth_settings.verify_email_next)
        session.s3.language = user.language

    auth_settings.on_failed_authorization = URL(f="error")

    auth.configure_user_fields()
    auth_settings.profile_onaccept = auth.s3_user_profile_onaccept
    auth_settings.register_onvalidation = register_validation

    self_registration = settings.get_security_self_registration()
    login_form = register_form = None

    # Check for template-specific customisations
    customise = settings.customise_auth_user_controller
    if customise:
        customise(arg=arg)

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
        form = register_form = auth.register()

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

    elif arg == "options.s3json":
        # Used when adding organisations from registration form
        return s3_rest_controller(prefix="auth", resourcename="user")

    else:
        # logout or verify_email
        title = ""
        form = auth()

    if form:
        if s3.crud.submit_style:
            form[0][-1][1][0]["_class"] = s3.crud.submit_style

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
    user_person_id = str(s3_logged_in_person())

    # When request.args = [], set it as user_person_id.
    # When it is not an ajax request and the first argument is not user_person_id, set it.
    # If it is an json request, leave the arguments unmodified.
    if not request.args or (request.args[0] != user_person_id and \
                            request.args[-1] != "options.s3json" and \
                            request.args[-1] != "validate.json"
                            ):
        request.args = [user_person_id]

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
                   args = [user_person_id, "user"])
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
    #    s3db.add_components("pr_person", asset_asset="assigned_to_id")

    # CRUD pre-process
    def prep(r):
        if r.method in ("options", "validate"):
            return True
        if r.interactive and r.method != "import":
            # Load default model to override CRUD Strings
            tablename = "pr_person"
            table = s3db[tablename]

            # Users can not delete their own person record
            r.resource.configure(deletable=False)

            s3.crud_strings[tablename].update(
                title_display = T("Personal Profile"),
                title_update = T("Personal Profile"))

            # Organisation-dependent Fields
            set_org_dependent_field = settings.set_org_dependent_field
            set_org_dependent_field("pr_person_details", "father_name")
            set_org_dependent_field("pr_person_details", "mother_name")
            set_org_dependent_field("pr_person_details", "affiliations")
            set_org_dependent_field("pr_person_details", "company")

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

                elif r.component_name == "config":
                    ctable = s3db.gis_config
                    s3db.gis_config_form_setup()

                    # Create forms use this
                    # (update forms are in gis/config())
                    fields = ["name",
                              "pe_default",
                              "default_location_id",
                              "zoom",
                              "lat",
                              "lon",
                              #"projection_id",
                              #"symbology_id",
                              #"wmsbrowser_url",
                              #"wmsbrowser_name",
                              ]
                    osm_table = s3db.gis_layer_openstreetmap
                    openstreetmap = db(osm_table.deleted == False).select(osm_table.id,
                                                                          limitby=(0, 1))
                    if openstreetmap:
                        # OpenStreetMap config
                        s3db.add_components("gis_config",
                                            auth_user_options={"joinby": "pe_id",
                                                               "pkey": "pe_id",
                                                               "multiple": False,
                                                              },
                                           )
                        fields += ["user_options.osm_oauth_consumer_key",
                                   "user_options.osm_oauth_consumer_secret",
                                   ]
                    crud_form = s3base.S3SQLCustomForm(*fields)
                    list_fields = ["name",
                                   "pe_default",
                                   ]
                    s3db.configure("gis_config",
                                   crud_form=crud_form,
                                   insertable=False,
                                   list_fields = list_fields,
                                   )
            else:
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
            if r.component_name == "identity":
                # Set the minimum valid_until to the same as the valid_from
                s3.jquery_ready.append(
'''S3.start_end_date('pr_identity_valid_from','pr_identity_valid_until')''')
            if r.component_name == "experience":
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('hrm_experience_start_date','hrm_experience_end_date')''')
            elif r.component_name == "config":
                update_url = URL(c="gis", f="config",
                                 args="[id]")
                s3_action_buttons(r, update_url=update_url)
                s3.actions.append(
                    dict(url=URL(c="gis", f="index",
                                 vars={"config":"[id]"}),
                         label=str(T("Show")),
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
            #(T("My Subscriptions"), "subscription"),
            (T("My Maps"), "config"),
            ]

    output = s3_rest_controller("pr", "person",
                                rheader = lambda r: \
                                    s3db.pr_rheader(r, tabs=tabs))
    return output

# -----------------------------------------------------------------------------
def group():
    """
        RESTful CRUD controller
        - needed when group add form embedded in default/person
        - only create method is allowed, when opened in a inline form.
    """

    # Check if it is called from a inline form
    if auth.permission.format != "popup":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "create":
            return False
        return True
    s3.prep = prep

    output = s3_rest_controller("pr", "group")

    return output

# -----------------------------------------------------------------------------
def skill():
    """
        RESTful CRUD controller
        - needed when skill add form embedded in default/person
        - only create method is allowed, when opened in a inline form.
    """

    # Check if it is called from a inline form
    if auth.permission.format != "popup":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "create":
            return False
        return True
    s3.prep = prep

    output = s3_rest_controller("hrm", "skill")

    return output

# -----------------------------------------------------------------------------
def facebook():
    """ Login using Facebook """

    channel = s3db.msg_facebook_login()

    if not channel:
        redirect(URL(f="user", args=request.args, vars=get_vars))

    from s3oauth import FaceBookAccount
    auth.settings.login_form = FaceBookAccount(channel)
    form = auth()

    return dict(form=form)

# -----------------------------------------------------------------------------
def google():
    """ Login using Google """

    channel = settings.get_auth_google()

    if not channel:
        redirect(URL(f="user", args=request.args, vars=get_vars))

    from s3oauth import GooglePlusAccount
    auth.settings.login_form = GooglePlusAccount(channel)
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
    if db_string.find("sqlite") != -1:
        try:
            import sqlite3
            sqlite_version = sqlite3.version
        except:
            sqlite_version = T("Unknown")
    elif db_string.find("mysql") != -1:
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
def video():
    """ Custom View """

    if settings.get_template() != "default":
        # Try a Custom View
        view = os.path.join(request.folder, "private", "templates",
                            settings.get_template(), "views", "video.html")
        if os.path.exists(view):
            try:
                # Pass view as file not str to work in compiled mode
                response.view = open(view, "rb")
            except IOError:
                from gluon.http import HTTP
                raise HTTP("404", "Unable to open Custom View: %s" % view)

    response.title = T("Video Tutorials")
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

        # Try a Custom View
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

    if settings.has_module("cms"):
        # Use CMS
        return s3db.cms_index("default", "contact", page_name=T("Contact Us"))

    # Just use default HTML View
    return dict()

# -----------------------------------------------------------------------------
def load_all_models():
    """
        Controller to load all models in web browser
        - to make it easy to debug in Eclipse
    """

    s3db.load_all_models()
    return "ok"

# -----------------------------------------------------------------------------
def audit():
    """
        RESTful CRUD Controller for Audit Logs
        - used e.g. for Site Activity
    """

    return s3_rest_controller("s3", "audit")

# -----------------------------------------------------------------------------
def get_settings():
    """
       Function to respond to get requests. Requires admin permissions
    """

    # Check if the request has a valid authorization header with admin cred.
    if not auth.s3_has_role("ADMIN"):
        auth.permission.format = None
        auth.permission.fail()

    elif not settings.get_base_allow_testing():
        raise(HTTP("405", "Testing not allowed"))

    else:
        arg = request.args(0)

        # Ex. request /get_settings/deployment_settings/template
        if arg == "deployment_settings":
            asked = request.args[1:]
            return_settings = {}

            for setting in asked:
                func_name = "get_%s" % setting
                function = getattr(settings, func_name)
                # Ex. value of function - settings.get_template()
                try:
                    value = function()
                except TypeError:
                    continue

                return_settings[setting] = value

            return response.json(return_settings)

        raise(HTTP("400", "Invalid/Missing argument"))

# END =========================================================================
