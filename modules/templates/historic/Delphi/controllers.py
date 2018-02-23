# -*- coding: utf-8 -*-

from gluon import current
from gluon.html import *

from s3 import S3CustomController

THEME = "historic.Delphi"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        T = current.T
        auth = current.auth
        db = current.db
        request = current.request
        response = current.response
        s3 = response.s3
        settings = current.deployment_settings

        title = settings.get_system_name()
        response.title = title

        # Check logged in AND permissions
        _s3 = current.session.s3
        AUTHENTICATED = _s3.system_roles.AUTHENTICATED
        roles = _s3.roles

        # Login/Registration forms
        self_registration = settings.get_security_registration_visible()
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

        self._view(THEME, "index.html")
        return dict(title = title,
                    self_registration=self_registration,
                    registered=registered,
                    login_form=login_form,
                    login_div=login_div,
                    register_form=register_form,
                    register_div=register_div
                    )

# END =========================================================================
