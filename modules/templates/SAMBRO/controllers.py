# -*- coding: utf-8 -*-

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3 import FS, S3CustomController, S3FilterForm, S3DateFilter, S3LocationFilter, S3OptionsFilter

THEME = "SAMBRO"

# =============================================================================
class index(S3CustomController):
    """ Custom home page for the Public """

    # -------------------------------------------------------------------------
    def __call__(self):
        """ Main entry point, configuration """

        logged_in = current.auth.s3_logged_in()
        if logged_in:
            fn = "alert"
        else:
            fn = "public"

        T = current.T
        s3db = current.s3db
        request = current.request

        output = {}

        # Map
        ftable = s3db.gis_layer_feature
        query = (ftable.controller == "cap") & \
                (ftable.function == fn)
        layer = current.db(query).select(ftable.layer_id,
                                         limitby=(0, 1)
                                         ).first()
        try:
            layer_id = layer.layer_id
        except:
            from s3 import s3_debug
            s3_debug("Cannot find Layer for Map")
            layer_id = None

        feature_resources = [{"name"      : T("Alerts"),
                              "id"        : "search_results",
                              "layer_id"  : layer_id,
                              "tablename" : "cap_alert",
                              "url"       : URL(c="cap", f=fn,
                                                extension="geojson"),
                              # We activate in callback after ensuring URL is updated for current filter status
                              "active"    : False,
                              }]

        _map = current.gis.show_map(callback='''S3.search.s3map()''',
                                    catalogue_layers=True,
                                    collapsed=True,
                                    feature_resources=feature_resources,
                                    save=False,
                                    )
        output["_map"] = _map

        # Filterable List of Alerts
        # - most recent first
        resource = s3db.resource("cap_alert")
        # Don't show Templates
        resource.add_filter(FS("is_template") == False)
        if not logged_in:
            # Only show Public Alerts
            resource.add_filter(FS("scope") == "Public")
        # Only show Alerts which haven't expired
        #resource.add_filter(FS("info.expires") >= request.utcnow)
        list_id = "cap_alert_datalist"
        list_fields = ["info.headline",
                       "area.name",
                       #"info.description",
                       #"info.sender_name",
                       "info.priority",
                       "status",
                       "scope",
                       "info.event_type_id",
                       ]
        # Order with most recent Alert first
        orderby = "cap_info.expires desc"
        datalist, numrows, ids = resource.datalist(fields = list_fields,
                                                   #start = None,
                                                   limit = 5,
                                                   list_id = list_id,
                                                   orderby = orderby,
                                                   layout = s3db.cap_alert_list_layout
                                                   )
        ajax_url = URL(c="cap", f=fn, args="datalist.dl", vars={"list_id": list_id})
        output[list_id] = datalist.html(ajaxurl = ajax_url,
                                        pagesize = 5
                                        )

        # @ToDo: Options are currently built from the full-set rather than the filtered set
        filter_widgets = [#S3LocationFilter("location.location_id",
                          #                 label=T("Location"),
                          #                 levels=("L0",),
                          #                 widget="multiselect",
                          #                 ),
                          S3OptionsFilter("info.priority",
                                          #label=T("Priority"),
                                          ),
                          S3OptionsFilter("info.event_type_id",
                                          #label=T("Event Type"),
                                          ),
                          S3OptionsFilter("scope",
                                          #label=T("Scope"),
                                          ),
                          S3DateFilter("info.expires",
                                       label = "",
                                       #label=T("Expiry Date"),
                                       hide_time=True,
                                       ),
                          ]
        filter_form = S3FilterForm(filter_widgets,
                                   ajax=True,
                                   submit=True,
                                   url=ajax_url,
                                   )
        output["alert_filter_form"] = filter_form.html(resource, request.get_vars, list_id)

        # Filterable News Feed
        # - most recent first
        resource = s3db.resource("cms_post")
        # Only show News posts (differentiate from e.g. online user guide)
        resource.add_filter(FS("series_id$name") == "News")
        list_id = "cms_post_datalist"
        list_fields = [#"series_id",
                       "location_id",
                       "date",
                       "body",
                       #"created_by",
                       #"created_by$organisation_id",
                       #"document.file",
                       ]
        # Order with most recent Post first
        orderby = "cms_post.date desc"
        datalist, numrows, ids = resource.datalist(fields = list_fields,
                                                   #start = None,
                                                   limit = 5,
                                                   list_id = list_id,
                                                   orderby = orderby,
                                                   # @ToDo: Custom layout with more button to expand content block
                                                   layout = s3db.cms_post_list_layout
                                                   )
        ajax_url = URL(c="cms", f="post", args="datalist.dl", vars={"list_id": list_id})
        output[list_id] = datalist.html(ajaxurl = ajax_url,
                                        pagesize = 5
                                        )

        #filter_widgets = [#S3LocationFilter("location_id",
        #                  #                 label="",
        #                  #                 levels=("L0",),
        #                  #                 widget="multiselect",
        #                  #                 ),
        #                  # @ToDo: Source (Series? Tag?)
        #                  #S3OptionsFilter(),
        #                  ]
        #filter_form = S3FilterForm(filter_widgets,
        #                           ajax=True,
        #                           submit=True,
        #                           url=ajax_url,
        #                           )
        #output["news_filter_form"] = filter_form.html(resource, request.get_vars, list_id)

        # Title and view
        output["title"] = current.deployment_settings.get_system_name()
        self._view(THEME, "index.html")

        s3 = current.response.s3
        # Custom CSS
        s3.stylesheets.append("../themes/SAMBRO/style.css")

        # Custom JS
        s3.scripts.append("/%s/static/themes/SAMBRO/js/homepage.js" % request.application)

        return output

# =============================================================================
class subscriptions(S3CustomController):
    """ Custom page to manage subscriptions """

    # -------------------------------------------------------------------------
    def __call__(self):
        """ Main entry point, configuration """

        T = current.T
        s3db = current.s3db
        settings = current.deployment_settings
        gis = current.gis

        # Must be logged in
        auth = current.auth
        if not auth.s3_logged_in():
            auth.permission.fail()

        # Available resources
        resources = [dict(resource="cap_alert",
                          url="cap/alert",
                          label=T("Updates")),
                     ]

        # Filter widgets
        # @note: subscription manager has no resource context, so
        #        must configure fixed options or lookup resources
        #        for filter widgets which need it.
        filters = [S3OptionsFilter("event_type_id",
                                   label = T("Event Type"),
                                   options=self._options("event_type_id"),
                                   widget="multiselect",
                                   resource = "cap_info",
                                   _name = "event-filter",
                                   ),
                   S3OptionsFilter("priority",
                                   label = T("Priority"),
                                   options=self._options("priority"),
                                   widget="multiselect",
                                   resource = "cap_info",
                                   _name = "priority-filter",
                                   ),
                   S3LocationFilter("location_id",
                                    label = T("Location(s)"),
                                    resource = "cap_area_location",
                                    options = self._options("location_id"),
                                    _name = "location-filter",
                                    ),
                   S3OptionsFilter("language",
                                   label = T("Language"),
                                   options = settings.get_cap_languages(),
                                   represent = "%(name)s",
                                   resource = "cap_info",
                                   _name = "language-filter",
                                   ),
                   ]

        # Title and view
        title = T("Subscriptions")
        self._view(THEME, "subscriptions.html")

        # Form
        form = self._manage_subscriptions(resources, filters)

        return dict(title = title,
                    form = form,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def _options(fieldname):
        """
            Lookup the full set of options for a Filter Widget
            - for Subscriptions we don't want to see just the options available in current data
        """
        
        if fieldname == "event_type_id":
            T = current.T
            etable = current.s3db.event_event_type
            rows = current.db(etable.deleted == False).select(etable.id,
                                                              etable.name)
            options = {}
            for row in rows:
                options[row.id] = T(row.name)
        elif fieldname == "priority":
            T = current.T
            wptable = current.s3db.cap_warning_priority
            rows = current.db(wptable.deleted == False).select(wptable.id,
                                                               wptable.name)
            options = {}
            for row in rows:
                options[row.id] = T(row.name)
        elif fieldname == "location_id":
            ltable = current.s3db.gis_location
            query = (ltable.deleted == False)
            # IDs converted inside widget's _options() function
            rows = current.db(query).select(ltable.id)
            options = [row.id for row in rows]
            
        return options

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

        methods = [("EMAIL", T("Email")),
                   ("SMS", T("SMS"))
                   ]
                        
        method_options = Storage(name = "method", requires = IS_IN_SET(methods))
        
        rows.append(("method_selector__row",
                     "%s:" % labels.NOTIFY_BY,
                     selector(method_options,
                              subscription["method"],
                              _id="method_selector"),
                     ""))

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
        script = URL(c="static", f="scripts", args=["S3", "s3.subscriptions.js"])
        response = current.response
        response.s3.scripts.append(script)

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
            subscription["method"] = formvars.method

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
                               stable.method,
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
                           "method": s.method
                           })

        else:
            # Form defaults
            output.update({"id": None,
                           "filter_id": None,
                           "get_vars" : get_vars,
                           "resources": None,
                           "notify_on": stable.notify_on.default,
                           "frequency": stable.frequency.default,
                           "method": stable.method.default
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
            print "Get resources", resources

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

# END =========================================================================
