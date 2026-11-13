"""
    CMS - Simple Content Management System
"""

module = request.controller

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
    s3_redirect_default(URL(f="post"))

# =============================================================================
# Series Management
#
def series():
    """ RESTful CRUD controller """

    # Pre-process
    def prep(r):

        record = r.record

        if record and r.component_name == "post":

            component = r.component
            ctable = component.table

            ctable.name.comment = None

            # Apply series settings
            field = ctable.avatar
            field.readable = field.writable = False
            field.default = record.avatar

            field = ctable.replies
            field.readable = field.writable = False
            field.default = record.replies

            field = ctable.roles_permitted
            field.readable = field.writable = False
            field.default = record.roles_permitted

            field = ctable.location_id
            field.readable = field.writable = bool(record.location)

            if record.richtext:
                ctable.body.represent = lambda body: XML(body)
                ctable.body.widget = s3_richtext_widget
            else:
                ctable.body.represent = lambda body: XML(s3base.s3_URLise(body))
                ctable.body.widget = None

            # Special-purpose series
            if record.name == "Announcements":
                # Homepage announcements for logged-in users

                field = ctable.priority
                field.readable = field.writable = True

                from core import CustomForm, InlineLink

                crud_fields = ["name",
                               "body",
                               "priority",
                               "date",
                               "expired",
                               InlineLink("roles",
                                          label = T("Roles"),
                                          field = "group_id",
                                          ),
                               ]
                list_fields = ["date",
                               "priority",
                               "name",
                               "body",
                               "post_role.group_id",
                               "expired",
                               ]

                component.configure(crud_form = CustomForm(*crud_fields),
                                    list_fields = list_fields,
                                    orderby = "cms_post.date desc",
                                    )

        return True
    s3.prep = prep

    return crud_controller(rheader=s3db.cms_rheader)

# =============================================================================
# Statuses
#
def status():
    """ RESTful CRUD controller """

    return crud_controller()

# =============================================================================
# Tags
#
def tag():
    """ RESTful CRUD controller """

    return crud_controller()

# =============================================================================
# Post authoring
#
def post():
    """ RESTful CRUD controller """

    tablename = "cms_post"
    # Filter out those posts which are part of a series
    #table = s3db[tablename]
    #s3.filter = (table.series_id == None)

    # Custom Method to add Comments
    s3db.set_method("cms_post",
                    method = "discuss",
                    action = discuss)

    def prep(r):
        if r.interactive:
            method = r.method
            if method in ("create", "update"):
                table = r.table

                # Filter from a Profile page?"
                series = get_vars.get("~.series_id$name", None)
                if series:
                    # Lookup ID
                    stable = db.cms_series
                    row = db(stable.name == series).select(stable.id,
                                                           limitby = (0, 1)
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
                url = get_vars.get("url") # custom redirect
                if page:
                    if method == "create":
                        query = (table.name == page) & \
                                (table.deleted == False)
                        record = current.db(query).select(table.id,
                                                          limitby = (0, 1)
                                                          ).first()
                        if record:
                            record_id = record.id
                            r.id = record_id
                            r.resource.add_filter(table.id == record_id)
                            r.method = "update"
                    table.name.default = page
                    table.name.readable = table.name.writable = False
                    _crud = s3.crud_strings[tablename]
                    _crud.label_create = T("New Page")
                    _crud.title_update = T("Edit Page")
                    if not url:
                        url = URL(c="default", f="index", vars={"page": page})
                    s3db.configure(tablename,
                                   create_next = url,
                                   update_next = url,
                                   )

                _module = get_vars.get("module", None)
                if _module:
                    table.avatar.readable = table.avatar.writable = False
                    table.location_id.readable = table.location_id.writable = False
                    table.date.readable = table.date.writable = False
                    table.expired.readable = table.expired.writable = False
                    # We always want the Rich Text widget here
                    table.body.widget = s3base.s3_richtext_widget
                    resource = get_vars.get("resource", None)
                    if resource in ("about", "contact", "help", "index"):

                        if resource == "about":
                            # We're creating/updating text for the About page
                            table.name.default = "About Page"
                        elif resource == "contact":
                            # We're creating/updating text for a Contact page
                            table.name.default = "Contact Page"
                        elif resource == "help":
                            # We're creating/updating text for the Help page
                            table.name.default = "Help Page"
                        else:
                            # We're creating/updating text for the Home page
                            table.name.default = "Home Page"

                        #table.title.readable = table.title.writable = False
                        table.replies.readable = table.replies.writable = False
                        if not url:
                            url = URL(c=_module, f=resource)
                    else:
                        record = get_vars.get("record", None)
                        if record:
                            # We're creating/updating text for a Profile page
                            table.name.default = "%s %s Profile Page" % (resource, record)
                            table.title.readable = table.title.writable = False
                            table.replies.readable = table.replies.writable = False
                            if not url:
                                url = URL(c=_module, f=resource, args=[record, "profile"])
                        elif resource:
                            # We're creating/updating text for a Resource Summary page
                            table.name.default = "%s Summary Page Header" % resource
                            table.title.readable = table.title.writable = False
                            table.replies.readable = table.replies.writable = False
                            if not url:
                                url = URL(c=_module, f=resource, args="summary")
                        else:
                            # We're creating/updating a Module home page
                            table.name.default = "%s Home Page" % _module
                            _crud = s3.crud_strings[tablename]
                            _crud.label_create = T("New Page")
                            _crud.title_update = T("Edit Page")
                            if not url:
                                url = URL(c=_module, f="index")

                    s3db.configure(tablename,
                                   create_next = url,
                                   update_next = url,
                                   )

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
                    _crud.label_create = T("Add Metadata")
                    _crud.title_update = T("Edit Metadata")

                if r.component_name == "module":
                    modules = {}
                    _modules = current.deployment_settings.modules
                    for module in _modules:
                        if module in ("appadmin", "errors"):
                            continue
                        modules[module] = _modules[module].get("name_nice")
                    s3db.cms_post_module.field.requires = IS_IN_SET_LAZY(
                        # Sort modules by human-readable name
                        lambda: sorted(modules.items(), key=lambda item: item[1]),
                        )

        return True
    s3.prep = prep

    return crud_controller(rheader=s3db.cms_rheader)

# =============================================================================
# Posts Rendering
#
def page():
    """
        RESTful CRUD controller for display of a post as a full-page read-only
        - with optional Comments
    """

    found = True
    get_vars = request.get_vars
    if "name" in get_vars:
        table = s3db.cms_post
        query = (table.name == get_vars.name) & \
                (table.deleted != True)
        row = db(query).select(table.id,
                               limitby = (0, 1)
                               ).first()
        if row:
            request.args.append(str(row.id))
        else:
            found = False

    # Pre-process
    def prep(r):
        if not found:
            r.error(404, T("Page not found"), next=auth.permission.homepage)
        s3db.configure(r.tablename, listadd=False)
        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.record and not r.transformable():
            output = {"item": s3base.XMLContentsRepresent(r.record.body).xml()}
            current.menu.options = None
            response.view = s3base.BasicCRUD._view(r, "cms/page.html")
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

    return crud_controller("cms", "post")

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
                             limitby = (0, recent)
                             )

    output = UL(_id="comments")
    import hashlib
    for post in posts:
        author = T("Anonymous")
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
                                   left = left,
                                   limitby = (0, 1)
                                   ).first()
            if row:
                person = row.pr_person
                user = row[utable._tablename]
                username = s3_fullname(person)
                email = user.email.strip().lower()
                hash = hashlib.md5(email.encode("utf-8")).hexdigest()
                url = "http://www.gravatar.com/%s" % hash
                author = A(username, _href=url, _target="top")
        header = H4(post.name)
        if post.avatar:
            avatar = s3base.s3_avatar_represent(post.created_by)
        else:
            avatar = ""
        row = LI(DIV(avatar,
                     DIV(DIV(header,
                             _class = "comment-header",
                             ),
                         DIV(XML(post.body),
                             _class = "comment-body",
                             ),
                         _class="comment-text"),
                         DIV(DIV(post.created_on,
                                 _class = "comment-date",
                                 ),
                             _class="fright"),
                         DIV(author,
                             _class = "comment-footer",
                             ),
                     _class = "comment-box",
                     ))
        output.append(row)

    return XML(output)

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
            response.view = s3base.BasicCRUD._view(r, "cms/blog.html")
        return output
    s3.postp = postp

    return crud_controller("cms", "series")

# =============================================================================
# Newsfeed
#
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
        (use with /datalist method)
    """

    # Load Model
    table = s3db.cms_post
    stable = db.cms_series

    # Hide Posts linked to Modules and Maps & Expired Posts
    s3.filter = (FS("post_module.module") == None) & \
                (FS("post_layer.layer_id") == None) & \
                (FS("expired") != True)

    title_list = T("Latest Information")

    # Ensure that filtered views translate into options which update the Widget
    if "~.series_id$name" in get_vars:
        series_name = get_vars["~.series_id$name"]
        # Disabled as can change filters dynamically
        # @ToDo: Better Mechanism: Another field in cms_series?
        #if series_name == "Request":
        #    title_list = T("Latest Requests")
        #elif series_name == "Offer":
        #    title_list = T("Latest Offers")
        series = db(stable.name == series_name).select(stable.id,
                                                       cache=s3db.cache,
                                                       limitby=(0, 1)).first()
        if series:
            series_id = str(series.id)
            get_vars.pop("~.series_id$name")
            get_vars["~.series_id__belongs"] = series_id

    s3.crud_strings["cms_post"].title_list = title_list

    contact_field = settings.get_cms_person()
    org_field = settings.get_cms_organisation()
    org_group_field = settings.get_cms_organisation_group()
    show_events = settings.get_cms_show_events()

    hidden = not settings.get_cms_filter_open()

    from core import TextFilter, OptionsFilter, LocationFilter, DateFilter
    filter_widgets = [TextFilter(["body"],
                                 label = T("Search"),
                                 _class = "filter-search",
                                 #_placeholder = T("Search").upper(),
                                 ),
                      LocationFilter("location_id",
                                     label = T("Filter by Location"),
                                     hidden = hidden,
                                     ),
                      ]
    fappend = filter_widgets.append
    finsert = filter_widgets.insert

    if show_events:
        fappend(OptionsFilter("event_post.event_id",
                              label = T("Filter by Disaster"),
                              hidden = hidden,
                              ))

    if org_field:
        fappend(OptionsFilter(org_field,
                              label = T("Filter by Organization"),
                              # Can't use this for created_by as integer, use field.represent instead
                              #represent = "%(name)s",
                              hidden = hidden,
                              ))

    if org_group_field:
        group_label = settings.get_org_groups()
        if group_label:
            fappend(OptionsFilter(org_group_field,
                                  label = T("Filter by %(type)s") % dict(type=T(group_label)),
                                  # Can't use this for created_by as integer, use field.represent instead
                                  #represent = "%(name)s",
                                  hidden = hidden,
                                  ))

    fappend(DateFilter("date",
                       label = T("Filter by Date"),
                       hide_time = True,
                       hidden = hidden,
                       ))

    if settings.get_cms_show_tags():
        finsert(1, OptionsFilter("tag_post.tag_id",
                                 label = T("Filter by Tag"),
                                 represent = "%(name)s",
                                 hidden = hidden,
                                 ))

    if settings.get_cms_bookmarks() and auth.user:
        finsert(1, OptionsFilter("bookmark.user_id",
                                 label = T("Filter by Bookmark"),
                                 # Can't just use "" as this is then omitted from rendering
                                 options = {"*": T("All"),
                                            auth.user.id: T("My Bookmarks"),
                                            },
                                 cols = 2,
                                 multiple = False,
                                 hidden = hidden,
                                 ))

    notify_fields = [(T("Date"), "date"),
                     (T("Location"), "location_id"),
                     ]

    len_series = db(stable.deleted == False).count()
    if len_series > 3:
        notify_fields.insert(0, (T("Type"), "series_id"))
        # Multiselect widget
        finsert(1, OptionsFilter("series_id",
                                 label = T("Filter by Type"),
                                 # We want translations
                                 #represent = "%(name)s",
                                 hidden = hidden,
                                 ))

    elif len_series > 1:
        notify_fields.insert(0, (T("Type"), "series_id"))
        # Checkboxes
        finsert(1, OptionsFilter("series_id",
                                 label = T("Filter by Type"),
                                 # We want translations
                                 #represent = "%(name)s",
                                 cols = 2,
                                 hidden = hidden,
                                 ))
    else:
        # No Widget or notify_field
        pass

    nappend = notify_fields.append
    if org_field:
        nappend((T("Organization"), org_field))
    if org_group_field:
        if isinstance(group_label, bool):
           group_label = T("Organization Group")
        nappend((T(group_label), org_group_field))
    if contact_field:
        nappend((T("Contact"), contact_field))
    nappend((T("Description"), "body"))

    # @todo: allow configuration (?)
    filter_formstyle = settings.get_ui_formstyle()
    s3db.configure("cms_post",
                   # We could use a custom Advanced widget
                   #filter_advanced = False,
                   filter_formstyle = filter_formstyle,
                   # No Submit button (done automatically)
                   #filter_submit = (T("SEARCH"), "btn btn-primary"),
                   filter_widgets = filter_widgets,
                   # Default anyway now:
                   #list_layout = s3db.cms_post_list_layout,
                   # Create form comes via AJAX in a Modal
                   #insertable = False,
                   notify_fields = notify_fields,
                   notify_template = "notify_post",
                   )

    s3.dl_pagelength = 6  # 5 forces an AJAX call

    def prep(r):
        if r.interactive or r.representation == "aadata":
            s3db.cms_configure_newsfeed_post_fields()

        if r.interactive:
            if len_series > 1:
                refresh = get_vars.get("refresh", None)
                if refresh == "datalist":
                    # We must be coming from the News Feed page so can change the type on-the-fly
                    field = table.series_id
                    field.label = T("Type")
                    field.readable = field.writable = True
            else:
                field = table.series_id
                row = db(stable.deleted == False).select(stable.id,
                                                         limitby=(0, 1)
                                                         ).first()
                try:
                    field.default = row.id
                except:
                    # Prepop not done: expose field to show error
                    field.label = T("Type")
                    field.readable = field.writable = True
                else:
                    field.readable = field.writable = False

            if r.method == "read":
                # Restore the label for the Location
                table.location_id.label = T("Location")
            elif r.method == "create":
                pass
                # @ToDo: deployment_setting
                #if not auth.s3_has_role("ADMIN"):
                #    represent = S3Represent(lookup="cms_series",
                #                            translate=settings.get_L10n_translate_cms_series())
                #    field.requires = IS_ONE_OF(db,
                #                               "cms_series.id",
                #                               represent,
                #                               not_filterby="name",
                #                               not_filter_opts = ("Alert",),
                #                               )

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
            from core import s3_comments_widget
            field.widget = s3_comments_widget
            #table.comments.readable = table.comments.writable = False

            #if request.controller == "default":
            #    # Don't override card layout for News Feed/Homepage
            #    return True

            from core import CustomForm, InlineComponent

            # Filter from a Profile page?
            # If so, then default the fields we know
            location_id = get_vars.get("~.(location)", None)
            if location_id:
                table.location_id.default = location_id
            event_id = get_vars.get("~.(event)", None)
            if event_id:
                def create_onaccept(form):
                    table = current.s3db.event_post
                    table.insert(event_id=event_id,
                                 post_id=form.vars.id)

                s3db.configure("cms_post",
                               create_onaccept = create_onaccept,
                               )

            crud_fields = ["date",
                           "series_id",
                           ]
            cappend = crud_fields.append
            if settings.get_cms_show_titles():
                cappend("title")
            crud_fields.extend(("body",
                                "location_id",
                                ))
            if not event_id and show_events:
                cappend(InlineComponent("event_post",
                                        # @ToDo: deployment_setting (use same one used to activate?)
                                        #label = T("Disaster(s)"),
                                        label = T("Disaster"),
                                        multiple = False,
                                        fields = [("", "event_id")],
                                        orderby = "event_id$name",
                                        ))
            if org_field == "post_organisation.organisation_id":
                cappend(InlineComponent("post_organisation",
                                        label = T("Organization"),
                                        fields = [("", "organisation_id")],
                                        # @ToDo: deployment_setting
                                        multiple = False,
                                        ))
            if org_group_field == "post_organisation_group.group_id":
                cappend(InlineComponent("post_organisation_group",
                                        label = T(group_label),
                                        fields = [("", "group_id")],
                                        # @ToDo: deployment_setting
                                        multiple = False,
                                        ))
            if contact_field == "person_id":
                cappend("person_id")

            if settings.get_cms_show_attachments():
                cappend(InlineComponent("document",
                                        name = "file",
                                        label = T("Files"),
                                        fields = [("", "file"),
                                                  #"comments",
                                                  ],
                                        ))

            if settings.get_cms_show_links():
                cappend(InlineComponent("document",
                                        name = "url",
                                        label = T("Links"),
                                        fields = [("", "url"),
                                                #"comments",
                                                ],
                                        ))
            crud_form = CustomForm(*crud_fields)

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
                           )

        elif r.representation in ("xlsx", "xls"):
            table.body.represent = None
            table.created_by.represent = s3db.auth_UserRepresent(show_email = False,
                                                                 show_link = False)
            #table.created_on.represent = datetime_represent
            utable = auth.settings.table_user
            utable.organisation_id.represent = s3db.org_organisation_represent

            list_fields = [(T("Date"), "date"),
                           #(T("Disaster"), "event_post.event_id"),
                           (T("Type"), "series_id"),
                           (T("Details"), "body"),
                           ]
            lappend = list_fields.append
            # Which levels of Hierarchy are we using?
            gis = current.gis
            levels = gis.get_relevant_hierarchy_levels()
            hierarchy = gis.get_location_hierarchy()
            for level in levels:
                lappend((hierarchy[level], "location_id$%s" % level))
            if contact_field:
                lappend((T("Contact"), contact_field))
            if org_field:
                lappend((T("Organization"), org_field))
            if org_group_field:
                lappend((T(group_label), org_group_field))
            s3db.configure("cms_post",
                           list_fields = list_fields,
                           )

        elif r.representation == "plain":
            # Map Popups
            table.location_id.represent = s3db.gis_LocationRepresent(sep=" | ")
            table.created_by.represent = s3db.auth_UserRepresent(show_email = False,
                                                                 show_link = False)
            # Used by default popups
            series = table.series_id.represent(r.record.series_id)
            s3.crud_strings["cms_post"].title_display = "%(series)s Details" % {"series": series}
            s3db.configure("cms_post",
                           popup_url = "",
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
            r.table.age = Field.Method("age", cms_post_age)

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if r.method == "datalist" and r.representation != "dl":
                # Hide side menu
                current.menu.options = None
                response.view = s3base.BasicCRUD._view(r, "cms/newsfeed.html")

        return output
    s3.postp = postp

    return crud_controller("cms", "post")

# =============================================================================
# Comments
#
def comment():
    """ RESTful CRUD controller """

    return crud_controller()

# -----------------------------------------------------------------------------
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

    author = T("Anonymous")
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
            author = A(username, _href=url, _target="top")
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
    from gluon.tools import Crud
    crud = Crud()
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
                        _id = "comment-title"),
                     form,
                     _id = "comment-form",
                     _class = "clear",
                     ),
                 SCRIPT(script))

    return XML(output)

# =============================================================================
# Announcements
#
def announcement():
    """ Homepage Announcements - CRUD Controller """

    # TODO restrict to ADMINs

    return crud_controller()

# =============================================================================
# Newsletters
#
def configure_newsletter_attachments(file_icons=False):
    """
        Configure newsletter attachments (doc_document)

        Args:
            file_icons: show files as icon+size rather than filename
    """

    dtable = s3db.doc_document

    # Document Title is required
    field = dtable.name
    requires = field.requires
    field.requires = IS_NOT_EMPTY()
    if requires:
        field.requires = [field.requires, requires]

    # Hide URL and Date
    field = dtable.url
    field.readable = field.writable = False
    field = dtable.date
    field.readable = field.writable = False

    if file_icons:
        # Represent files as icon+size
        from core import represent_file
        field = dtable.file
        field.represent = represent_file()

    # Reduced list fields
    s3db.configure("doc_document",
                   list_fields = ["name", "file", "comments"],
                   )

# -----------------------------------------------------------------------------
def newsletter():
    """ Newsletters, Author Perspective """

    # Configure newsletter methods
    update_newsletter = s3db.cms_UpdateNewsletter
    for method in ("update_recipients", "remove_recipients", "send"):
        s3db.set_method("cms_newsletter",
                        method = method,
                        action = update_newsletter,
                        )

    def prep(r):

        s3.crud_strings["cms_newsletter"]["title_list"] = T("Newsletters")

        configure_newsletter_attachments()

        resource = r.resource
        table = resource.table

        # Filter by accessible sender
        otable = s3db.org_organisation
        query = auth.s3_accessible_query("update", otable) & \
                (otable.deleted == False)
        permitted = db(query)._select(otable.id)
        resource.add_filter(table.organisation_id.belongs(permitted))

        # Limit selection of sender, too
        field = table.organisation_id
        field.requires = IS_ONE_OF(db(query), "org_organisation.id",
                                   field.represent,
                                   )

        lookup = resource.get_config("lookup_recipients")

        record = r.record
        component_name = r.component_name
        if not r.component:
            if record:
                field = table.message
                field.represent = lambda v, row=None: \
                                  DIV(v, _class="newsletter-text") if v else "-"
            if lookup:
                # Add distribution list to CRUD form
                types = settings.get_cms_newsletter_recipient_types()
                from core import CustomForm, InlineComponent, InlineLink
                crud_form = CustomForm(
                                "organisation_id",
                                "subject",
                                "message",
                                InlineComponent(
                                    "document",
                                    name = "file",
                                    label = T("Attachments"),
                                    fields = ["name", "file", "comments"],
                                    filterby = {"field": "file",
                                                "options": "",
                                                "invert": True,
                                                },
                                    ),
                                "contact_name",
                                "contact_email",
                                #"contact_phone",
                                InlineLink(
                                    "distribution",
                                    label = T("Distribution##list"),
                                    field = "saved_filter_id",
                                    filterby = {
                                        "pe_id": auth.user.pe_id if auth.user else None,
                                        "resource": types,
                                        },
                                    comment = T("Create saved filters for possible recipients to be able to select them here"),
                                    ),
                                "comments",
                                )
                resource.configure(crud_form = crud_form)

        elif component_name == "newsletter_recipient":

            if record.status == "NEW":
                # Unsent newsletter, so allow deletion of recipients
                r.component.configure(deletable = True)

        return True
    s3.prep = prep

    return crud_controller(rheader=s3db.cms_rheader)

# -----------------------------------------------------------------------------
def read_newsletter():
    """ Newsletters, Reader Perspective """

    s3.hide_last_update = True

    formkeys_mark = "_formkey[newsletter/mark]"

    def prep(r):

        s3.crud_strings["cms_newsletter"]["title_list"] = T("Newsletter Inbox")

        configure_newsletter_attachments(file_icons=True)

        from core import accessible_pe_query, \
                         DateFilter, \
                         OptionsFilter, \
                         CustomForm, \
                         InlineComponent, \
                         TextFilter

        resource = r.resource
        table = resource.table

        # Filter by accessible recipient
        rtable = s3db.cms_newsletter_recipient
        types = settings.get_cms_newsletter_recipient_types()
        query = accessible_pe_query(table = rtable,
                                    instance_types = types,
                                    c = "cms",
                                    f = "newsletter_recipient",
                                    )
        if auth.user:
            query |= (rtable.pe_id == auth.user.pe_id)
        resource.add_filter(query, "newsletter_recipient")

        # Filter by SENT-status
        query = FS("status") == "SENT"
        resource.add_filter(query)

        component = r.component
        if not component:
            if r.record:
                # If a newsletter is opened interactively, mark it as read
                if r.method in ("read", "update", None) and r.interactive:
                    s3db.cms_mark_newsletter(r.id)

                table = resource.table

                field = table.message
                field.represent = lambda v, row=None: \
                                  DIV(v, _class="newsletter-text") if v else "-"

                # Compact representation of contact information
                from core import s3_fieldmethod, VirtualFormField
                details = s3db.cms_NewsletterDetails
                table.contact = s3_fieldmethod("contact",
                                               details.contact,
                                               represent = details.contact_represent,
                                               )
                contact = VirtualFormField("contact", label=T("Contact"))

            elif r.method == "mark":
                # Mark all unread newsletters as read
                key = r.post_vars.get("_formkey")
                keys = session.get(formkeys_mark)
                if keys and key in keys:
                    keys.remove(key)
                    unread = s3db.cms_unread_newsletters(count=False, cached=False)
                    s3db.cms_mark_newsletter(unread)
                    redirect(r.url(method=""))
                else:
                    r.error(400, "invalid request", next=r.url(method=""))

            else:
                contact = None

            # CRUD Form
            crud_form = CustomForm(
                            "message",
                            InlineComponent("document",
                                            name = "file",
                                            label = T("Attachments"),
                                            fields = ["name", "file", "comments"],
                                            filterby = {"field": "file",
                                                        "options": "",
                                                        "invert": True,
                                                        },
                                            ),
                            contact,
                            )

            # Filter Widgets
            filter_widgets = [TextFilter(["subject",
                                          "message",
                                          "comments",
                                          "organisation_id$name",
                                          ],
                                         label = T("Search") ,
                                         ),
                              DateFilter("date_sent", hidden=True),
                              ]

            # List Fields
            list_fields = ["organisation_id",
                           "subject",
                           #"message",
                           "date_sent",
                           (T("Status"), "read_status"),
                           ]

            resource.configure(crud_form = crud_form,
                               filter_widgets = filter_widgets,
                               list_fields = list_fields,
                               insertable = False,
                               editable = False,
                               deletable = False,
                               )

        else:
            # All components are read-only, too
            component.configure(insertable = False,
                                editable = False,
                                deletable = False,
                                )
        return True
    s3.prep = prep

    def postp(r, output):

        if not r.record and not r.method and isinstance(output, dict):

            if "buttons" in output:
                buttons = output["buttons"]
            else:
                buttons = output["buttons"] = {}
            add = buttons.get("add_btn")

            if s3db.cms_unread_newsletters():
                # Add button to mark all unread newsletters as read
                import uuid
                key = str(uuid.uuid4())
                keys = session.get(formkeys_mark)
                session[formkeys_mark] = [key] if not keys else [key] + keys[:9]

                mark = FORM(BUTTON(T("Mark all as read"),
                                   _type="submit",
                                   _class="action-btn",
                                   ),
                            _action = r.url(method="mark"),
                            hidden = {"_formkey": key},
                            )
                buttons["add_btn"] = TAG[""](mark, add) if add else mark

        return output
    s3.postp = postp

    return crud_controller("cms", "newsletter", rheader=s3db.cms_rheader)

# END =========================================================================
