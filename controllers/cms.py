# -*- coding: utf-8 -*-

"""
    CMS

    Simple Content Management System
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

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
            response.view = "cms/blog.html"
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
                vars = request.get_vars

                # Filter from a Profile page?"
                series = vars.get("~.series_id$name", None)
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
                location_id = vars.get("(location)", None)
                if location_id:
                    field = table.location_id
                    field.default = location_id
                    field.readable = field.writable = False

                page = vars.get("page", None)
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

                _module = vars.get("module", None)
                if _module:
                    table.avatar.readable = table.avatar.writable = False
                    table.location_id.readable = table.location_id.writable = False
                    table.date.readable = table.date.writable = False
                    table.expired.readable = table.expired.writable = False
                    resource = request.get_vars.get("resource", None)
                    if resource:
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

                layer_id = vars.get("layer_id", None)
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
            response.view = "cms/page.html"
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
