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
from s3.s3utils import s3_auth_user_represent_name, s3_avatar_represent, S3CustomController

THEME = "NYC"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        T = current.T
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
        layout = s3db.cms_render_posts
        listid = "latest_events"
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
        output["latest_events"] = latest_records(resource, layout, listid, limit, list_fields, orderby)

        listid = "latest_reqs"
        resource = s3db.resource("req_req")
        s3db.req_customize_req_fields()
        list_fields = s3db.get_config("req_req", "list_fields")
        layout = s3db.req_render_reqs
        resource.add_filter(S3FieldSelector("cancel") != True)
        # Order with most recent Request first
        orderby = "date desc"
        output["latest_reqs"] = latest_records(resource, layout, listid, limit, list_fields, orderby)

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
        db = current.db
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

        self._view(THEME, "index.html")
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
        script = '''
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
'''
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
            raise HTTP(404, "Unable to open Custom View: %s" % view)

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
