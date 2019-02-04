# -*- coding: utf-8 -*-

from gluon import *
from s3 import S3CustomController

THEME = "HowCalm"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        T = current.T

        output = {}

        text = T("HOWCALM™ provides essential information to help coordinate response and manage long-term recovery in a disaster. Participation in HOWCALM™ enables us to provide you with emergency information before, during and after a disaster. We also will send you geographically tailored information about evacuation zones, relevant news, and information about preparedness trainings for your staff and house of worship.")
        output["text"] = text
        output["img_url"] = URL(c="static", f="themes", args=[THEME, "img", "logo.gif"])

        # Login/Registration forms
        self_registration = current.deployment_settings.get_security_registration_visible()
        registered = False
        login_form = None
        login_div = None
        register_form = None
        register_div = None

        # Check logged in and permissions
        auth = current.auth
        if not auth.s3_logged_in():
            jqappend = current.response.s3.jquery_ready.append
            #login_buttons = DIV(A(T("Login"),
            #                      _id="show-login",
            #                      _class="tiny secondary button"),
            #                    _id="login-buttons"
            #                    )
            # @ToDo: Move JS to static
            #script = '''
#$('#show-intro').click(function(e){
# e.preventDefault()
# $('#intro').slideDown(400, function() {
#   $('#login_box').hide()
# });
#})
#$('#show-login').click(function(e){
# e.preventDefault()
# $('#login_form').show()
# $('#register_form').hide()
# $('#login_box').show()
# $('#intro').slideUp()
#})'''
            #jqappend(script)

            # This user isn't yet logged-in
            if current.request.cookies.has_key("registered"):
                # This browser has logged-in before
                registered = True

            if self_registration is True:
                # Provide a Registration box on front page
                #login_buttons.append(A(T("Register"),
                #                       _id="show-register",
                #                       _class="tiny secondary button",
                #                       # @ToDo: Move to CSS
                #                       _style="margin-left:5px"))
                #script = '''
#$('#show-register').click(function(e){
# e.preventDefault()
# $('#login_form').hide()
# $('#register_form').show()
# $('#login_box').show()
# $('#intro').slideUp()
#})'''
                #jqappend(script)

                register_form = auth.register()
                register_div = DIV(H3(T("Register")),
                                   P(XML(T("If you would like to help, then please %(sign_up_now)s") % \
                                     {"sign_up_now": B(T("sign-up now"))})))

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
                jqappend(register_script)

            # Provide a login box on front page
            auth.messages.submit_button = T("Login")
            login_form = auth.login(inline=True)
            login_div = DIV(H3(T("Login")),
                            P(XML(T("Registered users can %(login)s to access the system") % \
                              {"login": B(T("login"))})))

        #else:
        #    login_buttons = ""

        #output["login_buttons"] = login_buttons
        output["self_registration"] = self_registration
        output["registered"] = registered
        output["login_div"] = login_div
        output["login_form"] = login_form
        output["register_div"] = register_div
        output["register_form"] = register_form

        self._view(THEME, "index.html")
        return output

# END =========================================================================
