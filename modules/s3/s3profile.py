# -*- coding: utf-8 -*-

""" S3 Profile

    @copyright: 2009-2013 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3crud import S3CRUD
from s3data import S3DataList

# =============================================================================
class S3Profile(S3CRUD):
    """
        Interactive Method Handler for Profile Pages

        Configure widgets using s3db.configure(tablename, profile_widgets=[])

        @ToDo: Make more configurable:
               * Currently assumes a max of 2 widgets per row
               * Currently uses Bootstrap classes
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            API entry point

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        if r.http == "GET":
            if r.record:
                output = self.profile(r, **attr)
            else:
                # Redirect to the List View
                redirect(r.url(method=""))
        else:
            r.error(405, current.manager.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def profile(self, r, **attr):
        """
            Generate a Profile page

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        tablename = self.tablename

        # Initialise Output
        output = dict()

        # Get the options
        widgets = current.s3db.get_config(tablename, "profile_widgets")
        rows = []
        if widgets:
            append = rows.append
            odd = True
            for widget in widgets:
                w_type = widget["type"]
                if odd:
                    row = DIV(_class="row profile")
                colspan = widget.get("colspan", 1)
                if w_type == "map":
                    row.append(self._map(r, widget, **attr))
                    if colspan == 2:
                        append(row)
                elif w_type == "comments":
                    row.append(self._comments(r, widget, **attr))
                    if colspan == 2:
                        append(row)
                elif w_type == "datalist":
                    row.append(self._datalist(r, widget, **attr))
                    if colspan == 2:
                        append(row)
                else:
                    raise
                if odd:
                    odd = False
                else:
                    odd = True
                    append(row)
        else:
            # @ToDo Some kind of 'Page not Configured'?
            pass

        output["rows"] = rows
        try:
            output["title"] = r.record.name
        except:
            output["title"] = current.T("Profile Page")
        current.response.view = self._view(r, "profile.html")
        return output

    # -------------------------------------------------------------------------
    def _comments(self, r, widget, **attr):
        """
            Generate a Comments widget

            @param r: the S3Request instance
            @param widget: the widget as a tuple: (label, type, icon)
            @param attr: controller attributes for the request

            @ToDo: Configurable to use either Disqus or internal Comments
        """

        label = widget.get("label", "")
        if label:
            label = current.T(label)
        icon = widget.get("icon", "")
        if icon:
            icon = TAG[""](I(_class=icon), " ")

        # Render the widget
        output = DIV(H4(icon,
                        label,
                        _class="profile-sub-header"),
                     DIV(_class="thumbnail"),
                     _class="span12")

        return output

    # -------------------------------------------------------------------------
    def _datalist(self, r, widget, **attr):
        """
            Generate a dataList

            @param r: the S3Request instance
            @param widget: the widget as a tuple: (label, tablename, icon, filter)
            @param attr: controller attributes for the request
        """


        tablename = widget.get("tablename", None)
        resource = current.s3db.resource(tablename)
        table = resource.table

        # @ToDo: Can we automate some of filter through link_table to the primary resource?
        filter = widget.get("filter", None)
        if filter:
            resource.add_filter(filter)

        listid = "profile-list-%s" % tablename
        if filter:
            # We may have multiple of the same resource with different filters
            listid = "%s-%s" % (listid, filter.right)

        c, f = tablename.split("_", 1)

        # Permission to create new items?
        if current.auth.s3_has_permission("create", table):
            create = A(I(_class="icon icon-plus-sign small-add"),
                       _href=URL(c=c, f=f,
                                 args=["create.popup"],
                                 vars={"refresh": listid}
                                 # @ToDo: Set defaults based on Filter (Disaster & Type)
                                 ),
                       _class="s3_modal",
                       )
        else:
            create = "" 

        # Config Options:
        # 1st choice: Widget
        # 2nd choice: get_config
        # 3rd choice: Default
        list_fields = widget.get("list_fields", 
                                 resource.get_config("list_fields",
                                                     [f for f in table.fields if table[f].readable]
                                                     ))
        list_layout = widget.get("list_layout", 
                                 resource.get_config("list_layout",
                                                     None))
        orderby = widget.get("orderby",
                             resource.get_config("list_orderby",
                                                 ~resource.table.created_on))

        # dataList
        datalist, numrows, ids = resource.datalist(fields=list_fields,
                                                   start=None,
                                                   limit=4,
                                                   listid=listid,
                                                   orderby=orderby,
                                                   layout=list_layout)
        if numrows == 0:
            msg = P(I(_class="icon-folder-open-alt"),
                    BR(),
                    S3CRUD.crud_string(resource.tablename,
                                       "msg_no_match"),
                    _class="empty_card-holder")
            data = msg
        else:
            # Render the list
            dl = datalist.html()
            data = dl

        label = widget.get("label", "")
        if label:
            label = current.T(label)
        icon = widget.get("icon", "")
        if icon:
            icon = TAG[""](I(_class=icon), " ")

        # Render the widget
        output = DIV(create,
                     H4(icon,
                        label,
                        _class="profile-sub-header"),
                     DIV(data,
                         _class="card-holder"),
                     _class="span6")

        return output

    # -------------------------------------------------------------------------
    def _map(self, r, widget, **attr):
        """
            Generate a Map widget

            @param r: the S3Request instance
            @param widget: the widget as a tuple: (label, type, icon)
            @param attr: controller attributes for the request
        """

        T = current.T
        s3db = current.s3db

        label = widget.get("label", "")
        if label:
            label = current.T(label)
        icon = widget.get("icon", "")
        if icon:
            icon = TAG[""](I(_class=icon), " ")

        # Default to showing all the resources in datalist widgets as separate layers
        feature_resources = []
        fappend = feature_resources.append
        widgets = s3db.get_config(r.tablename, "profile_widgets")
        for widget in widgets:
            if widget["type"] != "datalist":
                continue
            show_on_map = widget.get("show_on_map", True)
            if not show_on_map:
                continue
            tablename = widget["tablename"]
            resource = s3db.resource(tablename)
            filter = widget.get("filter", None)
            map_url = widget.get("map_url", None)
            if not map_url:
                # Build one
                c, f = tablename.split("_")
                map_url = URL(c=c, f=f, extension="geojson")
                if filter:
                    map_url = "%s?" % map_url
                    filter_url = filter.serialize_url(resource)
                    for f in filter_url:
                        map_url = "%s%s=%s" % (map_url, f, filter_url[f])

            id = "profile_map-%s" % tablename
            if filter:
                id = "%s-%s" % (id, filter.right)
            fappend({"name"      : T(widget["label"]),
                     "id"        : id,
                     "tablename" : tablename,
                     "url"       : map_url,
                     "active"    : True,          # Is the feed displayed upon load or needs ticking to load afterwards?
                     #"marker"    : None,         # Optional: A per-Layer marker dict for the icon used to display the feature
                     #"opacity"   : 1,            # Optional
                     #"cluster_distance",         # Optional
                     #"cluster_threshold"         # Optional
                     })

        height = widget.get("height", 383)
        width = widget.get("width", 460)
        map = current.gis.show_map(height=height,
                                   width=width,
                                   collapsed=True,
                                   feature_resources=feature_resources,
                                   )

        # Render the widget
        output = DIV(H4(icon,
                        label,
                        _class="profile-sub-header"),
                     DIV(map,
                         _class="card-holder"),
                     _class="span6")

        return output

# END =========================================================================
