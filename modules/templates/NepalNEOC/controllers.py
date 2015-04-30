# -*- coding: utf-8 -*-

from gluon import *
from s3 import S3CustomController

THEME = "NepalNEOC"

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

        menus = [{"title": T("Incidents"),
                  "icon": "incident",
                  #"description": T("Manage Incidents."),
                  "module": "event",
                  "function": "incident",
                  "buttons": [{"args": "summary",
                               "icon": "list",
                               "label": T("View"),
                               },
                              {"args": "create",
                               "icon": "plus-sign",
                               "label": T("Create"),
                               }]
                  },
                 {"title": T("Organizations"),
                  "icon": "sitemap",
                  #"description": T("Relief Organizations."),
                  "module": "org",
                  "function": "organisation",
                  "buttons": [{"args": [],
                               "icon": "list",
                               "label": T("View"),
                               },
                              {"args": "create",
                               "icon": "plus-sign",
                               "label": T("Create"),
                               }]
                  },
                 {"title": T("Activities"),
                  "icon": "cogs",
                  #"description": T("Manage Activities."),
                  "module": "project",
                  "function": "activity",
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
                  #"description": T("Requests for goods or services."),
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
