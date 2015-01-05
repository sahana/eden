# -*- coding: utf-8 -*-

from os import path

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import current
from gluon.html import *
from gluon.storage import Storage
from gluon.http import redirect

from s3 import FS, S3CustomController
from s3theme import formstyle_foundation_inline

TEMPLATE = "Kashmir"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        T = current.T
        request = current.request
        response = current.response
        s3 = response.s3

        # Check logged in and permissions
        auth = current.auth
        settings = current.deployment_settings
        roles = current.session.s3.roles
        system_roles = auth.get_system_roles()
        AUTHENTICATED = system_roles.AUTHENTICATED

        # Login/Registration forms
        self_registration = current.deployment_settings.get_security_self_registration()
        registered = False
        login_form = None
        login_div = None
        register_form = None
        register_div = None

        # Contact Form
        request_email = settings.get_frontpage("request_email")
        if request_email:
            from gluon.dal import Field
            from gluon.validators import IS_NOT_EMPTY
            from gluon.sqlhtml import SQLFORM
            fields = [Field("name",
                            label="Your name",
                            requires=IS_NOT_EMPTY(),
                            ),
                      Field("address",
                            label="Your e-mail address",
                            requires=IS_NOT_EMPTY(),
                            ),
                      Field("subject",
                            label="Subject",
                            requires=IS_NOT_EMPTY(),
                            ),
                      Field("message", "text",
                            label="Message",
                            requires=IS_NOT_EMPTY(),
                            ),
                      ]
            from s3 import s3_mark_required
            labels, required = s3_mark_required(fields)
            s3.has_required = required

            response.form_label_separator = ""
            contact_form = SQLFORM.factory(formstyle = settings.get_ui_formstyle(),
                                           submit_button = T("Submit"),
                                           labels = labels,
                                           separator = "",
                                           table_name = "contact", # Dummy table name
                                           _id="mailform",
                                           *fields
                                           )

            if contact_form.accepts(request.post_vars,
                                    current.session,
                                    formname="contact_form",
                                    keepvalues=False,
                                    hideerror=False):
                # Processs Contact Form
                form_vars = contact_form.vars
                sender = "%s <%s>" % (form_vars.name, form_vars.address)
                result = current.msg.send_email(to=request_email,
                                                sender=sender,
                                                subject=form_vars.subject,
                                                message=form_vars.message,
                                                reply_to=form_vars.address,
                                                )
                if result:
                    response.confirmation = "Thank you for your message - we'll be in touch shortly"
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
            validation_script = '''
$('#mailform').validate({
 errorClass:'req',
 rules:{
  name:{
   required:true
  },
  address: {
   required:true,
   email:true
  },
  subject:{
   required:true
  },
  message:{
   required:true
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
  error.appendTo(element.parents('div.controls'))
 },
 submitHandler:function(form){
  form.submit()
 }
})'''
            s3.jquery_ready.append(validation_script)

        else:
            contact_form = ""

        if AUTHENTICATED not in roles:

            login_buttons = DIV(A(T("Login"),
                                  _id="show-login",
                                  _class="tiny secondary button"),
                                _id="login-buttons"
                                )
            script = '''
$('#show-mailform').click(function(e){
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
            if request.cookies.has_key("registered"):
                # This browser has logged-in before
                registered = True

            if self_registration is True:
                # Provide a Registration box on front page
                login_buttons.append(A(T("Register"),
                                       _id="show-register",
                                       _class="tiny secondary button",
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
        output["contact_form"] = contact_form

        # Slick slider
        if s3.debug:
            s3.scripts.append("/%s/static/scripts/slick.js" % request.application)
        else:
            s3.scripts.append("/%s/static/scripts/slick.min.js" % request.application)
        script = '''
$(document).ready(function(){
 $('#title-image').slick({
  autoplay:true,
  autoplaySpeed:5000,
  speed:1000,
  fade:true,
  cssEase:'linear'
 });
});'''
        s3.jquery_ready.append(script)

        self._view(TEMPLATE, "index.html")
        return output

# =============================================================================
class listoforganizations(S3CustomController):
    """ Custom Page for rendering list of participating organizations """

    def __call__(self):

        self._view(TEMPLATE, "listoforg.html")
        return {"title": "List of Participating Organizations"}

# =============================================================================
class about(S3CustomController):
    """ Custom Page for rendering about"""

    def __call__(self):

        #redirect('https://docs.google.com/a/iquasar.com/file/d/0B3_TmWrJ52YBRmNoVVBhZkI1ZG8/edit')
        self._view(TEMPLATE, "about.html")
        return {}

# =============================================================================
class contact(S3CustomController):
    """ Custom Page for rendering contact us """

    def __call__(self):

        self._view(TEMPLATE, "contact.html")
        return {}

# =============================================================================
class userguide(S3CustomController):
     """ User Guide """

     def __call__(self):

        self._view(TEMPLATE, "userguide.html")
        return {}

# END =========================================================================
