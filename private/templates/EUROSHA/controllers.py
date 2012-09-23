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
        s3 = response.s3
        appname = request.application
        settings = current.deployment_settings

        has_module = settings.has_module
        if has_module("cr"):
            table = current.s3db.cr_shelter
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
        if AUTHENTICATED in roles and \
           auth.s3_has_permission("read", current.s3db.org_organisation):
            org_items = self.organisation()
            datatable_ajax_source = "/%s/default/organisation.aadata" % \
                                    appname
            s3.actions = None
            auth.permission.controller = "org"
            auth.permission.function = "site"
            permitted_facilities = auth.permitted_facilities(redirect_on_error=False)
            manage_facility_box = ""
            if permitted_facilities:
                facility_list = s3_represent_facilities(db, permitted_facilities,
                                                        link=False)
                facility_list = sorted(facility_list, key=lambda fac: fac[1])
                facility_opts = [OPTION(opt[1], _value = opt[0])
                                 for opt in facility_list]
                if facility_list:
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
                    manage_facility_box = DIV()

            org_box = DIV(H3(T("Organizations")),
                          A(T("Add Organization"),
                            _href = URL(c="org", f="organisation",
                                        args=["create"]),
                            _id = "add-btn",
                            _class = "action-btn",
                            _style = "margin-right: 10px;"),
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
                            P(XML(T("Registered users can %(login)s to access the system" % \
                                    dict(login=B(T("login")))))))

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
        resource = current.s3db.resource("org_organisation")
        totalrows = resource.count()
        table = resource.table

        list_fields = ["id", "name"]
        limit = int(request.get_vars["iDisplayLength"]) if request.extension == "aadata" else 1
        rfields = resource.resolve_selectors(list_fields)[0]
        (orderby, filter) = S3DataTable.getControlData(rfields, request.vars)
        resource.add_filter(filter)
        filteredrows = resource.count()
        if isinstance(orderby, bool):
            orderby = table.name
        rows = resource.select(list_fields,
                               orderby=orderby,
                               start=0,
                               limit=limit,
                               )
        data = resource.extract(rows,
                                list_fields,
                                represent=True,
                                )
        dt = S3DataTable(rfields, data)
        dt.defaultActionButtons(resource)
        current.response.s3.no_formats = True
        if request.extension == "html":
            items = dt.html(totalrows,
                            filteredrows,
                            "org_list_1",
                            dt_displayLength=10,
                            dt_ajax_url=URL(c="default",
                                            f="organisation",
                                            extension="aadata",
                                            vars={"id": "org_list_1"},
                                            ),
                           )
        elif request.extension.lower() == "aadata":
            limit = resource.count()
            if "sEcho" in request.vars:
                echo = int(request.vars.sEcho)
            else:
                echo = None
            items = dt.json(totalrows,
                            filteredrows,
                            "org_list_1",
                            echo)
        else:
            from gluon.http import HTTP
            raise HTTP(501, current.manager.ERROR.BAD_FORMAT)
        return items

# END =========================================================================
