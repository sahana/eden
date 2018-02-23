# -*- coding: utf-8 -*-

import json

from os import path

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3 import FS, S3CustomController
from s3theme import formstyle_foundation_inline

THEME = "historic.EVASS"

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

        # Login/Registration forms
        self_registration = current.deployment_settings.get_security_registration_visible()
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

            if self_registration is True:
                # Provide a Registration box on front page
                register_form = auth.register()
                register_div = DIV(H3(T("Register")),
                                   P(XML(T("If you would like to help, then please %(sign_up_now)s") % \
                                            dict(sign_up_now=B(T("sign-up now"))))))

                if request.env.request_method == "POST":
                    if login_form.errors:
                        hide, show = "#register_form", "#login_form"
                    else:
                        hide, show = "#login_form", "#register_form"
                    post_script = \
'''$('%s').addClass('hide')
$('%s').removeClass('hide')''' % (hide, show)
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

#                s3.js_global.append(feed_control)

            # Provide a login box on front page
            auth.messages.submit_button = T("Login")
            login_form = auth.login(inline=True)
            login_div = DIV(H3(T("Login")),
                            P(XML(T("Registered users can %(login)s to access the system") % \
                                  dict(login=B(T("login"))))))

        else:
            output["event_list"] = self.event_list()
            output["shelter_list"] = self.shelter_list()
            output["events_btn"] = self.events_btn()
            output["pr_btn"] = self.pr_btn()
            output["staff_btn"] = self.staff_btn()
            output["volunteers_btn"] = self.volunteers_btn()
            output["evacuees_btn"] = self.evacuees_btn()
            output["shelters_btn"] = self.shelters_btn()

        output["self_registration"] = self_registration
        output["registered"] = registered
        output["login_div"] = login_div
        output["login_form"] = login_form
        output["register_div"] = register_div
        output["register_form"] = register_form

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
numResults:3,
stacked:true,
horizontal:false,
title:"''', str(T("News")), '''"
}
new GFdynamicFeedControl(feeds,'feed-control',options)
}
google.load('feeds','1')
google.setOnLoadCallback(LoadDynamicFeedControl)'''))
            s3.js_global.append(feed_control)

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
  cssEase:'linear',
  adaptiveHeight:true
 });
});'''
        s3.jquery_ready.append(script)

        self._view(THEME, "index.html")
        return output

    # -------------------------------------------------------------------------
    def shelter_list(self):
        """ Provide a dropdown of links to shelters """

        T = current.T
        s3db = current.s3db

        resource = s3db.resource("cr_shelter",
                                    filter = FS("status")
                                                            .belongs([2, None]))
        data = resource.select(["id", "name"])
        shelter_list = UL(_id = "shelter_list",
                          _class = "f-dropdown",
                          data = {"dropdown-content": ""})
        rows = data["rows"]
        if rows:
            for row in rows:
                shelter_list.append(LI(A(row["cr_shelter.name"],
                                            _href=URL(c="cr",
                                                    f="shelter",
                                                    args=[row["cr_shelter.id"]])
                                            )
                                        )
                                    )
            return LI(A(T("Shelters"),
                        _class="button dropdown",
                        data = {"dropdown": "shelter_list"}),
                      shelter_list
                      )
        else:
            # @todo: check permission and provide an "Add Shelter" button
            #        if not shelters are yet registered
            return ""

    # -------------------------------------------------------------------------
    def event_list(self):
        """ Provide a dropdown of links to events """

        T = current.T
        s3db = current.s3db

        resource = s3db.resource("event_event")
        data = resource.select(["id", "name"])
        event_list = UL(_id = "event_list",
                        _class = "f-dropdown",
                        data = {"dropdown-content": ""})
        rows = data["rows"]
        if rows:
            for row in rows:
                event_list.append(LI(A(row["event_event.name"],
                                        _href=URL(c="event",
                                                  f="event",
                                                  args=[row["event_event.id"]])
                                        )
                                      )
                                    )
            return LI(A(T("Events"),
                        _class="button dropdown",
                        data = {"dropdown": "event_list"}),
                      event_list
                      )
        else:
            # @todo: check permission and provide an "Add Event" button
            #        if not events are yet registered?
            return ""

    # -------------------------------------------------------------------------
    def events_btn(self):
        T = current.T
        return LI(A(T("Events"),
                    _href=URL(c="event", f="event"),
                    _class="button button-home")
                  )

    # -------------------------------------------------------------------------
    def pr_btn(self):
        T = current.T
        return LI(A(T("Person Registry"),
                    _href=URL(c="pr", f="index"),
                    _class="button button-home",
                    _id="incident-report-btn")
                  )

    # -------------------------------------------------------------------------
    def staff_btn(self):
        T = current.T
        return LI(A(T("Staff"),
                    _href=URL(c="hrm", f="staff", args=["summary"]),
                    _class="button button-home")
                  )

    # -------------------------------------------------------------------------
    def volunteers_btn(self):
        T = current.T
        return LI(A(T("Volunteers"),
                    _href=URL(c="vol", f="volunteer"),
                    _class="button button-home")
                  )

    # -------------------------------------------------------------------------
    def evacuees_btn(self):
        T = current.T
        return LI(A(T("Evacuees"),
                    _href=URL(c="evr", f="person"),
                    _class="button button-home")
                  )

    # -------------------------------------------------------------------------
    def shelters_btn(self):
        T = current.T
        return LI(A(T("Shelters"),
                    _href=URL(c="cr", f="shelter"),
                    _class="button button-home")
                  )

# END =========================================================================
