# -*- coding: utf-8 -*-

from os import path

from gluon import *
from gluon.storage import Storage
from s3 import *

# =============================================================================
class index():
    """ Custom Home Page """

    def __call__(self):

        auth = current.auth
        if auth.is_logged_in():
            # Redirect to Map
            redirect(URL(c="hms", f="hospital", args=["map"]))

        request = current.request
        response = current.response
        response.title = current.deployment_settings.get_system_name()

        T = current.T
        db = current.db
        s3db = current.s3db
        s3 = response.s3
        appname = request.application
        settings = current.deployment_settings

        # Check logged in and permissions
        roles = current.session.s3.roles
        system_roles = auth.get_system_roles()
        AUTHENTICATED = system_roles.AUTHENTICATED
        if AUTHENTICATED in roles and \
           auth.s3_has_permission("read", s3db.hms_hospital):
            hospital_items = self.hospital()
            datatable_ajax_source = "/%s/default/hospital.aadata" % \
                                    appname
            s3.actions = None
            hospital_box = DIV(H3(T("Hospitals")),
                               A(T("Add Hospital"),
                                 _href = URL(c="hms", f="hospital",
                                             args=["create"]),
                                 _id = "add-btn",
                                 _class = "action-btn",
                                 _style = "margin-right:10px;"),
                               hospital_items,
                               _id = "org_box",
                               _class = "menu_box fleft"
                               )
        else:
            hospital_box = ""
            datatable_ajax_source = ""

        item = ""
        if settings.has_module("cms"):
            table = s3db.cms_post
            item = db(table.module == "default").select(table.body,
                                                        limitby=(0, 1)).first()
            if item:
                item = DIV(XML(item.body))
            else:
                item = ""

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
                register_form = auth.register()
                register_div = DIV(H3(T("Register")),
                                   P(XML(T("If you would like to help, then please %(sign_up_now)s") % \
                                            dict(sign_up_now=B(T("sign-up now"))))))

                 # Add client-side validation
                s3_register_validation()

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
                            P(XML(T("Registered users can %(login)s to access the system") % \
                                  dict(login=B(T("login"))))))

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

        view = path.join(request.folder, "private", "templates",
                         "Sandy", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        return dict(title = response.title,
                    item = item,
                    hospital_box = hospital_box,
                    r = None, # Required for dataTable to work
                    datatable_ajax_source = datatable_ajax_source,
                    self_registration=self_registration,
                    registered=registered,
                    login_form=login_form,
                    login_div=login_div,
                    register_form=register_form,
                    register_div=register_div
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def hospital():
        """
            Function to handle pagination for the hospitals list
            on the homepage
        """

        request = current.request
        get_vars = request.get_vars

        resource = current.s3db.resource("hms_hospital")
        totalrows = resource.count()
        if "iDisplayLength" in get_vars:
            display_length = int(request.get_vars["iDisplayLength"])
        else:
            display_length = 10
        limit = 4 * display_length

        list_fields = ["id", "name"]
        filter, orderby, left = resource.datatable_filter(list_fields,
                                                          get_vars)
        resource.add_filter(filter)

        data = resource.fast_select(list_fields,
                                    start=0,
                                    limit=limit,
                                    orderby=orderby,
                                    left=left,
                                    count=True,
                                    represent=True)
        filteredrows = data["numrows"]
        rfields = data["rfields"]
        data = data["data"]

        dt = S3DataTable(rfields, data)
        dt.defaultActionButtons(resource)
        current.response.s3.no_formats = True

        if request.extension == "html":
            items = dt.html(totalrows,
                            totalrows,
                            "hospital_list_1",
                            dt_displayLength=display_length,
                            dt_ajax_url=URL(c="default",
                                            f="hospital",
                                            extension="aadata",
                                            vars={"id": "hospital_list_1"},
                                            ),
                            dt_pagination="true",
                           )
        elif request.extension.lower() == "aadata":
            if "sEcho" in request.vars:
                echo = int(request.vars.sEcho)
            else:
                echo = None
            items = dt.json(totalrows,
                            filteredrows,
                            "hospital_list_1",
                            echo)
        else:
            from gluon.http import HTTP
            raise HTTP(501, resource.ERROR.BAD_FORMAT)
        return items

# END =========================================================================
