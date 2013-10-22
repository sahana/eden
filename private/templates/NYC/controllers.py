# -*- coding: utf-8 -*-

from os import path

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.html import *
from gluon.storage import Storage

from s3.s3crud import S3CRUD
from s3.s3filter import S3DateFilter, S3LocationFilter, S3OptionsFilter, S3TextFilter, S3FilterForm
from s3.s3resource import S3FieldSelector
from s3.s3utils import s3_avatar_represent, S3CustomController

THEME = "NYC"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        request = current.request
        s3 = current.response.s3

        # Check logged in and permissions
        auth = current.auth
        roles = current.session.s3.roles
        system_roles = auth.get_system_roles()
        AUTHENTICATED = system_roles.AUTHENTICATED

        # Login/Registration forms
        self_registration = current.deployment_settings.get_security_self_registration()
        registered = False
        login_form = None
        login_div = None
        register_form = None
        register_div = None
        if AUTHENTICATED not in roles:
            # This user isn't yet logged-in
            T = current.T
            if request.cookies.has_key("registered"):
                # This browser has logged-in before
                registered = True

            if self_registration:
                # Provide a Registration box on front page
                register_form = auth.s3_registration_form()
                register_div = DIV(H3(T("Register")),
                                   P(XML(T("If you would like to help, then please %(sign_up_now)s") % \
                                            dict(sign_up_now=B(T("sign-up now"))))))

                if request.env.request_method == "POST":
                    post_script = \
'''$('#register_form').removeClass('hide')
$('#login_form').addClass('hide')'''
                else:
                    post_script = ""
                register_script = \
'''$('#register-btn').attr('href','#register')
$('#login-btn').attr('href','#login')
%s
$('#register-btn').click(function(){
 $('#register_form').removeClass('hide')
 $('#login_form').addClass('hide')
})
$('#login-btn').click(function(){
 $('#register_form').addClass('hide')
 $('#login_form').removeClass('hide')
})''' % post_script
                s3.jquery_ready.append(register_script)

            # Provide a login box on front page
            request.args = ["login"]
            auth.messages.submit_button = T("Login")
            login_form = auth()
            login_div = DIV(H3(T("Login")),
                            P(XML(T("Registered users can %(login)s to access the system") % \
                                  dict(login=B(T("login"))))))
        output["self_registration"] = self_registration
        output["registered"] = registered
        output["login_div"] = login_div
        output["login_form"] = login_form
        output["register_div"] = register_div
        output["register_form"] = register_form

        # Latest 4 Events and Requests
        s3db = current.s3db
        layout = s3.render_posts
        listid = "news_datalist"
        limit = 4
        list_fields = ["series_id",
                       "location_id",
                       "date",
                       "body",
                       "created_by",
                       "created_by$organisation_id",
                       "document.file",
                       "event_post.event_id",
                       ]

        resource = s3db.resource("cms_post")
        resource.add_filter(S3FieldSelector("series_id$name") == "Event")
        # Only show Future Events
        resource.add_filter(resource.table.date >= request.now)
        # Order with next Event first
        orderby = "date"
        output["events"] = latest_records(resource, layout, listid, limit, list_fields, orderby)

        resource = s3db.resource("cms_post")
        resource.add_filter(S3FieldSelector("series_id$name") == "Request")
        # Order with most recent Request first
        orderby = "date desc"
        output["requests"] = latest_records(resource, layout, listid, limit, list_fields, orderby)

        self._view(THEME, "index.html")
        return output

# =============================================================================
class datalist():
    """ Alternate URL for News Feed page """

    def __call__(self):

        return _newsfeed()

# =============================================================================
class datalist_dl_post():
    """ AJAX URL for CMS Posts (for News Feed page) """

    def __call__(self):

        return _newsfeed()

# =============================================================================
class datalist_dl_filter():
    """ AJAX URL for CMS Posts Filter Form (for News Feed page) """

    def __call__(self):

        return _newsfeed()

# =============================================================================
class login():
    """ Custom Login page """

    def __call__(self):

        return _login()

# =============================================================================
class newsfeed():
    """ Newsfeed page """

    def __call__(self):

        return _newsfeed()

# =============================================================================
class validate():
    """ Alternate URL for News Feed page """

    def __call__(self):

        return _newsfeed()

# =============================================================================
def _newsfeed():
    """
        Custom Page
        - Filterable DataList of CMS Posts & a DataList of Events
    """

    #if not current.auth.is_logged_in():
    #    current.auth.permission.fail()

    T = current.T
    s3db = current.s3db
    request = current.request
    response = current.response
    s3 = response.s3

    # Ensure that filtered views translate into options which update the Widget
    if "~.series_id$name" in request.get_vars:
        series_name = request.vars["~.series_id$name"]
        table = s3db.cms_series
        series = current.db(table.name == series_name).select(table.id,
                                                              limitby=(0, 1)).first()
        if series:
            series_id = str(series.id)
            request.get_vars.pop("~.series_id$name")
            request.get_vars["~.series_id__belongs"] = series_id

    current.deployment_settings.ui.customize_cms_post()

    list_layout = s3.render_posts

    filter_widgets = [S3TextFilter(["body"],
                                   label="",
                                   _class="filter-search",
                                   #_placeholder=T("Search").upper(),
                                   ),
                      S3OptionsFilter("series_id",
                                      label=T("Filter by Type"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      hidden=True,
                                      ),
                      S3LocationFilter("location_id",
                                       label=T("Filter by Location"),
                                       levels=["L1", "L2", "L3"],
                                       widget="multiselect",
                                       hidden=True,
                                       ),
                      S3OptionsFilter("created_by$organisation_id",
                                      label=T("Filter by Organization"),
                                      # Can't use this for integers, use field.represent instead
                                      #represent="%(name)s",
                                      widget="multiselect",
                                      hidden=True,
                                      ),
                      S3DateFilter("created_on",
                                   label=T("Filter by Date"),
                                   hide_time=True,
                                   hidden=True,
                                   ),
                      ]

    s3db.configure("cms_post",
                   # We use a custom Advanced widget
                   filter_advanced = False,
                   filter_formstyle = filter_formstyle,
                   filter_submit = (T("SEARCH"), "btn btn-primary"),
                   filter_widgets = filter_widgets,
                   list_layout = list_layout,
                   # Create form comes via AJAX in a Modal
                   insertable = False,
                   notify_fields = [(T("Type"), "series_id"),
                                    (T("Date"), "date"),
                                    (T("Location"), "location_id"),
                                    (T("Description"), "body"),
                                   ],
                   notify_template = "notify_post",
                   )

    s3.dl_pagelength = 6  # 5 forces an AJAX call

    if "datalist_dl_post" in request.args:
        # DataList pagination or Ajax-deletion request
        request.args = ["datalist_f"]
        ajax = "list"
    elif "datalist_dl_filter" in request.args:
        # FilterForm options update request
        request.args = ["filter"]
        ajax = "filter"
    elif "validate.json" in request.args:
        # Inline component validation request
        request.args = []
        ajax = True
    elif current.auth.permission.format == "msg":
        # Subscription lookup request
        request.args = []
        ajax = True
    else:
        # Default
        request.args = ["datalist_f"]
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
        # Set Title & View after REST Controller, in order to override
        output["title"] = T("News Feed")
        view = path.join(request.folder, "private", "templates",
                         THEME, "views", "newsfeed.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        scripts = []
        sappend = scripts.append
        # Style the Search TextFilter widget
        sappend('''$('#post-cms_post_body-text-filter__row').addClass('input-append').append('<span class="add-on"><i class="icon-search"></i></span>')''')
        # Button to toggle Advanced Form
        sappend('''$('#list-filter').append('<a class="accordion-toggle"><i class="icon-reorder"></i> %s</a>')''' % T("Advanced Search"))
        # Toggle doesn't work directly when removing 'hide' & requires a 2nd click to open without this
        sappend('''$('.accordion-toggle').click(function(){var a=$('.advanced');if(a.hasClass('hide')){a.removeClass('hide').show()}else{a.toggle()}})''')
        s3.jquery_ready.append('''\n'''.join(scripts))
        
        # Latest 5 Disasters
        # resource = s3db.resource("event_event")
        # layout = render_events
        # listid = "event_datalist"
        # limit = 5
        # orderby = "zero_hour desc"
        # list_fields = ["name",
                       # "event_type_id$name",
                       # "zero_hour",
                       # "closed",
                       # ]
        # output["disasters"] = latest_records(resource, layout, listid, limit, list_fields, orderby)

    return output

# =============================================================================
def latest_records(resource, layout, listid, limit, list_fields, orderby):
    """
        Display a dataList of the latest records for a resource
    """

    #orderby = resource.table[orderby]
    datalist, numrows, ids = resource.datalist(fields=list_fields,
                                               start=None,
                                               limit=limit,
                                               listid=listid,
                                               orderby=orderby,
                                               layout=layout)
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

    return data

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
def render_events(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for 'Disasters' on the News Feed page

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "event_event.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    name = record["event_event.name"]
    date = record["event_event.zero_hour"]
    closed = raw["event_event.closed"]
    event_type = record["event_event_type.name"]

    if closed:
        edit_bar = DIV()
    else:
        item_class = "%s disaster" % item_class

        permit = current.auth.s3_has_permission
        table = resource.table
        if permit("update", table, record_id=record_id):
            edit_btn = A(I(" ", _class="icon icon-edit"),
                         _href=URL(c="event", f="event",
                                   args=[record_id, "update.popup"],
                                   vars={"refresh": listid,
                                         "record": record_id}),
                         _class="s3_modal",
                         _title=current.response.s3.crud_strings.event_event.title_update,
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

    # Render the item
    item = DIV(DIV(A(IMG(_class="media-object",
                         _src=URL(c="static",
                                  f="img",
                                  args=["event", "%s.png" % event_type]),
                         ),
                     _class="pull-left",
                     _href="#",
                     ),
  		           edit_bar,
                   DIV(A(H5(name,
                            _class="media-heading"),
                         SPAN(date,
                              _class="date-title",
                              ),
                         _href=URL(c="event", f="event",
                                   args=[record_id, "profile"]),
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
def render_cms_events(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for 'Events' on the Home page

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    T = current.T
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
    series = "Event"
    date = record["cms_post.date"]
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
                                 _style="width:50px;padding:5px;padding-top:0;")
    db = current.db
    ltable = current.s3db.pr_person_user
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

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = db.cms_post
    if permit("update", table, record_id=record_id):
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="cms", f="post",
                               args=[record_id, "update.popup"],
                               vars={"refresh": listid,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=T("Edit Event"),
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

    # Dropdown of available documents
    documents = raw["doc_document.file"]
    if documents:
        if not isinstance(documents, list):
            documents = [documents]
        doc_list = UL(_class="dropdown-menu",
                      _role="menu",
                      )
        retrieve = db.doc_document.file.retrieve
        for doc in documents:
            try:
                doc_name = retrieve(doc)[0]
            except IOError:
                doc_name = current.messages["NONE"]
            doc_url = URL(c="default", f="download",
                          args=[doc])
            doc_item = LI(A(I(_class="icon-file"),
                            " ",
                            doc_name,
                            _href=doc_url,
                            ),
                          _role="menuitem",
                          )
            doc_list.append(doc_item)
        docs = DIV(A(I(_class="icon-paper-clip"),
                     SPAN(_class="caret"),
                     _class="btn dropdown-toggle",
                     _href="#",
                     **{"_data-toggle": "dropdown"}
                     ),
                   doc_list,
                   _class="btn-group attachments dropdown pull-right",
                   )
    else:
        docs = ""

    # Render the item
    item = DIV(DIV(I(SPAN(" %s" % T("Event"),
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
                               docs,
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

# =============================================================================
class subscriptions(S3CustomController):
    """ Custom page to manage subscriptions """

    # -------------------------------------------------------------------------
    def __call__(self):
        """ Main entry point, configuration """

        T = current.T

        # Must be logged in
        auth = current.auth
        if not auth.s3_logged_in():
            auth.permission.fail()
            
        # Available resources
        resources = [dict(resource="cms_post",
                          url="default/index/newsfeed",
                          label=T("Updates")),
                    ]

        # Filter widgets
        # @note: subscription manager has no resource context, so
        #        must configure fixed options or lookup resources
        #        for filter widgets which need it.
        filters = [S3OptionsFilter("series_id",
                                   label=T("Subscribe to"),
                                   represent="%(name)s",
                                   widget="groupedopts",
                                   cols=2,
                                   resource="cms_post",
                                   _name="type-filter"),
                   S3LocationFilter("location_id",
                                    label=T("Location(s)"),
                                    levels=["L1"],
                                    widget="multiselect",
                                    cols=3,
                                    resource="cms_post",
                                    _name="location-filter"),
                   #S3OptionsFilter("created_by$organisation_id",
                                   #label=T("Filter by Organization"),
                                   #represent=s3db.org_organisation_represent,
                                   ##represent="%(name)s",
                                   #widget="multiselect",
                                   #cols=3,
                                   #resource="cms_post",
                                   #_name="organisation-filter"),
                   ]

        # Title and view
        title = T("Notification Settings")
        self._view(THEME, "subscriptions.html")

        # Form
        form = self._manage_subscriptions(resources, filters)
        
        return dict(title=title, form=form)
        
    # -------------------------------------------------------------------------
    def _manage_subscriptions(self, resources, filters):
        """
            Custom form to manage subscriptions

            @param resources: available resources config
            @param filters: filter widgets
        """

        from gluon.sqlhtml import SQLFORM
        from gluon.validators import IS_IN_SET
        from s3.s3widgets import S3GroupedOptionsWidget

        # L10n
        T = current.T
        labels = Storage(
            RESOURCES = T("Subscribe To"),
            NOTIFY_ON = T("Notify On"),
            FREQUENCY = T("Frequency"),
            NOTIFY_BY = T("Notify By"),
            MORE = T("More Options"),
            LESS = T("Less Options"),
        )
        messages = Storage(
            ERROR = T("Error: could not update notification settings"),
            SUCCESS = T("Notification settings updated"),
        )
        
        # Get current subscription settings resp. form defaults
        subscription = self._get_subscription()

        # Formstyle bootstrap
        formstyle = SQLFORM.formstyles.bootstrap

        # Initialize form
        form = FORM(_id="subscription-form",
                    hidden={"subscription-filters": ""})

        # Deactivated: resource selector
        #options = []
        #selected_resources = set()
        #subscribed = subscription["resources"]
        #for idx, rconfig in enumerate(resources):
            #options.append((idx, rconfig["label"]))
            #if subscribed:
                #for s in subscribed:
                    #if s.resource == rconfig["resource"] and \
                       #s.url == rconfig["url"]:
                        #selected_resources.add(idx)

        #dummy = Storage(name="resources", requires = IS_IN_SET(options))
        #selector = S3GroupedOptionsWidget(cols=2)
        #row = ("resource_selector__row",
               #"%s:" % labels.RESOURCES,
               #selector(dummy,
                        #list(selected_resources),
                        #_id="resource_selector"),
               #"")
        #fieldset = formstyle(form, [row])
        #form.append(fieldset)

        # Filters
        filter_form = S3FilterForm(filters, clear=False)
        fieldset = FIELDSET(filter_form.fields(None,
                                               subscription["get_vars"]),
                            _id="subscription-filter-form")
        form.append(fieldset)

        # Notification options
        rows = []
        stable = current.s3db.pr_subscription

        selector = S3GroupedOptionsWidget(cols=1)
        rows.append(("trigger_selector__row",
                     "%s:" % labels.NOTIFY_ON,
                     selector(stable.notify_on,
                              subscription["notify_on"],
                              _id="trigger_selector"),
                     ""))

        switch = S3GroupedOptionsWidget(cols=1, multiple=False, sort=False)
        rows.append(("frequency_selector__row",
                     "%s:" % labels.FREQUENCY,
                     switch(stable.frequency,
                            subscription["frequency"],
                            _id="frequency_selector"),
                     ""))

        # Deactivated: method selector
        #rows.append(("method_selector__row",
                     #"%s:" % labels.NOTIFY_BY,
                     #selector(stable.method,
                              #subscription["method"],
                              #_id="method_selector"),
                     #""))

        fieldset = formstyle(form, rows)
        fieldset.insert(0,
                        DIV(SPAN([I(_class="icon-reorder"), labels.MORE],
                                 _class="toggle-text",
                                 _style="display:none"),
                            SPAN([I(_class="icon-reorder"), labels.LESS],
                                 _class="toggle-text"),
                            _id="notification-options",
                            _class="control-group"))
        form.append(fieldset)

        # Submit button
        row = ("submit__row", "",
               INPUT(_type="submit", _value="Update Settings"), "")

        fieldset = formstyle(form, [row])
        form.append(fieldset)

        # Script (to extract filters on submit and toggle options visibility)
        script = """
$('#notification-options').click(function() {
  $(this).siblings().toggle();
  $(this).children().toggle();
});
$('#notification-options').siblings().toggle();
$('#notification-options').children().toggle();
$('#subscription-form').submit(function() {
  $('input[name="subscription-filters"]')
  .val(JSON.stringify(S3.search.getCurrentFilters($(this))));
});
"""
        response = current.response
        response.s3.jquery_ready.append(script)

        # Accept form
        if form.accepts(current.request.post_vars,
                        current.session,
                        formname="subscription",
                        keepvalues=True):

            formvars = form.vars

            listify = lambda x: None if not x else x if type(x) is list else [x]

            # Fixed resource selection:
            subscription["subscribe"] = [resources[0]]
            # Alternatively, with resource selector:
            #subscribe = listify(formvars.resources)
            #if subscribe:
                #subscription["subscribe"] = \
                        #[r for idx, r in enumerate(resources)
                           #if str(idx) in subscribe]

            subscription["filters"] = form.request_vars \
                                      .get("subscription-filters", None)

            subscription["notify_on"] = listify(formvars.notify_on)
            subscription["frequency"] = formvars.frequency
            # Fixed method:
            subscription["method"] = ["EMAIL"]
            # Alternatively, with method selector:
            #subscription["method"] = listify(formvars.method)

            success = self._update_subscription(subscription)

            if success:
                response.confirmation = messages.SUCCESS
            else:
                response.error = messages.ERROR

        return form

    # -------------------------------------------------------------------------
    def _get_subscription(self):
        """ Get current subscription settings """

        db = current.db
        s3db = current.s3db
        
        pe_id = current.auth.user.pe_id

        stable = s3db.pr_subscription
        ftable = s3db.pr_filter
        query = (stable.pe_id == pe_id) & \
                (stable.deleted != True)
        left = ftable.on(ftable.id == stable.filter_id)
        row = db(query).select(stable.id,
                               stable.notify_on,
                               stable.frequency,
                               #stable.method,
                               ftable.id,
                               ftable.query,
                               left=left,
                               limitby=(0, 1)).first()

        output = {"pe_id": pe_id}
                            
        get_vars = {}
        if row:
            # Existing settings
            s = getattr(row, "pr_subscription")
            f = getattr(row, "pr_filter")

            rtable = s3db.pr_subscription_resource
            query = (rtable.subscription_id == s.id) & \
                    (rtable.deleted != True)
            rows = db(query).select(rtable.id,
                                    rtable.resource,
                                    rtable.url,
                                    rtable.last_check_time,
                                    rtable.next_check_time)

            if f.query:
                filters = json.loads(f.query)
                for k, v in filters:
                    if v is None:
                        continue
                    if k in get_vars:
                        if type(get_vars[k]) is list:
                            get_vars[k].append(v)
                        else:
                            get_vars[k] = [get_vars[k], v]
                    else:
                        get_vars[k] = v

            output.update({"id": s.id,
                           "filter_id": f.id,
                           "get_vars" : get_vars,
                           "resources": rows,
                           "notify_on": s.notify_on,
                           "frequency": s.frequency,
                           "method": ["EMAIL"] #s.method,
                           })
            
        else:
            # Form defaults
            output.update({"id": None,
                           "filter_id": None,
                           "get_vars" : get_vars,
                           "resources": None,
                           "notify_on": stable.notify_on.default,
                           "frequency": stable.frequency.default,
                           "method": ["EMAIL"] #stable.method.default
                           })

        return output

    # -------------------------------------------------------------------------
    def _update_subscription(self, subscription):
        """ Update subscription settings """

        db = current.db
        s3db = current.s3db

        pe_id = subscription["pe_id"]

        # Save filters
        filter_id = subscription["filter_id"]
        filters = subscription.get("filters")
        if filters:
            ftable = s3db.pr_filter
            
            if not filter_id:
                success = ftable.insert(pe_id=pe_id, query=filters)
                filter_id = success
            else:
                success = db(ftable.id == filter_id).update(query=filters)
            if not success:
                return None

        # Save subscription settings
        stable = s3db.pr_subscription
        subscription_id = subscription["id"]
        frequency = subscription["frequency"]
        if not subscription_id:
            success = stable.insert(pe_id=pe_id,
                                    filter_id=filter_id,
                                    notify_on=subscription["notify_on"],
                                    frequency=frequency,
                                    method=subscription["method"])
            subscription_id = success
        else:
            success = db(stable.id == subscription_id).update(
                            pe_id=pe_id,
                            filter_id=filter_id,
                            notify_on=subscription["notify_on"],
                            frequency=frequency,
                            method=subscription["method"])
        if not success:
            return None

        # Save subscriptions
        rtable = s3db.pr_subscription_resource
        subscribe = subscription.get("subscribe")
        if subscribe:
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            resources = subscription["resources"]

            subscribed = {}
            timestamps = {}
            if resources:
                for r in resources:
                    subscribed[(r.resource, r.url)] = r.id
                    timestamps[r.id] = (r.last_check_time,
                                        r.next_check_time)
                                    
            intervals = s3db.pr_subscription_check_intervals
            interval = timedelta(minutes=intervals.get(frequency, 0))
                
            keep = set()
            fk = '''{"subscription_id": %s}''' % subscription_id
            for new in subscribe:
                resource, url = new["resource"], new["url"]
                if (resource, url) not in subscribed:
                    # Restore subscription if previously unsubscribed, else
                    # insert new record
                    unsubscribed = {"deleted": True,
                                    "deleted_fk": fk,
                                    "resource": resource,
                                    "url": url}
                    rtable.update_or_insert(_key=unsubscribed,
                                            deleted=False,
                                            deleted_fk=None,
                                            subscription_id=subscription_id,
                                            resource=resource,
                                            url=url,
                                            last_check_time=now,
                                            next_check_time=None)
                else:
                    # Keep it
                    record_id = subscribed[(resource, url)]
                    last_check_time, next_check_time = timestamps[record_id]
                    data = {}
                    if not last_check_time:
                        # Someone has tampered with the timestamps, so
                        # we need to reset them and start over
                        last_check_time = now
                        data["last_check_time"] = last_check_time
                    due = last_check_time + interval
                    if next_check_time != due:
                        # Time interval has changed
                        data["next_check_time"] = due
                    if data:
                        db(rtable.id == record_id).update(**data)
                    keep.add(record_id)
                    
            # Unsubscribe all others
            unsubscribe = set(subscribed.values()) - keep
            db(rtable.id.belongs(unsubscribe)).update(deleted=True,
                                                      deleted_fk=fk,
                                                      subscription_id=None)

        # Update subscription
        subscription["id"] = subscription_id
        subscription["filter_id"] = filter_id
        return subscription
        
# =============================================================================
class contact():
    """ Contact Form """

    def __call__(self):

        request = current.request
        response = current.response

        view = path.join(request.folder, "private", "templates",
                         THEME, "views", "contact.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        if request.env.request_method == "POST":
            # Processs Form
            vars = request.post_vars
            result = current.msg.send_email(
                    to=current.deployment_settings.get_mail_approver(),
                    subject=vars.subject,
                    message=vars.message,
                    reply_to=vars.address,
                )
            if result:
                response.confirmation = "Thankyou for your message - we'll be in touch shortly"

        #T = current.T

        form = DIV(
                H1("Contact Us"),
                P("You can leave a message using the contact form below."),
                FORM(TABLE(
                        TR(LABEL("Your name:",
                              SPAN(" *", _class="req"),
                              _for="name")),
                        TR(INPUT(_name="name", _type="text", _size=62, _maxlength="255")),
                        TR(LABEL("Your e-mail address:",
                              SPAN(" *", _class="req"),
                              _for="address")),
                        TR(INPUT(_name="address", _type="text", _size=62, _maxlength="255")),
                        TR(LABEL("Subject:",
                              SPAN(" *", _class="req"),
                              _for="subject")),
                        TR(INPUT(_name="subject", _type="text", _size=62, _maxlength="255")),
                        TR(LABEL("Message:",
                              SPAN(" *", _class="req"),
                              _for="name")),
                        TR(TEXTAREA(_name="message", _class="resizable", _rows=5, _cols=62)),
                        TR(INPUT(_type="submit", _value="Send e-mail")),
                        ),
                    _id="mailform"
                    )
                )
        s3 = response.s3
        if s3.cdn:
            if s3.debug:
                s3.scripts.append("http://ajax.aspnetcdn.com/ajax/jquery.validate/1.9/jquery.validate.js")
            else:
                s3.scripts.append("http://ajax.aspnetcdn.com/ajax/jquery.validate/1.9/jquery.validate.min.js")

        else:
            if s3.debug:
                s3.scripts.append("/%s/static/scripts/jquery.validate.js" % request.application)
            else:
                s3.scripts.append("/%s/static/scripts/jquery.validate.min.js" % request.application)
        s3.jquery_ready.append(
'''$('#mailform').validate({
 errorClass:'req',
 rules:{
  name:{
   required:true
  },
  subject:{
   required:true
  },
  message:{
   required:true
  },
  name:{
   required:true
  },
  address: {
   required:true,
   email:true
  }
 },
 messages:{
  name:"Enter your name",
  subject:"Enter a subject",
  message:"Enter a message",
  address:{
   required:"Please enter a valid email address",
   email:"Please enter a valid email address"
  }
 },
 errorPlacement:function(error,element){
  error.appendTo(element.parents('tr').prev().children())
 },
 submitHandler:function(form){
  form.submit()
 }
})''')
        # @ToDo: Move to static
        s3.jquery_ready.append(
'''$('textarea.resizable:not(.textarea-processed)').each(function() {
    // Avoid non-processed teasers.
    if ($(this).is(('textarea.teaser:not(.teaser-processed)'))) {
        return false;
    }
    var textarea = $(this).addClass('textarea-processed'), staticOffset = null;
    // When wrapping the text area, work around an IE margin bug. See:
    // http://jaspan.com/ie-inherited-margin-bug-form-elements-and-haslayout
    $(this).wrap('<div class="resizable-textarea"><span></span></div>')
    .parent().append($('<div class="grippie"></div>').mousedown(startDrag));
    var grippie = $('div.grippie', $(this).parent())[0];
    grippie.style.marginRight = (grippie.offsetWidth - $(this)[0].offsetWidth) +'px';
    function startDrag(e) {
        staticOffset = textarea.height() - e.pageY;
        textarea.css('opacity', 0.25);
        $(document).mousemove(performDrag).mouseup(endDrag);
        return false;
    }
    function performDrag(e) {
        textarea.height(Math.max(32, staticOffset + e.pageY) + 'px');
        return false;
    }
    function endDrag(e) {
        $(document).unbind("mousemove", performDrag).unbind("mouseup", endDrag);
        textarea.css('opacity', 1);
    }
});''')

        response.title = "Contact | NYC Prepared"
        return dict(form=form)

# END =========================================================================
