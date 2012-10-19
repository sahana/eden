# -*- coding: utf-8 -*-

from os import path

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.storage import Storage
from s3 import *

# =============================================================================
def INPUT_BTN(**attributes):
    """
        Utility function to create a styled button
    """

    return SPAN(INPUT(_class = "button-right",
                      **attributes),
                _class = "button-left")

# =============================================================================
class index():
    """ Custom Home Page """

    def __call__(self):

        request = current.request
        response = current.response

        response.title = current.deployment_settings.get_system_name()
        view = path.join(request.folder, "private", "templates",
                         "DRRPP", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        T = current.T
        appname = request.application

        home_img = IMG(_src="/%s/static/themes/DRRPP/img/home_img.jpg" % appname,
                       _id="home_img")
        home_page_img = IMG(_src="/%s/static/themes/DRRPP/img/home_page_img.png" % appname,
                            _id="home_page_img")
        home_map_img = IMG(_src="/%s/static/themes/DRRPP/img/home_map_img.png" % appname,
                           _id="home_map_img")

        list_img = A(IMG(_src="/%s/static/themes/DRRPP/img/list_img.png" % appname,
                         _id="list_img"),
                     _href=URL(c="project", f="project", args=["list"]),
                     _title="Project List")

        matrix_img = A(IMG(_src="/%s/static/themes/DRRPP/img/matrix_img.png" % appname,
                           _id="matrix_img"),
                       _href=URL(c="project", f="project", args=["matrix"]),
                       _title="Project Matrix Report")

        map_img = A(IMG(_src="/%s/static/themes/DRRPP/img/map_img.png" % appname,
                        _id="map_img"),
                    _href=URL(c="project", f="location", args=["map"]),
                    _title="Project Map")

        graph_img = A(IMG(_src="/%s/static/themes/DRRPP/img/graph_img.png" % appname,
                          _id="graph_img"),
                      _href=URL(c="project", f="project", args=["graphs"]),
                      _title="Project Graph")

        add_pipeline_project_link = URL(c="project",
                                        f="project",
                                        args=["create"],
                                        vars=dict(set_status_id = "1"))
        add_current_project_link = URL(c="project",
                                       f="project",
                                       args=["create"],
                                       vars=dict(set_status_id = "2"))
        add_completed_project_link = URL(c="project",
                                         f="project",
                                         args=["create"],
                                         vars=dict(set_status_id = "3"))
        add_offline_project_link = URL(c="static",
                                       f="DRR_Project_Portal_New_Project_Form.doc")

        add_framework_link = URL(c="project",
                                 f="framework",
                                 args=["create"])

        project_captions = {
            1:"DRR projects which will be being implemented in the future, and for which funding has been secured in the Asia and Pacific region.",
            2:"DRR projects which are currently being implemented in one or more country in the Asia and Pacific region.",
            3:"DRR projects which have been completed and are no longer being implemented in the Asia and Pacific region."
            }
        framework_caption = "Frameworks, action plans, road maps, strategies, declarations, statements and action agendas on DRR or DRR related themes, which are documents or instruments for guiding stakeholders on DRR planning, programming and implementation."
        add_div = DIV(A(DIV("ADD ", SPAN("CURRENT", _class="white_text"), " PROJECT"),
                        _href=add_current_project_link,
                        _title=project_captions[2]),
                      A(DIV("ADD ", SPAN("PROPOSED", _class="white_text"), " PROJECT" ),
                        _href=add_pipeline_project_link,
                        _title=project_captions[1]),
                      A(DIV("ADD ", SPAN("COMPLETED", _class="white_text"), " PROJECT" ),
                        _href=add_completed_project_link,
                        _title=project_captions[3]),
                      A(DIV("ADD PROJECT OFFLINE" ),
                        _href=add_offline_project_link,
                        _title="Download a form to enter a DRR projects off-line and submit by Email"),
                      A(DIV("ADD ", SPAN("DRR FRAMEWORK", _class="white_text")),
                        _href=add_framework_link,
                        _title=framework_caption),
                      _id="add_div"
                     )

        why_box = DIV(H1("WHY THIS PORTAL?"),
                      UL("Share information on implementation of DRR: Who? What? Where?",
                         "Collectively identify gaps, improve planning and programming on DRR",
                         "Identify areas of cooperation on implementation of DRR"
                         ),
                      _id="why_box")

        what_box = DIV(H1("WHAT CAN WE GET FROM THIS PORTAL?"),
                       UL("List of completed and ongoing DRR projects - by country, hazards, themes, partners and donors.",
                          "List of planned/proposed projects - better planning of future projects.",
                          "Quick analysis - on number and types of completed and ongoing DRR projects",
                          "Generate customised graphs and maps.",
                          "Know more on the DRR frameworks/action plans guiding the region - identify priority areas for providing support and implementation.",
                          "List of organisations implementing DRR projects at regional level.",
                          "Archive of periodic meetings of regional DRR mechanisms."
                          ),
                       _id="what_box")

        how_help_box = DIV(H1("HOW WOULD THIS INFORMATION HELP?"),
                           H2("National Government"),
                           UL("Gain clarity on types of support that may be accessed from regional level and thus receive coherent regional assistance"),
                           H2("Organisation Implementing DRR Projects"),
                           UL("Plan better-knowing who does what, and where; Find partners and scale up implementation; and Learn from past and ongoing work of partners"),
                           H2("Donor Agencies"),
                           UL("Identify priorities to match your policy and programmatic imperatives; and minimise overlap; maximise resources"),
                           _id="how_help_box")

        how_start_box = DIV(H1("HOW DO WE GET STARTED?"),
                            UL("Add information on  current / proposed / completed DRR projects",
                               "Search for information - project list, project analysis, DRR frameworks",
                               "Log in to add and edit your data",
                               "Link to this portal from your organisation website"
                               ),
                            _id="how_start_box")

        help = A(DIV("USER MANUAL",
                     _id="help_div"),
                 _href=URL(c="static", f="DRR_Portal_User_Manual.pdf"),
                 _target="_blank"
                 )

        tour = A(DIV("VIDEO TOUR",
                     _id="tour_div"),
                 _href=URL(c="default", f="index", args="video"),
                 _target="_blank"
                 )

        db = current.db
        s3db = current.s3db
        table = s3db.project_project
        query = (table.deleted == False)
        #approved = & (table.approved == True)
        #current = & (table.status_id == 2)
        #proposed = & (table.status_id == 1)
        #completed = & (table.status_id == 1)
        projects = db(query).count()
        ftable = s3db.project_framework
        query = (ftable.deleted == False)
        #approved = & (table.approved == True)
        frameworks = db(query).count()
        stats = DIV(DIV("Currently the DRR Projects Portal has information on:"),
                    TABLE(TR(projects,
                             A("Projects",
                               _href=URL(c="project", f="project",
                                         args=["list"]))
                             ),
                          TR(TD(),
                             TABLE(TR(projects,
                                      A("Current Projects",
                                        _href=URL(c="project", f="project",
                                                  args=["list"],
                                                  vars={"status_id":2}))
                                     )
                                   )
                             ),
                          TR(TD(),
                             TABLE(TR(projects,
                                      A("Proposed Projects",
                                        _href=URL(c="project", f="project",
                                                  args=["list"],
                                                  vars={"status_id":1}))
                                     )
                                    )
                             ),
                          TR(TD(),
                             TABLE(TR(projects,
                                      A("Completed Projects",
                                        _href=URL(c="project", f="project",
                                                  args=["list"],
                                                  vars={"status_id":3}))
                                     )
                                    )
                             ),
                          TR(frameworks,
                             A("Frameworks",
                               _href=URL(c="project", f="framework"))
                            ),
                         ),
                    _id="stats_div")

        market = DIV(DIV(I("Under Development...")),
                     H2("DRR Project Marketplace"),
                     DIV("A platform to coordinate and collaborate on future DRR Projects."),
                     _id = "market_div")

        auth = current.auth
        _table_user = auth.settings.table_user
        _table_user.language.label = T("Language")
        _table_user.language.default = "en"
        _table_user.language.comment = DIV(_class="tooltip",
                                           _title=T("Language|The language to use for notifications."))
        #_table_user.language.requires = IS_IN_SET(s3_languages)
        languages = current.deployment_settings.get_L10n_languages()
        _table_user.language.represent = lambda opt: \
            languages.get(opt, current.messages.UNKNOWN_OPT)

        request.args = ["login"]
        auth.settings.formstyle = "divs"
        login = auth()
        login[0][-1][1][0] = INPUT_BTN(_type = "submit",
                                      _value = T("Login"))

        return dict(title = T("Home"),
                    home_img = home_img,
                    add_div = add_div,
                    login = login,
                    why_box = why_box,
                    home_page_img = home_page_img,
                    what_box = what_box,
                    how_help_box = how_help_box,
                    home_map_img = home_map_img,
                    how_start_box = how_start_box,
                    tour = tour,
                    help = help,
                    stats = stats,
                    market = market,
                    list_img = list_img,
                    matrix_img = matrix_img,
                    map_img = map_img,
                    graph_img = graph_img,
                    )

# =============================================================================
class register():
    """ Custom Registration Page """

    def __call__(self):

        request = current.request
        response = current.response

        view = path.join(request.folder, "private", "templates",
                         "DRRPP", "views", "register.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        T = current.T
        auth = current.auth
        _settings = auth.settings

        # Default the profile language to the one currently active
        table = _settings.table_user
        table.language.default = T.accepted_language

        # Combo box for Organisation
        table.organisation_id.widget = S3OrganisationAutocompleteWidget(new_items=True)
        table.organisation_id.requires = IS_COMBO_BOX("org_organisation",
                                                      current.s3db.org_organisation_id.attr.requires)

        # Custom onaccept to process custom fields
        _settings.register_onaccept = register_onaccept

        # Build the registration form
        form = auth()
        form.attributes["_id"] = "regform"

        # Set the formstyle
        _form = form[0]
        _form[-1] = TR(TD(_class="w2p_fl"),
                       TD(_class="w2p_fc"),
                       TD(INPUT_BTN(_type="submit",
                                    _value=T("Register")),
                          _class="w2p_fw"),
                       _id="submit_record_row"
                       )
        _form[0] = TR(TD(SPAN(" *", _class="req"),
                         _class="w2p_fl"),
                      TD(LABEL(DIV("%s: " % T("First Name")),
                               _id="auth_user_first_name__label",
                               _for="auth_user_first_name"),
                         _class="w2p_fc"),
                      TD(INPUT(_id="auth_user_first_name",
                               _class="string",
                               _type="text",
                               _name="first_name",
                               _size="62"),
                         _class="w2p_fw"),
                      _id="auth_user_first_name_row"
                      )
        _form[1] = TR(TD(SPAN(" *", _class="req"),
                         _class="w2p_fl"),
                      TD(LABEL(DIV("%s: " % T("Last Name")),
                               _id="auth_user_last_name__label",
                               _for="auth_user_last_name"),
                         _class="w2p_fc"),
                      TD(INPUT(_id="auth_user_last_name",
                               _class="string",
                               _type="text",
                               _name="last_name",
                               _size="62"),
                         _class="w2p_fw"),
                      _id="auth_user_last_name_row"
                      )
        _form[2] = TR(TD(_class="w2p_fl"),
                      TD(LABEL(DIV("%s: " % T("Organization")),
                               _id="auth_user_organisation_id__label",
                               _for="auth_user_organisation_id"),
                         _class="w2p_fc"),
                      TD(form.custom.widget.organisation_id,
                         _class="w2p_fw"),
                      _id="auth_user_organisation_id_row"
                      )
        _form[3] = TR(TD(SPAN(" *", _class="req"),
                         _class="w2p_fl"),
                      TD(LABEL(DIV("%s: " % T("E-Mail")),
                               _id="auth_user_email__label",
                               _for="auth_user_email"),
                         _class="w2p_fc"),
                      TD(INPUT(_id="auth_user_email",
                               _class="string",
                               _type="text",
                               _name="email",
                               _size="62"),
                         _class="w2p_fw"),
                      _id="auth_user_email_row"
                      )
        _form[4] = TR(TD(SPAN(" *", _class="req"),
                         _class="w2p_fl"),
                      TD(LABEL(DIV("%s: " % T("Password")),
                               _id="auth_user_password__label",
                               _for="auth_user_password"),
                         _class="w2p_fc"),
                      TD(INPUT(_id="auth_user_password",
                               _type="password",
                               _name="password",
                               _class="password",
                               ),
                         _class="w2p_fw"),
                      _id="auth_user_password_row"
                      )
        _form[5] = TR(TD(SPAN(" *", _class="req"),
                         _class="w2p_fl"),
                      TD(LABEL(DIV("%s: " % T("Verify Password")),
                               _id="auth_user_password_two__label",
                               _for="auth_user_password_two"),
                         _class="w2p_fc"),
                      TD(INPUT(_id="auth_user_password_two",
                               _type="password",
                               _name="password_two",
                               _class="password",
                               ),
                         _class="w2p_fw"),
                      _id="auth_user_password_two_row"
                      )

        # Add custom fields
        append = _form[2].append
        append(
                TR(TD(SPAN(" *", _class="req"),
                      _class="w2p_fl"),
                   TD(LABEL(DIV("%s: " % T("Role")),
                            _id="auth_user_position__label",
                            _for="auth_user_position"),
                      _class="w2p_fc"),
                   TD(SELECT(OPTION(_value=""),
                             OPTION(T("Practitioner"),
                                    _value="1"),
                             OPTION(T("Consultant"),
                                    _value="2"),
                             OPTION(T("Researcher"),
                                    _value="3"),
                             OPTION(T("Academic"),
                                    _value="4"),
                             OPTION(T("Student"),
                                    _value="5"),
                             _name="position",
                             _id="auth_user_position",
                             _class="integer"
                             ),
                      _class="w2p_fw"),
                   _id="auth_user_position_row"
                   )
            )
        append(
                TR(TD(SPAN(" *", _class="req"),
                      DIV(_rel="If you do not specify an organisation, please enter your reason for using the DRR Project Portal.",
                          _class="labeltip"),
                      _class="w2p_fl"),
                   TD(LABEL(DIV("%s: " % T("Reason")),
                            _id="auth_user_reason__label",
                            _for="auth_user_reason"),
                      _class="w2p_fc"),
                   TD(TEXTAREA(_id="auth_user_reason",
                               _class="text",
                               _name="reason",
                               _rows="10",
                               _cols="50",
                               ),
                      _class="w2p_fw"),
                   _id="auth_user_reason_row"
                   )
            )

        # Add client-side validation
        s3 = response.s3
        appname = request.application
        if s3.debug:
            s3.scripts.append("/%s/static/scripts/jquery.pstrength.2.1.0.js" % appname)
            s3.scripts.append("/%s/static/scripts/jquery.validate.js" % appname)
        else:
            s3.scripts.append("/%s/static/scripts/jquery.pstrength.2.1.0.min.js" % appname)
            s3.scripts.append("/%s/static/scripts/jquery.validate.min.js" % appname)
        s3.jquery_ready.append("".join(('''
$('#regform').validate({
 errorClass:'req',
 rules:{
  first_name:{
   required:true
  },
  last_name:{
   required:true
  },
  position:{
   required:true,
  },
  reason:{
   required:true,
  },
  email:{
   required:true,
   email:true
  },
  password:{
   required:true
  },
  password_two:{
   required:true,
   equalTo:'.password:first'
  }
 },
 messages:{
  first_name:"''', str(T("Enter your first name")), '''",
  last_name:"''', str(T("Enter your last name")), '''",
  position:"''', str(T("Select your role")), '''",
  reason:"''', str(T("Enter a reason")), '''",
  password:{
   required:"''', str(T("Provide a password")), '''"
  },
  password_two:{
   required:"''', str(T("Repeat your password")), '''",
   equalTo:"''', str(T("Enter the same password as above")), '''"
  },
  email:{
   required:"''', str(T("Please enter a valid email address")), '''",
   email:"''', str(T("Please enter a valid email address")), '''"
  }
 },
 errorPlacement:function(error,element){
  error.appendTo(element.parent())
 },
 submitHandler:function(form){
  form.submit()
 }
})
$('.password:first').pstrength({minchar:''', str(_settings.password_min_length), ''',minchar_label:"''', str(T("The minimum number of characters is ")), '''"})
$('.labeltip').cluetip({activation:'hover',position:'mouse',sticky:false,showTitle:false,local:true})''')))

        response.title = T("DRRPP - Register")

        return dict(form=form)

# -----------------------------------------------------------------------------
def register_onaccept(form):
    """ Tasks to be performed after a new user registers """

    # Add newly-registered users to Person Registry, add 'Authenticated' role
    # If Organisation is provided, then add HRM record
    person_id = current.auth.s3_register(form)

    # Process Custom Fields
    vars = form.request_vars
    position = vars.get("position", "")
    reason = vars.get("reason", "")
    id = form.vars.id
    db = current.db
    table = db.auth_user
    db(table.id == form.vars.id).update(
                                    comments = "%s | %s" % (position, reason)
                                )

# =============================================================================
class contact():
    """ Contact Form """

    def __call__(self):

        request = current.request
        response = current.response

        view = path.join(request.folder, "private", "templates",
                         "DRRPP", "views", "contact.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        if request.env.request_method == "POST":
            # Processs Form
            vars = request.post_vars
            result = current.msg.send_email(
                    #to=current.deployment_settings.get_mail_approver(),
                    to="admin@drrprojects.net",
                    subject=vars.subject,
                    message=vars.message,
                    reply_to=vars.address,
                )
            if result:
                response.confirmation = "Thankyou for your message - we'll be in touch shortly"

        #T = current.T

        form = DIV(
                H1("Contact Us"),
                P("You can leave a message using the contact form below."),
                FORM(TABLE(
                        TR(LABEL("Your name:",
                              SPAN(" *", _class="req"),
                              _for="name")),
                        TR(INPUT(_name="name", _type="text", _size=62, _maxlength="255")),
                        TR(LABEL("Your e-mail address:",
                              SPAN(" *", _class="req"),
                              _for="address")),
                        TR(INPUT(_name="address", _type="text", _size=62, _maxlength="255")),
                        TR(LABEL("Subject:",
                              SPAN(" *", _class="req"),
                              _for="subject")),
                        TR(INPUT(_name="subject", _type="text", _size=62, _maxlength="255")),
                        TR(LABEL("Message:",
                              SPAN(" *", _class="req"),
                              _for="name")),
                        TR(TEXTAREA(_name="message", _class="resizable", _rows=5, _cols=62)),
                        TR(INPUT(_type="submit", _value="Send e-mail")),
                        ),
                    _id="mailform"
                    )
                )
        s3 = response.s3
        if s3.cdn:
            if s3.debug:
                s3.scripts.append("http://ajax.aspnetcdn.com/ajax/jquery.validate/1.9/jquery.validate.js")
            else:
                s3.scripts.append("http://ajax.aspnetcdn.com/ajax/jquery.validate/1.9/jquery.validate.min.js")

        else:
            if s3.debug:
                s3.scripts.append("/%s/static/scripts/jquery.validate.js" % request.application)
            else:
                s3.scripts.append("/%s/static/scripts/jquery.validate.min.js" % request.application)
        s3.jquery_ready.append(
'''$('#mailform').validate({
 errorClass:'req',
 rules:{
  name:{
   required:true
  },
  subject:{
   required:true
  },
  message:{
   required:true
  },
  name:{
   required:true
  },
  address: {
   required:true,
   email:true
  }
 },
 messages:{
  name:"Enter your name",
  subject:"Enter a subject",
  message:"Enter a message",
  address:{
   required:"Please enter a valid email address",
   email:"Please enter a valid email address"
  }
 },
 errorPlacement:function(error,element){
  error.appendTo(element.parents('tr').prev().children())
 },
 submitHandler:function(form){
  form.submit()
 }
})''')

        response.title = "Contact | DRR Project Portal"
        return dict(form=form)

# =============================================================================
class about():
    """
        Custom About page
    """

    def __call__(self):
        response = current.response
        request = current.request
        T = current.T

        view = path.join(request.folder, "private", "templates",
                         "DRRPP", "views", "about.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        response.title = T("About")

        return dict(
            title=T("About"),
        )

# =============================================================================
class analysis():
    """
        Custom page for Project Analysis
    """

    def __call__(self):
        response = current.response
        request = current.request
        T = current.T

        view = path.join(request.folder, "private", "templates",
                         "DRRPP", "views", "analysis.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        response.title = T("Project Analysis")

        return dict(
            title=T("Project Analysis"),
        )

# =============================================================================
class mypage():
    """
        Custom page for a User to manage their Saved Search & Subscriptions
    """

    def __call__(self):
        auth = current.auth

        if not auth.is_logged_in():
            response = current.response
            request = current.request
            T = current.T

            view = path.join(request.folder, "private", "templates",
                             "DRRPP", "views", "mypage.html")
            try:
                # Pass view as file not str to work in compiled mode
                response.view = open(view, "rb")
            except IOError:
                from gluon.http import HTTP
                raise HTTP("404", "Unable to open Custom View: %s" % view)

            response.title = T("My Page")

            return dict(
                title=T("My Page"),
            )
        else:
            person_id = auth.s3_logged_in_person()
            redirect(URL(c="pr", f="person", args=[person_id]))

# =============================================================================
class organisations():
    """
        Custom page to show 2 dataTables on a single page:
        * Regional Organisations
        * Committees, Forums, Mechanism, Meetings and Networks
    """

    def __call__(self):

        from gluon.storage import Storage
        from s3 import S3FieldSelector

        T = current.T
        request = current.request
        response = current.response

        response.title = "DRR Projects Portal - Regional Organizations"
        view = path.join(request.folder, "private", "templates",
                         "DRRPP", "views", "organisations.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        tables = []
        table = request.vars.get("table", None)

        # URL format breaks the REST controller conventions
        request.args.pop()

        if table is None or table == "regional":
            s3request, field_list = self._regional()

            if table is None:
                tables.append(self._table("regional", s3request.resource, field_list))

        if table is None or table == "groups":
            s3request, field_list = self._groups()

            if table is None:
                tables.append(self._table("groups", s3request.resource, field_list))

        if table is not None:
            current.s3db.configure(s3request.resource.tablename,
                                   list_fields = field_list)
            return s3request()

        return dict(tables=tables,
                    appname=request.application)

    # -------------------------------------------------------------------------
    @staticmethod
    def _regional():
        """
        """

        from s3 import S3FieldSelector, s3_request
        T = current.T

        s3request = s3_request("org", "organisation", extension="aadata")
        # (S3FieldSelector("project.id") != None) & \
        f = (S3FieldSelector("organisation_type_id$name").anyof(["Regional Organisation",
                                                                 "Regional Office",
                                                                 "Regional Center"]))
        s3request.resource.add_filter(f)

        field_list = [
            "id",
            "name",
            "acronym",
            (T("Type"), "organisation_type_id"),
            "website",
            "region",
            "year",
            (T("Notes"), "comments")
        ]
        return (s3request, field_list)

    # -------------------------------------------------------------------------
    @staticmethod
    def _groups():
        """
        """

        from s3 import S3FieldSelector, s3_request
        T = current.T

        s3request = s3_request("org", "organisation", extension="aadata")
        #(S3FieldSelector("project.id") != None) & \
        f = (S3FieldSelector("organisation_type_id$name").anyof(["Committees/Mechanism/Forum",
                                                                 "Network"]))
        s3request.resource.add_filter(f)

        field_list = [
            "id",
            "name",
            "acronym",
            (T("Type"), "organisation_type_id"),
            "year",
            "address",
            (T("Notes"), "comments")
        ]
        return (s3request, field_list)

    # -------------------------------------------------------------------------
    @staticmethod
    def _table(name, resource, field_list, limit=10, orderby="name"):
        """
        """

        from s3 import S3FieldSelector
        T = current.T

        fields = []
        cols = []
        for field_name in field_list:
            if isinstance(field_name, tuple):
                field_label = field_name[0]
                field_name = field_name[1]
            else:
                field_label = None

            fs = S3FieldSelector(field_name)
            list_field = fs.resolve(resource)

            if list_field.field != None:
                field = list_field.field
            else:
                field = field_name

            if field_label is None:
                if list_field.field is not None:
                    field_label = field.label
                else:
                    field_label = " ".join([w.capitalize() for w in field_name.split(".")[-1].split("_")])

            fields.append(field)
            cols.append({
                "name": field_name,
                "label": field_label
            })

            if orderby and str(orderby)==str(field_name):
                orderby=field

        records = resource.select(
            fields=field_list,
            start=None,
            limit=None,
            orderby=orderby,
            #as_page=True,
        )

        if records is None:
            records = []

        rows = []
        represent = current.manager.represent
        for record in records:
            row = []

            for field in fields:
                row.append(
                    represent(field=field, record=record)
                )

            rows.append(row)

        options = json.dumps({
            "iDisplayLength": limit,
            "iDeferLoading": resource.count(),
            "bProcessing": True,
            #"bServerSide": True,
            #"sAjaxSource": "/%s/default/index/organisations/?table=%s" % (current.request.application, name),
            "aoColumnDefs": [
                {
                    "bVisible": False,
                    "aTargets": [0]
                }
            ],
            "aoColumns": [{"sName": col["name"]} for col in cols],
            "sDom": "frltpi",
        })

        table = Storage(
            cols=cols,
            rows=rows,
            options=options,
            classes="dataTable display"
        )

        return table

# END =========================================================================
