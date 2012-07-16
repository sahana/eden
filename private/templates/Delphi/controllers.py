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
                         "Delphi", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        title = settings.get_system_name()
        response.title = title

        # Check logged in AND permissions
        _s3 = current.session.s3
        AUTHENTICATED = _s3.system_roles.AUTHENTICATED
        roles = _s3.roles

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
                    self_registration=self_registration,
                    registered=registered,
                    login_form=login_form,
                    login_div=login_div,
                    register_form=register_form,
                    register_div=register_div
                    )

# END =========================================================================
