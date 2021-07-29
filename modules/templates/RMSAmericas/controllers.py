# -*- coding: utf-8 -*-

from os import path

from gluon import *
from gluon.storage import Storage

from s3 import S3CustomController

THEME = "RMSAmericas"

# =============================================================================
def auth_formstyle(form, fields, *args, **kwargs):
    """
        Formstyle for the Login box on the homepage
    """

    def render_row(row_id, label, widget, comment, hidden=False):

        if hasattr(widget, "element"):
            submit = widget.element("input", _type="submit")
            if submit:
                submit.add_class("small primary button")
            elif label:
                widget["_placeholder"] = label[0]

        return DIV(widget,
                   _class = "row",
                   _id = row_id,
                   )

    if args:
        row_id = form
        label = fields
        widget, comment = args
        hidden = kwargs.get("hidden", False)
        return render_row(row_id, label, widget, comment, hidden)
    else:
        parent = TAG[""]()
        for row_id, label, widget, comment in fields:
            parent.append(render_row(row_id, label, widget, comment))
        return parent

# -----------------------------------------------------------------------------
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        auth = current.auth

        if auth.is_logged_in():
            if current.response.confirmation:
                has_role = auth.s3_has_role
                if has_role("wh_manager", include_admin=False) or \
                   has_role("national_wh_manager", include_admin=False):
                    # Redirect to WMS Dashboard
                    redirect(URL(c="inv", f="index"))

            login_form = ""
        else:
            auth.settings.label_separator = ""
            formstyle = auth_formstyle
            login_form = auth.login(formstyle = formstyle)

        output = {"login_form": login_form,
                  }

        self._view(THEME, "index.html")
        return output

# =============================================================================
class apps(S3CustomController):
    """ App Switcher """

    def __call__(self):

        T = current.T
        auth = current.auth
        has_roles = auth.s3_has_roles
        ORG_ADMIN = current.session.s3.system_roles.ORG_ADMIN

        # Which apps are available for this user?
        apps = []
        apps_append = apps.append
        _div = self.div

        if has_roles((ORG_ADMIN,
                      "hr_manager",
                      "hr_assistant",
                      "training_coordinator",
                      "training_assistant",
                      "surge_capacity_manager",
                      "disaster_manager",
                      )):
            apps_append(_div(label = T("Human Talent"),
                             url = URL(c = "hrm",
                                       f = "index",
                                       ),
                             image = "human_talent.png",
                             _class = "alh",
                             ))

        if has_roles((ORG_ADMIN,
                      "training_coordinator",
                      "training_assistant",
                      "ns_training_manager",
                      "ns_training_assistant",
                      "surge_capacity_manager",
                      "disaster_manager",
                      )):
            apps_append(_div(label = T("Training"),
                             url = URL(c = "hrm",
                                       f = "training_event",
                                       ),
                             image = "training.png",
                             ))

        if auth.permission.accessible_url(c = "member",
                                          f = "membership",
                                          ):
            apps_append(_div(label = T("Partners"),
                             url = URL(c = "member",
                                       f = "membership",
                                       ),
                             image = "partners.png",
                             ))

        if has_roles((ORG_ADMIN,
                      "wh_manager",
                      "national_wh_manager",
                      )):
            wh_url = URL(c = "inv",
                         f = "index",
                         )
        else:
            # Normal users see Warehouses module, but have a different page
            wh_url = URL(c = "req",
                         f = "req",
                         )
        apps_append(_div(label = T("Warehouses"),
                         url = wh_url,
                         image = "warehouses.png",
                         _class = "alw",
                         ))

        if has_roles(("project_reader",
                      "project_manager",
                      "monitoring_evaluation",
                      )):
            apps_append(_div(label = T("Projects"),
                             url = URL(c = "project",
                                       f = "project",
                                       args = "summary",
                                       ),
                             image = "projects.png",
                             ))

        if has_roles(("surge_capacity_manager",
                      "disaster_manager",
                      )):
            apps_append(_div(label = T("RIT"),
                             url = URL(c = "deploy",
                                       f = "mission",
                                       args = "summary",
                                       vars = {"status__belongs": 2},
                                       ),
                             image = "RIT.png",
                             ))

        # Layout the apps
        len_apps = len(apps)
        if len_apps == 0:
            # No Apps available
            # This generally gets caught earlier & user sees no App Switcher at all
            resize = True
            height = 112
            width = 110
            apps = DIV(_class = "row",
                       )
        elif len_apps == 1:
            # 1x1
            resize = True
            height = 112
            width = 110
            apps[0]["_class"] = "small-12 columns"
            apps = DIV(apps[0],
                       _class = "row",
                       )
        elif len_apps == 2:
            # 1x2
            resize = True
            height = 112
            width = 220
            apps[0]["_class"] = "small-6 columns"
            apps[1]["_class"] = "small-6 columns"
            apps = DIV(apps[0],
                       apps[1],
                       _class = "row",
                       )
        elif len_apps == 3:
            # 2x2
            resize = True
            height = 224
            width = 220
            apps[0]["_class"] = "small-6 columns"
            apps[1]["_class"] = "small-6 columns"
            apps[2]["_class"] = "small-6 columns"
            apps = TAG[""](DIV(apps[0],
                               apps[1],
                               _class = "row",
                               ),
                           DIV(apps[2],
                               _class = "row",
                               ),
                           )
        elif len_apps == 4:
            # 2x2
            resize = True
            height = 224
            width = 220
            apps[0]["_class"] = "small-6 columns"
            apps[1]["_class"] = "small-6 columns"
            apps[2]["_class"] = "small-6 columns"
            apps[3]["_class"] = "small-6 columns"
            apps = TAG[""](DIV(apps[0],
                               apps[1],
                               _class = "row",
                               ),
                           DIV(apps[2],
                               apps[3],
                               _class = "row",
                               ),
                           )
        else:
            # 2xX
            resize = False
            row2 = DIV(apps[3],
                       apps[4],
                       _class = "row",
                       )
            if len_apps == 6:
                row2.append(apps[5])
            apps = TAG[""](DIV(apps[0],
                               apps[1],
                               apps[2],
                               _class = "row",
                               ),
                           row2,
                           )

        output = {"apps": apps,
                  }

        if resize:
            # Insert JS to resize the parent iframe
            output["js"] = '''window.parent.$('#apps-frame').parent().height(%s).width(%s)''' % \
                                (height, width)

        self._view(THEME, "apps.html")
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def div(label,
            url,
            image,
            _class = None
            ):

        if _class:
            #Extra class on label's span to fit it in better
            _class = "al %s" % _class
        else:
            _class = "al"

        div = DIV(DIV(A(IMG(_src = URL(c="static", f="themes",
                                       args = [THEME,
                                               "img",
                                               image,
                                               ]),
                            _class = "ai",
                            _height = "64",
                            _width = "64",
                            ),
                        SPAN(label,
                             _class = _class,
                             ),
                        _href = url,
                        _target = "_top",
                        ),
                      _class = "ah",
                      ),
                  _class = "small-4 columns",
                  )

        return div

# =============================================================================
def deploy_index():
    """
        Custom module homepage for deploy (=RIT) to display online
        documentation for the module
    """

    def prep(r):
        default_url = URL(f="mission", args="summary", vars={})
        return current.s3db.cms_documentation(r, "RIT", default_url)
    current.response.s3.prep = prep
    output = current.rest_controller("cms", "post")

    # Custom view
    S3CustomController._view(THEME, "deploy_index.html")
    return output

# =============================================================================
def inv_index():
    """
        Custom module homepage for Warehouse Management module
        - Dashboard
    """

    output = {"title": current.T("Dashboard"),
              "contents": I("coming soon..."),
              }

    # Custom view
    S3CustomController._view(THEME, "inv_index.html")
    return output

# END =========================================================================
