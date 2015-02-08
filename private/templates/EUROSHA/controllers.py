# -*- coding: utf-8 -*-

from os import path

from gluon import *
from gluon.storage import Storage
from s3 import *

# =============================================================================
class index():
    """ Custom Home Page """

    def __call__(self):

        request = current.request
        response = current.response

        response.title = current.deployment_settings.get_system_name()

        T = current.T
        db = current.db
        auth = current.auth
        s3db = current.s3db
        s3 = response.s3
        appname = request.application
        settings = current.deployment_settings

        has_module = settings.has_module
        if has_module("cr"):
            table = s3db.cr_shelter
            SHELTERS = s3.crud_strings["cr_shelter"].title_list
        else:
            SHELTERS = ""

        # Menu Boxes
        menu_btns = [#div, label, app, function
                    #["col1", T("Staff"), "hrm", "staff"],
                    #["col1", T("Volunteers"), "vol", "volunteer"],
                    ["col1", T("Projects"), "project", "project"],
                    ["col1", T("Vehicles"), "vehicle", "vehicle"],
                    ["col2", T("Assets"), "asset", "asset"],
                    ["col2", T("Inventory Items"), "inv", "inv_item"],
                    #["facility", T("Facilities"), "org", "facility"],
                    ["facility", T("Hospitals"), "hms", "hospital"],
                    ["facility", T("Offices"), "org", "office"],
                    ["facility", SHELTERS, "cr", "shelter"],
                    ["facility", T("Transport"), "transport", "index"],
                    ["facility", T("Warehouses"), "inv", "warehouse"],
                    ]

        menu_divs = {"col1": DIV(_id="menu_div_col1", _class="menu_div"),
                     "col2": DIV(_id="menu_div_col2", _class="menu_div"),
                     "facility": DIV(H3(T("Facilities")),
                                     _id = "facility_box",
                                     _class = "menu_box"),
                     }

        for div, label, app, function in menu_btns:
            if has_module(app):
                # @ToDo: Also check permissions (e.g. for anonymous users)
                menu_divs[div].append(A(DIV(label,
                                            _class="menu-btn-r"),
                                        _class="menu-btn-l",
                                        _href = URL(app, function)
                                        )
                                     )

        cols_box = DIV(H3(T("Humanitarian Projects")),
                       DIV(_id="menu_div_col0"),
                       menu_divs["col1"],
                       menu_divs["col2"],
                       _id="cols_box",
                       #_class="menu_box fleft swidth"
                       _class="menu_box"
                       )
        facility_box  = menu_divs["facility"]
        facility_box.append(A(IMG(_src="/%s/static/img/map_icon_128.png" % \
                                        appname),
                              _href = URL(c="gis", f="index"),
                              _title = T("Map")
                              )
                            )

        datatable_ajax_source = ""

        # Check logged in AND permissions
        roles = current.session.s3.roles
        system_roles = auth.get_system_roles()
        AUTHENTICATED = system_roles.AUTHENTICATED
        table = s3db.org_organisation
        has_permission = auth.s3_has_permission
        if AUTHENTICATED in roles and \
           has_permission("read", table):
            org_items = self.organisation()
            datatable_ajax_source = "/%s/default/organisation.aadata" % \
                                    appname
            s3.actions = None
            permit = auth.permission
            permit.controller = "org"
            permit.function = "site"
            permitted_facilities = auth.permitted_facilities(redirect_on_error=False)
            if permitted_facilities:
                facilities = s3db.org_SiteRepresent().bulk(permitted_facilities)
                facility_list = [(fac, facilities[fac]) for fac in facilities]
                facility_list = sorted(facility_list, key=lambda fac: fac[1])
                facility_opts = [OPTION(fac[1], _value=fac[0])
                                 for fac in facility_list]
                manage_facility_box = DIV(H3(T("Manage Your Facilities")),
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
                                          _class = "menu_box fleft"
                                          )
                s3.jquery_ready.append(
'''$('#manage_facility_select').change(function(){
 $('#manage_facility_btn').attr('href',S3.Ap.concat('/default/site/',$('#manage_facility_select').val()))
})''')
            else:
                manage_facility_box = ""

            if has_permission("create", table):
                create = A(T("Add Organization"),
                           _href = URL(c="org", f="organisation",
                                       args=["create"]),
                           _id = "add-btn",
                           _class = "action-btn",
                           _style = "margin-right: 10px;")
            else:
                create = ""
            org_box = DIV(H3(T("Organizations")),
                          create,
                          org_items,
                          _id = "org_box",
                          _class = "menu_box fleft"
                          )
        else:
            manage_facility_box = ""
            org_box = ""

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
                         "EUROSHA", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        return dict(title = response.title,
                    cols_box = cols_box,
                    facility_box = facility_box,
                    manage_facility_box = manage_facility_box,
                    org_box = org_box,
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
    def organisation():
        """
            Function to handle pagination for the org list on the homepage
        """

        request = current.request
        get_vars = request.get_vars

        resource = current.s3db.resource("org_organisation")
        totalrows = resource.count()
        if "iDisplayLength" in get_vars:
            display_length = int(get_vars["iDisplayLength"])
        else:
            display_length = 10
        limit = 4 * display_length

        list_fields = ["id", "name"]
        filter, orderby, left = resource.datatable_filter(list_fields,
                                                          get_vars)
        resource.add_filter(filter)

        data = resource.select(list_fields,
                               start=0,
                               limit=limit,
                               orderby=orderby,
                               left=left,
                               count=True,
                               represent=True)
        filteredrows = data["numrows"]
        rfields = data["rfields"]
        rows = data["rows"]

        dt = S3DataTable(rfields, rows)
        dt_id = "org_dt"

        if request.extension == "html":
            dt.defaultActionButtons(resource)
            current.response.s3.no_formats = True
            items = dt.html(totalrows,
                            filteredrows,
                            dt_id,
                            dt_displayLength=display_length,
                            dt_ajax_url=URL(c="default",
                                            f="organisation",
                                            extension="aadata",
                                            vars={"id": dt_id},
                                            ),
                            dt_pagination="true",
                            )
        elif request.extension == "aadata":
            if "sEcho" in get_vars:
                echo = int(get_vars.sEcho)
            else:
                echo = None
            items = dt.json(totalrows,
                            filteredrows,
                            dt_id,
                            echo)
            current.response.headers["Content-Type"] = "application/json"
        else:
            from gluon.http import HTTP
            raise HTTP(501, resource.ERROR.BAD_FORMAT)
        return items

# END =========================================================================
