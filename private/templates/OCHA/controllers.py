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

        settings = current.deployment_settings
        response.title = settings.get_system_name()

        T = current.T
        s3 = response.s3
        appname = request.application

        project_items = project()()
        datatable_ajax_source = "/%s/default/index/project.aadata" % \
                                appname
        s3.actions = None
        project_box = DIV(H3(T("Projects")),
                          A(T("Add Project"),
                            _href = URL(c="project", f="project",
                                        args=["create"]),
                            _id = "add-btn",
                            _class = "action-btn",
                            _style = "margin-right:10px;"),
                          project_items,
                          _id = "org_box",
                          _class = "menu_box fleft"
                          )

        # Login/Registration forms
        self_registration = settings.get_security_self_registration()
        registered = False
        login_form = None
        login_div = None
        register_form = None
        register_div = None
        roles = current.session.s3.roles
        auth = current.auth
        system_roles = auth.get_system_roles()
        AUTHENTICATED = system_roles.AUTHENTICATED
        if AUTHENTICATED not in roles:
            # This user isn't yet logged-in
            if request.cookies.has_key("registered"):
                # This browser has logged-in before
                registered = True

            if self_registration:
                # Provide a Registration box on front page
                register_form = auth.register()
                register_div = DIV(H3(T("Register")),
                                   P(XML(T("If you would like to add data, then please %(sign_up_now)s") % \
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

        view = path.join(request.folder, "private", "templates",
                         "OCHA", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        return dict(title = response.title,
                    project_box = project_box,
                    r = None, # Required for dataTable to work
                    datatable_ajax_source = datatable_ajax_source,
                    self_registration=self_registration,
                    registered=registered,
                    login_form=login_form,
                    login_div=login_div,
                    register_form=register_form,
                    register_div=register_div
                    )

# =============================================================================
class project():
    """
        Function to handle pagination for the project list on the homepage
    """

    def __call__(self):

        request = current.request
        get_vars = request.get_vars

        resource = current.s3db.resource("project_project")
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
                            "org_dt",
                            dt_displayLength=display_length,
                            dt_ajax_url=URL(c="default",
                                            f="index",
                                            args=["project"],
                                            extension="aadata",
                                            vars={"id": "org_dt"},
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
                            "org_dt",
                            echo)
        else:
            from gluon.http import HTTP
            raise HTTP(501, resource.ERROR.BAD_FORMAT)
        return items

# END =========================================================================
