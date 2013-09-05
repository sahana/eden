# -*- coding: utf-8 -*-

from os import path

from gluon import current, URL
from gluon.html import *
#from gluon.storage import Storage

from s3.s3filter import S3FilterString
from s3.s3utils import S3CustomController

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

# =============================================================================
class filters(S3CustomController):
    """ Custom controller to manage saved filters """

    def __call__(self):
        """ Main entry point """

        # Authorization (user must be logged in)
        auth = current.auth
        permissions = auth.permission
        if not auth.user:
            permissions.fail()

        pe_id = auth.user.pe_id
        fmt = permissions.format
        s3 = current.response.s3

        # Filter
        from s3 import S3FieldSelector as FS
        f = FS("pe_id") == pe_id
        s3.filter = f

        # List Fields
        current.s3db.configure("pr_filter",
                               list_fields = ["title", "resource", "query"],
                               list_layout = self.render_filter,
                               orderby = "resource")

        # Page length
        s3.dl_pagelength = 10

        # Data list
        current.request.args = ["datalist.%s" % fmt]
        output = current.rest_controller("pr", "filter",
                                         list_ajaxurl = URL(f="index",
                                                            args="filters.dl"))

        # Title and view
        if fmt != "dl":
            output["title"] = current.T("Saved Filters")
            self._view(THEME, "filters.html")
        return output
        
    # -----------------------------------------------------------------------------
    @staticmethod
    def render_filter(listid, resource, rfields, record, **attr):
        """
            Custom dataList item renderer for 'Saved Filters'

            @param listid: the HTML ID for this list
            @param resource: the S3Resource to render
            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
            @param attr: additional HTML attributes for the item
        """

        item_class = "thumbnail"

        # Construct the item ID
        pkey = "pr_filter.id"
        if pkey in record:
            record_id = record[pkey]
            item_id = "%s-%s" % (listid, record_id)
        else:
            # template
            item_id = "%s-[id]" % listid

        raw = record._row
        resource_name = raw["pr_filter.resource"]
        resource = current.s3db.resource(resource_name)

        T = current.T
        
        # Resource title
        crud_strings = current.response.s3.crud_strings.get(resource.tablename)
        if crud_strings:
            resource_name = crud_strings.title_list
        else:
            resource_name = string.capwords(resource.name, "_")

        # Filter title
        title = record["pr_filter.title"]
        
        # Filter Query
        query = S3FilterString(resource, raw["pr_filter.query"]).represent()

        # Render the item
        item = DIV(
                   DIV(SPAN(T("%(resource)s Filter") % \
                            dict(resource=resource_name),
                            _class="card-title"),
                       DIV(A(I(" ", _class="icon icon-remove-sign"),
                             _class="dl-item-delete"),
                           _class="edit-bar fright"),
                       _class="card-header"),
                   DIV(
                       DIV(H5(title,
                              _class="media-heading"),
                           DIV(query),
                           _class="media-body"),
                       _class="media"),
                   _class=item_class,
                   _id=item_id)

        return item

# END =========================================================================
