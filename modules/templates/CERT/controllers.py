# -*- coding: utf-8 -*-

from gluon import *
from s3 import S3CustomController

THEME = "CERT"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        response = current.response
        response.s3.stylesheets.append("../themes/CERT/homepage.css")
        title = current.deployment_settings.get_system_name()
        response.title = title

        T = current.T

        # Check logged in and permissions
        #auth = current.auth
        #roles = current.session.s3.roles
        #system_roles = auth.get_system_roles()
        #ADMIN = system_roles.ADMIN
        #AUTHENTICATED = system_roles.AUTHENTICATED
        #has_role = auth.s3_has_role

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
                               "icon": "plus",
                               "label": T("Create"),
                               }]
                  },
                 {"title": T("Trainings"),
                  "icon": "book",
                  "description": T("Catalog of Training Courses which your Volunteers can attend."),
                  "module": "vol",
                  "function": "course",
                  "buttons": [{"args": "summary",
                               "icon": "list",
                               "label": T("View"),
                               },
                              {"args": "create",
                               "icon": "plus",
                               "label": T("Create"),
                               }]
                  },
                 {"title": T("Certificates"),
                  "icon": "certificate",
                  "description": T("Catalog of Certificates which your Volunteers can get."),
                  "module": "vol",
                  "function": "certificate",
                  "buttons": [{"args": "summary",
                               "icon": "list",
                               "label": T("View"),
                               },
                              {"args": "create",
                               "icon": "plus",
                               "label": T("Create"),
                               }]
                  },
                 {"title": T("Messaging"),
                  "icon": "envelope-o",
                  "description": T("Send Email, SMS and Twitter messages to your Volunteers."),
                  "module": "msg",
                  "function": "Index",
                  "args": None,
                  "buttons": [{"function": "inbox",
                               "args": None,
                               "icon": "inbox",
                               "label": T("Inbox"),
                               },
                              {"function": "compose",
                               "args": None,
                               "icon": "plus",
                               "label": T("Compose"),
                               }]
                  },
                 ]

        self._view(THEME, "index.html")
        return dict(title = title,
                    menus = menus,
                    )

# END =========================================================================
