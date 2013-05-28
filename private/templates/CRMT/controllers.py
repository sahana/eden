# -*- coding: utf-8 -*-

from os import path

from gluon import current, URL, TAG, BR, A
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

        # This will presumably be modified according to how the update  data is stored / retrieved
        updates = [
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
             "name": "My Organization Resources",
             "url": URL(""),
             },
            {"user": "Will Smith",
             "profile": URL("static", "themes", args = ["CRMT", "users", "3.jpeg"]),
             "action": "Edited a %s",
             "type": "Risk",
             "name": "Wirefires",
             "url": URL(""),
             },
#            {"user": "Marilyn Monroe",
#             "profile": URL("static", "themes", args = ["CRMT", "users", "4.jpeg"]),
#             "action": "Saved a %s",
#             "type": "Map",
#             "url": URL(""),
 #            },
            {"user": "Tom Cruise",
             "profile": URL("static", "themes", args = ["CRMT", "users", "5.jpeg"]),
             "action": "Add a %s",
             "type": "Evacuation Route",
             "name": "Main St",
             "url": URL(""),
             },
        ]

        # function for converting action, type & name to update content
        # (Not all updates will have a specific name associated with it, so the link will be on the type)
        def generate_update(action, type, name, url):
            if item.get("name"):
                return TAG[""]( action % type,
                                BR(),
                                A( name,
                                   _href=url)
                                )
            else:
                return TAG[""]( action % A(type,
                                           _href=url)
                               )

        output["updates"] = [dict(user = item["user"],
                                  profile = item["profile"],
                                  update = generate_update( item["action"],
                                                            item["type"],
                                                            item.get("name"),
                                                            item["url"],
                                                            )
                                  )
                             for item in updates]


        return output

# END =========================================================================
