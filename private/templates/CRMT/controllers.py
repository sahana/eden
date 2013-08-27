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
            #{"user": "Marilyn Monroe",
            # "profile": URL("static", "themes", args = ["CRMT", "users", "4.jpeg"]),
            # "action": "Saved a %s",
            # "type": "Map",
            # "url": URL(""),
            #},
            {"user": "Tom Cruise",
             "profile": URL("static", "themes", args = ["CRMT", "users", "5.jpeg"]),
             "action": "Add a %s",
             "type": "Evacuation Route",
             "name": "Main St",
             "url": URL(""),
             },
        ]

        # Function for converting action, type & name to update content
        # (Not all updates will have a specific name associated with it, so the link will be on the type)
        def generate_update(action, type, name, url):
            if item.get("name"):
                return TAG[""](action % type,
                               BR(),
                               A(name,
                                 _href=url)
                               )
            else:
                return TAG[""](action % A(type,
                                          _href=url)
                               )

        output["updates"] = [dict(user = item["user"],
                                  profile = item["profile"],
                                  update = generate_update(item["action"],
                                                           item["type"],
                                                           item.get("name"),
                                                           item["url"],
                                                           )
                                  )
                             for item in updates]

        # Map
        auth = current.auth
        callback = None
        if auth.is_logged_in():
            # Show the User's Coalition's Polygon
            org_group_id = auth.user.org_group_id
            if org_group_id:
                # Lookup Coalition Name
                db = current.db
                table = current.s3db.org_group
                query = (table.id == org_group_id)
                row = db(query).select(table.name,
                                       limitby=(0, 1)).first()
                if row:
                    callback = '''S3.gis.show_map();
var layer,layers=S3.gis.maps.default_map.layers;
for(var i=0,len=layers.length;i<len;i++){
 layer=layers[i];
 if(layer.name=='%s'){layer.setVisibility(true)}}''' % row.name
        if not callback:
            # Show all Coalition Polygons
            callback = '''S3.gis.show_map();
var layer,layers=S3.gis.maps.default_map.layers;
for(var i=0,len=layers.length;i<len;i++){
 layer=layers[i];
 if(layer.name=='All Coalitions'){layer.setVisibility(true)}}
'''
        map = current.gis.show_map(width=770,
                                   height=270,
                                   callback=callback,
                                   catalogue_layers=True,
                                   collapsed=True,
                                   save=False,
                                   )
        output["map"] = map

        from s3db.cms import S3CMS
        for item in current.response.menu:
            item["cms"] = S3CMS.resource_content(module = item["c"], 
                                                 resource = item["f"])

        return output

# END =========================================================================
