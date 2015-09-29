# -*- coding: utf-8 -*-

from gluon import *
from s3 import S3CustomController
from templates.Nepal.layouts import IndexMenuLayout

THEME = "Nepal"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        T = current.T
        response = current.response
        s3 = response.s3
        s3.stylesheets.append("../themes/Nepal/index.css")
        s3.stylesheets.append("../styles/font-awesome.css")
        self._view(THEME, "index.html")
        settings = current.deployment_settings
        output["title"] = response.title = settings.get_system_name()

        # Allow editing of page content from browser using CMS module
        if settings.has_module("cms"):
            system_roles = current.auth.get_system_roles()
            ADMIN = system_roles.ADMIN in current.session.s3.roles
            s3db = current.s3db
            table = s3db.cms_post
            ltable = s3db.cms_post_module
            module = "default"
            resource = "index"
            query = (ltable.module == module) & \
                    ((ltable.resource == None) | \
                     (ltable.resource == resource)) & \
                    (ltable.post_id == table.id) & \
                    (table.deleted != True)
            item = current.db(query).select(table.body,
                                            table.id,
                                            limitby=(0, 1)).first()
            if item:
                if ADMIN:
                    item = DIV(XML(item.body),
                               BR(),
                               A(T("Edit"),
                                 _href=URL(c="cms", f="post",
                                           args=[item.id, "update"]),
                                 _class="action-btn"))
                else:
                    item = DIV(XML(item.body))
            elif ADMIN:
                if s3.crud.formstyle == "bootstrap":
                    _class = "btn"
                else:
                    _class = "action-btn"
                item = A(T("Edit"),
                         _href=URL(c="cms", f="post", args="create",
                                   vars={"module": module,
                                         "resource": resource
                                         }),
                         _class="%s cms-edit" % _class)
            else:
                item = ""
        else:
            item = ""
        output["item"] = item

        IM = IndexMenuLayout
        index_menu = IM()(IM("Organizations", c="org", f="organisation", args="summary",
                             icon="organisation",
                             description=T("List of Organizations responding with contact details and their activities to provide 3W (Who's Doing What Where)."),
                             )(IM("View", args="summary", icon="list"),
                               IM("Create", args="create", icon="create")),
                          IM("Volunteers", c="vol", f="volunteer", args="summary",
                               icon="volunteers",
                               description=T("Manage people volunteering for your organization, their contact details, certificates and trainings."),
                               )(IM("View", args="summary", icon="list"),
                                 IM("Create", args="create", icon="create")),
                          IM("Hospitals", c="hms", f="hospital", args="summary",
                               description=T("List of Hospitals and other Health Facilities."),
                               )(IM("View", args="summary", icon="list"),
                                 IM("Create", args="create", icon="create")),
                          IM("Warehouses", c="inv", f="index", args="summary",
                               description=T("Manage Warehouses, their stock and shipments."),
                               icon="warehouse",
                               )(IM("View", f="warehouse", args="summary", icon="list"),
                                 IM("Create", f="warehouse", args="create", icon="create")),
                          IM("Resources", c="org", f="resource", args="summary",
                               description=T("Resources that organizations have that are useful for response."),
                               )(IM("View", args="summary", icon="list"),
                                 IM("Create", args="create", icon="create")),
                          IM("Shelters", c="cr", f="shelter", args="summary",
                               description=T("List of Shelters for displaced people."),
                               )(IM("View", args="summary", icon="list"),
                                 IM("Create", args="create", icon="create")),
                          IM("Patients", c="patient", f="patient", args="summary",
                               icon="ambulance",
                               description=T("Register and track Patients."),
                               )(IM("View", args="summary", icon="list"),
                                 IM("Create", args="create", icon="create")),
                          IM("Requests", c="req", f="req", args="summary",
                               icon="truck",
                               description=T("Requests for resources or services."),
                               )(IM("View", args="summary", icon="list"),
                                 IM("Create", args="create", icon="create")),
                        )
        output["index_menu"] = index_menu
        return output

# END =========================================================================
