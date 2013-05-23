# -*- coding: utf-8 -*-

from os import path

from gluon import current, URL
#from gluon.html import *
#from gluon.storage import Storage

THEME = "CRMT"

# =============================================================================
class index():
    """ Custom Home Page """

    def __call__(self):

        response = current.response
        output = {}
        output["title"] = response.title = current.deployment_settings.get_system_name()
        view = path.join(current.request.folder, "private", "templates",
                         THEME, "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        application = current.request.application
        T = current.T

        output["updates"] = [
            {"user": "Tom Jones",
             "profile": URL("static", "themes", args = ["CRMT", "users", "1.jpeg"]),
             "action": "Added a %s",
             "type": "Organization",
             "name": "Helping Hands",
             "url": URL(""),
             },
            {"user": "Frank Sinatra",
             "profile": URL("static", "themes", args = ["CRMT", "users", "2.jpeg"]),
             "action": "Saved a %s",
             "type": "Filter",
             "name": "My Community Resources",
             "url": URL(""),
             },
            {"user": "Will Smith",
             "profile": URL("static", "themes", args = ["CRMT", "users", "3.jpeg"]),
             "action": "Edited a %s",
             "type": "Risk",
             "name": "Aliens",
             "url": URL(""),
             },
            {"user": "Marilyn Monroe",
             "profile": URL("static", "themes", args = ["CRMT", "users", "4.jpeg"]),
             "action": "Saved a %s",
             "type": "Map",
             "url": URL(""),
             },
#            {"user": "Tom Cruise",
#             "profile": URL("static", "themes", args = ["CRMT", "users", "5.jpeg"]),
#             "action": "Add a %s",
#             "type": "Evacuation Route",
#             "name": "Through the Air Vents",
#             "url": URL(""),
#             },
        ]

        return output

# END =========================================================================
