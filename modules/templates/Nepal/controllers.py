# -*- coding: utf-8 -*-

from gluon import *
from s3 import S3CustomController

THEME = "Nepal"

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
                               "icon": "plus-sign",
                               "label": T("Create"),
                               }]
                  },
                 {"title": T("Shelters"),
                  "icon": "book",
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
                  "icon": "certificate",
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
                 {"title": T("Requests"),
                  "icon": "envelope-alt",
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
                 ]

        self._view(THEME, "index.html")
        return dict(title = title,
                    menus = menus,
                    )

# END =========================================================================
