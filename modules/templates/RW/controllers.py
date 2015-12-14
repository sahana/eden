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

from s3 import FS, ICON, S3CustomController
from s3theme import formstyle_foundation_inline

TEMPLATE = "RW"

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
        self_registration = settings.get_security_registration_visible()
        registered = False
        login_form = None
        login_div = None
        register_form = None
        register_div = None

        # Project Links
        project_links = DIV(_class="title-links hide-for-small")
        project_description = settings.get_frontpage("project_description")
        if project_description:
            project_links.append(A(ICON("link"), T("Project Description"),
                                   _class = "action-lnk",
                                   _href = project_description,
                                   _target = "_blank",
                                   ))
        project_links.append(A(ICON("link"), T("User Manual"),
                               _class = "action-lnk",
                               _href = URL(c="default", f="index",
                                           args = ["docs"],
                                           vars = {"name": "UserManual"},
                                           ),
                               _target = "_blank",
                               ))
        mailing_list = settings.get_frontpage("mailing_list")
        if mailing_list:
            project_links.append(A(ICON("link"), T("Mailing List"),
                                   _class = "action-lnk",
                                   _href = mailing_list,
                                   _target = "_blank",
                                   ))

        # Contact Form
        request_email = settings.get_frontpage("request_email")
        if request_email:
            from s3dal import Field
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
 $('#login_box').fadeOut(function(){$('#intro').fadeIn()})
})
$('#show-login').click(function(e){
 e.preventDefault()
 $('#login_form').show()
 $('#register_form').hide()
 $('#intro').fadeOut(function(){$('#login_box').fadeIn()})
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
 $('#intro').fadeOut(function(){$('#login_box').fadeIn()})
})'''
                s3.jquery_ready.append(script)

                register_form = auth.register()
                register_div = DIV(H3(T("Register")),
                                   P(XML(T("If you would like to help, then please %(sign_up_now)s") % \
                                            dict(sign_up_now=B(T("sign-up now"))))))

                register_script = '''
$('#register-btn').click(function(e){
 e.preventDefault()
 $('#login_form').fadeOut(function(){$('#register_form').fadeIn()})
})
$('#login-btn').click(function(e){
 e.preventDefault()
 $('#register_form').fadeOut(function(){$('#login_form').fadeIn()})
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

        # Create output dict
        output = {"login_buttons": login_buttons,
                  "self_registration": self_registration,
                  "registered": registered,
                  "login_div": login_div,
                  "login_form": login_form,
                  "register_div": register_div,
                  "register_form": register_form,
                  "contact_form": contact_form,
                  "project_links": project_links,
                  }

        # Count records (@todo: provide total/updated counters?)
        s3db = current.s3db
        db = current.db

        # Organisations
        table = s3db.org_organisation
        query = (table.deleted != True)
        count = table.id.count()
        row = db(query).select(count).first()
        output["total_organisations"] = row[count]

        # Service Locations (@todo)
        #table = s3db.org_service_location
        #query = (table.deleted != True)
        #count = table.id.count()
        #row = db(query).select(count).first()
        output["total_services"] = 0 #row[count]

        # Needs lists
        table = s3db.req_organisation_needs
        query = (table.deleted != True)
        count = table.id.count()
        row = db(query).select(count).first()
        output["total_needs"] = row[count]

        # Frontpage Feed Control
        if settings.frontpage.rss:
            s3.external_stylesheets.append("http://www.google.com/uds/solutions/dynamicfeed/gfdynamicfeedcontrol.css")
            s3.scripts.append("http://www.google.com/jsapi?key=notsupplied-wizard")
            s3.scripts.append("http://www.google.com/uds/solutions/dynamicfeed/gfdynamicfeedcontrol.js")
            counter = 0
            feeds = ""
            for feed in settings.frontpage.rss:
                counter += 1
                feeds = "".join((feeds,
                                 "{title:'%s',\n" % feed["title"],
                                 "url:'%s'}" % feed["url"]))
                # Don't add a trailing comma for old IEs
                if counter != len(settings.frontpage.rss):
                    feeds += ",\n"
            # feedCycleTime: milliseconds before feed is reloaded (5 minutes)
            feed_control = "".join(('''
function LoadDynamicFeedControl(){
 var feeds=[
  ''', feeds, '''
 ]
 var options={
  feedCycleTime:300000,
  numResults:5,
  stacked:true,
  horizontal:false,
  title:"''', str(T("News")), '''"
 }
 new GFdynamicFeedControl(feeds,'feed-control',options)
}
google.load('feeds','1')
google.setOnLoadCallback(LoadDynamicFeedControl)'''))

        s3.js_global.append(feed_control)
        s3.stylesheets.append("../themes/RW/homepage.css")

        self._view(TEMPLATE, "index.html")
        return output

# =============================================================================
class docs(S3CustomController):
    """
        Custom controller to display online documentation, accessible
        for anonymous users (e.g. information how to register/login)
    """

    def __call__(self):

        response = current.response

        def prep(r):
            default_url = URL(f="index", args=[], vars={})
            return current.s3db.cms_documentation(r, "HELP", default_url)
        response.s3.prep = prep
        output = current.rest_controller("cms", "post")

        # Custom view
        self._view("RW", "docs.html")

        current.menu.dashboard = None

        return output

# END =========================================================================
