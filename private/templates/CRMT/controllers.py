# -*- coding: utf-8 -*-

from os import path
from urllib import urlencode

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import current, URL
from gluon.html import *
#from gluon.storage import Storage

from s3.s3filter import S3FilterForm, S3FilterString, S3OptionsFilter
from s3.s3resource import S3FieldSelector, S3URLQuery
from s3.s3summary import S3Summary
from s3.s3utils import s3_auth_user_represent_name, S3CustomController

THEME = "CRMT"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        T = current.T
        db = current.db
        s3db = current.s3db
        request = current.request
        response = current.response
        s3 = response.s3

        output = {}
        output["title"] = response.title = current.deployment_settings.get_system_name()

        # Map
        auth = current.auth
        is_logged_in = auth.is_logged_in()
        callback = None
        if is_logged_in:
            # Show the User's Coalition's Polygon
            org_group_id = auth.user.org_group_id
            if org_group_id:
                # Lookup Coalition Name
                db = current.db
                table = s3db.org_group
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
                                   height=295,
                                   callback=callback,
                                   catalogue_layers=True,
                                   collapsed=True,
                                   save=False,
                                   )
        output["map"] = map

        # Description of available Modules
        from s3db.cms import S3CMS
        for item in response.menu:
            item["cms"] = S3CMS.resource_content(module = item["c"], 
                                                 resource = item["f"])

        # Site Activity Log
        resource = s3db.resource("s3_audit")
        resource.add_filter(S3FieldSelector("~.method") != "delete")
        orderby = "s3_audit.timestmp desc"
        list_fields = ["id",
                       "method",
                       "user_id",
                       "tablename",
                       "record_id",
                       ]
        #current.deployment_settings.ui.customize_s3_audit()
        db.s3_audit.user_id.represent = s3_auth_user_represent_name
        listid = "log"
        datalist, numrows, ids = resource.datalist(fields=list_fields,
                                                   start=None,
                                                   limit=4,
                                                   listid=listid,
                                                   orderby=orderby,
                                                   layout=s3.render_log)

        # Placeholder
        filter_form = DIV(_class="filter_form")
        if numrows == 0:
            # Empty table or just no match?
            from s3.s3crud import S3CRUD
            table = resource.table
            if "deleted" in table:
                available_records = db(table.deleted != True)
            else:
                available_records = db(table._id > 0)
            if available_records.select(table._id,
                                        limitby=(0, 1)).first():
                msg = DIV(S3CRUD.crud_string(resource.tablename,
                                             "msg_no_match"),
                          _class="empty")
            else:
                msg = DIV(S3CRUD.crud_string(resource.tablename,
                                             "msg_list_empty"),
                          _class="empty")
            data = msg
        else:
            # Render the list
            ajaxurl = URL(c="default", f="audit", args="datalist_f.dl")
            popup_url = URL(c="default", f="audit", args="datalist.popup")
            dl = datalist.html(ajaxurl=ajaxurl,
                               pagesize=4,
                               popup_url=popup_url,
                               popup_title=T("Updates"),
                               )
            data = dl

            if is_logged_in and org_group_id:
                # Add a Filter
                filter_widgets = [S3OptionsFilter("user_id$org_group_id",
                                                  label = "",
                                                  # Can't just use "" as this is then omitted from rendering
                                                  options = {"*": T("All"),
                                                             org_group_id: T("My Community"),
                                                             },
                                                  multiple = False,
                                                  ),
                                  ]

                filter_submit_url = URL(c="default", f="index")
                filter_ajax_url = URL(c="default", f="audit", args=["filter.options"])
                filter_form = S3FilterForm(filter_widgets,
                                           filter_manager = False,
                                           formstyle = filter_formstyle,
                                           clear = False,
                                           submit = True,
                                           ajax = True,
                                           url = filter_submit_url,
                                           ajaxurl = filter_ajax_url,
                                           _class = "filter-form",
                                           _id = "%s-filter-form" % listid
                                           )
                filter_form = filter_form.html(resource,
                                               request.get_vars,
                                               target=listid,
                                               )

        output["updates"] = data
        output["filter_form"] = filter_form

        # Add JavaScript
        appname = request.application
        debug = s3.debug
        scripts_append = s3.scripts.append
        if debug:
            # Infinite Scroll doesn't make sense here, but currently required by dataLists.js
            scripts_append("/%s/static/scripts/jquery.infinitescroll.js" % appname)
            scripts_append("/%s/static/scripts/jquery.viewport.js" % appname)
            scripts_append("/%s/static/scripts/S3/s3.dataLists.js" % appname)
        else:
            scripts_append("/%s/static/scripts/S3/s3.dataLists.min.js" % appname)
        #scripts_append("/%s/static/themes/%s/js/homepage.js" % (appname, THEME))

        self._view(THEME, "index.html")
        return output

# =============================================================================
def filter_formstyle(row_id, label, widget, comment, hidden=False):
    """
        Custom Formstyle for FilterForm

        @param row_id: HTML id for the row
        @param label: the label
        @param widget: the form widget
        @param comment: the comment
        @param hidden: whether the row should initially be hidden or not
    """

    if hidden:
        _class = "advanced hide"
    else:
        _class= ""

    if label:
        return DIV(label, widget, _id=row_id, _class=_class)
    else:
        return DIV(widget, _id=row_id, _class=_class)

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

        fmt = permissions.format

        if current.request.env.request_method == "POST" and fmt != "dl":
            return self.update()

        pe_id = auth.user.pe_id
        s3 = current.response.s3

        # Filter
        f = S3FieldSelector("pe_id") == pe_id
        s3.filter = f

        # List Fields
        current.s3db.configure("pr_filter",
                               list_fields = ["title",
                                              "resource",
                                              "url",
                                              "query"],
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
        T = current.T
        if fmt != "dl":
            output["title"] = T("Saved Filters")
            self._view(THEME, "filters.html")

        # Script for inline-editing of filter title
        options = {"cssclass": "jeditable-input",
                   "tooltip": str(T("Click to edit"))}
        script = """$('.jeditable').editable('%s', %s);""" % \
                 (URL(args="filters"), json.dumps(options))
        s3.jquery_ready.append(script)
        return output

    # -------------------------------------------------------------------------
    @classmethod
    def render_filter(cls, listid, resource, rfields, record, **attr):
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
            record_id = None
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

        # Filter Query and Summary URLs
        fstring = S3FilterString(resource, raw["pr_filter.query"])
        query = fstring.represent()
        links = cls.summary_urls(resource,
                                 raw["pr_filter.url"],
                                 fstring.get_vars)

        actions = []
        if links:
            if "map" in links:
                actions.append(A(I(" ", _class="icon icon-globe"),
                                 _title=T("Open Map"),
                                 _href=links["map"]))
            if "table" in links:
                actions.append(A(I(" ", _class="icon icon-list"),
                                 _title=T("Open Chart"),
                                 _href=links["table"]))
            if "chart" in links:
                actions.append(A(I(" ", _class="icon icon-list"),
                                 _title=T("Open Chart"),
                                 _href=links["chart"]))

        # Render the item
        item = DIV(
                   DIV(DIV(actions,
                           _class="action-bar fleft"),
                       SPAN(T("%(resource)s Filter") % \
                            dict(resource=resource_name),
                            _class="card-title"),
                        DIV(A(I(" ", _class="icon icon-remove-sign"),
                              _title=T("Delete this Filter"),
                              _class="dl-item-delete"),
                            _class="edit-bar fright"),
                       _class="card-header"),
                   DIV(
                       DIV(H5(title,
                              _id="filter-title-%s" % record_id,
                              _class="media-heading jeditable"),
                           DIV(query),
                           _class="media-body"),
                       _class="media"),
                   _class=item_class,
                   _id=item_id)

        return item

    # -------------------------------------------------------------------------
    def update(self):
        """ Simple ajax method to update a saved filter title """

        post_vars = current.request.post_vars

        record_id = post_vars["id"].rsplit("-", 1)[-1]
        new_title = post_vars["value"]

        if new_title:
            ftable = current.s3db.pr_filter
            success = current.db(ftable.id==record_id) \
                             .update(title=new_title)
        else:
            success = False

        if success:
            return new_title
        else:
            raise HTTP(400)

    # -------------------------------------------------------------------------
    @staticmethod
    def summary_urls(resource, url, filters):
        """
            Construct the summary tabs URLs for a saved filter.

            @param resource: the S3Resource
            @param url: the filter page URL
            @param filters: the filter GET vars
        """

        links = {}

        if not url:
            return links

        get_vars = S3URLQuery.parse_url(url)
        get_vars.pop("t", None)
        get_vars.pop("w", None)
        get_vars.update(filters)

        list_vars = []
        for (k, v) in get_vars.items():
            if v is None:
                continue
            values = v if type(v) is list else [v]
            for value in values:
                if value is not None:
                    list_vars.append((k, value))
        base_url = url.split("?", 1)[0]

        summary_config = S3Summary._get_config(resource)
        tab_idx = 0
        for section in summary_config:

            if section.get("common"):
                continue
            section_id = section["name"]

            tab_vars = list_vars + [("t", str(tab_idx))]
            links[section["name"]] = "%s?%s" % (base_url, urlencode(tab_vars))
            tab_idx += 1

        return links
        
# END =========================================================================
