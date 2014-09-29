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
        s3 = current.response.s3

        # Check logged in and permissions
        auth = current.auth
        settings = current.deployment_settings
        roles = current.session.s3.roles
        system_roles = auth.get_system_roles()
        AUTHENTICATED = system_roles.AUTHENTICATED

        # Login/Registration/Contact forms
        self_registration = current.deployment_settings.get_security_self_registration()
        registered = False
        login_form = None
        login_div = None
        register_form = None
        register_div = None
        contact_form = DIV(
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
                        TR(INPUT(_type="submit", _class="small button primary btn", _value="Send e-mail")),
                        ),
                    _id="mailform"
                    )
                )

        if AUTHENTICATED not in roles:
            # This user isn't yet logged-in
            if request.cookies.has_key("registered"):
                # This browser has logged-in before
                registered = True

            if self_registration is True:
                # Provide a Registration box on front page
                register_form = auth.register()
                register_div = DIV(H3(T("Register")),
                                   P(XML(T("If you would like to help, then please %(sign_up_now)s") % \
                                            dict(sign_up_now=B(T("sign-up now"))))))

                if request.env.request_method == "POST":
                    # Processs Contact Form
                    vars = request.post_vars
                    result = current.msg.send_email(
                            to="athewaas.requests@revivekashmir.org",
                            subject=vars.subject,
                            message=vars.message,
                            reply_to=vars.address,
                        )
                    if result:
                        response.confirmation = "Thank you for your message - we'll be in touch shortly"
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


        output["self_registration"] = self_registration
        output["registered"] = registered
        output["login_div"] = login_div
        output["login_form"] = login_form
        output["register_div"] = register_div
        output["register_form"] = register_form
        output["contact_form"] = contact_form

        self._view(TEMPLATE, "index.html")
        return output

# END =========================================================================
