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
from gluon.http import redirect
from gluon.storage import Storage

from s3crud import S3CRUD
from s3data import S3DataList
from s3resource import S3FieldSelector

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

        if r.http in ("GET", "POST", "DELETE"):
            if r.record:
                output = self.profile(r, **attr)
            else:
                # Redirect to the List View
                redirect(r.url(method=""))
        else:
            r.error(405, r.ERROR.BAD_METHOD)
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

        # Get the page widgets
        widgets = current.s3db.get_config(tablename, "profile_widgets")
        
        # Index the widgets by their position in the config
        for index, widget in enumerate(widgets):
            widget["index"] = index
            
        if r.representation == "dl":
            # Ajax-update of one datalist
            get_vars = r.get_vars
            index = r.get_vars.get("update", None)
            if index:
                try:
                    index = int(index)
                except ValueError:
                    datalist = ""
                else:
                    datalist = self._datalist(r, widgets[index], **attr)
            output["item"] = datalist
        else:
            # Default page-load
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
                # Method not supported for this resource
                # @ToDo Some kind of 'Page not Configured'?
                r.error(405, r.ERROR.BAD_METHOD)

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

        context = widget.get("context", None)
        if context:
            context = "(%s)" % context
            current.s3db.context = S3FieldSelector(context) == r.id

        tablename = widget.get("tablename", None)
        resource = current.s3db.resource(tablename, context=True)
        table = resource.table

        # Config Options:
        # 1st choice: Widget
        # 2nd choice: get_config
        # 3rd choice: Default
        config = resource.get_config
        list_fields = widget.get("list_fields", 
                                 config("list_fields", None))
        list_layout = widget.get("list_layout", 
                                 config("list_layout", None))
        orderby = widget.get("orderby",
                             config("list_orderby",
                                    ~resource.table.created_on))

        filter = widget.get("filter", None)
        if filter:
            resource.add_filter(filter)

        # Use the widget-index to create a unique ID
        listid = "profile-list-%s-%s" % (tablename, widget["index"])

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

        # Page size
        pagesize = 4
        representation = r.representation
        if representation == "dl":
            # Ajax-update
            get_vars = r.get_vars
            record_id = get_vars.get("record", None)
            if record_id is not None:
                # Ajax-update of a single record
                resource.add_filter(S3FieldSelector("id") == record_id)
                start, limit = 0, 1
            else:
                # Ajax-update of full page
                start = get_vars.get("start", None)
                limit = get_vars.get("limit", None)
                if limit is not None:
                    try:
                        start = int(start)
                        limit = int(limit)
                    except ValueError:
                        start, limit = 0, 4
                else:
                    start = None
        else:
            # Page-load
            start, limit = 0, 4

        # Ajax-delete items?
        if representation == "dl" and r.http in ("DELETE", "POST"):
            if "delete" in r.get_vars:
                return self._dl_ajax_delete(r, resource)
            else:
                r.error(405, r.ERROR.BAD_METHOD)

        # dataList
        datalist, numrows, ids = resource.datalist(fields=list_fields,
                                                   start=start,
                                                   limit=limit,
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
            ajaxurl = r.url(vars={"update": widget["index"]},
                            representation="dl")
            dl = datalist.html(ajaxurl = ajaxurl, pagesize = pagesize)
            data = dl

        if representation == "dl":
            # This is an Ajax-request, so we don't need the wrapper
            current.response.view = "plain.html"
            return data

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
        context = widget.get("context", None)
        if context:
            context = "(%s)=%s" % (context, r.id)

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
                    if context:
                        map_url = "%s&%s" % (map_url, context)
                elif context:
                    map_url = "%s?%s" % (map_url, context)

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
