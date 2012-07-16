# -*- coding: utf-8 -*-

from os import path

from gluon import current
from gluon.html import *

from s3 import s3_represent_facilities, s3_register_validation

# =============================================================================
class index():
    """ Custom Home Page """

    def __call__(self):

        T = current.T
        auth = current.auth
        db = current.db
        request = current.request
        appname = request.application
        response = current.response
        s3 = response.s3
        settings = current.deployment_settings

        view = path.join(request.folder, "private", "templates",
                         "RGIMS", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        title = settings.get_system_name()
        response.title = title

        # Menu Boxes
        menu_btns = [#div, label, app, function
                    ["sit", T("Request"), "req", "req"],
                    ["dec", T("Send"), "inv", "send"],
                    ["res", T("Receive"), "inv", "recv"]
                    ]

        menu_divs = {"facility": DIV( H3("Map"),
                                  _id = "facility_box", _class = "menu_box"),
                     "sit": DIV(
                                  _id = "menu_div_sit", _class = "menu_div"),
                     "dec": DIV(
                                  _id = "menu_div_dec", _class = "menu_div"),
                     "res": DIV(
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

        # Check logged in AND permissions
        _s3 = current.session.s3
        AUTHENTICATED = _s3.system_roles.AUTHENTICATED
        roles = _s3.roles
        if AUTHENTICATED in roles and \
           auth.s3_has_permission("read", db.org_organisation):
            auth.permission.controller = "org"
            auth.permission.function = "site"
            permitted_facilities = auth.permitted_facilities(redirect_on_error=False)
            manage_facility_box = ""
            if permitted_facilities:
                facility_list = s3_represent_facilities(db, permitted_facilities,
                                                        link=False)
                facility_list = sorted(facility_list, key=lambda fac: fac[1])
                facility_opts = [OPTION(opt[1], _value = opt[0])
                                 for opt in facility_list]
                facility_opts.insert(0, OPTION("Please Select a Warehouse"))
                if facility_list:
                    manage_facility_box = DIV(H3(T("Manage Your Warehouse")),
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
                    s3.jquery_ready.append(
'''$('#manage_facility_select').change(function(){
 $('#manage_facility_btn').attr('href',S3.Ap.concat('/default/site/',$('#manage_facility_select').val()))
})''')
                else:
                    manage_facility_box = DIV()

        else:
            manage_facility_box = ""
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
                s3_register_validation()

                if s3.debug:
                    s3.scripts.append("/%s/static/scripts/jquery.validate.js" % appname)
                else:
                    s3.scripts.append("/%s/static/scripts/jquery.validate.min.js" % appname)
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

        return dict(title = title,
                    sit_dec_res_box = sit_dec_res_box,
                    facility_box = facility_box,
                    manage_facility_box = manage_facility_box,
                    self_registration=self_registration,
                    registered=registered,
                    login_form=login_form,
                    login_div=login_div,
                    register_form=register_form,
                    register_div=register_div
                    )

# END =========================================================================
