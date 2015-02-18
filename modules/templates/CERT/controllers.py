# -*- coding: utf-8 -*-

from os import path

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.storage import Storage
from s3 import *

# =============================================================================
class index():
    """ Custom Home Page """

    def __call__(self):

        request = current.request
        response = current.response

        view = path.join(request.folder, "modules", "templates",
                         "CERT", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP(404, "Unable to open Custom View: %s" % view)
        current.response.s3.stylesheets.append("../themes/CERT/homepage.css")

        appname = request.application
        settings = current.deployment_settings
        title = settings.get_system_name()
        response.title = title

        T = current.T

        # Check logged in and permissions
        auth = current.auth
        roles = current.session.s3.roles
        system_roles = auth.get_system_roles()
        #ADMIN = system_roles.ADMIN
        AUTHENTICATED = system_roles.AUTHENTICATED
        #s3_has_role = auth.s3_has_role

        # @ToDo: Add event/human_resource - but this requires extending event_human_resource to link to event.
        menus = [{"title":T("Volunteers"),
                  "icon":"user",
                  "description":T("Manage people who have volunteered for your organization, their contact details, certicates and trainings."),
                  "module":"vol",
                  "function":"volunteer",
                  "buttons":[{"args":"summary",
                              "icon":"list",
                              "label":T("View"),
                             },
                             {"args":"create",
                              "icon":"plus-sign",
                              "label":T("Create"),
                             }]
                  },
                 {"title":T("Trainings"),
                  "icon":"book",
                  "description":T("Catalog of Training Courses which your Volunteers can attend."),
                  "module":"vol",
                  "function":"course",
                  "buttons":[{"args":"summary",
                              "icon":"list",
                              "label":T("View"),
                             },
                             {"args":"create",
                              "icon":"plus-sign",
                              "label":T("Create"),
                             }]
                  },
                 {"title":T("Certificates"),
                  "icon":"certificate",
                  "description":T("Catalog of Certificates which your Volunteers can get."),
                  "module":"vol",
                  "function":"certificate",
                  "buttons":[{"args":"summary",
                              "icon":"list",
                              "label":T("View"),
                             },
                             {"args":"create",
                              "icon":"plus-sign",
                              "label":T("Create"),
                             }]
                  },
                 {"title":T("Messaging"),
                  "icon":"envelope-alt",
                  "description":T("Send Email, SMS and Twitter messages to your Volunteers."),
                  "module":"msg",
                  "function":"Index",
                  "args":None,
                  "buttons":[{"function":"inbox",
                              "args":None,
                              "icon":"inbox",
                              "label":T("Inbox"),
                             },
                             {"function":"compose",
                              "args":None,
                              "icon":"plus-sign",
                              "label":T("Compose"),
                             }]
                  },
                 ] 

        return dict(title = title,
                    menus=menus,
                    )

# END =========================================================================
