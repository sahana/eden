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
class index():
    """ Custom Home Page """

    def __call__(self):

        request = current.request
        response = current.response

        view = path.join(request.folder, "private", "templates",
                         "CERT", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        appname = request.application
        settings = current.deployment_settings
        title = settings.get_system_name()
        response.title = title

        T = current.T

        # Check logged in and permissions
        auth = current.auth
        roles = current.session.s3.roles
        system_roles = auth.get_system_roles()
        #ADMIN = system_roles.ADMIN
        AUTHENTICATED = system_roles.AUTHENTICATED
        #s3_has_role = auth.s3_has_role

        # Menu Boxes
        # NB Order defined later (in sit_dec_res_box)
        menu_btns = [#div, label, app, function, is_icon
                    ["vol", T("View Volunteers"), "vol", "volunteer/search", True],
                    ["vol", T("View Volunteers"), "vol", "volunteer/search", False],
                    ["vol", T("Add Volunteer"), "vol", "volunteer/create", False],
                    ["qua", T("View Qualifications"), "vol", "certificate", True],
                    ["qua", T("View Qualifications"), "vol", "certificate", False],
                    ["qua", T("Add Qualification"), "vol", "certificate/create", False],
                    ["evt", T("View Event"), "vol", "event", True],
                    ["evt", T("View Events"), "vol", "event", False],
                    ["evt", T("Add Event"), "vol", "event/create", False],
                    ["adm", T("Deploy Volunteers"), "vol", "event", True],
                    ["adm", T("Deploy Volunteers"), "vol", "event", False],
                    ["not", T("Send Notification"), "msg", "compose", True],
                    ["not", T("Send Notification"), "msg", "compose", False],
                    ["rep", T("View Reports"), "vol", "experience/report", True],
                    ["rep", T("View Reports"), "vol", "experience/report", False],
                    ]

        # NB Order defined later (in sit_dec_res_box)
        menu_divs = {"facility": DIV(H3(T("Facilities")),
                                     _id = "facility_box",
                                     _class = "menu_box",
                                     ),
                     "vol": DIV(H3(T("Volunteers")),
                                _id = "menu_div_vol",
                                _class = "menu_div",
                                ),
                     "qua": DIV(H3(T("Qualifications")),
                                _id = "menu_div_qua",
                                _class = "menu_div",
                                ),
                     "evt": DIV(H3(A(T("Events")),
                                   _href="blue"),
                                _id = "menu_div_evt",
                                _class = "menu_div",
                                ),
                     "adm": DIV(H3(T("Volunteer Admin")),
                                _id = "menu_div_adm",
                                _class = "menu_div",
                                ),
                     "not": DIV(H3(T("Notifications")),
                                _id = "menu_div_not",
                                _class = "menu_div",
                                ),
                     "rep": DIV(H3(T("Reports")),
                                _id = "menu_div_rep",
                                _class = "menu_div",
                                ),
                    }

        for div, label, app, function, is_icon in menu_btns:
            if settings.has_module(app):
                # @ToDo: Also check permissions (e.g. for anonymous users)
                if is_icon:
                    menu_divs[div].append(A(DIV(label,
                                                _class = "icon"),
                                            _href = URL(app, function),
                                            _class = "",
                                            )
                                          )
                else:
                    menu_divs[div].append(DIV(A(label,
                                                _href = URL(app, function),
                                                _class = "",
                                                )
                                              )
                                          )

        div_clear = DIV(T(""),
                        _class="clear")

        sit_dec_res_box = DIV(menu_divs["vol"],
                              menu_divs["qua"],
                              menu_divs["evt"],
                              div_clear,
                              menu_divs["adm"],
                              menu_divs["not"],
                              menu_divs["rep"],
                              _id = "sit_dec_res_box",
                              _class = "menu_box fleft swidth"
                              )

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
                register_form = auth.s3_registration_form()
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
                response.s3.jquery_ready.append(register_script)

            # Provide a login box on front page
            request.args = ["login"]
            auth.messages.submit_button = T("Login")
            login_form = auth()
            login_div = DIV(H3(T("Login")),
                            P(XML(T("Registered users can %(login)s to access the system") % \
                                  dict(login=B(T("login"))))))

        return dict(title = title,
                    sit_dec_res_box = sit_dec_res_box,
                    self_registration=self_registration,
                    registered=registered,
                    login_form=login_form,
                    login_div=login_div,
                    register_form=register_form,
                    register_div=register_div
                    )

# END =========================================================================
