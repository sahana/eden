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

THEME = "DRRPP"

# =============================================================================
class index():
    """ Custom Home Page """

    def __call__(self):

        request = current.request
        response = current.response

        view = path.join(request.folder, "private", "templates",
                         THEME, "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        # Show full width instead of login box if user is logged in 
        if current.auth.is_logged_in():
            grid = "grid_12"
        else:
            grid = "grid_8"

        latest_projects = DIV(_id="front-latest-body",
                              _class="%s alpha" % grid)
        lappend = latest_projects.append
                              
        db = current.db
        s3db = current.s3db
        table = s3db.project_project
        table_drrpp = s3db.project_drrpp
        query = (table.deleted != True) & \
                (table.approved_by != None)
        rows = db(query).select(table.id,
                                table.name,
                                table_drrpp.activities,
                                table.organisation_id,
                                table.start_date,
                                left=table_drrpp.on(table.id == table_drrpp.project_id),
                                limitby=(0, 3))
        project_ids = [r.project_project.id for r in rows]
        ltable = s3db.project_location
        gtable = s3db.gis_location
        query = (ltable.deleted != True) & \
                (ltable.project_id == table.id) & \
                (gtable.id == ltable.location_id) & \
                (gtable.level == "L0")
        locations = db(query).select(ltable.project_id,
                                     gtable.L0)
        odd = True
        for row in rows:
            countries = [l.gis_location.L0 for l in locations if l.project_location.project_id == row.project_project.id]
            location = ", ".join(countries)
            if odd:
                _class = "front-latest-item odd %s alpha" % grid
            else:
                _class = "front-latest-item even %s alpha" % grid
            card = DIV(DIV(A(row.project_project.name,
                             _href=URL(c="project", f="project", args=[row.project_project.id])),
                           _class="front-latest-title %s"  % grid,
                           ),
                       
                       DIV("Lead Organization: %s" % s3db.org_organisation_represent(row.project_project.organisation_id),
                                _class="front-latest-desc %s" % grid,
                           ),
                       DIV(SPAN("Start Date: %s" % row.project_project.start_date,
                                _class="front-latest-info-date"),
                           SPAN("Countries: %s" % location,
                                _class="front-latest-info-location"),
                           _class="front-latest-info %s" % grid,
                           ),
                       DIV(row.project_drrpp.activities or "",
                           _class="front-latest-desc %s"  % grid,
                           ),
                       _class=_class,
                       )
            lappend(card)
            odd = False if odd else True

        request.args = ["login"]
        login = current.auth()

        appname = request.application
        s3 = response.s3
        if current.session.s3.debug:
            s3.scripts.append("/%s/static/themes/DRRPP/js/slides.jquery.js" % appname)
        else:
            s3.scripts.append("/%s/static/themes/DRRPP/js/slides.min.jquery.js" % appname)
        s3.jquery_ready.append('''
$('#slides').slides({
 play:8000,
 animationStart:function(current){
  $('.caption').animate({
   bottom:-35
  },100);
 },
 animationComplete:function(current){
  $('.caption').animate({
   bottom:0
  },200);
 },
 slidesLoaded:function() {
  $('.caption').animate({
   bottom:0
  },200);
 }
})''')

        return dict(title = "Home",
                    form = login,
                    latest_projects = latest_projects,
                    )

# =============================================================================
class register():
    """ Custom Registration Page """

    def __call__(self):

        request = current.request
        response = current.response

        view = path.join(request.folder, "private", "templates",
                         THEME, "views", "register.html")
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
                       TD(INPUT(_type="submit",
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
                         THEME, "views", "contact.html")
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

        # form = FORM(TABLE(
                        # TR(LABEL("Your name:",
                              # SPAN(" *", _class="req"),
                              # _for="name")),
                        # TR(INPUT(_name="name", _type="text", _size=62, _maxlength="255")),
                        # TR(LABEL("Your e-mail address:",
                              # SPAN(" *", _class="req"),
                              # _for="address")),
                        # TR(INPUT(_name="address", _type="text", _size=62, _maxlength="255")),
                        # TR(LABEL("Subject:",
                              # SPAN(" *", _class="req"),
                              # _for="subject")),
                        # TR(INPUT(_name="subject", _type="text", _size=62, _maxlength="255")),
                        # TR(LABEL("Message:",
                              # SPAN(" *", _class="req"),
                              # _for="name")),
                        # TR(TEXTAREA(_name="message", _class="resizable", _rows=5, _cols=62)),
                        # TR(INPUT(_type="submit", _value="Send e-mail")),
                        # ),
                   # _id="contact-form"
                   # )
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
'''$('#contact-form').validate({
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
        return dict(
                #form=form
            )

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
                         THEME, "views", "about.html")
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
class admin():
    """
        Custom Admin Index Page

    """

    def __call__(self):
        auth = current.auth
        s3_has_role = auth.s3_has_role
        system_roles = auth.get_system_roles()
        ADMIN = system_roles.ADMIN
        ORG_ADMIN = system_roles.ORG_ADMIN

        if s3_has_role(ADMIN) | s3_has_role(ORG_ADMIN):
            response = current.response
            request = current.request
            T = current.T

            view = path.join(request.folder, "private", "templates",
                             THEME, "views", "admin.html")
            try:
                # Pass view as file not str to work in compiled mode
                response.view = open(view, "rb")
            except IOError:
                from gluon.http import HTTP
                raise HTTP("404", "Unable to open Custom View: %s" % view)
            
            response.title = T("Administration Panel")
            
            panel_list = [A(T("Verify Users"),
                            _href = URL(c="admin", f = "user")
                            ),
                          A(T("User List (Excel)"),
                            _href = URL(c="admin", f = "user.xls")
                            ),
                          A(T("Manage Administrators"),
                            _href = URL(c="admin", f = "role", args = [1,"users"])
                            ),
                          A(T("Manage Organisation Contacts"),
                            _href = URL(c="admin", f = "role", args = [6,"users"])
                            ),
                          A(T("Manage Organisations"),
                            _href = URL(c="org", f = "organisation")
                            ),
                          A(T("Approve Projects"),
                            _href = URL(c="project", f = "project", args = "review")
                            ),
                          A(T("Approve Frameworks"),
                            _href = URL(c="project", f = "framework", args = "review")
                            ),
                          A(T("Approve Organisations"),
                            _href = URL(c="org", f = "organisation", args = "review")
                            ),
                          A(T("Edit Countries and Administrative Areas"),
                            _href = URL(c="gis", f = "location")
                            ),
                          A(T("Edit Hazards"),
                            _href = URL(c="project", f = "hazard")
                            ),
                          A(T("Edit Themes"),
                            _href = URL(c="project", f = "theme")
                            ),
                         ]
            
            return dict(item = UL(*panel_list,
                                  _id = "admin_panel_list") )
        else:
            redirect(URL(c="default", f="index"))

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
                         THEME, "views", "analysis.html")
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
class get_started():
    """
        Custom page
    """

    def __call__(self):
        response = current.response
        request = current.request
        T = current.T

        view = path.join(request.folder, "private", "templates",
                         THEME, "views", "get_started.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        response.title = T("Get Started")

        return dict(
        )

# =============================================================================
class login():
    """
        Custom Login page
    """

    def __call__(self):
        response = current.response
        request = current.request
        T = current.T

        view = path.join(request.folder, "private", "templates",
                         THEME, "views", "login.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        response.title = T("Login")

        request.args = ["login"]
        login = current.auth()

        return dict(
            form = login
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
                             THEME, "views", "mypage.html")
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
            redirect(URL(c="pr", f="person", args=[person_id, "saved_search"]))

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

        current.response.s3["dataTable_sDom"] = 'ripl<"dataTable_table"t>p'

        response.title = "DRR Projects Portal - Regional Organizations"
        view = path.join(request.folder, "private", "templates",
                         THEME, "views", "organisations.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        tables = []
        table = request.vars.get("table", None)

        # URL format breaks the REST controller conventions
        #request.args.pop()

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
            Regional Organisations
            - Filtered subset of Organisations
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
            (T("Notes"), "comments"),
        ]
        return (s3request, field_list)

    # -------------------------------------------------------------------------
    @staticmethod
    def _groups():
        """
            Committees/Mechanisms/Forums & Networks
            - Filtered subset of Organisations
        """

        from s3 import S3FieldSelector, s3_request
        T = current.T

        s3db = current.s3db
        table = s3db.org_organisation
        table.virtualfields.append(s3db.org_organisation_address_virtual_field())

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
            (T("Address"), "address"),
            (T("Notes"), "comments"),
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

        records = resource.select(fields=field_list,
                                  start=None,
                                  limit=None,
                                  orderby=orderby,
                                  #as_page=True,
                                  )

        if records is None:
            records = []

        rows = []
        rsappend = rows.append
        represent = current.manager.represent
        for record in records:
            row = []
            rappend = row.append
            for field in fields:
                if isinstance(field, basestring):
                    rappend(record[field])
                else:
                    rappend(represent(field=field, record=record))

            rsappend(row)

        options = json.dumps({
            "iDisplayLength": limit,
            "iDeferLoading": resource.count(),
            "bProcessing": True,
            #"bServerSide": True,
            #"sAjaxSource": "/%s/default/index/organisations/?table=%s" % (current.request.application, name),
            "aoColumnDefs": [{"bVisible": False,
                              "aTargets": [0]
                              }],
            "aoColumns": [{"sName": col["name"]} for col in cols],
            "sDom": 'rifpl<"dataTable_table"t>p'
        })

        table = Storage(cols=cols,
                        rows=rows,
                        options=options,
                        classes="dataTable display"
                        )

        return table

# END =========================================================================
