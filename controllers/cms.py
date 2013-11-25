# -*- coding: utf-8 -*-

"""
    CMS

    Simple Content Management System
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

from datetime import timedelta

# =============================================================================
def index():
    """ Module homepage """

    return s3db.cms_index(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the list of Posts
    redirect(URL(f="post"))

# -----------------------------------------------------------------------------
def series():
    """ RESTful CRUD controller """

    # Pre-process
    def prep(r):
        if r.component:
            # Settings are defined at the series level
            table = s3db.cms_post
            _avatar = table.avatar
            _avatar.readable = _avatar.writable = False
            _avatar.default = r.record.avatar
            _location = table.location_id
            if not r.record.location:
                _location.readable = _location.writable = False
            _replies = table.replies
            _replies.readable = _replies.writable = False
            _replies.default = r.record.replies
            _roles_permitted = table.roles_permitted
            _roles_permitted.readable = _roles_permitted.writable = False
            _roles_permitted.default = r.record.roles_permitted
            if not r.record.richtext:
                table.body.widget = None
            # Titles do show up
            table.name.comment = ""
        return True
    s3.prep = prep

    return s3_rest_controller(rheader=s3db.cms_rheader)

# -----------------------------------------------------------------------------
def blog():
    """
        RESTful CRUD controller for display of a series of posts as a full-page
        read-only showing last 5 items in reverse time order

        @ToDo: Convert to dataList
    """

    # Pre-process
    def prep(r):
        s3db.configure(r.tablename, listadd=False)
        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.record:
            response.view = s3base.S3CRUD._view(r, "cms/blog.html")
        return output
    s3.postp = postp

    output = s3_rest_controller("cms", "series")
    return output

# -----------------------------------------------------------------------------
def post():
    """ RESTful CRUD controller """

    tablename = "cms_post"
    # Filter out those posts which are part of a series
    #table = s3db[tablename]
    #s3.filter = (table.series_id == None)

    # Custom Method to add Comments
    s3db.set_method(module, resourcename,
                    method="discuss",
                    action=discuss)

    def prep(r):
        if r.interactive:
            if r.method in ("create", "update"):
                table = r.table
                get_vars = request.get_vars

                # Filter from a Profile page?"
                series = get_vars.get("~.series_id$name", None)
                if series:
                    # Lookup ID
                    stable = db.cms_series
                    row = db(stable.name == series).select(stable.id,
                                                           limitby=(0, 1)
                                                           ).first()
                    if row:
                        field = table.series_id
                        field.default = row.id
                        field.readable = field.writable = False

                # Context from a Profile page?"
                location_id = get_vars.get("(location)", None)
                if location_id:
                    field = table.location_id
                    field.default = location_id
                    field.readable = field.writable = False

                page = get_vars.get("page", None)
                if page:
                    table.name.default = page
                    table.name.readable = table.name.writable = False
                    _crud = s3.crud_strings[tablename]
                    _crud.title_create = T("New Page")
                    _crud.title_update = T("Edit Page")
                    url = URL(c="default", f="index", vars={"page": page})
                    s3db.configure(tablename,
                                   create_next = url,
                                   update_next = url)

                _module = get_vars.get("module", None)
                if _module:
                    table.avatar.readable = table.avatar.writable = False
                    table.location_id.readable = table.location_id.writable = False
                    table.date.readable = table.date.writable = False
                    table.expired.readable = table.expired.writable = False
                    resource = request.get_vars.get("resource", None)
                    if resource in ("contact", "index"):
                        # We're creating/updating text for a Contact page
                        table.name.default = "Contact Page"
                        #table.title.readable = table.title.writable = False
                        table.replies.readable = table.replies.writable = False
                        url = URL(c=_module, f=resource)
                    elif resource:
                        # We're creating/updating text for a Resource Summary page
                        table.name.default = "%s Summary Page Header" % resource
                        table.title.readable = table.title.writable = False
                        table.replies.readable = table.replies.writable = False
                        url = URL(c=_module, f=resource, args="summary")
                    else:
                        # We're creating/updating a Module home page
                        table.name.default = "%s Home Page" % _module
                        _crud = s3.crud_strings[tablename]
                        _crud.title_create = T("New Page")
                        _crud.title_update = T("Edit Page")
                        url = URL(c=_module, f="index")

                    s3db.configure(tablename,
                                   create_next = url,
                                   update_next = url)

                layer_id = get_vars.get("layer_id", None)
                if layer_id:
                    # Editing cms_post_layer
                    table.name.default = "Metadata Page for Layer %s" % layer_id
                    table.name.readable = table.name.writable = False
                    table.avatar.readable = table.avatar.writable = False
                    table.location_id.readable = table.location_id.writable = False
                    table.title.readable = table.title.writable = False
                    table.replies.readable = table.replies.writable = False
                    table.date.readable = table.date.writable = False
                    table.expired.readable = table.expired.writable = False
                    _crud = s3.crud_strings[tablename]
                    _crud.title_create = T("Add Metadata")
                    _crud.title_update = T("Edit Metadata")

                if r.component_name == "module":
                    modules = {}
                    _modules = current.deployment_settings.modules
                    for module in _modules:
                        if module in ("appadmin", "errors", "ocr"):
                            continue
                        modules[module] = _modules[module].name_nice
                    s3db.cms_post_module.field.requires = \
                        IS_IN_SET_LAZY(lambda: sort_dict_by_values(modules))

        return True
    s3.prep = prep

    output = s3_rest_controller(rheader=s3db.cms_rheader)
    return output

# -----------------------------------------------------------------------------
def page():
    """
        RESTful CRUD controller for display of a post as a full-page read-only
        - with optional Comments
    """

    # Pre-process
    def prep(r):
        s3db.configure(r.tablename, listadd=False)
        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.record:
            output = {"item": r.record.body}
            current.menu.options = None
            response.view = s3base.S3CRUD._view(r, "cms/page.html")
            if r.record.replies:
                ckeditor = URL(c="static", f="ckeditor", args="ckeditor.js")
                s3.scripts.append(ckeditor)
                adapter = URL(c="static", f="ckeditor", args=["adapters",
                                                              "jquery.js"])
                s3.scripts.append(adapter)

                # Toolbar options: http://docs.cksource.com/CKEditor_3.x/Developers_Guide/Toolbar
                js = "".join((
'''i18n.reply="''', str(T("Reply")), '''"
var img_path=S3.Ap.concat('/static/img/jCollapsible/')
var ck_config={toolbar:[['Bold','Italic','-','NumberedList','BulletedList','-','Link','Unlink','-','Smiley','-','Source','Maximize']],toolbarCanCollapse:false,removePlugins:'elementspath'}
function comment_reply(id){
 $('#cms_comment_post_id__row').hide()
 $('#cms_comment_post_id__row1').hide()
 $('#comment-title').html(i18n.reply)
 $('#cms_comment_body').ckeditorGet().destroy()
 $('#cms_comment_body').ckeditor(ck_config)
 $('#comment-form').insertAfter($('#comment-'+id))
 $('#cms_comment_parent').val(id)
 var post_id = $('#comment-'+id).attr('post_id')
 $('#cms_comment_post_id').val(post_id)
}'''))

                s3.js_global.append(js)
        return output
    s3.postp = postp

    output = s3_rest_controller("cms", "post")
    return output

# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
def cms_post_age(row):
    """
        The age of the post
        - used for colour-coding markers of Alerts & Incidents
    """

    if hasattr(row, "cms_post"):
        row = row.cms_post
    try:
        date = row.date
    except:
        # not available
        return messages["NONE"]

    now = request.utcnow
    age = now - date
    if age < timedelta(days=2):
        return 1
    elif age < timedelta(days=7):
        return 2
    else:
        return 3

# -----------------------------------------------------------------------------
def newsfeed():
    """
        RESTful CRUD controller for display of posts as a filterable dataList
    """

    # Load Model
    table = s3db.cms_post
    title_list = T("Latest Information")

    # Hide Posts linked to Modules & Expired Posts
    FS = s3base.S3FieldSelector
    s3.filter = (FS("post_module.module") == None) & (FS("expired") != True)

    # Ensure that filtered views translate into options which update the Widget
    get_vars = request.get_vars
    if "~.series_id$name" in get_vars:
        series_name = get_vars["~.series_id$name"]
        # Disabled as can change filters dynamically
        # @ToDo: Better Mechanism: Another field in cms_series?
        #if series_name == "Request":
        #    title_list = T("Latest Requests")
        #elif series_name == "Offer":
        #    title_list = T("Latest Offers")
        stable = s3db.cms_series
        series = db(stable.name == series_name).select(stable.id,
                                                       limitby=(0, 1)).first()
        if series:
            series_id = str(series.id)
            get_vars.pop("~.series_id$name")
            get_vars["~.series_id__belongs"] = series_id

    s3.crud_strings["cms_post"].title_list = title_list

    # Which levels of Hierarchy are we using?
    hierarchy = gis.get_location_hierarchy()
    levels = hierarchy.keys()
    if len(settings.get_gis_countries()) == 1:
        levels.remove("L0")

    # @ToDo: deployment_setting
    #org_field = "created_by$organisation_id"
    org_field = "post_organisation.organisation_id"

    # @ToDo: deployment_setting
    #contact_field = "created_by"
    #table.created_by.represent = s3_auth_user_represent_name
    contact_field = "person_id"

    from s3.s3filter import S3TextFilter, S3OptionsFilter, S3LocationFilter, S3DateFilter
    filter_widgets = [S3TextFilter(["body"],
                                   label=T("Search"),
                                   _class="filter-search",
                                   #_placeholder=T("Search").upper(),
                                   ),
                      S3OptionsFilter("series_id",
                                      label=T("Filter by Type"),
                                      # We want translations
                                      #represent="%(name)s",
                                      # @ToDo: deployment_setting or introspect when vals > 3?
                                      #widget="multiselect",
                                      cols=2,
                                      hidden=True,
                                      ),
                      S3LocationFilter("location_id",
                                       label=T("Filter by Location"),
                                       levels=levels,
                                       widget="multiselect",
                                       hidden=True,
                                       ),
                      S3OptionsFilter(org_field,
                                      label=T("Filter by Organization"),
                                      # Can't use this for created_by as integer, use field.represent instead
                                      #represent="%(name)s",
                                      widget="multiselect",
                                      hidden=True,
                                      ),
                      S3DateFilter("date",
                                   label=T("Filter by Date"),
                                   hide_time=True,
                                   hidden=True,
                                   ),
                      ]

    s3db.configure("cms_post",
                   # We could use a custom Advanced widget
                   #filter_advanced = False,
                   filter_formstyle = filter_formstyle,
                   # No Submit button (done automatically)
                   #filter_submit = (T("SEARCH"), "btn btn-primary"),
                   filter_widgets = filter_widgets,
                   list_layout = s3db.cms_render_posts,
                   # Create form comes via AJAX in a Modal
                   #insertable = False,
                   notify_fields = [(T("Type"), "series_id"),
                                    (T("Date"), "date"),
                                    (T("Location"), "location_id"),
                                    (T("Organization"), org_field),
                                    (T("Contact"), contact_field),
                                    (T("Description"), "body"),
                                    ],
                   notify_template = "notify_post",
                   )

    s3.dl_pagelength = 6  # 5 forces an AJAX call

    def prep(r):
        if r.interactive or r.representation == "aadata":
            s3db.cms_customize_post_fields()

        if r.interactive:
            field = table.series_id
            field.label = T("Type")

            if r.method == "read":
                # Restore the label for the Location
                table.location_id.label = T("Location")
            elif r.method == "create":
                pass
                # @ToDo: deployment_setting
                #ADMIN = session.s3.system_roles.ADMIN
                #if (not auth.s3_has_role(ADMIN)):
                #    represent = S3Represent(lookup="cms_series", 
                #                            translate=settings.get_L10n_translate_cms_series())
                #    field.requires = IS_ONE_OF(db, 
                #                               "cms_series.id",
                #                               represent,
                #                               not_filterby="name",
                #                               not_filter_opts = ["Alert"], 
                #                               )

            refresh = get_vars.get("refresh", None)
            if refresh == "datalist":
                # We must be coming from the News Feed page so can change the type on-the-fly
                field.readable = field.writable = True
            #field.requires = field.requires.other
            #field = table.name
            #field.readable = field.writable = False
            #field = table.title
            #field.readable = field.writable = False
            field = table.avatar
            field.default = True
            #field.readable = field.writable = False
            field = table.replies
            field.default = False
            #field.readable = field.writable = False

            field = table.body
            field.label = T("Description")
            # Plain text not Rich
            from s3.s3widgets import s3_comments_widget
            field.widget = s3_comments_widget
            #table.comments.readable = table.comments.writable = False

            #if request.controller == "default":
            #    # Don't override card layout for News Feed/Homepage
            #    return True

            from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent

            # Filter from a Profile page?
            # If so, then default the fields we know
            location_id = get_vars.get("~.(location)", None)
            if location_id:
                table.location_id.default = location_id
            event_id = get_vars.get("~.(event)", None)
            if event_id:
                crud_form = S3SQLCustomForm(
                    "date",
                    "series_id",
                    "body",
                    "location_id",
                    S3SQLInlineComponent(
                        "document",
                        name = "file",
                        label = T("Files"),
                        fields = ["file",
                                  #"comments",
                                  ],
                    ),
                )
                def create_onaccept(form):
                    table = current.s3db.event_event_post
                    table.insert(event_id=event_id,
                                 post_id=form.vars.id)

                s3db.configure("cms_post",
                               create_onaccept = create_onaccept, 
                               )
            else:
                crud_form = S3SQLCustomForm(
                    "date",
                    "series_id",
                    "body",
                    "location_id",
                    # @ToDo: deployment_setting for Events
                    #S3SQLInlineComponent(
                    #    "event_post",
                    #    #label = T("Disaster(s)"),
                    #    label = T("Disaster"),
                    #    multiple = False,
                    #    fields = ["event_id"],
                    #    orderby = "event_id$name",
                    #),
                    # @ToDo: deployment_setting
                    S3SQLInlineComponent(
                        "post_organisation",
                        label = T("Organization"),
                        fields = ["organisation_id"],
                        # @ToDo: deployment_setting
                        multiple = False,
                    ),
                    # @ToDo: deployment_setting
                    "person_id",
                    S3SQLInlineComponent(
                        "document",
                        name = "file",
                        label = T("Files"),
                        fields = ["file",
                                  #"comments",
                                  ],
                    ),
                )

            # Return to List view after create/update/delete
            # We now do all this in Popups
            #url_next = URL(c="default", f="index", args="newsfeed")

            s3db.configure("cms_post",
                           #create_next = url_next,
                           #delete_next = url_next,
                           #update_next = url_next,
                           crud_form = crud_form,
                           # Don't include a Create form in 'More' popups
                           listadd = False,
                           list_layout = s3db.cms_render_posts,
                           )

            s3.cancel = True

        elif r.representation == "xls":
            table.created_by.represent = s3base.s3_auth_user_represent_name
            #table.created_on.represent = datetime_represent
            utable = auth.settings.table_user
            utable.organisation_id.represent = s3db.org_organisation_represent

            list_fields = [(T("Date"), "date"),
                           #(T("Disaster"), "event_post.event_id"),
                           (T("Type"), "series_id"),
                           (T("Details"), "body"),
                           ]
            for level in levels:
                list_fields.append((hierarchy[level], "location_id$%s" % level))
            list_fields = + [(T("Contact"), contact_field),
                             (T("Organization"), org_field),
                             ]
            s3db.configure("cms_post",
                           list_fields = list_fields,
                           )

        elif r.representation == "plain" and \
             r.method != "search":
            # Map Popups
            table.location_id.represent = s3db.gis_LocationRepresent(sep=" | ")
            table.created_by.represent = s3base.s3_auth_user_represent_name
            # Used by default popups
            series = table.series_id.represent(r.record.series_id)
            s3.crud_strings["cms_post"].title_display = "%(series)s Details" % dict(series=series)
            s3db.configure("cms_post",
                           popup_url="",
                           )
            table.avatar.readable = False
            table.body.label = ""
            table.expired.readable = False
            table.replies.readable = False
            table.created_by.readable = True
            table.created_by.label = T("Author")
            # Used by cms_post_popup
            #table.created_on.represent = datetime_represent

        elif r.representation == "geojson":
            r.table.age = Field.Lazy(cms_post_age)

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if r.method == "datalist" and r.representation != "dl":
                response.view = s3base.S3CRUD._view(r, "cms/newsfeed.html")
        return output
    s3.postp = postp

    output = s3_rest_controller("cms", "post",
                                hide_filter=False,
                                )
    return output

# =============================================================================
# Comments
# =============================================================================
def discuss(r, **attr):
    """ Custom Method to manage the discussion of a Post """

    id = r.id

    # Add the RHeader to maintain consistency with the other pages
    rheader = s3db.cms_rheader(r)

    ckeditor = URL(c="static", f="ckeditor", args="ckeditor.js")
    s3.scripts.append(ckeditor)
    adapter = URL(c="static", f="ckeditor", args=["adapters",
                                                  "jquery.js"])
    s3.scripts.append(adapter)

    # Toolbar options: http://docs.cksource.com/CKEditor_3.x/Developers_Guide/Toolbar
    js = "".join((
'''i18n.reply="''', str(T("Reply")), '''"
var img_path=S3.Ap.concat('/static/img/jCollapsible/')
var ck_config={toolbar:[['Bold','Italic','-','NumberedList','BulletedList','-','Link','Unlink','-','Smiley','-','Source','Maximize']],toolbarCanCollapse:false,removePlugins:'elementspath'}
function comment_reply(id){
 $('#cms_comment_post_id__row').hide()
 $('#cms_comment_post_id__row1').hide()
 $('#comment-title').html(i18n.reply)
 $('#cms_comment_body').ckeditorGet().destroy()
 $('#cms_comment_body').ckeditor(ck_config)
 $('#comment-form').insertAfter($('#comment-'+id))
 $('#cms_comment_parent').val(id)
 var post_id=$('#comment-'+id).attr('post_id')
 $('#cms_comment_post_id').val(post_id)
}'''))

    s3.js_global.append(js)

    response.view = "cms/discuss.html"
    return dict(rheader=rheader,
                id=id)

# -----------------------------------------------------------------------------
def comment_parse(comment, comments, post_id=None):
    """
        Parse a Comment

        @param: comment - a gluon.sql.Row: the current comment
        @param: comments - a gluon.sql.Rows: full list of comments
        @param: post_id - a reference ID: optional post commented on
    """

    author = B(T("Anonymous"))
    if comment.created_by:
        utable = s3db.auth_user
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        query = (utable.id == comment.created_by)
        left = [ltable.on(ltable.user_id == utable.id),
                ptable.on(ptable.pe_id == ltable.pe_id)]
        row = db(query).select(utable.email,
                               ptable.first_name,
                               ptable.middle_name,
                               ptable.last_name,
                               left=left, limitby=(0, 1)).first()
        if row:
            person = row.pr_person
            user = row[utable._tablename]
            username = s3_fullname(person)
            email = user.email.strip().lower()
            import hashlib
            hash = hashlib.md5(email).hexdigest()
            url = "http://www.gravatar.com/%s" % hash
            author = B(A(username, _href=url, _target="top"))
    if not post_id and comment.post_id:
        post = "re: %s" % s3db.cms_post[comment.post_id].name
        header = DIV(author, " ", post)
        post_id = comment.post_id
    else:
        header = author
    thread = LI(DIV(s3base.s3_avatar_represent(comment.created_by),
                    DIV(DIV(header,
                            _class="comment-header"),
                        DIV(XML(comment.body)),
                        _class="comment-text"),
                        DIV(DIV(comment.created_on,
                                _class="comment-date"),
                            DIV(A(T("Reply"),
                                  _class="action-btn"),
                                _onclick="comment_reply(%i);" % comment.id,
                                _class="comment-reply"),
                            _class="fright"),
                    _id="comment-%i" % comment.id,
                    _post_id=post_id,
                    _class="comment-box"))

    # Add the children of this thread
    children = UL(_class="children")
    id = comment.id
    count = 0
    for comment in comments:
        if comment.parent == id:
            count = 1
            child = comment_parse(comment, comments, post_id=post_id)
            children.append(child)
    if count == 1:
        thread.append(children)

    return thread

# -----------------------------------------------------------------------------
def comments():
    """
        Function accessed by AJAX to handle Comments
        - for discuss(() & page()
    """

    try:
        post_id = request.args[0]
    except:
        raise HTTP(400)

    table = s3db.cms_comment

    # Form to add a new Comment
    table.post_id.default = post_id
    table.post_id.writable = table.post_id.readable = False
    form = crud.create(table)

    # List of existing Comments
    comments = db(table.post_id == post_id).select(table.id,
                                                   table.parent,
                                                   table.body,
                                                   table.created_by,
                                                   table.created_on)

    output = UL(_id="comments")
    for comment in comments:
        if not comment.parent:
            # Show top-level threads at top-level
            thread = comment_parse(comment, comments, post_id=post_id)
            output.append(thread)

    # Also see the outer discuss()
    script = \
'''$('#comments').collapsible({xoffset:'-5',yoffset:'50',imagehide:img_path+'arrow-down.png',imageshow:img_path+'arrow-right.png',defaulthide:false})
$('#cms_comment_parent__row1').hide()
$('#cms_comment_parent__row').hide()
$('#cms_comment_body').ckeditor(ck_config)
$('#submit_record__row input').click(function(){
 $('#comment-form').hide()
 $('#cms_comment_body').ckeditorGet().destroy()
 return true
})'''

    # No layout in this output!
    #s3.jquery_ready.append(script)

    output = DIV(output,
                 DIV(H4(T("New Post"),
                        _id="comment-title"),
                     form,
                     _id="comment-form",
                     _class="clear"),
                 SCRIPT(script))

    return XML(output)

# -----------------------------------------------------------------------------
def posts():
    """
        Function accessed by AJAX to handle a Series of Posts
    """

    try:
        series_id = request.args[0]
    except:
        raise HTTP(400)

    try:
        recent = request.args[1]
    except:
        recent = 5

    table = s3db.cms_post

    # List of Posts in this Series
    query = (table.series_id == series_id)
    posts = db(query).select(table.name,
                             table.body,
                             table.avatar,
                             table.created_by,
                             table.created_on,
                             limitby=(0, recent))

    output = UL(_id="comments")
    import hashlib
    for post in posts:
        author = B(T("Anonymous"))
        if post.created_by:
            utable = s3db.auth_user
            ptable = s3db.pr_person
            ltable = s3db.pr_person_user
            query = (utable.id == post.created_by)
            left = [ltable.on(ltable.user_id == utable.id),
                    ptable.on(ptable.pe_id == ltable.pe_id)]
            row = db(query).select(utable.email,
                                   ptable.first_name,
                                   ptable.middle_name,
                                   ptable.last_name,
                                   left=left, limitby=(0, 1)).first()
            if row:
                person = row.pr_person
                user = row[utable._tablename]
                username = s3_fullname(person)
                email = user.email.strip().lower()
                hash = hashlib.md5(email).hexdigest()
                url = "http://www.gravatar.com/%s" % hash
                author = B(A(username, _href=url, _target="top"))
        header = H4(post.name)
        if post.avatar:
            avatar = s3base.s3_avatar_represent(post.created_by)
        else:
            avatar = ""
        row = LI(DIV(avatar,
                     DIV(DIV(header,
                             _class="comment-header"),
                         DIV(XML(post.body)),
                         _class="comment-text"),
                         DIV(DIV(post.created_on,
                                 _class="comment-date"),
                             _class="fright"),
                         DIV(author,
                             _class="comment-footer"),
                     _class="comment-box"))
        output.append(row)

    return XML(output)

# END =========================================================================
