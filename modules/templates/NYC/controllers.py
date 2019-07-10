# -*- coding: utf-8 -*-

from gluon import *
from s3 import S3CustomController, S3DataTable, S3Method, s3_request

THEME = "NYC"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        T = current.T
        s3 = current.response.s3

        auth = current.auth
        settings = current.deployment_settings
        roles = current.session.s3.roles
        system_roles = auth.get_system_roles()

        # Allow editing of page content from browser using CMS module
        if settings.has_module("cms"):
            ADMIN = system_roles.ADMIN in roles
            s3db = current.s3db
            table = s3db.cms_post
            ltable = s3db.cms_post_module
            module = "default"
            resource = "index"
            query = (ltable.module == module) & \
                    ((ltable.resource == None) | \
                     (ltable.resource == resource)) & \
                    (ltable.post_id == table.id) & \
                    (table.deleted != True)
            item = current.db(query).select(table.id,
                                            table.body,
                                            limitby=(0, 1)).first()
            if item:
                if ADMIN:
                    item = DIV(XML(item.body),
                               BR(),
                               A(current.T("Edit"),
                                 _href=URL(c="cms", f="post",
                                           args=[item.id, "update"]),
                                 _class="action-btn"))
                else:
                    item = DIV(XML(item.body))
            elif ADMIN:
                if s3.crud.formstyle == "bootstrap":
                    _class = "btn"
                else:
                    _class = "action-btn"
                item = A(T("Edit"),
                         _href=URL(c="cms", f="post", args="create",
                                   vars={"module": module,
                                         "resource": resource
                                         }),
                         _class="%s cms-edit" % _class)
            else:
                item = ""
        else:
            item = ""
        output["item"] = item

        # Login/Registration forms
        self_registration = settings.get_security_registration_visible()
        registered = False
        login_form = None
        login_div = None
        register_form = None
        register_div = None

        # Check logged in and permissions
        if system_roles.AUTHENTICATED not in roles:

            login_buttons = DIV(A(T("Login"),
                                  _id="show-login",
                                  _class="tiny secondary button"),
                                _id="login-buttons"
                                )
            # @ToDo: Move JS to static
            script = '''
$('#show-intro').click(function(e){
 e.preventDefault()
 $('#intro').slideDown(400, function() {
   $('#login_box').hide()
 });
})
$('#show-login').click(function(e){
 e.preventDefault()
 $('#login_form').show()
 $('#register_form').hide()
 $('#login_box').show()
 $('#intro').slideUp()
})'''
            s3.jquery_ready.append(script)

            # This user isn't yet logged-in
            if "registered" in current.request.cookies:
                # This browser has logged-in before
                registered = True

            if self_registration is True:
                # Provide a Registration box on front page
                login_buttons.append(A(T("Register"),
                                       _id="show-register",
                                       _class="tiny secondary button",
                                       # @ToDo: Move to CSS
                                       _style="margin-left:5px"))
                script = '''
$('#show-register').click(function(e){
 e.preventDefault()
 $('#login_form').hide()
 $('#register_form').show()
 $('#login_box').show()
 $('#intro').slideUp()
})'''
                s3.jquery_ready.append(script)

                register_form = auth.register()
                register_div = DIV(H3(T("Register")),
                                   P(XML(T("If you would like to help, then please %(sign_up_now)s") % \
                                            dict(sign_up_now=B(T("sign-up now"))))))

                register_script = '''
$('#register-btn').click(function(e){
 e.preventDefault()
 $('#register_form').show()
 $('#login_form').hide()
})
$('#login-btn').click(function(e){
 e.preventDefault()
 $('#register_form').hide()
 $('#login_form').show()
})'''
                s3.jquery_ready.append(register_script)

            # Provide a login box on front page
            auth.messages.submit_button = T("Login")
            login_form = auth.login(inline=True)
            login_div = DIV(H3(T("Login")),
                            P(XML(T("Registered users can %(login)s to access the system") % \
                                  dict(login=B(T("login"))))))

        else:
            login_buttons = ""

        output["login_buttons"] = login_buttons
        output["self_registration"] = self_registration
        output["registered"] = registered
        output["login_div"] = login_div
        output["login_form"] = login_form
        output["register_div"] = register_div
        output["register_form"] = register_form

        output["items"] = network()()

        self._view(THEME, "index.html")
        return output

# -----------------------------------------------------------------------------
class network():
    """
        Function to handle pagination for the network list on the homepage
    """

    @staticmethod
    def __call__():

        request = current.request
        get_vars = request.get_vars
        representation = request.extension

        resource = current.s3db.resource("org_group")
        totalrows = resource.count()
        display_start = int(get_vars.displayStart) if get_vars.displayStart else 0
        display_length = int(get_vars.pageLength) if get_vars.pageLength else 10
        limit = 4 * display_length

        list_fields = ("id",
                       "name",
                       "mission",
                       "website",
                       "meetings",
                       )
        default_orderby = orderby = "org_group.name asc"
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
        current.response.s3.no_formats = True

        if representation == "html":
            items = dt.html(totalrows,
                            totalrows,
                            "org_dt",
                            dt_ajax_url=URL(c="default",
                                            f="index",
                                            args="network",
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

# =============================================================================
class contact(S3CustomController):
    """
        Contact Form

        @ToDo: i18n if-required
    """

    def __call__(self):

        request = current.request
        response = current.response
        s3 = response.s3
        settings = current.deployment_settings

        if request.env.request_method == "POST":
            # Processs Form
            vars = request.post_vars
            result = current.msg.send_email(to=settings.get_mail_approver(),
                                            subject=vars.subject,
                                            message=vars.message,
                                            reply_to=vars.address,
                                            )
            if result:
                response.confirmation = "Thankyou for your message - we'll be in touch shortly"

        T = current.T

        # Allow editing of page content from browser using CMS module
        if settings.has_module("cms"):
            ADMIN = current.auth.get_system_roles().ADMIN in \
                    current.session.s3.roles
            s3db = current.s3db
            table = s3db.cms_post
            ltable = s3db.cms_post_module
            module = "default"
            resource = "contact"
            query = (ltable.module == module) & \
                    ((ltable.resource == None) | \
                     (ltable.resource == resource)) & \
                    (ltable.post_id == table.id) & \
                    (table.deleted != True)
            item = current.db(query).select(table.id,
                                            table.body,
                                            limitby=(0, 1)).first()
            if item:
                if ADMIN:
                    item = DIV(XML(item.body),
                               BR(),
                               A(T("Edit"),
                                 _href=URL(c="cms", f="post",
                                           args=[item.id, "update"]),
                                 _class="action-btn"))
                else:
                    item = DIV(XML(item.body))
            elif ADMIN:
                if s3.crud.formstyle == "bootstrap":
                    _class = "btn"
                else:
                    _class = "action-btn"
                item = A(T("Edit"),
                         _href=URL(c="cms", f="post", args="create",
                                   vars={"module": module,
                                         "resource": resource
                                         }),
                         _class="%s cms-edit" % _class)
            else:
                item = ""
        else:
            item = ""

        form = FORM(TABLE(
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

        # @ToDo: Move to static with i18n
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
        # @ToDo: Move to static
        s3.jquery_ready.append(
'''$('textarea.resizable:not(.textarea-processed)').each(function() {
    // Avoid non-processed teasers.
    if ($(this).is(('textarea.teaser:not(.teaser-processed)'))) {
        return false;
    }
    var textarea = $(this).addClass('textarea-processed'), staticOffset = null;
    // When wrapping the text area, work around an IE margin bug. See:
    // http://jaspan.com/ie-inherited-margin-bug-form-elements-and-haslayout
    $(this).wrap('<div class="resizable-textarea"><span></span></div>')
    .parent().append($('<div class="grippie"></div>').mousedown(startDrag));
    var grippie = $('div.grippie', $(this).parent())[0];
    grippie.style.marginRight = (grippie.offsetWidth - $(this)[0].offsetWidth) +'px';
    function startDrag(e) {
        staticOffset = textarea.height() - e.pageY;
        textarea.css('opacity', 0.25);
        $(document).mousemove(performDrag).mouseup(endDrag);
        return false;
    }
    function performDrag(e) {
        textarea.height(Math.max(32, staticOffset + e.pageY) + 'px');
        return false;
    }
    function endDrag(e) {
        $(document).unbind("mousemove", performDrag).unbind("mouseup", endDrag);
        textarea.css('opacity', 1);
    }
});''')

        response.title = "Contact | NYC:Prepared"
        self._view(THEME, "contact.html")
        return dict(form=form,
                    item=item,
                    )

# =============================================================================
class register(S3CustomController):
    """ Registration Form """

    def __call__(self):

        auth = current.auth
        response = current.response

        # Allow editing of page content from browser using CMS module
        ADMIN = auth.get_system_roles().ADMIN in \
                current.session.s3.roles
        s3db = current.s3db
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        module = "default"
        resource = "register"
        query = (ltable.module == module) & \
                ((ltable.resource == None) | \
                 (ltable.resource == resource)) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.id,
                                        table.body,
                                        limitby=(0, 1)).first()
        if item:
            if ADMIN:
                item = DIV(XML(item.body),
                           BR(),
                           A(current.T("Edit"),
                             _href=URL(c="cms", f="post",
                                       args=[item.id, "update"]),
                             _class="action-btn"))
            else:
                item = DIV(XML(item.body))
        elif ADMIN:
            if response.s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            item = A(current.T("Edit"),
                     _href=URL(c="cms", f="post", args="create",
                               vars={"module": module,
                                     "resource": resource
                                     }),
                     _class="%s cms-edit" % _class)
        else:
            item = ""

        form = auth.register()

        response.title = "Register | NYC Prepared"
        self._view(THEME, "register.html")
        return dict(form=form,
                    item=item,
                    )

# =============================================================================
class dashboard(S3CustomController):
    """ Custom controller for personal dashboard """

    def __call__(self):

        auth = current.auth
        if not auth.s3_logged_in():
            auth.permission.fail()

        # Use custom method
        current.s3db.set_method("pr", "person",
                                method = "dashboard",
                                action = PersonalDashboard,
                                )

        # Call for currently logged-in person
        r = s3_request("pr", "person",
                       args=[str(auth.s3_logged_in_person()),
                             "dashboard.%s" % auth.permission.format,
                             ],
                       r = current.request,
                       )

        return r()

# =============================================================================
class PersonalDashboard(S3Method):
    """ Custom method for personal dashboard """

    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the request (S3Request)
            @param attr: REST controller parameters
        """

        if r.record and r.representation in ("html", "aadata"):

            T = current.T
            db = current.db
            s3db = current.s3db

            auth = current.auth
            is_admin = auth.s3_has_role("ADMIN")
            accessible = auth.s3_accessible_query

            # Profile widgets
            profile_widgets = []
            add_widget = profile_widgets.append

            dt_row_actions = self.dt_row_actions
            from s3 import FS

            # Organisations
            widget = {"label": T("My Organizations"),
                      "icon": "organisation",
                      "insert": False,
                      "tablename": "org_organisation",
                      "type": "datatable",
                      "actions": dt_row_actions("org", "organisation"),
                      "list_fields": ["name",
                                      (T("Type"), "organisation_organisation_type.organisation_type_id"),
                                      "phone",
                                      (T("Email"), "email.value"),
                                      "website",
                                      ],
                      }
            if not is_admin:
                otable = s3db.org_organisation
                rows = db(accessible("update", "org_organisation")).select(otable.id)
                organisation_ids = [row.id for row in rows]
                widget["filter"] = FS("id").belongs(organisation_ids)
            add_widget(widget)

            # Facilities
            widget = {"label": T("My Facilities"),
                      "icon": "facility",
                      "insert": False,
                      "tablename": "org_facility",
                      "type": "datatable",
                      "actions": dt_row_actions("org", "facility"),
                      "list_fields": ["name",
                                      "code",
                                      "site_facility_type.facility_type_id",
                                      "organisation_id",
                                      "location_id",
                                      ],
                      }
            if not is_admin:
                ftable = s3db.org_facility
                rows = db(accessible("update", "org_facility")).select(ftable.id)
                facility_ids = [row.id for row in rows]
                widget["filter"] = FS("id").belongs(facility_ids)
            add_widget(widget)

            # Networks (only if user can update any records)
            widget_filter = None
            if not is_admin:
                gtable = s3db.org_group
                rows = db(accessible("update", "org_group")).select(gtable.id)
                group_ids = [row.id for row in rows]
                if group_ids:
                    widget_filter = FS("id").belongs(group_ids)
            if is_admin or widget_filter:
                widget = {"label": T("My Networks"),
                          "icon": "org-network",
                          "insert": False,
                          "tablename": "org_group",
                          "filter": widget_filter,
                          "type": "datatable",
                          "actions": dt_row_actions("org", "group"),
                          }
                add_widget(widget)

            # Groups (only if user can update any records)
            widget_filter = None
            if not is_admin:
                gtable = s3db.pr_group
                rows = db(accessible("update", "pr_group")).select(gtable.id)
                group_ids = [row.id for row in rows]
                if group_ids:
                    widget_filter = FS("id").belongs(group_ids)
            if is_admin or widget_filter:
                widget = {"label": T("My Groups"),
                          "icon": "group",
                          "insert": False,
                          "tablename": "pr_group",
                          "filter": widget_filter,
                          "type": "datatable",
                          "actions": dt_row_actions("hrm", "group"),
                          "list_fields": [(T("Network"), "group_team.org_group_id"),
                                          "name",
                                          "description",
                                          (T("Chairperson"), "chairperson"),
                                          ],
                          }
                add_widget(widget)

            # CMS Content
            from gluon.html import A, DIV, H2, TAG
            item = None
            title = T("Dashboard")
            if current.deployment_settings.has_module("cms"):
                name = "Dashboard"
                ctable = s3db.cms_post
                query = (ctable.name == name) & (ctable.deleted != True)
                row = db(query).select(ctable.id,
                                       ctable.title,
                                       ctable.body,
                                       limitby=(0, 1)).first()
                get_vars = {"page": name,
                            "url": URL(args="dashboard", vars={}),
                            }
                if row:
                    title = row.title
                    if is_admin:
                        item = DIV(XML(row.body),
                                   DIV(A(T("Edit"),
                                         _href=URL(c="cms", f="post",
                                                   args=[row.id, "update"],
                                                   vars=get_vars,
                                                   ),
                                         _class="action-btn",
                                         ),
                                       _class="cms-edit",
                                       ),
                                   )
                    else:
                        item = DIV(XML(row.body))
                elif is_admin:
                    item = DIV(DIV(A(T("Edit"),
                                     _href=URL(c="cms", f="post",
                                               args="create",
                                               vars=get_vars,
                                               ),
                                     _class="action-btn",
                                     ),
                                   _class="cms-edit",
                                   )
                               )

            # Rheader
            if r.representation == "html":
                # Dashboard title
                profile_header = TAG[""](DIV(DIV(H2(title),
                                                 _class="medium-6 columns end",
                                                 ),
                                             _class="row",
                                             )
                                         )
                # CMS content
                if item:
                    profile_header.append(DIV(DIV(item,
                                                  _class="medium-12 columns",
                                                  ),
                                              _class="row",
                                              ))
                # Dashboard links
                dashboard_links = DIV(A(T("Personal Profile"),
                                        _href = URL(c="default", f="person"),
                                        _class = "action-btn",
                                        ),
                                      _class="dashboard-links",
                                      _style="padding:0.5rem 0;"
                                      )

                profile_header.append(DIV(DIV(dashboard_links,
                                              _class="medium-12 columns",
                                              ),
                                          _class="row",
                                          ))
            else:
                profile_header = None

            # Configure profile
            tablename = r.tablename
            s3db.configure(tablename,
                           profile_cols = 2,
                           profile_header = profile_header,
                           profile_widgets = profile_widgets,
                           )

            # Render profile
            from s3 import S3Profile
            profile = S3Profile()
            profile.tablename = tablename
            profile.request = r
            output = profile.profile(r, **attr)

            if r.representation == "html":
                output["title"] = \
                current.response.title = T("Personal Dashboard")
            return output
        else:
            r.error(405, current.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    @staticmethod
    def dt_row_actions(c, f):
        """ Data table row actions """

        return lambda r, list_id: [
            {"label": current.deployment_settings.get_ui_label_update(),
             "url": URL(c=c, f=f, args=["[id]", "update"]),
             "_class": "action-btn edit",
             },
        ]

# END =========================================================================
