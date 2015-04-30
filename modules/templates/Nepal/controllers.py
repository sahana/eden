# -*- coding: utf-8 -*-

from gluon import *
from s3 import S3CustomController

THEME = "Nepal"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        T = current.T
        response = current.response
        s3 = response.s3
        s3.stylesheets.append("../themes/CERT/homepage.css")
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

        menus = [{"title": T("Volunteers"),
                  "icon": "user",
                  "description": T("Manage people who have volunteered for your organization, their contact details, certicates and trainings."),
                  "module": "vol",
                  "function": "volunteer",
                  "buttons": [{"args": "summary",
                               "icon": "list",
                               "label": T("View"),
                               },
                              {"args": "create",
                               "icon": "plus-sign",
                               "label": T("Create"),
                               }]
                  },
                 {"title": T("Shelters"),
                  "icon": "home",
                  "description": T("List of Shelters."),
                  "module": "cr",
                  "function": "shelter",
                  "buttons": [{"args": "summary",
                               "icon": "list",
                               "label": T("View"),
                               },
                              {"args": "create",
                               "icon": "plus-sign",
                               "label": T("Create"),
                               }]
                  },
                 {"title": T("Hospitals"),
                  "icon": "h-sign",
                  "description": T("List of Hospitals."),
                  "module": "hms",
                  "function": "hospital",
                  "buttons": [{"args": "summary",
                               "icon": "list",
                               "label": T("View"),
                               },
                              {"args": "create",
                               "icon": "plus-sign",
                               "label": T("Create"),
                               }]
                  },
                 {"title": T("Patients"),
                  "icon": "ambulance",
                  "description": T("List of Patients."),
                  "module": "patient",
                  "function": "patient",
                  "buttons": [{"args": "summary",
                               "icon": "list",
                               "label": T("View"),
                               },
                              {"args": "create",
                               "icon": "plus-sign",
                               "label": T("Create"),
                               }]
                  },
                 {"title": T("Requests"),
                  "icon": "truck",
                  "description": T("Requests for goods or services."),
                  "module": "req",
                  "function": "req",
                  "args": None,
                  "buttons": [{"args": "summary",
                               "icon": "list",
                               "label": T("View"),
                               },
                              {"args": "create",
                               "icon": "plus-sign",
                               "label": T("Create"),
                               }]
                  },
                 {"title": T("Resources"),
                  "icon": "wrench",
                  "description": T("Resources that organizations have that are useful for response."),
                  "module": "org",
                  "function": "resource",
                  "args": None,
                  "buttons": [{"args": "summary",
                               "icon": "list",
                               "label": T("View"),
                               },
                              {"args": "create",
                               "icon": "plus-sign",
                               "label": T("Create"),
                               }]
                  },
                 ]
        output["menus"] = menus

        self._view(THEME, "index.html")
        return output

# END =========================================================================
