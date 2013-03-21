# -*- coding: utf-8 -*-

from os import path

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3.s3crud import S3CRUD
from s3.s3filter import S3DateFilter, S3LocationFilter, S3OptionsFilter, S3TextFilter
from s3.s3utils import s3_avatar_represent

THEME = "DRMP"

# =============================================================================
class index():
    """ Custom Home Page """

    def __call__(self):

        return homepage()

# =============================================================================
class datalist():
    """ Alternate URL for homepage """

    def __call__(self):

        return homepage()

# =============================================================================
class datalist_dl_post():
    """ AJAX URL for CMS Posts (for Homepage) """

    def __call__(self):

        return homepage()

# =============================================================================
class datalist_dl_filter():
    """ AJAX URL for CMS Posts Filter Form (for Homepage) """

    def __call__(self):

        return homepage()

# =============================================================================
class validate():
    """ Alternate URL for homepage """

    def __call__(self):

        return homepage()

# =============================================================================
def homepage():
    """
        Custom Homepage
        - DataList of CMS Posts
    """

    if not current.auth.is_logged_in():
        return login()

    T = current.T
    s3db = current.s3db
    request = current.request
    response = current.response
    s3 = response.s3

    current.deployment_settings.ui.customize_cms_post()

    list_layout = render_homepage_posts

    filter_widgets = [S3TextFilter(["body"],
                                   label="",
                                   _class="filter-search",
                                   _placeholder=T("Search").upper()),
                      S3OptionsFilter("series_id",
                                      label=T("Filter by Type"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      cols=3),
                      S3LocationFilter("location_id",
                                       label=T("Filter by Location"),
                                       levels=["L1", "L2", "L3"],
                                       #represent="%(name)s",
                                       widget="multiselect",
                                       cols=3),
                      S3OptionsFilter("created_by$organisation_id",
                                      label=T("Filter by Organization"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      #widget="multiselect-bootstrap",
                                      cols=3),
                      S3DateFilter("created_on",
                                   label=T("Filter by Date"),
                                   hide_time=True),
                      ]

    s3db.configure("cms_post",
                   filter_formstyle = filter_formstyle,
                   filter_submit = (T("Filter Results"), "btn btn-primary"),
                   filter_widgets = filter_widgets,
                   list_layout = list_layout,
                   )

    s3.dl_pagelength = 6  # 5 forces an AJAX call

    if "datalist_dl_post" in request.args:
        # DataList pagination or Ajax-deletion request
        request.args = ["datalist"]
        ajax = "list"
    elif "datalist_dl_filter" in request.args:
        # FilterForm options update request
        request.args = ["filter"]
        ajax = "filter"
    else:
        # Default
        request.args = ["datalist"]
        ajax = None

    def prep(r):
        if ajax == "list":
            r.representation = "dl"
        elif ajax == "filter":
            r.representation = "json"
        return True
    s3.prep = prep

    output = current.rest_controller("cms", "post",
                                     list_ajaxurl = URL(f="index",
                                                        args="datalist_dl_post"),
                                     filter_ajax_url = URL(f="index",
                                                           args="datalist_dl_filter",
                                                           vars={}))

    if ajax == "list":
        # Don't override view if this is an Ajax-deletion request
        if not "delete" in request.get_vars:
            response.view = "plain.html"
    elif not ajax:
        form = output["form"]
        # Remove duplicate Submit button
        form[0][-1] = ""
        if form.errors:
            s3.jquery_ready.append('''$("#myModal").modal("show")''')
        # Set Title & View after REST Controller, in order to override
        output["title"] = response.title = current.deployment_settings.get_system_name()
        view = path.join(request.folder, "private", "templates",
                         "DRMP", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        # Latest 5 Disasters
        resource = s3db.resource("event_event")
        list_fields = ["name",
                       "zero_hour",
                       "closed",
                       ]
        orderby = resource.get_config("list_orderby",
                                      ~resource.table.created_on)
        datalist, numrows, ids = resource.datalist(fields=list_fields,
                                                   start=None,
                                                   limit=5,
                                                   listid="event_datalist",
                                                   orderby=orderby,
                                                   layout=render_homepage_events)
        if numrows == 0:
            # Empty table or just no match?

            table = resource.table
            if "deleted" in table:
                available_records = current.db(table.deleted != True)
            else:
                available_records = current.db(table._id > 0)
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
            dl = datalist.html()
            data = dl

        output["disasters"] = data

    return output

# -----------------------------------------------------------------------------
def login():
    """
        Custom Login page
    """

    response = current.response
    request = current.request

    view = path.join(request.folder, "private", "templates",
                     "DRMP", "views", "login.html")
    try:
        # Pass view as file not str to work in compiled mode
        response.view = open(view, "rb")
    except IOError:
        from gluon.http import HTTP
        raise HTTP("404", "Unable to open Custom View: %s" % view)

    response.title = current.T("Login")

    request.args = ["login"]
    auth = current.auth
    auth.settings.formstyle = "bootstrap"
    login = auth()

    return dict(
        form = login
    )

# -----------------------------------------------------------------------------
def filter_formstyle(row_id, label, widget, comment):
    """
        Custom Formstyle for FilterForm

        @param row_id: HTML id for the row
        @param label: the label
        @param widget: the form widget
        @param comment: the comment
    """

    if label:
        return DIV(TR(label),
                   TR(widget))
    else:
        return widget

# -----------------------------------------------------------------------------
def render_homepage_posts(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for CMS Posts on the Homepage

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "cms_post.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    series = record["cms_post.series_id"]
    date = record["cms_post.created_on"]
    body = record["cms_post.body"]
    location = record["cms_post.location_id"]
    location_id = raw["cms_post.location_id"]
    location_url = URL(c="gis", f="location", args=[location_id])
    author = record["cms_post.created_by"]
    author_id = raw["cms_post.created_by"]
    organisation = record["auth_user.organisation_id"]
    organisation_id = raw["auth_user.organisation_id"]
    org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
    # @ToDo: Optimise by not doing DB lookups (especially duplicate) within render, but doing these in the bulk query
    avatar = s3_avatar_represent(author_id,
                                 _class="media-object",
                                 _style="width:50px;padding:5px;padding-top:0px;")
    db = current.db
    s3db = current.s3db
    ltable = s3db.pr_person_user
    ptable = db.pr_person
    query = (ltable.user_id == author_id) & \
            (ltable.pe_id == ptable.pe_id)
    row = db(query).select(ptable.id,
                           limitby=(0, 1)
                           ).first()
    if row:
        person_url = URL(c="hrm", f="person", args=[row.id])
    else:
        person_url = "#"
    author = A(author,
               _href=person_url,
               )
    avatar = A(avatar,
               _href=person_url,
               _class="pull-left",
               )
    permit = current.auth.s3_has_permission
    table = db.cms_post
    if permit("update", table, record_id=record_id):
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="cms", f="post",
                               args=[record_id, "update.popup"],
                               vars={"refresh": listid,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=current.response.s3.crud_strings.cms_post.title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       _class="dl-item-delete",
                      )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )
    # @ToDo: Dropdown of available documents
    document = raw["doc_document.file"]
    if document:
        doc_url = URL(c="default", f="download",
                      args=[document]
                      )
        doc_link = A(I(_class="icon icon-paper-clip fright"),
                     _href=doc_url)
    else:
        doc_link = ""

    if series == "Alert":
        item_class = "%s disaster" % item_class

    # Render the item
    item = DIV(DIV(I(SPAN(" %s" % current.T(series),
                          _class="card-title",
                          ),
                     _class="icon icon-%s" % series.lower().replace(" ", "_"),
                     ),
                   SPAN(A(location,
                          _href=location_url,
                          ),
                        _class="location-title",
                        ),
                   SPAN(date,
                        _class="date-title",
                        ),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(avatar,
                   DIV(DIV(body,
                           DIV(author,
                               " - ",
                               A(organisation,
                                 _href=org_url,
                                 _class="card-organisation",
                                 ),
                               doc_link,
                               _class="card-person",
                               ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def render_homepage_events(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for Events on the Homepage

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "event_event.id"

    # Construct the item ID
    if pkey in record:
        item_id = "%s-%s" % (listid, record[pkey])
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    record_id = raw["event_event.id"]
    name = record["event_event.name"]
    date = record["event_event.zero_hour"]
    closed = raw["event_event.closed"]

    if closed:
        edit_bar = DIV()
    else:
        item_class = "%s disaster" % item_class

        # @ToDo: Check Permissions
        edit_bar = DIV(A(I(" ",
                           _class="icon icon-edit",
                           ),
                         _class="s3_modal",
                         _href=URL(c="event", f="event",
                                   args=[record_id, "update.popup"],
                                   vars={"refresh": listid,
                                         "record": record_id}),
                         ),
                       A(I(" ",
                           _class="icon icon-remove-sign",
                           ),
                         _href=URL(c="event", f="event",
                                   args=[record_id, "delete"]),
                         ),
                       _class="edit-bar fright",
                       )

    # Render the item
    item = DIV(edit_bar,
               A(H5(name),
                 SPAN(date,
                      _class="date-title",
                      ),
                 _href=URL(c="event", f="event",
                           args=[record_id, "profile"]),
                 ),
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
class glossary():
    """
        Custom page
    """

    def __call__(self):

        view = path.join(current.request.folder, "private", "templates",
                         THEME, "views", "glossary.html")
        try:
            # Pass view as file not str to work in compiled mode
            current.response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        title = current.T("Glossary")

        return dict(
                title = title,
            )

# END =========================================================================
