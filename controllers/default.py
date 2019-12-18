# -*- coding: utf-8 -*-
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
        # No legitimate interactive request comes here without a filename,
        # so this hits mainly non-interactive clients, and those do not
        # recognize an error condition from a HTTP 303 => better to raise
        # a proper error than to redirect:
        raise HTTP(400, "No file specified")
        #session.error = T("Need to specify the file to download!")
        #redirect(URL(f="index"))

    # Check Permissions
    tablename = filename.split(".", 1)[0]
    if "_" in tablename:
        # Load the Model
        table = s3db.table(tablename)
        if table and not auth.s3_has_permission("read", tablename):
            auth.permission.fail()

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

    org = settings.get_auth_registration_organisation_default()
    if org:
        # Add to default organisation
        form_vars.organisation_id = org

    return

# =============================================================================
def index():
    """ Main Home Page """

    auth.settings.register_onvalidation = register_validation
    auth.configure_user_fields()

    current.menu.oauth = S3MainMenu.menu_oauth()

    page = None
    if len(request.args):
        # Use the first non-numeric argument as page name
        # (RESTful custom controllers may have record IDs in Ajax URLs)
        for arg in request.args:
            pname = arg.split(".", 1)[0] if "." in arg else arg
            if not pname.isdigit():
                page = pname
                break

    # Module name for custom controllers
    name = "controllers"

    custom = None
    templates = settings.get_template()

    if page:
        # Go to a custom page,
        # - args[0] = name of the class in /modules/templates/<template>/controllers.py
        # - other args & vars passed through
        if not isinstance(templates, (tuple, list)):
            templates = (templates,)
        for template in templates[::-1]:
            package = "applications.%s.modules.templates.%s" % (appname, template)
            try:
                custom = getattr(__import__(package, fromlist=[name]), name)
            except (ImportError, AttributeError):
                # No Custom Page available, continue with the default
                #page = "modules/templates/%s/controllers.py" % template
                #current.log.warning("File not loadable",
                #                    "%s, %s" % (page, sys.exc_info()[1]))
                continue
            else:
                if hasattr(custom, page):
                    controller = getattr(custom, page)()
                elif page != "login":
                    raise HTTP(404, "Function not found: %s()" % page)
                else:
                    controller = custom.index()
                output = controller()
                return output

    elif templates != "default":
        # Try a Custom Homepage
        if not isinstance(templates, (tuple, list)):
            templates = (templates,)
        for template in templates[::-1]:
            package = "applications.%s.modules.templates.%s" % (appname, template)
            try:
                custom = getattr(__import__(package, fromlist=[name]), name)
            except (ImportError, AttributeError):
                # No Custom Page available, continue with the next option, or default
                # @ToDo: cache this result in session
                #import sys
                #current.log.warning("Custom homepage cannot be loaded",
                                    #sys.exc_info()[1])
                continue
            else:
                if hasattr(custom, "index"):
                    output = custom.index()()
                    return output

    # Default Homepage
    title = settings.get_system_name()
    response.title = title

    # CMS Contents for homepage
    item = ""
    has_module = settings.has_module
    if has_module("cms"):
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        query = (ltable.module == module) & \
                ((ltable.resource == None) | (ltable.resource == "index")) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = db(query).select(table.body, limitby=(0, 1)).first()
        if item:
            item = DIV(XML(item.body))
        else:
            item = ""

    # Menu boxes
    from s3layouts import S3HomepageMenuLayout as HM

    sit_menu = HM("Situation Awareness")(
        HM("Map", c="gis", f="index", icon="map-marker"),
        HM("Incidents", c="event", f="incident_report", icon="incident"),
        HM("Alerts", c="cap", f="alert", icon="alert"),
        HM("Assessments", c="survey", f="series", icon="assessment"),
    )
    org_menu = HM("Who is doing What and Where")(
        HM("Organizations", c="org", f="organisation", icon="organisation"),
        HM("Facilities", c="org", f="facility", icon="facility"),
        HM("Activities", c="project", f="activity", icon="activity"),
        HM("Projects", c="project", f="project", icon="project"),
    )
    res_menu = HM("Manage Resources")(
        HM("Staff", c="hrm", f="staff", t="hrm_human_resource", icon="staff"),
        HM("Volunteers", c="vol", f="volunteer", t="hrm_human_resource", icon="volunteer"),
        HM("Relief Goods", c="inv", f="inv_item", icon="goods"),
        HM("Assets", c="asset", f="asset", icon="asset"),
    )
    aid_menu = HM("Manage Aid")(
        HM("Requests", c="req", f="req", icon="request"),
        HM("Commitments", c="req", f="commit", icon="commit"),
        HM("Sent Shipments", c="inv", f="send", icon="shipment"),
        HM("Received Shipments", c="inv", f="recv", icon="delivery"),
    )

    # @todo: re-integrate or deprecate (?)
    #if has_module("cr"):
    #    table = s3db.cr_shelter
    #    SHELTERS = s3.crud_strings["cr_shelter"].title_list
    #else:
    #    SHELTERS = ""
    #facility_box = HM("Facilities", _id="facility_box")(
    #    HM("Facilities", c="org", f="facility"),
    #    HM("Hospitals", c="hms", f="hospital"),
    #    HM("Offices", c="org", f="office"),
    #    HM(SHELTERS, c="cr", f="shelter"),
    #    HM("Warehouses", c="inv", f="warehouse"),
    #    HM("Map", c="gis", f="index",
    #       icon="/%s/static/img/map_icon_128.png" % appname,
    #       ),
    #)

    # Check logged in AND permissions
    roles = session.s3.roles
    table = s3db.org_organisation
    has_permission = auth.s3_has_permission
    AUTHENTICATED = auth.get_system_roles().AUTHENTICATED
    if AUTHENTICATED in roles and has_permission("read", table):

        org_items = organisation()
        datatable_ajax_source = "/%s/default/organisation.aadata" % appname

        # List of Organisations
        if has_permission("create", table):
            create = A(T("Create Organization"),
                       _href = URL(c = "org",
                                   f = "organisation",
                                   args = ["create"],
                                   ),
                       _id = "add-org-btn",
                       _class = "action-btn",
                       )
        else:
            create = ""
        org_box = DIV(create,
                      H3(T("Organizations")),
                      org_items,
                      _id = "org-box",
                      _class = "menu-box"
                      )

        s3.actions = None
        response.view = "default/index.html"

        # Quick Access Box for Sites
        permission = auth.permission
        permission.controller = "org"
        permission.function = "site"
        permitted_facilities = auth.permitted_facilities(redirect_on_error=False)

        if permitted_facilities:
            facilities = s3db.org_SiteRepresent().bulk(permitted_facilities,
                                                       include_blank=False,
                                                       )
            facility_list = [(fac, facilities[fac]) for fac in facilities]
            facility_list = sorted(facility_list, key=lambda fac: fac[1])
            facility_opts = [OPTION(fac[1], _value=fac[0])
                             for fac in facility_list]

            manage_facility_box = DIV(H3(T("Manage Your Facilities")),
                                      SELECT(_id = "manage-facility-select",
                                             *facility_opts
                                             ),
                                      A(T("Go"),
                                        _href = URL(c="default", f="site",
                                                    args=[facility_list[0][0]],
                                                    ),
                                        _id = "manage-facility-btn",
                                        _class = "action-btn"
                                        ),
                                      _id = "manage-facility-box",
                                      _class = "menu-box"
                                      )

            s3.jquery_ready.append('''$('#manage-facility-select').change(function(){
 $('#manage-facility-btn').attr('href',S3.Ap.concat('/default/site/',$('#manage-facility-select').val()))})
$('#manage-facility-btn').click(function(){
if (($('#manage-facility-btn').attr('href').toString())===S3.Ap.concat('/default/site/None'))
{$("#manage-facility-box").append("<div class='alert alert-error'>%s</div>")
return false}})''' % (T("Please Select a Facility")))

        else:
            manage_facility_box = ""

    else:
        datatable_ajax_source = ""
        manage_facility_box = ""
        org_box = ""

    # Login/Registration forms
    self_registration = settings.get_security_registration_visible()
    registered = False
    login_form = None
    login_div = None
    register_form = None
    register_div = None
    if AUTHENTICATED not in roles:
        # This user isn't yet logged-in
        if "registered" in request.cookies:
            # This browser has logged-in before
            registered = True

        # Provide a login box on front page
        auth.messages.submit_button = T("Login")
        login_form = auth.login(inline=True)
        login_div = DIV(H3(T("Login")),
                        P(XML(T("Registered users can %(login)s to access the system") % \
                              dict(login=B(T("login"))))))

        if self_registration:
            # Provide a Registration box on front page
            register_form = auth.register()
            register_div = DIV(H3(T("Register")),
                               P(XML(T("If you would like to help, then please %(sign_up_now)s") % \
                                        dict(sign_up_now=B(T("sign-up now"))))))

            if request.env.request_method == "POST":
                if login_form.errors:
                    hide, show = "#register_form", "#login_form"
                else:
                    hide, show = "#login_form", "#register_form"
                post_script = \
'''$('%s').addClass('hide')
$('%s').removeClass('hide')''' % (hide, show)
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

    # Feed Control
    rss = settings.frontpage.rss
    if rss:
        s3.external_stylesheets.append("//www.google.com/uds/solutions/dynamicfeed/gfdynamicfeedcontrol.css")
        s3.scripts.append("//www.google.com/jsapi?key=notsupplied-wizard")
        s3.scripts.append("//www.google.com/uds/solutions/dynamicfeed/gfdynamicfeedcontrol.js")

        feeds = ["{title:'%s',url:'%s'}" % (feed["title"], feed["url"])
                 for feed in rss
                 ]
        feeds = ",".join(feeds)

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

    # Output dict for the view
    output = {"title": title,

              # CMS Contents
              "item": item,

              # Menus
              "sit_menu": sit_menu,
              "org_menu": org_menu,
              "res_menu": res_menu,
              "aid_menu": aid_menu,
              #"facility_box": facility_box,

              # Quick Access Boxes
              "manage_facility_box": manage_facility_box,
              "org_box": org_box,

              # Login Form
              "login_div": login_div,
              "login_form": login_form,

              # Registration Form
              "register_div": register_div,
              "register_form": register_form,

              # Control Data
              "self_registration": self_registration,
              "registered": registered,
              "r": None, # Required for dataTable to work
              "datatable_ajax_source": datatable_ajax_source,
              }

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
    display_start = int(get_vars.start) if get_vars.start else 0
    display_length = int(get_vars.limit) if get_vars.limit else 10
    limit = display_length

    list_fields = ["id", "name"]
    default_orderby = orderby = "org_organisation.name asc"
    if representation == "aadata":
        query, orderby, left = resource.datatable_filter(list_fields, get_vars)
        if orderby is None:
            orderby = default_orderby
        if query:
            resource.add_filter(query)
    else:
        limit = 4 * limit

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
        draw = get_vars.get("draw")
        if draw:
            draw = int(draw)
        items = dt.json(totalrows,
                        filteredrows,
                        "org_dt",
                        draw)
    else:
        from gluon.http import HTTP
        raise HTTP(415, ERROR.BAD_FORMAT)

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

    return {"title": title,
            "message": message,
            "image_src": "/%s/static/img/%s" % (appname, image),
            }

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
    return {"item": str(session.s3.rapid_data_entry)}

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

    # Check for template-specific customisations
    customise = settings.customise_auth_user_controller
    if customise:
        customise(arg=arg)

    self_registration = settings.get_security_self_registration()
    login_form = register_form = None

    current.menu.oauth = S3MainMenu.menu_oauth()

    if not settings.get_auth_password_changes():
        # Block Password changes as these are managed externally (OpenID / SMTP / LDAP)
        auth_settings.actions_disabled = ("change_password",
                                          "retrieve_password",
                                          )
    elif not settings.get_auth_password_retrieval():
        # Block password retrieval
        auth_settings.actions_disabled = ("retrieve_password",
                                          )

    header = response.s3_user_header or ""

    if arg == "login":
        title = response.title = T("Login")
        # @ToDo: move this code to /modules/s3/s3aaa.py:def login()?
        auth.messages.submit_button = T("Login")
        form = auth()
        #form = auth.login()
        login_form = form

    elif arg == "register":
        # @ToDo: move this code to /modules/s3/s3aaa.py:def register()?
        if not self_registration:
            session.error = T("Registration not permitted")
            redirect(URL(f="index"))
        if response.title:
            # Customised
            title = response.title
        else:
            # Default
            title = response.title = T("Register")
        form = register_form = auth.register()

    elif arg == "change_password":
        title = response.title = T("Change Password")
        form = auth()
        # Add client-side validation
        js_global = []
        js_append = js_global.append
        js_append('''S3.password_min_length=%i''' % settings.get_auth_password_min_length())
        js_append('''i18n.password_min_chars="%s"''' % T("You must enter a minimum of %d characters"))
        js_append('''i18n.weak="%s"''' % T("Weak"))
        js_append('''i18n.normal="%s"''' % T("Normal"))
        js_append('''i18n.medium="%s"''' % T("Medium"))
        js_append('''i18n.strong="%s"''' % T("Strong"))
        js_append('''i18n.very_strong="%s"''' % T("Very Strong"))
        script = '''\n'''.join(js_global)
        s3.js_global.append(script)
        if s3.debug:
            s3.scripts.append("/%s/static/scripts/jquery.pstrength.2.1.0.js" % appname)
        else:
            s3.scripts.append("/%s/static/scripts/jquery.pstrength.2.1.0.min.js" % appname)
        s3.jquery_ready.append(
'''$('.password:eq(1)').pstrength({
 'minChar': S3.password_min_length,
 'minCharText': i18n.password_min_chars,
 'verdicts': [i18n.weak, i18n.normal, i18n.medium, i18n.strong, i18n.very_strong]
})''')

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

    templates = settings.get_template()
    if templates != "default":
        # Try a Custom View
        folder = request.folder
        if not isinstance(templates, (tuple, list)):
            templates = (templates,)
        for template in templates[::-1]:
            view = os.path.join(folder,
                                "modules",
                                "templates",
                                template,
                                "views",
                                "user.html")
            if os.path.exists(view):
                try:
                    # Pass view as file not str to work in compiled mode
                    response.view = open(view, "rb")
                except IOError:
                    from gluon.http import HTTP
                    raise HTTP("404", "Unable to open Custom View: %s" % view)
                else:
                    break

    return {"title": title,
            "header": header,
            "form": form,
            "login_form": login_form,
            "register_form": register_form,
            "self_registration": self_registration,
            }

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
    user_person_id = str(auth.s3_logged_in_person())

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
                   args = [user_person_id, "user_profile"])
        onaccept = lambda form: auth.s3_approve_user(form.vars),
        auth.configure_user_fields()
        form = auth.profile(next = next,
                            onaccept = onaccept)

        return dict(title = s3.crud_strings["pr_person"]["title_display"],
                    rheader = rheader,
                    form = form,
                    )

    set_method("pr", "person",
               method = "user_profile",
               action = auth_profile_method)

    # Custom Method for Contacts
    set_method("pr", "person",
               method = "contacts",
               action = s3db.pr_Contacts)

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
            r.resource.configure(deletable = False)

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
                    crud_fields = ["name",
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
                                            auth_user_options = {"joinby": "pe_id",
                                                                 "pkey": "pe_id",
                                                                 "multiple": False,
                                                                 },
                                           )
                        crud_fields += ["user_options.osm_oauth_consumer_key",
                                        "user_options.osm_oauth_consumer_secret",
                                        ]
                    crud_form = s3base.S3SQLCustomForm(*crud_fields)
                    list_fields = ["name",
                                   "pe_default",
                                   ]
                    s3db.configure("gis_config",
                                   crud_form = crud_form,
                                   insertable = False,
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
                dob = table.date_of_birth
                dob.widget = S3CalendarWidget(past_months = 972,
                                              future_months = -144,
                                              )
            return True
        else:
            # Disable non-interactive & import
            return False
    s3.prep = prep

    # CRUD post-process
    def postp(r, output):
        if r.interactive and r.component:
            if r.component_name == "config":
                update_url = URL(c="gis", f="config",
                                 args="[id]")
                s3_action_buttons(r, update_url=update_url)
                s3.actions.append(dict(url=URL(c="gis", f="index",
                                               vars={"config":"[id]"}),
                                       label=str(T("Show")),
                                       _class="action-btn",
                                       ))
            elif r.component_name == "asset":
                # Provide a link to assign a new Asset
                # @ToDo: Proper Widget to do this inline
                output["add_btn"] = A(T("Assign Asset"),
                                      _href=URL(c="asset", f="asset"),
                                      _id="add-btn",
                                      _class="action-btn",
                                      )
        return output
    s3.postp = postp

    if settings.get_hrm_record_tab():
        hr_tab = (T("Staff/Volunteer Record"), "human_resource")
    else:
        hr_tab = None

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

    if settings.get_pr_use_address():
        address_tab = (T("Address"), "address")
    else:
        address_tab = None

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

    setting = settings.get_pr_contacts_tabs()
    if setting:
        contacts_tab = (settings.get_pr_contacts_tab_label(), "contacts")
    else:
        contacts_tab = None

    tabs = [(T("Person Details"), None),
            (T("User Account"), "user_profile"),
            hr_tab,
            id_tab,
            description_tab,
            address_tab,
            contacts_tab,
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

    return s3_rest_controller("pr", "person",
                              rheader = lambda r, tabs=tabs: \
                                                s3db.pr_rheader(r, tabs=tabs))

# -----------------------------------------------------------------------------
def group():
    """
        RESTful CRUD controller
        - needed when group add form embedded in default/person
        - only create method is allowed, when opened in an inline form.
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

    return s3_rest_controller("pr", "group")

# -----------------------------------------------------------------------------
def skill():
    """
        RESTful CRUD controller
        - needed when skill add form embedded in default/person
        - only create method is allowed, when opened in an inline form.
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

    return s3_rest_controller("hrm", "skill")

# -----------------------------------------------------------------------------
def facebook():
    """ Login using Facebook """

    channel = s3db.msg_facebook_login()

    if not channel:
        redirect(URL(f="user", args=request.args, vars=get_vars))

    from s3oauth import FaceBookAccount
    auth.settings.login_form = FaceBookAccount(channel)
    form = auth()

    return {"form": form}

# -----------------------------------------------------------------------------
def google():
    """ Login using Google """

    channel = settings.get_auth_google()

    if not channel:
        redirect(URL(f="user", args=request.args, vars=get_vars))

    from s3oauth import GooglePlusAccount
    auth.settings.login_form = GooglePlusAccount(channel)
    form = auth()

    return {"form": form}

# -----------------------------------------------------------------------------
def humanitarian_id():
    """ Login using Humanitarian.ID """

    channel = settings.get_auth_humanitarian_id()

    if not channel:
        redirect(URL(f="user", args=request.args, vars=get_vars))

    from s3oauth import HumanitarianIDAccount
    auth.settings.login_form = HumanitarianIDAccount(channel)
    form = auth()

    return {"form": form}

# -----------------------------------------------------------------------------
def openid_connect():
    """ Login using OpenID Connect """

    channel = settings.get_auth_openid_connect()
    if not channel:
        redirect(URL(f="user", args=request.args, vars=get_vars))

    from s3oauth import OpenIDConnectAccount
    auth.settings.login_form = OpenIDConnectAccount(channel)
    form = auth()

    return {"form": form}

# -----------------------------------------------------------------------------
# About Sahana
def apath(path=""):
    """ Application path """

    from gluon.fileutils import up
    opath = up(request.folder)
    # @ToDo: This path manipulation is very OS specific.
    while path[:3] == "../": opath, path=up(opath), path[3:]
    return os.path.join(opath, path).replace("\\", "/")

def about():
    """
        The About page provides details on the software dependencies and
        versions available to this instance of Sahana Eden.
    """

    _custom_view("about")

    # Allow editing of page content from browser using CMS module
    if settings.has_module("cms"):
        ADMIN = auth.s3_has_role("ADMIN")
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        module = "default"
        resource = "about"
        query = (ltable.module == module) & \
                ((ltable.resource == None) | \
                 (ltable.resource == resource)) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = db(query).select(table.id,
                                table.body,
                                limitby=(0, 1)).first()

        get_vars = {"module": module, "resource": resource}

        if item:
            from s3 import S3XMLContents
            contents = S3XMLContents(item.body)
            if ADMIN:
                item = DIV(contents,
                           BR(),
                           A(T("Edit"),
                             _href=URL(c="cms", f="post",
                                       args=[item.id, "update"],
                                       vars=get_vars,
                                       ),
                             _class="action-btn"))
            else:
                item = DIV(contents)
        elif ADMIN:
            if s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            item = A(T("Edit"),
                     _href=URL(c="cms", f="post",
                               args="create",
                               vars=get_vars,
                               ),
                     _class="%s cms-edit" % _class)
        else:
            item = H2(T("About"))
    else:
        item = H2(T("About"))

    response.title = T("About")

    # Technical Support Details
    if not settings.get_security_version_info() or \
       settings.get_security_version_info_requires_login() and \
       not auth.s3_logged_in():

        return {"details": "",
                "item": item,
                }

    import platform
    import string
    import subprocess

    sahana_version = open(os.path.join(request.folder, "VERSION"), "r").read()
    web2py_version = open(apath("../VERSION"), "r").read()[8:]
    python_version = platform.python_version()
    os_version = platform.platform()

    # Database
    if db_string.find("sqlite") != -1:
        try:
            import sqlite3
            sqlite_version = sqlite3.version
        except:
            sqlite_version = T("Unknown")
        database = TR(TD("SQLite"),
                      TD(sqlite_version))

    elif db_string.find("mysql") != -1:
        try:
            # @ToDo: Support using pymysql & Warn
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

        database = TAG[""](TR(TD("MySQL"),
                              TD(mysql_version)),
                           TR(TD("MySQLdb python driver"),
                              TD(mysqldb_version)),
                           )

    else:
        # Postgres
        try:
            # @ToDo: Support using pg8000 & Warn
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

        database = TAG[""](TR(TD("PostgreSQL"),
                              TD(pgsql_version)),
                              TR(TD("psycopg2 python driver"),
                                 TD(psycopg_version)),
                              )

    # Libraries
    try:
        from lxml import etree
        lxml_version = ".".join([str(i) for i in etree.LXML_VERSION])
    except:
        lxml_version = T("Not installed or incorrectly configured.")
    try:
        import reportlab
        reportlab_version = reportlab.Version
    except:
        reportlab_version = T("Not installed or incorrectly configured.")
    try:
        import shapely
        shapely_version = shapely.__version__
    except:
        shapely_version = T("Not installed or incorrectly configured.")
    try:
        import xlrd
        xlrd_version = xlrd.__VERSION__
    except:
        xlrd_version = T("Not installed or incorrectly configured.")
    try:
        import xlwt
        xlwt_version = xlwt.__VERSION__
    except:
        xlwt_version = T("Not installed or incorrectly configured.")

    details = DIV(TABLE(THEAD(),
                        TBODY(TR(TD(STRONG(T("Configuration"))),
                                 TD(),
                                 _class="odd",
                                 ),
                              TR(TD(T("Public URL")),
                                 TD(settings.get_base_public_url()),
                                 ),
                              TR(TD(STRONG(T("Core Components"))),
                                 TD(STRONG(T("Version"))),
                                 _class="odd",
                                 ),
                              TR(TD(settings.get_system_name_short()),
                                 TD(sahana_version),
                                 ),
                              TR(TD(T("Web Server")),
                                 TD(request.env.server_software),
                                 _class="odd",
                                 ),
                              TR(TD("Web2Py"),
                                 TD(web2py_version),
                                 ),
                              TR(TD("Python"),
                                 TD(python_version),
                                 _class="odd",
                                 ),
                              TR(TD("Operating System"),
                                 TD(os_version),
                                 ),
                              TR(TD(STRONG(T("Database"))),
                                 TD(),
                                 _class="odd",
                                 ),
                              database,
                              TR(TD(STRONG(T("Other Components"))),
                                 TD(),
                                 _class="odd",
                                 ),
                              TR(TD("lxml"),
                                 TD(lxml_version),
                                 ),
                              TR(TD("ReportLab"),
                                 TD(reportlab_version),
                                 _class="odd",
                                 ),
                              TR(TD("Shapely"),
                                 TD(shapely_version),
                                 ),
                              TR(TD("xlrd"),
                                 TD(xlrd_version),
                                 _class="odd",
                                 ),
                              TR(TD("xlwt"),
                                 TD(xlwt_version),
                                 ),
                        _class="dataTable display"),
                  _class="table-container")
                  )

    return {"item": item,
            "details": details,
            }

# -----------------------------------------------------------------------------
def help():
    """ CMS page or Custom View """

    _custom_view("help")

    # Allow editing of page content from browser using CMS module
    if settings.has_module("cms"):
        ADMIN = auth.s3_has_role("ADMIN")
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        module = "default"
        resource = "help"
        query = (ltable.module == module) & \
                ((ltable.resource == None) | \
                 (ltable.resource == resource)) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = db(query).select(table.id,
                                table.body,
                                limitby=(0, 1)).first()

        get_vars = {"module": module, "resource": resource}

        if item:
            if ADMIN:
                item = DIV(XML(item.body),
                           BR(),
                           A(T("Edit"),
                             _href=URL(c="cms", f="post",
                                       args=[item.id, "update"],
                                       vars=get_vars,
                                       ),
                             _class="action-btn"))
            else:
                item = DIV(XML(item.body))
        elif ADMIN:
            if s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            item = A(T("Edit"),
                     _href=URL(c="cms", f="post",
                               args="create",
                               vars=get_vars,
                               ),
                     _class="%s cms-edit" % _class)
        else:
            item = TAG[""](H2(T("Help")),
                           A(T("User & Administration Guide"),
                            _href="http://eden.sahanafoundation.org/wiki/UserGuidelines",
                            _target="_blank"),
                           " - online version")
    else:
        item = TAG[""](H2(T("Help")),
                       A(T("User & Administration Guide"),
                         _href="http://eden.sahanafoundation.org/wiki/UserGuidelines",
                         _target="_blank"),
                         " - online version")

    response.title = T("Help")

    return {"item": item}

# -----------------------------------------------------------------------------
def privacy():
    """ Custom View """

    _custom_view("privacy")

    response.title = T("Privacy")
    return {}

# -----------------------------------------------------------------------------
def tos():
    """ Custom View """

    _custom_view("tos")

    response.title = T("Terms of Service")
    return {}

# -----------------------------------------------------------------------------
def video():
    """ Custom View """

    _custom_view("video")

    response.title = T("Video Tutorials")
    return {}

# -----------------------------------------------------------------------------
def view():
    """ Custom View """

    view = request.args(0)

    _custom_view(view)

    response.title = view
    return {}

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
                if not auth.s3_has_role("ADMIN"):
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

    templates = settings.get_template()
    if templates != "default":
        # Try a Custom Controller
        if not isinstance(templates, (tuple, list)):
            templates = (templates,)
        for template in templates[::-1]:
            package = "applications.%s.modules.templates.%s" % (appname, template)
            name = "controllers"
            try:
                custom = getattr(__import__(package, fromlist=[name]), name)
            except (ImportError, AttributeError):
                # No Custom Page available, try a custom view
                pass
            else:
                if hasattr(custom, "contact"):
                    controller = getattr(custom, "contact")()
                    return controller()

        # Try a Custom View
        for template in templates:
            view = os.path.join(request.folder,
                                "modules",
                                "templates",
                                template,
                                "views",
                                "contact.html")
            if os.path.exists(view):
                try:
                    # Pass view as file not str to work in compiled mode
                    response.view = open(view, "rb")
                except IOError:
                    from gluon.http import HTTP
                    raise HTTP("404", "Unable to open Custom View: %s" % view)

                response.title = T("Contact us")
                return {}

    if settings.has_module("cms"):
        # Use CMS
        return s3db.cms_index("default", "contact", page_name=T("Contact Us"))

    # Just use default HTML View
    return {}

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
def tables():
    """
        RESTful CRUD Controller for Dynamic Table Models
    """

    return s3_rest_controller("s3", "table",
                              rheader = s3db.s3_table_rheader,
                              csv_template = ("s3", "table"),
                              csv_stylesheet = ("s3", "table.xsl"),
                              )

# -----------------------------------------------------------------------------
def table():
    """
        RESTful CRUD Controller for Dynamic Table Contents

        NB: first argument is the resource name, i.e. the name of
            the dynamic table without prefix, e.g.:
            default/table/test to access s3dt_test table
    """

    args = request.args
    if len(args):
        return s3_rest_controller(dynamic = args[0].rsplit(".", 1)[0])
    else:
        raise HTTP(400, "No resource specified")

# -----------------------------------------------------------------------------
def masterkey():
    """ Master Key Verification and Context Query """

    # Challenge the client to login with master key
    if not auth.s3_logged_in():
        auth.permission.fail()

    # If successfully logged-in, provide context information for
    # the master key (e.g. project UUID + title, master key UUID)
    from s3.s3masterkey import S3MasterKey
    return S3MasterKey.context()

# -----------------------------------------------------------------------------
def get_settings():
    """
       Function to lookup the value of a deployment_setting
       Responds to GET requests.
       Requires admin permissions
    """

    # Check if the request has a valid authorization header with admin cred.
    if not auth.s3_has_role("ADMIN"):
        auth.permission.format = None
        auth.permission.fail()

    elif not settings.get_base_allow_testing():
        raise HTTP("405", "Testing not allowed")

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

        raise HTTP("400", "Invalid/Missing argument")

# -----------------------------------------------------------------------------
def _custom_view(filename):
    """
        See if there is a custom view for a page &, if so, use that
    """

    templates = settings.get_template()
    if templates != "default":
        folder = request.folder
        if not isinstance(templates, (tuple, list)):
            templates = (templates,)
        for template in templates[::-1]:
            # Try a Custom View
            view = os.path.join(folder,
                                "modules",
                                "templates",
                                template,
                                "views",
                                "%s.html" % filename)
            if os.path.exists(view):
                try:
                    # Pass view as file not str to work in compiled mode
                    response.view = open(view, "rb")
                except IOError:
                    from gluon.http import HTTP
                    raise HTTP("404", "Unable to open Custom View: %s" % view)
                else:
                    break

# END =========================================================================
