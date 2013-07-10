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
           * Currently uses internal widgets rather than S3Method widgets
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
        get_config = current.s3db.get_config

        # Page Title
        title = get_config(tablename, "profile_title")
        if not title:
            try:
                title = r.record.name
            except:
                title = current.T("Profile Page")

        # Page Header
        header = get_config(tablename, "profile_header")
        if not header:
            header = H2(title, _class="profile_header")

        output = dict(title=title,
                      header=header)

        # Get the page widgets
        widgets = get_config(tablename, "profile_widgets")

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
                    # @ToDo: Check permissions to the Resource & do something different if no permission
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

            current.response.view = self._view(r, "profile.html")

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def _resolve_context(context, id):
        """
            Resolve a context filter

            @param context: the context (as a string)
            @param id: the record_id
        """

        if context == "location":
            # Show records linked to this Location & all it's Child Locations
            s = "(location)$path"
            # This version doesn't serialize_url
            #m = ("%(id)s/*,*/%(id)s/*" % dict(id=id)).split(",")
            #filter = (S3FieldSelector(s).like(m)) | (S3FieldSelector(s) == id)
            m = ("%(id)s,%(id)s/*,*/%(id)s/*,*/%(id)s" % dict(id=id)).split(",")
            m = [f.replace("*", "%") for f in m]
            filter = S3FieldSelector(s).like(m)
        # @ToDo:
        #elif context == "organisation":
        #    # Show records linked to this Organisation and all it's Branches
        #    s = "(%s)" % context
        #    filter = S3FieldSelector(s) == id
        else:
            # Normal: show just records linked directly to this master resource
            s = "(%s)" % context
            filter = S3FieldSelector(s) == id

        return filter

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

        T = current.T
        s3db = current.s3db
        id = r.id
        context = widget.get("context", None)
        if context:
            context = self._resolve_context(context, id)
        s3db.context = context

        tablename = widget.get("tablename", None)
        resource = s3db.resource(tablename, context=True)
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
                        start, limit = 0, pagesize
                else:
                    start = None
        else:
            # Page-load
            start, limit = 0, pagesize

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
        # Render the list
        ajaxurl = r.url(vars={"update": widget["index"]},
                        representation="dl")
        data = datalist.html(ajaxurl=ajaxurl, pagesize=pagesize)
        if numrows == 0:
            msg = P(I(_class="icon-folder-open-alt"),
                    BR(),
                    S3CRUD.crud_string(tablename,
                                       "msg_no_match"),
                    _class="empty_card-holder")
            data.insert(1, msg)

        if representation == "dl":
            # This is an Ajax-request, so we don't need the wrapper
            current.response.view = "plain.html"
            return data

        # Interactive only below here
        label = widget.get("label", "")
        if label:
            label = T(label)
        icon = widget.get("icon", "")
        if icon:
            icon = TAG[""](I(_class=icon), " ")

        # Permission to create new items?
        insert = widget.get("insert", True)
        if insert and current.auth.s3_has_permission("create", table):
            #if r.tablename = "org_organisation":
                # @ToDo: Special check for creating resources on Organisation profile
            if filter:
                vars = filter.serialize_url(filter)
            else:
                vars = Storage()
            vars.refresh = listid
            if context:
                filters = context.serialize_url(resource)
                for f in filters:
                    vars[f] = filters[f]
            default = widget.get("default", None)
            if default:
                k, v = default.split("=", 1)
                vars[k] = v
            title_create = widget.get("title_create", None)
            if title_create:
                title_create = T(title_create)
            else:
                title_create = S3CRUD.crud_string(tablename, "title_create")
            c, f = tablename.split("_", 1)
            c = widget.get("create_controller", c)
            f = widget.get("create_function", f)
            create = A(I(_class="icon icon-plus-sign small-add"),
                       _href=URL(c=c, f=f, args=["create.popup"], vars=vars),
                       _class="s3_modal",
                       _title=title_create,
                       )
        else:
            create = ""

        if numrows > pagesize:
            # Button to display the rest of the records in a Modal
            more = numrows - pagesize
            vars = {}
            if context:
                filters = context.serialize_url(resource)
                for f in filters:
                    vars[f] = filters[f]
            if filter:
                filters = filter.serialize_url(resource)
                for f in filters:
                    vars[f] = filters[f]
            c, f = tablename.split("_", 1)
            url = URL(c=c, f=f, args=["datalist.popup"],
                      vars=vars)
            more = DIV(A(BUTTON("%s (%s)" % (T("see more"), more),
                                _class="btn btn-mini",
                                _type="button",
                                ),
                         _class="s3_modal",
                         _href=url,
                         _title=label,
                         ),
                       _class="more_profile")
        else:
            more = ""

        # Render the widget
        output = DIV(create,
                     H4(icon,
                        label,
                        _class="profile-sub-header"),
                     DIV(data,
                         more,
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

        from s3gis import Marker

        T = current.T
        db = current.db
        s3db = current.s3db

        label = widget.get("label", "")
        if label:
            label = current.T(label)
        icon = widget.get("icon", "")
        if icon:
            icon = TAG[""](I(_class=icon), " ")
        context = widget.get("context", None)
        if context:
            context = self._resolve_context(context, r.id)
            cserialize_url = context.serialize_url

        height = widget.get("height", 383)
        width = widget.get("width", 568) # span6 * 99.7%
        bbox = widget.get("bbox", {})

        # Default to showing all the resources in datalist widgets as separate layers
        ftable = s3db.gis_layer_feature
        mtable = s3db.gis_marker
        feature_resources = []
        fappend = feature_resources.append
        widgets = s3db.get_config(r.tablename, "profile_widgets")
        s3dbresource = s3db.resource
        for widget in widgets:
            if widget["type"] != "datalist":
                continue
            show_on_map = widget.get("show_on_map", True)
            if not show_on_map:
                continue
            # @ToDo: Check permission to access layer (both controller/function & also within Map Config)
            tablename = widget["tablename"]
            listid = "profile-list-%s-%s" % (tablename, widget["index"])
            layer = dict(name = T(widget["label"]),
                         id = listid,
                         active = True,
                         )
            filter = widget.get("filter", None)
            marker = widget.get("marker", None)
            if marker:
                marker = db(mtable.name == marker).select(mtable.image,
                                                          mtable.height,
                                                          mtable.width,
                                                          limitby=(0, 1)).first()
            layer_id = None
            layer_name = widget.get("layer", None)
            if layer_name:
                row = db(ftable.name == layer_name).select(ftable.layer_id,
                                                           limitby=(0, 1)).first()
                if row:
                    layer_id = row.layer_id
            if layer_id:
                layer["layer_id"] = layer_id
                if not marker:
                    marker = Marker(layer_id=layer_id).as_dict()
                resource = s3dbresource(tablename)
                filter_url = ""
                first = True
                if context:
                    filters = cserialize_url(resource)
                    for f in filters:
                        sep = "" if first else "&"
                        filter_url = "%s%s%s=%s" % (filter_url, sep, f, filters[f])
                        first = False
                if filter:
                    filters = filter.serialize_url(resource)
                    for f in filters:
                        sep = "" if first else "&"
                        filter_url = "%s%s%s=%s" % (filter_url, sep, f, filters[f])
                        first = False
                if filter_url:
                    layer["filter"] = filter_url
            else:
                layer["tablename"] = tablename
                map_url = widget.get("map_url", None)
                if not map_url:
                    # Build one
                    c, f = tablename.split("_", 1)
                    map_url = URL(c=c, f=f, extension="geojson")
                    resource = s3dbresource(tablename)
                    first = True
                    if context:
                        filters = cserialize_url(resource)
                        for f in filters:
                            sep = "?" if first else "&"
                            map_url = "%s%s%s=%s" % (map_url, sep, f, filters[f])
                            first = False
                    if filter:
                        filters = filter.serialize_url(resource)
                        for f in filters:
                            sep = "?" if first else "&"
                            map_url = "%s%s%s=%s" % (map_url, sep, f, filters[f])
                            first = False
                layer["url"] = map_url

            if marker:
                layer["marker"] = marker

            fappend(layer)

        map = current.gis.show_map(height=height,
                                   width=width,
                                   bbox=bbox,
                                   collapsed=True,
                                   feature_resources=feature_resources,
                                   )

        # Button to go full-screen
        fullscreen = A(I(_class="icon icon-fullscreen"),
                       _href=URL(c="gis", f="map_viewing_client"),
                       _class="gis_fullscreen_map-btn",
                       # If we need to support multiple maps on a page
                       #_map="default",
                       _title=T("View full screen"),
                       )
        s3 = current.response.s3
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.gis.fullscreen.js" % current.request.application
        else:
            script = "/%s/static/scripts/S3/s3.gis.fullscreen.min.js" % current.request.application
        s3.scripts.append(script)

        # Render the widget
        output = DIV(fullscreen,
                     H4(icon,
                        label,
                        _class="profile-sub-header"),
                     DIV(map,
                         _class="card-holder"),
                     _class="span6")

        return output

# END =========================================================================
